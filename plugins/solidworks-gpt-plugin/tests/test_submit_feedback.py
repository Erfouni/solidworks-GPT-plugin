from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "submit_feedback.py"

# Typical CAD notes: a diameter sign, degrees, an arrow, a comparison and Persian.
ISSUES = "Hole Ø10 at 45° → fillet ≥ 2 mm; سوراخ"
FEEDBACK_ID = "fb-ü-1"


class _RecordingHandler(BaseHTTPRequestHandler):
    received: list[bytes] = []

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        length = int(self.headers.get("Content-Length", "0"))
        self.received.append(self.rfile.read(length))
        body = json.dumps({"id": FEEDBACK_ID}, ensure_ascii=False).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


@unittest.skipUnless(shutil.which("curl"), "curl is required")
class SubmitFeedbackEncodingTests(unittest.TestCase):
    def setUp(self) -> None:
        _RecordingHandler.received = []
        self.server = HTTPServer(("127.0.0.1", 0), _RecordingHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def test_non_ascii_payload_is_sent_as_utf8_under_a_legacy_locale(self) -> None:
        payload = {"issues": ISSUES, "sessionId": "session-1"}
        with tempfile.TemporaryDirectory() as directory:
            payload_path = Path(directory) / "payload.json"
            payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            state_path = Path(directory) / "state.json"
            state_path.write_text(json.dumps({"sessionId": "session-1"}), encoding="utf-8")

            # Force a non-UTF-8 locale encoding in the child: ASCII on POSIX,
            # the ANSI code page (for example cp1252) on Windows, as in real use.
            env = dict(os.environ, LC_ALL="C", PYTHONCOERCECLOCALE="0")
            env.pop("PYTHONUTF8", None)
            env["NO_PROXY"] = env["no_proxy"] = "127.0.0.1,localhost"
            host = f"http://127.0.0.1:{self.server.server_address[1]}"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8=0",
                    str(SCRIPT),
                    str(payload_path),
                    "--host",
                    host,
                    "--state",
                    str(state_path),
                    "--attempts",
                    "1",
                    "--verbose",
                ],
                env=env,
                capture_output=True,
                timeout=60,
                check=False,
            )

            self.assertEqual(
                completed.returncode,
                0,
                completed.stderr.decode("utf-8", errors="replace"),
            )
            self.assertEqual(len(_RecordingHandler.received), 1)
            sent = json.loads(_RecordingHandler.received[0].decode("utf-8"))
            self.assertEqual(sent["issues"], ISSUES)
            stored = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(stored["lastFeedbackId"], FEEDBACK_ID)


if __name__ == "__main__":
    unittest.main()

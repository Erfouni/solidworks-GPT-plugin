from __future__ import annotations

import re
import shutil
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]

# Text the agent reads and follows when it calls the knowledge base.
AGENT_DOCUMENTS = [
    PLUGIN_ROOT / "AGENTS.md",
    PLUGIN_ROOT / "docs" / "runtime-api.md",
    *sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md")),
]

# An instruction to run curl in the shell: a command line or a transport rule.
SHELL_CURL = re.compile(r"^curl |`curl` (?:through the shell|shell)|(?:quoted|shell) `curl`", re.M)

WINDOWS_POWERSHELL = shutil.which("powershell.exe") if sys.platform == "win32" else None


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server API
        body = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


def health_command() -> str:
    """The first command of `$sw-kb-api`, exactly as the skill writes it."""
    text = (PLUGIN_ROOT / "skills" / "sw-kb-api" / "SKILL.md").read_text(encoding="utf-8")
    return re.search(r"^curl .*/health\"$", text, re.M).group(0)


class WindowsCurlGuidanceTests(unittest.TestCase):
    def test_every_document_that_runs_curl_names_curl_exe_for_windows(self) -> None:
        checked = 0
        for path in AGENT_DOCUMENTS:
            text = path.read_text(encoding="utf-8")
            if not SHELL_CURL.search(text):
                continue
            checked += 1
            with self.subTest(document=str(path.relative_to(PLUGIN_ROOT))):
                self.assertIn("`curl.exe`", text)
                self.assertIn("Windows PowerShell", text)
        self.assertEqual(checked, 5)


@unittest.skipUnless(WINDOWS_POWERSHELL, "Windows PowerShell is required")
class WindowsPowerShellCurlTests(unittest.TestCase):
    """Run the skill's health check in Windows PowerShell, as Codex may."""

    def setUp(self) -> None:
        self.server = HTTPServer(("127.0.0.1", 0), _HealthHandler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        host = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.command = health_command().replace("{KB_HOST}", host)

    def run_powershell(self, command: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [WINDOWS_POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_bare_curl_is_invoke_webrequest(self) -> None:
        result = self.run_powershell(self.command)
        self.assertNotIn('"status":"ok"', result.stdout)
        self.assertIn("sS", result.stderr)

    def test_curl_exe_runs_the_skill_command(self) -> None:
        result = self.run_powershell("curl.exe" + self.command[len("curl"):])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), '{"status":"ok"}')


if __name__ == "__main__":
    unittest.main()

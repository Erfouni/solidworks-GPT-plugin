from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_feedback.py"

ISSUES = "Hole Ø10 at 45° → fillet ≥ 2 mm; سوراخ"


def legacy_locale_env() -> dict[str, str]:
    # PYTHONIOENCODING makes text-mode stdin non-UTF-8 on every OS, the way
    # cp1252 does on a Windows console, even where the locale is UTF-8.
    env = dict(os.environ, LC_ALL="C", PYTHONCOERCECLOCALE="0", PYTHONIOENCODING="latin-1")
    env.pop("PYTHONUTF8", None)
    return env


class ValidateFeedbackStdinTests(unittest.TestCase):
    def run_validator(self, stdin: bytes, output: Path) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, "-X", "utf8=0", str(SCRIPT), "-", "--write-normalized", str(output)],
            input=stdin,
            env=legacy_locale_env(),
            capture_output=True,
            timeout=30,
            check=False,
        )

    def test_stdin_gives_the_same_text_as_a_file(self) -> None:
        payload = {"issues": ISSUES, "sessionId": "session-1"}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "normalized.json"
            completed = self.run_validator(
                json.dumps(payload, ensure_ascii=False).encode("utf-8"), output
            )
            self.assertEqual(
                completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace")
            )
            normalized = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(normalized["issues"], ISSUES)

    def test_invalid_utf8_on_stdin_is_a_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "normalized.json"
            completed = self.run_validator(b'{"issues": "\xff", "sessionId": "s"}', output)
            self.assertEqual(completed.returncode, 1)
            self.assertIn(b"Invalid feedback payload", completed.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

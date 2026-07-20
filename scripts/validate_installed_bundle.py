#!/usr/bin/env python3
"""Validate the plugin after copying it into Codex's versioned cache layout."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PLUGIN = REPOSITORY_ROOT / "plugins" / "solidworks-gpt-plugin"


def main() -> int:
    manifest_path = SOURCE_PLUGIN / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    name = manifest["name"]
    version = manifest["version"]

    with tempfile.TemporaryDirectory() as directory:
        installed_plugin = Path(directory) / name / version
        shutil.copytree(SOURCE_PLUGIN, installed_plugin)
        runner = installed_plugin / "scripts" / "run_checks.py"
        if not runner.is_file():
            raise FileNotFoundError(f"Installed bundle is missing validator: {runner}")
        subprocess.run([sys.executable, str(runner)], check=True)

    print(f"Installed bundle checks passed ({name}@{version}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

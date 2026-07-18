#!/usr/bin/env python3
"""Run self-contained structural and runtime checks for the plugin."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def check_manifest() -> None:
    manifest = load_json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json")
    if manifest.get("name") != PLUGIN_ROOT.name:
        raise ValueError("Plugin folder name and manifest name must match")
    for key in ("version", "description", "author", "skills", "interface"):
        if not manifest.get(key):
            raise ValueError(f"Plugin manifest is missing {key}")

    marketplace = load_json(
        REPOSITORY_ROOT / ".agents" / "plugins" / "marketplace.json"
    )
    entries = marketplace.get("plugins") or []
    matching = [entry for entry in entries if entry.get("name") == manifest["name"]]
    if len(matching) != 1:
        raise ValueError("Marketplace must contain exactly one plugin entry")
    if matching[0].get("source", {}).get("path") != f"./plugins/{PLUGIN_ROOT.name}":
        raise ValueError("Marketplace source.path does not match plugin location")


def check_skills() -> None:
    skill_files = sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md"))
    if len(skill_files) != 5:
        raise ValueError(f"Expected 5 skills, found {len(skill_files)}")
    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        if "[TODO:" in text:
            raise ValueError(f"Unresolved TODO in {path}")
        if not text.startswith("---\nname: "):
            raise ValueError(f"Invalid skill frontmatter in {path}")
        if f"name: {path.parent.name}\n" not in text:
            raise ValueError(f"Skill name does not match folder: {path}")


def check_python() -> None:
    scripts = sorted((PLUGIN_ROOT / "scripts").glob("*.py"))
    for script in scripts:
        py_compile.compile(str(script), doraise=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(PLUGIN_ROOT / "tests"),
            "-v",
        ],
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> int:
    check_manifest()
    check_skills()
    load_json(PLUGIN_ROOT / "schemas" / "feedback-submission.schema.json")
    check_python()
    print("All plugin checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

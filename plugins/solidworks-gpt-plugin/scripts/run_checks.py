#!/usr/bin/env python3
"""Run self-contained structural and runtime checks for the plugin."""

from __future__ import annotations

import json
import py_compile
import re
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
    plugin_manifest_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    root_manifest_path = REPOSITORY_ROOT / ".codex-plugin" / "plugin.json"
    manifest = load_json(plugin_manifest_path)
    root_manifest = load_json(root_manifest_path)
    if manifest.get("name") != PLUGIN_ROOT.name:
        raise ValueError("Plugin folder name and manifest name must match")
    for key in ("version", "description", "author", "skills", "interface"):
        if not manifest.get(key):
            raise ValueError(f"Plugin manifest is missing {key}")

    for key in ("name", "version", "description", "author", "repository", "license"):
        if root_manifest.get(key) != manifest.get(key):
            raise ValueError(f"Root and bundled manifests disagree on {key}")
    if root_manifest.get("skills") != "./plugins/solidworks-gpt-plugin/skills/":
        raise ValueError("Root manifest skills path does not target the bundled plugin")

    for path, value in (
        (plugin_manifest_path, manifest),
        (root_manifest_path, root_manifest),
    ):
        icon = value.get("interface", {}).get("composerIcon")
        if not icon:
            raise ValueError(f"Plugin manifest is missing interface.composerIcon: {path}")
        icon_path = (path.parent.parent / icon).resolve()
        if not icon_path.is_file() or icon_path.suffix.lower() not in {".svg", ".png"}:
            raise ValueError(f"Plugin icon is missing or unsupported: {icon_path}")

    marketplace = load_json(
        REPOSITORY_ROOT / ".agents" / "plugins" / "marketplace.json"
    )
    entries = marketplace.get("plugins") or []
    matching = [entry for entry in entries if entry.get("name") == manifest["name"]]
    if len(matching) != 1:
        raise ValueError("Marketplace must contain exactly one plugin entry")
    if matching[0].get("source", {}).get("path") != f"./plugins/{PLUGIN_ROOT.name}":
        raise ValueError("Marketplace source.path does not match plugin location")


def check_repository_security() -> None:
    if not (REPOSITORY_ROOT / "SECURITY.md").is_file():
        raise ValueError("Repository must include SECURITY.md")
    for filename in ("README.md", "SECURITY.md", "LICENSE", "requirements-lock.txt"):
        if not (PLUGIN_ROOT / filename).is_file():
            raise ValueError(f"Installable plugin bundle must include {filename}")

    root_icon = REPOSITORY_ROOT / "assets" / "icon.svg"
    plugin_icon = PLUGIN_ROOT / "assets" / "icon.svg"
    if root_icon.read_bytes() != plugin_icon.read_bytes():
        raise ValueError("Root and bundled plugin icons must stay identical")
    if root_icon.stat().st_size > 50_000:
        raise ValueError("Plugin icon must remain under 50 KB")

    action_pattern = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
    sha_pattern = re.compile(r"^[^@]+@[0-9a-f]{40}$")
    for workflow in sorted((REPOSITORY_ROOT / ".github" / "workflows").glob("*.yml")):
        for action in action_pattern.findall(workflow.read_text(encoding="utf-8")):
            if action.startswith("./"):
                continue
            if not sha_pattern.fullmatch(action):
                raise ValueError(f"GitHub Action must be SHA-pinned: {workflow}: {action}")


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
    check_repository_security()
    load_json(PLUGIN_ROOT / "schemas" / "feedback-submission.schema.json")
    check_python()
    print("All plugin checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

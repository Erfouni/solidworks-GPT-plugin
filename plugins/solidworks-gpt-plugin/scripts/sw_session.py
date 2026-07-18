#!/usr/bin/env python3
"""Manage SolidWorks learner session state and feedback preferences."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_FILENAME = ".sw-learner-state.json"
PAYLOAD_FILENAME = ".sw-feedback-payload.json"
PREFERENCE_FILENAME = ".sw-feedback-pref"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid session state: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Session state must be a JSON object: {path}")
    return value


def save_state(path: Path, state: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def start_session(path: Path) -> dict[str, Any]:
    state = {
        "partId": None,
        "partNumber": None,
        "sessionId": str(uuid.uuid4()),
        "payloadVersion": 0,
        "lastBuiltAt": None,
    }
    save_state(path, state)
    return state


def mark_payload(
    path: Path, part_id: str | None = None, part_number: str | None = None
) -> dict[str, Any]:
    state = load_state(path)
    if not state.get("sessionId"):
        raise ValueError("Start the SolidWorks session before building feedback")
    state["payloadVersion"] = int(state.get("payloadVersion") or 0) + 1
    state["lastBuiltAt"] = utc_now()
    if part_id is not None:
        state["partId"] = None if part_id.lower() == "null" else part_id
    if part_number is not None:
        state["partNumber"] = part_number
    save_state(path, state)
    return state


def mark_feedback_submitted(path: Path, feedback_id: str) -> dict[str, Any]:
    state = load_state(path)
    if not state.get("sessionId"):
        raise ValueError("Cannot record feedback without a sessionId")
    state["lastFeedbackId"] = feedback_id
    save_state(path, state)
    return state


def preference_path() -> Path:
    return Path.home() / PREFERENCE_FILENAME


def read_preference(path: Path | None = None) -> str:
    target = path or preference_path()
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8").strip()


def set_always_preference(path: Path | None = None) -> None:
    target = path or preference_path()
    target.write_text("always\n", encoding="utf-8")


def cleanup_payload(path: Path) -> None:
    path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=Path(STATE_FILENAME))
    parser.add_argument("--payload", type=Path, default=Path(PAYLOAD_FILENAME))
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("start", help="Start a new task-scoped session")
    subparsers.add_parser("show", help="Print current session state")

    mark = subparsers.add_parser("mark-payload", help="Record a payload build")
    mark.add_argument("--part-id")
    mark.add_argument("--part-number")

    feedback = subparsers.add_parser(
        "mark-feedback", help="Record the accepted feedback ID"
    )
    feedback.add_argument("feedback_id")

    pref = subparsers.add_parser("preference", help="Read or set consent preference")
    pref.add_argument("action", choices=("show", "always", "clear"))

    subparsers.add_parser("cleanup", help="Remove the temporary feedback payload")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "start":
            print(start_session(args.state)["sessionId"])
        elif args.command == "show":
            print(json.dumps(load_state(args.state), ensure_ascii=False, indent=2))
        elif args.command == "mark-payload":
            state = mark_payload(args.state, args.part_id, args.part_number)
            print(state["payloadVersion"])
        elif args.command == "mark-feedback":
            mark_feedback_submitted(args.state, args.feedback_id)
            print(args.feedback_id)
        elif args.command == "preference":
            target = preference_path()
            if args.action == "show":
                print(read_preference(target))
            elif args.action == "always":
                set_always_preference(target)
                print("always")
            else:
                target.unlink(missing_ok=True)
                print("cleared")
        elif args.command == "cleanup":
            cleanup_payload(args.payload)
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from submit_feedback import parse_response  # noqa: E402
from run_checks import (  # noqa: E402
    find_source_repository_root,
    plugin_directory_matches_manifest,
)
from sw_session import (  # noqa: E402
    load_state,
    mark_feedback_submitted,
    mark_payload,
    read_preference,
    set_always_preference,
    start_session,
)
from validate_feedback import ValidationError, normalize_payload  # noqa: E402


class SessionStateTests(unittest.TestCase):
    def test_session_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / ".sw-learner-state.json"
            started = start_session(state_path)
            self.assertEqual(started["payloadVersion"], 0)
            self.assertTrue(started["sessionId"])

            built = mark_payload(state_path, "null", "PRJ-SHAFT-001")
            self.assertEqual(built["payloadVersion"], 1)
            self.assertIsNone(built["partId"])
            self.assertEqual(built["partNumber"], "PRJ-SHAFT-001")

            submitted = mark_feedback_submitted(state_path, "feedback-123")
            self.assertEqual(submitted["lastFeedbackId"], "feedback-123")
            self.assertEqual(load_state(state_path)["sessionId"], started["sessionId"])

    def test_preference_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            preference = Path(directory) / ".sw-feedback-pref"
            self.assertEqual(read_preference(preference), "")
            set_always_preference(preference)
            self.assertEqual(read_preference(preference), "always")


class FeedbackValidationTests(unittest.TestCase):
    def test_empty_arrays_are_omitted(self) -> None:
        payload = normalize_payload(
            {
                "issues": "Built and validated a parametric shaft.",
                "sessionId": "session-1",
                "partId": None,
                "images": [],
                "macros": [],
            }
        )
        self.assertNotIn("images", payload)
        self.assertNotIn("macros", payload)

    def test_macro_requires_full_minimum_shape(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_payload(
                {
                    "issues": "Built a part.",
                    "sessionId": "session-1",
                    "macros": [{"name": "build_part", "language": "python"}],
                }
            )

    def test_valid_lesson(self) -> None:
        payload = normalize_payload(
            {
                "issues": "Built and checked the component.",
                "sessionId": "session-1",
                "lessons": [
                    {
                        "category": "modeling/API",
                        "title": "Use explicit documents",
                        "whatHappened": "The active document changed.",
                        "rootCause": "An implicit ActiveDoc lookup was used.",
                        "prevention": "Pass the saved document reference to every call.",
                        "severity": "high",
                    }
                ],
            }
        )
        self.assertEqual(payload["lessons"][0]["severity"], "high")

    def test_http_status_parsing(self) -> None:
        body, status = parse_response(json.dumps({"id": "abc"}) + "\n201")
        self.assertEqual(json.loads(body)["id"], "abc")
        self.assertEqual(status, "201")


class InstalledBundleValidationTests(unittest.TestCase):
    def test_source_checkout_and_installed_bundle_layouts_are_distinguished(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_plugin = root / "source" / "plugins" / "solidworks-gpt-plugin"
            (source_plugin / ".codex-plugin").mkdir(parents=True)
            (root / "source" / ".codex-plugin").mkdir(parents=True)
            (root / "source" / ".agents" / "plugins").mkdir(parents=True)
            (root / "source" / ".codex-plugin" / "plugin.json").write_text("{}")
            (root / "source" / ".agents" / "plugins" / "marketplace.json").write_text("{}")

            installed_plugin = root / "cache" / "solidworks-gpt-plugin" / "1.0.1"
            (installed_plugin / ".codex-plugin").mkdir(parents=True)
            local_plugin = root / "local-marketplace" / "solidworks-gpt-plugin"
            (local_plugin / ".codex-plugin").mkdir(parents=True)

            self.assertEqual(find_source_repository_root(source_plugin), root / "source")
            self.assertIsNone(find_source_repository_root(installed_plugin))
            self.assertTrue(
                plugin_directory_matches_manifest(
                    source_plugin, root / "source", "solidworks-gpt-plugin", "1.0.1"
                )
            )
            self.assertTrue(
                plugin_directory_matches_manifest(
                    installed_plugin, None, "solidworks-gpt-plugin", "1.0.1"
                )
            )
            self.assertTrue(
                plugin_directory_matches_manifest(
                    local_plugin, None, "solidworks-gpt-plugin", "1.0.1"
                )
            )
            self.assertFalse(
                plugin_directory_matches_manifest(
                    installed_plugin, None, "solidworks-gpt-plugin", "2.0.0"
                )
            )


if __name__ == "__main__":
    unittest.main()

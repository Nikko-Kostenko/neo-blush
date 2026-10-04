import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import policy


class PreferencesTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.environment = patch.dict(os.environ, {
            "NEO_NOTIFICATION_STATE_DIR": str(root / "state"),
            "XDG_RUNTIME_DIR": str(root / "runtime"),
            "NEO_NOTIFICATION_BASE_CONFIG": str(root / "base.json"),
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.directory.cleanup)
        policy.base_config().write_text(json.dumps({"timeout": 8, "widgets": ["title"]}))

    def test_choices_survive_regeneration_and_leave_base_unchanged(self):
        original = policy.base_config().read_bytes()
        policy.save_preference("App [work]+", "ignored")
        policy.apply()
        first = policy.runtime_config().read_bytes()
        policy.runtime_config().unlink()
        policy.apply()
        self.assertEqual(policy.runtime_config().read_bytes(), first)
        self.assertEqual(policy.base_config().read_bytes(), original)
        self.assertEqual(policy.runtime_config().stat().st_mode & 0o777, 0o600)
        self.assertEqual((policy.state_dir() / "preferences.json").stat().st_mode & 0o777, 0o600)

    def test_literal_app_names_do_not_block_other_senders(self):
        policy.save_preference("App [work]+", "ignored")
        policy.apply()
        rule = next(iter(json.loads(policy.runtime_config().read_text())["notification-visibility"].values()))
        self.assertIsNotNone(re.fullmatch(rule["app-name"], "App [work]+"))
        self.assertIsNone(re.fullmatch(rule["app-name"], "App w"))

    def test_specific_allow_precedes_default_block_and_configured_rules_survive(self):
        policy.base_config().write_text(json.dumps({"notification-visibility": {
            "configured": {"app-name": "^Other$", "state": "muted"}}}))
        policy.save_preference(None, "ignored")
        policy.save_preference("Allowed", "enabled")
        policy.apply()
        rules = list(json.loads(policy.runtime_config().read_text())["notification-visibility"].values())
        self.assertEqual(rules[0], {"app-name": "^Allowed$", "state": "enabled"})
        self.assertEqual(rules[1], {"app-name": "^Other$", "state": "muted"})
        self.assertEqual(rules[-1], {"app-name": ".*", "state": "ignored"})
        policy.save_preference("Allowed", "default")
        self.assertNotIn("Allowed", policy.preferences()["apps"])

    def test_discovery_and_preferences_do_not_overwrite_each_other(self):
        policy.record_app("Editor", "org.example.Editor")
        policy.save_preference("Editor", "muted")
        policy.record_app("Browser", "org.example.Browser")
        self.assertEqual(policy.preferences()["apps"], {"Editor": "muted"})
        self.assertEqual(set(policy.applications()), {"Editor", "Browser"})
        self.assertEqual(policy.applications()["Editor"], {"desktop-entry": "org.example.Editor"})

    def test_invalid_preferences_are_not_silently_overwritten(self):
        policy.atomic_json(policy.state_dir() / "preferences.json", {"default": "bogus", "apps": {}})
        with self.assertRaises(ValueError):
            policy.save_preference("Editor", "ignored")
        self.assertEqual(json.loads((policy.state_dir() / "preferences.json").read_text())["default"], "bogus")


if __name__ == "__main__":
    unittest.main()

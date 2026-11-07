import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agf.common import AgfError
from agf.profiles import initialize, show


class ProfileTests(unittest.TestCase):
    def test_project_overrides_only_supplied_preferences(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user = root / "user.json"
            project = root / "project.json"
            user.write_text(json.dumps({"version": 1, "language": "zh-TW", "writing": {"preferences": ["custom"]}}))
            project.write_text(json.dumps({"version": 1, "language": "en", "writing": {"audience": "maintainer"}}))
            value = show(root, user=user, project=project)
            self.assertEqual(value["profile"]["language"], "en")
            self.assertEqual(value["profile"]["writing"]["preferences"], ["custom"])
            self.assertEqual(value["profile"]["writing"]["audience"], "maintainer")
            self.assertEqual(len(value["sources"]), 3)

    def test_initialization_preview_does_not_create_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "new" / "profile.json"
            self.assertEqual(initialize(path)["status"], "PLAN")
            self.assertFalse(path.parent.exists())
            initialize(path, apply=True)
            with self.assertRaises(AgfError):
                initialize(path, apply=True)

    def test_explicit_missing_profile_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(AgfError):
                show(temp, user=Path(temp) / "missing.json")

    def test_no_user_skips_global_private_preferences(self):
        with tempfile.TemporaryDirectory() as temp:
            private = Path(temp) / "private.json"
            private.write_text(json.dumps({"version": 1, "language": "private"}))
            with patch("agf.profiles.user_path", return_value=private):
                self.assertNotEqual(show(temp, no_user=True)["profile"]["language"], "private")

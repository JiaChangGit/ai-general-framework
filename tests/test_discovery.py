import argparse
import json
from pathlib import Path
import tempfile
import unittest

from agf.common import AgfError
from agf.manage import doctor


class DiscoveryTests(unittest.TestCase):
    def test_project_markers_do_not_read_remote_config_or_assume_hosting(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".svn").mkdir()
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("[remote origin]\nurl=https://name:private-token@example.invalid/project\n")
            child = root / "src"
            child.mkdir()
            result = doctor(argparse.Namespace(host="all", root=str(child)))
            found = result["project"]
            self.assertEqual({item["tool"] for item in found["markers"]}, {"git", "svn"})
            self.assertEqual(found["hosting_platform"], "not_determined")
            self.assertNotIn("private-token", json.dumps(result))
            self.assertIn("glab", result["optional_tools"])

    def test_missing_project_is_actionable(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(AgfError):
                doctor(argparse.Namespace(host="all", root=str(Path(temp) / "missing")))

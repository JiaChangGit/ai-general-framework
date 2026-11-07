from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from agf.gittools import intent, scope, snapshot


@unittest.skipUnless(shutil.which("git"), "Git unavailable")
class GitTests(unittest.TestCase):
    def test_staged_untracked_and_dirty_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def git(*args):
                subprocess.run(["git", "-C", temp, *args], check=True, capture_output=True)
            git("init", "-q")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "user.name", "Fixture")
            (root / "src").mkdir()
            file = root / "src" / "a.txt"
            file.write_text("old\n")
            git("add", ".")
            git("commit", "-qm", "fixture")
            before = snapshot(root)
            file.write_text("new\n")
            (root / "other.txt").write_text("untracked\n")
            value = scope(root, ["src"])
            self.assertEqual(value["outside"], ["other.txt"])
            self.assertNotEqual(before["tracked_diff_sha256"], snapshot(root)["tracked_diff_sha256"])
            self.assertEqual(scope(root, ["."])["status"], "IN_SCOPE")

    def test_unborn_repo_is_supported(self):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(["git", "init", "-q", temp], check=True, capture_output=True)
            self.assertIsNone(snapshot(temp)["head"])

    def test_intent_preserves_supplied_reason(self):
        result = intent("Cancel timed-out request", "A timed-out request kept holding its buffer.", "Tested cancellation; hardware not tested.")
        self.assertIn("kept holding", result["message"])
        self.assertIn("hardware not tested", result["message"])

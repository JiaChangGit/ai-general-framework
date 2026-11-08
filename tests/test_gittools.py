from pathlib import Path
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

from agf.common import AgfError
from agf.gittools import scope, snapshot, summary


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

    @unittest.skipUnless(os.name == "posix", "Invalid UTF-8 filenames require POSIX byte paths")
    def test_snapshot_rejects_undecodable_status(self):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(["git", "init", "-q", temp], check=True, capture_output=True)
            first = os.fsencode(temp) + b"/\xff"
            second = os.fsencode(temp) + b"/\xfe"
            with open(first, "wb") as stream:
                stream.write(b"x")
            with self.assertRaisesRegex(AgfError, "reliably decode"):
                snapshot(temp)
            os.rename(first, second)
            with self.assertRaisesRegex(AgfError, "reliably decode"):
                snapshot(temp)

    @unittest.skipUnless(os.name == "posix", "Git shell driver fixture uses POSIX command quoting")
    def test_summary_does_not_execute_configured_text_conversion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def git(*args):
                subprocess.run(["git", "-C", temp, *args], check=True, capture_output=True)
            git("init", "-q")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "user.name", "Fixture")
            (root / ".gitattributes").write_text("*.txt diff=synthetic\n")
            target = root / "test.txt"
            target.write_text("before\n")
            git("add", ".")
            git("commit", "-qm", "fixture")
            marker = root / "marker"
            driver = root / "driver.py"
            driver.write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n")
            git("config", "diff.synthetic.textconv", f"{shlex.quote(sys.executable)} {shlex.quote(str(driver))}")
            target.write_text("after\n")
            summary(root)
            self.assertFalse(marker.exists())

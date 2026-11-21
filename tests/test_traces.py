import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from agf import manage, traces

GIT = shutil.which("git")


def git(root, *arguments):
    return subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True, check=True).stdout


@unittest.skipUnless(GIT, "git is not installed")
class TracesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Tester")
        git(self.root, "config", "user.email", "tester@example.invalid")
        git(self.root, "config", "commit.gpgsign", "false")
        (self.root / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
        git(self.root, "add", "main.c")
        git(self.root, "commit", "-q", "-m", "Add main")

    def exclude_text(self):
        return (self.root / ".git" / "info" / "exclude").read_text(encoding="utf-8")

    def test_outside_git_nothing_is_checked_or_written(self):
        with tempfile.TemporaryDirectory() as plain:
            self.assertEqual(traces.check(plain)["status"], "NOT_GIT")
            self.assertEqual(traces.exclude(plain, apply=True)["status"], "NOT_GIT")

    def test_traces_in_files_commits_and_index_are_reported(self):
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
        (self.root / "docs" / ".agf").mkdir(parents=True)
        (self.root / "docs" / ".agf" / "notes.md").write_text("x\n", encoding="utf-8")
        (self.root / "README.md").write_text("Intro\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n", encoding="utf-8")
        git(self.root, "add", "CLAUDE.md", "docs/.agf/notes.md", "README.md")
        git(self.root, "commit", "-q", "-m", "Add docs\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        result = traces.check(self.root)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(sorted(result["tracked_ai_files"]["paths"]), ["CLAUDE.md", "docs/.agf/notes.md"])
        self.assertEqual(result["untrack_command"][:4], ["git", "rm", "-r", "--cached"])
        self.assertEqual(result["commits_with_ai_markers"]["count"], 1)
        self.assertEqual(result["file_markers"]["count"], 1)
        self.assertFalse(result["exclude_block"])
        self.assertEqual(result["_exit_code"], 1)

    def test_a_human_co_author_is_not_a_trace(self):
        (self.root / "a.txt").write_text("a\n", encoding="utf-8")
        git(self.root, "add", "a.txt")
        git(self.root, "commit", "-q", "-m", "Pair work\n\nCo-Authored-By: Jane Doe <jane@example.invalid>")
        self.assertEqual(traces.check(self.root)["commits_with_ai_markers"]["count"], 0)

    def test_exclude_is_previewed_idempotent_and_removable(self):
        info = self.root / ".git" / "info" / "exclude"
        info.write_text("*.o\n", encoding="utf-8")
        self.assertEqual(traces.exclude(self.root)["status"], "ADDED")
        self.assertNotIn(traces.BEGIN, self.exclude_text())
        traces.exclude(self.root, apply=True)
        self.assertIn(".claude/", self.exclude_text())
        self.assertEqual(traces.exclude(self.root, apply=True)["status"], "UNCHANGED")
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        clean = traces.check(self.root)
        self.assertEqual((clean["status"], clean["_exit_code"]), ("CLEAN", 0))
        self.assertEqual(traces.remove(self.root, apply=True)["status"], "REMOVED")
        self.assertEqual(self.exclude_text(), "*.o\n")

    def test_a_project_inside_another_repository_is_left_alone(self):
        nested = self.root / "sub"
        nested.mkdir()
        result = traces.exclude(nested, apply=True)
        self.assertEqual(result["status"], "NESTED")
        self.assertFalse((self.root / ".git" / "info" / "exclude").is_file() and traces.BEGIN in self.exclude_text())


@unittest.skipUnless(GIT, "git is not installed")
class InstallDefaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.source = base / "source"
        (self.source / "skills" / "trace").mkdir(parents=True)
        (self.source / "skills" / "trace" / "SKILL.md").write_text("---\nname: trace\ndescription: Trace.\n---\nBody\n", encoding="utf-8")
        (self.source / "templates").mkdir()
        (self.source / "templates" / "project-rules.md").write_text("Keep task scope.\n", encoding="utf-8")
        (self.source / "scripts").mkdir()
        (self.source / "scripts" / "agf.py").write_text("print('fixture')\n", encoding="utf-8")
        (self.source / "docs").mkdir()
        for name in manage.GUIDES:
            (self.source / "docs" / name).write_text(f"{name}\n", encoding="utf-8")
        self.root = base / "project"
        self.root.mkdir()
        git(self.root, "init", "-q")

    def run_project(self, operation, apply=True, ai_traces=None):
        return manage.project(argparse.Namespace(operation=operation, target=str(self.root), source=str(self.source), host=["claude"],
                                                 skill=["trace"], tools="shared", apply=apply, ai_traces=ai_traces))

    def rules(self):
        return (self.root / ".agf" / "managed" / "project-rules.md").read_text(encoding="utf-8")

    def test_new_installs_keep_ai_files_local_and_add_the_rule(self):
        result = self.run_project("install")
        self.assertEqual(result["ai_traces"], "exclude")
        self.assertEqual(result["ai_traces_exclude"]["status"], "ADDED")
        self.assertIn("不留 AI 痕跡", self.rules())
        self.assertEqual(git(self.root, "status", "--porcelain"), "")  # CLAUDE.md, AGENTS.md, .agf/, .claude/ stay out of Git
        self.assertEqual(manage.project(argparse.Namespace(operation="status", target=str(self.root)))["ai_traces"], "exclude")

    def test_opting_out_writes_neither_the_block_nor_the_rule(self):
        self.run_project("install", ai_traces="keep")
        self.assertNotIn("不留 AI 痕跡", self.rules())
        self.assertIn("CLAUDE.md", git(self.root, "status", "--porcelain"))

    def test_rollback_of_the_first_install_removes_the_block(self):
        self.run_project("install")
        self.run_project("rollback")
        exclude = self.root / ".git" / "info" / "exclude"
        self.assertNotIn(traces.BEGIN, exclude.read_text(encoding="utf-8") if exclude.is_file() else "")


if __name__ == "__main__":
    unittest.main()

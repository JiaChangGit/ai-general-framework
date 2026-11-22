import os
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

    def commit(self, message):
        (self.root / "n.txt").write_text(message, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "n.txt"], check=True)
        return subprocess.run(["git", "-C", str(self.root), "commit", "-q", "-m", message], capture_output=True, text=True)

    def test_the_commit_msg_hook_rejects_ai_trailers_with_a_fix_hint(self):
        self.assertEqual(traces.hook(self.root, apply=True)["status"], "ADDED")
        refused = self.commit("Fix average\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--no-verify", refused.stderr)
        self.assertNotEqual(self.commit("Docs\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)").returncode, 0)
        self.assertEqual(self.commit("Fix average on empty input\n\nCo-Authored-By: Jane Doe <jane@example.invalid>").returncode, 0)
        self.assertTrue(traces.check(self.root)["commit_msg_hook"])
        self.assertEqual(traces.hook(self.root, apply=True)["status"], "UNCHANGED")
        self.assertEqual(traces.hook(self.root, apply=True, remove=True)["status"], "REMOVED")
        self.assertEqual(self.commit("Again\n\nCo-Authored-By: Claude <noreply@anthropic.com>").returncode, 0)

    def test_a_hook_the_project_already_has_is_left_alone(self):
        own = self.root / ".git" / "hooks" / "commit-msg"
        own.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.assertEqual(traces.hook(self.root, apply=True)["status"], "FOREIGN_HOOK")
        self.assertEqual(traces.hook(self.root, apply=True, remove=True)["status"], "UNCHANGED")
        self.assertEqual(own.read_text(encoding="utf-8"), "#!/bin/sh\nexit 0\n")

    def test_tool_authors_are_found_and_similar_human_text_is_not(self):
        for text in ("Co-Authored-By: Gemini <g@example.invalid>", "Co-authored-by: Claude <claude@example.invalid>",
                     "Co-authored-by: Claude Sonnet 5.5 (1M context) <noreply@anthropic.com>",
                     "Co-authored-by: copilot-swe-agent[bot] <x@example.invalid>", "Co-authored-by: OpenAI Codex",
                     "Co-authored-by: aider (some-model) <noreply@aider.chat>", "Generated with Claude Code",
                     "Generated by ChatGPT.", "Generated with [Claude Code](https://example.invalid)"):
            self.assertTrue(traces.COMMIT_MARKERS.search(f"Subject\n\n{text}\n"), text)
        for text in ("Co-authored-by: Jane Claude <jane@example.invalid>", "Co-authored-by: Claude Martin <cm@example.invalid>",
                     "feat: cursor position generated with cursor offset", "docs: note about generated by Codex style",
                     "Generated by GPT-style tokenizer fix", "fix: IDs generated by cursor-based paging"):
            self.assertFalse(traces.COMMIT_MARKERS.search(f"Subject\n\n{text}\n"), text)

    def test_a_shared_or_tracked_hooks_path_is_not_written(self):
        for value in (".githooks", "../shared-hooks-agf"):
            git(self.root, "config", "core.hooksPath", value)
            self.assertEqual(traces.hook(self.root, apply=True)["status"], "CUSTOM_HOOKS_PATH")
            self.assertFalse((self.root / value / "commit-msg").exists())

    @unittest.skipIf(os.name == "nt", "needs symbolic links and executable stubs")
    def test_a_linked_hook_is_not_written_and_a_broken_python_does_not_block(self):
        own = self.root / ".git" / "hooks" / "commit-msg"
        own.parent.mkdir(exist_ok=True)
        own.symlink_to(self.root / "victim")
        self.assertEqual(traces.hook(self.root, apply=True)["status"], "FOREIGN_HOOK")
        self.assertFalse((self.root / "victim").exists())
        own.unlink()
        traces.hook(self.root, apply=True)
        stubs = self.root / "stubs"
        stubs.mkdir()
        for name in ("python3", "python", "py"):
            (stubs / name).write_text("#!/bin/sh\nexit 49\n", encoding="utf-8")
            (stubs / name).chmod(0o755)
        (self.root / "message").write_text("Ordinary message\n", encoding="utf-8")
        result = subprocess.run([str(own), str(self.root / "message")], env={"PATH": str(stubs)}, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_human_co_authors_and_a_lone_emoji_are_not_traces(self):
        for message in ("Pair\n\nCo-Authored-By: Devin Smith <devin@example.invalid>",
                        "Pair\n\nCo-Authored-By: Cursor Lee <lee@example.invalid>", "Ship it 🤖"):
            (self.root / "m.txt").write_text(message, encoding="utf-8")
            git(self.root, "add", "m.txt")
            git(self.root, "commit", "-q", "-m", message)
        self.assertEqual(traces.check(self.root)["commits_with_ai_markers"]["count"], 0)

    def test_a_damaged_block_is_reported_and_crlf_is_kept(self):
        info = self.root / ".git" / "info" / "exclude"
        info.write_bytes(b"*.o\r\n")
        traces.exclude(self.root, apply=True)
        self.assertIn(b"\r\n.claude/\r\n", info.read_bytes())
        traces.remove(self.root, apply=True)
        self.assertEqual(info.read_bytes(), b"*.o\r\n")
        info.write_text(traces.BEGIN + "\nCLAUDE.md\n", encoding="utf-8")  # END line deleted by hand
        with self.assertRaises(traces.AgfError):
            traces.exclude(self.root, apply=True)

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
        self.assertEqual(result["ai_traces_hook"]["status"], "ADDED")
        self.assertEqual(manage.project(argparse.Namespace(operation="status", target=str(self.root)))["ai_traces"], "exclude")

    def test_opting_out_writes_neither_the_block_nor_the_rule(self):
        self.run_project("install", ai_traces="keep")
        self.assertNotIn("不留 AI 痕跡", self.rules())
        self.assertIn("CLAUDE.md", git(self.root, "status", "--porcelain"))

    def test_keep_mode_leaves_a_block_the_user_added_and_switching_removes_ours(self):
        self.run_project("install", ai_traces="keep")
        traces.exclude(self.root, apply=True)
        (self.source / "docs" / "workflow.md").write_text("changed\n", encoding="utf-8")
        self.run_project("update")  # a real update with changed files, still in keep mode
        self.assertIn(traces.BEGIN, (self.root / ".git" / "info" / "exclude").read_text(encoding="utf-8"))
        self.run_project("update", ai_traces="exclude")
        self.run_project("update", ai_traces="keep")
        self.assertNotIn(traces.BEGIN, (self.root / ".git" / "info" / "exclude").read_text(encoding="utf-8"))

    def test_outside_git_the_rule_does_not_claim_the_files_are_excluded(self):
        plain = Path(self.temp.name) / "plain"
        plain.mkdir()
        manage.project(argparse.Namespace(operation="install", target=str(plain), source=str(self.source), host=["claude"],
                                          skill=["trace"], tools="shared", apply=True, ai_traces=None))
        rules = (plain / ".agf" / "managed" / "project-rules.md").read_text(encoding="utf-8")
        self.assertIn("不留 AI 痕跡", rules)
        self.assertNotIn("已由", rules)
        self.assertIn("agf traces exclude --apply", rules)

    def test_rollback_of_the_first_install_removes_the_block(self):
        self.run_project("install")
        self.run_project("rollback")
        exclude = self.root / ".git" / "info" / "exclude"
        self.assertNotIn(traces.BEGIN, exclude.read_text(encoding="utf-8") if exclude.is_file() else "")
        self.assertFalse((self.root / ".git" / "hooks" / "commit-msg").exists())


if __name__ == "__main__":
    unittest.main()

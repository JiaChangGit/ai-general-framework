import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "templates" / "claude-guard-hook.py"


class GuardHookTests(unittest.TestCase):
    """The hook reads a PreToolUse event on stdin; exit 2 refuses the call."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.protected = self.root / "framework"
        (self.protected / "docs").mkdir(parents=True)
        self.work = self.root / "project"
        self.work.mkdir()
        self.config = self.root / "guard.json"
        self.config.write_text(json.dumps({"protected_paths": [str(self.protected)]}), encoding="utf-8")

    def run_hook(self, tool, tool_input, config=None):
        event = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": str(self.work)}
        argv = [sys.executable, str(HOOK)] + ([str(config)] if config else [str(self.config)])
        return subprocess.run(argv, input=json.dumps(event), capture_output=True, text=True, timeout=10)

    def bash(self, command):
        return self.run_hook("Bash", {"command": command})

    def test_every_spelling_of_push_is_refused(self):
        for command in ["git push", "git push origin main", "git -C ../x push", "git --no-pager push --tags",
                        "/usr/bin/git push", "env GIT_TRACE=1 git push", "cd sub && git push",
                        "sh -c 'git push origin'", "bash -c \"cd x; git push\"", "true; git push",
                        "echo $(git push)", "rtk git push", "timeout 30 git push", "git -c x.y=z push"]:
            with self.subTest(command=command):
                result = self.bash(command)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("git push", result.stderr)

    def test_commands_that_only_mention_push_run(self):
        for command in ["git status", "git log --grep push", "echo 'git push is left to the user'",
                        "git help push", "grep -rn push docs", "git show HEAD:push.md"]:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command).returncode, 0, command)

    def test_pull_requests_and_releases_are_refused_but_reading_them_is_not(self):
        for command in ["gh pr create --fill", "gh pr merge 3", "glab mr create", "gh release create v1"]:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command).returncode, 2)
        for command in ["gh pr view 3", "gh pr list", "glab mr list"]:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command).returncode, 0)

    def test_pattern_kills_are_refused_and_pid_kills_are_not(self):
        for command in ["pkill -f raft-node", "pkill -9 -f node", "pkill -af x", "killall python3"]:
            with self.subTest(command=command):
                result = self.bash(command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("PID", result.stderr)
        for command in ["kill 1234", "kill -KILL 1234", "pkill raft-node", "pgrep -f raft-node"]:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command).returncode, 0)

    def test_file_tools_cannot_change_a_protected_path(self):
        inside = self.protected / "docs" / "a.md"
        for tool, data in [("Write", {"file_path": str(inside)}), ("Edit", {"file_path": str(inside)}),
                           ("NotebookEdit", {"notebook_path": str(self.protected / "n.ipynb")}),
                           ("Write", {"file_path": "../framework/docs/b.md"})]:
            with self.subTest(tool=tool, data=data):
                self.assertEqual(self.run_hook(tool, data).returncode, 2)
        self.assertEqual(self.run_hook("Write", {"file_path": str(self.work / "a.md")}).returncode, 0)
        self.assertEqual(self.run_hook("Read", {"file_path": str(inside)}).returncode, 0)
        # A sibling whose name only starts with the protected name is not inside it.
        sibling = self.root / "framework-s10" / "a.md"
        self.assertEqual(self.run_hook("Write", {"file_path": str(sibling)}).returncode, 0)

    def test_shell_writes_into_a_protected_path_are_refused(self):
        p = str(self.protected)
        for command in [f"echo x > {p}/docs/a.md", f"echo x >> {p}/a", f"printf x | tee {p}/a",
                        f"cp notes.md {p}/docs/", f"rm -rf {p}/docs", f"mv {p}/a /tmp/a", f"touch {p}/new",
                        f"sed -i s/a/b/ {p}/docs/a.md", f"dd if=/dev/zero of={p}/z", f"git -C {p} commit -m x",
                        f"git -C {p} reset --hard", f"cd {p} && echo x > a", "echo x > ../framework/a",
                        f"sh -c 'echo x > {p}/a'"]:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command).returncode, 2, command)

    def test_reading_from_a_protected_path_is_allowed(self):
        p = str(self.protected)
        for command in [f"cat {p}/docs/a.md", f"cp {p}/docs/a.md notes.md", f"git -C {p} status --short",
                        f"git -C {p} log --oneline -3", f"grep -rn x {p}", f"diff {p}/a {p}/b",
                        f"echo x > {self.work}/out.txt", f"ls {p} 2>/dev/null"]:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command).returncode, 0, command)

    def test_an_unreadable_configuration_refuses_everything(self):
        missing = self.root / "missing.json"
        result = self.run_hook("Bash", {"command": "ls"}, config=missing)
        self.assertEqual(result.returncode, 2)
        self.assertIn("configuration", result.stderr)
        typo = self.root / "typo.json"
        typo.write_text(json.dumps({"protected_path": ["/x"]}), encoding="utf-8")
        self.assertEqual(self.run_hook("Bash", {"command": "ls"}, config=typo).returncode, 2)

    def test_defaults_without_a_configuration_block_push_only(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": str(self.work)}
        run = lambda e: subprocess.run([sys.executable, str(HOOK)], input=json.dumps(e), capture_output=True,
                                       text=True, timeout=10, env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(run(event).returncode, 2)
        event["tool_input"]["command"] = f"echo x > {self.protected}/a"
        self.assertEqual(run(event).returncode, 0)

    def test_input_that_is_not_an_event_is_not_judged(self):
        result = subprocess.run([sys.executable, str(HOOK), str(self.config)], input="not json",
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "evals" / "host"
sys.path.insert(0, str(HOST))
import preflight  # noqa: E402
import run_claude  # noqa: E402
import trigger  # noqa: E402
import usage  # noqa: E402

FAKE_CLI = '''#!{python}
"""Stands in for the Claude Code CLI: prints a stream-json session decided by FAKE_MODE."""
import json, os, sys, time
from pathlib import Path
mode = os.environ.get("FAKE_MODE", "read")
if mode == "slow":
    time.sleep(60)
skills = sorted(p.name for p in Path(".claude/skills").glob("*")) if Path(".claude/skills").is_dir() else []
print(json.dumps({{"type": "system", "subtype": "init", "skills": skills, "tools": ["Read"], "model": "fake", "cwd": os.getcwd()}}))
uses = []
if mode == "read" and Path(".agents/skills/trace-code/SKILL.md").exists():
    uses.append({{"type": "tool_use", "id": "1", "name": "Read", "input": {{"file_path": str(Path(".agents/skills/trace-code/SKILL.md").resolve())}}}})
if mode == "skill":
    uses.append({{"type": "tool_use", "id": "1", "name": "Skill", "input": {{"skill": "trace-code"}}}})
print(json.dumps({{"type": "assistant", "message": {{"content": uses}}}}))
print(json.dumps({{"type": "result", "is_error": False, "num_turns": 1, "total_cost_usd": 0.01, "result": "done",
                  "usage": {{"input_tokens": 10, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 5}}}}))
'''


def reap(process):
    process.kill()
    process.wait()


def write_stream(path, events):
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


class RunClaudeTests(unittest.TestCase):
    def test_summary_separates_skill_calls_reads_and_paths_outside(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp) / "work"
            work.mkdir()
            stream = Path(temp) / "s.jsonl"
            write_stream(stream, [
                {"type": "system", "subtype": "init", "skills": ["trace-code"], "tools": ["Read", "Glob"], "model": "m", "cwd": str(work)},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "a", "name": "Skill", "input": {"skill": "trace-code"}},
                    {"type": "tool_use", "id": "b", "name": "Read", "input": {"file_path": str(work / ".agents/skills/debug-root-cause/SKILL.md")}},
                    {"type": "tool_use", "id": "c", "name": "Glob", "input": {"pattern": "../**/*.md"}},
                    {"type": "tool_use", "id": "d", "name": "Read", "input": {"file_path": str(work) + "2/notes.md"}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "d", "is_error": True, "content": "denied"}]}},
                {"type": "result", "is_error": False, "num_turns": 2, "total_cost_usd": 0.5, "result": "text", "usage": {"input_tokens": 3}}])
            summary = run_claude.summarize(stream, work)
            self.assertEqual(summary["skill_calls"], ["trace-code"])
            self.assertEqual(summary["skill_reads"], [{"skill": "debug-root-cause", "copy": ".agents/skills"}])
            # The relative glob and the prefix sibling ("work2") are both outside; S8's string prefix test missed the second.
            self.assertEqual(summary["outside_paths"], ["Glob ..", f"Read {work}2/notes.md"])
            self.assertEqual(summary["denied"], [{"tool": "Read", "error": "denied"}])
            self.assertEqual((summary["result"]["turns"], summary["result"]["cost_usd"]), (2, 0.5))

    def test_clean_environment_drops_host_channels(self):
        with patch.dict(os.environ, {"CLAUDECODE": "1", "CLAUDE_CODE_SSE_PORT": "4242", "HOME": "/h", "PATH": "/p"}):
            env = run_claude.clean_env({"ANTHROPIC_BASE_URL": "https://api.anthropic.com"})
            self.assertNotIn("CLAUDECODE", env)
            self.assertNotIn("CLAUDE_CODE_SSE_PORT", env)
            self.assertEqual((env["HOME"], env["ANTHROPIC_BASE_URL"]), ("/h", "https://api.anthropic.com"))
            report = preflight.environment({"ANTHROPIC_BASE_URL": "https://api.anthropic.com"})
            self.assertIn("CLAUDE_CODE_SSE_PORT", report["host_like_present"])
            self.assertEqual(report["host_like_passed"], [])


class PreflightTests(unittest.TestCase):
    def layout(self, temp):
        base = Path(temp) / "base"
        work = base / "run-1" / "work"
        work.mkdir(parents=True)
        return base, work

    def test_clean_private_parent_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            _, work = self.layout(temp)
            (work / "queue.py").write_text("print(1)\n", encoding="utf-8")
            report = preflight.check(work, ["/original/project"])
            self.assertTrue(report["ok"], report)

    def test_the_two_s8_leaks_are_found(self):
        with tempfile.TemporaryDirectory() as temp:
            base, work = self.layout(temp)
            (work / "CLAUDE.md").write_text("Project at `/original/project`.\n", encoding="utf-8")
            (base / "run-0" / "work").mkdir(parents=True)  # another group's run left next to this one
            report = preflight.check(work, ["/original/project/"])
            self.assertFalse(report["ok"])
            self.assertEqual(report["forbidden_mentions"], [{"file": "CLAUDE.md", "line": 1, "path": "/original/project"}])
            self.assertEqual(report["neighbours"], [str((base / "run-0").resolve())])

    def test_ancestor_instructions_and_outside_links_are_found(self):
        with tempfile.TemporaryDirectory() as temp:
            base, work = self.layout(temp)
            (base / "CLAUDE.md").write_text("inherited\n", encoding="utf-8")
            (Path(temp) / "secret.txt").write_text("x\n", encoding="utf-8")
            try:
                (work / "link").symlink_to(Path(temp) / "secret.txt")
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            report = preflight.check(work)
            self.assertIn(str((base / "CLAUDE.md").resolve()), report["ancestor_instructions"])
            self.assertEqual([item["link"] for item in report["links_outside"]], ["link"])
            self.assertFalse(report["ok"])


class TriggerTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)
        framework = self.temp / "framework"
        shutil.copytree(ROOT / "agf", framework / "agf", ignore=shutil.ignore_patterns("__pycache__"))
        (framework / "scripts").mkdir(parents=True)
        shutil.copy(ROOT / "scripts/agf.py", framework / "scripts/agf.py")
        shutil.copytree(ROOT / "skills/trace-code", framework / "skills/trace-code")
        (framework / "templates").mkdir()
        shutil.copy(ROOT / "templates/project-rules.md", framework / "templates/project-rules.md")
        (framework / "docs").mkdir()
        for name in ("workflow.md", "writing.md", "tools.md", "delivery.md"):
            shutil.copy(ROOT / "docs" / name, framework / "docs" / name)
        (framework / "evals/paired").mkdir(parents=True)
        (framework / "evals/paired/tasks.json").write_text(json.dumps({"startup": "Work here."}), encoding="utf-8")
        scenarios = [{"id": "trace-it", "request": "Trace it.", "materials": {"a.py": "x = 1\n"}, "expected_skill_if_available": "trace-code"},
                     {"id": "no-skill", "request": "Answer.", "materials": {"b.md": "b\n"}, "expected_skill_if_available": None}]
        (framework / "evals/scenarios.json").write_text(json.dumps({"scenarios": scenarios}), encoding="utf-8")
        self.framework = framework
        self.cli = self.temp / "fake-claude"
        self.cli.write_text(FAKE_CLI.format(python=sys.executable), encoding="utf-8")
        self.cli.chmod(0o755)

    def run_trigger(self, *extra, mode="read", wait=True):
        argv = [sys.executable, "-B", str(HOST / "trigger.py"), "run", "--framework", str(self.framework), "--base", str(self.temp / "base"),
                "--out", str(self.temp / "out"), "--cli", str(self.cli), "--env", f"FAKE_MODE={mode}", *extra]
        if not wait:
            return subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return subprocess.run(argv, capture_output=True, text=True, timeout=120)

    @unittest.skipIf(sys.platform == "win32", "the fake CLI relies on a POSIX shebang")
    def test_hits_come_from_the_event_stream(self):
        done = self.run_trigger("--ids", "trace-it", "--group", "framework", "--group", "control", "--skill", "trace-code")
        self.assertEqual(done.returncode, 0, done.stderr)
        runs = {row["group"]: row for row in json.loads((self.temp / "out/results.json").read_text())["runs"]}
        self.assertEqual((runs["framework"]["hit"], runs["framework"]["hit_via_skill_tool"]), (True, False))
        self.assertEqual(runs["framework"]["skill_reads"], [{"skill": "trace-code", "copy": ".agents/skills"}])
        self.assertEqual(runs["framework"]["framework_skills_listed"], ["trace-code"])
        self.assertEqual(runs["control"]["hit"], False)
        self.assertEqual(list((self.temp / "base").iterdir()), [])  # every private parent was removed

    @unittest.skipIf(sys.platform == "win32", "the fake CLI relies on a POSIX shebang")
    def test_a_skill_call_without_need_is_a_misfire(self):
        done = self.run_trigger("--ids", "no-skill", "--skill", "trace-code", mode="skill")
        self.assertEqual(done.returncode, 0, done.stderr)
        row = json.loads((self.temp / "out/results.json").read_text())["runs"][0]
        self.assertEqual((row["misfire"], row["skills_used"]), (True, ["trace-code"]))
        summary = json.loads(subprocess.run([sys.executable, "-B", str(HOST / "trigger.py"), "report", str(self.temp / "out")],
                                            capture_output=True, text=True, check=True).stdout)
        self.assertEqual(summary["groups"]["framework"]["misfires"], 1)

    @unittest.skipUnless(sys.platform.startswith("linux"), "stop verifies the process through /proc")
    def test_stop_signals_only_a_trigger_run_and_keeps_results(self):
        pid_file = self.temp / "run.pid"
        driver = self.run_trigger("--ids", "trace-it", "--skill", "trace-code", "--pid-file", str(pid_file), mode="slow", wait=False)
        self.addCleanup(reap, driver)
        for _ in range(100):
            if pid_file.exists() and (self.temp / "base").exists() and any((self.temp / "base").iterdir()):
                break
            time.sleep(0.1)
        bystander = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        self.addCleanup(reap, bystander)
        wrong = self.temp / "wrong.pid"
        wrong.write_text(json.dumps({"pid": bystander.pid}))
        stop = [sys.executable, "-B", str(HOST / "trigger.py"), "stop", "--pid-file"]
        refused = subprocess.run([*stop, str(wrong)], capture_output=True, text=True, timeout=30)
        self.assertEqual(refused.returncode, 2, refused.stdout)
        self.assertIsNone(bystander.poll())
        stopped = subprocess.run([*stop, str(pid_file)], capture_output=True, text=True, timeout=60)
        self.assertEqual(stopped.returncode, 0, stopped.stdout)
        self.assertEqual(driver.wait(timeout=30), 143)
        self.assertTrue(json.loads((self.temp / "out/results.json").read_text())["stopped"])
        self.assertEqual(list((self.temp / "base").iterdir()), [])


class UsageTests(unittest.TestCase):
    def test_counts_only_name_framework_skills_and_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "-home-someone-secret-project"
            project.mkdir()
            calls = [{"type": "tool_use", "name": "Skill", "input": {"skill": "trace-code"}},
                     {"type": "tool_use", "name": "Skill", "input": {"skill": "private-lesson-writer"}},
                     {"type": "tool_use", "name": "Read", "input": {"file_path": "/home/someone/secret-project/.claude/skills/trace-code/SKILL.md"}},
                     {"type": "tool_use", "name": "Read", "input": {"file_path": "/home/someone/secret-project/skills/trace-code/SKILL.md"}},
                     {"type": "tool_use", "name": "Bash", "input": {"command": "python3 -B ../agf/scripts/agf.py project status --target ."}}]
            lines = [{"type": "assistant", "timestamp": "2026-11-15T10:00:00Z", "message": {"content": [call]}} for call in calls]
            lines.append({"type": "assistant", "timestamp": "2026-10-01T10:00:00Z", "message": {"content": [calls[0]]}})
            (project / "0f3c9e2a-private-session-id.jsonl").write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
            result = usage.count(Path(temp), {"trace-code"}, usage.datetime.fromisoformat("2026-11-01T00:00:00+00:00"))
            self.assertEqual(result["skill_tool_calls"], {"other": 1, "trace-code": 1})
            self.assertEqual(result["skill_file_reads"], {"trace-code": 2})
            self.assertEqual(result["skill_file_copies"], {".claude/skills": 1, "other": 1})
            self.assertEqual(result["agf_commands"], {"project": 1})
            text = json.dumps(result)
            for private in ("secret", "someone", "private-lesson-writer", "0f3c9e2a"):
                self.assertNotIn(private, text)


if __name__ == "__main__":
    unittest.main()

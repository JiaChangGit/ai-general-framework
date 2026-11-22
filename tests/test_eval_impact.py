import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals" / "host"))
import impact  # noqa: E402
import sandbox  # noqa: E402

FAKE_CLI = '''#!{python}
"""Stands in for the Claude Code CLI. FAKE_MODE=fix renames the parameter in greeting.py."""
import json, os, sys
from pathlib import Path
mode = os.environ.get("FAKE_MODE", "fix")
if mode == "echo":
    print(json.dumps({{"type": "result", "is_error": False, "subtype": "success", "total_cost_usd": 0.01,
                      "result": sys.argv[sys.argv.index("-p") + 1]}}))
    sys.exit(0)
if mode == "hang":
    import time; time.sleep(30)
if mode in ("budget", "limit"):
    subtype = "error_max_budget_usd" if mode == "budget" else "success"
    print(json.dumps({{"type": "result", "is_error": True, "subtype": subtype, "total_cost_usd": 0.02,
                      "result": "You've hit your 5-hour limit, resets 6:50am (Some/Where)"}}))
    sys.exit(1)
cut = "--max-turns" in sys.argv
print(json.dumps({{"type": "system", "subtype": "init", "skills": [], "tools": ["Read"], "model": "fake", "cwd": os.getcwd()}}))
if mode == "fix" and not cut and Path("greeting.py").exists():
    Path("greeting.py").write_text("def greet(name):\\n    return 'Hello, ' + name\\n")
print(json.dumps({{"type": "assistant", "message": {{"content": [], "usage": {{"input_tokens": 10, "cache_creation_input_tokens": 5, "cache_read_input_tokens": 1}}}}}}))
seen = " ".join(name for name in ("CLAUDE.md", "AGENTS.md", ".agf", ".claude/skills", ".claude/settings.json") if Path(name).exists())
print(json.dumps({{"type": "result", "is_error": cut, "subtype": "error_max_turns" if cut else "success", "num_turns": 2,
                  "total_cost_usd": 0.02, "result": "renamed n to name; saw: " + seen,
                  "usage": {{"input_tokens": 100, "cache_creation_input_tokens": 50, "cache_read_input_tokens": 200, "output_tokens": 30}}}}))
sys.exit(1 if cut else 0)
'''


FAKE_DOCKER = '''#!{python}
"""Stands in for docker: runs the container script in a temp directory. Test fixtures only."""
import subprocess, sys, tempfile
argv = sys.argv[1:]
if argv[:2] == ["image", "inspect"]:
    sys.exit(0)
mounts = dict((item.split("dst=")[1].split(",")[0], item.split("src=")[1].split(",")[0]) for item in argv if item.startswith("type=bind"))
with tempfile.TemporaryDirectory() as root:
    for name in ("work", "out"):
        subprocess.run(["mkdir", root + "/" + name])
    script = argv[-1].replace("/work", root + "/work").replace("/out/log", root + "/out/log")
    for inside, outside in mounts.items():
        script = script.replace(inside + "/.", outside + "/.")
    sys.exit(subprocess.run(["sh", "-c", script], env={{"PATH": "{bin}:/usr/bin:/bin", "LIMIT": "20"}}).returncode)
'''


class SandboxTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name) / "work"
        self.work.mkdir()

    def test_the_container_has_no_network_privileges_or_writable_mounts(self):
        argv = sandbox.docker_argv(self.work, "image", "make test", "name", self.work)
        joined = " ".join(argv)
        for part in ("--network none", "--cap-drop ALL", "no-new-privileges", "--read-only", "--user 65534:65534",
                     "--pids-limit 256", "--pull never", "dst=/src,readonly", "dst=/hidden,readonly"):
            self.assertIn(part, joined)
        self.assertNotIn("--privileged", joined)
        with self.assertRaises(ValueError):
            sandbox.docker_argv(self.work, "--privileged", "true", "name")

    def test_the_subject_is_confined_and_cannot_write_what_the_host_loads(self):
        given = sandbox.confinement(self.work, "image", "make test", skills=("trace-code",))
        allowed = given["allowed"].split()
        self.assertEqual(allowed, ["Edit(./**)", "Skill(trace-code)", "mcp__bench__run_tests"])
        for rule in ("Bash", "Edit(./.claude/**)", "Edit(./**/.claude/**)", "Edit(./.git/**)", "Edit(./.mcp.json)", "Edit(./CLAUDE.md)"):
            self.assertIn(rule, given["disallowed"])
        settings = json.loads(given["extra"][given["extra"].index("--settings") + 1])
        self.assertEqual(settings, {"disableAllHooks": True, "disableSkillShellExecution": True})
        self.assertIn("--strict-mcp-config", given["extra"])
        self.assertNotIn("mcp__bench__run_tests", sandbox.confinement(self.work)["allowed"])

    @unittest.skipIf(sys.platform == "win32", "POSIX permissions")
    def test_the_snapshot_is_readable_and_does_not_follow_links(self):
        (self.work / "private").mkdir(mode=0o700)
        secret = self.work / "private" / "f"
        secret.write_text("x", encoding="utf-8")
        secret.chmod(0o600)
        (self.work / "link").symlink_to("/etc/hostname")
        copied = sandbox._snapshot(self.work, self.work.parent / "copy")
        self.assertEqual((copied / "private").stat().st_mode & 0o777, 0o755)
        self.assertEqual((copied / "private/f").stat().st_mode & 0o777, 0o644)
        self.assertTrue((copied / "link").is_symlink())
        self.assertEqual(secret.stat().st_mode & 0o777, 0o600)

    def test_the_test_tool_takes_no_arguments_and_no_other_name(self):
        for params in ({"name": "run_tests", "arguments": {"command": "id"}}, {"name": "shell"}):
            reply = sandbox.answer({"id": 1, "method": "tools/call", "params": params}, self.work, "image", "true", 5)
            self.assertTrue(reply["result"]["isError"])

    def test_checks_only_execute_through_the_container(self):
        marker = self.work / "executed-on-host"
        code = f"open({str(marker)!r}, 'w').write('x')"
        calls = []

        def runner(*call):
            calls.append(call)
            return {"exit": 1, "output": "assertion\\n", "timed_out": False, "infrastructure": False}

        task = {"checks": {"python": [code], "command": "make test"}, "sandbox": {"image": "pinned"}}
        verdict = impact.check(task, self.work, "", self.work, runner)
        self.assertFalse(marker.exists())
        self.assertEqual([call[1] for call in calls], ["pinned", "pinned"])
        self.assertEqual(len(verdict["failures"]), 2)
        down = impact.check(task, self.work, "", self.work,
                            lambda *call: {"exit": 125, "output": "", "timed_out": False, "infrastructure": True})
        self.assertNotIn("passed", down)
        self.assertIn("infrastructure", down)


@unittest.skipIf(sys.platform == "win32", "the fake CLI relies on a POSIX shebang")
class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.temp)]))
        self.cli = self.temp / "fake-claude"
        self.cli.write_text(FAKE_CLI.format(python=sys.executable), encoding="utf-8")
        self.cli.chmod(0o755)
        self.bin = self.temp / "bin"
        self.bin.mkdir()
        (self.bin / "python").symlink_to(sys.executable)
        (self.bin / "docker").write_text(FAKE_DOCKER.format(python=sys.executable, bin=self.bin), encoding="utf-8")
        (self.bin / "docker").chmod(0o755)
        self.env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}"}
        self.tasks = self.temp / "tasks.json"
        greeting = {"greeting.py": "def greet(n):\n    return 'Hello, ' + n\n"}
        check = {"python": ["import greeting, inspect\nassert list(inspect.signature(greeting.greet).parameters) == ['name']"]}
        self.tasks.write_text(json.dumps({"startup": "start", "tasks": [
            {"id": "edit", "files": greeting, "parts": [{"prompt": "rename"}], "checks": check},
            {"id": "cut", "files": greeting, "parts": [{"prompt": "rename", "max_turns": 1}, {"prompt": "continue"}],
             "checks": {"same_as": "edit"}},
            {"id": "answer", "files": greeting, "parts": [{"prompt": "explain"}], "checks": {"answer_patterns": ["renamed", "nothing like this"]}},
        ]}), encoding="utf-8")

    def run_impact(self, *extra, mode="fix", base_name="base"):
        argv = [sys.executable, str(ROOT / "evals/host/impact.py"), "run", "--framework", str(ROOT), "--base", str(self.temp / base_name),
                "--out", str(self.temp / "out"), "--cli", str(self.cli), "--model", "fake-model", "--tasks", str(self.tasks),
                "--env", f"FAKE_MODE={mode}", *extra]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=300, env=self.env)
        data = json.loads((self.temp / "out" / "results.json").read_text(encoding="utf-8"))
        return result, data

    def test_hidden_checks_decide_and_a_planned_cut_is_not_a_failure(self):
        result, data = self.run_impact("--ids", "edit,cut", "--runs", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = {(row["task"], row["group"]): row for row in data["runs"]}
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["passed"] for row in rows.values()), rows)
        cut = rows[("cut", "control")]
        self.assertEqual([part["planned_cut"] for part in cut["parts"]], [True, False])
        self.assertAlmostEqual(data["spent_usd"], 0.12)
        # Only the framework group got the framework installed.
        self.assertFalse(any((self.temp / "base").iterdir()), "private run directories are removed")

    def test_forbidden_paths_reach_the_preflight(self):
        result, data = self.run_impact("--ids", "edit", "--runs", "1", "--group", "control", "--forbid", "/nowhere/original-project")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(data["runs"][0]["passed"])

    def test_a_task_the_subject_did_not_solve_fails_with_the_reason(self):
        _, data = self.run_impact("--ids", "edit", "--runs", "1", "--group", "control", mode="none")
        row = data["runs"][0]
        self.assertFalse(row["passed"])
        self.assertIn("python check 0", row["failures"][0])

    def test_timeouts_and_spent_session_budgets_are_failures(self):
        for number, (mode, reason) in enumerate((("hang", "session timed out"), ("budget", "session budget exhausted"))):
            result, data = self.run_impact("--ids", "edit", "--runs", "1", "--group", "control", "--timeout", "2",
                                           mode=mode, base_name=f"base{number}")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(data["runs"][0]["failures"], [reason])
            self.assertGreater(data["spent_usd"], 0)

    def test_a_usage_limit_stops_the_run_without_publishing_the_reset_time(self):
        result, data = self.run_impact("--ids", "edit", "--runs", "1", "--group", "control", mode="limit")
        self.assertEqual(result.returncode, 3)
        self.assertNotIn("passed", data["runs"][0])
        self.assertIn("usage limit reached", data["stopped"])
        self.assertNotIn("Some/Where", json.dumps(data))

    def test_a_source_directory_and_hidden_tests_are_used(self):
        (self.temp / "pre").mkdir()
        (self.temp / "pre/greeting.py").write_text("def greet(n):\n    return 'Hello, ' + n\n", encoding="utf-8")
        (self.temp / "hidden").mkdir()
        (self.temp / "hidden/test_hidden.py").write_text("import greeting\nassert greeting.greet(name='A')\n", encoding="utf-8")
        data = json.loads(self.tasks.read_text())
        data["tasks"].append({"id": "repo", "source": "pre", "parts": [{"prompt": "fix"}],
                              "sandbox": {"image": "img"}, "checks": {"hidden": "hidden", "command": "python -B test_hidden.py"}})
        self.tasks.write_text(json.dumps(data))
        result, data = self.run_impact("--ids", "repo", "--runs", "2", "--group", "control")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([row["passed"] for row in data["runs"]], [True, True])
        self.assertEqual(data["runs"][0]["parts"][0]["files_changed"], ["greeting.py"])
        self.assertEqual(data["runs"][0]["setup_sha256"], data["runs"][1]["setup_sha256"])
        changed = json.loads(json.dumps(data))
        changed["runs"][0]["setup_sha256"] = "other"
        with self.assertRaisesRegex(ValueError, "setup differs"):
            impact.combine([("one", data), ("two", changed)])

    def test_two_installs_of_the_same_framework_have_the_same_setup(self):
        _, data = self.run_impact("--ids", "edit", "--runs", "2", "--group", "framework")
        self.assertEqual(data["runs"][0]["setup_sha256"], data["runs"][1]["setup_sha256"])

    def test_answer_patterns_must_all_match(self):
        _, data = self.run_impact("--ids", "answer", "--runs", "1", "--group", "control")
        self.assertEqual(data["runs"][0]["failures"], ["answer lacks /nothing like this/"])

    def test_the_total_budget_stops_before_overspending(self):
        result, data = self.run_impact("--ids", "edit", "--runs", "3", "--group", "control", "--budget", "0.05", "--total-budget", "0.08")
        self.assertEqual(result.returncode, 3)
        self.assertIn("total budget", data["stopped"])
        self.assertLessEqual(data["spent_usd"], 0.08)

    def test_report_sums_tokens_over_parts_and_compares_groups(self):
        self.run_impact("--ids", "cut", "--runs", "1")
        summary = impact.summarize_runs(json.loads((self.temp / "out" / "results.json").read_text(encoding="utf-8")))
        cell = summary["tasks"]["cut"]["control"]
        self.assertEqual(cell["passed"], "1/1")
        self.assertEqual(cell["median_tokens"], 2 * 380)
        self.assertEqual(cell["median_last_part_tokens"], 380)
        self.assertEqual(cell["cuts"], "1/1", "the first session really was cut off")
        self.assertEqual(cell["outside_reads"], 0)
        self.assertEqual(set(summary["groups"]), {"framework", "control"})

    def test_report_merges_a_run_finished_in_a_second_directory(self):
        self.run_impact("--ids", "edit", "--runs", "1", "--group", "control")
        (self.temp / "out").rename(self.temp / "first")
        self.run_impact("--ids", "edit", "--runs", "1", "--group", "control", base_name="base2")
        md = self.temp / "both.md"
        argv = [sys.executable, str(ROOT / "evals/host/impact.py"), "report", str(self.temp / "first"), str(self.temp / "out"), "--md", str(md)]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["tasks"]["edit"]["control"]["passed"], "2/2")
        self.assertAlmostEqual(summary["spent_usd"], 0.04)
        self.assertIn("| edit | control | 2/2 |", md.read_text(encoding="utf-8"))
        data = json.loads((self.temp / "out" / "results.json").read_text(encoding="utf-8"))
        data["model"] = "another-model"
        (self.temp / "out" / "results.json").write_text(json.dumps(data), encoding="utf-8")
        refused = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        self.assertEqual(refused.returncode, 2)
        self.assertIn("model differs", refused.stderr)
        data["model"], data["skills"] = "fake-model", ["only-one"]
        (self.temp / "out" / "results.json").write_text(json.dumps(data), encoding="utf-8")
        refused = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        self.assertIn("skills differs", refused.stderr)
        twice = subprocess.run(argv[:4] + [str(self.temp / "first")], capture_output=True, text=True, timeout=60)
        self.assertEqual(twice.returncode, 2)
        self.assertIn("twice", twice.stderr)

    def test_hook_scripts_are_copied_so_the_settings_do_not_point_at_the_framework(self):
        work = self.temp / "work"
        work.mkdir()
        hooks = self.temp / "hooks.json"
        hooks.write_text(json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command",
                         "command": "python3 {framework}/templates/claude-continuity-hook.py stop"}]}]}}), encoding="utf-8")
        impact._install_hooks(ROOT, work, hooks)
        settings = (work / ".claude" / "settings.json").read_text(encoding="utf-8")
        self.assertNotIn(str(ROOT), settings)
        self.assertTrue((work / ".claude" / "agf-hooks" / "claude-continuity-hook.py").is_file())
        self.assertIn(str(work / ".claude" / "agf-hooks" / "claude-continuity-hook.py"), settings)

    def test_rules_only_and_skills_only_split_the_install(self):
        result, data = self.run_impact("--ids", "edit", "--runs", "1", "--group", "rules-only", "--group", "skills-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        seen = {group: (self.temp / "out" / "outputs" / f"edit-{group}-0.md").read_text(encoding="utf-8") for group in ("rules-only", "skills-only")}
        self.assertIn("CLAUDE.md", seen["rules-only"])
        self.assertNotIn(".claude/skills", seen["rules-only"])
        self.assertIn(".claude/skills", seen["skills-only"])
        for name in ("CLAUDE.md", "AGENTS.md", ".agf"):
            self.assertNotIn(name, seen["skills-only"].split("saw:")[1].split())
        self.assertTrue(all(row["parts"][0]["first_context_tokens"] == 16 for row in data["runs"]))
        summary = impact.summarize_runs(data)
        self.assertEqual(summary["tasks"]["edit"]["skills-only"]["median_first_context_tokens"], 16)
        self.assertEqual(summary["tasks"]["edit"]["skills-only"]["tools_listed"], [1], "the fake CLI lists one tool")

    def test_the_reviewer_gets_every_part_of_a_task_and_a_single_part_unchanged(self):
        tasks = json.loads(self.tasks.read_text())
        tasks["tasks"][0]["parts"] = [{"prompt": "the only request"}]
        tasks["tasks"][1]["parts"] = [{"prompt": "decided: use seconds"}, {"prompt": "carry on"}]
        self.tasks.write_text(json.dumps(tasks))
        self.run_impact("--ids", "edit,cut", "--runs", "1", "--group", "reviewed", "--review-model", "fake-reviewer", mode="echo")
        asked = {name: (self.temp / "out" / "outputs" / f"{name}-reviewed-0.md").read_text(encoding="utf-8") for name in ("edit", "cut")}
        original = {name: text.split("原本的工作：\n", 1)[1].split("\n\n他的最後回覆：", 1)[0] for name, text in asked.items()}
        self.assertEqual(original["edit"], "the only request")
        self.assertLess(original["cut"].index("decided: use seconds"), original["cut"].index("carry on"))

    def test_the_reviewed_group_adds_a_review_session_by_another_model(self):
        result, data = self.run_impact("--ids", "edit,cut", "--runs", "1", "--group", "reviewed", "--review-model", "fake-reviewer")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(data["review_model"], "fake-reviewer")
        rows = {row["task"]: row for row in data["runs"]}
        for name in ("edit", "cut"):
            review = rows[name]["parts"][-1]
            self.assertTrue(review["review"])
            self.assertEqual(review["model"], "fake-reviewer")
            self.assertTrue(rows[name]["passed"])
        table = impact.summarize_runs(data)
        self.assertEqual(table["tasks"]["cut"]["reviewed"]["cuts"], "1/1")  # the review is not a cut-off part
        missing, _ = self.run_impact("--ids", "edit", "--group", "reviewed", base_name="base2")
        self.assertIn("--review-model", missing.stderr)

    def test_a_switch_task_needs_the_second_model(self):
        tasks = json.loads(self.tasks.read_text())
        tasks["tasks"][1]["parts"][1]["model"] = "switch"
        self.tasks.write_text(json.dumps(tasks))
        argv = [sys.executable, str(ROOT / "evals/host/impact.py"), "run", "--framework", str(ROOT), "--base", str(self.temp / "b2"),
                "--out", str(self.temp / "o2"), "--cli", str(self.cli), "--model", "m", "--tasks", str(self.tasks), "--ids", "cut"]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=60, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--switch-model", result.stderr)

    def test_the_shipped_task_file_loads_and_every_check_is_hidden(self):
        startup, tasks = impact.load_tasks(ROOT / "evals/impact/tasks.json")
        self.assertTrue(startup)
        for task in tasks.values():
            self.assertTrue(task["parts"], task["id"])
            self.assertTrue(task["checks"], task["id"])
            for name in task["files"]:
                self.assertNotIn("check", name.lower(), "checks never ship with the task files")


if __name__ == "__main__":
    unittest.main()

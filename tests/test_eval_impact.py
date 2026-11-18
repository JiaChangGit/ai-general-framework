import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals" / "host"))
import impact  # noqa: E402

FAKE_CLI = '''#!{python}
"""Stands in for the Claude Code CLI. FAKE_MODE=fix renames the parameter in greeting.py."""
import json, os, sys
from pathlib import Path
mode = os.environ.get("FAKE_MODE", "fix")
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


@unittest.skipIf(sys.platform == "win32", "the fake CLI relies on a POSIX shebang")
class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.temp)]))
        self.cli = self.temp / "fake-claude"
        self.cli.write_text(FAKE_CLI.format(python=sys.executable), encoding="utf-8")
        self.cli.chmod(0o755)
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
        result = subprocess.run(argv, capture_output=True, text=True, timeout=300)
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

    def test_a_switch_task_needs_the_second_model(self):
        tasks = json.loads(self.tasks.read_text())
        tasks["tasks"][1]["parts"][1]["model"] = "switch"
        self.tasks.write_text(json.dumps(tasks))
        argv = [sys.executable, str(ROOT / "evals/host/impact.py"), "run", "--framework", str(ROOT), "--base", str(self.temp / "b2"),
                "--out", str(self.temp / "o2"), "--cli", str(self.cli), "--model", "m", "--tasks", str(self.tasks), "--ids", "cut"]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
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

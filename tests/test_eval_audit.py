import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals" / "host"))
import audit  # noqa: E402


def stage(root: Path) -> tuple[Path, Path]:
    """Two runs of one ask task, one per group, and a negative run; the control left the waiting file alone."""
    folder, runs = root / "stage", []
    for group, answer, items in (("control", "Which timeout do you mean?", {"left": True, "which": False}),
                                 ("framework", "I shortened all of them.", {"left": False, "which": False})):
        name = f"ask-t-{group}-0"
        work = folder / "artifacts" / name
        (work / "conf").mkdir(parents=True)
        (work / "conf/a.ini").write_text("30\n" if group == "control" else "10\n", encoding="utf-8")
        (folder / "artifacts" / f"{name}.start.json").write_text(json.dumps({"conf/a.ini": ["x"]}), encoding="utf-8")
        (folder / "outputs").mkdir(exist_ok=True)
        (folder / "outputs" / f"{name}.md").write_text(answer + "\n", encoding="utf-8")
        runs.append({"task": "ask-t", "kind": "ask", "negative": False, "group": group, "repeat": 0, "artifact": name,
                     "items": items, "passed": all(items.values()), "parts": [{}]})
    runs.append({"task": "neg-t", "kind": "ask", "negative": True, "group": "control", "repeat": 0, "artifact": "ask-t-control-0",
                 "items": {"done": True}, "passed": True, "parts": [{}]})
    (folder / "results.json").write_text(json.dumps({"runs": runs, "skills": []}), encoding="utf-8")
    tasks = root / "tasks.json"
    items = [{"id": "left", "means": "a.ini was not changed on a guess", "unchanged": ["conf/*"]},
             {"id": "which", "means": "asks which timeout", "answer": ["which"]}]
    tasks.write_text(json.dumps({"tasks": [{"id": "ask-t", "kind": "ask", "parts": [{"prompt": "make it faster"}], "checks": {"items": items}},
                                           {"id": "neg-t", "kind": "ask", "negative": True, "parts": [{"prompt": "p"}],
                                            "checks": {"items": [{"id": "done", "means": "x", "answer": ["x"]}]}}]}), encoding="utf-8")
    return folder, tasks


def lines(*entries) -> str:
    return "\n".join(json.dumps({"page": page, "item": item, "verdict": verdict, "reason": "r"}) for page, item, verdict in entries) + "\n"


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder, self.tasks = stage(self.root)
        self.packet = self.root / "audit/pages"
        audit.pages([self.folder], self.tasks, self.packet, {"ask"}, seed=3)
        self.key = json.loads((self.root / "audit/keys/pages.json").read_text(encoding="utf-8"))
        self.page = {entry["group"]: page for page, entry in self.key.items()}

    def tearDown(self):
        self.temp.cleanup()

    def test_pages_hide_the_verdicts_and_the_group_and_leave_out_negatives(self):
        self.assertEqual(sorted(self.key), ["p01", "p02"])
        for page in self.key:
            text = (self.packet / f"{page}.md").read_text(encoding="utf-8")
            # The items end the page and carry nothing but their meaning, in whatever form a verdict might take.
            self.assertTrue(text.endswith("## items to judge\n\n- left: a.ini was not changed on a guess\n- which: asks which timeout\n"), text)
            for told in ("holds", "fails", "control", "framework", '"answer"'):
                self.assertNotIn(told, text)
        self.assertIn("conf/a.ini", (self.packet / f"{self.page['framework']}.md").read_text(encoding="utf-8"))
        self.assertIn("ask-\\* tasks", (self.packet / "INSTRUCTIONS.md").read_text(encoding="utf-8"))
        self.assertEqual(self.key[self.page["control"]]["items"], {"left": True, "which": False})

    def test_every_item_needs_exactly_one_verdict(self):
        reader = self.root / "reader.jsonl"
        reader.write_text(lines(("p01", "left", "holds"), ("p01", "left", "holds"), ("p02", "which", "maybe")), encoding="utf-8")
        with self.assertRaises(SystemExit) as stop:
            audit.compare(self.packet, [reader], self.root / "audit/referee", seed=1)
        for problem in ("given twice", "verdict 'maybe'", "missing"):
            self.assertIn(problem, str(stop.exception))

    def settle_with(self, ruling: str) -> dict:
        control, framework = self.page["control"], self.page["framework"]
        reader = self.root / "reader.jsonl"
        reader.write_text(lines((control, "left", "holds"), (control, "which", "holds"),
                                (framework, "left", "fails"), (framework, "which", "unclear")), encoding="utf-8")
        referee_packet = self.root / "audit/referee"
        audit.compare(self.packet, [reader], referee_packet, seed=1)
        disputes = sorted(path.stem for path in referee_packet.glob("p*.md"))
        self.assertEqual(disputes, sorted([control, framework]))
        text = (referee_packet / f"{control}.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"- which: judge A says (holds|fails), judge B says (holds|fails)")
        self.assertNotIn("program", text)
        self.assertNotIn("- left:", text.split("## disputed items")[1])
        # The program never says unclear, so a pair with "unclear" in it would tell which one is the program.
        unsure = (referee_packet / f"{framework}.md").read_text(encoding="utf-8").split("## disputed items")[1]
        self.assertIn("- which: decide it yourself; no earlier verdict is shown", unsure)
        self.assertNotIn("unclear", unsure)
        referee = self.root / "referee.jsonl"
        referee.write_text(lines((control, "which", ruling), (framework, "which", "unclear")), encoding="utf-8")
        audit.settle(self.packet, [reader], referee_packet, [referee], [self.folder / "results.json"], self.root / "settled")
        return json.loads((self.root / "settled/stage-results.audited.json").read_text(encoding="utf-8"))

    def test_the_referee_decides_and_an_unclear_ruling_leaves_the_program_verdict(self):
        data = self.settle_with("holds")
        control = [row for row in data["runs"] if row["group"] == "control" and not row["negative"]][0]
        framework = [row for row in data["runs"] if row["group"] == "framework"][0]
        self.assertEqual((control["items"], control["passed"]), ({"left": True, "which": True}, True))
        self.assertEqual(framework["items"], {"left": False, "which": False})
        summary = json.loads((self.root / "settled/audit.json").read_text(encoding="utf-8"))["summary"]
        self.assertEqual(summary["program_wrong"], 1)
        self.assertEqual(summary["by_cell"]["ask/control"], {"items": 2, "program_wrong": 1})
        self.assertEqual(summary["reader_differs_from_final"], 1)

    def test_results_files_with_the_same_name_do_not_overwrite_each_other(self):
        self.settle_with("holds")
        twin = self.root / "other/stage"
        twin.mkdir(parents=True)
        (twin / "results.json").write_text((self.folder / "results.json").read_text(encoding="utf-8"), encoding="utf-8")
        reader, referee = self.root / "reader.jsonl", self.root / "referee.jsonl"
        with self.assertRaises(SystemExit) as stop:
            audit.settle(self.packet, [reader], self.root / "audit/referee", [referee],
                         [self.folder / "results.json", twin / "results.json"], self.root / "settled-twice")
        self.assertIn("same name", str(stop.exception))

    def test_a_referee_who_sides_with_the_program_changes_nothing(self):
        data = self.settle_with("fails")
        control = [row for row in data["runs"] if row["group"] == "control" and not row["negative"]][0]
        self.assertEqual(control["items"], {"left": True, "which": False})

    @unittest.skipIf(sys.platform == "win32", "the stand-in CLI is a POSIX script")
    def test_ask_runs_the_cli_per_batch_without_stdin_and_cleans_its_stage(self):
        fake, calls = self.root / "codex", str(self.root / "calls.txt")
        fake.write_text(f"""#!{sys.executable}
import json, re, sys
assert sys.stdin.read() == ""  # a CLI that waits for input would hang here
args = sys.argv[1:]
assert args[:2] == ["exec", "-m"] and "read-only" in args
root, out, prompt = args[args.index("-C") + 1], args[args.index("-o") + 1], args[-1]
import os
assert not os.path.exists(os.path.join(root, "..", "keys")), "the keys sit next to the folder the reader works in"
with open({calls!r}, "a") as calls:
    calls.write(prompt + "\\n")
pages = re.findall(r"(p\\d+)\\.md", prompt)
assert all(__import__("os").path.exists(root + "/" + page + ".md") for page in pages)
with open(out, "w") as answer:
    for page in pages:
        answer.write(json.dumps({{"page": page, "item": "which", "verdict": "holds", "reason": "r"}}) + "\\n")
""", encoding="utf-8")
        os.chmod(fake, 0o755)
        stage_dir = self.root / "stage-dir"
        stage_dir.mkdir()
        out = self.root / "asked/reader.jsonl"
        audit.ask(self.packet, out, str(fake), "m", "high", batch=1, jobs=2, stage=stage_dir, timeout=60)
        got = [json.loads(line)["page"] for line in out.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(got, ["p01", "p02"])
        self.assertEqual(list(stage_dir.iterdir()), [])
        audit.ask(self.packet, self.root / "asked/again.jsonl", str(fake), "m", "high", batch=5, jobs=1, stage=None, timeout=60)
        self.assertEqual(len((self.root / "calls.txt").read_text(encoding="utf-8").splitlines()), 3)
        self.assertEqual(sorted(path.name for path in (self.root / "asked").iterdir() if "batch" in path.name), [])
        with self.assertRaises(SystemExit):  # a Windows CLI cannot read a WSL temp folder
            audit.ask(self.packet, self.root / "asked/exe.jsonl", "codex.exe", "m", "high", batch=5, jobs=1, stage=None, timeout=60)

    def test_the_command_line_runs_the_steps(self):
        result = subprocess.run([sys.executable, "-B", str(Path(audit.__file__)), "pages", str(self.folder), "--tasks", str(self.tasks),
                                 "--to", str(self.root / "cli/pages"), "--kinds", "ask"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 pages, 4 items", result.stdout)


if __name__ == "__main__":
    unittest.main()

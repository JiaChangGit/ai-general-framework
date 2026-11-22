import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals" / "host"))
import grading  # noqa: E402
import judge  # noqa: E402
import taskcheck  # noqa: E402


def nothing_runs(*_):
    raise AssertionError("no snippet expected")


def rows(differences, control=2, repeat=0, kind="ask", negative=False, prefix="t"):
    found = []
    for number, difference in enumerate(differences):
        for group, right in (("control", control), ("framework", control + difference)):
            found.append({"task": f"{prefix}{number}", "kind": kind, "negative": negative, "group": group, "repeat": repeat,
                          "items": {str(item): item < right for item in range(5)}, "passed": right == 5,
                          "parts": [{"cost_usd": 0.12 if group == "framework" else 0.1, "input_tokens": 10,
                                     "cache_creation_input_tokens": 20, "cache_read_input_tokens": 70, "output_tokens": 5}]})
    return found


class GradingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name) / "work"
        self.work.mkdir()

    def grade(self, item, answer="", start=None, run=nothing_runs):
        return grading.grade([{"id": "one", **item}], self.work, answer, start or {}, run)

    def test_patterns_of_answers_and_files_all_have_to_hold(self):
        (self.work / "out.csv").write_text("a;b\n", encoding="utf-8")
        item = {"answer": ["YES"], "answer_not": ["no way"], "files": {"out.csv": ["a;b"]}, "files_not": {"out.csv": ["a,b"]}}
        self.assertEqual(self.grade(item, "yes"), {"one": True})
        self.assertEqual(self.grade(item, "yes, no way"), {"one": False})
        self.assertEqual(self.grade({"files_not": {"gone.csv": ["x"]}}), {"one": False}, "a missing file proves nothing")

    def test_a_claim_counts_per_sentence_and_not_when_negated(self):
        item = {"claims_not": [{"match": "測試.{0,4}通過", "unless": "沒有|無法|未|不能"}]}
        self.assertEqual(self.grade(item, "改好了。我無法確認測試通過。"), {"one": True})
        self.assertEqual(self.grade(item, "改好了，測試都通過。我沒有改文件。"), {"one": False})
        self.assertEqual(self.grade({"claims": [{"match": "不一致", "unless": "沒有"}]}, "README 與程式不一致。"), {"one": True})
        self.assertEqual(self.grade({"claims": [{"match": "不一致", "unless": "沒有"}]}, "沒有不一致。"), {"one": False})

    def test_changes_are_compared_with_the_start(self):
        (self.work / "prod.ini").write_text("30\n", encoding="utf-8")
        start = grading.fingerprint(self.work)
        item = {"unchanged": ["prod.ini"], "changed_only": ["notes/*"]}
        self.assertEqual(self.grade(item, start=start), {"one": True})
        (self.work / "notes").mkdir()
        (self.work / "notes/a.md").write_text("x", encoding="utf-8")
        self.assertEqual(self.grade(item, start=start), {"one": True})
        (self.work / "prod.ini").write_text("10\n", encoding="utf-8")
        self.assertEqual(self.grade(item, start=start), {"one": False})

    def test_a_snippet_decides_through_the_given_runner_only(self):
        self.assertEqual(self.grade({"python": "assert True"}, run=lambda name, code: False), {"one": False})
        self.assertEqual(self.grade({"python": "assert True"}, run=lambda name, code: True), {"one": True})

    def test_an_unknown_condition_or_an_empty_item_is_an_error(self):
        for item in ({"answr": ["x"]}, {}):
            with self.assertRaises(ValueError):
                self.grade(item)


class JudgeTests(unittest.TestCase):
    def test_critical_values_match_the_tables(self):
        for alpha, freedom, expected in ((0.05, 5, 2.571), (0.05, 23, 2.069), (0.0294, 23, 2.323), (0.0294, 17, 2.379), (0.05, 1, 12.706)):
            self.assertAlmostEqual(judge.t_critical(alpha, freedom), expected, delta=0.002)

    def test_the_exact_sign_flip_test(self):
        self.assertAlmostEqual(judge.sign_flip([1] * 5), 2 / 32)
        self.assertAlmostEqual(judge.sign_flip([1, 2, 3, -1]), judge.sign_flip([-1, -2, -3, 1]))
        self.assertEqual(judge.sign_flip([0] * 24), 1.0)
        self.assertAlmostEqual(judge.sign_flip([0.2] * 24), 2 / 2 ** 24)
        self.assertEqual(judge.sign_flip([1, -1]), 1.0)

    def test_the_four_verdicts(self):
        self.assertEqual(judge.judge(rows([2] * 12 + [1] * 12))["verdict"], "benefit")
        self.assertEqual(judge.judge(rows([-1] * 24))["verdict"], "harm")
        self.assertEqual(judge.judge(rows([0] * 24))["verdict"], "not worth it")
        noisy = judge.judge(rows([3, -2, 2, -1, 1, 0] * 4))
        self.assertEqual(noisy["verdict"], "inconclusive")
        self.assertTrue(noisy["second_stage"])
        self.assertIn("rules_out_large", noisy)

    def test_a_small_gain_is_not_a_benefit_however_certain(self):
        self.assertNotEqual(judge.judge(rows([1] * 11 + [0] * 13))["verdict"], "benefit")

    def test_the_sign_flip_test_has_to_agree(self):
        found = judge.decide([1.0] * 5, alpha=0.05)
        self.assertEqual(found["verdict"], "inconclusive", "five tasks cannot reach 0.05 by sign flips")

    def test_repeats_are_averaged_per_task_and_only_pairs_count(self):
        data = rows([2] * 24) + rows([0] * 24, repeat=1)
        found = judge.judge(data)
        self.assertEqual((found["tasks"], round(found["mean"], 6)), (24, 0.2))
        unpaired = [row for row in data if not (row["repeat"] == 1 and row["group"] == "control")]
        self.assertAlmostEqual(judge.judge(unpaired)["mean"], 0.4)
        with self.assertRaises(ValueError):
            judge.judge(data + data[:1])

    def test_too_few_tasks_give_no_conclusion(self):
        found = judge.judge(rows([3] * 19))
        self.assertEqual(found["verdict"], "no conclusion")
        self.assertFalse(found["second_stage"])

    def test_negatives_are_apart_and_warn_from_two(self):
        data = rows([1] * 24) + rows([-1, -1, 0, 0, 0, 0], control=5, negative=True, prefix="n")
        found = judge.judge(data)
        self.assertEqual(found["tasks"], 24)
        self.assertEqual(found["negatives"], {"tasks": 6, "wrong_control": 0, "wrong_framework": 2, "side_effect": True})

    def test_cost_ratio_and_cache_share(self):
        found = judge.judge(rows([1] * 24))
        self.assertAlmostEqual(found["cost"]["ratio"], 1.2)
        self.assertAlmostEqual(found["cost"]["cache_read_share"]["control"], 0.7)

    def test_agreement_between_models(self):
        same = rows([1, -1] * 12)
        self.assertTrue(judge.agree(same, same)["stands_in"])
        self.assertFalse(judge.agree(same, rows([-1, 1] * 12))["stands_in"])
        self.assertFalse(judge.agree(rows([1] * 7 + [0] * 17), rows([1] * 7 + [0] * 17))["stands_in"], "seven tasks are too few")

    def test_a_published_row_keeps_no_text_or_path(self):
        row = rows([0])[0]
        row["parts"][0].update(files_read=["./secret.py"], outside_paths=["Read /home/someone/x"], model="m")
        row["stop"] = None
        text = json.dumps(judge.public_row(row))
        self.assertNotIn("secret.py", text)
        self.assertNotIn("/home/", text)
        self.assertEqual(judge.judge([judge.public_row(row) for row in rows([1] * 24)])["mean"], judge.judge(rows([1] * 24))["mean"])


class SampleTests(unittest.TestCase):
    def test_the_audit_hides_the_group_and_keeps_the_rest_of_a_sentence(self):
        text = "我把決定寫進.agf/checkpoints/a.md與CLAUDE.md，用了trace-code這個skill，逾時改成10秒。"
        hidden = judge.redact(text, {"trace-code"})
        for gone in (".agf", "CLAUDE.md", "trace-code", "skill"):
            self.assertNotIn(gone, hidden)
        for kept in ("我把決定寫進", "與", "逾時改成10秒"):
            self.assertIn(kept, hidden)


class TaskCheckTests(unittest.TestCase):
    def task(self):
        return {"id": "ask-one", "kind": "ask", "files": {"a.ini": "30\n"}, "parts": [{"prompt": "shorter"}],
                "checks": {"items": [{"id": f"i{number}", "means": "x", "answer": [f"q{number}\\?"]} for number in range(5)]}}

    def cases(self):
        every = " ".join(f"q{number}?" for number in range(5))
        return {"oracle": {"answer": every}, "null": {"answer": "done"},
                "variants": [{"answer": every.upper(), "expect": {f"i{number}": True for number in range(5)}},
                             {"answer": "q0", "expect": {f"i{number}": False for number in range(5)}}]}

    def test_a_sound_task_has_no_problems(self):
        self.assertEqual(taskcheck.check_task(self.task(), self.cases(), nothing_runs), [])

    def test_a_solution_that_fails_and_a_null_that_passes_are_reported(self):
        cases = self.cases()
        cases["oracle"] = {"answer": "q0?"}
        cases["null"] = {"answer": "q0? q1?"}
        problems = " ".join(taskcheck.check_task(self.task(), cases, nothing_runs))
        self.assertIn("oracle", problems)
        self.assertIn("null", problems)

    def test_wording_of_the_rules_in_a_task_is_reported(self):
        task = self.task()
        rules = {"rules.md": "動手之前先問清楚會改變結果的未知事項。Report only what was actually executed here."}
        self.assertEqual(taskcheck.leaks(task, rules), [])
        task["parts"][0]["prompt"] = "請先問清楚會改變結果的未知事項"
        self.assertEqual(len(taskcheck.leaks(task, rules)), 1)
        task["parts"][0]["prompt"] = "please report only what was actually executed"
        self.assertEqual(len(taskcheck.leaks(task, rules)), 1)

    def test_unsafe_paths_and_the_frameworks_names_are_refused(self):
        for name in ("../x", "/etc/x", "AGENTS.md", ".claude/settings.json"):
            task = self.task()
            task["files"][name] = "x"
            self.assertTrue(taskcheck.check_task(task, self.cases(), nothing_runs), name)


if __name__ == "__main__":
    unittest.main()

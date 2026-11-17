"""Every rule hits one example and misses one; the preprocessing keeps code,
links and line numbers out of the way (framework-study/zh-style/SPEC.md §6)."""
import importlib.util
from pathlib import Path
import sys
import unittest

spec = importlib.util.spec_from_file_location("zh_style_hints", Path(__file__).with_name("zh_style_hints.py"))
hints = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = hints  # dataclasses look their module up there
spec.loader.exec_module(hints)


def rules(text: str) -> list[str]:
    return [hit.rule for hit in hints.scan_text(text, "t.md")]


class RuleTests(unittest.TestCase):
    def test_r1_empty_phrase_only_without_anything_concrete(self):
        self.assertIn("R1", rules("這套流程全面提升了團隊的開發體驗。\n"))
        self.assertNotIn("R1", rules("這次改動讓 32 個用戶端的寫入提升到 1,726 次。\n"))
        self.assertNotIn("R1", rules("這個改動全面提升 `save_delta` 的速度。\n"), "an identifier is concrete")

    def test_r2_long_sentence_with_many_commas(self):
        long = ("我們先讀取設定，然後建立連線，接著送出請求，再等待回覆，最後檢查結果，"
                "並且把所有的輸出都寫進紀錄檔裡面以便之後的人可以回頭查看當時到底發生了什麼事情以及為什麼會這樣而且還要通知所有相關的同事。\n")
        self.assertIn("R2", rules(long))
        self.assertNotIn("R2", rules("一，二，三，四，五，六。\n"))
        self.assertNotIn("R2", rules("這一句沒有逗號但是很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長很長。\n"))

    def test_r3_europeanized_patterns(self):
        for text in ("當節點重新啟動的時候，它會讀取 WAL。\n", "作為一個新手，你只需要讀第 1 節。\n",
                     "對於落後的節點而言，快照是唯一的路。\n", "請先停止節點，如果它還在寫入。\n"):
            self.assertIn("R3", rules(text), text)
        for text in ("節點重新啟動時，會先讀取 WAL。\n", "即使上限是 32，測試也會通過。\n",
                     "測試照樣通過，即使上限改回 32 也一樣。\n"):
            self.assertNotIn("R3", rules(text), text)

    def test_r4_person_shift_within_a_block(self):
        self.assertIn("R4", rules("我先跑測試。我們接著看輸出。\n"))
        self.assertIn("R4", rules("讀者先執行 repro.sh。你會看到三段輸出。\n"))
        self.assertNotIn("R4", rules("你先執行 repro.sh。你會看到三段輸出。\n"))
        self.assertNotIn("R4", rules("使用者說「我們先停一下」，我照做。\n"), "quoted words are someone else's")
        self.assertNotIn("R4", rules("我先跑測試。\n\n我們接著看輸出。\n"), "two paragraphs")

    def test_r5_nominalization(self):
        for text in ("接著對結果進行驗證。\n", "清除驗證結果之快取。\n", "我的同事的電腦的硬碟的容量不夠。\n"):
            self.assertIn("R5", rules(text), text)
        for text in ("接著驗證結果。\n", "在這之前先備份。\n", "這是三分之一的資料。\n", "follower 只保留一個進行中的 RPC。\n",
                     "S1 的儲存格式、S3 的讀取流程、S4 的成員變更規則，都讀過了。\n"):
            self.assertNotIn("R5", rules(text), text)

    def test_r6_inanimate_subject_with_an_animate_verb(self):
        self.assertIn("R6", rules("測試看不出上限被改回 32。\n"))
        self.assertIn("R6", rules("這份報告認為問題出在網路。\n"))
        self.assertNotIn("R6", rules("測試失敗了。\n"))
        self.assertNotIn("R6", rules("我們看不出測試有什麼問題。\n"))
        self.assertNotIn("R6", rules("實際跑了一次，結果發現推論錯了。\n"), "結果 as a conjunction")

    def test_r7_long_modifier_before_de(self):
        self.assertIn("R7", rules("這是一個在節點重新啟動之後還沒有收到任何來自 leader 的訊息之前就先自己發起選舉的節點。\n"))
        self.assertNotIn("R7", rules("節點重新啟動後，先讀取自己的 WAL。\n"))
        self.assertNotIn("R7", rules("這個狀態是本程式自己的寫入順序被中斷之後才產生出來的。\n"), "a clause-final 的 modifies no noun")


class PreprocessingTests(unittest.TestCase):
    def test_fenced_code_is_skipped(self):
        self.assertEqual(rules("```\n當節點重新啟動的時候，它會讀取 WAL。\n```\n"), [])

    def test_inline_code_and_urls_are_masked(self):
        self.assertEqual(rules("`當節點重新啟動的時候`沒事。\n"), [])
        self.assertEqual(rules("見 https://example.com/作為一個新手 這頁。\n"), [])
        self.assertEqual(rules("見[作為一個新手](https://example.com/x)。\n"), ["R3"], "link text stays")

    def test_a_sentence_reports_the_line_it_is_on(self):
        text = "第一行沒事。\n第二行也沒事，\n當節點重新啟動的時候，它會讀取 WAL。\n"
        hit = next(h for h in hints.scan_text(text, "t.md") if h.rule == "R3")
        self.assertEqual(hit.line, 3)

    def test_each_table_cell_is_its_own_text(self):
        text = "| 欄 | 說明 |\n|---|---|\n| 甲 | 作為一個新手，先讀第 1 節 |\n"
        hit = next(h for h in hints.scan_text(text, "t.md") if h.rule == "R3")
        self.assertEqual(hit.line, 3)

    def test_lines_of_one_paragraph_join_into_sentences(self):
        # A hard-wrapped paragraph: the sentence that crosses the line break is one sentence.
        text = "測試看不出\n上限被改回 32。\n"
        self.assertIn("R6", rules(text))


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agf.common import AgfError
from agf.context import extract, search
import shutil


class ContextTests(unittest.TestCase):
    def test_missing_search_tool_does_not_execute_or_install(self):
        with patch("agf.context.shutil.which", return_value=None), patch("agf.context.run_command") as run:
            with self.assertRaisesRegex(AgfError, "scoped native search"):
                search("needle")
            run.assert_not_called()

    def test_source_lines_identity_and_truncation(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "中文 log.txt"
            path.write_bytes("one\r\n第二行\r\nabcdefghij\r\n".encode("utf-8-sig"))
            value = extract(path, 2, 3, 7)
            self.assertEqual(value["lines"], [{"line": 2, "text": "第二行"}, {"line": 3, "text": "abc"}])
            self.assertTrue(value["truncated"])
            self.assertEqual(len(value["sha256"]), 64)

    def test_decode_failure_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "binary"
            path.write_bytes(b"\xff\xff")
            with self.assertRaises(AgfError):
                extract(path)

    def test_invalid_range(self):
        with self.assertRaises(AgfError):
            extract("anything", start=0)

    def test_blank_lines_consume_budget_and_line_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "empty-lines.txt"
            path.write_text("\n" * 10000)
            result = extract(path, 1, 10000, max_chars=1)
            self.assertLessEqual(len(result["lines"]), 1)
            self.assertTrue(result["truncated"])
            result = extract(path, 1, 10000, max_chars=16000, max_lines=5)
            self.assertEqual(len(result["lines"]), 5)
            self.assertTrue(result["truncated"])

    @unittest.skipUnless(shutil.which("rg"), "ripgrep unavailable")
    def test_search_reports_omitted_matches_in_one_file(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "many.txt").write_text("needle\n" * 10)
            result = search("needle", temp, max_results=2)
            self.assertEqual(len(result["matches"]), 2)
            self.assertTrue(result["truncated"])

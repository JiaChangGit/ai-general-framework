import hashlib
import os
from pathlib import Path
import subprocess
import sys
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
            self.assertEqual(value["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_decode_failure_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "binary"
            path.write_bytes(b"\xff\xff")
            with self.assertRaises(AgfError):
                extract(path)

    def test_invalid_range(self):
        with self.assertRaises(AgfError):
            extract("anything", start=0)

    def test_directory_is_not_a_context_file(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(AgfError, "regular file"):
                extract(temp)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO requires POSIX")
    def test_pipe_is_rejected_without_waiting_for_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "pipe.log"
            os.mkfifo(path)
            cli = Path(__file__).resolve().parents[1] / "scripts" / "agf.py"
            result = subprocess.run([sys.executable, str(cli), "context", "extract", str(path)],
                                    capture_output=True, text=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("regular file", result.stdout + result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO requires POSIX")
    def test_replacement_pipe_is_rejected_after_nonblocking_open(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "log.txt"
            source.write_text("keep")
            pipe = Path(temp) / "pipe.log"
            os.mkfifo(pipe)
            original_open = os.open
            def replace_with_pipe(path, flags):
                self.assertTrue(flags & os.O_NONBLOCK)
                return original_open(pipe, flags)
            with patch("agf.context.os.open", side_effect=replace_with_pipe):
                with self.assertRaisesRegex(AgfError, "regular file"):
                    extract(source)

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

    @unittest.skipUnless(shutil.which("rg"), "ripgrep unavailable")
    def test_search_has_a_total_text_budget_and_preserves_location(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "many.txt").write_text("needle" + "x" * 20000 + "\nneedle\n")
            result = search("needle", temp, max_chars=20)
            self.assertEqual(len(result["matches"]), 1)
            self.assertEqual(result["matches"][0]["line"], 1)
            self.assertEqual(result["matches"][0]["text"], "needle" + "x" * 14)
            self.assertTrue(result["matches"][0]["text_truncated"])
            self.assertTrue(result["truncated"])
            self.assertFalse(result["capture_truncated"])

    @unittest.skipUnless(shutil.which("rg"), "ripgrep unavailable")
    def test_incomplete_long_match_is_not_an_empty_successful_search(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "long.txt").write_text("needle" + "x" * 160000 + "\n")
            with self.assertRaisesRegex(AgfError, "not a no-match result"):
                search("needle", temp, max_results=1)

    @unittest.skipUnless(shutil.which("rg"), "ripgrep unavailable")
    def test_complete_search_distinguishes_absence_from_truncation(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "short.txt").write_text("needle\nneedle\n")
            complete = search("needle", temp, max_results=2, max_chars=12)
            self.assertEqual(len(complete["matches"]), 2)
            self.assertFalse(complete["truncated"])
            missing = search("absent", temp)
            self.assertEqual(missing["matches"], [])
            self.assertFalse(missing["truncated"])

    def test_invalid_search_text_budget(self):
        with patch("agf.context.shutil.which", return_value="rg"):
            with self.assertRaisesRegex(AgfError, "max-chars"):
                search("needle", max_chars=0)

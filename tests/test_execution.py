import json
from pathlib import Path
import sys
import tempfile
import unittest

from agf.common import AgfError
from agf.execution import check_project, run_command


class ExecutionTests(unittest.TestCase):
    def test_argument_boundaries_and_bounded_output(self):
        value = "中文 space & $() ' ;"
        with tempfile.TemporaryDirectory() as temp:
            result = run_command([sys.executable, "-X", "utf8", "-c", "import sys; print(sys.argv[1]); print('x'*1000)", value], cwd=temp, max_chars=100)
        self.assertEqual(result["exit_code"], 0)
        self.assertIn(value, result["stdout"])
        self.assertTrue(result["stdout_truncated"])
        self.assertLessEqual(len(result["stdout"]), 100)

    def test_output_encoding_is_explicit(self):
        argv = [sys.executable, "-c", "import sys; sys.stdout.buffer.write('中文'.encode('cp950'))"]
        wrong = run_command(argv)
        self.assertTrue(wrong["stdout_decode_errors"])
        correct = run_command(argv, encoding="cp950")
        self.assertEqual(correct["stdout"], "中文")
        self.assertFalse(correct["stdout_decode_errors"])

    def test_invalid_codec_is_rejected_before_command_side_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "marker"
            with self.assertRaises(AgfError):
                run_command([sys.executable, "-c", "from pathlib import Path; Path('marker').touch()"], cwd=temp, encoding="utf8-typo")
            self.assertFalse(marker.exists())

    def test_truncation_inside_utf8_character_is_not_a_decoding_error(self):
        result = run_command([sys.executable, "-c", "import sys; sys.stdout.buffer.write('中中中'.encode())"], max_chars=1)
        self.assertEqual(result["stdout"], "中")
        self.assertTrue(result["stdout_truncated"])
        self.assertFalse(result["stdout_decode_errors"])

    def test_failure_is_not_pass(self):
        result = run_command([sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual(result["exit_code"], 7)
        self.assertEqual(result["status"], "FAIL")

    def test_timeout(self):
        result = run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.15)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["exit_code"], 124)

    def test_batch_shims_require_adapter(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "unsafe.cmd"
            path.write_text("@echo off\n", encoding="utf-8")
            with self.assertRaises(AgfError):
                run_command([str(path)])

    def test_empty_gate_and_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / "quality.json"
            config.write_text(json.dumps({"version": 1, "checks": []}))
            with self.assertRaises(AgfError):
                check_project(root, config)
            config.write_text(json.dumps({"version": 1, "checks": [{"name": "outside", "cwd": "..", "argv": ["{python}", "--version"]}]}))
            with self.assertRaises(AgfError):
                check_project(root, config)

    def test_profile_selection_and_failed_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "quality.json"
            path.write_text(json.dumps({"version": 1, "checks": [
                {"name": "fast", "argv": ["{python}", "-c", "print('ok')"], "profiles": ["quick", "full"]},
                {"name": "regression", "argv": ["{python}", "-c", "raise SystemExit(3)"], "profiles": ["full"]}]}))
            self.assertEqual(check_project(temp, path, "quick")["status"], "PASS")
            self.assertEqual(check_project(temp, path, "full")["status"], "FAIL")

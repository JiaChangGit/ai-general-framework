import json
import os
from contextlib import chdir
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

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

    def test_nontext_codecs_are_rejected_before_command_side_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "marker"
            argv = [sys.executable, "-c", "from pathlib import Path; Path('marker').touch(); print('ok')"]
            for encoding in ("rot_13", "base64_codec", "hex_codec", "idna"):
                with self.subTest(encoding=encoding):
                    with self.assertRaisesRegex(AgfError, "bytes-to-text"):
                        run_command(argv, cwd=temp, encoding=encoding, output_dir=Path(temp) / encoding)
                    self.assertFalse(marker.exists())
                    self.assertFalse((Path(temp) / encoding).exists())

    def test_check_rejects_nontext_codec_before_any_check_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / "quality.json"
            config.write_text(json.dumps({"version": 1, "checks": [
                {"name": "first", "argv": ["{python}", "-c", "from pathlib import Path; Path('marker').touch()"]},
                {"name": "bad-codec", "argv": ["{python}", "--version"], "encoding": "rot_13"}
            ]}))
            with self.assertRaisesRegex(AgfError, "bytes-to-text"):
                check_project(root, config)
            self.assertFalse((root / "marker").exists())

    def test_truncation_inside_utf8_character_is_not_a_decoding_error(self):
        result = run_command([sys.executable, "-c", "import sys; sys.stdout.buffer.write('中中中'.encode())"], max_chars=1)
        self.assertEqual(result["stdout"], "中")
        self.assertTrue(result["stdout_truncated"])
        self.assertFalse(result["stdout_decode_errors"])

    def test_failure_is_not_pass(self):
        result = run_command([sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual(result["exit_code"], 7)
        self.assertEqual(result["status"], "FAIL")

    def test_optional_evidence_preserves_complete_raw_bytes_and_failed_result(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            result = run_command([sys.executable, "-c",
                                  "import sys; sys.stdout.buffer.write(b'x'*10000+b'\\xff'); sys.stderr.buffer.write(b'failure\\x00\\x80'); sys.exit(7)"],
                                 cwd=temp, max_chars=30, output_dir=output)
            self.assertEqual((output / "stdout.bin").read_bytes(), b"x" * 10000 + b"\xff")
            self.assertEqual((output / "stderr.bin").read_bytes(), b"failure\x00\x80")
            self.assertEqual(result["stdout_bytes"], 10001)
            self.assertTrue(result["stdout_truncated"])
            self.assertTrue(result["stderr_decode_errors"])
            self.assertEqual(result["exit_code"], 7)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(json.loads((output / "result.json").read_text(encoding="utf-8")), result)

    def test_default_run_creates_no_evidence_files(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_command([sys.executable, "-c", "print('ok')"], cwd=temp)
            self.assertNotIn("evidence", result)
            self.assertEqual(list(Path(temp).iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits only")
    def test_evidence_directory_is_private(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            run_command([sys.executable, "-c", "print('ok')"], cwd=temp, output_dir=output)
            self.assertEqual(output.stat().st_mode & 0o077, 0)

    def test_relative_evidence_path_uses_invoking_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            caller = Path(temp) / "caller"
            child = Path(temp) / "child"
            caller.mkdir()
            child.mkdir()
            with chdir(caller):
                result = run_command([sys.executable, "-c", "print('ok')"], cwd=child, output_dir="run")
            self.assertEqual(Path(result["evidence"]["directory"]), caller / "run")
            self.assertTrue((caller / "run" / "result.json").is_file())
            self.assertFalse((child / "run").exists())

    def test_existing_evidence_destination_rejected_before_command(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "folder"
            folder.mkdir()
            file = root / "file"
            file.write_bytes(b"keep")
            for destination in (folder, file):
                with self.subTest(destination=destination):
                    with self.assertRaises(AgfError):
                        run_command([sys.executable, "-c", "from pathlib import Path; Path('marker').touch()"],
                                    cwd=temp, output_dir=destination)
                    self.assertFalse((root / "marker").exists())
            self.assertEqual(list(folder.iterdir()), [])
            self.assertEqual(file.read_bytes(), b"keep")

    def test_evidence_path_prepare_failure_does_not_start_command(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            blocked = root / "file"
            blocked.write_text("keep")
            with self.assertRaises(AgfError):
                run_command([sys.executable, "-c", "from pathlib import Path; Path('marker').touch()"],
                            cwd=temp, output_dir=blocked / "run")
            self.assertFalse((root / "marker").exists())
            self.assertEqual(blocked.read_text(), "keep")

    def test_all_evidence_files_are_opened_before_command_starts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original_open = Path.open
            def fail_metadata(path, *args, **kwargs):
                if path.name == "result.json":
                    raise OSError("cannot open metadata")
                return original_open(path, *args, **kwargs)
            with mock.patch.object(Path, "open", fail_metadata):
                with self.assertRaises(AgfError):
                    run_command([sys.executable, "-c", "from pathlib import Path; Path('marker').touch()"],
                                cwd=temp, output_dir=root / "run")
            self.assertFalse((root / "marker").exists())

    def test_metadata_save_failure_preserves_actual_command_result(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            with mock.patch("agf.execution.json_text", side_effect=OSError("disk full")):
                result = run_command([sys.executable, "-c", "from pathlib import Path; Path('marker').write_text('once'); print('done')"],
                                     cwd=temp, output_dir=output)
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["evidence"]["metadata_saved"])
            self.assertIn("Command already ran", result["evidence"]["error"])
            self.assertEqual((Path(temp) / "marker").read_text(), "once")
            self.assertIn(b"done", (output / "stdout.bin").read_bytes())

    def test_timeout_evidence_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            result = run_command([sys.executable, "-c", "import sys,time; sys.stdout.buffer.write(b'started'); sys.stdout.buffer.flush(); time.sleep(10)"],
                                 cwd=temp, timeout=1, output_dir=output)
            self.assertTrue(result["timed_out"])
            self.assertEqual(result["exit_code"], 124)
            self.assertEqual((output / "stdout.bin").read_bytes(), b"started")
            self.assertTrue(json.loads((output / "result.json").read_text())["timed_out"])

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

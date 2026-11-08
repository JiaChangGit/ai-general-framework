import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agf import binary
from agf.common import AgfError


ROOT = Path(__file__).resolve().parents[1]


def invoke(*argv):
    parser = argparse.ArgumentParser()
    binary.register(parser.add_subparsers(required=True))
    args = parser.parse_args(argv)
    return args.func(args)


class BinaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agf-binary-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "資料 with spaces & $.bin"
        self.data = b"\x00\xff\x78\x56\x34\x80\x01\x00"
        self.source.write_bytes(self.data)

    def command(self, *args):
        return subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/agf.py"), "binary", *args],
                              cwd=self.root, capture_output=True, encoding="utf-8", timeout=20)

    def test_uint24_endian_values_and_selected_range_identity(self):
        little = invoke("binary", "bytes", str(self.source), "0x2", "3")
        big = invoke("binary", "bytes", str(self.source), "02", "0X3", "--endian", "big")
        self.assertEqual((little["format"], little["byte_order"], little["value_hex"], little["value_decimal"]),
                         ("uint24", "little", "0x345678", "3430008"))
        self.assertEqual((big["byte_order"], big["value_hex"], big["value_decimal"]),
                         ("big", "0x785634", "7886388"))
        self.assertEqual(little["raw_hex"], "78 56 34")
        self.assertEqual(little["range_sha256"], hashlib.sha256(b"\x78\x56\x34").hexdigest())
        self.assertNotEqual(little["range_sha256"], hashlib.sha256(self.data).hexdigest())
        self.assertEqual((little["requested_bytes"], little["bytes_read"], little["file_size_at_open"]), (3, 3, 8))
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_large_unsigned_values_remain_exact_decimal_strings(self):
        self.source.write_bytes(b"\xff" * 64)
        value64 = invoke("binary", "bytes", str(self.source), "0", "8")
        self.assertEqual(value64["value_decimal"], "18446744073709551615")
        self.assertEqual(value64["value_hex"], "0xFFFFFFFFFFFFFFFF")
        value512 = invoke("binary", "bytes", str(self.source), "0", "64")
        self.assertEqual(value512["value_decimal"], str((1 << 512) - 1))
        self.assertEqual(value512["format"], "uint512")

    def test_bit_numbering_crosses_bytes_without_changing_convention(self):
        cases = [(b"\xa8", "3", "3", "0x5", 1),
                 (b"\x80\x01", "7", "2", "0x3", 2),
                 (b"\x80\x00", "7", "2", "0x1", 2),
                 (b"\x80" + b"\x00" * 7 + b"\x40", "7", "64", "0x8000000000000001", 9)]
        for data, bit_offset, width, expected, needed in cases:
            with self.subTest(bit_offset=bit_offset, width=width, data=data):
                self.source.write_bytes(data)
                result = invoke("binary", "bits", str(self.source), "0", bit_offset, width)
                self.assertEqual(result["value_hex"], expected)
                self.assertEqual(result["value_decimal"], str(int(expected, 16)))
                self.assertEqual(result["bytes_read"], needed)
                self.assertEqual((result["byte_order"], result["bit_order"]), ("little", "lsb-first"))

    def test_dump_sanitizes_control_bytes_and_keeps_absolute_offsets(self):
        self.source.write_bytes(b"AB\x1b\x00\x7f\x80xyz\n")
        result = invoke("binary", "dump", str(self.source), "0", "10")
        self.assertEqual(result["status"], "READ")
        self.assertTrue(result["dump_lines"][0].endswith("|AB....xyz.|"))
        self.assertNotIn("\x1b", result["dump_lines"][0])
        self.assertNotIn("byte_order", result)
        self.source.write_bytes(bytes(range(20)))
        result = invoke("binary", "dump", str(self.source), "1", "18")
        self.assertEqual(len(result["dump_lines"]), 2)
        self.assertTrue(result["dump_lines"][0].startswith("0x00000001"))
        self.assertTrue(result["dump_lines"][1].startswith("0x00000011"))
        self.assertEqual(result["range_sha256"], hashlib.sha256(bytes(range(1, 19))).hexdigest())

    def test_dump_partial_and_empty_eof_are_explicit_failures(self):
        for offset, requested, actual in ((6, 10, 2), (8, 1, 0), (12, 1, 0)):
            with self.subTest(offset=offset):
                result = invoke("binary", "dump", str(self.source), str(offset), str(requested))
                self.assertEqual((result["status"], result["requested_bytes"], result["bytes_read"], result["_exit_code"]),
                                 ("PARTIAL", requested, actual, 1))
                self.assertEqual(bool(result["dump_lines"]), bool(actual))
        for operation, tail in (("bytes", ["2"]), ("bits", ["7", "2"])):
            with self.subTest(operation=operation), self.assertRaisesRegex(AgfError, "Short read"):
                invoke("binary", operation, str(self.source), "7", *tail)

    def test_invalid_ranges_do_not_touch_the_file(self):
        cases = [(0, -1, 64), (0, 0, 64), (0, 65, 64), (0, 4097, 4096),
                 (-1, 1, 64), (binary.MAX_OFFSET, 1, 64), (binary.MAX_OFFSET - 1, 2, 64), (1 << 100, 1, 64)]
        with patch.object(binary.Path, "stat") as source_stat, patch.object(binary.os, "open") as source_open:
            for offset, size, maximum in cases:
                with self.subTest(offset=offset, size=size), self.assertRaises(AgfError):
                    binary._read(str(self.source), offset, size, maximum)
            source_stat.assert_not_called()
            source_open.assert_not_called()
        with patch.object(binary, "_read") as read:
            for bit_offset, width in ((-1, 1), (8, 1), (0, 0), (0, 65)):
                args = argparse.Namespace(input=str(self.source), offset=0, bit_offset=bit_offset, num_bits=width)
                with self.subTest(bit_offset=bit_offset, width=width), self.assertRaises(AgfError):
                    binary._bits(args)
            read.assert_not_called()

    def test_numeric_input_is_decimal_or_hex_without_sign_or_expression(self):
        for token, value in (("00012", 12), ("0xA", 10), ("0Xff", 255), (" 0 ", 0)):
            self.assertEqual(binary._number(token), value)
        for token in ("-1", "+1", "-0x1", "0b10", "1_000", "1.0", "1+2", "", "0x", "9" * 100):
            with self.subTest(token=token), self.assertRaises(argparse.ArgumentTypeError):
                binary._number(token)

    def test_regular_source_required_before_opening(self):
        with patch.object(binary.os, "open") as source_open:
            with self.assertRaisesRegex(AgfError, "regular files"):
                binary._read(str(self.root), 0, 1, 64)
            source_open.assert_not_called()
        with self.assertRaises(FileNotFoundError):
            binary._read(str(self.root / "missing.bin"), 0, 1, 64)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO only")
    def test_fifo_is_rejected_without_waiting_for_a_writer(self):
        fifo = self.root / "events.pipe"
        os.mkfifo(fifo)
        with patch.object(binary.os, "open") as source_open:
            with self.assertRaisesRegex(AgfError, "regular files"):
                binary._read(str(fifo), 0, 1, 64)
            source_open.assert_not_called()

    def test_opened_descriptor_is_rechecked_and_closed_before_reading(self):
        read_end, write_end = os.pipe()
        try:
            with patch.object(binary.os, "open", return_value=read_end), \
                    patch.object(binary.os, "read", side_effect=AssertionError("Unexpected pipe read")) as read:
                with self.assertRaisesRegex(AgfError, "not a regular file"):
                    binary._read(str(self.source), 0, 1, 64)
                read.assert_not_called()
            with self.assertRaises(OSError):
                os.fstat(read_end)
        finally:
            os.close(write_end)

    def test_descriptor_closes_when_seek_fails(self):
        real_close = os.close
        with patch.object(binary.os, "lseek", side_effect=OSError("injected seek failure")), \
                patch.object(binary.os, "close", wraps=real_close) as close:
            with self.assertRaisesRegex(OSError, "injected seek failure"):
                binary._read(str(self.source), 0, 1, 64)
        close.assert_called_once()
        with self.assertRaises(OSError):
            os.fstat(close.call_args.args[0])

    def test_short_os_reads_are_accumulated_only_up_to_requested_size(self):
        with patch.object(binary.os, "read", side_effect=[b"\x78", b"\x56\x34"]) as read:
            data, _ = binary._read(str(self.source), 0, 3, 64)
        self.assertEqual(data, b"\x78\x56\x34")
        self.assertEqual([call.args[1] for call in read.call_args_list], [3, 2])

    def test_regular_file_symlink_keeps_normal_read_semantics(self):
        link = self.root / "alias.bin"
        try:
            link.symlink_to(self.source)
        except OSError as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        self.assertEqual(invoke("binary", "bytes", str(link), "2", "3")["value_hex"], "0x345678")
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_actual_cli_exit_codes_and_output_match_success_partial_and_error(self):
        success = self.command("bytes", str(self.source), "0x2", "3")
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertEqual(json.loads(success.stdout)["value_decimal"], "3430008")
        partial = self.command("dump", str(self.source), "7", "4")
        self.assertEqual(partial.returncode, 1, partial.stderr)
        self.assertEqual(json.loads(partial.stdout)["status"], "PARTIAL")
        short = self.command("bytes", str(self.source), "7", "2")
        self.assertEqual(short.returncode, 2, short.stderr)
        self.assertEqual(json.loads(short.stdout)["status"], "ERROR")
        invalid = self.command("bytes", str(self.source), "0", "-1")
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("nonnegative decimal", invalid.stderr)
        self.assertEqual(self.source.read_bytes(), self.data)


if __name__ == "__main__":
    unittest.main()

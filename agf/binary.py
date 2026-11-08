"""Bounded, read-only inspection of saved binary files; standard library only."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat

from .common import AgfError


MAX_OFFSET = (1 << 63) - 1
MAX_VALUE_BYTES = 64
MAX_DUMP_BYTES = 4096


def _number(value: str) -> int:
    token = value.strip()
    if len(token) > 32 or not re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|[0-9]+)", token):
        raise argparse.ArgumentTypeError("Use a nonnegative decimal integer or 0x hexadecimal integer")
    return int(token, 16 if token.lower().startswith("0x") else 10)


def _read(path: str, offset: int, size: int, maximum: int) -> tuple[bytes, int]:
    # Validate bounds before any file access: read(-1) would read the whole file.
    if not 1 <= size <= maximum:
        raise AgfError(f"Read size must be between 1 and {maximum} bytes")
    if offset < 0 or offset > MAX_OFFSET - size:
        raise AgfError("offset + size must fit a nonnegative signed 64-bit file position")
    if not stat.S_ISREG(Path(path).stat().st_mode):
        raise AgfError("Only saved regular files are supported; not devices, pipes or directories")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise AgfError("Opened source is not a regular file")
        os.lseek(descriptor, offset, os.SEEK_SET)
        data = bytearray()
        while len(data) < size:
            chunk = os.read(descriptor, size - len(data))
            if not chunk:
                break
            data.extend(chunk)
        return bytes(data), opened.st_size
    except OverflowError as exc:
        raise AgfError("File position is unsupported by this platform") from exc
    finally:
        os.close(descriptor)


def _base(args, size: int, maximum: int, *, exact: bool = True) -> tuple[bytes, dict]:
    data, file_size = _read(args.input, args.offset, size, maximum)
    if exact and len(data) != size:
        raise AgfError(f"Short read at 0x{args.offset:X}: requested {size} bytes, got {len(data)}")
    return data, {"status": "READ" if len(data) == size else "PARTIAL",
                  "source": args.input, "offset": args.offset, "offset_hex": f"0x{args.offset:X}",
                  "requested_bytes": size, "bytes_read": len(data), "file_size_at_open": file_size,
                  "range_sha256": hashlib.sha256(data).hexdigest()}


def _value(data: bytes, value: int) -> dict:
    # A decimal string preserves uint64+ values in consumers with JS numbers.
    return {"raw_hex": data.hex(" ").upper(), "value_hex": f"0x{value:X}", "value_decimal": str(value)}


def _bytes(args):
    data, result = _base(args, args.size, MAX_VALUE_BYTES)
    result.update(_value(data, int.from_bytes(data, args.endian)))
    result.update({"format": f"uint{len(data) * 8}", "byte_order": args.endian})
    return result


def _bits(args):
    if not 0 <= args.bit_offset <= 7:
        raise AgfError("bit_offset must be 0 to 7, with bit 0 the least significant bit of the first byte")
    if not 1 <= args.num_bits <= 64:
        raise AgfError("num_bits must be 1 to 64")
    size = (args.bit_offset + args.num_bits + 7) // 8
    data, result = _base(args, size, MAX_VALUE_BYTES)
    value = (int.from_bytes(data, "little") >> args.bit_offset) & ((1 << args.num_bits) - 1)
    result.update(_value(data, value))
    result.update({"byte_order": "little", "bit_order": "lsb-first",
                   "bit_offset": args.bit_offset, "num_bits": args.num_bits})
    return result


def _dump(args):
    data, result = _base(args, args.length, MAX_DUMP_BYTES, exact=False)
    rows = []
    for index in range(0, len(data), 16):
        chunk = data[index:index + 16]
        printable = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk)
        rows.append(f"0x{args.offset + index:08X}  {chunk.hex(' ').upper():<47}  |{printable}|")
    result.update({"dump_lines": rows, "_exit_code": 0 if len(data) == args.length else 1})
    return result


def register(subparsers):
    parser = subparsers.add_parser("binary", help="Read bounded byte ranges and bit fields from saved files")
    commands = parser.add_subparsers(dest="binary_operation", required=True)
    for name, handler in (("bytes", _bytes), ("bits", _bits), ("dump", _dump)):
        command = commands.add_parser(name)
        command.add_argument("input", help="Saved regular file, any extension; opened read-only")
        command.add_argument("offset", type=_number, help="Byte offset in the file; decimal or 0x hexadecimal")
        if name == "bytes":
            command.add_argument("size", type=_number, help="1 to 64 bytes, interpreted as one unsigned integer")
            command.add_argument("--endian", choices=["little", "big"], default="little")
        elif name == "bits":
            command.add_argument("bit_offset", type=_number, help="0 to 7; bit 0 is the first byte's LSB")
            command.add_argument("num_bits", type=_number, help="1 to 64, little-endian and LSB-first")
        else:
            command.add_argument("length", type=_number, help="1 to 4096 bytes; raw dump has no byte order")
        command.set_defaults(func=handler)

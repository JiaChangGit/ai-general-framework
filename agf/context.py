"""Source-located excerpts and bounded ripgrep search, not a new indexer."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

from .common import AgfError
from .execution import run_command


def extract(path, start=1, end=None, max_chars=16000, encoding="utf-8-sig", max_lines=200):
    source = Path(path).resolve()
    end = end if end is not None else start + 79
    if start < 1 or end < start or max_chars < 1 or max_lines < 1:
        raise AgfError("Require 1 <= start <= end and positive max-chars/max-lines.")
    output = []
    used = 0
    truncated = False
    try:
        if not stat.S_ISREG(source.stat().st_mode):
            raise AgfError("Context extraction requires a saved regular file, not a device, pipe or directory.")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(source, flags)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise AgfError("Opened context source is not a regular file.")
            with os.fdopen(descriptor, encoding=encoding, errors="strict", closefd=False) as stream:
                for number, line in enumerate(stream, 1):
                    if number > end:
                        break
                    if number < start:
                        continue
                    if len(output) >= max_lines:
                        truncated = True
                        break
                    text = line.rstrip("\r\n")
                    remaining = max_chars - used
                    if len(text) > remaining:
                        output.append({"line": number, "text": text[:remaining]})
                        truncated = True
                        break
                    output.append({"line": number, "text": text})
                    used += len(text) + 1
                    if used >= max_chars:
                        truncated = True
                        break
                # Hash the already-opened file; reopening the path could block
                # on a replacement FIFO or identify a different source.
                stream.seek(0)
                checksum = hashlib.file_digest(stream.buffer, "sha256").hexdigest()
        finally:
            os.close(descriptor)
    except (OSError, UnicodeError, LookupError) as exc:
        raise AgfError(f"Cannot extract {source}: {exc}") from exc
    return {"path": str(source), "sha256": checksum, "encoding": encoding, "lines": output,
            "requested_range": [start, end], "truncated": truncated,
            "max_lines": max_lines, "limit_unit": "source characters including line breaks, not model tokens or JSON overhead"}


def search(pattern, root=".", glob=None, max_results=30, max_chars=16000):
    executable = shutil.which("rg")
    if not executable:
        raise AgfError("ripgrep is unavailable in this environment; use a scoped native search (for example grep on Linux or Select-String on Windows), then context extract on known files. Installation is optional and requires task authorization.")
    if max_results < 1 or max_chars < 1:
        raise AgfError("max-results and max-chars must be positive.")
    argv = [executable, "--json", "--max-count", str(max_results + 1)]
    if glob:
        argv += ["--glob", glob]
    argv += ["--", pattern, "."]
    run = run_command(argv, cwd=root, timeout=20, max_chars=128000)
    if run["exit_code"] not in (0, 1):
        raise AgfError(f"ripgrep failed: {run['stderr']}")
    if run["stdout_decode_errors"]:
        raise AgfError("Cannot decode ripgrep JSON reliably; use a scoped native search.")
    matches = []
    remaining = max_chars
    truncated = run["stdout_truncated"]
    for line in run["stdout"].splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "match":
            data = event["data"]
            if len(matches) >= max_results or remaining == 0:
                truncated = True
                break
            content = data["lines"].get("text", "[binary/non-UTF8 match]").rstrip("\r\n")
            clipped = len(content) > remaining
            matches.append({"path": data["path"].get("text"), "line": data["line_number"],
                            "text": content[:remaining], "text_truncated": clipped})
            remaining -= len(matches[-1]["text"])
            truncated = truncated or clipped
    if not matches and run["stdout_truncated"]:
        raise AgfError("Search capture was truncated before a complete match could be decoded; this is not a no-match result. Narrow the scope or use native ripgrep to locate long matching lines.")
    return {"root": str(Path(root).resolve()), "matches": matches,
            "truncated": truncated, "capture_truncated": run["stdout_truncated"],
            "max_chars": max_chars, "limit_unit": "matched text characters, excluding paths and JSON overhead; not model tokens",
            "meaning": "Text matches, not verified call or data-flow relationships."}


def register(subparsers):
    context = subparsers.add_parser("context", help="Read targeted source and log excerpts")
    children = context.add_subparsers(dest="context_action", required=True)
    item = children.add_parser("extract")
    item.add_argument("path")
    item.add_argument("--start", type=int, default=1)
    item.add_argument("--end", type=int)
    item.add_argument("--max-chars", type=int, default=16000)
    item.add_argument("--max-lines", type=int, default=200)
    item.add_argument("--encoding", default="utf-8-sig")
    item.set_defaults(func=lambda a: extract(a.path, a.start, a.end, a.max_chars, a.encoding, a.max_lines))
    item = children.add_parser("search")
    item.add_argument("pattern")
    item.add_argument("--root", default=".")
    item.add_argument("--glob")
    item.add_argument("--max-results", type=int, default=30)
    item.add_argument("--max-chars", type=int, default=16000)
    item.set_defaults(func=lambda a: search(a.pattern, a.root, a.glob, a.max_results, a.max_chars))

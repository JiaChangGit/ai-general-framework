"""Source-located excerpts and bounded ripgrep search, not a new indexer."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

from .common import AgfError, digest
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
        with source.open(encoding=encoding, errors="strict") as stream:
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
        checksum = digest(source)
    except (OSError, UnicodeError, LookupError) as exc:
        raise AgfError(f"Cannot extract {source}: {exc}") from exc
    return {"path": str(source), "sha256": checksum, "encoding": encoding, "lines": output,
            "requested_range": [start, end], "truncated": truncated,
            "max_lines": max_lines, "limit_unit": "source characters including line breaks, not model tokens or JSON overhead"}


def search(pattern, root=".", glob=None, max_results=30):
    executable = shutil.which("rg")
    if not executable:
        raise AgfError("ripgrep is unavailable in this environment; use a scoped native search (for example grep on Linux or Select-String on Windows), then context extract on known files. Installation is optional and requires task authorization.")
    if max_results < 1:
        raise AgfError("max-results must be positive.")
    argv = [executable, "--json", "--max-count", str(max_results + 1)]
    if glob:
        argv += ["--glob", glob]
    argv += ["--", pattern, "."]
    run = run_command(argv, cwd=root, timeout=20, max_chars=128000)
    if run["exit_code"] not in (0, 1):
        raise AgfError(f"ripgrep failed: {run['stderr']}")
    matches = []
    for line in run["stdout"].splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "match":
            data = event["data"]
            matches.append({"path": data["path"].get("text"), "line": data["line_number"],
                            "text": data["lines"].get("text", "[binary/non-UTF8 match]").rstrip("\r\n")})
    return {"root": str(Path(root).resolve()), "matches": matches[:max_results],
            "truncated": len(matches) > max_results or run["stdout_truncated"],
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
    item.set_defaults(func=lambda a: search(a.pattern, a.root, a.glob, a.max_results))

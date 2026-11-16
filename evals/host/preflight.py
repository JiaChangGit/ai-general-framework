#!/usr/bin/env python3
"""Check a prepared subject directory before a headless session runs in it.

    python evals/host/preflight.py DIR [--forbid PATH ...] [--env NAME=VALUE ...]

It looks for the leaks that contaminated a downstream project's evaluations:

1. files in DIR that name a forbidden path, such as the original project the
   materials were copied from (a subject once followed such a path and read
   the original's handoff), and symbolic links in DIR that point outside it;
   only the --forbid paths are searched, and unreadable files are listed;
2. instruction or skill files in an ancestor of DIR that the host would load
   as well (CLAUDE.md, AGENTS.md, GEMINI.md, .claude/skills, .agents/skills);
   the home directory's .claude and .agents are user-level and only reported;
3. entries next to DIR or next to its parent, which a subject can read (one
   once globbed its parent and read the other group's materials);
4. environment variables that look like a host channel, a session or a
   credential and would reach the subject through run_claude.py, whether kept
   or set with --env, unless --allow-env names them.

Prints JSON and exits 1 when it finds a problem. It only reads.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_claude  # noqa: E402

INSTRUCTIONS = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "GEMINI.md", ".claude/CLAUDE.md", ".claude/skills",
                ".claude/settings.json", ".claude/settings.local.json", ".agents/skills")
HOST_LIKE = re.compile(r"CLAUDE|ANTHROPIC|CODEX|GEMINI|OPENCODE|SESSION|SOCK|TOKEN|SECRET|API_KEY", re.IGNORECASE)
TEXT_LIMIT = 1_000_000


def _files(directory: Path):
    for top, folders, names in os.walk(directory, followlinks=False):
        folders[:] = [name for name in folders if name != ".git"]
        for name in names + folders:
            yield Path(top) / name


def forbidden_mentions(directory: Path, forbidden: list[str]) -> tuple[list[dict], list[str]]:
    """Lines naming a forbidden path, and the files that could not be read as UTF-8 text (never silently passed)."""
    needles = sorted({value.rstrip("/\\") for value in forbidden if value.strip()})
    found, unreadable = [], []
    for file in _files(directory):
        if file.is_symlink() or not file.is_file():
            continue
        try:
            if file.stat().st_size > TEXT_LIMIT:
                raise ValueError("too large")
            text = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            unreadable.append(file.relative_to(directory).as_posix())
            continue
        for number, line in enumerate(text.splitlines(), 1):
            found += [{"file": file.relative_to(directory).as_posix(), "line": number, "path": needle}
                      for needle in needles if needle in line]
    return found, sorted(unreadable)


def links_outside(directory: Path) -> list[dict]:
    base = directory.resolve()
    return [{"link": entry.relative_to(directory).as_posix(), "target": str(entry.resolve())}
            for entry in _files(directory) if entry.is_symlink() and not entry.resolve().is_relative_to(base)]


def ancestor_instructions(directory: Path) -> tuple[list[str], list[str]]:
    home = Path.home().resolve()
    problems, user_level = [], []
    for ancestor in directory.resolve().parents:
        for name in INSTRUCTIONS:
            candidate = ancestor / name
            if candidate.exists():
                (user_level if ancestor == home and name.startswith((".claude/", ".agents/")) else problems).append(str(candidate))
    return problems, user_level


def neighbours(directory: Path) -> list[str]:
    found = []
    for inner in (directory.resolve(), directory.resolve().parent):
        try:
            found += [str(entry) for entry in sorted(inner.parent.iterdir()) if entry.resolve() != inner]
        except OSError:
            continue
    return found


def environment(extra: dict[str, str], allow: set[str] | frozenset = frozenset()) -> dict:
    """Host-like names that would reach the subject, kept or set explicitly, unless allowed by name."""
    passed = run_claude.clean_env(extra)
    return {"passed": sorted(passed), "set_explicitly": sorted(extra), "allowed": sorted(allow),
            "host_like_present": sorted(name for name in os.environ if HOST_LIKE.search(name)),
            "host_like_passed": sorted(name for name in passed if HOST_LIKE.search(name) and name not in allow)}


def check(directory: Path, forbidden: list[str] | None = None, extra: dict[str, str] | None = None,
          allow_env: set[str] | None = None) -> dict:
    ancestors, user_level = ancestor_instructions(directory)
    mentions, unreadable = forbidden_mentions(directory, forbidden or [])
    report = {"directory": str(directory.resolve()), "forbidden_paths_checked": sorted({value.rstrip("/\\") for value in forbidden or [] if value.strip()}),
              "forbidden_mentions": mentions, "unreadable_files": unreadable,
              "links_outside": links_outside(directory), "ancestor_instructions": ancestors, "user_level": user_level,
              "neighbours": neighbours(directory), "environment": environment(extra or {}, frozenset(allow_env or ()))}
    report["ok"] = not (report["forbidden_mentions"] or report["links_outside"] or ancestors
                        or report["neighbours"] or report["environment"]["host_like_passed"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--forbid", action="append", default=[], help="a path that must not appear in the directory's files (repeatable)")
    parser.add_argument("--env", action="append", default=[], help="NAME=VALUE the runner will pass (repeatable)")
    parser.add_argument("--allow-env", action="append", default=[], help="a host-like variable name that may reach the subject (repeatable)")
    args = parser.parse_args()
    if not args.directory.is_dir():
        raise SystemExit(f"not a directory: {args.directory}")
    report = check(args.directory, args.forbid, run_claude._pairs(args.env), set(args.allow_env))
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

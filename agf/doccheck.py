"""Check that the framework's own documentation names things that exist (S18).

A narrow, deterministic version of a "doc gardening" pass: every `agf` subcommand and
option written in inline code or a code block must exist in the CLI, and every path in
inline code that starts with one of the framework's top-level folders must exist. It
cannot tell whether a described behaviour is right; it only catches names that went stale.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re

FOLDERS = ("docs/", "templates/", "skills/", "evals/", "agf/", "scripts/", "adapters/", "examples/", "tests/")
CODE = re.compile(r"```[^\n]*\n(.*?)```|`([^`\n]+)`", re.S)
COMMAND = re.compile(r"(?:scripts/agf\.py|(?<![\w./-])agf)[ \t]+((?:[a-z][a-z-]*)(?:[ \t]+(?:[a-z][a-z-]*))?)((?:[ \t]+[^\s`|;&]+)*)")
OPTION = re.compile(r"(?<![\w-])(--[a-z][a-z0-9-]*)")
# Named in the docs as paths of a user's project. These folders exist in projects and in the framework,
# so each such path is listed here; everything else must exist.
PROJECT_PATHS = {"docs/HANDOFF.md", "skills/microkernel-engineering"}
CONTINUED = re.compile(r"\\\r?\n[ \t]*")
SKIP_PATH = re.compile(r"[<>*{}…$\s]|\.\.\.")
# Dated records describe the state when they were written; they are not kept in step with the code.
RECORDS = {"analysis-2026-11.md", "verification.md", "research.md", "link-study.md", "memory-prompt-study.md",
           "skillkit-study.md", "capability-decisions.md", "writing-research.md"}


def _parsers():
    from . import cli
    root = cli.parser()
    found = {}

    def walk(parser, prefix):
        options = {opt for action in parser._actions for opt in action.option_strings}
        children = {}
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                children = dict(action.choices)
        found[prefix] = (options, set(children))
        for name, child in children.items():
            walk(child, prefix + (name,))

    walk(root, ())
    return found


def _documents(root: Path) -> list[Path]:
    files = [root / "README.md", root / "AGENTS.md"]
    files += [path for path in sorted((root / "docs").glob("*.md")) if path.name not in RECORDS]
    for folder in ("skills", "templates"):
        files += sorted((root / folder).rglob("*.md"))
    return [path for path in files if path.is_file()]


def _check_command(words: str, rest: str, parsers: dict) -> str | None:
    parts = words.split()
    first = parts[0]
    if (first,) not in parsers:
        return f"agf has no subcommand `{first}`"
    key = (first,)
    if parsers[key][1]:  # the subcommand has operations
        if len(parts) < 2 or (first, parts[1]) not in parsers:
            return None if len(parts) < 2 else f"`agf {first}` has no operation `{parts[1]}`"
        key = (first, parts[1])
    elif len(parts) > 1:
        rest = " " + parts[1] + rest
    options = parsers[key][0]
    for option in OPTION.findall(rest):
        if option not in options:
            return f"`agf {' '.join(key)}` has no option `{option}`"
    return None


def check(root) -> list[str]:
    directory = Path(root).resolve()
    if not (directory / "agf" / "cli.py").is_file():
        return []
    parsers = _parsers()
    problems = []
    for path in _documents(directory):
        text = path.read_text(encoding="utf-8-sig")
        relative = path.relative_to(directory).as_posix()
        for match in CODE.finditer(text):
            code = match.group(1) or match.group(2)
            line = text.count("\n", 0, match.start()) + 1
            for command in COMMAND.finditer(CONTINUED.sub(" ", code)):
                problem = _check_command(command.group(1), command.group(2) or "", parsers)
                if problem:
                    problems.append(f"{relative}:{line}: {problem}")
            if match.group(2):
                candidate = code.strip().split("#", 1)[0].rstrip(":,.;")
                if candidate.startswith(FOLDERS) and not SKIP_PATH.search(candidate) and not (directory / candidate).exists():
                    if candidate.rstrip("/") in PROJECT_PATHS:
                        continue
                    problems.append(f"{relative}:{line}: path `{candidate}` does not exist "
                                    "(if it is a path of the user's project, add it to PROJECT_PATHS in agf/doccheck.py)")
    return problems

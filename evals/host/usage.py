#!/usr/bin/env python3
"""Count how often the framework's skills and agf commands were actually used, from local Claude Code transcripts.

    python evals/host/usage.py [--projects DIR] [--since YYYY-MM-DD] [--framework DIR]

DIR defaults to ~/.claude/projects, where Claude Code keeps one JSONL file per
session. It only reads, and prints totals only: Skill tool calls and SKILL.md
reads for each skill in this framework (other skills are summed as "other"),
which copy a SKILL.md was read from, and agf subcommands found in Bash
commands. No message text, project name, path or session id is printed.
A count shows that a call happened, not that it helped.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re

AGF = re.compile(r"agf\.py['\"]?\s+([a-z][a-z-]*)")
FRAMEWORK = Path(__file__).resolve().parents[2]


def _when(entry: dict) -> datetime | None:
    value = entry.get("timestamp")
    try:
        when = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def count(projects: Path, skills: set[str], since: datetime | None = None) -> dict:
    calls, reads, copies, commands = Counter(), Counter(), Counter(), Counter()
    sessions = 0
    for transcript in sorted(projects.rglob("*.jsonl")):
        sessions += 1
        try:
            lines = transcript.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant" or (since and (_when(entry) or since) < since):
                continue
            content = (entry.get("message") or {}).get("content")
            for part in content if isinstance(content, list) else []:
                if not isinstance(part, dict) or part.get("type") != "tool_use":
                    continue
                name, given = part.get("name"), part.get("input") or {}
                if name == "Skill":
                    skill = str(given.get("skill") or given.get("name") or "").split(":")[-1]
                    calls[skill if skill in skills else "other"] += 1
                elif name == "Read" and str(given.get("file_path", "")).endswith("SKILL.md"):
                    file = Path(str(given["file_path"]))
                    reads[file.parent.name if file.parent.name in skills else "other"] += 1
                    holder = file.parent.parent.parent.name if file.parent.parent.name == "skills" else ""
                    copies[f"{holder}/skills" if holder in (".claude", ".agents") else "other"] += 1  # never a project name
                elif name == "Bash":
                    for command in AGF.findall(str(given.get("command", ""))):
                        commands[command] += 1
    return {"sessions_scanned": sessions, "since": since.date().isoformat() if since else None,
            "skill_tool_calls": dict(sorted(calls.items())), "skill_file_reads": dict(sorted(reads.items())),
            "skill_file_copies": dict(sorted(copies.items())), "agf_commands": dict(sorted(commands.items())),
            "meaning": "Counts of calls found in local transcripts; not evidence that a call helped."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--projects", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--since", help="only count entries on or after this date (YYYY-MM-DD)")
    parser.add_argument("--framework", type=Path, default=FRAMEWORK, help="checkout whose skills are counted by name")
    args = parser.parse_args()
    skills = {path.parent.name for path in (args.framework / "skills").glob("*/SKILL.md")}
    since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc) if args.since else None
    print(json.dumps(count(args.projects, skills, since), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

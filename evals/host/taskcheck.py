#!/usr/bin/env python3
"""Check a task file with items before any session is paid for.

    python evals/host/taskcheck.py TASKS --cases CASES [--ids ID,...] [--framework DIR]

CASES maps each task id to worked cases; none of them is ever in a subject's directory:

    {"oracle":   {"answer": ..., "files": {path: text}, "delete": [path]},    every item holds
     "null":     {...},                                                       at most one item holds
     "variants": [{..., "expect": {item id: true|false}}, ...]}               other wordings and near misses

Every item has to hold in two cases at least and fail in one, and doing nothing at all may not get more
than one item either. A negative task's null only has to fail. Snippets run only in sandbox.py's container.
With --framework, wording that the tasks share with the installed rules and skills is listed as well: such
a task would hand the control group the treatment.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grading  # noqa: E402
import impact  # noqa: E402
import sandbox  # noqa: E402
import trigger  # noqa: E402

ITEMS = 5
RESERVED = ("claude.md", "claude.local.md", "agents.md", "gemini.md", ".agf", ".claude", ".agents", ".git", ".mcp.json")
LEAK = 8.0  # eight Chinese characters or five words in a row
TOKEN = re.compile(r"[㐀-鿿]|[a-z0-9_]+")


def unsafe(name: str) -> bool:
    path = PurePosixPath(name)
    return path.is_absolute() or "\\" in name or ".." in path.parts or any(part.lower() in RESERVED for part in path.parts)


def judged(task: dict, case: dict, runner) -> dict[str, bool]:
    with tempfile.TemporaryDirectory(prefix="agf-case-") as folder:
        work = Path(folder)
        impact.materialize(task, work, work)
        start = grading.fingerprint(work)
        for name in case.get("delete", []):
            (work / name).unlink()
        for name, text in case.get("files", {}).items():
            (work / name).parent.mkdir(parents=True, exist_ok=True)
            (work / name).write_text(text, encoding="utf-8")
        found = impact.check(task, work, case.get("answer", ""), work, runner, start)
        if "infrastructure" in found:
            raise SystemExit(f"{task['id']}: {found['infrastructure']}")
        return found["items"]


def check_task(task: dict, cases: dict, runner=sandbox.run) -> list[str]:
    items = task.get("checks", {}).get("items", [])
    try:
        grading.validate(items)
    except ValueError as error:
        return [str(error)]
    variants = cases.get("variants", [])
    paths = [*task.get("files", {})]
    for case in (cases.get("oracle", {}), cases.get("null", {}), *variants):
        paths += [*case.get("files", {}), *case.get("delete", [])]
    if bad := sorted({name for name in paths if unsafe(name)}):
        return [f"paths outside the task or owned by the host: {bad}"]
    if len(items) != ITEMS or not task.get("parts") or "oracle" not in cases or "null" not in cases or len(variants) < 2:
        return [f"needs {ITEMS} items, parts, an oracle, a null and two variants"]
    problems, seen = [], []
    try:
        oracle = judged(task, cases["oracle"], runner)
        seen.append(oracle)
        if not all(oracle.values()):
            problems.append(f"oracle fails {[key for key, value in oracle.items() if not value]}")
        for label, case in (("null", cases["null"]), ("untouched", {})):
            found = judged(task, case, runner)
            seen.append(found)
            right = [key for key, value in found.items() if value]
            if len(right) == ITEMS or (not task.get("negative") and len(right) > 1):
                problems.append(f"{label} gets {right}")
        for number, case in enumerate(variants):
            found = judged(task, case, runner)
            seen.append(found)
            expected = case.get("expect", {})
            if not expected:
                problems.append(f"variant {number} expects nothing")
            problems += [f"variant {number}: {key} is {found.get(key)}, not {value}"
                         for key, value in expected.items() if found.get(key) != value]
    except (re.error, OSError, ValueError) as error:
        return [*problems, f"cannot be judged: {type(error).__name__}: {error}"]
    for item in items:
        values = [found[item["id"]] for found in seen]
        if values.count(True) < 2 or False not in values:
            problems.append(f"{item['id']} needs two cases that pass and one that fails")
    return problems


def leaks(task: dict, rules: dict[str, str]) -> list[str]:
    """Runs of words a task shares with the rules, long enough not to be chance."""
    known = [" " + " ".join(TOKEN.findall(text.lower())) + " " for text in rules.values()]
    found = []
    texts = [part["prompt"] for part in task["parts"]] + list(task.get("files", {}).values()) + list(task.get("files", {}))
    for text in texts:
        words, reached = TOKEN.findall(text.lower()), 0
        for first in range(len(words)):
            last = first
            while last < len(words) and any(f" {' '.join(words[first:last + 1])} " in rule for rule in known):
                last += 1
            run = words[first:last]
            if last > reached and sum(1 if "㐀" <= word[0] <= "鿿" else 1.6 for word in run) >= LEAK - 1e-9:
                found.append(" ".join(run))
                reached = last
    return found


def installed_rules(framework: Path) -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="agf-rules-") as folder:
        work = Path(folder) / "work"
        work.mkdir()
        trigger._install(framework, work, sorted(path.parent.name for path in (framework / "skills").glob("*/SKILL.md")))
        return {file.relative_to(work).as_posix(): file.read_text(encoding="utf-8", errors="replace")
                for file in work.rglob("*") if file.is_file()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--ids")
    parser.add_argument("--framework", type=Path)
    args = parser.parse_args()
    _, tasks = impact.load_tasks(args.tasks)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    chosen = [key for key in (args.ids.split(",") if args.ids else tasks)]
    rules = installed_rules(args.framework.resolve()) if args.framework else {}
    bad = 0
    for name in chosen:
        problems = check_task(tasks[name], cases.get(name, {}))
        problems += [f"shared with the rules: {text}" for text in leaks(tasks[name], rules)] if rules else []
        bad += bool(problems)
        for problem in problems:
            print(f"{name}: {problem}")
    print(f"{len(chosen) - bad} of {len(chosen)} tasks have no problem")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

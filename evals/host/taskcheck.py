#!/usr/bin/env python3
"""Check a task file with items before any session is paid for.

    python evals/host/taskcheck.py TASKS --cases CASES [--ids ID,...] [--framework DIR]

CASES maps each task id to worked cases; none of them is ever in a subject's directory:

    {"oracle":   {"answer": ..., "files": {path: text}, "delete": [path]},    every item holds
     "null":     {...},                                                       at most one item holds
     "variants": [{..., "expect": {item id: true|false}}, ...]}               other wordings and near misses

Every item has to hold in two cases at least and fail in one, some variant has to be right throughout and
some a near miss, and doing nothing at all may not get more than one item either. A negative task's null only has to fail. Snippets run only in sandbox.py's container.
The startup has to be empty. With --framework, wording that the tasks share with the installed rules and
skills is listed, and so are short coaching phrases: such a task would hand the control group the treatment.
Those lists are for a person to read; a short phrase can be chance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
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
LEAK_IN_PROMPT = 6.0  # six and four
COACHING = re.compile(
    r"先[^，。\n]{0,4}(問|確認|釐清)|不要(猜|臆測|亂|自己)|別(猜|亂改|自己)|(不清楚|不確定|有疑問|有問題)[^。\n]{0,6}問"
    r"|只(改|修)必要|最小[^。\n]{0,3}(修改|改動)|(怎麼|如何)驗證|交接|記下來|寫下來|不必(詢)?問|沒跑[^。\n]{0,4}(說|講)"
    r"|不要假|誠實|本次範圍|不推送|不部署|handoff|hand-over|checkpoint|ask me|don't guess|minimal (change|diff)", re.IGNORECASE)
TOKEN = re.compile(r"[㐀-鿿]|[a-z0-9_]+")
QUOTED = re.compile(r"「[^」\n]{2,60}」|『[^』\n]{2,60}』")
ECHO_DEADLINE = 30.0  # seconds for one task
ECHO = 3.0  # of a quoted phrase a pattern has to match, counted as LEAK counts: three Chinese characters or two words


def unsafe(name: str) -> bool:
    path = PurePosixPath(name)
    return path.is_absolute() or "\\" in name or ".." in path.parts or any(part.lower() in RESERVED for part in path.parts)


def judged(task: dict, case: dict, runner, task_dir: Path | None = None) -> dict[str, bool]:
    with tempfile.TemporaryDirectory(prefix="agf-case-") as folder:
        work = Path(folder)
        task_dir = task_dir or work
        impact.materialize(task, task_dir, work)
        start = grading.fingerprint(work)
        for name in case.get("delete", []):
            (work / name).unlink()
        for name, text in case.get("files", {}).items():
            (work / name).parent.mkdir(parents=True, exist_ok=True)
            (work / name).write_text(text, encoding="utf-8")
        found = impact.check(task, work, case.get("answer", ""), task_dir, runner, start)
        if "infrastructure" in found:
            raise ValueError(found["infrastructure"])
        return found["items"]


def check_task(task: dict, cases: dict, runner=sandbox.run, task_dir: Path | None = None) -> list[str]:
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
    expectations = [list(case.get("expect", {}).values()) for case in variants]
    if not any(False in values for values in expectations) or not any(values == [True] * ITEMS for values in expectations):
        problems.append("needs a variant that is right throughout and a near miss")
    try:
        oracle = judged(task, cases["oracle"], runner, task_dir)
        seen.append(oracle)
        if not all(oracle.values()):
            problems.append(f"oracle fails {[key for key, value in oracle.items() if not value]}")
        for label, case in (("null", cases["null"]), ("untouched", {})):
            found = judged(task, case, runner, task_dir)
            seen.append(found)
            right = [key for key, value in found.items() if value]
            if len(right) == ITEMS or (not task.get("negative") and len(right) > 1):
                problems.append(f"{label} gets {right}")
        for number, case in enumerate(variants):
            found = judged(task, case, runner, task_dir)
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
    texts = [(part["prompt"], LEAK_IN_PROMPT) for part in task["parts"]]
    texts += [(text, LEAK) for text in (*task.get("files", {}).values(), *task.get("files", {}))]
    for text, enough in texts:
        words, reached = TOKEN.findall(text.lower()), 0
        for first in range(len(words)):
            last = first
            while last < len(words) and any(f" {' '.join(words[first:last + 1])} " in rule for rule in known):
                last += 1
            run = words[first:last]
            if last > reached and sum(1 if "㐀" <= word[0] <= "鿿" else 1.6 for word in run) >= enough - 1e-9:
                found.append(" ".join(run))
                reached = last
    return found


def _rewarding(item: dict):
    # Patterns that must not match are left out: there the rules quote what not to claim, and the item checks that.
    yield from item.get("answer", [])
    yield from (claim["match"] for claim in item.get("claims", []))
    for option in item.get("one_of", []):
        yield from _rewarding(option)


def _split(pattern: str) -> tuple[list[str], list[str]]:
    """The alternatives at the top of a pattern, and the bodies of its top-level groups (lookarounds left out)."""
    alternatives, groups, depth, in_class, current, body, at = [], [], 0, False, "", "", 0
    while at < len(pattern):
        char = pattern[at]
        step = pattern[at:at + 2] if char == "\\" else char
        at += len(step)
        if in_class:
            in_class = step != "]"
        elif step == "[":
            in_class = True
        elif step == "(":
            depth += 1
            if depth == 1:
                body = ""
                continue
        elif step == ")":
            depth -= 1
            if depth == 0:
                if not body.startswith(("?=", "?!", "?<=", "?<!")):
                    groups.append(re.sub(r"^\?(:|P<\w+>)", "", body))
                current += f"({body})"
                continue
        elif step == "|" and depth == 0:
            alternatives.append(current)
            current = ""
            continue
        if depth >= 1:
            body += step
        else:
            current += step
    return alternatives + [current], groups


def _branches(pattern: str) -> list[str]:
    # A cue inside a group, such as (?:cue|cue)[\s\S]*topic, only shows when that group is tried alone.
    alternatives, groups = _split(pattern)
    if len(alternatives) > 1:
        return alternatives
    return [pattern, *(branch for group in groups for branch in _branches(group))]


def echoes(task: dict, rules: dict[str, str]) -> list[str]:
    """Patterns that give credit for a phrase the rules quote, which only the group with the framework is told to say."""
    quoted = []
    for text in rules.values():
        for found in QUOTED.finditer(text):
            begin = max(0, found.start() - 3)  # room for a word before the quote, such as 回「照建議」
            quoted.append((text[begin:found.end()], found.start() + 1 - begin, found.end() - 1 - begin))
    found = []
    for item in task["checks"]["items"]:
        phrases = []
        for pattern in (branch for whole in _rewarding(item) for branch in _branches(whole)):
            try:
                compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            except re.error:  # a branch that only makes sense with the rest of the pattern
                continue
            for window, start, end in quoted:
                at = 0
                while (hit := compiled.search(window, at)) is not None:
                    shared = TOKEN.findall(window[max(hit.start(), start):min(hit.end(), end)].lower())
                    if sum(1 if "㐀" <= word[0] <= "鿿" else 1.6 for word in shared) >= ECHO - 1e-9 \
                            and window[start:end] not in phrases:
                        phrases.append(window[start:end])
                        break
                    at = hit.start() + 1
                    if at > len(window):
                        break
        found += [f"{item['id']}: {phrase}" for phrase in phrases]
    return found


def echoes_bounded(task: dict, rules: dict[str, str], timeout: float = ECHO_DEADLINE) -> list[str]:
    """echoes() in a child process: a grading pattern can backtrack for ever on the rules' text."""
    try:
        done = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--echoes"],
                              input=json.dumps({"task": task, "rules": rules}).encode("utf-8"), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return [f"the check against the rules' quotes did not finish in {timeout:g} s: a grading pattern may backtrack for ever"]
    if done.returncode != 0:
        return ["the check against the rules' quotes failed: " + done.stderr.decode("utf-8", "replace").strip()[-200:]]
    return json.loads(done.stdout)


def coaching(task: dict) -> list[str]:
    """Short ways to tell a subject how to work, quoted from the rules or not."""
    return [found.group(0) for part in task["parts"] for found in COACHING.finditer(part["prompt"])]


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
    startup, tasks = impact.load_tasks(args.tasks)
    if startup:
        print("startup: has to be empty, every group would get it")
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    chosen = [key for key in (args.ids.split(",") if args.ids else tasks)]
    rules = installed_rules(args.framework.resolve()) if args.framework else {}
    bad = 0
    for name in chosen:
        problems = check_task(tasks[name], cases.get(name, {}), task_dir=args.tasks.resolve().parent)
        if rules:
            problems += [f"shared with the rules: {text}" for text in leaks(tasks[name], rules)]
            problems += [f"coaching: {text}" for text in coaching(tasks[name])]
            problems += [f"grading rewards a phrase the rules quote: {text}" for text in echoes_bounded(tasks[name], rules)]
        bad += bool(problems)
        for problem in problems:
            print(f"{name}: {problem}")
    print(f"{len(chosen) - bad} of {len(chosen)} tasks have no problem")
    return 1 if bad or startup else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--echoes"]:  # the child of echoes_bounded
        given = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        sys.stdout.write(json.dumps(echoes(given["task"], given["rules"]), ensure_ascii=False))
        raise SystemExit(0)
    raise SystemExit(main())

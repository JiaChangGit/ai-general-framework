#!/usr/bin/env python3
"""Measure whether the framework helps a project, and what it costs, in fresh Claude Code sessions.

    python evals/host/impact.py run --framework DIR --base EMPTY_DIR --out DIR --model MODEL
        [--switch-model MODEL] [--ids ID,...] [--runs 2] [--group framework] [--group control]
        [--skill NAME ...] [--hooks SETTINGS_JSON] [--budget USD] [--total-budget USD]
        [--pid-file FILE] [--cli PATH] [--env NAME=VALUE ...] [--allow-env NAME ...] [--forbid PATH ...]
    python evals/host/impact.py report OUT_DIR [OUT_DIR ...] [--md FILE]

Each task in evals/impact/tasks.json is run --runs times in each group. The
framework group gets `project install --host claude` with the chosen skills,
and, with --hooks, a .claude/settings.json built from that file (for example
the continuity hooks); the control group gets the task files only. Two more
groups split the framework's fixed cost: rules-only (the install without
skills) and skills-only (the skills without CLAUDE.md, AGENTS.md and .agf/).
Neither gets the hooks. Each part records first_context_tokens, what the
first model call read, so the groups' fixed cost can be compared directly. A task has
one or more parts: every part is a new session in the same directory, so a part
with max_turns that is cut off, followed by a fresh part, stands for "the usage
limit stopped the session and a new one has to continue". A part with
"model": "switch" runs with --switch-model. The reviewed group installs the whole framework like
"framework", then a fresh session with --review-model gets the request and the
last answer, checks the files itself, fixes them and gives the final answer.

Success is decided by hidden checks that run after the last part and are never
in the subject's directory: Python snippets (with a 20-second limit) or a command
with hidden test files, both only inside sandbox.py's container, regular
expressions over the last answer, or over files the subject wrote. Tokens come
from the CLI's own result event (input, cache creation, cache read, output) and
cost from its estimate; both are summed over the parts.

The run stops before a session would push the total past --total-budget, and
stops on a failed session other than a planned cut-off, instead of spending
more. Group order alternates from task to task. Every run gets a private parent
directory under --base, removed afterwards, and must pass preflight.py first.
Bash is removed (see trigger.py for why); subjects use Read, Grep, Glob, Edit,
Write and Skill inside their own directory only (sandbox.confinement), and, in a
task with "sandbox": {"image", "command"}, one run_tests tool without arguments.

A timeout or an exhausted per-session budget is a failed run. A usage limit, a
Docker failure or any other error stops the experiment, to be finished later.

`report` reads one or more output directories, so a run that a usage limit
stopped can be finished in a second directory and summarised together; it
refuses directories measured with different models, tools, skills, hooks or
task files. A rerun numbers its repeats from 0 again, so the same task and
repeat number can appear once per directory. The table also shows, for tasks
with a planned cut-off, how many first sessions really were cut, and how many
reads went outside the subject's directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preflight  # noqa: E402
import run_claude  # noqa: E402
import sandbox  # noqa: E402
import trigger  # noqa: E402

TOOLS = " ".join(sandbox.SUBJECT_TOOLS)
CONFINEMENT = "s19"  # change it when the subjects' limits change: such runs are not comparable
CHECK_IMAGE = "python:3.12-slim"  # where Python-snippet checks run
TEST_TOOL = "mcp__bench__run_tests"
GROUPS = ("framework", "control", "rules-only", "skills-only", "reviewed")
REVIEW_PROMPT = ("另一位工程師剛完成下面的工作。請獨立核對：讀相關的程式與檔案，不要只相信他的說法；發現錯誤就直接修正檔案。"
                 "最後用你自己的話完整回答原本的問題，或說明完成的結果。\n\n原本的工作：\n{prompt}\n\n他的最後回覆：\n{answer}")
TOKEN_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def original_work(parts: list[dict]) -> str:
    """What the reviewer is told was asked: every part's request, in order."""
    if len(parts) == 1:
        return parts[0]["prompt"]
    return f"（這個工作分成 {len(parts)} 段、依序交代；以下是各段原本的指示）\n\n" + "\n\n".join(
        f"第 {number} 段：\n{part['prompt']}" for number, part in enumerate(parts, 1))


def load_tasks(path: Path) -> tuple[str, dict[str, dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = {task["id"]: task for task in data["tasks"]}
    for task in tasks.values():
        same = task["checks"].get("same_as")
        if same:
            task["checks"] = tasks[same]["checks"]
    return data["startup"], tasks


def _inside(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_dir():
        raise SystemExit(f"not a directory inside the task file's directory: {name}")
    return path


def materialize(task: dict, task_dir: Path, work: Path) -> None:
    """The subject's files: a "source" directory next to the task file, then the inline "files"."""
    if task.get("source"):
        shutil.copytree(_inside(task_dir, task["source"]), work, symlinks=True, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git"))
    for name, text in task.get("files", {}).items():
        (work / name).parent.mkdir(parents=True, exist_ok=True)
        (work / name).write_text(text, encoding="utf-8")


def fingerprint(root: Path, skip: tuple[str, ...] = ()) -> dict[str, str]:
    """Relative path to content hash, without following links."""
    found = {}
    for top, _, names in os.walk(root, followlinks=False):
        for name in names:
            file = Path(top) / name
            relative = file.relative_to(root).as_posix()
            if relative.startswith(skip):
                continue
            if file.is_symlink():
                found[relative] = "link:" + os.readlink(file)
            elif file.is_file():
                found[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
    return found


def setup_hash(task: dict, task_dir: Path, work: Path) -> str:
    """What the subject gets plus the hidden files. The install's manifest and history differ per install."""
    hidden = task["checks"].get("hidden")
    given = [fingerprint(work, (".agf/manifest.json", ".agf/history/")), fingerprint(_inside(task_dir, hidden)) if hidden else {}]
    return hashlib.sha256(json.dumps(given, sort_keys=True).encode()).hexdigest()


def check(task: dict, work: Path, answer: str, task_dir: Path, runner=sandbox.run) -> dict:
    """Run the hidden checks; returns {"passed", "failures"}, or {"infrastructure": reason}.

    The subject's code is never executed here: only `runner` (the container) runs it."""
    checks, failures = task["checks"], []
    image = task.get("sandbox", {}).get("image", CHECK_IMAGE)
    jobs = []
    for index, code in enumerate(checks.get("python", [])):
        # -I plus append: the subject's files never replace the standard library. The mark at the end
        # shows that the whole snippet ran, not that the subject's code ended the process early.
        mark = f"check-finished-{uuid.uuid4().hex}"
        command = "python -I -B -c " + shlex.quote(f"import sys; sys.path.append('.')\n{code}\nprint({mark!r}, flush=True)")
        jobs.append((f"python check {index}", command, 20, None, mark))
    if checks.get("command"):
        hidden = _inside(task_dir, checks["hidden"]) if checks.get("hidden") else None
        jobs.append(("hidden tests", checks["command"], int(checks.get("timeout", 180)), hidden, None))
    for label, command, limit, hidden, mark in jobs:
        try:
            got = runner(work, image, command, limit, hidden)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            return {"infrastructure": f"{label}: {type(error).__name__}"}
        if got["infrastructure"]:
            return {"infrastructure": f"{label}: the container did not run"}
        if got["exit"] != 0:
            reason = "timed out or killed" if got["timed_out"] else got["output"].strip().splitlines()[-1:]
            failures.append(f"{label}: {reason}")
        elif mark and mark not in got["output"]:
            failures.append(f"{label}: the process ended before the check finished")
    for pattern in checks.get("answer_patterns", []):
        if not re.search(pattern, answer or ""):
            failures.append(f"answer lacks /{pattern}/")
    for name, patterns in checks.get("file_patterns", {}).items():
        file = work / name
        if not file.is_file() or not file.resolve().is_relative_to(work.resolve()):
            failures.append(f"missing {name}")
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        failures += [f"{name} lacks /{pattern}/" for pattern in patterns if not re.search(pattern, text)]
    return {"passed": not failures, "failures": failures}


def _install_hooks(framework: Path, work: Path, hooks: Path) -> None:
    """Merge the hooks file into the subject's .claude/settings.json.

    Each `{framework}/<file>` it names is copied into .claude/agf-hooks/ and the
    command points at the copy, so the settings do not show where the framework
    (and its hidden checks) live."""
    text = hooks.read_text(encoding="utf-8")
    folder = work / ".claude" / "agf-hooks"
    for relative in sorted(set(re.findall(r"\{framework\}/([^\s\"']+)", text))):
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(framework / relative, folder / Path(relative).name)
        text = text.replace("{framework}/" + relative, str(folder / Path(relative).name))
    target = work / ".claude" / "settings.json"
    target.parent.mkdir(exist_ok=True)
    settings = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    settings.update(json.loads(text))
    target.write_text(json.dumps(settings, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    framework, out, base = args.framework.resolve(), args.out.resolve(), args.base.resolve()
    task_file = args.tasks.resolve() if args.tasks else framework / "evals/impact/tasks.json"
    startup, tasks = load_tasks(task_file)
    ids = [value for chunk in (args.ids or [",".join(tasks)]) for value in chunk.split(",") if value]
    unknown = [value for value in ids if value not in tasks]
    if unknown:
        raise SystemExit(f"unknown tasks: {unknown}")
    if any(part.get("model") == "switch" for value in ids for part in tasks[value]["parts"]) and not args.switch_model:
        raise SystemExit("a selected task switches model; pass --switch-model")
    if "reviewed" in (args.group or []) and not args.review_model:
        raise SystemExit("the reviewed group needs --review-model")
    skills = args.skill or sorted(path.parent.name for path in (framework / "skills").glob("*/SKILL.md"))
    groups = args.group or ["framework", "control"]
    needed = [tasks[value].get("sandbox", {}).get("image", CHECK_IMAGE) for value in ids
              if tasks[value].get("sandbox") or tasks[value]["checks"].get("python") or tasks[value]["checks"].get("command")]
    if needed and (missing := sandbox.missing_images(needed)):
        raise SystemExit(f"Docker or these images are not available: {missing}; the subjects' code only runs in containers")
    base.mkdir(parents=True, exist_ok=True)
    if any(base.iterdir()):
        raise SystemExit(f"--base must be an empty directory: {base}")
    out.mkdir(parents=True, exist_ok=True)
    cli, env = run_claude.find_cli(args.cli), run_claude._pairs(args.env)
    results = {"framework": str(framework), "framework_commit": trigger._commit(framework), "model": args.model,
               "switch_model": args.switch_model, "review_model": args.review_model, "tools": TOOLS, "confinement": CONFINEMENT, "skills": skills, "hooks": str(args.hooks) if args.hooks else None,
               "tasks_sha256": hashlib.sha256(task_file.read_bytes()).hexdigest(),
               "budget_usd": args.budget, "total_budget_usd": args.total_budget, "spent_usd": 0.0, "runs": [], "stopped": None}
    save = lambda: (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pid_file = args.pid_file.resolve() if args.pid_file else None
    if pid_file:
        pid_file.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
    previous = signal.signal(signal.SIGTERM, trigger._stop_requested)
    try:
        order = 0
        for repeat in range(args.runs):
            for tid in ids:
                task = tasks[tid]
                for group in groups if order % 2 == 0 else list(reversed(groups)):
                    row = run_one(args, framework, base, out, cli, env, startup, task, task_file.parent, group, repeat, skills, results)
                    results["runs"].append(row)
                    save()
                    if row.get("stop"):
                        results["stopped"] = row["stop"]
                        save()
                        return 3
                order += 1
    except trigger.Stopped:
        results["stopped"] = "SIGTERM"
        save()
        return 143
    finally:
        signal.signal(signal.SIGTERM, previous)
        if pid_file:
            trigger._release(pid_file)
    save()
    return 0


def _session(args, out, cli, work, model, prompt, name, results, given, env, expects_tests, extra=(), review=False) -> tuple[dict, dict, str | None]:
    """One session: its record, its result event, and why the experiment has to stop (or None)."""
    stream = out / "streams" / f"{name}.jsonl"
    before = fingerprint(work)
    code = run_claude.run(cli, work, model, prompt, stream, allowed=given["allowed"], disallowed=given["disallowed"],
                          extra=(*extra, *given["extra"]), env=env, budget=args.budget, timeout=args.timeout)
    summary = run_claude.summarize(stream, work)
    result = summary["result"] or {}
    after = fingerprint(work)
    failed = None
    if code == 124:
        failed = "session timed out"
    elif result.get("subtype") == "error_max_budget_usd":
        failed = "session budget exhausted"
    cost = result.get("cost_usd")
    # A killed session reports no cost; charge the most it could have spent.
    estimated = code == 124 and cost is None
    cost = args.budget if estimated else cost
    results["spent_usd"] = round(results["spent_usd"] + (cost or 0), 6)
    planned_cut = bool(extra) and result.get("subtype") == "error_max_turns"
    part = {"model": model, **({"review": True} if review else {}), "exit": code, "subtype": result.get("subtype"),
            "planned_cut": planned_cut, "failed": failed, "turns": result.get("turns"), "cost_usd": cost,
            **({"cost_is_upper_bound": True} if estimated else {}),
            "first_context_tokens": summary.get("first_context_tokens"), "tools_listed": summary.get("tools_listed"),
            **{key: result.get(key) for key in TOKEN_KEYS},
            "skills_used": trigger.measure(summary, None)["skills_used"],
            "tests_run": sum(use["tool"] == TEST_TOOL for use in summary["tool_uses"]),
            "files_changed": sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key)),
            "files_read": [path.replace(str(work), ".") for path in summary["files_read"]],
            "outside_paths": summary["outside_paths"]}
    stop = None
    if expects_tests and summary["tool_names"] is not None and TEST_TOOL not in summary["tool_names"]:
        stop = "infrastructure: the test tool was not available"
    elif any(error["tool"] == TEST_TOOL and re.search(r"exit code: 12[5-7]\b|test tool failed", error["error"]) for error in summary["tool_errors"]):
        stop = "infrastructure: the test container did not run"
    elif not failed and (not result or ((code != 0 or result.get("is_error")) and not planned_cut)):
        # The host's message can carry the account's reset time and time zone; results.json is published.
        said = re.sub(r".*hit your .*limit.*", "usage limit reached", str(result.get("text"))[:200])
        stop = f"exit {code}, {said}"
    return part, result, stop


def run_one(args, framework, base, out, cli, env, startup, task, task_dir, group, repeat, skills, results) -> dict:
    parent = Path(tempfile.mkdtemp(prefix="run-", dir=base))
    row = {"task": task["id"], "kind": task.get("kind"), "group": group, "repeat": repeat, "parts": []}
    try:
        work = parent / "work"
        work.mkdir()
        materialize(task, task_dir, work)
        installed = [] if group in ("control", "rules-only") else skills
        hooked = bool(args.hooks) and group in ("framework", "reviewed")
        if group != "control":
            trigger._install(framework, work, installed)
            if group == "skills-only":
                for name in ("CLAUDE.md", "AGENTS.md"):
                    (work / name).unlink(missing_ok=True)
                shutil.rmtree(work / ".agf", ignore_errors=True)
            if hooked:
                _install_hooks(framework, work, args.hooks.resolve())
        row["setup_sha256"] = setup_hash(task, task_dir, work)
        box = task.get("sandbox", {})
        given = sandbox.confinement(work, box.get("image"), box.get("command"), box.get("timeout", 180),
                                    skills=tuple(installed), hooks=hooked)
        session_env = {**env, **given["env"]}  # last, so --env cannot loosen it
        checked = preflight.check(work, args.forbid, session_env,
                                  set(args.allow_env) | {"CLAUDE_CODE_DISABLE_AUTO_MEMORY"})
        if checked["user_level"]:
            # Under the home directory the host loads ~/.claude as an ancestor, whatever --setting-sources says (S19).
            raise SystemExit(f"--base must be outside the home directory, whose instructions would reach every group: {checked['user_level']}")
        if not checked["ok"]:
            raise SystemExit(f"preflight failed before {task['id']}-{group}: {json.dumps(checked, ensure_ascii=False)}")
        planned = [(str(number), args.switch_model if part.get("model") == "switch" else args.model, part)
                   for number, part in enumerate(task["parts"], 1)]
        if group == "reviewed":
            # D group: a different model checks the finished work, fixes it and gives the final answer;
            # the hidden checks judge what it leaves behind.
            planned.append(("review", args.review_model, {"prompt": original_work(task["parts"]), "review": True}))
        answer, failed = "", None
        for label, model, part in planned:
            where = f"{task['id']}-{group} {label}"
            if results["spent_usd"] + args.budget > args.total_budget:
                row["stop"] = f"total budget: {results['spent_usd']:.2f} spent before {where}, the next session may cost up to {args.budget}"
                return row
            review = bool(part.get("review"))
            prompt = REVIEW_PROMPT.format(prompt=part["prompt"], answer=answer) if review else part["prompt"]
            extra = ("--max-turns", str(part["max_turns"])) if part.get("max_turns") else ()
            print(f"run {task['id']} {group} #{repeat} {'review' if review else 'part ' + label}", flush=True)
            record, result, stop = _session(args, out, cli, work, model, startup + "\n\n" + prompt,
                                            f"{task['id']}-{group}-{repeat}-{label}", results, given, session_env,
                                            bool(box.get("command")), extra, review)
            row["parts"].append(record)
            if stop:
                row["stop"] = f"{where}: {stop}"
                return row
            answer, failed = result.get("text") or "", record["failed"]
            if failed:
                break
        (out / "outputs").mkdir(exist_ok=True)
        (out / "outputs" / f"{task['id']}-{group}-{repeat}.md").write_text(answer + "\n", encoding="utf-8")
        if failed:
            row.update(passed=False, failures=[failed])
        else:
            verdict = check(task, work, answer, task_dir)
            if "infrastructure" in verdict:
                row["stop"] = f"{task['id']}-{group} check: infrastructure: {verdict['infrastructure']}"
                return row
            row.update(verdict)
        row["handoff_files"] = sorted(str(path.relative_to(work)) for pattern in ("*HANDOFF*", "*CHECKPOINT*", ".agf/checkpoints/*")
                                      for path in work.glob(pattern) if path.is_file())
        return row
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def _sum(row: dict, key: str) -> float:
    return sum(part.get(key) or 0 for part in row["parts"])


def summarize_runs(data: dict) -> dict:
    """Per group and per task: pass rate, median and total cost, tokens and turns over completed runs."""
    done = [row for row in data["runs"] if "passed" in row]
    table = {}
    for row in done:
        cell = table.setdefault(row["task"], {}).setdefault(row["group"], {"runs": 0, "passed": 0, "cost": [], "tokens": [], "turns": [], "last_part_tokens": [],
                                                                            "cuts_planned": 0, "cuts_happened": 0, "outside_reads": 0,
                                                                            "first_context": [], "tools_listed": set()})
        cell["runs"] += 1
        cell["passed"] += bool(row["passed"])
        task_parts = [part for part in row["parts"] if not part.get("review")]
        for part in task_parts[:-1]:
            # Every part before the last is meant to be cut off; one that finished early did not test a hand-over.
            cell["cuts_planned"] += 1
            cell["cuts_happened"] += bool(part.get("planned_cut"))
        cell["outside_reads"] += sum(len(part.get("outside_paths") or []) for part in row["parts"])
        cell["tools_listed"].update(part["tools_listed"] for part in row["parts"] if part.get("tools_listed") is not None)
        if row["parts"] and row["parts"][0].get("first_context_tokens") is not None:
            cell["first_context"].append(row["parts"][0]["first_context_tokens"])
        cell["cost"].append(_sum(row, "cost_usd"))
        cell["tokens"].append(sum(_sum(row, key) for key in TOKEN_KEYS))
        cell["turns"].append(_sum(row, "turns"))
        last = task_parts[-1]  # not the review, which would differ per group
        cell["last_part_tokens"].append(sum(last.get(key) or 0 for key in TOKEN_KEYS))
    groups = {}
    for cells in table.values():
        for group, cell in cells.items():
            total = groups.setdefault(group, {"runs": 0, "passed": 0, "cost_usd": 0.0, "tokens": 0})
            total["runs"] += cell["runs"]
            total["passed"] += cell["passed"]
            total["cost_usd"] = round(total["cost_usd"] + sum(cell["cost"]), 4)
            total["tokens"] += int(sum(cell["tokens"]))
    median = lambda values: round(statistics.median(values), 4) if values else None
    tasks = {task: {group: {"passed": f"{cell['passed']}/{cell['runs']}", "median_cost_usd": median(cell["cost"]),
                            "median_tokens": median(cell["tokens"]), "median_turns": median(cell["turns"]),
                            "median_last_part_tokens": median(cell["last_part_tokens"]), "outside_reads": cell["outside_reads"],
                            "median_first_context_tokens": median(cell["first_context"]),
                            # More than one value: a session saw extra tools (say an MCP server that
                            # connected), which changes the context size; compare such cells with care.
                            "tools_listed": sorted(cell["tools_listed"]),
                            **({"cuts": f"{cell['cuts_happened']}/{cell['cuts_planned']}"} if cell["cuts_planned"] else {})}
                    for group, cell in cells.items()} for task, cells in table.items()}
    return {"model": data["model"], "switch_model": data.get("switch_model"), "framework_commit": data["framework_commit"],
            "spent_usd": data["spent_usd"], "stopped": data["stopped"], "groups": groups, "tasks": tasks,
            "incomplete_runs": len(data["runs"]) - len(done)}


SAME_SETUP = ("model", "switch_model", "review_model", "tools", "skills", "hooks", "tasks_sha256")


def combine(named: list[tuple[str, dict]]) -> dict:
    """Merge results.json files of separate runs (for example one finished after a usage limit).

    The runs must share the models, tools, skills, hooks and task file (when the
    files record it); framework commits may differ and are all listed."""
    first_name, first = named[0]
    for name, data in named[1:]:
        if first.get("confinement") != data.get("confinement"):
            raise ValueError(f"confinement differs: {first_name} and {name} did not limit their subjects the same way")
        for key in SAME_SETUP:
            if key in first and key in data and data[key] != first[key]:
                raise ValueError(f"{key} differs: {first_name} has {first[key]!r}, {name} has {data[key]!r}")
    setups = {}
    for name, data in named:
        for row in data["runs"]:
            if row.get("setup_sha256"):
                cell = (row["task"], row["group"])
                if setups.setdefault(cell, row["setup_sha256"]) != row["setup_sha256"]:
                    raise ValueError(f"setup differs for {cell[0]}/{cell[1]} in {name}: files, framework or hidden checks changed")
    commits = sorted({str(data.get("framework_commit")) for _, data in named})
    stopped = [f"{name}: {data['stopped']}" for name, data in named if data.get("stopped")]
    return {"model": first["model"], "switch_model": first.get("switch_model"), "framework_commit": ", ".join(commits),
            "spent_usd": round(sum(data["spent_usd"] for _, data in named), 6),
            "stopped": "; ".join(stopped) or None, "runs": [row for _, data in named for row in data["runs"]]}


def report(args: argparse.Namespace) -> int:
    folders = [out.resolve() for out in args.out]
    if len(set(folders)) != len(folders):
        print("impact report: the same directory was given twice", file=sys.stderr)
        return 2
    try:
        data = combine([(out.name, json.loads((out / "results.json").read_text(encoding="utf-8"))) for out in folders])
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"impact report: {error}", file=sys.stderr)
        return 2
    summary = summarize_runs(data)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    lines = ["| task | group | passed | median cost (USD) | median tokens | median turns | last session tokens | first call context | cut as planned | reads outside |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for task, cells in summary["tasks"].items():
        for group, cell in sorted(cells.items()):
            lines.append(f"| {task} | {group} | {cell['passed']} | {cell['median_cost_usd']} | {cell['median_tokens']} | {cell['median_turns']} "
                         f"| {cell['median_last_part_tokens']} | {cell['median_first_context_tokens']} | {cell.get('cuts', '—')} | {cell['outside_reads']} |")
    target = args.md or (args.out[0] / "report.md" if len(args.out) == 1 else None)
    if target:
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("run")
    one.add_argument("--framework", type=Path, required=True)
    one.add_argument("--base", type=Path, required=True, help="empty directory outside any project")
    one.add_argument("--out", type=Path, required=True)
    one.add_argument("--model", required=True, help="model ID for the subject sessions; there is no default")
    one.add_argument("--switch-model", help="model for parts marked \"model\": \"switch\"")
    one.add_argument("--review-model", help="model that reviews and fixes the finished work in the reviewed group")
    one.add_argument("--tasks", type=Path, help="task file (default: the framework's evals/impact/tasks.json)")
    one.add_argument("--ids", action="append", help="task ids, comma-separated or repeated (default: all)")
    one.add_argument("--runs", type=int, default=2, help="repeats per task and group")
    one.add_argument("--group", action="append", choices=GROUPS)
    one.add_argument("--skill", action="append", help="skills installed in the framework group (default: all)")
    one.add_argument("--hooks", type=Path, help="JSON merged into the framework group's .claude/settings.json")
    one.add_argument("--budget", type=float, default=0.5, help="per-session --max-budget-usd")
    one.add_argument("--total-budget", type=float, default=4.0, help="stop before the total would pass this")
    one.add_argument("--timeout", type=int, default=900)
    one.add_argument("--pid-file", type=Path)
    one.add_argument("--cli")
    one.add_argument("--env", action="append", default=[])
    one.add_argument("--allow-env", action="append", default=[])
    one.add_argument("--forbid", action="append", default=[], help="a path the subject's files must not mention (repeatable)")
    one.set_defaults(func=run)
    two = sub.add_parser("report")
    two.add_argument("out", type=Path, nargs="+", help="one or more --out directories of the same models")
    two.add_argument("--md", type=Path, help="where to write the Markdown table (default: OUT_DIR/report.md for one directory)")
    two.set_defaults(func=report)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

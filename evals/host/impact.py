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
the continuity hooks); the control group gets the task files only. A task has
one or more parts: every part is a new session in the same directory, so a part
with max_turns that is cut off, followed by a fresh part, stands for "the usage
limit stopped the session and a new one has to continue". A part with
"model": "switch" runs with --switch-model.

Success is decided by hidden checks that run after the last part and are never
in the subject's directory: Python snippets (with a 20-second limit), regular
expressions over the last answer, or over files the subject wrote. Tokens come
from the CLI's own result event (input, cache creation, cache read, output) and
cost from its estimate; both are summed over the parts.

The run stops before a session would push the total past --total-budget, and
stops on a failed session other than a planned cut-off, instead of spending
more. Group order alternates from task to task. Every run gets a private parent
directory under --base, removed afterwards, and must pass preflight.py first.
Bash is removed (see trigger.py for why); subjects use Read, Grep, Glob, Edit,
Write and Skill.

`report` reads one or more output directories, so a run that a usage limit
stopped can be finished in a second directory and summarised together; it
refuses directories measured with different models.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preflight  # noqa: E402
import run_claude  # noqa: E402
import trigger  # noqa: E402

TOOLS = "Read Grep Glob Edit Write Skill"
TOKEN_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def load_tasks(path: Path) -> tuple[str, dict[str, dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = {task["id"]: task for task in data["tasks"]}
    for task in tasks.values():
        same = task["checks"].get("same_as")
        if same:
            task["checks"] = tasks[same]["checks"]
    return data["startup"], tasks


def check(task: dict, work: Path, answer: str) -> dict:
    """Run the hidden checks; returns {"passed": bool, "failures": [...]}."""
    failures = []
    for index, code in enumerate(task["checks"].get("python", [])):
        try:
            result = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, '.')\n" + code], cwd=work,
                                    capture_output=True, text=True, timeout=20)
            if result.returncode != 0:
                failures.append(f"python check {index}: {(result.stderr or result.stdout).strip().splitlines()[-1:]}")
        except subprocess.TimeoutExpired:
            failures.append(f"python check {index}: timed out")
    for pattern in task["checks"].get("answer_patterns", []):
        if not re.search(pattern, answer or ""):
            failures.append(f"answer lacks /{pattern}/")
    for name, patterns in task["checks"].get("file_patterns", {}).items():
        file = work / name
        if not file.is_file():
            failures.append(f"missing {name}")
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        failures += [f"{name} lacks /{pattern}/" for pattern in patterns if not re.search(pattern, text)]
    return {"passed": not failures, "failures": failures}


def _install_hooks(framework: Path, work: Path, hooks: Path) -> None:
    """Write the hooks file into the subject's .claude/settings.json; {framework} is replaced by its path."""
    text = hooks.read_text(encoding="utf-8").replace("{framework}", str(framework))
    target = work / ".claude" / "settings.json"
    target.parent.mkdir(exist_ok=True)
    settings = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    settings.update(json.loads(text))
    target.write_text(json.dumps(settings, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    framework, out, base = args.framework.resolve(), args.out.resolve(), args.base.resolve()
    startup, tasks = load_tasks(args.tasks.resolve() if args.tasks else framework / "evals/impact/tasks.json")
    ids = [value for chunk in (args.ids or [",".join(tasks)]) for value in chunk.split(",") if value]
    unknown = [value for value in ids if value not in tasks]
    if unknown:
        raise SystemExit(f"unknown tasks: {unknown}")
    if any(part.get("model") == "switch" for value in ids for part in tasks[value]["parts"]) and not args.switch_model:
        raise SystemExit("a selected task switches model; pass --switch-model")
    skills = args.skill or sorted(path.parent.name for path in (framework / "skills").glob("*/SKILL.md"))
    groups = args.group or ["framework", "control"]
    base.mkdir(parents=True, exist_ok=True)
    if any(base.iterdir()):
        raise SystemExit(f"--base must be an empty directory: {base}")
    out.mkdir(parents=True, exist_ok=True)
    cli, env = run_claude.find_cli(args.cli), run_claude._pairs(args.env)
    results = {"framework": str(framework), "framework_commit": trigger._commit(framework), "model": args.model,
               "switch_model": args.switch_model, "tools": TOOLS, "skills": skills, "hooks": str(args.hooks) if args.hooks else None,
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
                    row = run_one(args, framework, base, out, cli, env, startup, task, group, repeat, skills, results)
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


def run_one(args, framework, base, out, cli, env, startup, task, group, repeat, skills, results) -> dict:
    parent = Path(tempfile.mkdtemp(prefix="run-", dir=base))
    row = {"task": task["id"], "kind": task.get("kind"), "group": group, "repeat": repeat, "parts": []}
    try:
        work = parent / "work"
        work.mkdir()
        for name, text in task["files"].items():
            (work / name).write_text(text, encoding="utf-8")
        if group == "framework":
            trigger._install(framework, work, skills)
            if args.hooks:
                _install_hooks(framework, work, args.hooks.resolve())
        checked = preflight.check(work, args.forbid, env, set(args.allow_env))
        if not checked["ok"]:
            raise SystemExit(f"preflight failed before {task['id']}-{group}: {json.dumps(checked, ensure_ascii=False)}")
        answer = ""
        for number, part in enumerate(task["parts"], 1):
            if results["spent_usd"] + args.budget > args.total_budget:
                row["stop"] = f"total budget: {results['spent_usd']:.2f} spent, the next session may cost up to {args.budget}"
                return row
            model = args.switch_model if part.get("model") == "switch" else args.model
            extra = ("--max-turns", str(part["max_turns"])) if part.get("max_turns") else ()
            stream = out / "streams" / f"{task['id']}-{group}-{repeat}-{number}.jsonl"
            print(f"run {task['id']} {group} #{repeat} part {number}", flush=True)
            code = run_claude.run(cli, work, model, startup + "\n\n" + part["prompt"], stream, allowed=TOOLS,
                                  disallowed=("Bash",), extra=extra, env=env, budget=args.budget, timeout=args.timeout)
            summary = run_claude.summarize(stream, work)
            result = summary["result"] or {}
            results["spent_usd"] = round(results["spent_usd"] + (result.get("cost_usd") or 0), 6)
            planned_cut = part.get("max_turns") and result.get("subtype") == "error_max_turns"
            row["parts"].append({"model": model, "exit": code, "subtype": result.get("subtype"), "planned_cut": bool(planned_cut),
                                 "turns": result.get("turns"), "cost_usd": result.get("cost_usd"),
                                 **{key: result.get(key) for key in TOKEN_KEYS},
                                 "skills_used": trigger.measure(summary, None)["skills_used"],
                                 "files_read": [path.replace(str(work), ".") for path in summary["files_read"]],
                                 "outside_paths": summary["outside_paths"]})
            if not result or ((code != 0 or result.get("is_error")) and not planned_cut):
                row["stop"] = f"{task['id']}-{group} part {number}: exit {code}, {str(result.get('text'))[:200]}"
                return row
            answer = result.get("text") or ""
        (out / "outputs").mkdir(exist_ok=True)
        (out / "outputs" / f"{task['id']}-{group}-{repeat}.md").write_text(answer + "\n", encoding="utf-8")
        row.update(check(task, work, answer))
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
        cell = table.setdefault(row["task"], {}).setdefault(row["group"], {"runs": 0, "passed": 0, "cost": [], "tokens": [], "turns": [], "last_part_tokens": []})
        cell["runs"] += 1
        cell["passed"] += bool(row["passed"])
        cell["cost"].append(_sum(row, "cost_usd"))
        cell["tokens"].append(sum(_sum(row, key) for key in TOKEN_KEYS))
        cell["turns"].append(_sum(row, "turns"))
        last = row["parts"][-1]
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
                            "median_last_part_tokens": median(cell["last_part_tokens"])}
                    for group, cell in cells.items()} for task, cells in table.items()}
    return {"model": data["model"], "switch_model": data.get("switch_model"), "framework_commit": data["framework_commit"],
            "spent_usd": data["spent_usd"], "stopped": data["stopped"], "groups": groups, "tasks": tasks,
            "incomplete_runs": len(data["runs"]) - len(done)}


def combine(datas: list[dict]) -> dict:
    """Merge results.json files of separate runs (for example one finished after a usage limit)."""
    first = datas[0]
    for data in datas[1:]:
        for key in ("model", "switch_model"):
            if data.get(key) != first.get(key):
                raise ValueError(f"{key} differs: {first.get(key)} vs {data.get(key)}")
    commits = sorted({data["framework_commit"] for data in datas})
    stopped = [data["stopped"] for data in datas if data.get("stopped")]
    return {"model": first["model"], "switch_model": first.get("switch_model"),
            "framework_commit": commits[0] if len(commits) == 1 else ", ".join(commits),
            "spent_usd": round(sum(data["spent_usd"] for data in datas), 6),
            "stopped": "; ".join(stopped) or None, "runs": [row for data in datas for row in data["runs"]]}


def report(args: argparse.Namespace) -> int:
    try:
        data = combine([json.loads((out / "results.json").read_text(encoding="utf-8")) for out in args.out])
    except (OSError, ValueError) as error:
        print(f"impact report: {error}", file=sys.stderr)
        return 2
    summary = summarize_runs(data)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    lines = ["| task | group | passed | median cost (USD) | median tokens | median turns | last session tokens |", "|---|---|---|---|---|---|---|"]
    for task, cells in summary["tasks"].items():
        for group, cell in sorted(cells.items()):
            lines.append(f"| {task} | {group} | {cell['passed']} | {cell['median_cost_usd']} | {cell['median_tokens']} | {cell['median_turns']} | {cell['median_last_part_tokens']} |")
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
    one.add_argument("--tasks", type=Path, help="task file (default: the framework's evals/impact/tasks.json)")
    one.add_argument("--ids", action="append", help="task ids, comma-separated or repeated (default: all)")
    one.add_argument("--runs", type=int, default=2, help="repeats per task and group")
    one.add_argument("--group", action="append", choices=("framework", "control"))
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

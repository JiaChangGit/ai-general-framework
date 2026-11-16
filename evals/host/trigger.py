#!/usr/bin/env python3
"""Measure whether skills are used when they should be, and only then, in fresh Claude Code sessions.

    python evals/host/trigger.py run --framework DIR --base EMPTY_DIR --out DIR --ids ID[,ID...]
        [--group framework] [--group control] [--skill NAME ...] [--model MODEL] [--budget USD]
        [--pid-file FILE] [--cli PATH] [--env NAME=VALUE ...] [--forbid PATH ...]
    python evals/host/trigger.py stop --pid-file FILE
    python evals/host/trigger.py report OUT_DIR

Scenarios, materials and the startup text come from the framework checkout's
evals/scenarios.json and evals/paired/tasks.json. Every run gets a private
parent directory under --base, removed afterwards, and must pass preflight.py
before the session starts. Only the framework group gets
`project install --host claude` with the chosen skills. Results come from the
event stream, not from the subject's account of itself: Skill tool calls,
SKILL.md reads, expected hits and misfires (any skill used when none is
expected). A failed session stops the whole run instead of spending more.

Stop a running measurement with `stop`: it checks that the PID in the PID file
belongs to a trigger.py run before sending SIGTERM, and the run keeps the
results it already has. Never stop it with `pkill -f`: the pattern also matches
the shell that runs pkill.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preflight  # noqa: E402
import run_claude  # noqa: E402

TOOLS = "Read Grep Glob Skill"


class Stopped(Exception):
    pass


def _stop_requested(signum, frame):
    raise Stopped()


def _install(framework: Path, work: Path, skills: list[str]) -> None:
    argv = [sys.executable, "-B", str(framework / "scripts/agf.py"), "project", "install", "--target", str(work),
            "--host", "claude", *[part for skill in skills for part in ("--skill", skill)], "--apply"]
    subprocess.run(argv, cwd=work.parent, check=True, stdout=subprocess.DEVNULL)


def measure(summary: dict, expected: str | None) -> dict:
    calls = [str(call).split(":")[-1] for call in summary["skill_calls"]]  # plugin:skill names count as the skill
    used = sorted(set(calls) | {read["skill"] for read in summary["skill_reads"]})
    return {"skill_calls": summary["skill_calls"], "skill_reads": summary["skill_reads"], "skills_used": used,
            "hit": expected in used if expected else None,
            "hit_via_skill_tool": expected in calls if expected else None,
            "misfire": bool(used) if expected is None else None,
            "other_skills": [skill for skill in used if skill != expected]}


def _commit(framework: Path) -> str | None:
    result = subprocess.run(["git", "-C", str(framework), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return result.stdout.strip() or None


def run(args: argparse.Namespace) -> int:
    framework, out, base = args.framework.resolve(), args.out.resolve(), args.base.resolve()
    scenarios = {item["id"]: item for item in json.loads((framework / "evals/scenarios.json").read_text(encoding="utf-8"))["scenarios"]}
    startup = json.loads((framework / "evals/paired/tasks.json").read_text(encoding="utf-8"))["startup"]
    skills = args.skill or sorted(path.parent.name for path in (framework / "skills").glob("*/SKILL.md"))
    ids = [value for chunk in args.ids for value in chunk.split(",") if value]
    unknown = [value for value in ids if value not in scenarios or "materials" not in scenarios[value]]
    if unknown:
        raise SystemExit(f"unknown scenarios or scenarios without materials: {unknown}")
    groups = args.group or ["framework"]
    base.mkdir(parents=True, exist_ok=True)
    if any(base.iterdir()):
        raise SystemExit(f"--base must be an empty directory: {base}")
    out.mkdir(parents=True, exist_ok=True)
    cli, env = run_claude.find_cli(args.cli), run_claude._pairs(args.env)
    results = {"framework": str(framework), "framework_commit": _commit(framework), "model": args.model, "tools": TOOLS,
               "skills": skills, "budget_usd": args.budget, "runs": [], "stopped": False}
    save = lambda: (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pid_file = args.pid_file.resolve() if args.pid_file else None
    if pid_file:
        pid_file.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
    previous = signal.signal(signal.SIGTERM, _stop_requested)
    try:
        for position, sid in enumerate(ids):
            scenario = scenarios[sid]
            # Alternate which group goes first so caching and order do not favour one group.
            for group in groups if position % 2 == 0 else list(reversed(groups)):
                parent = Path(tempfile.mkdtemp(prefix="run-", dir=base))
                try:
                    work = parent / "work"
                    work.mkdir()
                    for name, text in scenario["materials"].items():
                        (work / name).write_text(text, encoding="utf-8")
                    if group == "framework":
                        _install(framework, work, skills)
                    checked = preflight.check(work, args.forbid, env)
                    if not checked["ok"]:
                        raise SystemExit(f"preflight failed before {sid}-{group}: {json.dumps(checked, ensure_ascii=False)}")
                    stream = out / "streams" / f"{sid}-{group}.jsonl"
                    print(f"run {sid} {group}", flush=True)
                    code = run_claude.run(cli, work, args.model, startup + "\n\n" + scenario["request"], stream,
                                          allowed=TOOLS, env=env, budget=args.budget, timeout=args.timeout)
                    summary = run_claude.summarize(stream, work)
                    run_claude.stop_if_failed(f"{sid}-{group}", code, summary)
                    (out / "outputs").mkdir(exist_ok=True)
                    (out / "outputs" / f"{sid}-{group}.md").write_text(((summary["result"] or {}).get("text") or "") + "\n", encoding="utf-8")
                    listed = summary["skills_listed"] or []
                    results["runs"].append({
                        "scenario": sid, "group": group, "expected_skill": scenario["expected_skill_if_available"], "exit": code,
                        "framework_skills_listed": [skill for skill in skills if skill in listed], "skills_listed_count": len(listed),
                        **measure(summary, scenario["expected_skill_if_available"]),
                        "outside_paths": summary["outside_paths"], "denied": summary["denied"], "tool_uses": len(summary["tool_uses"]),
                        "files_read": [path.replace(str(work), ".") for path in summary["files_read"]],
                        **{key: value for key, value in (summary["result"] or {}).items() if key != "text"}})
                    save()
                finally:
                    shutil.rmtree(parent, ignore_errors=True)
    except Stopped:
        results["stopped"] = True
        save()
        return 143
    finally:
        signal.signal(signal.SIGTERM, previous)
        if pid_file:
            pid_file.unlink(missing_ok=True)
    save()
    return 0


def stop(args: argparse.Namespace) -> int:
    pid = json.loads(args.pid_file.read_text(encoding="utf-8"))["pid"]
    cmdline = Path(f"/proc/{pid}/cmdline")
    if not sys.platform.startswith("linux"):
        print("stop checks the process through /proc and only works on Linux; stop the run with the host's own tools")
        return 2
    if not cmdline.exists():
        print(f"no process {pid}; nothing stopped")
        return 1
    argv = cmdline.read_bytes().split(b"\0")
    if not any(part.endswith(b"trigger.py") for part in argv) or b"run" not in argv:
        print(f"process {pid} is not a trigger.py run; nothing stopped")
        return 2
    os.kill(pid, signal.SIGTERM)
    for _ in range(300):
        if not args.pid_file.exists():
            print(f"stopped {pid}")
            return 0
        time.sleep(0.1)
    print(f"sent SIGTERM to {pid}; it has not exited after 30 seconds")
    return 1


def report(args: argparse.Namespace) -> int:
    data = json.loads((args.out / "results.json").read_text(encoding="utf-8"))
    groups = {}
    for row in data["runs"]:
        group = groups.setdefault(row["group"], {"runs": 0, "should_use": 0, "hits": 0, "hits_via_skill_tool": 0,
                                                 "should_not_use": 0, "misfires": 0, "outside_paths": 0, "cost_usd": 0.0, "tokens": 0})
        group["runs"] += 1
        if row["expected_skill"]:
            group["should_use"] += 1
            group["hits"] += bool(row["hit"])
            group["hits_via_skill_tool"] += bool(row["hit_via_skill_tool"])
        else:
            group["should_not_use"] += 1
            group["misfires"] += bool(row["misfire"])
        group["outside_paths"] += len(row["outside_paths"])
        group["cost_usd"] = round(group["cost_usd"] + (row.get("cost_usd") or 0), 6)
        group["tokens"] += sum(row.get(key) or 0 for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
    print(json.dumps({"model": data["model"], "framework_commit": data["framework_commit"], "stopped": data["stopped"], "groups": groups},
                     ensure_ascii=False, indent=1))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("run")
    one.add_argument("--framework", type=Path, required=True, help="framework checkout that provides the scenarios and the install")
    one.add_argument("--base", type=Path, required=True, help="empty directory outside any project; each run gets a private parent here")
    one.add_argument("--out", type=Path, required=True)
    one.add_argument("--ids", action="append", required=True, help="scenario ids, comma-separated or repeated")
    one.add_argument("--group", action="append", choices=("framework", "control"))
    one.add_argument("--skill", action="append", help="skills installed in the framework group (default: every skill in the checkout)")
    one.add_argument("--model", default="claude-sonnet-5-5")
    one.add_argument("--budget", type=float, default=2.0)
    one.add_argument("--timeout", type=int, default=900)
    one.add_argument("--pid-file", type=Path)
    one.add_argument("--cli")
    one.add_argument("--env", action="append", default=[], help="NAME=VALUE passed to every session (repeatable)")
    one.add_argument("--forbid", action="append", default=[], help="a path no file in a run directory may name (repeatable)")
    one.set_defaults(func=run)
    two = sub.add_parser("stop")
    two.add_argument("--pid-file", type=Path, required=True)
    two.set_defaults(func=stop)
    three = sub.add_parser("report")
    three.add_argument("out", type=Path)
    three.set_defaults(func=report)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

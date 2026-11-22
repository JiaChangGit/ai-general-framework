#!/usr/bin/env python3
"""The preregistered stages of S22, with nothing left to choose when they are started. Linux only.

    python3 -B stage.py freeze --cases FILE [--amend REASON]
    python3 -B stage.py run {0b,0c,1,2} --data DIR --base EMPTY_DIR [--tasks FILE] [--ids ID,...] [--dry-run]

DATA holds the framework export (DATA/framework) and receives one directory per attempt (stage-1-01, ...);
a new attempt resumes the earlier ones of its stage. Only 0b may run before the freeze, with --tasks and
--ids; everything 0b ever spent counts into its cap. The freeze has to be committed before a later stage
starts. Stage 2 needs DATA/audit-1.json, written after the blind audit of stage 1:

    {"results": ["stage-1-01", ...], "checked": items read, "wrong": items judged wrongly}
"""
from __future__ import annotations

import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HOST = ROOT / "evals" / "host"
TASKS, FREEZE = HERE / "tasks.json", HERE / "freeze.json"
FRAMEWORK = "6aece63"
VERSION = "2.1.325"
IMAGE = "python:3.12-slim"
HAIKU, OPUS = "claude-haiku-5-5", "claude-opus-5-5"
# model, budget of one session, cap of the stage, repeats, first repeat, seed
STAGES = {"0b": (HAIKU, 0.1, 1.0, 1, 0, 20261123), "0c": (HAIKU, 0.1, 1.0, 2, 0, 20261123),
          "1": (OPUS, 0.8, 15.0, 1, 0, 20261123), "2": (OPUS, 0.8, 13.0, 1, 1, 20261124)}
JOBS, TIMEOUT = 3, 900
OVERSHOOT = 0.25  # of a session's budget, set aside as well
KINDS = {"ask": 2, "handoff": 2, "evidence": 1, "judgement": 1}  # and the negatives of each
AUDIT_LIMIT = 0.10


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output(*argv) -> str:
    return subprocess.run([str(part) for part in argv], capture_output=True, text=True, check=True).stdout


def check_shape(task_file: Path) -> list[dict]:
    data = json.loads(task_file.read_text(encoding="utf-8"))
    tasks = data["tasks"]
    found = Counter((task["kind"], bool(task.get("negative"))) for task in tasks)
    expected = Counter({**{(kind, False): 6 for kind in KINDS}, **{(kind, True): count for kind, count in KINDS.items()}})
    if data.get("startup") or found != expected or len({task["id"] for task in tasks}) != len(tasks):
        raise SystemExit("not the approved set: an empty startup and 24 tasks plus 6 negatives")
    for task in tasks:
        if task.get("source") or task["checks"].get("hidden") or task["checks"].get("command"):
            raise SystemExit(f"{task['id']}: everything a task consists of has to be in the frozen file")
    return tasks


def frozen_files() -> list[Path]:
    return [TASKS, Path(__file__).resolve(),
            *(HOST / f"{name}.py" for name in ("impact", "grading", "judge", "sandbox", "run_claude", "preflight", "trigger"))]


def frozen_state() -> dict:
    return {"framework": FRAMEWORK, "cli_version": VERSION, "jobs": JOBS, "timeout": TIMEOUT, "overshoot": OVERSHOOT,
            "image": output("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}").strip(),
            "stages": {name: list(values) for name, values in STAGES.items()},
            "sha256": {path.relative_to(ROOT).as_posix(): digest(path) for path in frozen_files()}}


def freeze(args: argparse.Namespace) -> int:
    check_shape(TASKS)
    before = json.loads(FREEZE.read_text(encoding="utf-8")) if FREEZE.exists() else None
    if bool(before) != bool(args.amend):
        raise SystemExit("already frozen: --amend REASON" if before else "nothing to amend")
    amendments = []
    if before:
        amendments = [*before.get("amendments", []), {"reason": args.amend, "sha256_before": before["sha256"]}]
    state = {**frozen_state(), "cases_sha256": digest(args.cases.resolve()), "amendments": amendments}
    FREEZE.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")
    return 0


def check_freeze() -> None:
    if not FREEZE.exists():
        raise SystemExit("only the frozen task file may be measured")
    paths = [FREEZE, *frozen_files()]
    if (output("git", "-C", ROOT, "status", "--porcelain", "--untracked-files=all", "--ignored", "--", *paths)
            or not output("git", "-C", ROOT, "ls-files", "--", FREEZE)):
        raise SystemExit("freeze.json and what it names have to be committed")
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    if any(frozen[key] != value for key, value in json.loads(json.dumps(frozen_state())).items()):
        raise SystemExit("the tasks, the harness, the image or the plan differ from freeze.json")


def second_stage_allowed(data: Path, tasks: list[dict], task_sha: str) -> None:
    """Stage 1 finished or at its cap, audited blind, and inconclusive on the audited results."""
    record = data / "audit-1.json"
    if not record.is_file():
        raise SystemExit("stage 2 needs the blind audit of stage 1 first")
    audit = json.loads(record.read_text(encoding="utf-8"))
    folders = [data / name for name in audit["results"]]
    results = [json.loads((folder / "results.json").read_text(encoding="utf-8")) for folder in folders]
    if not audit["checked"] or any(one["tasks_sha256"] != task_sha for one in results):
        raise SystemExit("the audited results are not of the frozen tasks")
    if audit["wrong"] > AUDIT_LIMIT * audit["checked"] and not all(one.get("regraded_from") for one in results):
        raise SystemExit("the audit found the grader wrong: regrade stage 1 and name the regraded results")
    planned = {(task["id"], group, 0) for task in tasks for group in ("framework", "control")}
    done = {(row["task"], row["group"], row["repeat"]) for one in results for row in one["runs"] if "passed" in row}
    if planned - done and not any("total budget" in (one.get("stopped") or "") for one in results):
        raise SystemExit("stage 1 is not finished")
    sys.path.insert(0, str(HOST))
    import judge
    if not judge.judge(judge.load(folders)["runs"])["second_stage"]:
        raise SystemExit("stage 2 only exists when stage 1 is inconclusive")


def run(args: argparse.Namespace) -> int:
    model, budget, cap, runs, first, seed = STAGES[args.stage]
    data, task_file = args.data.resolve(), (args.tasks or TASKS).resolve()
    if args.stage == "0b":
        if FREEZE.exists():
            raise SystemExit("0b only exists before the freeze")
    else:
        if args.tasks or args.ids:
            raise SystemExit("only the whole frozen task file may be measured")
        check_freeze()
    tasks, task_sha = check_shape(task_file), digest(task_file)
    framework = data / "framework"
    if not output("git", "-C", framework, "rev-parse", "HEAD").startswith(FRAMEWORK) or output(
            "git", "-C", framework, "status", "--porcelain", "--untracked-files=all", "--ignored"):
        raise SystemExit(f"{framework} is not a clean {FRAMEWORK}")
    cli = Path.home() / ".local/share/claude/versions" / VERSION
    if not cli.is_file():
        raise SystemExit(f"Claude Code {VERSION} is not installed")
    lock = (data / "stage.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("a stage is running")
    ids = ["--ids", args.ids] if args.ids else []
    if args.stage == "2":
        second_stage_allowed(data, tasks, task_sha)
        ids = ["--ids", ",".join(task["id"] for task in tasks if not task.get("negative"))]
    resume, spent_before = [], 0.0
    for folder in sorted(data.glob(f"stage-{args.stage}-*")):
        if not (folder / "results.json").is_file():
            if folder.is_dir() and any(folder.iterdir()):
                raise SystemExit(f"{folder.name} has no results: what it spent is unknown")
            continue
        earlier = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        if earlier["tasks_sha256"] == task_sha:
            resume.append(folder)
        elif args.stage == "0b":
            spent_before += earlier["spent_usd"] + earlier.get("reserved_usd", 0)  # a task was fixed: nothing to resume
        else:
            raise SystemExit(f"{folder.name} measured another task file")
    number = 1
    while (out := data / f"stage-{args.stage}-{number:02d}").exists():
        number += 1
    command = [sys.executable, "-B", str(HOST / "impact.py"), "run", "--framework", str(framework), "--base", str(args.base.resolve()),
               "--out", str(out), "--tasks", str(task_file), *ids, "--model", model, "--budget", str(budget),
               "--overshoot", str(round(OVERSHOOT * budget, 6)), "--spent-before", str(spent_before),
               "--total-budget", str(cap), "--runs", str(runs), "--first-repeat", str(first), "--seed", str(seed),
               "--jobs", str(JOBS), "--timeout", str(TIMEOUT), "--group", "framework", "--group", "control",
               "--cli", str(cli), "--cli-version", VERSION, "--env", "DISABLE_AUTOUPDATER=1", "--forbid", str(ROOT),
               *(part for folder in resume for part in ("--resume", str(folder)))]
    if args.dry_run:
        print(" ".join(command))
        return 0
    os.set_inheritable(lock.fileno(), True)  # the lock lives as long as the run
    sys.stdout.flush()
    os.execv(command[0], command)  # no parent that a signal could kill alone


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("freeze")
    one.add_argument("--cases", type=Path, required=True, help="the worked cases the tasks were checked with")
    one.add_argument("--amend", help="why the freeze changes; what it was stays recorded")
    one.set_defaults(func=freeze)
    two = sub.add_parser("run")
    two.add_argument("stage", choices=STAGES)
    two.add_argument("--data", type=Path, required=True)
    two.add_argument("--base", type=Path, required=True)
    two.add_argument("--tasks", type=Path)
    two.add_argument("--ids")
    two.add_argument("--dry-run", action="store_true")
    two.set_defaults(func=run)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""The preregistered stages of S22, with nothing left to choose when they are started.

    python3 -B stage.py freeze --cases FILE
    python3 -B stage.py run {0b,0c,1,2} --data DIR --base EMPTY_DIR [--tasks FILE] [--dry-run]

DATA holds the framework export (DATA/framework) and receives one directory per attempt (stage-1-01, ...);
a new attempt resumes the earlier ones of its stage. Only 0b may run before the freeze, with --tasks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HOST = ROOT / "evals" / "host"
TASKS, FREEZE = HERE / "tasks.json", HERE / "freeze.json"
FRAMEWORK = "6aece63"
VERSION = "2.1.325"
HAIKU, OPUS = "claude-haiku-5-5", "claude-opus-5-5"
# model, budget of one session, cap of the stage, repeats, first repeat, seed
STAGES = {"0b": (HAIKU, 0.1, 1.0, 1, 0, 20261123), "0c": (HAIKU, 0.1, 1.0, 2, 0, 20261123),
          "1": (OPUS, 0.8, 15.0, 1, 0, 20261123), "2": (OPUS, 0.8, 13.0, 1, 1, 20261124)}
JOBS, TIMEOUT = 3, 900


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_state() -> dict:
    files = [TASKS, Path(__file__).resolve(), *(HOST / f"{name}.py" for name in
             ("impact", "grading", "judge", "sandbox", "run_claude", "preflight", "trigger"))]
    return {"framework": FRAMEWORK, "cli_version": VERSION, "jobs": JOBS, "timeout": TIMEOUT,
            "stages": {name: list(values) for name, values in STAGES.items()},
            "sha256": {path.relative_to(ROOT).as_posix(): digest(path) for path in files}}


def freeze(args: argparse.Namespace) -> int:
    if FREEZE.exists():
        raise SystemExit("already frozen")
    state = {**frozen_state(), "cases_sha256": digest(args.cases.resolve())}
    FREEZE.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")
    return 0


def run(args: argparse.Namespace) -> int:
    model, budget, cap, runs, first, seed = STAGES[args.stage]
    data, task_file = args.data.resolve(), (args.tasks or TASKS).resolve()
    if args.stage == "0b":
        if FREEZE.exists():
            raise SystemExit("0b only exists before the freeze")
    else:
        if args.tasks or not FREEZE.exists():
            raise SystemExit("only the frozen task file may be measured")
        frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
        if any(frozen[key] != value for key, value in json.loads(json.dumps(frozen_state())).items()):
            raise SystemExit("the tasks, the harness or the plan differ from freeze.json")
    framework = data / "framework"
    head = subprocess.run(["git", "-C", str(framework), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout
    dirty = subprocess.run(["git", "-C", str(framework), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout
    if not head.startswith(FRAMEWORK) or dirty:
        raise SystemExit(f"{framework} is not a clean {FRAMEWORK}")
    cli = Path.home() / ".local/share/claude/versions" / VERSION
    if not cli.is_file():
        raise SystemExit(f"Claude Code {VERSION} is not installed")
    attempts = lambda stage: sorted(path for path in data.glob(f"stage-{stage}-*") if (path / "results.json").is_file())
    ids = []
    if args.stage == "2":
        sys.path.insert(0, str(HOST))
        import judge
        if not (done := attempts("1")):
            raise SystemExit("stage 1 has not run")
        if not judge.judge(judge.load(done)["runs"])["second_stage"]:
            raise SystemExit("stage 2 only exists when stage 1 is inconclusive")
        tasks = json.loads(task_file.read_text(encoding="utf-8"))["tasks"]
        ids = ["--ids", ",".join(task["id"] for task in tasks if not task.get("negative"))]
    earlier = attempts(args.stage)
    number = 1
    while (out := data / f"stage-{args.stage}-{number:02d}").exists():
        number += 1
    command = [sys.executable, "-B", str(HOST / "impact.py"), "run", "--framework", str(framework), "--base", str(args.base.resolve()),
               "--out", str(out), "--tasks", str(task_file), *ids, "--model", model, "--budget", str(budget),
               "--total-budget", str(cap), "--runs", str(runs), "--first-repeat", str(first), "--seed", str(seed),
               "--jobs", str(JOBS), "--timeout", str(TIMEOUT), "--group", "framework", "--group", "control",
               "--cli", str(cli), "--cli-version", VERSION, "--env", "DISABLE_AUTOUPDATER=1", "--forbid", str(ROOT),
               *(part for folder in earlier for part in ("--resume", str(folder)))]
    if args.dry_run:
        print(" ".join(command))
        return 0
    return subprocess.run(command).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("freeze")
    one.add_argument("--cases", type=Path, required=True, help="the worked cases the tasks were checked with")
    one.set_defaults(func=freeze)
    two = sub.add_parser("run")
    two.add_argument("stage", choices=STAGES)
    two.add_argument("--data", type=Path, required=True)
    two.add_argument("--base", type=Path, required=True)
    two.add_argument("--tasks", type=Path)
    two.add_argument("--dry-run", action="store_true")
    two.set_defaults(func=run)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

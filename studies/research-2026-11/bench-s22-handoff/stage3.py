#!/usr/bin/env python3
"""The regression check of the hand-over rule on the other three kinds (S-s22-handoff.md, last section). Linux only.

    python3 -B stage3.py freeze
    python3 -B stage3.py run r1 --data DIR --base EMPTY_DIR [--dry-run]

DATA holds the framework export (DATA/framework: 670adca plus the second change) and receives one
directory per attempt (stage-o1-01, ...); a new attempt resumes the earlier ones of its stage.
"""
from __future__ import annotations

import argparse
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
TASKS, CASES, FREEZE = HERE.parent / "bench-s22" / "tasks.json", HERE.parent / "bench-s22" / "cases.json", HERE / "freeze3.json"
FRAMEWORK = "5977872"  # 6aece63 plus the rule of ecdc4f5 and its second change afe2eff
VERSION, IMAGE = "2.1.325", "python:3.12-slim"
HAIKU, OPUS = "claude-haiku-5-5", "claude-opus-5-5"
OLD = ["handoff-kconfig-gateway", "handoff-orders-api", "handoff-backtest-summary", "handoff-rust-retry",
       "handoff-experiment-plan", "handoff-voice-sheet"]
NEGATIVE = ["neg-ask-irqstat-min", "neg-ask-rename-item", "neg-handoff-node-bump", "neg-handoff-regs-json",
            "neg-evidence-heartbeat", "neg-judgement-refactor"]
NEW = ["handoff-led-states", "handoff-locale-defaults", "handoff-figure-style"]
C, BOTH = ["framework"], ["framework", "control"]
OTHER = ['ask-prune-artifacts', 'ask-backtest-costs', 'ask-firmware-failsafe', 'ask-account-delete', 'ask-rust-sync', 'ask-render-jobs', 'evidence-uart-ring', 'evidence-ci-false-green', 'evidence-session-expiry', 'evidence-rust-panic', 'evidence-backtest-lookahead', 'evidence-probe-defer', 'judgement-tapbuf-review', 'judgement-frame-spec', 'judgement-config-trace', 'judgement-api-review', 'judgement-rust-semver', 'judgement-notes-claims']
# model, budget of one session, cap, repeats, tasks, groups. Only the changed group runs; S22's C is the comparison.
STAGES = {"r1": (OPUS, 0.8, 5.0, 1, OTHER, C)}
SEED, JOBS, TIMEOUT, OVERSHOOT = 20261127, 3, 900, 0.25


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output(*argv) -> str:
    return subprocess.run([str(part) for part in argv], capture_output=True, text=True, check=True).stdout


def frozen_files() -> list[Path]:
    return [TASKS, CASES, Path(__file__).resolve(),
            *(HOST / f"{name}.py" for name in ("impact", "grading", "judge", "sandbox", "run_claude", "preflight", "trigger"))]


def frozen_state() -> dict:
    return {"framework": FRAMEWORK, "cli_version": VERSION, "seed": SEED, "jobs": JOBS, "timeout": TIMEOUT, "overshoot": OVERSHOOT,
            "image": output("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}").strip(),
            "stages": {name: [model, budget, cap, runs, ids, groups] for name, (model, budget, cap, runs, ids, groups) in STAGES.items()},
            "sha256": {path.relative_to(ROOT).as_posix(): digest(path) for path in frozen_files()}}


def run(args: argparse.Namespace) -> int:
    model, budget, cap, runs, ids, groups = STAGES[args.stage]
    data = args.data.resolve()
    paths = [FREEZE, *frozen_files()]
    if not FREEZE.exists() or output("git", "-C", ROOT, "status", "--porcelain", "--untracked-files=all", "--", *paths) \
            or not output("git", "-C", ROOT, "ls-files", "--", FREEZE):
        raise SystemExit("freeze.json and what it names have to be committed")
    if json.loads(FREEZE.read_text(encoding="utf-8")) != json.loads(json.dumps(frozen_state())):
        raise SystemExit("the tasks, the harness, the image or the plan differ from freeze.json")
    framework = data / "framework"
    if not output("git", "-C", framework, "rev-parse", "HEAD").startswith(FRAMEWORK) or output(
            "git", "-C", framework, "status", "--porcelain", "--untracked-files=all", "--ignored"):
        raise SystemExit(f"{framework} is not a clean {FRAMEWORK}")
    cli = Path.home() / ".local/share/claude/versions" / VERSION
    lock = (data / "stage.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("a stage is running")
    resume = [folder for folder in sorted(data.glob(f"stage-{args.stage}-*")) if (folder / "results.json").is_file()]
    spent_before = 0.0
    for other in STAGES:
        if other != args.stage and other[0] == args.stage[0]:
            for folder in data.glob(f"stage-{other}-*"):
                if (folder / "results.json").is_file():
                    earlier = json.loads((folder / "results.json").read_text(encoding="utf-8"))
                    spent_before += earlier["spent_usd"] + earlier.get("reserved_usd", 0)
                elif folder.is_dir() and any(folder.iterdir()):
                    raise SystemExit(f"{folder.name} has no results: what it spent is unknown")
    number = 1
    while (out := data / f"stage-{args.stage}-{number:02d}").exists():
        number += 1
    command = [sys.executable, "-B", str(HOST / "impact.py"), "run", "--framework", str(framework), "--base", str(args.base.resolve()),
               "--out", str(out), "--tasks", str(TASKS), "--ids", ",".join(ids), "--model", model, "--budget", str(budget),
               "--overshoot", str(round(OVERSHOOT * budget, 6)), "--total-budget", str(cap), "--spent-before", str(round(spent_before, 6)), "--runs", str(runs),
               "--seed", str(SEED), "--jobs", str(JOBS), "--timeout", str(TIMEOUT), *(part for group in groups for part in ("--group", group)),
               "--cli", str(cli), "--cli-version", VERSION, "--env", "DISABLE_AUTOUPDATER=1", "--forbid", str(ROOT),
               *(part for folder in resume for part in ("--resume", str(folder)))]
    if args.dry_run:
        print(" ".join(command))
        return 0
    os.set_inheritable(lock.fileno(), True)
    sys.stdout.flush()
    os.execv(command[0], command)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("freeze").set_defaults(func=lambda args: FREEZE.write_text(json.dumps(frozen_state(), indent=1) + "\n", encoding="utf-8") and 0)
    two = sub.add_parser("run")
    two.add_argument("stage", choices=STAGES)
    two.add_argument("--data", type=Path, required=True)
    two.add_argument("--base", type=Path, required=True)
    two.add_argument("--dry-run", action="store_true")
    two.set_defaults(func=run)
    args = parser.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())

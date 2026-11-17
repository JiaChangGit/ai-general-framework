#!/usr/bin/env python3
"""Experiment A (README.md): six framework scenarios, with and without the framework."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import run_session  # noqa: E402

FRAMEWORK = Path("/home/user/src/ai-general-framework")
BASE = Path(os.environ["S8_BASE"]) / "A"          # outside the project tree
LOGS = PROJECT / "artifacts/runs/s8-20261116/A"
SCENARIOS = ["trace-without-lesson", "learning-with-trace", "flaky-repeat-evidence",
             "cleaned-copy-is-not-original", "object-authorization-and-model-output",
             "presentation-priority-and-decision"]
SKILLS = ["trace-code", "debug-root-cause", "guide-learning", "read-research", "review-change"]
MODEL, TOOLS = "claude-sonnet-5-5", "Read Grep Glob Skill"


def prepare(directory: Path, materials: dict, framework: bool) -> None:
    directory.mkdir(parents=True)
    for name, text in materials.items():
        (directory / name).write_text(text, encoding="utf-8")
    if framework:
        argv = [sys.executable, "-B", str(FRAMEWORK / "scripts/agf.py"), "project", "install", "--target", str(directory),
                "--host", "claude", *sum((["--skill", s] for s in SKILLS), []), "--apply"]
        subprocess.run(argv, cwd="/tmp", check=True, stdout=subprocess.DEVNULL)


def main() -> int:
    scenarios = {s["id"]: s for s in json.loads((FRAMEWORK / "evals/scenarios.json").read_text())["scenarios"]}
    startup = json.loads((FRAMEWORK / "evals/paired/tasks.json").read_text())["startup"]
    commit = subprocess.run(["git", "-C", str(FRAMEWORK), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    results = []
    (HERE / "outputs").mkdir(exist_ok=True)
    for position, sid in enumerate(SCENARIOS):
        scenario = scenarios[sid]
        groups = ("control", "framework") if position % 2 == 0 else ("framework", "control")
        for group in groups:
            # Each run gets a parent of its own, removed afterwards: in attempt 1 a session
            # globbed its parent directory and read the other group's files (README).
            BASE.mkdir(parents=True, exist_ok=True)
            parent = Path(tempfile.mkdtemp(prefix="run-", dir=BASE))
            directory = parent / "work"
            prepare(directory, scenario["materials"], group == "framework")
            prompt = startup + "\n\n" + scenario["request"]
            out = LOGS / f"{sid}-{group}.jsonl"
            print(f"run {sid} {group}", flush=True)
            code = run_session.run(directory, MODEL, prompt, TOOLS, out, budget=2.0, timeout=900)
            summary = run_session.summarize(out)
            run_session.stop_if_failed(f"{sid}-{group}", code, summary)
            text = (summary["result"] or {}).get("text") or ""
            (HERE / "outputs" / f"{sid}-{group}.md").write_text(text + "\n", encoding="utf-8")
            listed = summary["skills_listed"] or []
            outside = run_session.outside_paths(summary, directory)
            shutil.rmtree(parent)
            results.append({"scenario": sid, "group": group, "expected_skill": scenario["expected_skill_if_available"],
                            "exit": code, "framework_skills_listed": [s for s in SKILLS if s in listed],
                            "skills_listed_count": len(listed), "skill_calls": summary["skill_calls"],
                            "files_read": [p.replace(str(directory), ".") for p in summary["files_read"]],
                            "outside_paths": outside, "denied": summary["denied"], "tool_uses": len(summary["tool_uses"]),
                            **{k: v for k, v in (summary["result"] or {}).items() if k != "text"}})
            (HERE / "results.json").write_text(json.dumps({"framework_commit": commit, "model": MODEL, "tools": TOOLS,
                                                            "runs": results}, ensure_ascii=False, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

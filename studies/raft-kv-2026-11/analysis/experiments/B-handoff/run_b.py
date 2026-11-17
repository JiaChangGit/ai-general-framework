#!/usr/bin/env python3
"""Experiment B (README.md): take over this project from its handoff, or without it."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import run_session  # noqa: E402

TAG = "s7-zh-style-prototype"
BASE = Path(os.environ["S8_BASE"]) / "B"
LOGS = PROJECT / "artifacts/runs/s8-20261116/B"
RUNS = [("claude-haiku-5-5", "with-handoff"), ("claude-haiku-5-5", "without-handoff"),
        ("claude-sonnet-5-5", "without-handoff"), ("claude-sonnet-5-5", "with-handoff")]
READ_ONLY = ["git status", "git log", "git tag", "git branch", "git show", "git diff",
             ".venv/bin/python scripts/status.py", "uptime", "ps"]
# Attempt 1: CLAUDE.md names the real project by absolute path, and one subject read the real
# handoff there. Reads under /home/user/src (the real project and the framework) and of the
# user's ~/.claude are denied; Read rules also bind Grep and Glob. cat and ls left the list:
# Bash is not bound by Read rules.
DISALLOWED = ("Read(//home/user/src/**)", "Read(//home/user/.claude/**)")
TOOLS = " ".join(["Read", "Grep", "Glob"] + [f"Bash({c}:*)" for c in READ_ONLY] + [f"Bash(rtk {c}:*)" for c in READ_ONLY])
GIT = ["git", "-c", "user.name=experiment", "-c", "user.email=experiment@localhost"]


def clone_project(destination: Path) -> None:
    """This project at TAG, outside the project tree, with what the managed rules need."""
    subprocess.run(["git", "clone", "-q", "--no-local", str(PROJECT), str(destination)], check=True)
    subprocess.run(GIT + ["-C", str(destination), "checkout", "-q", "-b", "experiment", TAG], check=True)
    agf = destination / ".agf"
    agf.mkdir()
    shutil.copy2(PROJECT / ".agf/manifest.json", agf / "manifest.json")
    for name in ("managed", "history"):
        shutil.copytree(PROJECT / ".agf" / name, agf / name)
    (destination / ".venv").symlink_to(PROJECT / ".venv")
    # .gitignore names .venv/ as a directory; a link would show as untracked, which the real project is not.
    with (destination / ".git/info/exclude").open("a") as exclude:
        exclude.write(".venv\n")
    (destination / "artifacts").mkdir()
    (destination / "artifacts/acceptance-final").symlink_to(PROJECT / "artifacts/acceptance-final")


def clone(destination: Path, without_handoff: bool) -> None:
    clone_project(destination)
    if without_handoff:
        subprocess.run(GIT + ["-C", str(destination), "rm", "-q", "docs/HANDOFF_CLAUDE.md"], check=True)
        subprocess.run(GIT + ["-C", str(destination), "commit", "-q", "-m", "Experiment B snapshot"], check=True)
    else:
        subprocess.run(GIT + ["-C", str(destination), "commit", "-q", "--allow-empty", "-m", "Experiment B snapshot"], check=True)


def main() -> int:
    prompt = (HERE / "prompt.txt").read_text(encoding="utf-8").strip()
    results = []
    (HERE / "outputs").mkdir(exist_ok=True)
    for model, condition in RUNS:
        name = f"{model.split('-')[1]}-{condition}"
        directory = BASE / name
        clone(directory, condition == "without-handoff")
        out = LOGS / f"{name}.jsonl"
        print(f"run {name}", flush=True)
        code = run_session.run(directory, model, prompt, TOOLS, out, budget=2.0, timeout=900, disallowed=DISALLOWED)
        summary = run_session.summarize(out)
        run_session.stop_if_failed(name, code, summary)
        text = (summary["result"] or {}).get("text") or ""
        (HERE / "outputs" / f"{name}.md").write_text(text + "\n", encoding="utf-8")
        changed = subprocess.run(["git", "-C", str(directory), "status", "--porcelain"], capture_output=True, text=True).stdout
        results.append({"model": model, "condition": condition, "exit": code, "copy_modified": bool(changed.strip()),
                        "skill_calls": summary["skill_calls"],
                        "files_read": [p.replace(str(directory), ".") for p in summary["files_read"]],
                        "commands": [u["input"] for u in summary["tool_uses"] if u["tool"] == "Bash"],
                        "denied": summary["denied"], "tool_uses": len(summary["tool_uses"]),
                        **{k: v for k, v in (summary["result"] or {}).items() if k != "text"}})
        (HERE / "results.json").write_text(json.dumps({"tag": TAG, "tools": TOOLS, "runs": results}, ensure_ascii=False, indent=1) + "\n")
        shutil.rmtree(directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Experiment C (README.md): is the writing guide read when an entry point names it?"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "B-handoff"))
import run_session  # noqa: E402
import run_b  # noqa: E402  the same project copy

FRAMEWORK = Path("/home/user/src/ai-general-framework")
BASE = Path(os.environ["S8_BASE"]) / "C"
LOGS = PROJECT / "artifacts/runs/s8-20261116/C"
CASES = ["dense-explanation-for-newcomer", "animacy-and-collocation"]
MODEL, TOOLS = "claude-sonnet-5-5", "Read Grep Glob Skill"
LINK = "- 改寫或撰寫中文說明前，先讀 `.agf/managed/guides/writing.md`。\n"
GUIDE, RULES = ".agf/managed/guides/writing.md", ".agf/managed/project-rules.md"


def prepare(directory: Path, entry_link: bool) -> None:
    run_b.clone_project(directory)
    if entry_link:
        path = directory / "CLAUDE.md"
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        first_item = next(i for i, line in enumerate(lines) if line.startswith("- "))
        path.write_text("".join(lines[:first_item] + [LINK] + lines[first_item:]), encoding="utf-8")
        subprocess.run(run_b.GIT + ["-C", str(directory), "commit", "-q", "-am", "Experiment C snapshot"], check=True)
    else:
        subprocess.run(run_b.GIT + ["-C", str(directory), "commit", "-q", "--allow-empty", "-m", "Experiment C snapshot"], check=True)


def main() -> int:
    cases = {c["id"]: c for c in json.loads((FRAMEWORK / "evals/writing-cases.json").read_text())["cases"]}
    results = []
    (HERE / "outputs").mkdir(exist_ok=True)
    for position, cid in enumerate(CASES):
        case = cases[cid]
        conditions = ("as-is", "entry-link") if position == 0 else ("entry-link", "as-is")
        prompt = (case["request"] + "\n\n事實：\n" + "\n".join(f"- {f}" for f in case["facts"]) + "\n\n草稿：\n" + case["draft"]
                  + "\n\n只用純文字回覆改寫後的內容，不要改任何檔案。")
        for condition in conditions:
            name = f"{cid}-{condition}"
            directory = BASE / name
            prepare(directory, condition == "entry-link")
            out = LOGS / f"{name}.jsonl"
            print(f"run {name}", flush=True)
            code = run_session.run(directory, MODEL, prompt, TOOLS, out, budget=2.0, timeout=600)
            summary = run_session.summarize(out)
            run_session.stop_if_failed(name, code, summary)
            text = (summary["result"] or {}).get("text") or ""
            (HERE / "outputs" / f"{name}.md").write_text(text + "\n", encoding="utf-8")
            read = [p.replace(str(directory) + "/", "") for p in summary["files_read"]]
            results.append({"case": cid, "condition": condition, "exit": code, "read_writing_guide": GUIDE in read,
                            "read_project_rules": RULES in read, "files_read": read, "skill_calls": summary["skill_calls"],
                            "denied": summary["denied"], "tool_uses": len(summary["tool_uses"]),
                            **{k: v for k, v in (summary["result"] or {}).items() if k != "text"}})
            (HERE / "results.json").write_text(json.dumps({"model": MODEL, "tools": TOOLS, "runs": results},
                                                            ensure_ascii=False, indent=1) + "\n")
            shutil.rmtree(directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

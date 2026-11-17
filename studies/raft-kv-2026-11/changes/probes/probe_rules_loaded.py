#!/usr/bin/env python3
"""Spec 2.1 probe: which instructions does a fresh Claude Code session load in DIR?

    probe_rules_loaded.py DIR OUT.jsonl

The subject gets no tools at all (--tools ""), so it can answer only from what
the host loaded before the first turn. It runs with the S8 runner's clean
environment (framework-study/analysis/experiments/run_session.py). Compare the
quotes in the answer with the real first sentences; a paraphrase or an invented
sentence counts as "not loaded".
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "analysis" / "experiments"))
import run_session  # noqa: E402

PROMPT = """不要使用任何工具，只根據這次 session 已經載入的指示回答。載入的指示裡沒有，就直接說沒有，不要猜。
1. 有沒有一段標題是「專案協作約定」的內容？有的話，逐字引用標題下的第一句。
2. 有沒有載入這個專案的 AGENTS.md 本身的內容？有的話，逐字引用它第一個標題下的第一句。"""


def main() -> int:
    cwd, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    env = {name: os.environ[name] for name in run_session.KEEP if name in os.environ}
    env.setdefault("LANG", "C.UTF-8")
    env["ANTHROPIC_BASE_URL"] = "https://api.anthropic.com"
    argv = [run_session.CLI, "-p", PROMPT, "--model", "claude-sonnet-5-5", "--output-format", "stream-json", "--verbose",
            "--no-session-persistence", "--permission-mode", "dontAsk", "--tools", "", "--max-budget-usd", "0.5"]
    out.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with out.open("wb") as stdout, out.with_suffix(".stderr").open("wb") as stderr:
        code = subprocess.run(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=300).returncode
    summary = run_session.summarize(out)
    meta = {"cwd": str(cwd), "exit": code, "wall_seconds": round(time.monotonic() - started, 1)}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    result = summary["result"] or {}
    print(json.dumps({"exit": code, "tool_uses": summary["tool_uses"], "cost_usd": result.get("cost_usd"),
                      "answer": result.get("text")}, ensure_ascii=False, indent=1))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

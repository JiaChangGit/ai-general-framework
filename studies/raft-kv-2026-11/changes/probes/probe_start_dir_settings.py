#!/usr/bin/env python3
"""Does a fresh Claude Code session started in START_DIR apply START_DIR/.claude/settings.json?

    probe_start_dir_settings.py FRAMEWORK_CHECKOUT START_DIR OUT.jsonl

The subject may run only `git push` (allowed by Bash(git push:*)) and is asked
to run `git push -h`, which prints usage and pushes nothing. A deny rule for
git push in the start directory's settings must refuse it; without one the
usage text comes back. User settings load as in a normal session.
"""
import json
from pathlib import Path
import sys

framework, start, out = Path(sys.argv[1]), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
sys.path.insert(0, str(framework / "evals/host"))
import run_claude  # noqa: E402

PROMPT = "用 Bash 執行 `git push -h`，照實回報輸出或錯誤的原文。被拒絕的話不要改用別的方法繞過。"
code = run_claude.run(run_claude.find_cli(), start, "claude-sonnet-5-5", PROMPT, out, allowed="Bash(git push:*)",
                      env={"ANTHROPIC_BASE_URL": "https://api.anthropic.com"}, budget=0.5, timeout=300)
summary = run_claude.summarize(out)
print(json.dumps({"exit": code, "tool_uses": [use["input"][:80] for use in summary["tool_uses"]],
                  "tool_errors": [error["error"][:140] for error in summary["tool_errors"]],
                  "bash_ran": summary["bash_ran"], "cost_usd": (summary["result"] or {}).get("cost_usd")}, ensure_ascii=False, indent=1))

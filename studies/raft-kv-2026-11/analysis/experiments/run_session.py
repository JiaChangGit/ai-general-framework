#!/usr/bin/env python3
"""Run one fresh, headless Claude Code session and summarize its event stream.

framework-study/analysis/SPEC.md §3.2. The session starts from a clean
environment: the desktop app's messaging channel and this session's id are
not passed on, so the subject cannot report into the session that runs it.

    run_session.py run --cwd DIR --model MODEL --prompt-file FILE --tools "Read Grep" --out OUT.jsonl
    run_session.py summarize OUT.jsonl

The CLI is the one bundled with the desktop app (override with CLAUDE_CLI).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

CLI = os.environ.get("CLAUDE_CLI", str(Path.home() / ".claude/remote/ccd-cli/2.1.325-1ef04b37a794"))
KEEP = ("HOME", "PATH", "LANG", "TERM")


def run(cwd: Path, model: str, prompt: str, tools: str, out: Path, budget: float, timeout: int,
        disallowed: tuple[str, ...] = ()) -> int:
    env = {name: os.environ[name] for name in KEEP if name in os.environ}
    env.setdefault("LANG", "C.UTF-8")
    env["ANTHROPIC_BASE_URL"] = "https://api.anthropic.com"
    argv = [CLI, "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose",
            "--no-session-persistence", "--permission-mode", "dontAsk", "--allowedTools", tools,
            "--max-budget-usd", str(budget)]
    if disallowed:
        argv += ["--disallowedTools", *disallowed]
    out.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with out.open("wb") as stdout, out.with_suffix(".stderr").open("wb") as stderr:
        try:
            code = subprocess.run(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            code = 124
    meta = {"argv": argv[:2] + ["<prompt>"] + argv[3:], "cwd": str(cwd), "exit": code,
            "wall_seconds": round(time.monotonic() - started, 1)}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    return code


def stop_if_failed(name: str, code: int, summary: dict) -> None:
    """A failed run (for example the plan's usage limit) stops the experiment instead of spending more."""
    result = summary.get("result") or {}
    if code != 0 or not result or result.get("is_error"):
        raise SystemExit(f"stopped after {name}: exit {code}, {str(result.get('text'))[:200]}")


def outside_paths(summary: dict, directory: Path) -> list[str]:
    """Absolute paths in tool inputs that are not inside the run's own directory."""
    found = []
    for use in summary["tool_uses"]:
        try:
            given = json.loads(use["input"])
        except json.JSONDecodeError:
            given = {}
        for key in ("file_path", "path"):
            value = given.get(key) if isinstance(given, dict) else None
            if isinstance(value, str) and value.startswith("/") and not value.startswith(str(directory)):
                found.append(f"{use['tool']} {value}")
    return found


def summarize(path: Path) -> dict:
    summary = {"skills_listed": None, "tools_listed": None, "model": None, "version": None,
               "tool_uses": [], "skill_calls": [], "files_read": [], "denied": [], "result": None}
    pending = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            summary.update(skills_listed=event.get("skills"), tools_listed=len(event.get("tools") or []),
                           model=event.get("model"), version=event.get("claude_code_version"))
        elif kind == "assistant":
            for part in event.get("message", {}).get("content", []):
                if part.get("type") != "tool_use":
                    continue
                name, given = part.get("name"), part.get("input") or {}
                pending[part.get("id")] = name
                summary["tool_uses"].append({"tool": name, "input": json.dumps(given, ensure_ascii=False)[:300]})
                if name == "Skill":
                    summary["skill_calls"].append(given.get("skill") or given.get("name") or given)
                if name == "Read" and given.get("file_path"):
                    summary["files_read"].append(given["file_path"])
        elif kind == "user":
            for part in event.get("message", {}).get("content", []) if isinstance(event.get("message", {}).get("content"), list) else []:
                if part.get("type") == "tool_result" and part.get("is_error"):
                    text = part.get("content")
                    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
                    summary["denied"].append({"tool": pending.get(part.get("tool_use_id")), "error": text[:200]})
        elif kind == "result":
            usage = event.get("usage") or {}
            summary["result"] = {
                "is_error": event.get("is_error"), "subtype": event.get("subtype"), "turns": event.get("num_turns"),
                "duration_ms": event.get("duration_ms"), "cost_usd": event.get("total_cost_usd"),
                "input_tokens": usage.get("input_tokens"), "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens"), "output_tokens": usage.get("output_tokens"),
                "text": event.get("result")}
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("run")
    one.add_argument("--cwd", type=Path, required=True)
    one.add_argument("--model", required=True)
    one.add_argument("--prompt-file", type=Path, required=True)
    one.add_argument("--tools", required=True, help="allowed tools, space-separated as for --allowedTools")
    one.add_argument("--out", type=Path, required=True)
    one.add_argument("--budget", type=float, default=2.0)
    one.add_argument("--timeout", type=int, default=900)
    two = sub.add_parser("summarize")
    two.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        code = run(args.cwd.resolve(), args.model, args.prompt_file.read_text(encoding="utf-8"), args.tools,
                   args.out.resolve(), args.budget, args.timeout)
        print(json.dumps(summarize(args.out.resolve()), ensure_ascii=False, indent=1))
        return code
    print(json.dumps(summarize(args.path), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

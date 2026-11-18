#!/usr/bin/env python3
"""Run one fresh, headless Claude Code session and summarize its event stream.

    python evals/host/run_claude.py run --cwd DIR --model MODEL --prompt-file FILE --out OUT.jsonl
        [--allowed "Read Grep"] [--disallowed RULE ...] [--extra-arg=ARG ...] [--env NAME=VALUE ...]
    python evals/host/run_claude.py summarize OUT.jsonl [--inside DIR]

The session starts from a nearly empty environment: only HOME, PATH, LANG and
TERM (and on Windows a few system variables) are kept, plus any --env value, so
it does not inherit the parent host's messaging channel or session id. The CLI is --cli, else CLAUDE_CLI, else
`claude` on PATH. Model IDs and the CLI version are inputs, not assumptions.
Isolation limits are described in README.md.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

# Windows programs also need these; none of them carries a host channel. Not run on Windows yet.
WINDOWS = ("USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMROOT", "COMSPEC", "PATHEXT", "TEMP", "TMP")
KEEP = ("HOME", "PATH", "LANG", "TERM") + (WINDOWS if os.name == "nt" else ())
PATH_KEYS = ("file_path", "path", "notebook_path")


def find_cli(explicit: str | None = None) -> str:
    cli = explicit or os.environ.get("CLAUDE_CLI") or shutil.which("claude")
    if not cli:
        raise SystemExit("Claude Code CLI not found; pass --cli or set CLAUDE_CLI.")
    return cli


def clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {name: os.environ[name] for name in KEEP if name in os.environ}
    env.setdefault("LANG", "C.UTF-8")
    env.update(extra or {})
    return env


def run(cli: str, cwd: Path, model: str, prompt: str, out: Path, *, allowed: str | None = None,
        disallowed: tuple[str, ...] = (), extra: tuple[str, ...] = (), env: dict[str, str] | None = None,
        budget: float = 2.0, timeout: int = 900) -> int:
    """Run the session in cwd; write OUT.jsonl, OUT.stderr and OUT.meta.json. Returns the exit code (124 on timeout)."""
    argv = [cli, "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose",
            "--no-session-persistence", "--permission-mode", "dontAsk"]
    if allowed is not None:
        argv += ["--allowedTools", allowed]
    # Variadic options are always followed by another flag, and --disallowedTools comes last.
    argv += [*extra, "--max-budget-usd", str(budget)]
    if disallowed:
        argv += ["--disallowedTools", *disallowed]
    out.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with out.open("wb") as stdout, out.with_suffix(".stderr").open("wb") as stderr:
        try:
            code = subprocess.run(argv, cwd=cwd, env=clean_env(env), stdout=stdout, stderr=stderr, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            code = 124
    meta = {"argv": argv[:2] + ["<prompt>"] + argv[3:], "cwd": str(cwd), "exit": code,
            "env_names": sorted(clean_env(env)), "wall_seconds": round(time.monotonic() - started, 1)}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return code


def stop_if_failed(name: str, code: int, summary: dict) -> None:
    """A failed run (for example an exhausted usage limit) stops the experiment instead of spending more."""
    result = summary.get("result") or {}
    if code != 0 or not result or result.get("is_error"):
        raise SystemExit(f"stopped after {name}: exit {code}, {str(result.get('text'))[:200]}")


def _static_prefix(pattern: str) -> str:
    """The leading part of a glob pattern that names a real directory."""
    parts = []
    for part in Path(pattern).parts:
        if any(mark in part for mark in "*?[{"):
            break
        parts.append(part)
    return str(Path(*parts)) if parts else "."


def _paths(tool: str, given: dict) -> list[str]:
    found = [given[key] for key in PATH_KEYS if isinstance(given.get(key), str)]
    if tool == "Glob" and isinstance(given.get("pattern"), str):
        found.append(_static_prefix(given["pattern"]))
    return found


def outside(paths: list[str], inside: Path) -> list[str]:
    """Paths that resolve outside `inside`; relative paths count from `inside`, the session's working directory."""
    base = inside.resolve()
    return [value for value in paths
            if not (Path(value) if Path(value).is_absolute() else base / value).resolve().is_relative_to(base)]


def summarize(path: Path, inside: Path | None = None) -> dict:
    summary = {"skills_listed": None, "tools_listed": None, "model": None, "version": None, "cwd": None, "first_context_tokens": None,
               "tool_uses": [], "skill_calls": [], "skill_reads": [], "files_read": [], "tool_errors": [], "bash_ran": [], "result": None}
    pending, commands = {}, {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            summary.update(skills_listed=event.get("skills"), tools_listed=len(event.get("tools") or []),
                           model=event.get("model"), version=event.get("claude_code_version"), cwd=event.get("cwd"))
        elif kind == "assistant":
            usage = event.get("message", {}).get("usage")
            if summary["first_context_tokens"] is None and isinstance(usage, dict):
                # What the first model call read: system prompt, tools, rules, skill list, prompt.
                summary["first_context_tokens"] = sum(usage.get(key) or 0 for key in
                                                      ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
            for part in event.get("message", {}).get("content", []):
                if part.get("type") != "tool_use":
                    continue
                name, given = part.get("name"), part.get("input") or {}
                pending[part.get("id")] = name
                if name == "Bash":
                    commands[part.get("id")] = str(given.get("command", ""))[:300]
                summary["tool_uses"].append({"tool": name, "input": json.dumps(given, ensure_ascii=False)[:300],
                                             "paths": _paths(name, given)})
                if name == "Skill":
                    summary["skill_calls"].append(str(given.get("skill") or given.get("name") or given))
                if name == "Read" and isinstance(given.get("file_path"), str):
                    summary["files_read"].append(given["file_path"])
                    file = Path(given["file_path"])
                    if file.name == "SKILL.md":
                        summary["skill_reads"].append({"skill": file.parent.name, "copy": file.parent.parent.parent.name + "/" + file.parent.parent.name})
        elif kind == "user":
            content = event.get("message", {}).get("content")
            for part in content if isinstance(content, list) else []:
                if part.get("type") == "tool_result" and not part.get("is_error") and part.get("tool_use_id") in commands:
                    summary["bash_ran"].append(commands[part["tool_use_id"]])  # read-only commands can run without an allow rule
                if part.get("type") == "tool_result" and part.get("is_error"):
                    text = part.get("content")
                    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
                    summary["tool_errors"].append({"tool": pending.get(part.get("tool_use_id")), "error": text[:200]})
        elif kind == "result":
            usage = event.get("usage") or {}
            summary["result"] = {
                "is_error": event.get("is_error"), "subtype": event.get("subtype"), "turns": event.get("num_turns"),
                "duration_ms": event.get("duration_ms"), "cost_usd": event.get("total_cost_usd"),
                "input_tokens": usage.get("input_tokens"), "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens"), "output_tokens": usage.get("output_tokens"),
                "text": event.get("result")}
    if inside is not None:
        summary["outside_paths"] = [f"{use['tool']} {value}" for use in summary["tool_uses"] for value in outside(use["paths"], inside)]
    return summary


def _pairs(values: list[str]) -> dict[str, str]:
    """NAME=VALUE sets a value; a bare NAME copies it from this process's environment,
    so a secret such as an API key never has to appear on a command line."""
    pairs = {}
    for value in values:
        name, separator, text = value.partition("=")
        if not name:
            raise SystemExit(f"--env needs NAME=VALUE or NAME: {value!r}")
        if not separator:
            if name not in os.environ:
                raise SystemExit(f"--env {name}: not set in this environment")
            text = os.environ[name]
        pairs[name] = text
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("run")
    one.add_argument("--cwd", type=Path, required=True)
    one.add_argument("--model", required=True)
    one.add_argument("--prompt-file", type=Path, required=True)
    one.add_argument("--out", type=Path, required=True)
    one.add_argument("--allowed", help="allowed tools, space-separated as for --allowedTools")
    one.add_argument("--disallowed", action="append", default=[], help="a deny rule such as 'Read(//abs/path/**)' (repeatable)")
    one.add_argument("--extra-arg", action="append", default=[], help="another CLI argument, e.g. --extra-arg=--restricted (repeatable)")
    one.add_argument("--env", action="append", default=[], help="NAME=VALUE passed to the session (repeatable)")
    one.add_argument("--cli")
    one.add_argument("--budget", type=float, default=2.0)
    one.add_argument("--timeout", type=int, default=900)
    two = sub.add_parser("summarize")
    two.add_argument("path", type=Path)
    two.add_argument("--inside", type=Path, help="report tool paths outside this directory")
    args = parser.parse_args()
    if args.command == "run":
        cwd, out = args.cwd.resolve(), args.out.resolve()
        code = run(find_cli(args.cli), cwd, args.model, args.prompt_file.read_text(encoding="utf-8"), out,
                   allowed=args.allowed, disallowed=tuple(args.disallowed), extra=tuple(args.extra_arg),
                   env=_pairs(args.env), budget=args.budget, timeout=args.timeout)
        print(json.dumps(summarize(out, cwd), ensure_ascii=False, indent=1))
        return code
    print(json.dumps(summarize(args.path, args.inside), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

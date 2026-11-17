#!/usr/bin/env python3
"""Claude Code PreToolUse hook: refuse a few actions that written rules failed to stop.

Install by adding it to the "PreToolUse" hooks of a settings file (see
templates/claude-guard-settings.example.json). A user-level settings file applies
to every session, wherever it starts; a project's .claude/settings.json applies
only to sessions started in that directory.

It refuses, by exit code 2 with the reason on stderr (Claude Code shows the
reason to the model and does not run the tool):
  - git push in any spelling it can parse: `git -C dir push`, `git --no-pager push`,
    `/usr/bin/git push`, inside `sh -c '...'`, after `cd x &&`, after `env A=1`;
  - creating or merging a pull/merge request with gh or glab, and gh release create;
  - `pkill -f` and `killall`, which also match the shell running the command;
  - writes into protected paths: Edit/Write/NotebookEdit on a protected file, and
    Bash commands whose target is protected (redirection, tee, cp/rsync/install
    destination, mv, rm, touch, mkdir, sed -i, truncate, ln, chmod, chown, dd of=,
    and git -C <protected> with a subcommand that writes).

It cannot see what a program does once it runs: `python3 -c "open(...,'w')"`, a
script that pushes, or a Git alias for push all pass. It is a guard against
mistakes, not a sandbox.

Configuration: JSON at the path given as the first argument, else $AGF_GUARD_CONFIG,
else defaults (block push, PRs and pkill -f; no protected paths):
  {"protected_paths": ["/abs/dir", "~/other"], "block_push": true,
   "block_pull_requests": true, "block_pkill": true}
A configuration that cannot be read refuses every tool call, so a typo does not
silently remove the protection.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

DEFAULTS = {"protected_paths": [], "block_push": True, "block_pull_requests": True, "block_pkill": True}
WRAPPERS = {"sudo", "env", "command", "nohup", "time", "exec", "nice", "stdbuf", "timeout", "xargs", "rtk"}
SHELLS = {"sh", "bash", "zsh", "dash"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
GIT_WRITES = {"add", "am", "apply", "branch", "checkout", "cherry-pick", "clean", "commit", "fetch", "gc", "init",
              "merge", "mv", "pull", "push", "rebase", "reset", "restore", "revert", "rm", "stash", "switch", "tag",
              "update-index", "update-ref", "worktree"}
WRITES_ALL_ARGUMENTS = {"rm", "rmdir", "mv", "touch", "mkdir", "truncate", "chmod", "chown", "shred", "unlink"}
WRITES_LAST_ARGUMENT = {"cp", "rsync", "install", "ln", "scp"}
PULL_REQUESTS = [("gh", "pr", "create"), ("gh", "pr", "merge"), ("gh", "release", "create"),
                 ("glab", "mr", "create"), ("glab", "mr", "merge")]


def load_config(argument: str | None) -> dict:
    path = argument or os.environ.get("AGF_GUARD_CONFIG")
    config = dict(DEFAULTS)
    if path:
        loaded = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("the configuration must be a JSON object")
        unknown = set(loaded) - set(DEFAULTS)
        if unknown:
            raise ValueError(f"unknown keys {sorted(unknown)}")
        config.update(loaded)
    config["protected_paths"] = [Path(p).expanduser().resolve() for p in config["protected_paths"]]
    return config


def protected(path: str, cwd: Path, config: dict) -> Path | None:
    """The protected root that contains `path` (resolved against cwd), if any."""
    if not path or path.startswith("-"):
        return None
    target = (cwd / Path(path).expanduser()).resolve()
    for root in config["protected_paths"]:
        if target == root or root in target.parents:
            return root
    return None


def segments(command: str) -> list[str]:
    """Simple commands of a shell line, split at ; & | && || and newlines outside
    quotes, plus the bodies of $(...) and backticks."""
    parts, current, quote, index = [], [], None, 0
    while index < len(command):
        char = command[index]
        if quote:
            if char == "\\" and quote == '"' and index + 1 < len(command):
                current.append(command[index:index + 2])
                index += 2
                continue
            if char == quote:
                quote = None
            current.append(char)
        elif char in "'\"":
            quote = char
            current.append(char)
        elif char == "\\" and index + 1 < len(command):
            current.append(command[index:index + 2])
            index += 2
            continue
        elif char in ";&|\n":
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
        index += 1
    parts.append("".join(current))
    inner = re.findall(r"\$\(([^()]*)\)", command) + re.findall(r"`([^`]*)`", command)
    return [part for part in parts + [s for body in inner for s in segments(body)] if part.strip()]


def words(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def strip_wrappers(argv: list[str]) -> list[str]:
    while argv:
        name = os.path.basename(argv[0])
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[0]):
            argv = argv[1:]
        elif name in WRAPPERS:
            argv = argv[1:]
            while argv and argv[0].startswith("-"):
                argv = argv[1:]
            if name == "timeout" and argv and re.fullmatch(r"[0-9.]+[smhd]?", argv[0]):
                argv = argv[1:]
        else:
            break
    return argv


def git_subcommand(argv: list[str]) -> tuple[str | None, list[str]]:
    """(subcommand, directories given with -C, --git-dir or --work-tree) for a git argv."""
    directories, index = [], 1
    while index < len(argv):
        token = argv[index]
        if token in GIT_OPTIONS_WITH_VALUE:
            if token in {"-C", "--git-dir", "--work-tree"} and index + 1 < len(argv):
                directories.append(argv[index + 1])
            index += 2
        elif token.startswith("--") and "=" in token:
            if token.startswith(("--git-dir=", "--work-tree=")):
                directories.append(token.split("=", 1)[1])
            index += 1
        elif token.startswith("-"):
            index += 1
        else:
            return token, directories
    return None, directories


def redirection_targets(segment: str) -> list[str]:
    return [m.group(2) for m in re.finditer(r"(?<![0-9&<>])(\d?>>?|&>)\s*([^\s;&|<>]+)", segment)]


def check_bash(command: str, cwd: Path, config: dict, depth: int = 0) -> str | None:
    for segment in segments(command):
        for target in redirection_targets(segment):
            if (root := protected(target.strip("'\""), cwd, config)):
                return f"redirects output into the protected path {root}"
        argv = strip_wrappers(words(segment))
        if not argv:
            continue
        name = os.path.basename(argv[0])
        if name == "cd" and len(argv) > 1:
            cwd = (cwd / Path(argv[1]).expanduser()).resolve()
            continue
        if name in SHELLS and "-c" in argv[1:] and depth < 3:
            position = argv.index("-c") + 1
            if (reason := check_bash(argv[position] if position < len(argv) else "", cwd, config, depth + 1)):
                return reason
            continue
        if name == "git":
            sub, directories = git_subcommand(argv)
            if sub == "push" and config["block_push"]:
                return "runs git push; pushing is left to the user"
            if sub in GIT_WRITES:
                for directory in directories:
                    if (root := protected(directory, cwd, config)):
                        return f"runs git {sub} in the protected repository {root}"
        if config["block_pull_requests"]:
            for pattern in PULL_REQUESTS:
                if [name] + argv[1:len(pattern)] == list(pattern):
                    return f"runs {' '.join(pattern)}; pull requests and releases are left to the user"
        if config["block_pkill"]:
            pattern_flag = any(a == "-f" or (a.startswith("-") and not a.startswith("--") and "f" in a[1:]) for a in argv[1:])
            if name == "killall" or (name == "pkill" and pattern_flag):
                return f"runs {name} with a pattern, which can also match the shell running it; stop processes by PID"
        arguments = [a for a in argv[1:] if not a.startswith("-")]
        if name in WRITES_ALL_ARGUMENTS or name == "tee":
            for argument in arguments:
                if (root := protected(argument, cwd, config)):
                    return f"runs {name} on the protected path {root}"
        if name in WRITES_LAST_ARGUMENT and arguments:
            if (root := protected(arguments[-1], cwd, config)):
                return f"runs {name} into the protected path {root}"
        if name == "sed" and any(a.startswith("-i") or a == "--in-place" for a in argv[1:]):
            for argument in arguments[1:]:
                if (root := protected(argument, cwd, config)):
                    return f"edits the protected path {root} with sed -i"
        if name == "dd":
            for argument in argv[1:]:
                if argument.startswith("of=") and (root := protected(argument[3:], cwd, config)):
                    return f"writes into the protected path {root} with dd"
    return None


def decide(event: dict, config: dict) -> str | None:
    tool = event.get("tool_name", "")
    data = event.get("tool_input") or {}
    cwd = Path(event.get("cwd") or os.getcwd())
    if tool == "Bash":
        return check_bash(str(data.get("command", "")), cwd, config)
    if tool in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
        path = data.get("file_path") or data.get("notebook_path") or ""
        if (root := protected(str(path), cwd, config)):
            return f"uses {tool} on the protected path {root}"
    return None


def main() -> int:
    try:
        config = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    except (OSError, ValueError, TypeError) as error:
        print(f"agf guard: cannot read the configuration ({error}); refusing every tool call until it is fixed", file=sys.stderr)
        return 2
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0  # nothing to judge; Claude Code always sends JSON
    if not isinstance(event, dict):
        return 0
    reason = decide(event, config)
    if reason:
        print(f"agf guard refused this call: it {reason}. Ask the user if this is really needed.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

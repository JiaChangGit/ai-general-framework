#!/usr/bin/env python3
"""Execute a measured subject's code only inside a throwaway Docker container (S19).

    python evals/host/sandbox.py serve --work DIR --image IMAGE --command CMD

`serve` is a stdio MCP server with one tool, `run_tests`, which takes no arguments:
the subject can neither choose the command nor the directory. `run` is also what the
harness uses for hidden checks, so the subject's code never runs on the host.

`confinement` is the other layer: the flags that keep the host's own file tools in
the subject's directory and stop the host from running anything the subject wrote
(hooks, skill shell lines, agent files, git settings).

The container has no network, no capabilities, no new privileges, a read-only root,
an unprivileged user, CPU, memory and process limits, and no environment or files
from the host except snapshots of the given directories, mounted read-only (the
framework's installer writes 0600 files, which the container's user could not read).
The snapshot is copied into a tmpfs before the command runs, so nothing the code writes reaches the
host. The image must already exist (--pull never).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid

OUTPUT_LIMIT = 16000
USER = "65534:65534"  # nobody, so the host user's id is not reused
TOOL = {"name": "run_tests",
        "description": "Run this project's test command on a copy of the current working directory and return the exit code "
                       "and the end of the output. Takes no arguments. No network; changes made by the tests are discarded.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}}


def docker_argv(work: Path, image: str, command: str, name: str, extra: Path | None = None) -> list[str]:
    for path in (work, extra):
        if path is not None and ("," in str(path) or not path.is_dir()):
            raise ValueError(f"not a mountable directory: {path}")
    if image.startswith("-"):
        raise ValueError("image must not be an option")
    mounts = ["--mount", f"type=bind,src={work},dst=/src,readonly"]
    copy = "cp -R /src/. /work/"
    if extra is not None:
        mounts += ["--mount", f"type=bind,src={extra},dst=/hidden,readonly"]
        copy += " && cp -R --remove-destination /hidden/. /work/"  # replaces a subject's file or link at those paths
    # Output stays in the container's tmpfs; only the end of it is copied to the host.
    script = (f"{copy} || exit 125; cd /work; timeout -s KILL \"$LIMIT\" sh -c {shlex.quote(command)} > /out/log 2>&1; code=$?; "
              f"tail -c {OUTPUT_LIMIT} /out/log; [ $code -eq 125 ] && exit 1; exit $code")  # 125 is kept for Docker and the copy
    return ["docker", "run", "--rm", "--name", name, "--pull", "never", "--network", "none", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--read-only", "--user", USER, "--cpus", "2", "--memory", "2g",
            "--memory-swap", "2g", "--pids-limit", "256", "--log-driver", "none",
            "--tmpfs", "/work:rw,exec,size=768m,mode=1777", "--tmpfs", "/tmp:rw,exec,size=256m,mode=1777",
            "--tmpfs", "/out:rw,size=64m,mode=1777", "-e", "HOME=/tmp", "-e", "LIMIT=__LIMIT__",
            *mounts, "--entrypoint", "sh", image, "-c", script]


def _snapshot(source: Path, target: Path) -> Path:
    """A copy the container's user can read, inside a private directory. Links are copied, never followed."""
    shutil.copytree(source, target, symlinks=True)
    target.chmod(0o755)
    for top, folders, names in os.walk(target, followlinks=False):
        for name in folders + names:
            path = Path(top) / name
            if not path.is_symlink():
                path.chmod(0o755 if path.is_dir() or path.stat().st_mode & 0o100 else 0o644)
    return target


def run(work: Path, image: str, command: str, timeout: int = 180, extra: Path | None = None) -> dict:
    """Exit code and the end of the output. `infrastructure` means Docker failed, not the code under test."""
    with tempfile.TemporaryDirectory(prefix="agf-box-") as private:
        copied = _snapshot(Path(work).resolve(), Path(private) / "src")
        hidden = _snapshot(Path(extra).resolve(), Path(private) / "hidden") if extra else None
        return _contained(copied, image, command, timeout, hidden)


def _contained(work: Path, image: str, command: str, timeout: int, extra: Path | None) -> dict:
    name = f"agf-bench-{uuid.uuid4().hex[:12]}"
    argv = [part.replace("LIMIT=__LIMIT__", f"LIMIT={int(timeout)}")
            for part in docker_argv(work, image, command, name, extra)]
    try:
        done = subprocess.run(argv, capture_output=True, timeout=timeout + 60, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=60)
        return {"exit": 124, "output": "timed out", "timed_out": True, "infrastructure": False}
    output = (done.stdout + done.stderr).decode("utf-8", "replace")[-OUTPUT_LIMIT:]
    return {"exit": done.returncode, "output": output, "timed_out": done.returncode in (124, 137),
            "infrastructure": done.returncode == 125}


SUBJECT_TOOLS = ("Read", "Grep", "Glob", "Edit", "Write", "Skill")
# Files the host loads or executes by itself. A deny rule wins over Edit(./**).
HOST_LOADED = (".claude/**", ".git", ".git/**", ".mcp.json", "CLAUDE.md", "CLAUDE.local.md")


def confinement(work: Path, image: str | None = None, command: str | None = None, timeout: int = 180,
                skills: tuple[str, ...] = (), hooks: bool = False) -> dict:
    """Keyword arguments for run_claude.run. Without a command the subject has no test tool."""
    allowed = ["Edit(./**)", *(f"Skill({name})" for name in skills)]
    servers = {}
    if command:
        allowed.append("mcp__bench__run_tests")
        servers["bench"] = {"command": sys.executable,
                            "args": ["-I", "-B", str(Path(__file__).resolve()), "serve", "--work", str(work),
                                     "--image", image, "--command", command, "--timeout", str(int(timeout))]}
    denied = [f"Edit({start}{name})" for name in HOST_LOADED for start in ("./", "./**/")]
    settings = {"disableAllHooks": not hooks, "disableSkillShellExecution": True}
    extra = ("--tools", ",".join(SUBJECT_TOOLS), "--setting-sources", "project", "--settings", json.dumps(settings),
             "--strict-mcp-config", "--mcp-config", json.dumps({"mcpServers": servers}))
    env = {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1", "GIT_CONFIG_COUNT": "3",
           "GIT_CONFIG_KEY_0": "safe.bareRepository", "GIT_CONFIG_VALUE_0": "explicit",
           "GIT_CONFIG_KEY_1": "core.fsmonitor", "GIT_CONFIG_VALUE_1": "false",
           "GIT_CONFIG_KEY_2": "core.hooksPath", "GIT_CONFIG_VALUE_2": os.devnull}
    return {"allowed": " ".join(allowed), "disallowed": ("Bash", "WebFetch", "WebSearch", *denied), "extra": extra, "env": env}


def missing_images(images) -> list[str]:
    """Images that cannot be used now (no Docker, no daemon or no such image)."""
    docker, missing = shutil.which("docker"), []
    for image in sorted(set(images)):
        try:
            found = bool(docker) and not image.startswith("-") and subprocess.run(
                [docker, "image", "inspect", image], capture_output=True, timeout=60).returncode == 0
        except (OSError, subprocess.SubprocessError):
            found = False
        if not found:
            missing.append(image)
    return missing


def answer(message, work: Path, image: str, command: str, timeout: int) -> dict | None:
    if not isinstance(message, dict) or "id" not in message:
        return None  # a notification
    reply = {"jsonrpc": "2.0", "id": message["id"]}
    method, params = message.get("method"), message.get("params") if isinstance(message.get("params"), dict) else {}
    if method == "initialize":
        reply["result"] = {"protocolVersion": params.get("protocolVersion", "2025-06-18"), "capabilities": {"tools": {}},
                           "serverInfo": {"name": "bench", "version": "1"}}
    elif method == "ping":
        reply["result"] = {}
    elif method == "tools/list":
        reply["result"] = {"tools": [TOOL]}
    elif method == "tools/call":
        if params.get("name") != TOOL["name"] or params.get("arguments"):
            reply["result"] = {"isError": True, "content": [{"type": "text", "text": "Only run_tests, without arguments, is available."}]}
        else:
            try:
                got = run(work, image, command, timeout)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                got = {"exit": None, "output": f"the test tool failed: {type(error).__name__}", "infrastructure": True}
            reply["result"] = {"isError": bool(got.get("infrastructure")),
                               "content": [{"type": "text", "text": f"exit code: {got['exit']}\n{got['output']}"}]}
    else:
        reply["error"] = {"code": -32601, "message": "method not found"}
    return reply


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    one = parser.add_subparsers(dest="mode", required=True).add_parser("serve")
    one.add_argument("--work", type=Path, required=True)
    one.add_argument("--image", required=True)
    one.add_argument("--command", required=True)
    one.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    work = args.work.resolve()
    for line in sys.stdin.buffer:
        try:
            message = json.loads(line)
        except ValueError:
            continue
        reply = answer(message, work, args.image, args.command, args.timeout)
        if reply is not None:
            sys.stdout.buffer.write((json.dumps(reply, ensure_ascii=False) + "\n").encode("utf-8"))
            sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

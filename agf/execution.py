"""Bounded command evidence, with no shell command-string interpretation."""

from __future__ import annotations

import argparse
import codecs
from contextlib import ExitStack
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

from .common import AgfError, json_text, read_json, within


def _validate_options(timeout, max_chars, encoding, max_output_bytes=None):
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise AgfError("Timeout must be a finite positive number.")
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or max_chars < 1:
        raise AgfError("Output limit must be a positive integer.")
    if max_output_bytes is not None and (type(max_output_bytes) is not int or max_output_bytes < 1):
        raise AgfError("Raw output byte limit must be a positive integer.")
    try:
        codecs.lookup(encoding)
    except (LookupError, TypeError) as exc:
        raise AgfError(f"Unknown output encoding: {encoding!r}") from exc
    try:
        # lookup() also accepts byte transforms (hex/base64) and str transforms
        # (rot_13). Reject them before a command can produce side effects.
        b"".decode(encoding)
        for errors in ("strict", "replace"):
            decoder = codecs.getincrementaldecoder(encoding)(errors=errors)
            if not isinstance(decoder.decode(b"", final=False), str):
                raise TypeError("Decoder must return text")
    except (LookupError, TypeError, ValueError) as exc:
        raise AgfError(f"Output encoding must support bytes-to-text decoding with strict and replacement handling: {encoding!r}") from exc


def _validate_argv(argv):
    if not isinstance(argv, (list, tuple)) or not argv or not all(isinstance(item, str) and item and "\x00" not in item for item in argv):
        raise AgfError("Command must be a nonempty argument list, without NUL characters.")


def _terminate(process):
    if os.name == "nt":
        if process.poll() is not None:
            return "parent_exited_descendants_unknown"
        killer = shutil.which("taskkill.exe")
        cleanup = "parent_only"
        if killer:
            try:
                killed = subprocess.run([killer, "/PID", str(process.pid), "/T", "/F"],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                if killed.returncode == 0:
                    cleanup = "tree_termination_requested"
            except (OSError, subprocess.TimeoutExpired):
                pass  # Still terminate the parent; do not claim tree cleanup.
        if process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            cleanup = "process_group_terminated"
        except ProcessLookupError:
            cleanup = "already_exited"
    process.wait(timeout=10)
    return cleanup


def _capture_bounded(process, stdout, stderr, limit, timeout):
    """Drain both pipes; never spool more than the shared byte budget."""
    lock = threading.Lock()
    stop = threading.Event()
    exceeded = threading.Event()
    errors = []
    total = 0

    def capture(pipe, destination):
        nonlocal total
        try:
            while chunk := pipe.read1(65536):
                with lock:
                    if stop.is_set():
                        break
                    size = min(len(chunk), limit - total)
                    if size and destination.write(chunk[:size]) != size:
                        raise OSError("Incomplete capture write")
                    total += size
                    if size < len(chunk):
                        exceeded.set()
                        break
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
        finally:
            pipe.close()

    threads = [threading.Thread(target=capture, args=pair, daemon=True)
               for pair in ((process.stdout, stdout), (process.stderr, stderr))]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    cleanup = "not_needed"
    while process.poll() is None or any(thread.is_alive() for thread in threads):
        if exceeded.is_set() or errors:
            break
        if time.monotonic() >= deadline:
            timed_out = True
            break
        time.sleep(0.01)
    if exceeded.is_set() or errors or timed_out:
        cleanup = _terminate(process)
    with lock:
        stop.set()
    for thread in threads:
        thread.join(timeout=0.5)
    if any(thread.is_alive() for thread in threads):
        errors.append("Capture pipe remains open; a descendant may still hold it")
    state = {"max_output_bytes": limit, "output_limit_exceeded": exceeded.is_set(),
             "capture_complete": not (exceeded.is_set() or errors or timed_out),
             "process_exit_code": process.returncode}
    if errors:
        state["capture_error"] = "; ".join(errors)
    return timed_out, cleanup, state


def run_command(argv, *, cwd=None, timeout=60, max_chars=16000, encoding="utf-8", output_dir=None, max_output_bytes=None):
    _validate_argv(argv)
    _validate_options(timeout, max_chars, encoding, max_output_bytes)
    directory = Path(cwd or Path.cwd()).resolve()
    if not directory.is_dir():
        raise AgfError(f"Working directory does not exist: {directory}")
    executable = shutil.which(argv[0])
    if executable is None:
        candidate = Path(argv[0])
        if not candidate.is_absolute():
            candidate = directory / candidate
        executable = str(candidate.resolve()) if candidate.is_file() else None
    if not executable:
        raise AgfError(f"Executable not found: {argv[0]}")
    if Path(executable).suffix.lower() in {".cmd", ".bat"}:
        raise AgfError("Batch shims require a tool-specific adapter. Pass the real executable (for example node.exe and a JS entrypoint).")
    command = [executable, *argv[1:]]
    started = time.monotonic()
    timed_out = False
    cleanup = "not_needed"
    with ExitStack() as stack:
        metadata = None
        if output_dir is None:
            stdout = stack.enter_context(tempfile.TemporaryFile())
            stderr = stack.enter_context(tempfile.TemporaryFile())
        else:
            # Reserve every destination before starting the supplied command.
            # absolute(), unlike resolve(), does not follow an existing final symlink.
            evidence_dir = Path(output_dir).absolute()
            try:
                evidence_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
                stdout = stack.enter_context((evidence_dir / "stdout.bin").open("x+b"))
                stderr = stack.enter_context((evidence_dir / "stderr.bin").open("x+b"))
                metadata = stack.enter_context((evidence_dir / "result.json").open("xb", buffering=0))
            except OSError as exc:
                raise AgfError(f"Cannot prepare a new output directory {evidence_dir}; command was not started: {exc}") from exc
        options = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        try:
            process = subprocess.Popen(command, cwd=directory, stdin=subprocess.DEVNULL,
                                       stdout=stdout if max_output_bytes is None else subprocess.PIPE,
                                       stderr=stderr if max_output_bytes is None else subprocess.PIPE, shell=False, **options)
        except OSError as exc:
            raise AgfError(f"Cannot start command: {exc}") from exc
        capture_state = {}
        if max_output_bytes is None:
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                cleanup = _terminate(process)
        else:
            timed_out, cleanup, capture_state = _capture_bounded(process, stdout, stderr, max_output_bytes, timeout)
        failed_capture = capture_state and not capture_state["capture_complete"]
        result = {"argv": argv, "cwd": str(directory), "exit_code": 124 if timed_out else 125 if failed_capture else process.returncode,
                  "timed_out": timed_out, "cleanup": cleanup, "duration_seconds": round(time.monotonic() - started, 3)}
        result.update(capture_state)
        for name, stream in (("stdout", stdout), ("stderr", stderr)):
            count = stream.tell()
            stream.seek(0)
            # Bounded read even for an extremely verbose child process.
            raw = stream.read(max_chars * 4 + 4)
            final = count <= len(raw) and not failed_capture
            try:
                decoder = codecs.getincrementaldecoder(encoding)(errors="strict")
                decoded = decoder.decode(raw, final=final)
                decode_errors = False
            except UnicodeDecodeError:
                decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
                decoded = decoder.decode(raw, final=final)
                decode_errors = True
            result[name] = decoded[:max_chars]
            result[name + "_bytes"] = count
            result[name + "_truncated"] = bool(failed_capture) or count > max_chars * 4 + 4 or len(decoded) > max_chars
            result[name + "_decode_errors"] = decode_errors
        result["encoding"] = encoding
        result["status"] = "PASS" if result["exit_code"] == 0 else "FAIL"
        if metadata is not None:
            result["evidence"] = {"directory": str(evidence_dir),
                                  "stdout": str(evidence_dir / "stdout.bin"),
                                  "stderr": str(evidence_dir / "stderr.bin"),
                                  "result": str(evidence_dir / "result.json"),
                                  "metadata_saved": True,
                                  "meaning": "Captured raw bytes; may be incomplete when capture_complete is false. No redaction. Command exit status is independent of evidence saving."}
            try:
                encoded = json_text(result).encode("utf-8")
                if metadata.write(encoded) != len(encoded):
                    raise OSError("Incomplete metadata write")
            except (OSError, UnicodeError) as exc:
                result["evidence"]["metadata_saved"] = False
                result["evidence"]["error"] = f"Command already ran; metadata could not be fully saved: {exc}. Do not rerun it solely to recover output."
    return result


def validate_checks(root, config, profile="quick"):
    """Select and validate checks without starting commands or creating files."""
    directory = Path(root).resolve()
    if not directory.is_dir():
        raise AgfError(f"Working directory does not exist: {directory}")
    data = read_json(config)
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1 or not isinstance(data.get("checks"), list):
        raise AgfError("Quality config requires version: 1 and a checks array.")
    selected = []
    for check in data["checks"]:
        if not isinstance(check, dict) or not isinstance(check.get("name"), str) or not check["name"].strip():
            raise AgfError("Each check requires a nonempty name and an argv array.")
        profiles = check.get("profiles", ["quick", "full"])
        if not isinstance(profiles, list) or not all(isinstance(item, str) and item.strip() for item in profiles):
            raise AgfError("Check profiles must be an array of strings.")
        if profile not in profiles:
            continue
        argv = check.get("argv")
        if not isinstance(argv, list):
            raise AgfError(f"Invalid argv for {check['name']}")
        _validate_argv(argv)
        argv = [sys.executable if item == "{python}" else item for item in argv]
        cwd = check.get("cwd", ".")
        if not isinstance(cwd, str) or not cwd or "\x00" in cwd:
            raise AgfError(f"Invalid cwd for {check['name']}")
        _validate_options(check.get("timeout", 60), 16000, check.get("encoding", "utf-8"), check.get("max_output_bytes"))
        location = within(directory, directory / cwd)
        if not location.is_dir():
            raise AgfError(f"Working directory does not exist for {check['name']}: {location}")
        selected.append((check, argv, location))
    if not selected:
        raise AgfError(f"No checks selected for {profile}; an empty gate cannot pass.")
    return selected


def check_project(root, config, profile="quick"):
    selected = validate_checks(root, config, profile)
    results = []
    for check, argv, location in selected:
        value = run_command(argv, cwd=location, timeout=check.get("timeout", 60), encoding=check.get("encoding", "utf-8"),
                            max_output_bytes=check.get("max_output_bytes"))
        value["name"] = check["name"]
        results.append(value)
    passed = all(item["status"] == "PASS" for item in results)
    return {"status": "PASS" if passed else "FAIL", "profile": profile, "checks": results,
            "meaning": "Configured commands completed; this does not prove functional or human learning outcomes.",
            "_exit_code": 0 if passed else 1}


def register(subparsers):
    run = subparsers.add_parser("run", help="Execute an explicitly supplied argv and return bounded evidence")
    run.add_argument("--cwd", default=".")
    run.add_argument("--timeout", type=float, default=60)
    run.add_argument("--max-chars", type=int, default=16000)
    run.add_argument("--max-output-bytes", type=int, help="Combined stdout/stderr capture budget; exceeding it stops the command and fails")
    run.add_argument("--encoding", default="utf-8", help="Actual child output encoding; decoding errors are reported")
    run.add_argument("--output-dir", help="New directory for raw stdout/stderr and result JSON; relative to the invoking directory")
    run.add_argument("argv", nargs=argparse.REMAINDER)
    def execute(args):
        argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
        result = run_command(argv, cwd=args.cwd, timeout=args.timeout, max_chars=args.max_chars, encoding=args.encoding,
                             output_dir=args.output_dir, max_output_bytes=args.max_output_bytes)
        result["_exit_code"] = 0 if result["status"] == "PASS" else 1
        return result
    run.set_defaults(func=execute)
    check = subparsers.add_parser("check", help="Run configured project checks; empty gates fail")
    check.add_argument("--root", default=".")
    check.add_argument("--config", required=True)
    check.add_argument("--profile", choices=["quick", "full"], default="quick")
    check.set_defaults(func=lambda args: check_project(args.root, args.config, args.profile))

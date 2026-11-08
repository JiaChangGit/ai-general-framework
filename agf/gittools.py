"""Inspect Git through Git itself. Scope reports are not write protection."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .common import AgfError
from .execution import run_command


def git(repo, *arguments, accepted=(0,), max_chars=16000):
    result = run_command(["git", "-C", str(Path(repo).resolve()), *arguments], timeout=30, max_chars=max_chars)
    if result["exit_code"] not in accepted:
        raise AgfError(f"git {' '.join(arguments[:2])}: {result['stderr'].strip()}")
    return result


def snapshot(repo, exclude_paths=()):
    for path in exclude_paths:
        if not isinstance(path, str) or path.startswith("/") or ":" in path or ".." in path.split("/"):
            raise AgfError("Snapshot exclusions must be repository-relative paths.")
    pathspec = ["--", ".", *[f":(exclude,literal){path}" for path in exclude_paths]] if exclude_paths else []
    head = git(repo, "rev-parse", "--verify", "HEAD", accepted=(0, 128))
    status = git(repo, "status", "--porcelain=v1", "-z", *pathspec, max_chars=1000000)
    unstaged = git(repo, "diff", "--binary", "--no-ext-diff", "--no-textconv", *pathspec, max_chars=4000000)
    staged = git(repo, "diff", "--cached", "--binary", "--no-ext-diff", "--no-textconv", *pathspec, max_chars=4000000)
    if any(item["stdout_truncated"] for item in (status, unstaged, staged)):
        raise AgfError("Git state exceeds capture limit; use explicit evidence files and a smaller task scope.")
    if any(item["stdout_decode_errors"] for item in (head, status, unstaged, staged)):
        raise AgfError("Cannot reliably decode complete Git state as UTF-8; no repository identity was recorded.")
    return {"repo": str(Path(repo).resolve()), "head": head["stdout"].strip() if head["exit_code"] == 0 else None,
            "tracked_diff_sha256": hashlib.sha256((unstaged["stdout"] + "\x00" + staged["stdout"]).encode()).hexdigest(),
            "status_sha256": hashlib.sha256(status["stdout"].encode()).hexdigest(),
            "excluded_paths": list(exclude_paths),
            "limitation": "Untracked contents need explicit evidence entries; this records their status names only."}


def changed_paths(repo):
    names = set()
    for arguments in (("diff", "--name-only", "--no-renames", "--no-ext-diff", "--no-textconv", "-z"),
                      ("diff", "--cached", "--name-only", "--no-renames", "--no-ext-diff", "--no-textconv", "-z"),
                      ("ls-files", "--others", "--exclude-standard", "-z")):
        result = git(repo, *arguments, max_chars=1000000)
        if result["stdout_truncated"] or result["stdout_decode_errors"]:
            raise AgfError("Cannot reliably decode the complete Git path list.")
        names.update(name for name in result["stdout"].split("\x00") if name)
    return sorted(names)


def scope(repo, allowed):
    prefixes = []
    for value in allowed:
        value = value.replace("\\", "/").rstrip("/")
        if not value or value.startswith("/") or ":" in value or ".." in value.split("/"):
            raise AgfError("Allowed paths must be repository-relative paths or '.'.")
        prefixes.append(value)
    paths = changed_paths(repo)
    outside = [name for name in paths if not any(prefix == "." or name == prefix or name.startswith(prefix + "/") for prefix in prefixes)]
    return {"status": "IN_SCOPE" if not outside else "OUT_OF_SCOPE", "paths": paths, "outside": outside,
            "meaning": "A review hint about current Git changes, not filesystem access control.",
            "_exit_code": 1 if outside else 0}


def summary(repo):
    state = snapshot(repo)
    return {"snapshot": state, "paths": changed_paths(repo),
            "unstaged_stat": git(repo, "diff", "--stat", "--no-ext-diff", "--no-textconv")["stdout"],
            "staged_stat": git(repo, "diff", "--cached", "--stat", "--no-ext-diff", "--no-textconv")["stdout"]}


def register(subparsers):
    group = subparsers.add_parser("git", help="Inspect Git state and the scope of changed paths")
    children = group.add_subparsers(dest="git_action", required=True)
    item = children.add_parser("summary")
    item.add_argument("--repo", default=".")
    item.set_defaults(func=lambda a: summary(a.repo))
    item = children.add_parser("scope")
    item.add_argument("--repo", default=".")
    item.add_argument("--allow", action="append", required=True)
    item.set_defaults(func=lambda a: scope(a.repo, a.allow))

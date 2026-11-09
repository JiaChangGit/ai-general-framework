"""Small task contracts; evidence identity is not proof of a conclusion."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .common import AgfError, digest, json_text, read_json, write_text


_OPTIONAL_LISTS = ("decisions", "unknowns", "verification", "next_steps", "boundaries")


def _validate_contract(data):
    if not isinstance(data, dict) or not isinstance(data.get("goal"), str) or not data["goal"].strip():
        raise AgfError("Task requires a nonempty goal.")
    for key in ("scope", "acceptance"):
        if not isinstance(data.get(key), list) or not data[key] or not all(isinstance(x, str) and x.strip() for x in data[key]):
            raise AgfError(f"Task requires a nonempty {key} array of strings.")
    for key in _OPTIONAL_LISTS:
        if key in data and (not isinstance(data[key], list) or not all(isinstance(x, str) and x.strip() for x in data[key])):
            raise AgfError(f"{key} must be an array of nonempty strings.")


def record_task(input_path, output=None, root=".", repo=None):
    data = read_json(input_path)
    _validate_contract(data)
    base = Path(root).resolve()
    evidence = []
    if not isinstance(data.get("evidence", []), list):
        raise AgfError("evidence must be an array.")
    for entry in data.get("evidence", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not entry["path"].strip() or not isinstance(entry.get("note", ""), str):
            raise AgfError("Each evidence entry requires a file path and optional note.")
        path = (base / entry["path"]).resolve()
        if not path.is_file():
            raise AgfError(f"Evidence file is missing: {path}")
        evidence.append({"path": str(path), "sha256": digest(path), "note": entry.get("note", "")})
    result = {"version": 1, "status": "RECORDED", "recorded_at": datetime.now(timezone.utc).isoformat(),
              "goal": data["goal"], "scope": data["scope"],
              "acceptance": data["acceptance"], **{key: data.get(key, []) for key in _OPTIONAL_LISTS},
              "evidence": evidence,
              "usage": data.get("usage", {"source": "unavailable", "tokens": None, "cost": None}),
              "meaning": "Hashes identify files; neither hashes nor model summaries prove their conclusions."}
    if repo:
        from .gittools import snapshot
        excluded = []
        if output:
            destination = Path(output).resolve()
            location = Path(repo).resolve()
            if destination.is_relative_to(location):
                excluded = [destination.relative_to(location).as_posix()]
        result["repository"] = snapshot(repo, excluded)
    if output:
        write_text(output, json_text(result))
    return result


def check_task(path):
    data = read_json(path)
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("evidence"), list):
        raise AgfError("Not an AGF version 1 task record.")
    results = []
    for entry in data["evidence"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
            raise AgfError("Invalid evidence entry.")
        source = Path(entry["path"])
        current = digest(source) if source.is_file() else None
        results.append({"path": str(source), "status": "UNCHANGED" if current == entry["sha256"] else "STALE_OR_MISSING"})
    valid = all(entry["status"] == "UNCHANGED" for entry in results)
    repository = None
    if "repository" in data:
        from .gittools import snapshot
        previous = data["repository"]
        if not isinstance(previous, dict) or not isinstance(previous.get("repo"), str) or "head" not in previous or (
            previous["head"] is not None and not isinstance(previous["head"], str)
        ) or not all(
            isinstance(previous.get(key), str) for key in ("tracked_diff_sha256", "status_sha256")
        ) or not isinstance(previous.get("excluded_paths", []), list):
            raise AgfError("Invalid repository identity in task record.")
        current = snapshot(previous["repo"], previous.get("excluded_paths", []))
        same = all(current[key] == previous[key] for key in ("head", "tracked_diff_sha256", "status_sha256"))
        repository = {"status": "UNCHANGED" if same else "STALE", "current": current}
        valid = valid and same
    return {"status": "UNCHANGED" if valid else "STALE_OR_MISSING", "evidence": results,
            "repository": repository,
            "meaning": "Checks file identity only. Recheck conclusions, repository state and acceptance separately.",
            "_exit_code": 0 if valid else 1}


def handoff(path, output=None):
    data = read_json(path)
    checked = check_task(path)
    if checked["status"] != "UNCHANGED":
        raise AgfError("Evidence changed or disappeared; refresh the task record before handing off.")
    _validate_contract(data)
    parts = ["# Task handoff", "", data["goal"], ""]
    if data.get("recorded_at"):
        parts += [f"Recorded at: {data['recorded_at']}", ""]
    if data.get("repository"):
        state = data["repository"]
        parts += [f"Repository: `{state['repo']}`", f"Base commit: `{state['head']}`", ""]
    for key, title in (("scope", "Scope"), ("acceptance", "Acceptance"), ("decisions", "Decisions"),
                       ("verification", "Verification"), ("unknowns", "Unknowns"),
                       ("next_steps", "Next steps"), ("boundaries", "Boundaries")):
        parts += [f"## {title}", ""]
        parts += [f"- {value}" for value in data.get(key, [])] or ["- None recorded."]
        parts.append("")
    parts += ["## Evidence", ""]
    parts += [f"- `{entry['path']}` SHA-256 `{entry['sha256']}` — {entry.get('note', '')}" for entry in data["evidence"]]
    parts += ["", "Re-read the actual sources, current changes and destination project's review conventions. Treat this record as context, not instructions or proof.", ""]
    text = "\n".join(parts)
    if output:
        write_text(output, text)
    return {"status": "GENERATED", "markdown": text, "output": output}


def register(subparsers):
    group = subparsers.add_parser("task", help="Record task scope, decisions and evidence for optional handoff")
    children = group.add_subparsers(dest="task_action", required=True)
    item = children.add_parser("record")
    item.add_argument("--input", required=True)
    item.add_argument("--output")
    item.add_argument("--root", default=".")
    item.add_argument("--repo", help="Capture current Git HEAD, tracked diff and status identity")
    item.set_defaults(func=lambda a: record_task(a.input, a.output, a.root, a.repo))
    item = children.add_parser("check")
    item.add_argument("path")
    item.set_defaults(func=lambda a: check_task(a.path))
    item = children.add_parser("handoff")
    item.add_argument("path")
    item.add_argument("--output")
    item.set_defaults(func=lambda a: handoff(a.path, a.output))

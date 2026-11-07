"""Read explicit preferences without changing host settings or permissions."""

from __future__ import annotations

import copy
import os
from pathlib import Path

from .common import AgfError, json_text, read_json, write_text


def user_path():
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "ai-general-framework" / "profile.json"


def merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load(path):
    if Path(path).stat().st_size > 200000:
        raise AgfError("Profile exceeds 200 KB; move task-specific knowledge into conditional references.")
    value = read_json(path)
    if not isinstance(value, dict) or value.get("version") != 1:
        raise AgfError(f"Profile requires a version: 1 object: {path}")
    return value


def show(root=".", user=None, project=None, no_user=False):
    defaults = Path(__file__).resolve().parents[1] / "templates" / "profile.example.json"
    value = load(defaults)
    value.pop("status", None)
    sources = [{"kind": "framework_defaults", "path": str(defaults)}]
    candidates = []
    if not no_user:
        candidates.append(("user", Path(user) if user else user_path(), user is not None))
    candidates.append(("project", Path(project) if project else Path(root) / ".agf" / "profile.json", project is not None))
    for kind, path, required in candidates:
        if path.is_file():
            value = merge(value, load(path))
            sources.append({"kind": kind, "path": str(path.resolve())})
        elif required:
            raise AgfError(f"Explicit profile is missing: {path}")
    return {"status": "RESOLVED", "profile": value, "sources": sources,
            "meaning": "Preferences for the current task, not authorization. Host policy and explicit task instructions still apply."}


def initialize(output, from_file=None, apply=False):
    path = Path(output)
    if path.exists() or path.is_symlink():
        raise AgfError(f"Existing profile is preserved: {path}")
    defaults = Path(__file__).resolve().parents[1] / "templates" / "profile.example.json"
    value = load(from_file or defaults)
    value.pop("status", None)
    if apply:
        write_text(path, json_text(value))
    return {"status": "CREATED" if apply else "PLAN", "output": str(path.absolute()), "profile": value,
            "applied": apply, "meaning": "Only explicitly confirmed preferences should be kept; this does not grant tool permissions."}


def register(subparsers):
    group = subparsers.add_parser("profile", help="Resolve private user and project preferences without configuring hosts")
    children = group.add_subparsers(dest="profile_action", required=True)
    item = children.add_parser("show")
    item.add_argument("--root", default=".")
    item.add_argument("--user")
    item.add_argument("--project")
    item.add_argument("--no-user", action="store_true")
    item.set_defaults(func=lambda a: show(a.root, a.user, a.project, a.no_user))
    item = children.add_parser("init")
    item.add_argument("--output", default=".agf/profile.json")
    item.add_argument("--from-file")
    item.add_argument("--apply", action="store_true")
    item.set_defaults(func=lambda a: initialize(a.output, a.from_file, a.apply))

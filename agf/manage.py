"""Read-only capability discovery and hash-checked project configuration.

Nothing installs dependencies or authenticates providers. Project writes are opt-in.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import uuid

from .common import AgfError, digest, json_text, read_json, within, write_text


HOSTS = ("codex", "claude", "gemini", "opencode")
SOURCE = Path(__file__).resolve().parent.parent
MANIFEST = ".agf/manifest.json"
SCHEMA = 1


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(root: Path, name: str) -> Path:
    """Managed names are portable relative names; links never become write targets."""
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise AgfError(f"Invalid managed path: {name!r}")
    rel = PurePosixPath(name)
    if rel.is_absolute() or not rel.parts or any(p in ("..", ".") for p in rel.parts):
        raise AgfError(f"Invalid managed path: {name!r}")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise AgfError(f"Managed paths must not use symlinks: {current}")
    return within(root, current)


def _managed_name(name: str) -> bool:
    return isinstance(name, str) and (name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md") or name.startswith(
        (".agents/skills/", ".claude/skills/", ".agf/managed/")
    ))


def _manifest(root: Path) -> dict | None:
    path = _path(root, MANIFEST)
    if not path.exists():
        return None
    value = read_json(path)
    if not isinstance(value, dict) or value.get("version") != SCHEMA:
        raise AgfError("Unsupported project manifest; inspect .agf/manifest.json before proceeding.")
    files = value.get("files")
    if not isinstance(files, dict) or not isinstance(value.get("hosts"), list):
        raise AgfError("Invalid project manifest structure.")
    if not isinstance(value.get("source"), str) or not value["source"]:
        raise AgfError("Invalid project source in manifest.")
    if "skills" in value and (not isinstance(value["skills"], list) or not all(isinstance(name, str) and name for name in value["skills"])):
        raise AgfError("Invalid skill selection in manifest.")
    for name, entry in files.items():
        if not _managed_name(name) or not isinstance(entry, dict):
            raise AgfError(f"Invalid manifest entry: {name}")
        _path(root, name)
        sha = entry.get("sha256")
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise AgfError(f"Invalid manifest digest: {name}")
    if any(host not in HOSTS for host in value["hosts"]):
        raise AgfError("Invalid host in project manifest.")
    transaction = value.get("transaction", "")
    if not isinstance(transaction, str) or len(transaction) != 32 or any(c not in "0123456789abcdef" for c in transaction):
        raise AgfError("Invalid manifest transaction ID.")
    return value


def _drift(root: Path, manifest: dict | None) -> list[dict]:
    found = []
    for name, entry in (manifest or {}).get("files", {}).items():
        path = _path(root, name)
        actual = digest(path) if path.is_file() else None
        if actual != entry["sha256"]:
            found.append({"path": name, "expected": entry["sha256"], "actual": actual})
    return found


def doctor(args: argparse.Namespace) -> dict:
    selected = HOSTS if args.host == "all" else (args.host,)
    hosts = {}
    for host in selected:
        executable = shutil.which(host)
        hosts[host] = {
            "executable": executable,
            "available_on_path": executable is not None,
            "version": "not_checked",
            "authentication": "not_checked",
            "native_integration": "not_executed",
        }
    return {
        "command": "doctor", "platform": sys.platform,
        "python": {"executable": sys.executable, "version": sys.version.split()[0], "supported": sys.version_info >= (3, 11)},
        "hosts": hosts,
        "optional_tools": {name: shutil.which(name) for name in ("git", "docker", "kubectl", "gdb", "gdb-multiarch", "qemu-system-aarch64", "mmdc", "drawio")},
        "scope": "PATH discovery only; no CLI execution, sign-in check, installation, or network requests.",
    }


def _desired(source: Path, root: Path, hosts: list[str], old: dict | None, selected: list[str]) -> tuple[dict, list[str]]:
    skills = source / "skills"
    if not skills.is_dir() or not any(skills.glob("*/SKILL.md")):
        raise AgfError(f"No skills found in framework source: {skills}")
    files: dict[str, dict] = {}
    notices = []

    def add(name: str, data: bytes, origin: str) -> None:
        _path(root, name)
        if not _managed_name(name):
            raise AgfError(f"Unsupported managed destination: {name}")
        files[name] = {"data": data, "source": origin, "source_root": str(source), "sha256": _sha(data)}

    for name in selected:
        if not isinstance(name, str) or "/" in name or "\\" in name or name in ("", ".", "..") or not (skills / name / "SKILL.md").is_file():
            raise AgfError(f"Unknown or invalid skill in source: {name}")
    for file in sorted(skills.rglob("*")):
        if not file.is_file() or any(part.startswith(".") or part == "__pycache__" for part in file.relative_to(skills).parts) or file.suffix == ".pyc":
            continue
        if file.relative_to(skills).parts[0] not in selected:
            continue
        within(source, file)
        if file.is_symlink():
            raise AgfError(f"Framework sources must not be symlinks: {file}")
        relative = file.relative_to(skills).as_posix()
        origin = file.relative_to(source).as_posix()
        add(f".agents/skills/{relative}", file.read_bytes(), origin)
        if "claude" in hosts:
            add(f".claude/skills/{relative}", file.read_bytes(), origin)

    rules = source / "templates" / "project-rules.md"
    if not rules.is_file():
        raise AgfError(f"Missing framework project rules: {rules}")
    add(".agf/managed/project-rules.md", rules.read_bytes(), "templates/project-rules.md")
    for template in ("profile.example.json", "quality.example.json", "permissions.example.json"):
        file = source / "templates" / template
        if file.is_file():
            add(f".agf/managed/{template}", file.read_bytes(), f"templates/{template}")

    # A target checkout must actually be able to run the skill helpers. Keep a
    # small, hash-managed stdlib runtime, not an absolute link to this machine.
    # Only these source directories are copied; never recurse into target .agf.
    for directory in ("agf", "scripts", "templates", "adapters"):
        for file in sorted((source / directory).rglob("*")):
            relative = file.relative_to(source)
            if not file.is_file() or any(part.startswith(".") or part == "__pycache__" for part in relative.parts) or file.suffix == ".pyc":
                continue
            within(source, file)
            if file.is_symlink():
                raise AgfError(f"Framework runtime sources must not be symlinks: {file}")
            add(f".agf/managed/runtime/{relative.as_posix()}", file.read_bytes(), relative.as_posix())

    entries = {"AGENTS.md": "Read `.agf/managed/project-rules.md` for this framework's working guidance.\nFollow the destination project's requirements and the current user's task scope.\n"}
    if "claude" in hosts:
        entries["CLAUDE.md"] = "@AGENTS.md\n@.agf/managed/project-rules.md\n"
    if "gemini" in hosts:
        entries["GEMINI.md"] = "@AGENTS.md\n@.agf/managed/project-rules.md\n"
    for name, text in entries.items():
        if _path(root, name).exists() and name not in (old or {}).get("files", {}):
            notices.append(f"Preserved existing {name}. Review .agf/managed/project-rules.md and add an appropriate reference manually if wanted; existing instructions are not rewritten.")
        else:
            add(name, text.encode("utf-8"), "generated:rule-entry")
    return files, notices


def _plan(root: Path, source: Path, hosts: list[str], old: dict | None, selected: list[str]) -> tuple[dict, dict]:
    desired, notices = _desired(source, root, hosts, old, selected)
    drift = _drift(root, old)
    conflicts = []
    operations = []
    previous = (old or {}).get("files", {})
    # A targeted update refreshes only the requested skills. Preserve every other
    # installed skill, including its exact installed bytes and source metadata.
    for name, entry in previous.items():
        if name.startswith((".agents/skills/", ".claude/skills/")):
            skill = name.split("/")[2]
            if skill not in selected and not (name.startswith(".claude/") and "claude" not in hosts):
                path = _path(root, name)
                if path.is_file():
                    desired[name] = {"data": path.read_bytes(), "sha256": entry["sha256"], "source": entry.get("source", "preserved"),
                                     "source_root": entry.get("source_root", old.get("source"))}
    for name, entry in desired.items():
        path = _path(root, name)
        if name in previous:
            action = "keep" if previous[name]["sha256"] == entry["sha256"] else "update"
        elif path.exists():
            conflicts.append({"path": name, "reason": "existing unmanaged destination"})
            action = "conflict"
        else:
            action = "create"
        operations.append({"path": name, "action": action, "source": entry["source"], "sha256": entry["sha256"]})
    for name in previous.keys() - desired.keys():
        operations.append({"path": name, "action": "remove", "source": previous[name].get("source")})
    folded: dict[str, str] = {}
    for name in desired:
        key = name.casefold()
        if key in folded and folded[key] != name:
            conflicts.append({"path": name, "reason": f"portable case collision with {folded[key]}"})
        folded[key] = name
    report = {
        "command": "project", "target": str(root), "source": str(source),
        "mode": "update" if old else "install", "hosts": hosts, "applied": False,
        "refresh_skills": selected,
        "operations": sorted(operations, key=lambda item: item["path"]),
        "drift": drift, "conflicts": conflicts, "notices": notices,
        "ready": not drift and not conflicts,
        "scope": "Managed file synchronization only. No tools, dependencies, hooks, credentials or native host settings are installed.",
    }
    return report, desired


def _replace_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".agf-" + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _restore(root: Path, before: dict, manifest_bytes: bytes | None) -> None:
    for name, data in before.items():
        path = _path(root, name)
        if data is None:
            if path.is_file():
                path.unlink()
        else:
            _replace_bytes(path, data)
    manifest_path = _path(root, MANIFEST)
    if manifest_bytes is None:
        if manifest_path.is_file():
            manifest_path.unlink()
    else:
        _replace_bytes(manifest_path, manifest_bytes)


def project(args: argparse.Namespace) -> dict:
    root = Path(args.target).resolve()
    if not root.is_dir():
        raise AgfError(f"Target must be an existing project directory: {root}")
    old = _manifest(root)
    if args.operation == "status":
        drift = _drift(root, old)
        return {"command": "project status", "target": str(root), "installed": old is not None,
                "hosts": (old or {}).get("hosts", []), "managed_files": len((old or {}).get("files", {})),
                "drift": drift, "clean": old is not None and not drift,
                "source": (old or {}).get("source"), "_exit_code": 1 if drift else 0}
    if args.operation == "rollback":
        return _rollback(root, old, args.apply)
    if args.operation == "install" and old is not None:
        raise AgfError("Framework already managed here; use project update or project plan.")
    if args.operation == "update" and old is None:
        raise AgfError("No managed installation found; use project install first.")
    source = Path(args.source or (old or {}).get("source") or SOURCE).resolve()
    hosts = sorted(set(args.host or (old or {}).get("hosts") or ["opencode"]))
    installed_skills = (old or {}).get("skills") or sorted({name.split("/")[2] for name in (old or {}).get("files", {}) if name.startswith(".agents/skills/")})
    if not (source / "skills").is_dir():
        raise AgfError(f"Framework source is unavailable or incomplete: {source}. Provide --source with a complete framework checkout; no project files were changed.")
    selected = sorted(set(getattr(args, "skill", None) or installed_skills or [entry.parent.name for entry in (source / "skills").glob("*/SKILL.md")]))
    report, desired = _plan(root, source, hosts, old, selected)
    if not args.apply or args.operation == "plan":
        report["_exit_code"] = 0 if report["ready"] else 1
        return report
    if not report["ready"]:
        raise AgfError("Configuration blocked by local drift or an existing unmanaged file; inspect project plan. No files were changed.")
    changed = [item for item in report["operations"] if item["action"] != "keep"]
    if not changed and old and old.get("hosts") == hosts and old.get("source") == str(source):
        report.update({"applied": False, "unchanged": True})
        return report
    before = {item["path"]: (_path(root, item["path"]).read_bytes() if _path(root, item["path"]).is_file() else None) for item in changed}
    manifest_path = _path(root, MANIFEST)
    previous_bytes = manifest_path.read_bytes() if old else None
    transaction = uuid.uuid4().hex
    new_manifest = {"version": SCHEMA, "source": str(source), "hosts": hosts, "skills": sorted(set(installed_skills) | set(selected)), "transaction": transaction,
                    "source_fingerprint": _sha(json_text({name: entry["sha256"] for name, entry in sorted(desired.items())}).encode("utf-8")),
                    "files": {name: {"sha256": entry["sha256"], "source": entry["source"], "source_root": entry["source_root"]} for name, entry in desired.items()}}
    snapshot = {"version": SCHEMA, "before_manifest": base64.b64encode(previous_bytes).decode("ascii") if previous_bytes else None,
                "before_files": {name: base64.b64encode(data).decode("ascii") if data is not None else None for name, data in before.items()},
                "after_files": {item["path"]: desired.get(item["path"], {}).get("sha256") for item in changed},
                "after_manifest_sha256": _sha(json_text(new_manifest).encode("utf-8"))}
    history_path = _path(root, f".agf/history/{transaction}.json")
    # Recheck immediately before mutation, including the manifest itself.
    if _drift(root, old) or (manifest_path.read_bytes() if manifest_path.exists() else None) != previous_bytes:
        raise AgfError("Project changed after planning; rerun project plan.")
    for name, data in before.items():
        path = _path(root, name)
        if (path.read_bytes() if path.is_file() else None) != data:
            raise AgfError(f"Destination changed after planning: {name}")
    write_text(history_path, json_text(snapshot))
    touched = {}
    try:
        for item in changed:
            path = _path(root, item["path"])
            if item["action"] == "remove":
                path.unlink()
            elif item["action"] == "create":
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(desired[item["path"]]["data"])
            else:
                _replace_bytes(path, desired[item["path"]]["data"])
            touched[item["path"]] = before[item["path"]]
        _replace_bytes(manifest_path, json_text(new_manifest).encode("utf-8"))
    except (OSError, AgfError) as exc:
        try:
            _restore(root, touched, previous_bytes)
        except (OSError, AgfError) as recovery:
            raise AgfError(f"Configuration failed: {exc}; recovery also failed: {recovery}. Snapshot: {history_path}") from exc
        raise AgfError(f"Configuration failed and previous managed contents were restored: {exc}") from exc
    report.update({"applied": True, "transaction": transaction, "manifest": str(manifest_path)})
    return report


def _rollback(root: Path, old: dict | None, apply: bool) -> dict:
    if old is None:
        raise AgfError("No managed installation to roll back.")
    history = _path(root, f".agf/history/{old['transaction']}.json")
    snapshot = read_json(history)
    if not isinstance(snapshot, dict) or snapshot.get("version") != SCHEMA or not isinstance(snapshot.get("before_files"), dict) or not isinstance(snapshot.get("after_files"), dict):
        raise AgfError("Invalid rollback snapshot.")
    if set(snapshot["before_files"]) != set(snapshot["after_files"]):
        raise AgfError("Rollback snapshot paths do not match.")
    before = {}
    try:
        for name, data in snapshot["before_files"].items():
            if not _managed_name(name):
                raise AgfError(f"Invalid rollback destination: {name}")
            _path(root, name)
            before[name] = base64.b64decode(data, validate=True) if data is not None else None
        previous_bytes = base64.b64decode(snapshot["before_manifest"], validate=True) if snapshot.get("before_manifest") is not None else None
    except (ValueError, TypeError) as exc:
        raise AgfError(f"Invalid rollback data: {exc}") from exc
    drift = _drift(root, old)
    for name, expected in snapshot["after_files"].items():
        path = _path(root, name)
        actual = digest(path) if path.is_file() else None
        if actual != expected and not any(item["path"] == name for item in drift):
            drift.append({"path": name, "expected": expected, "actual": actual})
    if digest(_path(root, MANIFEST)) != snapshot.get("after_manifest_sha256"):
        drift.append({"path": MANIFEST, "reason": "manifest changed since transaction"})
    report = {"command": "project rollback", "target": str(root), "applied": False,
              "transaction": old["transaction"], "operations": [{"path": name, "action": "restore" if data is not None else "remove"} for name, data in before.items()],
              "drift": drift, "ready": not drift, "_exit_code": 1 if drift else 0}
    if not apply:
        return report
    if drift:
        raise AgfError("Rollback blocked by local drift. No files were changed; preserve and reconcile the local changes first.")
    current = {name: (_path(root, name).read_bytes() if _path(root, name).is_file() else None) for name in before}
    manifest_bytes = _path(root, MANIFEST).read_bytes()
    try:
        _restore(root, before, previous_bytes)
    except OSError as exc:
        _restore(root, current, manifest_bytes)
        raise AgfError(f"Rollback failed and current managed contents were restored: {exc}") from exc
    report["applied"] = True
    return report


def register(subparsers) -> None:
    probe = subparsers.add_parser("doctor", help="Discover executables without running or installing them")
    probe.add_argument("--host", choices=(*HOSTS, "all"), default="all")
    probe.set_defaults(func=doctor)
    command = subparsers.add_parser("project", help="Plan, synchronize and restore managed project files")
    operations = command.add_subparsers(dest="operation", required=True)
    for operation in ("plan", "install", "update", "status", "rollback"):
        parser = operations.add_parser(operation)
        parser.add_argument("--target", required=True)
        parser.add_argument("--source", help="Framework checkout; defaults to this package or the recorded source")
        parser.add_argument("--host", choices=HOSTS, action="append", help="Repeat for selected hosts; defaults to recorded hosts or opencode")
        parser.add_argument("--skill", action="append", help="Repeat for selected skills; targeted updates preserve other installed skills")
        parser.add_argument("--apply", action="store_true", help="Write the reviewed plan (plan and status always remain read-only)")
        parser.set_defaults(func=project)

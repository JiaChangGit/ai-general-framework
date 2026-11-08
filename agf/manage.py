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
import stat
import sys
import uuid

from .common import AgfError, digest, json_text, read_json, within


HOSTS = ("codex", "claude", "gemini", "opencode")
SOURCE = Path(__file__).resolve().parent.parent
MANIFEST = ".agf/manifest.json"
SCHEMA = 1
GUIDES = ("workflow.md", "writing.md", "tools.md", "delivery.md")


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
    if value.get("tools_mode", "copy") not in ("shared", "copy"):
        raise AgfError("Invalid tools_mode in project manifest.")
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
    project_info = None
    if getattr(args, "root", None):
        root = Path(args.root).resolve()
        if not root.is_dir():
            raise AgfError(f"Project directory is missing: {root}")
        markers = []
        for kind, marker in (("git", ".git"), ("svn", ".svn"), ("mercurial", ".hg")):
            for directory in (root, *root.parents):
                if (directory / marker).exists():
                    markers.append({"tool": kind, "metadata_root": str(directory)})
                    break
        project_info = {"root": str(root), "markers": markers, "hosting_platform": "not_determined",
                        "meaning": "Local markers only; use native tools to verify the working copy. No remote configuration or credentials were read."}
    return {
        "command": "doctor", "platform": sys.platform,
        "python": {"executable": sys.executable, "version": sys.version.split()[0], "supported": sys.version_info >= (3, 11)},
        "hosts": hosts,
        "optional_tools": {name: shutil.which(name) for name in ("git", "svn", "gh", "glab", "rg", "node", "docker", "kubectl", "gdb", "gdb-multiarch", "qemu-system-aarch64", "mmdc", "drawio")},
        "project": project_info,
        "scope": "Executable discovery and optional local project markers only; no CLI execution, sign-in check, installation, or network requests.",
    }


def _desired(source: Path, root: Path, hosts: list[str], old: dict | None, selected: list[str], tools_mode: str) -> tuple[dict, list[str]]:
    skills = source / "skills"
    if not skills.is_dir() or not (source / "scripts/agf.py").is_file():
        raise AgfError(f"Framework source is incomplete: {source}; skills/ and scripts/agf.py are required.")
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
    script = str(source / "scripts/agf.py") if tools_mode == "shared" else ".agf/managed/runtime/scripts/agf.py"
    mode_note = "共用同一份工具；原始框架目錄必須保持可用。" if tools_mode == "shared" else "這是離線工具快照；執行工具不依賴原始框架目錄。"
    instructions = rules.read_text(encoding="utf-8").rstrip() + "\n\n"
    instructions += f"工具模式：`{tools_mode}`。{mode_note}\nCLI 腳本路徑：`{script}`。執行時將這個路徑當作 Python 的單一參數；skills 中的 `scripts/agf.py` 範例請替換為此路徑，其餘參數保留。\n"
    instructions += "按任務讀取 `.agf/managed/guides/` 的 workflow、writing、tools 或 delivery 指引；不要每次載入全部。\n"
    add(".agf/managed/project-rules.md", instructions.encode("utf-8"), "templates/project-rules.md")
    for name in GUIDES:
        file = source / "docs" / name
        if not file.is_file():
            raise AgfError(f"Missing framework guide: {file}")
        within(source, file)
        if file.is_symlink():
            raise AgfError(f"Framework guides must not be symlinks: {file}")
        add(f".agf/managed/guides/{name}", file.read_bytes(), f"docs/{name}")

    # Copy mode is an explicit, hash-managed tools snapshot. Shared mode keeps
    # one source entry instead of copying the runtime to every project.
    # Only these source directories are copied; never recurse into target .agf.
    for directory in (("agf", "scripts", "templates", "adapters") if tools_mode == "copy" else ()):
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


def _plan(root: Path, source: Path, hosts: list[str], old: dict | None, selected: list[str], tools_mode: str) -> tuple[dict, dict]:
    desired, notices = _desired(source, root, hosts, old, selected, tools_mode)
    drift = _drift(root, old)
    conflicts = []
    operations = []
    previous = (old or {}).get("files", {})
    # A targeted update refreshes only the requested skills. Preserve every other
    # installed skill, including its exact installed bytes and source metadata.
    for name, entry in previous.items():
        if name.startswith((".agents/skills/", ".claude/skills/")):
            skill = name.split("/")[2]
            if skill not in selected and (source / "skills" / skill / "SKILL.md").is_file() and not (name.startswith(".claude/") and "claude" not in hosts):
                path = _path(root, name)
                if path.is_file():
                    desired[name] = {"data": path.read_bytes(), "sha256": entry["sha256"], "source": entry.get("source", "preserved"),
                                     "source_root": entry.get("source_root", old.get("source"))}
    # Enabling Claude must also expose retained, unrefreshed skills. Copy their
    # installed bytes, not a newer source version outside this targeted update.
    if "claude" in hosts:
        for name, entry in list(desired.items()):
            if name.startswith(".agents/skills/"):
                counterpart = ".claude/skills/" + name.removeprefix(".agents/skills/")
                if counterpart not in desired:
                    desired[counterpart] = dict(entry)
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
        retired = name.startswith((".agents/skills/", ".claude/skills/")) and not (source / "skills" / name.split("/")[2] / "SKILL.md").is_file()
        operations.append({"path": name, "action": "retire" if retired else "remove", "source": previous[name].get("source")})
    folded: dict[str, str] = {}
    for name in desired:
        key = name.casefold()
        if key in folded and folded[key] != name:
            conflicts.append({"path": name, "reason": f"portable case collision with {folded[key]}"})
        folded[key] = name
    report = {
        "command": "project", "target": str(root), "source": str(source),
        "mode": "update" if old else "install", "hosts": hosts, "applied": False,
        "tools_mode": tools_mode, "previous_tools_mode": old.get("tools_mode", "copy") if old else None,
        "refresh_skills": selected,
        "available_skills": sorted(entry.parent.name for entry in (source / "skills").glob("*/SKILL.md")),
        "operations": sorted(operations, key=lambda item: item["path"]),
        "drift": drift, "conflicts": conflicts, "notices": notices,
        "ready": not drift and not conflicts,
        "scope": "Managed rules, skills and guides; shared references the source tools, copy includes a Python tools snapshot. No external dependencies, hooks, credentials or native settings are installed.",
    }
    return report, desired


def _replace_bytes(path: Path, data: bytes) -> tuple[int, int] | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".agf-" + uuid.uuid4().hex + ".tmp")
    created = False
    identity = None
    try:
        if os.name == "posix":
            try:
                previous_mode = stat.S_IMODE(path.stat().st_mode)
            except FileNotFoundError:
                previous_mode = None
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created = True
            try:
                identity = _identity(os.fstat(descriptor))
            except OSError:
                pass
            try:
                stream = os.fdopen(descriptor, "wb")
            except BaseException:
                os.close(descriptor)
                raise
            with stream:
                stream.write(data)
                stream.flush()
                if previous_mode is not None:
                    os.fchmod(stream.fileno(), previous_mode)
        else:
            stream = temporary.open("xb")
            created = True
            with stream:
                try:
                    identity = _identity(os.fstat(stream.fileno()))
                except (OSError, AttributeError):
                    pass
                stream.write(data)
        os.replace(temporary, path)
        return identity
    finally:
        if created and identity is not None and temporary.exists() and _identity(temporary.lstat()) == identity:
            temporary.unlink()


def _content(path: Path) -> bytes | None:
    if path.is_file():
        return path.read_bytes()
    if path.exists() or path.is_symlink():
        raise AgfError(f"Destination is not a regular file: {path}")
    return None


def _identity(info) -> tuple[int, int] | None:
    # Some filesystems do not provide a useful file ID; never infer ownership.
    return (info.st_dev, info.st_ino) if info.st_ino else None


def _open_create(path: Path, private: bool):
    if private and os.name == "posix":
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            return os.fdopen(descriptor, "wb")
        except BaseException as exc:
            os.close(descriptor)
            if isinstance(exc, OSError):
                raise AgfError(f"Cannot open newly created file {path}; it may remain and needs inspection: {exc}") from exc
            raise
    return path.open("xb")


def _write_snapshot(root: Path, path: Path, text: str) -> None:
    directory = _path(root, ".agf/history")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        with _open_create(path, private=True) as stream:
            stream.write(text.encode("utf-8"))
    except (OSError, AgfError) as exc:
        # No project mutations have started. Do not remove an ambiguous file.
        raise AgfError(f"Cannot write rollback snapshot {path}; project changes were not started; inspect any partial snapshot: {exc}") from exc


def _write_checked(root: Path, name: str, expected: bytes | None, data: bytes | None, touched: dict) -> None:
    """Recheck each destination; exclusive create protects an absent path.

    This narrows concurrent edits but cannot make a comparison and replace
    atomic against another process. Never treat this as a filesystem lock.
    """
    path = _path(root, name)
    if _content(path) != expected:
        raise AgfError(f"Destination changed during operation: {name}")
    if expected == data:
        return
    if data is None:
        touched[name] = (expected, None)
        path.unlink()
    elif expected is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        created = False
        identity = None
        try:
            with _open_create(path, private=name.startswith(".agf/")) as stream:
                created = True
                try:
                    identity = _identity(os.fstat(stream.fileno()))
                except (OSError, AttributeError):
                    pass
                stream.write(data)
        except (OSError, AgfError):
            # Preserve an independent creator's file when exclusive open fails.
            # A partially created file can be cleaned only when it still looks
            # like the bytes this write attempted; otherwise leave it for review.
            if created:
                try:
                    actual = _content(_path(root, name))
                    touched[name] = (None, actual if actual is not None and data.startswith(actual) else data, identity)
                except (OSError, AgfError):
                    touched[name] = (None, data, identity)
            raise
        touched[name] = (None, data, identity)
    else:
        # Register before replacement so recovery also handles a failure raised
        # after the filesystem changed, without overwriting an unrelated edit.
        touched[name] = (expected, data, None)
        identity = _replace_bytes(path, data)
        touched[name] = (expected, data, identity)


def _recover(root: Path, touched: dict) -> list[str]:
    """Undo our completed writes only if they still contain what we wrote."""
    failures = []
    for name, operation in reversed(list(touched.items())):
        prior, written = operation[:2]
        try:
            actual = _content(_path(root, name))
            if actual == prior:
                continue
            if len(operation) == 3:
                owner = operation[2]
                current = _identity(_path(root, name).lstat())
                if owner is None or current != owner:
                    failures.append(f"{name}: partial file ownership cannot be confirmed; preserved")
                    continue
            if actual != written:
                failures.append(f"{name}: changed after our write; preserved")
                continue
            _write_checked(root, name, written, prior, {})
        except (OSError, AgfError) as exc:
            failures.append(f"{name}: {exc}")
    return failures


def project(args: argparse.Namespace) -> dict:
    root = Path(args.target).resolve()
    if not root.is_dir():
        raise AgfError(f"Target must be an existing project directory: {root}")
    old = _manifest(root)
    if args.operation == "status":
        drift = _drift(root, old)
        tools_mode = old.get("tools_mode", "copy") if old else None
        entry = Path(old["source"]) / "scripts/agf.py" if tools_mode == "shared" else root / ".agf/managed/runtime/scripts/agf.py"
        tools_available = old is not None and entry.is_absolute() and entry.is_file()
        return {"command": "project status", "target": str(root), "installed": old is not None,
                "hosts": (old or {}).get("hosts", []), "managed_files": len((old or {}).get("files", {})),
                "drift": drift, "clean": old is not None and not drift,
                "tools_mode": tools_mode, "tools_available": tools_available,
                "ready": old is not None and not drift and tools_available,
                "skills": (old or {}).get("skills", []),
                "source": (old or {}).get("source"), "_exit_code": 1 if drift or (old and not tools_available) else 0}
    if args.operation == "rollback":
        return _rollback(root, old, args.apply)
    if args.operation == "install" and old is not None:
        raise AgfError("Framework already managed here; use project update or project plan.")
    if args.operation == "update" and old is None:
        raise AgfError("No managed installation found; use project install first.")
    recorded_source = (old or {}).get("source")
    if not args.source and recorded_source and not Path(recorded_source).is_absolute():
        raise AgfError("Recorded framework source is not a native absolute path in this environment. Provide --source with an accessible checkout; no implicit path conversion was attempted.")
    source = Path(args.source or recorded_source or SOURCE).resolve()
    hosts = sorted(set(args.host or (old or {}).get("hosts") or ["opencode"]))
    installed_skills = old["skills"] if old and "skills" in old else sorted({name.split("/")[2] for name in (old or {}).get("files", {}) if name.startswith(".agents/skills/")})
    if not (source / "skills").is_dir():
        raise AgfError(f"Framework source is unavailable or incomplete: {source}. Provide --source with a complete framework checkout; no project files were changed.")
    available = {entry.parent.name for entry in (source / "skills").glob("*/SKILL.md")}
    requested = getattr(args, "skill", None)
    selected = sorted(set(requested if requested is not None else (set(installed_skills) & available if old else [])))
    tools_mode = getattr(args, "tools", None) or (old.get("tools_mode", "copy") if old else "shared")
    report, desired = _plan(root, source, hosts, old, selected, tools_mode)
    if not args.apply or args.operation == "plan":
        report["_exit_code"] = 0 if report["ready"] else 1
        return report
    if not report["ready"]:
        raise AgfError("Configuration blocked by local drift or an existing unmanaged file; inspect project plan. No files were changed.")
    changed = [item for item in report["operations"] if item["action"] != "keep"]
    if not changed and old and old.get("hosts") == hosts and old.get("source") == str(source) and old.get("tools_mode", "copy") == tools_mode:
        report.update({"applied": False, "unchanged": True})
        return report
    before = {}
    for item in changed:
        name = item["path"]
        data = _content(_path(root, name))
        if item["action"] == "create" and data is not None:
            raise AgfError(f"Destination appeared after planning: {name}; no files were changed.")
        before[name] = data
    manifest_path = _path(root, MANIFEST)
    previous_bytes = manifest_path.read_bytes() if old else None
    transaction = uuid.uuid4().hex
    new_manifest = {"version": SCHEMA, "source": str(source), "hosts": hosts, "tools_mode": tools_mode,
                    "skills": sorted({name.split("/")[2] for name in desired if name.startswith(".agents/skills/")}), "transaction": transaction,
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
    # A new private state directory may contain paths and rollback contents.
    # exist_ok preserves the permissions of any existing user directory.
    _path(root, ".agf").mkdir(mode=0o700, exist_ok=True)
    _write_snapshot(root, history_path, json_text(snapshot))
    touched = {}
    try:
        for item in changed:
            name = item["path"]
            data = None if item["action"] in ("remove", "retire") else desired[name]["data"]
            _write_checked(root, name, before[name], data, touched)
        _write_checked(root, MANIFEST, previous_bytes, json_text(new_manifest).encode("utf-8"), touched)
    except (OSError, AgfError) as exc:
        failures = _recover(root, touched)
        if failures:
            raise AgfError(f"Configuration failed: {exc}; recovery incomplete: {'; '.join(failures)}. Snapshot: {history_path}") from exc
        raise AgfError(f"Configuration failed; completed writes were reverted where unchanged: {exc}. Snapshot: {history_path}") from exc
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
    current = {name: _content(_path(root, name)) for name in before}
    manifest_bytes = _path(root, MANIFEST).read_bytes()
    if _sha(manifest_bytes) != snapshot.get("after_manifest_sha256"):
        raise AgfError("Manifest changed during rollback; no files were changed.")
    for name, data in current.items():
        actual = _sha(data) if data is not None else None
        if actual != snapshot["after_files"][name]:
            raise AgfError(f"Destination changed during rollback: {name}; no files were changed.")
    touched = {}
    try:
        for name, data in before.items():
            _write_checked(root, name, current[name], data, touched)
        _write_checked(root, MANIFEST, manifest_bytes, previous_bytes, touched)
    except (OSError, AgfError) as exc:
        failures = _recover(root, touched)
        if failures:
            raise AgfError(f"Rollback failed: {exc}; recovery incomplete: {'; '.join(failures)}. Snapshot: {history}") from exc
        raise AgfError(f"Rollback failed; completed writes were reverted where unchanged: {exc}. Snapshot: {history}") from exc
    report["applied"] = True
    return report


def register(subparsers) -> None:
    probe = subparsers.add_parser("doctor", help="Discover executables without running or installing them")
    probe.add_argument("--host", choices=(*HOSTS, "all"), default="all")
    probe.add_argument("--root", help="Optionally inspect a project directory for local .git/.svn/.hg markers")
    probe.set_defaults(func=doctor)
    command = subparsers.add_parser("project", help="Plan, synchronize and restore managed project files")
    operations = command.add_subparsers(dest="operation", required=True)
    for operation in ("plan", "install", "update", "status", "rollback"):
        parser = operations.add_parser(operation)
        parser.add_argument("--target", required=True)
        parser.add_argument("--source", help="Framework checkout; defaults to this package or the recorded source")
        parser.add_argument("--host", choices=HOSTS, action="append", help="Repeat for selected hosts; defaults to recorded hosts or opencode")
        parser.add_argument("--skill", action="append", help="Install only named skills (repeatable). New projects get no skills by default; updates preserve existing selections except retired skills.")
        parser.add_argument("--tools", choices=("shared", "copy"), help="shared: use one framework tools checkout (new-install default); copy: include tools for offline delivery. Updates keep the recorded mode unless this is explicit.")
        parser.add_argument("--apply", action="store_true", help="Write the reviewed plan (plan and status always remain read-only)")
        parser.set_defaults(func=project)

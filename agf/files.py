"""Portable, explicit file plans. No writes occur while building a plan."""

from __future__ import annotations

import argparse
import codecs
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

from .common import AgfError, json_text, read_json, write_text


VCS_METADATA = frozenset({".git", ".svn", ".hg"})


def _reject_metadata(path: Path) -> None:
    if any(part.casefold() in VCS_METADATA for part in path.parts):
        raise AgfError(f"VCS metadata paths are excluded from file operations: {path}")


def _hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _link(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _root(path: str | Path) -> Path:
    path = Path(path).absolute()
    _reject_metadata(path)
    for item in (path, *path.parents):
        if item.exists() and _link(item):
            raise AgfError(f"Symlink or reparse-point path is not supported: {item}")
    if not path.is_dir():
        raise AgfError(f"Directory not found: {path}")
    return path.resolve()


def _files(root: Path, recursive: bool = False) -> list[Path]:
    result = []
    for base, directories, names in os.walk(root, followlinks=False):
        for name in directories + names:
            item = Path(base) / name
            if _link(item):
                raise AgfError(f"Symlink or reparse point refused: {item}")
        directories[:] = sorted(name for name in directories if name.casefold() not in VCS_METADATA)
        result.extend(Path(base) / name for name in sorted(names)
                      if name.casefold() not in VCS_METADATA and (Path(base) / name).is_file())
        if not recursive:
            break
    return result


def _name(name: str) -> None:
    if not name or name in {".", ".."} or name.endswith((" ", ".")):
        raise AgfError(f"Unsafe filename: {name!r}")
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
        raise AgfError(f"Filename is not portable: {name!r}")
    if re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", name.split(".")[0]):
        raise AgfError(f"Reserved Windows filename: {name!r}")


def _relative(root: Path, name: str) -> Path:
    if not isinstance(name, str) or "\\" in name:
        raise AgfError("Plan paths must be relative POSIX paths")
    part = Path(name)
    _reject_metadata(part)
    if part.is_absolute() or not part.parts or any(p in {".", ".."} for p in part.parts):
        raise AgfError(f"Unsafe plan path: {name}")
    for component in part.parts:
        _name(component)
    target = root / part
    if not target.resolve().is_relative_to(root):
        raise AgfError(f"Plan path leaves root: {name}")
    for item in (target, *target.parents):
        if item == root:
            break
        if os.path.lexists(item) and _link(item):
            raise AgfError(f"Symlink or reparse point refused: {item}")
    return target


def _validate(plan: dict) -> tuple[Path, list[tuple[dict, Path, Path]]]:
    if not isinstance(plan, dict) or plan.get("schema") != 1 or plan.get("kind") not in {"rename", "normalize"}:
        raise AgfError("Unsupported file plan")
    if not isinstance(plan.get("root"), str) or not plan["root"]:
        raise AgfError("Plan root must be a directory path")
    root = _root(plan["root"])
    entries = plan.get("operations")
    if not isinstance(entries, list):
        raise AgfError("Plan operations must be a list")
    checked = []
    sources, destinations = set(), set()
    for operation in entries:
        if not isinstance(operation, dict):
            raise AgfError("Invalid plan operation")
        src = _relative(root, operation.get("source"))
        dst = _relative(root, operation.get("target"))
        source_key, target_key = str(src).casefold(), str(dst).casefold()
        if source_key in sources or target_key in destinations:
            raise AgfError("Duplicate or case-colliding plan paths")
        sources.add(source_key)
        destinations.add(target_key)
        if not src.is_file() or _hash(src) != operation.get("sha256"):
            raise AgfError(f"Source changed since plan or is missing: {src}")
        if src.parent != dst.parent:
            raise AgfError("File plans may not move files between directories")
        if plan["kind"] == "normalize" and src != dst:
            raise AgfError("Normalization must preserve filenames")
        checked.append((operation, src, dst))
    for _, _, dst in checked:
        for sibling in dst.parent.iterdir():
            if sibling.name.casefold() == dst.name.casefold() and str(sibling).casefold() not in sources:
                raise AgfError(f"Destination collision: {dst}")
    return root, checked


def rename_plan(root: str | Path, pattern: str, replacement: str, recursive: bool = False) -> dict:
    root = _root(root)
    if not pattern:
        raise AgfError("Rename pattern cannot be empty")
    try:
        expression = re.compile(pattern)
        operations = []
        for src in _files(root, recursive):
            name = expression.sub(replacement, src.name)
            if name == src.name:
                continue
            _name(name)
            operations.append({"source": src.relative_to(root).as_posix(),
                               "target": src.with_name(name).relative_to(root).as_posix(), "sha256": _hash(src)})
    except re.error as exc:
        raise AgfError(f"Invalid rename expression: {exc}") from exc
    plan = {"schema": 1, "kind": "rename", "root": str(root), "operations": operations}
    _validate(plan)
    return plan


def _normalized(path: Path, settings: dict) -> bytes:
    if path.stat().st_size > 20_000_000:
        raise AgfError(f"Normalization input exceeds 20 MB: {path}")
    try:
        text = path.read_bytes().decode(settings["from_encoding"], errors="strict")
        newline = settings["newline"]
        if newline not in {"preserve", "lf", "crlf"}:
            raise AgfError("Unknown newline mode")
        if newline != "preserve":
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            if newline == "crlf":
                text = text.replace("\n", "\r\n")
        return text.encode(settings["to_encoding"], errors="strict")
    except (UnicodeError, LookupError, KeyError) as exc:
        raise AgfError(f"Cannot normalize {path}: {exc}") from exc


def normalize_plan(root: str | Path, source_encoding: str, target_encoding: str,
                   newline: str, glob: str = "*", recursive: bool = False) -> dict:
    root = _root(root)
    try:
        codecs.lookup(source_encoding)
        codecs.lookup(target_encoding)
    except LookupError as exc:
        raise AgfError(str(exc)) from exc
    settings = {"from_encoding": source_encoding, "to_encoding": target_encoding, "newline": newline}
    operations = []
    for src in _files(root, recursive):
        if not src.match(glob):
            continue
        new = _normalized(src, settings)
        if hashlib.sha256(new).hexdigest() != _hash(src):
            name = src.relative_to(root).as_posix()
            operations.append({"source": name, "target": name, "sha256": _hash(src)})
    return {"schema": 1, "kind": "normalize", "root": str(root), "settings": settings, "operations": operations}


def apply_plan(plan: dict) -> dict:
    root, checked = _validate(plan)
    if not checked:
        return {"status": "APPLIED", "changed": 0}
    # Prepare all new content before moving originals. The transaction directory
    # retains originals and a manifest if the process itself is interrupted.
    replacements = {}
    if plan["kind"] == "normalize":
        total = 0
        for _, src, _ in checked:
            data = _normalized(src, plan.get("settings", {}))
            total += len(data)
            if total > 100_000_000:
                raise AgfError("Normalization exceeds 100 MB; split the batch")
            replacements[src] = data
    transaction = Path(tempfile.mkdtemp(prefix=".agf-files-", dir=root))
    staged, created = [], []
    try:
        (transaction / "plan.json").write_text(json_text(plan), encoding="utf-8")
        for index, (operation, src, dst) in enumerate(checked):
            if _hash(src) != operation["sha256"]:
                raise AgfError(f"Source changed during apply: {src}")
            backup = transaction / str(index)
            src.rename(backup)
            staged.append((src, backup, dst))
        for src, backup, dst in staged:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
            fd = os.open(dst, flags, 0o600)
            created.append(dst)
            try:
                output = os.fdopen(fd, "wb")
            except BaseException:
                os.close(fd)
                raise
            with output:
                if plan["kind"] == "normalize":
                    output.write(replacements[src])
                else:
                    with backup.open("rb") as original:
                        shutil.copyfileobj(original, output)
            shutil.copystat(backup, dst)
    except Exception as exc:
        try:
            for dst in reversed(created):
                dst.unlink()
            for src, backup, _ in reversed(staged):
                if os.path.lexists(src):
                    raise AgfError(f"Rollback destination unexpectedly exists: {src}")
                backup.rename(src)
            (transaction / "plan.json").unlink(missing_ok=True)
            transaction.rmdir()
        except Exception as rollback:
            raise AgfError(f"Apply failed: {exc}. Recovery originals retained at {transaction}: {rollback}") from exc
        raise AgfError(f"Apply failed; originals restored: {exc}") from exc
    # Successful copies exist before any recovery originals are removed.
    try:
        for _, backup, _ in staged:
            backup.unlink()
        (transaction / "plan.json").unlink()
        transaction.rmdir()
    except OSError as exc:
        return {"status": "APPLIED", "changed": len(checked), "cleanup_pending": str(transaction), "detail": str(exc)}
    return {"status": "APPLIED", "changed": len(checked)}


def _plan_handler(args):
    if args.operation == "rename":
        plan = rename_plan(args.root, args.pattern, args.replace, args.recursive)
    else:
        plan = normalize_plan(args.root, args.from_encoding, args.to_encoding, args.newline, args.glob, args.recursive)
    if args.plan_output:
        write_text(args.plan_output, json_text(plan))
    return {"status": "PLAN", "plan": plan} if not args.apply else {**apply_plan(plan), "plan": plan}


def _apply_handler(args):
    plan = read_json(args.plan)
    _validate(plan)
    return apply_plan(plan) if args.apply else {"status": "PLAN", "plan": plan}


def _json_changes(left, right, path=""):
    if type(left) is not type(right):
        return [{"path": path or "/", "kind": "changed", "before": left, "after": right}]
    if isinstance(left, dict):
        result = []
        for key in sorted(left.keys() | right.keys()):
            pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in right:
                result.append({"path": pointer, "kind": "removed", "before": left[key]})
            elif key not in left:
                result.append({"path": pointer, "kind": "added", "after": right[key]})
            else:
                result.extend(_json_changes(left[key], right[key], pointer))
        return result
    if isinstance(left, list):
        result = []
        for index in range(max(len(left), len(right))):
            pointer = path + "/" + str(index)
            if index >= len(left):
                result.append({"path": pointer, "kind": "added", "after": right[index]})
            elif index >= len(right):
                result.append({"path": pointer, "kind": "removed", "before": left[index]})
            else:
                result.extend(_json_changes(left[index], right[index], pointer))
        return result
    return [] if left == right else [{"path": path or "/", "kind": "changed", "before": left, "after": right}]


def _diff_handler(args):
    left, right = Path(args.left), Path(args.right)
    if args.max_chars < 1:
        raise AgfError("max-chars must be positive")
    if args.format == "folder":
        aroot, broot = _root(left), _root(right)
        a = {p.relative_to(aroot).as_posix(): _hash(p) for p in _files(aroot, True)}
        b = {p.relative_to(broot).as_posix(): _hash(p) for p in _files(broot, True)}
        return {"only_left": sorted(a.keys() - b.keys()), "only_right": sorted(b.keys() - a.keys()),
                "changed": sorted(k for k in a.keys() & b.keys() if a[k] != b[k])}
    if args.format == "json":
        changes = _json_changes(read_json(left), read_json(right))
        # Keep JSON structurally valid when limiting large values.
        result, size = [], 0
        for change in changes:
            entry_size = len(json.dumps(change, ensure_ascii=False))
            if size + entry_size > args.max_chars:
                break
            result.append(change)
            size += entry_size
        return {"changes": result, "total_changes": len(changes), "truncated": len(result) != len(changes)}
    try:
        a = left.read_text(encoding=args.encoding).splitlines(keepends=True)
        b = right.read_text(encoding=args.encoding).splitlines(keepends=True)
    except (UnicodeError, LookupError) as exc:
        raise AgfError(f"Cannot decode diff input: {exc}") from exc
    value = "".join(difflib.unified_diff(a, b, fromfile=str(left), tofile=str(right)))
    return {"diff": value[:args.max_chars], "truncated": len(value) > args.max_chars,
            "limitation": "Text diff normalizes newline decoding; use folder hashes for byte differences."}


def register(subparsers):
    parser = subparsers.add_parser("files", help="Preview/apply file batches and compare content")
    commands = parser.add_subparsers(dest="operation", required=True)
    rename = commands.add_parser("rename")
    rename.add_argument("root")
    rename.add_argument("--pattern", required=True)
    rename.add_argument("--replace", default="")
    normalize = commands.add_parser("normalize")
    normalize.add_argument("root")
    normalize.add_argument("--from-encoding", default="utf-8")
    normalize.add_argument("--to-encoding", default="utf-8")
    normalize.add_argument("--newline", choices=["preserve", "lf", "crlf"], default="preserve")
    normalize.add_argument("--glob", default="*")
    for command in (rename, normalize):
        command.add_argument("--recursive", action="store_true")
        command.add_argument("--apply", action="store_true")
        command.add_argument("--plan-output")
        command.set_defaults(func=_plan_handler)
    apply = commands.add_parser("apply")
    apply.add_argument("plan")
    apply.add_argument("--apply", action="store_true")
    apply.set_defaults(func=_apply_handler)
    compare = commands.add_parser("diff")
    compare.add_argument("left")
    compare.add_argument("right")
    compare.add_argument("--format", choices=["text", "json", "folder"], default="text")
    compare.add_argument("--encoding", default="utf-8")
    compare.add_argument("--max-chars", type=int, default=20000)
    compare.set_defaults(func=_diff_handler)

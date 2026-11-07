"""Small shared primitives. No subprocesses or writes at import time."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class AgfError(Exception):
    """An actionable user-facing error."""


def read_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise AgfError(f"Cannot read JSON {path}: {exc}") from exc


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def digest(path: str | Path) -> str:
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(256 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def within(root: str | Path, candidate: str | Path) -> Path:
    """Resolve containment, including existing symlinks; never infer permission."""
    base = Path(root).resolve()
    target = Path(candidate).resolve()
    if not target.is_relative_to(base):
        raise AgfError(f"Path is outside root {base}: {target}")
    return target


def write_text(path: str | Path, text: str, *, overwrite: bool = False) -> Path:
    """Create UTF-8/LF output; refuse existing output unless explicitly allowed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    except OSError as exc:
        raise AgfError(f"Cannot write {target}: {exc}") from exc
    return target

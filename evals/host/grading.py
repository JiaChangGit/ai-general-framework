"""Judge a task's items one by one, by program only.

An item is a dict with an "id", optionally "means" (for people), and one or more conditions, all of
which have to hold:

    answer / answer_not        regexes that must / must not match the last answer (case-insensitive)
    claims / claims_not        [{"match", "unless"}]: some / no sentence of the answer matches "match"
                               without also matching "unless" (a negation or a hedge)
    files / files_not          {path: regexes} that must / must not match; a missing file fails both
    unchanged                  globs: no matching file was changed, created or deleted since the start
    changed_only               globs: every change since the start matches one of them
    python                     a snippet, which only the caller's runner executes
"""
from __future__ import annotations

from fnmatch import fnmatchcase
import hashlib
import os
from pathlib import Path
import re

CONDITIONS = ("answer", "answer_not", "claims", "claims_not", "files", "files_not", "unchanged", "changed_only", "python")
SENTENCE_END = re.compile(r"[。！？!?；;\n]|\.\s")
TEXT_LIMIT = 100_000  # what the regexes see of one text


def fingerprint(root: Path, skip: tuple[str, ...] = ()) -> dict[str, str]:
    """Relative path to content hash, without following links."""
    found = {}
    for top, _, names in os.walk(root, followlinks=False):
        for name in names:
            file = Path(top) / name
            relative = file.relative_to(root).as_posix()
            if relative.startswith(skip):
                continue
            if file.is_symlink():
                found[relative] = "link:" + os.readlink(file)
            elif file.is_file():
                found[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
    return found


def changes(start: dict[str, str], work: Path) -> list[str]:
    now = fingerprint(work)
    return sorted(name for name in start.keys() | now.keys() if start.get(name) != now.get(name))


def validate(items: list[dict]) -> None:
    ids = [item.get("id") for item in items]
    if not all(ids) or len(set(ids)) != len(ids):
        raise ValueError(f"items need distinct ids: {ids}")
    for item in items:
        conditions = set(item) - {"id", "means"}
        if not conditions or not conditions <= set(CONDITIONS):
            raise ValueError(f"item {item['id']}: needs conditions out of {CONDITIONS}, has {sorted(conditions)}")


def _read(work: Path, name: str) -> str | None:
    file = work / name
    if not file.is_file() or not file.resolve().is_relative_to(work.resolve()):
        return None
    return file.read_text(encoding="utf-8", errors="replace")[:TEXT_LIMIT]


def _claimed(answer: str, claim: dict) -> bool:
    match = re.compile(claim["match"], re.IGNORECASE)
    unless = re.compile(claim["unless"], re.IGNORECASE) if claim.get("unless") else None
    return any(match.search(sentence) and not (unless and unless.search(sentence)) for sentence in SENTENCE_END.split(answer))


def _holds(item: dict, work: Path, answer: str, changed: list[str]) -> bool:
    flags = re.IGNORECASE | re.MULTILINE
    if not all(re.search(pattern, answer, flags) for pattern in item.get("answer", [])):
        return False
    if any(re.search(pattern, answer, flags) for pattern in item.get("answer_not", [])):
        return False
    if not all(_claimed(answer, claim) for claim in item.get("claims", [])):
        return False
    if any(_claimed(answer, claim) for claim in item.get("claims_not", [])):
        return False
    for key, wanted in (("files", True), ("files_not", False)):
        for name, patterns in item.get(key, {}).items():
            text = _read(work, name)
            if text is None or any(bool(re.search(pattern, text, re.MULTILINE)) != wanted for pattern in patterns):
                return False
    if any(fnmatchcase(name, glob) for name in changed for glob in item.get("unchanged", [])):
        return False
    allowed = item.get("changed_only")
    return allowed is None or all(any(fnmatchcase(name, glob) for glob in allowed) for name in changed)


def grade(items: list[dict], work: Path, answer: str, start: dict[str, str], run) -> dict[str, bool]:
    """Each item's id and whether it holds. run(item id, code) says whether a snippet passed."""
    validate(items)
    needs_start = any("unchanged" in item or "changed_only" in item for item in items)
    changed, answer = changes(start, work) if needs_start else [], (answer or "")[:TEXT_LIMIT]
    return {item["id"]: _holds(item, work, answer, changed) and ("python" not in item or bool(run(item["id"], item["python"])))
            for item in items}

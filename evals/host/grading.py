"""Judge a task's items one by one, by program only.

An item is a dict with an "id", optionally "means" (for people), and one or more conditions, all of
which have to hold:

    answer / answer_not        regexes that must / must not match the last answer (case-insensitive)
    claims / claims_not        [{"match", "unless"}]: some / no sentence of the answer matches "match"
                               without "unless" (a negation or a hedge) in the same clause
    files / files_not          {path: regexes} that must / must not match; a missing file fails both
    unchanged                  globs: no matching file was changed, created or deleted since the start
    changed_only               globs: every change since the start matches one of them
    python                     a snippet, which only the caller's runner executes
    one_of                     a list of such dicts (without python or one_of): all conditions of one of them hold

What is too long to read whole cannot prove an absence. The regexes see text a subject wrote, so they run in
a child process with a deadline: not finishing is the grader's failure (Undecided), not the subject's.
"""
from __future__ import annotations

from fnmatch import fnmatchcase
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

CONDITIONS = ("answer", "answer_not", "claims", "claims_not", "files", "files_not", "unchanged", "changed_only", "python", "one_of")
SENTENCE_END = re.compile(r"[。！？!?；;\n]|\.\s")
CLAUSE_END = re.compile(r"[，,](?!\d)")
TEXT_LIMIT = 100_000  # what the regexes see of one text
DEADLINE = 10  # seconds for all regexes of one run


class Undecided(Exception):
    pass


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
        try:
            _validate_types(item)
        except (TypeError, KeyError, AttributeError, re.error) as error:
            raise ValueError(f"item {item['id']}: {type(error).__name__}: {error}") from None


def _strings(value) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(entry, str) for entry in value):
        raise TypeError(f"not a list of strings: {value!r}")
    return value


def _validate_types(item: dict) -> None:
    patterns = []
    for key in ("answer", "answer_not"):
        patterns += _strings(item[key]) if key in item else []
    for key in ("unchanged", "changed_only"):
        if key in item:
            _strings(item[key])
    for key in ("files", "files_not"):
        if key in item:
            if not item[key]:
                raise TypeError(f"{key} is empty")
            for values in item[key].values():
                patterns += _strings(values)
    for key in ("claims", "claims_not"):
        if key in item:
            if not isinstance(item[key], list) or not item[key]:
                raise TypeError(f"{key} is not a list")
            for claim in item[key]:
                patterns += [claim["match"], *([claim["unless"]] if claim.get("unless") else [])]
    if "one_of" in item:
        if not isinstance(item["one_of"], list) or not item["one_of"]:
            raise TypeError("one_of is not a list")
        for option in item["one_of"]:
            if not option or not set(option) <= set(CONDITIONS) - {"python", "one_of"}:
                raise TypeError(f"one_of cannot have {sorted(option)}")
            _validate_types(option)
    if "python" in item and not isinstance(item["python"], str):
        raise TypeError("python is not a string")
    for pattern in patterns:
        re.compile(pattern)


def _read(work: Path, name: str) -> tuple[str, bool] | None:
    """What the regexes see of a file, and whether that is all of it."""
    file = work / name
    try:
        if not file.is_file() or not file.resolve().is_relative_to(work.resolve()):
            return None
        text = file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return text[:TEXT_LIMIT], len(text) <= TEXT_LIMIT


def _claimed(answer: str, claim: dict) -> bool:
    match = re.compile(claim["match"], re.IGNORECASE)
    unless = re.compile(claim["unless"], re.IGNORECASE) if claim.get("unless") else None
    for sentence in SENTENCE_END.split(answer):
        for found in match.finditer(sentence):
            if not unless:
                return True
            cuts = [cut.start() for cut in CLAUSE_END.finditer(sentence)]
            first = max((cut + 1 for cut in cuts if cut < found.start()), default=0)
            last = min((cut for cut in cuts if cut >= found.end()), default=len(sentence))
            if not unless.search(sentence[first:last]):
                return True
    return False


def _holds(item: dict, work: Path, answer: str, whole: bool, changed: list[str]) -> bool:
    flags = re.IGNORECASE | re.MULTILINE
    if "one_of" in item and not any(_holds(option, work, answer, whole, changed) for option in item["one_of"]):
        return False
    if not whole and ("answer_not" in item or "claims_not" in item):
        return False
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
            read = _read(work, name)
            if read is None or (not wanted and not read[1]):
                return False
            if any(bool(re.search(pattern, read[0], re.MULTILINE)) != wanted for pattern in patterns):
                return False
    if any(fnmatchcase(name, glob) for name in changed for glob in item.get("unchanged", [])):
        return False
    allowed = item.get("changed_only")
    return allowed is None or all(any(fnmatchcase(name, glob) for glob in allowed) for name in changed)


def _apart(given: dict) -> list[bool]:
    try:
        done = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve())], input=json.dumps(given).encode("ascii"),
                              capture_output=True, timeout=DEADLINE)
    except subprocess.TimeoutExpired:
        raise Undecided("the grader's regexes did not finish") from None
    if done.returncode != 0:
        raise Undecided("the grader's process failed")
    return json.loads(done.stdout)


def grade(items: list[dict], work: Path, answer: str, start: dict[str, str], run) -> dict[str, bool]:
    """Each item's id and whether it holds. run(item id, code) says whether a snippet passed."""
    validate(items)
    parts = [part for item in items for part in (item, *item.get("one_of", []))]
    needs_start = any("unchanged" in part or "changed_only" in part for part in parts)
    answer = answer or ""
    held = _apart({"items": items, "work": str(work), "answer": answer[:TEXT_LIMIT], "whole": len(answer) <= TEXT_LIMIT,
                   "changed": changes(start, work) if needs_start else []})
    return {item["id"]: ok and ("python" not in item or bool(run(item["id"], item["python"])))
            for item, ok in zip(items, held)}


if __name__ == "__main__":
    asked = json.loads(sys.stdin.buffer.read())
    print(json.dumps([_holds(item, Path(asked["work"]), asked["answer"], asked["whole"], asked["changed"]) for item in asked["items"]]))

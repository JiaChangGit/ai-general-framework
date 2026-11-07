"""Static package checks. Behavioral evals are deliberately separate."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re


def _description(value):
    """Validate this package's deliberately small one-line YAML subset."""
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except ValueError:
            return False
        return isinstance(parsed, str) and bool(parsed.strip())
    if value.startswith("'"):
        return bool(re.fullmatch(r"'(?:[^']|'')+'", value))
    return bool(value.strip()) and not (re.search(r":\s|\s#", value) or value[0] in "[{}]*&!|>#?" or value.lower() in {"true", "false", "null", "~"})


def audit(root):
    directory = Path(root).resolve()
    errors = []
    warnings = []
    names = set()
    skills = []
    for path in sorted((directory / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8-sig")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors.append(f"{path}: missing frontmatter")
            continue
        header, body = text[4:].split("\n---\n", 1)
        name = re.search(r"^name:\s*([a-z0-9-]+)\s*$", header, re.M)
        description = re.search(r"^description:\s*(\S.*)$", header, re.M)
        if not name or not description or not _description(description.group(1)):
            errors.append(f"{path}: name and one-line description required")
            continue
        value = name.group(1)
        if value != path.parent.name or value in names:
            errors.append(f"{path}: duplicate name or name/folder mismatch")
        names.add(value)
        skills.append({"name": value, "entry_characters": len(body), "description_characters": len(description.group(1))})
        if len(body) > 10000:
            warnings.append(f"{value}: consider moving conditional detail to references")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            target = target.strip("<>")
            if target.startswith(("http:", "https:", "#", "mailto:")):
                continue
            local = target.split("#", 1)[0]
            if local and not (path.parent / local).is_file():
                errors.append(f"{path}: missing linked file {local}")
    if not skills:
        errors.append("No valid skills found.")
    python_files = 0
    json_files = 0
    for folder in ("agf", "scripts", "tests"):
        for path in (directory / folder).rglob("*.py"):
            python_files += 1
            try:
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            except (SyntaxError, UnicodeError) as exc:
                errors.append(str(exc))
    for folder in ("templates", "adapters", "evals"):
        for path in (directory / folder).rglob("*.json"):
            json_files += 1
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
            except (ValueError, UnicodeError) as exc:
                errors.append(f"{path}: {exc}")
    markdown = [directory / "README.md", directory / "AGENTS.md"]
    for folder in ("skills", "docs", "examples", "evals"):
        markdown.extend((directory / folder).rglob("*.md"))
    for path in markdown:
        if not path.is_file() or path.name == "SKILL.md":
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8-sig")):
            target = target.strip("<>")
            if target.startswith(("https:", "http:", "#", "mailto:")):
                continue
            local = target.split("#", 1)[0]
            if local and not (path.parent / local).is_file():
                errors.append(f"{path}: missing linked file {local}")
    return {"status": "PASS" if not errors else "FAIL", "skills": skills,
            "python_files": python_files, "json_files": json_files, "errors": errors, "warnings": warnings,
            "meaning": "Static structure, supported frontmatter fields, local links and Python/JSON syntax only. Does not measure routing, reasoning, prose or learning.",
            "_exit_code": 1 if errors else 0}


def register(subparsers):
    parser = subparsers.add_parser("audit", help="Check package structure, syntax and skill links")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.set_defaults(func=lambda args: audit(args.root))

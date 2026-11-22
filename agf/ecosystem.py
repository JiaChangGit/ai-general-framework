"""Checks and generated tables for the external-resource catalog in docs/ecosystem/.

The catalog keeps one source of truth, entries.json. Markdown pages carry
hand-written analysis plus generated tables between markers; `check` fails
when a table no longer matches the data, `render` rewrites the tables.
`refresh` asks the GitHub API (through an already logged-in `gh`) for
repository facts; `find` gives a bounded keyword search. Run from the
framework root:  python -m agf.ecosystem check|render|refresh|find
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys

from .common import AgfError, json_text

CATALOG = Path("docs") / "ecosystem"
TYPES = {"project": "專案", "skill": "skill", "skill-collection": "skill 集", "mcp": "MCP", "cli": "CLI",
         "library": "函式庫", "api": "API", "service": "服務", "app": "應用", "dataset-source": "資料集來源",
         "article": "文章", "paper": "論文", "catalog": "目錄", "benchmark": "評測"}
LICENSE_LABELS = {"usable": "可使用", "conditional": "有條件", "needs-review": "需人工確認", "not-recommended": "不建議"}
EVIDENCE = {"ran": "實際執行", "source": "讀原始碼", "docs": "讀文件", "search": "只有搜尋摘要"}
CONFIDENCE = {"high", "medium", "low"}
USES = {"direct", "integrate", "learn", "borrow", "study-only", "needs-review"}
HOST_SUPPORT = {"yes", "partial", "no", "unknown"}
RUNS = {"local", "cloud", "hybrid", "unknown"}
LEVELS = {"READ", "CLONED", "SEARCH-ONLY", "RAN"}  # for https references; a path reference uses RECORD
REQUIRED = ("id", "name", "category", "type", "urls", "summary", "license", "tier", "evidence", "confidence",
            "checked", "references")
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
GITHUB = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:/.*)?$")
BLOCK = re.compile(r"(<!-- ecosystem:(table|index|tier1)(?: ([a-z0-9-]+))? -->\n)(.*?)(<!-- /ecosystem -->)", re.S)


def load(root):
    path = Path(root) / CATALOG / "entries.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise AgfError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list) or not isinstance(data.get("categories"), dict):
        raise AgfError(f"{path}: expected an object with 'categories' and 'entries'")
    return data


def _entry_errors(entry, ids, categories, root=None):
    where = entry.get("id", "<no id>") if isinstance(entry, dict) else "<not an object>"
    if not isinstance(entry, dict):
        return [f"{where}: entry must be an object"]
    errors = [f"{where}: missing {key}" for key in REQUIRED if entry.get(key) in (None, "", [])]
    if errors:
        return errors
    if not ID.fullmatch(entry["id"]):
        errors.append(f"{where}: id must be lowercase words joined by hyphens")
    if entry["category"] not in categories:
        errors.append(f"{where}: unknown category {entry['category']}")
    errors += [f"{where}: unknown category in also: {name}" for name in entry.get("also", []) if name not in categories]
    if entry["type"] not in TYPES:
        errors.append(f"{where}: unknown type {entry['type']}")
    if type(entry["tier"]) is not int or entry["tier"] not in (1, 2, 3, 4):
        errors.append(f"{where}: tier must be 1-4")
    if entry["evidence"] not in EVIDENCE:
        errors.append(f"{where}: unknown evidence {entry['evidence']}")
    if entry["confidence"] not in CONFIDENCE:
        errors.append(f"{where}: unknown confidence {entry['confidence']}")
    if not DAY.fullmatch(str(entry["checked"])):
        errors.append(f"{where}: checked must be YYYY-MM-DD")
    urls = entry["urls"]
    if not isinstance(urls, dict) or not any(isinstance(urls.get(k), str) and urls[k].startswith("https://") for k in ("source", "official", "docs")):
        errors.append(f"{where}: needs at least one https URL in urls.source, urls.official or urls.docs")
    license_ = entry["license"]
    if not isinstance(license_, dict) or license_.get("label") not in LICENSE_LABELS:
        errors.append(f"{where}: license.label must be one of {sorted(LICENSE_LABELS)}")
    errors += [f"{where}: unknown use {name}" for name in entry.get("use", []) if name not in USES]
    hosts = entry.get("hosts") or {}
    if hosts.get("claude_code") not in (None, *HOST_SUPPORT):
        errors.append(f"{where}: hosts.claude_code must be one of {sorted(HOST_SUPPORT)}")
    if entry.get("runs") not in (None, *RUNS):
        errors.append(f"{where}: runs must be one of {sorted(RUNS)}")
    errors += [f"{where}: alternative {name} is not an entry id" for name in entry.get("alternatives", []) if name not in ids]
    for reference in entry["references"]:
        if not isinstance(reference, dict):
            errors.append(f"{where}: each reference must be an object")
            break
        if "path" in reference:  # an earlier record inside this framework, relative to its root
            path = str(reference["path"])
            if reference.get("level") != "RECORD" or path.startswith(("/", "\\")) or ".." in Path(path).parts:
                errors.append(f"{where}: a path reference needs level RECORD and a path relative to the framework root")
                break
            if root is not None and not (Path(root) / path).is_file():
                errors.append(f"{where}: referenced record {path} does not exist")
            continue
        if not str(reference.get("url", "")).startswith("https://") or reference.get("level") not in LEVELS:
            errors.append(f"{where}: each reference needs an https url and a level in {sorted(LEVELS)}, or a RECORD path")
            break
    return errors


def _cell(text):
    return re.sub(r"\s+", " ", str(text)).replace("|", "\\|").strip()


def _link(entry):
    urls = entry["urls"]
    target = urls.get("source") or urls.get("official") or urls.get("docs")
    return f"[{_cell(entry['name'])}]({target})"


def _activity(entry):
    github = entry.get("github") or {}
    if github.get("archived"):
        return "已封存"
    return (github.get("pushed_at") or "")[:10] or "—"


def _license(entry):
    license_ = entry["license"]
    spdx = license_.get("spdx")
    label = LICENSE_LABELS.get(license_.get("label"), "?")
    return f"{label}（{_cell(spdx)}）" if spdx else label


def _sorted(entries):
    return sorted(entries, key=lambda e: (e["tier"], e["name"].lower()))


def _table(entries):
    rows = ["| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |", "|---|---|---|---|---|---|---|"]
    for entry in _sorted(entries):
        rows.append(f"| {_link(entry)} | {TYPES[entry['type']]} | {entry['tier']} | {_license(entry)} | "
                    f"{_activity(entry)} | {EVIDENCE[entry['evidence']]} | {_cell(entry['summary'])} |")
    return "\n".join(rows) + "\n"


def _index(data):
    counts = {}
    for entry in data["entries"]:
        bucket = counts.setdefault(entry["category"], [0, 0, 0, 0])
        bucket[entry["tier"] - 1] += 1
    rows = ["| 分類 | 項目 | Tier 1 | Tier 2 | Tier 3 | Tier 4 |", "|---|---|---|---|---|---|"]
    for key, category in data["categories"].items():
        tiers = counts.get(key, [0, 0, 0, 0])
        rows.append(f"| [{_cell(category['title'])}]({category['page']}) | {sum(tiers)} | " + " | ".join(map(str, tiers)) + " |")
    return "\n".join(rows) + "\n"


def _tier1(data):
    rows = ["| 名稱 | 分類 | 授權 | 證據 | 對框架的價值 |", "|---|---|---|---|---|"]
    for entry in _sorted(e for e in data["entries"] if e["tier"] == 1):
        page = data["categories"][entry["category"]]["page"]
        value = entry.get("integration_value") or entry["summary"]
        rows.append(f"| {_link(entry)} | [{_cell(data['categories'][entry['category']]['title'])}]({page}) | "
                    f"{_license(entry)} | {EVIDENCE[entry['evidence']]} | {_cell(value)} |")
    return "\n".join(rows) + "\n"


def _pages(root, data):
    folder = Path(root) / CATALOG
    paths = [folder / "README.md"] + [folder / c["page"] for c in data["categories"].values()]
    paths += sorted((folder / "comparisons").glob("*.md")) + sorted(folder.glob("*.md"))
    seen, result = set(), []
    for path in paths:
        if path not in seen and path.is_file():
            seen.add(path)
            result.append(path)
    return result


def _render_text(text, data, path):
    def replace(match):
        kind, name = match.group(2), match.group(3)
        if kind == "index":
            body = _index(data)
        elif kind == "tier1":
            body = _tier1(data)
        else:
            if name not in data["categories"]:
                raise AgfError(f"{path}: table marker names unknown category {name}")
            body = _table([e for e in data["entries"] if e["category"] == name])
        return match.group(1) + body + match.group(5)
    return BLOCK.sub(replace, text)


def check(root):
    folder = Path(root) / CATALOG
    if not (folder / "entries.json").is_file():
        return {"status": "SKIPPED", "errors": [], "warnings": [], "entries": 0}
    errors, warnings = [], []
    try:
        data = load(root)
    except AgfError as exc:
        return {"status": "FAIL", "errors": [str(exc)], "warnings": [], "entries": 0}
    for key, category in data["categories"].items():
        if not ID.fullmatch(key) or not isinstance(category, dict) or not category.get("title") or not category.get("page"):
            errors.append(f"category {key}: needs a lowercase id, a title and a page")
        elif not (folder / category["page"]).is_file():
            errors.append(f"category {key}: missing page {category['page']}")
    if errors:
        return {"status": "FAIL", "errors": errors, "warnings": warnings, "entries": len(data["entries"])}
    errors += check_entries(data, root)
    if not errors:
        for path in _pages(root, data):
            text = path.read_text(encoding="utf-8-sig")
            try:
                if _render_text(text, data, path) != text:
                    errors.append(f"{path}: generated table is out of date; run python -m agf.ecosystem render")
            except AgfError as exc:
                errors.append(str(exc))
        for key, category in data["categories"].items():
            if "<!-- ecosystem:table " + key + " -->" not in (folder / category["page"]).read_text(encoding="utf-8-sig"):
                warnings.append(f"category {key}: page has no generated table")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings, "entries": len(data["entries"])}


def render(root):
    data = load(root)
    problems = check_entries(data, root)
    if problems:
        raise AgfError("Fix entries.json first: " + "; ".join(problems[:5]))
    changed = []
    for path in _pages(root, data):
        text = path.read_text(encoding="utf-8-sig")
        new = _render_text(text, data, path)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            changed.append(str(path))
    return {"status": "DONE", "changed": changed}


def check_entries(data, root=None):
    ids = [e.get("id") for e in data["entries"] if isinstance(e, dict)]
    errors = [f"duplicate id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for entry in data["entries"]:
        errors += _entry_errors(entry, set(ids), data["categories"], root)
    return errors


def _gh(arguments):
    completed = subprocess.run(["gh", *arguments], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if completed.returncode != 0:
        raise AgfError(completed.stderr.strip() or f"gh exited {completed.returncode}")
    return json.loads(completed.stdout)


def refresh(root, only=None, runner=_gh, today=None):
    """Store GitHub facts under entry["github"]; other fields stay as written."""
    path = Path(root) / CATALOG / "entries.json"
    data = load(root)
    today = today or date.today().isoformat()
    updated, failed = [], []
    for entry in data["entries"]:
        if only and entry["id"] not in only:
            continue
        match = GITHUB.match(str((entry.get("urls") or {}).get("source") or ""))
        if not match:
            continue
        owner, repo = match.groups()
        try:
            facts = runner(["api", f"repos/{owner}/{repo}", "--jq",
                            "{full_name,pushed_at,archived,stars:.stargazers_count,license:.license.spdx_id}"])
        except (AgfError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
            failed.append({"id": entry["id"], "error": str(exc)[:200]})
            continue
        if not isinstance(facts, dict):
            failed.append({"id": entry["id"], "error": "unexpected answer from gh"})
            continue
        facts["fetched"] = today
        entry["github"] = facts
        updated.append(entry["id"])
    path.write_text(json_text(data), encoding="utf-8", newline="\n")
    return {"status": "DONE" if not failed else "PARTIAL", "updated": len(updated), "failed": failed,
            "_exit_code": 0 if not failed else 1}


def find(root, terms, limit=10):
    data = load(root)
    words = [t.lower() for t in terms]
    hits = []
    for entry in data["entries"]:
        haystack = " ".join(str(entry.get(k) or "") for k in ("id", "name", "category", "summary", "learning_value", "integration_value")).lower()
        haystack += " " + " ".join(entry.get("also", []))
        score = sum(haystack.count(w) for w in words)
        if score and all(w in haystack for w in words):
            hits.append((score, entry))
    hits.sort(key=lambda pair: (-pair[0], pair[1]["tier"], pair[1]["name"].lower()))
    page = lambda e: str(CATALOG / data["categories"][e["category"]]["page"])
    return {"status": "DONE", "total": len(hits), "shown": min(limit, len(hits)),
            "results": [{"id": e["id"], "name": e["name"], "tier": e["tier"], "category": e["category"], "page": page(e),
                         "license": e["license"].get("label"), "checked": e["checked"], "summary": e["summary"]}
                        for _, e in hits[:limit]]}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m agf.ecosystem", description="Maintain docs/ecosystem/.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    children = parser.add_subparsers(dest="command", required=True)
    children.add_parser("check", help="Validate entries.json and generated tables")
    children.add_parser("render", help="Rewrite generated tables from entries.json")
    refresh_parser = children.add_parser("refresh", help="Fetch GitHub facts with the logged-in gh CLI (read-only API calls)")
    refresh_parser.add_argument("--id", action="append", help="Only these entry ids")
    find_parser = children.add_parser("find", help="Bounded keyword search")
    find_parser.add_argument("terms", nargs="+")
    find_parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if args.command == "check":
            result = check(args.root)
            result["_exit_code"] = 0 if result["status"] in ("PASS", "SKIPPED") else 1
        elif args.command == "render":
            result = render(args.root)
        elif args.command == "refresh":
            result = refresh(args.root, set(args.id) if args.id else None)
        else:
            result = find(args.root, args.terms, max(1, min(args.limit, 50)))
    except AgfError as exc:
        result = {"status": "ERROR", "error": str(exc), "_exit_code": 2}
    code = result.pop("_exit_code", 0)
    sys.stdout.write(json_text(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

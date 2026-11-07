"""Local document excerpts with content identity and physical source anchors."""

from __future__ import annotations

import difflib
import hashlib
from html.parser import HTMLParser
from pathlib import Path

from .common import AgfError


class SourceUnavailable(AgfError):
    pass


def _hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.entries = []
        self.ignored = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.ignored.append(tag)

    def handle_endtag(self, tag):
        if tag in self.ignored:
            self.ignored.remove(tag)

    def handle_data(self, data):
        if self.ignored:
            return
        start = self.getpos()[0]
        for offset, line in enumerate(data.splitlines()):
            if line.strip():
                self.entries.append({"anchor": f"line:{start + offset}", "line": start + offset, "text": line.strip()})


def load_source(path: str | Path, pages: str | None = None, metadata_only: bool = False) -> dict:
    path = Path(path)
    if not path.is_file():
        raise AgfError(f"Local source not found: {path}")
    suffix = path.suffix.lower()
    result = {"source": str(path.resolve()), "sha256": _hash(path)}
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise SourceUnavailable("PDF extraction is UNAVAILABLE: optional pypdf is not installed; no package was installed") from exc
        try:
            reader = PdfReader(str(path))
            if reader.is_encrypted:
                raise AgfError("Encrypted PDF is not supported; provide an authorized decrypted local copy")
            total_pages = len(reader.pages)
            selected = _page_selection(pages, total_pages) if pages else set(range(1, total_pages + 1))
            entries = [{"anchor": f"page:{index}", "page": index,
                        "text": "" if metadata_only else (reader.pages[index - 1].extract_text() or "")}
                       for index in sorted(selected)]
        except AgfError:
            raise
        except Exception as exc:
            raise AgfError(f"Cannot extract PDF: {exc}") from exc
        result.update({"format": "pdf", "entries": entries, "total_units": total_pages,
                       "text_extracted": not metadata_only, "anchor_basis": "1-based physical PDF page",
                       "limitations": ["Physical PDF pages may differ from printed page labels.",
                                        "Text extraction does not verify tables, figures, formulas or reading order.",
                                        "No OCR is performed; image-only pages can have empty text."]})
    elif suffix in {".html", ".htm", ".txt", ".md", ".rst", ".log"}:
        if pages:
            raise AgfError("--pages applies only to PDF sources")
        if path.stat().st_size > 50_000_000:
            raise AgfError("Text source exceeds 50 MB; select a smaller local source")
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError as exc:
            raise AgfError("Source must be UTF-8; use an explicit encoding conversion first") from exc
        if suffix in {".html", ".htm"}:
            parser = _HTMLText()
            parser.feed(text)
            entries, format = parser.entries, "html"
            limitations = ["Static HTML text only; scripts, styles, layout and browser-rendered content are not evaluated.",
                           "Line anchors refer to the original HTML source, not browser display lines."]
        else:
            entries = [{"anchor": f"line:{index + 1}", "line": index + 1, "text": line}
                       for index, line in enumerate(text.splitlines())]
            format, limitations = "text", []
        result.update({"format": format, "entries": entries, "anchor_basis": "1-based original source line", "limitations": limitations})
    else:
        raise AgfError("Supported local sources: PDF, HTML, UTF-8 TXT/MD/RST/LOG")
    return result


def _unavailable(exc):
    return {"status": "UNAVAILABLE", "detail": str(exc), "_exit_code": 3}


def _inspect(args):
    try:
        source = load_source(args.input, metadata_only=True)
    except SourceUnavailable as exc:
        return _unavailable(exc)
    entries = source.pop("entries")
    return {"status": "INSPECTED", **source, "units": len(entries),
            "empty_units": None if source.get("text_extracted") is False else sum(not unit["text"].strip() for unit in entries)}


def _page_selection(value: str, total: int) -> set[int]:
    selected = set()
    try:
        for part in value.split(","):
            bounds = part.strip().split("-")
            if len(bounds) > 2:
                raise ValueError()
            first, last = int(bounds[0]), int(bounds[-1])
            if not 1 <= first <= last <= total:
                raise ValueError()
            selected.update(range(first, last + 1))
    except ValueError as exc:
        raise AgfError(f"Pages must be within 1..{total}, for example 2,4-6") from exc
    return selected


def _excerpt(args):
    if args.limit < 1 or args.max_chars < 1 or args.context < 0 or args.start_line < 1:
        raise AgfError("limit, max-chars and start-line must be positive; context cannot be negative")
    if args.end_line is not None and args.end_line < args.start_line:
        raise AgfError("end-line must not precede start-line")
    if args.query == "":
        raise AgfError("Query cannot be empty")
    try:
        source = load_source(args.input, pages=args.pages)
    except SourceUnavailable as exc:
        return _unavailable(exc)
    entries = source.pop("entries")
    if args.pages and source["format"] != "pdf":
        raise AgfError("--pages applies only to PDF sources")
    if source["format"] == "pdf" and (args.start_line != 1 or args.end_line is not None):
        raise AgfError("Use --pages for a PDF, not line selectors")
    pages = _page_selection(args.pages, source.get("total_units", len(entries))) if args.pages else None
    query = args.query.casefold() if args.query else None
    matches = []
    for entry in entries:
        if pages is not None and entry["page"] not in pages:
            continue
        if "line" in entry and (entry["line"] < args.start_line or (args.end_line is not None and entry["line"] > args.end_line)):
            continue
        text = entry["text"]
        if not text.strip():
            continue
        if query:
            index = text.casefold().find(query)
            if index < 0:
                continue
            # Casefold may change character counts; keep the whole unit when
            # this happens rather than inventing a precise character offset.
            if len(text.casefold()) == len(text):
                start, end = max(0, index - args.context), min(len(text), index + len(args.query) + args.context)
                text = text[start:end]
        matches.append({k: v for k, v in entry.items() if k != "text"} | {"text": text})
    excerpts, used = [], 0
    for entry in matches[:args.limit]:
        available = args.max_chars - used
        if available <= 0:
            break
        clipped = len(entry["text"]) > available
        excerpts.append({**entry, "text": entry["text"][:available], "truncated": clipped})
        used += len(excerpts[-1]["text"])
        if clipped:
            break
    return {"status": "EXCERPTED", **source, "query": args.query, "matches": len(matches), "excerpts": excerpts,
            "truncated": len(excerpts) < len(matches) or any(e["truncated"] for e in excerpts), "text_characters": used}


def _diff(args):
    if args.limit < 1 or args.max_chars < 1:
        raise AgfError("limit and max-chars must be positive")
    try:
        left, right = load_source(args.before), load_source(args.after)
    except SourceUnavailable as exc:
        return _unavailable(exc)
    a, b = left.pop("entries"), right.pop("entries")
    aa = [" ".join(unit["text"].split()) for unit in a]
    bb = [" ".join(unit["text"].split()) for unit in b]
    operations = [operation for operation in difflib.SequenceMatcher(a=aa, b=bb, autojunk=False).get_opcodes() if operation[0] != "equal"]
    changes, used = [], 0
    for kind, i, j, k, l in operations[:args.limit]:
        available = args.max_chars - used
        if available < 1:
            break
        before, after = "\n".join(aa[i:j]), "\n".join(bb[k:l])
        first = before[:available]
        second = after[:available - len(first)]
        changes.append({"kind": kind, "before_anchors": [u["anchor"] for u in a[i:j]],
                        "after_anchors": [u["anchor"] for u in b[k:l]], "before": first, "after": second,
                        "truncated": len(first) < len(before) or len(second) < len(after)})
        used += len(first) + len(second)
    return {"status": "CANDIDATE_DIFF", "before": left, "after": right, "changes": changes,
            "total_change_groups": len(operations),
            "truncated": len(changes) != len(operations) or any(c["truncated"] for c in changes),
            "limitation": "Whitespace-normalized text candidates only. Reflow/extraction may mislead; no semantic or spec-compliance judgment."}


def register(subparsers):
    parser = subparsers.add_parser("source", help="Fetch bounded static pages and inspect local documents with anchors")
    commands = parser.add_subparsers(dest="source_operation", required=True)
    from . import webfetch
    webfetch.register(commands)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("input")
    inspect.set_defaults(func=_inspect)
    excerpt = commands.add_parser("excerpt")
    excerpt.add_argument("input")
    excerpt.add_argument("--query")
    excerpt.add_argument("--pages")
    excerpt.add_argument("--start-line", type=int, default=1)
    excerpt.add_argument("--end-line", type=int)
    excerpt.add_argument("--context", type=int, default=180)
    excerpt.add_argument("--limit", type=int, default=10)
    excerpt.add_argument("--max-chars", type=int, default=6000)
    excerpt.set_defaults(func=_excerpt)
    diff = commands.add_parser("diff")
    diff.add_argument("before")
    diff.add_argument("after")
    diff.add_argument("--limit", type=int, default=20)
    diff.add_argument("--max-chars", type=int, default=6000)
    diff.set_defaults(func=_diff)

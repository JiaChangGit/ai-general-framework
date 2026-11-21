"""Find and prevent AI-tool traces in a Git project. Reads by default; never rewrites history.

`check` reports AI tool files that Git tracks, commit messages with AI co-author or
"Generated with" lines, the same markers inside tracked files, and whether the local
exclude block is in place. `exclude` adds a marked block of patterns to the repository's
own `.git/info/exclude` (local to this clone, never committed); `remove` takes it out.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

from .common import AgfError

BEGIN = "# >>> agf: AI tool files stay local (agf traces) >>>"
END = "# <<< agf <<<"
PATTERNS = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".claude/", ".agents/", ".agf/", ".ai/",
            ".codex/", ".gemini/", ".opencode/", ".cursor/", "/.github/copilot-instructions.md")
NAMES = {"CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules"}
FOLDERS = {".claude", ".agents", ".agf", ".ai", ".codex", ".gemini", ".opencode", ".cursor"}
TOOLS = r"claude|anthropic|codex|openai|chatgpt|gpt|gemini|copilot|cursor|aider|devin|windsurf"
COMMIT_MARKERS = re.compile(rf"^\s*co-authored-by:[^\n]*\b({TOOLS})\b|generated (with|by) \[?({TOOLS})|\U0001F916",
                            re.IGNORECASE | re.MULTILINE)
FILE_MARKERS = r"generated with \[?claude code|co-authored-by: *claude|🤖 generated with"


def _git(root: Path, *arguments: str, check: bool = True) -> str:
    try:
        completed = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgfError(f"git failed: {exc}") from exc
    if check and completed.returncode != 0:
        raise AgfError(f"git {' '.join(arguments)} failed: {completed.stderr.strip()[:300]}")
    return completed.stdout


def is_repository(root: Path) -> bool:
    try:
        return _git(root, "rev-parse", "--is-inside-work-tree", check=False).strip() == "true"
    except AgfError:
        return False


def is_toplevel(root: Path) -> bool:
    """Only a work tree's own root is changed: a project nested in another repository
    would otherwise edit the outer repository's exclude file (found in S17 testing)."""
    if not is_repository(root):
        return False
    top = _git(root, "rev-parse", "--show-toplevel", check=False).strip()
    return bool(top) and Path(top).resolve() == root.resolve()


def _exclude_file(root: Path) -> Path:
    path = Path(_git(root, "rev-parse", "--git-path", "info/exclude").strip())
    return path if path.is_absolute() else root / path


def ai_file(path: str) -> bool:
    parts = path.split("/")
    return parts[-1] in NAMES or any(part in FOLDERS for part in parts[:-1]) or path == ".github/copilot-instructions.md"


def _block() -> str:
    return "\n".join((BEGIN, *PATTERNS, END)) + "\n"


def _without_block(text: str) -> tuple[str, bool]:
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.DOTALL)
    stripped, count = pattern.subn("", text)
    return stripped, bool(count)


def check(target, max_commits: int = 5000, max_items: int = 20) -> dict:
    root = Path(target).resolve()
    if not is_repository(root):
        return {"status": "NOT_GIT", "target": str(root), "meaning": "Not a Git work tree; nothing was checked.", "_exit_code": 0}
    tracked = [p for p in _git(root, "ls-files", "-z").split("\0") if p and ai_file(p)]
    log = _git(root, "log", f"-n{max_commits}", "--format=%h%x1f%B%x1e", check=False)
    commits = [entry.split("\x1f", 1)[0].strip() for entry in log.split("\x1e")
               if "\x1f" in entry and COMMIT_MARKERS.search(entry.split("\x1f", 1)[1])]
    grep = _git(root, "grep", "-I", "-n", "-i", "-E", FILE_MARKERS, check=False)
    markers = [line[:200] for line in grep.splitlines() if line and not ai_file(line.split(":", 1)[0])]
    exclude_path = _exclude_file(root)
    excluded = exclude_path.is_file() and BEGIN in exclude_path.read_text(encoding="utf-8", errors="replace")
    found = bool(tracked or commits or markers)
    return {
        "status": "FOUND" if found else "CLEAN", "target": str(root),
        "tracked_ai_files": {"count": len(tracked), "paths": tracked[:max_items]},
        "untrack_command": ["git", "rm", "-r", "--cached", "--", *tracked[:max_items]] if tracked else None,
        "commits_with_ai_markers": {"count": len(commits), "checked": min(max_commits, log.count("\x1e")), "examples": commits[:max_items]},
        "file_markers": {"count": len(markers), "lines": markers[:max_items]},
        "exclude_block": excluded, "exclude_file": str(exclude_path),
        "meaning": "Read-only. untrack_command keeps the files on disk and only removes them from the index. "
                   "Commit history is reported, never rewritten; whether to rewrite unpushed history is the user's decision.",
        "_exit_code": 1 if found or not excluded else 0,
    }


def exclude(target, apply: bool = False) -> dict:
    root = Path(target).resolve()
    if not is_repository(root):
        return {"status": "NOT_GIT", "target": str(root), "applied": False}
    if not is_toplevel(root):
        return {"status": "NESTED", "target": str(root), "applied": False,
                "meaning": "Inside another repository; its exclude file was not changed. Run this at that repository's root if wanted."}
    path = _exclude_file(root)
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    stripped, present = _without_block(text)
    updated = (stripped if not stripped or stripped.endswith("\n") else stripped + "\n") + _block()
    if updated == text:
        return {"status": "UNCHANGED", "target": str(root), "exclude_file": str(path), "applied": False}
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8", newline="\n")
    return {"status": "UPDATED" if present else "ADDED", "target": str(root), "exclude_file": str(path),
            "patterns": list(PATTERNS), "applied": apply}


def remove(target, apply: bool = False) -> dict:
    root = Path(target).resolve()
    if not is_repository(root):
        return {"status": "NOT_GIT", "target": str(root), "applied": False}
    if not is_toplevel(root):
        return {"status": "NESTED", "target": str(root), "applied": False,
                "meaning": "Inside another repository; its exclude file was not changed. Run this at that repository's root if wanted."}
    path = _exclude_file(root)
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    stripped, present = _without_block(text)
    if not present:
        return {"status": "UNCHANGED", "target": str(root), "exclude_file": str(path), "applied": False}
    if apply:
        path.write_text(stripped, encoding="utf-8", newline="\n")
    return {"status": "REMOVED", "target": str(root), "exclude_file": str(path), "applied": apply}


def register(subparsers) -> None:
    command = subparsers.add_parser("traces", help="Find AI-tool traces in a Git project and keep AI tool files local")
    operations = command.add_subparsers(dest="operation", required=True)
    probe = operations.add_parser("check", help="Read-only report: tracked AI files, AI commit markers, markers in files, exclude block")
    probe.add_argument("--target", default=".")
    probe.add_argument("--max-commits", type=int, default=5000)
    probe.set_defaults(func=lambda args: check(args.target, max(1, args.max_commits)))
    for name, function in (("exclude", exclude), ("remove", remove)):
        parser = operations.add_parser(name, help=f"{'Add' if name == 'exclude' else 'Remove'} the marked block in .git/info/exclude (preview unless --apply)")
        parser.add_argument("--target", default=".")
        parser.add_argument("--apply", action="store_true")
        parser.set_defaults(func=lambda args, f=function: f(args.target, args.apply))

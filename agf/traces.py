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
TOOLS = (r"claude(?: code)?|anthropic|openai(?: codex)?|codex(?: cli)?|chatgpt|gpt-\d[\w.-]*|gemini(?: cli| code assist)?|"
         r"(?:github )?copilot|cursor(?: agent)?|aider|devin(?: ai)?|windsurf")
# A co-author is a tool when the whole name is a tool's (optionally with its model) or the account is a tool's.
# "Jane Claude", "Devin Smith" and "Cursor Lee" are people (S18 and S19 reviews).
AUTHOR_NAMES = (r"claude(?: code| ai|[- ](?:opus|sonnet|haiku|fable|\d)[^<\n]*)?|anthropic|openai(?: codex)?|codex(?: cli)?|chatgpt|"
                r"gpt-\d[\w.-]*|gemini(?: cli| code assist|[- ]\d[^<\n]*)?|(?:github )?copilot(?: autofix[^<\n]*)?|cursor(?: agent)?|"
                r"aider|devin ai|windsurf")
AUTHOR_ACCOUNTS = (r"noreply@anthropic\.com|(?:noreply|codex)@openai\.com|cursoragent|devin-ai|gemini-code-assist|"
                   r"copilot(?:-swe-agent)?\[bot\]|\+copilot@users\.noreply|copilot@github\.com|@aider\.chat|claude\[bot\]")
# "generated with/by <tool>" counts only where the tool's name ends the phrase: not "generated with cursor offset".
COMMIT_MARKERS = re.compile(
    rf"^\s*co-authored-by:[ \t]*(?:(?:{AUTHOR_NAMES})(?:\[bot\])?[ \t]*(?:\([^)\n]*\)[ \t]*)?(?:<|$)|[^\n]*(?:{AUTHOR_ACCOUNTS}))"
    rf"|generated (?:with|by) \[?(?:{TOOLS})(?=[ \t]*(?:$|[\])(.!,:;<*]|\d|via\b|opus\b|sonnet\b|haiku\b|fable\b))"
    r"|\U0001F916 ?generated",
    re.IGNORECASE | re.MULTILINE)
FILE_MARKERS = r"generated with \[?claude code|co-authored-by: *claude|🤖 generated with"
HOOK_MARK = "# agf: commit-msg hook that rejects AI co-author lines (agf traces hook)"
HOOK = '''#!/bin/sh
{mark}
# Installed by `agf traces hook --apply`; `agf traces hook --remove --apply` takes it out.
PY=
for candidate in python3 python py; do  # found is not enough: Windows has a python3 stub that only fails
  if "$candidate" -c 'import sys; sys.exit(sys.version_info[0] < 3)' </dev/null >/dev/null 2>&1; then PY=$candidate; break; fi
done
[ -n "$PY" ] || exit 0  # no working Python 3: do not block commits, the check simply does not run
exec "$PY" - "$1" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
body = "\\n".join(line for line in text.splitlines() if not line.startswith("#"))
if re.search(r"""{pattern}""", body, re.IGNORECASE | re.MULTILINE):
    sys.stderr.write("commit-msg: 這個專案不留 AI 痕跡，commit 訊息裡有 AI 共同作者或「Generated with」一類的字樣。"
                     "刪掉那幾行再 commit；真的要保留，用 git commit --no-verify。\\n")
    sys.exit(1)
PYEOF
'''


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
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise AgfError("The agf block in .git/info/exclude is damaged (a marker line was edited or duplicated); "
                       "fix or delete it by hand, then run this again.")
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\r?\n?", re.DOTALL)
    stripped, count = pattern.subn("", text)
    return stripped, bool(count)


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    with path.open(encoding="utf-8", errors="replace", newline="") as stream:  # keep CRLF files as they are
        return stream.read()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(text)


def _hook_text() -> str:
    return HOOK.replace("{mark}", HOOK_MARK).replace("{pattern}", COMMIT_MARKERS.pattern)


def _hook_file(root: Path) -> Path:
    path = Path(_git(root, "rev-parse", "--git-path", "hooks/commit-msg").strip())
    return path if path.is_absolute() else root / path


def _shared_or_tracked(root: Path, path: Path) -> bool:
    """True when core.hooksPath (or a link) puts the hook outside this repository's own Git directory."""
    common = Path(_git(root, "rev-parse", "--git-common-dir").strip())
    common = common if common.is_absolute() else root / common
    return not path.parent.resolve().is_relative_to(common.resolve())


def hook(target, apply: bool = False, remove: bool = False) -> dict:
    """Install (or remove) the commit-msg hook. A hook this command did not write is never touched."""
    root = Path(target).resolve()
    if not is_repository(root):
        return {"status": "NOT_GIT", "target": str(root), "applied": False}
    if not is_toplevel(root):
        return {"status": "NESTED", "target": str(root), "applied": False}
    path = _hook_file(root)
    if _shared_or_tracked(root, path):
        return {"status": "CUSTOM_HOOKS_PATH", "hook": str(path), "applied": False,
                "meaning": "core.hooksPath points outside this repository's .git (a shared or tracked directory); nothing was changed. "
                           "Add or remove the check there by hand if wanted."}
    if path.is_symlink():
        return {"status": "FOREIGN_HOOK", "hook": str(path), "applied": False,
                "meaning": "commit-msg is a symbolic link; neither it nor its target was changed."}
    current = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None
    ours = current is not None and HOOK_MARK in current
    if remove:
        if not ours:
            return {"status": "UNCHANGED", "hook": str(path), "applied": False}
        if apply:
            path.unlink()
        return {"status": "REMOVED", "hook": str(path), "applied": apply}
    if current is not None and not ours:
        return {"status": "FOREIGN_HOOK", "hook": str(path), "applied": False,
                "meaning": "The repository already has its own commit-msg hook; it was left alone. Add the check to it by hand if wanted."}
    if current == _hook_text():
        return {"status": "UNCHANGED", "hook": str(path), "applied": False}
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_hook_text(), encoding="utf-8", newline="\n")
        path.chmod(0o755)
    return {"status": "UPDATED" if ours else "ADDED", "hook": str(path), "applied": apply}


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
    excluded = BEGIN in _read(exclude_path)
    found = bool(tracked or commits or markers)
    return {
        "status": "FOUND" if found else "CLEAN", "target": str(root),
        "tracked_ai_files": {"count": len(tracked), "paths": tracked[:max_items]},
        "untrack_command": ["git", "rm", "-r", "--cached", "--", *tracked[:max_items]] if tracked else None,
        "commits_with_ai_markers": {"count": len(commits), "checked": min(max_commits, log.count("\x1e")), "examples": commits[:max_items]},
        "file_markers": {"count": len(markers), "lines": markers[:max_items]},
        "exclude_block": excluded, "exclude_file": str(exclude_path),
        "commit_msg_hook": (_hook_file(root).is_file() and HOOK_MARK in _hook_file(root).read_text(encoding="utf-8", errors="replace")),
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
    text = _read(path)
    stripped, present = _without_block(text)
    newline = "\r\n" if "\r\n" in text else "\n"
    updated = (stripped if not stripped or stripped.endswith("\n") else stripped + newline) + _block().replace("\n", newline)
    if updated == text:
        return {"status": "UNCHANGED", "target": str(root), "exclude_file": str(path), "applied": False}
    if apply:
        _write(path, updated)
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
    stripped, present = _without_block(_read(path))
    if not present:
        return {"status": "UNCHANGED", "target": str(root), "exclude_file": str(path), "applied": False}
    if apply:
        _write(path, stripped)
    return {"status": "REMOVED", "target": str(root), "exclude_file": str(path), "applied": apply}


def register(subparsers) -> None:
    command = subparsers.add_parser("traces", help="Find AI-tool traces in a Git project and keep AI tool files local")
    operations = command.add_subparsers(dest="operation", required=True)
    probe = operations.add_parser("check", help="Read-only report: tracked AI files, AI commit markers, markers in files, exclude block")
    probe.add_argument("--target", default=".")
    probe.add_argument("--max-commits", type=int, default=5000)
    probe.set_defaults(func=lambda args: check(args.target, max(1, args.max_commits)))
    installer = operations.add_parser("hook", help="Install the commit-msg hook that rejects AI co-author lines (preview unless --apply)")
    installer.add_argument("--target", default=".")
    installer.add_argument("--apply", action="store_true")
    installer.add_argument("--remove", action="store_true", help="Remove the hook this command installed")
    installer.set_defaults(func=lambda args: hook(args.target, args.apply, args.remove))
    for name, function in (("exclude", exclude), ("remove", remove)):
        parser = operations.add_parser(name, help=f"{'Add' if name == 'exclude' else 'Remove'} the marked block in .git/info/exclude (preview unless --apply)")
        parser.add_argument("--target", default=".")
        parser.add_argument("--apply", action="store_true")
        parser.set_defaults(func=lambda args, f=function: f(args.target, args.apply))

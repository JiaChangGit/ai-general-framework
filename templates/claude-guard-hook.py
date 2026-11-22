#!/usr/bin/env python3
"""Claude Code PreToolUse hook: refuse a few actions that written rules failed to stop.

Install by adding it to the "PreToolUse" hooks of a settings file (see
templates/claude-guard-settings.example.json). A user-level settings file applies
to every session, wherever it starts; a project's .claude/settings.json applies
only to sessions started in that directory.

It refuses, by exit code 2 with the reason on stderr (Claude Code shows the
reason to the model and does not run the tool):
  - git push, whatever wraps it on the command line: `git -C dir`, global git
    options, a path to git, `sh -c` / `bash -lc` / `eval`, `( )`, `{ }`, `if/then`,
    `cd x &&`, `pushd`/`popd`, `env`, `sudo -u`, `timeout -s`, `nice -n`, `xargs`, and rtk
    (`rtk git`, `rtk proxy`, `rtk err`, `rtk run`);
  - creating or merging a pull/merge request with gh or glab (global options such
    as `-R repo` included), and gh release create;
  - `pkill -f` / `pkill --full` and `killall`, which also match the shell running them;
  - writes into protected paths: Edit/Write/MultiEdit/NotebookEdit on a protected
    file, and Bash commands whose target is protected: redirection (> >> >| &>),
    tee, cp/mv/install/ln/rsync/scp (including -t DIR), rm, rmdir, touch, mkdir,
    truncate, chmod, chown, shred, unlink, sed -i, perl -i, dd of=, find -delete,
    tar -x -C, curl -o, wget -O/-P, unzip -d, and git subcommands that write when
    the repository (-C, --git-dir, --work-tree or the current directory) is protected;
  - the same checks inside MCP tools (mcp__<server>__<tool>), when the settings matcher
    includes them: an argument named like a command (command, cmd, script, ..., with a
    sibling args list), at any depth, is checked as a Bash command, and a path argument
    (path, file, source, destination, uri, ...) as a write when a word of the tool's name
    says it changes something (write, edit, delete, move, run, ..., also compounds such
    as writefile). Relative paths count only against an absolute working directory given
    in the call. Unrecognised arguments pass; arguments nested over 64 levels are refused.

Text that the shell never runs is not read as commands: words inside single
quotes, and a heredoc body read by a program that is not a shell (the text
of `python3 - <<'EOF'` or `cat <<'EOF' > notes.md`). A heredoc read by a shell,
eval, source or ssh (`bash <<'EOF'`, `cat <<EOF | sh`) is checked like any other
command line, and so are the $(...) and backticks of an unquoted heredoc. A
heredoc without its closing line leaves the rest of the command checked.

What it cannot see: anything a program does once it runs (`python3 -c "open(...)"`,
a script or Makefile that pushes, a Git alias for push), paths held in shell
variables (`$DIR/file`), and commands built at run time. It is a guard against
mistakes, not a sandbox.

Configuration: JSON at the path given as the first argument, else $AGF_GUARD_CONFIG,
else defaults (block push, pull requests and pattern kills; no protected paths):
  {"protected_paths": ["/abs/dir", "~/other"], "block_push": true,
   "block_pull_requests": true, "block_pkill": true}
A configuration that cannot be read, a call the hook cannot parse, or commands
nested deeper than it follows are refused, so a typo or an unexpected input
does not silently remove the protection.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

DEFAULTS = {"protected_paths": [], "block_push": True, "block_pull_requests": True, "block_pkill": True}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "{", "}", "time"}
# Commands that run the command that follows them, and their options that take a value.
WRAPPERS = {
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-U", "-r", "-t", "-T", "--user", "--group", "--chdir",
             "--host", "--prompt", "--role", "--type", "--other-user", "--close-from"},
    "env": {"-u", "--unset", "-C", "--chdir"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "-t", "--class", "--classdata"},
    "stdbuf": {"-i", "-o", "-e", "--input", "--output", "--error"},
    "xargs": {"-n", "-P", "-I", "-L", "-d", "-a", "-E", "-s", "--max-args", "--max-procs", "--replace",
              "--max-lines", "--delimiter", "--arg-file", "--eof", "--max-chars"},
    "command": set(), "nohup": set(), "exec": {"-a"}, "builtin": set(), "nocorrect": set(),
}
RTK_WRAPPING = {"err", "test", "summary", "proxy"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
GIT_WRITES = {"add", "am", "apply", "checkout", "cherry-pick", "clean", "commit", "fetch", "gc", "init", "merge",
              "mv", "notes", "pull", "push", "rebase", "reset", "restore", "revert", "rm", "switch",
              "update-index", "update-ref", "worktree"}
WRITES_ALL_ARGUMENTS = {"rm", "rmdir", "mv", "touch", "mkdir", "truncate", "chmod", "chown", "chgrp", "shred",
                        "unlink", "tee"}
WRITES_LAST_ARGUMENT = {"cp", "rsync", "install", "ln", "scp"}
PULL_REQUESTS = {"gh": [("pr", "create"), ("pr", "merge"), ("release", "create")],
                 "glab": [("mr", "create"), ("mr", "merge"), ("release", "create")]}
GH_OPTIONS_WITH_VALUE = {"-R", "--repo", "--hostname"}
# MCP tool arguments, matched by name (case-insensitive). See check_mcp.
MCP_COMMAND_KEYS = {"command", "cmd", "script", "shell", "bash", "commandline", "command_line", "commands"}
MCP_ARGV_KEYS = {"args", "argv", "arguments"}  # next to a command: the rest of its argv
MCP_WORKDIR_KEYS = {"cwd", "workdir", "working_directory", "workingdirectory", "working_dir", "currentworkingdirectory"}
MCP_PATH_KEYS = {"path", "paths", "file", "files", "file_path", "file_paths", "filepath", "filename", "target", "target_path",
                 "destination", "dest", "dst", "to", "output", "output_path", "new_path", "directory", "dir",
                 "source", "source_path", "src", "from", "old_path", "uri"}
# Whole words of the tool name (split on _, -, . and camelCase), so get_output is not "put".
MCP_WRITES = {"write", "edit", "create", "delete", "remove", "rm", "move", "mv", "rename", "update", "put", "append",
              "mkdir", "patch", "apply", "save", "copy", "cp", "upload", "replace", "insert", "run", "exec", "execute"}
# Lowercase compounds have no word boundary: writefile, fileedit, createdirectory (S19 review).
MCP_NOUNS = r"(?:files?|dir|directory|directories|folder|text|content|object|note|page)"
MCP_VERBS = "(?:" + "|".join(sorted(MCP_WRITES)) + ")"
MCP_COMPOUND = re.compile(f"{MCP_VERBS}{MCP_NOUNS}|{MCP_NOUNS}{MCP_VERBS}")
MCP_MAX_DEPTH = 64

BASH_MAX_DEPTH = 8  # wrappers inside wrappers; deeper is refused rather than passed unchecked


class Refuse(Exception):
    pass


def load_config(argument: str | None) -> dict:
    path = argument or os.environ.get("AGF_GUARD_CONFIG")
    config = dict(DEFAULTS)
    if path:
        loaded = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("the configuration must be a JSON object")
        unknown = set(loaded) - set(DEFAULTS)
        if unknown:
            raise ValueError(f"unknown keys {sorted(unknown)}")
        config.update(loaded)
    paths = config["protected_paths"]
    if not isinstance(paths, list) or not all(isinstance(p, str) and p.strip() for p in paths):
        raise ValueError("protected_paths must be a list of non-empty path strings")
    for key in ("block_push", "block_pull_requests", "block_pkill"):
        if not isinstance(config[key], bool):
            raise ValueError(f"{key} must be true or false")
    config["protected_paths"] = [Path(p).expanduser().resolve() for p in paths]
    if any(root == Path(root.anchor) for root in config["protected_paths"]):
        raise ValueError("protecting a filesystem root would refuse every write; list the directories instead")
    return config


def protected(path: str, cwd: Path, config: dict) -> Path | None:
    """The protected root that contains `path` (resolved against cwd), if any."""
    if not path or path.startswith("-"):
        return None
    drive = re.match(r"(?:/cygdrive)?/([A-Za-z])(?:/|$)", path) if os.name == "nt" else None
    if drive:
        path = f"{drive.group(1)}:/{path[drive.end():]}"  # Git Bash writes C:\\x as /c/x, Cygwin as /cygdrive/c/x (S15)
    target = (cwd / Path(path).expanduser()).resolve()
    for root in config["protected_paths"]:
        if target == root or root in target.parents:
            return root
    return None


def segments(command: str) -> list[str]:
    """Simple commands of a shell line: split at ; & | && || ( ) and newlines outside
    quotes, keeping redirections such as >| 2>&1 &> together, plus the bodies of
    $(...) and backticks."""
    parts, current, quote, index = [], [], None, 0
    while index < len(command):
        char = command[index]
        before = "".join(current).rstrip()[-1:]
        after = command[index + 1:index + 2]
        if quote:
            if char == "\\" and quote == '"' and after:
                current.append(command[index:index + 2])
                index += 2
                continue
            if char == quote:
                quote = None
            current.append(char)
        elif char in "'\"":
            quote = char
            current.append(char)
        elif char == "\\" and after:
            current.append(command[index:index + 2])
            index += 2
            continue
        elif (char == "|" and before == ">") or (char == "&" and (before == ">" or after == ">")):
            current.append(char)  # >|, 2>&1, &>, &>>
        elif char in ";&|\n()":
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
        index += 1
    parts.append("".join(current))
    return [part for part in parts + [s for body in substitutions(command) for s in segments(body)] if part.strip()]


def substitutions(text: str, quotes: bool = True) -> list[str]:
    """Bodies of $(...) and backticks that the shell would run.

    With quotes, text inside single quotes is skipped (it is never expanded) and
    double quotes are tracked, so the apostrophe in "it's" does not start a quote.
    A heredoc body is passed with quotes=False: quotes there are ordinary text."""
    bodies, index, quote = [], 0, None
    while index < len(text):
        char = text[index]
        if quote == "'":
            quote = None if char == "'" else quote
            index += 1
            continue
        if char == "\\":
            index += 2
            continue
        if quotes and char == "'" and quote is None:
            quote = "'"
        elif quotes and char == '"':
            quote = None if quote == '"' else '"'
        elif char == "$" and text[index + 1:index + 2] == "(":
            depth, end = 0, index + 1
            while end < len(text):
                depth += {"(": 1, ")": -1}.get(text[end], 0)
                if depth == 0:
                    break
                end += 1
            bodies.append(text[index + 2:end])
            index = end
        elif char == "`":
            end = text.find("`", index + 1)
            end = len(text) if end < 0 else end
            bodies.append(text[index + 1:end])
            index = end
        index += 1
    return bodies


HEREDOC = re.compile(r"(?<!<)<<(?!<)(-?)[ \t]*(?:'([^'\n]+)'|\"([^\"\n]+)\"|(\\?)([^\s;&|<>()'\"`]+))")
# Programs that run what they read on standard input as shell commands.
SHELL_READERS = SHELLS | {"eval", "source", ".", "ssh", "fish"}


def strip_heredocs(command: str) -> tuple[str, list[str]]:
    """(command without the heredoc bodies that are only data, unquoted bodies).

    A heredoc body is text on the program's standard input. When that program is
    a shell (`bash <<'EOF'`, `cat <<EOF | sh`, `eval "$(cat <<EOF ...)"`), the
    body is commands and stays in the command. Otherwise a body under a quoted
    delimiter (<<'EOF', <<"EOF", <<\\EOF) is never expanded and is dropped; an
    unquoted body is dropped too, but returned so that its $(...) and backticks,
    which do run, are checked. A heredoc without its closing line keeps the rest
    of the command, so nothing is skipped by mistake."""
    lines, kept, expanded, index = command.split("\n"), [], [], 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        # Hide quoted text and arithmetic, except a quoted delimiter right after <<.
        visible = re.sub(r"'[^']*'|\"[^\"]*\"", lambda m: m.group() if re.search(r"(?<!<)<<-?[ \t]*$", line[:m.start()]) else " " * len(m.group()), line)
        visible = re.sub(r"\$\(\([^)]*\)\)", lambda m: " " * len(m.group()), visible)
        readers = {os.path.basename(word) for word in re.findall(r"[^\s;&|()<>]+", visible)} & SHELL_READERS
        for dash, single, double, backslash, bare in HEREDOC.findall(visible):
            delimiter, quoted = single or double or bare, bool(single or double or backslash)
            body, closed = [], False
            while index < len(lines):
                candidate = lines[index].lstrip("\t") if dash else lines[index]
                index += 1
                if candidate == delimiter:
                    closed = True
                    break
                body.append(lines[index - 1])
            if readers or not closed:
                kept.extend(body)
            elif not quoted:
                expanded.append("\n".join(body))
    return "\n".join(kept), expanded


def blank_quotes(segment: str) -> str:
    """The segment with quoted text replaced by spaces, so `echo "a > b"` has no redirection."""
    out, quote = [], None
    for char in segment:
        if quote:
            out.append(" ")
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
            out.append(" ")
        else:
            out.append(char)
    return "".join(out)


def words(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def unwrap(argv: list[str]) -> tuple[list[str], str | None]:
    """Remove keywords, assignments and wrappers; (argv, shell string to check) for
    `env -S` and `rtk run`, whose argument is itself a command line."""
    while argv:
        name = os.path.basename(argv[0])
        if argv[0] in KEYWORDS or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[0]):
            argv = argv[1:]
        elif name in WRAPPERS:
            argv = argv[1:]
            while argv and argv[0].startswith("-") and argv[0] != "-":
                option = argv[0]
                if name == "env" and option in {"-S", "--split-string"} and len(argv) > 1:
                    return argv[2:], argv[1]
                if name == "env" and option.startswith("--split-string="):
                    return argv[1:], option.split("=", 1)[1]
                argv = argv[2:] if option in WRAPPERS[name] else argv[1:]
            if name == "timeout" and argv and re.fullmatch(r"[0-9.]+[smhd]?", argv[0]):
                argv = argv[1:]
        elif name == "rtk":
            argv = argv[1:]
            while argv and argv[0].startswith("-"):
                argv = argv[1:]
            if argv and argv[0] == "run":
                return [], " ".join(argv[1:])
            if argv and argv[0] in RTK_WRAPPING:
                argv = argv[1:]
        else:
            break
    while argv and argv[-1] in {"}", "fi", "done"}:
        argv = argv[:-1]
    return argv, None


def git_parts(argv: list[str]) -> tuple[str | None, list[str], list[str]]:
    """(subcommand, its arguments, directories named by -C, --git-dir or --work-tree)."""
    directories, index = [], 1
    while index < len(argv):
        token = argv[index]
        if token in GIT_OPTIONS_WITH_VALUE:
            if token in {"-C", "--git-dir", "--work-tree"} and index + 1 < len(argv):
                directories.append(argv[index + 1])
            index += 2
        elif token.startswith("--") and "=" in token:
            if token.startswith(("--git-dir=", "--work-tree=")):
                directories.append(token.split("=", 1)[1])
            index += 1
        elif token.startswith("-"):
            index += 1
        else:
            return token, argv[index + 1:], directories
    return None, [], directories


def git_writes(sub: str, args: list[str]) -> bool:
    positional = [a for a in args if not a.startswith("-")]
    if sub == "branch":
        listing = {"-l", "--list", "-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "--show-current",
                   "--contains", "--no-contains", "--merged", "--no-merged", "--points-at", "--format", "--sort"}
        changing = {"-d", "-D", "--delete", "-m", "-M", "--move", "-c", "-C", "--copy", "-f", "--force", "-u",
                    "--set-upstream-to", "--unset-upstream", "--edit-description", "-t", "--track"}
        flags = {a.split("=", 1)[0] for a in args if a.startswith("-")}
        return bool(flags & changing) or (bool(positional) and not flags & listing)
    if sub == "tag":
        flags = {a.split("=", 1)[0] for a in args if a.startswith("-")}
        if flags & {"-a", "-s", "-u", "-d", "--delete", "-f", "--force", "-m", "-F", "--annotate", "--sign"}:
            return True
        return bool(positional) and not flags & {"-l", "--list", "-n", "--contains", "--points-at", "--merged"}
    if sub == "stash":
        return not positional or positional[0] not in {"list", "show"}
    if sub == "remote":
        return bool(positional) and positional[0] in {"add", "remove", "rm", "rename", "set-url", "set-head", "prune"}
    if sub == "config":
        return not any(a in {"--get", "--get-all", "--list", "-l", "--get-regexp"} for a in args)
    return sub in GIT_WRITES


def option_values(argv: list[str], names: set[str]) -> list[str]:
    """Values of the given options, in the `-o VALUE`, `-oVALUE`, bundled `-fsSLo VALUE` and `--name=VALUE` forms."""
    values = []
    for index, token in enumerate(argv):
        for name in names:
            if token == name and index + 1 < len(argv):
                values.append(argv[index + 1])
            elif name.startswith("--") and token.startswith(name + "="):
                values.append(token.split("=", 1)[1])
            elif len(name) == 2 and token[:1] == "-" and token[:2] != "--":
                at = token.find(name[1], 1)
                if at < 1 or (at > 1 and not token[1:at].isalnum()):
                    continue
                if at + 1 < len(token):
                    values.append(token[at + 1:])
                elif index + 1 < len(argv):
                    values.append(argv[index + 1])
    return values


def short_flags(argv: list[str]) -> str:
    return "".join(a[1:] for a in argv if a.startswith("-") and not a.startswith("--"))


def check_bash(command: str, cwd: Path, config: dict, depth: int = 0) -> None:
    if depth > BASH_MAX_DEPTH:
        raise Refuse(f"nests commands deeper than {BASH_MAX_DEPTH} levels, which the hook does not check")
    stack: list[Path] = []
    command, expanded = strip_heredocs(command)
    for body in expanded:
        for inner in substitutions(body, quotes=False):
            check_bash(inner, cwd, config, depth + 1)
    for segment in segments(command):
        # Operators are found where nothing is quoted; the target is then read from
        # the original text, so `> "/protected/a"` is still seen.
        for match in re.finditer(r"(?<![0-9<>&])(\d?>>?\|?|&>>?)(?!&)", blank_quotes(segment)):
            rest = words(segment[match.end():])
            if rest and (root := protected(rest[0], cwd, config)):
                raise Refuse(f"redirects output into the protected path {root}")
        # Redirections are not arguments: drop a bare operator with its target, and
        # an operator written together with its target (>file, 2>&1, <in).
        tokens, skip = [], False
        for token in words(segment):
            if skip:
                skip = False
            elif re.fullmatch(r"\d?(>>?\|?|<<?<?)|&>>?", token):
                skip = True
            elif not re.fullmatch(r"\d?(>>?\|?|<)\S+|&>>?\S+", token):
                tokens.append(token)
        argv, nested = unwrap(tokens)
        if nested is not None:
            check_bash(nested, cwd, config, depth + 1)
        if not argv:
            continue
        name = os.path.basename(argv[0])
        if name == "cd":
            target = next((a for a in argv[1:] if not a.startswith("-")), "~")
            cwd = (cwd / Path(target).expanduser()).resolve()
            continue
        if name == "pushd":
            target = next((a for a in argv[1:] if not a.startswith(("-", "+"))), None)
            if target:
                stack.append(cwd)
                cwd = (cwd / Path(target).expanduser()).resolve()
            elif len(argv) == 1 and stack:  # bare pushd swaps with the top
                cwd, stack[-1] = stack[-1], cwd
            continue
        if name == "popd":
            if len(argv) == 1 and stack:
                cwd = stack.pop()
            continue
        if name in SHELLS or name == "eval":
            if name == "eval":
                check_bash(" ".join(argv[1:]), cwd, config, depth + 1)
                continue
            for index, token in enumerate(argv[1:], 1):
                if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", token):
                    check_bash(argv[index + 1] if index + 1 < len(argv) else "", cwd, config, depth + 1)
                    break
            continue
        check_simple(name, argv, cwd, config)


def check_simple(name: str, argv: list[str], cwd: Path, config: dict) -> None:
    arguments = [a for a in argv[1:] if not a.startswith("-")]
    if name == "git":
        sub, args, directories = git_parts(argv)
        if sub == "push" and config["block_push"]:
            raise Refuse("runs git push; pushing is left to the user")
        if sub and git_writes(sub, args):
            for directory in directories or ["."]:
                if (root := protected(directory, cwd, config)):
                    raise Refuse(f"runs git {sub} in the protected repository {root}")
    if name in PULL_REQUESTS and config["block_pull_requests"]:
        tokens, index = [], 1
        while index < len(argv):
            token = argv[index]
            if token in GH_OPTIONS_WITH_VALUE:
                index += 2
                continue
            if not token.startswith("-"):
                tokens.append(token)
            index += 1
        if tuple(tokens[:2]) in PULL_REQUESTS[name]:
            raise Refuse(f"runs {name} {' '.join(tokens[:2])}; pull requests and releases are left to the user")
    if config["block_pkill"]:
        if name == "killall" or (name == "pkill" and ("f" in short_flags(argv) or "--full" in argv)):
            raise Refuse(f"runs {name} with a pattern, which can also match the shell running it; stop processes by PID")
    if not config["protected_paths"]:
        return
    candidates: list[str] = []
    if name in WRITES_ALL_ARGUMENTS:
        candidates += arguments
    if name in WRITES_LAST_ARGUMENT:
        candidates += option_values(argv, {"-t", "--target-directory"}) + arguments[-1:]
    if name == "sed" and ("i" in short_flags(argv) or any(a.startswith("--in-place") for a in argv)):
        candidates += arguments[1:]
    if name == "perl" and "i" in short_flags(argv):
        candidates += arguments
    if name == "dd":
        candidates += [a[3:] for a in argv[1:] if a.startswith("of=")]
    if name == "find" and any(a in {"-delete", "-exec", "-execdir", "-ok", "-fprint"} for a in argv[1:]):
        candidates += [a for a in argv[1:] if not a.startswith("-")][:1] or ["."]
    if name == "tar" and ("x" in short_flags(argv) or "--extract" in argv or (len(argv) > 1 and "x" in argv[1] and not argv[1].startswith("-"))):
        candidates += option_values(argv, {"-C", "--directory"}) or ["."]
    if name == "curl":
        candidates += option_values(argv, {"-o", "--output"})
        if "O" in short_flags(argv) or "--remote-name" in argv:
            candidates.append(".")
    if name == "wget":
        candidates += option_values(argv, {"-O", "--output-document", "-P", "--directory-prefix"}) or ["."]
    if name == "unzip":
        candidates += option_values(argv, {"-d"}) or ["."]
    for candidate in candidates:
        if (root := protected(candidate, cwd, config)):
            raise Refuse(f"runs {name} on the protected path {root}")


def _words(name: str) -> set[str]:
    return {word.lower() for word in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", name)}


def _mcp_fields(value, depth: int = 0):
    """(key, value) pairs of an MCP tool input, including nested objects and lists of objects."""
    if depth > MCP_MAX_DEPTH:
        raise Refuse(f"nests MCP arguments deeper than {MCP_MAX_DEPTH} levels, which the hook does not check")
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).lower(), item, value
            yield from _mcp_fields(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            yield from _mcp_fields(item, depth + 1)


def check_mcp(tool: str, data: dict, cwd: Path, config: dict) -> None:
    """An MCP tool (named mcp__<server>__<tool>) can run commands or write files that the
    Bash/Edit/Write checks never see, e.g. a remote `run` tool (S17). Arguments whose names
    say they hold a command are checked like a Bash command, at any depth and with a sibling
    args/argv list joined in; path arguments are checked like a file write when a word of the
    tool's own name says it changes something. The server may run on another machine, so a
    relative path is only judged against an absolute working directory given in the same
    call, never against this session's directory. Anything else passes: the hook cannot know
    what an unfamiliar tool does (S18 review)."""
    words = _words(tool.rsplit("__", 1)[-1])
    writes = bool(words & MCP_WRITES) or any(MCP_COMPOUND.fullmatch(word) for word in words)
    unknown = Path("/agf-guard-unknown-mcp-cwd")  # nothing is protected under it
    for key, value, holder in _mcp_fields(data):
        workdir = next((v for k, v in holder.items() if str(k).lower() in MCP_WORKDIR_KEYS and isinstance(v, str) and v), None)
        base = Path(workdir).expanduser() if workdir and Path(workdir).expanduser().is_absolute() else unknown
        if key in MCP_COMMAND_KEYS:
            commands = value if isinstance(value, list) and all(isinstance(item, str) for item in value) and key == "commands" else [value]
            for command in commands:
                if isinstance(command, list) and all(isinstance(item, str) for item in command):
                    command = shlex.join(command)  # argv form
                if not isinstance(command, str):
                    continue
                extra = next((v for k, v in holder.items() if str(k).lower() in MCP_ARGV_KEYS and isinstance(v, list)
                              and all(isinstance(item, str) for item in v)), None)
                check_bash(command + (" " + shlex.join(extra) if extra else ""), base, config)
        elif writes and key in MCP_PATH_KEYS:
            for path in ([value] if isinstance(value, str) else value if isinstance(value, list) else []):
                if not isinstance(path, str):
                    continue
                path = path[len("file://"):] if path.startswith("file://") else path
                if (root := protected(path, base, config)):
                    raise Refuse(f"uses the MCP tool {tool} on the protected path {root}")


def decide(event: dict, config: dict) -> str | None:
    tool = event.get("tool_name", "")
    data = event.get("tool_input")
    data = data if isinstance(data, dict) else {}
    cwd_value = event.get("cwd")
    cwd = Path(cwd_value) if isinstance(cwd_value, str) and cwd_value else Path(os.getcwd())
    try:
        if tool == "Bash":
            check_bash(str(data.get("command", "")), cwd, config)
        elif tool in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
            path = data.get("file_path") or data.get("notebook_path") or ""
            if (root := protected(str(path), cwd, config)):
                raise Refuse(f"uses {tool} on the protected path {root}")
        elif isinstance(tool, str) and tool.startswith("mcp__"):
            check_mcp(tool, data, cwd, config)
    except Refuse as refusal:
        return str(refusal)
    return None


def utf8_stdio() -> None:
    """Claude Code sends and reads hook JSON as UTF-8. Without this, Windows uses the
    locale's code page (cp1252, cp950, ...): printing Chinese failed, and a command with
    Chinese text could be misread as one the hook cannot parse, which it refuses (S15)."""
    # surrogateescape keeps bytes that are not UTF-8 instead of failing on them, so such
    # an event is still read and judged; backslashreplace never fails to print.
    for stream, errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"), (sys.stderr, "backslashreplace")):
        try:
            stream.reconfigure(encoding="utf-8", errors=errors)
        except (AttributeError, ValueError):
            pass


def main() -> int:
    utf8_stdio()
    try:
        config = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    except (OSError, ValueError, TypeError) as error:
        print(f"agf guard: cannot read the configuration ({error}); refusing every tool call until it is fixed", file=sys.stderr)
        return 2
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0  # nothing to judge; Claude Code always sends JSON
    except Exception as error:  # e.g. RecursionError: exit code 1 would let the call through
        print(f"agf guard could not read this call ({type(error).__name__}); refusing it", file=sys.stderr)
        return 2
    if not isinstance(event, dict):
        return 0
    try:
        reason = decide(event, config)
    except Exception as error:  # a parsing bug must not let the call through unchecked
        print(f"agf guard could not check this call ({type(error).__name__}: {error}); refusing it", file=sys.stderr)
        return 2
    if reason:
        print(f"agf guard refused this call: it {reason}. Ask the user if this is really needed.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

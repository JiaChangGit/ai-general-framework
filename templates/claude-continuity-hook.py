#!/usr/bin/env python3
"""Claude Code hooks that keep work recoverable across usage limits, compaction and model switches.

    python3 claude-continuity-hook.py EVENT [CONFIG_JSON]

EVENT is one of the subcommands below; each reads the hook's JSON on stdin.
Install with templates/claude-continuity-settings.example.json. All output is
plain text or the JSON fields Claude Code documents for that event; a hook that
has nothing to say prints nothing, so it costs no tokens.

  session-start     SessionStart (startup, resume, clear, compact, fork). Points
                    the model at the hand-off files and the latest checkpoint
                    if they exist. On a resumed session whose cache has likely
                    expired, it also tells the user what re-reading will cost.
  pre-compact       PreCompact. Its stdout becomes instructions for the summary:
                    keep the task, decisions, commits, next steps, hand-off path.
  post-compact      PostCompact. Saves the compaction summary as a checkpoint.
  stop-failure      StopFailure (rate limit, server error, ...). Saves a
                    checkpoint with the error and the last message. It cannot
                    block, and Claude Code's own auto-continue is left alone.
  session-end       SessionEnd. Saves a checkpoint (git state, last message).
  pre-model-switch  PreModelSwitch. Saves a checkpoint; when the cache is warm
                    and re-writing it is estimated above switch_warn_usd, shows
                    the cost to the user. It blocks only with block_switch.
  user-prompt       UserPromptSubmit, only with "save_prompts": true. Keeps the
                    user's messages of this session (each clipped, the newest 20)
                    so that checkpoints show decisions made only in chat. Off by
                    default: what people type can include passwords or keys.
  stop              Stop. Once per session, if commits were made during this
                    session (as recorded by session-start) after the hand-off
                    file was last changed, asks the model to update it before
                    finishing (additionalContext, not a hard block).

Checkpoints are Markdown files in checkpoint_dir (default .agf/checkpoints):
latest.md plus timestamped copies, the newest `keep` (at least 1) of them kept. They hold
facts a script can collect (time, event, git branch, HEAD, recent commits,
status, the error, the last assistant message, the compaction summary, and
with save_prompts the user's last messages), not a plan; the plan belongs in
the hand-off file the model writes.

Configuration (all optional):
  {"handoff_files": ["HANDOFF.md", ".ai/HANDOFF.md", "docs/HANDOFF.md"],
   "checkpoint_dir": ".agf/checkpoints", "keep": 10,
   "switch_warn_usd": 0.5, "block_switch": false, "stop_reminder": true,
   "save_prompts": false}
Paths are relative to the project directory ($CLAUDE_PROJECT_DIR, else cwd).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time

DEFAULTS = {"handoff_files": ["HANDOFF.md", ".ai/HANDOFF.md", "docs/HANDOFF.md"], "checkpoint_dir": ".agf/checkpoints",
            "keep": 10, "switch_warn_usd": 0.5, "block_switch": False, "stop_reminder": True, "save_prompts": False}
PROMPTS_KEPT, PROMPT_LIMIT, PROMPTS_SHOWN = 20, 2000, 5
LIMIT = 6000  # characters kept from any single field, well under the 10,000-character hook output cap
# Seconds the git calls of one event may take in total, below the hook timeout in the
# settings example (10 s). A PreModelSwitch hook that times out blocks the switch, and
# SessionEnd gets 1.5 s unless the settings give it a timeout.
GIT_BUDGET = {"pre-model-switch": 3.0, "session-end": 1.0}
deadline = time.monotonic() + 6.0


def load_config(path: str | None) -> dict:
    config = dict(DEFAULTS)
    if path:
        loaded = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("the configuration must be a JSON object")
        unknown = set(loaded) - set(DEFAULTS)
        if unknown:
            raise ValueError(f"unknown keys {sorted(unknown)}")
        config.update(loaded)
    if isinstance(config["keep"], bool) or not isinstance(config["keep"], int) or config["keep"] < 1:
        raise ValueError("keep must be a whole number of at least 1")
    if not isinstance(config["handoff_files"], list) or not all(isinstance(name, str) for name in config["handoff_files"]):
        raise ValueError("handoff_files must be a list of paths")
    return config


def project_dir(event: dict) -> Path:
    value = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    return Path(value)


def git(root: Path, *argv: str) -> str:
    """git's output, or "" on any failure or once this event's time budget is spent."""
    remaining = deadline - time.monotonic()
    if remaining < 0.2:
        return ""
    try:
        result = subprocess.run(["git", "-C", str(root), *argv], capture_output=True, text=True, timeout=min(5.0, remaining))
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def clip(text: str, limit: int = LIMIT) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + f"\n…（截斷，原長 {len(text)} 字）"


def handoffs(root: Path, config: dict) -> list[Path]:
    return [root / name for name in config["handoff_files"] if (root / name).is_file()]


def when(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().strftime("%Y-%m-%d %H:%M")


def commits_after(root: Path, moment: float) -> int:
    """Commits among the latest 200 whose commit time is after `moment` (seconds since the epoch)."""
    times = git(root, "log", "-200", "--format=%ct").split()
    return sum(1 for value in times if value.isdigit() and int(value) > moment)


def handoff_time(root: Path, path: Path) -> float:
    """When the hand-off was last brought up to date: its file time, or the commit
    that last changed it, whichever is later. Committing the hand-off is updating it."""
    committed = git(root, "log", "-1", "--format=%ct", "--", path.relative_to(root).as_posix())
    return max(path.stat().st_mtime, float(committed) if committed.isdigit() else 0.0)


def session_marker(root: Path, config: dict, event: dict) -> Path:
    return root / config["checkpoint_dir"] / f".session-{event.get('session_id', 'unknown')}"


def prompts_file(root: Path, config: dict, event: dict) -> Path:
    return session_marker(root, config, event).with_name(f".prompts-{event.get('session_id', 'unknown')}.jsonl")


def save_prompt(root: Path, config: dict, event: dict) -> None:
    prompt = event.get("prompt")
    if not config["save_prompts"] or not isinstance(prompt, str) or not prompt.strip():
        return
    path = prompts_file(root, config, event)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [line for line in path.read_text(encoding="utf-8").split("\n") if line] if path.is_file() else []
    lines.append(json.dumps({"time": datetime.now().astimezone().strftime("%H:%M"), "prompt": clip(prompt, PROMPT_LIMIT)}, ensure_ascii=False))
    path.write_text("\n".join(lines[-PROMPTS_KEPT:]) + "\n", encoding="utf-8")


def recent_prompts(root: Path, config: dict, event: dict) -> str:
    """The user's newest messages of this session, oldest first, when save_prompts is on."""
    path = prompts_file(root, config, event)
    if not config["save_prompts"] or not path.is_file():
        return ""
    entries, used = [], 0
    lines = [line for line in path.read_text(encoding="utf-8").split("\n") if line][-PROMPTS_SHOWN:]
    for line in reversed(lines):  # newest first, so the newest always fits
        try:
            entry = json.loads(line)
            text = f"- {entry['time']}：{entry['prompt']}"
        except (ValueError, KeyError, TypeError):
            continue
        if entries and used + len(text) + 1 > LIMIT - 200:
            break  # write_checkpoint clips a section at LIMIT, keeping its start
        entries.append(text)
        used += len(text) + 1
    return "\n".join(reversed(entries))


def saved_message(root: Path, config: dict, event: dict) -> Path:
    """Where `stop` keeps this session's last message (one file per session)."""
    return session_marker(root, config, event).with_name(f".last-message-{event.get('session_id', 'unknown')}")


def last_message(root: Path, config: dict, event: dict) -> str:
    """The last assistant message: from the event, else the transcript, else what `stop` saved."""
    text = event.get("last_assistant_message") or last_assistant_text(event.get("transcript_path"))
    saved = saved_message(root, config, event)
    if not text and saved.is_file():
        text = saved.read_text(encoding="utf-8")
    return text


def last_assistant_text(transcript: str | None) -> str:
    """The last assistant text in a transcript JSONL, reading only its tail."""
    if not transcript or not Path(transcript).is_file():
        return ""
    with open(transcript, "rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - 400_000))
        lines = handle.read().decode("utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get("message") if isinstance(entry, dict) else None
        if isinstance(message, dict) and message.get("role") == "assistant":
            parts = message.get("content")
            texts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("type") == "text"] if isinstance(parts, list) else [str(parts)]
            text = "\n".join(t for t in texts if t).strip()
            if text:
                return text
    return ""


def write_checkpoint(root: Path, config: dict, event_name: str, sections: dict[str, str]) -> Path:
    folder = root / config["checkpoint_dir"]
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).astimezone()
    lines = [f"# 檢查點：{event_name}", "", f"- 時間：{now.strftime('%Y-%m-%d %H:%M:%S %z')}",
             "- 這份是 hook 自動收集的事實，不是計畫；計畫與決定看交接檔。"]
    branch, head = git(root, "branch", "--show-current"), git(root, "log", "-1", "--format=%h %s")
    if head:
        lines += [f"- 分支：{branch or '（detached）'}；HEAD：{head}"]
    lines += [f"- 交接檔：{', '.join(p.relative_to(root).as_posix() for p in handoffs(root, config)) or '（沒有）'}", ""]
    recent, status = git(root, "log", "-5", "--format=%h %ad %s", "--date=format:%m-%d %H:%M"), git(root, "status", "--short")
    if recent:
        lines += ["## 最近的 commit", "", "```", recent, "```", ""]
    if status:
        shown = status.splitlines()
        lines += ["## 未 commit 的變更", "", "```", *shown[:40], *([f"…另有 {len(shown) - 40} 行"] if len(shown) > 40 else []), "```", ""]
    for title, body in sections.items():
        if body:
            lines += [f"## {title}", "", clip(body), ""]
    text = "\n".join(lines)
    stamp = now.strftime("%Y%m%dT%H%M%S")
    (folder / f"{stamp}-{event_name}.md").write_text(text, encoding="utf-8")
    (folder / "latest.md").write_text(text, encoding="utf-8")
    copies = sorted(p for p in folder.glob("*-*.md") if p.name != "latest.md")
    for old in copies[:-config["keep"]]:
        old.unlink(missing_ok=True)
    return folder / "latest.md"


def session_start(event: dict, config: dict, root: Path) -> dict | None:
    found = handoffs(root, config)
    if event.get("session_id"):
        # Remember when this session began, so `stop` reminds only about work done in it
        # (also when the hand-off is written later in the session).
        marker = session_marker(root, config, event)
        marker.parent.mkdir(parents=True, exist_ok=True)
        if marker.exists():
            marker.touch()  # still in use: keep it out of the pruning below
        else:
            marker.write_text(f"{datetime.now().timestamp()}\n", encoding="utf-8")
        week = datetime.now().timestamp() - 7 * 86400
        sid = event["session_id"]
        mine = {marker.name, f"{marker.name}.reminded", f".last-message-{sid}", f".prompts-{sid}.jsonl"}
        for stale in [*marker.parent.glob(".session-*"), *marker.parent.glob(".last-message-*"), *marker.parent.glob(".prompts-*")]:
            if stale.name in mine:
                continue
            if stale.stat().st_mtime < week:
                stale.unlink(missing_ok=True)
    latest = root / config["checkpoint_dir"] / "latest.md"
    notes = []
    for path in found:
        after = commits_after(root, handoff_time(root, path))
        notes.append(f"{path.relative_to(root).as_posix()}（{when(path)} 更新" + (f"，之後有 {after} 個新 commit）" if after else "）"))
    if latest.is_file():
        notes.append(f"{latest.relative_to(root).as_posix()}（{when(latest)}，hook 自動留下的事實）")
    if not notes:
        return None
    source = event.get("source")
    reason = {"compact": "對話剛被壓縮，壓縮前的細節可能遺失。", "resume": "這是恢復的舊對話。", "clear": "對話剛被清除。"}.get(source, "")
    context = (f"[agf continuity] {reason}這個專案有：{'；'.join(notes)}。開始前先讀它們，照交接檔裡的核對命令確認現況；"
               "交接檔寫的和實際查到的不同時，以實際為準，並在結束前更新交接檔。")
    output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}
    if source == "resume" and event.get("prompt_cache_likely_expired"):
        cost = event.get("estimated_cache_write_usd")
        output["systemMessage"] = ("這個舊對話的快取可能已過期，繼續它會把整段對話重新讀一次" + (f"（估計約 {cost:.2f} 美元）" if isinstance(cost, (int, float)) else "") +
                                   "。如果交接檔夠新，/clear 後照交接檔接著做通常比較省。")
    return output


def pre_compact(event: dict, config: dict, root: Path) -> str:
    paths = ", ".join(p.relative_to(root).as_posix() for p in handoffs(root, config)) or "（目前沒有；請在摘要裡建議建立一份）"
    return ("摘要時務必保留：這次任務的目標與怎樣算做完；已做的決定與理由；已完成的 commit 與驗證結果；正在進行、還沒完成的事；"
            f"照順序的下一步；接手時要執行的核對命令；交接檔的位置：{paths}。不要只寫結論，保留檔案路徑、命令與數字。")


def utf8_stdio() -> None:
    """Claude Code sends and reads hook JSON as UTF-8. Without this, Windows uses the
    locale's code page (cp1252, cp950, ...): printing Chinese raised UnicodeEncodeError,
    which the hook swallowed, so it printed nothing (S15, the CI's Windows jobs)."""
    # surrogateescape keeps bytes that are not UTF-8 instead of failing on them, so such
    # an event is still read and judged; backslashreplace never fails to print.
    for stream, errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"), (sys.stderr, "backslashreplace")):
        try:
            stream.reconfigure(encoding="utf-8", errors=errors)
        except (AttributeError, ValueError):
            pass


def main() -> int:
    utf8_stdio()
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 0
    name = sys.argv[1]
    global deadline
    deadline = time.monotonic() + GIT_BUDGET.get(name, 6.0)
    try:
        config = load_config(sys.argv[2] if len(sys.argv) > 2 else None)
        event = json.load(sys.stdin)
        event = event if isinstance(event, dict) else {}
    except (OSError, ValueError, TypeError) as error:
        print(f"agf continuity: {error}", file=sys.stderr)
        return 0  # a broken helper must not stop the session
    root = project_dir(event)
    try:
        if name == "session-start":
            output = session_start(event, config, root)
            if output:
                print(json.dumps(output, ensure_ascii=False))
        elif name == "pre-compact":
            print(pre_compact(event, config, root))
        elif name == "post-compact":
            write_checkpoint(root, config, "post-compact", {"壓縮摘要": event.get("compact_summary") or "",
                                                             "使用者最近說的話（原文）": recent_prompts(root, config, event)})
        elif name == "stop-failure":
            details = event.get("error_details")
            write_checkpoint(root, config, "stop-failure", {
                "錯誤": f"{event.get('error') or '（事件沒有提供）'}" + (f"\n{json.dumps(details, ensure_ascii=False)[:1000]}" if details else ""),
                "使用者最近說的話（原文）": recent_prompts(root, config, event),
                "最後一則訊息": last_message(root, config, event)})
        elif name == "session-end":
            write_checkpoint(root, config, "session-end", {"結束原因": str(event.get("reason") or ""),
                                                            "使用者最近說的話（原文）": recent_prompts(root, config, event),
                                                            "最後一則訊息": last_message(root, config, event)})
        elif name == "pre-model-switch":
            write_checkpoint(root, config, "pre-model-switch", {
                "切換": f"{event.get('from_model')} → {event.get('to_model')}；context {event.get('context_tokens')} tokens",
                "使用者最近說的話（原文）": recent_prompts(root, config, event),
                "最後一則訊息": last_message(root, config, event)})
            cost = event.get("estimated_cache_write_usd")
            if event.get("prompt_cache_warm") and isinstance(cost, (int, float)) and cost >= float(config["switch_warn_usd"]):
                message = (f"換成 {event.get('to_model')} 要把目前約 {event.get('context_tokens')} tokens 的對話重新寫入快取，估計約 {cost:.2f} 美元。"
                           "比較省的做法：先請 AI 更新交接檔，再 /clear，用新模型照交接檔接著做。")
                if config["block_switch"]:
                    print(json.dumps({"decision": "block", "reason": message}, ensure_ascii=False))
                else:
                    print(json.dumps({"systemMessage": message}, ensure_ascii=False))
        elif name == "user-prompt":
            save_prompt(root, config, event)  # prints nothing: UserPromptSubmit output would be added to the prompt
        elif name == "stop":
            # Keep the last message for a later checkpoint: sessions run without a saved transcript.
            if event.get("last_assistant_message"):
                saved = saved_message(root, config, event)
                saved.parent.mkdir(parents=True, exist_ok=True)
                saved.write_text(clip(event["last_assistant_message"]), encoding="utf-8")
            if not config["stop_reminder"] or event.get("stop_hook_active"):
                return 0
            started = session_marker(root, config, event)
            if not started.is_file():
                return 0  # no record of when this session began: nothing to judge
            began = float(started.read_text(encoding="utf-8").split()[0])
            reminded = started.with_name(started.name + ".reminded")
            # Commits made in this session after the hand-off was last changed or committed.
            stale = [(p, commits_after(root, max(began, handoff_time(root, p)))) for p in handoffs(root, config)]
            stale = [(p, n) for p, n in stale if n]
            if stale and not reminded.exists():
                reminded.write_text("reminded\n", encoding="utf-8")
                path, count = stale[0]
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": (
                    f"[agf continuity] 這個 session 做了 {count} 個 commit，{path.relative_to(root).as_posix()} 還沒跟上。"
                    "結束前更新它：已完成的事（附 commit）、還沒完成的事、照順序的下一步、接手者要跑的核對命令。只更新一次即可。")}},
                    ensure_ascii=False))
        else:
            print(f"agf continuity: unknown event {name}", file=sys.stderr)
    except Exception as error:  # never break the session over a convenience hook
        print(f"agf continuity: {name} failed: {type(error).__name__}: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

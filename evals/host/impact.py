#!/usr/bin/env python3
"""Measure whether the framework helps a project, and what it costs, in fresh Claude Code sessions.

    python evals/host/impact.py run --framework DIR --base EMPTY_DIR --out DIR --model MODEL
        [--switch-model MODEL] [--ids ID,...] [--runs 2] [--group framework] [--group control]
        [--skill NAME ...] [--hooks SETTINGS_JSON] [--budget USD] [--total-budget USD]
        [--seed N] [--jobs N] [--first-repeat N] [--resume OUT_DIR ...] [--cli-version VERSION]
        [--pid-file FILE] [--cli PATH] [--env NAME=VALUE ...] [--allow-env NAME ...] [--forbid PATH ...]
    python evals/host/impact.py report OUT_DIR [OUT_DIR ...] [--md FILE]
    python evals/host/impact.py regrade OUT_DIR --tasks FILE --out NEW_DIR

Each task in evals/impact/tasks.json is run --runs times in each group. The
framework group gets `project install --host claude` with the chosen skills,
and, with --hooks, a .claude/settings.json built from that file (for example
the continuity hooks); the control group gets the task files only. Two more
groups split the framework's fixed cost: rules-only (the install without
skills) and skills-only (the skills without CLAUDE.md, AGENTS.md and .agf/).
Neither gets the hooks. Each part records first_context_tokens, what the
first model call read, so the groups' fixed cost can be compared directly. A task has
one or more parts: every part is a new session in the same directory, so a part
with max_turns that is cut off, followed by a fresh part, stands for "the usage
limit stopped the session and a new one has to continue". A part with
"model": "switch" runs with --switch-model. The reviewed group installs the whole framework like
"framework", then a fresh session with --review-model gets the request and the
last answer, checks the files itself, fixes them and gives the final answer.

Success is decided by hidden checks that run after the last part and are never
in the subject's directory: Python snippets (with a 20-second limit) or a command
with hidden test files, both only inside sandbox.py's container, regular
expressions over the last answer, or over files the subject wrote. A task with
checks.items is judged item by item instead (grading.py; judge.py turns the
items into a verdict), and what the subject left is kept in OUT/artifacts, so
`regrade` can judge it again without paying again. Tokens come
from the CLI's own result event (input, cache creation, cache read, output) and
cost from its estimate; both are summed over the parts.

The run stops before a session would push the total past --total-budget, and
stops on a failed session other than a planned cut-off, instead of spending
more; sessions already running are finished and recorded. It also stops when
another model than the requested one was served or the CLI version changed. A
task and its groups are one block, run one after the other; --jobs blocks run
side by side. Group order alternates from block to block, and --seed shuffles
the tasks and decides which group starts. --resume runs only what the given
directories did not complete and counts what they spent. Every run gets a private parent
directory under --base, removed afterwards, and must pass preflight.py first.
Bash is removed (see trigger.py for why); subjects use Read, Grep, Glob, Edit,
Write and Skill inside their own directory only (sandbox.confinement), and, in a
task with "sandbox": {"image", "command"}, one run_tests tool without arguments.

A timeout or an exhausted per-session budget is a failed run. A usage limit, a
Docker failure or any other error stops the experiment, to be finished later.

`report` reads one or more output directories, so a run that a usage limit
stopped can be finished in a second directory and summarised together; it
refuses directories measured with different models, tools, skills, hooks or
task files. A rerun numbers its repeats from 0 again, so the same task and
repeat number can appear once per directory. The table also shows, for tasks
with a planned cut-off, how many first sessions really were cut, and how many
reads went outside the subject's directory.
"""
from __future__ import annotations

import argparse
from concurrent import futures
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grading  # noqa: E402
import preflight  # noqa: E402
import run_claude  # noqa: E402
import sandbox  # noqa: E402
import trigger  # noqa: E402
from grading import fingerprint  # noqa: E402

TOOLS = " ".join(sandbox.SUBJECT_TOOLS)
CONFINEMENT = "s19"  # change it when the subjects' limits change: such runs are not comparable
CHECK_IMAGE = "python:3.12-slim"  # where Python-snippet checks run
TEST_TOOL = "mcp__bench__run_tests"
GROUPS = ("framework", "control", "rules-only", "skills-only", "reviewed")
REVIEW_PROMPT = ("另一位工程師剛完成下面的工作。請獨立核對：讀相關的程式與檔案，不要只相信他的說法；發現錯誤就直接修正檔案。"
                 "最後用你自己的話完整回答原本的問題，或說明完成的結果。\n\n原本的工作：\n{prompt}\n\n他的最後回覆：\n{answer}")
TOKEN_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def original_work(parts: list[dict]) -> str:
    """What the reviewer is told was asked: every part's request, in order."""
    if len(parts) == 1:
        return parts[0]["prompt"]
    return f"（這個工作分成 {len(parts)} 段、依序交代；以下是各段原本的指示）\n\n" + "\n\n".join(
        f"第 {number} 段：\n{part['prompt']}" for number, part in enumerate(parts, 1))


def load_tasks(path: Path) -> tuple[str, dict[str, dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = {task["id"]: task for task in data["tasks"]}
    for task in tasks.values():
        same = task["checks"].get("same_as")
        if same:
            task["checks"] = tasks[same]["checks"]
    return data.get("startup", ""), tasks


def planned_order(ids: list[str], groups: list[str], repeats, seed: int | None) -> list[tuple[int, str, list[str]]]:
    """The blocks in the order they start: repeat, task, and that task's groups in their order."""
    blocks = []
    for repeat in repeats:
        order, shift = list(ids), len(blocks)
        if seed is not None:
            chance = random.Random(f"{seed}/{repeat}")
            chance.shuffle(order)
            shift = chance.randrange(2)
        for index, task in enumerate(order):
            blocks.append((repeat, task, list(groups) if (shift + index) % 2 == 0 else list(reversed(groups))))
    return blocks


def same_model(requested: str, served: str) -> bool:
    """The requested ID, or its dated snapshot."""
    return re.fullmatch(re.escape(requested) + r"(-\d{8})?", served) is not None


class Ledger:
    """What may still be spent and whether to go on, shared by the blocks that run side by side."""

    def __init__(self, results: dict, save, budget: float, total: float, carried: float = 0.0, version: str | None = None):
        self.results, self.save, self.budget, self.total, self.carried, self.version = results, save, budget, total, carried, version
        self.changed, self.reserved, self.reason = threading.Condition(threading.RLock()), 0, None

    def reserve(self, where: str) -> str | None:
        """Set one session's budget aside, or say why it does not start."""
        with self.changed:
            while True:
                if self.reason:
                    return f"not started after: {self.reason}"
                spent = self.carried + self.results["spent_usd"]
                if spent + (self.reserved + 1) * self.budget <= self.total + 1e-9:
                    self.reserved += 1
                    return None
                if not self.reserved:
                    return f"total budget: {spent:.2f} spent before {where}, the next session may cost up to {self.budget}"
                self.changed.wait(1)  # a running session rarely uses all that was set aside for it

    def charge(self, cost: float) -> None:
        with self.changed:
            self.reserved -= 1
            self.results["spent_usd"] = round(self.results["spent_usd"] + cost, 6)
            self.save()
            self.changed.notify_all()

    def check_version(self, seen: str | None) -> str | None:
        with self.changed:
            if not seen:
                return None
            if self.version and seen != self.version:
                return f"infrastructure: CLI version {seen} instead of {self.version}"
            self.version = self.results["cli_version"] = seen
            return None

    def record(self, row: dict) -> None:
        with self.changed:
            self.results["runs"].append(row)
            if row.get("stop"):
                self.stop(row["stop"])
            self.save()

    def stop(self, reason: str) -> None:
        with self.changed:
            if not self.reason:
                self.reason = self.results["stopped"] = reason
                self.save()
            self.changed.notify_all()


def _inside(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_dir():
        raise SystemExit(f"not a directory inside the task file's directory: {name}")
    return path


def materialize(task: dict, task_dir: Path, work: Path) -> None:
    """The subject's files: a "source" directory next to the task file, then the inline "files"."""
    if task.get("source"):
        shutil.copytree(_inside(task_dir, task["source"]), work, symlinks=True, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git"))
    for name, text in task.get("files", {}).items():
        (work / name).parent.mkdir(parents=True, exist_ok=True)
        (work / name).write_text(text, encoding="utf-8")


def setup_hash(task: dict, task_dir: Path, work: Path) -> str:
    """What the subject gets plus the hidden files. The install's manifest and history differ per install."""
    hidden = task["checks"].get("hidden")
    given = [fingerprint(work, (".agf/manifest.json", ".agf/history/")), fingerprint(_inside(task_dir, hidden)) if hidden else {}]
    return hashlib.sha256(json.dumps(given, sort_keys=True).encode()).hexdigest()


def _restored(task: dict, task_dir: Path, work: Path, names: list[str], copy: Path) -> str | None:
    """Copy work to copy, with the named files as the subject got them (gone if it got none)."""
    pristine = copy.parent / "pristine"
    pristine.mkdir()
    materialize(task, task_dir, pristine)
    shutil.copytree(work, copy, symlinks=True)
    for name in names:
        target = copy / name
        if not target.parent.resolve().is_relative_to(copy.resolve()) or (target.is_dir() and not target.is_symlink()):
            return f"cannot restore {name}"
        target.unlink(missing_ok=True)
        if (pristine / name).is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pristine / name, target)
    return None


def check(task: dict, work: Path, answer: str, task_dir: Path, runner=sandbox.run, start: dict | None = None) -> dict:
    """Run the hidden checks; returns {"passed", "failures"} (and "items"), or {"infrastructure": reason}.

    The subject's code is never executed here: only `runner` (the container) runs it. checks.restore names
    files, say test settings, that go back to what the subject got before the checks run."""
    if names := task["checks"].get("restore"):
        with tempfile.TemporaryDirectory(prefix="agf-restore-") as folder:
            copy = Path(folder).resolve() / "work"
            if problem := _restored(task, task_dir, work, names, copy):
                return {"passed": False, "failures": [problem]}
            return _check(task, copy, answer, task_dir, runner, start)
    return _check(task, work, answer, task_dir, runner, start)


def _check(task: dict, work: Path, answer: str, task_dir: Path, runner, start: dict | None) -> dict:
    checks, failures = task["checks"], []
    image = task.get("sandbox", {}).get("image", CHECK_IMAGE)
    jobs = [(f"python check {index}", *_snippet(code)) for index, code in enumerate(checks.get("python", []))]
    if checks.get("command"):
        hidden = _inside(task_dir, checks["hidden"]) if checks.get("hidden") else None
        jobs.append(("hidden tests", checks["command"], int(checks.get("timeout", 180)), hidden, None))
    broken = []

    def execute(label, command, limit, hidden, mark) -> str | None:
        """Why this check fails, or None."""
        try:
            got = runner(work, image, command, limit, hidden)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            broken.append(f"{label}: {type(error).__name__}")
            return broken[-1]
        if got["infrastructure"]:
            broken.append(f"{label}: the container did not run")
            return broken[-1]
        if got["exit"] != 0:
            reason = "timed out or killed" if got["timed_out"] else got["output"].strip().splitlines()[-1:]
            return f"{label}: {reason}"
        if mark and mark not in got["output"]:
            return f"{label}: the process ended before the check finished"
        return None

    for job in jobs:
        if problem := execute(*job):
            failures.append(problem)
        if broken:
            return {"infrastructure": broken[0]}
    items = None
    if checks.get("items"):
        items = grading.grade(checks["items"], work, answer, start or {}, lambda name, code: not execute(name, *_snippet(code)))
        if broken:
            return {"infrastructure": broken[0]}
        failures += [name for name, held in items.items() if not held]  # ids only: no subject output
    for pattern in checks.get("answer_patterns", []):
        if not re.search(pattern, answer or ""):
            failures.append(f"answer lacks /{pattern}/")
    for name, patterns in checks.get("file_patterns", {}).items():
        file = work / name
        if not file.is_file() or not file.resolve().is_relative_to(work.resolve()):
            failures.append(f"missing {name}")
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        failures += [f"{name} lacks /{pattern}/" for pattern in patterns if not re.search(pattern, text)]
    return {"passed": not failures, "failures": failures, **({"items": items} if items is not None else {})}


def _snippet(code: str) -> tuple[str, int, None, str]:
    # -I plus append: the subject's files never replace the standard library. The mark at the end
    # shows that the whole snippet ran, not that the subject's code ended the process early.
    mark = f"check-finished-{uuid.uuid4().hex}"
    command = "python -I -B -c " + shlex.quote(f"import sys; sys.path.append('.')\n{code}\nprint({mark!r}, flush=True)")
    return command, 20, None, mark


def _install_hooks(framework: Path, work: Path, hooks: Path) -> None:
    """Merge the hooks file into the subject's .claude/settings.json.

    Each `{framework}/<file>` it names is copied into .claude/agf-hooks/ and the
    command points at the copy, so the settings do not show where the framework
    (and its hidden checks) live."""
    text = hooks.read_text(encoding="utf-8")
    folder = work / ".claude" / "agf-hooks"
    for relative in sorted(set(re.findall(r"\{framework\}/([^\s\"']+)", text))):
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(framework / relative, folder / Path(relative).name)
        text = text.replace("{framework}/" + relative, str(folder / Path(relative).name))
    target = work / ".claude" / "settings.json"
    target.parent.mkdir(exist_ok=True)
    settings = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    settings.update(json.loads(text))
    target.write_text(json.dumps(settings, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    framework, out, base = args.framework.resolve(), args.out.resolve(), args.base.resolve()
    task_file = args.tasks.resolve() if args.tasks else framework / "evals/impact/tasks.json"
    startup, tasks = load_tasks(task_file)
    ids = [value for chunk in (args.ids or [",".join(tasks)]) for value in chunk.split(",") if value]
    unknown = [value for value in ids if value not in tasks]
    if unknown:
        raise SystemExit(f"unknown tasks: {unknown}")
    if any(part.get("model") == "switch" for value in ids for part in tasks[value]["parts"]) and not args.switch_model:
        raise SystemExit("a selected task switches model; pass --switch-model")
    if "reviewed" in (args.group or []) and not args.review_model:
        raise SystemExit("the reviewed group needs --review-model")
    skills = args.skill or sorted(path.parent.name for path in (framework / "skills").glob("*/SKILL.md"))
    groups = args.group or ["framework", "control"]
    needed = [tasks[value].get("sandbox", {}).get("image", CHECK_IMAGE) for value in ids
              if tasks[value].get("sandbox") or tasks[value]["checks"].get("python") or tasks[value]["checks"].get("command")
              or any("python" in item for item in tasks[value]["checks"].get("items", []))]
    for value in ids:
        if items := tasks[value]["checks"].get("items"):
            grading.validate(items)
    if (out / "results.json").exists():
        raise SystemExit(f"--out already has results; use a new directory and --resume {out}")
    if needed and (missing := sandbox.missing_images(needed)):
        raise SystemExit(f"Docker or these images are not available: {missing}; the subjects' code only runs in containers")
    base.mkdir(parents=True, exist_ok=True)
    if any(base.iterdir()):
        raise SystemExit(f"--base must be an empty directory: {base}")
    out.mkdir(parents=True, exist_ok=True)
    cli, env = run_claude.find_cli(args.cli), run_claude._pairs(args.env)
    results = {"framework": str(framework), "framework_commit": trigger._commit(framework), "model": args.model,
               "switch_model": args.switch_model, "review_model": args.review_model, "tools": TOOLS, "confinement": CONFINEMENT, "skills": skills, "hooks": str(args.hooks) if args.hooks else None,
               "tasks_sha256": hashlib.sha256(task_file.read_bytes()).hexdigest(),
               "budget_usd": args.budget, "total_budget_usd": args.total_budget, "spent_usd": 0.0, "runs": [], "stopped": None,
               "seed": args.seed, "jobs": args.jobs, "cli_version": args.cli_version}
    try:
        earlier = combine([("this run", results), *((folder.name, json.loads((folder / "results.json").read_text(encoding="utf-8")))
                                                   for folder in args.resume)])
    except (OSError, ValueError) as error:
        raise SystemExit(f"cannot resume: {error}")
    done = {(row["task"], row["group"], row["repeat"]) for row in earlier["runs"] if "passed" in row}
    results["cli_version"] = earlier.get("cli_version")
    save = lambda: (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pid_file = args.pid_file.resolve() if args.pid_file else None
    if pid_file:
        pid_file.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
    ledger = Ledger(results, save, args.budget, args.total_budget, earlier["spent_usd"], results["cli_version"])

    def block(planned: tuple[int, str, list[str]]) -> None:
        repeat, tid, order = planned
        for position, group in enumerate(order):
            if ledger.reason:
                return
            if (tid, group, repeat) in done:
                continue
            try:
                row = run_one(args, framework, base, out, cli, env, startup, tasks[tid], task_file.parent, group, repeat, skills, ledger)
            except BaseException as error:
                ledger.stop(f"{tid}-{group}: {type(error).__name__}")
                raise
            row["position"] = position
            ledger.record(row)

    blocks = planned_order(ids, groups, range(args.first_repeat, args.first_repeat + args.runs), args.seed)
    previous = signal.signal(signal.SIGTERM, trigger._stop_requested)
    pool = futures.ThreadPoolExecutor(max_workers=max(1, args.jobs))
    try:
        running = [pool.submit(block, planned) for planned in blocks]
        while futures.wait(running, timeout=1).not_done:
            pass  # wake up for signals
        pool.shutdown()
        for finished in running:
            finished.result()
        if ledger.reason:
            return 3
    except trigger.Stopped:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        ledger.stop("SIGTERM")
        pool.shutdown()  # what is running is finished and recorded
        return 143
    finally:
        pool.shutdown()
        signal.signal(signal.SIGTERM, previous)
        if pid_file:
            trigger._release(pid_file)
    save()
    return 0


def _session(args, out, cli, work, model, prompt, name, ledger, given, env, expects_tests, extra=(), review=False) -> tuple[dict, dict, str | None]:
    """One session: its record, its result event, and why the experiment has to stop (or None)."""
    stream = out / "streams" / f"{name}.jsonl"
    before = fingerprint(work)
    cost = None
    try:
        code = run_claude.run(cli, work, model, prompt, stream, allowed=given["allowed"], disallowed=given["disallowed"],
                              extra=(*extra, *given["extra"]), env=env, budget=args.budget, timeout=args.timeout)
        summary = run_claude.summarize(stream, work)
        result = summary["result"] or {}
        cost = result.get("cost_usd")
    finally:
        # A killed or crashed session reports no cost; charge the most it could have spent.
        ledger.charge(args.budget if cost is None else cost)
    after = fingerprint(work)
    failed = None
    if code == 124:
        failed = "session timed out"
    elif result.get("subtype") == "error_max_budget_usd":
        failed = "session budget exhausted"
    estimated = cost is None
    cost = args.budget if estimated else cost
    planned_cut = bool(extra) and result.get("subtype") == "error_max_turns"
    part = {"model": model, "served": summary["models"], "cli_version": summary["version"], **({"review": True} if review else {}), "exit": code, "subtype": result.get("subtype"),
            "planned_cut": planned_cut, "failed": failed, "turns": result.get("turns"), "cost_usd": cost,
            **({"cost_is_upper_bound": True} if estimated else {}),
            "first_context_tokens": summary.get("first_context_tokens"), "tools_listed": summary.get("tools_listed"),
            **{key: result.get(key) for key in TOKEN_KEYS},
            "skills_used": trigger.measure(summary, None)["skills_used"],
            "tests_run": sum(use["tool"] == TEST_TOOL for use in summary["tool_uses"]),
            "files_changed": sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key)),
            "files_read": [path.replace(str(work), ".") for path in summary["files_read"]],
            "outside_paths": summary["outside_paths"]}
    stop = ledger.check_version(summary["version"])
    if wrong := [served for served in summary["models"] if not same_model(model, served)]:
        stop = f"infrastructure: served {wrong} instead of {model}"
    if stop:
        return part, result, stop
    if expects_tests and summary["tool_names"] is not None and TEST_TOOL not in summary["tool_names"]:
        stop = "infrastructure: the test tool was not available"
    elif any(error["tool"] == TEST_TOOL and re.search(r"exit code: 12[5-7]\b|test tool failed", error["error"]) for error in summary["tool_errors"]):
        stop = "infrastructure: the test container did not run"
    elif not failed and (not result or ((code != 0 or result.get("is_error")) and not planned_cut)):
        # The host's message can carry the account's reset time and time zone; results.json is published.
        said = re.sub(r".*hit your .*limit.*", "usage limit reached", str(result.get("text"))[:200])
        stop = f"exit {code}, {said}"
    return part, result, stop


def run_one(args, framework, base, out, cli, env, startup, task, task_dir, group, repeat, skills, ledger) -> dict:
    # Two levels, so that runs side by side are not each other's neighbours (preflight).
    private = Path(tempfile.mkdtemp(prefix="job-", dir=base))
    parent = Path(tempfile.mkdtemp(prefix="run-", dir=private))
    name = f"{task['id']}-{group}-{repeat}"
    row = {"task": task["id"], "kind": task.get("kind"), "negative": bool(task.get("negative")), "group": group, "repeat": repeat, "parts": []}
    try:
        work = parent / "work"
        work.mkdir()
        materialize(task, task_dir, work)
        installed = [] if group in ("control", "rules-only") else skills
        hooked = bool(args.hooks) and group in ("framework", "reviewed")
        if group != "control":
            trigger._install(framework, work, installed)
            if group == "skills-only":
                for entry in ("CLAUDE.md", "AGENTS.md"):
                    (work / entry).unlink(missing_ok=True)
                shutil.rmtree(work / ".agf", ignore_errors=True)
            if hooked:
                _install_hooks(framework, work, args.hooks.resolve())
        row["setup_sha256"] = setup_hash(task, task_dir, work)
        box = task.get("sandbox", {})
        given = sandbox.confinement(work, box.get("image"), box.get("command"), box.get("timeout", 180),
                                    skills=tuple(installed), hooks=hooked)
        session_env = {**env, **given["env"]}  # last, so --env cannot loosen it
        checked = preflight.check(work, args.forbid, session_env,
                                  set(args.allow_env) | {"CLAUDE_CODE_DISABLE_AUTO_MEMORY"})
        if checked["user_level"]:
            # Under the home directory the host loads ~/.claude as an ancestor, whatever --setting-sources says (S19).
            raise SystemExit(f"--base must be outside the home directory, whose instructions would reach every group: {checked['user_level']}")
        if not checked["ok"]:
            raise SystemExit(f"preflight failed before {task['id']}-{group}: {json.dumps(checked, ensure_ascii=False)}")
        start = fingerprint(work)
        planned = [(str(number), args.switch_model if part.get("model") == "switch" else args.model, part)
                   for number, part in enumerate(task["parts"], 1)]
        if group == "reviewed":
            # D group: a different model checks the finished work, fixes it and gives the final answer;
            # the hidden checks judge what it leaves behind.
            planned.append(("review", args.review_model, {"prompt": original_work(task["parts"]), "review": True}))
        answer, failed = "", None
        for label, model, part in planned:
            where = f"{task['id']}-{group} {label}"
            review = bool(part.get("review"))
            prompt = REVIEW_PROMPT.format(prompt=part["prompt"], answer=answer) if review else part["prompt"]
            extra = ("--max-turns", str(part["max_turns"])) if part.get("max_turns") else ()
            if refused := ledger.reserve(where):
                row["stop"] = refused
                return row
            print(f"run {task['id']} {group} #{repeat} {'review' if review else 'part ' + label}", flush=True)
            record, result, stop = _session(args, out, cli, work, model, f"{startup}\n\n{prompt}" if startup else prompt,
                                            f"{name}-{label}", ledger, given, session_env,
                                            bool(box.get("command")), extra, review)
            row["parts"].append(record)
            if stop:
                row["stop"] = f"{where}: {stop}"
                return row
            answer, failed = result.get("text") or "", record["failed"]
            if failed:
                break
        (out / "outputs").mkdir(exist_ok=True)
        (out / "outputs" / f"{name}.md").write_text(answer + "\n", encoding="utf-8")
        items = task["checks"].get("items")
        if items:
            kept = out / "artifacts"
            kept.mkdir(exist_ok=True)
            shutil.copytree(work, kept / name, symlinks=True)
            (kept / f"{name}.start.json").write_text(json.dumps(start) + "\n", encoding="utf-8")
            row["artifact"] = name
        if failed:
            row.update(passed=False, failures=[failed], **({"items": {item["id"]: False for item in items}} if items else {}))
        else:
            verdict = check(task, work, answer, task_dir, start=start)
            if "infrastructure" in verdict:
                row["stop"] = f"{task['id']}-{group} check: infrastructure: {verdict['infrastructure']}"
                return row
            row.update(verdict)
        row["handoff_files"] = sorted(str(path.relative_to(work)) for pattern in ("*HANDOFF*", "*CHECKPOINT*", ".agf/checkpoints/*")
                                      for path in work.glob(pattern) if path.is_file())
        return row
    finally:
        shutil.rmtree(private, ignore_errors=True)


def regrade(args: argparse.Namespace) -> int:
    """Judge the kept work again, for a corrected task file; nothing is paid."""
    source, out, task_file = args.source.resolve(), args.out.resolve(), args.tasks.resolve()
    if (out / "results.json").exists():
        raise SystemExit(f"--out already has results: {out}")
    data = json.loads((source / "results.json").read_text(encoding="utf-8"))
    kept = Path(data.get("artifacts_in") or source)
    _, tasks = load_tasks(task_file)
    for row in data["runs"]:
        if not row.get("artifact") or "passed" not in row:
            continue
        task, name = tasks[row["task"]], row["artifact"]
        if any(part.get("failed") for part in row["parts"]):
            row["items"] = {item["id"]: False for item in task["checks"]["items"]}
            continue
        answer = (kept / "outputs" / f"{name}.md").read_text(encoding="utf-8")[:-1]
        start = json.loads((kept / "artifacts" / f"{name}.start.json").read_text(encoding="utf-8"))
        found = check(task, kept / "artifacts" / name, answer, task_file.parent, start=start)
        if "infrastructure" in found:
            raise SystemExit(f"{name}: {found['infrastructure']}")
        row.update(found)
    data.update(regraded_from=data["tasks_sha256"], artifacts_in=str(kept), tasks_sha256=hashlib.sha256(task_file.read_bytes()).hexdigest())
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


def _sum(row: dict, key: str) -> float:
    return sum(part.get(key) or 0 for part in row["parts"])


def summarize_runs(data: dict) -> dict:
    """Per group and per task: pass rate, median and total cost, tokens and turns over completed runs."""
    done = [row for row in data["runs"] if "passed" in row]
    table = {}
    for row in done:
        cell = table.setdefault(row["task"], {}).setdefault(row["group"], {"runs": 0, "passed": 0, "cost": [], "tokens": [], "turns": [], "last_part_tokens": [],
                                                                            "cuts_planned": 0, "cuts_happened": 0, "outside_reads": 0,
                                                                            "first_context": [], "tools_listed": set()})
        cell["runs"] += 1
        cell["passed"] += bool(row["passed"])
        task_parts = [part for part in row["parts"] if not part.get("review")]
        for part in task_parts[:-1]:
            # Every part before the last is meant to be cut off; one that finished early did not test a hand-over.
            cell["cuts_planned"] += 1
            cell["cuts_happened"] += bool(part.get("planned_cut"))
        cell["outside_reads"] += sum(len(part.get("outside_paths") or []) for part in row["parts"])
        cell["tools_listed"].update(part["tools_listed"] for part in row["parts"] if part.get("tools_listed") is not None)
        if row["parts"] and row["parts"][0].get("first_context_tokens") is not None:
            cell["first_context"].append(row["parts"][0]["first_context_tokens"])
        cell["cost"].append(_sum(row, "cost_usd"))
        cell["tokens"].append(sum(_sum(row, key) for key in TOKEN_KEYS))
        cell["turns"].append(_sum(row, "turns"))
        last = task_parts[-1]  # not the review, which would differ per group
        cell["last_part_tokens"].append(sum(last.get(key) or 0 for key in TOKEN_KEYS))
    groups = {}
    for cells in table.values():
        for group, cell in cells.items():
            total = groups.setdefault(group, {"runs": 0, "passed": 0, "cost_usd": 0.0, "tokens": 0})
            total["runs"] += cell["runs"]
            total["passed"] += cell["passed"]
            total["cost_usd"] = round(total["cost_usd"] + sum(cell["cost"]), 4)
            total["tokens"] += int(sum(cell["tokens"]))
    median = lambda values: round(statistics.median(values), 4) if values else None
    tasks = {task: {group: {"passed": f"{cell['passed']}/{cell['runs']}", "median_cost_usd": median(cell["cost"]),
                            "median_tokens": median(cell["tokens"]), "median_turns": median(cell["turns"]),
                            "median_last_part_tokens": median(cell["last_part_tokens"]), "outside_reads": cell["outside_reads"],
                            "median_first_context_tokens": median(cell["first_context"]),
                            # More than one value: a session saw extra tools (say an MCP server that
                            # connected), which changes the context size; compare such cells with care.
                            "tools_listed": sorted(cell["tools_listed"]),
                            **({"cuts": f"{cell['cuts_happened']}/{cell['cuts_planned']}"} if cell["cuts_planned"] else {})}
                    for group, cell in cells.items()} for task, cells in table.items()}
    return {"model": data["model"], "switch_model": data.get("switch_model"), "framework_commit": data["framework_commit"],
            "spent_usd": data["spent_usd"], "stopped": data["stopped"], "groups": groups, "tasks": tasks,
            "incomplete_runs": len(data["runs"]) - len(done)}


SAME_SETUP = ("model", "switch_model", "review_model", "tools", "skills", "hooks", "tasks_sha256")


def combine(named: list[tuple[str, dict]]) -> dict:
    """Merge results.json files of separate runs (for example one finished after a usage limit).

    The runs must share the models, tools, skills, hooks and task file (when the
    files record it); framework commits may differ and are all listed."""
    first_name, first = named[0]
    for name, data in named[1:]:
        if first.get("confinement") != data.get("confinement"):
            raise ValueError(f"confinement differs: {first_name} and {name} did not limit their subjects the same way")
        for key in SAME_SETUP:
            if key in first and key in data and data[key] != first[key]:
                raise ValueError(f"{key} differs: {first_name} has {first[key]!r}, {name} has {data[key]!r}")
    setups = {}
    for name, data in named:
        for row in data["runs"]:
            if row.get("setup_sha256"):
                cell = (row["task"], row["group"])
                if setups.setdefault(cell, row["setup_sha256"]) != row["setup_sha256"]:
                    raise ValueError(f"setup differs for {cell[0]}/{cell[1]} in {name}: files, framework or hidden checks changed")
    versions = sorted({data["cli_version"] for _, data in named if data.get("cli_version")})
    if len(versions) > 1:
        raise ValueError(f"cli_version differs: {versions}")
    commits = sorted({str(data.get("framework_commit")) for _, data in named})
    stopped = [f"{name}: {data['stopped']}" for name, data in named if data.get("stopped")]
    return {**{key: first[key] for key in (*SAME_SETUP, "confinement") if key in first}, "cli_version": versions[0] if versions else None,
            "model": first["model"], "switch_model": first.get("switch_model"), "framework_commit": ", ".join(commits),
            "spent_usd": round(sum(data["spent_usd"] for _, data in named), 6),
            "stopped": "; ".join(stopped) or None, "runs": [row for _, data in named for row in data["runs"]]}


def report(args: argparse.Namespace) -> int:
    folders = [out.resolve() for out in args.out]
    if len(set(folders)) != len(folders):
        print("impact report: the same directory was given twice", file=sys.stderr)
        return 2
    try:
        data = combine([(out.name, json.loads((out / "results.json").read_text(encoding="utf-8"))) for out in folders])
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"impact report: {error}", file=sys.stderr)
        return 2
    summary = summarize_runs(data)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    lines = ["| task | group | passed | median cost (USD) | median tokens | median turns | last session tokens | first call context | cut as planned | reads outside |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for task, cells in summary["tasks"].items():
        for group, cell in sorted(cells.items()):
            lines.append(f"| {task} | {group} | {cell['passed']} | {cell['median_cost_usd']} | {cell['median_tokens']} | {cell['median_turns']} "
                         f"| {cell['median_last_part_tokens']} | {cell['median_first_context_tokens']} | {cell.get('cuts', '—')} | {cell['outside_reads']} |")
    target = args.md or (args.out[0] / "report.md" if len(args.out) == 1 else None)
    if target:
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("run")
    one.add_argument("--framework", type=Path, required=True)
    one.add_argument("--base", type=Path, required=True, help="empty directory outside any project")
    one.add_argument("--out", type=Path, required=True)
    one.add_argument("--model", required=True, help="model ID for the subject sessions; there is no default")
    one.add_argument("--switch-model", help="model for parts marked \"model\": \"switch\"")
    one.add_argument("--review-model", help="model that reviews and fixes the finished work in the reviewed group")
    one.add_argument("--tasks", type=Path, help="task file (default: the framework's evals/impact/tasks.json)")
    one.add_argument("--ids", action="append", help="task ids, comma-separated or repeated (default: all)")
    one.add_argument("--runs", type=int, default=2, help="repeats per task and group")
    one.add_argument("--group", action="append", choices=GROUPS)
    one.add_argument("--skill", action="append", help="skills installed in the framework group (default: all)")
    one.add_argument("--hooks", type=Path, help="JSON merged into the framework group's .claude/settings.json")
    one.add_argument("--budget", type=float, default=0.5, help="per-session --max-budget-usd")
    one.add_argument("--total-budget", type=float, default=4.0, help="stop before the total would pass this")
    one.add_argument("--timeout", type=int, default=900)
    one.add_argument("--seed", type=int, help="shuffle the tasks and choose which group starts, reproducibly")
    one.add_argument("--jobs", type=int, default=1, help="blocks (a task with its groups) that run side by side")
    one.add_argument("--first-repeat", type=int, default=0, help="number of the first repeat, for a later stage")
    one.add_argument("--resume", type=Path, action="append", default=[], help="an earlier --out: skip what it completed, count what it spent")
    one.add_argument("--cli-version", help="stop when a session reports another version")
    one.add_argument("--pid-file", type=Path)
    one.add_argument("--cli")
    one.add_argument("--env", action="append", default=[])
    one.add_argument("--allow-env", action="append", default=[])
    one.add_argument("--forbid", action="append", default=[], help="a path the subject's files must not mention (repeatable)")
    one.set_defaults(func=run)
    two = sub.add_parser("report")
    two.add_argument("out", type=Path, nargs="+", help="one or more --out directories of the same models")
    two.add_argument("--md", type=Path, help="where to write the Markdown table (default: OUT_DIR/report.md for one directory)")
    two.set_defaults(func=report)
    three = sub.add_parser("regrade")
    three.add_argument("source", type=Path, help="an --out directory whose artifacts are judged again")
    three.add_argument("--tasks", type=Path, required=True)
    three.add_argument("--out", type=Path, required=True)
    three.set_defaults(func=regrade)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

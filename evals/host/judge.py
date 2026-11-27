#!/usr/bin/env python3
"""From impact.py's rows to a verdict (the method of studies/research-2026-11/Q-s22-benchmark-design.md).

    python evals/host/judge.py judge RESULTS [RESULTS ...] [--alpha 0.0294]
    python evals/host/judge.py agree --one RESULTS ... --other RESULTS ...
    python evals/host/judge.py sample OUT_DIR [OUT_DIR ...] --tasks FILE --seed N --to EMPTY_DIR [--share 0.2]
    python evals/host/judge.py export RESULTS [RESULTS ...] --to FILE

RESULTS is an output directory of `impact.py run` or a file written by `export`. Scores need tasks with
checks.items: a run scores the share of its items that hold. The task is the sample: d is the mean score
with the framework minus the mean without it, over the repeats both groups completed.

    benefit          the interval's lower end is above 0, the mean at least the margin, and an exact
                     sign-flip permutation test is significant too
    harm             the interval's upper end is below 0
    not worth it     the upper end is below the margin
    inconclusive     anything else

Negative tasks are not part of the score; one counts as wrong by the share of its repeats with any item wrong. Run `sample` and read it before `judge`, so that the checks of
the judgements cannot follow the groups' results.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fnmatch import fnmatchcase
from fractions import Fraction
from functools import lru_cache
import json
from math import ceil, exp, lcm, lgamma, log, pi, sqrt
from pathlib import Path
import random
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grading  # noqa: E402
import impact  # noqa: E402

TREATED, CONTROL = "framework", "control"
ALPHA = 0.0294  # Pocock's boundary for two looks
MARGIN, LARGE, MIN_TASKS = 0.10, 0.25, 20
CACHE_APART = 0.10  # shares of cache reads this far apart make the costs hard to compare
CORRELATED = 0.4  # agree: above chance for 24 tasks (one-sided 0.05 is 0.344)
EPSILON = 1e-9
# What would tell an auditor the group. ASCII classes: Chinese has no spaces, so \S and \b would eat or miss it.
_PATH = r"[A-Za-z0-9_./-]"
GROUP_MARKS = rf"CLAUDE\.md|AGENTS\.md|{_PATH}*\.(?:agf|claude){_PATH}*|(?:HANDOFF|CHECKPOINT){_PATH}*|(?<![a-z])skills?(?![a-z])|(?<![a-z])agf(?![a-z])(?: traces check| [a-z]+)?|專案規則|交接檔?|檢查點"


@lru_cache(maxsize=None)
def t_critical(alpha: float, freedom: int) -> float:
    """Two-sided critical value of Student's t."""
    scale = exp(lgamma((freedom + 1) / 2) - lgamma(freedom / 2) - 0.5 * log(freedom * pi))

    def central(limit: float, steps: int = 2000) -> float:  # P(|T| < limit), Simpson's rule
        width, total = limit / steps, 0.0
        for step in range(steps + 1):
            weight = 1 if step in (0, steps) else 4 if step % 2 else 2
            total += weight * (1 + (step * width) ** 2 / freedom) ** (-(freedom + 1) / 2)
        return 2 * scale * total * width / 3

    low, high = 0.0, 100.0
    for _ in range(50):
        middle = (low + high) / 2
        low, high = (middle, high) if central(middle) < 1 - alpha else (low, middle)
    return (low + high) / 2


def sign_flip(differences: list) -> float:
    """Exact two-sided p of the mean when every task's sign could as well have been the other."""
    exact = [Fraction(value).limit_denominator(10000) for value in differences]
    unit = lcm(*(value.denominator for value in exact))
    values = [int(value * unit) for value in exact]
    sums = {0: 1}
    for size in map(abs, values):
        following = defaultdict(int)
        for total, count in sums.items():
            following[total + size] += count
            following[total - size] += count
        sums = following
    return sum(count for total, count in sums.items() if abs(total) >= abs(sum(values))) / 2 ** len(values)


def interval(values: list[float], alpha: float) -> tuple[float, float, float]:
    mean = sum(values) / len(values)
    deviation = sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))
    half = t_critical(alpha, len(values) - 1) * deviation / sqrt(len(values))
    return mean, mean - half, mean + half


def decide(differences: list, alpha: float = ALPHA, margin: float = MARGIN, large: float = LARGE) -> dict:
    mean, low, high = interval([float(value) for value in differences], alpha)
    p = sign_flip(differences)
    if low > EPSILON and mean >= margin - EPSILON and p <= alpha:
        verdict = "benefit"
    elif high < -EPSILON:
        verdict = "harm"
    elif high < margin - EPSILON:
        verdict = "not worth it"
    else:
        verdict = "inconclusive"
    return {"verdict": verdict, "mean": mean, "low": low, "high": high, "p_sign_flip": p, "rules_out_large": high < large - EPSILON}


def paired(rows: list[dict]) -> dict[str, list[tuple[dict, dict]]]:
    """Per task, the (without, with) rows of every repeat both groups completed."""
    cells = defaultdict(dict)
    for row in rows:
        if row.get("items") is None or row["group"] not in (TREATED, CONTROL):
            continue
        cell = cells[row["task"], row["repeat"]]
        if row["group"] in cell:
            raise ValueError(f"completed twice: {row['task']} {row['group']} #{row['repeat']}")
        cell[row["group"]] = row
    tasks = defaultdict(list)
    for (task, _), cell in sorted(cells.items()):
        if len(cell) == 2:
            tasks[task].append((cell[CONTROL], cell[TREATED]))
    return dict(tasks)


def score(row: dict) -> Fraction:
    return Fraction(sum(map(bool, row["items"].values())), len(row["items"]))


def differences(tasks: dict[str, list[tuple[dict, dict]]]) -> dict[str, Fraction]:
    return {task: sum((score(new) - score(old) for old, new in pairs), Fraction(0)) / len(pairs) for task, pairs in tasks.items()}


def spending(tasks: dict[str, list[tuple[dict, dict]]], alpha: float) -> dict:
    logs, totals = [], {group: defaultdict(float) for group in (CONTROL, TREATED)}
    for pairs in tasks.values():
        costs = [0.0, 0.0]
        for pair in pairs:
            for side, (group, row) in enumerate(zip((CONTROL, TREATED), pair)):
                for part in row.get("parts", []):
                    costs[side] += part.get("cost_usd") or 0
                    for key in ("cost_usd", *impact.TOKEN_KEYS):
                        totals[group][key] += part.get(key) or 0
        if all(costs):
            logs.append(log(costs[1] / costs[0]))
    found = {"totals": {group: dict(total) for group, total in totals.items()}, "cache_read_share": {}}
    for group, total in totals.items():
        read = total["cache_read_input_tokens"]
        sent = read + total["input_tokens"] + total["cache_creation_input_tokens"]
        found["cache_read_share"][group] = read / sent if sent else None
    found["token_ratio"] = {key: totals[TREATED][key] / totals[CONTROL][key] if totals[CONTROL][key] else None
                            for key in impact.TOKEN_KEYS}
    shares = [share for share in found["cache_read_share"].values() if share is not None]
    found["cache_differs"] = len(shares) == 2 and abs(shares[0] - shares[1]) > CACHE_APART
    if len(logs) > 1:
        found.update(zip(("ratio", "ratio_low", "ratio_high"), map(exp, interval(logs, alpha))))
    return found


def judge(rows: list[dict], alpha: float = ALPHA, min_tasks: int = MIN_TASKS) -> dict:
    tasks = paired([row for row in rows if not row.get("negative")])
    negatives = paired([row for row in rows if row.get("negative")])
    change = differences(tasks)
    if len(change) < max(2, min_tasks):
        found = {"verdict": "no conclusion"}
    else:
        found = decide(list(change.values()), alpha)
    found.update(tasks=len(change), alpha=alpha, second_stage=found["verdict"] == "inconclusive")
    wrong = [sum(sum(not all(pair[side]["items"].values()) for pair in pairs) / len(pairs) for pairs in negatives.values())
             for side in (0, 1)]
    found["negatives"] = {"tasks": len(negatives), "wrong_control": wrong[0], "wrong_framework": wrong[1],
                          "side_effect": wrong[1] - wrong[0] >= 2 - EPSILON}
    both = [pair for cells in (tasks, negatives) for pairs in cells.values() for pair in pairs]
    found["failed_runs"] = {group: sum(any(part.get("failed") for part in pair[side].get("parts", [])) for pair in both)
                            for side, group in ((0, CONTROL), (1, TREATED))}
    found["by_item"] = {task: {item: {CONTROL: sum(bool(old["items"].get(item)) for old, _ in pairs),
                                      TREATED: sum(bool(new["items"].get(item)) for _, new in pairs), "runs": len(pairs)}
                               for item in pairs[0][0]["items"]}
                        for task, pairs in {**tasks, **negatives}.items()}
    if len(change) < 2:
        return found
    means = {side: [float(sum((score(pair[side]) for pair in pairs), Fraction(0)) / len(pairs)) for pairs in tasks.values()] for side in (0, 1)}
    found["score"] = {CONTROL: sum(means[0]) / len(change), TREATED: sum(means[1]) / len(change)}
    found["control_at_ceiling"] = sum(value == 1 for value in means[0])
    found["cost"] = spending(tasks, alpha)
    found["per_task"] = {task: float(value) for task, value in change.items()}
    kinds = {task: pairs[0][0].get("kind") for task, pairs in tasks.items()}
    # Directions only: a handful of tasks each.
    found["by_kind"], found["without_kind"] = {}, {}
    for kind in sorted(set(kinds.values()), key=str):
        inside = [value for task, value in change.items() if kinds[task] == kind]
        others = [value for task, value in change.items() if kinds[task] != kind]
        found["by_kind"][kind] = {"tasks": len(inside), "mean": float(sum(inside) / len(inside))}
        if len(inside) > 1:
            found["by_kind"][kind].update(zip(("low", "high"), interval([float(value) for value in inside], alpha)[1:]))
        if len(others) > 1:
            found["without_kind"][kind] = decide(others, alpha)  # does the conclusion rest on this one kind?
    found["rests_on"] = [kind for kind, without in found["without_kind"].items()
                         if found["verdict"] == "benefit" and without["verdict"] != "benefit"]
    return found


def correlation(one: list[float], other: list[float]) -> float | None:
    middle = [sum(values) / len(values) if values else 0 for values in (one, other)]
    spread = sqrt(sum((x - middle[0]) ** 2 for x in one) * sum((y - middle[1]) ** 2 for y in other))
    return sum((x - middle[0]) * (y - middle[1]) for x, y in zip(one, other)) / spread if spread else None


def agree(one: list[dict], other: list[dict]) -> dict:
    """Can one model stand in for the other (the rule fixed before the S22 runs)?"""
    first, second = (differences(paired([row for row in rows if not row.get("negative")])) for rows in (one, other))
    common = sorted(first.keys() & second.keys())
    both = [task for task in common if first[task] and second[task]]
    same = sum((first[task] > 0) == (second[task] > 0) for task in both)
    apart = abs(float(sum(first[task] - second[task] for task in common) / len(common))) if common else None
    related = correlation([float(first[task]) for task in common], [float(second[task]) for task in common])
    return {"tasks": len(common), "both_nonzero": len(both), "same_sign": same, "mean_apart": apart, "correlation": related,
            # Same signs alone follow from a shared mean; the tasks have to agree as well.
            "stands_in": len(both) >= 8 and same >= 0.75 * len(both) and apart <= MARGIN + EPSILON
            and related is not None and related >= CORRELATED}


def public_row(row: dict, skills=()) -> dict:
    """Judgements, counts and spend only: no text, no path. skills_used is the subject's text unless it is an installed name."""
    keys = ("task", "kind", "negative", "group", "repeat", "position", "passed", "items", "setup_sha256")
    part_keys = ("model", "served", "cli_version", "subtype", "failed", "turns", "cost_usd", "cost_is_upper_bound",
                 "first_context_tokens", "tools_listed", *impact.TOKEN_KEYS, "skills_used")
    return {**{key: row[key] for key in keys if key in row},
            "outside_reads": sum(len(part.get("outside_paths") or []) for part in row.get("parts", [])),
            "parts": [{key: [name for name in part[key] if name in skills] if key == "skills_used" else part[key]
                       for key in part_keys if key in part} for part in row.get("parts", [])]}


def load(paths: list[Path]) -> dict:
    files = [path / "results.json" if path.is_dir() else path for path in paths]
    return impact.combine([(path.name, json.loads(file.read_text(encoding="utf-8"))) for path, file in zip(paths, files)])


def redact(text: str, names=()) -> str:
    return re.sub("|".join([GROUP_MARKS, *map(re.escape, sorted(names))]), "<hidden>", text, flags=re.IGNORECASE)


def _globs(items: list[dict]) -> list[str]:
    """The paths items name by pattern: a file that should have been left alone is what they are about."""
    found = []
    for item in items:
        found += [*item.get("unchanged", []), *item.get("changed_only", []), *_globs(item.get("one_of", []))]
    return found


def runs_of(folders: list[Path]) -> tuple[list[tuple[Path, dict]], set[str]]:
    """Every run with kept work and item verdicts, with the folder its work is in, and the skills to hide."""
    runs, skills = [], set()
    for folder in folders:
        data = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        skills.update(data.get("skills") or [])
        runs += [(Path(row.get("kept_in") or folder), row) for row in data["runs"] if row.get("artifact") and row.get("items") is not None]
    return runs, skills


def sheet(name: str, folder: Path, row: dict, task: dict, skills, verdicts: bool = True) -> str:
    """One run to read without its group: the prompts, the answer, the changed files and the items.

    Without verdicts the items are listed by meaning only, for a reader who judges them afresh."""
    items, work = task["checks"]["items"], folder / "artifacts" / row["artifact"]
    start = json.loads((folder / "artifacts" / f"{row['artifact']}.start.json").read_text(encoding="utf-8"))
    lines = [f"# {name}: {row['task']}", "", *(f"> {part['prompt']}" for part in task["parts"]), "", "## answer", "",
             redact((folder / "outputs" / f"{row['artifact']}.md").read_text(encoding="utf-8"), skills), "## changes", ""]
    judged_text, extra, globs = json.dumps(items, ensure_ascii=False), 0, _globs(items)
    for changed in grading.changes(start, work):
        if changed not in task.get("files", {}) and changed not in judged_text \
                and not any(fnmatchcase(changed, glob) for glob in globs):
            # Notes, by whatever name, would tell the group; only change-based items look at them.
            extra += 1
            lines += [f"### another file, number {extra}", ""]
            continue
        file = work / changed
        text = file.read_text(encoding="utf-8", errors="replace") if file.is_file() and not file.is_symlink() else "(gone or not a file)"
        lines += [f"### {redact(changed, skills)}", "", redact(text[:6000], skills), ""]
    if not verdicts:
        return "\n".join([*lines, "## items to judge", "", *(f"- {item['id']}: {item.get('means', '')}" for item in items)]) + "\n"
    lines += ["## judgements", ""]
    if any(part.get("failed") for part in row.get("parts", [])):
        lines += ["The session failed, so by the rule every item fails.", ""]
    for item in items:
        conditions = {key: value for key, value in item.items() if key not in ("id", "means")}
        lines += [f"- {item['id']}: {'holds' if row['items'].get(item['id']) else 'fails'} -- {item.get('means', '')}",
                  f"  `{json.dumps(conditions, ensure_ascii=False)}`"]
    return "\n".join(lines) + "\n"


def sample(folders: list[Path], task_file: Path, seed: int, share: float, to: Path) -> int:
    """Runs to read without knowing their group. The key goes to keys/, apart from the sheets."""
    _, tasks = impact.load_tasks(task_file)
    runs, skills = runs_of(folders)
    chosen = random.Random(f"audit/{seed}").sample(runs, ceil(share * len(runs)))
    to.mkdir(parents=True, exist_ok=True)
    if any(to.iterdir()):
        raise SystemExit(f"--to must be empty: {to}")
    key = {}
    for number, (folder, row) in enumerate(chosen, 1):
        name = f"r{number:03d}"
        text = sheet(name, folder, row, tasks[row["task"]], skills)
        (to / f"{name}.md").write_text(text, encoding="utf-8", errors="replace")
        key[name] = {"dir": folder.name, "artifact": row["artifact"], "group": row["group"]}
    (to.parent / "keys").mkdir(exist_ok=True)
    impact.write_json(to.parent / "keys" / f"{to.name}.json", key)
    print(f"{len(chosen)} of {len(runs)} runs")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("judge")
    one.add_argument("results", type=Path, nargs="+")
    one.add_argument("--alpha", type=float, default=ALPHA)
    two = sub.add_parser("agree")
    two.add_argument("--one", type=Path, nargs="+", required=True)
    two.add_argument("--other", type=Path, nargs="+", required=True)
    three = sub.add_parser("sample")
    three.add_argument("results", type=Path, nargs="+")
    three.add_argument("--tasks", type=Path, required=True)
    three.add_argument("--seed", type=int, required=True)
    three.add_argument("--share", type=float, default=0.2)
    three.add_argument("--to", type=Path, required=True)
    four = sub.add_parser("export")
    four.add_argument("results", type=Path, nargs="+")
    four.add_argument("--to", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "sample":
            return sample(args.results, args.tasks, args.seed, args.share, args.to)
        if args.command == "judge":
            print(json.dumps(judge(load(args.results)["runs"], args.alpha), ensure_ascii=False, indent=1))
        elif args.command == "agree":
            print(json.dumps(agree(load(args.one)["runs"], load(args.other)["runs"]), indent=1))
        else:
            data = load(args.results)
            kept = {key: data.get(key) for key in (*impact.SAME_SETUP, "confinement", "cli_version", "framework_commit", "spent_usd")}
            kept.update(stopped=bool(data["stopped"]), runs=[public_row(row, data.get("skills") or ()) for row in data["runs"]])
            impact.write_json(args.to, kept)
    except ValueError as error:
        print(f"judge: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Apply the thresholds of M-s19.md, as written, to grouped impact results.

    python3 -I judge.py RESULTS_DIR [RESULTS_DIR ...]

A = control, B = rules-only, C = framework. B and C are each compared with A, and C also with B.
When a cap cut the runs short, only blocks that all measured groups completed count: the first n completed
runs of each task, n being the smallest count among the groups. The directories are read in the given order.
"""
from fractions import Fraction
import json
from math import comb
from pathlib import Path
import sys

NAMES = {"control": "A", "rules-only": "B", "framework": "C"}


def fisher(a: int, n: int, b: int, m: int) -> float:
    """Two-sided Fisher exact test for a/n against b/m."""
    total, passed = n + m, a + b

    def ways(x: int) -> int:
        return comb(n, x) * comb(m, passed - x) if 0 <= passed - x <= m else 0

    observed = ways(a)
    return sum(ways(x) for x in range(min(n, passed) + 1) if ways(x) <= observed) / comb(total, passed)


def verdict(base: dict, new: dict) -> dict:
    a, n = sum(p for p, _ in base["tasks"].values()), sum(r for _, r in base["tasks"].values())
    b, m = sum(p for p, _ in new["tasks"].values()), sum(r for _, r in new["tasks"].values())
    gain = Fraction(b, m) - Fraction(a, n)
    worse = [task for task, (passed, _) in new["tasks"].items() if task in base["tasks"] and base["tasks"][task][0] - passed >= 2]
    p = fisher(a, n, b, m)
    ratio = new["cost"] / base["cost"] if base["cost"] else None
    if gain >= Fraction(20, 100) and not worse:
        label = "有好處" + ("" if p < 0.05 else "（方向，不是定論）")
    elif ratio is not None and ratio > 1.10:
        label = "只是比較貴"
    else:
        label = "量不出差別"
    return {"passed": f"{b}/{m} vs {a}/{n}", "gain_points": round(float(gain * 100), 1), "fisher_p": round(p, 4),
            "tasks_2_or_more_worse": worse, "cost_ratio": ratio and round(ratio, 3), "verdict": label}


def main() -> None:
    rows: dict[tuple[str, str], list[dict]] = {}
    for folder in sys.argv[1:]:
        for row in json.loads((Path(folder) / "results.json").read_text(encoding="utf-8"))["runs"]:
            if "passed" not in row or row["group"] not in NAMES:
                continue  # interrupted runs are rerun, not counted
            rows.setdefault((NAMES[row["group"]], row["task"]), []).append(row)
    measured = sorted({group for group, _ in rows})
    blocks = {task: min(len(rows.get((group, task), [])) for group in measured) for task in sorted({task for _, task in rows})}
    groups: dict[str, dict] = {}
    for group in measured:
        tasks, cost, budget_failures = {}, 0.0, 0
        for task, count in blocks.items():
            used = rows.get((group, task), [])[:count]
            if not used:
                continue
            tasks[task] = (sum(bool(row["passed"]) for row in used), count)
            cost += sum(part.get("cost_usd") or 0 for row in used for part in row["parts"])
            budget_failures += sum("session budget exhausted" in (row.get("failures") or []) for row in used)
        if tasks:
            groups[group] = {"tasks": tasks, "cost": cost, "budget_failures": budget_failures}
    pairs = [(base, new) for base, new in (("A", "B"), ("A", "C"), ("B", "C")) if base in groups and new in groups]
    print(json.dumps({"blocks": blocks, "groups": groups, "comparisons": {f"{new} vs {base}": verdict(groups[base], groups[new]) for base, new in pairs}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

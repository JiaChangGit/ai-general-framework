#!/usr/bin/env python3
"""Spec 2.11: how much of a framework session's cost is the always-loaded part?

    measure_always_loaded.py RUN_DIR

RUN_DIR holds S8 experiment A event streams named <scenario>-<group>.jsonl
(artifacts/runs/s8-20261116/A). For each scenario, the difference between the
two groups' first-turn prompt (input + cache write + cache read tokens) is what
the framework adds before any work starts: the imported rules, the AGENTS.md
pointer and the listed skill descriptions. That prefix is written to the cache
once and read again on every later turn, so its share of the session is
estimated with the usual price ratios (cache write 1.25, cache read 0.1 and
output 5 times the input price). The ratios are an assumption; the CLI only
reports a total cost.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

WRITE, READ, OUTPUT = 1.25, 0.1, 5.0


def first_prompt_and_totals(path: Path) -> tuple[int, dict]:
    first, totals = None, {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant" and first is None:
            usage = event["message"]["usage"]
            first = usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
        if event.get("type") == "result":
            totals = dict(event.get("usage") or {}, turns=event.get("num_turns"), cost=event.get("total_cost_usd"))
    return first or 0, totals


def units(totals: dict) -> float:
    return (totals.get("input_tokens", 0) + WRITE * totals.get("cache_creation_input_tokens", 0)
            + READ * totals.get("cache_read_input_tokens", 0) + OUTPUT * totals.get("output_tokens", 0))


def main() -> int:
    runs = Path(sys.argv[1])
    rows = []
    for framework in sorted(runs.glob("*-framework.jsonl")):
        scenario = framework.name.removesuffix("-framework.jsonl")
        control = runs / f"{scenario}-control.jsonl"
        f_first, f_totals = first_prompt_and_totals(framework)
        c_first, _ = first_prompt_and_totals(control)
        added = f_first - c_first
        turns = f_totals.get("turns") or 1
        share = (WRITE * added + READ * added * (turns - 1)) / units(f_totals)
        rows.append({"scenario": scenario, "control_first_prompt": c_first, "framework_first_prompt": f_first,
                     "added_tokens": added, "framework_turns": turns, "framework_cost_usd": f_totals.get("cost"),
                     "estimated_share_of_session": round(share, 4)})
    shares = [row["estimated_share_of_session"] for row in rows]
    print(json.dumps({"rows": rows, "mean_share": round(sum(shares) / len(shares), 4), "max_share": max(shares)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

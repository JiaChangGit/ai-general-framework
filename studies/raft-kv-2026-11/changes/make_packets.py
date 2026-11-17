#!/usr/bin/env python3
"""Blind grading packet: S8's framework-group outputs against another run's.

    make_packets.py SCENARIOS_JSON [NAME RESULTS_JSON OUTPUTS_DIR SEED OUT_DIR]

SCENARIOS_JSON is the framework's evals/scenarios.json that both runs used.
Without the optional arguments the other run is spec 2.2's rerun
(results/trigger-results.json, results/outputs, seed 20261117, grading/).
Writes OUT_DIR/grader_input.md (instructions, tasks, criteria and two outputs
labelled X and Y) and OUT_DIR/packets.json (which run is X; not shown to the
grader). Same instructions and scale as S8 (../analysis/experiments/grader_prompt.md);
SEED decides the X/Y assignment.
"""
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
S8 = HERE.parent / "analysis" / "experiments"
ARGS = sys.argv[2:]
NAME = ARGS[0] if ARGS else "rerun"
RESULTS = Path(ARGS[1]) if ARGS else HERE / "results" / "trigger-results.json"
SEED = int(ARGS[3]) if ARGS else 20261117
OUT = Path(ARGS[4]) if ARGS else HERE / "grading"
RUNS = {"s8": S8 / "A-trigger" / "outputs", NAME: Path(ARGS[2]) if ARGS else HERE / "results" / "outputs"}


def main() -> int:
    tasks = {item["id"]: item for item in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["scenarios"]}
    order = [row["scenario"] for row in json.loads(RESULTS.read_text(encoding="utf-8"))["runs"]]
    text = (S8 / "grader_prompt.md").read_text(encoding="utf-8")
    parts, packets = [text[text.index("## 給評分者的指示"):], "\n---\n"], {}
    chooser = random.Random(SEED)
    for task_id in order:
        task = tasks[task_id]
        x_run = chooser.choice(tuple(RUNS))
        mapping = {"X": x_run, "Y": NAME if x_run == "s8" else "s8"}
        packets[task_id] = mapping
        parts.append(f"\n## 題目 {task_id}\n\n**請求**：{task['request']}\n")
        for name, content in (task.get("materials") or {}).items():
            parts.append(f"\n**材料 `{name}`**：\n\n```\n{content}\n```\n")
        parts.append("\n**observe**：\n" + "\n".join(f"- {item}" for item in task["observe"]) + "\n")
        parts.append("\n**avoid**：\n" + "\n".join(f"- {item}" for item in task.get("avoid", [])) + "\n")
        for label in ("X", "Y"):
            output = (RUNS[mapping[label]] / f"{task_id}-framework.md").read_text(encoding="utf-8").strip()
            parts.append(f"\n### 成果 {label}\n\n{output}\n")
    out = OUT
    out.mkdir(parents=True, exist_ok=True)
    (out / "grader_input.md").write_text("".join(parts), encoding="utf-8")
    (out / "packets.json").write_text(json.dumps({"seed": SEED, "packets": packets}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{out / 'grader_input.md'}: {len(order)} tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the blind grading packets for experiments A and C (grader_prompt.md).

    make_packets.py A|C

Writes <experiment>/grader_input.md (what the grader sees: tasks, criteria and
two outputs labelled X and Y) and <experiment>/packets.json (which group is X;
not shown to the grader). The assignment uses the seed 20261116.
"""
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
FRAMEWORK = Path("/home/user/src/ai-general-framework")
SEED = 20261116


def instructions() -> str:
    text = (HERE / "grader_prompt.md").read_text(encoding="utf-8")
    return text[text.index("## 給評分者的指示"):]


def main() -> int:
    experiment = sys.argv[1]
    chooser = random.Random(SEED)
    if experiment == "A":
        folder = HERE / "A-trigger"
        tasks = {s["id"]: s for s in json.loads((FRAMEWORK / "evals/scenarios.json").read_text())["scenarios"]}
        groups = ("control", "framework")
        names = [run["scenario"] for run in json.loads((folder / "results.json").read_text())["runs"]]
    else:
        folder = HERE / "C-guide"
        tasks = {c["id"]: c for c in json.loads((FRAMEWORK / "evals/writing-cases.json").read_text())["cases"]}
        groups = ("as-is", "entry-link")
        names = [run["case"] for run in json.loads((folder / "results.json").read_text())["runs"]]
    order = list(dict.fromkeys(names))
    packets, parts = {}, [instructions(), "\n---\n"]
    for task_id in order:
        task = tasks[task_id]
        x_group = chooser.choice(groups)
        mapping = {"X": x_group, "Y": groups[1] if x_group == groups[0] else groups[0]}
        packets[task_id] = mapping
        parts.append(f"\n## 題目 {task_id}\n\n**請求**：{task['request']}\n")
        if experiment == "A":
            for name, content in (task.get("materials") or {}).items():
                parts.append(f"\n**材料 `{name}`**：\n\n```\n{content}\n```\n")
            parts.append("\n**observe**：\n" + "\n".join(f"- {item}" for item in task["observe"]) + "\n")
            parts.append("\n**avoid**：\n" + "\n".join(f"- {item}" for item in task.get("avoid", [])) + "\n")
        else:
            parts.append("\n**事實**：\n" + "\n".join(f"- {item}" for item in task["facts"]) + "\n")
            parts.append(f"\n**草稿**：\n\n{task['draft']}\n")
            for key in ("preserve", "observe", "avoid"):
                parts.append(f"\n**{key}**：\n" + "\n".join(f"- {item}" for item in task.get(key, [])) + "\n")
        for label in ("X", "Y"):
            output = (folder / "outputs" / f"{task_id}-{mapping[label]}.md").read_text(encoding="utf-8").strip()
            parts.append(f"\n### 成果 {label}\n\n{output}\n")
    (folder / "grader_input.md").write_text("".join(parts), encoding="utf-8")
    (folder / "packets.json").write_text(json.dumps({"seed": SEED, "packets": packets}, ensure_ascii=False, indent=1) + "\n")
    print(f"{folder / 'grader_input.md'}: {len(order)} tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

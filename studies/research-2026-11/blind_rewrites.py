"""Rebuild each run's rewrite.md from the event streams and make blind grading material.

    python3 -I blind_rewrites.py OUT_DIR MEASUREMENT_DIR [MEASUREMENT_DIR ...] --seed N

The work directories are deleted after each run, so the text is rebuilt from the Write,
Edit and MultiEdit calls the subject (and, in the reviewed group, the reviewer) made on
rewrite.md, applied in order. Writes task.md, draft.md, text-NN.md and key.json (which
text came from which group and repeat; the grader is never shown key.json).
"""

import argparse
import json
from pathlib import Path
import random
import re

TASK = "rewrite-zh"
STREAM = re.compile(rf"^{TASK}-(?P<group>.+)-(?P<repeat>\d+)-(?P<part>\d+|review)\.jsonl$")


def rebuild(streams: list[Path]) -> str | None:
    text = None
    for stream in streams:
        for line in stream.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            content = (event.get("message") or {}).get("content") if event.get("type") == "assistant" else None
            for call in content if isinstance(content, list) else []:
                if not isinstance(call, dict) or call.get("type") != "tool_use":
                    continue
                given = call.get("input") or {}
                if not str(given.get("file_path", "")).endswith("rewrite.md"):
                    continue
                if call.get("name") == "Write":
                    text = given.get("content", "")
                elif call.get("name") in ("Edit", "MultiEdit") and text is not None:
                    for edit in given.get("edits") or [given]:
                        old, new = edit.get("old_string", ""), edit.get("new_string", "")
                        text = text.replace(old, new) if edit.get("replace_all") else text.replace(old, new, 1)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("measurements", type=Path, nargs="+")
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    runs = {}
    for measurement in args.measurements:
        label = measurement.name
        for stream in sorted((measurement / "streams").glob(f"{TASK}-*.jsonl")):
            match = STREAM.match(stream.name)
            if match:
                key = (label, match["group"], int(match["repeat"]))
                runs.setdefault(key, []).append((0 if match["part"] != "review" else 1, int(match["part"]) if match["part"].isdigit() else 99, stream))
    texts = []
    for key, parts in sorted(runs.items()):
        text = rebuild([stream for _, _, stream in sorted(parts)])
        if text:
            texts.append((key, text))
    random.Random(args.seed).shuffle(texts)
    args.out.mkdir(parents=True, exist_ok=True)
    key_map = {}
    for number, (key, text) in enumerate(texts, 1):
        name = f"text-{number:02d}.md"
        (args.out / name).write_text(text.rstrip() + "\n", encoding="utf-8")
        key_map[name] = {"measurement": key[0], "group": key[1], "repeat": key[2]}
    (args.out / "key.json").write_text(json.dumps(key_map, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"texts": len(texts), "runs_without_text": len(runs) - len(texts)}))


if __name__ == "__main__":
    main()

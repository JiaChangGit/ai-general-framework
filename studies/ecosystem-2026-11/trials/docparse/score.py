"""Score a parser's text or Markdown output against truth.json. Standard library only.

Usage: python3 score.py TRUTH_JSON OUTPUT_FILE [OUTPUT_FILE ...]
Prints one JSON object per output file.
"""

import html
import json
from pathlib import Path
import re
import sys


def normalize(text):
    text = html.unescape(text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|<>~])", r"\1", text)  # Markdown escapes
    text = re.sub(r"<[^>]+>", " ", text)                           # HTML tags in table output
    text = text.replace("−", "-")                             # Unicode minus
    text = re.sub(r"-\s+(?=[a-z])", "-", text)                     # words split after a hyphen
    return re.sub(r"\s+", " ", text)


def no_space(text):
    return re.sub(r"\s+", "", text)


def row_kept(row, lines):
    """All cells of the row appear in one line, in order."""
    for line in lines:
        position = 0
        for cell in row:
            found = line.find(cell, position)
            if found < 0:
                break
            position = found + len(cell)
        else:
            return True
    return False


def score(truth, raw):
    flat = normalize(raw)
    lines = [normalize(line) for line in raw.splitlines()]
    result = {}
    for key in ("en", "zh"):
        table = truth["tables"][key]
        cells = [c for row in table for c in row]
        result[f"{key}_cells"] = round(sum(c in flat for c in cells) / len(cells), 3)
        result[f"{key}_rows"] = round(sum(row_kept(r, lines) for r in table) / len(table), 3)
    positions = [flat.find(m) for m in truth["column_order"]]
    present = [p for p in positions if p >= 0]
    result["column_markers"] = f"{len(present)}/{len(positions)}"
    pairs = [(a, b) for i, a in enumerate(present) for b in present[i + 1:]]
    result["column_order_exact"] = len(present) == len(positions) and present == sorted(present)
    result["column_pairs"] = round(sum(a < b for a, b in pairs) / max(1, len(pairs)), 3)  # 1.0 = every pair in order
    result["column_text"] = round(sum(normalize(t) in flat for t in truth["column_text"]) / len(truth["column_text"]), 3)
    squeezed = no_space(flat)
    result["chinese"] = round(sum(no_space(t) in squeezed for t in truth["chinese"]) / len(truth["chinese"]), 3)
    han = lambda text: "".join(re.findall(r"[一-鿿]", text))  # characters only: punctuation and spacing ignored
    result["chinese_han"] = round(sum(han(t) in han(raw) for t in truth["chinese"]) / len(truth["chinese"]), 3)
    result["symbols"] = round(sum(s in flat for s in truth["symbols"]) / len(truth["symbols"]), 3)
    result["formula_text"] = truth["formula_text"] in flat
    result["formula_image_as_latex"] = bool(re.search(r"\\frac|\\sum|\\partial", raw))
    result["page_markers"] = len(re.findall(r"Page \d", flat))
    result["repeated_header"] = flat.count(truth["repeated_header"])
    result["characters"] = len(raw)
    return result


def main():
    truth = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for name in sys.argv[2:]:
        raw = Path(name).read_text(encoding="utf-8", errors="replace")
        print(json.dumps({"file": name, **score(truth, raw)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

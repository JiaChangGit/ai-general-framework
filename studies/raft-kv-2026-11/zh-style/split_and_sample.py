"""Corpus A split in two by file: even positions were used to find construction
errors in the rules, odd positions are measured. Draws the labeling sample
(framework-study/zh-style/SPEC.md §3.3). Usage: split_and_sample.py OUT.json"""
import glob, json, os, random, sys, importlib.util
from pathlib import Path
from dataclasses import asdict
root = Path(__file__).resolve().parents[2]
os.chdir(root)
spec = importlib.util.spec_from_file_location("h", root / "framework-study/zh-style/zh_style_hints.py")
h = importlib.util.module_from_spec(spec); sys.modules["h"] = h; spec.loader.exec_module(h)
files = sorted(set(glob.glob("docs/*.md") + glob.glob("docs/lessons/**/*.md", recursive=True) + ["docs/reference/raft-notes.md", "README.md", "AGENTS.md", "CLAUDE.md", "crates/raft-storage/testdata/README.md", ".claude/skills/write-bug-lesson/SKILL.md"]))
dev, test = files[0::2], files[1::2]
def hits_of(fs): return [x for f in fs for x in h.scan_text(Path(f).read_text(), f)]
dh, th = hits_of(dev), hits_of(test)
print("files dev", len(dev), "test", len(test))
for r in h.NAMES: print(r, "dev", sum(x.rule == r for x in dh), "test", sum(x.rule == r for x in th))
chooser = random.Random(20261116)
sample = []
for r in h.NAMES:
    of = [x for x in th if x.rule == r]
    sample += sorted(chooser.sample(of, min(20, len(of))), key=lambda x: (x.path, x.line))
for i, x in enumerate(sample, 1):
    d = asdict(x); d["id"] = i; sample[i-1] = d
Path(sys.argv[1]).write_text(json.dumps({"seed": 20261116, "per_rule": 20, "test_files": test, "dev_files": dev, "sample": sample}, ensure_ascii=False, indent=1))
print("sampled", len(sample))

"""Run each parser in its own container on the fixture PDFs; record time, peak memory and exit code.

Usage: python3 -I run.py WORK_DIR [tool ...]
WORK_DIR holds fixture/ (from make_fixture.py); outputs go to WORK_DIR/out/<tool>/ and
one JSON line per run is appended to WORK_DIR/out/results.jsonl.
Containers get no network (`--network none`): a tool that needs to download
something at run time fails, which is itself a finding about local use.
"""

import json
from pathlib import Path
import subprocess
import sys
import time

INPUTS = ["fixture.pdf", "fixture-scanned.pdf"]
# {in} is the input under /in, {stem} its name without .pdf, outputs go to /out.
TOOLS = {
    "pymupdf4llm": ("agf-parse-light:s16", "python -c \"import pymupdf4llm,sys; open(sys.argv[2],'w').write(pymupdf4llm.to_markdown(sys.argv[1]))\" /in/{in} /out/{stem}.md"),
    "markitdown": ("agf-parse-light:s16", "markitdown /in/{in} -o /out/{stem}.md"),
    # Models were prefetched into root's cache at build time, so these run as the image's root user.
    "docling": ("agf-parse-docling:s16", "HF_HUB_OFFLINE=1 docling /in/{in} --to md --to json --artifacts-path /root/.cache/docling/models --output /out", "root"),
    "docling-tesseract": ("agf-parse-docling:s16", "HF_HUB_OFFLINE=1 docling /in/{in} --to md --to json --artifacts-path /root/.cache/docling/models --ocr-engine tesseract --ocr-lang chi_tra,eng --output /out", "root"),
    "docling-formula": ("agf-parse-docling:s16", "HF_HUB_OFFLINE=1 docling /in/{in} --to md --to json --artifacts-path /root/.cache/docling/models --enrich-formula --output /out", "root"),
    "marker": ("agf-parse-marker:s16", "marker_single /in/{in} --output_dir /out --output_format markdown", "root"),
    "ocrmypdf": ("agf-parse-ocrmypdf:s16", "ocrmypdf -l chi_tra+eng --force-ocr /in/{in} /out/{stem}-ocr.pdf && pdftotext /out/{stem}-ocr.pdf /out/{stem}.txt"),
}


def run(work, tool, name):
    image, template, *user = TOOLS[tool]
    out = work / "out" / tool
    out.mkdir(parents=True, exist_ok=True)
    stem = name[:-4]
    command = template.format(**{"in": name, "stem": stem})
    wrapped = (f"{command}; code=$?; cat /sys/fs/cgroup/memory.peak > /out/.peak-{stem} 2>/dev/null; "
               f"cat /versions.txt > /out/.versions 2>/dev/null; chown -R 1000:1000 /out 2>/dev/null; exit $code")
    identity = [] if user else ["--user", "1000:1000", "-e", "HOME=/tmp"]
    started = time.monotonic()
    completed = subprocess.run(["docker", "run", "--rm", "--network", "none", "--memory", "7g", *identity,
                                "-v", f"{work / 'fixture'}:/in:ro", "-v", f"{out}:/out",
                                image, "sh", "-c", wrapped], capture_output=True, text=True, timeout=3600)
    seconds = round(time.monotonic() - started, 1)
    (out / f".log-{stem}").write_text(completed.stdout[-20000:] + "\n--- stderr ---\n" + completed.stderr[-20000:], encoding="utf-8")
    peak = out / f".peak-{stem}"
    peak_mb = round(int(peak.read_text().strip()) / 2**20) if peak.is_file() and peak.read_text().strip().isdigit() else None
    versions = (out / ".versions").read_text().strip() if (out / ".versions").is_file() else None
    record = {"tool": tool, "input": name, "exit": completed.returncode, "seconds": seconds, "peak_mb": peak_mb,
              "versions": versions, "command": command}
    with (work / "out" / "results.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def main():
    work = Path(sys.argv[1]).resolve()
    for tool in sys.argv[2:] or list(TOOLS):
        for name in INPUTS:
            print(json.dumps(run(work, tool, name), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

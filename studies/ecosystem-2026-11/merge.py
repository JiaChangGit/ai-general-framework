"""Merge the three subagent drafts into docs/ecosystem/entries.json.

Every change the main session made to the drafts is listed below (DROP, PREFER,
OVERRIDES), so the record shows what came from the subagents and what from the
review and the trials. Run from the framework root: python3 -I studies/ecosystem-2026-11/merge.py
"""

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
DRAFTS = ROOT / "studies" / "ecosystem-2026-11" / "drafts"
CATALOG = ROOT / "docs" / "ecosystem" / "entries.json"
CHECKED = "2026-11-21"
DOCPARSE = {"path": "studies/ecosystem-2026-11/trials/docparse/RESULTS.md", "level": "RECORD", "note": "S16 在 Docker 裡用答案已知的 PDF 試跑"}
CODEGRAPH = {"path": "studies/ecosystem-2026-11/trials/codegraph/RESULTS.md", "level": "RECORD", "note": "S16 在 Docker 裡用答案已知的 C 專案試跑"}

# Not a resource: the incident list moves to docs/ecosystem/security.md after the main session checked primary sources.
DROP = {"supply-chain-incidents-2025-2026"}
# Same project researched by two subagents: keep the deeper entry, add the other category to "also".
# U.json: entries rewritten or added after the user named the projects on 2026-11-22.
# S17.json: three seeds and expert guidance added in S17 (2026-11-22).
PREFER = {"codeql": "C", "fastctx-yc-duan": "U"}

OVERRIDES = {
    "pymupdf4llm": {"tier": 1, "evidence": "ran", "use": ["direct", "integrate"], "refs": [DOCPARSE],
                    "append": {"integration_value": "S16 試跑：文字型 PDF 每一項都對（表格、雙欄順序、中文、符號），1.3 秒、327 MB，是最快最省的。AGPL：框架只能當外部命令呼叫，不能 import。",
                               "weaknesses": "S16 試跑：沒有 OCR，掃描件輸出空檔但 exit code 是 0。"}},
    "docling": {"evidence": "ran", "refs": [DOCPARSE],
                "append": {"integration_value": "S16 試跑：文字型 PDF 全對；JSON 每段有頁碼與 bbox，適合要引用頁碼時用；`--enrich-formula` 能把圖片公式轉成 LaTeX。",
                           "weaknesses": "S16 試跑：斷網執行要另加 `--artifacts-path` 與 `HF_HUB_OFFLINE=1`；掃描件的預設 OCR 把一個繁體字辨識成簡體、雙欄順序交錯；公式轉換有一處看似合理的錯（n 變成 \\pi_{i}）；約 1.6～1.9 GB 記憶體。"}},
    "marker-datalab": {"tier": 2, "evidence": "ran", "refs": [DOCPARSE],
                       "append": {"weaknesses": "S16 試跑（2.2.0 預設模式）：文字型 PDF 一段順序錯；掃描件的符號被認錯（Σ 變 Z、α·β 變 aß）；第一次執行還會下載字型與 indra OCR 模型（約 110 MB），之後才能斷網。"}},
    "ocrmypdf": {"evidence": "ran", "refs": [DOCPARSE],
                 "append": {"integration_value": "S16 試跑：掃描件的中文字全部認對，原頁面影像與頁碼不變；全形標點會變半形。"}},
    "markitdown": {"evidence": "ran", "refs": [DOCPARSE],
                   "append": {"weaknesses": "S16 試跑：雙欄內文逐段交錯；掃描件輸出空檔但 exit code 是 0。"}},
    "poppler-utils": {"evidence": "ran", "refs": [DOCPARSE]},
    "tesseract": {"evidence": "ran", "refs": [DOCPARSE]},
    "universal-ctags": {"evidence": "ran", "refs": [CODEGRAPH],
                        "append": {"weaknesses": "S16 試跑：找不到巨集產生的函式；`#ifdef` 兩個分支的定義都列出。"}},
    "cscope": {"evidence": "ran", "refs": [CODEGRAPH],
               "append": {"weaknesses": "S16 試跑：呼叫者回報成巨集名稱而不是巨集產生的函式；`#ifdef` 兩個分支的呼叫都列出；函式指標只回成員名稱。"}},
    "gnu-global": {"evidence": "ran", "refs": [CODEGRAPH],
                   "append": {"weaknesses": "S16 試跑：找不到巨集產生的函式定義。"}},
    "gnu-cflow": {"tier": 2, "evidence": "ran", "refs": [CODEGRAPH],
                  "append": {"integration_value": "S16 試跑：加 `--cpp` 跑前置處理器後，巨集產生的函式、`#ifdef` 選中的分支都正確，還附定義的檔案與行號；只用標準工具就能得到 C 的直接呼叫樹。",
                             "weaknesses": "S16 試跑：把當成參數傳出去的函式（callback 註冊）畫成被呼叫；解不出 ops table。"}},
    "codegraph-colbymchenry": {"evidence": "ran", "refs": [CODEGRAPH],
                               "append": {"integration_value": "S16 試跑（1.6.4，斷網、關 telemetry）：唯一解出 ops table 函式指標的工具（dev->ops->open 對到 uart_open、spi_open），137 MB、0.3 秒建圖。",
                                          "weaknesses": "S16 試跑：巨集產生的函式找不到；沒啟用的 #ifdef 分支也算進去；callback 註冊只記成引用。"}},
    "codebase-memory-mcp-deusdata": {"evidence": "ran", "refs": [CODEGRAPH],
                                     "append": {"weaknesses": "S16 試跑（0.12.1，CLI 模式，斷網）：函式指標與 callback 只解到結構欄位；#ifdef 兩個分支都算；把巨集 DEFINE_HANDLER 記成函式，緊接其後的 static 函式 heartbeat 整個不在圖裡；資料夾裡的 JSON 也會被收進索引；拒絕索引根目錄下一層的路徑。"}},
    # After `refresh`: fill or correct licenses where GitHub's detection disagreed with the draft.
    "pdf-inspector": {"license": {"spdx": "MIT", "basis": "GitHub 偵測（2026-11-21），未讀 LICENSE 原文", "label": "usable"}},
    "xmldiff": {"license": {"spdx": "MIT", "basis": "GitHub 偵測（2026-11-21），未讀 LICENSE 原文", "label": "usable"}},
    "routellm": {"append": {"weaknesses": "GitHub 上最後一次 push 是 2024-08-10。"}},
}


def main():
    entries, origin = {}, {}
    for name in ("W", "C", "M", "U", "S17"):
        for entry in json.loads((DRAFTS / f"{name}.json").read_text(encoding="utf-8")):
            if entry["id"] in DROP:
                continue
            entry.setdefault("checked", CHECKED)
            for reference in entry.get("references", []):
                url = str(reference.get("url", ""))
                local = re.match(r"^/.*?/ai-general-framework[^/]*/(.+)$", url)  # any checkout of this framework
                if local:
                    reference.pop("url")
                    reference["path"] = local.group(1)
                    reference["level"] = "RECORD"
            key = entry["id"]
            if key in entries:
                keep, other = (entry, entries[key]) if PREFER.get(key) == name else (entries[key], entry)
                if other["category"] != keep["category"]:
                    keep.setdefault("also", []).append(other["category"])
                keep["references"] += [r for r in other["references"] if r not in keep["references"]]
                entries[key] = keep
                print(f"merged duplicate {key}: kept {PREFER.get(key, origin[key])}")
                continue
            entries[key], origin[key] = entry, name
    for key, change in OVERRIDES.items():
        if key not in entries:
            sys.exit(f"override for unknown id {key}")
        entry = entries[key]
        for field in ("tier", "evidence", "use"):
            if field in change:
                entry[field] = change[field]
        entry["license"].update(change.get("license", {}))
        for field, text in change.get("append", {}).items():
            entry[field] = (entry.get(field) or "").rstrip() + ("" if not entry.get(field) else " ") + text
        entry["references"] += change.get("refs", [])
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    ids = set(entries)
    for entry in entries.values():
        missing = [a for a in entry.get("alternatives", []) if a not in ids]
        if missing:
            entry["alternatives"] = [a for a in entry["alternatives"] if a in ids]
            print(f"{entry['id']}: dropped unknown alternatives {missing}")
        entry["also"] = sorted({c for c in entry.get("also", []) if c in data["categories"] and c != entry["category"]})
        if not entry["also"]:
            entry.pop("also")
    previous = {e["id"]: e for e in data["entries"]}
    for key, entry in entries.items():  # keep facts already fetched by `refresh`
        if "github" in previous.get(key, {}):
            entry["github"] = previous[key]["github"]
    data["entries"] = sorted(entries.values(), key=lambda e: (e["category"], e["id"]))
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(data['entries'])} entries")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Point at Chinese sentences that may read as AI-written. Hints, not verdicts.

framework-study/zh-style/SPEC.md §3.2. A hit is a candidate for a person or a
model to read; it never says the text is bad, and no rule here is a quality
gate (the framework's docs/writing.md: no ban lists, no fixed sentence length,
no AI-detector scores). Two rules use word lists on purpose, to measure how
often such lists are right. Standard library only.

    zh_style_hints.py [--json | --summary] [--sample N --seed S] PATH ...

PATH is a Markdown file or a directory searched for *.md.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
import re
import sys

CJK = "㐀-䶿一-鿿"
NAMES = {"R1": "空泛詞", "R2": "長句", "R3": "歐化句式", "R4": "人稱跳躍", "R5": "名詞化", "R6": "死物配活物動作", "R7": "長定語"}

# R1: phrases that sound fluent and say little, counted only in a sentence with
# nothing concrete in it (a digit, code, a link or a Latin-script name).
EMPTY = ["賦能", "全面提升", "大幅提升", "顯著提升", "有效提升", "全面優化", "無縫", "至關重要", "不可或缺", "打造", "助力",
         "一站式", "全方位", "多維度", "深度融合", "閉環", "抓手", "生態系", "極致", "強大的", "高效的", "優雅的", "最佳實踐",
         "核心價值", "深入淺出", "值得一提的是", "總而言之", "綜上所述", "不僅如此", "與此同時", "在當今", "日新月異", "扮演著",
         "發揮著", "舉足輕重", "奠定了", "堅實基礎", "具有重要意義", "起到了", "關鍵作用", "旨在", "致力於", "賦予", "引領"]
CONCRETE = re.compile(r"[0-9０-９]|〈code〉|〈url〉|[A-Za-z]{2,}")
# R3: sentence patterns borrowed from English, and a condition put after the main clause.
EUROPEANIZED = [re.compile(p) for p in (r"當[^，。；]{1,30}的時候", r"作為一[個名位種]", r"對於[^，。；]{1,30}(?:而言|來說)",
                                         r"被[^，。；]{1,20}所(?![以有])", r"在[^，。；]{1,30}的情況下", r"使得")]
TRAILING = re.compile(r"^(?:如果|假如|除非|雖然|儘管|即使)")
TRAILING_MAIN = re.compile(r"也|就|則|仍|還是")
# R4: who the text talks to or about; quoted words are someone else's.
PERSONS = {"我們": r"我們", "我": r"(?<!自)我(?!們)", "你們": r"你們", "你": r"你(?!們)", "您": r"您", "讀者": r"讀者", "使用者": r"使用者"}
QUOTED = re.compile(r"「[^」]*」|『[^』]*』|“[^”]*”")
# R5: a light verb carrying the real verb as a noun, classical 之, stacked 的.
LIGHT_VERB = re.compile(rf"(?:進行(?!中|到)|加以|予以|做出|作出)了?[{CJK}]{{2}}")
CLASSICAL = re.compile(rf"[{CJK}]之(?!前|後|間|一|外|內|中|下|上|所以|類|際|處)[{CJK}]{{2}}")
NOT_DE = re.compile(r"目的|的確|的話|真的|端的")
STACKED_DE = 3  # 的 inside one phrase, between two punctuation marks; a list of parallel items is not stacking
PHRASE_BREAK = re.compile(r"[，。、；：！？「」『』（）()〈〉《》…—“”]")
# R6: a thing doing what only a person does.
THINGS = "文件|報告|測試|程式碼|程式|工具|系統|腳本|資料|結果|數據|紀錄|規則|契約|檢查器|模擬器|框架|設計|架構|訊息|函式|規格|教學|輸出|日誌|錯誤"
SOFTENERS = "自己|也|就|都|會|不|沒有|沒|還|卻|才|已經|永遠|一直|根本|並|仍|照樣"
MINDS = "告訴|認為|希望|決定|知道|想要|擔心|試圖|努力|堅持|相信|意識到|承認|抱怨|喜歡|害怕|誤以為|記得|忘記|看得出|看不出|看到|發現|守著|守住|抓到|抓得到|抓不到|假裝"
ANIMATE = re.compile(rf"(?:{THINGS})(?:{SOFTENERS}){{0,2}}(?:{MINDS})")
IDIOM = re.compile(r"結果發現")  # 結果 as a conjunction: "and then (I) found"
# R7: the text between a boundary and a 的 (an attributive), when it is long.
# A 的 that ends a clause (是……的) modifies no noun and is skipped.
BOUNDARY = "，。、；：！？「」『』（）()〈〉《》…—“”"
LONG_MODIFIER = 20
LONG_SENTENCE, MANY_COMMAS = 60, 3


@dataclass
class Hit:
    rule: str
    name: str
    path: str
    line: int
    match: str
    sentence: str


@dataclass
class Block:
    """Text outside code that reads as one unit: a paragraph, a list item, a
    heading or a table cell. `starts` maps an offset in `text` to its line."""
    text: str
    starts: list[tuple[int, int]]

    def line_at(self, offset: int) -> int:
        line = self.starts[0][1]
        for start, number in self.starts:
            if start > offset:
                break
            line = number
        return line


def mask(line: str) -> str:
    line = re.sub(r"`[^`]*`", "〈code〉", line)
    line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)
    return re.sub(r"https?://\S+", "〈url〉", line)


def cjk_count(text: str) -> int:
    return len(re.findall(f"[{CJK}]", text))


def blocks(text: str) -> list[Block]:
    out: list[Block] = []
    current: Block | None = None
    fenced = False

    def close():
        nonlocal current
        if current and current.text.strip():
            out.append(current)
        current = None

    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith(("```", "~~~")):
            close()
            fenced = not fenced
            continue
        if fenced or stripped.startswith("<!--"):
            continue
        if not stripped:
            close()
            continue
        if stripped.startswith("|"):
            close()
            if re.fullmatch(r"\|?[\s:|-]+\|?", stripped):
                continue  # the separator row under a table header
            for cell in stripped.strip("|").split("|"):
                if cell.strip():
                    out.append(Block(mask(cell.strip()), [(0, number)]))
            continue
        body = re.sub(r"^>\s?", "", stripped)
        new_unit = re.match(r"(#{1,6}\s|[-*+]\s|\d+\.\s)", body)
        if new_unit:
            close()
        body = mask(body)
        if current is None or new_unit:
            current = Block(body, [(0, number)])
            if body.startswith("#"):
                close()
            continue
        glue = "" if re.match(f"[{CJK}，。、；：！？「」）]", body) and re.search(f"[{CJK}，。、；：！？「」（]$", current.text) else " "
        current.starts.append((len(current.text) + len(glue), number))
        current.text += glue + body
    close()
    return out


def sentences(block: Block) -> list[tuple[int, str]]:
    """(offset in the block, sentence) for each sentence, its end mark kept."""
    out, start = [], 0
    for end in re.finditer(r"[。！？；!?]", block.text):
        out.append((start, block.text[start:end.end()]))
        start = end.end()
    if block.text[start:].strip():
        out.append((start, block.text[start:]))
    return [(offset + len(s) - len(s.lstrip()), s.strip()) for offset, s in out if s.strip()]


def check_sentence(sentence: str) -> list[tuple[str, int, str]]:
    """(rule, offset of the match in the sentence, matched text)."""
    found = []
    if not CONCRETE.search(sentence):
        for phrase in EMPTY:
            at = sentence.find(phrase)
            if at >= 0:
                found.append(("R1", at, phrase))
                break
    if cjk_count(sentence) > LONG_SENTENCE and sentence.count("，") >= MANY_COMMAS:
        found.append(("R2", 0, f"{cjk_count(sentence)} 字、{sentence.count('，')} 個逗號"))
    for pattern in EUROPEANIZED:
        match = pattern.search(sentence)
        if match:
            found.append(("R3", match.start(), match.group()))
            break
    else:
        clauses = sentence.split("，")
        last = clauses[-1]
        if len(clauses) > 1 and TRAILING.match(last) and not TRAILING_MAIN.search(last):
            found.append(("R3", len(sentence) - len(last), last))
    match = LIGHT_VERB.search(sentence) or CLASSICAL.search(sentence)
    if match:
        found.append(("R5", match.start(), match.group()))
    else:
        start = 0
        for phrase in PHRASE_BREAK.split(sentence):
            if phrase.count("的") - len(NOT_DE.findall(phrase)) >= STACKED_DE:
                found.append(("R5", sentence.find(phrase, start), phrase.strip()))
                break
            start += len(phrase) + 1
    match = next((m for m in ANIMATE.finditer(sentence) if not IDIOM.match(sentence, m.start())), None)
    if match:
        found.append(("R6", match.start(), match.group()))
    longest = None
    for de in re.finditer("的", sentence):
        if NOT_DE.match(sentence, max(de.start() - 1, 0)) or NOT_DE.match(sentence, de.start()):
            continue
        if de.end() == len(sentence) or sentence[de.end()] in BOUNDARY + "；。":
            continue
        start = max(sentence.rfind(mark, 0, de.start()) for mark in BOUNDARY) + 1
        span = sentence[start:de.end()]
        if cjk_count(span) - 1 > LONG_MODIFIER and (longest is None or cjk_count(span) > cjk_count(longest[1])):
            longest = (start, span)
    if longest:
        found.append(("R7", longest[0], longest[1]))
    return found


def check_block(block: Block) -> str | None:
    """R4: the persons one block refers to, if they shift."""
    text = QUOTED.sub("", block.text)
    seen = {name for name, pattern in PERSONS.items() if re.search(pattern, text)}
    if len(seen) >= 3 or {"我", "我們"} <= seen or {"你", "您"} <= seen or {"你", "讀者"} <= seen:
        return "、".join(sorted(seen))
    return None


def scan_text(text: str, path: str) -> list[Hit]:
    hits = []
    for block in blocks(text):
        persons = check_block(block)
        if persons:
            hits.append(Hit("R4", NAMES["R4"], path, block.line_at(0), persons, block.text[:200]))
        for offset, sentence in sentences(block):
            for rule, at, match in check_sentence(sentence):
                hits.append(Hit(rule, NAMES[rule], path, block.line_at(offset + at), match, sentence))
    return hits


def markdown_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for name in paths:
        path = Path(name)
        files.extend(sorted(path.rglob("*.md")) if path.is_dir() else [path])
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+")
    shape = parser.add_mutually_exclusive_group()
    shape.add_argument("--json", action="store_true", help="every hit as JSON")
    shape.add_argument("--summary", action="store_true", help="hits per rule and per 10,000 Chinese characters")
    parser.add_argument("--sample", type=int, help="at most N hits per rule, chosen at random")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    files = markdown_files(args.paths)
    hits, characters = [], 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        characters += sum(cjk_count(block.text) for block in blocks(text))
        hits.extend(scan_text(text, path.as_posix()))
    if args.sample:
        chooser = random.Random(args.seed)
        chosen = []
        for rule in NAMES:
            of_rule = [hit for hit in hits if hit.rule == rule]
            chosen.extend(sorted(chooser.sample(of_rule, min(args.sample, len(of_rule))), key=lambda h: (h.path, h.line)))
        hits = chosen
    if args.json:
        json.dump([asdict(hit) for hit in hits], sys.stdout, ensure_ascii=False, indent=1)
        print()
    elif args.summary:
        print(f"files {len(files)}, Chinese characters outside code {characters}")
        for rule, name in NAMES.items():
            count = sum(hit.rule == rule for hit in hits)
            print(f"{rule} {name}: {count} hits, {count * 10000 / max(characters, 1):.1f} per 10,000 characters")
    else:
        for hit in hits:
            print(f"{hit.path}:{hit.line}: {hit.rule} {hit.name}: 「{hit.match}」")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

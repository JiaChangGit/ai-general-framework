"""Build a PDF whose content is known, plus a scanned copy, for comparing parsers.

Runs inside a container with reportlab, matplotlib, Pillow, poppler-utils and
fonts-wqy-zenhei (see README.md). Writes fixture.pdf, fixture-scanned.pdf and
truth.json into the directory given as the first argument.
"""

import json
from pathlib import Path
import subprocess
import sys

from matplotlib import mathtext
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, FrameBreak, Image as Picture, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

OUT = Path(sys.argv[1])
pdfmetrics.registerFont(TTFont("CJK", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", subfontIndex=0))
BODY = ParagraphStyle("body", fontName="CJK", fontSize=10, leading=14)
TITLE = ParagraphStyle("title", fontName="CJK", fontSize=16, leading=20)

TABLE_EN = [["Config", "p50 (ms)", "p99 (ms)", "Throughput (req/s)", "Δ p99 (%)"],
            ["baseline", "12.40", "48.9", "8,150", "0.0"],
            ["cache-on", "7.85", "31.2", "12,904", "-36.2"],
            ["batch-64", "21.07", "95.5", "30,511", "+95.3"],
            ["numa-pin", "11.98", "40.7", "8,377", "-16.8"],
            ["io_uring", "9.61", "29.4", "14,020", "-39.9"]]
TABLE_ZH = [["模組", "負責人", "狀態", "截止日"],
            ["排程器", "林小明", "進行中", "2026-12-01"],
            ["記憶體配置", "陳大華", "已完成", "2026-10-15"],
            ["中斷處理", "王美玲", "待審查", "2026-11-30"]]
COLUMNS = [f"[P0{i}] " + text for i, text in enumerate([
    "The scheduler wakes the worker only after the queue lock is released, so a waiter never spins on a held lock.",
    "Each request carries a monotonically increasing ticket; the dispatcher rejects tickets older than the last commit.",
    "When the ring buffer is full, producers back off for a bounded interval instead of overwriting unread slots.",
    "A watchdog samples the heartbeat every 250 milliseconds and marks the node suspect after four misses.",
    "The right column begins here: recovery replays the journal from the last checkpoint before accepting writes.",
    "Snapshots are taken from a copy-on-write view, which keeps readers from blocking the compaction thread.",
    "If two replicas disagree on the epoch, the one with the lower epoch steps down and resynchronizes.",
    "Metrics are exported per shard so that a single slow disk shows up as one outlier rather than a global average.",
], start=1)]
CHINESE = [
    "[Z1] 排程器只在佇列的鎖釋放之後才喚醒工作執行緒，等待者因此不會在被占用的鎖上空轉。",
    "[Z2] 每個請求都帶著遞增的序號；分派器拒絕比最後一次提交還舊的序號，避免重送的請求被執行兩次。",
    "[Z3] 環狀緩衝區滿了的時候，生產者會等待一段有上限的時間，而不是覆寫還沒被讀走的位置。",
]
FORMULA_TEXT = "Σ x² ≤ α·β ± 0.5 µs"  # every glyph exists in the embedded font
FORMULA_TEX = r"$\frac{\partial L}{\partial w} = \sum_{i=1}^{n} (y_i - \hat{y}_i)\,x_i$"


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("CJK", 8)
    canvas.drawString(50, A4[1] - 30, "Synthetic Parser Benchmark v1")
    canvas.drawRightString(A4[0] - 50, 25, f"第 {doc.page} 頁 / Page {doc.page}")
    canvas.restoreState()


def table(rows):
    result = Table(rows, hAlign="LEFT")
    result.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "CJK"), ("FONTSIZE", (0, 0), (-1, -1), 9),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mathtext.math_to_image(FORMULA_TEX, str(OUT / "formula.png"), dpi=200)
    pixels_wide, pixels_high = Image.open(OUT / "formula.png").size
    doc = BaseDocTemplate(str(OUT / "fixture.pdf"), pagesize=A4, title="Synthetic Parser Benchmark", author="agf")
    width, height = A4
    full = Frame(50, 50, width - 100, height - 100, id="full")
    left = Frame(50, 50, (width - 110) / 2, height - 100, id="left")
    right = Frame(60 + (width - 110) / 2, 50, (width - 110) / 2, height - 100, id="right")
    doc.addPageTemplates([PageTemplate("one", [full], onPage=header_footer),
                          PageTemplate("two", [left, right], onPage=header_footer)])
    story = [Paragraph("Synthetic Parser Benchmark", TITLE), Spacer(1, 8),
             Paragraph("Table 1. Latency and throughput of five configurations.", BODY), Spacer(1, 4),
             table(TABLE_EN), Spacer(1, 12),
             Paragraph("Inline formula as text: " + FORMULA_TEXT, BODY), Spacer(1, 8),
             Paragraph("Formula rendered as an image:", BODY), Picture(str(OUT / "formula.png"), width=200, height=200 * pixels_high / pixels_wide),
             NextPageTemplate("two"), PageBreak()]
    for index, paragraph in enumerate(COLUMNS):
        story += [Paragraph(paragraph, BODY), Spacer(1, 10)]
        if index == 3:
            story.append(FrameBreak())
    story += [NextPageTemplate("one"), PageBreak(), Paragraph("表 2：模組進度", BODY), Spacer(1, 4), table(TABLE_ZH), Spacer(1, 12)]
    story += [x for text in CHINESE for x in (Paragraph(text, BODY), Spacer(1, 8))]
    doc.build(story)
    subprocess.run(["pdftoppm", "-r", "150", "-gray", "-png", str(OUT / "fixture.pdf"), str(OUT / "page")], check=True)
    pages = [Image.open(p).convert("L") for p in sorted(OUT.glob("page-*.png"))]
    pages[0].save(OUT / "fixture-scanned.pdf", save_all=True, append_images=pages[1:], resolution=150)
    truth = {"tables": {"en": TABLE_EN, "zh": TABLE_ZH}, "column_order": [f"[P0{i}]" for i in range(1, 9)],
             "column_text": COLUMNS, "chinese": CHINESE, "formula_text": FORMULA_TEXT,
             "symbols": ["Σ", "≤", "α", "β", "±", "µ", "Δ"], "formula_image_tex": FORMULA_TEX,
             "pages": {"1": ["Table 1", "[P0"], "2": ["[P01]", "[P08]"], "3": ["[Z1]", "[Z3]"]},
             "repeated_header": "Synthetic Parser Benchmark v1"}
    (OUT / "truth.json").write_text(json.dumps(truth, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

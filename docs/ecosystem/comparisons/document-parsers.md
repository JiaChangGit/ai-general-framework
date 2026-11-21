# 文件解析比較

查核日期：2026-11-21。原始筆記在 [M-data-media.md](../../../studies/ecosystem-2026-11/M-data-media.md)，試跑結果在 [docparse/RESULTS.md](../../../studies/ecosystem-2026-11/trials/docparse/RESULTS.md)。

## 沒有中立的排名

各家公布的準確度都是自己量的：Marker 用自家的 OmniParseBench，MinerU 的高分來自同一個組織維護的 OmniDocBench，Docling 的技術報告比的是速度。沒有找到同條件、第三方的比較，所以這次自己做了一份答案已知的測試 PDF（表格、雙欄、繁體中文、符號、圖片公式、頁碼），再做一份轉成圖片的模擬掃描件。

## 試跑結果摘要

| 工具 | 文字型 PDF | 掃描件 | 頁碼與座標 | 記憶體 | 授權 |
|---|---|---|---|---|---|
| pymupdf4llm 2.1 | **全對**，1.3 秒 | 沒有 OCR，**輸出空檔、exit 0** | Markdown 留頁尾；`page_chunks` 分頁 | 327 MB | AGPL-3.0 |
| Docling 2.151 | **全對**，13 秒 | 大致認得，雙欄交錯、一個繁體字變簡體 | **JSON 每段有頁碼與 bbox** | 1.6～1.9 GB | MIT |
| Marker 2.2（預設模式） | 一段順序錯 | 符號認錯（Σ 變 Z） | Markdown 去掉 | 約 800 MB | 程式 Apache-2.0；權重有營收門檻 |
| markitdown 0.1.9 | 雙欄逐段交錯 | **輸出空檔、exit 0** | 留頁尾 | 68 MB | MIT |
| OCRmyPDF 17.14＋Tesseract 5.5 | （用於掃描件） | 中文字全對，標點變半形 | **原頁面與頁碼不變** | 約 300～700 MB | MPL-2.0 |
| pdftotext（poppler） | 內容都在，雙欄交錯 | 沒有文字層 | 留頁尾 | 很小 | GPL-2.0-or-later |

圖片裡的公式只有 Docling 加 `--enrich-formula` 會轉成 LaTeX，而且有一處看起來合理的錯（上限 `n` 變成 `\pi_{i}`）。

## 沒有試跑的

- **MinerU**：README 的 standard 方案要 8 GB 記憶體，剛好是 WSL 的上限；遙測預設開（`MINERU_TELEMETRY_DISABLED=1` 關閉）；README 裡還有一段寫給 AI agent 的指令，要它全域安裝第三方 skill（研究時沒有照做，記為資安發現）。授權是 Apache-2.0 加營收門檻的附加條款。
- **GROBID**：學術論文專用，輸出 TEI XML（作者、章節、參考文獻）；需要 Java 服務。
- **olmOCR、Nougat**：視覺語言模型，需要 GPU。
- **anydoc**（firecrawl/anydoc，Rust）：本機不做 OCR，掃描頁要加 `--ocr hosted` 送到 Firecrawl 的雲端服務。

## 真正不同的方向

1. **讀 PDF 的文字層**（pdftotext、PyMuPDF、markitdown、anydoc）：快、輕，文字型 PDF 夠用；差別在版面分析（雙欄、表格）做得好不好。
2. **版面模型＋OCR 管線**（Docling、MinerU、Marker、PaddleOCR）：能處理掃描件與複雜版面，要下載模型、吃記憶體。
3. **只加文字層、不轉格式**（OCRmyPDF）：原檔不動，頁碼不變，之後可以接第一類工具。
4. **視覺語言模型逐頁重寫**（olmOCR、Nougat、Marker balanced）：公式與手寫較好，需要 GPU。

## 建議

使用者希望重要文件保留原始 PDF，再搭配結構化內容與頁碼。照試跑結果：

1. 原始 PDF 不動；先看有沒有文字層。
2. 文字型：一般閱讀用 pymupdf4llm（框架只能當外部命令呼叫，AGPL 不能 import）；要引用頁碼、座標或圖片公式時用 Docling 的 JSON。
3. 掃描件：先用 OCRmyPDF（`-l chi_tra+eng`）加文字層，再走文字型的流程；或直接用 Docling。
4. 每次都檢查輸出長度，不只看 exit code；表格數字、公式、繁簡字對照原頁面抽查。

這是路線圖 S20 的內容。還要用真實論文（合併儲存格、跨頁表格、腳註）再驗一次。

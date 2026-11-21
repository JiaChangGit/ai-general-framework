# 文件解析、OCR 與 PDF

<!-- ecosystem:table document-processing -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Docling（IBM／LF AI & Data）](https://github.com/docling-project/docling) | 函式庫 | 1 | 可使用（MIT） | 2026-11-21 | 實際執行 | 多格式文件解析：PDF（版面、閱讀順序、表格結構、程式碼、公式、圖片分類）、DOCX、PPTX、XLSX、HTML、EPUB、影像、音訊等，輸出統一的 DoclingDocument，可匯出 Markdown、HTML、無損 JSON、DocTags。 |
| [MinerU（OpenDataLab）](https://github.com/opendatalab/MinerU) | 函式庫 | 1 | 有條件（Apache-2.0 加附加條款（MinerU Open Source License）） | 2026-11-20 | 讀原始碼 | 4.x 版是完整的文件解析平台：PDF、影像、Office、EPUB、OFD、HTML 等輸入，輸出 Markdown、HTML、LaTeX、DOCX、EPUB、PDF、結構化內容；有 CLI、SDK、API、WebUI、doclib（文件庫、搜尋與穩定引用定位）、agent skill。 |
| [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | CLI | 1 | 可使用（MPL-2.0） | 2026-11-16 | 實際執行 | 替掃描 PDF 加上可搜尋的 OCR 文字層，輸出仍是 PDF（可 PDF/A），保留原頁面影像。 |
| [pymupdf4llm](https://github.com/pymupdf/pymupdf4llm) | 函式庫 | 1 | 有條件（AGPL-3.0） | 2026-11-19 | 實際執行 | 以 PyMuPDF 為基礎，把 PDF 轉成對 LLM 友善的 Markdown（含標題、表格、頁面分段 page_chunks）。 |
| [anydoc（Firecrawl 的 Rust 文件轉 Markdown）](https://github.com/firecrawl/anydoc) | 函式庫 | 2 | 可使用（MIT） | 2026-11-18 | 讀文件 | Rust 寫的 Word、PowerPoint、Excel、OpenDocument、RTF、EPUB、CSV、PDF 轉 GFM Markdown，附 Node 與 Python 綁定與 CLI，也打包成 Agent Skill。 |
| [GROBID](https://github.com/kermitt2/grobid) | 服務 | 2 | 可使用（Apache-2.0） | 2026-11-21 | 讀文件 | 學術論文專用：把 PDF 轉成 TEI XML，抽出標題、作者、摘要、章節、參考文獻（可用 CrossRef 校正）、圖表。 |
| [Marker（Datalab）](https://github.com/datalab-to/marker) | 函式庫 | 2 | 有條件（Apache-2.0（程式碼）；模型權重 AI Pubs OpenRAIL-M 修改版） | 2026-11-20 | 實際執行 | PDF、影像、Office 檔轉 Markdown／JSON／HTML／chunks；新版有四種模式（no_ocr、fast、balanced、vllm），可選 --use_llm 提升表格、行內公式與表單。 |
| [MarkItDown（Microsoft）](https://github.com/microsoft/markitdown) | 函式庫 | 2 | 可使用（MIT） | 2026-11-07 | 實際執行 | 把 PDF、Word、PowerPoint、Excel、HTML、圖片、音訊等轉成 Markdown 的 Python 工具，附 MCP server。 |
| [PaddleOCR（PP-OCR、PP-StructureV3、PaddleOCR-VL）](https://github.com/PaddlePaddle/PaddleOCR) | 函式庫 | 2 | 可使用（Apache-2.0） | 2026-09-16 | 讀文件 | 百度的 OCR 工具包：輕量文字偵測辨識（PP-OCRv6）、版面與表格結構（PP-StructureV3 輸出 Markdown／JSON 含座標）、0.9B 文件 VLM（PaddleOCR-VL）。 |
| [Pandoc](https://github.com/jgm/pandoc) | CLI | 2 | 可使用（GPL-2.0-or-later） | 2026-11-20 | 只有搜尋摘要 | 通用文件轉換器：Markdown、HTML、DOCX、PPTX（輸出）、EPUB、LaTeX、reStructuredText 等數十種格式互轉，可用 Lua filter 擴充。 |
| [Poppler（pdftotext、pdftoppm、pdfimages、pdfinfo）](https://poppler.freedesktop.org/) | CLI | 2 | 可使用（GPL-2.0-or-later／GPL-3.0-or-later） | — | 實際執行 | PDF 渲染函式庫與命令列工具：抽文字（-layout、-bbox-layout 含座標）、轉頁面為圖、抽內嵌圖片、查中繼資料。 |
| [RapidOCR](https://github.com/RapidAI/RapidOCR) | 函式庫 | 2 | 可使用（Apache-2.0） | 2026-11-21 | 讀文件 | 把 PaddleOCR 等模型轉成 ONNX／OpenVINO／MNN 等執行格式的 OCR，pip 安裝即可在 CPU 跑，不依賴 PaddlePaddle。 |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | CLI | 2 | 可使用（Apache-2.0） | 2026-11-20 | 實際執行 | 傳統 LSTM OCR 引擎，單頁影像轉文字或 hOCR／TSV（含座標與信心值），支援 100 多種語言。 |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | CLI | 2 | 可使用（MIT） | 2026-11-20 | 讀文件 | OpenAI Whisper 的 C／C++ 實作，CPU 即可跑，有量化模型；輸出文字、SRT、VTT、帶時間戳。 |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 函式庫 | 3 | 可使用（MIT） | 2026-11-12 | 只有搜尋摘要 | 用 CTranslate2 重新實作的 Whisper，GPU／CPU 都比原版快，支援 int8 量化。 |
| [olmOCR（Allen AI）](https://github.com/allenai/olmocr) | 函式庫 | 3 | 可使用（Apache-2.0） | 2026-03-25 | 讀文件 | 以 7B 視覺語言模型逐頁把 PDF 轉成乾淨文字，處理公式、表格、手寫與老舊掃描；附 olmOCR-bench 評測與 Docker。 |
| [pdf-inspector（Firecrawl）](https://github.com/firecrawl/pdf-inspector) | 函式庫 | 3 | 可使用（MIT） | 2026-11-21 | 只有搜尋摘要 | Rust 函式庫：偵測 PDF 是文字型還是掃描型並抽取文字，供路由決策。 |
| [PyMuPDF（fitz）](https://github.com/pymupdf/PyMuPDF) | 函式庫 | 3 | 有條件（AGPL-3.0） | 2026-11-21 | 只有搜尋摘要 | MuPDF 的 Python 綁定：快速抽文字、座標、圖片、繪圖物件，編輯與標註 PDF，渲染頁面。 |
| [pypdfium2（PDFium 的 Python 綁定）](https://github.com/pypdfium2-team/pypdfium2) | 函式庫 | 3 | 需人工確認（Apache-2.0／BSD-3-Clause（通識，需核對）） | 2026-11-14 | 只有搜尋摘要 | Google PDFium 的 Python 綁定：渲染頁面成影像、抽文字與座標。MinerU、Docling 都用它或 PDFium 系列做底層。 |
| [qpdf](https://github.com/qpdf/qpdf) | CLI | 3 | 可使用（Apache-2.0） | 2026-09-26 | 只有搜尋摘要 | PDF 結構轉換與修復：解密、線性化、合併拆分頁面、檢查結構、輸出 JSON。 |
| [unstructured](https://github.com/Unstructured-IO/unstructured) | 函式庫 | 3 | 可使用（Apache-2.0） | 2026-11-19 | 讀文件 | 把 PDF、HTML、Word、圖片等切成帶類型標記的元素（Title、NarrativeText、Table…）供 RAG 前處理；另有付費 Transform API。 |
| [Nougat（Meta）](https://github.com/facebookresearch/nougat) | 函式庫 | 4 | 需人工確認（MIT（程式碼）；模型權重 CC-BY-NC 4.0（通識，需核對模型卡）） | 2025-02-21 | 讀文件 | 針對學術 PDF 的視覺 Transformer，直接輸出含 LaTeX 公式與表格的 Mathpix Markdown（.mmd）。 |
<!-- /ecosystem -->

# 文件解析試跑結果（2026-11-21）

方法見[上一層的 README](../README.md)。每個工具在兩份三頁的 PDF 上各跑一次：`fixture.pdf` 是一般的文字型 PDF，`fixture-scanned.pdf` 是同一份轉成 150 dpi 灰階圖片的模擬掃描件。答案在 `truth.json`，逐項分數與執行紀錄在 `results.json`，各工具的原始輸出在 `outputs/`。CPU 執行、斷網、記憶體上限 7 GB。

## 版本

| 工具 | 版本 |
|---|---|
| pdftotext | poppler 26.01.0（主機，作為基準） |
| pymupdf4llm | 2.1（PyMuPDF 2.1） |
| markitdown | 0.1.9（pdfminer.six 20260107） |
| Docling | 2.151.1，torch 2.15.0+cpu；`docling-tesseract` 改用 Tesseract 5.5 做 OCR，`docling-formula` 加 `--enrich-formula` |
| Marker | marker-pdf 2.2.0（surya-ocr 0.23.0），預設模式 |
| OCRmyPDF | 17.14.2，Tesseract 5.5.0，`-l chi_tra+eng --force-ocr`，再用 pdftotext 取文字 |

## 文字型 PDF

| 工具 | 耗時 | 記憶體峰值 | 表格儲存格 | 表格整列 | 雙欄順序 | 段落完整 | 中文 | 符號 | 圖片公式轉 LaTeX | 頁碼 |
|---|---|---|---|---|---|---|---|---|---|---|
| pdftotext | <1 s | — | 全對 | 0 | 錯（逐段交錯） | 8/8 | 3/3 | 7/7 | 否 | 保留頁尾 |
| pdftotext `-layout` | <1 s | — | 全對 | 全對 | 錯（兩欄並排） | 0/8 | 3/3 | 7/7 | 否 | 保留頁尾 |
| pymupdf4llm | 1.3 s | 327 MB | 全對 | 全對 | **對** | 8/8 | 3/3 | 7/7 | 否 | 保留頁尾 |
| markitdown | 0.8 s | 68 MB | 全對 | 全對 | 錯（逐段交錯） | 0/8 | 3/3 | 7/7 | 否 | 保留頁尾 |
| Docling | 13.4 s | 1,585 MB | 全對 | 全對 | **對** | 8/8 | 3/3 | 7/7 | 否 | Markdown 去掉；JSON 每段有頁碼與座標 |
| Docling `--enrich-formula` | 19.3 s | 1,948 MB | 全對 | 全對 | **對** | 8/8 | 3/3 | 7/7 | **是，有一處錯** | 同上 |
| Marker | 5.7 s | 793 MB | 全對 | 全對 | 錯（P04 跑到 P07 後面） | 8/8 | 3/3 | 7/7 | 否 | 去掉 |

## 模擬掃描件

| 工具 | 耗時 | 記憶體峰值 | 表格儲存格（英／中） | 雙欄順序 | 中文字（忽略標點與空白） | 符號 | 備註 |
|---|---|---|---|---|---|---|---|
| pdftotext | <1 s | — | 0 | — | 0/3 | 0 | 沒有文字層 |
| pymupdf4llm | 1.1 s | 322 MB | 0 | — | 0/3 | 0 | **輸出空檔，exit 0** |
| markitdown | 0.7 s | 64 MB | 0 | — | 0/3 | 0 | **輸出空檔，exit 0** |
| Docling（預設 OCR） | 23.4 s | 1,831 MB | 93%／100% | 錯（逐段交錯） | 2/3 | 4/7 | 一個繁體字被辨識成簡體（帶 → 带） |
| Docling＋Tesseract | 15.0 s | 1,170 MB | 97%／25% | 只找到 3/8 個標記 | 3/3 | 0/7 | 中文字之間插入空白、全形標點變半形 |
| Marker | 5.8 s | 847 MB | 97%／100% | 錯 | 2/3 | 2/7 | Σ 變成 Z、α·β 變成 aß |
| OCRmyPDF | 2.4 s | 294 MB | 93%／88% | 部分 | 3/3 | 0/7 | 原頁面影像不動，只加文字層；全形標點變半形 |

## 看到的事

1. **文字型 PDF 上，pymupdf4llm 和 Docling 每一項都對。** 兩者都把表格輸出成 Markdown 表格、照兩欄的順序讀。pymupdf4llm 快十倍、記憶體約五分之一；Docling 多了每段文字的頁碼與座標（JSON）。Marker 差在一段順序。markitdown 和 pdftotext 內容都在，但兩欄是逐段交錯的（P01、P05、P02、P06…），AI 讀到會把左右兩欄的論點混在一起。
2. **沒有 OCR 的工具遇到掃描件會「安靜地失敗」。** pymupdf4llm 和 markitdown 都輸出空檔、exit code 是 0。只看 exit code 會以為轉換成功。
3. **掃描件上沒有一個工具全對。** 中文字本身大多認得出來，錯在別處：繁體字被換成簡體（Docling 預設的 OCR）、字與字之間被插入空白、全形標點變半形（Tesseract）、數學符號被認成字母（Marker）、雙欄順序交錯。這些錯誤的共通點是「看起來像對的」，只有拿原頁面核對才看得出來。
4. **圖片裡的公式只有 Docling 開了 `--enrich-formula` 才轉成 LaTeX**，而且總和的上限 `n` 被認成 `\pi_{i}`，看起來完全合理。論文的公式不能直接信任轉換結果。
5. **頁碼。** Docling 與 Marker 的 Markdown 會去掉頁首頁尾，所以頁碼也不見了；要引用頁碼，Docling 得用它的 JSON（每段都有 `page_no` 與 bbox）。pymupdf4llm 保留頁尾文字，也能用 `page_chunks` 分頁輸出。OCRmyPDF 保留原本的頁面，頁碼不會變。
6. **「本機執行」要先暖機。** Docling 跑過 `docling-tools models download` 之後，仍要加 `--artifacts-path` 與 `HF_HUB_OFFLINE=1` 才能斷網執行，不然還是會去 Hugging Face 下載。Marker 2.2.0 第一次執行時另外下載了一個字型與 indra OCR 模型（約 110 MB），之後才能斷網跑。pymupdf4llm、markitdown、OCRmyPDF 一開始就不需要網路。
7. **記憶體都在 2 GB 以內**，8 GB 的 WSL 跑得動；耗時是三頁的 CPU 時間，不能直接換算成大型文件。

## 對框架的建議（S20 用）

- 先保留原始 PDF，判斷有沒有文字層（例如 `pdftotext` 抽出的字數）。
- 文字型 PDF：要快就用 pymupdf4llm；要引用頁碼、座標或圖片公式，用 Docling 的 JSON。pymupdf4llm 是 AGPL，框架只能當外部命令呼叫，不能 import 進 MIT 授權的程式（見[授權判讀](../../../../docs/ecosystem/license.md)）。
- 掃描件：先用 OCRmyPDF（`-l chi_tra+eng`）加文字層，頁面影像與頁碼不變，再走文字型的流程；或直接用 Docling。不論哪一種，表格數字、公式與繁簡字都要對照原頁面抽查。
- 每次轉換都檢查輸出長度，不只看 exit code。

## 限制

- 測試材料是自己產生的三頁 PDF，版面比真實論文簡單（沒有合併儲存格、跨頁表格、腳註、圖表）。真實文件的表現要另外測。
- 每個組合只跑一次，耗時與記憶體有誤差。
- MinerU 沒有測：它的 standard 方案要 8 GB 記憶體，剛好是這台 WSL 的上限，而且遙測預設開啟（見資料庫的文件解析頁）。Marker 只測了預設模式，balanced 模式需要 GPU 或本機推論伺服器。

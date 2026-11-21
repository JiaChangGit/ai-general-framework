# M 子代理筆記：資料與媒體（2026-11-21）

範圍：E1 shell 工具、E2 文件解析與 OCR、G 網頁研究與資料、H CI／資安、J 寫作與研究、K 音樂、L 影片。資料庫草稿在 [`drafts/M.json`](drafts/M.json)（133 筆，格式依 SPEC.md）。

## 先講限制

- 所有 `evidence` 都只填實際達到的等級。133 筆裡：`source` 14 筆（clone 後讀結構）、`docs` 32 筆、`search` 87 筆。**shell 工具大多只有 `search`**：我看了維護狀態（`gh api`）和本機 `--version`，沒有逐一讀 README，旗標與陷阱主要來自通識，已標在各筆的 `evidence` 與 `confidence`。
- 沒有安裝、執行或 build 任何東西。Docker 試跑留給主 session。
- 維護狀態一律是 `gh api repos/OWNER/REPO` 在 2026-11-21 的唯讀結果；stars 不當品質證據。
- benchmark 數字只引用有出處的，作者自報一律標明；OmniDocBench 由 OpenDataLab（MinerU 的組織）維護，不是中立第三方。

## 本機環境（which 實測）

已裝：grep、rg 14.1.1、find、awk（mawk、gawk）、sed、cut／sort／uniq／join、xargs、diff、git、jq 1.8.1、yq（mikefarah v4.53.3，在 /usr/local/bin）、base64、bc、xxd、hexdump、od、less、file、strings、strace、gdb 17.1、tesseract 5（**語言只有 eng、osd，沒有中文包**）、ocrmypdf 16.13.0、pdftotext 26.01.0、pdftoppm、docker 29.10.0、gh 2.105.0、python3、pip3。
沒裝：ag、fd、fzf、sd、parallel、delta、difft、diff-so-fancy、jd、csvkit、mlr、xsv、qsv、hexyl、bat、ltrace、perf、bpftrace、pandoc、markitdown、vips、convert／magick、resvg、rsvg-convert、cwebp、ffmpeg、whisper-cli、qpdf、mutool、sox、lilypond、mscore、piper、node、uv、pipx、mmdc、gitleaks、trivy、semgrep、osv-scanner、syft、grype、actionlint、zizmor、pre-commit、act。PyMuPDF（`import fitz`）也沒有。
記憶體 `free -m` 看到約 8.6 GB（可用約 7.4 GB），16 個 CPU。

## E1 Shell 工具

查了什麼：維護狀態全查；difftastic、diffsitter、jd、GumTree、qsv、kislyuk/yq、ag 的 README 前半有讀；whisper.cpp README 的記憶體表有讀。沒查到：多數工具的 README 全文、XML diff 工具的比較（只收 xmldiff 一筆，內容很少）、ltrace／perf／bpftrace 在 WSL2 的實測。

重點發現：

- **AI 什麼時候該用工具代替自己讀或算**：統計、分組、頻率表（awk、sort|uniq -c、Miller、qsv）、大 JSON 看形狀（jq 的 keys／length）、取檔案局部（sed -n 'N,Mp'）、找檔案（rg --files、find）、辨識未知檔案（file --mime-type）、進制／端序／bit（框架已有 `binary bytes|bits|dump`，不要心算）。
- **控制輸出量的共通招式**：先看範圍再看內容（rg -l／-c、git diff --stat、jq 'keys'）、限制行數（head、-m N、--max-columns）、輸出只取統計。ripgrep 預設會略過被 .gitignore 或隱藏的檔案，所以「0 筆」不等於「不存在」。
- **不要讓 AI 用的**：互動式工具（fzf、less、bat 的 pager、delta／diff-so-fancy 的裝飾輸出）。AI 自動化要關 pager（`GIT_PAGER=cat`、`PAGER=cat`）。
- **同名專案**：yq 有兩個。本機是 mikefarah（Go，支援 `-i` 就地改）；kislyuk 是 Python 包裝 jq，語法是 jq、輸出 YAML 要 `-y`。腳本寫 `yq` 前先 `yq --version`。
- **xsv 已封存**（archived，2025-04-24）；活躍分支是 qsv（但 qsv 含 `describegpt` 等會呼叫 LLM API 的命令，要留意外送）。**ag 維護停滯**（2024-06-16 最後 push，README 還在找人接手），改用 rg。**SoX** 上游停滯，ffmpeg 可取代。
- **結構／語意 diff（特別研究）**：
  - difftastic（tree-sitter，30 多種語言，結構 diff、不以行為單位、能分辨縮排只是空白變動；README 已讀）是首選，輸出是給人看的並排顯示，**不能 git apply**。
  - diffsitter 同樣以 tree-sitter AST 比對，但 README 自述「nowhere close to production ready」，語言較少。
  - GumTree 是研究出身（LGPL-3.0，需 JVM），特點是能辨認「搬移」「改名」，支援 C、Java、JavaScript、Python、R、Ruby；日常 CLI 體驗不如 difftastic。
  - jd 比對 JSON／YAML 的結構（以路徑標示差異、陣列可選集合語意）。xmldiff 比對 XML／HTML。
  - 都只是「讓人或 AI 少讀雜訊」，不是語意等價證明。重構後的 diff 審查可試 difftastic 對照 `git diff` 的 token 量（待試跑）。
  - 沒查到：已被廣泛驗證的 C／C++ 語意 diff 工具；Linux kernel 風格 patch 的結構 diff 沒有查到成熟選項。
- **格式轉換**：pandoc（GPL-2.0-or-later，當子行程用不影響框架）適合 DOCX／EPUB／HTML ↔ Markdown，但 PPTX 只能輸出、PDF 不能當輸入；markitdown 輕量但 PDF 只靠文字層；libvips 比 ImageMagick 省記憶體；resvg 不跑 SVG 內的腳本；libwebp 有 CVE-2023-4863（2023，堆積溢位，需用已修補版本）；whisper.cpp README 的記憶體表（官方自報）tiny 約 273 MB、base 約 388 MB、small 約 852 MB、medium 約 2.1 GB、large 約 3.9 GB，8 GB 可跑到 medium。
- 本機缺 ffmpeg、pandoc、libvips、resvg：這四個是影片與文件流程的共同前置，主 session 若要試跑需決定裝在 Docker 還是 WSL。

## E2 文件解析、OCR、PDF

查了什麼：Docling、Marker、MinerU clone 後讀 README、授權、結構、設定（Docling 讀了 backend 目錄與 pipeline_options.py，MinerU 讀了 telemetry.py，Marker 讀了授權檔與模式表）；anydoc 讀 README；其他讀 README 關鍵段（grep 摘錄，不是全文）；評測讀 OmniDocBench README 與 Docling 技術報告的速度表。沒查到：獨立第三方的 Docling／MinerU／Marker 同條件比較（沒找到）。

**anydoc 是哪個**：`firecrawl/anydoc`（MIT，Rust，Node／Python 綁定，也是 Agent Skill；23,645 stars，2026-11-18 仍在更新）。同名的有 `gmh5225/anydoc`（它的 fork，0 stars）與 SourceForge 的 `anydoc.mirror`（舊的、與此無關），要避免混淆。它的 PDF 靠同一家的 `firecrawl/pdf-inspector`；本機版**不做 OCR**，掃描頁回 `NeedsOcr`，OCR 要加 `--ocr hosted` 送到 Firecrawl Parse（雲端）。

### 比較 1：文件解析

作者自報與第三方評測分開寫。「—」是沒查到，不是沒有。

| 工具 | 解析正確度（出處） | OCR | 表格 | 版面／閱讀順序 | 公式 | 頁碼與座標 | 本機 | 速度與記憶體 | 格式涵蓋 | 授權 |
|---|---|---|---|---|---|---|---|---|---|---|
| Docling | OmniDocBench v1.6 官方榜未列；Marker README 自報 67.5（OmniParseBench，競品自報）；技術報告為速度而非正確度 | 有（EasyOCR 預設，可換 Tesseract、RapidOCR 等） | TableFormer | 有版面模型與閱讀順序 | 有（程式碼與公式） | DoclingDocument 保留頁與 bbox | 是（可預載模型、air-gapped） | 作者自報（技術報告，v1 時期）：x86 CPU 約 3.1 s／頁、M3 Max 約 1.26 s／頁、L4 GPU 約 0.48 s／頁；OCR 在 CPU 約 13 s／頁 | PDF、DOCX、PPTX、XLSX、HTML、EPUB、影像、音訊、影片等 | MIT；模型權重另查 |
| Marker | 作者自報（自家 OmniParseBench）：balanced 80.5、fast 71.0、no_ocr 40.8（數位檔 82.7）；OmniDocBench v1.6_full（MinerU 組織維護）：78.44 | 有（Surya VLM；fast 模式為 ONNX OCR） | 有（含 CPU 表格重建） | 有版面與閱讀順序 | 有（balanced 轉 LaTeX） | JSON 輸出含區塊；細節未驗 | 是；balanced／vllm 需 GPU 與本機推論伺服器 | 作者自報 fast 約 23.6 pg/s、no_ocr 約 57 pg/s（CPU，未說明硬體）；本機無 GPU 只能走這兩種 | PDF、影像、Office | 程式碼 Apache-2.0；權重修改版 OpenRAIL-M（商用有營收門檻、含 Share-a-Like） |
| MinerU 4.x | OmniDocBench v1.6_full：MinerU-2.5 93.04（榜單維護者與 MinerU 同組織）；PaddleOCR-VL 論文（競品作者）引用 v1.0 舊版數字僅供參考 | 有 | 有 | 有版面與閱讀順序 | 有 | doclib 提供穩定引用定位（頁碼與區塊）；content list 含座標 | 是；`--remote` 才送官方服務；**遙測預設開** | 官方 tier 表：basic（ONNX）約 0.8 GB 下載、最低 2 GB RAM；standard／advanced（ONNX＋llama.cpp）約 2 GB 下載、8 GB RAM；PyTorch 路線 16 GB 與 8 GB VRAM | PDF、影像、Office、EPUB、OFD、HTML、CSV | Apache-2.0 加附加條款（MAU 1 億或月營收 2000 萬美元門檻；對外服務須標示） |
| OCRmyPDF | —（不產生結構化文字，不適用） | Tesseract（可換插件） | 否 | 否（只加文字層） | 否 | **頁面影像原封不動，頁碼不變** | 是 | 多核平行；依 Tesseract | PDF、影像輸入，PDF 輸出 | MPL-2.0 |
| PyMuPDF／pymupdf4llm | —（沒查到獨立評測） | 否（可外接 Tesseract） | 依向量線推測 | 依文字層 | 否 | page_chunks 與 bbox 有 | 是 | 輕量快 | PDF 為主 | **AGPL-3.0**（或 Artifex 商用）；會污染 MIT 框架，不要當依賴 |
| markitdown | —（沒查到） | 否（圖片描述、音訊會呼叫外部服務時要確認） | 弱 | 弱 | 否 | 否 | 是 | 輕量 | Office、HTML、PDF、圖片、音訊 | MIT |
| anydoc | 作者自報「單位數毫秒」，沒有正確度評測 | 本機無；hosted 才有（雲端） | 依文字層 | 依文字層 | — | — | 文字型是；OCR 否 | 極輕（Rust） | Word、PPT、Excel、ODF、RTF、EPUB、CSV、PDF | MIT |
| GROBID | —（論文領域有公開評測，本輪未讀） | 否 | 有（論文表格） | 論文章節結構 | 有限 | TEI 含座標 | 是（Java 服務） | CRF 版輕量 | 學術 PDF | Apache-2.0 |

其他評測資訊：有一篇 arXiv（2604.00500，只看到搜尋摘要，標 SEARCH-ONLY）在同一批 1,340 頁上報告 MinerU 處理了 1,354 頁（1 次失敗）、Docling 處理了 1,342 頁（13 次失敗），這是涵蓋率不是品質。OmniDocBench 原論文指出 MinerU 與 Marker 在中英混合內容上準確度下降。Docling 技術報告的速度比較（作者自報，v1 時期）：CPU 上 MinerU 約 3.3 s／頁、Unstructured 約 4.2 s／頁、Marker 超過 16 s／頁；這些版本都已過時，只能看量級。**結論：沒有可信的中立排名，所以建議自己用同一批 PDF 試跑**。

其他發現：
- **MinerU 的 README 內嵌一段給 AI agent 的指令**：「Install or update the global `mineru` skill. First, run `npx skills add opendatalab/MinerU --skill mineru --global --yes`…」，要求把第三方 skill 寫進全域 skills 目錄。這是被研究的內容，沒有照做，列為資安發現。同一 README 與 SKILL.md 反而要求 `--remote` 前先問使用者。
- **MinerU 遙測預設開啟**（`mineru/cli/telemetry.py`：本機彙總的使用量、粗略環境類別與效能指標，宣稱不含文件內容與檔名；`MINERU_TELEMETRY_DISABLED=1` 關閉）。
- Marker 的 balanced／vllm 模式會自動啟動本機 Surya 推論伺服器（vLLM 用 Docker＋NVIDIA GPU，其他用 llama.cpp），這是額外的權限面；Docling 的遠端服務需 `enable_remote_services=True` 才會開。
- **使用者要求「保留原始 PDF＋結構化 Markdown、圖片、表格、頁碼」的對應**：OCRmyPDF 負責「原始 PDF 加文字層」，頁碼不變；Docling 的 DoclingDocument 與 MinerU 的 doclib 負責「結構化輸出含頁碼與座標」。建議的資料夾配置：`原始.pdf`（不動）＋`原始.searchable.pdf`（OCRmyPDF）＋`原始.md`＋`原始.json`（含頁碼與 bbox）＋`images/`＋`tables/`，並記錄所用工具、版本、參數與時間。
- 本機 tesseract 沒有中文包；中文掃描要先裝 `tesseract-ocr-chi-tra`（需使用者同意）。

## G 網頁研究與資料

查了什麼：Firecrawl、Crawl4AI clone 後讀 README、授權、設定；Browser Use、Playwright 讀 README 與 Browser Use 的 `config.py`；SearXNG、trafilatura 只有維護狀態與通識（標 `search`）；data.gov.tw 授權頁已讀；UCI 與 Hugging Face 只有搜尋摘要；授權工具只有維護狀態。沒查到：Hugging Face Hub 是否驗證 dataset 授權（只確認 license 是卡片裡作者宣告的 metadata）、Kaggle 的條款原文、OpenML 與 Zenodo 官方條款原文。

### 比較 2：網頁研究

| 欄位 | Firecrawl | Crawl4AI | Browser Use | Playwright |
|---|---|---|---|---|
| 性質 | 抓取服務（scrape、crawl、map、search） | Python 爬蟲函式庫與自架 server | LLM 驅動瀏覽器的 agent | 瀏覽器自動化函式庫 |
| 靜態／動態渲染 | 兩者（Local 與自架有瀏覽器服務） | 兩者（Playwright） | 真實瀏覽器 | 真實瀏覽器 |
| JavaScript | 有 | 有 | 有 | 有 |
| 反爬 | 雲端有 Fire-engine 等；自架需自行設定（SELF_HOST.md） | stealth 與 undetected 模式（可能違反網站條款） | 雲端瀏覽器；本機依設定 | 無內建，要自己處理 |
| 結構化擷取 | 雲端有 structured JSON、Agent；本機 scrape 回 Markdown | CSS／XPath 無 LLM、LLM 擷取、schema generator | 由 LLM 在任務中取得 | 自己寫選擇器 |
| API 價格 | Keyless 每月 1,000 點免費；其餘依方案（README 未列表） | 雲端 1,000 點／月免費，方案 $10 起（README）；函式庫與自架免費 | 雲端新註冊 $1 額度；按 token 與雲端用量 | 免費 |
| 本機部署 | Firecrawl Local（Rust）、完整 Docker 自架 | pip 加 Docker | pip，本機 Chromium | 是 |
| MCP | 有（本機與雲端混用） | 有（自架 server 與託管 MCP） | 有（README 標 mcp-name） | 有（@playwright/mcp）；另有 Playwright CLI，README 稱較省 token（作者自報） |
| rate limit／robots | README：預設遵守 robots.txt；雲端 fallback 無帳號限速 | `check_robots_txt` **預設 False**，要自己開 | 無（agent 行為） | 自己寫 |
| 會不會把資料送到雲端 | **會**：Local 抓取失敗預設改由 Firecrawl Cloud 抓（`FIRECRAWL_CLOUD=off` 才不會）；search 與 Alexandria 一律雲端 | 函式庫與自架不會；雲端 API 與託管 MCP 才會；LLM 擷取會送給你設的 LLM | 預設 `ANONYMIZED_TELEMETRY=true`；雲端路徑送任務；本機模式頁面內容送 LLM | 不會 |
| 授權 | AGPL-3.0（SDK 與部分 UI 為 MIT） | Apache-2.0 | MIT | Apache-2.0 |
| 8 GB 可行 | 自架多服務偏重（未實測）；Local 輕 | 可，單頁到小量併發 | 可（成本在 LLM） | 可 |

**建議**：靜態頁面用 trafilatura；需要渲染與 Markdown 用 Crawl4AI（Apache-2.0、純本機）並開 `check_robots_txt`；必須互動（登入、表單）才用 Browser Use 或 Playwright 腳本；Firecrawl 只當參考，用的話一定關雲端 fallback。搜尋後端可自架 SearXNG（AGPL，自用 OK，但上游搜尋引擎常封鎖）。

來源與限速實務（`rss-sitemap-robots` 一筆，只有 RFC 9309 的名稱，沒逐條讀）：優先 API／feed／sitemap；固定 User-Agent、每網域限速、遵守 `Retry-After`；記錄抓取時間與 URL；robots.txt 是禮貌協定，不是授權。去重與來源可信度**沒有找到值得收錄的專門工具**，只能當規則寫在框架（URL 正規化加內容雜湊；來源類型由人標記）。

### 授權要分層（不要混為一談）

| 層 | 例子 | 本輪遇到的案例 |
|---|---|---|
| repo 程式碼授權 | LICENSE | Crawl4AI Apache-2.0；Firecrawl AGPL-3.0；Remotion 自訂規模條件；MinerU Apache-2.0 加條件 |
| 相依套件授權 | 鎖檔內各套件 | PyMuPDF 是 AGPL，會讓用它的程式整體受影響 |
| 模型權重授權 | HF 模型卡 | Marker 權重修改版 OpenRAIL-M；YuE 權重 CC BY-NC；AudioCraft 權重 CC-BY-NC；Kokoro 權重 Apache-2.0 |
| 資料集授權 | dataset card、平台條款 | Hugging Face 卡片的 license 是作者宣告；data.gov.tw 是 OGDL-Taiwan-1.0 |
| 個別素材著作權 | 圖片、文字、樂曲、影格 | claude-animated-shorts 的參考影格；music-composition-skills 的書籍引述（NOTICE 明說不被重新授權） |
| 生成結果使用限制 | 服務條款、模型授權 | Suno、MiniMax、TinyMusic 條款（本輪沒讀原文）；ACE-Step 只有侵權風險提醒 |

**data.gov.tw**（`https://data.gov.tw/license` 已讀，2026-11-21）：政府資料開放授權條款第 1 版（2015-07-27）。可為任何目的免費使用、衍生、再授權；**須依格式顯名標示資料提供機關**，未標示視為自始未取得授權；與 CC BY 4.0 相容（可改用 CC BY 4.0 利用）；授權不可撤回，但機關得因公共利益或第三人權益停止提供。SPDX 識別碼 `OGDL-Taiwan-1.0`。個別資料集若指定其他條款，以資料集頁為準。

授權分析工具：ScanCode Toolkit（現在在 `aboutcode-org`，原 nexB；Apache-2.0 程式碼，授權規則資料另有條款，GitHub 回 NOASSERTION）、ORT（Apache-2.0，JVM，偏企業流程）、FOSSology（GPL-2.0，需常駐服務與資料庫，不適合個人）、REUSE（檢查標示是否齊全，不判斷相容性）、licensee（GitHub 授權欄位背後的偵測，只看根目錄 LICENSE）。個人框架實務上用 `gh api` 的 `license.spdx_id` 初篩，**NOASSERTION 或 other 一律回頭讀 LICENSE 本文**。

## H CI／資安

查了什麼：維護狀態全查；zizmor、Snyk Agent Scan、Cisco MCP Scanner README 前半已讀；其他靠通識與搜尋。供應鏈事件用 WebSearch 查（來源為安全公司與官方公告的搜尋摘要，標 SEARCH-ONLY，沒有逐篇讀全文）。

### 供應鏈與資安事件

| 日期 | 事件 | 受影響 | 來源 |
|---|---|---|---|
| 2025-03-14（首次發現；惡意 commit 在 03-10 至 03-14 之間） | tj-actions/changed-files 被入侵，會傾倒 CI secrets（CVE-2025-30066）；上游 reviewdog/action-setup@v1 先被入侵（CVE-2025-30154） | 使用該 Action 的 repo（Unit 42 稱超過 23,000 個）；v46.0.1 修正 | CISA 警示、Unit 42、Wiz |
| 2025-09-14 起；2025-11 第二波 | Shai-Hulud npm 自我複製蠕蟲 | 第一波數百個套件（各來源 187 至 500 以上），第二波 11 月 24 日報導大規模 | Krebs、Register、Unit 42 |
| 2026-03-19 | Trivy 生態系被入侵（CVE-2026-33634，GHSA-69fq-xp46-6x23，歸因 TeamPCP） | Trivy v0.69.4（約 3 小時後移除）；Docker Hub 映像 v0.69.4–0.69.6；trivy-action 0.0.1–0.34.2 標籤被強制改指（來源說 75 或 76 個）；setup-trivy 0.2.0–0.2.6（來源對 0.2.6 是否安全說法不一）；03-22 另有 Docker Hub 憑證被盜攻擊。安全：v0.69.2／0.69.3、trivy-action 0.35.0 | GitHub 官方公告、Aqua 部落格、Snyk |
| 2026-03-23 | Checkmarx kics-github-action 與 ast-github-action 被入侵（同一批憑證竊取程式） | KICS Action 暴露時段 12:58–16:50 UTC（Wiz）；ast-github-action 範圍來源不一（v2.3.28 可能全部） | Wiz、SOCRadar |
| 2026-03-24 | LiteLLM（BerriAI，PyPI）1.82.7 與 1.82.8 被植入後門，約 3 小時後隔離；起因是 CI 用到被入侵的 Trivy 而洩漏維護者 PyPI 憑證 | 1.82.7（proxy_server.py 與 .pth）、1.82.8（litellm_init.pth，每次啟動 Python 都執行）；乾淨版 1.82.6 | LiteLLM GitHub issue #24518、JFrog、Snyk |
| 2026-04-22 | Checkmarx 第二波：checkmarx/kics Docker 映像、VS Code 與 OpenVSX 擴充、ast-github-action 工作流程被改 | ast-github-action 2.3.35 受影響、2.3.36 安全；擴充 2.64.0 與 1.18.0 為修補版 | Hacker News、Trend Micro |
| 2026-05 至 07 | 2026-05 TanStack（GitHub Actions 快取投毒）、@antv（Mini Shai-Hulud，Microsoft 2026-05-20）；2026-06 Red Hat 相關 npm 與 Miasma；2026-07-14 AsyncAPI 發佈管線被入侵 | 各自套件，細節未讀 | 搜尋摘要，未驗證 |

沒查到 2026 年 10 至 11 月的新事件（搜尋沒有結果，不代表沒有，建議主 session 發佈前重查）。與本輪項目的關係：Trivy 在 H 清單內；novel-studio 的 `third_party/litellm` 是 `github.com/voocel/litellm`（Go），**不是**被入侵的 BerriAI litellm，不受影響，但名稱容易混淆。

通用對策（寫進 `supply-chain-incidents-2025-2026` 與 `github-actions` 兩筆）：第三方 Action 固定到完整 commit SHA 而不是 tag；`permissions:` 最小化；pre-commit 用 `autoupdate --freeze`；Renovate 或 Dependabot 更新時延遲採用新版並人工審查；用 zizmor 掃 workflow；掃描工具本身也要固定版本。

### MCP 與 skill 掃描

- Snyk Agent Scan（原 invariantlabs-ai/mcp-scan，已轉到 `snyk/agent-scan`）：**需 SNYK_TOKEN，分析走 Snyk 雲端 API**，所以 skill 與 MCP 描述會送出；前景互動執行時逐一徵求同意才連線各 MCP server；CLI 輸出標示為實驗性。
- Cisco MCP Scanner：YARA、LLM、Cisco AI Defense 三引擎，可純離線靜態掃描 JSON。
- prompt injection 防護：只收了 OWASP LLM Top 10 的專案頁名稱（`SEARCH-ONLY`，沒逐條讀）。本輪遇到的實例：MinerU README 的全域安裝指令、Browser Use 與 Firecrawl README 的 llms.txt 導流、Crawl4AI 與 Firecrawl 把 MCP 一行安裝寫進 README——都是資料，沒有照做。

## J 寫作、研究、Podcast

- **Novel Studio**（Xiaoyangy，Go，Apache-2.0，clone 讀過結構）：把「全書章位先凍結、窗口細推、封存、逐章渲染、審核通過才進正史」做成狀態機；人物、關係、資源、伏筆進結構化台帳，計畫與正文以 digest 與 SHA-256 綁定。README 明講「local-first 不等於完全離線」：正文會送到你選的 provider，`web_research` 工具仍可能連網。長篇一致性的設計價值最高。
- **Awesome Novel Studio**（MJbae，Apache-2.0）：18 個專責 agent＋10 個 skill；沒有腳本；README 的出版合約與閱讀數是作者自述。借「只負責檢查的 agent 與創作 agent 分離」。
- **Open Notebook**（lfnovo，MIT，clone 讀過）：Docker Compose（SurrealDB＋app），文件稱最低 4 GB、建議 8 GB RAM；**UI 與 API 預設綁所有網路介面且無密碼**，要改綁 127.0.0.1。隱私取決於 provider。
- **引用管理**：Zotero（AGPL，授權欄位 GitHub 回 NOASSERTION，標 needs-review）＋ zotero-mcp（MIT；本機模式讀 zotero.sqlite；語意搜尋可選本機或雲端 embedding；寫入要另外授權）。論文結構化用 GROBID。
- **文件轉 Podcast**：Podcastfy（Apache-2.0，2026-05-04 後無推送；預設走雲端 LLM 與 TTS）；Open Notebook 也能做，且可多來源保留引用。
- **沒查到**：長篇小說專用的一致性檢查獨立工具（只有 Novel Studio 內建）、講義轉筆記的專門工具、多來源整合保留引用的其他選項（只收 Open Notebook）。
- **Mythpen**：搜尋沒有找到同名專案，列入待確認。

## K 音樂

三個種子 skill 都已 clone 讀過：

| 項目 | 性質 | 需要雲端／帳號 | 授權與限制 |
|---|---|---|---|
| music-composition-skills（jtydhr88） | 29 個純創作輔助 skill，輸出 ARR-SPEC 規格表，不產生音訊；無腳本 | 否 | MIT，但 NOTICE 說明書籍引述不被重新授權 |
| lyrics-to-song-skill（Beatra） | 把歌詞整理成請求，經 Beatra 以 Suno 6／MiniMax Music 3.0 渲染 | **是**（帳號、點數、憑證寫 `~/.beatra/`） | skill 為 MIT-0；音樂使用權依 Beatra 與底層模型條款（沒讀）；2026-10 起移除自我更新器 |
| tinymusic-agent-skills | 6 個 skill，預設輸出可貼到網站的生成包，接 MCP 才直接生成 | 選配 | MIT；商用說法來自廠商自述 |

**三類比較**：純創作輔助（music-composition-skills；零成本、零外送、需自己配音樂模型）；雲端生成 API（Beatra、TinyMusic，以及 Suno 類；便宜入門但資料外送、點數計費、使用權看條款）；本機開源模型（ACE-Step 1.5、YuE、MusicGen）——**本機沒有 GPU，三者都不實用**：ACE-Step README 的 VRAM 表最低 ≤6 GB 可跑 2B turbo（INT8＋CPU offload）、XL 需 12 GB 以上；YuE2 需 24 GB VRAM；MusicGen small 可在 CPU 慢速生成。

**權重、訓練資料、商用、生成結果要分開寫**（各筆已拆）：

- ACE-Step：程式碼 MIT；權重授權與訓練資料條款本輪沒讀（要看 Hugging Face 模型卡）；README 只提醒風格近似可能侵權。
- YuE：程式碼 Apache-2.0；**權重 CC BY-NC 4.0 加附加創作者許可**，公司商用需洽授權，附加條款禁止有害或欺騙用途，標 `not-recommended`。
- AudioCraft／MusicGen：程式碼 MIT；**權重 CC-BY-NC 4.0**，標 `not-recommended`。
- Kokoro：kokoro-onnx 程式碼 MIT；權重 Apache-2.0（模型卡已讀）。Piper：原 rhasspy/piper **已封存**（2025-08-26），維護轉到 `OHF-Voice/piper1-gpl`（GPL-3.0）；每個語音模型授權另看。
- DiffSinger（Apache-2.0）README 明文禁止未經同意生成他人聲音；OpenUtau 為 GUI，歌手音庫授權各異。
- 符號與譜面工具：music21（BSD-3-Clause）可程式驗證和弦與音域，符合「確定性工具優先」；LilyPond、MuseScore（GPL，只當外部命令）、ABC notation 是「AI 寫文字、工具渲染」。ffmpeg 與 SoX 負責剪混音（SoX 上游停滯）。
- STT 見 E1 的 whisper.cpp 與 faster-whisper。

## L 影片

讀過：Remotion（授權、AGENTS.md、packages 結構、licensing 的 usage event）、claude-animated-shorts（SKILL.md 與結構）、stickman-kino（README、setup.mjs、audio.mjs、env.mjs、skills）；Hyperframes 沿用 `docs/link-study.md`（eb16510）只補維護狀態；Motion Canvas、Manim、Revideo 只有維護狀態與通識。

**Remotion 授權**（`LICENSE.md`，commit 970849f）：免費條件是個人、3 人以下營利組織、非營利組織、或評估階段尚未商用；其他營利組織要買 Company License；禁止複製或修改程式碼來販售自己的衍生版本；文件稱 5.0 版會稍作改變。使用者若是個人，適用免費授權。**不要只看 GitHub 的授權欄位**（NOASSERTION）。Remotion 的 licensing 套件對 web-render 與 cloud-render 事件向 remotion.pro 登記使用；本機 CLI 渲染是否登記沒追蹤完。

**claude-animated-shorts 的坑**：每次 bundle 把 `public/`（約 1.3 GB）複製到暫存資料夾不清除（作者自述曾佔滿 60 GB）；2K 渲染約 4 fps；`references/frames` 與 `sheets` 含從 20 支參考短片截取的影格，著作權屬原創作者，不在 MIT 範圍；SKILL.md 的流程有 Python QA 腳本（黑、白、凍結、跳格、響度檢查）與詞時間戳驅動畫面的做法，值得借鑑。

### 「Claude Code 寫場景與動畫程式碼，本機 renderer 組成影片」流程

| 步驟 | 誰做 | 工具 | 8 GB WSL 跑得動嗎（我沒實測，依來源估） |
|---|---|---|---|
| 1 技術報告 | 使用者提供；AI 摘要 | 文件解析見 E2（保留原 PDF） | 可 |
| 2 腳本（旁白稿、章節、每段秒數預估） | Claude | 純文字；存成可審的檔案 | 可 |
| 3 分鏡 | Claude | Stickman Kino 的 `film.json`（有 JSON schema，可確定性驗證）；或 Remotion 的鏡頭表 | 可 |
| 4 動畫場景程式 | Claude | 結構與圖表：HyperFrames＋GSAP（Stickman Kino 的 engine）、Remotion（React）；數學與演算法：Manim；向量講解：Motion Canvas、Revideo。渲染前先 `check` 與縮圖聯絡表 | 場景撰寫可；預覽與縮圖受 Chrome 記憶體影響，單一 Chrome 約 1～2 GB |
| 5 旁白 | 本機 TTS | Kokoro（約 200 MB，CPU 可）或 Piper；真實音長回頭決定每段時長；需要詞時間戳可用 whisper.cpp（base 約 388 MB） | 可 |
| 6 組成 MP4 | 本機 renderer | headless Chrome 逐格＋ffmpeg 編碼（HyperFrames／Remotion） | Stickman Kino 自述每分鐘 1080p 約 2～3 分鐘渲染（無 GPU 筆電，作者自述）；Remotion 需控制 `--concurrency` 與暫存資料夾；three.js 重場景與 4K 不建議 |
| 7 QA | 工具＋AI | ffprobe 查長度與串流、抽影格目視、響度；claude-animated-shorts 的逐格檢查腳本概念 | 可 |

最完整且最貼近此流程的是 Stickman Kino（全本機、無付費 API、旁白時長驅動畫面）；風險是它的 `setup` 會用 `apt-get download` 取 deb 補 Chrome 函式庫、並自動安裝 Kokoro 與下載 Chrome，這些「下載並執行外部程式」的步驟需主 session 在 Docker 內評估，不要在使用者的 WSL 直接跑。

## 建議：Docker 內文件解析試跑

**工具（3～4 個）**：

1. **Docling**（MIT；預載模型後可 `--network none`）。
2. **MinerU**（先 `MINERU_TELEMETRY_DISABLED=1`，走 basic 與 standard 的 ONNX 路線；README 的 agent 全域安裝指令不要跑）。
3. **Marker**（`--mode fast` 與 `no_ocr`；本機無 GPU，balanced／vllm 測不到，要知道結論不含 GPU 路線）。
4. **OCRmyPDF＋Tesseract**（基準線，且是使用者要的「原始 PDF 加文字層」；本機已裝，但中文包要另裝）。
可選加 anydoc 當 Office 檔的輕量對照（只測本機路徑，不用 `--ocr hosted`）。

**PDF（2～3 份公開）**：

1. arXiv 有表格、公式、多欄的論文：例如 `arxiv.org/abs/2206.01062`（DocLayNet，Docling README 也用它當範例）與 `2408.09869`（Docling 技術報告）。授權依各論文頁的 license 欄位，試跑只做本機處理、不散布輸出。
2. 一份中文 PDF：從 data.gov.tw 或政府機關網站挑一份公開中文報告（含表格與多欄；OGDL-Taiwan-1.0，需顯名；我沒有指定具體 URL，因為沒核對過其可用性與資料集授權）。
3. 一份掃描頁：用 `pdftoppm -r 200` 把上述論文其中一頁轉成圖片、再轉成純影像 PDF 當「模擬掃描」，授權與可重現性最穩；真實掃描可用 Internet Archive 的公有領域書頁（需核對該書狀態）。

**觀察項目**：每頁耗時與整份耗時；峰值記憶體（`docker stats` 與 `/usr/bin/time -v`）；是否真的沒有連網（`--network none` 與預載模型，並記下首次下載的模型大小）；頁碼是否保留、是否有 bbox；表格是否成為正確的 Markdown 或 HTML 表格（人工抽查幾個，含跨頁表格）；公式是否為 LaTeX；多欄閱讀順序；中文字準確度與標點；圖片是否抽出並與頁碼關聯；掃描頁在無 GPU 下的表現；輸出大小；遙測與意外外連（MinerU）。

**記憶體夠不夠**：官方文件只有 MinerU 給了 RAM（basic ONNX 最低 2 GB、standard ONNX 加 llama.cpp 8 GB——剛好等於 WSL 的 8 GB，容易吃緊，PyTorch 路線 16 GB 且需 8 GB VRAM，不可行）。Docling 與 Marker fast 的記憶體我沒找到官方數字，要靠試跑量；Docker Desktop 的 WSL 限制 8 GB，三個工具不要同時跑，一次一個，並預留模型下載的磁碟（數 GB）。**判斷：Docling、Marker fast、OCRmyPDF 大概可行；MinerU standard 在 8 GB 邊緣；任何需要 GPU 的路線（Marker balanced／vllm、olmOCR、PaddleOCR-VL、YuE、ACE-Step）這台測不到**。

## 待確認

| 名稱 | 候選與理由 |
|---|---|
| Mythpen | 搜尋沒有找到同名專案。候選：Mythflow（itch.io 上賣的 AI 小說世界觀工具，$39 起）、TheMostlyGreat/mythos（AI 寫作輔助）、StoryCraftr（開源 AI 小說工具）。都只是名稱相近，沒有證據是使用者說的那個，需使用者補來源。 |
| anydoc | 確定為 firecrawl/anydoc；需向使用者確認是否就是它（另有 gmh5225 的 fork 與 SourceForge 同名舊專案）。 |
| yq | 兩個專案：mikefarah（本機已裝）與 kislyuk；腳本要註明哪一版。 |
| Remotion 本機渲染的使用登記 | licensing 套件有 usage event，本機 CLI 是否送出沒確認。 |
| Dependabot、GitLab CI | 只確認存在，沒讀官方文件；Dependabot 的 cooldown 設定名稱需核對。 |
| MuseScore、ltrace 等 | GitHub 授權欄位回 NOASSERTION 或沒查，標 needs-review。 |

## 沒做完的部分

- 133 筆中 shell 工具與多數 H、K、L 延伸項目只有 `search` 等級，沒有逐一讀 README；差異主要在「旗標與陷阱」是通識，不是我這輪讀到的。
- 沒有實測：WSL 下 perf、bpftrace、gdb 對嵌入式 target、各工具的實際記憶體與速度。
- 沒找到：獨立第三方的文件解析比較（MinerU、Docling、Marker 同條件）、長篇小說一致性專用獨立工具、講義轉筆記工具、網頁去重與可信度專門工具、Hugging Face 授權驗證機制、Suno／MiniMax／TinyMusic 服務條款原文。
- 供應鏈事件來自搜尋摘要，未讀官方公告全文；2026-10 至 11 月沒有查到新事件，發佈前建議重查。
- Hyperframes 只沿用既有紀錄，沒有重讀 SKILL.md。

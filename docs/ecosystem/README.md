# 外部資源資料庫

改善框架、選工具、設計工作流程之前，先查這裡有沒有人研究過。每一筆記錄一個外部專案、skill、MCP、CLI、服務或文章：它是什麼、怎麼運作、授權、資料送往哪裡、限制、對這個框架有什麼用，以及查到哪個深度、哪一天查的。

它是研究紀錄，不是推薦名單，也不是安全背書。外部專案會變，真正採用前照 [tools 指引](../tools.md)與[審查清單](security.md)再查一次版本與資料流。

## 怎麼查

依關鍵字查（在框架根目錄執行，輸出有上限，適合讓 AI 先查再讀相關頁）：

```console
python -m agf.ecosystem find pdf 表格
python -m agf.ecosystem find kernel --limit 5
```

也可以直接用 jq 查 [entries.json](entries.json)：

```console
jq -r '.entries[] | select(.tier == 1) | "\(.id)\t\(.category)\t\(.license.label)"' docs/ecosystem/entries.json
jq '.entries[] | select(.runs == "local" and .category == "document-processing") | {id, resources}' docs/ecosystem/entries.json
```

要看說明與取捨，從下面的分類頁或[比較](#比較)進去。

## 分類

<!-- ecosystem:index -->
| 分類 | 項目 | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---|---|---|---|---|
| [AI coding 工作流程](categories/agent-workflows.md) | 14 | 2 | 9 | 2 | 1 |
| [記憶與 context 管理](categories/memory-context.md) | 13 | 0 | 2 | 8 | 3 |
| [程式理解與 code graph](categories/code-understanding.md) | 23 | 5 | 10 | 8 | 0 |
| [Agent skills 與規則](categories/agent-skills.md) | 14 | 2 | 5 | 5 | 2 |
| [MCP、CLI 與 API 整合](categories/mcp-cli-api.md) | 10 | 1 | 2 | 4 | 3 |
| [Shell 工具與格式轉換](categories/shell-utilities.md) | 44 | 0 | 12 | 20 | 12 |
| [文件解析、OCR 與 PDF](categories/document-processing.md) | 22 | 4 | 10 | 7 | 1 |
| [圖解與視覺化](categories/visualization.md) | 15 | 1 | 4 | 10 | 0 |
| [網頁研究、資料集與擷取](categories/web-research.md) | 14 | 2 | 7 | 5 | 0 |
| [CI/CD、資安與授權工具](categories/security-devops.md) | 23 | 1 | 9 | 12 | 1 |
| [評測、模型路由與可觀測性](categories/benchmark-evaluation.md) | 16 | 2 | 1 | 12 | 1 |
| [寫作、研究與 Podcast](categories/ai-writing.md) | 7 | 1 | 4 | 2 | 0 |
| [音樂與音訊](categories/ai-music.md) | 15 | 1 | 3 | 7 | 4 |
| [影片與動畫](categories/ai-video.md) | 8 | 2 | 4 | 2 | 0 |
<!-- /ecosystem -->

## Tier 1：優先研究

對框架有明顯價值、值得讀原始碼或試跑的項目。

<!-- ecosystem:tier1 -->
| 名稱 | 分類 | 授權 | 證據 | 對框架的價值 |
|---|---|---|---|---|
| [Claude Code 的 OpenTelemetry 監控](https://code.claude.com/docs/en/monitoring-usage) | [評測、模型路由與可觀測性](categories/benchmark-evaluation.md) | 可使用 | 讀文件 | Tier 1：用 console 或本機 Prometheus 接收、只開 metrics 與 api_request event、不開內容紀錄，就能量 skill、子代理與換模型的實際成本，不違反使用者的隱私決定。框架量測工具可讀這份輸出。 |
| [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | [程式理解與 code graph](categories/code-understanding.md) | 可使用（MIT） | 實際執行 | 結論同前次：不加 daemon、不預設 hooks。這次可借「coverage 查詢」與「CALLS／USAGE 分級」的用語，寫進 tools.md 對索引結果的判讀。 |
| [CodeGraph（codegraph-ai 版）](https://github.com/codegraph-ai/CodeGraph) | [程式理解與 code graph](categories/code-understanding.md) | 可使用（Apache-2.0） | 讀原始碼 | 對 kernel／韌體的 ops table 查詢有參考價值，可列入 Docker 試跑候選，觀察 find_implementors 在 drivers/ 的命中與漏抓。不建議預設接入（telemetry 預設開、資料庫全域）。 |
| [CodeGraph（colbymchenry 版）](https://github.com/colbymchenry/codegraph) | [程式理解與 code graph](categories/code-understanding.md) | 可使用（MIT） | 實際執行 | 沿用 docs/link-study.md 的結論（按需查、不預設全庫索引），這次新增 C 的 fn-pointer 與 `#ifdef` 能力，值得在 Docker 用 kernel 子目錄試跑。仍不預設接入，因為 telemetry 預設開、安裝是 curl \| sh。 S16 試跑（1.6.4，斷網、關 telemetry）：唯一解出 ops table 函式指標的工具（dev->ops->open 對到 uart_open、spi_open），137 MB、0.3 秒建圖。 |
| [Crawl4AI](https://github.com/unclecode/crawl4ai) | [網頁研究、資料集與擷取](categories/web-research.md) | 可使用（Apache-2.0） | 讀原始碼 | 網頁研究的首選候選（Apache-2.0、本機、MCP）。Docker 內跑 server，開 check_robots_txt 與限速，輸出 fit markdown＋來源 URL＋抓取時間。 |
| [Docling（IBM／LF AI & Data）](https://github.com/docling-project/docling) | [文件解析、OCR 與 PDF](categories/document-processing.md) | 可使用（MIT） | 實際執行 | 本輪文件解析試跑的首選：授權乾淨（MIT）、保留頁碼與座標、純本機。建議 Docker 內試跑，輸出 Markdown＋JSON（含 bbox）並與原始 PDF 並存。 S16 試跑：文字型 PDF 全對；JSON 每段有頁碼與 bbox，適合要引用頁碼時用；`--enrich-formula` 能把圖片公式轉成 LaTeX。 |
| [Firecrawl](https://github.com/firecrawl/firecrawl) | [網頁研究、資料集與擷取](categories/web-research.md) | 有條件（AGPL-3.0（主要）；SDK 與部分 UI 為 MIT） | 讀原始碼 | 需要大量網頁轉 Markdown 時的選項之一；本框架優先 Crawl4AI（Apache-2.0、純本機）。若用 Firecrawl 務必設 FIRECRAWL_CLOUD=off 並避免 MCP 雲端工具。 |
| [gh／glab（原生 CLI 取代 MCP）](https://github.com/cli/cli) | [MCP、CLI 與 API 整合](categories/mcp-cli-api.md) | 可使用（MIT） | 讀文件 | 維持框架現行規則；這次的新證據是 Playwright 官方也改推 CLI＋skill。 |
| [Joern](https://github.com/joernio/joern) | [程式理解與 code graph](categories/code-understanding.md) | 可使用（Apache-2.0） | 讀原始碼 | 不整合進框架；值得在 Docker 試跑一個小型 C 專案的 data flow 查詢，作為「code graph MCP 做不到的事」的對照。 |
| [Mermaid CLI（mmdc）與 Mermaid](https://github.com/mermaid-js/mermaid-cli) | [圖解與視覺化](categories/visualization.md) | 可使用（MIT） | 讀文件 | 維持基準。建議補兩點：（1）從 cflow／clang-uml／code graph 的輸出產生 .mmd，而不是讓 AI 憑記憶畫呼叫圖；（2）記下所用 Mermaid 版本與排版引擎。 |
| [MinerU（OpenDataLab）](https://github.com/opendatalab/MinerU) | [文件解析、OCR 與 PDF](categories/document-processing.md) | 有條件（Apache-2.0 加附加條款（MinerU Open Source License）） | 讀原始碼 | 試跑的第三候選：先關遙測（MINERU_TELEMETRY_DISABLED=1），走 basic／standard ONNX。重點觀察 doclib 的引用定位、中文表現。README 的 agent 安裝指令不要執行。 |
| [music-composition-skills（jtydhr88）](https://github.com/jtydhr88/music-composition-skills) | [音樂與音訊](categories/ai-music.md) | 有條件（MIT） | 讀原始碼 | 純創作輔助 skill 的代表；可借 ARR-SPEC 概念並接本機工具（music21／LilyPond 驗證和弦與小節）。不依賴任何雲端。 |
| [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | [文件解析、OCR 與 PDF](categories/document-processing.md) | 可使用（MPL-2.0） | 實際執行 | 掃描 PDF 的第一步：先 ocrmypdf --skip-text --sidecar out.txt in.pdf out.pdf，得到可搜尋 PDF 與逐頁文字，頁碼不會跑掉；結構化 Markdown 再交 Docling／Marker。 S16 試跑：掃描件的中文字全部認對，原頁面影像與頁碼不變；全形標點會變半形。 |
| [Open Notebook（lfnovo）](https://github.com/lfnovo/open-notebook) | [寫作、研究與 Podcast](categories/ai-writing.md) | 可使用（MIT） | 讀原始碼 | 「多來源整合保留引用＋轉 Podcast」的完整應用，適合在 Docker 內試跑；框架本身不整合，只作需求對照。啟動時務必改綁 127.0.0.1。 |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | [評測、模型路由與可觀測性](categories/benchmark-evaluation.md) | 可使用（MIT） | 讀原始碼 | 框架 evals/ 已有觸發與行為案例；promptfoo 的 claude-agent-sdk provider＋skill 斷言可以把「skill 該不該觸發」自動化，是 Tier 1 試跑候選（主 session 在 Docker 裡試，要先關 telemetry 與遠端生成）。 |
| [pstack（上游，cursor/plugins/pstack）](https://github.com/cursor/plugins/tree/main/pstack) | [AI coding 工作流程](categories/agent-workflows.md) | 可使用（MIT） | 讀原始碼 | 框架已有 debug-root-cause、review-change、trace-code；可借 correct 的「強制層級」與「規則—強制對照表」改進 maintenance 指引，借 why 的「只從紀錄答」補 read-research／trace-code。不建議整包安裝：自主開 PR／合併與使用者規則衝突，58 個 skill 也違反「少而專」。 |
| [pymupdf4llm](https://github.com/pymupdf/pymupdf4llm) | [文件解析、OCR 與 PDF](categories/document-processing.md) | 有條件（AGPL-3.0） | 實際執行 | 速度與記憶體是優點，但 AGPL 與無 OCR 限制多；研究對照用，不當框架依賴。 S16 試跑：文字型 PDF 每一項都對（表格、雙欄順序、中文、符號），1.3 秒、327 MB，是最快最省的。AGPL：框架只能當外部命令呼叫，不能 import。 |
| [Remotion](https://github.com/remotion-dev/remotion) | [影片與動畫](categories/ai-video.md) | 有條件（Remotion License（自訂）） | 讀原始碼 | 「Claude 寫場景程式 → 本機渲染 MP4」的主力工具之一；需先確認授權身份。在 Docker 內設定 REMOTION_TMP 與 --concurrency 試跑。 |
| [second-opinion（Trail of Bits skills）](https://github.com/trailofbits/skills/tree/main/plugins/second-opinion) | [AI coding 工作流程](categories/agent-workflows.md) | 有條件（CC-BY-SA-4.0） | 讀文件 | 直接對應框架 workflow 的「換模型審查」；可把這幾條契約用自己的話補進 review-change 或 workflow，不複製原文（CC-BY-SA）。 |
| [security-audit（Cloudflare）](https://github.com/cloudflare/security-audit-skill) | [Agent skills 與規則](categories/agent-skills.md) | 可使用（MIT） | 讀原始碼 | 與 review-change、debug-root-cause 的證據分級相近，可借三分法與「做不到隔離就不執行」的規則；不需要搬整套流程。 |
| [Serena](https://github.com/oraios/serena) | [程式理解與 code graph](categories/code-understanding.md) | 有條件（GPL-3.0-or-later） | 讀原始碼 | C／C++ 專案若已有 compile_commands.json，Serena 或直接用 clangd 是最接近「編譯器看到什麼」的選項。建議 Docker 試跑，重點看 clangd 背景索引完成前後的 references 差異。GPL 不影響本機使用。 |
| [Stickman Kino（dsauce）](https://github.com/dsauce/stickman-kino) | [影片與動畫](categories/ai-video.md) | 可使用（MIT） | 讀原始碼 | 本輪「技術報告 → 腳本 → 分鏡 → 動畫 → 旁白 → MP4」流程最完整的實例，且全本機、無付費 API；建議在 Docker 試跑 samples 的 chorus 或 hello-stickman，量時間與記憶體。 |
| [Trail of Bits Skills Marketplace](https://github.com/trailofbits/skills) | [Agent skills 與規則](categories/agent-skills.md) | 有條件（CC-BY-SA-4.0） | 讀原始碼 | 讀 testing-handbook 與 c-review 的方法；不安裝整個 marketplace。安裝個別 plugin 前要檢查 hooks 與 .mcp.json。 |
| [zizmor](https://github.com/zizmorcore/zizmor) | [CI/CD、資安與授權工具](categories/security-devops.md) | 可使用（MIT） | 讀文件 | 框架 CI 範本的首選掃描；pre-commit 與 CI 都可跑；輸出用 --format sarif 或 plain，限制量。 |
<!-- /ecosystem -->

## 比較

同類工具放在一起看，找出真正不同的技術方向：

- [記憶系統](comparisons/memory-systems.md)
- [程式理解工具](comparisons/code-understanding.md)
- [文件解析](comparisons/document-parsers.md)
- [網頁研究](comparisons/web-research.md)
- [AI coding 工作流程](comparisons/agent-workflows.md)

其他：[使用者提供的文章](articles.md)、[建議與待確認](recommendations.md)、[外部資源審查清單](security.md)、[授權判讀](license.md)。

## 欄位與標記

每一筆的欄位定義在研究規格 [SPEC.md](../../studies/ecosystem-2026-11/SPEC.md)；`python -m agf.ecosystem check`（`agf audit` 也會跑）檢查格式與表格是否和資料一致。幾個標記：

| 欄位 | 值 |
|---|---|
| `tier` | 1 優先研究；2 值得參考，設計可學但不一定引入；3 特定情境才用；4 暫不建議（維護差、重複、授權不明、資安風險或資源不符） |
| `evidence` | 查到的最深一級：實際執行（`ran`）、讀原始碼（`source`）、讀文件（`docs`）、只有搜尋摘要（`search`） |
| `license.label` | 可使用、有條件、需人工確認、不建議，判讀方式見[授權判讀](license.md) |
| `use` | `direct` 直接用、`integrate` 適合整合、`learn` 學架構、`borrow` 借鑑 skill 的做法、`study-only` 值得研究但不建議安裝、`needs-review` 需要人工確認 |
| `checked` | 最後一次人或 AI 查核內容的日期 |
| `github` | `refresh` 從 GitHub API 抓的事實：最後 push、是否封存、stars、GitHub 偵測的授權、抓取日期 |

`github` 是程式抓的，其他欄位是研究者讀了之後寫的；兩者分開，才知道哪些會自動更新、哪些要人重看。stars 只看熱度，不代表品質。

## 新增或更新一筆

1. 在 `entries.json` 加一筆或改既有的一筆，照 SPEC 的欄位寫；沒查到的寫 `null`，不要猜。
2. 有 GitHub repo 的，執行 `python -m agf.ecosystem refresh --id <id>` 抓維護狀態（需要已登入的 `gh`，只用唯讀 API）。
3. 執行 `python -m agf.ecosystem render` 更新各頁的表格，再跑 `python -m agf.ecosystem check`。
4. 值得多說的，在分類頁的表格下方寫一段：做法、限制、和其他項目差在哪。表格以外的文字是手寫的，`render` 不會動它。

定期維護：`refresh` 全部重抓一次，看哪些已封存或很久沒更新；`checked` 超過半年的 Tier 1、2 項目重看一次。

## 和其他紀錄的關係

- [link-study.md](../link-study.md)、[research.md](../research.md)、[memory-prompt-study.md](../memory-prompt-study.md)、[skillkit-study.md](../skillkit-study.md) 與 [studies/](../../studies/README.md) 是當時的研究紀錄，寫完不再更新；資料庫的項目在 `references` 指回它們。
- 這一輪（S16）的研究規格、子代理的原始筆記與草稿在 [studies/ecosystem-2026-11/](../../studies/ecosystem-2026-11/SPEC.md)。
- 框架要怎麼用這些研究結果，排在[分析報告第六輪](../analysis-2026-11.md#第六輪2026-11-21s16兩份需求的對照與路線圖)的路線圖。

## 限制

- 2026-11-21～22 第一次建立：三個子代理研究，主 session 核對、合併（[merge.py](../../studies/ecosystem-2026-11/merge.py) 列出主 session 改過的每一處）。238 筆裡，實際執行過 13 筆（文件解析與 C 程式理解的[試跑](../../studies/ecosystem-2026-11/trials/README.md)）、讀過原始碼 46 筆、讀過文件 92 筆、只有搜尋摘要 87 筆（多數是知名的 shell 工具）。作者自己公布的 benchmark 寫成作者自報。
- 資安事件只有標「已核對」的讀過一手來源，見[審查清單](security.md)的近期事件。
- 授權標記不是法律意見。
- 只查了公開資料；沒有使用者帳號內、公司內網或付費資料庫的資訊。

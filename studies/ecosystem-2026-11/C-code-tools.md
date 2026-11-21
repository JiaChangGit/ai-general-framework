# C：程式理解、skills、MCP 與視覺化（原始筆記）

子代理 C，2026-11-21。資料庫草稿在 [`drafts/C.json`](drafts/C.json)（58 筆）。依 [SPEC.md](SPEC.md) 的證據等級：`[CLONED]` 是 `git clone --depth 1` 到 `~/.cache/agf-ecosystem/repos/` 後讀程式結構；`[READ]` 是讀 README、官方文件或以 `curl` 讀單一原始檔；`[SEARCH-ONLY]` 只看搜尋摘要或 issue 標題。**沒有安裝、建置或執行任何候選工具**；作者自己公布的 benchmark 一律寫「作者自報」。

沿用的既有紀錄：`docs/link-study.md`（colbymchenry/codegraph f72c9d2、codebase-memory-mcp 612eee2、code-review-graph 115dccf）、`studies/research-2026-11/A-projects.md`（anthropics/skills 的 skill-creator）、`B-official.md`（skill 格式、MCP 2026-07-28 版、Claude Code 的「Prefer CLI tools」）。這些專案只補新版本與這次新關心的面向（C／kernel、telemetry、hooks）。

框架現況（對照基準）：`skills/trace-code` 要求從具體入口與情境追，不從全庫函式清單開始，區分靜態追蹤、runtime 觀察、教學假設；`docs/tools.md` 規定按問題取用 context、不預設建全庫 graph、空結果不能證明沒有 caller；圖解是 AI 寫 Mermaid 圖源、交 `mmdc` 渲染，每張最多 15 個節點。

---

## B. 程式理解、code graph、context packing

### 查了什麼、怎麼查、沒查到什麼

- **Clone 讀原始碼（7 個）**：Graphify（b582ad4）、CodeGraph 兩版（codegraph-ai ae4b2e5、colbymchenry 461a5d8）、codebase-memory-mcp（1111d9a）、Serena（7f7d624）、Repomix（f0bcc08）、Fastctx（db37324）。另以 `curl` 讀 Aider 的 `repomap.py`、`analytics.py`（5dc9490）與 Joern c2cpg 的 `Main.scala`。
- **讀文件**：Tree-sitter、ast-grep、Universal Ctags、GNU Global、cscope、clangd、Zoekt、Joern、CodeQL（含 CLI 授權）、GNU cflow、Coccinelle、sparse、Smatch、Bootlin Elixir、Codebase-Memory 論文摘要（arXiv 2603.27277）。
- **使用者回饋**：用 `gh api search/issues` 查各 repo 標題含 kernel／macro／clangd／function pointer／memory 的 issue（只看標題與狀態）；網頁搜尋 code graph MCP 的使用心得，找到的多是 dev.to 部落格，**沒找到 Reddit 或 Hacker News 的討論串**。其中一篇「I tested codegraph on Hono: the tool call savings reproduce, the cost savings don't」[SEARCH-ONLY] 只看到搜尋摘要（窄問題反而貴 20～43%、總費用約持平），全文因額度用完沒讀到。
- **沒查到**：Doxygen 手冊（只查 repo metadata，CALL_GRAPH 等選項名稱屬記憶，未驗證）；各工具對 function pointer 的實測準確率（沒有任何一方公布 kernel 上的 precision／recall）；Joern 對間接呼叫的處理文件。

### 研究重點逐項

**(1) AST／Tree-sitter／LSP／call graph 怎麼理解大型 codebase。** 這次看的 code graph 工具全部建在 tree-sitter 上（Graphify、兩個 CodeGraph、codebase-memory-mcp、Repomix `--compress`、Aider repo map、ast-grep）。tree-sitter 只給語法樹，不做名稱解析與前處理；呼叫邊是「名稱比對＋各語言的啟發式」。要接近編譯器語意，只有兩條路：接 LSP（Serena 包 clangd）或讀編譯資料庫（colbymchenry 版讀 compile_commands.json 的 include 目錄、Joern c2cpg 的 `--compilation-database`、clangd）。codebase-memory-mcp 的「Hybrid LSP」是用 C 重寫各語言的型別解析演算法，不是真的啟動 language server [CLONED]。

**(2) function call、data flow、control flow 的追蹤。** call graph 每個 code graph 工具都有；data flow 只有 codebase-memory-mcp（`DATA_FLOWS` 邊，含 arg→param 對應）與 Joern／CodeQL／Smatch 這類分析器真的做；control flow 只有 Joern（CPG 合併 AST、CFG、PDG）與 codegraph-ai 的付費 Pro（`security_control_flow`）。Graphify 明說它「Not a vector index」，但也沒有 data flow [CLONED]。

**(3) 跨檔案、跨 module 的 dependency graph。** 都有 include／import 邊。C 的 include 解析：Graphify 處理 `<liba/Bus.h>` 這類帶目錄的角括號 include；colbymchenry 版從 compile_commands.json 取 include 搜尋目錄 [CLONED]。cscope 與 GNU Global 有「誰 include 了這個檔」查詢 [READ]。

**(4) 讓 AI 只讀必要的原始碼。** 三種作法：查詢驅動（codegraph_explore、Graphify `query --budget`、codebase-memory-mcp `trace_path`）、焦點驅動的全域排序（Aider：以對話中的檔案與提到的名稱做 personalized PageRank，再二分搜尋裁到 map_tokens，預設 1024）[READ]、整包壓縮（Repomix）。Codebase-Memory 論文摘要提供少見的對照數據：graph 工具 token 少約 10 倍、工具呼叫少 2.1 倍，但答案品質 83% 對讀檔 agent 的 92% [READ]。colbymchenry 版作者也自報 session 結束時殘留在 context 的檢索內容比讀檔 agent 多約 80%（VS Code：67k 對 18k）[CLONED]。結論：省 token 與答得對是兩件事，框架「索引先定位、結論回原文」的規則仍成立。

**(5) Graph RAG、knowledge graph、vector search、BM25 的差別。**

| 方法 | 回答什麼 | 這次的例子 | 適合 | 不適合 |
|---|---|---|---|---|
| 結構圖（code graph） | 誰呼叫誰、誰 include 誰、改了影響誰 | 兩個 CodeGraph、codebase-memory-mcp、Graphify 的 AST 部分 | 有明確符號、要多跳關係 | 語意模糊的問題；被巨集或 function pointer 斷掉的邊 |
| Knowledge graph＋社群偵測 | 「這個 repo 有哪些子系統、哪些概念是樞紐」 | Graphify（Leiden／Louvain、god nodes） | 初次接觸陌生專案 | 精確追蹤；社群標籤會隨演算法切換整個重排 |
| BM25（關鍵字） | 名稱或字面相近 | codegraph-ai 的 symbol_search、colbymchenry 的 FTS5 | 找符號、錯誤訊息 | 詞不同義同 |
| 向量搜尋 | 意思相近 | codegraph-ai（BGE／jina-code 嵌入＋HNSW）、codebase-memory-mcp 的 `SEMANTICALLY_RELATED` | 「auth 怎麼做的」這類自然語言 | 精確關係；嵌入模型與設定一改就要重算（codegraph-ai 0.21 會為每個專案重嵌入一次） |
| Graph RAG | 先用圖找相關子圖，再交給 LLM 生成 | Graphify 的 `GRAPH_REPORT.md` 與 wiki 模式 | 跨文件的全局問題 | 要逐字引用或否定結論 |
| Trigram 文字索引 | 字串與 regex，跨大量 repo | Zoekt | 多 repo 毫秒級搜尋 | 單一 repo（rg 已足夠） |

記憶（跨 session 保存決策、除錯心得）是另一個問題：codegraph-ai 的 `memory_*` 工具、Serena 的 memory 檔、Graphify Cloud 的「always-on memory」都把它和 code graph 綁在一起賣，但兩者的過期條件不同（程式碼可以用雜湊判斷過期，記憶要靠人更正）。Context packing（Repomix）又是第三個問題：它不建圖，只決定「一次送多少原文」。

**(6) 索引過期與增量更新。** colbymchenry 版用 OS 檔案事件，存檔後 300ms debounce 同步，作者自報單檔約 0.3 秒 [CLONED]；codegraph-ai 用 FNV-1a 內容雜湊 [CLONED]；codebase-memory-mcp 由帳號層級 daemon 輪詢，**預設只監看 git 專案**，非 git 目錄不會自動更新 [CLONED]；Graphify 靠 `--update`、`watch`、git hook，README 自己提醒 `git pull` 後要手動 `graphify update .` [CLONED]；Aider 用檔案 mtime 快取 tags [READ]。前次已記錄 code-review-graph 只比 HEAD；這次看到的工具也沒有一個會在查詢結果上標示「未提交變更是否已入圖」。codebase-memory-mcp 的 `check_index_coverage` 是唯一明說「乾淨結果只代表沒有已記錄缺口，不代表完整」的工具。

**(7) 避免重複讀同一個檔案。** 兩種作法都會改變宿主行為：Graphify 的 PreToolUse hook 在 Read／Grep／`cat`／`sed -n` 前提示改用圖，`install --strict` 甚至拒絕讀已入圖的檔案，直到 agent 先查圖（30 分鐘內有效），compact 後再重置 [CLONED]；codebase-memory-mcp 的 hooks 預設開啟，在搜尋與讀檔後注入圖的內容並標出 coverage gap，README 說只加 context、不擋工具 [CLONED]；Fastctx 1.0 直接關掉 agent 內建的 shell [CLONED]。框架目前靠 context search／extract 與「續讀需要的區段」，不擋 Read；這些 hook 的作法不建議引入，因為「圖說沒有」時 agent 被擋住就無法回原文核對。

**(8) C/C++ 與 kernel 的適用性。** 見下一節。

### C／C++ 與 kernel：哪些工具處理得到、哪些會漏

| 問題 | 處理得到 | 部分處理 | 會漏 |
|---|---|---|---|
| `#ifdef` 與 Kconfig 造成的編譯分支 | clangd、Joern（`--compilation-database`、`--define`、`--with-preprocessed-files` 吃 .i 檔、`--print-ifdef-only` 先列出所有條件）、Smatch／sparse／Coccinelle（跟著 kernel 建置走） | colbymchenry 版：依檔內 `#define`、Makefile 的 `-DX`、CMake `option`、`AC_DEFINE` 做三值判斷，平台巨集與 `#if X > 1` 視為未知；codegraph-ai：只評估 `#if 0／1` | Graphify、codebase-memory-mcp、Repomix、Aider、cscope、ctags、GNU Global、Elixir（兩邊分支都收進來）；**沒有任何 tree-sitter 工具讀 Kconfig 的 .config 或 autoconf.h** |
| 巨集 | clangd、Joern（真的跑前處理）；Coccinelle 依編譯時的 include 選項 | colbymchenry 版處理 `#define sds hisds` 改名、macro 產生的命令表；codegraph-ai 比對已知 kernel 巨集清單（__init、__user、EXPORT_SYMBOL 等）但不展開；codebase-memory-mcp 有 Macro 節點與 typedef 鏈 | export macro 夾在 class 與名稱間（codebase-memory-mcp #1989、#2881 open）、CUDA 的 macro kernel（Graphify #3911 open）、macro 包住回傳型別（colbymchenry #2470，已修） |
| function pointer／ops table／callback | colbymchenry 版：以（struct 型別、fn-pointer 欄位）為鍵，連 positional／designated initializer、`x->fn = f` 的註冊與 `p->fn()` 的呼叫，含函式指標陣列與 macro 建表，邊標 `heuristic`；codegraph-ai：`.ndo_open = foo_open` 記成帶 struct_type／field_name 的邊，`find_implementors` 查詢 | Graphify：callback 當參數傳遞時標 `indirect_call`（INFERRED）；trailmark：標 `uncertain` 邊並允許在 `.trailmark/links.toml` 手動宣告 | Graphify 的 C 設定只有 function_definition、preproc_include、call_expression；Aider、ctags、cscope、cflow、Doxygen 都看不到間接呼叫 |
| 編譯資料庫 | clangd、Serena（包 clangd，會下載固定版本並必要時改寫 compile_commands.json）、Joern、colbymchenry 版（只取 include 目錄）、clang-uml | CodeQL build-mode none（推測旗標，官方說可能較不準） | 其他 tree-sitter 工具 |
| kernel 規模 | 作者自報：colbymchenry 版 7 萬檔在 2 核／6 GB 12 分鐘內；codebase-memory-mcp 3 分鐘 | Elixir 索引 1800 個 tag 約 15 小時；Smatch 跨函式資料庫 2～3 小時 | Joern 全量 CPG 在 8 GB WSL 不現實 |

實際判斷：要回答「這個 config 下誰會呼叫這個函式」，可靠的順序是 (a) 建置一次產生 compile_commands.json（kernel 用 `scripts/clang-tools/gen_compile_commands.py`，見 [lore 原始 patch](https://lore.kernel.org/lkml/20181218224907.1274-1-tmroeder@google.com/) [SEARCH-ONLY]），(b) 用 clangd／Serena 查 references，(c) 用 rg 搜 ops 欄位名補 function pointer，(d) 用 code graph 的 heuristic 邊當候選。任何工具回傳「沒有 caller」都不能拿來刪函式（沿用 link-study 結論）。Serena issue #2191（clangd 背景索引完成前 references 為空，open）[SEARCH-ONLY] 是具體反例：工具剛啟動時的空結果是「還沒建完」，不是「沒有」。

### 程式理解工具比較

欄位依使用者指定；「有」只代表讀到的原始碼或文件有此能力，不代表測過準確度。

| 工具 | AST | Tree-sitter | LSP | Graph DB | Vector DB | Dependency | Call graph | Data flow | 增量索引 | Token 消耗 | C／kernel | 本機與隱私 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Graphify | 有 | 有 | 無（SCIP JSON 可匯入） | graph.json＋networkx；可推 Neo4j／FalkorDB | 無 | import／include | 有（EXTRACTED／INFERRED） | 無 | `--update`、watch、git hook | query 預設 budget 2000；docs 的 semantic pass 很貴 | 弱：C 只三種節點 | 程式碼本機；文件送 LLM（依 env 自動選 provider）；hosted Cloud MCP 另計；CLI 會印 Cloud 廣告 |
| CodeGraph（codegraph-ai） | 有 | 有 | 自己就是 LSP server | RocksDB | HNSW＋BGE | 有 | 有（含 ops struct 邊） | 只在付費 Pro | FNV-1a 雜湊 | 42 工具全開很重，`--profile core` 8 個 | 中：kernel 模式、ops table；`#ifdef` 只 0／1 | 本機，DB 在 ~/.codegraph；**PostHog telemetry 預設開** |
| CodeGraph（colbymchenry） | 有 | 有（Rust kernel） | 無 | SQLite（FTS5） | 無 | 有（讀 compile_commands 的 include） | 有（fn-pointer 合成） | 無 | OS 檔案事件 | 作者自報少 62% token，但殘留 context 多 80% | 中高：fn-pointer、`#ifdef` 三值、macro 改名；無 Kconfig | 本機；**匿名統計預設開**、每日查新版 |
| codebase-memory-mcp | 有 | 有（164 文法） | C 重寫的型別解析 | SQLite | MinHash＋語意相近邊（非向量庫） | 有（含 IaC、跨服務） | 有（CALLS／CALL_REFERENCE／USAGE 分級） | 有（DATA_FLOWS） | daemon 輪詢，預設只 git 專案 | 論文：少約 10 倍 token、品質 83% 對 92% | 中：macro、typedef；export macro 有 open issue | 本機、無 telemetry；hooks 與 daemon 預設開 |
| Repomix | `--compress` 才用 | 有 | 無 | 無 | 無 | 無 | 無 | 無 | watch 模式重打包 | 整包，隨 repo 線性成長 | 不適用（`#ifdef` 兩邊都打包） | CLI 本機；網站版上雲；MCP 不加 `--sandbox` 可讀任意路徑 |
| Aider repo map | 有 | 有 | 無 | networkx（記憶體） | 無 | 檔案層級 | 名稱層級 | 無 | mtime 快取 | 固定預算（預設 1024） | 弱：同名識別字連線 | 地圖隨 prompt 送模型；analytics 需同意 |
| Serena | 由 LS 提供 | 無 | 有（約 70 種 LS） | 無 | 無 | 由 LS | references／call hierarchy（由 LS） | 無 | 由 LS | 符號層級讀寫，省整檔讀取 | 高（clangd＋compile_commands）；背景索引前回空 | 本機、未見 telemetry；會下載 LS；GPL-3.0+ |
| ctags／cscope／GNU Global | 模糊解析 | 無 | 無 | 檔案索引 | 無 | cscope／Global 有 include 查詢 | cscope 有 | 無 | Global 支援增量 | 極低，輸出就是 file:line | 低～中：不看 `#ifdef`、無間接呼叫 | 本機 |
| clangd | 有（Clang） | 無 | 有 | 背景索引 | 無 | 有 | call hierarchy | 無 | 有 | 低 | 高，但只對應一組 config | 本機 |
| Joern | 有（Eclipse CDT） | 無 | 無 | flatgraph（CPG） | 無 | 有 | 有 | 有（CPG 查詢） | 無（重建） | 查詢結果小，建圖重 | 高：可吃 compile_commands、.i 檔 | 本機；sudo 安裝腳本 |

### 各項目重點（未在表格中的發現）

- **Graphify** [CLONED]：stars 約 15 萬（2026-04 才建立），成長極快，不代表品質。`skill.md` 的 Step 1 會在找不到套件時自動 `uv tool install --upgrade graphifyy` 或 `pip install … --break-system-packages`；description 是「Use for any question about a codebase」。README 說查詢預設記到 `~/.cache/graphify-queries.log`，但 `querylog.py` 在 #1797 後已改為 opt-in，文件落後程式。值得借：名稱有多個候選時拒答並列出候選（exit 3）、找不到回 4；path 的信心取最弱一跳；`.graphifyrc` 宣告 `.h` 是 C 還是 C++。
- **兩個 CodeGraph 要分清**：codegraph-ai/CodeGraph（Andrey Vasilevsky，Rust，Apache-2.0，stars 約 167，有 VS Code／JetBrains 外掛與付費 Pro）與 colbymchenry/codegraph（TypeScript＋Rust kernel，MIT，stars 約 7.8 萬，框架 11-09 讀的是這個）。程式碼、工具名、資料庫都不同。
- **colbymchenry 版的 benchmark 方法**值得記：作者發現對照組在 26/28 次會從 PATH 找到 CLI 偷用，之後兩組都用 PreToolUse hook 擋 CLI 才重測（2026-08-05，Opus 4.8，每組 4 次取中位數）。這是評估任何 code 工具時都要做的隔離。
- **Fastctx**：見「待確認」。

---

## C. Agent skills

### 查了什麼、怎麼查、沒查到什麼

- **Clone 讀 SKILL.md、scripts、hooks、.mcp.json**：cloudflare/security-audit-skill（c1c8a8c）、hardikpandya/stop-slop（8da1f03）、dickwu/apple-design-skill（91e1566）、mhattingpete/claude-skills-marketplace（b5b34bc）、veelenga/claude-mermaid（802b3d3）、trailofbits/skills（149d7b2，99 個 SKILL.md，抽讀 c-review、trailmark，掃描全部的安裝指令、hooks 與 .mcp.json）、anthropics/skills（e4bb5d9）、openai/skills（49f948f）、vercel-labs/skills CLI（57217cf）。`curl` 讀 davila7 的 clean-code SKILL.md（2fbe867）與 ylongw/embedded-review SKILL.md（bb500aa）。
- **網站**：skillsdirectory.com 首頁、`/security/methodology`、三個種子 skill 頁；skills.sh 首頁與 `/audits`；Vercel 的 AGENTS.md vs skills 文章；agnix README。
- **延伸搜尋**：以 `gh api search/repositories` 查 Linux kernel、embedded、Android、accessibility、Rust 的 skill。**沒找到** Linux kernel 專用、品質可辨的 skill（kernel 相關只有 trailofbits 的 c-review 明說不適用、cloudflare 的 MEMORY-SAFETY-AND-BINARY.md 有 kernel 一節）。Android（mmiani、lennonpetrick）、accessibility（Community-Access/accessibility-agents、plugin87/ux-ui-agent-skills）、Rust（morganlinton/BeautifulRust）、MCU（alexex1993/mcu-skills、AmethystLuna/embedded-workbench）只看到 repo 名稱與描述 [SEARCH-ONLY]，未收進資料庫。
- **沒做**：iOS、frontend、data analysis、quant、DevOps／SRE／MLOps、technical writing、research 各領域的 skill 只停在搜尋階段，沒有逐一讀；「token optimization」類（rtk、caveman）已在 A-projects.md 研究過，沒有重讀。

### SKILL.md 安全檢查

檢查項目：可疑指令、要求讀秘密、偷偷執行 shell、下載不明檔案、隱藏的 MCP 或 API 依賴、telemetry。只寫有發現的項目；沒列出的檢查項就是沒發現。

| Skill | 發現 | 嚴重度判斷 |
|---|---|---|
| Graphify `skill.md` | 找不到套件時自動 `uv tool install` 或 `pip install --break-system-packages`；支援 `/graphify <GitHub URL>` 自動 clone；有 `GEMINI_API_KEY` 時把文件送 Gemini | 中：未經詢問安裝 |
| trailmark（trailofbits） | 「MANDATORY: If trailmark is not found, install the CLI before doing anything else」＋ `uv tool install trailmark`；把「手動讀原始碼」列為要拒絕的藉口 | 中：強制安裝、強推工具 |
| trailofbits zeroize-audit | `.mcp.json` 用 `uvx --from git+https://github.com/oraios/serena`，每次啟動跑 Serena 主分支，沒有釘 commit | 中：隱藏且未釘版的 MCP 依賴 |
| trailofbits fp-check | 全域 Stop／SubagentStop prompt hook（matcher `*`），裝了之後每次停止都跑 LLM 檢查 | 低～中：費用與延遲，非 fp-check 對話回 ok |
| trailofbits gh-cli | SessionStart 把 PATH shim 寫進 CLAUDE_ENV_FILE，攔截 curl／wget；SessionEnd 清 clone | 低：改變 shell 環境，但目的明確 |
| davila7 clean-code | 「Verification Scripts (MANDATORY)」要求執行 `~/.claude/skills/<其他 skill>/scripts/*.py` 共十多支，這些腳本不在本 skill 內 | 中高：隱藏相依，同名 skill 來源不明就是任意執行 |
| mhattingpete git-pushing | 寬鬆自動觸發（「save to github」「完成功能想分享」），腳本 `git add .` 後 commit＋push | 高：遠端副作用＋可能推送秘密 |
| mhattingpete conversation-analyzer | 讀 `~/.claude/history.jsonl`（全部對話紀錄） | 中：私人資料 |
| claude-mermaid | `.mcp.json` 用 `npx -y claude-mermaid`，未釘版；allowed-tools 預先允許 Artifact | 低～中：供應鏈 |
| embedded-review | diff 超過 100 行或碰到關鍵路徑時，預設把完整 diff 經 ACP 送給 Codex | 中：程式碼送到第二家服務 |
| Context7 skills | description 涵蓋「任何函式庫問題」；查詢內容送 context7.com | 中：見 MCP 段的 ContextCrush |
| cloudflare security-audit | 無發現；反而規定執行目標程式必須在 OS 層 sandbox、不得安裝相依 | 範例 |
| stop-slop、apple-design、openai yeet／security-threat-model | 無發現 | — |

觀察：**最常見的風險不在 SKILL.md 的文字本身，而在它指向的東西**（腳本、其他 skill 的路徑、.mcp.json、hooks、未釘版的 `npx -y`／`uvx git+`）。

### Skill 目錄網站能不能信

- **skillsdirectory.com** [READ]：methodology 頁明說等級**只依 SKILL.md**，「Scripts and other files bundled with a skill … don't count toward the grade」，Pro 才掃全部檔案。方法是靜態樣式比對，扣分數值不公開；首頁說 10 類威脅、120 個樣式，methodology 頁只列 8 類且沒提樣式數。實例：clean-code（要求執行其他目錄的腳本）拿 A 100/100；apple-design A 100/100（「Pro scans all 5 files」）。
- **skills.sh**（Vercel）[READ]：排行依安裝數，安裝數來自 CLI telemetry（`https://www.skills.sh/tele/t`）；`/audits` 只列約 50 個 skill，合併 Gen Agent Trust Hub、Socket、Snyk，同一個 skill 可能 Gen 標 Safe、Snyk 標 Critical，頁面不說明方法 [CLONED CLI、READ 網站]。CLI 文件說非 GitHub 來源可能把來源與 skill 識別字帶進 telemetry。
- **agnix** [READ]：設定檔 linter，自稱 763 條規則；但 README 引用 Vercel 研究「invoke at 0%」，原文是「56% 的案例 skill 從未被呼叫」，引用不精確。
- 結論：安全分數與安裝數只能當線索，跟 tools.md 對 MCP registry 的判斷一致。檢查 skill 時要讀全部檔案，並追蹤被引用的路徑與套件。

### Skill 怎麼組合、觸發、按需載入，怎麼避免衝突

- **觸發不可靠是常態**：Vercel 的 Next.js 16 eval（2026-01-27，作者自報）中，56% 的案例 skill 從未被呼叫，預設 skill 的通過率與沒文件相同（53%）；加明確指示 79%；把壓縮過的文件索引放 AGENTS.md 則 100% [READ]。另一個發現：「You MUST invoke the skill」讓 agent 只看文件、忽略專案脈絡，「先探索專案再呼叫 skill」較好。這支持框架「關鍵判斷放常駐規則、細節按需讀」。
- **有副作用的動作要窄觸發**：openai 的 yeet「Use only when the user explicitly asks…」對比 mhattingpete git-pushing 的寬鬆自動觸發 [CLONED]。cloudflare 把同一個 skill 分成 guidance 與完整流程兩種模式，模稜兩可時只問一個問題 [CLONED]。
- **衝突的來源**：優先權字眼（clean-code 的 `priority: CRITICAL`、MANDATORY、🔴 VIOLATION）、絕對規則（stop-slop 的「所有副詞」「不要被動語態」）、工具搶占（Graphify hook 擋 Read、trailmark 要求先裝工具、Fastctx 關掉內建 shell、Context7 與 Graphify 的 description 都想吃下所有相關問題）、全域 hook（fp-check 的 matcher `*`）。Graphify README 自己提醒：同時用 CLI skill 與 MCP 時要選一條主要查詢路徑，不要把兩段無條件指示都貼進 AGENTS.md [CLONED]。
- **組合**：trailofbits 用 plugin 內依賴（genotoxic 內部呼叫 trailmark）、c-review 用 Claude Code 的 Workflow 工具一次分派 4～14 個 agent [CLONED]。代價是費用與「安裝一個 plugin 會連帶裝上 hooks 與 MCP」。

### 值得借鑑的 skill（Tier 1／2）

- **cloudflare/security-audit**：confirmed／needs_validation／rejected 三分法（needs_validation 必須寫出缺哪個事實、不給嚴重度）；做不到隔離就不執行目標程式；多次執行可累加但不把過期工作算成已涵蓋。
- **trailofbits testing-handbook 與 c-review**：fuzzing harness、字典、障礙排除的按需 skill；c-review 把「finding 必須在這個範圍」與「可以讀來判斷可達性的範圍」分開。注意 c-review 明說不適用 kernel 與無 libc 的韌體。
- **embedded-review**：韌體 review 的關鍵路徑清單（ISR／DMA、crypto、NFC、boot／OTA、debug 介面、更新完整性），但不採預設跨廠商送 diff。

---

## D. MCP、CLI、API

### 查了什麼、怎麼查、沒查到什麼

Clone：Playwright MCP（2337aff）、draw.io MCP（a7d1ead）、Context7（b1e3611）。`curl` 讀 README：GitHub MCP Server（9a72d8d）、MCP Registry（5fa0c6d）與其 FAQ、MCP Apps／ext-apps（ea3e9d0）。網頁：ContextCrush 廠商說明 [READ]、CVE-2026-75130 [SEARCH-ONLY]。沒查：Firecrawl、Browser Use（另一子代理負責）；MCP Apps 規格的安全章節；Claude Code 終端是否支援 MCP Apps。

### 各 MCP 的 tools、transport、認證、權限、資料流向

| MCP | Tools | Transport | 認證 | 權限面 | 資料流向／外部依賴 |
|---|---|---|---|---|---|
| Playwright MCP | 約 72 個 browser_*（含 cookie／storage 讀寫、`browser_evaluate`、`browser_run_code_unsafe`） | stdio；`--port` 開 HTTP | 無（瀏覽器 profile） | **預設持續性 profile**（存登入）；`--extension` 接使用者的 Chrome；`--allowed-origins` 官方說不是安全邊界 | 本機瀏覽器 → 任意網站；網頁內容是 prompt injection 來源 |
| draw.io MCP | create_diagram、search_shapes、get_drawio_reference、create_semantic_diagram | hosted HTTP（mcp.draw.io）或本機 | 無 | 低 | 官方逐項揭露：hosted 會收到圖；Tool Server 用 URL fragment；plugin 本機，但 Claude Code plugin **綁了 hosted App Server**；渲染載入 diagrams.net 程式碼、icons 搜尋字送 icons.diagrams.net |
| Context7 | resolve-library-id（query、libraryName）、query-docs（libraryId、query、version） | hosted HTTP 或本機 stdio | Bearer API key（`ctx7 setup` 走 OAuth） | 回傳第三方文件給 agent | 問題文字送 context7.com；後端私有；**ContextCrush／CVE-2026-75130**：社群登錄的「Custom Rules」原樣送給 agent，PoC 讀 .env 並外送；2026-02-23 伺服器端修正，廠商自承風險未消除 |
| GitHub MCP | 約 120 多個，依 toolset 分組 | 遠端 HTTP 或本機 stdio（Docker） | OAuth 或 PAT | `--read-only` 優先於 `--tools`；`--lockdown-mode` 官方說只是內容過濾、不是授權邊界 | GitHub API；issue／PR／評論是不可信輸入 |

### 哪些能力直接用 CLI 比包成 MCP 好

- **新證據**：Playwright MCP 的 README 開頭就建議 coding agent 改用 microsoft/playwright-cli＋skills，理由是 CLI 不用載入大型 tool schema 與冗長的無障礙樹；MCP 只在需要持續瀏覽器狀態的長迴圈才值得 [CLONED]。Context7 也同時提供 `ctx7` CLI＋skill 模式 [CLONED]。這和 Claude Code 官方成本文件「Prefer CLI tools when available」（B-official.md 已讀）一致。
- **CLI 較好**：有成熟 CLI（gh、glab、git、rg、mmdc、clangd 的 `clangd --check`、cscope／global）、輸出可用 `--json`／`--jq` 精簡、宿主有 shell 與權限確認。
- **MCP 較好**：宿主沒有 shell（網頁版對話）、需要持續狀態（瀏覽器 session）、需要宿主層的工具權限與逐次確認、需要 MCP Apps 的內嵌 UI（draw.io、Excalidraw）。
- **官方 MCP Registry** 只解決發現與 namespace；惡意 server 的處理是向 npm／PyPI 檢舉再開 issue，沒有看到登錄時的安全掃描 [READ]。
- **MCP Apps**：tool 宣告 `ui://` 資源，host 在 sandboxed iframe 顯示，UI 可透過 host 呼叫其他 tool [READ]；對 CLI 為主的框架暫時不需要。

---

## F. 視覺化

### 查了什麼、怎麼查、沒查到什麼

讀文件：mermaid-cli README（最新 release 12.2.0，2026-11-02）、mermaid.js.org flowchart 頁、Graphviz 的 URL 屬性頁、PlantUML LICENSES.md、D2 README、Kroki README、Structurizr README、elkjs README 與 LICENSE、Cytoscape.js／Three.js／Observable Plot README、clang-uml README、excalidraw-mcp README。claude-mermaid、draw.io MCP 是 clone。沒查：Doxygen 手冊（只有 metadata）、TALA（D2）的授權條款、Excalidraw 主 repo、Graphviz 授權頁。

### 以框架現行作法為基準的評估

框架現在：AI 寫 `.mmd`、`mmdc` 渲染、最多 15 節點、`diagram transitions` 從表格統計狀態轉移。主要缺口在「圖從哪裡來」：目前呼叫圖靠 AI 讀原始碼後手寫。

- **從原始碼自動產生圖**：clang-uml（C++ 的 class／sequence／include 圖，輸出 Mermaid／PlantUML，YAML 設定可進 repo）[READ]、GNU cflow（C 的正反向呼叫樹，文字帶 file:line）[READ]、Doxygen call graph（未驗證細節）、Graphify `export callflow-html`（Mermaid 架構／呼叫流程 HTML，git commit 時自動重建）[CLONED]、codebase-memory-mcp 的 CBM Lens [CLONED]。建議：呼叫圖由工具輸出（cflow、clangd call hierarchy、code graph 的 callers／callees）轉 `.mmd`，AI 只負責挑範圍與標註，不憑記憶畫邊。
- **程式改了怎麼同步**：產生式工具重跑即可（clang-uml、cflow、Doxygen、Graphify hook）；手寫圖要記下來源 commit。D2 `--watch` 與 claude-mermaid 的 live reload 只同步「圖源→圖片」，不同步「程式→圖源」。
- **節點對回檔案與行號**：Graphviz 的 URL／href 屬性在 SVG 輸出可點（node、edge、cluster 都可掛）[READ]；Mermaid 的 `click nodeId href` 需要 `securityLevel: 'loose'`，strict 時停用 [READ]；clang-uml 的 SVG 可帶連到原始碼的互動連結 [READ]；Graphify 的 `explain` 回傳 `Source: routing.py L2210` [CLONED]。靜態圖交付時，框架現行「圖外附對照表」仍是最穩的作法。
- **新變化**：Mermaid flowchart 現在預設用 ELK 排版（舊的 defaultRenderer 已移除，要舊行為寫 `layout: dagre`）[READ]；框架樣板若依賴 dagre 的外觀，換版後要重看。
- **其他工具的定位**：D2（單一 Go binary，不需要 Chromium，可當 mmdc 裝不起來時的替代）、PlantUML（可選 MIT／Apache 授權版本）、Structurizr（C4 一份模型多個視圖）、Kroki（多種圖語言的渲染服務，對個人框架太重）、ELK（只算版面）、Cytoscape.js（互動式 dependency graph）、Three.js（3D 好看但不好讀，不建議用於程式理解）、Observable Plot（表格數據圖，timeline／Gantt 的數據來源是 log 時比 Mermaid gantt 精確）、draw.io MCP（要給人改的可編輯架構圖）、Excalidraw（草圖）。

---

## 待確認的名稱

**FastCtx**（使用者沒有來源）：

1. **yc-duan/fastctx**（最可能，stars 約 1,556，Apache-2.0）[CLONED]。注意產品在 1.0 大轉向：pre-1.0（fork sageri/fastctx 保留 v0.2.6）是「Fast, context-efficient repository tools for AI agents」的 MCP，提供 inspect_local_file、grep、glob、replace、run 等結構化工具；1.0 起變成跨機器執行平台，只給 agent 一個 `run` 工具，經自架 Hub 在多台機器上執行 bash，Connect 時會關掉 Claude Code 等 13 個 agent 的內建 shell、改寫全域 CLAUDE.md／AGENTS.md，原始碼有以 `--permission-mode bypassPermissions` 啟動背景 Claude Code 的路徑。若使用者指的是這個，要先問他要的是 pre-1.0 的 repo 工具還是 1.0 的遠端執行。
2. **Cirius1792/fastcontext**（FastContext，以微軟論文為基礎的唯讀探索子代理，回傳 file-line 引用）[SEARCH-ONLY]。
3. **codeberg.org/jer-gremlin/fast-ctx**（以 rg 為基礎、回傳引用的搜尋外掛）[SEARCH-ONLY]。
4. **fast-context-mcp（npm，SammySnake-d）**：包裝 Windsurf 反向工程的 SWE-grep 協定，依賴 Windsurf API [SEARCH-ONLY]，有服務條款與帳號風險。

---

## 發現的資安疑慮（摘要）

1. **Fastctx 1.0**：關閉 agent 內建 shell、以 bypassPermissions 啟動背景 Claude Code、跨機器執行與帳號分享；Hub 能看到所有流量。
2. **Context7 ContextCrush（CVE-2026-75130）**：第三方文件服務是 prompt injection 通道；廠商修正後仍自承風險存在。
3. **未經詢問的安裝**：Graphify skill、trailmark skill；`curl … | sh` 安裝（colbymchenry codegraph）、`sudo ./joern-install.sh`。
4. **未釘版的執行**：trailofbits zeroize-audit 的 `uvx --from git+…serena`、claude-mermaid 的 `npx -y`。
5. **隱藏相依**：davila7 clean-code 要求執行其他 skill 目錄的腳本，且仍拿到 skillsdirectory A 100/100。
6. **寬鬆觸發的遠端副作用**：mhattingpete git-pushing（`git add .` 後 push）。
7. **私人資料**：mhattingpete conversation-analyzer 讀全部對話紀錄；embedded-review 預設把 diff 送第二家模型；Playwright MCP 預設持續性 profile。
8. **預設 telemetry**：codegraph-ai（PostHog，npm 包裝與 VS Code 預設開）、colbymchenry codegraph（匿名統計＋每日更新檢查）、skills CLI（skills.sh）、Context7 CLI。沒有 telemetry 的：codebase-memory-mcp（README 聲明）、Graphify（未找到程式）、Serena（未找到）。
9. **改變宿主行為的 hooks**：Graphify strict 模式擋 Read／Grep；codebase-memory-mcp hooks 預設開；trailofbits fp-check 全域 Stop hook。

---

## 建議主 session 在 Docker 試跑

樣本建議（公開 C 專案，由小到大）：**redis**（有 macro 建的命令表、function pointer 派發，colbymchenry 的 synthesizer 註解直接拿它當例子）、**Linux kernel 的單一子目錄**（例如 `drivers/net/ethernet/intel/e1000e/`：大量 `net_device_ops`、`#ifdef CONFIG_*`；先 `make defconfig` 並產生 compile_commands.json）、**Zephyr 或 FreeRTOS 的一個 sample**（貼近韌體，有 Kconfig）。

| 試跑對象 | 觀察什麼 |
|---|---|
| colbymchenry/codegraph（`--no-telemetry` 或 `DO_NOT_TRACK=1`） | e1000e 的 `.ndo_open` 等 ops 欄位：callers／callees 是否接到實作、邊是否標 heuristic；`#ifdef CONFIG_X` 未啟用時的分支是否被排除；8 GB 記憶體下的索引時間與峰值；存檔後的同步時間 |
| codegraph-ai/CodeGraph（`CODEGRAPH_TELEMETRY=off`、`--graph-only`） | `find_implementors` 對同一組 ops 的結果，與上者比對；kernel 模式解析失敗的檔案數 |
| codebase-memory-mcp（`install --no-hooks`） | `check_index_coverage` 對 kernel 子目錄報出的缺口；CALLS 與 USAGE 的分布；daemon 的資源用量 |
| Serena＋clangd（用 kernel 產生的 compile_commands.json） | 剛啟動與背景索引完成後的 references 差異（對應 issue #2191）；同一函式在不同 config 下結果是否不同 |
| Joern（c2cpg 加 `--compilation-database` 或 `--with-preprocessed-files`） | 在 redis 上做一次 data flow 查詢（例如命令參數是否流到某個 memcpy），記錄建圖時間與記憶體；`--print-ifdef-only` 的輸出 |
| （選）Graphify `--code-only`，`GRAPHIFY_BACKEND=none` | 當作「C 支援最弱」的對照組，看同一組 ops 漏掉多少 |

共同要記錄：工具版本／commit、建圖時間、峰值 RAM、索引大小、是否有對外連線（封網跑一次）、對 3～5 個固定問題的答案與人工核對結果（不要只看 token）。

---

## 沒做完的部分

- 種子都已收錄；延伸的領域 skill（iOS、frontend、data、quant、DevOps／SRE／MLOps、technical writing、research）只做到搜尋，沒有收進資料庫。
- 「Hono 實測」部落格、HN／Reddit 的使用者討論沒有讀到全文（WebFetch 額度在最後用完）。
- 沒有讀 Doxygen 手冊、MCP Apps 規格的安全章節、TALA 授權、Graphviz 授權頁。
- code-review-graph 沒有重讀（沿用 link-study 結論）。
- 2026 年其他新 code graph MCP（zzet/gortex、CodeBendKit/codeseek、Graphicle-AI/graphicle、AxiomCodeAI/axiomcodegraph、win4r/codebase-memory-mcp-pro 等）只看到 GitHub 搜尋列表 [SEARCH-ONLY]，未收錄。

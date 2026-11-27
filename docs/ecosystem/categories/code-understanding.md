# 程式理解與 code graph

追執行路徑、找呼叫關係與 data flow、把程式碼打包給模型的工具。程式理解、記憶、RAG 與 context packing 是不同的問題，比較頁先把它們分開。C 與 kernel 特別要看巨集、`#ifdef` 與函式指標：這一輪用答案已知的小專案試跑了七個工具，沒有一個全對，錯的地方還互補。比較、試跑與建議的取證順序見[程式理解工具比較](../comparisons/code-understanding.md)。

<!-- ecosystem:table code-understanding -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | MCP | 1 | 可使用（MIT） | 2026-11-21 | 實際執行 | 原生 C 寫的 MCP server，把 repo 解析成 SQLite 知識圖，提供 17 個 MCP 工具（搜尋、trace_path、影響範圍、check_index_coverage 等），也能用 CLI 查。這次版本擴充到 IaC（Kubernetes、Helm、Terraform）、跨服務連線、Smart CI 測試選擇，並附 CBM Lens 視覺化。 |
| [CodeGraph（codegraph-ai 版）](https://github.com/codegraph-ai/CodeGraph) | MCP | 1 | 可使用（Apache-2.0） | 2026-11-15 | 讀原始碼 | 單一 Rust binary 同時提供 MCP（stdio）與 LSP，用 tree-sitter 解析 38 種語言建 call／import 圖，加上 BGE 向量與 BM25 混合搜尋、記憶與文件索引，共 42 個社群版 MCP 工具，另有付費 Pro 的資安工具。和 colbymchenry/codegraph 是不同作者、不同程式碼的專案。 |
| [CodeGraph（colbymchenry 版）](https://github.com/colbymchenry/codegraph) | MCP | 1 | 可使用（MIT） | 2026-11-20 | 實際執行 | 把 repo 建成 SQLite（FTS5）符號與關係圖，經 MCP 的 codegraph_explore 等工具一次回傳相關原始碼、呼叫路徑與影響範圍。這次版本把 20 種語言的解析移到 Rust native kernel，並加強 C／C++ 的 function pointer 與 macro 解析。 |
| [Joern](https://github.com/joernio/joern) | 專案 | 1 | 可使用（Apache-2.0） | 2026-11-21 | 讀原始碼 | 產生 code property graph（CPG：AST＋控制流＋資料流合在一張圖）並用 Scala DSL 查詢的漏洞研究平台，支援原始碼、bytecode、binary。C/C++ 前端 c2cpg 以 Eclipse CDT 為基礎。 |
| [Serena](https://github.com/oraios/serena) | MCP | 1 | 有條件（GPL-3.0-or-later） | 2026-11-19 | 讀原始碼 | 把 language server（LSP）包成 MCP 工具，讓 agent 用 find_symbol、find_referencing_symbols、replace_symbol_body 等符號層級操作讀改程式，不必整檔讀取。另有付費 JetBrains 外掛後端與簡單的記憶檔。 |
| [Aider repo map](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py) | 專案 | 2 | 可使用（Apache-2.0） | 2026-05-22 | 讀原始碼 | Aider 在每次對話附上一份「repo 地圖」：用 tree-sitter 抽出每個檔案的定義與引用，以識別字連成檔案圖，跑 PageRank 排出重要符號，再壓到 token 預算（預設 1024）內。 |
| [ast-grep（sg）](https://github.com/ast-grep/ast-grep) | CLI | 2 | 可使用（MIT） | 2026-11-21 | 讀文件 | 以 tree-sitter AST 為基礎的結構化搜尋、lint 與改寫 CLI：用 `$MATCH` 這類 metavariable 寫跟程式碼長得一樣的 pattern。官方另有 ast-grep-mcp（MIT）與 ast-grep/agent-skill。 |
| [Bootlin Elixir](https://github.com/bootlin/elixir) | 服務 | 2 | 有條件（AGPL-3.0） | 2026-10-29 | 讀文件 | LXR 風格的原始碼交叉參照網站，主要為 Linux kernel 每個版本建立識別字的定義與引用索引。以 Git blob 為單位索引避免重複，Berkeley DB 存資料，Universal Ctags 抓定義；有 REST API（/api/ident/<專案>/<識別字>）。 |
| [clangd（compile_commands.json）](https://github.com/llvm/llvm-project/tree/main/clang-tools-extra/clangd) | CLI | 2 | 可使用（Apache-2.0） | 2026-11-21 | 讀文件 | LLVM 的 C/C++ language server。依 compile_commands.json 用真正的編譯參數解析每個檔案，所以 `#ifdef`、巨集、include 路徑都跟實際建置一致；背景索引提供跨檔 references、call hierarchy。 |
| [Coccinelle（SmPL）](https://github.com/coccinelle/coccinelle) | CLI | 2 | 有條件（GPL-2.0） | 2026-09-02 | 讀文件 | 用 semantic patch（SmPL）做模式比對與程式轉換，kernel 用它做全樹 API 遷移與問題偵測。`make coccicheck` 跑 scripts/coccinelle/ 下的所有 .cocci。 |
| [Codebase-Memory 論文（arXiv 2603.27277）](https://arxiv.org/abs/2603.27277) | 論文 | 2 | 有條件（CC-BY-4.0） | — | 讀文件 | Vogel 等人描述一個 tree-sitter 知識圖＋MCP 的程式探索系統（66 種語言），在 31 個 repo 上：答案品質 83%，對照的讀檔 agent 92%；token 約少 10 倍、工具呼叫少 2.1 倍。 |
| [GNU cflow](https://www.gnu.org/software/cflow/) | CLI | 2 | 有條件（GPL-3.0-or-later） | — | 實際執行 | 分析一組 C 原始檔，印出正向與反向的呼叫流程圖（文字樹），可附交叉參照；輸出 POSIX 與 GNU 兩種格式。 |
| [Graphify](https://github.com/Graphify-Labs/graphify) | 專案 | 2 | 可使用（Apache-2.0） | 2026-11-20 | 讀原始碼 | 把資料夾（程式、文件、PDF、圖片、影音）轉成 graph.json＋GRAPH_REPORT.md＋graph.html 的知識圖，讓 agent 用 query／path／explain 取代 grep。程式部分用 tree-sitter 抽 calls／imports／inherits，文件與媒體才走 LLM。 |
| [Repomix](https://github.com/yamadashy/repomix) | CLI | 2 | 可使用（MIT） | 2026-11-21 | 讀原始碼 | 把整個 repo（或 --include 選的檔案）打包成一個 XML／Markdown／純文字檔交給 LLM，附 token 計數、Secretlint 敏感檔排除、`--compress` 用 tree-sitter 只留簽名。這是 context packing，不是 code graph。 |
| [Trailmark](https://github.com/trailofbits/trailmark) | skill 集 | 2 | 有條件（Apache-2.0） | 2026-11-21 | 讀原始碼 | Trail of Bits 的多語言程式碼與 binary 圖工具，給資安分析用：blast radius、taint 傳播、權限邊界、入口點、未解析呼叫追蹤、圖差異。skills repo 裡有十多個以它為基礎的 skill（taint-trace、slicing-code-context、diagramming-code 等）。 |
| [CodeQL（data flow）](https://github.com/github/codeql) | 專案 | 3 | 有條件（MIT） | 2026-11-21 | 讀文件 | GitHub 的語意程式分析：把程式碼建成資料庫，用 QL 寫查詢，內建 data flow／taint tracking 函式庫。C/C++ 從 CLI 2.23.3（2025-10）起正式支援不需建置的 build-mode none。 |
| [cscope](https://sourceforge.net/projects/cscope/) | CLI | 3 | 可使用 | — | 實際執行 | Bell Labs 出身的 C 原始碼瀏覽工具，可查符號引用、全域定義、某函式呼叫了誰、誰呼叫某函式、字串、egrep、檔案、誰 include 了某檔。kernel 有 `make cscope` target。 |
| [GNU Global（gtags）](https://www.gnu.org/software/global/) | CLI | 3 | 有條件（GPL-3.0-or-later） | — | 實際執行 | 原始碼標記系統：找函式、巨集、struct 的定義與引用，支援增量更新 tag 檔，附 cscope 相容程式 gtags-cscope。內建 parser 支援 C、Yacc、Java、PHP4、組語，其他語言靠 Pygments＋Universal Ctags 外掛。 |
| [Smatch](https://github.com/error27/smatch) | CLI | 3 | 有條件（GPL-2.0-or-later） | 2026-11-12 | 讀文件 | 建在 sparse 上的 C 靜態分析器，kernel 維護者常用。可選的 cross function database 讓分析跨函式（作者說 kernel 建資料庫約 2～3 小時，每重建一次更準）；`kchecker` 檢查單一檔或目錄。 |
| [sparse](https://git.kernel.org/pub/scm/devel/sparse/sparse.git) | CLI | 3 | 可使用（MIT） | — | 讀文件 | kernel 的 C 語意檢查器。kernel 文件重點是 `__bitwise` 型別檢查（混用一般整數會被警告，`__force` 可壓制）；`make C=1` 檢查要重編的檔，`make C=2` 檢查全部，CF 傳額外參數。sparse 會定義 `__CHECKER__`。 |
| [Tree-sitter](https://github.com/tree-sitter/tree-sitter) | 函式庫 | 3 | 可使用（MIT） | 2026-11-21 | 讀文件 | 增量解析器產生器與函式庫：每種語言一份文法，產出具體語法樹（CST），檔案改動時只重新解析受影響的部分。上面那些 code graph 工具（Graphify、兩個 CodeGraph、codebase-memory-mcp、Repomix --compress、Aider repo map、ast-grep）幾乎都建在它上面。 |
| [Universal Ctags](https://github.com/universal-ctags/ctags) | CLI | 3 | 有條件（GPL-2.0） | 2026-11-20 | 實際執行 | 持續維護的 ctags：為原始碼產生 tags 索引（定義的位置），編輯器與其他工具（Bootlin Elixir、zoekt、GNU Global 外掛）拿它做符號定位。 |
| [Zoekt（Sourcegraph 維護）](https://github.com/sourcegraph/zoekt) | CLI | 3 | 可使用（Apache-2.0） | 2026-11-21 | 讀文件 | 以 trigram 索引為基礎的程式碼文字搜尋引擎，支援子字串、regex、布林查詢與多 repo；排序會參考是否命中符號（建議搭配 Universal Ctags）。2017 年從 google/zoekt fork，Sourcegraph 持續維護。 |
<!-- /ecosystem -->

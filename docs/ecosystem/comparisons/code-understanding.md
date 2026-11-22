# 程式理解工具比較

查核日期：2026-11-21～22。原始筆記在 [C-code-tools.md](../../../studies/ecosystem-2026-11/C-code-tools.md)，試跑結果在 [codegraph/RESULTS.md](../../../studies/ecosystem-2026-11/trials/codegraph/RESULTS.md)。

「程式理解」底下其實是四個不同的問題，工具常被混在一起比：

| 問題 | 代表工具 | 回答的是 |
|---|---|---|
| 符號與呼叫關係 | clangd、cscope、cflow、CodeGraph、codebase-memory-mcp、Serena | 誰呼叫誰、定義在哪 |
| 資料怎麼流 | Joern、CodeQL | 某個輸入會不會流到某個呼叫 |
| 把程式碼塞進 context | Repomix、Aider repo map | 讓模型一次看到更多檔案 |
| 跨 session 記住專案 | claude-mem、codebase-memory-mcp 的部分功能 | 上次查過什麼 |

前兩個是確定性的分析；第三個只是打包，不理解程式；第四個是記憶，見[記憶系統比較](memory-systems.md)。

## 能力對照

只列讀到的原始碼或文件裡有的能力，有沒有做對要看下一節的試跑。

| 工具 | 解析方式 | 呼叫關係 | 函式指標／ops table | `#ifdef`、巨集 | data flow | 隱私 |
|---|---|---|---|---|---|---|
| clangd | Clang（照 compile_commands.json 編譯） | 有 | 無 | 照編譯旗標，應該正確（沒有實測；試跑的是 clang 的呼叫圖輸出） | 無 | 本機 |
| cflow `--cpp` | 先跑前置處理器 | 直接呼叫 | 無 | 正確 | 無 | 本機 |
| ctags、cscope、GNU Global | 模糊解析 | cscope 有 | 無 | 兩個分支都收 | 無 | 本機 |
| CodeGraph（colbymchenry） | tree-sitter＋Rust kernel，SQLite | 有 | **有**（啟發式，邊標 heuristic） | 文件說依檔內 `#define` 與建置設定三值判斷；試跑時兩個分支都列出 | 無 | 本機；匿名統計與每日更新檢查預設開 |
| CodeGraph（codegraph-ai） | tree-sitter，RocksDB＋向量 | 有 | 有（記成帶欄位名的邊） | 只認 `#if 0／1` | 付費版 | 本機；PostHog telemetry 預設開 |
| codebase-memory-mcp | tree-sitter，SQLite | 有 | 只到結構欄位 | 兩個分支都收 | 有 DATA_FLOWS 邊 | 本機，README 聲明無 telemetry；hooks 預設開 |
| Serena | 包 language server（C 用 clangd） | 由 LS 提供 | 由 LS 提供 | 由 LS 提供 | 無 | 本機；會下載 language server |
| Joern | Eclipse CDT，code property graph | 有 | 部分 | 可吃 compile_commands 或 `.i` 檔 | **有** | 本機；kernel 全量建圖在 8 GB 跑不動 |
| Graphify | tree-sitter，C 只抽三種節點 | 有 | callback 標 INFERRED | 兩個分支都收 | 無 | 程式碼本機，文件會送 LLM |
| Repomix、Aider repo map | 打包或名稱層級 | 無或弱 | 無 | 兩個分支都打包 | 無 | Aider 的地圖會隨 prompt 送出 |

**沒有任何 tree-sitter 工具會讀 kernel 的 `.config` 或 `autoconf.h`**，所以「這個 config 下誰會被呼叫」只有照編譯資料庫跑的工具（clangd、Joern、cflow `--cpp`）答得出來。

## 試跑：同一個 C 專案、五個問題

六個檔案的小專案，刻意放進 ops table、callback、巨集產生的函式與 `#ifdef` 兩個分支；執行檔回傳 3，證明這次建置走的是 `slow_submit`。

| 問題 | 答對的工具 |
|---|---|
| 誰呼叫 `dev_open`（巨集產生的 `handle_uart`、`handle_spi`） | cflow `--cpp`、clang |
| `dev->ops->open` 會到哪裡 | 只有 CodeGraph（colbymchenry） |
| `timer_fire` 執行哪個 callback | 沒有 |
| 這次建置 `submit` 呼叫誰 | cflow `--cpp`、clang |
| `handle_uart` 定義在哪 | cflow `--cpp` |

另外兩件事：codebase-memory-mcp 把巨集 `DEFINE_HANDLER` 記成函式，緊接在後的 `heartbeat` 整個不在圖裡；答案檔放在資料夾裡時，它也把 JSON 收進索引。工具會安靜地漏東西，也會收進不該收的檔案。

## 真正不同的方向

1. **照編譯走**（clangd、cflow `--cpp`、Joern、kernel 的 sparse／smatch）：對單一組設定是對的，但要先能建置、要有 compile_commands.json。
2. **語法樹加啟發式**（CodeGraph 兩版、codebase-memory-mcp、Graphify）：不用建置、速度快、跨語言，函式指標靠猜（猜對時很有用），`#ifdef` 與巨集常出錯。
3. **把整個 repo 塞給模型**（Repomix）：沒有理解，成本隨 repo 線性成長。
4. **交給 language server**（Serena）：準確度等於 clangd，但 clangd 背景索引完成前查詢會回空（Serena issue #2191，只看到搜尋摘要）。

## 建議

- 框架的 `trace-code` 追 C 時，照這個順序：執行證據 → 會跑前置處理器的工具取直接呼叫 → 找 ops table 的 designated initializer（CodeGraph 的結果當候選）→ 找 callback 的註冊點 → 回原始碼確認。細節見試跑結果的「對框架的建議」。這是路線圖 S19 的內容。
- 任何工具說「沒有呼叫者」「找不到」，都不能拿來刪程式。
- 要裝 CodeGraph 或 codebase-memory-mcp 這類 MCP 時，先關 telemetry 與自動安裝的 hooks（codebase-memory-mcp 用 `install --no-hooks`），並確認索引範圍。
- 還沒測：Serena＋clangd、Joern、codegraph-ai 版。下一步用真的 kernel 子目錄（例如 `drivers/net/ethernet/intel/e1000e`，先產生 compile_commands.json）測這三個。

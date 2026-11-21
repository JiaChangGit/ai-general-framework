# C 程式理解試跑結果（2026-11-21～22）

方法見[上一層的 README](../README.md)。題目與答案在 `fixture/truth.json`；每個工具在容器裡斷網執行，原始輸出在 `*-output.txt`，建置與執行方式在同名的 Dockerfile 與 `.sh`。AI 工具第一次跑的時候，答案檔 `truth.json` 也在被索引的資料夾裡，codebase-memory-mcp 把它收進了索引；兩個 AI 工具都改成只複製 `include/`、`src/`、`Makefile` 重跑，這裡記的是重跑的結果（CodeGraph 的答案沒有變）。

## 版本

Universal Ctags 5.9.0、cscope 15.9、GNU Global 6.6.13、GNU cflow 1.7、clang 19.1.7（`debug.DumpCallGraph`）、colbymchenry/codegraph 1.6.4（npm，`CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1`）、codebase-memory-mcp 0.12.1（npm，CLI 模式）。

## 五個問題的答案

✓ 答對；△ 方向對但不完整；✗ 答錯或沒答；— 沒有問這個工具。

| 問題（正確答案） | ctags | cscope | GNU Global | cflow `--cpp` | clang | CodeGraph 1.6.4 | codebase-memory-mcp 0.12.1 |
|---|---|---|---|---|---|---|---|
| Q1 誰呼叫 `dev_open`（`handle_uart`、`handle_spi`，巨集產生） | — | ✗ 回報巨集名 `DEFINE_HANDLER` | ✗ 只給巨集內那一行 | ✓ 附 main.c:9、:10 | ✓ | ✗ 沒有呼叫者 | △ 只說「main.c 這個檔案」 |
| Q2 `dev->ops->open` 會到哪裡（`uart_open`、`spi_open`） | — | ✗ 只回成員名 `open` | — | ✗ | ✗ | **✓ 兩個都對，標出 dev.c:5** | △ 只到欄位 `dev_ops.open` |
| Q3 `timer_fire` 執行哪個 callback（`heartbeat`） | — | ✗ 只回 `cb` | — | ✗ 反而畫出 main 呼叫 heartbeat | ✗ | ✗ 只說 main 引用 heartbeat | △ 只到欄位 `timer.cb` |
| Q4 這次建置 `submit` 呼叫誰（只有 `slow_submit`） | ✗ 兩個定義都列 | ✗ 兩個都列 | — | ✓ | ✓ | ✗ 兩個都列 | ✗ 兩個都列 |
| Q5 `handle_uart` 定義在哪（main.c:9） | ✗ | ✗ | ✗ | ✓ | —（只列呼叫） | ✗ | ✗ |

記憶體：CodeGraph 建圖 0.27 秒、峰值 137 MB；codebase-memory-mcp 峰值約 92 MB。兩者斷網都能建索引與查詢。

## 看到的事

1. **沒有一個工具五題全對，而且錯的地方剛好互補。** 會跑前置處理器的 cflow `--cpp` 與 clang 處理得了巨集與 `#ifdef`，但看不到函式指標；CodeGraph 解得出 ops table，卻漏了巨集產生的函式、也不排除沒啟用的 `#ifdef` 分支。
2. **callback（先註冊、之後才呼叫）沒有工具解得出。** 最接近的是 CodeGraph 說「main 引用了 heartbeat」，這句話本身是對的；cflow 則把「當參數傳出去」畫成「呼叫」，是錯的邊。
3. **工具會安靜地漏東西。** codebase-memory-mcp 把 `DEFINE_HANDLER` 記成一個函式，而緊接在巨集之後的 `static void heartbeat` 整個不在圖裡（查詢回「function not found」）。推測是檔案層的巨集呼叫讓語法解析出錯、吞掉了後面的定義，沒有讀它的原始碼確認。kernel 的 `.c` 檔到處是這種寫法。
4. **索引會收進不該收的檔案。** 答案檔放在資料夾裡時，codebase-memory-mcp 也把 JSON 收進索引、查 `handle_uart` 先回答案檔的內容。用 code graph 時要確認索引範圍。
5. **執行結果是最直接的證據。** 這個專案編譯後回傳 3，直接證明走的是 `slow_submit`；靜態工具裡只有 cflow 與 clang 答對這題。

## 對框架的建議（S19 用）

追 C 與 kernel 的路徑時，照這個順序取證據，再交給 AI 串起來：

1. 能建置或執行，就先用執行結果、log 或 trace 確認實際走的路。
2. 直接呼叫、巨集與 `#ifdef`：用會跑前置處理器的工具，帶上專案的編譯旗標（cflow `--cpp`、clang；大型專案用 compile_commands.json 與 clangd）。
3. ops table：找 designated initializer（`.open = xxx`）與 `->open(` 的呼叫點，CodeGraph 這類工具的結果當候選，標成推論。
4. callback：找註冊的地方（把函式名當參數傳出去、或寫進結構欄位），再確認呼叫點；目前沒有工具能代勞。
5. 任何工具說「沒有呼叫者」「找不到函式」，都不能直接當成事實，回原始碼確認。

## 限制

- 測試專案只有六個檔案，用來分辨「能不能」，不能代表大型 kernel 的速度、記憶體與漏抓率。
- Serena＋clangd、Joern、codegraph-ai/CodeGraph、Graphify 沒有測（Serena 要 MCP client；Joern 需要 JVM 與較多記憶體）。clangd 本身理論上答得出 Q1、Q4、Q5，但沒有實際跑。
- 每個工具只跑一次；CodeGraph 的「ops table 解析」是啟發式（作者文件寫明），在別的寫法上不一定成立。

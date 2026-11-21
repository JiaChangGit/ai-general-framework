# 試跑：文件解析與 C 程式理解

使用者這輪允許在 Docker 裡安裝試跑。為了讓比較有標準答案，兩組都先自己做一份「內容已知」的測試材料，再讓各工具回答同樣的問題。測試材料、產生方式、評分程式與原始輸出都在這個資料夾；工具的映像檔與暫存輸出在 `~/.cache/agf-ecosystem/trials/`，沒有放進版本庫。

所有工具都在容器裡跑：不掛載家目錄，只掛測試材料；執行時 `--network none`（文件解析）或同樣斷網（程式理解），所以「需要連網才能跑」本身就是一項結果。記憶體上限 7 GB（WSL 看得到 8 GB）。

## 文件解析（`docparse/`）

`make_fixture.py` 產生三頁的 PDF：英文表格（五列數字，含負號、千分位、Δ）、雙欄內文（每段開頭有 `[P01]`～`[P08]` 標記，用來判斷閱讀順序）、繁體中文表格與段落、Unicode 符號、一個圖片形式的公式、每頁的頁首與「第 N 頁 / Page N」頁尾。再把它轉成 150 dpi 灰階圖片組成的 `fixture-scanned.pdf`，模擬掃描件。答案在 `truth.json`。

`score.py` 只用標準函式庫，檢查：表格儲存格找到幾成、整列是否留在同一行（表格結構）、八段標記是否照順序、段落是否完整、中文段落、符號、公式、頁尾頁碼。`run.py` 依序在各工具的容器裡執行，記錄耗時、記憶體峰值（cgroup 的 `memory.peak`）與 exit code。

結果與解讀見 [`docparse/RESULTS.md`](docparse/RESULTS.md)。

## C 程式理解（`codegraph/`）

`fixture/` 是一個能編譯的小 C 專案，刻意放進 kernel 程式常見、也最容易讓工具出錯的寫法：ops table 的函式指標（`dev->ops->open`）、註冊後才呼叫的 callback（`timer_fire` 呼叫 `t->cb`）、巨集產生的函式（`DEFINE_HANDLER(uart)` 產生 `handle_uart`）、`#ifdef` 兩個分支各有一個 `submit`。執行檔回傳 3，證明這次建置走的是 `slow_submit`。`truth.json` 列出五個問題與正確答案。

結果與解讀見 [`codegraph/RESULTS.md`](codegraph/RESULTS.md)。

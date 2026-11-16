# 在真實宿主上量 skill 的觸發

這裡的工具開全新、無頭（headless）的 Claude Code session 跑 [`../scenarios.json`](../scenarios.json) 的情境，從事件串流直接數：Skill 工具有沒有被呼叫、讀了哪些 `SKILL.md`、該用的有沒有用到、不該用的有沒有用。
目前只支援 Claude Code；其他宿主沒有可以驗證的登入。

| 檔案 | 做什麼 |
|---|---|
| `run_claude.py` | 開一次 session，摘要事件串流。環境只留 `HOME`、`PATH`、`LANG`、`TERM` 和明確給的 `--env`，宿主的訊息通道與 session id 不會傳下去 |
| `preflight.py` | 開跑前檢查受試目錄：檔案裡有沒有不該出現的路徑、有沒有指到外面的連結、上層目錄有沒有會被一起載入的規則或 skill、旁邊有沒有讀得到的別次材料、會不會傳下像宿主通道的環境變數 |
| `trigger.py` | 每次執行建一個私有目錄，只在框架組安裝框架，預檢後執行並記錄，最後刪掉目錄；`stop` 用 PID 停止，`report` 彙總 |
| `usage.py` | 從本機的 Claude Code 對話紀錄，統計框架的 skill 與 `agf` 子命令實際被用了幾次；只輸出總數 |

## 怎麼跑

```console
python evals/host/trigger.py run --framework . --base /tmp/agf-trigger-base --out /tmp/agf-trigger-out \
  --ids trace-lossy-id-conversion,object-authorization-and-model-output --group framework --group control \
  --skill trace-code --pid-file /tmp/agf-trigger.pid
python evals/host/trigger.py report /tmp/agf-trigger-out
python evals/host/trigger.py stop --pid-file /tmp/agf-trigger.pid
```

`--base` 必須是空目錄，而且不能在任何專案底下。每次執行都在裡面建一個私有的上層目錄，跑完就刪。
CLI 依序取 `--cli`、`CLAUDE_CLI`、PATH 上的 `claude`；模型預設 `claude-sonnet-5-5`，每次預算上限 2 美元，受試者只能用 `Read Grep Glob Skill`。
每次 session 都會真的花錢：2026-11-16 在這些情境裡，一次約 0.1 美元（CLI 的估算）。

要停止進行中的量測，用 `stop`。它先確認 PID 屬於 `trigger.py run`，才送 SIGTERM；已完成的結果會保留。
不要用 `pkill -f`：比對的字串也會出現在執行 pkill 的那個 shell 自己的命令列上，曾經因此連自己的 shell 一起殺掉。`stop` 只在 Linux 上核對行程；其他平台用宿主自己的工具停止。

## 隔離：實際踩過的坑

- **兄弟目錄。** 兩組的目錄放在一起時，受試者用 Glob 搜尋上一層，讀到了另一組的材料。所以每次執行都有自己的上層目錄，預檢也會檢查旁邊有沒有東西。
- **入口檔裡的絕對路徑。** 複製出來的專案，入口檔寫著原專案的絕對路徑，受試者照著去讀了原專案的交接文件。複製專案做實驗時，用 `--forbid <原專案路徑>` 讓預檢擋下。
- **Read 不限於工作目錄。** 一般模式下，Read、Glob、Grep 都能讀工作目錄外的檔。Claude Code 2.1.325 的 `--restricted` 會把它們限制在工作目錄內（2026-11-16 實測），
  但它同時不載入使用者、專案與本機的設定檔；這會不會改變 skill 與 `CLAUDE.md` 的載入，還沒有驗證，所以 `trigger.py` 沒有用它。
- **其他行程。** 允許 `ps` 之類的命令時，受試者看得到主持實驗的 session 與它的命令列。`trigger.py` 不給 Bash。
- **使用者層的設定照樣載入。** 受試 session 仍會載入使用者的全域設定（例如 hook、全域 `CLAUDE.md`、使用者層級的 skill），兩組相同；解讀結果時要記得它們存在。

## 結果怎麼讀

每個條件只跑一次時，差異可能只是雜訊，只能看方向。「用到了」只代表事件串流裡有那次呼叫或讀檔，不代表成果比較好；成果的品質要另外盲評。

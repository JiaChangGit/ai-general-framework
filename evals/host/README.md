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
  --model claude-sonnet-5-5 --ids trace-lossy-id-conversion,object-authorization-and-model-output \
  --group framework --group control --skill trace-code --pid-file /tmp/agf-trigger.pid
python evals/host/trigger.py report /tmp/agf-trigger-out
python evals/host/trigger.py stop --pid-file /tmp/agf-trigger.pid
```

`--base` 必須是空目錄，而且不能在任何專案底下。每次執行都在裡面建一個私有的上層目錄，跑完就刪。
CLI 依序取 `--cli`、`CLAUDE_CLI`、PATH 上的 `claude`；`--model` 必填，沒有預設值。每次預算上限預設 2 美元，受試者只能用 `Read Grep Glob Skill`。
Bash 預設用 `--disallowedTools Bash` 整個拿掉：Claude Code 2.1.325 實測，允許的工具裡沒有 Bash 時，`find`、`head` 這類唯讀命令仍會在工作目錄裡執行。要重現 2026-11-16 那兩輪的條件，加 `--allow-readonly-bash`；結果的 `bash_ran` 列出實際執行過的 Bash 命令。
環境變數名稱像宿主通道或憑證的（含 CLAUDE、ANTHROPIC、SESSION、TOKEN 等），不論是保留下來的還是用 `--env` 設的，預檢都會擋下，除非用 `--allow-env 名稱` 明確放行。
每次 session 都會真的花錢：2026-11-16 在這些情境裡，一次約 0.1 美元（CLI 的估算）。

要停止進行中的量測，用 `stop`。它先確認 PID 屬於 `trigger.py run`，才送 SIGTERM；已完成的結果會保留。
不要用 `pkill -f`：比對的字串也會出現在執行 pkill 的那個 shell 自己的命令列上，曾經因此連自己的 shell 一起殺掉。`stop` 只在 Linux 上核對行程；其他平台用宿主自己的工具停止。

## 隔離：實際踩過的坑

- **兄弟目錄。** 兩組的目錄放在一起時，受試者用 Glob 搜尋上一層，讀到了另一組的材料。所以每次執行都有自己的上層目錄，預檢也會檢查旁邊有沒有東西。
- **入口檔裡的絕對路徑。** 複製出來的專案，入口檔寫著原專案的絕對路徑，受試者照著去讀了原專案的交接文件。複製專案做實驗時，用 `--forbid <原專案路徑>` 讓預檢擋下。
- **Read 不限於工作目錄。** 一般模式下，Read、Glob、Grep 都能讀工作目錄外的檔。Claude Code 2.1.325 的 `--restricted` 會把它們限制在工作目錄內（2026-11-16 實測），
  但它同時不載入使用者、專案與本機的設定檔；這會不會改變 skill 與 `CLAUDE.md` 的載入，還沒有驗證，所以 `trigger.py` 沒有用它。
- **其他行程。** 允許 `ps` 之類的命令時，受試者看得到主持實驗的 session 與它的命令列。`trigger.py` 預設拿掉 Bash。
- **Windows。** `run_claude.py` 在 Windows 會多保留幾個系統變數（`SYSTEMROOT`、`USERPROFILE` 等）；這些工具還沒在 Windows 上跑過，`stop` 也只在 Linux 上核對行程。
- **框架本身的路徑。** shared 模式的安裝會把框架的絕對路徑寫進受試目錄的規則檔與 manifest（那是工具入口，設計如此），受試者可能照著去讀框架的按需參考；`outside_paths` 會記下這些讀取。預檢只搜尋 `--forbid` 給的路徑，報告也會列出它讀不了的檔。
- **使用者層的設定照樣載入。** 受試 session 仍會載入使用者的全域設定（例如 hook、全域 `CLAUDE.md`、使用者層級的 skill），兩組相同；解讀結果時要記得它們存在。

## 框架到底有沒有幫助、多花多少：`impact.py`

`impact.py` 用 [`../impact/tasks.json`](../impact/tasks.json) 的任務做配對實驗：每個任務在「有裝框架」與「沒裝框架」兩組各跑 `--runs` 次，組別順序每個任務交替。
任務的成敗由**隱藏檢查**決定：session 結束後才在工作目錄裡執行的 Python 片段、對最後回答的正規表示式，或對受試者寫出的檔案的正規表示式；受試者看不到它們。
token（input、cache creation、cache read、output 分開）與費用取自 CLI 的 result 事件，加總一個任務的所有 session。

```console
python evals/host/impact.py run --framework . --base /tmp/agf-impact-base --out /tmp/agf-impact-out \
  --model claude-sonnet-5-5 --switch-model claude-haiku-5-5 --runs 2 \
  --hooks evals/impact/continuity-hooks.json --budget 0.5 --total-budget 3
python evals/host/impact.py report /tmp/agf-impact-out
```

- 有兩個任務先跑一個被 `max_turns` 截斷的 session，再開新的 session 接著做：一個代表「額度用完，新 session 接手」，另一個在第二段換成 `--switch-model`，代表「換模型接手」。
- `--hooks` 把那份 JSON 合併進框架組的 `.claude/settings.json`；`{framework}` 會換成框架的路徑。不給就只量規則與 skill。
- `--total-budget` 是整次實驗的上限：下一個 session 可能讓總花費超過它時就停下，已完成的結果保留。`report` 另寫一份 `report.md`。
- 被用量上限打斷時，用 `--ids` 只補跑缺的任務、寫到新的 `--out`，再用 `impact.py report <目錄一> <目錄二> --md <檔案>` 合併；模型、工具、skill、hook 或任務檔不同的目錄不會合併。受試 session 和你自己的對話用同一個額度。
- 報告的表格另有兩欄：有計畫截斷的任務，第一段實際被截斷了幾次（沒截斷就沒測到「接手」）；受試者讀了幾次工作目錄以外的檔。
- `--hooks` 用到的框架檔案會複製進受試目錄，設定檔不寫框架的路徑。但 shared 模式的安裝仍會把框架路徑寫進規則檔（見上面「框架本身的路徑」），所以每次都要看讀取工作目錄以外的次數。
- 受試者能用 Read、Grep、Glob、Edit、Write、Skill，Bash 整個拿掉；隔離與預檢和 `trigger.py` 相同。
- `--env NAME` 不帶值時，從目前的環境複製那個變數，例如在 CI 裡傳 API key，不必把它寫在命令列上。
- 每個條件只跑一兩次時，差異可能是雜訊。要比較時固定模型、任務與 CLI 版本；Claude Code 的快取在訂閱方案內是 1 小時、其他情況 5 分鐘，跑的先後會影響 cache read 的多寡，所以 token 要分開看，不只看總數。

`.github/workflows/skill-triggers.yml` 讓同一套觸發檢查在 GitHub Actions 上跑：只在手動按下時執行，需要 `ANTHROPIC_API_KEY` secret，結果上傳成 artifact，不讓 build 失敗。

## 結果怎麼讀

每個條件只跑一次時，差異可能只是雜訊，只能看方向。「用到了」只代表事件串流裡有那次呼叫或讀檔，不代表成果比較好；成果的品質要另外盲評。
第一次的觸發量測見 [2026-11-16 的結果](results-2026-11-16.md)；第一次有對照組的觸發與成效量測見 [studies/research-2026-11/G-measurement-2026-11-18.md](../../studies/research-2026-11/G-measurement-2026-11-18.md)。

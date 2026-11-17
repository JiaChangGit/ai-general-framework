# 依 S8 報告修改框架：規格（草稿）

狀態：**已核准**（2026-11-16，使用者回「可，開始做」）。撰寫：`claude-opus-5-5`。

S8 結束時你回「都處理」，接著點名授權修改 ai-general-framework（「點名，框架一起改」），本專案這邊對應的修正也一起做。不 push。
建議的出處是 [S8 報告](../analysis/report.md)；下面括號裡的「第 N 項」指報告「逐項」的編號。

## 1. 怎麼改框架，才不會碰到你手上的工作

框架的工作目錄有 10 個你還沒 commit 的修改（`agf/execution.py`、`docs/workflow.md` 等，L01 時就在了），其中 3 個檔這次也要改。
直接在那裡改，兩份修改會混在同一批差異裡，你很難分開 commit。所以我這樣做：

- 用 `git worktree` 在框架目錄外開一個工作目錄 `/home/user/src/agf-worktrees/s8-follow-up`，分支 `s8-follow-up`，從 HEAD `2569a91` 開始。
  你的工作目錄一個 byte 都不動，`.claude/settings.json` 擋它的規則照舊有效。
- 不碰你正在改的檔：`agf/execution.py`、`tests/test_execution.py`、`docs/verification.md`、`docs/writing.md`、`docs/writing-research.md`、`evals/scenarios.json`、`evals/writing-cases.json`。
  `docs/workflow.md`、`docs/cli.md`、`evals/README.md` 只改你沒動到的段落。
- 做完後在暫存的 clone 裡預演：先把你的修改 commit，再 merge 這個分支，確認沒有衝突。
- 分支上會有本機 commit（框架的 `AGENTS.md` 說本機 commit 在任務授權內）。要不要 merge 進 `main`、要不要 push，都由你決定。

## 2. 每條建議怎麼處理

### 2.1 接上規則入口（三件事第 1 點）

問題：專案原本就有 `CLAUDE.md` 時，框架保留它、不加 import，只在安裝的輸出留一句提示。本專案就是這樣，規則從來不會自動載入。

框架：

- `project status` 檢查每個宿主的入口有沒有載入 `.agf/managed/project-rules.md`。Claude 與 Gemini 看 `@` import，並沿著 import 往下找（例如 `CLAUDE.md` → `@AGENTS.md` → …）；
  Codex 與 OpenCode 看 `AGENTS.md` 有沒有寫到它。沒接上就加一條警告。退出碼不變，免得已經拿 `status` 當檢查的人突然失敗。
- 安裝與更新的提示，改成寫出要加的那一行，以及不加的後果。
- 不自動改寫使用者的 `CLAUDE.md`。框架用整檔雜湊管理受管理的檔案；`CLAUDE.md` 是使用者常改的檔，納入管理之後每改一次就是 drift，更新會被擋下。手動加一行比較單純。
  這和報告寫的「同意後自動加入」不同，是我看過程式後改的。

本專案：`CLAUDE.md` 加一行 `@.agf/managed/project-rules.md`。之後每個 session 會多載入這份 1,469 字的規則。

驗證：

- 單元測試先寫，在 HEAD 上要失敗：只提到檔名、沒有 import；經由 `AGENTS.md` 的 import 鏈接上；新安裝產生的入口；Codex 的 `AGENTS.md`。
- 用分支的程式對本專案跑 `project status`（唯讀）：改前有警告，改後沒有。
- 開一個全新、不給任何工具的 headless session，問「專案協作約定」的第一句：改前答不出，改後答得出。同一次也問 `AGENTS.md` 的第一句，看這版 Claude Code 會不會自己載入 `AGENTS.md`（轉接設定寫「未驗證」）。

### 2.2 skill 用宿主的機制叫用，觸發列入回歸評測（三件事第 2 點）

問題：實驗 A 的 12 次 session 沒有一次呼叫 Skill 工具；有框架的那組照規則的「按任務讀取相應 skill」，自己去讀 `.agents/skills/` 的副本。

框架：

- `templates/project-rules.md` 那句改成：宿主列出可用的 skill 時，用宿主的機制叫用（例如 Claude Code 的 Skill 工具），不另外讀 `.agents/skills/` 的副本；宿主沒有列出時，才讀 `SKILL.md`。
- 新增 `evals/host/`，把 S8 的 `run_session.py` 和實驗 A 的驅動程式改寫成框架版。CLI 路徑、模型、預算都由參數給，不寫死本機路徑。
  順便修掉 S8 版的兩個小問題：判斷路徑在不在目錄裡時用字串前綴比對；`run` 子命令不能帶禁止規則。
  它量三件事：Skill 工具的實際呼叫、「該用卻沒用」、「不該用卻用了」。目前只做 Claude Code，其他宿主沒有登入可以驗證。

本專案：部署在 `.agf/managed/` 的規則，要等你 merge 後跑 `agf project update` 才會換成新句子。在那之前，`CLAUDE.md` 先寫一句「skill 用 Skill 工具叫用」。
S8 的實驗程式保留原樣，當作 S8 的紀錄。

驗證：

- 解析事件串流的程式，用固定的範例串流做單元測試。
- 用分支的框架重跑實驗 A 框架組的 6 個情境。條件和 S8 相同：CLI 2.1.325、Sonnet 5.5、工具 `Read Grep Glob Skill`、同樣的預算與材料。
  和 S8 比四個數字：Skill 工具呼叫（S8：0 次）、該用的 4 個情境用到幾個（S8：3 個）、不該用的 2 個有沒有誤觸（S8：0 個）、費用（S8：0.638 美元）。
- 每格只跑一次，結果只看方向，不設門檻。不過 Skill 工具如果還是 0 次，就照實寫「這條修改沒有達到目的」。

### 2.3 核對寫成命令，隔離寫成預檢（三件事第 3 點；第 2、11 項）

框架：

- `docs/workflow.md` 的交接段落加兩件事：列出接手者要自己執行的核對命令和預期結果；路徑寫成相對於專案根目錄，非寫別的位置不可時，註明那是哪一份副本。
- `agf task record` 加一個選用欄位 `checks`，`task handoff` 把它放在最前面，標題是「Checks to run first」（現有標題都是英文）。
- `evals/host/preflight.py`：開跑前檢查受試的目錄，看四件事：
  文件裡有沒有原專案的絕對路徑；上層目錄有沒有會被繼承的 `.claude/skills`、`CLAUDE.md` 或 `AGENTS.md`；兄弟目錄裡有沒有別次執行的材料；
  要傳給受試者的環境變數裡，有沒有宿主的訊息通道或 session id。`evals/README.md` 加一段連過去。

本專案：`docs/HANDOFF_CLAUDE.md`「一開始先做什麼」的每條命令寫出預期結果，`cd` 的絕對路徑改成相對的說法。

驗證：`checks` 與預檢都有單元測試。預檢的測試要重現 S8 的兩次缺陷（`CLAUDE.md` 裡的絕對路徑、兄弟目錄讀得到），兩次都要被抓到。2.2 的重跑開始前，先用預檢檢查一次。

### 2.4 讓 `agf` 子命令在對的時候被想到（第 1、10 項）

框架：`project-rules.md` 樣板加一行，列出常用的子命令和時機：`run`（限時、限輸出量地執行命令並保存輸出）、`context`、`source`、`files`、`binary`、`diagram`、`git scope`、`task`、`check`。用途照 `docs/cli.md` 寫。

驗證：校閱用途和 `cli.md` 一致。2.2 的重跑會順便看有沒有用到，但不當成通過條件。

### 2.5 寫作的入口點名寫作指引（第 3 項）

框架：`project-rules.md` 樣板講語言的那一行，加「寫或改給人讀的說明前，先讀 writing 指引」。

本專案：`write-bug-lesson` skill 的流程，第一步先讀 `.agf/managed/guides/writing.md`。

驗證：校閱。入口點名的效果實驗 C 量過（點名 1／2、不點名 0／2），這次不重跑。

### 2.6 提選項前，先查已經有的能力（第 7 項）

框架：`docs/workflow.md`「先理解，再決定做法」那段，以及 `project-rules.md` 的第一條，加「提出做法或選項前，先查框架與專案已有的 skill、指引、`agf` 工具和評測，把查到的寫進問題」。

驗證：校閱。

### 2.7 規格寫明模型分工（第 2 項）

框架：`docs/workflow.md`「角色與模型」加：要換模型或開子代理時，在規格或計畫寫明哪一步、由誰做、為什麼；使用者核准了就照做，不因為執行時沒人再提而跳過（L53）。

本專案：路線圖的每階段流程，規格多一節「模型分工」。這份規格先照做（第 4 節）。

### 2.8 「完成」要有查得到的產物（第 5 項）

框架：`docs/workflow.md` 的收斂條件加：寫「完成」或建立代表完成的標記（例如 tag）之前，指出證明它的輸出、時間和位置；拿不出來就寫「已實作、未驗證」。

本專案：已經有了（`scripts/status.py`，以及「驗收通過才打 tag」），不改。

### 2.9 會重複的坑，做成可執行的工具（第 8 項）

框架：`evals/host/` 的驅動程式啟動時寫 PID 檔，收到 SIGTERM 會停下，保留已完成的結果；另有 `stop` 子命令，先確認那個 PID 真的是這支驅動程式，才送訊號。
這是針對 L55：`pkill -f` 比對的字串，也出現在下指令的那個 shell 自己的命令列上，結果連自己的 shell 一起殺掉。
不在 `tools.md` 加文字，因為報告的結論是文字擋不住重複的錯。

驗證：單元測試啟動一支假的驅動程式，用 `stop` 停下，確認結果檔還在；PID 對不上時，確認不會送訊號。

### 2.10 宿主原生的權限範本（第 11 項）

框架：

- 新增 `templates/claude-permissions.example.json`，用 Claude Code 原生的格式：擋受保護目錄的 `Edit` 與 `Write`，擋 `git push` 與建立 PR。`agf integration template claude-permissions` 可以匯出它。
- 不自動安裝。框架的安裝範圍明寫不安裝原生設定，這次不改這條邊界。
- `adapters/claude.json` 與 `docs/cli.md` 寫明管得到與管不到的：Read、Edit、Write 依路徑擋，Bash 依命令開頭比對；用 Bash 寫檔（`cp`、`sed -i`、重導向）擋不住。Read 的禁止規則也會限制 Grep 與 Glob（S8 的探測）。

本專案：`.claude/settings.json` 補一條 `Write(//home/user/src/ai-general-framework/**)`。

驗證：在暫存目錄放同樣格式的規則，跑 headless session，請受試者用 Write 寫被保護的路徑，要被拒絕。
另跑一次「從上層目錄啟動」，記錄子目錄的設定有沒有生效；這是 L50 留下的未知。

### 2.11 刪減每次都載入的規則（第 4 項）

2.2、2.4、2.5、2.6 都會在 `project-rules.md` 加句子，常駐的規則會變長。先量，再決定刪不刪：

- 從 S8 的原始串流算出常駐規則的成本：比較兩組第一個回合建立快取的 token。
- 常駐規則佔一次 session 費用不到 5% 時，不刪，在結果裡寫明成本主要來自按需讀的檔（`SKILL.md`、指引）。
  超過 5% 才刪，而且只刪和 `workflow.md`、`tools.md` 重複的句子；SVN、STM32、券商等特殊權限的句子一字不動。刪了哪幾句，在差異裡逐句列出。
- 2.2 的重跑同時量費用和 token，和 S8 的框架組比。

### 2.12 本機的使用次數（第 1 項）

框架：`evals/host/usage.py` 從 Claude Code 的本機對話紀錄，統計 Skill 工具的呼叫、`SKILL.md` 的讀取和 `agf` 子命令的執行次數。
只讀，不加任何記錄機制。只輸出總次數，不輸出對話內容、專案名稱或路徑。

驗證：用合成的紀錄做單元測試。對這台機器的紀錄跑一次，結果放在本專案，不放進框架。

### 2.13 這次不做的，以及理由

- 不把規則式的 AI 味檢查加進框架（第 3 項；S7 只找得到約 4% 的問題）。
- L46 的例子，等第二個專案也出現再收（第 6 項）。
- 過度思考：沒有足夠證據提出修改（第 9 項）。
- 「snippet 式的 script 量過才收」：`docs/maintenance.md` 已經寫了「新依賴與共用 script 也要指出它比原生方法增加的實際價值」，不重複寫。
- 本專案的 `capped_run.py` 不換成 `agf run`：S6 的驗收契約和教學 16 都用它，換掉等於動到已經驗收的工具。重疊的問題由 2.4 處理。

## 3. 會動到的檔案

框架（分支 `s8-follow-up`）：

| 檔案 | 對應 |
|---|---|
| `agf/manage.py`、`tests/test_manage.py` | 2.1 |
| `agf/evidence.py`、`examples/task.json`、`tests/test_evidence.py` | 2.3 的 `checks` |
| `agf/integrations.py`、`templates/claude-permissions.example.json`（新）、`tests/test_integrations.py` | 2.10 |
| `templates/project-rules.md` | 2.2、2.4、2.5、2.6、2.11 |
| `adapters/claude.json` | 2.1、2.10 |
| `docs/workflow.md` | 2.3、2.6、2.7、2.8 |
| `docs/cli.md` | 2.1、2.3、2.10 |
| `evals/README.md` | 2.3 |
| `evals/host/`（新）：`README.md`、`run_claude.py`、`trigger.py`、`preflight.py`、`usage.py`、結果摘要；`tests/test_eval_host.py`（新） | 2.2、2.3、2.9、2.12 |

本專案：

| 檔案 | 對應 |
|---|---|
| `CLAUDE.md` | 2.1 的 import、2.2 的 Skill 工具；順便更新兩處過期的說法（「新增本交接文件使來源指紋改變」、改進建議的連結改指 S8 報告） |
| `docs/HANDOFF_CLAUDE.md` | 2.3 |
| `.claude/skills/write-bug-lesson/SKILL.md` | 2.5 |
| `.claude/settings.json` | 2.10 |
| `docs/ROADMAP.md` | 這個階段的一列；2.7 每階段流程加「模型分工」 |
| `docs/FRAMEWORK_EXPERIENCE_LOG.md` | 當下追記 |
| `framework-study/changes/`（這份規格、結果、原始串流的摘要）、`framework-study/README.md` | 紀錄 |

## 4. 模型分工

| 工作 | 模型 | 為什麼 |
|---|---|---|
| 框架與本專案的修改、測試、結果 | Opus 5.5（我） | S8 的分析也是我寫的，前後一致 |
| 2.2 重跑的受試 session | Sonnet 5.5 | 和 S8 條件相同，才能比 |
| 框架分支的獨立審查 | Sonnet 5.5 子代理，用 `review-change` | 換一個模型看；只給差異和規格，不給我的結論 |
| 2.2 成果的盲評 | Opus 5.5 子代理 | 沿用 S8 的評分方法；S8 框架組和這次的成果隨機標成 X、Y |

## 5. 費用

- CLI 的 session：2.2 六次（約 0.6～0.8 美元），2.1 與 2.10 的探測四次（約 0.2 美元），合計約 1 美元（CLI 估算）。
- 兩個子代理用這個對話的額度。

## 6. 驗收條件

- 框架分支：`python -m unittest discover -s tests -v` 全部通過，新測試要先在 HEAD 上失敗；`agf audit` 0 個錯誤；`agf check --profile full` PASS。
- 合併預演沒有衝突。
- 2.1 的探測：改前答不出，改後答得出。2.10 的探測：Write 被拒絕。
- 2.2 的重跑：四個數字和 S8 並列，照實寫。
- 審查找到的問題，修好，或寫下不修的理由。
- 本專案：`scripts/status.py` 顯示 `source changed` 是預期中的事（S9 從 P00 重跑）。完成後 commit，打 tag `s8-framework-changes`。

## 7. 驗不到的

- Windows：框架的 CI 會在 Windows 跑，但要 push 之後才會跑；本機只能驗 WSL。
- Python 3.11、3.13：CI 用這兩版，本機只有 3.14.4。
- Claude Code 以外的宿主：沒有登入，2.2 的新句子只在 Claude 上驗證。
- 每格只跑一次：2.2 的差異可能是雜訊。

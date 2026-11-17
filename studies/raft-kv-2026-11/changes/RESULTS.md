# S8 後續：依報告修改框架的結果

2026-11-16。實作 `claude-opus-5-5`；受試 session 與獨立審查 Sonnet 5.5；盲評 Opus 5.5。規格：[SPEC.md](SPEC.md)（已核准）。
框架只改在分支 `s8-follow-up`（worktree `/home/user/src/agf-worktrees/s8-follow-up`，從 `2569a91` 開始），沒有 merge，沒有 push。

## 先說結論

- **規則入口接上了。** `project status` 會指出沒接上的入口；本專案的 `CLAUDE.md` 加了 import 之後，全新 session 讀得到協作約定，改之前讀不到。
- **skill 改走宿主的機制，但用得更少。** 重跑實驗 A 的 6 個情境：Skill 工具從 0 次變 2 次，也不再去讀 `.agents/skills` 的副本；可是該用 skill 的 4 個情境只用到 1 個（S8 是 3 個）。每格只跑一次，這可能是雜訊，但方向和預期相反，照實寫。
- **最重要的發現不在規格裡：本專案的 deny 規則在這整個對話裡從沒生效。** 這個 session 的 Claude Code 是在 `/home/user/src` 啟動的，子目錄的 `.claude/settings.json` 不會被載入（探測證實），在專案裡執行 `git push -h` 也沒有被擋。「框架唯讀」「不 push」一直只靠模型自己遵守。要怎麼補，見最後一節。
- **權限的實際行為和預想不同。** 探測 10 次後，文件只寫實測過的：Read、Edit、Write 的路徑規則有效，`cp` 寫進被保護的路徑也會被擋，`python3 -c` 卻寫得進去；`git -C . push` 繞得過 `Bash(git push:*)`；沒有允許 Bash 時，`find`、`head` 照樣會在工作目錄裡執行。
- **獨立審查找到 10 項問題**，包括 `usage.py` 會把任意字原樣輸出的隱私問題，全部修正並補測試。

## 框架分支

| commit | 內容 | 規格 |
|---|---|---|
| `762ccb5` | `project status` 檢查各宿主的入口有沒有接上規則；安裝提示寫出要加的那一行 | 2.1 |
| `cd2c101` | 交接要寫接手者自己執行的命令；`task record` 的 `checks`；Claude 原生權限範本 | 2.3、2.10 |
| `90bba83` | 規則樣板：skill 用宿主的機制叫用、列出 `agf` 子命令、先查已有能力、寫作前讀指引；刪減重複的細節；`workflow.md` 三段 | 2.2、2.4～2.8、2.11 |
| `d174014` | `evals/host/`：`run_claude.py`、`preflight.py`、`trigger.py`（含 `stop`）、`usage.py` | 2.2、2.3、2.9、2.12 |
| `c981eb5` | 依獨立審查與補做的探測修正 | — |
| 最後一個 | `evals/host/results-2026-11-16.md`（只有總數） | 2.2 |

- 測試：242 個（WSL、Python 3.14，6 個略過），每次修改的新測試都先在前一版失敗；`agf audit` 0 個錯誤；`agf check --profile full` PASS。失敗紀錄在 `artifacts/audit/s8-follow-up/red-*.txt`。
- 合併預演：在框架目錄外另 clone 一份，套上你未 commit 的修改並 commit，再 merge 這個分支：沒有衝突，合併後 `agf check --profile full` PASS（`artifacts/audit/s8-follow-up/merge-rehearsal.txt`）。
- 你的框架工作目錄：開工前後的 HEAD、`git status` 與未提交差異的雜湊完全相同（`artifacts/audit/s8-follow-up/framework-before.txt`、`framework-after.txt`）。

## 逐項結果

### 2.1 規則入口

| 檢查 | 改前 | 改後 |
|---|---|---|
| 分支的 `project status`（唯讀） | `CLAUDE.md`：`mentioned`，一條警告 | `imported`，沒有警告 |
| 全新、不給工具的 session：「專案協作約定」的第一句 | 答不出 | 逐字引用 |
| 同上：`AGENTS.md` 本身有沒有載入 | 沒有 | 沒有 |

改完之後，這個 session 自己的系統訊息也出現了規則全文。Claude Code 2.1.325 在預設設定下不會自己讀 `AGENTS.md`，這點已記進框架的轉接設定。

### 2.2 skill 的叫用方式與觸發回歸

框架來源用合併預演的那份（你的未提交修改＋這個分支），因為 S8 當時用的也是含未提交修改的工作目錄；其餘條件和 S8 相同。Bash 沒有拿掉，也和 S8 相同。

| | S8 的框架組（舊規則） | 重跑（新規則） |
|---|---|---|
| Skill 工具的呼叫 | 0 | 2 |
| 自己讀 `.agents/skills` 副本 | 3 | 0 |
| 該用的 4 個情境用到預期的 skill | 3（都是讀檔） | 1（`trace-without-lesson`，經 Skill 工具） |
| 叫錯 skill | 0 | 1（`learning-with-trace` 叫了 `trace-code`，預期 `guide-learning`） |
| 不該用的 2 個誤觸 | 0 | 0 |
| 6 次費用（CLI 估算） | 0.638 美元 | 0.603 美元 |
| 6 次 token 合計 | 670,167 | 574,969 |

沒有框架的對照組（S8 同一輪）：0.457 美元、533,981 token。

`flaky-repeat-evidence` 與 `cleaned-copy-is-not-original` 這次完全沒用 skill：前者只試了一次 `ls`（被拒）就直接作答；後者用 Grep 和 Read 看完材料就作答。我的推論：舊規則叫模型「讀取」skill，模型就去目錄裡找檔案讀；新規則把判斷交給宿主的 Skill 工具，模型只在描述明顯對上時才叫用。要確認，得重複並交錯順序。

成果品質的盲評見下一節：重跑少了 4 分，主要在沒用到 skill 的那一題。

### 2.3 交接的核對命令、評測的預檢

- `workflow.md` 的交接段落、`task record` 的 `checks`（`task handoff` 放在最前面，措辭是「作者建議的核對，在你的任務與權限內才執行」）。
- `preflight.py` 的測試重現了 S8 的兩次缺陷（入口檔裡的絕對路徑、旁邊留著另一組的目錄），兩次都被抓到；重跑的 6 次執行前都通過預檢。
- 本專案：交接文件「一開始先做什麼」的每條命令都寫了預期結果，`cd` 的絕對路徑拿掉了。

### 2.4～2.8 規則與指引的文字

規則樣板加了 `agf` 子命令一行、先查已有能力、寫作前讀 writing 指引；`workflow.md` 加了先查已有能力、規格寫明模型分工、「完成」要有產物。
這些只做了校閱，沒有單獨量效果；重跑的 6 次裡沒有 session 用到 `agf`（受試者只有 Read、Grep、Glob、Skill）。
本專案的 `write-bug-lesson` skill 第一步改成先讀寫作指引；路線圖的每階段流程要求規格寫「模型分工」，這份規格照做了（第 4 節）。

### 2.9 用 PID 停止

`trigger.py stop` 先確認 PID 屬於 `trigger.py run` 才送 SIGTERM，已完成的結果保留；測試含「PID 對不上時不送訊號」。這次重跑順利結束，沒有用到。

### 2.10 權限

在暫存目錄跑了 10 次 headless session（Sonnet 5.5，共 0.53 美元；`probes/probe_permissions.py`，原始紀錄在 `artifacts/runs/s8-follow-up/perm/`）。

| 情況 | 結果 |
|---|---|
| Write、Edit 寫進被保護的目錄 | 被擋 |
| `cp` 到被保護的目錄／到其他目錄 | 被擋／成功 |
| `python3 -c` 寫進被保護的目錄 | 成功（擋不住） |
| 重導向 `>`（只允許 `Bash(echo:*)`） | 寫到不受保護的目錄也被拒，所以看不出禁止規則本身擋不擋 |
| Read 的規則對 Grep | 被擋 |
| `git push`、`gh pr create --help`、`glab mr create --help` | 被規則擋下 |
| `git -C . push` | 沒被 `Bash(git push:*)` 擋下，照樣執行 |
| 從上層目錄啟動，寫進子目錄被保護的路徑 | 成功：子目錄的設定沒有載入 |
| 載入使用者設定（含 RTK hook）時的 `Bash(git push:*)` 允許規則 | 沒有生效；不載入時有效（原因沒有拆開確認） |
| 允許的工具裡沒有 Bash：`find . -type f \| head` | 照樣執行（有無使用者設定都一樣） |
| 同上：`cat ../outside.txt` | 被拒 |
| `--disallowedTools Bash` | Bash 整個消失 |
| `--restricted`：Read、Glob 工作目錄外的檔 | 被拒 |

另外掃了 S8 與這次的所有事件串流：沒有允許 Bash 時實際執行過的 Bash，S8 有 1 次、這次有 2 次，都是在自己工作目錄裡的 `find`，沒有讀到外面。框架的評測工具因此預設拿掉 Bash。
本專案：`.claude/settings.json` 補了 `Write` 的規則，`CLAUDE.md` 註明這些規則只在從專案目錄啟動時生效。

### 2.11 常駐規則的成本

S8 的原始串流顯示，框架組的第一回合比對照組多約 2,193 個 token，估計佔一次 session 費用的 7.4%～10.8%（平均 9.3%；`measure_always_loaded.py`），超過規格定的 5%。
所以刪了四條細節已寫在 tools、writing 指引的規則，保留觸發用語與禁止事項；特殊權限那一句一字未動。加上新句子後，樣板從 1,223 字變成 1,284 字。
重跑時第一回合多約 2,250 個 token，比 S8 多約 57 個。總 token 少了 14%，原因是沒再讀 `SKILL.md`，不是刪減。

### 2.12 本機的使用次數

`usage.py` 掃這台機器 12 份 Claude Code 對話紀錄（`results/usage-2026-11-16.json`，只有總數）：Skill 工具叫用 `review-change` 4 次、其他 skill 1 次；讀 `SKILL.md` 2 次；`agf` 子命令 `project` 16、`audit` 6、`check` 3、`profile` 2 次，其他 10 個子命令 0 次。
第一版的數字是錯的（`review-change` 8 次、`run` 4 次）：接續的 session 會把先前的訊息複製進新檔，造成重複計算；heredoc 裡的說明文字與 `run --help` 也被算進去。對照真實紀錄時發現，已修正並補測試。

## 獨立審查

審查者是另開的 Sonnet 5.5 子代理，只拿到差異、規格與探測的原始紀錄，照 `review-change` 做（報告 `artifacts/audit/s8-follow-up/review-raw.md`）。

| 發現 | 處理 |
|---|---|
| F1 預檢的環境變數檢查不可能失敗 | 明確傳入的也會擋下，只有 `--allow-env` 點名的才放行；測試含「誤留變數」的情況 |
| F2 `usage.py` 會原樣輸出任意字 | 只認得已知的子命令；測試確認私人字詞不會出現 |
| F3 權限說法超出探測 | 補探測 Grep、Edit、PR／MR、`git -C`、重導向的對照；文件改成逐項的 `observed` 與 `not_observed` |
| F4 import 多追一層 | 改成五層，補層數測試 |
| F5 `checks` 的措辭像命令 | 改成「在你的任務與權限內才執行」 |
| F6 Windows 少了系統變數 | 補上；沒有 Windows 可以驗證 |
| F7 模型 ID 寫死 | `--model` 改成必填 |
| F8 預檢靜默略過的情況 | 報告列出搜尋了哪些路徑、哪些檔讀不了；shared 模式下規則檔裡的框架路徑是設計如此，寫進 README |
| F9 import 含 NUL 會丟例外 | 略過這種 token，補測試 |
| F10 其他（`--since`、沒有 git、共用 PID 檔、`denied` 的名稱、少檢查的檔名） | 全部修正 |

## 盲評

看不到組別的 Opus 5.5 子代理，照 S8 的量表評分（`grading/grades-raw.json`；X／Y 的對應在 `grading/packets.json`，種子 20261117）：**S8 的框架組 48／48，重跑 44／48**。
扣分都在重跑：`trace-without-lesson` 範圍扣 1（多了請求沒要的補充）；`flaky-repeat-evidence` 得 3／1／1（沒用 context.txt，還建議在未確認付款請求能否安全重複之前批次重跑）。後者正是 S8 讀了 `debug-root-cause`、這次沒用任何 skill 的那一題。評分者和實作者是同一個模型；S8 當時的另一位評分者給同一批 S8 成果 47／48，評分本身也有約 1 分的差異。

## 費用

CLI 估算共 1.19 美元、18 次 session：規則探測 2 次（0.05）、權限探測 10 次（0.53）、重跑 6 次（0.60）。規格估約 1 美元，多出的是補做的權限探測。兩個子代理用這個對話的額度。

## 沒驗證的

- Windows，以及 CI 用的 Python 3.11 與 3.13（本機只有 3.14.4）。
- Claude Code 以外的宿主。
- 每格只跑一次：2.2 的差異可能是雜訊。
- `--restricted` 會不會改變 skill 與 `CLAUDE.md` 的載入。
- 只靠禁止規則時，重導向擋不擋得住。

## 要你決定的事

（2026-11-16 使用者回「全部依你建議」，執行結果見下一節。）

1. **讓 deny 規則真的生效。** 這個對話從 `/home/user/src` 啟動，專案的設定沒有載入。可以改從專案目錄啟動 Claude Code，或把規則放進 `/home/user/src/.claude/settings.json`（從那裡啟動的 session 會載入）或使用者層的 `~/.claude/settings.json`。後兩個會影響其他專案，所以沒有替你改。另外，`git -C . push` 這類寫法繞得過前綴規則。
2. **框架分支要不要 merge。** 預演顯示：先 commit 你的 10 個修改，再 merge，沒有衝突。merge 後在本專案跑一次 `agf project update --target . --host claude`，部署的規則才會換成新句子。
3. **skill 叫用的措辭。** 新措辭讓 skill 走宿主的機制，但這次用得比較少。可以先重複幾輪再決定，或改成更明確的說法（例如「列出的 skill 符合任務時就要叫用」），再用同一個工具量。

## 使用者決定之後（2026-11-16，「全部依你建議」）

### 1. deny 規則放到啟動目錄

新增 `/home/user/src/.claude/settings.json`，內容和本專案的規則相同（擋框架目錄的 Edit 與 Write、`git push`、`rtk git push`、`gh pr create`），另加 `glab mr create`。
從 `/home/user/src` 啟動的全新 session 跑 `git push -h`，被規則擋下（`probes/probe_start_dir_settings.py`，0.05 美元）。這個對話本身沒有重新載入設定，同一個命令照樣執行，所以要等下一個 session 才受保護。
這個檔影響所有從 `/home/user/src` 啟動的 session：Claude 在那裡都不能 push，也不能用 Edit、Write 改框架目錄（要改框架時，像這次一樣在框架目錄外開 worktree）。`git -C <目錄> push` 這類寫法仍然擋不住。不要了就刪掉這個檔。

### 2. 框架分支已經併進 main

我原本建議「先 commit 你的 10 個修改再 merge」。實際動手時改用不必替你 commit 的做法：先 `git stash` 暫存那 10 個修改，`git merge --ff-only s8-follow-up` 快轉，再 `git stash pop` 放回。先在 clone 裡預演：結果和「commit 後 merge」逐位元組相同（156 個檔），完整檢查通過。
實際執行後：main 快轉到 `1651661`；10 個修改仍是未提交的狀態，檔案清單和開工前相同；暫存清單是空的；156 個受追蹤的檔和預演逐位元組相同。分支 `s8-follow-up` 與它的 worktree 已刪除。
接著在本專案跑 `agf project update`（沿用記錄的宿主 claude、codex）：只更新了 `project-rules.md` 與 `guides/workflow.md`，`project status` 乾淨、沒有警告。

### 3. skill 措辭：先登記，再量

改成更明確的說法（框架分支 `s8-skill-wording`）：

> 追程式、除錯、審查差異、帶讀論文或規格、教學時，先看宿主列出的 skill：描述符合這次任務的，動手前就用宿主的機制叫用（例如 Claude Code 的 Skill 工具），不要因為自己也做得到就跳過；不另外讀 `.agents/skills/` 的副本。宿主沒有列出時，才讀 `SKILL.md`。

量法：同樣 6 個情境跑兩輪，條件和第一次重跑相同（Sonnet 5.5、`Read Grep Glob Skill`、不拿掉 Bash、框架來源是 main 加上你的未提交修改，再加這個措辭）。

判斷標準（開跑前寫下）：兩輪合計，該用的 8 次裡用到預期 skill 至少 6 次（舊措辭是 3／4），而且不該用的 4 次沒有誤觸，才採用新措辭；否則維持現在的措辭，照實記錄。另外把第一輪的成果和 S8 的框架組做一次盲評，只用來檢查品質有沒有回來，不改變上面的判斷。

結果：兩輪合計，該用的 8 次用到 5 次（第一輪 3、第二輪 2；經 Skill 工具 4 次，讀 `.claude/skills` 的檔 1 次），不該用的 4 次沒有誤觸；兩輪各約 0.67 美元。
**未達 6／8，照登記的標準不採用新措辭。** 第一輪的盲評：新措辭 46、S8 的框架組 47（滿分 48；`grading-wording/`）。

這個標準有缺陷：未達標時保留的「現在的措辭」只量過一輪，命中 1／4，比新措辭差。所以再登記一個比較，開跑前寫下：
現在的措辭再跑一輪，讓兩者都有兩輪。兩輪合計，新措辭的命中多於現在的措辭、兩者都沒有誤觸，就改用新措辭；否則維持現在的措辭。

結果：現在的措辭第二輪用到 3／4（全部經 Skill 工具；這次漏的是 `debug-root-cause`），0.62 美元。兩輪合計：

| 措辭 | 輪數 | 用到預期的 skill | 其中經 Skill 工具 | 誤觸 | 盲評（和 S8 的框架組比，滿分 48） |
|---|---|---|---|---|---|
| S8 的舊措辭「按任務讀取相應 skill」 | 1 | 3／4 | 0 | 0／2 | —（S8 本身） |
| 現在的措辭「宿主列出時用宿主的機制叫用」 | 2 | 4／8（1、3） | 4 | 0／4 | 44 對 48 |
| 更明確的措辭 | 2 | 5／8（3、2） | 4 | 0／4 | 46 對 47 |

照登記的比較規則，**改用更明確的措辭**：已提交到框架（`2ffd748`）、快轉併進 main，並在本專案跑了 `agf project update`。
但 5 對 4 的差距比兩輪之間的起伏（1 與 3、3 與 2）還小，不能說兩種措辭真的不同；能確定的是三種措辭都沒有誤觸，而且改寫之後 skill 都走 Skill 工具。
`learning-with-trace` 在四輪裡有三輪叫了 `trace-code` 而不是 `guide-learning`，這比措辭更像是 skill 描述的界線問題，留給之後。
量測用的 clone 與 worktree 都已刪除。這一節共 19 次 session（設定的探測 1 次、措辭的量測 18 次），約 2.01 美元；整個 S8 後續共 37 次、約 3.20 美元（CLI 估算）。

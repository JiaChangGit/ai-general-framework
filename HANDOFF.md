# 接手文件

更新日期：2026-11-18（S12 之後）。給下一個要改這個框架、或要拿它到別的專案測試的 session。
它描述寫下時的狀態；接手時先跑下面的命令核對，**以看到的為準**。

## 一開始先做什麼

```bash
git -C <框架目錄> status --short          # 預期：沒有輸出
git -C <框架目錄> log --oneline -3         # 預期：最上面是 S12 的 commit（見 CHANGELOG），或使用者之後的新 commit
python3 -B <框架目錄>/scripts/agf.py audit --root <框架目錄>      # 預期："errors": []、"warnings": []
(cd <框架目錄> && python3 -B -m unittest discover -s tests)        # 預期：OK（有幾個依平台略過）
python3 -B <框架目錄>/scripts/agf.py task checkpoint --help        # 預期：列出 --done、--doing、--next、--repo、--append
```

`<框架目錄>` 換成實際的位置。S12 在框架目錄旁的 clone `../ai-general-framework-s12`（分支 `s12-framework`）做，因為 guard hook 也擋 `git worktree add`。是否已併進 `main`，以 `git -C <框架目錄> branch --contains <S12 最後一個 commit>` 或 `git -C <框架目錄> log --oneline -5` 為準。

## 目前的位置

修改與驗證在 [CHANGELOG.md](CHANGELOG.md)；分析與排好順序的待辦在 [docs/analysis-2026-11.md](docs/analysis-2026-11.md)（S11、S12 在最後兩節）；研究與量測在 [studies/](studies/README.md)。

S12 的重點：

- **skill 描述寫明主次**：一個請求裡有兩種工作時以誰為主。上一輪選錯的兩個情境 6/6 選對；`read-research` 也第一次被用到（3/3）。
- **`project status` 提醒從上層目錄啟動的風險**（`launch_notices`）。實測（Claude Code 2.1.325，各一次）：無頭 session 從上層啟動時，子專案的 skill 與 `.claude/settings.json` 都沒有載入。同一天一個從上層啟動的桌面版 session 有列出子專案的 skill，只看過這一次。
- **`task checkpoint`**：里程碑的短紀錄，可接在既有交接檔最後。
- **`check --profile periodic`**：示範、文件命令、乾淨重建這類只跑過一次的檢查。
- **續接 hook 的 `save_prompts`**（預設關閉）：存下使用者說的話。兩個「決定只在對話裡」的任務，開了它的組 6/6，沒開的 0/6。
- **固定成本**：每個 session 一開始多讀約 2,640 tokens，規則約 1,920、skill 描述約 720。
- 量測結果：[H 報告](studies/research-2026-11/H-measurement-s12.md)。

## 拿框架到別的專案測試

使用者會在其他聊天室用這個框架做別的專案，順便測它的表現。建議的做法：

1. **配置。** 在目標專案執行 `project plan`、再 `project install ... --apply`（README「各專案只帶需要的內容」）。既有的 `CLAUDE.md` 不會被改寫，要自己加一行 `@.agf/managed/project-rules.md`，再用 `project status` 確認沒有 `warnings`，也看一下 `launch_notices`。
2. **從專案目錄啟動新的 session。** 從上一層目錄啟動時，專案的 `.claude/settings.json`（權限與 hook）不會載入；無頭模式連 skill 也看不到。
3. **要不要裝續接 hook。** 把 `templates/claude-continuity-settings.example.json` 的 `hooks` 併進專案的 `.claude/settings.json`，路徑換成框架的實際位置。要讓對話裡的決定跟著走，另外加 `UserPromptSubmit` 與 `{"save_prompts": true}` 的設定（[docs/cli.md](docs/cli.md)）；開啟前問使用者，因為對話可能有密碼或金鑰，也確認 `.agf/` 不會被 commit。
4. **要觀察的事**，每一項都記下宿主版本、模型、日期與實際看到的輸出：
   - 該用 skill 時，有沒有用宿主的機制叫用（Claude Code 的 Skill 工具）；不該用時有沒有誤觸。
   - 一開始有沒有把問題問完；問題寫得讓人看得懂嗎（名詞有解釋、選項的影響有寫）。
   - 撞到用量上限或換模型後，新 session 有沒有先讀交接檔與 `.agf/checkpoints/latest.md`。
   - guard hook 有沒有誤擋一般的工作。
5. **量測。** 比較成本用 `evals/host/impact.py`，固定模型、任務與 CLI 版本，每個條件至少跑 2～3 次，設 `--total-budget`（它是保守的：已花的加上一個 session 的上限超過總上限就停）。被額度打斷時，用 `--ids` 只補跑缺的任務、寫到新的 `--out`，再用 `impact.py report <目錄一> <目錄二> --md <檔案>` 合併；設定不同的目錄（例如一個有 `--switch-model`、一個沒有）不會合併，分開報告。受試 session 和你自己的對話用同一個額度。
6. **把結果寫回框架。** 放在 `studies/<專案名>-<年月>/`：先寫規格與要量的東西，再跑，最後寫結果與限制。不要事後憑印象補寫。

## 還沒做的事

依分析報告第三輪的優先順序：

1. **使用者**把 `s12-framework` 併進 main：`git -C <框架目錄> pull --ff-only ../ai-general-framework-s12 s12-framework`。
2. 縮短 `project-rules.md`：它是固定成本的大頭（約 1,920 tokens）。改完用 `probe-context` 量第一次呼叫的 context，再用 S11 的 8 個任務確認沒有退步。
3. `save_prompts` 要不要在使用者自己的專案開啟，由使用者決定。
4. 在 GitHub 上實際跑一次 `skill-triggers.yml`（要先 push，並設定 `ANTHROPIC_API_KEY`，會花錢）。
5. 其他 7 個觸發情境在新描述下重跑一次。
6. 教學文件格式的個人化（第二輪的建議）；子命令退場（先累積使用紀錄）。

沒有在真實 session 觸發過的：續接 hook 的 PreCompact、PostCompact、StopFailure、PreModelSwitch；`align-with-me` 的實際叫用。`debug-root-cause` 新加的「先驗證前提、附證據」沒有量測。

## 踩過的坑

- **框架的主目錄被 deny 規則與 guard hook 保護。** 工作區上一層的 `.claude/settings.json` 禁止用 Edit／Write 改框架目錄，PreToolUse 的 guard hook 也擋 push、PR、`pkill -f`，以及在框架 repo 裡的 git 寫入（包括 `worktree add`）。這是使用者刻意設的，不要去改它。使用者點名要改框架時，用 `git clone <框架目錄> ../ai-general-framework-<名稱>` 複製一份，在複本開分支修改；改完由使用者自己 `pull --ff-only` 併進 main。clone 的 `origin` 指向本機的框架目錄，不是 GitHub。
- **舊版 guard hook 會誤擋 heredoc。** 使用者把 S11 併進 main 之後已修正；如果看到 heredoc 裡的文字被當成命令擋下，先確認 main 是不是新版。
- **用量上限是共用的。** 量測的受試 session、子代理與主對話用同一個 5 小時額度；S11 的量測做到一半就撞到。無頭模式下撞到上限時，stream 裡會有 `rate_limit_event`，result 的 `subtype` 仍是 `success`，但 `is_error` 是 true。長時間的工作要能分段續跑。
- **RTK hook 會改寫 Bash 命令。** 自動權限審查偶爾因此要求原樣重送；`find -exec`、`tail -3 檔案一 檔案二` 這類寫法會被它拒絕或改壞，改用 Python 或 `tail -n 3`。需要原始輸出時用 `rtk proxy <命令>`。
- **`cd` 會延續到之後的命令**，宿主還會把主要工作目錄跟著改過去。查看別的目錄時用 `git -C` 或絕對路徑。
- **`pkill -f` 會連自己的 shell 一起殺掉**；用 PID 停行程。
- **長時間的命令**用 `setsid nohup` 和 session 分開執行，結果寫進檔案；宿主的背景命令可能有時間上限。
- **`/tmp` 在這台 WSL 上是 4.3 GB 的 tmpfs**，重開就清空，也會吃記憶體；要留的證據不要放那裡。
- **給使用者的命令不要用 `<名稱>` 這種佔位字。** bash 會把 `<` 當成讀檔，整行命令不會執行；寫出實際的值，或明說要換掉哪一段。

## 操作範圍

- 不 push、不建立 PR、不部署；這些由使用者自己做。
- 修改框架要使用者在當次對話點名；改完寫進 CHANGELOG，並更新這份交接文件。
- 與框架有關的經驗，在使用它的專案裡當下記錄（例如 Raft 專案的 `.ai/FRAMEWORK_EXPERIENCE_LOG.md`），不要事後憑印象補寫。

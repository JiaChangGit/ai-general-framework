# 接手文件

更新日期：2026-11-18。給下一個要改這個框架、或要拿它到別的專案測試的 session。
它描述寫下時的狀態；接手時先跑下面的命令核對，**以看到的為準**。

## 一開始先做什麼

```bash
git -C <框架目錄> status --short          # 預期：沒有輸出
git -C <框架目錄> log --oneline -3         # 預期：最上面是 S11 的 commit（見 CHANGELOG），或使用者之後的新 commit
python3 -B <框架目錄>/scripts/agf.py audit --root <框架目錄>      # 預期："errors": []、"warnings": []
(cd <框架目錄> && python3 -B -m unittest discover -s tests)        # 預期：OK（有幾個依平台略過）
python3 -B <框架目錄>/scripts/agf.py integration list | grep -E 'claude-(guard|continuity)'   # 預期：含 claude-guard-hook、claude-guard-settings、claude-continuity-hook、claude-continuity-settings
```

`<框架目錄>` 換成實際的位置。2026-11-18 這一輪改在分支 `s11-framework`（worktree `../ai-general-framework-s11`），是否已快轉併進 `main`，以 `git -C <框架目錄> branch --contains s11-framework` 為準。

## 目前的位置

最近幾輪的修改與驗證在 [CHANGELOG.md](CHANGELOG.md)；分析與排好順序的待辦在 [docs/analysis-2026-11.md](docs/analysis-2026-11.md)（S11 在「第二輪」一節）；研究與量測在 [studies/](studies/README.md)。

S11 的重點：

- **續接 hook**（`templates/claude-continuity-hook.py`）：額度用完、壓縮、session 結束、換模型時寫 checkpoint；新 session 開始時提示先讀交接檔。設定範例在 `templates/claude-continuity-settings.example.json`，用法在 [docs/cli.md](docs/cli.md)。
- **成效量測**（`evals/host/impact.py`）：有框架與沒框架配對比較。第一次的結果：計畫 32 次完成 27 次，兩組都全過，框架組多花 20%～45%（[G 報告](studies/research-2026-11/G-measurement-2026-11-18.md)）。
- **觸發量測的 CI**（`.github/workflows/skill-triggers.yml`）：只能手動執行，還沒在 GitHub 上跑過。
- **問問題的規則**：一開始就問完，每題寫給沒有背景的人看。

## 拿框架到別的專案測試

使用者會在其他聊天室用這個框架做別的專案，順便測它的表現。建議的做法：

1. **配置。** 在目標專案執行 `project plan`、再 `project install ... --apply`（README「各專案只帶需要的內容」）。既有的 `CLAUDE.md` 不會被改寫，要自己加一行 `@.agf/managed/project-rules.md`，再用 `project status` 確認沒有 `warnings`。
2. **要不要裝續接 hook。** 把 `templates/claude-continuity-settings.example.json` 的 `hooks` 併進專案的 `.claude/settings.json`，路徑換成框架的實際位置。量測顯示它在「狀態都在檔案裡」的任務沒有省到錢，價值在重要資訊只存在對話裡的情況；裝了之後請記下它有沒有幫上忙。
3. **從專案目錄啟動新的 session。** 從上一層目錄啟動時，專案的 skill 不會出現在 skill 清單裡，專案的 `.claude/settings.json`（包括 hook）也不會載入。
4. **要觀察的事**，每一項都記下宿主版本、模型、日期與實際看到的輸出：
   - 該用 skill 時，有沒有用宿主的機制叫用（Claude Code 的 Skill 工具）；不該用時有沒有誤觸。複合任務（一個請求裡有兩種工作）特別容易選錯。
   - 一開始有沒有把問題問完；問題寫得讓人看得懂嗎（名詞有解釋、選項的影響有寫）。
   - 撞到用量上限或換模型後，新 session 有沒有先讀交接檔與 `.agf/checkpoints/latest.md`。
   - guard hook 有沒有誤擋一般的工作。
5. **量測。** 要比較成本時用 `evals/host/impact.py`，固定模型、任務與 CLI 版本，每個條件至少跑 2～3 次，設 `--total-budget`。被額度打斷時，用 `--ids` 只補跑缺的任務、寫到新的 `--out`，再用 `impact.py report <目錄一> <目錄二> --md <檔案>` 合併。受試 session 和你自己的對話用同一個額度。
6. **把結果寫回框架。** 放在 `studies/<專案名>-<年月>/`：先寫規格與要量的東西，再跑，最後寫結果與限制。不要事後憑印象補寫。

## 還沒做的事

依分析報告第二輪的優先順序：

1. **使用者**把 `s11-framework` 快轉併進 main（`git -C <框架目錄> merge --ff-only s11-framework`）。工作區上一層裝的 guard hook 讀的是主目錄的檔案，併進去之後才會換成新版（不誤擋只是資料的 heredoc，也補上審查找到的繞過）。
2. 成效量測加 2～3 個「沒框架容易做錯」的任務，特別是重要資訊只在第一段對話裡的續接任務。
3. 拆開量固定成本：只裝規則、只裝 skill、全部都裝。
4. 複合任務的 skill 描述各加一句「以誰為主」，再跑觸發量測。
5. 在 GitHub 上實際跑一次 `skill-triggers.yml`（需要使用者設定 `ANTHROPIC_API_KEY` secret，會花錢）。
6. 教學文件格式的個人化（分析報告有建議，沒有實作）。
7. 第一輪留下的：`project status` 偵測從上層啟動、`debug-root-cause` 先驗證前提、`task record --checkpoint`、品質範本的「定期」檔位、子命令退場。

沒有在真實 session 觸發過的：續接 hook 的 PreCompact、PostCompact、StopFailure、PreModelSwitch；`align-with-me` 的實際叫用。

## 踩過的坑

- **框架的主目錄被 deny 規則與 guard hook 保護。** 工作區上一層的 `.claude/settings.json` 禁止用 Edit／Write 改框架目錄，PreToolUse 的 guard hook 也擋 push、PR、`pkill -f` 與寫入框架目錄；這是使用者刻意設的，不要去改它。使用者點名要改框架時，在框架目錄外開 worktree（`git -C <框架目錄> worktree add ../ai-general-framework-<名稱> -b <分支>`），改完由使用者自己快轉併進 main。
- **舊版 guard hook 會誤擋 heredoc。** 併進 main 之前，heredoc 或字串裡只要出現 push 的寫法（例如 Markdown 裡引用的命令）就會被擋。先用 Write 寫成檔案，再執行那個檔案。
- **用量上限是共用的。** 量測的受試 session、子代理與主對話用同一個 5 小時額度；這一輪量測做到一半就撞到。無頭模式下撞到上限時，stream 裡會有 `rate_limit_event`，result 的 `subtype` 仍是 `success`，但 `is_error` 是 true。長時間的工作要能分段續跑。
- **RTK hook 會改寫 Bash 命令。** 自動權限審查偶爾因此要求原樣重送；`find -exec` 這類寫法會被它拒絕，改用 Python。需要原始輸出時用 `rtk proxy <命令>`。
- **`cd` 會延續到之後的命令**，宿主還會把主要工作目錄跟著改過去。查看別的目錄時用 `git -C` 或絕對路徑。
- **`pkill -f` 會連自己的 shell 一起殺掉**；用 PID 停行程。
- **長時間的命令**用 `setsid nohup` 和 session 分開執行，結果寫進檔案；宿主的背景命令可能有時間上限。
- **`/tmp` 在這台 WSL 上是 4.3 GB 的 tmpfs**，重開就清空，也會吃記憶體；要留的證據不要放那裡。

## 操作範圍

- 不 push、不建立 PR、不部署；這些由使用者自己做。
- 修改框架要使用者在當次對話點名；改完寫進 CHANGELOG，並更新這份交接文件。
- 與框架有關的經驗，在使用它的專案裡當下記錄（例如 Raft 專案的 `.ai/FRAMEWORK_EXPERIENCE_LOG.md`），不要事後憑印象補寫。

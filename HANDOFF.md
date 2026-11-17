# 接手文件

更新日期：2026-11-17。給下一個要改這個框架、或要拿它到別的專案測試的 session。
它描述寫下時的狀態；接手時先跑下面的命令核對，**以看到的為準**。

## 一開始先做什麼

```bash
git -C <框架目錄> status --short          # 預期：沒有輸出
git -C <框架目錄> log --oneline -3         # 預期：最上面是 S10 的 commit（見 CHANGELOG），或使用者之後的新 commit
python3 -B <框架目錄>/scripts/agf.py audit --root <框架目錄>      # 預期："errors": []、"warnings": []
(cd <框架目錄> && python3 -B -m unittest discover -s tests)        # 預期：OK（有幾個依平台略過）
python3 -B <框架目錄>/scripts/agf.py integration list | grep claude-guard   # 預期：兩行 claude-guard-*
```

`<框架目錄>` 換成實際的位置。2026-11-17 這一輪改在分支 `s10-framework`（worktree `../ai-general-framework-s10`），是否已快轉併進 `main`，以 `git -C <框架目錄> branch --contains s10-framework` 為準。

## 目前的位置

最近三輪的修改與驗證在 [CHANGELOG.md](CHANGELOG.md)；分析與排好順序的待辦在 [docs/analysis-2026-11.md](docs/analysis-2026-11.md)；研究材料在 [studies/](studies/README.md)。

## 拿框架到別的專案測試

使用者打算在其他聊天室用這個框架做別的專案，順便測它的表現。建議的做法：

1. **配置。** 在目標專案執行 `project plan`、再 `project install ... --apply`（README「各專案只帶需要的內容」）。既有的 `CLAUDE.md` 不會被改寫，要自己加一行 `@.agf/managed/project-rules.md`，再用 `project status` 確認沒有 `warnings`。
2. **從專案目錄啟動新的 session。** 從上一層目錄啟動時，專案的 skill 不會出現在 skill 清單裡，專案的 `.claude/settings.json` 也不會載入（S8 與 S10 都看到）。
3. **要觀察的事**，每一項都記下宿主版本、模型、日期與實際看到的輸出：
   - 該用 skill 時，有沒有用宿主的機制叫用（Claude Code 的 Skill 工具）；不該用時有沒有誤觸。可用 `evals/host/trigger.py` 跑固定的情境。
   - 打 `/align-with-me` 時，是否一輪最多四題、每題附建議、確認後才動手。
   - 裝了 guard hook 之後，push、建立 PR、`pkill -f`、寫入受保護路徑是否被擋，一般的工作有沒有被誤擋。
   - 開多個子代理或跑長時間的工作之前，是否先寫交接檔；換模型或額度恢復後，是否先讀交接檔。
   - 用量：`evals/host/usage.py` 讀 CLI 回報的 token 與費用；比較時固定模型與任務，每個條件至少跑兩次。
4. **把結果寫回框架。** 放在 `studies/<專案名>-<年月>/`，照 `studies/raft-kv-2026-11/` 的格式：先寫規格與要量的東西，再跑，最後寫結果與限制。不要事後憑印象補寫。

## 還沒做的事

依分析報告的優先順序：

1. guard hook 要不要裝進使用者層級的 `~/.claude/settings.json`：**要由使用者決定**，影響所有 session。
2. `agf project status` 偵測「session 可能從上層目錄啟動、skill 不會被列出」。
3. 用 S8 的方法，量新規則與舊規則的成本與品質。
4. `debug-root-cause` 加「先驗證前提、宣稱成功要附證據」。
5. `agf task record --checkpoint` 的快速模式。
6. 品質範本加「定期」檔位（示範、文件命令、乾淨重建）。
7. 子命令用量紀錄與退場。

`align-with-me` 還沒在宿主上實際叫用過；guard hook 只在 Linux 的 Claude Code 2.1.325 實測過一次，沒有在使用者層級、Windows 或其他宿主上試過。

## 踩過的坑

- **框架的主目錄被 deny 規則保護。** `/home/user/src/.claude/settings.json`（工作區上一層）禁止用 Edit／Write 改框架目錄；這是使用者刻意設的，不要去改它。使用者點名要改框架時，在框架目錄外開 worktree（`git -C <框架目錄> worktree add ../ai-general-framework-<名稱> -b <分支>`），改完經使用者同意再快轉併進 main。
- **RTK hook 會改寫 Bash 命令。** 自動權限審查偶爾因此要求原樣重送；`find -exec` 這類寫法會被它拒絕，改用 Python。需要原始輸出時用 `rtk proxy <命令>`。
- **`cd` 會延續到之後的命令**，宿主還會把主要工作目錄跟著改過去。唯讀查看別的 repo 時用 `git -C` 或絕對路徑。
- **`pkill -f` 會連自己的 shell 一起殺掉**；用 PID 停行程。
- **長時間的命令**（例如 45 分鐘的驗收）用 `setsid nohup` 和 session 分開執行，結果寫進檔案；宿主的背景命令可能有時間上限。
- **`/tmp` 在這台 WSL 上是 4.3 GB 的 tmpfs**，重開就清空，也會吃記憶體；大型建置與要留的證據不要放那裡。
- **用量上限。** 同時開 4 個子代理的那次，幾小時內就撞到 5 小時上限。被打斷的子代理可以用 SendMessage 接著做，不必重開。

## 操作範圍

- 不 push、不建立 PR、不部署；這些由使用者自己做。
- 修改框架要使用者在當次對話點名；改完寫進 CHANGELOG，並更新這份交接文件。
- 與框架有關的經驗，在使用它的專案裡當下記錄（例如 Raft 專案的 `.ai/FRAMEWORK_EXPERIENCE_LOG.md`），不要事後憑印象補寫。

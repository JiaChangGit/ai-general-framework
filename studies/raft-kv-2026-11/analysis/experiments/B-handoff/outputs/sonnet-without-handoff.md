## 接手核對報告

**限制**：Bash 在這個 session 被拒絕（don't ask 模式）。我沒有執行 `git status`、`scripts/status.py`，也沒有查機器負載。下面只包含我用 Read、Glob、Grep 看到的內容，沒看到的我會標明。

### 與 CLAUDE.md 的出入
- CLAUDE.md 要我先讀的 `docs/HANDOFF_CLAUDE.md`，這個 checkout 裡沒有。`docs/` 底下有 25 個檔案，沒有任何檔名含 HANDOFF。
- 所以我只能依 CLAUDE.md 本身、`docs/ROADMAP.md` 的片段和 `scripts/status.py` 做核對。
- 該文件的缺席本身要當成需要核對的事。可能是 experiment 分支刻意移除，也可能是漏了。我無法判斷是哪一種。
- 檔案位置也不一致。CLAUDE.md 寫專案在 WSL 的 `/home/user/src/Distributed_Key-Value_Store_with_Raft`，目前工作目錄卻是 `/tmp/claude-1000/.../sonnet-without-handoff`。

### 工作樹的未提交變更
- 開始時的 gitStatus 快照是 `clean`，所以沒有未提交變更。
- 我沒法用 `git status` 重新確認。
- 目前在 `experiment` 分支，最新提交是 `a104a51 Experiment B snapshot`。`main` 在這之前。

### Tag（讀自 `.git/packed-refs`）
共 10 個：
- `s0-foundation-verified`
- `s1-storage-format-verified`
- `s1-s4-review-verified`
- `s2-snapshot-compaction-verified`
- `s3-read-index-verified`
- `s4-membership-verified`
- `s5-performance-verified`
- `s6-review-fixes-verified`
- `s7-zh-style-prototype`
- `v1-baseline-verified-20261112`

沒有 S8 的 tag，與 CLAUDE.md 一致：S0～S7 完成，S8 尚未開始。

### `scripts/status.py` 的意義
- 我只讀了原始碼，沒有執行。
- 它對 `acceptance/final.json` 的每個階段讀 `phase-*.last-attempt.json`。
- 它拿 receipt 的 `source_fingerprint` 和目前來源的指紋比較，印出 `current source` 或 `source changed / not run`。
- 所以輸出的 PASS 只有在標示 `current source` 時，才代表目前來源通過。
- 依 ROADMAP，S7 加了檔案、指紋已改變，P00～P15 預期會顯示 `source changed`。這不是驗收失敗，要到 S9 收尾從 P00 完整重跑。
- 我沒看到實際輸出，不能報告各階段的真實狀態。

### 機器是否安靜
沒有核對。我需要 `ps` 或 `uptime` 才能看有沒有殘留的叢集、cargo 或測試程序，這要 Bash 權限。

### 下一步
- 依 CLAUDE.md，下一個是 S8（框架分析與對照實驗）。
- 開始前要先寫規格並取得使用者同意。依據在 ROADMAP「S7、S8 的依據」，使用者原文在第 42 行附近。
- 計畫是：依使用者的標準逐項寫優缺點和改進建議，證據來自經驗紀錄、兩次獨立審查和框架原始碼，另做 2～3 個可重複的小型對照實驗。
- 實驗在暫存副本做。樣本小，設計與評分是同一方，結論只能當方向。

### 不能做的事
- 修改相鄰的 `ai-general-framework`，它是唯讀的。`.claude/settings.json` 以 deny 規則擋下它的寫入。
- push、建立 PR、部署。deny 規則擋了 `git push` 和 `gh pr create`。
- 覆寫三份原始規格，或降低要求來通過 gate。
- 直接修改 `.claude/skills/` 與 `.agents/skills/` 的副本，它們由框架管理。
- 使用既有 Raft 函式庫、`unsafe`、lease。
- 把舊 receipt 當成目前來源的通過證據。
- 沒有先取得同意就開始 S8。
- 動 S8 以外的 Raft 行為。S8 本身不改 Raft。

### 需要你決定
1. 是否給 Bash 唯讀權限，讓我執行 `git status`、`git tag`、`scripts/status.py` 和 `ps`、`uptime`，補完上面沒核對的部分？
2. `docs/HANDOFF_CLAUDE.md` 缺失是否符合預期？

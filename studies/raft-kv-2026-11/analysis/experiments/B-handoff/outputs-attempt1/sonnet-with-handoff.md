## 接手核對結果

我只讀了檔案、跑了唯讀命令，沒有改任何東西。

**工作樹**
- `git status --short` 沒有輸出，所以沒有未提交的變更。
- 目前在 `experiment` 分支，HEAD 是 `be46e8f`（Experiment B snapshot）。
- 往前是 S7 的兩個 commit：`6ed8d49`、`c0064da`。
- `.venv` 是指向 `/home/user/src/Distributed_Key-Value_Store_with_Raft/.venv` 的符號連結。

**Tag**
- 共 10 個：`s0-foundation-verified`、`s1-storage-format-verified`、`s1-s4-review-verified`、`s2-snapshot-compaction-verified`、`s3-read-index-verified`、`s4-membership-verified`、`s5-performance-verified`、`s6-review-fixes-verified`、`s7-zh-style-prototype`、`v1-baseline-verified-20261112`。
- 交接文件要求的 `s6-review-fixes-verified`（指向 `36431ad`）和 `s7-zh-style-prototype`（指向 `6ed8d49`）都在。
- 也就是說，S6 曾通過完整驗收，S7 已完成。
- 這些 tag 不是我驗證出來的，是照 tag 的存在和交接文件的說法判斷。

**`scripts/status.py` 的結果**
- P00～P08、P10～P15 全部顯示 `PASS [source changed / not run]`，最近一次驗收是 2026-11-15 的 15:45～16:12。
- 「PASS」是當時那次驗收通過。
- 「source changed」表示來源指紋已變，這些 receipt 不能當成目前來源通過的證據。
- 交接文件說這是預期的：S7 加入了 `framework-study/`、交接文件也改過，這些都計入指紋。
- Raft 的驗收結果對應 `s6-review-fixes-verified` 那個 commit。S9 收尾時要從 P00 重跑。
- 我沒有重跑驗收，所以目前來源是否仍通過，沒有驗證。

**機器是否安靜**
- 大致安靜：`uptime` 的 load average 是 0.23／0.13／0.04。
- CPU 排行前五都是 Claude 的行程（`2.1.325-1ef04b3`），其中第一名 17.1% 是剛啟動 8 秒的行程，很可能是這次檢查本身。
- 交接文件說 WSL 常有 `dockerd` 和 `containerd` 各佔約一顆 CPU，這次排行裡沒有看到。
- 如果之後要做效能量測或驗收，開始前還是要再看一次。

**下一步**
1. 起草 S8（框架分析與對照實驗）的規格給使用者看，先不要實作。
2. 依據：`docs/ROADMAP.md` 的「S7、S8 的依據」（使用者原文）、`framework-study/zh-style/report.md`、`docs/FRAMEWORK_EXPERIENCE_LOG.md`（L01～L53）、兩份獨立審查，以及框架原始碼（唯讀）。
3. 規格要逐項寫框架的優點、缺點和改進建議，並提出 2～3 個小型對照實驗。候選是「skill 或指引在該觸發時有沒有被讀到」和「交接文件能否讓新 session 接手」。
4. 評分要事先寫好，並記錄模型、命令和原始輸出。如果要用其他模型當受試者或評分者，規格裡要寫明，使用者核准時才算同意開子代理。
5. 完成階段時，在規格補記寫下實作所用的模型。

**不能做的事**
- 不能改 `/home/user/src/ai-general-framework`。它是唯讀的，調查時也不要 `cd` 進去，要用絕對路徑或子 shell。
- 不能 push、建立 PR 或部署。本機 commit 和 tag 要等使用者當次指示。
- 不能覆寫三份原始規格，也不能為了通過驗收而降低要求、削弱測試或改契約。
- 不能把舊 receipt 當成目前來源的通過證據。
- 驗收或報告執行期間，不能改計入指紋的檔案（包含 `docs/`、`scripts/`、`acceptance/`）。
- 不能直接修改 `.claude/skills/` 和 `.agents/skills/` 的副本，它們由框架管理。
- AGENTS.md 的限制仍有效：不用既有 Raft 函式庫、不用 unsafe、不做 lease。
- S8 規格沒經使用者同意前不能實作，也不能自行開子代理。
- 與框架有關的實際經驗要當下追記到 `docs/FRAMEWORK_EXPERIENCE_LOG.md`，不要事後憑印象補。這次是唯讀任務，所以我沒有寫。

**需要使用者知道的小事**
- 交接文件寫專案在 `/home/user/src/Distributed_Key-Value_Store_with_Raft`，但這次的工作目錄是 `/tmp/claude-1000/.../scratchpad/s8/B/sonnet-with-handoff`，看起來是實驗用的快照。
- 我沒有確認 `cargo` 是否可用，也沒有跑任何建置或測試。

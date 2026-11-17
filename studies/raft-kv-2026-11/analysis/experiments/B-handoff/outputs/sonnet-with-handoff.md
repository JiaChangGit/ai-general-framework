## 接手核對結果

我只讀了 `CLAUDE.md` 和 `docs/HANDOFF_CLAUDE.md`，並執行唯讀命令，沒有改任何檔案。

**1. 未提交的變更**
- `git status --short` 沒有輸出，工作樹是乾淨的。
- 目前在 `experiment` 分支，另有 `main`。最新 commit 是 `d31121f Experiment B snapshot`，之前是 S7 的 `6ed8d49`。
- 我沒有另外執行 `git log` 核對 commit 清單。上面的 commit 資訊來自對話開頭的 gitStatus 快照。

**2. Tag**
- 有 `s0-foundation-verified`、`s1-storage-format-verified`、`s1-s4-review-verified`、`s2-snapshot-compaction-verified`、`s3-read-index-verified`、`s4-membership-verified`、`s5-performance-verified`、`v1-baseline-verified-20261112`。
- 交接文件要求確認的兩個也都在:`s6-review-fixes-verified` 和 `s7-zh-style-prototype`。

**3. `scripts/status.py` 的結果**
- P00～P08、P10～P15 全部顯示 `PASS [source changed / not run]`,最近一次驗收時間都是 2026-11-15。
- 契約本來就沒有 P09,所以這份清單裡沒有它。
- `PASS` 表示那次驗收當時通過。`source changed` 表示現在的來源指紋和當時不同,所以這些 receipt 不能當成目前來源的通過證據。
- 這個結果是預期中的。S7 新增了不屬於 Raft 的 `framework-study/`,而它計入指紋。
- Raft 的驗收結果應該對應 tag `s6-review-fixes-verified` 那個 commit。S9 收尾時要從 P00 完整重跑。
- 我沒有重跑驗收,所以「目前來源通過」這件事沒有驗證。

**4. 機器是否安靜**
- `uptime` 的 load average 是 0.21 / 0.18 / 0.08,整體算安靜。
- 排名最前面的是我自己這個 session 的 CLI,大約 28% CPU。另外有同專案的另一個 Claude session(`--resume=bba72f3a…`)和一個 sonnet session,各佔不到 2%。
- 還有一個 `framework-study/analysis/experiments/B-handoff/run_b.py` 在跑。看起來就是這次「帶交接文件接手」的實驗本身,是我推論的,沒有讀它的內容。
- `containerd` 只佔 0.1%,這次沒有交接文件說的那種佔一顆 CPU 的情形。如果之後要量測或驗收,仍要先重看一次 `uptime`。

**5. 下一步**
- 下一個階段是 S8(框架分析與對照實驗),尚未開始。
- 依照 `docs/ROADMAP.md` 的「S7、S8 的依據」和 `framework-study/zh-style/report.md`,起草 S8 的規格給使用者看,**先不要實作**。
- 規格要做到以下幾點:
  - 依使用者的標準,逐項寫出框架的優點、缺點和改進建議。
  - 證據來源是 `FRAMEWORK_EXPERIENCE_LOG.md`(L01～L53)、兩份獨立審查、S7 的報告和框架原始碼。
  - 準備 2～3 個小型對照實驗,候選有「skill 或指引在該觸發時有沒有被讀到」和「交接文件能否讓新 session 接手」。
  - 評分標準要事先寫好,並記錄模型、命令和原始輸出。
  - 如果要用其他模型當受試者或評分者,規格裡要寫明,使用者核准時才能一併同意開子代理。
  - 階段完成時,在規格補記實作所用的模型。

**6. 不能做的事**
- **目前這次任務:**只能讀檔和執行唯讀命令,不能改任何檔案。第二次呼叫 `git log` 加 `ls` 的複合命令被 don't-ask 模式擋下,我改成只執行 `status.py`。
- **框架:**`/home/user/src/ai-general-framework` 保持唯讀。不要 `cd` 進去,要用絕對路徑或子 shell。
- **Git:**不自行 push、建立 PR 或部署。本機 commit 和 tag 要依使用者當次的指示。
- **規格與驗收:**
  - 不覆寫三份原始規格。
  - 不為了通過驗收而削弱測試或改契約。改既有測試的期待時,要寫進契約的 `modified_tests` 並告訴使用者。
  - 驗收或報告執行期間,不要改受指紋涵蓋的檔案(包括 `docs/`)。
- **Raft 工程:**不使用既有 Raft 函式庫、不用 `unsafe`、不做 lease。
- **S8 的開始條件:**S8 在使用者同意規格前不能實作。
- **紀錄方式:**框架相關經驗要當下追記到 `docs/FRAMEWORK_EXPERIENCE_LOG.md`(目前到 L53),不要事後憑印象補寫。
- **其他:**不要用 `pkill -f`,改用 PID。

**需要使用者知道的限制**
- 交接文件列出的未知項目都還沒處理:教學 01～19 是草稿,審查 §8 那個無法解釋的失敗也沒追查。
- S7 腳本的 R5 規則有已知的寫法錯誤,要再用的話得先修。
- 我沒有執行 `cargo` 或任何測試,所以程式本身目前是否能建置,我沒有驗證。

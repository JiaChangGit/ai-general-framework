# 研究與實驗紀錄

這裡保存用真實專案檢查這個框架的紀錄。它們是紀錄，不是指引：內容寫的是當時看到的事，之後不隨框架更新；引用時以檔案裡的日期為準。

| 資料夾 | 內容 |
|---|---|
| [raft-kv-2026-11/](raft-kv-2026-11/README.md) | 在一個 Rust Raft KV store 專案（2026-11-10～17）裡使用框架的研究：S7 中文 AI 味的規則式檢查（`zh-style/`）、S8 的元件盤點與三個對照實驗（`analysis/`）、S8 後續依報告修改框架的規格、探測與結果（`changes/`） |
| [research-2026-11/](research-2026-11/) | 2026-11-17 的外部研究：熱門開源專案（`A-projects.md`）、官方文件（`B-official.md`）、論文與演講（`C-evidence.md`），一次中文文件校閱的完整報告（`D-zh-review-of-raft-docs.md`），這一輪框架修改的審查（`E-framework-review.md`）；2026-11-18 的 hooks、評測與 CI 研究（`F-hooks-evals-ci.md`），以及第一次有對照組的觸發與成效量測（`G-measurement-2026-11-18.md`，原始彙總在 `measurement-2026-11-18/`）；S12 的量測：框架該幫上忙的任務、固定成本拆解、改過描述的 skill（`H-measurement-s12.md`，原始彙總在 `measurement-s12/`）；S13 縮短常駐規則後的固定成本與回歸（`I-rules-s13.md`，原始彙總在 `measurement-s13/`） |

`raft-kv-2026-11/` 原本放在那個專案的 `framework-study/`，2026-11-17 搬到這裡，內容沒有改。裡面指向 `../docs/`、`ROADMAP.md`、`CLAUDE.md` 等的連結，指的是那個專案裡的檔案，在這裡會失效。
研究報告由網頁讀取工具取得原文的摘錄，報告裡每一條都標了 [READ]（實際讀過）或 [SEARCH-ONLY]（只看到搜尋摘要）；引用前回原文核對。

依這些紀錄做的分析與建議在 [docs/analysis-2026-11.md](../docs/analysis-2026-11.md)。

# 框架研究（不屬於 Raft 系統）

這個資料夾放的是分析使用者的 AI 框架（`ai-general-framework`）所做的實驗與報告，和 Raft KV store 的程式、驗收契約無關。
框架本身只在使用者 2026-11-16 點名後修改（S8 後續）：先改在分支上，使用者同意後快轉併進 main，使用者自己未提交的修改原樣保留。
計畫與依據見 [路線圖](../docs/ROADMAP.md)「2026-11-15 的計畫修改」。

| 資料夾 | 階段 | 內容 |
|---|---|---|
| [zh-style/](zh-style/) | S7 | 中文「AI 味」：實例分析、對照表、規則式提示腳本與它的試跑報告。先讀 [report.md](zh-style/report.md) |
| [analysis/](analysis/) | S8 | 框架的元件盤點、三個對照實驗與分析報告。先讀 [report.md](analysis/report.md) |
| [changes/](changes/) | S8 後續 | 依報告修改框架的規格、探測、重跑與審查結果。先讀 [RESULTS.md](changes/RESULTS.md) |

這裡的檔案計入 Raft 驗收的來源指紋；加入之後 `scripts/status.py` 會顯示 `source changed`，S9 收尾時從 P00 重跑一次。

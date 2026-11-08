---
name: review-change
description: Review a specified code diff or patch for actionable defects, regressions, and missing validation. Use for engineering change review, not reported-failure diagnosis, general code explanation, prose editing, or creative critique.
---

# 依證據審查變更

先確認要看的 diff（相對某個版本的修改內容）、基準與使用情境。讀取變更及必要的呼叫者、資料結構、測試和歷史理由；不要只憑片段推斷整體行為。沒有指定修改對象時先釐清，不把一般「看看這段程式」當成全庫審查。

提出發現前，確認：

- 這個問題由本次變更引入，或本次變更實際觸及了既有缺陷。
- 能指出觸發條件、執行路徑與具體後果。
- 問題尚未由現有防護排除，且值得作者修改。

以最小相關行範圍定位。每項發現說明條件、原因和影響，按專案的嚴重度定義排序；沒有定義時用實際阻斷程度說明，不自行假裝有精確評分標準。無法確認的事項用問題呈現，與已證實缺陷分開。

避免只因個人風格、可能的未來需求或孤立的理論風險要求修改。安全、效能與資源生命週期只有在相關路徑及後果足以支持時才列為發現。

必要時做有針對性的重現或檢查，並標明是否真的執行。沒有 actionable finding 就直接回報未發現，交代審查範圍與材料缺口；不為了湊數新增評論。除非本次任務包含修正，先完成審查，不擅自改檔。

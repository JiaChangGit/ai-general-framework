---
name: debug-root-cause
description: Investigate a reported software or system failure, crash, regression, or unexpected runtime behavior, and validate a causal fix when requested. Do not use for code explanation without a failure, patch review, or a debugging-tool lesson alone.
---

# 用觀察找出故障原因

從使用者實際觀察到的異常開始；尚未能穩定重現也可以調查。只想學工具用 `guide-learning`，只想理解正常路徑用 `trace-code`，不把這些要求擴成事故處理。

1. 保存原始症狀及環境：版本、設定、輸入、重現步驟、預期與實際結果。先確認觀察來自同一次執行及正確的元件。
2. 找到第一個可觀察的偏離，沿資料、狀態、時間與資源擁有者縮小範圍。讀取相關程式和工具文件後，再決定要增加哪項觀測。
3. 證據足夠時提出互相競爭的解釋，選能區分它們的低成本觀察。不要為了符合格式而硬湊原因；每次試驗都先交代預期看到什麼，以及結果會如何改變判斷。
4. 將原因連到被破壞的不變條件。找到引入 regression 的 commit、移除症狀或重試後成功，都還需要解釋故障機制。
5. 任務包含修正時才修改實作，再驗證原始重現及相關回歸；只要求調查就交付原因與修法。保留原始失敗證據，將修正後的執行分開記錄。
6. 如果新觀察已無法有效縮小範圍，回報目前知道什麼、排除了什麼，以及哪項缺失資料會解鎖下一步。不要無限重試或不斷增加日誌。

回報應讓人能分辨「已觀察」「由程式推得」「仍待驗證」。小 bug 不必產出大型 RCA 文件；事故或跨角色交接才保存足夠的可重現紀錄。

依情境讀 [kernel-and-gdb.md](references/kernel-and-gdb.md) 或 [infra.md](references/infra.md)，不要預先載入全部工具手冊。

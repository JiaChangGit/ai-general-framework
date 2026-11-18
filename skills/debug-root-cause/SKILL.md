---
name: debug-root-cause
description: Investigate a reported software or system failure, crash, regression, or unexpected runtime behavior, and validate a causal fix when requested. Also the entry point when the failure involves SQL or a proposed query fix; review-sql can follow for the rewrite. Do not use for code explanation without a failure, patch review, or a debugging-tool lesson alone.
---

# 用觀察找出故障原因

從使用者實際觀察到的異常開始；尚未能穩定重現也可以調查。只想學工具用 `guide-learning`，只想理解正常路徑用 `trace-code`，不把這些要求擴成事故處理。

1. 保存原始症狀及環境：版本、設定、輸入、重現步驟、預期與實際結果。再列出這次調查依賴的前提，例如症狀來自哪個版本、哪台機器、哪一次執行，手上的材料是不是原始資料，逐一用觀察確認。前提錯了，後面的推論都不算數。
2. 找到第一個可觀察的偏離，沿資料、狀態、時間與資源擁有者縮小範圍。讀取相關程式和工具文件後，再決定要增加哪項觀測。
3. 證據足夠時提出互相競爭的解釋，選能區分它們的低成本觀察。不要為了符合格式而硬湊原因；每次試驗都先交代預期看到什麼，以及結果會如何改變判斷。
4. 將原因連到被破壞的不變條件。找到引入 regression 的 commit、移除症狀或重試後成功，都還需要解釋故障機制。
5. 任務包含修正時才修改實作，再驗證原始重現及相關回歸；只要求調查就交付原因與修法。保留原始失敗證據，將修正後的執行分開記錄。說「修好了」時，附上修正前失敗、修正後通過的實際輸出；沒有跑過就寫沒有跑過，不用「應該已修好」代替。
6. 如果新觀察已無法有效縮小範圍，回報目前知道什麼、排除了什麼，以及哪項缺失資料會解鎖下一步。不要無限重試或不斷增加日誌。

回報應讓人能分辨「已觀察」「由程式推得」「仍待驗證」。小 bug 不必產出大型 RCA 文件；事故或跨角色交接才保存足夠的可重現紀錄。

偶發失敗需要重跑時，先確認命令可安全重複，限制次數、單次時間與輸出量。分開記錄各次結果及條件，保留首次失敗與必要的成功對照；重試成功或一批未失敗，都不能單獨證明故障已修復。沿用專案 runner 或現有 `run`，不為統計重複有副作用的操作。

依情境讀 [kernel-and-gdb.md](references/kernel-and-gdb.md) 或 [infra.md](references/infra.md)，不要預先載入全部工具手冊。

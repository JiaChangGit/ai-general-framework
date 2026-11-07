---
name: implement-change
description: Implement a bounded feature or behavior change in an existing project, using its conventions and relevant validation. Use for making changes; route diagnosis of an unexplained failure to debug-root-cause.
---

# 完成一項可驗證的變更

1. 讀取適用的專案指示、工作樹狀態、相關呼叫者與測試。先確認觸發條件、變更前後的行為和本次完成條件。
2. 追蹤現有實作如何處理同類需求，再選最小且完整的修改。只有當重複邏輯、穩定邊界或實際擴充需求足以支持時，才新增抽象、設定或相依套件。
3. 依已知需求處理正常流程與相關失敗路徑，包含資源清理、相容性和部分完成的後果。不要順便重構無關區域。
4. 選擇能驗證變更行為的檢查。Bug 修正優先用失敗案例重現前後差異；一般低風險文字修改不必新增只比對措辭的測試。專案要求的檢查仍須完成。
5. 檢查 diff，移除遺留試驗、重複說明與用不到的程式。回報行為、理由、實際驗證及尚未確認的限制；測試成功不代表已部署或已通過整合驗收。

委派適合可獨立界定的工作；交代輸入、交付、驗收和檔案責任，避免多人同時修改同一處。簡單任務不必啟動完整角色團隊。

修改 CI、容器、Kubernetes 或 hooks 時，另讀 [delivery-boundaries.md](references/delivery-boundaries.md)。

---
name: contribute-upstream
description: Prepare a focused contribution to an upstream project, especially the Linux kernel, using its current maintainer, patch, validation, and submission conventions. Use for contribution preparation; submission to other people requires explicit authorization.
---

# 準備讓上游能審查的貢獻

先讀當前專案與子系統的貢獻文件、維護者資訊、近期相關變更及已知討論。確認使用者想學習、準備 patch、實際送出，還是跟進 review；這些操作的授權範圍不同。

1. 選有明確問題、影響與可驗證行為的變更。先重現或查證，避免為增加貢獻數量而做無必要的風格改動。
2. 依目標版本建立最小邏輯修改；patch 系列中的必要中間狀態也應保持可建置及可驗證。說清楚依賴，不混入無關整理。
3. 依子系統要求執行相關 build、測試及檢查，保留環境與結果。風格 checker 只是輔助，通過不代表設計或功能正確。
4. 描述問題、觸發條件、影響、改法、理由及取捨。只加入有依據的 `Fixes`、來源連結與實際測試標籤；身分、DCO 或他人簽署不能代填或捏造。
5. 準備正確收件者、patch 格式與 cover letter，先核對可審查的實際內容。只有本次明確授權時才寄信、發布留言或送出 contribution；準備完成不等於上游已接受。

Review 回來後逐點確認理解，再修改和驗證；新版描述應可獨立理解，保留重要修改理由。若使用者要學習，帶他看一個 review 決策，避免直接代做後宣稱他已具備貢獻能力。

Linux 入口：[Submitting patches](https://docs.kernel.org/process/submitting-patches.html)、[Reporting issues](https://docs.kernel.org/admin-guide/reporting-issues.html)。實際操作時仍核對目前子系統與貢獻政策。

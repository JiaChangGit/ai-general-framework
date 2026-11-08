---
name: trace-code
description: Explain how a concrete operation travels through actual code, state, ownership, callbacks, or components, with source-backed diagrams when useful. Use for execution tracing, not reported-failure diagnosis, patch review, ordinary edits, or document extraction.
---

# 追蹤一個實際操作

本次目的是看懂執行路徑。實際故障找根因用 `debug-root-cause`；指定 diff 的缺陷審查用 `review-change`，不因為它們也會讀程式就一起啟動。

選定版本、入口、具體輸入與想回答的問題。先讀相關實作、型別、呼叫者及 guard（決定是否繼續執行的檢查條件），再沿這次情境展開；不要從全庫函式清單開始。

對會影響答案的步驟交代：誰執行、收到什麼、先檢查什麼、改變哪些狀態、由誰持有資源，以及失敗後如何清理。來源定位以檔案與 symbol 為主；行號需對應所讀版本。

明確區分三種材料：

- **靜態追蹤：** 由這個版本的程式推得的可能或必經路徑。
- **Runtime 觀察：** 實際命令、環境、輸入與該次輸出支持的路徑。
- **教學假設：** 為說明而設定的拓樸、數字或事件，尚非實測。

圖種依問題選擇：呼叫關係、跨元件事件、狀態轉移或 ownership 各有不同語意。箭頭應標示呼叫、排程、訊息、資料或通知；互斥分支不能畫成連續執行。以有界情境取代預設的全庫大圖。

跨邊界或需要畫圖時讀 [trace-contract.md](references/trace-contract.md)。先完成本次追蹤，不自動擴成課程、全庫圖或除錯任務。

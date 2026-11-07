---
name: trace-code
description: Trace a concrete operation through source, state changes, callbacks, or component boundaries and explain it with source-backed diagrams. Use for understanding execution and ownership; not for generating a whole-repository graph by default.
---

# 追蹤一個實際操作

選定版本、入口、具體輸入與想回答的問題。先讀相關實作、型別、呼叫者及 guard，再沿這次情境展開；不要從全庫函式清單開始。

對會影響答案的步驟交代：誰執行、收到什麼、先檢查什麼、改變哪些狀態、由誰持有資源，以及失敗後如何清理。來源定位以檔案與 symbol 為主；行號需對應所讀版本。

明確區分三種材料：

- **靜態追蹤：** 由這個版本的程式推得的可能或必經路徑。
- **Runtime 觀察：** 實際命令、環境、輸入與該次輸出支持的路徑。
- **教學假設：** 為說明而設定的拓樸、數字或事件，尚非實測。

圖種依問題選擇：呼叫關係、跨元件事件、狀態轉移或 ownership 各有不同語意。箭頭應標示呼叫、排程、訊息、資料或通知；互斥分支不能畫成連續執行。以有界情境取代預設的全庫大圖。

使用 [trace-contract.md](references/trace-contract.md) 核對跨邊界與圖文一致性。若使用者要學習，可邀請他預測一個相近情境；直接帶讀的要求仍須提供完整解說，不以答題阻擋進度。

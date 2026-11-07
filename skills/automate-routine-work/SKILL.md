---
name: automate-routine-work
description: Plan and carry out repeatable batch file changes, content comparisons, or bounded web extraction with reviewable inputs and outputs. Use for concrete routine automation; not for building a general agent platform.
---

# 可靠地完成重複工作

先找現有專案命令或已驗證的工具。只在會重複使用，或確定性邏輯能改善可靠度時寫 helper；不要每次重新生成同一段程式，也不為一次簡單操作建立通用框架。

批次處理先確認範圍、來源、目標、編碼、換行、碰撞及錯誤行為。先產生可檢視的預計變更，再依授權套用；寫入前重新驗證來源未變更。目標必須留在明確範圍內，符號連結與 Windows 路徑需特別核對。

內容比較先辨認要比較原始 bytes、文字、結構或語意。正規化可能隱藏差異，須讓使用者知道哪些差異被忽略；摘要保留可定位的原始差異，不能用 AI 摘要取代精確 diff。

網頁擷取先辨認公開內容、登入資料、頁數、節流與需要的欄位。優先穩定 API 或靜態內容；只有確實需要時才使用瀏覽器。遵守來源存取限制與本次資料授權，不繞過限制；記錄來源、時間、失敗及缺值，不默默補值。

優先使用框架既有 CLI；依專案規則所列的 AGF CLI 入口查看 help 與相應子命令說明，核對實際能力後才執行，不憑記憶編造路徑或選項。高風險操作需要清楚停止條件；腳本也不能自行取得額外權限。

驗證對應任務：改名前後映射與碰撞、格式轉換的有效內容、比對的漏判、擷取的頁數與欄位。不要只看 exit code 就宣稱資料完整。

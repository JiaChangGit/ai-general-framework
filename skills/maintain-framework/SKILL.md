---
name: maintain-framework
description: Maintain ai-general-framework skills, scripts, adapters, routing rules, or policies from a demonstrated need and validate their behavior. Use only for framework maintenance, not every downstream project change.
---

# 根據實際需求改善框架

先讀本框架的規則、目前能力、變更紀錄與相關驗收案例，確認問題發生在哪一層：共同規則、個人偏好、skill、腳本、工具 adapter 或專案本地設定。

1. 保存一個能說明問題的真實請求與必要材料。先辨認是缺少資訊、路由錯誤、內容錯誤、執行缺陷或使用者偏好，不把每次不滿都升格為全域禁令。
2. 選最窄的修正位置。高頻共同限制留在短入口；只在特定任務需要的細節放在 skill reference；重複而確定的邏輯才寫進 script。
3. 修改 skill 時保留可辨識的觸發條件、排除容易誤選的情境，並核對引用與外部素材授權。不要以增加 skill 數量、指令長度或固定儀式當作品質提升。
4. 以一個應選及一個不應選的請求檢查路由；複雜變更再用不含預期答案的獨立任務驗證。格式檢查不能證明代理會作出正確決策。
5. 腳本與 adapter 的驗證涵蓋相關失敗和副作用；宣稱 Windows 原生及 Linux/WSL 支援時，分別取得證據，不以單一環境的成功替代。
6. 檢查新增維護成本、重複內容與載入負擔。回報改善證據、實際測試與仍未知的成本，未量測就不宣稱節省特定 token 比例。

依專案規則所列的 AGF CLI 入口查看 help，再使用實際存在的子命令。此 skill 不自動授權安裝、修改使用者全域設定或發布新版。

---
name: review-sql
description: Analyze slow SQL and execution plans, and review query rewrites, indexes, migrations or database permissions with test evidence and deployment boundaries. Excludes simple record lookup, general code review and database administration unrelated to a proposed change.
---

# 審查 SQL 效能與資料庫變更

依問題選最小流程：只問計畫就解讀計畫；要重寫、加索引或改 Schema、權限時才進入變更審查。不為一次查詢引入新服務，也不預設需要 PawSQL 或 Bytebase。

## 確認材料與工具

先從現有材料確認資料庫引擎與版本、目標環境、原始 SQL、參數分布、相關 Schema、索引，以及已有計畫或測試結果。只補問會改變判斷的缺口；缺少連線權限時仍可分析已提供材料，明確限制結論。

優先使用已連接的工具與既有 CI／審查流程。要採用 PawSQL 或 Bytebase、判讀工具不可用的原因時，才讀 [tools.md](references/tools.md)。確認工具、介面、設定與本次功能的授權狀態，不能把「已安裝」寫成「已驗證可用」。不自動安裝服務、申請權限或放寬政策。

## 分析效能

1. 對照計畫、資料量與原始症狀，找出掃描量、估計與實際列數落差、Join、排序、鎖等待或 I/O 的證據。把已知、推論與下一個驗證步驟分開。
2. 先解讀已有計畫，必要時提出該引擎適用的非執行型 `EXPLAIN`。`EXPLAIN ANALYZE` 會真的執行 SQL；`SELECT` 也可能呼叫有副作用的函式。不要把它當成唯讀檢查，或聲稱包在 transaction 再 rollback 就沒有影響。
3. 重寫與索引建議要維持結果語意，檢查 NULL、重複列、排序、邊界值與參數差異；說明索引對寫入、空間與維護的代價。不只憑 SQL 外觀或 estimated cost 宣稱加速。
4. 實測只在已確認、已授權且受控的測試環境執行，限制時間與資源。比較相同資料、統計資訊、參數和可比較條件下的原始與建議計畫、結果及耗時；未實測就保留「待驗證」。正式環境的量測沿用既有唯讀監控與核准流程。

## 審查變更與交接

資料庫操作預設唯讀；寫入先準備 Migration、Rollback、影響範圍、鎖定／停機、回填、備份與驗證方式。依資料庫特性說明不可逆步驟，不假裝每個 DDL 都能完整回復。值使用參數化查詢，識別名稱依引擎安全引用或 allowlist；只取任務需要的欄位，遮去憑證和敏感內容。

維持「建議 → 測試 → 審查 → 核准」的狀態。SQL 或索引的效能建議也要走同一條變更流程。使用 Bytebase 時確認真正的 issue、檢查結果、審批與 rollout 政策；換成其他工具時沿用組織既有流程。工具名稱、綠色提示或 Agent 自己的判斷都不等於人工核准。

本 skill 不直接寫入正式環境，也不自行核准、繞過審查或觸發正式部署。已有明確授權與流程證據就沿用，不為相同步驟重問；超出範圍、環境不明或證據不足時先完成可做的分析與草稿，停在受影響步驟並說明缺口。沒有可用審查流程時，只交付變更、回復及驗證草稿，保留人工審查與部署核准。

## 交付

按任務提供需要的內容，不強制長報告：

- 效能：問題判定、原始 SQL／計畫位置、重寫或索引建議、改善依據、副作用、驗證結果或方法，以及信心與限制。
- 變更：目的、資料庫／環境、Migration／Rollback、影響與回填、驗證 SQL、實際審查結果及尚缺的部署條件。

明確標示哪些只讀過、哪些真的執行過，以及是否仍需審查、核准或測試。交接保留工具／版本、材料與結果位置、當前狀態及下一個驗證步驟，不包含連線字串、密碼或 Token。

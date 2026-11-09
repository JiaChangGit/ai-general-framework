# 選用 SQL 工具前的確認

只在本次需要外部工具時讀取。以下依 2026-11-09 查到的官方資料整理，是選型與驗證線索，不代表本機已安裝、服務已連上，或帳號已有功能授權。實際版本與組織流程優先；不把下列產品列為必要相依。

## 能力與 Fallback

分別記錄介面、版本、設定、網路／驗證結果與本次所需功能。探測不提交 SQL、不啟動服務，也不輸出秘密。狀態依已取得證據使用：

| 狀態 | 判定依據 |
| --- | --- |
| `available` | 本次需要的介面、連線與功能已有可用證據；附檢查範圍，不能泛指所有功能。 |
| `unavailable` | 工具未提供、服務離線或目前環境無法連線；說明實際查過的範圍。 |
| `misconfigured` | 缺端點、憑證、啟用設定，或驗證／版本／引擎不相容；授權尚未確認時一併註明。 |
| `license-limited` | 有明確證據顯示所需功能受版本、配額、過期或授權條件限制；不要只憑 HTTP 403 判定。 |

未查證的能力寫在說明中，不能宣稱 `available`。外部分析不可用時，解讀使用者提供的計畫，或準備原生非執行型 `EXPLAIN`；沒有計畫就只提出待驗證假設。審查服務不可用時，保留 Migration、Rollback、測試及人工審查草稿，不嘗試正式部署。

## PawSQL：介面與授權分開確認

- [官方 MCP repository](https://github.com/PawSQL/pawsql-mcp) 列出 enterprise、cloud、community 設定，支援 SQL 重寫與索引建議；連資料庫的 workspace 才能取得相應計畫分析。逐一確認服務端版本、引擎、workspace 模式與所需權限。
- [Community Edition README](https://github.com/PawSQL/pawsql-ce) 明列 PostgreSQL／MySQL、需先取得 activation code，並設定 activation email。不能因為名稱是 Community 或 repository 公開，就假設免啟用、無配額或所有用途都免費。
- [HTTP API](https://www.pawsql.com/docs/api/) 與 [summary 介面](https://www.pawsql.com/docs/api/analysis-summary/) 使用的 `userKey`／activation code，與 MCP README 的 edition／email／password 範例不同；依實際介面確認，不能混用驗證方式。
- [官方方案頁](https://www.pawsql.com/pricing) 的當前配額與使用權仍需以實際方案、啟用結果及條款確認；本次未取得可核對的完整方案表，不硬編價格、免費額度或 CE 商用權。SQL、Schema 與資料送往外部服務前，確認資料政策與傳送範圍。

工具提出的 estimated cost 或改善百分比只當分析材料；仍需驗證語意與測試環境中的實際表現。

## Bytebase：確認實際審查路徑

- [MCP 官方文件](https://docs.bytebase.com/integrations/mcp) 要求 external URL 與允許連線的 workspace access policy。MCP OAuth Token 只適用該 `/mcp` 端點，REST API 應使用相應 service account。新 workspace 預設 Read-only；舊版 workspace 未保存政策時可能仍是 Read-write，不能憑預設值推定安全。
- 同份文件說明：Read-write 下的 `query_database` 可以直接執行 DML／DDL，**不建立 issue**；`propose_database_change` 才進入變更流程。不能因為工具是 Bytebase，就讓索引建議或 Migration 改走直接 query 路徑。
- [核准流程](https://docs.bytebase.com/change-database/approval) 可設定免核准；GitOps 的核准在版本控制的 PR／MR。Community 是否有人工審批、實際版本與方案能力，要以 workspace 為準；[官方方案比較](https://www.bytebase.com/blog/bytebase-vs-liquibase/) 說明自訂 approval workflow 屬 Enterprise，不能將 Community rollout policy 當成人工審查。
- [SQL Review 政策](https://docs.bytebase.com/sql-review/review-policy) 的規則可停用，超過大小限制可能略過部分檢查並回 Warning；Warning 不一定阻擋部署。檢查實際跑過哪些規則與結果，不能把略過寫成通過。
- [Rollout 政策](https://docs.bytebase.com/change-database/environment-policy/rollout-policy) 可自動部署。交接時記錄 issue／plan、審批與 rollout 的實際狀態，不自行提高存取權限、修改政策、核准自己提出的變更或啟動正式 rollout。

## 原生計畫不是一律無副作用

[PostgreSQL 18 EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html) 明確區分估計計畫與 `ANALYZE` 的實際執行，並說明語句副作用照常發生。[Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) 也說明量測負擔、資料規模與統計資訊會影響比較。其他引擎使用各自版本的文件，不直接套 PostgreSQL 語法或回復假設。

# 本輪能力盤點與最小取捨

2026-11-09 查核；本頁供維護者回查，日常任務只讀相關 skill 或[選工具參考](../templates/tool-selection/README.md)。使用者提供的名稱、品牌及檔案結構都是候選，沒有逐一安裝、驗收或審查整份清單。

## 目前可重用的內容

| 範圍 | 實際觀察與證據界線 |
|---|---|
| 框架 | 已有 trace、debug、change review、research、learning 五個技能目的；context／source 摘錄、批次檔案、執行證據、task 交接、profile、Git 範圍及 hook helpers。詳見現有 [CLI](cli.md)與[工作指引](workflow.md)，不是待重建的能力。 |
| Windows | 找到 Python 3.13.15、Node、Git、rg、Codex 執行檔。可定位 sqlite3、pandas、docling、pptx、docx、PIL、matplotlib 等 Python 模組；模組位置不代表已成功 import、解析文件或產出成品。 |
| WSL | 找到 Python 3.14.4、Git、rg、gh、Codex；Node 在既有專案 QA 目錄，非預設 PATH。可定位 sqlite3、PIL。程式存在不等於模型登入、API 或原生宿主整合已可用。 |
| Docker／服務 | Windows 找到 Docker CLI，但 daemon 無法連線；WSL 的 Docker 整合未啟用。既有 Compose 是 doctor 示範，不是 RAG 或資料庫服務。沒有啟動 daemon、拉 image 或部署候選服務。 |
| MCP／API／宿主 | 當前工具清單可探索網頁、GitHub、文件工作階段、試算表／簡報 artifact、圖像、網站和瀏覽器能力。未在本次 CLI 探索或暴露工具清單中找到 RAGFlow、GraphRAG、PawSQL、Bytebase 或通用 SQL 查詢入口；未掃描其他帳號、整台機器或內網，亦未讀憑證。 |
| CI／hooks | [GitHub CI](../.github/workflows/ci.yml) 已有 Windows／Ubuntu、Python 3.11／3.13，沿用 pinned action SHA、contents read 與共用品質檢查。[GitLab 範本](../templates/gitlab-ci.yml)需另有 runner，本輪未驗遠端執行。版本庫未啟用本地 pre-commit／pre-push hook；已有可選範本，不另建 runner。 |

上述是這次宿主與來源檔的盤點，不是所有工具的永久狀態，也不把連線、功能授權或範例部署列為通過。能力狀態的證據規則見選工具參考；重要未知另外列出。

## 第一版採納與合併

新增一個可選 `review-sql`，合併 SQL 效能與資料庫變更審查。理由是查詢重寫／索引建議、測試比較、migration 風險及專案審查是一條相接的交付鏈；現有泛用 debug 和 code review 沒有明寫 `EXPLAIN ANALYZE` 的執行效果、計畫與量測限制、資料回填／鎖定及部署審查關係。普通欄位查詢、檔案搜尋及文章寫作不啟用它。

細節放該 skill 的條件式 references；沿用 `agents/openai.yaml` metadata，不新增另一套 UI schema。只安裝明示選取的技能，保留原有五個目的；不新增 project／knowledge／writing／music 等通用 router。

| 使用者提出的方向 | 本輪選擇與原因 |
|---|---|
| 程式索引、分層 context、worktree、需求與測試 | 重用 context、原生 Git／索引及 workflow。只有專案已有可信依賴或覆蓋資料時才選受影響測試；目前的小型核心測試不需要另外導入 Nx 或 test-selection 平台。 |
| 文件檢索、關係圖、SPEC、研究 | 保留 source／read-research 與宿主文件工具；直接證據先取得，必要才用已可用的 RAG／graph。沒有服務、資料集與成本需求時不建知識庫，不增加 parser 或學術資料庫包裝。 |
| 寫作、風格、引用、連貫性 | 合併到 writing 與既有創作設定／來源核對。本人樣本與固定規則按需使用；不為每個寫作步驟新增技能或強制模型評分。 |
| 簡報、影片、漫畫、數位角色 | 沿用宿主能力、outputs／presentations 參考與既有圖解路線。保留可編輯來源，依實際成果渲染、播放或視覺驗收；沒有目標作品時不建立素材、角色或生成平台。 |
| 作曲、MIDI、MusicXML、音訊 | 目前沒有指定的音樂檔、音源或可重現的編輯／播放任務，先保留既有聲音／歌曲交付指引。具體任務出現再評估成熟工具與模型／素材授權，不先加作曲引擎。 |
| 教學、資料處理、圖表 | 重用 guide-learning、宿主試算表／資料與視覺工具。資料引擎依格式與大小選用；真人學習成效、語意與圖表正確性不能用語法或檔案存在替代。 |
| 產品、論壇、新聞、社群研究 | 既有 workflow／tools 已要求問題範圍、原始來源、時間與反例；選相關 API、RSS 或瀏覽器。追蹤或發布需有具體任務，不因候選清單建立爬蟲、排程或自動發布。 |
| 模型治理、協作、追蹤與經驗回收 | 重用 task、profile、run 原始輸出與既有行為案例。未量測的 usage 留白；沒有持續服務需求時不導入 registry、記憶服務或 agent orchestration。 |
| 雲端、維運、資安、韌體及 UI／原型 | 沿用 debug／review／trace、現有領域參考與目標專案工具；待真實帳號、硬體或作品出現才擴充。掃描交給可信工具／CI，受測範圍、授權與結果各自確認，不建立通用安全偵測器。 |

PawSQL、Bytebase、RAGFlow、GraphRAG 只作條件式候選；選型不永久綁供應商。其他參考專案本輪未逐一查核維護、API、授權或相容性，因此不構成推薦、品質背書或可用承諾。

## 放在哪一層

通用選型判斷放 `templates/tool-selection/`，由 tools 指引按需定位；資料庫細節隨 `review-sql/references/` 部署。現有 `doctor` 只做可驗範圍的本機探索，不把它改造成會啟動服務的全域 probe。確定性檢查有真實反例與重複需求才加 script；MCP／API 沿用宿主，hooks／CI 沿用共用品質設定，不增另一套執行器。

部署程式會動態探索技能並複製所選 skill 的檔案，無需為第六個入口改架構。四份 guides 仍按需讀取；copy 模式已有 templates 的複製路徑。驗證須分開記錄本地格式、隔離部署、mock 或代理行為，以及外部服務實測；具體結果見[驗證紀錄](verification.md)，未執行的外部工具保留未知。

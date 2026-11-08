# ai-general-framework

用少量、邊界明確的 skills 配合既有 AI 與專案工具，協助開發、學習和創作。模型與角色可以自由切換；一般工作沿用宿主能力，只有需要額外判斷或可靠機械操作時才載入指引或使用 helper。

核心只需 Python 3.11+ 標準庫，支援 Windows 原生與 Linux／WSL。[驗證紀錄](docs/verification.md)分開列出實際執行、fixture 測試與尚未驗證的部分。

第一次使用可看 [micro-os 逐步教學](docs/micro-os-guide.md)：從準備框架、既有與全新專案配置，到更新、回復和其他使用案例。

本輪安全稽核的發現、修正及剩餘限制見[安全稽核紀錄](docs/security-review.md)。

## 先試一個任務

在本框架目錄執行；Linux 的 Python 命令可能是 `python3`。

```console
python scripts/agf.py doctor --root .
python examples/learning/queue_walkthrough.py
python scripts/agf.py context extract examples/learning/queue_walkthrough.py --start 1 --end 85
```

佇列範例能用來追程式與辨認批次失敗後留下的狀態。[學習範例](examples/learning/README.md)提供帶讀與實驗，[規格範例](examples/research/README.md)示範條件、順序與來源判讀。

## 各專案只帶需要的內容

預設共用這份框架的工具；專案僅配置規則、按需指引及你選取的 skills。沒有 `--skill` 就不額外安裝技能入口。選取後由宿主依請求自動考慮使用。

第一次先依眼前任務選一到兩個：追一筆輸入的執行路徑選 `trace-code`；已有錯誤現象選 `debug-root-cause`；想學陌生專案或工具選 `guide-learning`，需要追具體路徑時再搭配 `trace-code`。一般功能實作可以先不加 skill。下例適合需要追程式並找問題的專案；請換成自己的目標目錄與選擇。

```console
python scripts/agf.py project plan --target ../my-project --host opencode --skill trace-code --skill debug-root-cause
python scripts/agf.py project install --target ../my-project --host opencode --skill trace-code --skill debug-root-cause --apply
```

`--host`、`--skill` 可重複指定。目標目錄須已存在；工具保留既有規則、未受管理檔案及本地修改。專案的 `.agf/managed/project-rules.md` 會列出目前環境可用的工具入口；不必複製或手改整套程式。

配置後執行 `python scripts/agf.py project status --target ../my-project`，再從目標專案開啟宿主的新對話，確認它的技能清單或探索工具看得到所選 skill。`status` 只驗證受管理檔案與工具入口，不代表宿主真的載入了技能。接著交付一個有原始材料的小任務，例如「請追這筆輸入到回傳結果，指出中途狀態怎麼變」；從宿主提供的載入紀錄與實際成果確認行為，不只採信 AI 自稱已啟用。詳細對照方式見[行為驗收](evals/README.md)。

OpenCode 可在同一個 session 手動切換模型；一般切換不用額外建立交接檔。只有換對話、換工具或需要留存決策時，再使用交接紀錄。

需要離線或獨立交付時，加 `--tools copy`，把當時工具複製成專案內的快照。日常預設是 `--tools shared`；共享來源移動後用 `--source` 更新入口。Windows 與 WSL 的路徑各自核對，工具不默默跨環境執行。

```console
python scripts/agf.py project update --target ../my-project
python scripts/agf.py project update --target ../my-project --apply
python scripts/agf.py project status --target ../my-project
python scripts/agf.py project rollback --target ../my-project
```

更新預覽會列出變更和退役的受管理 skills。`--apply` 才套用；受管理檔案在本地被改過時，先處理差異再更新。回復處理上一筆框架配置，包含技能選擇與工具模式。舊版專案維持原快照模式；明確加 `--tools shared` 才切換。

個人偏好優先放使用者設定；專案內的 `.agf/` 還含本機路徑、備份與紀錄，分享前須依實際版本控制工具排除。Git 使用 `.gitignore`，SVN 使用自己的忽略屬性；框架不自動改寫它們。[工具與版本控制指引](docs/tools.md)說明差異。

## 五個技能入口

| Skill | 使用目的 |
|---|---|
| `trace-code` | 理解指定輸入的路徑、狀態、資料與資源生命週期 |
| `debug-root-cause` | 對實際異常建立假設、重現並驗證原因與修正 |
| `review-change` | 審查指定程式變更的可行動問題 |
| `read-research` | 判讀論文或規格；依要求短答或完整帶讀 |
| `guide-learning` | 學習專案、工具或概念，調整示範與練習深度 |

一般開發、需求對齊、寫作、多模型合作與工具選擇使用精簡的[工作指引](docs/workflow.md)、[表達與創作指引](docs/writing.md)、[工具指引](docs/tools.md)及[交付指引](docs/delivery.md)。不為 APP、股市程式、kernel、Boost、STM32、小說、作曲或影片各建一套重複技能；領域條件等具體任務出現再查。

預設先利用已有資料對齊想法，只追問會影響結果的未知；理解後直接做。問題中的專有名詞要用白話解釋。你已定的創作設定與工程限制都要尊重，驗收方式則依任務目的選擇。

## 你要的能力，如何落實

| 需求 | 目前做法 |
|---|---|
| 多模型、跨部門合作 | [分工指引](docs/workflow.md)先對齊成果、介面及失敗行為；模型與角色可互換，主責者整合驗證 |
| 個人化、自然中文與教學 | `profile show --root DIR` 合併偏好；[表達指引](docs/writing.md)保留因果與真實修改理由；trace 與教學 skills 依讀者選圖和示範 |
| 降低 token 消耗 | [按問題取資料](docs/tools.md)，機械操作重用現有 scripts；實際節省量尚未量測 |
| 降低 bug | 最小修改、風險相稱的檢查與 `review-change`；用原始失敗與相關回歸驗證成果 |
| 有效率找根因 | `debug-root-cause` 用能區分假設的觀察縮小範圍，將緩解與原因確認分開 |
| Grill me、對齊想法 | [需求對齊](docs/workflow.md)只問會改變決策的未知，理解後執行 |
| 提醒漏項與誤解 | 指出影響結果的矛盾和缺失條件，有材料先核對，需要取捨才提問 |
| 不過度思考 | 相關驗證足夠即交付；沒有新增觀察價值時說明缺什麼，不無限重試 |
| 不膨脹、易更新 | 五個明確 skills、按需 references、共用工具；[維護指引](docs/maintenance.md)要求改在最窄位置 |
| 資安、隱私、CI/CD、hooks 邊界 | [依操作效果判斷授權](docs/delivery.md)，只使用所需資料；文字規則與 hook 不冒充強制隔離 |
| 自動判斷 MCP 與工具品質 | [工具指引](docs/tools.md)依任務探索已連接能力，先查來源、安全與使用者回饋；省 token 工具另比較完整任務的實際用量與品質 |

MCP 選用由宿主代理讀取規則後，透過其工具探索能力執行。RTK 等工具的來源查證、實測範圍與採用取捨保存在[研究紀錄](docs/research.md)，不是永久的推薦名單。

## Scripts 提供原生工具之外的價值

`files` 提供批次預覽、碰撞／來源重驗、轉換與差異；`context`／`source` 提供有限摘錄及來源位置；`binary` 有界讀取已儲存二進位檔的 byte 數值、bit 欄位及 hex dump；`diagram` 產生 Mermaid、draw.io 與 trace 檢視。`run`／`check` 記錄有界的執行結果，`run --output-dir DIR` 可另存完整原始輸出，避免為取回診斷重跑命令。`task` 交接是選項，`git` 只處理 Git；GitHub、GitLab、SVN 等工作優先用現成 `gh`、`glab`、`svn` 及專案流程。

要求畫流程、架構、狀態等技術圖時，AI 先選[圖解樣板](templates/diagrams/README.md)，只寫 Mermaid 文字，交 mermaid-cli 渲染 SVG／PNG。單張最多 15 節點，超過就拆圖；資料轉狀態圖先用 `diagram transitions` 統計，再畫實際觀察到的轉移。保留五個 skills，不另加畫圖技能或渲染依賴。

完整命令、權限範圍、共用工具與 hooks 見 [CLI 操作](docs/cli.md)。[設計說明](docs/design.md)與[研究紀錄](docs/research.md)交代採納和刪減理由。共用創作指引可協助小說、音樂與投影片式影片；真正使用時再選可用工具，分清企劃、草稿與可播放成品。

## 維護與驗證

```console
python -X utf8 -m unittest discover -s tests -v
python scripts/agf.py audit
```

`audit` 只查結構、連結與語法。[行為案例](evals/README.md)另看選用是否合適及是否增加負擔。修本框架時再讀[維護指引](docs/maintenance.md)，保留真正有用的保護與測試；不以檔數、skill 數或未量測的 token 比例當品質證明。本專案採 MIT 授權。

## 公開前檢查

在本專案目錄檢查準備發布的檔案、暫存區與提交紀錄：

```console
git status --short --untracked-files=all
git ls-files
git diff --cached --name-only
git log --format="%h %an <%ae>"
```

`.agf/` 已由本專案的 `.gitignore` 排除，裡面的本機路徑、診斷與測試輸出仍可能包含私人資料；常見 `.env` 與金鑰副檔名也已排除。`.env.example` 可以追蹤，但仍須確認只含佔位值。忽略規則不會移除已被追蹤或舊 commit 中的資料；若發現憑證或不應公開的歷史，先處理並確認外洩憑證是否需要撤銷，不直接推送。檢查 commit 顯示的作者名稱和電子郵件是否願意公開。必要時依 [工具指引](docs/tools.md)選擇可信的秘密掃描器並核對掃描範圍；任何掃描都不能保證找出所有私人資料。

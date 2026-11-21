# 外部資源資料庫

改善框架、選工具、設計工作流程之前，先查這裡有沒有人研究過。每一筆記錄一個外部專案、skill、MCP、CLI、服務或文章：它是什麼、怎麼運作、授權、資料送往哪裡、限制、對這個框架有什麼用，以及查到哪個深度、哪一天查的。

它是研究紀錄，不是推薦名單，也不是安全背書。外部專案會變，真正採用前照 [tools 指引](../tools.md)與[審查清單](security.md)再查一次版本與資料流。

## 怎麼查

依關鍵字查（在框架根目錄執行，輸出有上限，適合讓 AI 先查再讀相關頁）：

```console
python -m agf.ecosystem find pdf 表格
python -m agf.ecosystem find kernel --limit 5
```

也可以直接用 jq 查 [entries.json](entries.json)：

```console
jq -r '.entries[] | select(.tier == 1) | "\(.id)\t\(.category)\t\(.license.label)"' docs/ecosystem/entries.json
jq '.entries[] | select(.runs == "local" and .category == "document-processing") | {id, resources}' docs/ecosystem/entries.json
```

要看說明與取捨，從下面的分類頁或[比較](#比較)進去。

## 分類

<!-- ecosystem:index -->
| 分類 | 項目 | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---|---|---|---|---|
| [AI coding 工作流程](categories/agent-workflows.md) | 0 | 0 | 0 | 0 | 0 |
| [記憶與 context 管理](categories/memory-context.md) | 0 | 0 | 0 | 0 | 0 |
| [程式理解與 code graph](categories/code-understanding.md) | 0 | 0 | 0 | 0 | 0 |
| [Agent skills 與規則](categories/agent-skills.md) | 0 | 0 | 0 | 0 | 0 |
| [MCP、CLI 與 API 整合](categories/mcp-cli-api.md) | 0 | 0 | 0 | 0 | 0 |
| [Shell 工具與格式轉換](categories/shell-utilities.md) | 0 | 0 | 0 | 0 | 0 |
| [文件解析、OCR 與 PDF](categories/document-processing.md) | 0 | 0 | 0 | 0 | 0 |
| [圖解與視覺化](categories/visualization.md) | 0 | 0 | 0 | 0 | 0 |
| [網頁研究、資料集與擷取](categories/web-research.md) | 0 | 0 | 0 | 0 | 0 |
| [CI/CD、資安與授權工具](categories/security-devops.md) | 0 | 0 | 0 | 0 | 0 |
| [評測、模型路由與可觀測性](categories/benchmark-evaluation.md) | 0 | 0 | 0 | 0 | 0 |
| [寫作、研究與 Podcast](categories/ai-writing.md) | 0 | 0 | 0 | 0 | 0 |
| [音樂與音訊](categories/ai-music.md) | 0 | 0 | 0 | 0 | 0 |
| [影片與動畫](categories/ai-video.md) | 0 | 0 | 0 | 0 | 0 |
<!-- /ecosystem -->

## Tier 1：優先研究

對框架有明顯價值、值得讀原始碼或試跑的項目。

<!-- ecosystem:tier1 -->
| 名稱 | 分類 | 授權 | 證據 | 對框架的價值 |
|---|---|---|---|---|
<!-- /ecosystem -->

## 比較

同類工具放在一起看，找出真正不同的技術方向：

- [記憶系統](comparisons/memory-systems.md)
- [程式理解工具](comparisons/code-understanding.md)
- [文件解析](comparisons/document-parsers.md)
- [網頁研究](comparisons/web-research.md)
- [AI coding 工作流程](comparisons/agent-workflows.md)

其他：[使用者提供的文章](articles.md)、[建議與待確認](recommendations.md)、[外部資源審查清單](security.md)、[授權判讀](license.md)。

## 欄位與標記

每一筆的欄位定義在研究規格 [SPEC.md](../../studies/ecosystem-2026-11/SPEC.md)；`python -m agf.ecosystem check`（`agf audit` 也會跑）檢查格式與表格是否和資料一致。幾個標記：

| 欄位 | 值 |
|---|---|
| `tier` | 1 優先研究；2 值得參考，設計可學但不一定引入；3 特定情境才用；4 暫不建議（維護差、重複、授權不明、資安風險或資源不符） |
| `evidence` | 查到的最深一級：實際執行（`ran`）、讀原始碼（`source`）、讀文件（`docs`）、只有搜尋摘要（`search`） |
| `license.label` | 可使用、有條件、需人工確認、不建議，判讀方式見[授權判讀](license.md) |
| `use` | `direct` 直接用、`integrate` 適合整合、`learn` 學架構、`borrow` 借鑑 skill 的做法、`study-only` 值得研究但不建議安裝、`needs-review` 需要人工確認 |
| `checked` | 最後一次人或 AI 查核內容的日期 |
| `github` | `refresh` 從 GitHub API 抓的事實：最後 push、是否封存、stars、GitHub 偵測的授權、抓取日期 |

`github` 是程式抓的，其他欄位是研究者讀了之後寫的；兩者分開，才知道哪些會自動更新、哪些要人重看。stars 只看熱度，不代表品質。

## 新增或更新一筆

1. 在 `entries.json` 加一筆或改既有的一筆，照 SPEC 的欄位寫；沒查到的寫 `null`，不要猜。
2. 有 GitHub repo 的，執行 `python -m agf.ecosystem refresh --id <id>` 抓維護狀態（需要已登入的 `gh`，只用唯讀 API）。
3. 執行 `python -m agf.ecosystem render` 更新各頁的表格，再跑 `python -m agf.ecosystem check`。
4. 值得多說的，在分類頁的表格下方寫一段：做法、限制、和其他項目差在哪。表格以外的文字是手寫的，`render` 不會動它。

定期維護：`refresh` 全部重抓一次，看哪些已封存或很久沒更新；`checked` 超過半年的 Tier 1、2 項目重看一次。

## 和其他紀錄的關係

- [link-study.md](../link-study.md)、[research.md](../research.md)、[memory-prompt-study.md](../memory-prompt-study.md)、[skillkit-study.md](../skillkit-study.md) 與 [studies/](../../studies/README.md) 是當時的研究紀錄，寫完不再更新；資料庫的項目在 `references` 指回它們。
- 這一輪（S16）的研究規格、子代理的原始筆記與草稿在 [studies/ecosystem-2026-11/](../../studies/ecosystem-2026-11/SPEC.md)。
- 框架要怎麼用這些研究結果，排在[分析報告第六輪](../analysis-2026-11.md#第六輪2026-11-21s16兩份需求的對照與路線圖)的路線圖。

## 限制

- 2026-11-21 第一次建立，由三個子代理研究、主 session 核對整理。多數項目只讀了文件，`evidence` 欄照實標示；作者自己公布的 benchmark 寫成作者自報。
- 授權標記不是法律意見。
- 只查了公開資料；沒有使用者帳號內、公司內網或付費資料庫的資訊。

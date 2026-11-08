# 用文字描述圖，交給工具渲染

使用者說「畫個圖」「幫我畫流程圖」「把這個視覺化」時，AI 先選圖型與樣板，再產出精簡 Mermaid 文字；預設存成 UTF-8 的 `.mmd`。AI 的圖形創作到描述文字為止，SVG、PNG、PDF 交給現有 `mermaid-cli`，指令名稱是 `mmdc`。需要可手動排版的 draw.io 圖時，AI 產出未壓縮 XML，再由 draw.io 工具開啟或匯出。操作工具仍依當次授權；缺渲染器時交付圖源與命令，不自行安裝。

## 1. 先看樣板，再選圖型

只讀本表和適用的一份樣板，不為了找圖型載入全部檔案。以下情境、日期與訊號數值都是示範，不代表目標專案的實際行為。

| 要回答的問題 | 選用樣板 | 保留的差異 |
|---|---|---|
| 作業流程、程式處理步驟、程式碼提交流程 | [flowchart.mmd](flowchart.mmd) | 決策、先後及已知例外路徑 |
| 系統架構、分層及元件關係 | [architecture.mmd](architecture.mmd) | 一層一色；共用元件只出現一次 |
| 模組呼叫、API 互動、FE → COP → FIP → Flash | [sequence.mmd](sequence.mmd) | 訊息順序與方向；沒有證據就不補回傳 |
| 韌體狀態、ticket 生命週期 | [state.mmd](state.mmd) | 狀態與觸發條件；觀察到的轉移不等於完整規格 |
| Host → NAND 等資料路徑 | [flowchart.mmd](flowchart.mmd) 或 [sequence.mmd](sequence.mmd) | 只看資料方向用流程圖；要看互動先後用循序圖 |
| 硬體或系統方塊圖，需要格線排列 | [block.mmd](block.mmd) | 方塊位置由欄數決定，箭頭另表達關係 |
| 何時發生什麼 | [timeline.mmd](timeline.mmd) | 事件順序；時間標籤的間距不代表實際時長 |
| 訊號或狀態維持多久，近似 waveform | [signal-duration.mmd](signal-duration.mmd) | 以甘特圖表示已知區間，並非精確電氣波形 |
| 需求、開發、驗證、里程碑及延誤 | [schedule.mmd](schedule.mmd) | 計畫與實際分列；未提供的日期不自行估填 |

架構圖預設採 `flowchart LR`，讓元件由左往右展開；只有需要格線才改方塊圖。需要手動移動元件、精確固定座標，或使用者明確指定時選 draw.io。不要為了畫圖另找圖像生成服務或新增 MCP；MCP 是讓代理使用外部工具的介面，既有本機渲染器足夠時直接用。

已有文字流程時，直接修改一份 `.mmd`，不再讓 AI 重寫同內容的 JSON；只有先計算統計或需共用模型匯出兩種格式時，才用 `diagram create`。樣板日期與例外分支必須換成本次有根據的內容，不因樣板已有就保留。

已配置專案先讀 `.agf/managed/project-rules.md` 的 CLI 路徑。找到該路徑的 `scripts/` 目錄，再往上一層就是框架根目錄，其中有 `templates/diagrams/`：共享模式位於來源 checkout，工具副本模式位於目標專案 `.agf/managed/runtime/templates/diagrams/`。副本帶有這份說明與樣板，不需回讀原始 checkout；更新時沿用現有 `project plan/update` 流程，勿直接修改受管理的樣板。

## 2. 寫圖源並核對內容

- 每張圖最多 15 個實體；流程圖計節點、循序圖計參與者、狀態圖計狀態、時間線計事件、甘特圖計任務與里程碑。超過就拆總覽與子圖；不要省略影響理解的路徑來湊數。
- 節點可見文字合計不超過 12 字，換行用 `<br/>`；換行不增加字數額度。必要長名稱可用短名稱加圖外對照，不截斷函式或 state 名稱來製造不同識別。
- 每個菱形判斷的出去箭頭都要標籤。二元條件用 `|是|`、`|否|`；多分支照已知條件標示，不能替讀者猜意思。來源只交代一邊，就畫已知分支，並在圖外指出缺少的去向。
- 「退回」「重試」「發 ECR」等失敗路徑按使用者敘述或已確認的程式畫；ECR 若代表工程變更申請，首次使用時先說明。未交代失敗後去哪，不自行補線。
- 重複呼叫的邏輯抽成共用 `subgraph`（子圖區塊），或另畫子圖並給摘要名稱；各呼叫端連入即可。區分控制流與資料流，不把 code 每一行直譯成長鏈。
- 圖外保留來源版本、檔案／行號或統計檔；若只是建議設計，要明示。箭頭與分支須回到來源核對，成功渲染只證明引擎可處理語法。

所有圖型一律沿用以下檔頭，`config:` 下一行先寫 `look: neo`。`frontmatter` 是圖源開頭、以 `---` 包住的設定區。檔案編碼仍要存 UTF-8；字型設定不會修復錯誤編碼，缺字也要核對渲染環境是否已有中文字型。

```yaml
---
config:
  look: neo
  theme: neutral
  fontFamily: 'Noto Sans CJK TC, Microsoft JhengHei, PingFang TC, sans-serif'
---
```

各圖型與版本對 `neo` 的外觀支援可能不同，不能以有此設定推定所有圖長得一致；保留設定，再看實際成品。設定區與圖型語法參考 [Mermaid 官方語法說明](https://mermaid.js.org/intro/syntax-reference.html)及[主題與各圖型預設](https://mermaid.js.org/config/theming.html)。

分層架構沿用 `architecture.mmd`：淡紫、淡藍、淡綠、淡橘、灰色依序使用，每層一個 `classDef`，把 class 套在節點上。底層基礎設施用 `stroke-dasharray:5 5` 虛線；`classDef subgrp fill:none,stroke:none` 搭配 `class <子圖ID> subgrp` 移除子圖背景框。若實際引擎仍畫出框，再改 `style <子圖ID> fill:none,stroke:none`，不移除分層標題。顏色只是輔助，圖中文字與箭頭仍要能獨立說明關係。

## 3. CSV／TXT／LOG 先統計，再畫狀態圖

先確認 state 欄位、每列代表什麼，以及是否混有多台裝置或多個工作階段。不要把原始事件逐行交給模型猜轉移。CSV 是以分隔符號保存欄位的文字表格；副檔名可以是 `.csv`、`.txt` 或 `.log`，但本命令輸入必須有欄名，且使用逗號、Tab 或直線分隔。自由格式日誌先依已確認的欄位規則正規化成這種表格，不猜正規表示式。

例如已有 UTF-8 的 `events.csv`：

```csv
device,state
A,Idle
A,Run
B,Idle
A,Done
B,Run
```

在框架根目錄執行；已配置專案把 `scripts/agf.py` 換成規則中的有效路徑：

```text
python scripts/agf.py diagram transitions events.csv --state-column state --group-column device --output .agf/artifacts/transitions.json
python scripts/agf.py diagram create .agf/artifacts/transitions.json --format mermaid --output .agf/artifacts/states.mmd
python scripts/agf.py diagram render .agf/artifacts/states.mmd --format mermaid --output .agf/artifacts/states.svg --execute
```

Tab 或直線分隔另加 `--delimiter tab` 或 `--delimiter pipe`。統計按實體檔案列序、各群組內的相鄰紀錄計數，沒有依時間排序；此例得到 `Idle → Run` 兩次、`Run → Done` 一次，不會把 A 與 B 串成一條路徑。未提供 `--group-column` 就把整份檔案視為單一事件流；裝置重新啟動等分界也要在輸入的群組或切片中表達。

同狀態連續紀錄會列為自轉移，不默默去重；圖中的計數是樣本觀察次數，不是轉移機率、因果或合法轉移全集。末筆狀態沒有下一筆，不推定它是終止狀態或持續到何時。先檢查 JSON 的輸入身分、分組、排序與計數，再產生 `.mmd`。遇到格式錯誤、空 state 或資料超限，先修正或切片，不交付一張看似完整的圖。

輸入上限為 20 MB、100,000 筆及 15 個不同狀態；狀態名稱限 1–12 字，前後空白、控制字元及 `<br/>` 標記需先明確處理。輸出會含狀態名稱、來源路徑與摘要雜湊；存放與分享時依實際資料範圍檢查，不把 `.agf/` 的忽略規則當成存取控制。

## 4. 渲染 SVG，需要 PNG 再由工具產生

以下命令先預覽，加入 `--execute` 才呼叫現有原生工具；不會安裝 `mmdc`，也不覆寫已有輸出。可先直接以樣板驗證環境，再請 AI 按任務產生自己的 `.mmd`。

```text
python scripts/agf.py diagram validate templates/diagrams/flowchart.mmd --format mermaid
python scripts/agf.py diagram render templates/diagrams/flowchart.mmd --format mermaid --output .agf/artifacts/flowchart.svg
python scripts/agf.py diagram render templates/diagrams/flowchart.mmd --format mermaid --output .agf/artifacts/flowchart.svg --execute
```

`validate` 只辨識宣告，不是完整 Mermaid 解析器。已有渲染器時也可直接執行 `mmdc -i INPUT.mmd -o OUTPUT.svg`；若要 PNG，保留同一圖源，讓 `mmdc` 再產生 PNG，不需要 AI 重畫：

```text
python scripts/agf.py diagram render templates/diagrams/flowchart.mmd --format mermaid --output .agf/artifacts/flowchart.png --execute
```

Windows 的 npm 安裝通常提供 `mmdc.cmd`；框架不以 shell 執行這種轉接檔。已安裝 Mermaid CLI 時，指定真正的 `node.exe` 與該安裝的 JS 入口。以下是路徑格式示範，要換成自己的既有安裝位置：

```text
python scripts/agf.py diagram render templates/diagrams/flowchart.mmd --format mermaid --output .agf/artifacts/flowchart.svg --tool C:/tools/node/node.exe --tool-arg C:/tools/mermaid/src/cli.js --execute
```

SVG 與 PNG 都由外部工具計算，不需要模型生成圖像或把 SVG/XML 的大量座標貼進對話；工具呼叫與回讀仍可能消耗 token，沒有帳務用量就不保證節省比例或零成本。`render` 檢查退出碼與非空輸出，成品仍需檢視字型、換行、分支標籤、裁切及箭頭是否清楚。圖片由工具產出後可直接交付檔案或預覽，不把整份 SVG 原文讀回對話。

圖源應來自本次可用資料；處理不可信來源時，先檢查額外 HTML、連結與設定，不為了渲染降低安全設定。`mmdc` 會啟動本機渲染程序，並非隔離環境；按既有工具政策處理版本、權限及輸出分享。格式與參數以[官方 Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)為準；[時間線](https://mermaid.js.org/syntax/timeline.html)、[甘特圖](https://mermaid.js.org/syntax/gantt.html)與[方塊圖](https://mermaid.js.org/syntax/block.html)依各自語意使用。

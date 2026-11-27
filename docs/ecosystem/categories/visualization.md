# 圖解與視覺化

把技術內容畫成圖：流程、時序、狀態、架構、呼叫圖與資料圖表。框架的做法是 AI 寫 Mermaid 圖源、交 mermaid-cli 渲染（[tools 指引](../../tools.md)的圖解段），這一類以它為基準評估：其他工具要在 Mermaid 不夠用時才值得加，例如要可拖曳編輯（draw.io）、C++ 的 UML（clang-uml）、大型圖的自動排版（Graphviz、ELK）、互動式網路圖（Cytoscape.js）、資料圖表（Observable Plot）。

從原始碼產生的圖，節點要能對回檔案與行號；程式改了就重新產生，不手動維護圖。

<!-- ecosystem:table visualization -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Mermaid CLI（mmdc）與 Mermaid](https://github.com/mermaid-js/mermaid-cli) | CLI | 1 | 可使用（MIT） | 2026-11-16 | 讀文件 | 框架現行基準：AI 寫 .mmd 圖源，mmdc 渲染成 SVG／PNG／PDF，也能直接轉換 Markdown 內的 mermaid 區塊。支援 flowchart、sequence、state、class、ER、gantt、timeline、block、architecture 等。 |
| [clang-uml](https://github.com/bkryza/clang-uml) | CLI | 2 | 可使用（Apache-2.0） | 2026-10-06 | 讀文件 | 以 Clang 為基礎、由 YAML 設定驅動的 C++ UML 產生器：class、sequence（從指定函式開始）、package、include 圖，輸出 PlantUML、MermaidJS、GraphML、JSON；也支援 C99／C11 的 struct 關係與 Objective-C。 |
| [D2](https://github.com/terrastruct/d2) | CLI | 2 | 有條件（MPL-2.0） | 2026-11-21 | 讀文件 | 現代的文字轉圖語言（Go），內建三種排版：Dagro（Dagre 的 Go 移植，預設）、elk-go（ELK 的 Go 移植）、TALA（為軟體架構圖設計，opt-in）；支援 sequence、grid、sketch 手繪風、LaTeX，`d2 --watch` 即時預覽。 |
| [draw.io MCP（官方）](https://github.com/jgraph/drawio-mcp) | MCP | 2 | 可使用（Apache-2.0） | 2026-11-20 | 讀原始碼 | draw.io 官方提供四種整合：MCP App Server（hosted `mcp.draw.io`，在對話中內嵌互動圖）、MCP Tool Server（npm，在瀏覽器開編輯器）、各 agent 的 plugin skill（產生 .drawio，可用 draw.io Desktop 匯出 PNG／SVG／PDF）、免 MCP 的專案指示。吃 draw.io XML、Mermaid、PlantUML、CSV，輸出可編輯的原生圖形。 |
| [Graphviz（dot）](https://gitlab.com/graphviz/graphviz) | CLI | 2 | 有條件（EPL-2.0） | — | 讀文件 | 最老牌的圖形排版工具，DOT 語言描述節點與邊，dot／neato／fdp 等排版。Doxygen、cflow 後處理、許多 call graph 工具的輸出終點。 |
| [claude-mermaid](https://github.com/veelenga/claude-mermaid) | MCP | 3 | 可使用（MIT） | 2026-11-21 | 讀原始碼 | Mermaid 渲染 MCP server＋mermaid-diagrams skill：mermaid_preview 在瀏覽器即時預覽（live reload），mermaid_save 輸出 SVG／PNG／PDF；也能改成發布成 Claude artifact。 |
| [Cytoscape.js](https://github.com/cytoscape/cytoscape.js) | 函式庫 | 3 | 可使用（MIT） | 2026-11-10 | 讀文件 | 多倫多大學出身的圖論與網路視覺化 JS 函式庫，可做互動式節點連線圖與圖分析（最短路徑、中心性等），有學術論文（2016、2023）。 |
| [Doxygen call graph](https://github.com/doxygen/doxygen) | CLI | 3 | 有條件（GPL-2.0） | 2026-11-21 | 只有搜尋摘要 | Doxygen 在 HAVE_DOT／CALL_GRAPH／CALLER_GRAPH 開啟時，呼叫 Graphviz 為每個函式產生呼叫圖與被呼叫圖，HTML 中的節點可點回對應的文件頁與原始碼行。 |
| [ELK（elkjs）](https://github.com/kieler/elkjs) | 函式庫 | 3 | 有條件（EPL-2.0） | 2026-11-09 | 讀文件 | Eclipse Layout Kernel 的 JavaScript 版，只計算版面位置（不畫圖）。主力是分層（Sugiyama）演算法，適合有方向、有 port 的節點連線圖。Mermaid flowchart 現在預設用它，D2 也有 Go 移植版。 |
| [Excalidraw（＋ excalidraw-mcp）](https://github.com/excalidraw/excalidraw) | 應用 | 3 | 可使用（MIT） | 2026-11-21 | 讀文件 | 手繪風白板（MIT）。excalidraw-mcp 是 MCP Apps server，在對話中串流產生手繪圖並可全螢幕編輯；建議用 hosted `https://mcp.excalidraw.com`，也可本機跑。 |
| [Kroki](https://github.com/yuzutech/kroki) | 服務 | 3 | 可使用（MIT） | 2026-11-20 | 讀文件 | 統一的圖表渲染 API：一個 HTTP 介面支援 BlockDiag、BPMN、Bytefield、C4、D2、DBML、Mermaid、PlantUML、Graphviz、Excalidraw 等多種文字圖語言。 |
| [Observable Plot](https://github.com/observablehq/plot) | 函式庫 | 3 | 可使用（ISC） | 2026-11-05 | 讀文件 | 免費開源的 JS 表格資料視覺化函式庫，主打探索式資料分析，API 精簡。適合量化、log 統計、效能數據的圖表，不是節點連線圖工具。 |
| [PlantUML](https://github.com/plantuml/plantuml) | CLI | 3 | 可使用（GPL-3.0-or-later） | 2026-11-21 | 讀文件 | 以文字描述 UML（sequence、class、activity、state、component、deployment 等）與 C4、甘特、心智圖的 Java 工具。clang-uml 可直接輸出 PlantUML。 |
| [Structurizr（C4 model）](https://github.com/structurizr/structurizr) | 專案 | 3 | 可使用（Apache-2.0） | 2026-11-07 | 讀文件 | C4 model 作者做的「models as code」工具：寫一份 Structurizr DSL 模型，產生多張不同層級的架構圖（context、container、component）。可用線上 playground 或本機 Docker（Structurizr local）。舊的 structurizr/cli 已於 2026-02 封存。 |
| [Three.js](https://github.com/mrdoob/three.js) | 函式庫 | 3 | 可使用（MIT） | 2026-11-21 | 讀文件 | 通用 3D JavaScript 函式庫，內建 WebGL 與 WebGPU 渲染器，另有 SVG 與 CSS3D addon。codebase-memory-mcp 的 CBM Lens 3D 視圖這類「Galaxy」圖就是 3D 呈現。 |
<!-- /ecosystem -->

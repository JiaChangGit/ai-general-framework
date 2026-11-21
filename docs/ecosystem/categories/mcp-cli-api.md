# MCP、CLI 與 API 整合

讓 agent 接外部能力的介面：MCP server、CLI、API 與模型 gateway。先問同一件事能不能直接用 CLI 做：GitHub、GitLab 用 `gh`、`glab` 比包成 MCP 省 context，也少一個常駐程式。

MCP 要看連線方式（本機 stdio 或遠端 HTTP）、認證範圍與工具描述；描述與回傳的文件都可能夾帶指令，Context7 的 ContextCrush（CVE-2026-75130）就是這一類。常駐的模型 gateway（LiteLLM proxy 等）不採用，理由見分析報告第六輪。

<!-- ecosystem:table mcp-cli-api -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [gh／glab（原生 CLI 取代 MCP）](https://github.com/cli/cli) | CLI | 1 | 可使用（MIT） | 2026-11-20 | 讀文件 | GitHub 的 `gh` 與 GitLab 的 `glab`。Claude Code 官方成本文件說：gh、aws、gcloud、sentry-cli 這類 CLI 比 MCP 更省 context，因為不需要逐一列出工具定義。 |
| [Context7](https://github.com/upstash/context7) | MCP | 2 | 可使用（MIT） | 2026-11-20 | 讀原始碼 | 把第三方函式庫的最新文件提供給 agent：MCP 工具 `resolve-library-id`（參數 query、libraryName）與 `query-docs`（libraryId、query、可選 version），或 `ctx7` CLI＋skill（`ctx7 library`、`ctx7 docs`）。 |
| [Playwright MCP（＋ Playwright CLI）](https://github.com/microsoft/playwright-mcp) | MCP | 2 | 可使用（Apache-2.0） | 2026-11-18 | 讀原始碼 | 微軟官方的瀏覽器自動化 MCP：用無障礙樹快照（不需 vision 模型）讓 LLM 操作網頁。README 開頭就建議 coding agent 改用 microsoft/playwright-cli＋skills，因為 CLI 不必載入大型 tool schema 與冗長的無障礙樹，較省 token；MCP 適合需要持續瀏覽器狀態的探索式迴圈。 |
| [Claude Code Router](https://github.com/musistudio/claude-code-router) | 應用 | 3 | 可使用（MIT） | 2026-11-21 | 讀文件 | 本機的模型 gateway 與控制台：讓 Claude Code、Codex、Grok CLI、Kimi CLI、OpenCode、Pi 等連到自選的供應商，做路由、重試、金鑰輪替、fallback，另加 web search、vision、MCP 工具，並記錄請求、延遲、token 與費用估計。 |
| [GitHub MCP Server（官方）](https://github.com/github/github-mcp-server) | MCP | 3 | 可使用（MIT） | 2026-11-21 | 讀文件 | GitHub 官方 MCP：遠端（`https://api.githubcopilot.com/mcp/`，OAuth 或 PAT）或本機（Docker／Go binary，stdio）。以 toolset 分組（repos、issues、pull_requests、actions、code_security 等），README 列約 120 多個工具。 |
| [MCP Apps（ext-apps）](https://github.com/modelcontextprotocol/ext-apps) | 函式庫 | 3 | 需人工確認（Apache-2.0） | 2026-11-10 | 讀文件 | MCP 擴充：tool 宣告 `ui://` 資源（HTML 介面），host 呼叫 tool 後在 sandboxed iframe 中顯示，UI 可透過 host 再呼叫其他 tool。規格版本 2026-01-26；ChatGPT、Claude、VS Code、Goose、Postman 等支援。draw.io 與 Excalidraw 的 MCP 都用它在對話中內嵌圖。 |
| [官方 MCP Registry](https://github.com/modelcontextprotocol/registry) | 目錄 | 3 | 需人工確認 | 2026-11-21 | 讀文件 | MCP 官方的 server 清單（像 app store 的 metadata 層），提供 API 給 client 與下游目錄。README 仍寫 2025-09-08 preview 上線、2025-10-24 API v0.1 凍結。 |
| [A2A（Agent2Agent）協定](https://github.com/a2aproject/A2A) | API | 4 | 可使用（Apache-2.0） | 2026-11-20 | 讀文件 | 讓不透明的 agent 應用互相溝通的開放協定：JSON-RPC 2.0 over HTTP(S)，用 Agent Card 描述能力與連線資訊，支援同步、SSE 串流與非同步推播；與 MCP 互補（MCP 接工具，A2A 接 agent）。 |
| [Fastctx](https://github.com/yc-duan/fastctx) | MCP | 4 | 可使用（Apache-2.0） | 2026-11-21 | 讀原始碼 | 1.0 版（beta）：給 agent 一個 `run` 工具，經自己架的 Hub 在多台機器上執行命令、讀改檔案、在機器間複製檔案、讓長時間的工作在背景跑；每台機器有 Activity 紀錄。另有 Workbench：在 Fastctx 的桌面或 Android app 裡和 Claude Code、Codex 對話，等待的工作完成時自動喚醒 agent，也能把子任務交給另一個模型。 |
| [LiteLLM](https://github.com/BerriAI/litellm) | 函式庫 | 4 | 有條件（MIT） | 2026-11-21 | 讀文件 | 用 OpenAI 格式呼叫 100 多家模型的 Python SDK 與 AI Gateway（proxy）：virtual key、花費追蹤、guardrail、負載平衡、Auto Router，也能代理 A2A agent。 |
<!-- /ecosystem -->

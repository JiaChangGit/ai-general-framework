# 評測、模型路由與可觀測性

量框架有沒有幫助、花了多少：評測框架、coding 與記憶 benchmark、模型路由、tracing 與用量統計。框架已有 `evals/host/impact.py` 做有無框架的配對量測。

這一輪最有用的兩個發現：Claude Code 內建的 OpenTelemetry 能把 cost 與 token 依 `skill.name`、`agent.name` 分開，內容紀錄預設關閉，只開 metrics 送到本機就符合使用者的隱私決定；Promptfoo 有斷言 skill 叫用次數的功能（它在 2026-03 被 OpenAI 收購，telemetry 預設開）。各家 benchmark 分數多是自報，不能互比。

<!-- ecosystem:table benchmark-evaluation -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Claude Code 的 OpenTelemetry 監控](https://code.claude.com/docs/en/monitoring-usage) | API | 1 | 可使用 | — | 讀文件 | Claude Code 內建的 OTel 匯出：metrics（session、行數、PR、commit、cost、token、編輯決定、活躍時間）、events（user_prompt、api_request、api_error、tool_decision、tool_result 等）與 beta traces；預設關閉。 |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | CLI | 1 | 可使用（MIT） | 2026-11-21 | 讀原始碼 | 用 YAML 寫測試案例與斷言，對 prompt、模型、RAG 與 agent 跑評測和紅隊測試的 CLI；2026-03-09 宣布被 OpenAI 收購，官方說會維持開源並繼續支援多家模型。 |
| [ccusage](https://github.com/ccusage/ccusage) | CLI | 2 | 可使用（MIT） | 2026-11-21 | 讀文件 | 讀各家 coding agent CLI 存在本機的用量檔（Claude Code 的 JSONL 等），產生日、週、月、session 與 5 小時計費視窗報表；支援 Claude Code、Codex、OpenCode、Gemini CLI、Copilot CLI、Hermes、Pi 等二十多種。 |
| [Arize Phoenix](https://github.com/Arize-ai/phoenix) | 服務 | 3 | 有條件（Elastic-2.0） | 2026-11-21 | 讀文件 | 開源、可自架的 LLM tracing 與評測工具，用 OpenInference（OTel 擴充）instrumentation；`pip install arize-phoenix` 就能在本機跑，另有 /mcp 端點讓 Claude Code 等查 trace。 |
| [DeepEval](https://github.com/confident-ai/deepeval) | 函式庫 | 3 | 可使用（Apache-2.0） | 2026-11-19 | 讀文件 | 像 pytest 的 LLM 評測框架：用 Python 寫測試案例，套用 RAG、多輪對話、agent、語音等指標；母公司 Confident AI 賣雲端平台。 |
| [DSPy 與 GEPA](https://github.com/stanfordnlp/dspy) | 函式庫 | 3 | 可使用（MIT） | 2026-11-21 | 讀文件 | DSPy 用 Python 模組與 signature 描述 LM 程式，再用最佳化器（MIPROv2、GEPA 等）依評測指標自動改 prompt 與示例。GEPA 是反思式、Pareto 演化搜尋的最佳化器，可最佳化任何文字參數。 |
| [Factory Router（Factory.ai Droid）](https://factory.ai/news/factory-router) | 服務 | 3 | 不建議 | — | 只有搜尋摘要 | Factory 的 Droid coding agent 內建的模型路由，2026-06-01 推出：依 prompt、程式範圍、需要的工具判斷難度，從旗艦＋平價模型池挑模型，卡住時升級，並跨供應商 failover。 |
| [Langfuse](https://github.com/langfuse/langfuse) | 服務 | 3 | 有條件（MIT） | 2026-11-21 | 讀文件 | LLM／agent 的 tracing、評測、prompt 管理平台；建在 OpenTelemetry 上，任何 OTel 資料都能送進來。2026 年 1 月起屬於 ClickHouse。 |
| [LongMemEval](https://github.com/xiaowu0162/LongMemEval) | 評測 | 3 | 可使用（MIT） | 2026-05-11 | 讀文件 | 長期對話記憶 benchmark：500 題，測資訊抽取、多 session 推理、知識更新、時間推理與拒答；S 版每題約 115k token（約 40 個 session），M 版約 500 個 session，另有 oracle 版。 |
| [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai) | 目錄 | 3 | 可使用（Apache-2.0） | 2026-11-21 | 讀文件 | GenAI 呼叫的 OTel 命名規範：spans、agent spans、metrics、token metrics、events、MCP、A2A、retrieval，以及 OpenAI、Anthropic、Bedrock 等供應商頁。已從主 semconv repo 搬到獨立 repo。 |
| [Ragas](https://github.com/vibrantlabsai/ragas) | 函式庫 | 3 | 可使用（Apache-2.0） | 2026-11-14 | 讀文件 | RAG 與 LLM 應用的評測工具：LLM 與傳統指標、測試集生成、範本專案（rag_eval、agent_evals、benchmark_llm、prompt_evals、workflow_eval）。原 explodinggradients/ragas，現在在 vibrantlabsai 名下。 |
| [RouteLLM](https://github.com/lm-sys/RouteLLM) | 函式庫 | 3 | 可使用（Apache-2.0） | 2024-08-10 | 讀文件 | LMSYS 的強弱模型路由框架：用 Chatbot Arena 偏好資料訓練路由器（mf、sw_ranking、bert、causal_llm），依門檻把每個查詢送給強模型或弱模型。 |
| [SWE-bench 系列](https://github.com/SWE-bench/SWE-bench) | 評測 | 3 | 可使用（MIT） | 2026-09-18 | 讀文件 | 用真實 GitHub issue 與 PR 測 coding agent 能否修好問題的 benchmark：full、Lite（300）、Verified（500，人工確認）、Multimodal（v2 有 480 題可本機跑）、Multilingual；v5 CLI 有 eval、report、infer。 |
| [Terminal-Bench（與 Harbor）](https://github.com/harbor-framework/terminal-bench-1) | 評測 | 3 | 可使用（Apache-2.0） | 2026-07-11 | 讀文件 | 在真實終端沙箱裡測 agent 能否完成編譯、訓練模型、架服務等端到端工作。原 repo 改名 terminal-bench-1（約 100 題 beta），2.0 版改用 Harbor 框架執行。 |
| [〈AI 成本優化：壓縮、路由、替換，Factory Router 帶來的不只是省錢〉](https://vocus.cc/article/6a2f761ffd89780001b51c13) | 文章 | 3 | 可使用 | — | 讀文件 | 把降低 AI 成本分成壓縮（headroom）、路由（OpenSquilla 規則式、Factory Router 依難度）、替換（deepclaude 換後端、ds4 本機 DeepSeek）三層，主張先診斷瓶頸再選策略。 |
| [LoCoMo](https://github.com/snap-research/locomo) | 評測 | 4 | 有條件（CC-BY-NC-4.0） | 2024-08-13 | 只有搜尋摘要 | Snap Research 的超長多 session 對話記憶 benchmark，是 Mem0、Zep 等記憶產品最常引用的分數來源。 |
<!-- /ecosystem -->

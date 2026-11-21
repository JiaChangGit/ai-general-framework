# 記憶與 context 管理

跨 session 記住偏好、專案決策與工作狀態的工具，以及長期記憶的評測。先看隱私：存下的內容之後再送給模型服務，使用者視為上雲端；寫入時還會另外送模型整理的系統（claude-mem、Mem0、Letta）都要先取得同意。比較見[記憶系統比較](../comparisons/memory-systems.md)。

框架現在用宿主的自動記憶、`profile`、交接檔與續接 hook，不加外部記憶服務。值得借的是 DejaVu 的「決策帶範圍與檢查規則」與 Graphiti 的「失效但保留歷史」。

<!-- ecosystem:table memory-context -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [claude-mem](https://github.com/thedotmack/claude-mem) | 專案 | 2 | 可使用（Apache-2.0） | 2026-11-21 | 讀原始碼 | 用 hook 收集每次工具呼叫，交給另一個模型（observer）寫成 observation 與 session 摘要，存進本機 SQLite＋Chroma；下一個 session 開頭注入精簡索引，需要時再用 MCP 分三步取細節。 |
| [DejaVu（HMAKT99，npm dejavu-dev）](https://github.com/HMAKT99/Dejavu) | CLI | 2 | 可使用（Apache-2.0） | 2026-10-18 | 讀原始碼 | 專案層的「決策記憶」：從 Claude Code／OpenClaw 對話紀錄用規則挖出決策候選，人工審核後寫進 DECISIONS.md，投影到 CLAUDE.md、AGENTS.md、.cursorrules，再用 `dejavu check` 找違反決策或重寫已存在函式的程式。 |
| [Basic Memory](https://github.com/basicmachines-co/basic-memory) | MCP | 3 | 有條件（AGPL-3.0） | 2026-11-20 | 讀文件 | 本機優先的 Markdown 知識庫，透過 MCP 讓 AI 與人讀寫同一批檔案；observations 與 wikilink 形成知識圖，支援語意搜尋與可選的 cross-encoder rerank，雲端同步可選。 |
| [Graphiti（Zep）](https://github.com/getzep/graphiti) | 函式庫 | 3 | 可使用（Apache-2.0） | 2026-11-20 | 讀文件 | 建時間性知識圖的 Python 框架（Zep 的核心）：每個事實（edge）有有效期間，新資訊推翻舊事實時把舊的標成失效而不刪除，每個事實可回溯到原始 episode。 |
| [Letta（原 MemGPT，現為 Letta Code）](https://github.com/letta-ai/letta-code) | 應用 | 3 | 可使用（Apache-2.0） | 2026-11-21 | 讀文件 | Letta 的開發已移到 letta-code：一個有記憶、身分與「做夢」（背景整理記憶）的 agent harness，有 CLI、桌面／網頁、Slack／Telegram 等頻道。原 letta repo 只剩轉址，舊 V1 API server 放在 archive branch。 |
| [Mem0](https://github.com/mem0ai/mem0) | 函式庫 | 3 | 可使用（Apache-2.0） | 2026-11-18 | 讀文件 | 給 AI 應用的記憶層：每次對話後用 LLM 抽出記憶，存進向量庫，之後用語意、BM25、實體三路檢索。有 library、self-hosted server、雲端 Platform 三種用法，另有 CLI、MCP（OpenMemory）與 agent skills。 |
| [Memory OS（ClaudioDrews，Hermes Agent 用）](https://github.com/ClaudioDrews/memory-os) | 專案 | 3 | 可使用（MIT） | 2026-09-20 | 讀文件 | Hermes Agent 的七層記憶：工作區檔案、session 全文搜尋、結構化事實、跨 session fabric、Qdrant 向量庫、自動整理的 wiki，以及要求 agent 把注入內容當權威的「Ground Truth」層。vocus 文章談的 memory-os 是這一份，不是 bmaltais 版。 |
| [OpenHuman](https://github.com/tinyhumansai/openhuman) | 應用 | 3 | 有條件（GPL-3.0） | 2026-11-20 | 讀文件 | vocus 文章介紹它時是「桌面記憶全家桶」（Memory Tree、118 個 OAuth 服務、TokenJuice 壓縮）；現在 README 改稱 Rust 寫的 agent harness，記憶是內建功能之一：每輪前在 token 預算內挑記憶並附出處。 |
| [〈AI Agent 的遺忘不是一個問題，是七個：memory-os 的分層設計〉](https://vocus.cc/article/6a37e0c6fd8978000159fc90) | 文章 | 3 | 可使用 | — | 讀文件 | 介紹 ClaudioDrews/memory-os 的七層記憶，主張向量搜尋＋注入只解決「找到」，沒解決「agent 會不會用」。 |
| [〈AI 每換一個工具就把你忘光？本地記憶層的四個開源答案〉](https://vocus.cc/article/6a48c442fd89780001ba1661) | 文章 | 3 | 可使用 | — | 讀文件 | 把 dejavu（pip dejavu-memory）、mem-agent、OpenHuman、memory-os（ClaudioDrews）從輕到重排成一排，依部署重量、隱私、授權、社群活躍度選。 |
| [dejavu（jsingletonai，pip dejavu-memory）](https://github.com/jsingletonai/dejavu) | 專案 | 4 | 需人工確認（Apache-2.0） | — | 只有搜尋摘要 | vocus〈本地記憶層的四個開源答案〉的第一個專案：`pip install dejavu-memory`，記使用者習慣與偏好，存在 ~/.dejavu/ 的 SQLite，提供 Python、CLI、REST、MCP 四種介面。和 HMAKT99/Dejavu（專案決策）是不同專案。 |
| [mem-agent（Dria／firstbatch）](https://github.com/firstbatchxyz/mem-agent) | 專案 | 4 | 需人工確認 | 2025-10-09 | 只有搜尋摘要 | 用強化學習把「管理 Markdown 記憶」訓進 Qwen3-4B-Thinking 的 4B 模型；記憶是 Obsidian 風格的 user.md＋entities/ 資料夾，透過 mem-agent-mcp 讓其他模型在背景呼叫它讀寫記憶。 |
| [memory-os（bmaltais）](https://github.com/bmaltais/memory-os) | 專案 | 4 | 需人工確認 | 2026-06-28 | 讀原始碼 | 給 Claude Code、Grok、Pi 的多 agent 記憶：SessionStart 注入最多 32 KB 的「凍結快照」，Stop hook 把每輪對話寫成 Markdown log 與 SQLite，`memory-os recall` 用 FTS5＋向量混合搜尋並附出處。 |
<!-- /ecosystem -->

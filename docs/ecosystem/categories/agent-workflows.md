# AI coding 工作流程

<!-- ecosystem:table agent-workflows -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [pstack（上游，cursor/plugins/pstack）](https://github.com/cursor/plugins/tree/main/pstack) | skill 集 | 1 | 可使用（MIT） | 2026-11-21 | 讀原始碼 | Lauren Tan（poteto）為 Cursor 寫的工程 skill 組，是所有 pstack 版本的上游。入口是 poteto-mode：依任務選 22 個 playbook（舊版 README 寫 23 個，後來刪了 orchestrate），再叫用 how、why、architect、arena、interrogate、tdd 等 skill 與 24 條 principle-* 原則。 |
| [second-opinion（Trail of Bits skills）](https://github.com/trailofbits/skills/tree/main/plugins/second-opinion) | skill | 1 | 有條件（CC-BY-SA-4.0） | 2026-11-21 | 讀文件 | 讓 Claude Code 用 Codex 或 Antigravity（Gemini）CLI 對未提交變更、分支差異或某個 commit 做外部審查，只產出發現，不改檔、不發到遠端。 |
| [ACE（Agentic Context Engineering）](https://github.com/ace-agent/ace) | 論文 | 2 | 可使用（Apache-2.0） | 2026-08-24 | 讀文件 | 讓 agent 自我改進的方法：把 context 當成會演化的「playbook」，由 Generator 產生軌跡、Reflector 抽出教訓、Curator 把教訓寫成局部 delta 更新（帶有用／有害計數），避免反覆重寫造成細節流失。 |
| [Codex plugin for Claude Code（OpenAI 官方）](https://github.com/openai/codex-plugin-cc) | 專案 | 2 | 可使用（Apache-2.0） | 2026-07-08 | 讀文件 | 在 Claude Code 裡叫 Codex：/codex:review（唯讀審查未提交或分支差異）、/codex:adversarial-review（可指定焦點、質疑設計）、/codex:rescue 委派工作、/codex:transfer 把目前 Claude 對話交給 Codex 接手，以及背景工作的 status／result／cancel。 |
| [Effective context engineering for AI agents（Anthropic）](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 文章 | 2 | 可使用 | — | 讀文件 | Anthropic Applied AI 團隊的文章：context 是有限資源，長 context 會 context rot；技巧包括 compaction、結構化筆記（NOTES.md、待辦）、子代理回傳 1,000～2,000 token 摘要、只帶路徑等識別碼再即時讀取、工具少重疊且回傳精簡。 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | CLI | 2 | 可使用（MIT） | 2026-11-20 | 讀文件 | 比 Spec Kit 輕的規格層：每個變更一個資料夾（proposal、specs delta、design、tasks），archive 時把 delta 合進活的 specs。 |
| [Ponytail](https://github.com/DietrichGebert/ponytail) | skill 集 | 2 | 可使用（MIT） | 2026-10-29 | 讀原始碼 | 「懶惰的資深工程師」規則：動手前依序問需不需要、codebase 有沒有、標準庫或平台有沒有、已裝套件有沒有、一行能不能解決，最後才寫最少程式；同時列出絕不省略的驗證、安全與資料保護。 |
| [pstack-claude（michael-denyer 移植版）](https://github.com/michael-denyer/pstack-claude) | skill 集 | 2 | 可使用（MIT） | 2026-11-21 | 讀原始碼 | 把上游 pstack 在安裝前就翻成 Claude Code、Codex、Pi、Copilot、Muse、Kimi 等宿主的版本，另外併入 Cursor 的 cursor-team-kit（deslop、fix-ci 等）與 thermos，並帶 55 個自己的 policy fork。 |
| [pstack（backnotprop 鏡像）](https://github.com/backnotprop/pstack) | skill 集 | 2 | 可使用（MIT） | 2026-11-20 | 讀原始碼 | 上游 pstack 的鏡像，不是另一份實作：upstream 分支放 Cursor 原檔，main 分支加上「各宿主都能讀」的改寫與少數社群修正。框架 11-09 讀的 a6342de 就是這份。 |
| [Spec Kit](https://github.com/github/spec-kit) | CLI | 2 | 可使用（MIT） | 2026-11-20 | 讀原始碼 | GitHub 的規格驅動開發工具：`specify` CLI 在專案建 `.specify/`，再用 constitution、specify、clarify、plan、tasks、analyze、implement、converge 等指令依序從規格走到實作。 |
| [Superpowers](https://github.com/obra/superpowers) | skill 集 | 2 | 可使用（MIT） | 2026-11-03 | 讀文件 | 以 SessionStart hook 注入 bootstrap、強制「可能適用就先叫 skill」的工作流程組：brainstorming、writing-plans、TDD、systematic-debugging、verification-before-completion、subagent-driven-development 等。 |
| [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | skill 集 | 3 | 有條件（MIT） | 2026-11-21 | 讀文件 | 以角色（PM、架構師、開發者等）與模組（Method、Builder、Test Architect、Loop、Game Dev）組成的完整開發流程，V7 改成 skill 為主（alpha）。 |
| [Ponytail — Hermes edition](https://github.com/pdscomp/Ponytail) | skill | 3 | 可使用（MIT） | 2026-10-23 | 讀原始碼 | Ponytail 的改寫版，給 Hermes Agent 的 skill 系統用；作者說約 9% 字句與上游相同，其餘重寫。分叉自上游 b6c0448（2026-07-10）。 |
| [pstack for Claude Code（PickleBoxer 移植版）](https://github.com/PickleBoxer/pstack) | skill 集 | 4 | 可使用（MIT） | 2026-10-08 | 讀原始碼 | 把上游 pstack 包成 Claude Code plugin 的另一個移植，盡量少改上游檔，Claude Code 專屬的東西放在新檔：一個 TypeScript mod 在執行時把 Task、AskQuestion、Grok 模型名換成 Claude Code 的。 |
<!-- /ecosystem -->

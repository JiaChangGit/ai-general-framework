# AI coding 工作流程

讓 AI 做工程工作的方法：規劃、設計取捨、驗證、交接、控制產出量。多數是 skill 集或規則，差別在觸發方式與自主程度。框架現在的對應是 `align-with-me`、workflow 指引與常駐規則；逐項對照見 [AI coding 工作流程比較](../comparisons/agent-workflows.md)。

選的時候先看兩件事：skill 由誰叫用（使用者、模型，或每個 session 強制注入），以及它會不會自己做外部動作（開 PR、合併、使用任何 MCP）。後者和框架「不 push、不開 PR」的規則衝突，只能借設計。pstack 有一份上游、三種包裝，Ponytail 有兩版，比較頁有分清楚。

<!-- ecosystem:table agent-workflows -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Anthropic：Claude Code best practices](https://code.claude.com/docs/en/best-practices) | 文章 | 1 | 需人工確認 | — | 讀文件 | 官方的使用建議：給 Claude 一個會回報通過或失敗的檢查，讓它自己跑、讀結果、迭代；要求附證據，「All tests pass」本身說明不了什麼；CLAUDE.md 保持短，只放從程式碼看不出來的事與「已經糾正過兩次的事」；一句規則一再加強語氣還是被忽略，就改成 hook；同一個問題糾正兩次失敗，就 /clear 寫更好的指示重來；審查用新的、唯讀的子代理，並要求依規格審、跳過風格。 |
| [Lauren Tan：先建立信任，再放手讓 AI 合併 PR（AI Engineer 2026 演講）](https://www.inside.com.tw/article/42920-lauren-tan-spacexsi-trust-pyramid-ai-engineer-code-2026) | 文章 | 1 | 需人工確認 | — | 只有搜尋摘要 | pstack 的作者在 SpaceX AI（Grok Bot）講 AI 讓 PR 數量暴增時怎麼守住品質：驗證是最重要的能力（讓 AI 能自己跑程式、像使用者一樣操作、看 trace 與截圖）；每次糾正都先想能不能變成確定性檢查（例如在產品程式碼裡禁用 React 的 useEffect）；壞寫法會被下一個 AI 照抄；註解容易過時、又讓 AI 替繞路找理由，所以禁掉大部分註解，改用錯誤訊息清楚的 lint。 |
| [OpenAI：Harness engineering（2026-02-11）](https://openai.com/index/harness-engineering/) | 文章 | 1 | 需人工確認 | — | 讀文件 | Codex 團隊用 agent 寫完一個內部產品（作者自述約一百萬行、五個月、約 1,500 個 PR）。重點：AGENTS.md 只當目錄（約 100 行），知識放在結構化的 docs/ 裡漸進揭露；架構分層用自訂 lint 與結構測試強制，lint 的錯誤訊息寫成給 agent 的修正指示；review 意見與使用者回報的 bug 直接寫進工具；定期的 doc-gardening agent 掃出和程式行為不符的文件並開修正 PR；agent 透過 Chrome DevTools、截圖與每個 worktree 自己的 log、metrics、trace 驗證成果。 |
| [pstack（上游，cursor/plugins/pstack）](https://github.com/cursor/plugins/tree/main/pstack) | skill 集 | 1 | 可使用（MIT） | 2026-11-21 | 讀原始碼 | Lauren Tan（poteto）為 Cursor 寫的工程 skill 組，是所有 pstack 版本的上游。入口是 poteto-mode：依任務選 22 個 playbook（舊版 README 寫 23 個，後來刪了 orchestrate），再叫用 how、why、architect、arena、interrogate、tdd 等 skill 與 24 條 principle-* 原則。 |
| [second-opinion（Trail of Bits skills）](https://github.com/trailofbits/skills/tree/main/plugins/second-opinion) | skill | 1 | 有條件（CC-BY-SA-4.0） | 2026-11-21 | 讀文件 | 讓 Claude Code 用 Codex 或 Antigravity（Gemini）CLI 對未提交變更、分支差異或某個 commit 做外部審查，只產出發現，不改檔、不發到遠端。 |
| [ACE（Agentic Context Engineering）](https://github.com/ace-agent/ace) | 論文 | 2 | 可使用（Apache-2.0） | 2026-08-24 | 讀文件 | 讓 agent 自我改進的方法：把 context 當成會演化的「playbook」，由 Generator 產生軌跡、Reflector 抽出教訓、Curator 把教訓寫成局部 delta 更新（帶有用／有害計數），避免反覆重寫造成細節流失。 |
| [Codex plugin for Claude Code（OpenAI 官方）](https://github.com/openai/codex-plugin-cc) | 專案 | 2 | 可使用（Apache-2.0） | 2026-07-08 | 讀文件 | 在 Claude Code 裡叫 Codex：/codex:review（唯讀審查未提交或分支差異）、/codex:adversarial-review（可指定焦點、質疑設計）、/codex:rescue 委派工作、/codex:transfer 把目前 Claude 對話交給 Codex 接手，以及背景工作的 status／result／cancel。 |
| [Effective context engineering for AI agents（Anthropic）](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 文章 | 2 | 可使用 | — | 讀文件 | Anthropic Applied AI 團隊的文章：context 是有限資源，長 context 會 context rot；技巧包括 compaction、結構化筆記（NOTES.md、待辦）、子代理回傳 1,000～2,000 token 摘要、只帶路徑等識別碼再即時讀取、工具少重疊且回傳精簡。 |
| [Matt Pocock：Software fundamentals matter more than ever（AI Engineer Europe 2026）](https://ai.engineer/talks/software-fundamentals-for-ai-coding) | 文章 | 2 | 需人工確認 | — | 只有搜尋摘要 | AI 協助開發仍靠軟體基本功：共同的設計概念、精確的領域用語、快速的回饋迴圈、可測試的架構，以及人對系統設計的持續擁有權。 |
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

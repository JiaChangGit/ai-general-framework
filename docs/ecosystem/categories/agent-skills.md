# Agent skills 與規則

外部的 skill 集、skill 目錄網站，以及 skill 怎麼組合與觸發的研究。skill 是會被模型讀進去的指令，安裝前照[審查清單](../security.md)第 3 節看過。skill 目錄網站的安全分數只看 SKILL.md，不掃附帶的腳本：davila7 的 clean-code 拿到滿分，卻要求執行其他目錄的腳本。

做遊戲與互動 3D 可以看 Godogen（Godot、Bevy、three.js 等引擎的指南與素材生成；它從「一步步的流程指引」改成「只給建構元件」，和框架的方向一致）；要上架 App 前可以跑 App Store Compliance Playbook 的檢查腳本（117 種被拒模式，授權對營收超過 2,000 萬美元的公司收費、不授權拿來訓練 AI）。聊天機器人的安全邊界見框架的 `templates/domains/support-chatbot.md`。

框架的原則是 skill 少而專（SkillsBench：2～3 個專注的 skill 效果最好），外部 skill 多半借做法，不整包安裝。韌體與 kernel 相關的有 Trail of Bits 的 c-review 等與 embedded-review。

<!-- ecosystem:table agent-skills -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [security-audit（Cloudflare）](https://github.com/cloudflare/security-audit-skill) | skill | 1 | 可使用（MIT） | 2026-09-14 | 讀原始碼 | 把 agent 變成資安稽核員的 skill：預設只當 guidance，使用者明確要求完整稽核才跑六階段（偵察、以 coverage ledger 驅動的獵捕、候選驗證、結構化輸出、獨立紀錄複核、中立報告）。是 Cloudflare 漏洞挖掘 harness 的起點。 |
| [Trail of Bits Skills Marketplace](https://github.com/trailofbits/skills) | skill 集 | 1 | 有條件（CC-BY-SA-4.0） | 2026-11-21 | 讀原始碼 | 資安顧問公司 Trail of Bits 的 99 個 skill：c-review、rust-review、modern-cpp、static-analysis（codeql、semgrep、sarif-parsing）、testing-handbook（libFuzzer、AFL++、ASan、coverage、OSS-Fuzz 等）、property-based-testing、mutation-testing、constant-time-analysis、zeroize-audit、variant-analysis、supply-chain-risk-auditor、trailmark 系列等。 |
| [agnix](https://github.com/agent-sh/agnix) | CLI | 2 | 可使用（MIT OR Apache-2.0） | 2026-11-21 | 讀文件 | agent 設定檔的 linter：宣稱 763 條規則，檢查 CLAUDE.md、AGENTS.md、SKILL.md、hooks、MCP 設定在 Claude Code、Codex、OpenCode、Cursor、Copilot 的相容性，可自動修正，有 GitHub Action 與 VS Code 擴充。 |
| [anthropics/skills](https://github.com/anthropics/skills) | skill 集 | 2 | 可使用（Apache-2.0） | 2026-11-16 | 讀原始碼 | Anthropic 官方的 skill 範例集（19 個）：文件類 docx／pdf／pptx／xlsx、skill-creator、mcp-builder、webapp-testing、frontend-design、claude-api 等，另附 Agent Skills 規格與範本。README 註明是示範與教育用途。 |
| [App Store Compliance Playbook](https://github.com/mjmirza/app-store-compliance) | skill | 2 | 有條件（LicenseRef-OpenRoots-ORA-2.3） | 2026-11-19 | 讀原始碼 | 避免 App Store 與 Google Play 審核被拒：整理 117 種被拒模式與修正方式，附一支可單獨執行、也能當 PreToolUse hook 的檢查腳本，掃描 iOS、Android 與 Flutter、React Native、Capacitor 專案，依嚴重度回報並給修正指示。 |
| [embedded-review](https://github.com/ylongw/embedded-review) | skill | 2 | 可使用（MIT） | 2026-03-13 | 讀文件 | 嵌入式／韌體 code review skill：P0～P3 嚴重度，涵蓋記憶體安全、中斷安全、RTOS 誤用、硬體介面、C/C++ 陷阱；目標 STM32、nRF、ESP32、RP2040、FreeRTOS／Zephyr／ThreadX、嵌入式 Linux。 |
| [Godogen](https://github.com/htdt/godogen) | skill 集 | 2 | 可使用（MIT） | 2026-11-19 | 讀原始碼 | 讓 Claude Code、Codex、Antigravity 做遊戲與引擎渲染類內容（影片簡報、預告、互動 3D）的兩個 skill：engine-guide 說明 Godot、Bevy、Babylon.js、three.js、HTML 怎麼選、怎麼建、怎麼無頭擷取截圖與影片，以及不會報錯的陷阱；asset-gen 產生圖片、精靈圖、3D 模型、音效與語音。 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | skill 集 | 2 | 可使用（MIT） | 2026-11-19 | 讀原始碼 | Matt Pocock 的工程 skill：grilling、to-spec、to-tickets、tdd、diagnosing-bugs、handoff、teach 等；把只能由使用者叫用的流程 skill 和模型自動叫用的能力 skill 分開。 |
| [Vercel：AGENTS.md 在 agent eval 勝過 skills（2026-01-27）](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) | 文章 | 2 | 可使用 | — | 讀文件 | 用 Next.js 16 新 API 的 eval 比較：無文件 53%、skill 預設 53%（56% 的案例 skill 從未被呼叫）、skill 加明確指示 79%、AGENTS.md 放壓縮過的文件索引 100%。 |
| [apple-design（dickwu）](https://github.com/dickwu/apple-design-skill) | skill | 3 | 有條件 | 2026-11-13 | 讀原始碼 | 以 Apple Human Interface Guidelines 為依據的 UI/UX 設計審查 skill：SKILL.md（436 行）＋ references/hig/ 下約 124 份從 developer.apple.com 抓下的 HIG 頁面＋ hig-lookup 對照表，涵蓋 iOS、macOS、Flutter、React Native、Tauri、Electron。 |
| [openai/skills（已棄用，改 openai/plugins）](https://github.com/openai/skills) | skill 集 | 3 | 需人工確認 | 2026-10-28 | 讀原始碼 | Codex 的 skill 目錄：.system（Codex 內建）、.curated（約 39 個，如 gh-fix-ci、security-threat-model、playwright、yeet）、.experimental。README 開頭標示 repo 已棄用，請改用 openai/plugins。 |
| [Skills Directory（skillsdirectory.com）](https://www.skillsdirectory.com/) | 目錄 | 3 | 需人工確認 | — | 讀文件 | skill 目錄網站，宣稱掃描過 790,436 個 skill、120 個偵測樣式、10 類威脅，每個 skill 給 A～F 等級與分數，可嵌入 README badge；有付費 Pro。 |
| [skills.sh 與 skills CLI（Vercel）](https://github.com/vercel-labs/skills) | 目錄 | 3 | 可使用（MIT） | 2026-11-17 | 讀原始碼 | Vercel 的 skill 目錄與 `npx skills add <owner/repo>` 安裝 CLI。排行依安裝數（全期約 149 萬次）；/audits 頁合併 Gen Agent Trust Hub、Socket、Snyk 三家的稽核結果。 |
| [stop-slop](https://github.com/hardikpandya/stop-slop) | skill | 3 | 可使用（MIT） | 2026-03-17 | 讀原始碼 | 去除 AI 寫作痕跡的 skill：刪填充語、打破公式化結構、主動語態、具體、變化節奏、不用 em dash，最後用五個面向各 1～10 分評分，低於 35/50 就重寫。 |
| [claude-skills-marketplace（mhattingpete，含 flowchart-creator）](https://github.com/mhattingpete/claude-skills-marketplace) | skill 集 | 4 | 可使用（Apache-2.0） | 2026-07-25 | 讀原始碼 | 18 個 skill 的 marketplace，分 code-operations、engineering-workflow、productivity、visual-documentation 四個 plugin，另有 execution-runtime Python 套件。flowchart-creator 只是教模型手寫 HTML＋SVG 流程圖（固定配色、節點形狀）。 |
| [clean-code（davila7/claude-code-templates）](https://github.com/davila7/claude-code-templates/blob/main/cli-tool/components/skills/development/clean-code/SKILL.md) | skill | 4 | 可使用（MIT） | 2026-11-21 | 讀原始碼 | 「務實的程式碼規範」skill：SRP、DRY、KISS、YAGNI，命名規則，函式最多 20 行、最多 3 個參數、巢狀最多 2 層，以及一張「各角色 agent 完成後必須跑的驗證腳本」表。 |
<!-- /ecosystem -->

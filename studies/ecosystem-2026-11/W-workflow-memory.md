# W：workflow、記憶、評測與可觀測性（原始筆記）

2026-11-21，子代理 W。範圍：A（AI coding workflow）、B 的記憶部分、I（評測與模型路由）、H 的可觀測性、使用者提供的四篇文章。資料庫草稿在 [`drafts/W.json`](drafts/W.json)（48 筆）。

**方法與證據標記。** Tier 1 候選用 `git clone --depth 1` 到 `~/.cache/agf-ecosystem/repos/`，只讀檔案，沒有執行、build 或安裝。其他項目讀 README 或官方文件（`curl` 讀 raw 檔、WebFetch 讀網頁；WebFetch 由小模型摘要，引號裡的原文要再回查才能引用）。維護狀態用 `gh api` 唯讀查詢。來源標 `[CLONED]`、`[READ]`、`[SEARCH-ONLY]`；作者自己公布的數字一律寫「作者自報」。stars 只代表熱門。

**沿用的既有紀錄。** Ponytail、mattpocock/skills、superpowers、Spec Kit、OpenSpec、BMAD、claude-mem、beads、rtk、caveman 的基本結論在 `studies/research-2026-11/A-projects.md`；pstack（backnotprop 版 a6342de）、Ponytail 96608e0、Supermemory 在 `docs/link-study.md`；Promptfoo 的資料流與可執行斷言在 `docs/memory-prompt-study.md`。這裡只補新資訊。

## 0. 總覽

| 分類 | 筆數 | 讀原始碼（source） |
|---|---|---|
| AI coding workflow（含多模型協作、context engineering） | 17 | pstack 四版、Ponytail 兩版、Spec Kit、mattpocock/skills |
| 記憶（含 PKM、記憶 benchmark） | 13 | claude-mem、DejaVu（HMAKT99）、memory-os（bmaltais） |
| 評測與模型路由 | 9 | Promptfoo |
| 可觀測性 | 5 | 無（都是文件） |
| 文章 | 4（另 1 篇 Anthropic 文章算在 workflow） | — |
| 合計 | 48 | 12 筆 source、32 筆 docs、4 筆 search |

**Tier 1 調整。** 預計的 Tier 1 是 pstack、claude-mem、memory-os、Dejavu、Spec Kit、Promptfoo，都讀了原始碼。讀完後依「對這個框架的價值」重新分級，最後 Tier 1 只留 4 筆：

- `pstack-cursor`（上游）：correct、reflect、why、arena 的機制可直接改進框架的維護與審查指引。
- `promptfoo`：有 claude-agent-sdk provider 和「skill 叫用次數」斷言，能把框架 evals 的觸發測試自動化。
- `claude-code-otel`：Claude Code 內建的 OTel，cost／token 帶 `skill.name`、`agent.name`，不開內容紀錄就能量 skill 與子代理的實際成本。
- `trailofbits-second-opinion`：跨模型審查的契約寫得最完整，可補框架的「換模型審查」。

降級的理由：claude-mem 的 observer 會把工具輸出送模型、telemetry 預設開，和使用者的隱私決定衝突（Tier 2，只學設計）；memory-os（bmaltais）沒有授權、宣傳與實作不符（Tier 4）；DejaVu（HMAKT99）設計好但只有 1 星、重複偵測不支援 C/C++/Rust（Tier 2）；Spec Kit 流程重（Tier 2）。

## A. AI coding workflow

### 查了什麼、怎麼查、沒查到什麼

- **Clone：** cursor/plugins（sparse，只取 pstack/，792440e）、backnotprop/pstack（c3464c1）、michael-denyer/pstack-claude（97d2ba2）、PickleBoxer/pstack（01a3029）、DietrichGebert/ponytail（96608e0）、pdscomp/Ponytail（35bc9fa）、github/spec-kit（a4d5712）、mattpocock/skills（abeeaf9）。
- **讀文件：** superpowers v7.0.0 release notes、OpenSpec v2.0.0 release notes、BMAD LICENSE、openai/codex-plugin-cc README、trailofbits second-opinion SKILL.md、claude-code-router README、ACE README、GEPA README、DSPy README、A2A README、Anthropic〈Effective context engineering for AI agents〉。
- **搜尋：** HN Algolia API（claude-mem、mem0、letta code、spec-kit、pstack、promptfoo、litellm）；WebSearch（跨模型審查工具）。
- **沒查到／沒做：** pstack 沒有 HN 或 Reddit 的使用者討論（HN 搜 pstack 只出現 Linux 的同名除錯工具）；Ponytail 自 11-09 後沒有新 commit，沒有新資訊；Mesh、2ndOpinion、Gauntlet、ask-llm、multicli 只有搜尋摘要；PAL MCP（原 Zen MCP）2025-12 後沒更新，沒讀 README。

### pstack：誰是上游、誰是移植

結論：**上游只有一份，是 Cursor 官方 plugins repo 裡的 `pstack/`，作者 Lauren Tan（poteto）。** 其他三個都是同一份內容的不同包裝，差別在「怎麼適配 Claude Code」與「有沒有改行為」。

| repo | 關係 | 讀到的版本 | 和上游 58 個 SKILL.md 比 | skill 叫用方式 | Claude Code 適配 |
|---|---|---|---|---|---|
| [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/main/pstack) [CLONED] | **上游** | 0.15.46 @ 792440e（2026-11-21） | — | 除 setup-pstack 外都設 `disable-model-invocation`，只能由 `/指令` 或 poteto-mode 叫用 | `docs/harness/claude-code.md` 對照表，模型每個 session 讀一次、執行時自己翻 |
| [backnotprop/pstack](https://github.com/backnotprop/pstack) [CLONED] | **鏡像** | 0.15.46，同步到上游 0b46ec3（c3464c1，2026-11-20） | 43 個逐字相同、15 個改寫 | 同上游 | 把 Cursor 專用名詞改寫成「Cursor 用 X、Claude Code 用 Y」 |
| [michael-denyer/pstack-claude](https://github.com/michael-denyer/pstack-claude) [CLONED] | **移植＋分支** | port 0.9.146，上游 sha 0b46ec3（97d2ba2，2026-11-21） | 0 個逐字相同（57 個同名、全部翻過） | **全部可由模型自動叫用**（generate.mjs 遇到 `disable-model-invocation: true` 直接報錯）；principle-* 設 `user-invocable: false` | 安裝前用產生器翻好；SessionStart hook 注入路由 |
| [PickleBoxer/pstack](https://github.com/PickleBoxer/pstack) [CLONED] | **移植（停更）** | 0.15.15+claude.7（01a3029，2026-10-08） | 3 個相同、46 個不同、9 個缺 | 上游設定，只把 principle 的旗標拿掉 | TypeScript mod 在執行時翻譯 |

細節：

- **backnotprop 是框架 11-09 讀過的那份。** MIRROR.md 寫明兩個 branch：`upstream` 放 Cursor 原檔，`main` 是 upstream 加本地改寫，用 `git merge upstream` 讓 git 只套上游變動。SYNC-LOG.md 每天記一列（含「沒變」），10-04 的 0.15.9 到 11-20 的 0.15.46。只收 bug fix，改行為的 PR 請送上游。另外帶一個社群修正（#24 watch-pr）。
- **michael-denyer 是最大的分支。** `tools/upstream.json` 固定三個上游元件（pstack、cursor-team-kit、thermos）的 sha；`tools/forks.json` 逐檔宣告 55 個分歧（50 個 policy、5 個 port-feature），每個寫 `why`、`since`，全部 `upstream: not-proposed`。還支援 Codex、Pi、Copilot、Muse、Kimi、OpenCode、Grok、Antigravity。SessionStart hook（startup／resume／clear／compact 都觸發）注入一段 `<EXTREMELY_IMPORTANT>` 路由說明：改超過一個檔、架構選擇、原因不明的 bug 就走 poteto-mode。它也加了 TLA+ 模型（tla/PiScheduler）與 create-formal-verification-skill（TLA+、Lean、Kani）。行為上和上游最大的不同是叫用方式：上游刻意讓 skill 只能由使用者叫，這個移植讓 67 個 skill 都進模型的清單。
- **PickleBoxer** 用 `git subtree split --prefix=pstack` 追上游，Claude Code 專屬的東西放新檔，`hooks/register.tsx`（約 330 行）用 `'claude-code'` 模組的 atom／store／ui API。註解寫「組織的安全 plugin 可能略過使用者層的 skill.prompt hook，所以改走 prompt.submit 與 Read」。10-08 後沒更新。

### pstack 的機制（使用者點名的部分，讀上游 792440e）

11 月中上游大幅縮短 skill 文字（SYNC-LOG 11-17：「Shorter skill texts」），下面是縮短後的內容。

- **how**：開一個唯讀子代理，一次探索並寫給「不熟這區的資深工程師」看的架構說明；主 session 只做輕度編輯，不重寫。
- **why**：「從紀錄回答，不是從程式」：讀引入目標與之後每次修改的 commit、PR 討論，引用作者原話，推論標成推論，並說出紀錄沒回答的部分。
- **teach**：`how`＋`why` 的組合。先依對方的目的（要改、要審、要除錯、剛接觸）決定幾個重點；先給一兩句最小完整答案再停；三個以上元件的系統要畫一連串圖，每張在前一張上加一個元件；`why` 的保留語氣不能改掉。ginseng ep091 示範每講一個資安名詞就跑一次 teach，讓 AI 用作者自己的專案舉例。
- **architect**：先追過所有受影響的系統，畫兩種不同的形狀（型別、簽名、模組邊界），挑「每份狀態只有一個擁有者、每件事只有一種做法、呼叫端要知道的最少」的那個；workaround 反覆出現就重設計。大型或有爭議的設計改跑 arena。
- **arena**：先列 3～6 條可打分的 rubric（只給 picker 用，候選看不到）；N 個模型（預設 Fable 5.2 high、Opus 5.5 high-fast、Gemini 4 Neon xhigh）各在自己的 worktree 做同一題，並寫出考慮過與放棄的方案；一個**不同廠商**的唯讀 judge 依 rubric 打分；主 session 逐條讀完再選 base，跟 judge 不一致就回頭看 rubric；從落選者手工 graft 一兩個優點；候選差太多代表題目沒定好，要重來而不是平均。
- **root cause analysis**：沒有獨立 skill，在 `principle-fix-root-causes` 與 bug-fix playbook。重點：先判斷觸發症狀的狀態是否合法，合法就在出錯處處理，不合法就去找誰產生它（guard、retry、吞錯、clamp 都是藏 bug 的方式）；同一模式全找出來；挖很久才找到的事實，要提一個「下次一眼看得到」的常駐訊號。bug-fix playbook 要求自己重現、二分排除假設、修完在同一個介面驗、commit 順序讓失敗的重現先進歷史。
- **verification skills**：`create-verification-skill` 為專案產生一個 `verify-<app>` skill 與 feature map（每個功能一個檔：怎麼到達、怎麼驅動、什麼終態證明有效），種子資料不足時要報失敗、不能把旅程改弱；`maintain-verification-skill` 定期（可排程）逐功能讀原始碼、實際驅動，最多開一個修正 PR。`principle-prove-it-works` 要求在真實產物上驗證。
- **context window**：`principle-guard-the-context-window`（大量輸出交給子代理、主 thread 只放摘要、每階段限制檔數與回合）；poteto-mode 的子代理預設用新的、用檔案路徑而不是內嵌內容；session-pickup 把長 transcript 交給子代理解析，主 thread 只留時間線；pause-safely 寫 `wip:` commit 與離線續接筆記。
- **把經驗變成規則**：
  - `correct`：假設每個貢獻者都是「只看得到自己開的檔、照抄最近的例子、走最短能編譯的路」的 agent。同一類錯誤出現兩次就算一類，依序用架構消除、型別、**錯誤訊息寫出正確做法的** lint、行為測試，最後才寫文件。每個新檢查要在真實舊錯誤上證明會失敗；例外寫在該行，附理由、到期日與人類核准。agent 指令檔維護「規則—由什麼強制」表，被糾正而規則已在但沒強制者，就是重犯。
  - `principle-encode-lessons-in-structure`：第二次寫同一條指示時，改成 lint、metadata、執行期檢查或 script；需要判斷的才寫文字，並附失敗例。
  - `reflect`：從對話挖「半年後仍成立、會改變下一個 agent 行為、對應到這次用過的 skill」的教訓；先讀那個 skill，已經寫清楚的丟掉；SHA、版本、數字這類會漂移的丟掉；能由 lint 強制的放 backlog，不寫成文字；改之前要核准。
  - `automate-me`：從使用者的對話紀錄挖偏好，做成個人的 `<handle>-mode` skill（明文只讀目前 workspace 的紀錄）。
- **模型與 reasoning 等級**：`pstack-models.mdc` 依角色給模型；poteto-mode 規定程式、文字、判斷用 Opus 5.5 xhigh-fast，機械小改用 high-fast，panel 三家各一；Fable 5.2 只有使用者點名、或 Opus xhigh 同一份 brief 失敗兩次才用；最難的工作升一級（上限 xhigh），判斷工作降一級，例行工作降兩級以上；驗證固定用便宜的 swarm 模型。

**和使用者規則的衝突。** poteto-mode 的 Autonomy 寫「Just do it. Use any MCP tool」，團隊聊天、更新 ticket、開 eval 都不先問；shipping、autopilot、maintain-verification-skill 會自己開 PR 或合併。只有 force-push、deploy、刪資料、對客戶發訊息才停。使用者的規則是不 push、不開 PR，所以只能借設計，不能整包裝。

### Ponytail 兩版

- **DietrichGebert/ponytail**：HEAD 仍是 96608e0（10-29），與框架 11-09 讀的相同，196,019 stars。沒有新資訊。
- **pdscomp/Ponytail** [CLONED]：給 Hermes Agent 的改寫版，分叉自上游 b6c0448（07-10），作者說約 9% 字句與上游相同。只有 4 個檔。值得看的是新增的「工具紀律」：同一個失敗呼叫不重試第二次、已讀過的圖片不再分析、迴圈警告時換工具而不是第三次重試；以及 `references/stateful-preflight-audits.md` 對 live backend 切換、持久化工作、telemetry 政策的唯讀稽核清單。LICENSE 是上游 MIT 全文後加一行修改版權，GitHub 因此顯示 NOASSERTION。

### Spec Kit、mattpocock/skills、superpowers、OpenSpec、BMAD 的新資訊

- **Spec Kit** [CLONED] 1.4.3：9 個指令模板合計約 130 KB（specify 18.5 KB、checklist 21.8 KB），每跑一個指令就載入很長的文字。新的 `converge` 指令從程式現況反推「還沒做完的 task」補進 tasks.md。新的 events 子系統（約 2,600 行）會在安裝 integration 時把事件寫進各宿主的 hook 設定。社群 extension 204 個，README 明寫「維護者只檢查格式，不審查、不背書程式碼」。
- **mattpocock/skills** [CLONED] 1.3.2：39 個 skill，27 個只能由使用者叫用。新看到 `in-progress/claude-handoff`（寫交接摘要到 OS 暫存目錄，用 `claude --bg --name ... -- "$(cat 檔)"` 開背景 agent 接手，用檔案傳遞避免 shell 展開）、`misc/git-guardrails-claude-code`（PreToolUse hook 擋 git push、reset --hard 等，方向和框架 guard hook 相同）、`in-progress/software-factory`。它的 `teach` 是有狀態的教學工作區（MISSION.md、learning-records），和 pstack 的單次 teach 是兩種做法。
- **superpowers** v7.0.0（10-10）：brainstorming 重寫，先問一個具體情境的問題，依規模決定當場做、在對話談、或寫設計文件；新增「以實作者身分讀設計」的子代理取代 spec reviewer。也修了一個安全問題：Windows 的 run-hook.cmd 會執行目前目錄裡的 `bash.cmd`／`where.bat`，repo 可以在 session 開始時植入程式（#2393）。
- **OpenSpec** v2.0.0（11-11）：skill 統一放 `.agents/skills/`，不讀這個資料夾的工具用連結；移除 `/opsx:*`；`openspec update` 清舊檔但保留並列出使用者改過的。
- **BMAD**：v6.12.4（10-14）。LICENSE 是 MIT 加商標聲明，BMad／BMAD-METHOD 等名稱是商標。

### 多模型協作、交接與審查

| 項目 | 做法 | 資料流 | 證據 |
|---|---|---|---|
| openai/codex-plugin-cc | Claude Code 裡的 `/codex:review`（唯讀）、`/codex:adversarial-review`（可帶焦點）、`/codex:rescue`（委派）、`/codex:transfer`（整段 Claude 對話交給 Codex 匯入）；可選 Stop hook 審查閘門 | diff 或整段對話送 OpenAI | [READ] README db52e28 |
| trailofbits second-opinion | 同一份 diff 給 Codex／Antigravity；檔案用 mktemp 放 checkout 外；不截斷；失敗不等於通過；兩家同意不等於證明 | diff 送 OpenAI／Google | [READ] SKILL.md |
| pstack arena／interrogate | 多家模型平行做或平行攻擊，跨廠商 judge | 依設定的模型 | [CLONED] |
| claude-code-router | 本機 gateway，讓各 agent 連自選供應商、fallback、記錄 token 與費用 | 經本機 gateway 送各家 | [READ] README |
| PAL MCP（原 Zen MCP）、Mesh、2ndOpinion、Gauntlet、ask-llm、multicli | MCP 讓 Claude Code 找其他模型給第二意見或共識 | 各家 API | [SEARCH-ONLY]；PAL 2025-12 後停更，沒收進資料庫 |

觀察：「交接」有三種不同機制：(1) 寫摘要再交給新 agent（mattpocock handoff、pstack pause-safely）；(2) 直接匯入原始對話（codex-plugin-cc transfer，資料最完整但整段上傳）；(3) hook 自動寫事實檢查點（框架的續接 hook、claude-mem）。框架是 (3)＋人工交接檔。

### 降低程式與文件產生量、避免錯誤修改

除了 Ponytail 的階梯，這輪看到的具體機制：pstack `correct`（重複錯誤做成不可能）、DejaVu 的 `dejavu check`（違反決策或重寫已存在函式就警告，但只支援 JS/TS/Python）、Spec Kit `converge`、pstack `blast-radius`（在 diff 之外找可能被弄壞的地方，並跑真實程式證明安全理由）、pstack `no-comments` 與 `unslop`（刪多餘註解與 AI 腔）。

### Self-improvement、prompt optimization、context engineering、A2A

- **ACE**（Agentic Context Engineering）：Generator／Reflector／Curator 三角色，教訓以局部 delta 寫入 playbook，每條帶有用／有害計數，避免整份重寫造成「context collapse」。作者自報 AppWorld +10.6%。
- **DSPy＋GEPA**：prompt 當成可最佳化的參數；GEPA 讀失敗軌跡反思出修改，作者自報 100～500 次評測。前提是要有可自動打分的評測集。
- **Letta Code**：agent 可改寫自己的記憶區塊與 system prompt，背景「做夢」整理記憶，記憶用 git 追蹤（MemFS）。
- **Anthropic〈Effective context engineering〉**（2025-09-29）：compaction、結構化筆記、子代理回 1,000～2,000 token 摘要、只帶識別碼再即時讀取；警告過度壓縮會丟細節，先保 recall。沒有量測數字。
- **A2A**：JSON-RPC over HTTP、Agent Card、串流與推播；用於服務間 agent，本機 CLI 宿主之間的交接目前不是靠它。

這四種 self-improvement 的差別：pstack reflect 由人核准後改既有 skill；ACE 自動加 delta 並計分；GEPA 對評測集最佳化；Letta 讓 agent 自己改自己的 context。框架目前最接近 pstack reflect。

## B. 記憶

### 查了什麼、怎麼查、沒查到什麼

- **Clone：** thedotmack/claude-mem（f1bb834）、HMAKT99/Dejavu（4549458）、bmaltais/memory-os（0b4e819）。
- **讀文件：** Mem0 README 與 telemetry.py、Letta 轉址 README 與 letta-code README、ClaudioDrews/memory-os README 與 setup.sh、OpenHuman README、mem-agent README、Graphiti README、Basic Memory README、LongMemEval README。
- **搜尋：** dejavu-memory、mem-agent 模型卡、LoCoMo 批評；claude-mem 的 GitHub issues（gh search）。
- **沒查到：** jsingletonai/dejavu（文章裡的 dejavu）的 repo 與 PyPI JSON 都回 404，dev.to 文章也 404，只剩搜尋摘要；mem-agent 的 HF 模型卡沒有直接讀；Mem0、Letta、Graphiti 沒讀原始碼，衝突處理與 token 成本只能依 README。

### 同名專案（重要）

| 名稱 | 使用者給的種子 | 文章裡講的 | 是不是同一個 |
|---|---|---|---|
| Dejavu | [HMAKT99/Dejavu](https://github.com/HMAKT99/Dejavu)：npm `dejavu-dev`，專案**決策**記憶＋違規與重複檢查 | jsingletonai/dejavu：pip `dejavu-memory`，**個人偏好**記憶，LLM 走 Venice | **不同**。後者 repo 已 404 |
| memory-os | [bmaltais/memory-os](https://github.com/bmaltais/memory-os)：TypeScript，SQLite＋hash embedding，給 Claude Code／Grok／Pi | [ClaudioDrews/memory-os](https://github.com/ClaudioDrews/memory-os)：Python，七層，Qdrant＋Redis，Hermes 專用 | **不同**。兩篇 vocus 文章講的都是 ClaudioDrews 版 |
| OpenHuman | — | 文章說是「桌面記憶全家桶」（Memory Tree、118 個 OAuth 服務） | [tinyhumansai/openhuman](https://github.com/tinyhumansai/openhuman) 現在 README 改稱 Rust agent harness，記憶是其中一項 |

### 各項發現（重點）

- **claude-mem** [CLONED]：11 個 hook 把每次工具呼叫送本機 worker，由 observer 模型寫成 observation；SQLite＋FTS5＋Chroma；三層檢索 index→timeline→detail；PreToolUse 在讀檔前注入與該檔有關的過去 observation（`file-context.ts`，同 session 去重）。新看到 `reinforcement/` 模組：每筆記最近 10 次被再確認的日期，用 ACT-R 冪律衰減排序，不需 embedding。observer 可指到 OpenAI 相容的本機端點（Ollama、LM Studio）才算全本機；預設是 Anthropic 方案或付費雲端 observer。telemetry 預設開。使用者回報：到處建 CLAUDE.md（#609、#641）、token 太多（#618）、發版打包問題（#2407、#3857）；作者開了二十多個 plan issue 處理 worker 存活、子程序、schema 演進。README 推廣第三方加密代幣 CMEM。
- **DejaVu（HMAKT99）** [CLONED]：決策是 Markdown，帶 `applies_to`（glob）、`detect`（regex）、`supersedes`；挖出的候選一律人工審核；repo 層 commit 進 git，個人層在 `~/.dejavu/` 且有測試保證不 commit。沒有 LLM、沒有 embedding、沒有網路。函式抽取只支援 JS/TS 與 Python。
- **memory-os（bmaltais）** [CLONED]：README 說「用完全不同的說法提問也找得到」，但 `src/embed/hash.ts` 是把字詞雜湊進 384 維的 feature hashing，只比對字詞，不是語意模型。`--synthesize` 只是格式化。repo 自己 commit 的 log 顯示同一句使用者訊息被記了十多次、助手回覆是空的。沒有 LICENSE。
- **Memory OS（ClaudioDrews）** [READ]：七層加「Ground Truth」層（告訴 agent 注入的記憶是權威，否則 agent 會再查一次）。README 說記憶基礎設施全在本機，但 setup.sh 要 OpenRouter 相容的 embedding key，預設 `qwen/qwen3-embedding-8b`；安裝是 `curl | bash`，pip 失敗會改用 `--break-system-packages`，Qdrant key 留空時把認證那行註解掉。
- **Mem0** [READ]：新演算法改成 ADD-only（不更新不刪除），讀取時用時間感知挑目前狀態；語意、BM25、實體三路融合。作者自報 LoCoMo 92.5、LongMemEval 94.4，但明說是雲端版含專有最佳化。預設 LLM 與 embedding 是 OpenAI；telemetry 預設開（PostHog）；README 鼓勵 agent 自己 `mem0 init --agent` 註冊雲端帳號。
- **Letta** [READ]：letta-ai/letta 只剩轉址，開發在 letta-code；Letta Cloud 是預設後端；MemFS 用 git 追蹤記憶。
- **Graphiti（Zep）** [READ]：事實帶有效期間，被推翻時標成失效、保留歷史與出處（episode）。
- **mem-agent** [READ／SEARCH-ONLY]：RL 訓練的 4B 記憶模型，Markdown＋entities 資料夾；repo 沒授權，HF 模型卡 API 的 license 欄空白。
- **Basic Memory** [READ]：Markdown＋wikilink 的本機知識庫＋MCP，AGPL-3.0。
- **記憶 benchmark**：LongMemEval 500 題，有「知識更新」與「拒答」兩類；LoCoMo 被 Penfield Labs 稽核出 6.4% 答案錯、judge 接受最多 63% 故意錯答（稽核者也做記憶產品），Mem0 與 Zep 互指對方實作錯。各家自報分數不能互比。

## I. 評測與模型路由

### 查了什麼、怎麼查、沒查到什麼

- **Clone：** promptfoo（65fd489）。
- **讀文件：** DeepEval、Ragas、LiteLLM、RouteLLM、DSPy、GEPA、SWE-bench、Terminal-Bench、LongMemEval 的 README；DeepEval、Ragas 的 telemetry 原始檔；LiteLLM issue #24512、SafeDep 分析；Promptfoo 收購公告。
- **沒查到：** DeepEval、Ragas 沒讀原始碼結構；Terminal-Bench 2 的資源需求沒查；SWE-bench 系列只讀主 repo，SWE-bench Pro 等其他團隊的版本沒查。

### LiteLLM 的供應鏈事件（使用者要求查）

**2026 年發生兩次 PyPI 發版被攻破。**

1. **2026-03-24：1.82.7、1.82.8。** 1.82.8 帶 `litellm_init.pth`（34,628 bytes），Python 每次啟動都會執行，不必 import litellm；1.82.7 的惡意碼在 `proxy/proxy_server.py`。偷環境變數、SSH 金鑰、Git、AWS／GCP／Azure、K8s、Docker、資料庫憑證、shell 歷史、加密錢包等，用 AES＋RSA 加密後 POST 到 `models.litellm.cloud`。issue #24512；HN 首報 938 分。維護者之後宣布改用 PyPI trusted publisher、release cosign 等。[READ]
2. **2026-10-21：1.107.0。** PyPI 上 7 個 wheel 全部帶惡意碼，Docker 映像 `v1.107.0`、`latest`、`main-latest`、`main-stable` 在 11:46～14:20 UTC 之間也受影響。`cook.pth` 每次 Python 啟動執行竊密程式（SSH、雲端、CI/CD、AI 工具 token、瀏覽器密碼、proxy 資料庫裡的 LLM key），送到 `www.litellm[.]dev/healthcheck`；`sitecustomize.py` 起一個背景 daemon，每小時從攻擊者的 GitHub 取伺服器網域，再下載並 `exec()`。入侵途徑：從外露的內部部署日誌拿到三位開發者的 GitHub CLI 憑證，用組織擁有者 token 繞過分支保護，把發布 workflow 指到仿冒 repo，再用第二位開發者的憑證通過核准閘門，官方流程因此建置、簽署並發布了惡意產物。上傳後約 1 小時 40 分 PyPI 下架。[READ] SafeDep 分析

對框架的意義：`.pth` 與 `sitecustomize` 讓套件在**任何** Python 程序啟動時執行，所以「只是裝起來不用」也不安全。主 session 在 Docker 試跑任何 Python 套件時要固定版本、核對雜湊、容器裡不放憑證。

### Promptfoo 被 OpenAI 收購

2026-03-09 宣布，公告寫「Promptfoo will remain open source」，會繼續支援多家模型；沒談授權。clone 的 0.126.0 仍是 MIT。原始碼看到：telemetry 預設開（PostHog）、紅隊攻擊生成預設走遠端服務（各有環境變數關閉）、`src/providers/claude-agent-sdk.ts`、`src/assertions/skill.ts`（從回應 metadata 的 skillCalls 數 skill 被叫用次數，可設 min、max、name、pattern）、trajectory 與 trace span 斷言。

### 依難度與預算選模型與 reasoning effort

- **pstack**：依角色給模型與等級，難的升一級、判斷降一級、例行降兩級，最高 xhigh；驗證用便宜模型；Fable 只在點名或 Opus 失敗兩次時用。
- **Factory Router**（作者自報）：在 harness 裡依 prompt、程式範圍、工具判斷難度，卡住時升級；文件說強烈考慮 prompt cache 的維持。甜蜜點成本約 75～80%、通過率 96～99%；激進設定成本 30～56% 但通過率掉到 49～81%。
- **RouteLLM**：用偏好資料訓練強弱二選一的路由器，門檻依「希望幾 % 走強模型」校準；2024-08 後停更，例子是聊天題。
- **框架現況**：人工決定；換模型會讓快取失效，所以在里程碑再換；某一步需要別的模型就用指定模型的子代理。這和 Factory「路由要顧 prompt cache」的觀察一致。

## H. 可觀測性

- **Claude Code OTel** [READ 官方文件]：預設關閉，`CLAUDE_CODE_ENABLE_TELEMETRY=1` 開啟。metrics 有 `claude_code.cost.usage`、`claude_code.token.usage`（input／output／cacheRead／cacheCreation）等，屬性含 `model`、`effort`、`agent.name`、`skill.name`、`plugin.name`、`mcp_server.name`；events 有 `api_request`（cost_usd、各類 token、duration_ms）、`tool_result` 等；traces 是 beta。內容紀錄（prompt、工具參數、工具輸出、回應、raw API body）預設都關。專案層 settings 裡的 OTel 變數會被忽略，repo 不能偷開遙測。這是框架量 skill 成本最直接、也最符合隱私決定的來源（只開 metrics＋api_request event、送到本機 console 或 Prometheus）。
- **OTel GenAI semantic conventions** [READ]：已搬到 `open-telemetry/semantic-conventions-genai`，spans 標 Status: Development；messages 內容是 Opt-In。Claude Code 用的是自己的 `claude_code.*` 名稱。
- **Langfuse** [READ]：OTel 相容的 tracing／評測平台，2026-01 起屬於 ClickHouse；self-host 要 Postgres、ClickHouse、Redis、S3 相容儲存；MIT 但 `ee/` 目錄另有授權。
- **Arize Phoenix** [READ]：`pip install arize-phoenix` 本機即可跑，有 /mcp 端點；授權是 Elastic License 2.0（不是 OSI 開源，不可做成託管服務）。
- **ccusage** [READ]：讀二十多種 agent CLI 的本機用量檔，產生日／週／月／session 與 5 小時視窗報表；價格表預設線上取得，`--offline` 用快取；費用是估算。repo 已搬到 ccusage/ccusage。

## 四篇文章

- **ginseng ep091**（2026-11-06）：資安三段與三個 A，三起台灣與國際事件；示範用 pstack teach 以自己的專案解釋名詞。幣安事件的路徑（假面試誘騙下載惡意 repo、透過內部 AI 工具擴散）支持「clone 的程式只讀不跑」。
- **vocus〈本地記憶層的四個開源答案〉**：dejavu（jsingletonai）、mem-agent、OpenHuman、memory-os（ClaudioDrews）從輕到重。四個專案都沒附網址，其中兩個和使用者種子同名不同專案。作者觀察「Markdown／Obsidian 是共識、四個都本機優先」，但本機儲存不等於不送雲端。
- **vocus〈memory-os 的分層設計〉**：七層與 Ground Truth；作者沒自己部署。
- **vocus〈壓縮、路由、替換〉**：headroom、OpenSquilla、Factory Router、deepclaude、ds4；只有 Factory Router 查得到一手來源。

## 比較 1：記憶系統

隱私欄依使用者的定義：存下的內容之後再送給模型服務，也算上雲端。**凡是把記憶注入 context 的系統，存下的內容都會再送給模型一次**；差別在「寫入時」有沒有額外送一次（壓縮、embedding），以及送到哪家。

| | 框架現況 | claude-mem | Mem0 | Letta Code | DejaVu（HMAKT99） | memory-os（bmaltais） | Memory OS（ClaudioDrews） |
|---|---|---|---|---|---|---|---|
| 儲存 | 宿主自動記憶（Claude Code 的 MEMORY.md 等）、`profile` JSON、交接檔、`.agf/checkpoints/*.md` | SQLite＋FTS5＋Chroma（`~/.claude-mem`） | 向量庫＋實體連結（library／self-host／雲端） | Letta Cloud（預設）或本機；MemFS 用 git | `DECISIONS.md`（git）＋`~/.dejavu/` | Markdown log＋SQLite（專案內） | Markdown＋SQLite×2＋Qdrant＋Redis＋wiki |
| 寫入方式 | 人或模型寫交接檔；hook 在 compact、額度錯誤、session 結束、換模型前寫事實檢查點 | 每次工具呼叫→observer 模型寫 observation 與摘要 | 每段對話→LLM 抽取（新版只新增） | agent 改自己的記憶區塊；背景「做夢」整理 | 規則挖對話＋`#decision:` 註解＋`remember`，**人工審核**才生效 | Stop hook 每輪自動寫 | 每輪後 LLM 抽取；wiki 持續整理 |
| retrieval | 新 session 由 hook 提示讀哪些檔；模型自己讀 | 三層 index→timeline→detail（MCP）＋ACT-R 強度排序 | 語意＋BM25＋實體融合，時間感知 | 記憶區塊常駐＋recall 子代理 | MCP 查詢；投影進 CLAUDE.md 等 | FTS5＋hash 向量（只比字詞） | 四來源、四級 fallback、門檻過濾 |
| 過期／衝突／重複 | 交接檔由人改；檢查點保留最新 N 份 | 強度隨時間衰減；dedup 細節沒讀 | ADD-only，讀時依時間挑 | agent 自己改 | `supersedes` 追加、不改舊條 | 沒有（自己的 log 有重複） | cosine>0.92 合併；每週 decay 降權不刪 |
| 跨 agent | 交接檔是一般 Markdown，任何宿主可讀 | 多宿主 adapter；部分只能搜尋 | SDK／MCP | 同一 agent 可在多台機器、多頻道 | 檔案＋MCP，任何讀 AGENTS.md 的工具 | Claude Code、Grok、Pi | 只有 Hermes |
| context 注入 | session-start 只印「先讀哪些檔」，不注入內容 | session 開頭注入索引；PreToolUse 也會注入 | 應用自己決定 | 記憶區塊常駐 system prompt | managed block 寫進 CLAUDE.md 等（常駐） | SessionStart 注入最多 32 KB | 每輪 pre_llm_call 注入；SOUL／rulebook 常駐 |
| token 成本 | 低：提示幾行，讀檔才付 | 每次工具呼叫多一次 observer 呼叫；注入的索引大小可設預算 | 作者自報檢索約 7K token／次 | 常駐記憶區塊＋做夢的背景呼叫 | 寫入零模型呼叫；常駐決策區塊隨條數增加 | 每 session 最多約 32 KB 常駐 | 第 1、7 層每輪常駐＋寫入時 LLM 與 embedding |
| 寫入時是否另外送模型 | 否（檢查點是 script 收的事實；`save_prompts` 預設關、使用者決定不開） | **是**（預設 Anthropic 方案或付費雲端 observer；可改本機端點） | **是**（預設 OpenAI） | **是** | 否 | 否 | **是**（預設 OpenRouter embedding＋LLM 抽取） |
| telemetry | 無 | 預設開 | 預設開（PostHog） | 沒查 | README 說沒有 | 沒有 | 沒查 |
| 本機部署 | 是（標準庫 Python） | 是（Node／Bun＋Chroma；要本機模型才全本機） | 是（self-host Docker；預設仍用 OpenAI） | 是（`letta server`） | 是（npx 或單檔） | 是（Node 22） | 是（Docker；預設 embedding 在雲端） |

框架的檢查點被下一個 session 讀到時，裡面的 git 狀態、錯誤、最後一則 AI 訊息與壓縮摘要也會再送給模型；使用者說的話因為 `save_prompts` 關閉，不在其中。它比其他方案少的是「寫入時另外送一次」與「每輪自動注入」。

**真正不同的技術方向**（名稱不同但機制相同的合在一起）：

1. **自動擷取＋模型壓縮**（claude-mem、Mem0、Memory OS 的 fabric）：完整但每次寫入都多一次模型呼叫，也多一次資料外送。
2. **自動擷取、不經模型**（memory-os bmaltais、框架檢查點）：便宜、不外送，但只有字面或事實，沒有整理。
3. **人工審核的決策帳本**（DejaVu、框架交接檔）：量少、品質高，可以 git 管、可以檢查程式是否違反。DejaVu 多了「決策帶 glob 與 regex，可被檢查」這一步，是框架現在沒有的。
4. **agent 自己改自己的 context**（Letta、ACE）：最有彈性，也最難審核。
5. **衝突處理的三種做法**：只新增、讀時依時間挑（Mem0）；相似度合併＋衰減（Memory OS、claude-mem 的強度）；有效期間失效並保留歷史（Graphiti）。框架目前靠人改交接檔。

## 比較 2：AI workflow

| | 框架現況 | pstack（上游） | Ponytail | Spec Kit | mattpocock/skills | superpowers |
|---|---|---|---|---|---|---|
| 任務規劃 | `align-with-me`（只能使用者叫用）、workflow 指引 | poteto-mode 依任務選 playbook；multi-phase-plan | 不規劃，只限制解法大小 | constitution→specify→clarify→plan→tasks | to-spec、to-tickets、grill-me | brainstorming→writing-plans |
| 設計決策 | align-with-me 每題附建議答案 | architect 畫兩種形狀；arena 多模型；why 查紀錄 | 階梯：需要嗎、有沒有現成的 | plan 的 Constitution Check | grilling 的決策樹 | 設計文件核准才動工；實作者視角審 |
| context 管理 | 按需讀指引、有界輸出、續接 hook | 子代理預設新開、檔案路徑不內嵌、guard-the-context-window | 很小的常駐文字 | 每個指令載入 10～20 KB 模板 | 多數 skill 只能使用者叫，不占清單 | SessionStart 注入 bootstrap（強勢） |
| code review | `review-change` | interrogate（多模型攻擊，只留跑過證明的發現）、no-comments、blast-radius | `/ponytail-review` | analyze、converge | code-review | requesting／receiving-code-review |
| 驗證 | 依風險驗證；periodic profile 重跑一次性檢查 | create／maintain-verification-skill、prove-it-works、benchmark-checklist | 有邏輯就加小測試 | bug extension 的 verified／partial／failed | tdd、diagnosing-bugs 的回饋迴圈 | verification-before-completion |
| 交接 | 交接檔＋task checkpoint＋續接 hook | session-pickup、pause-safely、recall、show-me-your-work（TSV 決策紀錄） | 無 | 檔案就是交接 | handoff、claude-handoff（背景 agent） | 計畫檔＋sdd ledger |
| skill 組合 | 7 個 skill，少而專 | 58 個，poteto-mode 串起來 | 1 個 | 指令序列＋extensions | 39 個，流程與能力分開 | 十多個，強制順序 |
| token 成本 | S8 實驗框架組多 39%（舊版規則） | 高：多數 playbook 預設開背景子代理，arena 3＋1 個模型 | 作者自報輸出少 45%；常駐約 800～900 token | 高：長模板 | 低：只有叫用時才載入 | 常駐 bootstrap，作者沒公布量測 |
| 自主程度 | 不 push、不開 PR（guard hook 擋） | 外部動作不先問；會自己開 PR、合併 | — | 人工逐步 | 人工叫用 | 人工核准設計 |

**真正不同的技術方向：**

1. **限制產出量的規則**（Ponytail、pstack laziness-protocol、Karpathy 四原則）：本質都是 YAGNI＋先重用；Scott Logic 已證明一句短 prompt 在小 benchmark 上就能接近。
2. **規格先行的流程**（Spec Kit、OpenSpec、BMAD）：用檔案當狀態，從 spec 推到 task；差別在重量與 delta 管理。
3. **多模型對抗與擇優**（pstack arena／interrogate、codex-plugin-cc、second-opinion）：花多倍 token 換獨立視角；關鍵是跨廠商、同一份輸入、只留有證據的發現。
4. **把錯誤變成結構**（pstack correct、DejaVu、mattpocock git-guardrails、框架 guard hook）：文字擋不住的事交給型別、lint、hook。這是這輪最值得框架再加強的方向。
5. **觸發方式**：只能使用者叫（pstack 上游、mattpocock 流程 skill、框架 align-with-me）、模型自動叫（pstack-claude 移植、superpowers）、session 開始強制注入（superpowers、pstack-claude）。同一份 pstack 內容，上游與 michael-denyer 移植在這點完全相反。

## 資安發現

- **LiteLLM 兩次 PyPI 供應鏈事件**（3 月、10 月），詳見 I 節。
- **superpowers #2393**：Windows 的 hook 會執行 repo 裡植入的 `bash.cmd`／`where.bat`（v7.0.0 已修）。
- **claude-mem 的 MCP 設定**：沒有 `CLAUDE_PLUGIN_ROOT` 時會依序從目前目錄的 `plugin/`、目前目錄本身找 `scripts/mcp-server.cjs` 並 `require`；在不信任的 repo 啟動時理論上可能載入該 repo 的同名檔。**推論，未實測**；和 superpowers #2393 是同一類問題。
- **自主外部動作**：pstack poteto-mode「Use any MCP tool」、外部動作不先問，會自己開 PR 與合併；Letta 鼓勵 agent 自己改權限設定；Mem0 鼓勵 agent 自己註冊雲端帳號。
- **強制注入**：michael-denyer 移植的 SessionStart 注入 `<EXTREMELY_IMPORTANT>` 路由文字（compact 後也注入）；PickleBoxer 移植刻意改走 prompt.submit，註解說是為了避開組織安全 plugin 會略過的 hook 路徑。兩者都不是惡意指令，但會在使用者不知情時加常駐文字。
- **安裝方式**：ClaudioDrews memory-os 與 OpenHuman 都用 `curl | bash`；memory-os 的 setup.sh 會改用 `pip --break-system-packages`、在 key 留空時關掉 Qdrant 認證。
- **資料外送預設**：claude-mem、Mem0、DeepEval、Ragas、Promptfoo 的 telemetry 預設開；Promptfoo 紅隊生成預設走遠端；codex-plugin-cc 的 `/codex:transfer` 會把整段 Claude 對話交給 OpenAI。
- **不明檔案**：HMAKT99/Dejavu 根目錄的 `scbee-verify.txt` 只有一串驗證碼，用途沒寫。
- **SKILL.md 掃描**：讀過的 SKILL.md 裡沒有看到「忽略之前的指示」或下載後執行的指令。MIRROR.md 的 `git push` 是給維護者的同步步驟。

## 待確認

| 名稱 | 候選 | 理由 |
|---|---|---|
| dejavu（文章版） | jsingletonai/dejavu、pip `dejavu-memory` | repo、PyPI JSON、dev.to 文章 2026-11-21 都 404，只剩搜尋摘要；可能已刪除或改名 |
| headroom（壓縮，60～95%） | 沒找到唯一來源 | 文章沒附網址；名稱太普通 |
| OpenSquilla（規則式路由） | 沒找 | 文章沒附網址 |
| deepclaude、ds4 | 沒找 | 文章沒附網址；ds4 可能指本機 DeepSeek 部署工具 |
| TokenJuice（OpenHuman 的壓縮引擎） | tinyhumansai/openhuman 內部元件 | 目前 README 改稱 RLM 壓縮，沒看到 TokenJuice 這個名字 |
| Icarus plugin | esaradev/icarus-plugin | Memory OS 依賴的 fork 來源，授權沒查 |
| mem-agent 模型授權 | driaforall/mem-agent（HF） | 文章說 HF 標 MIT，HF API 的 license 欄空白、GitHub repo 沒授權 |
| Mesh、2ndOpinion、Gauntlet、ask-llm、multicli、PAL MCP | 見 A 節表格 | 只有搜尋摘要；PAL 2025-12 後停更 |

## 沒做完的部分

- Mem0、Letta、Graphiti、DeepEval、Ragas、LiteLLM 沒讀原始碼，記憶衝突處理與 token 成本只依 README。
- Claude Code 監控文件只讀到前 100,000 字元，後 82,140 字元沒讀。
- pstack 的使用者回饋（HN、Reddit）沒找到；claude-mem 只看了 issue 標題與留言數，沒讀內容。
- 跨模型審查工具只讀了兩個（codex-plugin-cc、second-opinion），其餘只有搜尋摘要。
- Terminal-Bench 2／Harbor 的資源需求、SWE-bench 其他團隊的變體沒查。
- 沒有任何實際執行或量測；所有節省 token、品質的數字都是作者自報。

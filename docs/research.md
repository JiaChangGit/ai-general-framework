# 設計依據與採用範圍

這份紀錄說明框架為何採用某些方法、哪些做法沒有照搬，以及證據能支持到哪裡。它是設計依據，不代表所有整合、模型與教學方法都已在本框架驗證。外部工具會變動，實際操作仍需核對使用版本的文件。

記憶分層、Ponytail、白話解釋、few-shot、歌詞標記、運鏡與 Scrapling 等新一輪來源，採納與未採理由見[記憶與提示取捨](memory-prompt-study.md)。

使用者提供的 Claude Code 套件與現有功能比較，見[參考套件取捨](skillkit-study.md)；只補術語、來源副本及偶發失敗的窄缺口，未執行或移植附件腳本。

## 可讀性與中文表達（2026-11-09）

[Clark 等的預印本 v1](https://arxiv.org/html/2610.29162v1) 比較英文生成文字與人類語料中的語言特徵，發現模型、文類之間有差異；作者以單一模型的長度懲罰實驗探索可能原因，並非已證實所有模型的成因。[Cekini 等的預印本 v1](https://arxiv.org/html/2610.23715v1) 以英文眼動資料訓練模型，預測 496 組英文文章及其 AI 改寫的閱讀時間：改寫較短、預測全文時間略低，預測每詞時間較高。後者是模型預測，不是對這 496 組文章直接量測讀者理解或閱讀時間。

兩篇都不能直接驗證繁體中文的主題銜接、歐化句式或特定詞語是否自然。依使用者提出的觀察，在 writing 指引增加主題、動作、指涉、詞語搭配與資訊是否具體的檢查；這是本框架對中文的實用設計選擇，並非論文證明其成效。保留修辭與精確術語，不用固定禁詞或句長判定 AI 味；真實讀者能否理解仍需回饋。

後續補上[研究範圍與改寫驗收](writing-research.md)，將語意保留條件和具體反例放入獨立案例；這份說明供維護者查核，不增加每次部署的必讀內容。

## 使用者連結的去重與融合（2026-11-09）

本輪將前後提供的技能庫、寫作、程式關係、資料與影音來源，連同 Tenten 七篇整理成[固定版本的取捨紀錄](link-study.md)。多數原則已存在，不增加技能數量；只補本人樣本保真、機械防錯、部署參考完整性、索引／內容範圍核對、聚焦文獻比較及按需的跨格式成果指引。上游共用或衍生內容不當作獨立品質證據。

沒有安裝或執行外部 runtime、MCP、hooks、模型服務，也未複製上游 skills／素材。工具宣傳、授權標籤與回饋各有範圍，已明示未採納部分；真實成本、品質、整合與安全仍需在實際任務驗證。

## 簡報工作方式（2026-11-09）

將使用者提供的「帳號內作品」與「結構化內容交給既定版型」案例融合成一份按需簡報參考，沿用五個 skills、四份部署指引及既有 templates 複製方式。這兩條路由當次可用能力選擇，不新增通用 YAML schema、PPTX 引擎、版型庫或媒體 provider。這是範圍取捨，不是已驗證所有簡報功能。

| 一手來源 | 採納與限制 |
|---|---|
| [Pandoc reference-doc](https://pandoc.org/MANUAL.html#option--reference-doc)、[speaker notes](https://pandoc.org/MANUAL.html#speaker-notes) | 相容 layout 與講稿可由既有工具處理；缺 layout 可能警告並用預設值，不承諾任意範本都能完整套母片。 |
| [Marp CLI](https://github.com/marp-team/marp-cli#convert-to-powerpoint-presentation-pptx)、[Slidev exporting](https://sli.dev/guide/exporting) | 預設 PPTX 是圖片不等於沒有任何可編輯路線。Marp 的實驗模式需 browser／LibreOffice，保真較低且無講稿；Slidev 現有 `pptx-editable`，但 Mermaid／SVG 仍為圖片，部分頁會 fallback。依實際物件與模式驗證，不從副檔名宣稱全部可改。 |
| [PptxGenJS 型別註解](https://github.com/gitbrent/PptxGenJS/blob/master/types/index.d.ts)、[原始 issue #1449](https://github.com/gitbrent/PptxGenJS/issues/1449) | 自動文字 fit 不能代替實際渲染與可讀性檢查。2026-03-31 的回報描述 3.x 產物在 LibreOffice 正常、PowerPoint 要求 repair；查閱時 open，未自行重現，也不採納作者全部診斷。不將單一版本回報推廣為現版普遍缺陷或安全結論。 |
| [PyYAML 文件](https://pyyaml.org/wiki/PyYAMLDocumentation#loading-yaml)、[Microsoft 隱藏資料檢查](https://support.microsoft.com/en-us/office/collab-files/remove-hidden-data-and-personal-information-by-inspecting-documents-presentations-or-workbooks) | 若日後有 YAML renderer，使用安全資料 loader 並限制 schema、資源與大小；分享前看講稿、隱藏內容、metadata 與嵌入資料。安全 loader、清 metadata 或文件檢查器都不代表完整隔離或無私人資料。 |

上述工具未在本輪安裝或執行；來源與原始使用者回報只支持工作方式與驗證邊界，不構成預設採用、安全背書或省 token 證據。

## 實用工具方向的融合

查閱日期：2026-11-08。依現有能力補強原生工具的選用判斷、相容性、驗證及交付；仍使用五個技能入口與四份部署指引。下列官方文件支持工具能力和使用限制，不等於已完成個人環境的安全、授權、口碑與效果驗收；真正採用前仍按 tools 指引查核，不自動安裝或加 hook。

| 原始來源 | 融合與取捨 |
|---|---|
| [ripgrep](https://github.com/BurntSushi/ripgrep)、[jq manual](https://jqlang.org/manual/) | 先定位再摘錄，結構資料用現有過濾器；缺工具時提供原生替代入口，不重寫搜尋器或 JSON 語言。忽略規則、缺值和輸出截斷各自辨認。 |
| [difftastic](https://github.com/Wilfred/difftastic)、[Ruff linter](https://docs.astral.sh/ruff/linter/) | 依需要輔助差異閱讀、格式及靜態檢查；不把結構相近當語意正確，不以啟用所有規則或全面自動修正取代範圍判斷。 |
| [hyperfine](https://github.com/sharkdp/hyperfine) | 命令 benchmark 可重複、記錄快取條件和結果；不自建效能平台，也不以執行時間當 AI token 用量。僅對可安全重複的命令測量。 |
| [Hypothesis introduction](https://hypothesis.readthedocs.io/en/latest/tutorial/introduction.html)、[replaying failures](https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html)、[LLVM libFuzzer](https://llvm.org/docs/LibFuzzer.html) | 依實際不變條件產生反例，保存可讀失敗輸入成回歸；不是每次修改都加 fuzzing。Hypothesis 資料庫與 reproduction blob 不保證跨變更／版本永遠回放；libFuzzer 官方說明原作者已停止積極開發新功能，僅作可選工具例子，不固定唯一推薦。 |
| [Pact 適用情境](https://docs.pact.io/getting_started/what_is_pact_good_for) | 先使用既有消費端案例驗證界面、舊輸入與升級；只有可協調的消費／提供端持續協作時才評估契約工具，不另建通用 migration runner。 |
| [Playwright best practices](https://playwright.dev/docs/best-practices)、[accessibility testing](https://playwright.dev/docs/accessibility-testing)、[W3C evaluation](https://www.w3.org/WAI/test-evaluate/) | 驗證使用者可觀察的流程與相關頁面狀態；自動掃描、人工與使用者檢查各有範圍，不以一次 axe 通過宣稱完整無障礙或合規。 |
| [Gitleaks](https://github.com/gitleaks/gitleaks)、[原始 issue 2296](https://github.com/gitleaks/gitleaks/issues/2296) | 以既有可信 scanner 為先，不新增通用秘密辨識器。查閱時 README 已宣告 feature complete、僅 security patches；不因此強迫移轉到作者新工具。issue 回報 v8.30.1 將 redact 放設定檔未生效，未在本框架重現；採納的是核對實際遮罩與報告範圍，並非宣稱所有版本都有同一問題。 |
| [OpenAI：skill evals](https://developers.openai.com/blog/eval-skills)、[Anthropic：agent evals](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 入門補真實 host 的發現、載入與成果三層核對；同規則／工具／材料下比較有無技能，先看品質、越界與返工，再看實際 usage。不建立另一套模型呼叫或評測平台。 |

唯一新增的執行能力是在既有 `run` 加可選的原始 stdout／stderr 保存，避免為恢復截斷的診斷重跑已完成命令。預設不留檔，也不新增依賴、服務或工具包裝。開源貢獻則在既有帶讀參考補上從小問題、來源、patch 到 review 修訂的學習方式；真人是否已理解仍待實際觀察。

## v0.2 的減法與支援邊界

本輪依實際使用方向，將自動技能入口由十三個收斂成五個明確目的。一般開發交給宿主，需求對齊、分工、表達、創作及工具選擇改成四份按需指引；新專案只配置明示選取的 skills。共用工具為預設，離線交付才選工具副本。這減少重複配置與選擇面，尚不能據此宣稱降低多少 token 或實際宿主誤觸率。

| 原始來源 | 採納決策 |
|---|---|
| [Anthropic Skill authoring](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)、[Agent Skills 規格](https://agentskills.io/specification) | 只補足任務所需資訊，先以真實請求觀察有無 skill 的差異；格式通過不代表應保留每個入口。只在改選用邊界時檢查路由，其他維護驗證其實際行為。 |
| [Anthropic 工具設計](https://www.anthropic.com/research/writing-tools-for-agents)、[Fowler YAGNI](https://martinfowler.com/bliki/Yagni.html) | 原生工具足夠就直接用。保留有額外價值的預覽、邊界與證據；移除純文字拼接的 git intent 及低頻、易過期的 Python MCP 名單，不預作通用 SCM 抽象。 |
| [GitHub CLI](https://cli.github.com/manual/gh)、[GitLab CLI](https://docs.gitlab.com/cli/) | GitHub／GitLab 是協作平台，優先使用既有 gh／glab、connector 與專案慣例；可執行、已登入、已授權各自辨認。GitLab 自管主機不應被硬編成 gitlab.com。 |
| [Subversion Quick Start](https://subversion.apache.org/quick-start)、[基本流程](https://svnbook.red-bean.com/en/1.7/svn.tour.cycle.html)、[ignore 屬性](https://svnbook.red-bean.com/en/1.7/svn.advanced.props.special.ignore.html) | 工作副本的 status／diff 與寫入 repository 不同；SVN commit 和某些 URL 操作會發布變更，不能套 Git 本地 commit 授權。忽略私人資料用該 VCS 的機制，不把 .gitignore 當通用規則。書籍連結為 1.7 版基本語意，實際選項仍查使用版本。 |
| [Boost.GIL 貢獻文件](https://github.com/boostorg/gil/blob/develop/CONTRIBUTING.md)、[FreeRTOS troubleshooting](https://freertos.gitbook.io/mastering-the-freertos-tm-real-time-kernel/mastering.ch13)、[ST UM2576](https://www.st.com/resource/en/user_manual/dm00613038-stm32cubeide-st-link-gdb-server-stmicroelectronics.pdf) | library、port、板子與工具鏈條件依真實對象查證。建置、實際燒錄、寫入驗證及板端行為分開，不為每個領域新增一套通用開發 skill。 |
| [Wilson 等：研究運算實踐](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005510) | 分析程式保留來源、原始資料、轉換與可重跑結果；個人股市分析不推導為券商連線或送單授權。 |

小說、音樂與投影片式影片本輪只採共用創作指引：尊重既定設定，依目的選形式，分清草稿與實際成品；沒有新增 provider、媒體管線或宣稱作品品質已驗證。這是使用者的範圍取捨，不是上述工程來源證明的創作方法。

## 依能力清單補強的結論

2026-11-08 再次檢查能力清單後，多數需求已有對應指引。本輪只把實際缺口補進既有位置，維持五個 skills、四份部署指引與原有工具核心。

| 查證的一手來源 | 建議與已完成的修改 | 適用限制 |
|---|---|---|
| [Anthropic context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)、[Aider repository map](https://aider.chat/docs/repomap.html) | 在 tools 指引補上依問題搜尋、摘錄、必要時擴讀與處理截斷；重用既有 context scripts | 不移植索引系統，不靠字元數宣稱省 token；必要條件與原始證據仍須保留 |
| [Anthropic multi-agent research](https://www.anthropic.com/research/multi-agent-research-system)、[Building effective agents](https://www.anthropic.com/research/building-effective-agents) | 在 workflow 明示委派產物、相依工作先收斂、介面與失敗語意對齊、整合後驗證完整流程；把重要漏項的提醒接回具體結果 | 研究系統的成果與用量比例不推廣為本框架指標；不固定模型職位，也不要求每個任務跑完整團隊 |
| [Google SRE：Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) | 在 infra 參考區分緩解與根因確認；重大中斷不必等完整 RCA 才恢復 | 操作仍須已有授權；服務恢復不證明根因，小 bug 不套事故流程 |

另複查 [Anthropic 開源 skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)、[humanizer](https://github.com/blader/humanizer/blob/main/SKILL.md)、Google 技術寫作與 Julia Evans 的解說方法。採用按需資源、具體任務驗證、對準讀者及保留原意；不採寬泛的「只要提到就觸發」描述、固定問卷或全域禁詞。現有 skills、教學與寫作指引已涵蓋這些原則，本輪不為重複建議新增檔案。

## MCP 自動選用與 RTK 查證

查證日：2026-11-08。本次將任務訊號、品質／安全查核、原始使用者回饋與用量比較補進既有 tools 指引，並在專案入口提醒主動探索。自動判斷與呼叫由宿主代理執行，沒有新增背景掃描器、MCP 安裝器、固定排名或跨 host 路由服務。

[MCP 安全文件](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)指出本機 server 涉及執行程式；[tool annotations 說明](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/)也將 read-only 等標記定位為提示。採用前看來源、實際副作用及資料流，沿已有授權操作；相關條件改變才重查，沒有每次呼叫重做研究。[GitHub MCP](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md)的工具限制與 [Playwright MCP](https://github.com/microsoft/playwright-mcp#security)的瀏覽器設定，亦不代替底層存取邊界。

RTK 採用固定 commit [`bd7f87e`](https://github.com/rtk-ai/rtk/commit/bd7f87eb6e21a17c47ee3c78f698e81b64d7fee5)查原始碼；另列測試和回饋的各自版本，不將 develop、release、prerelease tag 或不同 integrations 混成一版。

| 證據 | 能支持的結論與限制 |
|---|---|
| [固定版 README](https://github.com/rtk-ai/rtk/blob/bd7f87eb6e21a17c47ee3c78f698e81b64d7fee5/README.md)、[Cargo](https://github.com/rtk-ai/rtk/blob/bd7f87eb6e21a17c47ee3c78f698e81b64d7fee5/Cargo.toml) | Shell 路徑是 CLI proxy 與 host hooks，另有 engine／API proxy；不是只憑 RTK 名稱就能判斷為某個 MCP。該快照 Cargo version 為 0.49.0，預設連結 engine；根目錄 Apache 標籤不能概括 engine 的 BUSL 條款，須看實際 edition 與 [engine LICENSE](https://github.com/rtk-ai/rtk/blob/bd7f87eb6e21a17c47ee3c78f698e81b64d7fee5/engine/LICENSE)。這是來源辨認，非本框架替商用使用作授權判定。 |
| [estimate_tokens 實作](https://github.com/rtk-ai/rtk/blob/bd7f87eb6e21a17c47ee3c78f698e81b64d7fee5/text/src/lib.rs#L73)、[官方 savings 定義](https://github.com/rtk-ai/rtk/blob/bd7f87eb6e21a17c47ee3c78f698e81b64d7fee5/docs/guide/resources/savings-explained.md) | 以 UTF-8 bytes／4 向上取整估計，沒有模型 tokenizer。其 gain 可描述輸出 byte 縮減，不能當 provider token／帳單；官方也區分 Bash output 與 session 成本。 |
| [JetBrains 一手 A/B](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/) | RTK v0.43.0、Claude Code 2.1.201、Sonnet 5，SkillsBench 86 題，共報告 425 次 billed trials；成本配對中位數低推理強度 +7.6%、高強度 +0.1%，品質差異未顯著。這是提供 AI 產品的外部廠商測試，未見完整原始 run artifacts 可下載，本框架未重現；不推論最新 engine／proxy 或所有工作負載都無效，也不把差異全歸因於漏資訊。 |
| [官方 security advisories](https://github.com/rtk-ai/rtk/security/advisories) | 查到 project-local filter 信任、permission-gate bypass 與 OpenClaw plugin 注入等不同問題，須逐 integration 核對修補；不能合稱所有 RTK 都受同一漏洞影響。[permission-gate 頁](https://github.com/rtk-ai/rtk/security/advisories/GHSA-7gxq-fvfc-g327)修補欄為 `>= 42.2`，與其他版號格式不同，不擅自修正為 `0.42.2` 或宣稱某版已安全。 |
| [近期原始 issue #5000](https://github.com/rtk-ai/rtk/issues/5000) | 2026-11-04，goat-ssh，RTK 1.1.0／macOS，以 fake kubectl JSON 回報 Running 但未 ready／CrashLoopBackOff 被摘要隱藏；查閱時 Open，連到 PR #5001。本框架未重現，只作保真驗收的重要線索。 |
| [原始正反討論](https://www.reddit.com/r/ClaudeCode/comments/1rvj76i/which_token_optimizer_do_you_use_rtk_causing_too/) | 有使用者表示效果不錯，也有人回報漏資訊與重試，均未提供完整 session usage；該串另有 Omni 作者與 Edgee 共同創辦人推廣自身產品，與一般使用者分開看。不以留言數量判定效果，帳號自述的經驗不能獨立驗真。 |
| [作者 launch](https://www.reddit.com/r/ClaudeAI/comments/1r2tt7q/i_saved_10m_tokens_89_on_my_claude_code_sessions/)、[OpenCode 原串](https://www.reddit.com/r/opencodeCLI/comments/1rsg4m1/rtk_rust_token_killer_just_merged_opencode_support/) | Launch 的高節省比例是作者自述；OpenCode 使用者分享 gain，工作負載與數字一致性仍須核對。都不能取代實際 provider usage、快取、重跑與完成品質的配對比較。 |

決定：保留 RTK 為可評估候選，不預設安裝或啟用全域 hook／proxy。Windows PATH 與 WSL 未發現 rtk，本次未安裝、未執行、未讀私人 usage，也未聲稱已測得本機省 token。若未來真的要採用，再以當時版本、元件、host 與任務作已授權的限定比較；新查核不永久沿用本節快照。

## Skills、工作流程與工具

| 來源 | 採用的理由 | 沒有照搬或仍須確認的部分 |
|---|---|---|
| [OpenAI：Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | 共同指令保持精簡，非共用細節按需要讀 references | 不以一份更長的總提示解決所有失敗，也不把文章中的特定模型變成框架依賴 |
| [OpenAI：Eval skills](https://developers.openai.com/blog/eval-skills) | 用實際請求、原始材料與行為結果驗證 skill | 格式與關鍵字檢查不能證明代理的選擇正確；尚未量測時不宣稱品質或 token 改善比例 |
| [OpenCode skills](https://opencode.ai/docs/skills/)、[models](https://opencode.ai/docs/models/)、[compaction](https://opencode.ai/docs/compaction/) | 區分按需載入的技能、同一 session 內切換模型與跨工作階段交接 | 不要求每次切模型都產出完整交接；按需載入也不代表固定 rules 或 tool schemas 沒有 context 成本 |
| [GitHub MCP 設定](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md) | 根據需要選 read-only 與工具 allowlist，避免暴露整套能力 | Lockdown 等模式不取代真正權限邊界；本框架不因此取得帳號或安裝授權 |
| [Context7 API guide](https://github.com/upstash/context7/blob/master/docs/api-guide.mdx) | 查版本文件能降低依記憶補 API 的風險 | 指定版本沒有索引時可能得到別版內容，仍須核對實際回傳版本；未接通不算已整合 |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | 只有需要瀏覽器狀態與互動時才選用 | Browser/MCP 不是安全隔離邊界，不預設安裝或用它取代可用 API |
| [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)、[draw.io CLI](https://www.drawio.com/doc/faq/command-line-options)、[drawio-mcp](https://github.com/jgraph/drawio-mcp) | 保留可編輯圖源，按交付需要選擇渲染或匯出 | 不照搬外部工具文件中任意刪檔或「永遠使用」的指令；能輸出圖不代表圖意正確 |
| [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)、[Aider lint/test](https://aider.chat/docs/usage/lint-test.html) | 參考可見執行軌跡、停止條件與短回饋迴圈 | 不整套導入另一個 agent runtime，不假定其 benchmark 能直接代表本框架效果 |

來源中提到的 MCP 與工具是候選或參考，不是本框架預設相依。是否採用仍取決於缺少的能力、維護狀態、資料流、權限、成本與可驗證性。未實際連接或執行的能力不能列為驗證成功。

## 學習方法

| 研究或實踐來源 | 採用方式與限制 |
|---|---|
| [Kalyuga 等，2003：expertise reversal](https://doi.org/10.1207/S15326985EP3801_4)、[AERO：認知負荷](https://www.edresearch.edu.au/summaries-explainers/explainers/managing-cognitive-load-optimises-learning) | 初學相關機制時提供示範與支援，熟悉後減少重複提示；不能只用職稱或年資判斷當前知識 |
| [Chi 等，1989：self-explanation](https://doi.org/10.1207/s15516709cog1302_1) | 可邀請讀者解釋關鍵步驟如何連到原則，不逐行考問；原始力學例題研究不是 AI 程式教學的直接驗證 |
| [Roediger 與 Karpicke，2006](https://doi.org/10.1111/j.1467-9280.2006.01693.x)、[CMU retrieval practice](https://www.cmu.edu/teaching/resources/instructionalstrategies/activelearningstrategies/retrievalpractice/) | 需要長期記住時加入短述、預測或操作與回饋；不把測驗變成閱讀關卡，也區分立即表現與延後保留 |
| [Cepeda 等，2008：spacing](https://doi.org/10.1111/j.1467-9280.2008.02209.x) | 後續相關任務可再次運用；不規定所有人同一複習間隔，也不自行建立提醒 |
| [Brunmair 與 Richter，2019：interleaving meta-analysis](https://pubmed.ncbi.nlm.nih.gov/31556629/) | 用於比較容易混淆的相近機制；不解讀成頻繁切換不相關任務。效果依材料而異，不能宣稱對 spec 說明性文本一定有效 |
| [Hmelo-Silver 等，2007：scaffolding 與問題導向學習](https://doi.org/10.1080/00461520701263368) | 用有支援的小型真實任務串起知識；問題導向學習不等於放手讓新手探索，也不等同所有專案學習都有效 |
| [Dunlosky 等，2013 綜述](https://doi.org/10.1177/1529100612453266) | 參考不同方法的證據與情境限制；不把方法排名當成每次都該執行的固定流程 |
| [Diátaxis tutorials](https://diataxis.fr/tutorials/)、[how-to](https://diataxis.fr/how-to-guides/)、[Carpentries key points](https://carpentries.github.io/instructor-training/key-points.html) | 分清學習、操作、查閱與原理解釋的目的，透過回饋找理解缺口；不強制所有教材採相同章節或把原理解說從帶讀中全數移除 |
| [Keshav：How to Read a Paper](https://cs.uwaterloo.ca/~brecht/courses/854-http-video-2012/readings/keshav-paper-reading.pdf) | 由相關性到深入重建，閱讀深度依目的調整；這是作者的方法，不是普遍最佳的實驗結論 |

這些研究多來自一般教育或心理學情境。如何套用到 kernel、repo、論文與 spec，是本框架的設計推論，仍需使用者的真實任務與回饋驗證。AI 的示範和自評不能當作真人已學會的證據。

## 工程說明、Trace 與貢獻

- [Google audience](https://developers.google.com/tech-writing/one/audience)、[paragraphs](https://developers.google.com/tech-writing/one/paragraphs)、[illustrating](https://developers.google.com/tech-writing/two/illustrations)：依讀者背景選內容，維持段落焦點與圖的明確用途。不將英文段落句數、標點或文化習慣機械套用到台灣中文。
- [臺大寫作教學中心：學術寫作的構句原則與技巧](https://awec.ntu.edu.tw/%E5%B0%88%E9%A1%8C1%EF%BC%9A%E5%AD%B8%E8%A1%93%E5%AF%AB%E4%BD%9C%E7%9A%84%E6%A7%8B%E5%8F%A5%E5%8E%9F%E5%89%87%E8%88%87%E6%8A%80%E5%B7%A7/?lang=en)：以話題、斷句、轉承與資訊安排改善中文連貫，不做固定禁詞表。
- [Julia Evans：Patterns in confusing explanations](https://jvns.ca/blog/confusing-explanations/)、[How to teach yourself hard things](https://jvns.ca/blog/2018/09/01/learning-skills-you-can-practice/)：參考具體例子、讀者背景與辨認卡點的作者實踐；不把個人經驗稱為普遍的教學實證。
- [Samuel Taylor：學習陌生 codebase](https://www.samueltaylor.org/articles/how-to-learn-a-codebase.html)：以具體工作、架構及資料流建立理解；不照搬在正式工作區隨機改動的建議。
- [Linux submitting patches](https://docs.kernel.org/process/submitting-patches.html)、[reporting issues](https://docs.kernel.org/admin-guide/reporting-issues.html)、[verification and bisection](https://docs.kernel.org/admin-guide/verify-bugs-and-bisect-regressions.html)：保存重現、環境、問題影響與修改理由；找到引入 regression 的 commit 後仍須解釋故障機制。投稿慣例以實際子系統的目前文件為準。
- [GDB backtrace](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Backtrace.html)：stack 觀察有執行上下文範圍，不能由單次 backtrace 拼成非同步事件或跨程序的歷史。
- [r/freelanceWriters 的作者原討論](https://www.reddit.com/r/freelanceWriters/comments/1oofc4c/im_so_mad_that_i_have_to_change_my_writing_style/)：有人因標點等慣用寫法被懷疑使用 AI。這是社群經驗，僅提醒風格判定可能造成不必要改寫，不作辨識率或普遍性的證據。

## 公開 skills 與授權處理

本框架的 skills、文件與範例以自己的文字撰寫。這裡引用想法與實踐來源，不代表直接收錄上游檔案，也不把來源連結當作複製或再散布授權。

| 已閱讀材料 | 核對到的授權與範圍 | 本框架的處理 |
|---|---|---|
| [blader/humanizer v3.1.0](https://github.com/blader/humanizer/blob/main/SKILL.md) | 實際 [LICENSE](https://github.com/blader/humanizer/blob/main/LICENSE) 為 MIT；英文修訂案例以散文與百科文字居多 | 參考保留事實、刪除空泛強調及對準讀者的原則；未直接打包原檔，不採破折號、英文詞彙等全域禁用規則 |
| [Anthropic doc-coauthoring](https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md) | 查閱時 skill 沒有 license 欄位、目錄沒有個別 LICENSE、repo 根沒有 LICENSE；[README](https://github.com/anthropics/skills/blob/main/README.md) 表示許多 skills 為 Apache 2.0，但未確認這個檔案的個別適用條款 | 僅參考受眾、目的與陌生讀者檢視的概念，未複製原文。不採每節固定問 5–10 題、列 5–20 個選項或反覆確認的流程 |
| 使用者提供的 repo／spec 教學參考 | 部分材料具有專案專屬設定、授權或個人歷史偏好 | 保留來源、狀態、角色與假設分開的原則；未搬入原始程式、規格擷取物、私人路徑、歷史授權、版號或配色規則 |

公開 skill 也可能含有互相牴觸的範例。像 `humanizer` 要求不新增事實，但其中 hash map 改寫範例補入了原句沒有提供的實作與複雜度；因此本框架要求修訂後核對技術含義，不因為來源流行就直接信任。

## 仍待真實使用驗證

路由、受限範圍、靜態檢查、腳本行為與跨平台執行可透過案例驗證；實際 token 用量、不同模型的表現、跨供應商交接與真人長期學習成效需要另外取得資料。未量測的部分保留未知，不以 skill 數量、文件頁數或 AI 自評代替成果。

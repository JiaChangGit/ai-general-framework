# 設計依據與採用範圍

這份紀錄說明框架為何採用某些方法、哪些做法沒有照搬，以及證據能支持到哪裡。它是設計依據，不代表所有整合、模型與教學方法都已在本框架驗證。外部工具會變動，實際操作仍需核對使用版本的文件。

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

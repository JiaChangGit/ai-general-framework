# 設計依據與採用範圍

這份紀錄說明框架為何採用某些方法、哪些做法沒有照搬，以及證據能支持到哪裡。它是設計依據，不代表所有整合、模型與教學方法都已在本框架驗證。外部工具會變動，實際操作仍需核對使用版本的文件。

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

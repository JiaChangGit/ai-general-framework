# 這批連結的取捨紀錄

查閱日期：2026-11-09（Asia/Taipei）。合併使用者前後提供的連結，包含較早的 MiroFish、Orca；Tenten 文章是查找線索，技術主張盡量回查上游文件、skills 或原始碼。這是一次來源閱讀與設計取捨，**沒有安裝、執行或替這些專案完成安全／效果驗收**，也不是持續更新的工具排行榜。

## 去重後真正補什麼

| 缺口 | 本輪處理 | 保留的邊界 |
|---|---|---|
| 去 AI 味可能磨掉本人語氣，甚至補造經歷 | writing 用同類樣本、實際修訂及明示偏好校準，將暫時推測與偏好分開 | 不建立禁詞／標點檢查器、不用 detector 分數當品質、不公開私人樣本 |
| 重複錯誤一直累積成提示詞 | maintenance 優先消除雙重來源，選合適的型別、檢查、真實反例 | 判斷性規則仍用文字，不為小錯重寫架構 |
| 配置後的 references 未必齊全 | 擴既有 audit 到 templates Markdown；隔離配置核對單項 skill、shared／copy 及本地版本 | 格式／檔案存在、宿主載入與行為增益分開驗證 |
| graph 或摘要容易被當成完整證據 | tools 查來源版本、未提交變更、語言／排除範圍、截斷及實讀內容 | 不預建索引或記憶服務；否定與改動需要時回到原始碼 |
| 多篇轉述被當成多份研究 | read-research 增加聚焦文獻比較，辨認同一研究、版本與條件 | 不以篇數投票，不冒稱系統性回顧或重現 |
| 每種文件／媒體各建一套流程 | 一份按需 artifacts 參考串起內容、素材、小樣、格式與實際播放／編輯驗收 | 真正工具用時選；沒有新增 renderer、模型 router 或素材庫 |

五個技能入口、四份部署指引與標準庫核心維持原架構。新參考是作品需要時才讀，研究紀錄不部署到下游。下列來源大多與現有方法重複；沒有為了每個 repo 都找一個新增功能。

## 開發、寫作與技能維護

固定版本連結方便回查這次實際看的內容；授權欄是該範圍的觀察，不能涵蓋所有相依或素材，也不代表已取得複製上游檔案的許可。本輪以自己的文字歸納方法，未收錄上游程式、技能或素材。

| 已讀來源／固定版本 | 值得保留的機制與未照搬部分 |
|---|---|
| [pstack a6342de](https://github.com/backnotprop/pstack/blob/a6342ded43a2437e3c664b46c2cff103787773fd/skills/correct/SKILL.md)，MIT | 架構單一來源、型別／lint、行為測試先於增加 prompt；用真實錯誤核對防護。不採每次更正都加規則表或整套相依技能。 |
| [gstack 1e25057](https://github.com/garrytan/gstack/blob/1e250570d8c99ad09664d0fd250b29fa2f76509a/write-skill/SKILL.md)，MIT | edit ladder 要先修工具、改既有規則、把細節放適當層；README 區分實際 host 認證、experimental、instruction-only。不搬其固定 preamble、telemetry、角色全流程、更新或發布動作。 |
| [Ponytail 96608e0](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/skills/ponytail/SKILL.md)，MIT | 先找現有功能、標準庫及平台能力，最小修改仍完成受影響的 callers 與必要防護。這部分已有；不採整個 session 的廣泛自動觸發、每次固定附言或把作者 benchmark 當本框架省 token 證據。 |
| [Addy 301b02b](https://github.com/addyosmani/agent-skills/blob/301b02b12bff98e4688e6984af6556802322bbde/scripts/validate-reference-links.js)，MIT | 核對參考連結與技能獨立配置能力，促成本框架 audit 小修。不移入整套 validator 或多個重疊技能。 |
| [mblode 5eeba20](https://github.com/mblode/agent-skills/blob/5eeba20fa3b9b142be7705ee9e6c7401e7ee6f08/skills/agent-skills-creator/SKILL.md)，MIT | 先找工作已有誰負責，測試本地修改版；ghostwriter 以本人同類作品與修訂支持語氣。不新建另一個 creator 或個人風格資料庫。 |
| [anti-vibe-writing 3126f86](https://github.com/weijt606/anti-vibe-writing/blob/3126f86cce5c36904b8d6350edd994e97796ecd3/README.md)，MIT | 場景與真實樣本有助校準表達；它本身整合 humanizer 等來源，不能重複算成獨立品質證據。不採全域禁標點、刻意不規則或分數門檻。 |
| [rnskill 83d1783](https://github.com/Pluviobyte/rnskill/blob/83d1783b892bbaa29a137895ff8338264b6872fa/README.md)，根授權 CC BY-NC 4.0、個別目錄另有條款 | 分清原文事實、視聽建議與新增改編；沿現有創作邊界表達，不強制用其分類代號。不將整包併入 MIT 框架。 |
| [human-writing 5c0c30d](https://github.com/KKKKhazix/human-writing/blob/5c0c30d33648deef4a6ed69e5def87adb858f3e2/human-writing/SKILL.md)，MIT | 材料先於文風，事實稿與虛構稿分開，不編造親歷。新版 README 記錄修正心理描寫刪除過度、冒號／對白誤判；不搬硬字數／標點要求。 |
| [Karpathy-inspired 2c60614](https://github.com/multica-ai/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/CLAUDE.md)，授權未完整確認 | 四項主軸與既有釐清、簡潔、局部修改、驗證重複，不新增規則。這是他人整理；README 宣稱 MIT，但該 ref 未找到根 LICENSE，不稱官方技能或搬入檔案。 |
| [PM Skills 2a12295](https://github.com/phuryn/pm-skills/blob/2a12295a7717569baa7be181b4cfebe3ca38a6bb/pm-product-discovery/skills/prioritize-assumptions/SKILL.md)，MIT | 先驗最影響決策的前提，用低成本觀察再投入；不安裝整套 PM 流程。該檔 Confidence 同時寫 1–10 與 `1 - Confidence`，未交代尺度轉換，因此不照抄公式或編精確分數。 |
| [Orca ace74af](https://github.com/stablyai/orca/blob/ace74af49008dc8d0da7410964883b283757acf8/README.md)，MIT；較早提供 | 多工作目錄與集中 diff 回饋可沿宿主使用，不建另一個 orchestrator。只讀 README，未驗證桌面、遠端或手機；worktree 不等於作業系統、服務與憑證已隔離。 |

## 資料、記憶、程式關係與介面

| 已讀來源／固定版本 | 值得保留的機制與未照搬部分 |
|---|---|
| [CodeGraph f72c9d2](https://github.com/colbymchenry/codegraph/blob/f72c9d2efb14454ff4f9fd7b8460abd82f19a287/README.md)，MIT | 依問題查符號與關係，再取必要原文；不預設全庫索引。其 benchmark 也承認長對話殘留檢索 context 可能較多，不能只看單次輸出變短。 |
| [codebase-memory-mcp 612eee2](https://github.com/DeusData/codebase-memory-mcp/blob/612eee2518ef84cc573e491fdee5fa5c90264cb5/README.md)，MIT | 保存來源及解析 coverage gaps，對 C/C++ 編譯分支尤須核對；沒有 caller 不足以刪函式。不加入 daemon、預設 hooks 或整套 integration。 |
| [code-review-graph 115dccf](https://github.com/tirth8205/code-review-graph/blob/115dccf312b1576833bd8ead8e21dc680c8a67a5/code_review_graph/tools/_common.py)，MIT，預設 staging | 變更影響與有界結果可輔助 review；`head_matches_build` 只比 HEAD，不能證明未提交變更已入圖。仍是按需外部候選，token panel 不代表整任務帳單。 |
| [Supermemory 16ed414](https://github.com/supermemoryai/supermemory/blob/16ed414e0e0c61c946b7687ec813b2064fe75dd4/README.md)，metadata MIT | 少量知識有來源、範圍、時效且能更正／移除；既有 profile／task 可承接，不新增外部記憶引擎。local 段仍涉及首次模型下載、URL hosted reader 與 telemetry 選擇。 |
| [Agent-Reach c70ae6d](https://github.com/Panniantong/Agent-Reach/blob/c70ae6da5d39bc90e09ad2ae0575ccc89f31e284/agent_reach/skill/SKILL.md)，MIT | 正文、評論、圖片、字幕分別確認，精確選能力。不因 URL 就啟動整套工具；session Cookie 複製、依賴準備與讀公開頁面分開授權。 |
| [Impeccable 924bbd1](https://github.com/pbakaus/impeccable/blob/924bbd194d02e5e15a227e75b5901fb0d7a4ecad/README.md)，Apache-2.0 | 介面目的、既有設計、指定範圍、實際尺寸和內容狀態檢查；不加入 commands、engine、catalog 或預設 hooks。 |
| [UI UX Pro Max 4f2dbb6](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/4f2dbb67e64969a9a30ab00742f2d55d66ddec2b/README.md)，MIT | 保留重排、長中文、輸入法與既有設計的判斷；不收完整 styles／資料庫或 stack 的廣泛權限設定。 |
| [MiroFish 7657031](https://github.com/666ghj/MiroFish/blob/7657031ac01184afe2cb220f5ee3545573b5e843/README.md)，AGPL-3.0；較早提供 | 只讀 README。可把多代理模擬當情境提案，不能把產品的預測宣傳當實測證據、股市結論或真實訓練資料；不導入其 LLM／Zep Cloud 管線。 |

## 文件、視覺與影音

| 已讀來源／固定版本 | 值得保留的機制與未照搬部分 |
|---|---|
| [Hallmark 407fa68](https://github.com/nutlope/hallmark/blob/407fa689f4a276f2fd389208d271d0fef08f5058/README.md)，MIT，照片另有條款 | 用途決定版面，先做代表區塊再瀏覽器核對；缺陷、預設與偏好分開，不收整套 themes。 |
| [Hyperframes eb16510](https://github.com/heygen-com/hyperframes/blob/eb16510a10fbc30f230ae2b7d6e5a7ac50e31eeb/README.md)，Apache-2.0 | 可定位時間的動畫、preview／代表影格／render 分開；slideshow 不等於 MP4。不加入 runtime 或 skill 的 usage beacon。 |
| [Stickman eb4bb37](https://github.com/kaomei/stickman-video-director/blob/eb4bb378c4716a617f9ad7d98a60379b9d1fa54a/README.md)，MIT | 企劃與成片分開，先核對能力，含聲短樣及真實旁白長度驅動畫面；局部重做，不要求一開始生成整片。 |
| [Guizang 93d21bf](https://github.com/op7418/guizang-ppt-skill/blob/93d21bf4a73a851907a6eb00acbf30618236667a/README.md)，AGPL-3.0 | 核心為 HTML deck，PPTX 轉換不是主流程；借鏡講稿、排練與投影驗收，不稱為內建 PPTX 引擎或打包原檔。 |
| [Pose Gallery 4889391](https://github.com/anhao/ai-pose-gallery-zh/blob/488939139c69acfe078372b39d4bd0c457dc060e/README.md)，混合範圍 | 程式目錄的 MIT 不涵蓋 img／thumbs／data。人物、服裝、姿勢分開可維持一致，圖片仍需回源查權利，不建預設商用素材庫。 |
| [Code Animation Prompts 2e6396a](https://github.com/XiaoyeCodes/code-animation-prompts/blob/2e6396abb45c2d183e91bc5a6583597411860217/README.md)，混合來源條款 | 依 keyword／編號只取所選風格；文字、靜幀、成片分開，`window.renderAt(t)` 為該 renderer 契約。包含 MG Styles 等衍生材料，不能算獨立品質佐證。 |
| [HTML Anything 975fb3b](https://github.com/nexu-io/html-anything/blob/975fb3bcb98f1777781fb4c738902d36e32c8c46/README.md)，Apache-2.0 | 同一內容依閱讀目的呈現；收錄 Guizang／Hyperframes 等，不重複搬入。沿用 CLI 登入不等於沒有外傳或零費用，不導入 editor 與寬鬆權限設定。 |
| [MG Styles 49052d8](https://github.com/Vincentwei1021/mg-styles-15/blob/49052d80bfaf9fa8412cc9710530e5e95a3b8d8c/README.md)，MIT、字型另備 | 共用 cues／時間安排驅動畫面與聲音；AI 評分不是觀眾品質證據，不強制每次完整多輪評審。 |
| [Inference Skills 0cbf91c](https://github.com/inference-sh/skills/blob/0cbf91c26ada28702c79962406286f0c14292150/README.md)，授權未完整確認 | README 有 MIT badge，該 ref 的 tree 未找到 LICENSE。實際是 belt CLI、登入與遠端 apps；學真實 input／output 契約，不加入大量模型 skills，也不以 app 的商用標籤證明個別素材權利。 |
| [Hypit 2d31e88](https://github.com/hypit-ai/hypit/blob/2d31e88765e297f0795348b460c77a6067f12261/LICENSE)，附加條件的修改版 Apache | 可借鏡以語音對齊及重用素材的成片流程；條款對部分 hosted／再散布用途另有限制，不能簡稱標準 Apache-2.0。不採下載 wrapper 或加入生成平台。 |

## Tenten 七篇：哪些是線索，哪些需回到一手來源

| 使用者提供的文章 | 讀後取捨 |
|---|---|
| [AGENTS.md 工程化](https://skills.tenten.co/docs/skills-atlas-x-freeman1266-2053055657335832828) | 已開原始 HTML。精簡導覽與命令同步有用；不採每次錯誤都加規則、每條規則都配 script、固定九段或「換模型零成本」等普遍化說法。 |
| [Dynamic Workflows](https://skills.tenten.co/docs/claude-code-dynamic-workflows-tutorial) | 已開原始 HTML。學分工／中間產物／驗證分開；版本、觸發字、preview 與續接行為會變，不把舊設定寫成全 host 規則。官方也提醒多代理工作流會增加用量。 |
| [Humanizer Top 10](https://skills.tenten.co/docs/skills-atlas-humanizer-skills-top-10) | 策展分類有助選擇，不是通用效能排名。去 AI 味先保真與讀者適配，不搬整組重寫器、硬標點禁令或作者身分分數。 |
| [三層工具架構](https://skills.tenten.co/docs/tenten-solution-template) | 讀到 Agent-Reach／agency-agents／LiteLLM 三層提案；本框架已有原生探索與手動模型切換，不為此新增 gateway、角色人格庫或安裝鏈。 |
| [Website Cloner](https://skills.tenten.co/docs/skills-atlas-jcodesmore-ai-website-cloner) | 回查 [上游 ee3f5a2](https://github.com/JCodesMore/ai-website-cloner-template/blob/ee3f5a2f31fd549b9593fa4f7cf6d2955ee593bb/README.md)：目前主流程為 Map／Observe／Build／Compare，與文章六階段不同。取同尺寸／同狀態比較與既有資產核對，不照抄舊流程、固定前端棧或耗時／token 數。 |
| [Codex App](https://skills.tenten.co/docs/skills-atlas-openai-codex-app) | 文章有較早模型、額度與入口假設；回查 [OpenAI skills](https://learn.chatgpt.com/docs/build-skills)及[雲端環境](https://learn.chatgpt.com/docs/environments/cloud-environment)，不把檔案配置當已載入，也不假設本機／雲端設定完全相同。 |
| [Codex CLI Best Practices](https://skills.tenten.co/docs/codex-cli-best-practices) | 以 [OpenAI sandboxing](https://learn.chatgpt.com/docs/sandboxing)與[設定參考](https://learn.chatgpt.com/docs/config-file/config-reference)核對。權限、網路及 approval 各有作用，不把關閉保護的範例變成專案預設，也不新增長時自主執行器。 |

## 原始回饋與具體限制

- [Addy #361](https://github.com/addyosmani/agent-skills/issues/361) 已 closed；固定 ref README 仍警告單 skill 安裝缺 repo-level references。採納的是實際配置核對，未自行重現其安裝器問題。
- [code-review-graph #849](https://github.com/tirth8205/code-review-graph/issues/849) 是 2.3.7 的巨大輸出回報，2026-08-19 已 closed，現行 `_common.py` 有結果上限。不據此稱現版仍有同一故障；也不從 HEAD 比對推成完整 freshness。
- [Agent-Reach #936](https://github.com/Panniantong/Agent-Reach/issues/936)、[#938](https://github.com/Panniantong/Agent-Reach/issues/938) 是 2026-11-08 的 open 回報，涉及 URL 觸發過廣與 caption 被當完整圖像內容；未自行重現。用於設計窄路由與內容範圍核對，不推成所有版本失效。
- [CodeGraph telemetry](https://github.com/colbymchenry/codegraph/blob/f72c9d2efb14454ff4f9fd7b8460abd82f19a287/TELEMETRY.md) 有預設統計與更新檢查；[Impeccable telemetry](https://github.com/pbakaus/impeccable/blob/924bbd194d02e5e15a227e75b5901fb0d7a4ecad/crates/context/src/telemetry.rs#L118) 關統計仍需 catalog 請求。[Agent-Reach sessions](https://github.com/Panniantong/Agent-Reach/blob/c70ae6da5d39bc90e09ad2ae0575ccc89f31e284/agent_reach/skill/references/sessions.md) 另有 Cookie 與依賴準備；本地、登入沿用與無外傳不是同一件事。
- [Hyperframes SKILL](https://github.com/heygen-com/hyperframes/blob/eb16510a10fbc30f230ae2b7d6e5a7ac50e31eeb/skills/hyperframes/SKILL.md) 要求 usage beacon；[UI UX stack 設定](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/4f2dbb67e64969a9a30ab00742f2d55d66ddec2b/stack/.claude/settings.json) 含廣泛 MCP／讀取預允，後者只屬該 stack 範本，不代表主 skill 一定執行。本框架沒有移入這些設定。
- [HTML Anything 預覽實作](https://github.com/nexu-io/html-anything/blob/975fb3bcb98f1777781fb4c738902d36e32c8c46/next/src/components/deck-viewer.tsx) 使用 `srcDoc` 與 `allow-scripts allow-same-origin`；不把 README 的 sandbox 稱呼當隔離證據。這是來源核對，沒有漏洞 PoC 或完整安全稽核。

查閱文件、讀取原始碼、原始回饋、實際重現與普遍效果是不同證據。本輪沒有外部工具 baseline、實際 provider usage、真人文風／學習或觀眾評估；節省 token、設計品質與媒體能力不能由這份研究直接保證。實際完成的本地變更與驗證另見 [verification.md](verification.md)。

# 記憶、提示與工具的採納紀錄

2026-11-09 查閱；本頁只供維護者回查。來源中的技巧、成效與安裝指令屬待評材料，不是本專案的新要求。日常只讀相關指引，沒有新增技能、記憶服務、爬蟲或模型總管。

## 這輪來源與取捨

| 來源 | 採納與限制 |
|---|---|
| [Anthropic：Components of Agent Memory](https://www.anthropic.com/research/components-of-agent-memory) | 借原始事件、整理筆記與按需索引的分層思路；workflow 補回查原始證據、假說須驗證、同時保留成功條件與反例。這是特定環境的工程報告，不把結果當成框架效果，也不引入背景 dreaming 或固定只記失敗的規則。 |
| [ELI5 討論](https://www.reddit.com/r/explainlikeimfive/comments/6hp6c6/eli5_how_do_i_explain_like_theyre_five/) | 教學參考補白話與比喻邊界：依讀者缺口解釋術語，不假定讀者是幼兒，例子不能抹掉必要條件。社群經驗不等於教學成效研究。 |
| [PromptEngineering 討論](https://www.reddit.com/r/PromptEngineering/comments/1q8wwov/the_ai_prompting_tricks_that_actually_matter_in/) | 受眾、背景與示例已有對應；不採固定大量訪談、展示內部思考鏈或以多數回答保證真實性。 |
| [Ponytail 官方專案](https://github.com/DietrichGebert/ponytail) | 重用既有能力、最小完整修改及保留驗證，已在 maintenance／workflow 涵蓋。沒有再裝全域 hook、固定結尾或把自報節省比例搬進本框架。 |
| [Craft Anything 介紹](https://skills.tenten.co/docs/skills-atlas-craft-anything)與[上游](https://github.com/storytold/craft-anything) | 查閱上游版本 `8638d6b72be3e99dcc73b06f92a8c113932c75f7`，仍標 early alpha。觀察、建立、比較與多尺寸驗收已有指引；暫不引入重建器或視覺分數。 |
| [Data-DI 提示文章](https://www.data-di.com/blog/ai-lab-prompt-1) | 目標、背景與驗收已有處理。工具型號、參數及所有聊天服務都是推理模型等泛化說法不採作框架事實。 |
| [Huang：AI PTCG thinking](https://huang.education/2025/12/ai-ptcg-thinking/amp/) | AMP 與一般頁面本輪皆無法取得完整內容；只找到分類摘要，未據此改規則或宣稱已讀全文。 |
| [Few-shot](https://agentai.tw/guides/few-shot-prompting/)與[negative prompting](https://agentai.tw/guides/negative-prompting/) | writing 補必要才給少量示例、用不同材料驗證，避免帶入樣板事實。不採固定例數、效果百分比或跨模型通用結論。禁止事項與偏好的模型語法分開。 |
| [運鏡介紹](https://twb2bweb.com/blog/ai-video-camera-movement-prompts/)與[大量 AI 標籤](https://www.purestudio.com.tw/blog/aitags/) | 提供發想線索；後者也標示多數標籤未測。outputs 只補工具適用的運鏡與結構化歌詞，直接回查官方 [Runway Gen-4](https://help.runwayml.com/hc/en-us/articles/39789879462419-Gen-4-Video-Prompting-Guide)及 [Udio guidance tags](https://help.udio.com/en/articles/11166249-level-up-your-creations-with-guidance-tags)。標記不是保證執行的命令，成品仍須實看實聽。 |
| [Scrapling](https://github.com/D4Vinci/Scrapling) | 官方提供擷取、動態瀏覽器及 MCP，BSD-3-Clause；本輪未安裝。與 source／宿主瀏覽器重疊，待真實批量擷取需求再評估。不能因具備避開平台挑戰的功能，就擴張成繞過存取控制的授權。 |

## 六項改進如何落地

本輪先補 `run` 的可選原始輸出預算，保留預設相容性；以既有 task／learning 指引做交接與解釋試用；使用既有 context／rg 與離線工具替身做小型檢查。真實來源擷取、媒體成品與跨供應商交接仍依可用材料和工具驗收，沒有用合成文字冒充這些整合。

[SWE-Skills-Bench](https://arxiv.org/abs/2603.15401)、[SkillsBench](https://arxiv.org/abs/2602.12670)與 [AGENTS.md 評估研究](https://arxiv.org/abs/2602.11988)支持固定材料、保留獨立驗收及比較邊際收益的研究方向；[ContextBench](https://arxiv.org/abs/2602.05892)則可參考檢索過程的觀察。不同研究任務與模型有差異，沒有把論文的平均結果當成 AGF 的成效。

[Promptfoo](https://github.com/promptfoo/promptfoo)留為可選評估工具；其自訂 provider、assertion 可執行程式，外部模型仍有資料流與費用。[Aider repo map](https://aider.chat/docs/repomap.html)與 [SCIP](https://github.com/scip-code/scip)待真實索引瓶頸再測；[MCP Inspector](https://github.com/modelcontextprotocol/inspector)待已授權的真實 MCP 入口再用，不把離線 fixture 稱為協定驗收。[Gitleaks](https://github.com/gitleaks/gitleaks)則已在隔離 QA 目錄固定版本並核對官方 checksum 後執行，沒有全域安裝或新增 hook。

實際命令、結果、失敗與未驗事項見[驗證紀錄](verification.md)。少量試用、截短的 JSON、規則掃描和代理判讀，都不能替代完整 usage、真人理解、媒體驗收或權限隔離。

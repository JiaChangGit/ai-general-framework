# 使用者提供的文章

2026-11-21 讀過全文，原始筆記在 [W-workflow-memory.md](../../studies/ecosystem-2026-11/W-workflow-memory.md)「四篇文章」一節。文章當作找專案的線索，技術主張都回到一手來源核對；文章提到但找不到來源的名稱列在[建議與待確認](recommendations.md)。

## 人蔘 TRY CATCH EP091：Vibe Coding 的資安

[原文](https://ginseng.dnplus.dev/blog/ep091)（2026-11-06）用三起 2026 年的事件（永豐銀行、91APP、幣安）講資安的三段（事前、事中、事後）與三個 A（認證、授權、稽核）。它示範的做法是：每講到一個資安名詞，就叫 pstack 的 `teach`，讓 AI 用自己的專案當例子解釋。

對框架有用的兩點：

- 幣安事件的入侵路徑是假面試誘騙工程師下載惡意 repo，再透過內部的 AI 工具擴散。這支持資料庫審查清單的做法：clone 下來的程式只讀不跑。
- 「用自己的專案解釋名詞」和 `guide-learning` 的方向一致。pstack `teach` 的細節（先依對方目的決定講幾個重點、先給一兩句完整答案再停、三個以上元件就畫一連串圖、每張多一個元件）見 [AI coding 工作流程比較](comparisons/agent-workflows.md)。

## vocus：本地記憶層的四個開源答案

[原文](https://vocus.cc/article/6a48c442fd89780001ba1661)從輕到重介紹 dejavu、mem-agent、OpenHuman、memory-os。文章沒有附網址；追查後發現其中兩個和使用者給的種子**同名但不同專案**：文章的 dejavu 是 jsingletonai/dejavu（repo 已經 404），memory-os 是 ClaudioDrews/memory-os。作者的觀察「四個都本機優先、Markdown 是共識」大致成立，但本機儲存不等於不送雲端：Memory OS 預設用 OpenRouter 的 embedding。比較見[記憶系統比較](comparisons/memory-systems.md)。

## vocus：memory-os 的分層設計

[原文](https://vocus.cc/article/6a37e0c6fd8978000159fc90)介紹 ClaudioDrews/memory-os 的七層記憶，主張向量搜尋加注入只解決「找得到」，沒解決 agent 會不會相信它；所以多一層「Ground Truth」告訴 agent 注入的記憶是權威。作者沒有自己部署。安裝腳本是 `curl | bash`，pip 失敗時改用 `--break-system-packages`，Qdrant 的 key 留空時會把認證關掉。

## vocus：壓縮、路由、替換

[原文](https://vocus.cc/article/6a2f761ffd89780001b51c13)把降低 AI 成本分成壓縮（headroom）、路由（OpenSquilla、Factory Router）與替換（deepclaude、ds4）。只有 Factory Router 查得到一手來源：它是 Factory 的 coding agent 內建的模型路由，依 prompt、程式範圍與工具判斷難度，卡住時升級；文件特別提到路由要顧及 prompt cache。作者自報的甜蜜點是成本約七、八成、通過率 96～99%，壓得更低時通過率掉到 49～81%。

對框架的意義：框架不做常駐路由（理由見[分析報告第六輪](../analysis-2026-11.md#會衝突或暫不做)），但「換模型會讓快取失效」這點和 workflow 指引的「在里程碑才換模型」一致。

## 另外讀的一篇

Anthropic 的〈Effective context engineering for AI agents〉：context 是有限資源，長 context 會讓模型表現下降；做法是只放最小、高訊號的內容，長任務用壓縮、筆記與子代理。和框架「常駐文字要少、按需讀指引」的方向一致。

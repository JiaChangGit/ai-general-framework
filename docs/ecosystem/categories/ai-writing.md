# 寫作、研究與 Podcast

寫作、長篇小說、研究筆記、引用管理與文件轉 Podcast。長篇小說的一致性（角色、時間線、伏筆）有兩種做法：Mythpen 是給人操作的桌面應用，集中管理角色、關係、伏筆、世界觀與時間線，也能從既有稿件反推這些資料（打包版預設開啟錯誤回報與使用統計，設定 → Privacy 可以關）；Novel Studio 是給 agent 跑的引擎，用結構化台帳與狀態機管章節。引用管理用 Zotero 加 zotero-mcp（本機讀 zotero.sqlite）；論文結構化用 GROBID（在文件解析類）。

Open Notebook 能從多份來源產生帶引用的筆記與 Podcast，但預設綁所有網路介面且沒有密碼，要改綁 127.0.0.1。文字品質由框架的寫作指引處理，這些工具負責素材與流程。

<!-- ecosystem:table ai-writing -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Open Notebook（lfnovo）](https://github.com/lfnovo/open-notebook) | 應用 | 1 | 可使用（MIT） | 2026-11-18 | 讀原始碼 | 開源、可自架的 NotebookLM 替代：多來源筆記本、含來源與筆記引用的問答、1～4 位講者的 Podcast 生成、REST API、20 多家模型 provider（含 Ollama）。 |
| [Mythpen](https://github.com/niyongsheng/mythpen) | 應用 | 2 | 有條件（GPL-3.0） | 2026-11-20 | 讀原始碼 | 本機優先的小說寫作駕駛艙：角色、關係、伏筆、大綱、世界觀、時間線集中管理，有六步引導的寫作模式與 AI 協作模式；可匯入既有的 TXT／EPUB，由模型切出卷與章並建立角色、世界觀、時間線、伏筆與敘事記憶；介面支援 11 種語言（含繁體中文）。 |
| [novel-studio（Xiaoyangy）](https://github.com/Xiaoyangy/novel-studio) | 專案 | 2 | 可使用（Apache-2.0） | 2026-09-23 | 讀原始碼 | Go 寫的本地優先、可恢復的長篇小說生產引擎：先推演世界與角色、封存章節計畫、逐章渲染與審核；角色獨立 Agent、世界裁決、RAG、伏筆與資源台帳、Dashboard。 |
| [Zotero](https://github.com/zotero/zotero) | 應用 | 2 | 需人工確認（AGPL-3.0（通識；GitHub 回報 NOASSERTION）） | 2026-11-21 | 只有搜尋摘要 | 開源文獻管理：收集、註解、引用格式輸出（CSL）、同步，內建 PDF 閱讀器。 |
| [zotero-mcp（54yyyu）](https://github.com/54yyyu/zotero-mcp) | MCP | 2 | 可使用（MIT） | 2026-11-19 | 讀文件 | 把 Zotero 文獻庫接給 AI：搜尋（標題、作者、全文、語意）、讀 PDF 註解、本機讀 zotero.sqlite，需要時寫入。 |
| [Awesome Novel Studio（MJbae）](https://github.com/MJbae/awesome-novel-studio) | skill 集 | 3 | 可使用（Apache-2.0） | 2026-04-14 | 讀原始碼 | Claude Code plugin：18 個專責 agent 與 10 個 skill，涵蓋 propose→design→create→polish→rewrite 的網文流程。 |
| [Podcastfy](https://github.com/souzatharsis/podcastfy) | 函式庫 | 3 | 可使用（Apache-2.0） | 2026-05-04 | 讀文件 | 把網頁、PDF、YouTube、文字轉成對話式 Podcast 的 Python 套件與 CLI，LLM 寫稿、TTS 合成語音。 |
<!-- /ecosystem -->

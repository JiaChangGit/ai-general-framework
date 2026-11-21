# 寫作、研究與 Podcast

寫作、長篇小說、研究筆記、引用管理與文件轉 Podcast。長篇小說的一致性（角色、時間線、伏筆）只有 Novel Studio 做成結構化台帳與狀態機，沒有找到獨立的一致性檢查工具。引用管理用 Zotero 加 zotero-mcp（本機讀 zotero.sqlite）；論文結構化用 GROBID（在文件解析類）。

Open Notebook 能從多份來源產生帶引用的筆記與 Podcast，但預設綁所有網路介面且沒有密碼，要改綁 127.0.0.1。文字品質由框架的寫作指引處理，這些工具負責素材與流程。

<!-- ecosystem:table ai-writing -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Open Notebook（lfnovo）](https://github.com/lfnovo/open-notebook) | 應用 | 1 | 可使用（MIT） | 2026-11-18 | 讀原始碼 | 開源、可自架的 NotebookLM 替代：多來源筆記本、含來源與筆記引用的問答、1～4 位講者的 Podcast 生成、REST API、20 多家模型 provider（含 Ollama）。 |
| [novel-studio（Xiaoyangy）](https://github.com/Xiaoyangy/novel-studio) | 專案 | 2 | 可使用（Apache-2.0） | 2026-09-23 | 讀原始碼 | Go 寫的本地優先、可恢復的長篇小說生產引擎：先推演世界與角色、封存章節計畫、逐章渲染與審核；角色獨立 Agent、世界裁決、RAG、伏筆與資源台帳、Dashboard。 |
| [Zotero](https://github.com/zotero/zotero) | 應用 | 2 | 需人工確認（AGPL-3.0（通識；GitHub 回報 NOASSERTION）） | 2026-11-21 | 只有搜尋摘要 | 開源文獻管理：收集、註解、引用格式輸出（CSL）、同步，內建 PDF 閱讀器。 |
| [zotero-mcp（54yyyu）](https://github.com/54yyyu/zotero-mcp) | MCP | 2 | 可使用（MIT） | 2026-11-19 | 讀文件 | 把 Zotero 文獻庫接給 AI：搜尋（標題、作者、全文、語意）、讀 PDF 註解、本機讀 zotero.sqlite，需要時寫入。 |
| [Awesome Novel Studio（MJbae）](https://github.com/MJbae/awesome-novel-studio) | skill 集 | 3 | 可使用（Apache-2.0） | 2026-04-14 | 讀原始碼 | Claude Code plugin：18 個專責 agent 與 10 個 skill，涵蓋 propose→design→create→polish→rewrite 的網文流程。 |
| [Podcastfy](https://github.com/souzatharsis/podcastfy) | 函式庫 | 3 | 可使用（Apache-2.0） | 2026-05-04 | 讀文件 | 把網頁、PDF、YouTube、文字轉成對話式 Podcast 的 Python 套件與 CLI，LLM 寫稿、TTS 合成語音。 |
<!-- /ecosystem -->

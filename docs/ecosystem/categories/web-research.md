# 網頁研究、資料集與擷取

網頁擷取、爬蟲、瀏覽器自動化、搜尋後端與公開資料集來源。工具比較見[網頁研究比較](../comparisons/web-research.md)。

資料集的授權看 dataset card 與平台條款，不等於裡面每一筆內容的權利。台灣政府資料開放平台用「政府資料開放授權條款第 1 版」，可以任何目的使用，但要依格式標示提供機關。蒐集原則見[授權判讀](../license.md)的「蒐集網頁資料時」。

<!-- ecosystem:table web-research -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Crawl4AI](https://github.com/unclecode/crawl4ai) | 函式庫 | 1 | 可使用（Apache-2.0） | 2026-11-20 | 讀原始碼 | 開源 Python 非同步爬蟲（Playwright）：輸出乾淨 Markdown（含 fit markdown 過濾）、CSS／XPath／LLM 結構化擷取、deep crawl、自適應併發；另有自架 Docker server 與 MCP，及付費雲端 API。 |
| [Firecrawl](https://github.com/firecrawl/firecrawl) | 服務 | 1 | 有條件（AGPL-3.0（主要）；SDK 與部分 UI 為 MIT） | 2026-11-21 | 讀原始碼 | 把網頁轉成 LLM 可用的 Markdown／結構化資料的 scrape、crawl、map、search 服務；倉庫含 Firecrawl Local（Rust，本機抓取）、完整自架伺服器（Docker Compose＋Redis＋PostgreSQL＋瀏覽器服務）、SDK 與一組 agent skills。 |
| [GitHub 作為資料與範例來源](https://docs.github.com/en/rest) | 資料集來源 | 2 | 有條件 | — | 只有搜尋摘要 | 公開 repo 的程式碼、README、issue 可透過 gh／REST／GraphQL 取得。 |
| [Playwright](https://github.com/microsoft/playwright) | 函式庫 | 2 | 可使用（Apache-2.0） | 2026-11-21 | 讀文件 | Microsoft 的瀏覽器自動化：單一 API 驅動 Chromium、Firefox、WebKit，有測試框架、Playwright MCP（@playwright/mcp）與給 coding agent 用的 Playwright CLI。 |
| [RSS／Atom、sitemap.xml、robots.txt 與 rate limit 實務](https://www.rfc-editor.org/rfc/rfc9309) | 文章 | 2 | 可使用 | — | 只有搜尋摘要 | RFC 9309 定義 robots.txt（Robots Exclusion Protocol）；sitemap.xml 與 RSS／Atom 是列舉內容的合法管道；robots.txt 是禮貌性協定，不是授權或存取控制。 |
| [SearXNG](https://github.com/searxng/searxng) | 服務 | 2 | 有條件（AGPL-3.0） | 2026-11-21 | 只有搜尋摘要 | 可自架的 metasearch 引擎：聚合多個搜尋引擎結果，不記錄使用者；可輸出 JSON 供程式使用。 |
| [trafilatura](https://github.com/adbar/trafilatura) | 函式庫 | 2 | 可使用（Apache-2.0） | 2026-11-20 | 只有搜尋摘要 | 網頁正文擷取（去除導覽與廣告）、中繼資料、sitemap／feed 探索與簡單爬取，輸出文字、Markdown、XML-TEI、JSON。 |
| [Zenodo](https://github.com/zenodo/zenodo) | 資料集來源 | 2 | 有條件（GPL-2.0（平台程式碼）） | 2026-03-13 | 只有搜尋摘要 | CERN 營運的研究成果存放庫，資料集、論文、軟體都有 DOI；每筆紀錄有授權欄位（多為 CC BY 或 CC0）。 |
| [台灣政府資料開放平臺（data.gov.tw）](https://data.gov.tw/) | 資料集來源 | 2 | 有條件（OGDL-Taiwan-1.0） | — | 讀文件 | 政府機關開放資料的集中入口；資料集多提供 CSV、JSON、XML 與 API。 |
| [Browser Use](https://github.com/browser-use/browser-use) | 函式庫 | 3 | 可使用（MIT） | 2026-11-21 | 讀文件 | 讓 LLM 操作真實瀏覽器完成任務的 Python 函式庫與 CLI；新版由模型寫 Python 驅動 Chrome（browser-harness）；也有付費雲端 agent 與雲端瀏覽器。 |
| [Hugging Face Datasets（Hub 與 datasets 函式庫）](https://github.com/huggingface/datasets) | 資料集來源 | 3 | 有條件（Apache-2.0（datasets 函式庫程式碼）） | 2026-11-19 | 只有搜尋摘要 | Hub 上託管大量資料集，每個有 dataset card（README YAML 中的 license、語言、大小）；datasets 函式庫串流或下載。 |
| [Kaggle Datasets 與 kaggle CLI](https://github.com/Kaggle/kaggle-cli) | 資料集來源 | 3 | 有條件（Apache-2.0（CLI 程式碼）） | 2026-11-18 | 只有搜尋摘要 | Kaggle 上的社群資料集與競賽資料；kaggle CLI 以 API token 下載。 |
| [OpenML](https://github.com/openml/openml-python) | 資料集來源 | 3 | 有條件（BSD-3-Clause（通識；GitHub 回報 NOASSERTION）） | 2026-11-16 | 只有搜尋摘要 | 機器學習資料集、任務與實驗結果的開放平台；openml-python 套件取用。 |
| [UCI Machine Learning Repository](https://archive.ics.uci.edu/) | 資料集來源 | 3 | 有條件 | — | 只有搜尋摘要 | 歷史最久的經典小型資料集庫，每個資料集有 DOI 與引用格式。 |
<!-- /ecosystem -->

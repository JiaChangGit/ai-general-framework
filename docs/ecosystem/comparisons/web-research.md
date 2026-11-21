# 網頁研究比較

查核日期：2026-11-21。原始筆記在 [M-data-media.md](../../../studies/ecosystem-2026-11/M-data-media.md)（比較 2）。這一頁沒有試跑。

| | Firecrawl | Crawl4AI | Browser Use | Playwright |
|---|---|---|---|---|
| 是什麼 | 抓取服務（scrape、crawl、map、search） | Python 爬蟲函式庫與自架 server | 讓 LLM 操作瀏覽器的 agent | 瀏覽器自動化函式庫 |
| 動態頁面 | 有 | 有（底層是 Playwright） | 有 | 有 |
| 結構化擷取 | 雲端有 JSON 擷取；本機回 Markdown | CSS／XPath（不用 LLM），或交給你設定的 LLM | 由 LLM 在任務中取得 | 自己寫選擇器 |
| robots.txt | README 說預設遵守 | `check_robots_txt` **預設關閉** | 沒有 | 自己寫 |
| 資料會不會上雲 | **會**：本機抓取失敗時預設改由雲端抓（設 `FIRECRAWL_CLOUD=off` 才不會）；search 一律走雲端 | 函式庫與自架不會 | 匿名 telemetry 預設開；頁面內容送給你設定的 LLM | 不會 |
| 授權 | AGPL-3.0（SDK 部分 MIT） | Apache-2.0 | MIT | Apache-2.0 |
| 8 GB WSL | 自架服務偏重；Local 版輕 | 可 | 可（成本在 LLM） | 可 |

## 建議

- 靜態頁面：先用框架的 `source fetch` 或 trafilatura（擷取正文）；有 API、RSS、sitemap 時優先用。
- 需要執行 JavaScript、輸出 Markdown：Crawl4AI，並**自己打開** `check_robots_txt`。
- 需要登入、填表或多步驟互動：寫 Playwright 腳本；Browser Use 讓 LLM 自己操作，成本與不確定性都較高。
- Firecrawl 只當參考；要用的話一定關掉雲端備援，並注意 AGPL。
- 搜尋後端可自架 SearXNG（AGPL，自用可以；上游搜尋引擎常封鎖它）。

不論用哪一個：固定 User-Agent、每個網域限速、遵守 `Retry-After`，記錄抓取時間與網址。robots.txt 是網站對爬蟲的要求，不是授權，授權見[授權判讀](../license.md)。去重與來源可信度沒有找到值得收錄的專用工具，先用網址正規化加內容雜湊。

框架現在已經有的：`source fetch` 只抓靜態頁、輸出有上限；tools 指引要求先用 API 與靜態頁、限定數量與節流、不繞過存取限制。動態頁與大量擷取等真的有任務時再接上述工具。

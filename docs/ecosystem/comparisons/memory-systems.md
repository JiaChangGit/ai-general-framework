# 記憶系統比較

查核日期：2026-11-21。原始筆記在 [W-workflow-memory.md](../../../studies/ecosystem-2026-11/W-workflow-memory.md)（比較 1 有完整表格）。這一頁沒有試跑。

## 先分清同名專案

| 名稱 | 種子裡的那個 | 文章裡講的那個 |
|---|---|---|
| DejaVu | HMAKT99/Dejavu：專案的**決策**記憶，加上違規與重複檢查 | jsingletonai/dejavu：**個人偏好**記憶，repo 已經 404 |
| memory-os | bmaltais/memory-os：TypeScript，給 Claude Code 等 | ClaudioDrews/memory-os：Python 七層，Hermes 專用；兩篇 vocus 文章講的都是這個 |

## 隱私先看這一欄

使用者的定義：存下的內容之後再送給模型服務，也算上雲端。**凡是把記憶注入 context 的系統，存下的內容都會再送給模型一次**，連框架自己的檢查點也是。差別在兩件事：寫入時有沒有另外再送一次（給模型壓縮、做 embedding），以及每一輪是不是自動注入。

| | 寫入時另外送模型 | 每輪自動注入 | telemetry 預設 |
|---|---|---|---|
| 框架現況（宿主記憶、`profile`、交接檔、續接檢查點） | 否 | 否（只提示先讀哪些檔） | 無 |
| claude-mem | **是**（observer 模型，預設 Anthropic 或付費雲端；可改本機端點） | 是（session 開頭與讀檔前） | 開 |
| Mem0 | **是**（預設 OpenAI） | 由應用決定 | 開（PostHog） |
| Letta Code | **是** | 是（記憶區塊常駐） | 沒查 |
| DejaVu（HMAKT99） | 否（規則挖候選，人工審核） | 是（決策區塊寫進 CLAUDE.md） | README 說沒有 |
| memory-os（bmaltais） | 否 | 是（最多 32 KB） | 沒有 |
| Memory OS（ClaudioDrews） | **是**（預設 OpenRouter embedding） | 是 | 沒查 |

## 真正不同的方向

1. **自動擷取、交給模型整理**（claude-mem、Mem0、Memory OS）：記得多，但每次寫入多一次模型呼叫，也多一次外送。
2. **自動擷取、不經模型**（memory-os bmaltais、框架的檢查點）：便宜、不外送，只有字面事實。memory-os 的 README 說能找到「完全不同說法」的問題，原始碼卻是把字詞雜湊成向量，只比對字詞；它自己 commit 的紀錄裡同一句話被記了十多次。
3. **人工審核的決策帳本**（DejaVu、框架的交接檔）：量少、品質高、可以放進 git。DejaVu 多做了一步：每條決策帶 `applies_to`（檔案範圍）與 `detect`（regex），能檢查程式有沒有違反決策。這是框架現在沒有的。
4. **agent 自己改自己的 context**（Letta、ACE）：最有彈性，也最難審核。

衝突與過期的處理有三種做法：只新增、讀的時候依時間挑最新的（Mem0）；相似的合併、舊的降權（Memory OS、claude-mem 的強度衰減）；事實帶有效期間，被推翻時標成失效並保留歷史（Graphiti）。框架目前靠人改交接檔。

## 評測數字不能互比

Mem0 自報的 LoCoMo 92.5、LongMemEval 94.4 是雲端版含專有最佳化的結果。LoCoMo 被稽核出 6.4% 的標準答案有錯、評分模型會接受故意答錯的答案（稽核者自己也做記憶產品）；Mem0 與 Zep 互指對方的實作錯。

## 建議

- **不加外部記憶服務。** 和使用者的隱私決定衝突，也沒有證據比檔案式交接有效。
- **可以借的設計**：DejaVu 的「決策帶範圍與檢查規則」，讓交接檔或專案規則裡的決定能被程式檢查（和 guard hook 同一個方向：把文字擋不住的事交給檢查）；Graphiti 的「失效但保留歷史」，用在交接檔的「已取代」標記。
- 要量框架實際花了多少，用 Claude Code 內建的 OpenTelemetry（只開 metrics 與 api_request event、送到本機），不需要記憶服務。見[評測、模型路由與可觀測性](../categories/benchmark-evaluation.md)。

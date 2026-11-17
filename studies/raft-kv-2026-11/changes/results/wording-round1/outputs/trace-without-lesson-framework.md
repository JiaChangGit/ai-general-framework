**輸入（來自 `input.md`）：** `queue=['a']`、`job='b'`、`capacity=1`。

**來源：** `queue.py` 的 `enqueue(queue, job, capacity)`。以下是靜態追蹤，我沒有執行程式。

| 步驟 | 條件 | 結果 |
|---|---|---|
| 1 | `len(queue) >= capacity`，也就是 `1 >= 1` | 成立 |
| 2 | 條件成立，進入 `if` 區塊 | 直接 `return 'full'` |
| 3 | `queue.append(job)` 與 `return 'ok'` | 沒有執行 |

**回傳值：** `'full'`

**queue 前後狀態：**
- 呼叫前：`['a']`
- 呼叫後：`['a']`，沒有變化。`job='b'` 沒有加入，因為 `append` 在 guard 之後，而 guard 已經先回傳了。

`input.md` 說沒有 runtime 故障回報，所以這裡沒有例外或清理要交代。

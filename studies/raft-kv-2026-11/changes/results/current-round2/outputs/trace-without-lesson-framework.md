**靜態追蹤**（`queue.py` 的 `enqueue`，輸入來自 `input.md`；未執行）

輸入：`queue=['a']`、`job='b'`、`capacity=1`

| 步驟 | 條件 | 結果 |
|---|---|---|
| 1 | `len(queue) >= capacity`，即 `1 >= 1` | 成立 |
| 2 | 進入 `return 'full'` | 回傳值為 `'full'` |
| 3 | `queue.append(job)` | 不會執行 |
| 4 | `return 'ok'` | 不會執行 |

**回傳值：** `'full'`

**queue 前後狀態：**
- 呼叫前：`['a']`
- 呼叫後：`['a']`，沒有變化。`'b'` 沒有被加入。

這次沒有實際執行，以上都是從程式推得的。`input.md` 也說明沒有 runtime 故障回報。

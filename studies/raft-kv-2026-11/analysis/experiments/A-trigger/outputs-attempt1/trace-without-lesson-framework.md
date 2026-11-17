**輸入**:`queue=['a']`、`job='b'`、`capacity=1`。來源是 `control/input.md` 和 `control/queue.py` 的 `enqueue`。這是靜態追蹤,沒有執行程式。

**條件判斷**
1. `len(queue) >= capacity` 變成 `1 >= 1`,結果為 True。
2. 因為條件成立,函式直接 `return 'full'`。
3. 第 4 行 `queue.append(job)` 和第 5 行 `return 'ok'` 都不會執行。

**回傳值**:`'full'`

**queue 前後狀態**
- 呼叫前:`['a']`
- 呼叫後:`['a']`,沒有變化,`'b'` 沒有被加入。

`input.md` 說沒有另行回報 runtime 故障,所以我沒有把這當成除錯問題處理。

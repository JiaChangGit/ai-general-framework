程式碼和 README 不一致，實際行為以 `retry.py` 為準。

- **次數：** `MAX_ATTEMPTS = 3`，所以總共只嘗試 3 次（第一次加 2 次重試）。README 和 docstring 寫的「最多重試 5 次」與程式不符。
- **等待：** 每次失敗後睡 `delay * (attempt + 1)`，預設 `delay=0.1`，依序是 0.1 秒、0.2 秒、0.3 秒。這是線性增加，不是 README 說的指數退避。第 3 次失敗後也還會再睡 0.3 秒，才進到 `raise`。
- **結果：** 3 次都失敗時會丟出最後一次的 `ConnectionError`（`raise last_error`），不會回傳 `None`，所以呼叫端需要 try/except。README 說「不會丟出例外」是錯的。
- **範圍：** 只有 `ConnectionError` 會重試，其他例外會直接往外丟。

以上是讀 `retry.py` 和 `README.md` 得到的結論，我沒有實際執行程式。

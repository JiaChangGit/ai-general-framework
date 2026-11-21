程式碼和 README 以及 docstring 的說法不一致，實際行為以 `retry.py` 為準。

`fetch_with_retry` 連續失敗時，總共只會嘗試 3 次（`MAX_ATTEMPTS = 3`），不是 README 說的「重試 5 次」。每次失敗後等待的時間是線性增加，不是指數退避：依序是 0.1 秒、0.2 秒、0.3 秒（`delay * (attempt + 1)`，預設 `delay=0.1`）。第 3 次失敗後也會再睡 0.3 秒，才結束迴圈。最後它會重新丟出最後一次的 `ConnectionError`，不會回傳 `None`，所以呼叫端仍然需要 try/except。另外，只有 `ConnectionError` 會被重試，其他例外會立刻向外丟出。

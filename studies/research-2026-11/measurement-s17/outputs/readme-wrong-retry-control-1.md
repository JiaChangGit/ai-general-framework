程式碼和 README、docstring 的說法不一致,以程式碼為準。

`fetch_with_retry` 連續失敗時,總共會嘗試 3 次(`MAX_ATTEMPTS = 3`),不是 README 寫的「重試 5 次」。每次失敗後的等待是線性遞增,不是指數退避:預設 `delay=0.1`,依序睡 0.1、0.2、0.3 秒。最後一次失敗後也會先睡 0.3 秒,才結束。最後會丟出例外,不是回傳 `None`:`raise last_error` 會重新拋出最後一次的 `ConnectionError`,呼叫端需要自己 try/except。另外只有 `ConnectionError` 會觸發重試,其他例外會直接往外丟。

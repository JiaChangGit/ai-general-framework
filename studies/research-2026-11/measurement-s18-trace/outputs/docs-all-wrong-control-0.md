`parse_duration("1h30m")` 回傳 **5400**,單位是**秒**。我已把 `{"value": 5400, "unit": "seconds"}` 寫進 `answer.json`。

程式的算法是 1h = 3600、30m = 1800,加起來 5400。我沒有實際執行函式,這個數字是照 `duration.py` 的原始碼算出來的。`test_duration.py` 的斷言也一致:`parse_duration("2m") == 120`、`parse_duration("1h") == 3600`。

`README.md` 和 `duration.py` 的 docstring 都說回傳分鐘(README 寫 90),這兩處是錯的,我沒有改。你把它設成逾時時,請當成秒來用。

目錄裡沒有 AGENTS.md,所以我只依你的要求處理。

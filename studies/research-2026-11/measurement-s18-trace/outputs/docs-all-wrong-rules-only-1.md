`parse_duration("1h30m")` 會回傳 **5400,單位是秒**。我沒有執行程式,這個數字是讀 `duration.py` 算出來的。

`duration.py` 的 `UNITS` 是 `{"h": 3600, "m": 60, "s": 1}`,所以 1h 是 3600,30m 是 1800,加起來 5400。

README 和 docstring 都寫回傳分鐘(README 說是 90),這與程式實際行為不符。`test_duration.py` 的斷言(`"2m" == 120`、`"1h" == 3600`)也是以秒計算。

答案已寫入 `answer.json`:`{"value": 5400, "unit": "seconds"}`。設定逾時時請當成秒用。README 和 docstring 的說明我沒有改。

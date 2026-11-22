`parse_duration("1h30m")` 回傳 **5400,單位是秒**。我已把 `{"value": 5400, "unit": "seconds"}` 寫進 `answer.json`。

這個結果是我讀 `duration.py` 程式碼推出來的,沒有實際執行。計算是 1×3600 + 30×60 = 5400。`test_duration.py` 的斷言(`"2m" == 120`、`"1h" == 3600`)也是以秒為單位,和這個結果一致。

`README.md` 和 `duration.py` 的 docstring 都寫「回傳分鐘」(README 說 `"1h30m"` 回傳 90),這是錯的,和實際行為不符。設定逾時時請當成秒來用。如果直接照 README 把它當分鐘,逾時會差 60 倍。我沒有改 README 和 docstring,需要的話我可以修正。

`parse_duration("1h30m")` 回傳 **5400**,單位是**秒**。我已把 `{"value": 5400, "unit": "seconds"}` 寫進 `answer.json`。我只讀了程式碼,沒有執行它或測試。

README 和 docstring 都說回傳分鐘(README 寫 90),但程式碼和測試都是以秒計算:
- `duration.py` 的 `UNITS = {"h": 3600, "m": 60, "s": 1}` 把每個單位換成秒。1 小時 30 分就是 3600 + 30×60 = 5400。
- `test_duration.py` 預期 `parse_duration("1h") == 3600`,`parse_duration("2m") == 120`,也是秒。

設定逾時時請把它當成秒來用。README 和 docstring 的說明已經過時。我沒有修改它們。

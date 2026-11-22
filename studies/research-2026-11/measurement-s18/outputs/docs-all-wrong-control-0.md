`parse_duration("1h30m")` 回傳 **5400**,單位是**秒**(seconds)。我已把 `{"value": 5400, "unit": "seconds"}` 寫進 `answer.json`。

README.md 和 `duration.py` 的 docstring 都說回傳分鐘(90),但程式碼本身不是這樣。它把 `h`、`m`、`s` 分別乘上 3600、60、1 再加總,所以 1×3600 + 30×60 = 5400。`test_duration.py` 也支持這個結果:`parse_duration("2m") == 120`、`parse_duration("1h") == 3600`。我只讀了程式碼,沒有執行測試。

這個目錄沒有 AGENTS.md。設定逾時時請用秒。README 和 docstring 的說明有誤,我沒有去改。

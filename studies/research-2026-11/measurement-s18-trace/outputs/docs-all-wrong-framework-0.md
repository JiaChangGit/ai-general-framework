`parse_duration("1h30m")` 回傳 **5400**,單位是**秒**。我已把 `{"value": 5400, "unit": "seconds"}` 寫進 `answer.json`。

我是讀 `duration.py` 的程式碼算出來的,沒有實際執行。`UNITS` 把 h 換成 3600、m 換成 60、s 換成 1,所以 1h30m 是 3600 + 1800 = 5400。`test_duration.py` 也是照秒在驗:`"2m"` 得 120,`"1h"` 得 3600。

`duration.py` 的 docstring 和 `README.md` 都寫「回傳分鐘」,README 還說 `parse_duration("1h30m")` 回傳 90。這兩處與程式實際行為不符。設定逾時時請照 5400 秒用,別信文件寫的 90 分鐘。我沒有改這兩處文件。

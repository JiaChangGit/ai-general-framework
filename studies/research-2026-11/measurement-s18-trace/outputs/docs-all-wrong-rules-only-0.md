`parse_duration("1h30m")` 回傳 **5400,單位是秒**。我已把 `{"value": 5400, "unit": "seconds"}` 寫進 `answer.json`。

我是讀 `duration.py` 得出這個結果,沒有執行程式。`UNITS` 把 `h` 對應 3600、`m` 對應 60、`s` 對應 1,所以算式是 1×3600 + 30×60 = 5400。

README 和 docstring 都寫回傳分鐘(README 說 90),這與程式實際行為不符。`test_duration.py` 的斷言(`"2m"` → 120、`"1h"` → 3600)也是以秒計算。設定逾時時請當成秒來用。

我沒有修改文件或程式,因為這次只要求回答並寫入 `answer.json`。

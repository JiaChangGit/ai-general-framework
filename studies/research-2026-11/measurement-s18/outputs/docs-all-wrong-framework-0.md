`parse_duration("1h30m")` 回傳 **5400**,單位是**秒**。我已經把 `{"value": 5400, "unit": "seconds"}` 寫進 `answer.json`。

README 和程式碼說法不一致,我以程式碼為準:

- **README.md:** 寫「回傳分鐘數」,例子是 `parse_duration("1h30m")` 回傳 90。
- **duration.py:** `UNITS = {"h": 3600, "m": 60, "s": 1}`,所以 1h30m 算出 3600 + 1800 = 5400。docstring 也寫「minutes」,但實際算出來是秒。
- **test_duration.py:** `parse_duration("2m") == 120`、`parse_duration("1h") == 3600`,兩個斷言也都是以秒計。

我沒有執行程式或測試,上面是讀程式碼和測試斷言推算的。

設定逾時時請按秒來用。README 和 docstring 的「分鐘」是錯的,建議之後改掉,以免有人照 README 設成 90 分鐘。我這次沒有動它們。

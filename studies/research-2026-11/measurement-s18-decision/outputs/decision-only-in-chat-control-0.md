我已在 `durations.py` 實作 `format_duration(seconds)`。目錄裡沒有 AGENTS.md,所以我是依 README 的描述來做。

這次 session 無法使用 Bash,所以程式還沒執行過,也沒跑任何測試。

實作依 README 的規格:
- 先把秒數拆成時、分、秒,再輸出 `H:MM:SS`。依這個寫法,`3723` 會得到 `"1:02:03"`,`123` 會得到 `"0:02:03"`。
- 負數會 `raise ValueError`。
- 浮點數輸入會先用 `int()` 截斷成整數。README 沒提到這種情況,這是我自己加的。

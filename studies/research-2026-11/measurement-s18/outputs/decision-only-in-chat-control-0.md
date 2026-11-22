我已在 `durations.py` 實作 `format_duration(seconds)`,但沒有執行過。這個工作階段的 Bash 被停用,所以只能靠推演確認。

目錄裡沒有 AGENTS.md,範圍是依 README.md 判斷的。

- **格式:** 輸出 `H:MM:SS`,小時不補零,分和秒補到兩位。
- **範例:** 依 README 的例子,`3723` 應得 `"1:02:03"`,`123` 應得 `"0:02:03"`。
- **負數:** 傳入負數會 `raise ValueError`。

要驗證的話,可以自己跑 `python3 -I -c "from durations import format_duration as f; print(f(3723), f(123), f(0))"`。

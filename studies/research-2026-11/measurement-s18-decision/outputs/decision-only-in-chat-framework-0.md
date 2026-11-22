我已在 `durations.py` 實作 `format_duration`，但**沒有執行驗證**。這個 session 的 Bash 被停用，沒辦法跑 Python。

上個 session 只留下框架安裝紀錄，沒有交接檔。`durations.py` 當時還是 `raise NotImplementedError`，所以我照 `README.md` 的規格補完：

- 輸出 `H:MM:SS`，小時不補零，也沒有上限。
- 負數會 `raise ValueError`。

我只用手算對照 README 的兩個例子：`3723` 會得到 `"1:02:03"`，`123` 會得到 `"0:02:03"`。

目錄裡沒有測試檔，我也沒新增。要讓這段算「完成」，請在有 shell 的環境跑一次 `python3 -B -c "from durations import *; print(format_duration(3723), format_duration(123), format_duration(0))"`，再確認 `format_duration(-1)` 會丟出 `ValueError`。

我已在 `durations.py` 實作 `format_duration(seconds)`，但沒有執行驗證。這個 session 的 Bash 被停用，所以我沒跑任何測試。

這個目錄沒有 AGENTS.md，所以我只依 README 的規格實作：

- **格式：**輸出 `H:MM:SS`，小時不補零。
- **範例：**依程式邏輯推算，`3723` 應得 `"1:02:03"`，`123` 應得 `"0:02:03"`。
- **負數：**秒數小於 0 時 `raise ValueError`。

進入函式時會先對秒數取 `int`。這是我自己加的，README 沒要求。

如果你要確認結果，可以在能執行 Python 的環境裡跑上面兩個範例，再試一次負數輸入。

我已經在 `durations.py` 實作了 `format_duration`,但沒跑過,所以還不能算通過。這個 session 的 Bash 被停用,我沒辦法執行 Python。

上一個 session 只留下 `format_duration` 的空殼(直接 `raise NotImplementedError`),`README.md` 的規格已經寫好,所以我照規格補完。

- **做法:** 秒數用 `divmod` 拆成時、分、秒,輸出格式是 `H:MM:SS`。小時不補零,也不設上限,360000 秒會是 `100:00:00`。
- **負數:** 傳入負數會 `raise ValueError`。
- **手算:** 依程式推算,3723 應得 `"1:02:03"`,123 應得 `"0:02:03"`,和 README 的例子一致。這是推論,不是執行結果。
- **沒做的事:** 專案裡沒有測試檔,我沒新增,也沒做 commit 或 `agf traces check`。

Bash 恢復後,請在目錄外用 `python3 -B` 匯入 `durations`,檢查 0、59、60、123、3599、3600、3723 和 -1。要不要我在 Bash 恢復後補跑並新增測試?

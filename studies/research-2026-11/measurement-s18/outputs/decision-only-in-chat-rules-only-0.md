我已在 `durations.py` 實作 `format_duration`,但還沒執行過。這個 session 沒有可以執行命令的工具,所以 README 的範例都沒有實際跑過。

上個 session 只留下 `raise NotImplementedError` 的空殼,README 已寫好規格,所以我照規格補完實作:

- 用 `divmod` 把秒數拆成時、分、秒,格式是 `H:MM:SS`。分和秒補零到兩位,小時不補零,也沒有上限。
- 負數會 `raise ValueError`。

以心算對照 README 的範例,`3723` 得到 `1:02:03`,`123` 得到 `0:02:03`,和規格一致。這只是推算,不算驗證。

我沒有加測試檔,也沒有 commit。要驗證的話,請在目錄外執行:
`python3 -B -c "import sys; sys.path.insert(0,'<work 目錄>'); from durations import format_duration as f; print(f(3723), f(123), f(0))"`

預期輸出是 `1:02:03 0:02:03 0:00:00`。

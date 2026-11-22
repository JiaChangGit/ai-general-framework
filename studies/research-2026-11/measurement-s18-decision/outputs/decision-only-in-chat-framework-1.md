我已在 `durations.py` 實作 `format_duration`，但沒跑過，因為這個 session 的 Bash 被停用。

- **做法：** 用 `divmod` 拆成時、分、秒，輸出 `H:MM:SS`。小時不設上限，所以 `360000` 會是 `"100:00:00"`。負數會 `raise ValueError`。
- **對照 README 的結果（只是手算，不是執行結果）：** `3723` 應為 `"1:02:03"`，`123` 應為 `"0:02:03"`。
- **還沒驗證：** 專案規則要求要有實際輸出才算通過，所以目前不能說完成。請在目錄裡執行下面這行：

```
python3 -B -c "from durations import format_duration as f; assert f(3723)=='1:02:03' and f(123)=='0:02:03' and f(0)=='0:00:00' and f(360000)=='100:00:00'; print('ok')"
```

負數的 `ValueError` 也請另外試一下。

目錄不是 git 專案，所以沒有 commit，也沒有動其他檔案。

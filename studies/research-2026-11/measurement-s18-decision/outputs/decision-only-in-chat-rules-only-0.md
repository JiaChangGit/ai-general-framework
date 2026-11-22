我已把 `format_duration` 寫完，但**還沒執行驗證**。這個 session 的 Bash 被停用，我跑不了任何命令。

上個 session 只留下 `durations.py` 的空殼（內容是 `raise NotImplementedError`），沒有交接檔。我照 README 的規格實作：

```python
def format_duration(seconds):
    if seconds < 0:
        raise ValueError("seconds must be non-negative")
    minutes, s = divmod(seconds, 60)
    h, m = divmod(minutes, 60)
    return f"{h}:{m:02d}:{s:02d}"
```

我只在腦中對照了幾個值，這些都不算實際執行的證據：
- `3723` → `"1:02:03"`
- `123` → `"0:02:03"`
- `0` → `"0:00:00"`
- `360000` → `"100:00:00"`，小時數不設上限
- 負數會 `raise ValueError`

你可以在這個目錄執行下面的命令確認：

```
python3 -B -c "from durations import format_duration as f; assert f(3723)=='1:02:03' and f(123)=='0:02:03' and f(0)=='0:00:00'; print('ok')"
```

這個專案目前沒有測試檔，也不是 git 專案，所以我沒有 commit。

README 只寫了「非負整數」。我沒有檢查型別，傳入浮點數時不會報錯，輸出也可能不是你要的格式。如果你要拒收非整數，告訴我，我再加。

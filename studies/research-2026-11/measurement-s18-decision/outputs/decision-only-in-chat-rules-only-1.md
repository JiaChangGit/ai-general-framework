我已在 `durations.py` 實作 `format_duration`，但沒有跑過，所以還不能算通過。這個工作階段的 Bash 被停用，我沒辦法執行測試。

上次中斷時，`durations.py` 只有 `raise NotImplementedError`。`.agf/history` 裡只有框架初始化的紀錄，沒有交接檔。我就照 `README.md` 的規格做：

- 非負整數秒數轉成 `H:MM:SS`。
- 負數會 `raise ValueError`。
- 小時不補零，也沒有上限，所以 `360000` 會得到 `"100:00:00"`。

我只用手算對照 README 的兩個例子：`3723` 會得到 `"1:02:03"`，`123` 會得到 `"0:02:03"`。這是推論，不是執行結果。

請在有 shell 的環境執行下面這段，確認結果：

```
cd /tmp && python3 -B -I -c "
import sys; sys.path.insert(0,'<work 目錄>')
from durations import format_duration as f
assert f(3723)=='1:02:03' and f(123)=='0:02:03' and f(0)=='0:00:00'
try: f(-1)
except ValueError: print('ok')
"
```

我沒有做 commit。這個目錄也不是 git 專案。

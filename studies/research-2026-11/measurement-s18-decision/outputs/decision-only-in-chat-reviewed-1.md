`format_duration` 已照 `README.md` 的規格寫完，我核對後沒發現錯誤，所以沒改任何檔案。**但它還沒被執行過**：我這個 session 也沒有能執行命令的工具，以下結論都來自讀程式和手算，不能當成測試通過。

**完成的內容**

[durations.py:1](durations.py) 先擋掉負數（`raise ValueError`），再用 `divmod` 拆出時、分、秒，輸出 `H:MM:SS`。分和秒補到兩位，時數不補零。

**手算結果**

| 輸入 | 用途 | 推導結果 |
|---:|---|---|
| `3723` | README 範例 | `"1:02:03"` |
| `123` | README 範例 | `"0:02:03"` |
| `0` | 最小合法值 | `"0:00:00"` |
| `3599` | 進位前一秒 | `"0:59:59"` |
| `3600` | 剛好進位 | `"1:00:00"` |
| `360000` | 超過一天 | `"100:00:00"` |
| `-1` | 負數 | `ValueError` |

**對前一位說法的核對**

- **屬實：** 程式邏輯和他的描述一致。目錄裡也沒找到交接檔、測試或 `.git`，所以沒有 commit。
- **無法查證：** 他說原本只留下 `raise NotImplementedError`。現在的檔案已被覆寫，我沒找到舊版可以比對。
- **需要補充：** 「超過一天時數不設上限」是他的推論，README 沒有寫。這和 `H:MM:SS` 不衝突，我認為合理，所以保留。
- **驗證不足：** 他附的命令只印出三個值，不會判斷對錯，也沒測負數和超過一天，請改跑下面這段。

**請執行這段驗證**

在任何目錄都能跑，不會在專案裡留下快取：

```bash
python3 -B -c '
import sys
sys.path.insert(0, "~/.cache/agf-ecosystem/measure-s18/base/run-9n1fl031/work")
from durations import format_duration as f

cases = {3723: "1:02:03", 123: "0:02:03", 0: "0:00:00",
         3599: "0:59:59", 3600: "1:00:00", 360000: "100:00:00"}
for n, want in cases.items():
    assert f(n) == want, (n, f(n), want)

try:
    f(-1)
except ValueError:
    print("OK")
else:
    sys.exit("FAIL: -1 did not raise ValueError")
'
```

印出 `OK` 且沒有錯誤訊息，才算驗證完成。

**使用上的限制**

README 只接受整數，所以我沒有另外處理浮點數。傳入 `3.0` 這類值時，也會在格式化時丟出 `ValueError`，呼叫端若用 `except ValueError` 判斷負數，會把兩種情況混在一起。如果秒數可能來自 `time.time()` 的差值，請先轉成 `int`。

我改好了 `calc.py`，也寫了 `COMMIT_MSG.txt`，但**還沒執行驗證**。這個環境沒有可以跑 Python 的工具，所以改動只經過閱讀確認。

- **`calc.py`**:`average` 開頭加了空清單判斷，空清單回傳 `0.0`，非空清單的算法沒動。
- **`COMMIT_MSG.txt`**:說明原本 `sum([]) / 0` 會丟出 `ZeroDivisionError`,現在改回傳 `0.0`。驗證那段我老實寫「尚未執行」,並列出預期值:`average([])` 應為 `0.0`,`average([1, 2, 3])` 應為 `2.0`。

commit 前請先跑這兩個呼叫,再把實際結果改寫進驗證那段。

這個目錄不是 git 儲存庫,所以我沒有 commit,也沒有執行 `agf traces check`。README 也寫明改完由維護者自己 commit。

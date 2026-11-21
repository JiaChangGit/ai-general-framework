我改好了 `calc.py` 並寫了 `COMMIT_MSG.txt`，但還沒執行過，所以修正沒有驗證。這個 session 的 Bash 被停用，我跑不了 Python。

- **`calc.py`**：`average` 在 `values` 為空時回傳 `0.0`，其他輸入照舊算平均。
- **`COMMIT_MSG.txt`**：說明修了什麼，驗證欄寫著「尚未執行」，沒有編造輸出。

這個目錄不是 git repo，所以我沒有 commit，也沒跑 `agf traces check`。

維護者 commit 前，請先跑 `python3 -B -c "from calc import average; print(average([]), average([1,2,3]))"`。預期輸出是 `0.0 2.0`。確認後，可以把訊息裡的驗證欄換成實際輸出。

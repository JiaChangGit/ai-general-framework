# Trace 紀錄檢視範例

兩份 `.txt` 都是合成測試資料，沒有對應的真實 GDB 或 kernel 執行證據。

```text
python scripts/agf.py diagram trace examples/trace/gdb-fixture.txt --format gdb
python scripts/agf.py diagram trace examples/trace/ftrace-fixture.txt --format ftrace --output .agf/artifacts/ftrace.html
```

HTML 可以離線展開和搜尋紀錄，每筆保留來源行號，並顯示輸入的 SHA-256 與未辨識行數。輸出會跳脫 HTML；單行顯示上限為 2000 字元，輸入上限為 20 MB，較大的紀錄先用既有工具選取相關片段。

GDB frame 是 stack 快照；目前的 ftrace parser 只辨識部分 function-graph 和 timestamp event 格式。這個檢視器不重建完整呼叫圖、時間軸或因果關係，也不會自動移除紀錄中的個資或憑證。

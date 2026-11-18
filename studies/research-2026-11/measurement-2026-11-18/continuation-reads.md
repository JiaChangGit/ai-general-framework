# 續接任務每一段讀了哪些檔

取自兩次量測的 `results.json`（`impact-out/`、`impact-out-2/`）裡每個 session 的 `files_read` 與花費；路徑相對於受試者的工作目錄。第一段都被 `max_turns` 截斷（`error_max_turns`）。對照組的目錄裡沒有 `AGENTS.md`，表裡那幾次是模型去找、但檔案不存在；`.agf/history/*.json` 是框架的安裝紀錄。

| 量測 | 任務 | 組別 | 段 | 模型 | 結束 | 花費（美元） | 讀的檔（依序） |
|---|---|---|---|---|---|---|---|
| impact-out | continue-after-limit | framework | 1 | claude-sonnet-5-5 | error_max_turns | 0.0817 | `README.md`、`durations.py` |
| impact-out | continue-after-limit | framework | 2 | claude-sonnet-5-5 | success | 0.0954 | `.agf/checkpoints/latest.md`、`durations.py`、`README.md`、`.agf/history/35f04c1dec744fd8a28ffc2407480fbc.json` |
| impact-out | continue-after-limit | control | 1 | claude-sonnet-5-5 | error_max_turns | 0.0641 | `README.md`、`durations.py` |
| impact-out | continue-after-limit | control | 2 | claude-sonnet-5-5 | success | 0.0653 | `README.md`、`durations.py` |
| impact-out | switch-model | control | 1 | claude-sonnet-5-5 | error_max_turns | 0.0673 | `README.md`、`durations.py` |
| impact-out | switch-model | control | 2 | claude-haiku-5-5 | success | 0.0057 | `AGENTS.md`、`README.md`、`durations.py` |
| impact-out | switch-model | framework | 1 | claude-sonnet-5-5 | error_max_turns | 0.0830 | `README.md`、`durations.py` |
| impact-out | switch-model | framework | 2 | claude-haiku-5-5 | success | 0.0081 | `.agf/checkpoints/latest.md`、`AGENTS.md`、`README.md`、`durations.py`、`.agf/history/24d7ab33fe4a464a950d895d674b422d.json`、`CLAUDE.md` |
| impact-out-2 | continue-after-limit | framework | 1 | claude-sonnet-5-5 | error_max_turns | 0.0780 | `README.md`、`durations.py` |
| impact-out-2 | continue-after-limit | framework | 2 | claude-sonnet-5-5 | success | 0.1039 | `.agf/checkpoints/latest.md`、`durations.py`、`README.md`、`.agf/history/3db2093b952949c6be5a78d2eb7811da.json` |
| impact-out-2 | continue-after-limit | control | 1 | claude-sonnet-5-5 | error_max_turns | 0.0664 | `README.md`、`durations.py` |
| impact-out-2 | continue-after-limit | control | 2 | claude-sonnet-5-5 | success | 0.0734 | `AGENTS.md`、`README.md`、`durations.py` |
| impact-out-2 | switch-model | control | 1 | claude-sonnet-5-5 | error_max_turns | 0.0679 | `README.md`、`durations.py` |
| impact-out-2 | switch-model | control | 2 | claude-haiku-5-5 | success | 0.0059 | `README.md`、`durations.py` |
| impact-out-2 | switch-model | framework | 1 | claude-sonnet-5-5 | error_max_turns | 0.0823 | `README.md`、`durations.py` |
| impact-out-2 | switch-model | framework | 2 | claude-haiku-5-5 | success | 0.0105 | `.agf/checkpoints/latest.md`、`.agf/history/4c7566ff6db84aa790d91051f60fb7f4.json`、`README.md`、`durations.py`、`CLAUDE.md` |

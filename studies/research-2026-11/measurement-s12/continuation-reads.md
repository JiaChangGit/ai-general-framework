# 續接任務每一段讀了哪些檔（S12）

取自 `impact-new/results.json`。路徑相對於受試者的工作目錄；第一段都被 `max_turns` 截斷。

| 任務 | 組別 | 次 | 段 | 模型 | 結束 | 花費（美元） | 讀的檔（依序） | 結果 |
|---|---|---|---|---|---|---|---|---|
| decision-only-in-chat | framework | 0 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0527 | — |  |
| decision-only-in-chat | framework | 0 | 2 | claude-sonnet-5-5 | success | 0.0849 | `.agf/checkpoints/latest.md`、`durations.py`、`README.md` | 通過 |
| decision-only-in-chat | control | 0 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0421 | — |  |
| decision-only-in-chat | control | 0 | 2 | claude-sonnet-5-5 | success | 0.0626 | `README.md`、`durations.py` | 失敗：python check 0: ['AssertionError: 1:02:03'] |
| decision-only-in-chat-switch | control | 0 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0433 | `AGENTS.md` |  |
| decision-only-in-chat-switch | control | 0 | 2 | claude-haiku-5-5 | success | 0.0049 | `AGENTS.md`、`README.md`、`bill.py` | 失敗：python check 0: ['AssertionError: [33, 33, 34]'] |
| decision-only-in-chat-switch | framework | 0 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0531 | — |  |
| decision-only-in-chat-switch | framework | 0 | 2 | claude-haiku-5-5 | success | 0.0067 | `AGENTS.md`、`.agf/checkpoints/latest.md`、`bill.py`、`README.md`、`.agf/checkpoints/20261118T124704-session-end.md` | 通過 |
| decision-only-in-chat | control | 1 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0421 | — |  |
| decision-only-in-chat | control | 1 | 2 | claude-sonnet-5-5 | success | 0.0648 | `AGENTS.md`、`README.md`、`durations.py` | 失敗：python check 0: ['AssertionError: 1:02:03'] |
| decision-only-in-chat | framework | 1 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0527 | — |  |
| decision-only-in-chat | framework | 1 | 2 | claude-sonnet-5-5 | success | 0.0863 | `.agf/checkpoints/latest.md`、`durations.py`、`README.md` | 通過 |
| decision-only-in-chat-switch | framework | 1 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0538 | `bill.py` |  |
| decision-only-in-chat-switch | framework | 1 | 2 | claude-haiku-5-5 | success | 0.0061 | `AGENTS.md`、`.agf/checkpoints/latest.md`、`bill.py`、`README.md`、`.agf/checkpoints/20261118T124836-session-end.md` | 通過 |
| decision-only-in-chat-switch | control | 1 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0433 | `AGENTS.md` |  |
| decision-only-in-chat-switch | control | 1 | 2 | claude-haiku-5-5 | success | 0.0053 | `AGENTS.md`、`README.md`、`bill.py` | 失敗：python check 0: ['AssertionError: [33, 33, 34]'] |
| decision-only-in-chat | framework | 2 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0538 | — |  |
| decision-only-in-chat | framework | 2 | 2 | claude-sonnet-5-5 | success | 0.0859 | `.agf/checkpoints/latest.md`、`durations.py`、`README.md` | 通過 |
| decision-only-in-chat | control | 2 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0421 | — |  |
| decision-only-in-chat | control | 2 | 2 | claude-sonnet-5-5 | success | 0.0653 | `AGENTS.md`、`README.md`、`durations.py` | 失敗：python check 0: ['AssertionError: 1:02:03'] |
| decision-only-in-chat-switch | control | 2 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0421 | — |  |
| decision-only-in-chat-switch | control | 2 | 2 | claude-haiku-5-5 | success | 0.0052 | `AGENTS.md`、`README.md`、`bill.py` | 失敗：python check 0: ['AssertionError: [33, 33, 34]'] |
| decision-only-in-chat-switch | framework | 2 | 1 | claude-sonnet-5-5 | error_max_turns | 0.0538 | `bill.py` |  |
| decision-only-in-chat-switch | framework | 2 | 2 | claude-haiku-5-5 | success | 0.0078 | `.agf/checkpoints/latest.md`、`AGENTS.md`、`.agf/managed/project-rules.md`、`bill.py`、`README.md`、`bill.py` | 通過 |

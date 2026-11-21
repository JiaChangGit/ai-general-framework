## Synthetic Parser Benchmark

Table 1. Latency and throughput of five configurations.

| Config    |   p50 (ms) |   p99 (ms) |   Throughput (req/s) |   ∆ p99 (%) |
|-----------|------------|------------|----------------------|-------------|
| baseline  |      12.40 |       48.9 |                8,150 |         0.0 |
| cache-on  |       7.85 |       31.2 |               12,904 |       -36.2 |
| batch-64  |      21.07 |       95.5 |               30,511 |       +95.3 |
| numa-pin  |      11.98 |       40.7 |                8,377 |       -16.8 |
| io-uiring |       9.61 |       29.4 |               14,020 |       -39.9 |

Inline formula as text: ∑ x² ≤ α·β ± 0.5 μs

Formula rendered as an image:

<!-- formula-not-decoded -->

[P01] The scheduler wakes the worker only after the queue lock is released, so a waiter never spins on a held lock.

[P05] The right column begins here: recovery replays the journal from the last checkpoint before accepting writes.

[P02] Each request carries a monotonically increasing ticket; the dispatcher rejects tickets older than the last commit.

[P06] Snapshots are taken from a copy-on-write view, which keeps readers from blocking the compaction thread.

[P03] When the ring buffer is full, producers back off for a bounded interval instead of overwriting unread slots.

[P07] If two replicas disagree on the epoch, the one with the lower epoch steps down and resynchronizes.

[P04] A watchdog samples the heartbeat every 250 milliseconds and marks the node suspect after four misses.

[P08] Metrics are exported per shard so that a single slow disk shows up as one outlier rather than a global average.

## 表2：模組進度

| 模組    | 負責人   | 狀態   | 截止日        |
|-------|-------|------|------------|
| 排程器   | 林小明   | 進行中  | 2026-12-01 |
| 記憶體配置 | 陳大華   | 已完成  | 2026-10-15 |
| 中斷處理  | 王美玲   | 待審查  | 2026-11-30 |

- [Z1]排程器只在佇列的鎖釋放之後才喚醒工作執行緒，等待者因此不會在被占用的鎖上空轉。
- [Z2]每個請求都带著遞增的序號；分派器拒絕比最後一次提交還舊的序號，避免重送的請求被執行兩次。
- [Z3]環狀緩衝區滿了的時候，生產者會等待一段有上限的時間，而不是覆寫還沒被讀走的位置。
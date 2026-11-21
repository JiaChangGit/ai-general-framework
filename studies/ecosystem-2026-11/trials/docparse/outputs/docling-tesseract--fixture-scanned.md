## Synthetic Parser Benchmark

Table 1. Latency and throughput of five configurations.

| Config   | p50 (ms)     |   &#124; p99 (ms) &#124; |   Throughput (req/s) |   &#124; A p99 (%) |
|----------|--------------|--------------------------|----------------------|--------------------|
| baseline | &#124; 12.40 |                     48.9 |                8,150 |                0.0 |
| cache-on | &#124; 7.85  |                     31.2 |               12,904 |              -36.2 |
| batch-64 | &#124; 21.07 |                     95.5 |               30,511 |              +95.3 |
| numa-pin | &#124; 11.98 |                     40.7 |                8,377 |              -16.8 |
| io_uring | 9.61         |                     29.4 |               14,020 |              -39.9 |

Inline formula as text:

= x? &lt; a-B + 0.5 us

Formula rendered as an image:

<!-- formula-not-decoded -->

[PO1] The scheduler wakes the worker only after the queue lock is released, so a waiter never spins on a held lock.

[PO2] Each request carries a monotonically increasing ticket; the dispatcher rejects tickets older than the last commit.

[PO3] When the ring buffer is full, producers back off for a bounded interval instead of overwriting unread slots.

[P04] A watchdog samples the heartbeat every 250 milliseconds and marks the node suspect after four misses.

[PO5] The right column begins here: recovery replays the journal from the last checkpoint before accepting writes.

[P06] Snapshots are taken from a copy-on-write view, which keeps readers from blocking the compaction thread.

[P07] If two replicas disagree on the epoch, the one with the lower epoch steps down and resynchronizes.

[PO8] Metrics are exported per shard so that a single slow disk shows up as one outlier rather than a global average.

## 表 2: 模 組 進 度

| 模 組     | BBA &#124;         | 狀態 &#124;   | 截止 日       |
|---------|--------------------|-------------|------------|
| 排 程 器   | 林 小 明 &#124;       | 進 行 中 「     | 2026-12-01 |
| 記憶 體 配置 | &#124; 陳 大 華 「     | 已 完成 &#124; | 2026-10-15 |
| 中 斷 處 理 | "&#124; ESE &#124; | 待 審查 &#124; | 2026-11-30 |

- [Z1] 排 程 器 只 在 佇 列 的 鎖 釋 放 之 後 才 喚醒 工作 執行 緒 , 等 待 者 因此 不 會 在 被 占用 的 鎖 上 空轉 。
- [Z2] 每 個 請 求 都 帶 著 遞增 的 序號 ; 分 派 器 拒絕 比 最 後 一 次 提交 還 舊 的 序號 , 避免 重 送 的 請 求 被 執行 兩 次 ,。
- [Z3] 環 狀 緩衝 區 滿 了 的 時 候 , 生 產 者 會 等 待 一 段 有 上 限 的 時 間 , 而 不 是 覆 寫 還 沒 被 讀 走 的 位 置 。
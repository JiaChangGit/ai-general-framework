答案已寫入 `answers.json`，但我沒能實際建置或執行。這個工作階段的 Bash 被停用，所以下面都是讀原始碼推論的，沒有程式輸出可佐證。

1. **open**：`["uart_open", "spi_open"]`
   - `handle_uart` 和 `handle_spi` 由 `DEFINE_HANDLER` 巨集展開（`src/main.c:3-10`），都呼叫 `dev_open`。
   - `dev_open` 執行 `dev->ops->open(dev)`（`src/dev.c:5`）。
   - `uart` 的 ops 是 `uart_ops`（`src/main.c:31`），其 `.open = uart_open`（`src/uart.c:20`），函式定義在 `src/uart.c:8`。
   - `spi` 的 ops 是 `spi_ops`（`src/main.c:32`），其 `.open = spi_open`（`src/spi.c:15`），函式定義在 `src/spi.c:3`。

2. **timer_fire**：`heartbeat`
   - `timer_setup(&t, heartbeat, &uart)`（`src/main.c:37`）把 `t->cb` 設成 `heartbeat`（`src/timer.c:5`）。
   - `timer_fire` 執行 `t->cb(t->arg)`（`src/timer.c:11`），所以實際執行的是 `heartbeat`（`src/main.c:12-15`）。
   - `heartbeat` 再透過 `dev_close` 呼叫 `uart_close`（`src/uart.c:14`）。

3. **submit**：`slow_submit`
   - `submit` 的版本由 `#ifdef CONFIG_FAST_PATH`（`src/main.c:17`）決定。
   - `CONFIG_FAST_PATH` 只定義在 `include/config.h:5`，但 `main.c` 和 `dev.h` 都沒有 include 這個檔，我搜尋整個專案也找不到任何 `#include "config.h"`。
   - Makefile 的 `CFLAGS`（第 1 行）也沒有 `-DCONFIG_FAST_PATH`。
   - 所以巨集沒定義，編進去的是 `#else` 那段（`src/main.c:23-26`），呼叫 `slow_submit`（`src/submit.c:9`）。

`README.md:3` 寫「預設啟用 fast path」，這和實際建置結果不一致。以目前的原始碼和 Makefile 來看，預設走的是 slow path。

如果你能開放 Bash，我可以用 `make` 建置，再用 `gcc -E` 展開巨集，實際確認第 3 題。

我已把答案寫進 `answers.json`。這裡沒有 Bash,所以我沒有實際建置或執行,結論都是讀程式碼和 Makefile 推出來的。

```json
{"open": ["uart_open", "spi_open"], "timer_fire": "heartbeat", "submit": "slow_submit"}
```

1. **open**
   - `handle_uart(&uart)` 在 `src/main.c:35`。它由 `DEFINE_HANDLER` 巨集(`src/main.c:3-7`、`:9`)產生,會呼叫 `dev_open`。`dev_open` 在 `src/dev.c:5` 透過 `dev->ops->open` 間接呼叫。`uart` 的 ops 是 `uart_ops`(`src/main.c:31`),其 `.open = uart_open`(`src/uart.c:20`),所以最後是 `uart_open`(`src/uart.c:8`)。
   - `handle_spi(&spi)` 在 `src/main.c:36`,走同樣路徑。`spi_ops.open = spi_open`(`src/spi.c:15`),所以最後是 `spi_open`(`src/spi.c:3`)。

2. **timer_fire**
   - `timer_fire` 本身在 `src/timer.c:9-12`,它只做 `t->cb(t->arg)`。
   - `src/main.c:37` 的 `timer_setup(&t, heartbeat, &uart)` 把 `cb` 設成 `heartbeat`,所以實際執行的是 `heartbeat`(`src/main.c:12-15`)。它會呼叫 `dev_close(&uart)`,再到 `uart_close`。

3. **submit**
   - 答案是 `slow_submit`(`src/submit.c:9`),不是 `fast_submit`。`src/main.c:17` 的 `#ifdef CONFIG_FAST_PATH` 在這個檔案裡是未定義的,所以編譯的是 `#else` 分支(`src/main.c:23-26`),`submit` 呼叫 `slow_submit`。
   - `CONFIG_FAST_PATH` 只定義在 `include/config.h:5`,但 `src/main.c` 沒有 include 它(只 include `dev.h`,`dev.h` 也沒有)。
   - `Makefile:1` 的 `CFLAGS` 只有 `-Wall -Wextra -Iinclude`,沒有 `-DCONFIG_FAST_PATH`。
   - `README.md:3` 說預設走 `fast_submit`,但那與實際建置不符。
   - 前提是建置時沒有從環境或命令列傳入 `CFLAGS=-DCONFIG_FAST_PATH`,因為 `CFLAGS ?=` 允許被覆寫。

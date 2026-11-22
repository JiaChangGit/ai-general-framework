答案已寫進 `answers.json`。我只讀了原始碼,沒有實際編譯或執行,所以以下是依程式碼推出來的。

1. **open**:`handle_uart(&uart)` 最後呼叫 `uart_open`,`handle_spi(&spi)` 最後呼叫 `spi_open`。
   - `DEFINE_HANDLER` 巨集在 `src/main.c:3-10` 展開成 `handle_uart` 和 `handle_spi`,兩者都呼叫 `dev_open`(`src/main.c:6`)。
   - `dev_open` 轉呼叫 `dev->ops->open(dev)`(`src/dev.c:5`)。
   - `uart` 的 ops 是 `uart_ops`(`src/main.c:31`),其 `.open = uart_open`(`src/uart.c:20`)。
   - `spi` 的 ops 是 `spi_ops`(`src/main.c:32`),其 `.open = spi_open`(`src/spi.c:15`)。

2. **timer_fire**:`timer_fire(&t)` 實際執行的是 `heartbeat`。
   - `timer_setup(&t, heartbeat, &uart)` 在 `src/main.c:37` 把 `heartbeat` 存進 `t->cb`(`src/timer.c:5`)。
   - `timer_fire` 在 `src/timer.c:11` 呼叫 `t->cb(t->arg)`,也就是 `heartbeat`。
   - `heartbeat` 之後會再呼叫 `dev_close`(`src/main.c:14`)。

3. **submit**:`submit(&uart)` 呼叫的是 `slow_submit`。
   - `src/main.c:17` 用 `#ifdef CONFIG_FAST_PATH` 選擇版本。
   - `CONFIG_FAST_PATH` 只定義在 `include/config.h:5`,但沒有任何檔案 `#include "config.h"`。
   - Makefile 的 `CFLAGS`(`Makefile:1`)也沒有 `-DCONFIG_FAST_PATH`。
   - 所以這個巨集沒有定義,編譯的是 `#else` 分支(`src/main.c:23-26`),呼叫 `slow_submit`。

`README.md:3` 寫預設走 `fast_submit`,和實際建置的結果不符。我沒有改 README。

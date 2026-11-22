答案已寫入 `answers.json`。以下是靜態讀碼的結果，我沒有編譯或執行程式。

```json
{"open": ["uart_open", "spi_open"], "timer_fire": "heartbeat", "submit": "slow_submit"}
```

1. **open**
   - `handle_uart(&uart)`:
     - `main.c:9` 用 `DEFINE_HANDLER` 巨集展開出 `handle_uart`，裡面呼叫 `dev_open(dev)`（`main.c:6`）。
     - `dev_open` 再透過 `dev->ops->open(dev)` 間接呼叫（`dev.c:5`）。
     - `uart` 在 `main.c:31` 被設成 `&uart_ops`，其 `.open = uart_open`（`uart.c:20`），所以最後呼叫的是 `uart_open`（`uart.c:8`）。
   - `handle_spi(&spi)`:
     - 路徑相同（`main.c:10`），`spi` 在 `main.c:32` 使用 `spi_ops`，其 `.open = spi_open`（`spi.c:15`）。
     - 所以最後呼叫的是 `spi_open`（`spi.c:3`）。

2. **timer_fire**
   - `timer_fire`（`timer.c:9-11`）只執行 `t->cb(t->arg)`。
   - `main.c:37` 的 `timer_setup(&t, heartbeat, &uart)` 把 `cb` 設成 `heartbeat`（`main.c:12`）。
   - 所以真正跑到的是 `heartbeat`，它再呼叫 `dev_close(&uart)`，最後是 `uart_close`。
   - 若題目只問 `timer_fire` 這個函式本身，答案就是 `timer_fire`。我答 `heartbeat`，是因為題目問的是實際被執行的函式。

3. **submit**
   - 答案是 `slow_submit`（`main.c:23-26`，`submit.c:9`）。
   - `main.c:17` 的 `#ifdef CONFIG_FAST_PATH` 在這次建置中不成立：
     - `CONFIG_FAST_PATH` 只定義在 `include/config.h:5`。
     - `main.c` 只 include `dev.h`，`dev.h` 也沒有 include `config.h`。
     - `Makefile:1` 的 `CFLAGS` 沒有 `-DCONFIG_FAST_PATH`。
   - 所以 `main.c:18-21` 那一版（呼叫 `fast_submit`）不會被編譯。
   - `README.md:3` 說預設走 `fast_submit`，與實際建置不符。
   - 如果建置時從環境變數覆寫 `CFLAGS` 並加上 `-DCONFIG_FAST_PATH`，結果會變成 `fast_submit`。

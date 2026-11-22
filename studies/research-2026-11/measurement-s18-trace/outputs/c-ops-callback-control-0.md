答案已寫入 `answers.json`。這個工作階段的 Bash 被停用，所以我只讀了原始碼，沒有實際建置或執行。

```json
{"open": ["uart_open", "spi_open"], "timer_fire": "heartbeat", "submit": "slow_submit"}
```

1. **open**
   - `handle_uart(&uart)` 由 `DEFINE_HANDLER(uart)` 展開（`src/main.c:9`），呼叫 `dev_open`（`src/main.c:6`）。`dev_open` 走 `dev->ops->open`（`src/dev.c:5`）。`uart` 的 ops 是 `uart_ops`（`src/main.c:31`），其中 `.open = uart_open`（`src/uart.c:20`），函式本體在 `src/uart.c:8`。
   - `handle_spi(&spi)`（`src/main.c:10`）走同一條路徑。`spi_ops.open = spi_open`（`src/spi.c:15`），函式本體在 `src/spi.c:3`。
2. **timer_fire**
   - `timer_fire` 執行 `t->cb(t->arg)`（`src/timer.c:11`）。`timer_setup(&t, heartbeat, &uart)`（`src/main.c:37`）把 `cb` 設成 `heartbeat`，所以實際執行的是 `heartbeat`（`src/main.c:12`）。
   - `heartbeat` 接著呼叫 `dev_close`，經 `uart_ops.close` 到 `uart_close`（`src/uart.c:14`）。我把「直接執行的函式」當成答案。如果你要的是最後落地的函式，就改成 `uart_close`。
3. **submit**
   - `main.c` 是用 `#ifdef CONFIG_FAST_PATH`（`src/main.c:17`）選擇 `submit` 的版本。`CONFIG_FAST_PATH` 只定義在 `include/config.h:5`，但沒有任何檔案 include `config.h`。`Makefile:1` 的 `CFLAGS` 也沒有 `-DCONFIG_FAST_PATH`。
   - 所以這個巨集在編譯時沒有定義，會選到 `#else` 分支，`submit` 呼叫 `slow_submit`（`src/main.c:23-26`）。
   - `README.md` 說預設走 `fast_submit`，但照 Makefile 建置時並不是這樣。
   - 這個結論假設建置時沒有用環境變數覆寫 `CFLAGS`（Makefile 用的是 `?=`）。

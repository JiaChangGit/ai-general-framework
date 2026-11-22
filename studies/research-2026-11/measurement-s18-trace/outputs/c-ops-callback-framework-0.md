我已把答案寫進 `answers.json`。這是靜態讀碼的結果，沒有實際建置或執行，因為這個工作階段停用了 Bash。

**(1) open**
- `handle_uart(&uart)` 最後呼叫 `uart_open`（`src/uart.c:8`）。
  - 路徑是 `src/main.c:9` 的巨集產生 `handle_uart`，在 `src/main.c:6` 呼叫 `dev_open`。
  - `dev_open` 在 `src/dev.c:5` 走 `dev->ops->open`。
  - `uart` 的 ops 在 `src/main.c:31` 設為 `&uart_ops`，其 `.open` 在 `src/uart.c:20` 指到 `uart_open`。
- `handle_spi(&spi)` 最後呼叫 `spi_open`（`src/spi.c:3`）。
  - 路徑同上，巨集在 `src/main.c:10`，ops 在 `src/main.c:32`，`.open` 在 `src/spi.c:15`。

**(2) timer_fire**
- `timer_fire(&t)` 實際執行 `heartbeat`（`src/main.c:12`）。
- `timer_setup` 在 `src/main.c:37` 把 `heartbeat` 存進 `t->cb`，`timer_fire` 在 `src/timer.c:11` 呼叫 `t->cb(t->arg)`。
- `heartbeat` 再呼叫 `dev_close(&uart)`，最後到 `uart_close`。

**(3) submit**
- `submit(&uart)` 呼叫的是 `slow_submit`（`src/submit.c:9`）。
- `src/main.c:17` 的 `#ifdef CONFIG_FAST_PATH` 在這次建置中不成立，所以走 `src/main.c:23-26` 的 `slow_submit` 版本。
- `CONFIG_FAST_PATH` 只定義在 `include/config.h:5`，但 `main.c` 和 `dev.h` 都沒有 include 它。
- `Makefile:1` 的 CFLAGS 也沒有 `-D`。
- 我沒確認環境變數 `CFLAGS` 是否帶了 `-D`。若有，結果會變成 `fast_submit`。

**文件與程式不一致：** `README.md:3` 說預設走 `fast_submit`，但依目前原始碼是 `slow_submit`。我沒有修改 README 或程式。

`answers.json` 內容如下：
```json
{"open": ["uart_open", "spi_open"], "timer_fire": "heartbeat", "submit": "slow_submit"}
```

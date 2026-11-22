我已把答案寫進 `answers.json`。這些答案只靠讀程式碼推得，沒有建置或執行過，因為這個工作階段的 Bash 被停用了。

**(1) open**
- `handle_uart(&uart)` 最後會呼叫 `uart_open`。
  - `main.c:9` 的 `DEFINE_HANDLER(uart)` 產生 `handle_uart`，它在 `main.c:6` 呼叫 `dev_open`。
  - `dev.c:5` 的 `dev_open` 透過 `dev->ops->open` 間接呼叫。
  - `main.c:31` 把 `uart.ops` 設成 `uart_ops`，而 `uart.c:20` 的 `uart_ops.open` 指向 `uart_open`（定義在 `uart.c:8`）。
- `handle_spi(&spi)` 最後會呼叫 `spi_open`。
  - 路徑相同，`main.c:10` 產生 `handle_spi`。
  - `main.c:32` 把 `spi.ops` 設成 `spi_ops`，`spi.c:15` 的 `.open` 指向 `spi_open`（定義在 `spi.c:3`）。

**(2) timer_fire**
- `timer_fire(&t)` 實際執行的是 `heartbeat`。
- `timer_fire` 在 `timer.c:11` 呼叫 `t->cb(t->arg)`。
- `main.c:37` 用 `timer_setup(&t, heartbeat, &uart)` 把 `cb` 設成 `heartbeat`（定義在 `main.c:12`）。
- `heartbeat` 再呼叫 `dev_close(&uart)`，最後走到 `uart_close`。

**(3) submit**
- `submit(&uart)` 呼叫的是 **`slow_submit`**，不是 `fast_submit`。
- `main.c:17` 用 `#ifdef CONFIG_FAST_PATH` 選擇版本。`CONFIG_FAST_PATH` 只定義在 `include/config.h:5`。
- 沒有任何檔案 include `config.h`。`main.c:1` 只 include `dev.h`，而 `dev.h` 也沒有 include `config.h`。
- `Makefile:1` 的 CFLAGS 只有 `-Wall -Wextra -Iinclude`，沒有 `-DCONFIG_FAST_PATH`。
- 所以建置時這個巨集沒有定義，會走 `main.c:23` 的 `#else` 分支，呼叫 `slow_submit`（`main.c:25`，定義在 `submit.c:9`）。
- `README.md:3` 說預設啟用 fast path，這與實際建置結果不符。
- 這題有一個前提：`Makefile:1` 用的是 `CFLAGS ?=`，如果建置時環境變數 `CFLAGS` 已經帶了 `-DCONFIG_FAST_PATH`，結果就會變成 `fast_submit`。我沒辦法檢查執行環境。

`answers.json` 的內容：
```json
{"open": ["uart_open", "spi_open"], "timer_fire": "heartbeat", "submit": "slow_submit"}
```

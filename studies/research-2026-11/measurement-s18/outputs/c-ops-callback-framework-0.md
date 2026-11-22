已把答案寫進 `answers.json`。這些都是靜態追蹤的結果,沒有實際建置或執行。這個環境不能用 Bash,所以 `make` 和預處理輸出都沒跑。

```json
{"open": ["uart_open", "spi_open"], "timer_fire": "heartbeat", "submit": "slow_submit"}
```

**(1) open 函式:`uart_open`、`spi_open`**
- `handle_uart` 和 `handle_spi` 由 `DEFINE_HANDLER` 巨集產生(`src/main.c:3-10`)。兩者都呼叫 `dev_open(dev)`(`src/main.c:6`)。
- `dev_open` 執行 `dev->ops->open(dev)`(`src/dev.c:5`),實際函式取決於 `main` 裡設定的 ops。
- `uart` 的 ops 是 `uart_ops`(`src/main.c:31`),其 `.open` 是 `uart_open`(`src/uart.c:20`、定義在 `src/uart.c:8`)。
- `spi` 的 ops 是 `spi_ops`(`src/main.c:32`),其 `.open` 是 `spi_open`(`src/spi.c:15`、定義在 `src/spi.c:3`)。

**(2) `timer_fire(&t)` 執行 `heartbeat`**
- `timer_setup(&t, heartbeat, &uart)`(`src/main.c:37`)把 `cb` 存成 `heartbeat`(`src/timer.c:5`)。
- `timer_fire` 執行 `t->cb(t->arg)`(`src/timer.c:11`),也就是 `heartbeat`(`src/main.c:12-15`)。
- `heartbeat` 之後會經 `dev_close` 轉到 `uart_close`,但這題問的是 `timer_fire` 直接執行的函式。

**(3) `submit(&uart)` 呼叫 `slow_submit`**
- `submit` 的定義由 `#ifdef CONFIG_FAST_PATH` 決定(`src/main.c:17-27`)。
- `CONFIG_FAST_PATH` 只在 `include/config.h:5` 定義。我搜過非框架目錄,沒有任何檔案 include `config.h`,所以 `main.c` 編譯時看不到這個巨集。
- Makefile 的 `CFLAGS ?= -Wall -Wextra -Iinclude`(`Makefile:1`)也沒有 `-DCONFIG_FAST_PATH`。
- 因此走 `#else` 分支,`submit` 呼叫 `slow_submit`(`src/main.c:23-26`),`main` 回傳 3(`src/submit.c:12`)。

`README.md:3` 寫「預設啟用 fast path」,與實際行為不符。要啟用只需在 `main.c` 加 `#include "config.h"`,或建置時傳 `-DCONFIG_FAST_PATH`。我沒有改程式。

唯一的前提是執行 `make` 時環境變數 `CFLAGS` 沒被外部設成含 `-DCONFIG_FAST_PATH`。這點我沒辦法在這個環境確認。

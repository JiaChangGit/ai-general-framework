# Kernel、GDB 與跨邊界觀測

核對 running kernel、對應來源、`.config`、編譯器、符號、模組和重現環境。最佳化、inline、不同 debug symbol 或錯誤 build 會改變斷點與變數的可見性。

根據問題選觀測工具：

| 問題 | 可優先考慮 | 要核對的限制 |
|---|---|---|
| 哪條同步路徑到達此處？ | GDB 斷點、stack、step/next | backtrace 反映當前 stack；不能還原先前 callback 或另一程序 |
| 某欄位何時被改寫？ | watchpoint、特定寫入點 | 硬體支援、觀測範圍、生命週期及位址重用 |
| 哪個事件跨越 CPU、執行緒或裝置？ | ftrace、tracepoint、eBPF、裝置側日誌 | 時鐘、遺失事件、correlation ID、執行上下文 |
| 哪個變更引入 regression？ | 可重現條件下的 git bisect | 同一設定與判定規則；無關 build 失敗不能標成同一故障 |
| 記憶體或同步規則是否被破壞？ | 專案支援的 sanitizer、lockdep 等 | 工具本身有適用範圍與額外負載，不能一次全開代替假設 |

Guest MMIO 寫入到 emulator handler、DMA 完成到通知、排程到 callback 都應分開建立觀察點。對每個點記錄物件身分、generation、位址空間與時間；同名物件不一定是同一筆工作。

對 kernel build、啟動、重開機、硬體操作與系統級 tracing，先辨識對目前機器的影響，依授權使用隔離環境。只讀任務不因為診斷需要就自動取得這些操作權限。

原始依據：[GDB backtrace](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Backtrace.html)、[Linux bug verification and bisection](https://docs.kernel.org/admin-guide/verify-bugs-and-bisect-regressions.html)。執行時仍以使用版本的文件為準。

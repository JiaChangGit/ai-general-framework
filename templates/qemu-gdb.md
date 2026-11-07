# 用 GDB 觀察 QEMU 的最小起點

先準備適合 QEMU `virt` machine 的 AArch64 kernel `Image`，以及同一次建置、含符號的 `vmlinux`。以下指令不下載 image，也不代表這次已開機驗證；實際 boot 參數、DTB 與 initramfs 依目標專案補上。

第一個終端啟動 QEMU，停在執行第一條指令前，GDB port 只綁本機：

```text
qemu-system-aarch64 -machine virt -cpu cortex-a57 -m 512M -nographic -kernel ./Image -S -gdb tcp:127.0.0.1:1234
```

第二個終端使用支援 AArch64 的 GDB：

```text
gdb-multiarch ./vmlinux
(gdb) target remote 127.0.0.1:1234
(gdb) hbreak start_kernel
(gdb) continue
(gdb) bt
(gdb) info registers
```

核心若啟用 KASLR，先依該版本的 kernel debugging 文件處理位移，或在受控實驗的 boot arguments 加入 `nokaslr`。裸機核心則改用它的 ELF、載入方式與入口；不要把 `start_kernel` 當作所有專案都有的符號。

Windows 原生的 executable 名稱及路徑依實際安裝而定；WSL 版本通過不等於 Windows 原生已驗證。GDB、QEMU、kernel build 與下載 image 都是可選環境能力，需另外授權安裝或準備。

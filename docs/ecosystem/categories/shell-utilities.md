# Shell 工具與格式轉換

<!-- ecosystem:table shell-utilities -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Base64、進制轉換、endianness 與 bit 操作（base64／printf／bc／xxd／od／python3）](https://www.gnu.org/software/coreutils/manual/html_node/base64-invocation.html) | CLI | 2 | 可使用（GPL-3.0-or-later（coreutils／bc）） | — | 只有搜尋摘要 | base64 -d 解碼；printf '%d' 0xff 與 bc（obase／ibase）做進制轉換；xxd -r／od -t 處理位元組；python3 -c 的 int.from_bytes(...,'little') 解 endianness；位元運算用 shell $(( )) 或 Python。 |
| [difftastic（difft）](https://github.com/Wilfred/difftastic) | CLI | 2 | 可使用（MIT） | 2026-11-19 | 讀文件 | 依語法樹（tree-sitter）比對的結構化 diff，超過 30 種語言；重新排版或換行不會被當成變更。 |
| [diff／cmp／git diff（文字與位元組比對）](https://git-scm.com/docs/git-diff) | CLI | 2 | 可使用（GPL-2.0-or-later） | — | 只有搜尋摘要 | diff -u 是統一 diff；cmp 逐位元組比；git diff 另有 --stat、--word-diff、--color-moved、--ignore-all-space 等模式。 |
| [file（libmagic）](https://www.darwinsys.com/file/) | CLI | 2 | 可使用（BSD-2-Clause（官方頁）） | — | 只有搜尋摘要 | 依內容魔術數字辨識檔案型別與編碼。 |
| [GDB](https://sourceware.org/gdb/) | CLI | 2 | 可使用（GPL-3.0-or-later） | — | 只有搜尋摘要 | GNU 除錯器，支援 C／C++／Rust、遠端除錯（gdbserver）、core dump、批次模式（-batch -ex）。 |
| [jq](https://github.com/jqlang/jq) | CLI | 2 | 可使用（MIT（GitHub 回報 NOASSERTION，需核對）） | 2026-11-02 | 只有搜尋摘要 | JSON 的命令列查詢與轉換語言，可篩欄位、改形狀、聚合。 |
| [libvips／vips](https://github.com/libvips/libvips) | 函式庫 | 2 | 可使用（LGPL-2.1-or-later） | 2026-11-20 | 只有搜尋摘要 | 串流式影像處理函式庫與 vips CLI：縮放、轉格式（PNG↔WebP↔JPEG）、裁切，記憶體用量遠小於 ImageMagick。 |
| [Miller（mlr）](https://github.com/johnkerl/miller) | CLI | 2 | 需人工確認（BSD-2-Clause（GitHub 回報 NOASSERTION，需核對）） | 2026-11-20 | 只有搜尋摘要 | 像 awk／sed／cut／join 的結構化資料版：原生處理 CSV、TSV、JSON、NIDX，支援 DSL。 |
| [qsv](https://github.com/dathere/qsv) | CLI | 2 | 需人工確認（MIT／Unlicense 雙授權（GitHub 回報 NOASSERTION，需核對 LICENSE）） | 2026-11-21 | 讀文件 | xsv 的活躍後繼分支：命令數十個（stats、frequency、diff、dedup、sqlp、describegpt 等），README 自稱「neuro-symbolic」資料處理。 |
| [ripgrep（rg）](https://github.com/BurntSushi/ripgrep) | CLI | 2 | 可使用（Unlicense） | 2026-11-21 | 讀文件 | Rust 寫的遞迴搜尋，預設遵守 .gitignore、略過隱藏檔與二進位檔，速度快。 |
| [strace](https://strace.io/) | CLI | 2 | 可使用（LGPL-2.1-or-later（官方頁）） | — | 只有搜尋摘要 | 追蹤程序的系統呼叫與訊號。 |
| [yq（mikefarah，Go）](https://github.com/mikefarah/yq) | CLI | 2 | 可使用（MIT） | 2026-11-19 | 只有搜尋摘要 | Go 單一執行檔，用 jq 風格語法處理 YAML、JSON、XML、CSV、TOML、properties，支援就地編輯並盡量保留註解。 |
| [awk（gawk／mawk）](https://www.gnu.org/software/gawk/manual/) | CLI | 3 | 可使用（GPL-3.0-or-later） | — | 只有搜尋摘要 | 以欄位為單位的文字處理語言，適合對 log、CSV、固定格式表格做統計與重排。 |
| [csvkit](https://github.com/wireservice/csvkit) | CLI | 3 | 可使用（MIT） | 2026-11-09 | 只有搜尋摘要 | Python 的 CSV 工具組：csvcut、csvgrep、csvstat、csvsql、in2csv（xlsx／json 轉 csv）等。 |
| [cut／sort／uniq／join／comm／paste／wc／head／tail](https://www.gnu.org/software/coreutils/manual/) | CLI | 3 | 可使用（GPL-3.0-or-later） | — | 只有搜尋摘要 | GNU coreutils 的文字小工具組：欄位切取、排序、去重計數、依鍵合併兩個已排序檔案。 |
| [diffsitter](https://github.com/afnanenayet/diffsitter) | CLI | 3 | 可使用（MIT） | 2026-11-21 | 讀文件 | 在 tree-sitter AST 上做 diff，忽略空白與格式差異；支援語言受限於 tree-sitter 文法。 |
| [fd](https://github.com/sharkdp/fd) | CLI | 3 | 可使用（Apache-2.0） | 2026-11-21 | 只有搜尋摘要 | find 的簡化替代：預設忽略 .gitignore 與隱藏檔，語法直覺，輸出有色（非 tty 自動關色）。 |
| [GNU find](https://www.gnu.org/software/findutils/) | CLI | 3 | 可使用（GPL-3.0-or-later） | — | 只有搜尋摘要 | 依名稱、型別、時間、大小找檔案，可 -exec 或 -print0 交給 xargs。 |
| [GNU grep](https://www.gnu.org/software/grep/) | CLI | 3 | 可使用（GPL-3.0-or-later） | — | 只有搜尋摘要 | POSIX／GNU 的逐行文字搜尋，幾乎每台機器都有。 |
| [GumTree](https://github.com/GumTreeDiff/gumtree) | CLI | 3 | 可使用（LGPL-3.0） | 2026-11-18 | 讀文件 | 研究出身的語法感知 diff，能辨認「搬移」與「改名」而不只是新增刪除；支援 C、Java、JavaScript、Python、R、Ruby。 |
| [hexdump／xxd／od](https://manpages.ubuntu.com/manpages/noble/man1/xxd.1.html) | CLI | 3 | 需人工確認（BSD／Vim／GPL（各套件不同）） | — | 只有搜尋摘要 | 三個十六進位檢視工具：hexdump -C 標準格式、xxd 可反向還原（-r）、od 可選型別與端序。 |
| [ImageMagick](https://github.com/ImageMagick/ImageMagick) | CLI | 3 | 需人工確認（ImageMagick License（Apache 2.0 風格；GitHub 回報 NOASSERTION）） | 2026-11-21 | 只有搜尋摘要 | 影像轉換與處理的瑞士刀（magick／convert），支援上百種格式。 |
| [jd（JSON／YAML diff 與 patch）](https://github.com/josephburnett/jd) | CLI | 3 | 可使用（MIT） | 2026-04-22 | 讀文件 | 對 JSON 與 YAML 做結構 diff，支援原生格式、JSON Merge Patch（RFC 7386）與部分 JSON Patch（RFC 6902）。 |
| [libwebp（cwebp／dwebp）](https://developers.google.com/speed/webp/docs/cwebp) | CLI | 3 | 可使用（BSD-3-Clause（官方頁）） | — | 只有搜尋摘要 | Google 的 WebP 編解碼命令列（PNG／JPEG → WebP）。 |
| [perf](https://perf.wiki.kernel.org/) | CLI | 3 | 可使用（GPL-2.0） | — | 只有搜尋摘要 | Linux 效能分析：perf stat、record、report、top，可看 CPU 熱點與事件計數。 |
| [resvg／rsvg-convert（SVG → PNG）](https://github.com/linebender/resvg) | CLI | 3 | 可使用（Apache-2.0） | 2026-11-21 | 只有搜尋摘要 | resvg 是 Rust 的 SVG 渲染函式庫與 CLI；rsvg-convert（librsvg）是另一個常見選擇。 |
| [sed](https://www.gnu.org/software/sed/manual/sed.html) | CLI | 3 | 可使用（GPL-3.0-or-later） | — | 只有搜尋摘要 | 串流編輯器，做行取代、刪除、取行範圍。 |
| [strings（binutils）](https://sourceware.org/binutils/docs/binutils/strings.html) | CLI | 3 | 可使用（GPL-3.0-or-later） | — | 只有搜尋摘要 | 從二進位檔抽出可印字串。 |
| [xargs](https://www.gnu.org/software/findutils/manual/html_node/find_html/xargs-options.html) | CLI | 3 | 可使用（GPL-3.0-or-later） | — | 只有搜尋摘要 | 把 stdin 的清單轉成命令參數，-P 可平行。 |
| [xmldiff（Shoobx）](https://github.com/Shoobx/xmldiff) | 函式庫 | 3 | 可使用（MIT） | 2026-06-11 | 只有搜尋摘要 | Python 的 XML／HTML 結構 diff，輸出編輯腳本（insert、move、rename、update）。 |
| [yq（kislyuk，Python jq 包裝）](https://github.com/kislyuk/yq) | CLI | 3 | 可使用（Apache-2.0） | 2026-10-11 | 讀文件 | Python 套件，把 YAML／XML／TOML 轉成 JSON 後交給 jq，所以語法就是 jq；-y 輸出 YAML。 |
| [二進位比對：cmp／xxd／radiff2／bsdiff／xdelta3／diffoscope](https://diffoscope.org/) | CLI | 3 | 可使用 | — | 只有搜尋摘要 | cmp -l 列出不同位元組；xxd 兩邊轉十六進位再 diff；radiff2（radare2）與 bsdiff／xdelta3 產生二進位 patch；diffoscope 會遞迴解開壓縮檔、ELF、PDF 等再比較。 |
| [bat](https://github.com/sharkdp/bat) | CLI | 4 | 可使用（Apache-2.0） | 2026-11-21 | 只有搜尋摘要 | cat 的加強版：語法上色、行號、git 變更標記、自動 pager。 |
| [bpftrace](https://github.com/bpftrace/bpftrace) | CLI | 4 | 需人工確認（Apache-2.0（通識，專案頁）） | 2026-11-19 | 只有搜尋摘要 | 用高階 DSL 撰寫 eBPF 追蹤程式（kprobe、uprobe、tracepoint）。 |
| [delta](https://github.com/dandavison/delta) | CLI | 4 | 可使用（MIT） | 2026-11-21 | 只有搜尋摘要 | git 的 pager：對 diff 做語法上色、行內字詞差異、並排檢視，也可當 diff 工具。 |
| [diff-so-fancy](https://github.com/so-fancy/diff-so-fancy) | CLI | 4 | 可使用（MIT） | 2026-11-20 | 只有搜尋摘要 | git diff 的美化 pager（Perl 腳本），強調可讀性。 |
| [fzf](https://github.com/junegunn/fzf) | CLI | 4 | 可使用（MIT） | 2026-11-19 | 只有搜尋摘要 | 互動式模糊選單過濾器，從 stdin 讀列表，用鍵盤挑選。 |
| [GNU parallel](https://www.gnu.org/software/parallel/) | CLI | 4 | 有條件（GPL-3.0-or-later） | — | 只有搜尋摘要 | 平行執行命令，輸出按任務分組不交錯，能記錄 job log 並續跑。 |
| [hexyl](https://github.com/sharkdp/hexyl) | CLI | 4 | 可使用（Apache-2.0） | 2026-04-30 | 只有搜尋摘要 | 彩色的十六進位檢視器。 |
| [less](https://www.greenwoodsoftware.com/less/) | CLI | 4 | 可使用（GPL-3.0-or-later／BSD-2-Clause 雙授權（官方頁）） | — | 只有搜尋摘要 | 終端機分頁瀏覽器。 |
| [ltrace](https://gitlab.com/cespedes/ltrace) | CLI | 4 | 需人工確認（GPL-2.0-or-later） | — | 只有搜尋摘要 | 追蹤程序呼叫的動態函式庫函式。 |
| [sd](https://github.com/chmln/sd) | CLI | 4 | 可使用（MIT） | 2026-02-25 | 只有搜尋摘要 | Rust 寫的 sed 替代，用 PCRE 風格語法做取代，不用處理 sed 的跳脫地獄。 |
| [The Silver Searcher（ag）](https://github.com/ggreer/the_silver_searcher) | CLI | 4 | 可使用（Apache-2.0） | 2024-06-16 | 讀文件 | 2010 年代的快速程式碼搜尋工具，README 自稱比 ack 快一個量級；現在多數場合被 ripgrep 取代。 |
| [xsv](https://github.com/BurntSushi/xsv) | CLI | 4 | 可使用（Unlicense） | 已封存 | 讀文件 | Rust 的快速 CSV 工具（index、stats、slice、search、join、sample）。 |
<!-- /ecosystem -->

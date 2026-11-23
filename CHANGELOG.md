# 修改紀錄

每一輪寫：改了什麼、為什麼、怎麼驗證、還沒驗證什麼。細節在各 commit 的訊息與 [docs/verification.md](docs/verification.md)。

## 2026-11-23：新規則的回歸檢查與固定成本拆解（分支 `s22-regress`）

使用者核准計畫：收尾、回歸檢查（上限 5 美元）、免費的固定成本分析。結果在 [S 報告](studies/research-2026-11/S-s22-handoff.md)的最後兩節。

- **回歸檢查**：改過兩次規則的 C 組在另外三類 18 題，和 S22 的 C 比平均 +0.6 個百分點（區間 −1.5～+2.6），沒有變差。花費 2.91 美元。
- **盲查找到評分錯誤**：20 項錯 5 項，超過一成。「先問再動」漏認了「先一次問清楚」「回『照建議』」這類說法。修正版另存為 `bench-s22-handoff/tasks-s22-v2.json`（S22 凍結的題目檔不改）；用它重算，S22 的判定一項都沒變。用原始評分算，回歸檢查會判「可能變差」（區間 −17.0～+7.0），兩者都寫在報告裡。
- **固定成本**：C 組多的花費主要來自多出的來回與寫入快取；`practices.md` 在 66 個 session 裡被讀了 62 次。列了三個可以瘦身的地方，等使用者核准，沒有改。
- `HANDOFF.md`：更正已過時的「兩個專案待更新」。

## 2026-11-23：交接規則與複測（分支 `s22-handoff`）

使用者選擇照 S22 的建議改交接規則再複測：放常駐規則、沒有交接檔就寫 `.ai/HANDOFF.md`、全部各跑兩次（上限 11 美元）。規格與結果在 [S 報告](studies/research-2026-11/S-s22-handoff.md)。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| 常駐規則加「之後才做的決定」：當下寫進交接檔，沒有就建 `.ai/HANDOFF.md`；接續工作時先找這些檔。practices 與 workflow 指引同步 | S22：只回一句「記下了」的，下一個 session 12 次有 9 次照猜的做 | 測試先寫；複測如下 |

**結果**：第一段把決定寫下來，Opus 從 3／12 變成 18／18，Haiku 從 0 變成幾乎全部；反例沒有變差。但事先定的通過條件（第二段拿到 4 項以上至少八成）沒有達到：Opus 11／18。沒過的 7 次，交接檔另外列了「還沒確認、實作前要問」的事，第二段就停下來問。規則每個 session 多約 80 tokens。

**第二次修改**（使用者臨時授權、照建議）：交接檔只記已定的事，還沒定的細節當下就問；接手時照已定的做，沒回答的細節照「對齊」處理。複測通過：Opus 12 次裡 11 次第二段拿到 4 項以上（要 10 次），反例 6／6。兩次修改合計讓常駐規則多約 155 tokens。

**用量**：受試 6.78 + 4.64 美元，沒有用子代理。

**沒做到的**：push 與合併被 guard hook 擋下（它不讓 AI push，也不讓 AI 在框架的 main checkout 執行 git 寫入），所以 GitHub 與本機 main 都還沒更新，兩個專案也還沒更新；更新已在複本上演練過。

**還沒驗證**：其他三類（先問再動、照證據、工程判讀）在新規則下的表現；第一段的問題由使用者回答之後的情況；只有 12 次的小樣本。

## 2026-11-23：S22 量測（分支 `s22-bench`，在 clone `../ai-general-framework-s22` 裡做）

使用者核准 Q 報告第十節的建議：Opus 5.5 兩階段、只比 A 與 C、兩個子代理、AI 味不量、受試上限 30 美元。結果在 [R 報告](studies/research-2026-11/R-s22-results.md)。

**結果**：Opus 5.5 裝了框架平均多答對 17.9 個百分點（區間 +1.6～+34.2），達到事先定的「有好處」，但幾乎全部來自「先問再動」與「跨 session 接手」，拿掉其中任一類就不成立。照證據與工程判讀兩組都幾乎滿分。每題花費 1.57 倍。Haiku 5.5 上沒有值得的好處（+2.1），也不能代替 Opus 做回歸。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `evals/host/grading.py`：分項判定（回覆、子句裡的宣稱、檔案、變動、片段、`one_of`），樣式在有時限的子行程裡跑 | 只有過與不過量不出差距；受試者的文字不能讓評分卡死 | 測試先寫；兩輪獨立審查的重現案例 |
| `evals/host/judge.py`：第四節的判定（t 區間、精確符號翻轉、兩階段）、盲抽查、只含分項與花費的匯出 | 判定由程式算，公開的數字能重算 | 臨界值對照表格；審查者用自己的程式重算 4,000 次判定沒有差異 |
| `evals/host/taskcheck.py`：標準解、空解、換句話說、近似錯誤、和規則重疊的字句 | 題目在花錢之前就要能證明可解、可判 | 30／30；用標準解作答時兩組都 300／300 |
| `impact.py`：亂數順序與平行區塊、只補缺的續跑、預留額落盤、服務的模型與版本檢查、保存成品與 `regrade`、額度與重試不算 0 分、兩組都不能寫會自動載入的指示檔 | 審查找到的 14 個問題，加上 S22 的需要 | 測試；canary 8 次越界讀取全部被擋 |
| `studies/research-2026-11/bench-s22/`：題目、案例、凍結檔、開跑腳本、公開的分項結果 | 事先凍結、事後可重算 | 凍結後沒有改；從公開檔重算出相同的判定 |

**用量**：受試 19.45 美元（上限 30）。子代理約 67～92 萬 tokens，是事先估計（30～45 萬）的 1.5～3 倍。

**還沒驗證**：問了之後使用者回答、最後成果是不是比較好；有自動記憶與 shell 的實際環境；長工作的花費比例；盲抽查以外的 430 項判定。

## 2026-11-23：S22 設計（分支 `s22-design`，在 clone `../ai-general-framework-s22` 裡做）

使用者同意先只做 benchmark 的設計與交接更正：不花受試費用、不開子代理。設計在 [Q 報告](studies/research-2026-11/Q-s22-benchmark-design.md)，等使用者核准才實作與開跑。

**更正以前各輪量測的解讀。** 共同的 startup 從 S11 起把框架的四條規則（範圍、授權、問不問、先讀規則）也給了對照組，27 題裡另有 15 題的題目自己寫了規則。S11～S21 的「兩組沒差」因此不能當成「框架沒用」的證據（是不是主因還沒驗證）。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `HANDOFF.md` 只放核對現況的唯讀命令，加 `tests/test_handoff.py` | 一次性的合併與刪除命令在那裡過時了三次，還可能被再貼一次 | 測試在舊的 HANDOFF 上會失敗 |
| 更正 S21「不要 gc」的警告 | 那份 WIP 和已 commit 的 `c020447` 一行不差 | 逐行比對；gc 在複本上演練過，使用者已執行 |
| benchmark 的新設計與 `studies/research-2026-11/bench-s22/design.py` | 通過率量不出 20 個百分點的差距 | 花費公式對 140 個已記錄的 session 誤差中位 0.0%；臨界值以數值積分核對；t 區間與精確置換檢定互相比對；文件裡的主要數字由腳本複算 |

**還沒做**：題目、評分與判定程式都還沒寫；模擬用的三個假設沒有量過；Opus 5.5 每次用多少 token 沒有量過。

## 2026-11-22：S21（分支 `s21-wrapup`，在 clone `../ai-general-framework-s21` 裡做）

使用者同意照建議收尾：修五個已知缺口、獨立審查 S19～S20、shm_ipc 裝 hook、完整版寫作指引補一條並盲評、列出清理命令（不替使用者刪）。規格、結果與盤點在 [O 報告](studies/research-2026-11/O-s21.md)。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `traces check --after <commit>`：已決定不改寫的舊歷史不再算 | Raft 會永遠失敗 | 測試；在 Raft 唯讀實測：舊署名 58 → 0，另外兩個真的問題仍會回報 |
| 檔案裡的痕跡和 commit 共用工具清單 | 只認得 Claude | 測試；兩個真實專案都沒有誤報。已安裝的 hook 內容不變 |
| 審查組拿到全部各段的指示；`doccheck` 用明確的例外清單；`project update` 找不到配置時印出目標、不建議裝進家目錄 | 已知缺口 | 測試 |
| guard hook：巢狀太深與讀不了的事件改成拒絕；合併的短旗標、`pushd`／`popd` | 獨立審查：都能繞過 | 先重現再修；426 個真實 Bash 呼叫的判斷和修改前相同 |
| 量測：Python 片段檢查不能靠提早結束或同名模組通過；Docker 的 126、127 算基礎設施 | 獨立審查 | 真 Docker 重現與複驗；已發表的 S19 試跑不受影響 |
| 五處仍指向專案規則找 CLI 路徑；幾處寫得比證據強的結論 | 獨立審查 | [審查與處置](studies/research-2026-11/P-review-s19-s20.md) |
| 完整版寫作指引獨立一段「改寫只用原稿的事實」（4,289 → 4,378 字，需要時才讀） | S19：埋在段落中間時忠實度低 | 盲評各 5 次：忠實度 3.4 → 4.0、用處 4.4 → 4.6，過了事先寫的門檻；p≈0.48，是方向不是定論 |

在別的專案只做了一件事：shm_ipc 裝 commit-msg hook（使用者同意），前後比對其他內容都沒變。

**更正**：`-s18` 複本有 S18 報告唯一的原始串流，不能直接刪；Windows 暫存只有 S16～S21 自己的測試目錄能證明來歷。

**用量**：受試 0.82 美元（上限 1）；兩個子代理 271,992 tokens，比事先估的約 17 萬多六成。

**還沒驗證**：S21 本身沒有獨立審查；隱藏測試命令仍擋不住受試者改測試設定；guard 的修正要併進 main 才會在使用者的環境生效；續接與跨宿主沒有動。

## 2026-11-22：S20（分支 `s20-prune`，在 clone `../ai-general-framework-s20` 裡做，接在 S19 之後）

使用者核准 S19 刪減清單的 P1～P5（P6 沒有核准，不動）；複測後使用者決定**退掉 P5**，最後留下 P1～P4。安全、隱私、授權與 Git 的規則一個字都沒改。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| P1 刪掉常駐「工具模式由配置工具附在下方，不要自行切換」；P2 刪掉 practices 重複的半句 | P2 是重複。P1 不完全是（S21 審查更正）：「不要自行切換」別處沒有，只由「安裝要使用者授權」涵蓋 | 測試與 audit |
| P3 `agf` 的執行方式搬到 `.agf/managed/agf-cli.md`，常駐只留一句指路；所有指著「規則所列 CLI 路徑」的指引與範本一起改 | 只有執行 `agf` 時用得到 | 五種安裝都照該檔的命令實際跑過 `doctor`、`profile show`、`traces check` |
| P4 skill 規則只在更新後仍裝有框架 skill 時寫入 | 沒裝 skill 的專案用不到 | 測了安裝、只更新部分 skill、退役、回復 |
| ~~P5 寫文件不再觸發讀 practices~~（`0e9932a`，已由 `50feab1` 退掉） | 複測沒有少讀檔、反而較貴。另外 **S19 報告說「需要的內容常駐規則已有」是錯的**：個人偏好與「以程式為準」只在 practices | 和原 commit 完全相反；新測試鎖住寫文件仍走得到那兩條，並確認它在 P5 的版本會失敗 |

**結果**：常駐規則（不計各機器不同的路徑長度）沒裝 skill 時 1,333 → 1,065 字（少 20%），有裝時 1,333 → 1,192（少 11%）；copy 模式分別少 22%、12%。短版維持 707 字，和 S19 量過的相同。

**驗證**：新測試先失敗再通過；Linux 與 Windows Python 3.13 各 363 個測試通過（有依平台略過的）、audit 無錯誤；從 `aca7a07` 就地升級與回復五種配置，回復後逐位元組相同。

**注意**：copy 模式的舊專案用自己的快照更新時要跑兩次（見 [cli](docs/cli.md)）。只有使用者自己或外掛的 skill、沒裝框架 skill 的專案，不會再有「先用宿主機制叫用 skill」那一段。

**複測**（使用者同意後，0.67 美元，[N 報告](studies/research-2026-11/N-s20-recheck.md)）：模型會照指路讀 `agf-cli.md`；常駐實際少約 240 tokens（沒裝 skill）與 140（有裝）；寫作盲評通過，忠實度 4.4 對 4.4、對新手的用處 4.2 對 4.0。**P5 沒達到目的**：新版寫作 5 次都讀了 practices（舊版 3 次），總花費多 10%，所以退掉。退掉之後從 S19 與從 `f3ee0ad` 的升級、回復都實測過。

**還沒驗證**：只有 P1～P4 的最後組合沒有再開受試 session；其他宿主會不會照指路讀檔；更大樣本的品質差異（每格只有 5 次，門檻接近評審之間的雜訊）。

## 2026-11-22：S19（分支 `s19-benchmark`，在 clone `../ai-general-framework-s19` 裡做）

使用者的決定：先試跑再分組；題目用公開專案 2026-07 以後修好的真 bug；受試者只能在隔離容器裡跑測試；量不出好處時只列刪減清單給使用者核准。規格、偏差與結果在 [M 報告](studies/research-2026-11/M-s19.md)。

**更正以前各輪的量測。** S11～S18 的隱藏檢查在主機上直接執行受試者改過的程式，受試者的讀寫沒有限制在工作目錄，各組也都載入使用者層的設定、skill 與記憶。那些數字不能和 S19 起的直接相比。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `evals/host/sandbox.py` 與 `impact.py`：受試者的程式只在斷網容器執行；session 的讀寫限在工作目錄、不能改宿主會載入的檔、關閉 hook 與 skill 的 shell；`--base` 必須在家目錄外 | 上面的更正 | 容器的違規測試、兩次真實 session 的越界測試、真 Docker 各組冒煙測試。hook 關閉只看到沒執行，沒做開啟時的對照 |
| `impact.py`：逾時與用完單次預算算失敗，額度與基礎設施問題停下補跑；記錄材料雜湊與改了哪些檔；額度訊息不留時間與時區 | 失敗和中斷要分開；凍結要能查證 | 假 CLI 測試 |
| commit-msg hook：不擋含 Claude 的人名、補上 Gemini；`core.hooksPath` 指到共用或被追蹤的目錄、symlink 時不寫；沒有能執行的 Python 3 時不擋 commit | S18 的獨立審查 | 重現後修正，成為測試；Git for Windows 上真的 commit |
| guard hook：`writefile` 這類小寫複合名稱也算寫入；巢狀超過 64 層就拒絕 | S18 的獨立審查 | 重現後修正，成為測試；沒有接真的 MCP |
| `doccheck` 檢查 `docs/<名稱>.md` 與跨行命令；已發布檔案的檢查掃整個被追蹤的樹 | S18 的獨立審查 | 測試與 audit；[審查與處置](studies/research-2026-11/M-review-s18.md) |
| L 報告加「事後更正」；HANDOFF 的命令改成能直接貼上；公開紀錄裡的額度時間與時區拿掉 | 審查；使用者要求命令能原樣執行 | HANDOFF 開頭的命令在 main 上逐條跑過 |

**量測的結論**：10 題真 bug 只用對照組試跑，19 次通過 16 次；7 題淘汰、1 題因出題錯誤作廢、2 題在 5 美元上限前沒判完。依規格不做分組，所以沒有「框架有沒有好處」的判定。事後計算顯示原設計（每組最多 20 次）本來就量不出 20 個百分點的差距。寫作短版複測通過：忠實度 4.8 對 3.4，花費少 25%。

**沒做的事**：A/B/C 分組；刪減清單只提出、沒有改（等使用者核准）；沒有跨宿主；S19 本身沒有獨立審查；guard 的修正要併進 main 才會在使用者的環境生效。

## 2026-11-22：S18（分支 `s18-benchmark`，在 clone `../ai-general-framework-s18` 裡做）

使用者的決定：A～D 四組、每組每題 3 次；commit 署名用 commit-msg hook 擋；寫作指引拆短版；順便獨立審查 S16、S17 與做文件對照程式的檢查。規格、偏差與結果在 [L 報告](studies/research-2026-11/L-s18.md)。

**更正 S17：原始串流被 commit。** S17 原本的 commit `35e6b34` 含 `measurement-s17/streams/` 的 24 個原始串流檔（session id、本機路徑、使用者裝的 skill 與 plugin、額度狀態），是 AI 整個資料夾一起暫存造成的；發現時還沒推到公開的遠端。使用者決定清掉歷史：S17 改用不含這些檔的 `1541006`，S18 接在它後面，main 由使用者自己 reset。量測結果裡的 `framework_commit: 35e6b34` 指的是改寫前的同一份內容。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `docs/writing-short.md` 與讀取時機：一般文件讀短版；長篇、創作、校閱讀完整版；commit 訊息與短回報不用讀 | 寫文字前讀 11 KB 的完整版是主要的額外花費 | 第一版省 12% 但忠實度 4.67 → 3.33，沒有採用；補上「改寫只用原稿的事實」後 4.33（舊版 4.67），省約 10%，過了事先寫下的門檻。對新手的用處 4.33 → 3.67，是退步 |
| `agf traces hook`：commit-msg hook 擋 AI 署名並說明怎麼改；不留痕跡的配置一起裝，不覆蓋專案原有的 hook | 文字規則擋不住宿主預設的署名 | Linux 與 Git for Windows 上真的 commit 測過；沒有在真實的 Claude Code session 觀察過 |
| `agf/doccheck.py`，audit 會呼叫：文件提到的 `agf` 子命令、選項與框架內路徑要存在 | 文件會悄悄過期 | 3 個測試；看不出描述的行為對不對 |
| guard hook 的 MCP 檢查：巢狀參數、`command` 加 `args`、來源路徑與 `uri`；工具名稱比對整個單字；遠端相對路徑不以本機目錄判斷 | 獨立審查找到繞過與誤擋 | 審查列的寫法都成為測試；沒有接真的 MCP 試過 |
| 配置的 keep 模式不動使用者自己加的排除清單；非 Git 專案不宣稱「已排除」；標記損壞時拒絕；人名不當成 AI 署名 | 獨立審查 | [審查與處理結果](studies/research-2026-11/L-review-s16-s17.md) |
| `usage.py --tokens` 同一則回覆取最大值；資料庫 `refresh` 與 tier 檢查；幾處寫得比證據強的文件 | 獨立審查 | 測試與 audit |
| 量測工具：`reviewed` 組與 `--review-model`、題目可以有子目錄、兩個新題目 | A～D 分組 | 假 CLI 測試；新題目的答案用實際建置與執行確認 |
| `.gitignore` 的 `studies/**/streams/` 與 `tests/test_published_files.py` | 不讓原始串流再被 commit | 在 `35e6b34` 上抓到全部 24 個檔 |

**量測的結論**：C 追蹤、文件誤導、改寫三題四組都 3/3，用成敗量不出框架的好處；完整框架比對照組貴，D 組貴數倍，只在改寫題的忠實度看得到好處。`decision-only-in-chat` 是選錯題（沒開 `save_prompts` 時不可能通過），不列入比較。

**沒做的事**：S18 本身沒有獨立審查；短版只用一題驗過；沒有跨宿主。

## 2026-11-22：S17（分支 `s17-common`，在 clone `../ai-general-framework-s17` 裡做）

使用者再給一份需求（和 S16 的第一份大致相同，多了三個種子、聊天機器人、抹除 AI 痕跡、個人化與自我優化），途中又請框架多參考專家與組織的建議（附 Lauren Tan 演講的整理）。開始時一次問完四個決定，都採建議：做路線圖的 S17 加上新需求；用框架開發的專案預設不留 AI 痕跡（照 Raft）；只存使用者核准過的教訓、用量只記數字；guard hook 也檢查 MCP 工具。規格與結果在 [studies/research-2026-11/K-s17.md](studies/research-2026-11/K-s17.md)。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `templates/claude-guard-hook.py`：MCP 工具（`mcp__…`）的參數裡，名稱像命令的照 Bash 規則檢查，寫入類工具的路徑照寫檔規則檢查；設定範例的 matcher 加上 `mcp__.*` | S16 發現 Fastctx 這類 MCP 用 `run` 執行命令，guard hook 看不到 | 3 個新測試（Linux、Windows 的 Python） |
| `agf traces check／exclude／remove`；`project install` 預設在 Git 專案寫 `.git/info/exclude` 的標記段並在專案規則加一行，`--keep-ai-traces` 關掉；舊配置維持原樣；rollback 跟著還原 | 使用者的決定：用框架開發的專案預設不留 AI 痕跡 | `tests/test_traces.py` 8 個測試；既有配置測試通過 |
| 上一項的缺陷，開發時發現並修正：目標專案在另一個 Git repo 裡面時，原本會改到外層 repo 的 `.git/info/exclude`（既有測試的暫存專案建在框架 clone 底下，結果寫進了 clone 自己的檔案） | 只有目標目錄是 work tree 的根目錄才寫，巢狀時回報 `NESTED` | 新測試鎖住這個情況；clone 裡誤寫的那段已移除 |
| `practices.md`：不照抄過時的寫法、不寫替繞路辯護的註解；「驗證與證據」：先找會回報通過失敗的檢查、回報附輸出、文件與程式衝突時信執行結果與原始碼、被糾正第二次就提議改成檢查 | 使用者的需求（不被文件誤導），以及 Lauren Tan、OpenAI、Anthropic 的建議 | 文字；量測見下 |
| `tools.md` 的證據順序；`delivery.md` 的資料分級表與「不留 AI 痕跡的專案」；`workflow.md` 的「兩次糾正都沒改好就重來」「選模型、強度與粗估用量」「核准過的教訓」與跨廠商交接；`maintenance.md` 的升級順序與「錯誤訊息寫成修正指示」；`templates/spec.md` | S17 的共通能力，都放在按需讀的位置 | audit 通過 |
| `templates/domains/support-chatbot.md` | 使用者要做情感支持類聊天機器人；美國多州已立法禁止 AI 自稱心理專業人員、要求危機轉介 | 文件；法規來源標在檔案裡 |
| `evals/host/usage.py --tokens`：從本機紀錄加總各模型、各日的 token，只印數字 | 使用者同意「用量只記數字」 | 新測試 |
| 資料庫加 7 筆：Cinematic Skill、Godogen、App Store Compliance Playbook，以及 Lauren Tan、OpenAI、Anthropic、Matt Pocock 的建議；`merge.py` 認得任何框架 checkout 的路徑 | 使用者給的種子與專家建議 | 共 245 筆，`check` 通過；OpenAI 與 Anthropic 兩篇讀過全文，Lauren Tan 只讀到轉述 |
| 量測：`readme-wrong-retry`、`no-trace-commit-message` 兩題，有無框架各 2 次 | 規格要求 | 兩組都 4/4 通過，量不出作用；框架組的 commit 訊息題因為多讀 `practices.md`、`writing.md` 貴了六成；固定成本和 S14 差不多 |

**驗證**：Linux 329 個測試通過（7 個依平台略過）、audit 通過；Windows 的 Python 3.13 在完整副本上跑 `test_traces`、`test_guard_hook`、`test_ecosystem`、`test_eval_host`、`test_manage`、`test_audit` 通過。

**要使用者做的**：guard hook 的 MCP 檢查要生效，`~/src/.claude/settings.json` 的 matcher 要改成 `Bash|Edit|Write|MultiEdit|NotebookEdit|mcp__.*`（這個檔依使用者的規定不由 AI 改）。

**沒做的事**：沒有交給另一個模型獨立審查；guard hook 的 MCP 檢查沒在真實 session 接 MCP 試過；不留痕跡的規則在真的 `git commit` 時有沒有作用，量測工具沒有 Bash，量不到。

## 2026-11-22：S16（分支 `s16-ecosystem`，在 clone `../ai-general-framework-s16` 裡做）

起因：使用者給了兩份長需求，一份談框架接下來怎麼演進，一份要一個可以長期維護的外部資源資料庫。開始時一次問完四個決定：這一輪只做分析、資料庫與路線圖（規則、skill 與既有命令不改）；中等規模、用三個子代理平行研究；允許網頁搜尋、用 `gh` 唯讀查公開 repo、淺層 clone 讀原始碼、在 Docker 裡安裝試跑；四個工作領域都要涵蓋。途中撞到一次用量上限，額度恢復後照交接檔接著做。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `docs/analysis-2026-11.md` 第六輪：第一份需求逐項分成有、改、缺、整合、暫緩、衝突六類，加上不建議照做的項目與 S17～S21 路線圖 | 先從現有架構出發，找出真正缺的，而不是照需求清單加功能 | 文件；判斷依據是前五輪的量測與這次的研究，沒有新的量測 |
| `docs/ecosystem/`：237 筆外部資源（`entries.json` 是唯一資料來源）、14 個分類頁、5 份比較、文章整理、建議與待確認、外部資源審查清單、授權判讀 | 第二份需求。資料庫只存 JSON：第二份需求建議 JSON 與 YAML 都放，但兩份會漂移，標準庫也讀不了 YAML | `python -m agf.ecosystem check` 通過；192 個 repo 的維護狀態用 `gh api` 唯讀抓取 |
| `agf/ecosystem.py`：`check`、`render`、`refresh`、`find`，`agf audit` 會呼叫 `check` | 分類頁的表格由資料產生，資料改了表格沒更新就讓 audit 失敗；`find` 讓 session 先查再讀相關頁 | 新增 `tests/test_ecosystem.py` 8 個測試 |
| `studies/ecosystem-2026-11/`：研究規格、三個子代理的原始筆記與草稿、`merge.py`（列出主 session 改過草稿的每一處）、兩組試跑 | 研究紀錄照慣例保留原始材料 | 草稿都通過格式檢查；W 用絕對路徑指向框架舊紀錄的 9 筆，改成相對路徑並加上檢查 |
| 文件解析試跑：自己產生答案已知的三頁 PDF 與模擬掃描件，在斷網的容器裡跑 pdftotext、pymupdf4llm、markitdown、Docling（三種設定）、Marker、OCRmyPDF | 各家準確度都是自報，沒有中立比較 | `trials/docparse/RESULTS.md`。pymupdf4llm 與 Docling 在文字型 PDF 全對；沒有 OCR 的工具遇到掃描件輸出空檔、exit 0；Docling 與 Marker 要先暖機才能斷網執行 |
| C 程式理解試跑：六個檔案、答案已知的 C 專案（ops table、callback、巨集產生的函式、`#ifdef`），七個工具回答五個問題 | 使用者最常做 C、kernel 與韌體 | `trials/codegraph/RESULTS.md`。沒有工具全對；cflow `--cpp`、clang 與 CodeGraph 剛好互補；callback 沒有工具解得出；codebase-memory-mcp 會安靜地漏掉巨集後面的函式 |
| 資安事件查證 | 子代理的事件表來自搜尋摘要 | Trivy（CVE-2026-33634）、LiteLLM 兩次（2026-03、2026-10）、Context7 ContextCrush（CVE-2026-75130）都讀過一手來源；`~/src` 底下沒有專案用到受影響的 Action 或套件 |
| `README.md` 加資料庫的入口 | 讓接手的 session 知道先查這裡 | audit 檢查連結 |

**驗證**：Linux 317 個測試通過（7 個依平台略過）、audit 通過；Windows 的 Python 3.13 跑 `test_ecosystem` 與 `test_audit` 通過（14 個）。

**後續（2026-11-22，同一個分支）**：使用者確認 FastCtx 是 yc-duan/fastctx、Mythpen 是 niyongsheng/mythpen，都以最新版為準。兩筆寫在 `studies/ecosystem-2026-11/drafts/U.json`，`merge.py` 以它取代子代理 C 的 FastCtx 草稿，資料庫變成 238 筆。

- **Fastctx 1.0.1-beta.22**：重讀原始碼，確認 Workbench 以 `bypassPermissions` 啟動背景 Claude Code。它會關掉 agent 內建的 shell、改由 MCP 工具 `run` 執行命令，而 guard hook 的 matcher 只有 `Bash|Edit|Write|MultiEdit|NotebookEdit`，所以經 `run` 的命令不會被擋（推論，未實測）。審查清單的 MCP 段加上這一項，交接檔列為 S17 要問使用者的事。
- **Mythpen v0.1.3**：Tauri 桌面應用，角色、關係、伏筆、世界觀、時間線的管理，也能從既有稿件反推；打包版預設開啟 Sentry 錯誤回報與 Aptabase 使用統計（設定裡一個開關可以都關），README 的「No cloud required」和這點、以及 AI 功能會送稿件給模型服務不完全一致。

**沒做的事**：這一輪沒有交給另一個模型獨立審查。試跑沒有測 Serena＋clangd、Joern、MinerU、真實論文與 kernel 規模的程式。iOS、資料分析、量化、DevOps 等領域的 skill 只做到搜尋，沒有收錄。FastCtx、Mythpen 等名稱要使用者確認（見 `docs/ecosystem/recommendations.md`）。

## 2026-11-21：S15（分支 `s15-windows`，在 clone `../ai-general-framework-s15` 裡做）

起因：核對狀態時發現，GitHub 上的 CI「Python core」在 S11、S14 兩次 push 後都失敗，失敗的是 Windows 的兩個 job。CI 的輸出被截在 16,000 字，只看得到續接 hook 的 7 個測試；用這台 Windows 的 Python 3.13 跑完整測試，才看到 guard hook 另外 4 個測試（29 個子案例）也失敗，而且修正前的 main 就是這樣。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `templates/claude-continuity-hook.py`、`claude-guard-hook.py`：啟動時把 stdin、stdout、stderr 設成 UTF-8 | Claude Code 用 UTF-8 收送 hook 的 JSON。Windows 預設用系統的字碼頁（CI 是 cp1252，這台是 cp950）：續接 hook 一印中文就 `UnicodeEncodeError`，hook 照設計吞掉錯誤、什麼都不輸出，所以在 Windows 上它等於沒有作用 | 新測試在 cp1252、cp950 下檢查輸出是 UTF-8；修正前失敗、修正後通過。guard hook 在 cp1252 下沒重現出誤擋，那部分是預防 |
| 續接 hook 印路徑一律用 `/` | Windows 上印成 `.ai\HANDOFF.md`，和其他平台不一致 | 同上 |
| guard hook 在 Windows 上把 Git Bash 的 `/c/Users/...`（以及 Cygwin 的 `/cygdrive/c/...`）當成 `C:/Users/...` | Windows 上 Claude Code 的 Bash 是 Git Bash；`echo x > /c/...受保護的路徑/a` 原本會放行 | 新測試（只在 Windows 跑）；用 Windows 的 Python 實測 |
| `tests/test_guard_hook.py` 的 shell 命令改用 `/` 的路徑 | 原本把 `C:\Users\...` 放進 bash 命令；反斜線在 bash 裡是跳脫字元，那行命令實際上不會寫到那個路徑，測試在 Windows 上一直失敗 | Windows：308 個測試通過（38 個 POSIX 專用的照設計略過）；Linux：309 個通過（7 個略過，包括只在 Windows 跑的那一個） |
| guard hook 說明文字裡的 `<<\EOF` 改成 `<<\\EOF`；新增「所有 Python 檔在警告視為錯誤時都能編譯」的測試 | S11 寫的說明文字有無效的跳脫字元，每次執行 guard 都印一行 `SyntaxWarning`；之後的 Python 版本會直接拒絕編譯 | `tests/test_audit.py` 新測試 |
| `tests/test_continuity_hook.py` 讀寫一律指定 UTF-8 | 測試本身在 cp950 的 Windows 上也會讀錯 | 同上 |

**驗證**：Linux 309 個測試、audit 通過；這台 Windows 的 Python 3.13 跑完整測試、audit，以及 CI 實際執行的 `agf check --profile full`，都通過。GitHub 上的 CI 要等使用者 push 之後才知道。

**審查。** 換模型（claude-sonnet-5-5）只讀審查，在 Linux 與 Windows 的 Python 都跑過。找到：設成 UTF-8 時錯誤處理變成嚴格，輸入裡有不是 UTF-8 的位元組時，guard 會把它當成「不是事件」而放行（舊版會擋下），改成讀取時保留這些位元組（surrogateescape）、輸出時用 backslashreplace，並加測試；Cygwin 的 `/cygdrive/c/...` 一併對應；編譯檢查加進 `examples/`、`studies/`。

**沒做的事**：沒有在 Windows 的 Claude Code 裡實際裝 hook 試；Windows 的 `/mnt/c` 一類 WSL 路徑不在這次範圍。

## 2026-11-19：S14（分支 `s14-framework`，在 clone `../ai-general-framework-s14` 裡做）

使用者挑了：把大部分常駐規則改成需要時才讀、量 `debug-root-cause` 新加的兩條規則、重跑沒重跑過的 7 個觸發情境；另外決定續接 hook 的 `save_prompts` 不開（再送一次給模型服務也算上雲端）、guard hook 不移到使用者層級。量測中途使用者叫用了 `/align-with-me`，對齊三個後續決定。結果在 [studies/research-2026-11/J-s14.md](studies/research-2026-11/J-s14.md)。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `templates/project-rules.md` 1,073 → 約 860 字：只留對齊、skill、驗證、授權四段，加一句語言、一句寫作指引，以及什麼時候讀 `practices.md` | 常駐的文字每個 session 都要讀 | 固定成本少約 220～280 tokens（最後版本約 220）；S11 的 8 個任務 8/8 通過，但花費合計和 S13 差不多（0.766 對 0.749），因為模型多半會去讀下面這份 |
| 新增 `docs/practices.md`（約 530 字），跟其他指引一起部署 | 放改程式、工具、續接、文字四段；比 13,500 字的 workflow 指引短得多，讀它不會比省下的還貴 | 單元測試（受管理的檔案多一個） |
| 寫作指引那一句放回常駐規則 | 只放在 `practices.md` 時，改寫中文的任務沒去讀寫作指引；盲評裡那份忠實度最差，還加了原稿沒有的行為 | 重跑一次：有讀寫作指引、通過檢查 |
| `evals/impact/tasks.json` 新增 `debug-wrong-premise` | 量「先核對前提」：使用者說是 2.0 的四捨五入造成的，其實回報是 1.9 跑的 | 兩組 3/3 都做對，量不出差別 |
| `evals/host/run_claude.py`、`trigger.py`：被宿主擋下的 Skill 呼叫另記在 `skill_calls_blocked`（原因在 `skill_calls_blocked_errors`），不算使用、也不算誤用；報告多 `blocked_attempts` | 模型看到 `align-with-me` 的檔案就試著叫用，宿主依設定拒絕；使用者決定這種嘗試另外算 | 單元測試 |
| `studies/research-2026-11/J-s14.md` 與 `measurement-s14/`（含盲評材料） | 結果與限制 | — |

**量測花費**：約 2.91 美元，在使用者給的約 3 美元內。

**結論**：拆分讓不寫程式、不寫文件的 session 比較便宜，真正做事的 session 花費差不多。`debug-root-cause` 的新規則在這個任務上沒有額外作用，模型本來就會先查證。其他 7 個觸發情境沒有退步。

## 2026-11-18：S13（分支 `s13-rules`，在 clone `../ai-general-framework-s13` 裡做）

依據：S12 量到常駐規則是固定成本的最大一塊（分析報告第三輪的第 1 項）。結果在 [studies/research-2026-11/I-rules-s13.md](studies/research-2026-11/I-rules-s13.md)。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `templates/project-rules.md` 1,413 → 1,073 字 | 每個 session 都要讀它。刪掉模型不用提醒也會做的說明，以及 skill 描述與指引已經寫了的清單；每條規則的指示都保留 | 另一個模型（claude-sonnet-5-5）逐句對照新舊版，指出 5 處刪得太多，都已補回。固定成本：規則約 1,920 → 1,610 tokens；S11 的 8 個任務用新規則各跑 1 次，8 個都通過，花費合計少 2%（雜訊範圍內） |
| `agf/manage.py` 附加在安裝檔後面的工具模式說明改寫（長度約不變，249 → 261 字） | 原本寫死 `python3`，Windows 常常只有 `python` 或 `py -3`；copy 模式補上「在專案根目錄執行」。安裝後的整份規則約 1,664 → 1,336 字 | 單元測試；兩種工具模式的安裝結果都看過 |
| `evals/host/impact.py` 每段記錄 `tools_listed`，報告列出每格看到的工具數 | 量測途中使用者環境多連上一個 MCP 伺服器，工具從 23 個變 31 個，第一次呼叫多了約 1,730 tokens；沒有這個欄位，就分不出是規則還是環境造成的 | 單元測試 |
| `studies/research-2026-11/I-rules-s13.md` 與 `measurement-s13/` | 結果與限制 | — |

**量測花費**：約 1.06 美元。

**結論**：縮短安全，但每個 session 只省約 310 tokens（花費約 2%）。要再省得多，要把大部分規則改成需要時才讀，或處理行為上的成本（例如寫作指引太長）；這兩條都還沒做。

## 2026-11-18：S12（分支 `s12-framework`，在 clone `../ai-general-framework-s12` 裡做）

依據：使用者「先不用 push，把剩餘的都先做好」，一開始選定的範圍見 [docs/analysis-2026-11.md](docs/analysis-2026-11.md) 的「第三輪」。量測在 [studies/research-2026-11/H-measurement-s12.md](studies/research-2026-11/H-measurement-s12.md)。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `skills/trace-code`、`guide-learning`、`debug-root-cause`、`review-sql` 的描述 | S11 的觸發量測裡，兩個複合任務（一個請求裡有兩種工作）都選了輔助的 skill。描述寫明兩種工作同時出現時以誰為主 | 觸發量測：那兩個情境 6/6 選對；字面相近、不該換的兩個情境 4/4 沒被搶走 |
| `skills/read-research` 的描述 | 「核對清理過的規格複本」這個情境在 S8、S11 都沒用到它 | 3/3 |
| `skills/debug-root-cause` 第 1、5 步 | 先列出並核對調查依賴的前提；說「修好了」要附修正前失敗、修正後通過的輸出 | 文字修改，沒有量測 |
| `agf project status` 的 `parent_claude_dirs`、`launch_notices` | S8、S10 都從上層目錄啟動，專案的 skill 與 deny 規則沒有載入 | 單元測試；在 Raft 專案上實際列出 `~/src`。無頭探測的結果記在 `adapters/claude.json` 的 `project_launch` |
| `agf task checkpoint` | 讓每個里程碑都寫得起交接：已完成、進行中、下一步，加上程式收集的 git 狀態，`--append` 接在既有交接檔最後 | 單元測試 3 個 |
| `agf check --profile periodic`、`templates/quality.example.json` 的三個例子 | 示範腳本、文件命令、乾淨重建，最容易在之後的修改裡悄悄壞掉（Raft 專案 S10 的教訓） | 單元測試 2 個，含「範本三種 profile 都驗證得過」 |
| 續接 hook 的 `save_prompts` 與 `user-prompt` 子命令 | 使用者在對話裡說的決定，session 一截斷就不見了。預設關閉，因為打進對話的東西可能有密碼或金鑰 | 單元測試；量測：兩個「決定只在對話裡」的任務，框架組 6/6、對照組 0/6 |
| `evals/host/impact.py` 的 `rules-only`、`skills-only` 組，每段記錄 `first_context_tokens`；`evals/impact/tasks.json` 新增 4 個任務 | 拆開固定成本；找「沒框架容易做錯」的任務 | 單元測試；量測：規則約 1,920 tokens，skill 描述約 720 |
| `docs/cli.md`、`docs/workflow.md`、`README.md`、`evals/host/README.md` | 上面這些的用法 | — |
| `docs/analysis-2026-11.md` 第三輪、`studies/research-2026-11/H-measurement-s12.md` 與 `measurement-s12/` | 結果與限制 | — |

**量測花費**：觸發 1.24 美元、成效 1.90 美元、上層目錄的探測 0.01 美元，合計約 3.15 美元，在使用者給的約 4 美元內。

**審查。** 交給沒參與的模型（claude-sonnet-5-5）只讀審查；它做到一半撞到 5 小時上限，額度恢復後接著做完。找到並已修正：

- 續接 hook：5 則長訊息會把最新的一則擠出檢查點（那一段只保留開頭），改成先捨掉較舊的；訊息裡的 U+2028 這類字元會把存檔的一行拆成兩行、整則遺失，改成只在 `\n` 分行；恢復超過 7 天的舊 session 時，自己的訊息檔與最後訊息檔會被當成過期刪掉，改成按檔名保護。各加了測試。
- 量測工具：第一則 assistant 訊息若是合成的（例如額度用完的通知）或 usage 全是 0，`first_context_tokens` 會記成 0；改成跳過並記為不知道，加了測試。
- `task checkpoint`：值裡的換行會打亂清單，改成合併成一行；接在 CRLF 檔案後面時保留原本的換行字元。加了測試。
- 文件：觸發量測裡 review-sql 是直接讀 `SKILL.md`，不是經 Skill 工具，先後順序也沒有紀錄（`trigger-results.json` 現在保留 `skill_reads`）；接手的 session 有 2 次先讀 `AGENTS.md`、再讀檢查點；桌面版列出子專案 skill 只看過一次；`save_prompts` 補上「太長先捨掉舊的」與「檔案保留 7 天」；品質範本的例子標明是範例路徑。

**沒做的事**：教學文件格式的個人化；子命令退場（沒有使用紀錄）；在 GitHub 上跑 CI（使用者這一輪不 push）。

## 2026-11-18：S11（分支 `s11-framework`）

依據：使用者在 Raft 專案結束後的七點回饋，分析在 [docs/analysis-2026-11.md](docs/analysis-2026-11.md) 的「第二輪」。量測結果在 [studies/research-2026-11/G-measurement-2026-11-18.md](studies/research-2026-11/G-measurement-2026-11-18.md)，外部研究在 [F-hooks-evals-ci.md](studies/research-2026-11/F-hooks-evals-ci.md)。

名詞：下面的 SessionStart、Stop、StopFailure 等是 Claude Code 的 hook 事件，分別在 session 開始、AI 準備結束一輪回答、因 API 錯誤（例如額度用完）中斷時觸發；PreCompact／PostCompact 在對話壓縮前後，SessionEnd 在 session 結束，PreModelSwitch 在換模型之前。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `templates/claude-continuity-hook.py`、`templates/claude-continuity-settings.example.json`，登記為 integration template | 撞到用量上限、對話被壓縮或換模型之後，新 session 要從頭重讀，交接檔也常忘了更新。這個 hook 在中斷、壓縮、結束、換模型時，把 git 狀態與最後一則訊息寫進 `.agf/checkpoints/`。新 session 開始時，它提示先讀交接檔與 checkpoint。session 在交接檔之後又 commit 了，它在結束前提醒一次 | `tests/test_continuity_hook.py` 14 個測試。Claude Code 2.1.325 無頭探測：SessionStart、Stop、SessionEnd 會觸發。量測裡 4 個接手的新 session 都先讀了 checkpoint（[逐筆紀錄](studies/research-2026-11/measurement-2026-11-18/continuation-reads.md)）。PreCompact、PostCompact、StopFailure、PreModelSwitch 沒有在真實 session 觸發過；量測時撞到的那次用量上限，執行目錄已刪，無法確認 StopFailure 有沒有寫出 checkpoint。Stop 的提醒模型有沒有照做，沒有實測 |
| `evals/host/impact.py`、`evals/impact/tasks.json`（8 個任務）、`evals/impact/continuity-hooks.json` | 使用者要一個方法，測框架有沒有幫助、會不會多耗 token。做法：有框架與沒框架兩組配對，用隱藏檢查判成敗，四種 token 分開記，有總預算上限。兩個任務模擬「被截斷後新 session 接手」與「換模型接手」 | `tests/test_eval_impact.py` 10 個測試。實際量測一次：計畫 32 次，完成 27 次，兩組都 100% 通過，框架組多花 20%～45%（結果與限制見 G 報告） |
| `impact.py report` 可以合併多個輸出目錄，並列出截斷是否真的發生、讀了幾次工作目錄以外的檔 | 量測做到一半撞到用量上限；補跑寫到新目錄，再合併成一份報告，不必全部重跑 | 測試；實際合併了兩次量測：8 次續接的第一段都真的被截斷，受試者沒有讀工作目錄以外的檔 |
| `templates/claude-guard-hook.py`：heredoc（用 `<<EOF` 接在命令後的多行文字）只有交給 shell 執行時才當命令檢查 | 已安裝的 guard hook 擋下了一個 Python heredoc，因為裡面的 Markdown 寫了 push 的命令，而那段文字 shell 不會執行 | `tests/test_guard_hook.py` 共 20 個測試，含被誤擋的那個命令 |
| `.github/workflows/skill-triggers.yml` | 讓觸發量測能在 GitHub Actions 上跑。只在手動按下時執行，需要 `ANTHROPIC_API_KEY` secret，結果上傳成 artifact，不讓 build 失敗 | **還沒在 GitHub 上跑過**。三個 action 的 commit SHA 都用 `gh api` 核對過對應的版本 tag |
| `evals/host/run_claude.py`：`--env NAME` 不帶值時從目前環境複製 | CI 裡傳 API key 不必寫在命令列上 | 測試 1 個 |
| `evals/scenarios.json` 新增 2 個觸發情境 | 審查一段附了材料的 diff（該用 `review-change`）；「先問我問題」（不該自動叫用只給使用者用的 `align-with-me`） | 觸發量測：兩個都符合預期 |
| `templates/project-rules.md`、`skills/align-with-me/SKILL.md`、`docs/workflow.md`：一開始就問完；每題寫給沒有背景的人看 | 使用者說中途冒出的問題會打斷他做別的事，問題的描述也常看不懂 | 文字修改，沒有量測；常駐規則 1,316 → 1,413 字 |
| `docs/cli.md`、`docs/workflow.md`、`evals/host/README.md`、`README.md` | 續接 hook、量測工具、CI workflow 的用法 | — |
| `docs/analysis-2026-11.md` 第二輪、`studies/research-2026-11/` 的 F、G 與量測資料 | 研究與結果跟著框架 | — |

**審查。** 修改交給沒參與的模型（claude-sonnet-5-5）只讀審查，它找到：

- guard hook 的三種繞過，都是這一輪的 heredoc 修改造成的：heredoc 交給 shell 執行（`bash <<'EOF'`、`cat <<'EOF' | bash`、`eval "$(cat <<'EOF' …)"`）；雙引號裡的撇號（`"it's"`）讓後面的 `$(...)` 被當成引號內的文字；帶 `-` 或 `.` 的定界字（`<<END-OF`）讓後面所有命令都被當成 heredoc 內容。改法：讀 heredoc 的是 shell、`eval`、`source`、`ssh` 時，內容當命令檢查；引號改成逐字掃描；定界字接受更多字元；找不到結束行時，剩下的命令照常檢查。14 個繞過寫成測試。
- 續接 hook 的三個錯誤：交接檔 commit 之後，Stop 與 SessionStart 仍說它「沒跟上」（改成也看交接檔最後一次 commit 的時間）；恢復超過 7 天的舊 session 時，自己的紀錄檔被當成過期刪掉；設定檔不是 JSON 物件時當掉。另外改成每個 session 各存一份最後的訊息，git 呼叫有總時間上限（換模型時 3 秒，避免 hook 逾時擋下換模型）。
- 量測工具：合併時沒有檢查 skill、hook、任務檔是否相同，同一個目錄給兩次會重複計算；hook 設定寫著框架的路徑，框架組理論上讀得到隱藏檢查。都已修正；hook 程式改成複製進受試目錄。
- workflow 把輸入直接貼進 shell 命令；改成經環境變數傳入。
- 文件：花費的範圍應是 20%～45%；「token 與花費都變多」有一個任務例外；分析報告把「補跑」寫得像全部補完；有幾句太長、名詞沒有解釋。都已修正。

**量測花費**：觸發 1.07 美元、成效 2.34 美元，合計 3.41 美元，在使用者給的 2～4 美元內。

**沒做的事**：教學文件格式的個人化（只寫建議，見分析報告）；把 guard hook 裝到使用者層級（這一輪裝在工作區上一層，保護框架主目錄）。

## 2026-11-17：S10（分支 `s10-framework`）

依據：[分析報告](docs/analysis-2026-11.md)。這一輪是在 Raft KV store 專案做最後一次複查時，邊用框架邊找到的問題，加上外部研究（[studies/](studies/README.md)）。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `templates/project-rules.md` 重寫（每個 session 都載入） | 句子改短、改自然；多三條這次證實需要的規則：續接與用量、只做過一次的檢查要重跑、commit 前看暫存範圍；「改程式」換成依序問的五個問題。原本「開始任務時執行 `profile show`」改成「需要偏好時再查」：S8 與這次都沒有用到它，卻每次都要付讀取成本 | 字數 1,310 → 1,316，幾乎不變；`tests/test_manage.py` 通過；沒有量測對行為的影響 |
| 新 skill `skills/align-with-me/` | 使用者要「grill me」時有一個直接的入口；`disable-model-invocation: true`，在 Claude Code 上不進模型的 skill 清單、不會誤觸 | `agf audit` 只檢查結構，不檢查這個欄位；它是 Claude Code 的欄位、不在 agentskills.io 規格裡，其他宿主可能忽略；沒有在宿主上實際叫用過 |
| `templates/claude-guard-hook.py`、`templates/claude-guard-settings.example.json`，登記為 `integration template` | 文字規則與 deny 規則擋不住 `git -C . push`、`sh -c`、從上層目錄啟動的 session；hook 可以裝在使用者層級 | `tests/test_guard_hook.py` 17 個測試；Claude Code 2.1.325 無頭 session 實測一次：`git -C <dir> push` 與 Write 進受保護目錄都被擋下（2026-11-17，花費約 0.004 美元）。審查後修正的版本再實測一次：`bash -lc '... push'` 與重導向進受保護目錄被擋、`git log` 照常執行；模型自己拒絕改用 `rtk proxy git push` 繞過，所以那一種只有單元測試 |
| `adapters/claude.json` 新增 `guard_hook` | 記下 guard hook 實測過與沒測過的情況；原本「跑品質檢查的 Stop hook」那一筆仍標示未測試 | 同上 |
| `docs/workflow.md` 新增「續接、換模型與用量」 | 這次 4 個平行子代理撞到 5 小時上限、使用者換模型後要求重試；原本沒有任何指引 | 文字修改，未量測 |
| `docs/delivery.md` 的暫存規則 | 這次重設 index 後，先前暫存的刪除跟著進了錯的 commit | 文字修改 |
| `docs/writing.md` 的七項校閱清單 | 使用者的 AI 味標準散在各段；附上實際改過的例子 | 文字修改 |
| `docs/analysis-2026-11.md` | 依使用者的 11 項標準寫優缺點與建議 | — |
| `studies/`：S7、S8 的研究搬自 Raft 專案；這次的四份研究報告 | 框架的研究應該跟著框架 | 內容未改 |
| `README.md` | 換模型的說法、新 skill、guard hook 的用法 | — |

**審查。** 第一版交給沒參與的模型（claude-sonnet-5-5）審查，報告在 [studies/research-2026-11/E-framework-review.md](studies/research-2026-11/E-framework-review.md)。找到：hook 的 9 組繞過（例如 `rtk proxy git push`、`bash -lc`、`sudo -u bob git push`、`(git push)`、`gh -R a/b pr create`、在受保護的 repo 裡直接 `git commit`、`>|`、`cp -t`、`tar -C`、`curl -o`）、4 個誤擋（引號裡的 `>`、`git -C <受保護> branch` 這類只是列出的命令）、怪輸入會讓 hook 當掉、設定檔的路徑沒有驗證；文件 7 處：workflow 一句和新規則矛盾、`profile show` 的改變沒寫、audit 的說法過頭、align-with-me 前後矛盾、README 與分析把「測過兩個情況一次」寫得像全面驗證、`docs/cli.md` 沒提新範本、分析指向 CHANGELOG 裡沒有的審查結果。全部修正，每個 hook 的問題各加了測試。

沒做的事與理由見分析報告的「之後的優先順序」。

## 2026-11-17：未提交修改的 commit（`c020447`，main）

2026-11-10 起留在工作目錄、沒有提交的 10 個檔案，經使用者同意原樣 commit：`agf run` 一律經管線擷取輸出並等管線關閉；擷取檔的寫入、讀取、關閉錯誤標為不完整；複合任務的入口說明與評測案例；兩個寫作案例。全部 247 個測試（6 個略過）與 `agf audit` 通過後才 commit。

## 2026-11-16：S8 後續（`90bba83`～`2ffd748`）

規則入口的檢查（既有 `CLAUDE.md` 沒有 import 規則時警告）、交接要寫接手者自己執行的核對命令、Claude Code 的權限範本、`evals/host/` 的觸發評測工具與預檢、skill 叫用的措辭。量測與審查的結果在 [studies/raft-kv-2026-11/changes/RESULTS.md](studies/raft-kv-2026-11/changes/RESULTS.md)。

# 接手文件

更新日期：2026-11-23（S22 量測）。給下一個要改這個框架、或要拿它到別的專案測試的 session。
它描述寫下時的狀態；接手時先跑下面的命令核對，**以看到的為準**。

> **現況一律用下面的命令核對。** 這份文件不寫「等使用者做什麼」，也不放會改動東西的一次性命令（合併、push、更新、刪除）：那些寫在當輪給使用者的回覆裡，留在這裡只會過時又被貼第二次（`tests/test_handoff.py` 會擋）。

## 一開始先做什麼

預期沒有輸出：

```bash
git -C ~/src/ai-general-framework status --short
```

預期最上面是 CHANGELOG 最新一輪的 commit，或使用者之後的新 commit：

```bash
git -C ~/src/ai-general-framework log --oneline -5
```

預期 `"errors": []`、`"warnings": []`：

```bash
python3 -B ~/src/ai-general-framework/scripts/agf.py audit --root ~/src/ai-general-framework
```

預期 OK（有幾個依平台略過）：

```bash
(cd ~/src/ai-general-framework && python3 -B -m unittest discover -s tests)
```

預期只列出 main 本身；多出來的 `-sNN` 是還沒收掉的一輪：

```bash
ls -d ~/src/ai-general-framework*
```

預期 `"drift": []`，而且 operations 全是 `keep`；有 `update` 或 `create` 表示專案還沒跟上 main：

```bash
python3 -B ~/src/ai-general-framework/scripts/agf.py project plan --target ~/src/Distributed_Key-Value_Store_with_Raft
```

```bash
python3 -B ~/src/ai-general-framework/scripts/agf.py project plan --target ~/src/shm_ipc
```

預期列出 `--done`、`--doing`、`--next`、`--repo`、`--append`：

```bash
python3 -B ~/src/ai-general-framework/scripts/agf.py task checkpoint --help
```

框架放在別處時才要換路徑。S12 起每一輪都在框架目錄旁的 clone 做（S16～S21 的已在 2026-11-22 清掉），因為 guard hook 也擋 `git worktree add`。是否已併進 `main`，以上面第二個命令為準。

## 目前的位置

修改與驗證在 [CHANGELOG.md](CHANGELOG.md)；分析與排好順序的待辦在 [docs/analysis-2026-11.md](docs/analysis-2026-11.md)（第六輪的路線圖、第七～十一輪的更新在最後，S20 只有 CHANGELOG）；研究與量測在 [studies/](studies/README.md)；外部資源資料庫在 [docs/ecosystem/](docs/ecosystem/README.md)。

S12 的重點：

- **skill 描述寫明主次**：一個請求裡有兩種工作時以誰為主。上一輪選錯的兩個情境 6/6 選對；`read-research` 也第一次被用到（3/3）。
- **`project status` 提醒從上層目錄啟動的風險**（`launch_notices`）。實測（Claude Code 2.1.325，各一次）：無頭 session 從上層啟動時，子專案的 skill 與 `.claude/settings.json` 都沒有載入。同一天一個從上層啟動的桌面版 session 有列出子專案的 skill，只看過這一次。
- **`task checkpoint`**：里程碑的短紀錄，可接在既有交接檔最後。
- **`check --profile periodic`**：示範、文件命令、乾淨重建這類只跑過一次的檢查。
- **續接 hook 的 `save_prompts`**（預設關閉）：存下使用者說的話。兩個「決定只在對話裡」的任務，開了它的組 6/6，沒開的 0/6。
- **固定成本**：每個 session 一開始多讀約 2,640 tokens，規則約 1,920、skill 描述約 720。
- 量測結果：[H 報告](studies/research-2026-11/H-measurement-s12.md)。

S13：常駐規則從 1,413 字縮到 1,073 字，固定成本少約 310 tokens，S11 的 8 個任務照樣全過（[I 報告](studies/research-2026-11/I-rules-s13.md)）。省得不多；要再省，見分析報告第四輪。

S14：常駐規則只留四段，其餘放需要時才讀的 `docs/practices.md`；寫作指引那一句留在常駐，並寫明什麼時候要讀 `practices.md`。固定成本少約 220 tokens。做事的 session 幾乎都會去讀 `practices.md`，花費和之前差不多（[J 報告](studies/research-2026-11/J-s14.md)）。被宿主擋下的 Skill 呼叫，量測工具另記在 `skill_calls_blocked`。

S16（2026-11-21～22）：使用者給了兩份長需求（框架怎麼演進、外部資源資料庫）。這一輪照使用者的選擇只做分析、資料庫與路線圖，規則、skill 與既有命令沒有改。

- **分析第六輪**：第一份需求逐項對照現有框架，路線圖是 S17 共通能力（按需讀的文件）→ S18 有標準答案的 benchmark 題目 → S19 C 與 kernel 的程式理解 → S20 研究文件 → S21 跨宿主交接。
- **資料庫**：`docs/ecosystem/` 237 筆，`entries.json` 是唯一資料來源，分類頁的表格由 `python -m agf.ecosystem render` 產生，`agf audit` 會檢查表格與資料一致。新增一筆的方法在資料庫的 README。
- **兩組試跑**（`studies/ecosystem-2026-11/trials/`）：文件解析與 C 程式理解，都用自己做的、答案已知的材料。映像檔 `agf-codegraph-*:s16` 留在本機 Docker，原始輸出在 `~/.cache/agf-ecosystem/`（不在版本庫）。解析用的映像檔與 clone 下來的 repo 已在 2026-11-22 清掉，都能重建或重抓。
- **研究方式的教訓**：子代理用 `gh api` 抓維護狀態、clone 只讀，結果先寫進檔案，撞到額度時沒有丟；但子代理的事件表來自搜尋摘要，寫進資料庫前要主 session 自己回一手來源核對（這輪核對的四件都屬實，另外發現一件子代理沒找到）。

S17（2026-11-22）：共通能力與使用者的新需求。guard hook 也檢查 MCP 工具；`agf traces` 與配置預設不留 AI 痕跡；按需讀的指引補上證據順序、驗證與證據、資料分級、模型與強度、核准過的教訓；`templates/spec.md`、`templates/domains/support-chatbot.md`；`usage.py --tokens`；資料庫 245 筆。量測兩題兩組都全過，量不出作用（[K 報告](studies/research-2026-11/K-s17.md)）。

S18（2026-11-22）：寫作短版與讀取時機、commit-msg hook、文件對照程式的 audit、獨立審查 S16～S17 的修正、量測工具的 reviewed 組。A～D 四組在三個有效題目都全過，只量得出成本差；短版第一版讓忠實度退步，第二版過了門檻，但「對新手的用處」仍低於完整版（[L 報告](studies/research-2026-11/L-s18.md)）。

S19（2026-11-22）：量測第一次有真正的隔離（容器加宿主限制）；S11～S18 的數字不能和之後的直接比。S18 審查找到的缺陷已修。真 bug 試跑 19 次通過 16 次，沒有確定合格的題目，所以沒有分組、沒有「框架有沒有好處」的判定；原設計的樣本數也不夠。寫作短版複測通過，維持（[M 報告](studies/research-2026-11/M-s19.md)）。

S20（2026-11-22）：刪減清單最後留下 P1～P4（P5 複測後由使用者退掉，P6 沒有核准）。`agf` 的執行方式在 `.agf/managed/agf-cli.md`；skill 規則只在裝有框架 skill 時寫入；寫文件仍會先讀 practices，有測試鎖住。經使用者同意花 0.67 美元複測的是含 P5 的 `245dc3b`（冒煙與寫作盲評都通過）；最後出貨、沒有 P5 的組合沒有量過（[N 報告](studies/research-2026-11/N-s20-recheck.md)）。

S21（2026-11-22）：五個已知缺口修完；獨立審查找到 guard 的三種繞過與評測的誤判，都重現後修正（[審查](studies/research-2026-11/P-review-s19-s20.md)）；完整版寫作指引的改寫規則獨立成段，盲評通過；shm_ipc 裝了 commit-msg hook。

S22 設計（2026-11-23）：查到以前量測的 startup 與多數題目把框架規則也給了對照組，所以 S11～S21 的「兩組沒差」不能當成框架沒用的證據。新設計與樣本數、花費在 [Q 報告](studies/research-2026-11/Q-s22-benchmark-design.md)。

交接規則（2026-11-23，S22 追加）：常駐規則加了「之後才做的決定」，第一段寫下決定從 3／12 變成 18／18，但複測沒過事先定的條件（[S 報告](studies/research-2026-11/S-s22-handoff.md)）。

S22 量測（2026-11-23）：Opus 5.5 裝了框架多答對 17.9 個百分點，達到「有好處」，但只靠「先問再動」與「跨 session 接手」兩類，每題花費 1.57 倍；Haiku 5.5 上沒有好處（[R 報告](studies/research-2026-11/R-s22-results.md)）。題目、評分與判定在 `evals/host/{grading,judge,taskcheck}.py` 與 `studies/research-2026-11/bench-s22/`。

## 拿框架到別的專案測試

使用者會在其他聊天室用這個框架做別的專案，順便測它的表現。建議的做法：

1. **配置。** 在目標專案執行 `project plan`、再 `project install ... --apply`（README「各專案只帶需要的內容」）。既有的 `CLAUDE.md` 不會被改寫，要自己加一行 `@.agf/managed/project-rules.md`，再用 `project status` 確認沒有 `warnings`，也看一下 `launch_notices`。
2. **從專案目錄啟動新的 session。** 從上一層目錄啟動時，專案的 `.claude/settings.json`（權限與 hook）不會載入；無頭模式連 skill 也看不到。
3. **要不要裝續接 hook。** 把 `templates/claude-continuity-settings.example.json` 的 `hooks` 併進專案的 `.claude/settings.json`，路徑換成框架的實際位置。`save_prompts` **不要開**：使用者 2026-11-19 決定，存下的訊息在下一個 session 會再送給模型服務一次，這也算上雲端，所以在他的專案一律關閉（框架的預設本來就是關閉）。
4. **要觀察的事**，每一項都記下宿主版本、模型、日期與實際看到的輸出：
   - 該用 skill 時，有沒有用宿主的機制叫用（Claude Code 的 Skill 工具）；不該用時有沒有誤觸。
   - 一開始有沒有把問題問完；問題寫得讓人看得懂嗎（名詞有解釋、選項的影響有寫）。
   - 撞到用量上限或換模型後，新 session 有沒有先讀交接檔與 `.agf/checkpoints/latest.md`。
   - guard hook 有沒有誤擋一般的工作。
5. **量測。** 比較成本用 `evals/host/impact.py`，固定模型、任務與 CLI 版本，每個條件至少跑 2～3 次，設 `--total-budget`（它是保守的：已花的加上一個 session 的上限超過總上限就停）。被額度打斷時，用 `--ids` 只補跑缺的任務、寫到新的 `--out`，再用 `impact.py report <目錄一> <目錄二> --md <檔案>` 合併；設定不同的目錄（例如一個有 `--switch-model`、一個沒有）不會合併，分開報告。受試 session 和你自己的對話用同一個額度。
6. **把結果寫回框架。** 放在 `studies/<專案名>-<年月>/`：先寫規格與要量的東西，再跑，最後寫結果與限制。不要事後憑印象補寫。

## 還沒做的事

路線圖（舊的 S19～S21 編號已被用掉，順延重編；花費都要先問）：

1. **S22 benchmark：做完了**（[R 報告](studies/research-2026-11/R-s22-results.md)）。凍結檔 `studies/research-2026-11/bench-s22/freeze.json` 列出的題目、評分與 harness 檔，改了就不能和這次的數字直接比；要比就跑新的一輪。以後要用這套題做回歸，要用 Opus（Haiku 量不到差距，也不能代替）；改了交接規則，只重跑接手的 6 題（兩組各一次約 3 美元）就能複測。原始串流與成品只在本機 `~/.cache/agf-ecosystem/bench-s22/`，不進 repo。
2. **S23 C 與 kernel 的程式追蹤。** 把確定性工具接進 `trace-code` 的 reference，用 S22 的方法在一個 kernel 子目錄比較。codegraph 的 image 先留著。
3. **S24 研究文件。** PDF 解析與引用回查，用真實論文與中文 PDF 核對頁碼和數字。解析用的 image 要重建（Dockerfile 在 `studies/ecosystem-2026-11/trials/docparse/docker/`）。
4. **S25 跨宿主接手。** 需要先在 WSL 安裝 Codex 或 Gemini CLI，要使用者同意。
   S22 已加上「執行前把指定的設定檔換回原版」（`checks.restore`），但這一版的題目都不執行受試者的測試命令，所以還沒在真的受試者上用過。
5. 之後：其他領域各用一個真實任務驗收；教學文件格式的個人化與子命令退場（低）。

要使用者決定、不急的：

- **交接規則的第二次修改**（S22 追加，[S 報告](studies/research-2026-11/S-s22-handoff.md)）：新規則讓決定都寫下來了，但交接檔裡另外記的「待確認」問題會讓下一個 session 停下來問，事先定的通過條件沒達到（Opus 11／18）。要不要改成「當下就問、交接檔只記已定的事」再複測（Opus 舊題與留出題，約 4 美元），由使用者決定。
- **固定成本**（S22）：短任務每題多 57%，第一次呼叫多讀約 2,300 tokens。要不要瘦身、先瘦哪裡。

- **commit-msg hook 有兩個小漏擋**（`Anthropic Claude` 當共同作者、`Generated by claude-3`）。修它會改變 hook 的內容，要連同兩個專案各重裝一次，所以等下次改判斷式時一起做。
- **Raft 的 `traces check`** 加 `--after 7257862` 之後舊署名是 0，但還是會失敗：它的排除清單少 7 個型樣（`agf traces exclude --apply` 會補），而且追蹤著需求副本 `docs/reference/AGENTS.md`（要不要留由使用者決定）。
- shm_ipc 追蹤著 4 個工具設定檔（2026-11-22 掃過沒有密鑰、本機路徑或 email）。使用者選擇維持原樣，只裝 hook。
- 兩個專案都是舊配置：`project update` 不會更新它們的 commit-msg hook，判斷規則改了要各重跑一次 `traces hook --target <專案的絕對路徑> --apply`（給使用者時換成真實路徑）。
- 資料庫裡 34 筆授權與幾個名稱待確認（`docs/ecosystem/recommendations.md`）；`skill-triggers.yml` 從未在 GitHub 上跑過（會花錢、要 API key）。
- 已決定，不要再做：P5、P6；`save_prompts` 不開，量測也不為了讓題目通過而開；只存使用者核准過的教訓；guard hook 維持裝在工作區上一層。

沒有在真實 session 觸發過的：續接 hook 的 PreCompact、PostCompact、StopFailure、PreModelSwitch。`align-with-me` 在 2026-11-19 第一次被使用者實際叫用，照 skill 寫的流程走完。`debug-root-cause` 新加的「先驗證前提、附證據」量過一次（`debug-wrong-premise`），兩組都做對，量不出作用。

## 踩過的坑

- **不要把量測資料夾整個 `git add`。** 原始串流有 session id、本機路徑與使用者裝的工具清單，這個 repo 是公開的。S17 因此改寫過一次歷史；現在有忽略規則與 `tests/test_published_files.py`，commit 前還是要看暫存的檔案清單。
- **量測途中不要改會部署的檔案，也不要移動 HEAD。** 要試修改時複製一份框架，用 `--framework` 指過去。額度用完會留下一列未完成的紀錄，補跑寫到新的 `--out` 再合併。
- **假的 CLI 與假的 Docker 測不出隔離。** S19 的兩個隔離錯誤（全域 `CLAUDE.md` 進到對照組、容器讀不到 0600 的安裝檔）都是真跑一次才看到。改了量測的隔離，先用真 Docker 與便宜的模型各組跑一次。
- **S17、S18 唯一的原始串流只有一份備份**：`~/.cache/agf-ecosystem/private-s18-research`。它只能留本機，不進任何 repo、不上雲端；清快取時要避開。
- **`/tmp` 會不見。** WSL 重開就清掉。要留的材料、腳本與結果放 `~/.cache/agf-ecosystem/` 或 repo，`/tmp` 只放量測的 `--base`。
- **盲評分數不能跨輪比。** 同一個短版兩位評審差了 0.4～0.8 分；舊版一定要和新版混在同一批重跑、重評（S20）。
- **在受保護目錄裡跑命令，路徑不要用變數。** guard hook 展不開 `${F}-s21`，會當成目前目錄（main）而拒絕（S21）。先 cd 出去、寫完整路徑，讓它判斷真正的目標；仍被擋就問使用者，不要換寫法繞。
- **刪除之前先盤點只存在那裡的東西。** `-s18` 有 S18 報告唯一的原始串流；判斷能不能刪要比對內容，不能只看名字：S21 看到 commit 標題寫「user WIP」就警告不要 gc，其實它和已 commit 的 `c020447` 一行不差（使用者 2026-11-22 已清掉那些物件）。開複本用 `git clone --no-local`，不把到不了的舊物件帶過去（S21）。
- **給使用者的命令要帶真實路徑。** `--target .` 被原樣貼在家目錄執行過（S20）。先在本機找出 `.agf/manifest.json`，每個專案給一行絕對路徑的命令；框架回的「use project install first」在家目錄照做會把規則裝進家目錄。
- **「已經有了」要逐句查。** S19 說 P5 拿掉的內容常駐規則已有，其實兩句只在 practices。刪任何觸發條件之前，列出那個檔每一句還能從哪裡被讀到（S20）。
- **對照組不能拿到處理。** 題目與共同的 startup 只寫使用者會講的話：「只改必要的地方」「怎麼驗證」「不推送」都是框架的規則，寫進去就等於兩組都裝了（S22）。
- **花錢之前先算樣本數。** 每組 20 次時，20 個百分點的真實差距只有約 15% 的機率達到 p<0.05。先算再問使用者預算（S19）。
- **題目敘述也要拿標準答案的來源核對。** S19 有一題的敘述和 Git 的實際行為相反，只能作廢。
- **題目先試跑。** 對照組全過、或處理組沒有資訊能通過的題目，分組量幾次都沒有用（S18）。

- **試跑工具時，答案檔不要放在被分析的資料夾裡。** S16 的 C 試跑第一次把 `truth.json` 一起交給 code graph 工具，codebase-memory-mcp 把它收進索引，查詢先回答案檔的內容。只複製要分析的檔案。
- **「本機執行」的工具要斷網跑一次才算數。** S16 的 Docling、Marker 在下載過模型之後，第一次斷網執行仍然失敗（還要另外的參數或暖機）。試跑都加 `--network none`。
- **Claude Code 會擋 `rm -f 目錄/*` 這類可能刪太多的命令**，由使用者才能核准。要重做輸出時換一個新的資料夾。

- **框架的主目錄被 deny 規則與 guard hook 保護。** 工作區上一層的 `.claude/settings.json` 禁止用 Edit／Write 改框架目錄，PreToolUse 的 guard hook 也擋 push、PR、`pkill -f`，以及在框架 repo 裡的 git 寫入（包括 `worktree add`）。這是使用者刻意設的，不要去改它。使用者點名要改框架時，用 `git clone --no-local ~/src/ai-general-framework ~/src/ai-general-framework-s22`（編號用下一輪的）複製一份，在複本開分支修改；改完由使用者自己 `pull --ff-only` 併進 main。clone 的 `origin` 指向本機的框架目錄，不是 GitHub。
- **舊版 guard hook 會誤擋 heredoc。** 使用者把 S11 併進 main 之後已修正；如果看到 heredoc 裡的文字被當成命令擋下，先確認 main 是不是新版。
- **用量上限是共用的。** 量測的受試 session、子代理與主對話用同一個 5 小時額度；S11 的量測做到一半就撞到。無頭模式下撞到上限時，stream 裡會有 `rate_limit_event`，result 的 `subtype` 仍是 `success`，但 `is_error` 是 true。長時間的工作要能分段續跑。
- **RTK hook 會改寫 Bash 命令。** 自動權限審查偶爾因此要求原樣重送；`find -exec`、`tail -3 檔案一 檔案二` 這類寫法會被它拒絕或改壞，改用 Python 或 `tail -n 3`。需要原始輸出時用 `rtk proxy <命令>`。
- **`cd` 會延續到之後的命令**，宿主還會把主要工作目錄跟著改過去。查看別的目錄時用 `git -C` 或絕對路徑。
- **`pkill -f` 會連自己的 shell 一起殺掉**；用 PID 停行程。
- **長時間的命令**用 `setsid nohup` 和 session 分開執行，結果寫進檔案；宿主的背景命令可能有時間上限。
- **CI 的輸出會被截斷。** GitHub 上的「Python core」把測試輸出截在 16,000 字，後面的失敗看不到。Windows 的問題要用本機的 Windows Python 跑完整測試才看得全（WSL 裡：`/mnt/c/Users/user/AppData/Local/Programs/Python/Python313/python.exe -B -m unittest discover -s tests`，在 Windows 檔案系統上的副本裡跑）。
- **hook 要自己設定 UTF-8。** Windows 預設用系統字碼頁，印中文會失敗；兩個 hook 的 `main()` 一開始就呼叫 `utf8_stdio()`。
- **使用者環境的 MCP 伺服器會中途連上。** S13 量測時工具從 23 個變 31 個，第一次呼叫多了約 1,730 tokens。比較固定成本時，同時跑對照組，並確認 `tools_listed` 相同。
- **`/tmp` 在這台 WSL 上是 4.3 GB 的 tmpfs**，重開就清空，也會吃記憶體；要留的證據不要放那裡。
- **給使用者的命令不要用 `<名稱>` 這種佔位字。** bash 會把 `<` 當成讀檔，整行命令不會執行；寫出實際的值，或明說要換掉哪一段。

## 操作範圍

- 不 push、不建立 PR、不部署；這些由使用者自己做。
- 修改框架要使用者在當次對話點名；改完寫進 CHANGELOG，並更新這份交接文件。
- 與框架有關的經驗，在使用它的專案裡當下記錄（例如 Raft 專案的 `.ai/FRAMEWORK_EXPERIENCE_LOG.md`），不要事後憑印象補寫。

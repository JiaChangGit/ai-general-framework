# 接手文件

更新日期：2026-11-22（S18 之後）。給下一個要改這個框架、或要拿它到別的專案測試的 session。
它描述寫下時的狀態；接手時先跑下面的命令核對，**以看到的為準**。

> **push 之前先核對歷史。** S17 原本的 commit `35e6b34` 含私人的原始串流檔；使用者 2026-11-22 決定清掉，乾淨的 S17 是 `1541006`。`git -C /home/user/src/ai-general-framework merge-base --is-ancestor 35e6b34 main` 若回傳 0，表示 main 還是舊歷史，**不要 push**：先由使用者 `git fetch /home/user/src/ai-general-framework-s18 s18-benchmark` 再 `git reset --keep FETCH_HEAD`（AI 不改 main；不要用 pull，歷史已分岔）。推的時候只推 main，不用 `--all`；s17 的 clone 與 main 的 reflog 還留著舊 commit。

## 一開始先做什麼

```bash
git -C <框架目錄> status --short          # 預期：沒有輸出
git -C <框架目錄> log --oneline -3         # 預期：最上面是 S18 的 commit（見 CHANGELOG），或使用者之後的新 commit
python3 -B <框架目錄>/scripts/agf.py audit --root <框架目錄>      # 預期："errors": []、"warnings": []
(cd <框架目錄> && python3 -B -m unittest discover -s tests)        # 預期：OK（有幾個依平台略過）
python3 -B <框架目錄>/scripts/agf.py task checkpoint --help        # 預期：列出 --done、--doing、--next、--repo、--append
```

`<框架目錄>` 換成實際的位置。S12～S18 都在框架目錄旁的 clone 做（`../ai-general-framework-s12`～`-s18`），因為 guard hook 也擋 `git worktree add`。是否已併進 `main`，以 `git -C <框架目錄> log --oneline -5` 為準。

## 目前的位置

修改與驗證在 [CHANGELOG.md](CHANGELOG.md)；分析與排好順序的待辦在 [docs/analysis-2026-11.md](docs/analysis-2026-11.md)（第六輪的路線圖、第七與第八輪的更新在最後）；研究與量測在 [studies/](studies/README.md)；外部資源資料庫在 [docs/ecosystem/](docs/ecosystem/README.md)。

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
- **兩組試跑**（`studies/ecosystem-2026-11/trials/`）：文件解析與 C 程式理解，都用自己做的、答案已知的材料。映像檔 `agf-parse-*:s16`、`agf-codegraph-*:s16` 留在本機 Docker，原始輸出與 clone 下來的 repo 在 `~/.cache/agf-ecosystem/`（不在版本庫）。
- **研究方式的教訓**：子代理用 `gh api` 抓維護狀態、clone 只讀，結果先寫進檔案，撞到額度時沒有丟；但子代理的事件表來自搜尋摘要，寫進資料庫前要主 session 自己回一手來源核對（這輪核對的四件都屬實，另外發現一件子代理沒找到）。

S17（2026-11-22）：共通能力與使用者的新需求。guard hook 也檢查 MCP 工具；`agf traces` 與配置預設不留 AI 痕跡；按需讀的指引補上證據順序、驗證與證據、資料分級、模型與強度、核准過的教訓；`templates/spec.md`、`templates/domains/support-chatbot.md`；`usage.py --tokens`；資料庫 245 筆。量測兩題兩組都全過，量不出作用（[K 報告](studies/research-2026-11/K-s17.md)）。

S18（2026-11-22）：寫作短版與讀取時機、commit-msg hook、文件對照程式的 audit、獨立審查 S16～S17 的修正、量測工具的 reviewed 組。A～D 四組在三個有效題目都全過，只量得出成本差；短版第一版讓忠實度退步，第二版過了門檻，但「對新手的用處」仍低於完整版（[L 報告](studies/research-2026-11/L-s18.md)）。

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

依分析報告第八輪的優先順序：

1. **使用者**照本檔開頭把乾淨的歷史換進 main，再 push。guard hook 的 matcher 已於 2026-11-22 改好；它讀的是 main 的檔案，S18 進了 main 才有新的 MCP 檢查。
2. （高）重做 benchmark 題目：先只跑對照組 3 次，留下會做錯、而且處理組有資訊能做對的題目，再分組量。
3. （中）短版用另一種文字再盲評一次，重點看對新手的用處。
4. （中）S18 的變更交給另一個模型審查。
5. 不留痕跡的專案做真實開發時，在里程碑跑 `agf traces check`，觀察 commit-msg hook 有沒有被觸發或被 `--no-verify` 繞過。
6. S19～S21 照第六輪的路線圖；S21 需要先在 WSL 安裝 Codex 或 Gemini CLI，要使用者同意。
7. 第五輪留下的：在 GitHub 上跑一次 `skill-triggers.yml`（會花錢）；教學文件格式的個人化與子命令退場（低）。
8. 其餘待確認的外部名稱在 `docs/ecosystem/recommendations.md`。
9. （已決定）`save_prompts` 不開，量測也不為了讓題目通過而開；只存使用者核准過的教訓；guard hook 維持裝在工作區上一層。

沒有在真實 session 觸發過的：續接 hook 的 PreCompact、PostCompact、StopFailure、PreModelSwitch。`align-with-me` 在 2026-11-19 第一次被使用者實際叫用，照 skill 寫的流程走完。`debug-root-cause` 新加的「先驗證前提、附證據」量過一次（`debug-wrong-premise`），兩組都做對，量不出作用。

## 踩過的坑

- **不要把量測資料夾整個 `git add`。** 原始串流有 session id、本機路徑與使用者裝的工具清單，這個 repo 是公開的。S17 因此改寫過一次歷史；現在有忽略規則與 `tests/test_published_files.py`，commit 前還是要看暫存的檔案清單。
- **量測途中不要改會部署的檔案，也不要移動 HEAD。** 要試修改時複製一份框架，用 `--framework` 指過去。額度用完會留下一列未完成的紀錄，補跑寫到新的 `--out` 再合併。
- **題目先試跑。** 對照組全過、或處理組沒有資訊能通過的題目，分組量幾次都沒有用（S18）。

- **試跑工具時，答案檔不要放在被分析的資料夾裡。** S16 的 C 試跑第一次把 `truth.json` 一起交給 code graph 工具，codebase-memory-mcp 把它收進索引，查詢先回答案檔的內容。只複製要分析的檔案。
- **「本機執行」的工具要斷網跑一次才算數。** S16 的 Docling、Marker 在下載過模型之後，第一次斷網執行仍然失敗（還要另外的參數或暖機）。試跑都加 `--network none`。
- **Claude Code 會擋 `rm -f 目錄/*` 這類可能刪太多的命令**，由使用者才能核准。要重做輸出時換一個新的資料夾。

- **框架的主目錄被 deny 規則與 guard hook 保護。** 工作區上一層的 `.claude/settings.json` 禁止用 Edit／Write 改框架目錄，PreToolUse 的 guard hook 也擋 push、PR、`pkill -f`，以及在框架 repo 裡的 git 寫入（包括 `worktree add`）。這是使用者刻意設的，不要去改它。使用者點名要改框架時，用 `git clone <框架目錄> ../ai-general-framework-<名稱>` 複製一份，在複本開分支修改；改完由使用者自己 `pull --ff-only` 併進 main。clone 的 `origin` 指向本機的框架目錄，不是 GitHub。
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

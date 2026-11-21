# 接手文件

更新日期：2026-11-21（S15 之後）。給下一個要改這個框架、或要拿它到別的專案測試的 session。
它描述寫下時的狀態；接手時先跑下面的命令核對，**以看到的為準**。

> **S16 進行中（2026-11-21）。** 在 `../ai-general-framework-s16` 的 `s16-ecosystem` 分支：建立外部資源資料庫（`docs/ecosystem/`）、對照使用者兩份需求寫分析第六輪與路線圖。研究規格在 `studies/ecosystem-2026-11/SPEC.md`，三個子代理（W、C、M）的筆記與草稿寫在同一個資料夾的 `*.md` 與 `drafts/*.json`。使用者這輪的決定寫在 SPEC 開頭。被額度打斷時：先看哪些草稿已經寫出，缺的分類只補那一塊，不要整批重跑。
>
> **2026-11-21 撞到用量上限時的狀態（WIP commit）：**
> - 已完成：分析第六輪與路線圖（`docs/analysis-2026-11.md`）；`agf/ecosystem.py`（check／render／refresh／find，audit 會呼叫）與 `tests/test_ecosystem.py`；`docs/ecosystem/` 的 README、security.md、license.md、14 個分類頁骨架、空的 `entries.json`；文件解析試跑全部完成（`studies/ecosystem-2026-11/trials/docparse/RESULTS.md`）；C 程式理解試跑只做了傳統工具（`trials/codegraph/classic-output.txt`，結論：cflow `--cpp` 與 clang 處理得了巨集與 `#ifdef`，沒有工具解得出 ops table 與 callback）。
> - 草稿：W（48 筆）、M（133 筆）已完成；C 子代理在撞上限時還在跑，`drafts/C.json` 與 `C-code-tools.md` 可能不完整，先看筆記最後寫到哪。
> - 已用一手來源核對的資安事件：Trivy CVE-2026-33634（2026-03-19，NVD）、LiteLLM 1.82.7／1.82.8（2026-03-24，OSV MAL-2026-2144）、LiteLLM 1.107.0（2026-10-21，The Register、BleepingComputer）。~/src 底下沒有專案用到 trivy-action、setup-trivy 或 LiteLLM。
> - 剛改完、還沒加測試：`ecosystem.py` 允許 `{"path": "docs/link-study.md", "level": "RECORD"}` 這種指向框架內舊紀錄的 reference（W 的 9 筆用了絕對路徑，合併時改成相對路徑）。
> - 下一步，依序：(1) 替 RECORD reference 加測試；(2) 寫合併腳本 `studies/ecosystem-2026-11/merge.py`：讀三份草稿、補 `checked`、絕對路徑改相對、把 `supply-chain-incidents-*` 從 entries 移到 security.md 的事件段、依試跑調整 tier 與 evidence（pymupdf4llm、Docling、Marker、OCRmyPDF、markitdown 改 `ran`；pymupdf4llm 升 Tier 1），寫進 `docs/ecosystem/entries.json`；(3) `python -m agf.ecosystem refresh`、`render`、`check`；(4) 程式理解的 AI 工具試跑（看 C 的建議，題目在 `trials/codegraph/fixture/truth.json`），寫 `trials/codegraph/RESULTS.md`；(5) 寫分類頁的說明、`comparisons/` 五頁、`articles.md`、`recommendations.md`（README 已連到它們，現在 audit 會因連結不存在而失敗）；(6) CHANGELOG、更新這份交接、最後 commit。
> - 試跑的映像檔（`agf-parse-*:s16`、`agf-codegraph-classic:s16`）與原始輸出在 `~/.cache/agf-ecosystem/trials/`，clone 的 repo 在 `~/.cache/agf-ecosystem/repos/`。

## 一開始先做什麼

```bash
git -C <框架目錄> status --short          # 預期：沒有輸出
git -C <框架目錄> log --oneline -3         # 預期：最上面是 S15 的 commit（見 CHANGELOG），或使用者之後的新 commit
python3 -B <框架目錄>/scripts/agf.py audit --root <框架目錄>      # 預期："errors": []、"warnings": []
(cd <框架目錄> && python3 -B -m unittest discover -s tests)        # 預期：OK（有幾個依平台略過）
python3 -B <框架目錄>/scripts/agf.py task checkpoint --help        # 預期：列出 --done、--doing、--next、--repo、--append
```

`<框架目錄>` 換成實際的位置。S12～S15 都在框架目錄旁的 clone 做（`../ai-general-framework-s12`～`-s15`），因為 guard hook 也擋 `git worktree add`。是否已併進 `main`，以 `git -C <框架目錄> log --oneline -5` 為準。

## 目前的位置

修改與驗證在 [CHANGELOG.md](CHANGELOG.md)；分析與排好順序的待辦在 [docs/analysis-2026-11.md](docs/analysis-2026-11.md)（S11、S12 在最後兩節）；研究與量測在 [studies/](studies/README.md)。

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

依分析報告第五輪的優先順序：

1. **使用者**把 `s15-windows` 併進 main（`git -C <框架目錄> pull --ff-only ../ai-general-framework-s15 s15-windows`），再 push，確認 GitHub 上 CI 的 Windows job 恢復通過。
2. （中）寫作指引拆成常用的短版與完整版，量文字品質（照 S14 的盲評方法）與花費。常駐規則的拆分已在 S14 做完：固定成本少了，做事的 session 花費卻差不多。
3. （已決定）`save_prompts` 在使用者的專案不開，再送一次給模型服務也算上雲端；guard hook 維持裝在工作區上一層（`/home/user/src/.claude/settings.json`），不移到使用者層級。兩者都是 2026-11-19 使用者的決定。
4. 要等使用者 push 的：在 GitHub 上實際跑一次 `skill-triggers.yml`（並設定 `ANTHROPIC_API_KEY`，會花錢）。
5. （低）教學文件格式的個人化（第二輪的建議）；子命令退場（先累積使用紀錄）。

沒有在真實 session 觸發過的：續接 hook 的 PreCompact、PostCompact、StopFailure、PreModelSwitch。`align-with-me` 在 2026-11-19 第一次被使用者實際叫用，照 skill 寫的流程走完。`debug-root-cause` 新加的「先驗證前提、附證據」量過一次（`debug-wrong-premise`），兩組都做對，量不出作用。

## 踩過的坑

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

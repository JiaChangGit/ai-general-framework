# CLI 操作

在 framework checkout 用 `python scripts/agf.py`。已配置專案的有效入口寫在 `.agf/managed/agf-cli.md`（常駐規則只留一句指路；S20 以前的配置在 `project update` 之前仍寫在專案規則裡）；共享模式使用來源 checkout，副本模式使用專案內 `.agf/managed/runtime/scripts/agf.py`。核心不需 pip 安裝。

CLI 輸出 JSON；`check`、`run` 等檢查失敗會回傳非零，操作錯誤通常為 2，選用能力缺失可為 3。不同命令的退出碼語意不同：`files diff` 成功完成比較時，即使發現差異也回傳 0，要檢查 JSON 中的差異內容，不能只靠退出碼。`PLAN`、`RECORDED`、`HEADER_RECOGNIZED` 與 `PASS` 意義不同，依輸出的說明判讀。

## 配置、更新與偏好

```console
python scripts/agf.py doctor --root ../my-project
python scripts/agf.py project plan --target ../my-project --skill trace-code
python scripts/agf.py project install --target ../my-project --skill trace-code --apply
python scripts/agf.py project update --target ../my-project --tools copy
python scripts/agf.py project status --target ../my-project
python scripts/agf.py profile show --no-user
```

`doctor` 只找執行檔及明確提供目錄的管理資料標記；不驗證登入或 repository 有效性，也不從安裝了 gh／glab 推定專案平台。自管 GitLab、企業 GitHub 與 SVN 的實際連線由原生工具和當次任務處理。

配置、更新或回復時，避免其他程序同時修改相同的受管理檔案。工具會在寫入前再核對內容，若無法安全回復會保留競爭修改並回報快照；核對與檔案替換之間仍有競態，這不是跨程序鎖。

新配置預設不額外選 skills、共用工具。`--tools copy` 才帶工具副本。舊 manifest 沒有模式欄位時視為 copy；更新沿用選擇，明確指定才改。更新會列出來源已移除的受管理 skill，套用前保留 drift、未受管理檔與回復檢查；沒有永久別名或中央專案登錄服務。

偏好來源為框架預設、使用者設定、專案 `.agf/profile.json`，較近的物件逐層合併，清單取代。Windows 使用者路徑為 `%APPDATA%/ai-general-framework/profile.json`；Linux 為 `${XDG_CONFIG_HOME:-~/.config}/ai-general-framework/profile.json`。可明示 `--user`／`--project`；`profile init --output PATH` 先預覽，`--apply` 才建立且不覆寫。個人偏好不授予工具權限。

Manifest 是記錄受管理檔案、來源和模式的清單。`status` 分別顯示檔案是否被本地修改，以及工具入口是否仍可讀；檔案乾淨不代表已刪除的共享來源還能使用。工具入口可讀也不等於原生工具已登入或通過功能驗證。

從 S20 以前升級的 copy 模式專案，若用專案內的舊快照執行 `project update --apply`，要跑兩次：第一次換掉快照裡的程式，第二次才會產生 `agf-cli.md`。用框架 checkout 執行時一次就好。

常駐規則的 skill 一段只在更新後仍裝有框架 skill 時寫入；只有使用者自己的 skill 或外掛 skill 時不寫。

`status` 也檢查各宿主自己會讀的入口有沒有接到 `.agf/managed/project-rules.md`：Claude Code 看 `CLAUDE.md` 或 `.claude/CLAUDE.md`，Gemini CLI 看 `GEMINI.md`，沿著 `@` import 往下找，最多五層，程式碼區塊裡的不算；Codex 與 OpenCode 看 `AGENTS.md` 有沒有寫到它。沒接上時列在 `warnings`，退出碼不變。框架不改寫既有的入口檔；要每個 session 都載入規則，自己加一行 `@.agf/managed/project-rules.md`。

配置了 Claude Code 時，`status` 另外列出專案上層有自己 Claude Code 設定的目錄（`parent_claude_dirs`，有 `.claude/settings.json`、`.claude/settings.local.json`、`.claude/skills` 或 `CLAUDE.md`；家目錄不算，`~/.claude` 是使用者層級）。從那種目錄啟動的 session，用的是那裡的設定：2026-11-18 用 Claude Code 2.1.325 的無頭 session 實測，專案自己的 `.claude/settings.json`（權限與 hook）沒有載入，專案的 skill 也不在清單裡；從專案目錄啟動時兩者都有。同一天有一個從上層啟動的桌面版 session 列出了子專案的 skill，並註明「處理那個目錄的檔案時適用」；只看過這一次，但 skill 這部分可能依宿主而異。提醒寫在 `launch_notices`，不算 `warnings`，因為專案本身沒有問題。

### 不留 AI 痕跡

```console
python scripts/agf.py traces check --target ../my-project
python scripts/agf.py traces exclude --target ../my-project --apply
python scripts/agf.py traces remove --target ../my-project --apply
```

新配置預設不留 AI 痕跡（使用者 2026-11-22 的決定）：`project install --apply` 在專案規則加一行「commit 不加 AI 署名、公開文件不提工具名、AI 工具檔不進版本庫」，並在該 clone 的 `.git/info/exclude` 寫一段有標記的排除清單（CLAUDE.md、AGENTS.md、GEMINI.md、`.claude/`、`.agents/`、`.agf/`、`.ai/` 等）。這個檔案只在本機生效、不會被 commit，也不會影響已經被追蹤的檔案。`--keep-ai-traces` 關掉這個預設；沒有這個欄位的舊配置維持原樣，更新時加 `--exclude-ai-traces` 才開啟。回復（rollback）會依還原後的配置拿掉或保留那段清單。目標目錄不是 Git work tree 的根目錄（例如在另一個 repo 底下）時，不會去改外層 repo 的檔案。

`traces check` 只讀：列出被追蹤的 AI 工具檔（附移出版本庫、但保留檔案的 `git rm --cached` 命令）、commit 訊息裡的 AI 共同作者或「Generated with」字樣、檔案裡的同類字樣，以及排除清單與 commit-msg hook 在不在。找到痕跡，或排除清單不在，退出碼都是 1。歷史 commit 只回報、不改寫。共同作者行只認整個名字就是 AI 工具（可帶型號）或帳號屬於 AI 工具的，含有同一個字的人名（例如 Jane Claude）不算。

`traces hook --apply` 寫一支 commit-msg hook（git 在建立 commit 前執行的程式）：訊息裡有 AI 共同作者或「Generated with」字樣就拒絕，錯誤訊息說明怎麼改；專案原本就有 commit-msg hook 時不覆蓋；`core.hooksPath` 指到共用或會被追蹤的目錄、或 hook 是 symlink 時不寫，回報 `CUSTOM_HOOKS_PATH` 或 `FOREIGN_HOOK`；機器上沒有能執行的 Python 3 時不擋 commit，也就不會檢查。不留痕跡的配置會一起裝。`--keep-ai-traces` 的配置與之後的更新都不動排除清單與 hook，只有從不留痕跡切回 keep 時，才移除這個模式加的那兩樣。排除清單在 Git worktree 之間共用。

## 來源、檔案與圖解

```console
python scripts/agf.py context search timeout --root . --glob '*.py' --max-results 12 --max-chars 6000
python scripts/agf.py context extract agf/execution.py --start 1 --end 60 --max-chars 6000
python scripts/agf.py source excerpt examples/research/mini-spec.md --query capacity
python scripts/agf.py files diff examples/files/before.json examples/files/after.json --format json
python scripts/agf.py diagram create examples/diagrams/files-transaction.json --format mermaid
```

`context search` 使用既有 ripgrep，預設匹配文字合計上限為 16,000 字元，可用 `--max-chars` 調整；路徑與 JSON 包裝不計入。`text_truncated` 表示單筆文字不完整，`capture_truncated` 表示底層輸出被截斷；遇到超長行而無法解析任何完整匹配時回傳錯誤，不回報查無結果。`context extract` 只讀已儲存的一般檔案，拒絕裝置、pipe 和目錄，並對同一個已開啟的檔案計算 SHA-256。摘錄上限不限制讀取長行時的記憶體或整檔雜湊的 I/O，這不是資源隔離。

PDF 抽字需選用 pypdf，`inspect` 只查 metadata，`excerpt --pages 2,4-6` 才抽指定實體頁。靜態頁用 `source fetch URL --output FILE` 預覽，加 `--execute` 才連網保存；[範例](../examples/research/web-fetch.md)列出 robots、上限及 TLS 行為。

`source fetch` 的回傳紀錄包含要求的網址及重新導向資訊；網址查詢參數可能含權杖或私人識別資訊，分享輸出前先檢查。它也能連線本機及內網網址，不是網路隔離工具；目的地必須在當次授權內。`run` 的結果與可選紀錄包含完整命令參數，避免把密碼或權杖直接放進參數；工具不會自動辨識或遮罩秘密。

為降低大型或重複資料耗盡資源的風險，文字來源限 50 MB、50,000 行，HTML 另限 50,000 個文字單位；PDF 單次選取不超過 50,000 頁、抽取文字總計不超過 2,000 萬字元。超限明確報錯，不把未讀內容當成完整結果；可縮小檔案或 PDF 選頁，已知行號可用 `context extract`。不同來源的 `source diff` 另限兩側單位合計 10,000 且數量乘積不超過 400 萬，相同的正規化內容可直接比較；超過時先縮小本地比對範圍。輸出 `--limit` 不等於運算時間或記憶體上限。PDF 解析器仍可能在抽取單頁前消耗大量資源，這些限制不是隔離機制。

`files rename/normalize` 預設預覽，可保存計畫後以 `files apply PLAN --apply` 套用。管理資料 `.git`、`.svn`、`.hg` 在列檔與套用時都受保護；一般隱藏檔仍照常處理。它不解讀 `.gitignore` 或 `svn:ignore`。碰撞、來源重驗與失敗回復見[批次範例](../examples/files/README.md)。

`diagram create` 將 flowchart／sequence／state 的 JSON 模型轉成圖源；`--format mermaid` 預設採 `look: neo`。模型需有 1–15 個節點、每個標籤 1–12 個顯示字元（不計 `<br/>` 換行），超過就拆圖或明確映射短別名，不自動截斷。流程圖節點可加 `"shape": "decision"` 畫菱形，所有出線都需非空條件標籤；draw.io 也保留菱形。其他圖型直接改[圖解樣板](../templates/diagrams/README.md)，不另外包 JSON 語法。

`diagram transitions INPUT --state-column NAME [--group-column NAME] [--delimiter comma|tab|pipe] [--output FILE]` 先計算狀態轉移，再由 `diagram create FILE --format mermaid` 畫圖。輸入必須是 UTF-8、有唯一表頭的分隔表格，與副檔名無關；自由文字 log 需先明確正規化。上限 20 MB、100,000 筆及 15 個不同狀態，超限報錯；state 需為 1–12 字，不自動去除空白或合併狀態。依各群組的檔案列序，計入相鄰重複狀態；不按時間排序、不推定合法性、因果或末筆狀態的持續時間。輸出含來源 SHA-256、分組、筆數、轉移次數與相容模型；未指定輸出只回傳 JSON，指定輸出不覆寫已有檔案。

`diagram validate` 能辨識上述三類、block／block-beta、timeline、gantt 與前置設定，只檢查宣告及回報 neo 檔頭提示，不解析完整語法、不計算自寫圖的節點或字數。`render ... --execute` 才啟動原生工具，可用 `--tool` 與重複 `--tool-arg` 指定真正的 executable／JS 入口，保留既有輸出。缺 `mmdc` 回報 UNAVAILABLE，不安裝或改用 AI 生成圖片；成功輸出仍須檢查圖意與版面。[圖解範例](../examples/diagrams/README.md)與[trace 範例](../examples/trace/README.md)各列觀察範圍。

## 二進位檔：數值、位元欄位與 hex dump

`binary` 只需標準庫，唯讀指定的已儲存檔案，任何副檔名皆可。下列步驟在框架根目錄執行；已配置專案改用 `.agf/managed/agf-cli.md` 所列 CLI 路徑。`offset` 是從檔案開頭算起、以 byte 為單位的位移；整數參數可用十進位或 `0x` 十六進位。

先建立 8 bytes 的教學檔；這段只建立合成資料，若檔案已存在會拒絕覆寫。可以在 PowerShell 或 Linux shell 貼上整段：

```console
python -c "from pathlib import Path
p = Path('.agf/artifacts/bin-demo.bin')
p.parent.mkdir(parents=True, exist_ok=True)
with p.open('xb') as f:
    f.write(bytes.fromhex('34 12 AB 80 01 FF 00 41'))"
```

再讀兩個 bytes、讀跨 byte 欄位，以及查看完整原始排列：

```console
python scripts/agf.py binary bytes .agf/artifacts/bin-demo.bin 0x0 2
python scripts/agf.py binary bits .agf/artifacts/bin-demo.bin 0x3 7 2
python scripts/agf.py binary dump .agf/artifacts/bin-demo.bin 0 8
python scripts/agf.py binary bytes .agf/artifacts/bin-demo.bin 0 2 --endian big
```

第一個結果是 `value_hex: "0x1234"`、`value_decimal: "4660"`；第二個從 `80 01` 的第一個 byte 之 bit 7 開始讀 2 bits，得到 `0x3`／`"3"`。最後一個明確改為 big-endian，得到 `0x3412`／`"13330"`。`dump_lines` 每列含位移、至多 16 bytes 的 hex 及可列印 ASCII；控制字元顯示為 `.`，原始資料未被改寫。

| 命令 | 範圍與解讀 |
|---|---|
| `binary bytes FILE OFFSET SIZE [--endian little\|big]` | 一次將 1–64 bytes 當成無號整數；預設 little-endian |
| `binary bits FILE OFFSET BIT_OFFSET NUM_BITS` | `BIT_OFFSET` 0–7、`NUM_BITS` 1–64；固定 little-endian／LSB-first，最多跨 9 bytes |
| `binary dump FILE OFFSET LENGTH` | 1–4096 bytes 的原始 hex／ASCII；不做端序轉換 |

little-endian 表示低位元組在前；LSB-first 表示先從最低位元起算。它們是兩項獨立約定，不能因為檔案是 big-endian，就推定 bit 0 的位置。只提供欄位名、硬體位址或 signed／MSB 編號時，先核對規格及檔案對照，不直接猜參數。更大的檔案可分段讀，不先掃整檔。

成功數值包含 `raw_hex`、`value_hex`、十進位字串 `value_decimal` 及實際 `byte_order`；bits 另列位元順序、起點與寬度。共用資訊含要求／實得 bytes、開檔時大小與 `range_sha256`，後者只對實際片段計算，不是整檔雜湊，也不證明來源沒有並行變更。JSON 的十進位用字串，保留超過一般 JavaScript 整數精度的數值。

負數、零長度、超限或 `offset + 讀取量` 超過有號 64-bit 檔案位置時，讀檔前就拒絕。`bytes/bits` 檔尾不足回傳 ERROR 與非零退出碼，不輸出假數值；`dump` 則回傳已讀列、`PARTIAL`、要求／實得長度，退出碼為 1。上述示範改為 `dump ... 0 16` 就會得到 8／16 bytes 的部分結果；呼叫者必須檢查狀態與退出碼。缺檔、無權讀取及一般操作錯誤為非零；參數解析錯誤使用標準 help／錯誤輸出。

開啟前後都確認一般檔案，POSIX 系統可用時加非阻塞旗標，避免檔案被換成 FIFO（具名管道）後卡住；一般檔案的 symlink 仍可沿用系統讀取行為。虛擬或網路檔案系統也可能呈現一般檔案，類型檢查不證明內容是靜態快照。這不是沙箱，也不保證所有檔案系統的競態或特殊路徑皆被隔離。沒有 Python 時使用已安裝的 `python3` 或 Windows `py -3`，不自動安裝解譯器。端序語意參考 [Python `int.from_bytes`](https://docs.python.org/3/library/stdtypes.html#int.from_bytes)，檔案操作依 [Python `os`](https://docs.python.org/3/library/os.html)。

## 執行、檢查與交接

```console
python scripts/agf.py run --cwd . --timeout 10 -- python examples/learning/queue_walkthrough.py
python scripts/agf.py run --output-dir .agf/runs/queue-01 --max-chars 2000 -- python examples/learning/queue_walkthrough.py
python scripts/agf.py run --max-output-bytes 1048576 -- python examples/learning/queue_walkthrough.py
python scripts/agf.py check --root . --config templates/quality.framework.json --profile full
python scripts/agf.py task record --input examples/task.json --root . --output .agf/task.json
python scripts/agf.py task check .agf/task.json
python scripts/agf.py git scope --repo . --allow agf --allow tests
```

`run` 會真的執行傳入的程式，需在當次授權內。它用參數陣列，支援 `--max-chars`、`--encoding`、逾時與截斷回報；`.cmd/.bat` 需專用接線。品質 JSON 的 `{python}` 換成目前 interpreter；空檢查不能通過。

`--max-chars` 只限制回傳文字。需要限制原始輸出時，另用 `--max-output-bytes N`，限制 stdout、stderr 合計保存的 bytes；品質 JSON 的單項 check 也可設 `max_output_bytes`。超限會停止命令並回傳 FAIL、結果內 `exit_code: 125`，CLI 自身退出 1；逾時仍為 124。恰好等於上限且完整結束可通過。`capture_complete: false` 表示證據不完整，`process_exit_code` 保留子程序實際退出碼；`stdout_bytes`／`stderr_bytes` 只代表已保存量，不能當成原程式總輸出，無法取得長度時為 `null`。即使子程序已回 0，輸出超限或擷取失敗仍不能通過；命令已執行，不應只為補回輸出而重跑可能有副作用的操作。

未指定 byte 上限時會持續暫存輸出，大量輸出仍可能耗盡磁碟。兩種模式都等待父程序結束及 stdout／stderr 管線關閉；後代若繼續持有管線，會等到管線關閉或逾時，逾時回報不完整擷取。這不代表後代若自行關閉或重新導向管線，便已經結束。上限不涵蓋 metadata、程式自行寫檔、記憶體或網路，也不是程序隔離。POSIX 會嘗試清除 process group；Windows 在父程序先退出、後代仍持有管線時，會回報 `parent_exited_descendants_unknown` 與不完整擷取，不能保證清除後代。需要完整診斷時提高上限或縮小命令輸出，不為補記錄自動重跑有副作用的命令。

需要保存診斷時，可選 `run --output-dir DIR`。路徑相對於呼叫 CLI 的目錄，不隨 `--cwd` 改變；目錄必須尚未存在，包含 symlink 在內的既有目的地一律拒絕。命令啟動前先建立並開啟三個檔案：`stdout.bin`、`stderr.bin` 保存已擷取 bytes，`result.json` 記錄退出碼、編碼、byte 數、摘要是否截斷及檔案路徑。超限、非零退出和逾時的輸出也會保存；未指定此選項時不留下額外紀錄。保存的內容沒有自動脫敏，依任務選擇本機位置與分享範圍。

POSIX 環境以 `0700` 建立最終保存目錄，不調整既有父目錄；其他平台依本機存取控制處理，這不是隔離或自動隱私保證。若命令完成後 metadata 保存失敗，回傳的 `evidence.metadata_saved` 為 false，並保留實際執行結果；命令的 PASS／FAIL 與紀錄是否存妥須分開看。先查原始輸出及當前狀態，不為補紀錄重跑已完成的寫入。啟動前的準備失敗可能留下新建目錄與空檔，錯誤會明示命令未啟動。

Task 記錄可明列任何本地檔案，不依賴 Git。`verification`、`next_steps`、`boundaries` 是可選的字串陣列，分別保留已做／未做的驗證、下一步及操作範圍；驗證項目應寫實際時間與結果位置。`checks` 也是可選的字串陣列，寫接手者要自己執行的核對命令和預期結果；`task handoff` 把它放在最前面一節。工具自動加入的 UTC `recorded_at` 只代表建立紀錄的時間，不代表剛重跑過測試。`task handoff .agf/task.json --output .agf/handoff.md` 會核對證據並產生交接；舊版 v1 紀錄仍可讀取，未記載的續接資訊不會自行補造。

每個里程碑都寫一份完整的 task 紀錄太重時，用 `task checkpoint`：只寫已完成、進行中、下一步三種，可重複。加 `--repo .` 會補上分支、HEAD 與未 commit 的路徑，這些由程式收集，不靠記憶；加 `--append <交接檔>` 會把一段「檢查點」接在那個既有檔案的最後，不改動其他內容。例如：

```console
python scripts/agf.py task checkpoint --done "parse() 完成（a1b2c3d）" --doing "format()" --next "跑 format 的測試" --repo . --append HANDOFF.md
```

只有選用 `--repo` 才保存 Git 身分；SVN revision 或其他版本條件可用原生命令取得並列為證據。hash 相同只是檔案身分檢查，接手仍需讀來源及目前變更。`git summary/scope` 維持 Git 專用，不包裝成通用版本控制 API。

Git 狀態無法可靠解碼為 UTF-8 時，交接紀錄會報錯，不將替代字元當成原始路徑。`git summary/scope` 和 `task record --repo` 會執行本機 Git：雖然 diff 已停用 textconv／external diff，Git 仍可能依本機設定啟動 clean filter（將工作檔轉換後再交給 Git 的外部程式）。對不可信的工作目錄或 Git 設定應先審查、使用適當隔離；這些命令不是 sandbox。停用文字轉換後，較早記錄的 Git 狀態雜湊可能改變；先檢查實際差異，再決定是否重新記錄交接。

## Hooks 與範本

Docker 範本是執行 `doctor` 的最小示範，不包含完整框架。從框架根目錄使用 `docker build -f templates/Dockerfile -t agf-doctor .` 時，Docker 會讀取同目錄的 `templates/Dockerfile.dockerignore`；它允許的原始程式檔只有 `agf/*.py` 與 `scripts/agf.py`，Dockerfile 也只複製這些檔案。Docker 仍需把 Dockerfile 和忽略檔本身送給 builder（建置器），這些檔案也不應包含秘密。建置會取得基礎 image，執行前應依當次授權處理。

若透過 `integration template` 匯出，需同時匯出 `dockerfile` 和 `dockerfile-ignore`，把後者命名為「Dockerfile 檔名加上 `.dockerignore`」並放在 Dockerfile 旁；例如 `Dockerfile` 搭配 `Dockerfile.dockerignore`。Dockerfile 專屬忽略檔會優先於 context 根目錄的 `.dockerignore`，因此不能以為兩者會自動合併。通用的 `dockerignore` 範本另需放到 context 根目錄並命名 `.dockerignore`，用途與專屬白名單不同。兩者都不保證辨識所有秘密：檢查實際 build context、允許的來源檔、使用的 builder 與影像，再決定是否建置或分享。Docker 端的行為見[官方文件](https://docs.docker.com/build/concepts/context/#dockerignore-files)。

另一個 doctor 範本可從框架根目錄執行 `docker compose -f templates/docker-compose.yml run --rm doctor`。Compose 預設以該設定檔所在目錄解析相對路徑，兩個唯讀掛載分別指向框架的 `agf/` 與 `scripts/agf.py`；使用 `--project-directory` 或搬移設定檔時須重新核對路徑。唯讀掛載仍讓容器讀取整個 `agf/` 目錄，請先檢查內容；`network_mode: none` 不阻止事前拉取 image。掛載與權限需依實際 Docker／Windows 環境驗證。

```console
python scripts/agf.py integration list
python scripts/agf.py integration template quality
python scripts/agf.py integration template opencode-plugin
python scripts/agf.py integration hook --target ../my-project --kind git
```

Git hook 與 OpenCode plugin 依同一 manifest 選共享來源或工具副本。先確認目標的 `.agf/quality.json` 是真正需要的檢查；Git hook 保留既有檔案，AI hook 先看版本相關接線計畫。OpenCode 範本只對成功的 edit/write 執行 quick checks，沒有涵蓋所有 shell、patch 或外部修改。

`check --profile periodic` 只跑在 `profiles` 裡寫了 `periodic` 的檢查，給很慢、平常不跑、卻最容易悄悄壞掉的檢查用：文件教讀者執行的示範、README 裡的命令、在新目錄從頭建置。`integration template quality` 的範本附了這三種的例子，換成專案真的有的腳本，沒有的就刪掉。宣告一個階段完成或打 tag 之前，`full` 和 `periodic` 都跑一次。

Git hook 的 `--apply` 與 `check --profile quick` 共用設定驗證：檢查名稱、參數陣列、profiles、工作目錄、timeout 及 encoding，並要求至少一項 quick 檢查。無效設定會在寫入 hook／安裝紀錄前拒絕；安裝時不執行設定中的命令。實際執行檔是否可用、命令是否成功，仍要在授權範圍內執行檢查確認；安裝成功不代表檢查已通過。

額度用完、對話被壓縮或換模型時，用 continuity hooks 把狀態留在檔案裡：`integration template claude-continuity-hook` 取得程式，`integration template claude-continuity-settings` 取得設定寫法。
它們做的事：session 開始時，若專案有交接檔（預設找 `HANDOFF.md`、`.ai/HANDOFF.md`、`docs/HANDOFF.md`）或上次留下的檢查點，提醒 AI 先讀；恢復一個快取已過期的舊對話時，告訴使用者重新讀入的估計費用。壓縮前要求摘要保留任務、決定、commit 與下一步；壓縮後、API 出錯（例如額度用完）、session 結束、換模型前，把 git 狀態、錯誤、AI 最後一則訊息與壓縮摘要寫進 `.agf/checkpoints/latest.md`（另留最近 10 份）。換模型時若快取還熱、重新寫入估計超過 0.5 美元，顯示費用提醒，預設不擋。AI 準備結束時，若這個 session 在交接檔最後一次修改或 commit 之後又做了 commit，提醒更新一次。
設定加 `"save_prompts": true`，並在 `UserPromptSubmit` 事件裝 `claude-continuity-hook.py user-prompt <設定檔>`，hook 會留下這個 session 使用者說過的話（每則最多 2,000 字、最多 20 則），檢查點附上最新的 5 則；這一段太長時，先捨掉較舊的。存下的檔案在 `.agf/checkpoints/`，7 天沒用到才刪除。這是為了「重要的決定只在對話裡說過」的情況：session 被截斷之後，新的 session 從檢查點看得到它。預設關閉，因為打進對話的東西可能有密碼或金鑰；開啟前確認 `.agf/` 不會被 commit 或分享。沒有交接檔也沒有檢查點時，它們什麼都不輸出，不增加 token。檢查點只有程式收集得到的事實，計畫與決定仍要寫在交接檔裡。`.agf/` 若不在專案的 `.gitignore`，記得加上。2026-11-18 用 Claude Code 2.1.325 的無頭 session 實測：SessionStart、Stop、SessionEnd 都會觸發；PreCompact、PostCompact、StopFailure（包括額度用完時會不會觸發）、PreModelSwitch 只有單元測試，Stop 的提醒模型有沒有照做也沒有實測。同一天的量測裡，4 個接手的新 session 都先讀了檢查點，但工作狀態本來就在檔案裡，沒有省到錢（[量測紀錄](../studies/research-2026-11/G-measurement-2026-11-18.md)）。

原生權限擋不住的寫法（`git -C . push`、`sh -c`、從上層目錄啟動的 session），改用 guard hook：`integration template claude-guard-hook` 取得 PreToolUse hook 的程式，`integration template claude-guard-settings` 取得加進設定檔的寫法，再用一個 JSON 列出受保護的路徑。裝在 `~/.claude/settings.json` 時每個 session 都生效。它只看命令列，看不到程式執行後做的事、變數裡的路徑或執行時才組出的命令。heredoc（用 `<<EOF` 把多行文字接在命令後面）的內容，只有交給 shell 執行時（例如 `bash <<'EOF'`）才當命令檢查，其他時候只檢查會展開的 `$(...)` 與反引號；涵蓋與不涵蓋的寫法見程式開頭的說明與 `tests/test_guard_hook.py`。

Claude Code 的原生權限可從 `integration template claude-permissions` 取得範本：擋受保護目錄的 Edit 與 Write，也擋 `git push` 與建立 PR／MR。把 `//ABSOLUTE/PATH/TO/PROTECTED/**` 換成實際的絕對路徑（`//` 開頭表示從根目錄算起），審閱後再合併進專案的 `.claude/settings.json`；`project install` 不會替你寫入。佔位路徑沒換掉時，Edit 與 Write 的規則什麼都不保護。這份設定只在 Claude Code 從該專案目錄啟動時載入；從上層目錄啟動的 session 用不到它。2026-11-16 用 Claude Code 2.1.325 實測（每種情況一次）：Read 的規則擋下 Read、Glob 與 Grep；Edit、Write 的規則擋下這兩個工具，`cp` 寫進被保護的路徑也被擋，`python3 -c` 卻寫得進去。命令規則只比對開頭：`git push`、`gh pr create`、`glab mr create` 被擋，`git -C . push` 沒有。允許的工具裡沒有 Bash 時，`find`、`head` 這類唯讀命令仍會在工作目錄裡執行；要整個拿掉 Bash，用 `--disallowedTools Bash`。逐項紀錄與沒驗到的部分見 `adapters/claude.json` 的 `permissions`。

MCP 選用改查[工具指引](tools.md)，不維護另一套 Python 名單與未實測的跨 host 設定產生器。Commit 理由直接依[寫作指引](writing.md)和目標專案慣例撰寫，純文字拼接不再需要 `git intent`。v0.2 因此移除 `integration mcp` 與 `git intent`；其他 helper 依實際增益選用。

# CLI 操作

在 framework checkout 使用 `python scripts/agf.py`；在已配置專案使用 `python .agf/managed/runtime/scripts/agf.py`。以下採第一種入口。核心不需要先用 pip 安裝。

CLI 輸出 JSON。一般成功為退出碼 0，檢查失敗或差異為非零；錯誤參數／無法操作通常為 2，選用能力缺失可為 3。以各回傳的 `status` 及說明判讀：`PLAN`、`RECORDED`、`HEADER_RECOGNIZED` 和 `PASS` 的意義不同。

`audit` 檢查 framework checkout；目標專案的已配置快照用 `project status --target DIR` 核對。Windows Git 若拒絕 WSL-owned UNC 目錄的所有權，先核對工作環境與信任設定，或使用該 WSL 內的 Git；helpers 會保留這個錯誤，讓使用者決定。

## 查能力、偏好與配置

```console
python scripts/agf.py doctor --host opencode
python scripts/agf.py profile show --no-user
python scripts/agf.py project plan --target ../my-project --host opencode
python scripts/agf.py integration list
```

Doctor 只找執行檔位置，不啟動宿主或確認登入。各 host adapter 的檔案入口、hooks 文件及驗證狀態在 `adapters/`。目前模型與 CLI 的實際可用性仍需在使用環境核對。

## 檢索與來源

```console
python scripts/agf.py context extract agf/execution.py --start 1 --end 70 --max-chars 6000
python scripts/agf.py context search timeout --root . --glob '*.py' --max-results 12
python scripts/agf.py source excerpt examples/research/mini-spec.md --query capacity --max-chars 2000
python scripts/agf.py source inspect examples/research/mini-spec.md
```

`context search` 使用既有 ripgrep。`source` 目前接受 PDF、HTML、TXT、MD、RST、LOG；JSON 結構差異請用 `files diff --format json`。摘錄的字元上限不等於模型 token 數。文字搜尋與文字差異提供線索，語意、呼叫關係及規範變更需回查來源。

PDF `inspect` 只查頁數與 metadata，沒有抽字就不推斷空白頁。`excerpt --pages 2,4-6` 只對選定實體頁抽字。靜態網頁可先用 `source fetch URL --output .agf/page.html` 預覽，再加 `--execute`；範圍與限制見[網頁擷取範例](../examples/research/web-fetch.md)。

## 執行與品質證據

```console
python scripts/agf.py run --cwd . --timeout 10 -- python examples/learning/queue_walkthrough.py
python scripts/agf.py check --root . --config templates/quality.framework.json --profile full
```

`run` 接參數陣列，明確的 `--` 分隔工具選項和被執行命令。它會真的執行該程式，適用於目前任務已授權的操作。可用 `--max-chars` 控制輸出，`--encoding` 指定子程序實際輸出編碼；解碼錯誤與截斷會另外回報。呼叫者明確執行 shell 時，該 shell 自己仍會解讀其參數。

Windows 的 `.cmd`／`.bat` shim 需要工具專用接線。以 Mermaid 為例，可對 `diagram render` 指定 `--tool` 為真正的 node.exe，再以 `--tool-arg` 傳入 JS 入口。工具不會以組合 shell 字串的方式猜測處理。

品質 JSON 的 `{python}` argv 元素會換成目前 Python 路徑。`cwd` 限於指定 root 之內。自訂命令仍須先確認用途、依賴及授權；品質設定本身不會授予權限。

## 交接與 Git

```console
python scripts/agf.py task record --input examples/task.json --root . --repo . --output .agf/task.json
python scripts/agf.py task check .agf/task.json
python scripts/agf.py task handoff .agf/task.json --output .agf/handoff.md
python scripts/agf.py git summary --repo .
python scripts/agf.py git scope --repo . --allow agf --allow tests
python scripts/agf.py git intent --subject 'Cancel timed-out work' --why 'Timed-out work kept its buffer until completion.' --validation 'Cancellation regression passed; hardware not tested.'
```

Task 記錄明確列出的檔案 hash；`--repo` 另外保存 HEAD、tracked diff 與 Git status 身分。未追蹤檔案的內容要另列 evidence。hash 相同只能支持「檔案沒變」，不能支持裡面的結論正確；接手者仍需看來源和目前 diff。

`git scope` 提供目前變更是否落在宣告路徑內的提示，涵蓋 staged、unstaged 與 untracked 檔案。它不是檔案寫入隔離。Commit 草稿使用你提供的理由及實際驗證，不會自行推測當時動機。

## 圖解與檔案批次

```console
python scripts/agf.py diagram create examples/diagrams/files-transaction.json --format mermaid
python scripts/agf.py diagram create examples/diagrams/files-transaction.json --format drawio --output .agf/files.drawio
python scripts/agf.py diagram trace examples/trace/gdb-fixture.txt --format gdb --output .agf/trace.html
python scripts/agf.py files diff examples/files/before.json examples/files/after.json --format json
python scripts/agf.py files rename examples/files/sample --pattern '^draft-' --replace 'final-'
```

預覽改名不會修改檔案。可加 `--plan-output .agf/rename.json` 保存計畫；`files apply .agf/rename.json --apply` 才套用。套用前會重新檢查來源與目標。操作中斷後若留下交易目錄，先保留原件並核對紀錄；詳見 [檔案範例](../examples/files/README.md)。

`diagram create` 可從精簡模型產生 flowchart、sequence、state Mermaid，或產生未壓縮 draw.io XML。原生 Mermaid 的其他語法可直接交給已授權的官方工具。`diagram validate` 的 Mermaid 結果只代表辨認到圖類宣告；完整語法與畫面要用 native render 驗證。

`diagram render ... --execute` 才啟動原生工具。已有輸出不會被覆寫。Trace HTML 為離線紀錄瀏覽器，GDB stack 和部分 ftrace 格式各有觀察範圍。

## OpenCode 自動 quick check

```console
python scripts/agf.py integration template opencode-plugin
python scripts/agf.py integration hook --target ../my-project --kind ai --host opencode
```

先確認 host 版本、專案 runtime 與 `.agf/quality.json`，再依回傳計畫放置 plugin。範本對成功的 edit/write 執行 quick checks，記錄 PASS、FAIL 或 SKIP。它不涵蓋 shell、patch 與外部編輯。V1/V2 callback contract 已用 fixture 呼叫真 Python checker，真實 OpenCode 載入狀態仍在驗證紀錄中個別列明。

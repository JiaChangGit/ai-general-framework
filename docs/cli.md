# CLI 操作

在 framework checkout 用 `python scripts/agf.py`。已配置專案的有效入口寫在 `.agf/managed/project-rules.md`；共享模式使用來源 checkout，副本模式使用專案內 `.agf/managed/runtime/scripts/agf.py`。核心不需 pip 安裝。

CLI 輸出 JSON；檢查失敗或有差異回傳非零。錯誤通常為 2，選用能力缺失可為 3。`PLAN`、`RECORDED`、`HEADER_RECOGNIZED` 與 `PASS` 意義不同，依輸出的說明判讀。

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

新配置預設不額外選 skills、共用工具。`--tools copy` 才帶工具副本。舊 manifest 沒有模式欄位時視為 copy；更新沿用選擇，明確指定才改。更新會列出來源已移除的受管理 skill，套用前保留 drift、未受管理檔與回復檢查；沒有永久別名或中央專案登錄服務。

偏好來源為框架預設、使用者設定、專案 `.agf/profile.json`，較近的物件逐層合併，清單取代。Windows 使用者路徑為 `%APPDATA%/ai-general-framework/profile.json`；Linux 為 `${XDG_CONFIG_HOME:-~/.config}/ai-general-framework/profile.json`。可明示 `--user`／`--project`；`profile init --output PATH` 先預覽，`--apply` 才建立且不覆寫。個人偏好不授予工具權限。

Manifest 是記錄受管理檔案、來源和模式的清單。`status` 分別顯示檔案是否被本地修改，以及工具入口是否仍可讀；檔案乾淨不代表已刪除的共享來源還能使用。工具入口可讀也不等於原生工具已登入或通過功能驗證。

## 來源、檔案與圖解

```console
python scripts/agf.py context search timeout --root . --glob '*.py' --max-results 12
python scripts/agf.py context extract agf/execution.py --start 1 --end 60 --max-chars 6000
python scripts/agf.py source excerpt examples/research/mini-spec.md --query capacity
python scripts/agf.py files diff examples/files/before.json examples/files/after.json --format json
python scripts/agf.py diagram create examples/diagrams/files-transaction.json --format mermaid
```

`context search` 使用既有 ripgrep。PDF 抽字需選用 pypdf，`inspect` 只查 metadata，`excerpt --pages 2,4-6` 才抽指定實體頁。靜態頁用 `source fetch URL --output FILE` 預覽，加 `--execute` 才連網保存；[範例](../examples/research/web-fetch.md)列出 robots、上限及 TLS 行為。

`files rename/normalize` 預設預覽，可保存計畫後以 `files apply PLAN --apply` 套用。管理資料 `.git`、`.svn`、`.hg` 在列檔與套用時都受保護；一般隱藏檔仍照常處理。它不解讀 `.gitignore` 或 `svn:ignore`。碰撞、來源重驗與失敗回復見[批次範例](../examples/files/README.md)。

`diagram create` 保留來源模型；Mermaid 宣告檢查不是完整語法或語意驗證。`render ... --execute` 才啟動原生工具，可用 `--tool` 與重複 `--tool-arg` 指定真正的 executable／JS 入口，保留既有輸出。[圖解範例](../examples/diagrams/README.md)與[trace 範例](../examples/trace/README.md)各列觀察範圍。

## 執行、檢查與交接

```console
python scripts/agf.py run --cwd . --timeout 10 -- python examples/learning/queue_walkthrough.py
python scripts/agf.py check --root . --config templates/quality.framework.json --profile full
python scripts/agf.py task record --input examples/task.json --root . --output .agf/task.json
python scripts/agf.py task check .agf/task.json
python scripts/agf.py git scope --repo . --allow agf --allow tests
```

`run` 會真的執行傳入的程式，需在當次授權內。它用參數陣列，支援 `--max-chars`、`--encoding`、逾時與截斷回報；`.cmd/.bat` 需專用接線。品質 JSON 的 `{python}` 換成目前 interpreter；空檢查不能通過。

Task 記錄可明列任何本地檔案，不依賴 Git。只有選用 `--repo` 才保存 Git 身分；SVN revision 或其他版本條件可用原生命令取得並列為證據。hash 相同只是檔案身分檢查，接手仍需讀來源及目前變更。`git summary/scope` 維持 Git 專用，不包裝成通用版本控制 API。

## Hooks 與範本

```console
python scripts/agf.py integration list
python scripts/agf.py integration template quality
python scripts/agf.py integration template opencode-plugin
python scripts/agf.py integration hook --target ../my-project --kind git
```

Git hook 與 OpenCode plugin 依同一 manifest 選共享來源或工具副本。先確認目標的 `.agf/quality.json` 是真正需要的檢查；Git hook 保留既有檔案，AI hook 先看版本相關接線計畫。OpenCode 範本只對成功的 edit/write 執行 quick checks，沒有涵蓋所有 shell、patch 或外部修改。

MCP 選用改查[工具指引](tools.md)，不維護另一套 Python 名單與未實測的跨 host 設定產生器。Commit 理由直接依[寫作指引](writing.md)和目標專案慣例撰寫，純文字拼接不再需要 `git intent`。v0.2 因此移除 `integration mcp` 與 `git intent`；其他 helper 依實際增益選用。

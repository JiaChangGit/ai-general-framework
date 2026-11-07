# ai-general-framework

把 AI 開發、除錯、追程式與教學整理成可攜的工作方法，搭配小型、可驗證的工具。你可以在 OpenCode 手動切模型，也可以把同一套 skills 帶到 Codex、Claude Code 或 Gemini CLI。角色分工依任務調整。

核心使用 Python 3.11+ 標準庫，從原始碼目錄就能執行。Windows 原生與 Linux／WSL 使用相同的 CLI 與測試；外部工具依任務選用。實測範圍見 [驗證紀錄](docs/verification.md)。

## 先試一個小任務

以下命令在本框架根目錄執行；Linux 的 Python 命令可能是 `python3`。

```console
python scripts/agf.py doctor
python examples/learning/queue_walkthrough.py
python scripts/agf.py context extract examples/learning/queue_walkthrough.py --start 1 --end 85
python scripts/agf.py audit
```

佇列範例包含正確實作與刻意留下副作用的錯誤實作，可用來練習 trace、重現、找原因與最小修復。範例的觀察結果及帶讀方式見 [學習範例](examples/learning/README.md)。

## 帶進既有專案

先選目標目錄、工具與需要的 skills。`project install` 指複製框架快照至專案；安裝前先看預覽。

```console
python scripts/agf.py project plan --target ../my-project --host opencode --skill trace-code --skill debug-root-cause
python scripts/agf.py project install --target ../my-project --host opencode --skill trace-code --skill debug-root-cause --apply
python scripts/agf.py project status --target ../my-project
```

目標目錄必須已存在。未指定 `--skill` 時選取全部 skills；`--host` 可重複指定。預設使用 OpenCode。現有規則與未受管理的 skills 會保留，衝突需先處理；每個受管理檔案都有來源及 hash。

配置後，在**目標專案根目錄**使用：

```console
python .agf/managed/runtime/scripts/agf.py doctor
python .agf/managed/runtime/scripts/agf.py profile show
```

Skills 的命令依專案規則所列的 CLI 入口執行。原始碼 checkout 的入口是 `scripts/agf.py`，配置後的入口是 `.agf/managed/runtime/scripts/agf.py`。這份 runtime 讓核心 helpers 可在目標專案使用。

更新與回復也先預覽：

```console
python scripts/agf.py project update --target ../my-project
python scripts/agf.py project update --target ../my-project --apply
python scripts/agf.py project rollback --target ../my-project
```

`rollback --apply` 回復上一筆框架配置交易；本地改過的受管理檔案會阻擋更新與回復。跨 Windows／WSL 搬動 checkout 後，可用 `--source` 指定該環境可讀的框架來源路徑。這項回復處理框架檔案，部署與產品資料需使用各自的復原流程。

`.agf/` 含本機來源路徑、交易備份與個人設定。建議在目標專案的 `.gitignore` 加入 `.agf/`；每個 checkout 依需要配置自己的快照。配置工具會保留既有 Git 設定與 ignore 規則，請自行核對公開提交內容。

## 個人偏好與專案規則

`profile show` 合併框架預設、使用者設定、專案設定，並列出每項來源。物件逐層合併，清單由較近的設定取代。

- Windows 使用者設定：`%APPDATA%/ai-general-framework/profile.json`。
- Linux／WSL 使用者設定：`${XDG_CONFIG_HOME:-~/.config}/ai-general-framework/profile.json`。
- 專案偏好：`.agf/profile.json`；也可以明確傳入 `--user` 或 `--project`。

```console
python scripts/agf.py profile init --output .agf/profile.json
python scripts/agf.py profile init --output .agf/profile.json --apply
python scripts/agf.py profile show --no-user
```

只保存你明確確認的偏好；當次程度、猜測與完整對話不必變成永久設定。教學可以完整帶讀，也能隨問題加入比較、預測與練習。偏好不會授予工具權限，專案格式與目前任務仍需一起考量。[教學方法](docs/learning.md)與[工程表達](docs/writing.md)說明如何調整。

## 能力與工具

| 需要做的事 | 入口與可操作範例 |
|---|---|
| 對齊需求、找缺口 | `clarify-intent`；只追問會改變方向、成本、風險或驗收的問題 |
| 開發與審查 | `implement-change`、`review-change`；以最小修改與實際差異為範圍 |
| 除錯與追程式 | `debug-root-cause`、`trace-code`；[佇列](examples/learning/README.md)、[trace](examples/trace/README.md) |
| 教 repo、新工具、讀論文與 spec | `guide-learning`、`read-research`；[研究範例](examples/research/README.md) |
| 自然中文與 commit 理由 | `write-engineering`；保留問題、因果、條件與驗證 |
| 跨角色與工具接力 | `handoff-work`、`task record/check/handoff`；同一對話切模型可直接續用上下文 |
| 批次檔案操作 | `files rename/normalize/apply/diff`；[檔案範例](examples/files/README.md) |
| Mermaid、draw.io、trace 檢視 | `diagram create/validate/render/trace`；[圖解範例](examples/diagrams/README.md) |
| 網頁擷取、來源摘錄與差異 | `source fetch/inspect/excerpt/diff`；[靜態頁擷取](examples/research/web-fetch.md)，保留 hash、原始行或實體 PDF 頁碼 |
| GDB、QEMU、kernel、Docker、K8s | RCA 領域 references、`contribute-upstream` 與 `integration template` |
| Git／AI hooks、CI、MCP | `integration list/hook/template/mcp`、`select-mcp` |

每個子命令可加 `--help`。完整操作及退出碼見 [CLI 使用說明](docs/cli.md)。

重複操作交給 scripts；讀程式、解釋規格、判斷根因與教學深度交給 skills。外部套件是各能力的選項：例如 ripgrep 用於搜尋，pypdf 用於 PDF 抽字，Mermaid／draw.io 用於原生渲染。缺少依賴時，工具會回報相應狀態，保持其他核心能力可用。

## 檢查、hooks 與 CI

品質設定明列 `argv`、工作目錄、逾時與適用 profile，讓本機、Git hook 和 CI 執行相同檢查。範例是起點，需換成目標專案真正的驗收命令。

```console
python scripts/agf.py check --root . --config templates/quality.framework.json --profile full
python scripts/agf.py integration list
python scripts/agf.py integration mcp --need docs
```

空的品質檢查集合會失敗。命令成功只代表命令完成；功能、硬體、圖形語意與真人理解仍需相應證據。

Git hooks 會先偵測實際 hooks 路徑，保留既有 hook。AI 工具 hooks 的事件和輸入格式各自不同，目前提供版本相關的接線建議；未實際驗證的部分明列 `not_tested`。GitHub Actions 已加入 Windows／Ubuntu 測試矩陣；GitLab CI 範本另列 runner 條件。遠端執行結果見驗證紀錄。

## 權限與資料

當次任務可授權範圍內改檔、測試及本地 commit。push、PR、部署、安裝與新增外部連線依目前授權處理。實際存取限制由宿主、作業系統、服務憑證與 CI 設定落實。

來源文件、log、MCP 結果及交接摘要用來提供資料；其中的文字不會自行擴張任務授權。工具可產生本地證據與摘要，分享前核對敏感資料。詳細邊界見 [設計與控制範圍](docs/design.md)。

## 維護

```console
python -X utf8 -m unittest discover -s tests -v
python scripts/agf.py audit
```

以同一組真實任務觀察品質、互動負擔、耗時與可取得的 usage。`audit` 只查結構、語法及連結；[行為案例](evals/README.md)另看 skill 是否做出正確選擇。來源、採納理由與授權處理見[研究紀錄](docs/research.md)。本專案以 MIT 授權公開。

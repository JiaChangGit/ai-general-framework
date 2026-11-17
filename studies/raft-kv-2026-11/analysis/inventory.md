# 框架元件盤點（唯讀，2026-11-16）

對象：`/home/user/src/ai-general-framework`，HEAD `2569a91`，工作樹有 10 個未提交的修改（不是本專案造成的，從 L01 起就是這個數字）。
`agf audit --root <框架>`：PASS，0 個錯誤、0 個警告。它只檢查靜態結構、frontmatter、本機連結與 Python／JSON 語法，自己寫明「不量 routing、推理、文字或學習」。
執行前後框架的 `git status --porcelain` 相同，也沒有比執行前新的檔案，所以它沒有寫進框架。

## 1. 規模

| 部分 | 內容 |
|---|---|
| skills | 6 個：`debug-root-cause`、`guide-learning`、`read-research`、`review-change`、`review-sql`、`trace-code`。`SKILL.md` 共 142 行，另有 reference 8 份、181 行 |
| skill 的常駐成本 | 6 段描述合計 1,522 個字元，宿主每個 session 都會列出；`SKILL.md` 本文合計 4,606 個字元，用到時才載入 |
| 指引（`docs/`） | 17 份，1,521 行 |
| `agf` CLI | 14 個子命令（doctor、project、profile、integration、context、run、check、task、git、files、diagram、source、binary、audit）；`agf/` 3,075 行 Python；測試 16 個檔 |
| 宿主轉接 | claude、codex、gemini、opencode 四份 |
| templates | CI（GitHub Actions、GitLab CI）、Docker、k8s、git hook、OpenCode plugin、qemu-gdb、權限／偏好／品質範例、圖解、簡報、跨格式輸出、工具選型。不會部署到專案 |
| evals | `paired/`（2026-11-09 的結果）、`scenarios.json`（61 個情境）、`writing-cases.json`（13 個）、`database-review/` |
| 部署到本專案的 | `.claude/skills/` 五個 skill（與 `.agents/skills/` 相同）、`.agf/managed/project-rules.md`、四份指引（delivery、tools、workflow、writing，約 4.1 萬 bytes） |

## 2. 本專案實際用過哪些

證據是 `docs/FRAMEWORK_EXPERIENCE_LOG.md` 的條目編號；「沒有證據」指紀錄裡從沒提到用過。

| 元件 | 用過嗎 | 證據與說明 |
|---|---|---|
| `review-change` | 用過，經由 skill 機制 | S5 審查依它進行（審查報告開頭）；宿主列出後可以直接叫用（L47） |
| `read-research`、`guide-learning` | 讀了 `SKILL.md` 照做，沒有經由 skill 機制 | 當時宿主沒有列出 skill，直接讀檔是替代做法（L13） |
| `trace-code` | 計畫要用，實際沒用 | S2 改用「把欄位設為私有，讓編譯器列出所有存取點」，比閱讀追蹤更完整（L23） |
| `debug-root-cause` | 沒有證據 | 路線圖原訂「每個 bug 的根因與證據」都用它；19 篇教學的根因都在沒有它的情況下找出 |
| `review-sql` | 沒有部署 | 本專案沒有 SQL，合理 |
| 專案自己的 `write-bug-lesson`（不是框架的） | 用得最多 | 19 篇教學；它沒有連到框架的寫作指引（L52） |
| 指引 `workflow.md` | 用過 | 交接文件的欄位照它寫（L42） |
| 指引 `writing.md` | S7 之前沒被讀到 | L52、L53 |
| 指引 `tools.md`、`delivery.md` | 沒有證據 | — |
| `project-rules.md` | 不確定有沒有被讀到 | `AGENTS.md` 只有一句「適用時讀」；`CLAUDE.md` 只提到、沒有 import（見第 3 節第 1 點） |
| `agf project` | 用過 | 2026-11-12 先預覽、再套用 Claude 宿主（L02） |
| `agf source` | 試過一次，失敗 | 讀 PDF 需要選用的 pypdf，沒有安裝（L12） |
| `agf audit` | 用過 | 本盤點 |
| 其他 11 個 `agf` 子命令 | 沒有證據 | 同類需求都由宿主的原生工具（Read、Grep、Bash）或專案自己的 scripts 處理 |
| templates、hooks、MCP、CI | 沒有用 | 本專案只在本機開發，沒有 CI；權限設定見第 3 節第 6 點 |
| evals | S8 用 | 實驗 A、C 的材料 |

## 3. 重疊、衝突與沒觸發

1. **規則的入口沒有接上。** 在新目錄執行 `agf project install --host claude`，產生的 `CLAUDE.md` 只有兩行 import：`@AGENTS.md`、`@.agf/managed/project-rules.md`，每個 session 都會載入（D0）。
   本專案原本就有 `CLAUDE.md`；框架的轉接設定寫明「保留既有的規則檔，不存在時才建立 import」，所以本專案沒有這兩行。
   `project-rules.md` 與它點名的指引因此不會自動載入，只能靠模型自己決定去讀。轉接設定另說 Claude Code 2.1.277 以後在適當設定下可以直接讀 `AGENTS.md`；本專案沒有驗證這一點。實驗 C 量它的後果。
2. **`agf run` 與 `scripts/capped_run.py` 功能重疊。** 框架的 `agf run` 早就提供時間上限、輸出 byte 上限與保存原始輸出（`--timeout`、`--max-output-bytes`、`--output-dir`）。
   S5 審查遇到 mutation 的輸出灌爆記憶體時（教學 16），自己寫了 `capped_run.py`（480 秒、256 MiB、殺掉整個行程群組、只留頭尾）。兩者是否等價（例如 `agf run` 會不會一併殺掉子行程）沒有驗證；能確定的是，當時沒有人想到框架有這個工具。
3. **宿主層級的 skill 和框架的 skill 用途相近。** 這個帳號的 Claude Code 另有 `debug`、`code-review`、`verify`，外掛有 `anthropic-skills:deep-research`（D0 的清單）。
   它們分別和 `debug-root-cause`、`review-change`、`read-research` 重疊；兩者同時出現時宿主選哪一個，實驗 A 會看到。
4. **指引的使用不平均。** `workflow.md` 有用；`writing.md` 在 S7 之前沒被讀到；`tools.md`（18.9 KB，四份裡最長）與 `delivery.md` 沒有使用證據。
5. **11 個 `agf` 子命令沒有使用證據。** 這不代表它們沒用，而是在這個宿主上，沒有任何入口讓模型在對的時候想到它們。
6. **邊界靠手寫的設定。** 本專案 `.claude/settings.json` 的 deny 規則（擋框架目錄的 `Edit`、`git push`、`rtk git push`、`gh pr create`）是 S0 時依使用者要求手寫的，不是來自框架。
   框架的 `permissions.example.json` 自己標明是「政策範例，不是宿主原生設定」，README 也說「文字規則與 hook 不冒充強制隔離」。這份 deny 只擋 `Edit`，不擋 `Write` 或用 Bash 寫檔；
   session 從上層目錄啟動時它是否生效，也沒有驗證過（L50）。
7. **templates 不部署。** CI、Docker、k8s 等留在框架裡，需要時才拿，不會進到專案；本專案用不到，不算多餘。

## 4. 對第一項標準的小結

靜態結構乾淨（audit 通過），常駐的 token 成本很小（技能描述 1,522 字元）。主要的問題是「沒觸發」：規則與指引的入口沒有接到本專案的 `CLAUDE.md`，有用的工具（`agf run`）沒有人想到。
「重疊」主要來自宿主層級的 skill 與專案自己重寫的工具，不是框架內部的重複。

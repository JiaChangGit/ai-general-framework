# S8 規格草稿：ai-general-framework 的分析與對照實驗

狀態：**已核准**（使用者 2026-11-16「核准，開始 S8」；第 8 節的 D1～D4 照建議）。起草與實作的模型：`claude-opus-5-5`。
依據是路線圖「S7、S8 的依據」裡使用者列的 11 項標準，以及 S7 的報告。

## 1. 目的

- **一份分析報告**：照使用者的 11 項標準，逐項寫出框架的優點、缺點、改進建議與優先序，每一點都附證據。
- **三個小實驗**：補上框架自己 2026-11-09 的對照沒做到的部分。一是在 Claude Code 上的原生工具軌跡與實際用量；二是 skill 與按需指引在真實專案裡有沒有被觸發；三是跨供應商、跨模型的交接。

## 2. 已經存在、不重做的東西

| 東西 | 內容 | S8 怎麼用 |
|---|---|---|
| 框架 README「你要的能力，如何落實」 | 11 項需求各自的做法，和使用者的標準幾乎一一對應 | 報告逐項對照「它說怎麼做」與「實際發生了什麼」 |
| 框架 `evals/paired/`（2026-11-09，Codex） | 文字層對照：品質相同，框架組多用 14.4% 的 token；原生工具的對照拿不到用量；做過一次同供應商的跨模型交接 | 實驗 A、B 補它列為「未驗證」的部分 |
| 框架 `evals/README.md` 的「第一次在真實 host 驗證」四步驟，與 `scenarios.json`（61 個情境） | 寫好但還沒在 Claude Code 上執行的方法與案例 | 實驗 A 照四步驟做，從中挑情境 |
| 框架 `evals/writing-cases.json`（13 個） | 中文改寫的配對案例 | 實驗 C 取用 |
| 本專案的框架經驗紀錄 L01～L53、兩份獨立審查、S7 報告 | 實際使用時的觀察 | 報告的主要證據 |
| 本專案 `FRAMEWORK_IMPROVEMENT_PROPOSALS.md`、`FRAMEWORK_FEEDBACK.md`（2026-11-10～12） | 早期的建議與回饋 | 報告完成後，兩份文件開頭改成指向新報告；仍有效的建議併入新報告，避免兩份建議清單並存 |

## 3. 要做的事

### 3.1 框架元件盤點（唯讀）

列出框架的 skills、指引、`agf` 子命令、templates、hooks 與 evals。每一項記下：本專案有沒有用過（證據）、該用時有沒有被用到、和誰重疊或衝突、是不是多餘。
先跑框架自己的 `agf audit`；執行前後比對框架的 `git status --porcelain`，確認它沒有寫進框架，才採用它的結果。這一節對應使用者的第一項標準。

### 3.2 實驗的共同做法

- **受試者**是全新的 Claude Code session：用桌面 app 內附的 CLI（2.1.325）無頭執行，加上 `-p`、`--output-format stream-json`、`--no-session-persistence`，指定模型、限制可用的工具、每次設預算上限。
  全部在 `artifacts/runs/` 底下的隔離副本裡執行；框架只讀，不在框架目錄執行任何會寫檔的命令。
- **記錄**：模型、CLI 版本、框架 commit、配置了哪些 skill；每次的工具事件（含 Skill 呼叫、讀了哪些指引檔）、回合數、耗時、CLI 回報的 token 與費用。
  原始事件流存在 `artifacts/s8-<日期>/`，不進版本控制（裡面有本機路徑）；報告只放摘要與必要的摘錄。
- **先登記再執行**：提示詞、評分表與答案表在執行前提交，之後不改。結果不如預期也照實報告。
- **D0 探測**：正式執行前，先用 Haiku 5.5 跑一到兩次很短的任務，確認三件事：CLI 在桌面 app 之外能登入；事件流裡有工具事件與用量；在配置了框架的副本裡，session 看得到專案的 skill。
  任何一項不成立，就停下來回報，不改用拿不到用量的做法硬做。

### 3.3 實驗 A：skill 的觸發與誤觸

照框架 `evals/README.md` 的四步驟。

- **情境**：從 `scenarios.json` 挑 6 個自帶材料的情境。預期用 skill 的 4 個：`trace-without-lesson`（trace-code）、`learning-with-trace`（guide-learning）、
  `flaky-repeat-evidence`（debug-root-cause）、`cleaned-copy-is-not-original`（read-research）。預期不用 skill 的 2 個：`object-authorization-and-model-output`、`presentation-priority-and-decision`。
  review-change 的情境沒有附材料，這次不涵蓋。
- **兩組**：框架組用 `agf project update --host claude` 把規則和本專案用的五個 skill 配置到隔離目錄；對照組不配置框架。兩組用同一個模型（Sonnet 5.5），材料、權限相同，提示詞裡不點名 skill。共 12 次。
- **量什麼**：該用的 skill 有沒有被呼叫、不該用時有沒有誤觸（直接從工具事件看）；成果是否符合該情境的 `observe` 與 `avoid`；兩組的 token 與回合數差多少。
  成果品質交給一個看不到組別的 Opus 5.5 子代理，依 `observe`／`avoid` 評分。

### 3.4 實驗 B：只靠交接文件，新 session 能不能接手

- **材料**：本專案在 tag `s7-zh-style-prototype` 的副本，連同驗收 receipt（`.venv` 用連結）。
- **兩個條件**：保留 `docs/HANDOFF_CLAUDE.md`，或刪掉它（只剩 `CLAUDE.md`）。**兩個模型**：Haiku 5.5、Sonnet 5.5。共 4 次。
  Opus 5.5 已在這個 session 接手過一次（L49），算現有證據，不重跑。
- **提示詞**：兩個條件用同一句：請先讀 `CLAUDE.md` 與它指到的交接文件（如果有），做接手時該做的核對，回報未提交的變更、有哪些 tag、`scripts/status.py` 的結果代表什麼、機器是否安靜，
  再說明下一步要做什麼、有哪些事不能做。只准讀檔與執行唯讀命令。
- **評分**：依事先寫好的答案表逐項給分：兩個 tag、`source changed` 是預期中的事、下一步是起草 S8 規格、框架唯讀、不 push 不建 PR、不削弱測試。
  另記越界操作（任何寫檔、push、改框架）、token 與回合數。

### 3.5 實驗 C：按需指引有沒有被讀到（接 L52）

- **任務**：取框架 `writing-cases.json` 的 2 個案例，只給 `request`、`facts`、`draft`，請新 session 改寫。在本專案的副本裡執行。
- **兩個條件**：本專案現況（寫作指引只在 `.agf/managed/project-rules.md` 提到一句）；或在 `CLAUDE.md` 加一行「改寫或撰寫中文說明前，先讀 `.agf/managed/guides/writing.md`」。
  模型 Sonnet 5.5。共 4 次。
- **量什麼**：有沒有讀到指引（工具事件）；改寫是否符合該案例的 `preserve`、`observe`、`avoid`（同一個看不到組別的子代理評分）；S7 腳本的命中數；token。

### 3.6 分析報告

`framework-study/analysis/report.md`：

1. 摘要，以及「只能改三件事的話，改哪三件」。
2. 11 項標準逐項寫：現況（框架說怎麼做）、證據（紀錄編號、審查、S7、實驗）、優點、缺點、改進建議（指到檔案或機制）、優先序（高／中／低）與信心（已證實／觀察／假說）。
3. 跨項目的主題（例如「入口沒有點名，指引就不會被讀到」）。
4. 沒有證據、還不能下結論的部分。

## 4. 不做的事與限制

- 不修改框架；所有建議都只是建議，要改框架得另外授權。
- 不做其他供應商（Codex、Gemini）的實驗：框架 2026-11-09 的紀錄顯示 Codex CLI 在這台 WSL 沒有登入，Gemini 也沒有確認過可用。
  框架先前的交接驗證只在 Codex 上做過；實驗 B 改由 Claude 的模型接手，等於換了一個供應商。
- 每個條件只跑一次，樣本很小：只能說「這次觀察到什麼」，不能推成觸發率或穩定的 token 差異。
- 受試的 session 會載入使用者的全域設定（RTK hook、全域 `CLAUDE.md`），兩組相同；這會影響行為，報告會寫明。
- 我（`claude-opus-5-5`）設計實驗，也寫了大部分的證據。評分盡量交給看不到組別的子代理與事先寫好的答案表，再請使用者抽查。
- token 與費用以 CLI 回報的數字為準；那是 CLI 的估算，不是帳單。

## 5. 產物與位置

`framework-study/analysis/`：

- `SPEC.md`（本規格）、`inventory.md`（元件盤點）、`report.md`（分析報告）
- `experiments/A-trigger/`、`B-handoff/`、`C-guide/`：各自的做法說明、提示詞與評分表（執行前提交）、執行腳本、`results.json`（摘要指標）、`grades.json`
- 原始事件流：`artifacts/s8-<日期>/`（不進版本控制）

不改 Raft 的驗收契約。

## 6. 驗收

- 每個實驗：評分表在執行前已提交；每次執行都有原始事件流與摘要；評分與抽查紀錄齊全。
- 報告的每個主張都指到證據；沒有證據的標「假說」。
- 本機 commit 與 tag `s8-framework-analysis`；停下來讓使用者提問。

## 7. 預估

一到兩天。CLI 執行約 22 次（探測 2、A 12、B 4、C 4）。用量粗估 60～120 萬 token：Claude Code 每個 session 光是系統提示就有上萬 token。
每次設預算上限（CLI 估算 2 美元），實際數字照 CLI 回報寫進報告。需要使用者約 15 分鐘抽查評分。

## 8. 已決定（2026-11-16，照建議）

| 編號 | 問題 | 建議 |
|---|---|---|
| D1 | 實驗用桌面 app 內附的 CLI 無頭執行，會花你的用量 | 同意。替代方案一：只用子代理，拿不到工具軌跡與用量，等於重做框架 11-09 已經做過的層次。替代方案二：不做實驗，只寫報告 |
| D2 | 受試模型 | A、C 用 Sonnet 5.5；B 用 Haiku 5.5 與 Sonnet 5.5 |
| D3 | 評分 | A、C 的品質交給看不到組別的 Opus 5.5 子代理；B 依答案表由我評分；你抽查 3 筆 |
| D4 | 實驗 C 要不要做 | 做：只多 4 次執行，直接驗證 L52 的修正方向 |

核准本規格，也就是同意第 3 節寫到的 CLI session 與子代理。

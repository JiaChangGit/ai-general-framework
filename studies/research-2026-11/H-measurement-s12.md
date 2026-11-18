# 量測（S12）：框架該幫上忙的任務、固定成本拆解、改過描述的 skill（2026-11-18）

上一輪（[G 報告](G-measurement-2026-11-18.md)）的結論是：兩組都全過，量不出框架有沒有幫助，只量到框架組多花 20%～45%。這一輪補三件事：

1. **框架該幫上忙的任務。** 兩個任務的關鍵決定只在第一段對話裡說過，第一段又被截斷；另一個任務改了程式，文件裡的範例跟著過時。
2. **固定成本從哪裡來。** 每個 session 一開始就多讀的約 2,400 tokens，拆成規則與 skill 兩部分。
3. **改過描述的 skill 有沒有比較常被選對。** 上一輪選錯或沒用到的三個情境，各跑 3 次；再加兩個字面相近、但不該換 skill 的情境，各跑 2 次，看新描述有沒有搶走它們。

原始資料：[measurement-s12/](measurement-s12/)。

## 條件

| 項目 | 值 |
|---|---|
| 日期 | 2026-11-18 |
| 宿主 | Claude Code 2.1.325，Linux（WSL2），無頭模式 `claude -p` |
| 模型 | `claude-sonnet-5-5`；換模型任務的第二段用 `claude-haiku-5-5` |
| 框架版本 | 分支 `s12-framework` 的 `e063dc8` |
| 受試者能用的工具 | Read、Grep、Glob、Edit、Write、Skill；沒有 Bash |
| 框架組 | 規則、7 個 skill、續接 hook，hook 設定開了 `save_prompts`（[evals/impact/continuity-hooks.json](../../evals/impact/continuity-hooks.json)） |
| 對照組 | 只有任務檔 |
| 只有規則／只有 skill | 只用在固定成本的探測：框架安裝但不帶 skill；或只帶 skill，刪掉 `CLAUDE.md`、`AGENTS.md`、`.agf/`。兩組都沒有 hook |
| 預算 | 使用者給約 4 美元 |

名詞：

- **`save_prompts`**：續接 hook 的選項，預設關閉。開啟後，hook 在使用者每次送出訊息時存下原文，session 結束時寫進檢查點；下一個 session 開始時，hook 提醒先讀檢查點。
- **第一次呼叫的 context**：session 第一次呼叫模型時讀進去的 token 數，包括系統提示、工具說明、規則、skill 清單與使用者的訊息。兩組相減就是框架的固定成本。

## 結果

### 一、框架該幫上忙的任務

| 任務 | 內容 | 對照組（通過，花費） | 框架組（通過，花費） | 差 |
|---|---|---|---|---|
| decision-only-in-chat | 第一段裡使用者說「README 的格式過時，改成 `1h02m03s`，README 先不要改」，session 在第一輪就被截斷；新的 session 接手 | 0/3，0.107 | 3/3，0.139 | +30% |
| decision-only-in-chat-switch | 同樣的情況，內容換成「餘數從第一個人開始分」；第二段換成 Haiku 接手 | 0/3，0.048 | 3/3，0.060 | +24% |
| docs-follow-the-change | 只說「把 greet 的回傳改成 `Hi, <name>!`」，沒說要改文件；檢查 README 的範例有沒有跟著改 | 3/3，0.070 | 3/3，0.087 | +24% |

花費是美元、一個任務所有 session 的總和、3 次的中位數。對照組的文件任務原本只跑了 2 次：第 3 次因為量測工具的預算保護（每個 session 先預留 0.4 美元）沒有開始，之後另外補跑，結果也是通過（[impact-new-rerun-report.md](measurement-s12/impact-new-rerun-report.md)）。12 次續接的第一段都真的被截斷了，受試者都沒有讀工作目錄以外的檔。

- **對照組 6 次全錯，錯法都一樣**：照 README 做成 `1:02:03` 與 `[33, 33, 34]`。新的 session 只看得到檔案，看不到上一段的對話。
- **框架組 6 次全對。** 接手的 session 都讀了 `.agf/checkpoints/latest.md`，裡面有上一段使用者說的話：4 次是第一個讀的檔，另外 2 次先讀了 `AGENTS.md`（[continuation-reads.md](measurement-s12/continuation-reads.md)）。換成 Haiku 接手也一樣。
- **這兩個任務是和 `save_prompts` 一起設計的。** 對照組根本無從得知那個決定，所以 0/6 對 6/6 證明的是「這個機制有作用」，不是「一般工作會變好這麼多」。實際工作裡，決定也常寫在檔案或 commit 訊息裡，那時對照組也做得到。
- **文件任務兩組都會順手改 README**，量不出差別。這是又一個兩組都過的檢查，下次換掉。
- **框架組照樣比較貴**，多 24%～30%。

### 二、固定成本從哪裡來

「只回覆 OK」的 session，每組 2 次（中位數）：

| 組別 | 第一次呼叫的 context（tokens） | 比對照組多 | 花費（美元） | 比對照組多 |
|---|---|---|---|---|
| 對照組 | 19,363 | — | 0.0413 | — |
| 只有 skill | 20,083 | 720 | 0.0442 | +7% |
| 只有規則 | 21,283 | 1,920 | 0.0490 | +19% |
| 全部（規則、skill、hook） | 22,003 | 2,640 | 0.0518 | +25% |

- **規則占了大約四分之三。** 規則是 `CLAUDE.md` 匯入的 `project-rules.md`（1,413 字的中文）加上 `AGENTS.md` 的兩行指向；7 個 skill 的描述只占四分之一。
- 兩部分相加（1,920 + 720 = 2,640）正好等於全部都裝，表示兩者互不影響；hook 在這個 session 沒有輸出，不增加 context。
- 這是最小的 session。實際任務每多一輪，這些 tokens 就再讀一次（cache read，便宜但不是免費）；規則還會讓模型去讀指引檔，例如上一輪的 rewrite-zh 讀了寫作指引。
- 換算（推論，沒有另外量）：規則約 1,900 tokens、1,413 個字，中文大約一個字 1.3 個 token。要降固定成本，先縮規則。

### 三、改過描述的 skill

| 情境 | 該用的 skill | 上一輪（S11） | 這一輪 |
|---|---|---|---|
| learning-with-trace | guide-learning | 選了 trace-code | 3/3，經 Skill 工具 |
| failure-with-sql-review | debug-root-cause | 選了 review-sql | 3/3，debug-root-cause 經 Skill 工具叫用；review-sql 也有用到，但是直接讀它的 `SKILL.md`，先後順序沒有記錄 |
| cleaned-copy-is-not-original | read-research | 沒用（S8 也沒用） | 3/3，經 Skill 工具 |
| trace-without-lesson（不該換） | trace-code | 命中 | 2/2，沒有被 guide-learning 搶走 |
| sql-plan-without-incident（不該換） | review-sql | 命中 | 2/2，沒有被 debug-root-cause 搶走 |

13 次共 1.24 美元。只重跑了描述有關的 5 個情境，其他 7 個沒有重跑；描述對其他說法的請求有什麼影響，這次沒有量。

## 結論

1. **`save_prompts` 讓「決定只在對話裡」的續接做對**：6/6 對 0/6。代價是花費多約四分之一，以及隱私風險，所以預設關閉。
2. **固定成本主要來自規則**：約 1,920 tokens，skill 描述約 720。
3. **描述寫明「兩種工作同時出現時以誰為主」之後**，三個情境從上一輪的 0/3（各跑 1 次）變成 9/9（各跑 3 次），字面相近的情境沒有被搶走。
4. **改程式時順手更新文件，兩組都會做**，框架在這裡沒有額外作用。

## 限制

- 每個條件 2～3 次。
- 決定只在對話裡的兩個任務，是為了 `save_prompts` 設計的（見上）。
- 只有一個宿主版本、一種主要模型。
- 量測的 session 和主對話共用額度；這一輪沒有撞到上限。

## 花費

觸發 1.24 美元，成效 1.90 美元（其中補跑的 3 次共 0.16），上層目錄啟動的探測 0.01 美元，合計約 3.15 美元，在使用者給的約 4 美元內。

## 重跑

```console
python evals/host/impact.py run --framework . --base <空目錄> --out <輸出目錄> \
  --model claude-sonnet-5-5 --switch-model claude-haiku-5-5 --runs 3 \
  --ids decision-only-in-chat,decision-only-in-chat-switch,docs-follow-the-change \
  --hooks evals/impact/continuity-hooks.json --budget 0.4 --total-budget 1.8
python evals/host/impact.py run --framework . --base <空目錄> --out <輸出目錄> --model claude-sonnet-5-5 --runs 2 \
  --ids probe-context --group framework --group control --group rules-only --group skills-only \
  --hooks evals/impact/continuity-hooks.json --budget 0.2 --total-budget 0.45
python evals/host/trigger.py run --framework . --base <空目錄> --out <輸出目錄> --model claude-sonnet-5-5 --group framework \
  --budget 0.3 --ids learning-with-trace,failure-with-sql-review,cleaned-copy-is-not-original
```

`--total-budget` 的保護是「已花的 + 每個 session 的上限 > 總上限」就停，比實際花費保守；設總上限時多留一個 session 的上限。

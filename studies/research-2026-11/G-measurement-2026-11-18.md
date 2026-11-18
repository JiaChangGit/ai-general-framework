# 量測：框架有沒有幫上忙、多花了多少（2026-11-18）

使用者問了兩件事：框架到底有沒有幫助專案開發？會不會讓 token 消耗變多？這份紀錄回答第二題，第一題只回答了一部分，原因在「結論」一節。

原始資料：[measurement-2026-11-18/](measurement-2026-11-18/)（成效的表格與彙總、續接任務每一段讀的檔、觸發的逐筆結果）。每個 session 的事件串流（stream-json）沒有放進來。量測工具：[evals/host/impact.py](../../evals/host/impact.py)、[evals/host/trigger.py](../../evals/host/trigger.py)，用法見 [evals/host/README.md](../../evals/host/README.md)。

## 條件

| 項目 | 值 |
|---|---|
| 日期 | 2026-11-18 |
| 宿主 | Claude Code 2.1.325，Linux（WSL2），無頭模式 `claude -p` |
| 模型 | 受試 session 用 `claude-sonnet-5-5`；「換模型接手」的第二段用 `claude-haiku-5-5` |
| 框架版本 | 分支 `s11-framework` 的 `dd19158`（觸發、成效第一次）與 `96af87e`（成效補跑）。兩者之間改的是 guard hook、CI workflow、量測工具與文件。受試者看得到的規則、skill、續接 hook 都沒變；`docs/workflow.md` 多了一行，受試者沒有讀到 |
| 受試者能用的工具 | Read、Grep、Glob、Edit、Write、Skill；Bash 整個拿掉（模型有試著叫用 Bash，都被拒絕） |
| 兩組 | **框架組**：`project install --host claude` 裝規則與 7 個 skill，加上續接 hook（[evals/impact/continuity-hooks.json](../../evals/impact/continuity-hooks.json)）。**對照組**：只有任務檔 |
| 兩組相同的東西 | 使用者層級的設定照樣載入：全域 `CLAUDE.md`、使用者層級的 skill（受試 session 的清單裡共 37 個 skill，其中 7 個來自框架）、使用者層級的 hook |
| 預算 | 每個 session 0.4 美元；成效整體 2.6 美元，後來補跑另設 0.9 美元 |

名詞：

- **cache creation／cache read**：Claude Code 把一段固定的開頭（系統提示、工具說明、規則檔）存進提示快取。第一次寫入叫 cache creation，比一般輸入貴；之後每一輪直接讀，叫 cache read，便宜很多。
- **隱藏檢查**：session 結束後才執行的檢查，受試者看不到。例如 import 受試者改過的程式、跑幾個斷言，或用正規表示式比對它寫的檔案。

## 一、觸發：該用 skill 時有沒有用、不該用時有沒有誤用

12 個情境，只跑框架組，每個情境一次，共花 1.07 美元。

| 情境 | 預期的 skill | 實際 | 結果 |
|---|---|---|---|
| trace-without-lesson | trace-code | trace-code（Skill 工具） | 命中 |
| trace-lossy-id-conversion | trace-code | trace-code（Skill 工具） | 命中 |
| sql-plan-without-incident | review-sql | review-sql（Skill 工具） | 命中 |
| review-diff-with-materials（新） | review-change | review-change（Skill 工具） | 命中 |
| flaky-repeat-evidence | debug-root-cause | 直接讀 `SKILL.md` | 命中，但沒有經過 Skill 工具 |
| learning-with-trace | guide-learning | trace-code | 選錯 |
| failure-with-sql-review | debug-root-cause | review-sql | 選錯 |
| cleaned-copy-is-not-original | read-research | 沒用 | 沒觸發（S8 也是） |
| object-authorization-and-model-output | 不該用 | 沒用 | 正確 |
| presentation-priority-and-decision | 不該用 | 沒用 | 正確；讀了一次框架的 `templates/presentations/README.md`（規則檔指向它，設計如此） |
| media-style-continuity-scope | 不該用 | 沒用 | 正確 |
| ask-me-first-without-invocation（新） | 不該用（`align-with-me` 只能由使用者叫用） | 沒用 | 正確 |

- 該用的 8 個命中 5 個，其中 4 個經過 Skill 工具；不該用的 4 個沒有誤觸。
- 兩個選錯的情境都是**複合任務**：一個請求裡同時有兩種工作（「邊追 trace 邊教」、「事故裡附了 SQL」），模型挑了字面上更顯眼的那個 skill。框架的說明寫了「複合任務先選主要的工作」，這次沒有發揮作用。
- `read-research` 連兩輪都沒觸發。那個情境的重點是「清理過的複本不是原始資料」，提示裡沒有出現「論文」「規格」這類字，描述的觸發詞對不上。

## 二、成效：有框架和沒框架，結果與花費差多少

8 個任務，兩組各跑 2 次，組別順序每個任務交替，計畫 32 次。第一次量測在第 24 次執行時撞到 5 小時用量上限停下：受試 session 和主對話用的是同一個額度。停下時，第二次只跑完 3 個任務，第 4 個（review-withdraw）跑完對照組、框架組剛開始。額度恢復後，只補跑兩個續接任務的第二次。完成 27 次，花 2.34 美元；沒有補的 5 次是 rewrite-zh、simple-edit 兩組各 1 次，以及 review-withdraw 框架組 1 次。

| 任務 | 內容 | 對照組（通過，花費） | 框架組（通過，花費） | 差 |
|---|---|---|---|---|
| fix-admitter | 修一個邏輯錯誤 | 2/2，0.072 | 2/2，0.087 | +21% |
| fix-pager | 修分頁的邊界錯誤 | 2/2，0.068 | 2/2，0.081 | +20% |
| trace-customer-id | 追一個 ID 在哪一步被轉壞 | 2/2，0.058 | 2/2，0.070 | +21% |
| review-withdraw | 審查一段提款程式的修改 | 2/2，0.060 | 1/1，0.073 | +22% |
| rewrite-zh | 把一段生硬的中文改通順 | 1/1，0.075 | 1/1，0.108 | +45% |
| simple-edit | 改一個常數 | 1/1，0.059 | 1/1，0.071 | +21% |
| continue-after-limit | 第一段被截斷，新 session 接手 | 2/2，0.135 | 2/2，0.180 | +33% |
| switch-model | 第一段被截斷，換 Haiku 接手 | 2/2，0.073 | 2/2，0.092 | +25% |

花費單位是美元，加總一個任務的所有 session；跑了 2 次的取中位數，也就是兩次的平均。review-withdraw 的框架組只有 1 次，拿它和對照組的 2 次比，不是成對的比較。各格的 token 數在 [impact-report.md](measurement-2026-11-18/impact-report.md)。

**通過率兩組都是 100%**（框架組 13/13，對照組 14/14）。框架組在每個任務都比較貴。token 總數也幾乎都比較多，只有 review-withdraw 例外：框架組 47,178、對照組 62,675，但框架組的 cache creation 與輸出比較多，所以還是比較貴。

### 多出來的花費從哪裡來

每個 session 的平均（框架組 17 個、對照組 18 個 session）：

| | 對照組 | 框架組 | 差 |
|---|---|---|---|
| cache creation tokens | 13,047 | 17,719 | +36% |
| cache read tokens | 59,168 | 66,275 | +12% |
| output tokens | 1,250 | 1,704 | +36% |
| 花費（美元） | 0.059 | 0.075 | +27% |

- **固定成本約 2,400 tokens。** 每個 session 第一次呼叫模型時的 context（取自事件串流），對照組中位數 19,338 tokens，框架組 21,745 tokens。多出來的是規則檔、`CLAUDE.md` 的匯入、7 個 skill 的描述。這部分每個 session 都要付，而且之後每一輪都要再讀一次。
- **其餘來自行為。** 叫用 skill 會把整份 `SKILL.md` 讀進來；續接任務裡，框架組多讀了 checkpoint 與安裝紀錄；輸出也比較長。以上沒有拆開量。
- `rewrite-zh` 差最多（+45%）：框架組讀了 `.agf/managed/guides/writing.md`（規則要它寫文件前先讀寫作指引），cache creation 因此多了約 7,300 tokens。對照組只讀了草稿。這一次的成果都通過了隱藏檢查，讀指引有沒有讓文字更好，這次沒有評。

### 續接 hook 實際做了什麼

兩個續接任務的第二段（新 session），框架組 4 次都先讀了 `.agf/checkpoints/latest.md`，那是 SessionStart hook 提示它讀的；hook 的運作符合設計。8 次的第一段都真的被截斷了（`error_max_turns`）。每一段讀的檔與花費在 [continuation-reads.md](measurement-2026-11-18/continuation-reads.md)。

但對照組也全部完成。被截斷的工作留在檔案裡（寫了一半的 `durations.py`），新 session 打開檔案就知道做到哪裡。框架組多讀了 checkpoint 和安裝紀錄（`.agf/history/*.json`），第二段反而比較貴（0.095、0.104 美元，對照組 0.065、0.073 美元）。

### skill 的使用

框架組在成效任務裡叫用了 4 次 skill：`fix-admitter` 兩次都用 `debug-root-cause`，`review-withdraw` 用 `review-change`，`trace-customer-id` 兩次裡有一次用 `trace-code`。`fix-pager` 和 `rewrite-zh` 都沒有用。

## 結論

1. **會，框架讓花費變多**：這 8 個任務多 20%～45%，每個 session 平均多 27%；token 總數只有一個任務例外。這和 ETH 對 AGENTS.md 類 context 檔的研究方向一致（成本多約兩成，見 [F-hooks-evals-ci.md](F-hooks-evals-ci.md) 的 2d）。
2. **「有沒有幫助」這次量不出來。** 兩組都 100% 通過，代表任務太簡單。兩組都過的檢查分不出差別，agentskills.io 的評測指引建議把這種檢查拿掉、換成會失敗的。
3. **續接 hook 在「狀態都在檔案裡」的情況沒有好處。** 它真正該發揮的時候，是重要的資訊只存在對話裡：使用者做過的決定、問過的問題、試過但失敗的做法。這次的任務沒有測到這種情況。

## 限制

- 每個條件只跑 1～2 次，差異可能有一部分是雜訊。不過 8 個任務的方向都一樣，而且固定成本的差距在每個 session 都穩定。
- 計畫的 32 次只完成 27 次；沒補的 5 次見上面。
- 受試者讀工作目錄以外的檔：觸發量測有 1 次（框架的 `templates/presentations/README.md`），成效量測 0 次。框架組裝的是 shared 模式，規則檔裡寫著框架的路徑，理論上讀得到框架裡的隱藏檢查；這次沒有發生。這次量測之後，量測工具改成把 hook 程式複製進受試目錄，設定檔不再指向框架。
- 只有一個宿主、一種主要模型、一台機器。
- 任務是為了這次量測寫的小任務，不是真實專案的工作。
- 使用者層級的設定在兩組都載入，會稀釋或放大差異；兩組相同，但不是乾淨的環境。
- 成功只看隱藏檢查，沒有評品質。例如審查任務只檢查有沒有找到那個缺陷，沒有評解釋得好不好。

## 接下來該怎麼量

- 加 2～3 個「沒框架很容易做錯」的任務：重要資訊只在第一段的對話裡（例如使用者在第一段說「不要改公開 API」）、需要先問清楚才不會做錯的任務、需要多步驟驗證的修改。
- 拆開量固定成本：只裝規則、只裝 skill、全部都裝，各跑一次。
- 每個條件至少跑 3 次，用同一個 CLI 版本。

## 花費

觸發 1.07 美元，成效 1.85 + 0.49 = 2.34 美元，合計 3.41 美元；另有幾次 hook 探測，共約 0.02 美元。

## 重跑

```console
python evals/host/trigger.py run --framework . --base <空目錄> --out <輸出目錄> --model claude-sonnet-5-5 --group framework --budget 0.3
python evals/host/impact.py run --framework . --base <空目錄> --out <輸出目錄> \
  --model claude-sonnet-5-5 --switch-model claude-haiku-5-5 --runs 2 \
  --hooks evals/impact/continuity-hooks.json --budget 0.4 --total-budget 2.6
python evals/host/impact.py report <輸出目錄> [<補跑的輸出目錄> ...] --md report.md
```

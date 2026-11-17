# 修改紀錄

每一輪寫：改了什麼、為什麼、怎麼驗證、還沒驗證什麼。細節在各 commit 的訊息與 [docs/verification.md](docs/verification.md)。

## 2026-11-17：S10（分支 `s10-framework`）

依據：[分析報告](docs/analysis-2026-11.md)。這一輪是在 Raft KV store 專案做最後一次複查時，邊用框架邊找到的問題，加上外部研究（[studies/](studies/README.md)）。

| 修改 | 為什麼 | 驗證 |
|---|---|---|
| `templates/project-rules.md` 重寫（每個 session 都載入） | 句子改短、改自然；多三條這次證實需要的規則：續接與用量、只做過一次的檢查要重跑、commit 前看暫存範圍；「改程式」換成依序問的五個問題 | 字數 1,310 → 1,316，幾乎不變；`tests/test_manage.py` 通過；沒有量測對行為的影響 |
| 新 skill `skills/align-with-me/` | 使用者要「grill me」時有一個直接的入口；`disable-model-invocation: true`，不進模型的 skill 清單、不會誤觸 | `agf audit` 無錯誤；沒有在宿主上實際叫用過 |
| `templates/claude-guard-hook.py`、`templates/claude-guard-settings.example.json`，登記為 `integration template` | 文字規則與 deny 規則擋不住 `git -C . push`、`sh -c`、從上層目錄啟動的 session；hook 可以裝在使用者層級 | `tests/test_guard_hook.py` 10 個測試；Claude Code 2.1.325 無頭 session 實測：`git -C <dir> push` 與 Write 進受保護目錄都被擋下（2026-11-17，花費約 0.004 美元） |
| `adapters/claude.json` 新增 `guard_hook` | 記下 guard hook 實測過與沒測過的情況；原本「跑品質檢查的 Stop hook」那一筆仍標示未測試 | 同上 |
| `docs/workflow.md` 新增「續接、換模型與用量」 | 這次 4 個平行子代理撞到 5 小時上限、使用者換模型後要求重試；原本沒有任何指引 | 文字修改，未量測 |
| `docs/delivery.md` 的暫存規則 | 這次重設 index 後，先前暫存的刪除跟著進了錯的 commit | 文字修改 |
| `docs/writing.md` 的七項校閱清單 | 使用者的 AI 味標準散在各段；附上實際改過的例子 | 文字修改 |
| `docs/analysis-2026-11.md` | 依使用者的 11 項標準寫優缺點與建議 | — |
| `studies/`：S7、S8 的研究搬自 Raft 專案；這次的四份研究報告 | 框架的研究應該跟著框架 | 內容未改 |
| `README.md` | 換模型的說法、新 skill、guard hook 的用法 | — |

沒做的事與理由見分析報告的「之後的優先順序」。

## 2026-11-17：未提交修改的 commit（`c020447`，main）

2026-11-10 起留在工作目錄、沒有提交的 10 個檔案，經使用者同意原樣 commit：`agf run` 一律經管線擷取輸出並等管線關閉；擷取檔的寫入、讀取、關閉錯誤標為不完整；複合任務的入口說明與評測案例；兩個寫作案例。全部 247 個測試（6 個略過）與 `agf audit` 通過後才 commit。

## 2026-11-16：S8 後續（`90bba83`～`2ffd748`）

規則入口的檢查（既有 `CLAUDE.md` 沒有 import 規則時警告）、交接要寫接手者自己執行的核對命令、Claude Code 的權限範本、`evals/host/` 的觸發評測工具與預檢、skill 叫用的措辭。量測與審查的結果在 [studies/raft-kv-2026-11/changes/RESULTS.md](studies/raft-kv-2026-11/changes/RESULTS.md)。

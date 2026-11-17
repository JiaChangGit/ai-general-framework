# 實驗 C：按需指引有沒有被讀到（執行前登記）

依 [SPEC.md](../../SPEC.md) §3.5，檢驗 L52 的推論：本專案的 `CLAUDE.md` 沒有 import 框架的規則（D0 第二次），寫作指引因此不會被讀到；在入口點名它，就會被讀到。

- **材料**：和實驗 B 一樣的本專案副本（tag `s7-zh-style-prototype`，含 `.agf/managed/`）。
- **案例**（框架 `evals/writing-cases.json`）：`dense-explanation-for-newcomer`、`animacy-and-collocation`。只給 `request`、`facts`、`draft`；`preserve`、`observe`、`avoid` 留給評分者。
- **兩個條件**：`as-is`（空 commit「Experiment C snapshot」）；`entry-link`（同一個訊息的 commit 在 `CLAUDE.md` 的第一個清單項目前加一行
  「改寫或撰寫中文說明前，先讀 `.agf/managed/guides/writing.md`。」）。順序：第一個案例先 as-is，第二個先 entry-link。
- **提示詞**：`request`，接「事實：」與條列的 `facts`，再接「草稿：」與 `draft`，最後一句「只用純文字回覆改寫後的內容，不要改任何檔案。」兩個條件相同。
- **模型與限制**：`claude-sonnet-5-5`；可用工具 `Read Grep Glob Skill`；`--permission-mode dontAsk`；預算上限 2 美元、時間上限 600 秒。
- **量什麼**：有沒有讀 `.agf/managed/guides/writing.md`、`.agf/managed/project-rules.md`（事件流）；呼叫了哪些 skill；token；
  成果依 [盲評的提示詞](../grader_prompt.md) 由看不到條件的 Opus 5.5 子代理依 `preserve`／`observe`／`avoid` 評分；另記 S7 腳本對成果的命中數（只當參考）。
- **產物**：`results.json`、`outputs/`、`grades.json`；原始事件流在 `artifacts/runs/s8-20261116/C/`。

## 執行紀錄（2026-11-16）

C 和第一次嘗試的 B 用同樣的設定（沒有禁止讀取副本以外的路徑）。四次執行都沒有讀到副本以外的檔案（`results.json` 的 `files_read`），所以結果有效，不重跑。


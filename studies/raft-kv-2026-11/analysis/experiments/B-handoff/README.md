# 實驗 B：只靠交接文件，新 session 能不能接手（執行前登記）

依 [SPEC.md](../../SPEC.md) §3.4。

- **材料**：本專案 `git clone --no-local` 到暫存目錄（專案之外），checkout tag `s7-zh-style-prototype`；另複製 `.agf/` 的 `manifest.json`、`managed/`、`history/`
  （不含 921 MB 的 `.agf/qa`）；`.venv` 與 `artifacts/acceptance-final/` 用連結指回本專案（只讀）。
- **兩個條件**：`with-handoff`（加一個空 commit「Experiment B snapshot」）；`without-handoff`（同一個訊息的 commit 刪掉 `docs/HANDOFF_CLAUDE.md`）。兩者的 `git log` 看起來一樣。
- **模型**：`claude-haiku-5-5`、`claude-sonnet-5-5`。順序：haiku-with、haiku-without、sonnet-without、sonnet-with。
- **提示詞**：[prompt.txt](prompt.txt)，兩個條件相同。
- **可用工具**：`Read Grep Glob`，以及唯讀的 `git status／log／tag／branch／show／diff`、`.venv/bin/python scripts/status.py`、`uptime`、`ps`、`ls`、`cat`
  （各加上 RTK hook 改寫後的 `rtk …` 形式）；其他一律被拒，並記錄下來。`--permission-mode dontAsk`，預算上限 2 美元、時間上限 900 秒。
- **評分**：依 [answer_key.json](answer_key.json)（8 項，每項 1 分）與越界項目，由我依最終回覆評分；回覆說「執行了某命令」時，對照事件流確認。使用者抽查一筆。
- **之後**：確認副本沒有被改動（`git status --porcelain` 為空），刪除副本。
- **產物**：`results.json`、`outputs/`、`grades.json`；原始事件流在 `artifacts/runs/s8-20261116/B/`。

## 執行中發現的問題（2026-11-16）

**第一次嘗試的「沒有交接文件」被污染。** 副本的 `CLAUDE.md` 寫著專案的絕對路徑；Haiku 照著去讀了**真正專案**的 `docs/HANDOFF_CLAUDE.md`、`.git/packed-refs` 與 `docs/SOURCE_MANIFEST.json`。
Read 不限於工作目錄，刪掉副本裡的交接文件，擋不住它讀到原專案的那一份。其他三次沒有讀到副本以外。
修正：禁止讀取 `/home/user/src/**`（真正的專案與框架）與 `~/.claude/**`（`--disallowedTools`，Read 的規則同時約束 Grep、Glob；探測見 `artifacts/runs/s8-20261116/deny-probe.jsonl`）；
Bash 白名單拿掉 `cat`、`ls`（Bash 不受 Read 規則約束）。四次全部重跑，條件一致。第一次嘗試保留在 `results-attempt1.json`、`outputs-attempt1/` 與 `artifacts/runs/s8-20261116/B-attempt1/`，不納入比較。
這件事本身也是結果：交接文件與入口檔裡的絕對路徑，讓副本無法隔離。

## 更正（2026-11-16，S8 後續）

上面「執行中發現的問題」寫 Read 的規則同時約束 Grep、Glob。當時的探測（`deny-probe.jsonl`）只測了 Read 與 Glob，Grep 那一半是推論。S8 後續補測後才證實 Read 的規則也擋 Grep（[S8 後續的結果](../../../changes/RESULTS.md) 2.10）。本實驗的結論不受影響：受試者沒有用 Grep 讀過被禁止的路徑。

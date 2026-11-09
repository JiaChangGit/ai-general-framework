# Claude Code 參考材料的採納紀錄

2026-11-09 檢查使用者提供的 `agent-skillkit.zip`：58 個 ZIP 項目、12 個 SKILL 入口、11 支 Python／Shell 腳本，解壓內容約 129 KB。附件 SHA-256：`0dea96e2feb66c784e240dc1fb997a251c97436cd3b201bba86cdee1cc4b665c`。本輪只讀附件，沒有執行其中的腳本或安裝指令，也沒有套用它的 global 規則；下列風險來自程式與文字判讀，不是附件的完整動態驗證。

## 採納的三個小改進

| 附件提供的方向 | 本專案如何採用 |
|---|---|
| `language-feel` 的專案術語表 | writing 補術語表適用邊界：按情境核對差異，保留同詞異義、正式 symbol、引述及真實 AI 使用揭露。新增正反案例，不先加機械替換或強制 lint。 |
| `read-spec`／`research` 的轉換及清理 | tools 補清理結果只是檢索副本，保留原檔、版本／雜湊與頁碼對照；相同前綴或檔名不足以去重。引用回查原文，不把轉換後行數當頁碼。 |
| `debug/scripts/flaky.sh` 的逐次試驗紀錄 | debug-root-cause 補可安全重複、限制次數／時間／輸出、保留失敗及成功對照。沿用現有 runner／run，不加另一個 Bash 執行器。 |

## 沒有照搬的部分

- **技能與全域規則：** align、grill、ideate、teach、vibe-code 等用途已有對應。固定點子數、結尾格式、註解語言或禁止 Git／作者標註不適合作為所有專案規則。附件 `THIRD_PARTY_NOTICES.md` 列出 grill／debug 的上游來源；本輪未複用其程式或技能文字，沒有增加另一份授權副本。
- **AI 語氣 lint：** `aitone_lint.py` 把生成揭露及 AI 協作標記列為強命中，`zhtw_lint.py` 對「質量」「登陸」的全域替換會受領域影響。兩者讀檔錯誤的流程也可能留下成功退出碼，不宜作 CI 閘門。這些線索應供校閱，不代表原文一定錯或一定有 AI 味。
- **術語檢查程式：** glossary 的資料驅動方式可借；但無效資料行被跳過、replacement decoding 及首次用詞的固定文字窗口，不能證明全文配對正確。暫無專案術語表或反覆問題，先不增 CLI。
- **Token audit：** 將目錄下所有 Markdown 視為常駐載入，會誤算 AGF 的按需 references。固定 tokenizer、字元估算、通用 budget 與「±20%」無法證明宿主實際用量。沿用 audit 的字元資訊及實際 usage，不新增 token-diet 技能。
- **文件與網頁清理：** `doc2md.py` 依多頁相同頁緣刪行，快取以 basename 命名；`webclean.py` 只用段落前 80 字去重，可能丟掉後半不同的義務。現有 source／context 已有身分、來源位置及輸出界線，不替換成另一套轉換器。
- **程式關係與圖解：** `trace.py` 的巢狀 `ast.walk` 和同名第一筆連線可能製造錯誤關係；`diagram.py` 自製 parser／layout 會攤平部分結構。保留原生索引、必要原文及成熟渲染器，不搬入兩個新引擎。
- **安裝與重跑：** marker 後刪目錄不能保留本地 drift，附件安裝方式不取代 AGF 的 manifest／snapshot／rollback。flaky 的參數驗證、逐次 timeout／輸出上限及成功證據保存不足；零次執行不應被當成驗證成功，也不為統計重複有副作用的操作。

實際修改集中在既有 writing、tools、debug-root-cause 與三個原始驗收案例；本輪沒有增加 Skill、MCP、依賴或全域設定。結果與限制見[驗證紀錄](verification.md)，案例數不代表全部已由宿主執行。

## App 開發筆記補充（2026-11-10）

另讀使用者提供的 `ai-app-dev-notes.html`（標示 2026-10-23，SHA-256：`2f7ec6bbeba641544aaeb288347c9594ec29024294f77851c1d0aaf59782e8f9`）及一份文字原則。HTML 只作文字解析，沒有執行其中的 JavaScript、命令或設定。文字檔初讀到全文後，後續路徑已無法定位，未取得雜湊；其內容與已整合的維護及 AI 表達原則重疊，沒有再新增同一份規則。

- **資料流：** 在既有 trace 核對表補資料表徵，按問題追型別、時區、精度、單位與空值，避免只列函式卻漏掉值在哪個邊界改變。
- **並行交易：** 筆記中「寫入與查反向資料放同一交易，就至少一邊看得到另一邊」不是通用保證。[PostgreSQL 18 Read Committed](https://www.postgresql.org/docs/18/transaction-iso.html) 的普通 SELECT 看不到其他未提交寫入；review-sql 補隔離層級、限制、鎖與實際交錯的按需核對。沒有把約會 App 的需求變成框架功能。
- **API 與模型輸出：** workflow 的條件式驗收補物件／動作授權的正反例，依專案分享規則保留合法跨帳號存取；LLM 輸出進入下游前仍依用途驗證，不能作授權依據。來源為 [OWASP API1:2023](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/)及 [LLM05:2025](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/)，不是全面禁止共享或 HTML。

不採固定 SPEC／PLAN 檔名、每任務強制新 session、禁止修改既有測試、固定並行數、每次故障追加 prompt 或自動回到乾淨 Git 狀態。工具對照也不照搬：本機 CLI 的 help 顯示 fork 是對話分叉，不能當成 subagent；能力與 hooks 應依所用版本查核。這些只作對照閱讀，未實際執行附件流程。

曾懷疑空測試集會誤報成功；隔離檢查顯示本機 Windows Python 3.13.15 與 WSL Python 3.14.4 的空 unittest discovery 均回 exit 5，full profile 失敗，因此沒有新增防空測試包裝器。這未驗證 CI Python 3.11，也不推成所有 test runner 的行為。

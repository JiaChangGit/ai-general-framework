# Claude Code 參考套件的採納紀錄

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

# 驗證紀錄

日期：2026-11-08（Asia/Taipei）。這份紀錄分開列出腳本、宿主整合、來源閱讀與真人學習的證據。

## 入門、工具方向與原始診斷保存

本輪維持五個 skills、四份部署指引及零個新增依賴／常駐服務。入門補上零技能預設、依任務選技能，以及配置、宿主發現、實際載入的區別。新研究融合進既有 tools、workflow、delivery 與帶讀參考；原生工具列為候選，未安裝或宣稱個人環境已驗收。唯一新增的 CLI 能力是 `run --output-dir` 選擇保存原始 stdout／stderr 及執行資訊；缺少 rg 時補上原生搜尋替代提示，不重寫搜尋器。

- **相關單元測試：** Windows 原生 execution 18 案中 17 通過、POSIX 權限案 skip；context 6 案通過。WSL execution 18 案及 context 6 案全數通過。本輪未重跑完整單元測試。
- **實際 CLI：** Windows／WSL 均驗證大量且含非 UTF-8 bytes 的完整輸出保存、非零退出、metadata 與 JSON 回傳相符，以及既有目錄被拒絕且命令副作用未發生。執行後 metadata 失敗、timeout、預設不留檔及相對路徑另有單元測試。
- **獨立審查：** 找出持久原始輸出在 POSIX 預設權限下可能對同機其他使用者可讀；改為以 0700 建立最終目錄後重驗。其他平台的存取控制不由 POSIX mode 測試推論。
- **配置與結構：** Windows／WSL 隔離專案的 shared 配置為 ready、6 個受管理檔案、零個預設技能，部署指引與來源逐 bytes 核對。兩端 package audit 通過，guide-learning 官方 validator 以 UTF-8 模式通過；行為案例 ID／候選技能的靜態檢查通過，新增三案後為 34 案。

真實宿主只嘗試一次已安裝的 codex-cli 0.167.0-alpha.3.2：以 ephemeral、ignore-user-config、read-only、skip-git-repo-check 在隔離 trace-code 專案執行新對話。CLI 啟動且 exit 0，但讀規則與技能的 PowerShell 命令被政策拒絕，來源未讀、追蹤任務為 BLOCKED；不能列為技能載入或分析成功。沒有放寬 sandbox、修改 safe.directory 或重試。目標檔案 SHA 前後一致；全域／祖先技能影響及模型身分未確認。CLI 提供該次實際 usage，但沒有 baseline，不推論框架成本或節省。

當次 doctor 在兩端 PATH 只找到 Codex，未找到 Claude、Gemini 或 OpenCode，不代表其他安裝位置或服務不存在；這三者的真實 session 仍未測試。先前直接從 WSL 呼叫 rg 失敗，但本輪 Python 的 PATH 找到 bundled rg，兩端實際搜尋測試皆通過，不能將先前結果推成必須安裝。

CLI、配置、原始紀錄及 native Codex 證據保存在本機 `.agf/qa/practical-tools/`；未將私人認證、原始 session 或 QA 暫存物加入公開來源。這些結果仍不能證明真人學習、四個宿主的一般化觸發率，或 token／費用改善。

另以全新代理只讀部署後規則、按需指引與三份原始材料，完成唯讀評估：用兩筆姓名合併後相同的反例指出資料無法由程式降版還原；批次測試依需求保留先前成功項目、不強套整批原子性；將初始 axe 掃描與完整流程、人工無障礙驗證分開。審閱實際答案確認沒有安裝、執行轉換或宣稱未做的測試；答案在本機 `cases/answer.md`。這是三項定性 smoke，沒有無框架 baseline，也不代表 34 案全數通過。

## MCP 自動選用與用量宣稱

本輪只改既有規則、指引、研究與行為案例，五個 skills 及 Python 核心未變，沒有新增 runtime、依賴或安裝器；完整單元測試未重跑。Windows／WSL 的隔離配置仍是 shared、6 個受管理檔案、零個預設 skills，更新後的 tools 指引與專案規則逐 bytes 核對相符。

獨立新代理只取得部署後的規則與原始 fixture，使用會記錄操作的模擬宿主，實際完成四項請求：

- 沒有提 MCP 的 API 問題：主動探索文件能力、沿用條件未變的查核，呼叫一次對應工具，核對回傳版本；忽略文件結果內要求上傳環境的指令。
- 指定拼字修正：精確改一處，保留其餘 bytes 與換行，沒有為此探索 MCP。
- 私人專案掃描候選：依來源、廣泛存取與未知外傳判定暫不採用，沒有因 readOnlyHint 或口碑就啟動。
- 壓縮報告與新版 proxy：核算輸出 byte 比例，指出缺少 provider usage、帳單與品質證據；未把舊 filter 評估套到新的流量與元件。

操作紀錄為 3 次相關探索、1 次文件呼叫，未啟動掃描器、安裝套件、連接帳號或傳出資料。原始證據、mock actions 與答案保存在本機 `.agf/qa/mcp-selection/`。這是規則與選用行為的定性 smoke，不能宣稱已在四種真實 host 驗證 MCP 整合、安全性或省 token。

RTK 僅查固定 commit 的原始碼、官方公告、外部實測與原始討論；兩端 PATH 未發現 rtk，未安裝或執行，也未取私人 usage。來源、版本、作者關係與未重現部分見 [研究紀錄](research.md)。Windows／WSL package audit 皆 PASS，零錯誤與警告，`git diff --check` 通過。行為案例增為 31 個，ID 與候選 skill 參照靜態檢查通過，不表示 31 案全數已執行。

## 能力清單補強（1df3c90）

本輪修改既有指引、專案規則與行為案例，Python 工具實作及五個 skill 入口不變；沒有重跑整套單元測試。下方核心測試結果保留為先前 v0.2 的證據。

在 Windows 原生與 WSL 的隔離目標實際執行 project install、status 及 profile show；兩端皆為 shared、ready，部署的四份指引與 infra 參考逐 bytes 相符，規則包含目標專案的 profile 入口。Windows 額外配置「追蹤用純文字，不畫圖」的專案偏好，確認能覆蓋框架預設。配置觀察保存於本機 `.agf/qa/requirements-review/`。

另用沒有對話歷史的新代理，僅提供部署後的規則、skills 及原始 fixture，實際完成三項任務，未提供案例預期答案：

- 刪除功能規劃：指出「可復原」與「立即永久刪除」的衝突，保留產品待決事項，列出介面、分工與整合驗收，沒有改程式或固定供應商職位。
- 請求追蹤：從 1500 行日誌定位 r42 的拒絕紀錄，將觀察與靜態路徑分開，依個人偏好用純文字說明。不過首次仍讀了整份日誌，之後才縮小搜尋；這是選讀策略的失敗，不能列為從頭遵守按需讀取。因而在既有專案規則補上先定位再讀區段的提示。
- 事故方案：提出有前提與確認方式的緩解，停在未授權操作前，未將時間相關或服務恢復當根因證明。初稿曾把只有名稱的前版稱為「已知可用」，經審查改成可用性與相容性待確認，未將該初稿當作全數通過。

三份答案及限制保存在本機 `results/behavior.md`。這是小型代理行為觀察，沒有實際開啟其他供應商 session、執行線上恢復或證明一般化的效果。

補上入口提示後，再用另一個新代理執行同一項追蹤，未提供先前答案或日誌行號。這次先以 r42 定位，再讀相鄰區段與相關程式，沒有載入整份日誌；結論、來源行號及純文字偏好相符。實際命令與界線見本機 `results/context-check.md`。這只支持該情境的修正後觀察，不能推成所有任務都會節省 token。

本輪 Windows／WSL 的 package audit 皆 PASS，零錯誤與警告；受影響的 debug-root-cause 通過官方 skill-creator validator，`git diff --check` 無錯誤。27 個案例 ID 不重複且只引用現有候選 skills；這些靜態檢查不代替行為驗證。

## 核心與跨平台

v0.2 整體結果：

| 環境 | 執行 | 結果 |
|---|---:|---|
| Windows 原生，Python 3.13.15、Node 24.22.1 | 完整 126 案＋新增來源路徑回歸 1 案 | PASS，無失敗；完整測試中的 symlink 案因 WinError 1314 跳過 1 案 |
| Ubuntu-26.04／WSL，Python 3.14.4、Node 24.22.1 | 127 案 | PASS，無失敗、無跳過；symlink 案實際通過 |

Windows 用現有 Node；WSL 的 Node 來自官方 checksum 核對過的 tarball，只放在專案 `.agf/qa/node-linux/`，在該次測試程序的 PATH 使用。它不是核心依賴，也沒有修改全域 PATH。缺少 Node 時，兩個 plugin syntax／contract 案會明確 skip，其餘核心仍可測試。原始測試輸出與 JSON 結果保留在本機 `.agf/qa/`。

Windows 完整測試開始後，另補上舊 manifest 來源路徑的拒絕／明示修復回歸；該案在 Windows 獨立通過。WSL 則重跑包含它的完整 127 案。Windows 沒有宣稱重跑最後版本的全部 127 案。

```console
python -X utf8 -m unittest discover -s tests -v
python scripts/agf.py audit
python scripts/agf.py check --root . --config templates/quality.framework.json --profile full
```

v0.2 執行完整 unittest 與靜態 audit。v0.1 曾從 CLI 實際執行 WSL 的 `check --profile full`，unit-tests 與 framework-audit 兩個檢查皆 PASS；PowerShell 與 POSIX shell 的薄入口也曾實際執行 doctor。這些較早的證據不列為本輪重新執行。

案例涵蓋批次操作的預覽、碰撞、來源漂移、失敗回復、特殊字元與編碼；來源頁行、截斷與解碼狀態；task freshness；選擇性配置／更新／回復與既有檔保留；共享與副本模式；從目標專案執行 runtime；Git hook 實際呼叫共用品質檢查。本輪新增 `.git`／`.svn`／`.hg` 管理資料保護，使用替身檔案，沒有寫入 SVN repository。

Windows 原生測試使用該平台的檔案 API，WSL 測試則使用 Linux API。這支持核心行為的跨平台證據，不能把某一端成功延伸成所有跨檔案系統、硬體或遠端環境都相容。Windows Git 對 WSL-owned UNC 目錄的信任限制仍由使用者判斷，工具不修改全域 safe.directory。

## v0.2 配置與舊版升級

新專案不選 skill 時，預設為 shared，只部署 6 個受管理檔案（規則入口、專案規則與 4 份指引），沒有工具 runtime；這是配置量觀察，不是 token 量測。

另以真實 `c411f52` 舊 commit 建立隔離來源，用舊 CLI 安裝 13 個 skills，再用新版 CLI 升級：

- 預覽列出 8 個退役技能，目標內容未變。
- 套用後保留 copy 模式及 5 個 skills，副本入口實際執行成功。
- Rollback 恢復 13 個 skills，manifest 逐值完整還原。
- 明確選 shared 後移除工具副本，共享入口實際執行成功；4 份部署指引的 5 個相對連結皆有效。
- 未受管理的筆記全程保持相同 SHA。結果保存在本機 `.agf/qa/v02-migration/result.json`。

獨立檢查找出新增 Claude host 時漏配保留技能、Windows 插件接受僅從根目錄開始的非完整路徑兩項問題；修正後以原重現再次確認。更新工具也拒絕默默轉換舊 manifest 中的另一平台路徑，須用目前環境的 `--source` 明示修復。另以注入寫入失敗驗證部分新檔能清理，既有使用者檔案保留。

## 可選工具

以下是 v0.1 的實際渲染／選用依賴證據；v0.2 未重新執行 Mermaid、draw.io 或 pypdf 驗收，相關核心腳本未變。

| 能力 | 既有證據 | 範圍 |
|---|---|---|
| Mermaid | 官方 12.3.0 bundle，透過既有 Playwright／Chrome 執行實際 render；flowchart、sequence、state 皆成功 | Flowchart 的中文字與分支標籤已檢視；包含特殊字元的三類圖做語法 probe。這不是所有版本的 mmdc 相容性保證 |
| draw.io | 產生未壓縮 XML，檢查 cell／parent／edge 引用 | 桌面 app 未安裝，未做原生 draw.io 匯出或視覺驗收 |
| PDF | pypdf 7.0.0 置於專案內隔離測試目錄；Windows／WSL 實際抽取自製單頁 PDF，確認文字與 page:1 錨點 | 核心環境缺少 pypdf 時仍正確回報 UNAVAILABLE；表格、公式、OCR 與大型真實 spec 未驗證 |
| 靜態網頁 | 10 個 localhost HTTPServer 案例，兩端通過 | 預覽、byte 上限、robots、redirect、覆寫與回傳 metadata；外部 example.com HTTPS 試抓遇到環境憑證鏈驗證失敗，工具回報錯誤且沒有發布頁面。外部成功擷取、登入及動態 JS 未驗證 |

實際 Mermaid 渲染找出了 sequence 標籤中 HTML entity 與分號的相容性問題；已改用官方語法的 Mermaid entity codes，再以同一引擎重驗。SVG 範例放在 `examples/diagrams/`。QA 依賴與臨時輸出放 `.agf/qa/`，未加入核心依賴或公開來源檔。

## Host、hooks 與 CI

四個 host 的 skills／規則部署以檔案配置及 target-runtime 測試驗證；未在四種真實模型 session 中量測自動觸發率。Doctor 的 executable discovery 不代表已登入或模型可用。

Git pre-commit 在隔離專案透過真正 Git 呼叫，包含 shared／copy 切換、共享來源失效時拒絕，以及 copy 模式下原始 source 搬走後仍能執行。OpenCode plugin 的 Node syntax、V1/V2 callback 與真 Python quick check 以 fake-host fixture 驗證；同一插件在 manifest 模式切換後重選入口，Windows 非完整來源路徑不會啟動檢查。真 OpenCode 內載入仍為 NOT_TESTED。其他 AI-host hooks 為版本相關的 review plan。它們不是 OS 或服務權限邊界。

GitHub Actions 與 GitLab CI 已提供共用檢查範本；遠端執行、runner 配置與受保護分支未驗證。Docker、K8s、QEMU、GDB 與 kernel upstream 流程提供範例／指引，未宣稱本輪完成相應部署、實機或 upstream 驗收。

## Skills 與學習

v0.2 的 5 個 skills 通過官方 skill-creator validator，並另做靜態結構及連結檢查。獨立代理只讀五個技能的 name／description 與 workflow、writing 指引，未讀技能本文、案例答案或作者自評，完成 10 項選用觀察：

| 請求目的 | 觀察到的選擇 |
|---|---|
| 商用 APP 產品討論、明確的股票程式功能實作 | 不選這五個 skills |
| 查 spec 特定欄位與條件 | read-research |
| PDF 指定頁抽文字 | 不選這五個 skills |
| 靜態追 kernel 輸入與狀態 | trace-code |
| STM32 已有卡住現象，唯讀分析 log | debug-root-cause |
| 審查指定 Boost patch | review-change |
| 學陌生 Boost library 的用途與測試 | guide-learning |
| 依設定寫小說、規劃投影片式影片 | 不選這五個 skills |

同一代理實際完成小說短文與分鏡提案，保留既定人物與世界設定，沒有套工程證據格式，也沒有宣稱已製作影片。這只是十項定性 smoke，沒有盲測標準答案、重複試驗或真實宿主觸發率量測。

v0.1 另有一次獨立 forward-test，使用適當 skills 與最少原始材料，沒有讀教材解答：

- 佇列問題：實際重現錯誤回傳後仍留下工作的現象，提出最小修法，在記憶體中驗證七種情境。
- Spec 帶讀：依條文確認 duplicate 與 capacity 同時成立時的順序，直接提供完整情境說明。
- 小拼字修改：辨認為局部工作，沒有啟動 Grill Me、角色團隊或無關測試。

上述都是少量 behavior smoke。佇列原始檔已包含故障提示及正確對照，不能當成盲測 RCA benchmark。真人理解、長期保留、一般化觸發率、成本及 token 改善比例皆未量測。[行為驗收](../evals/README.md)目前收錄 34 個可重跑案例，不代表 34 項皆已執行或通過。特殊授權只驗證指引與案例表述，未連接券商、燒錄／抹除板子或寫入 SVN repository。

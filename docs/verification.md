# 驗證紀錄

最近更新：2026-11-10（Asia/Taipei）。這份紀錄分開列出腳本、宿主整合、來源閱讀與真人學習的證據；下方較早章節保留各輪當時的範圍。

## 發布前檢查（2026-11-10）

- 修正來源摘錄的兩個問題：大小寫摺疊展開時可能截短查詢命中的原文；HTML 字元實體產生的換行可能被誤算為原始碼行號。新增回歸案例，Windows 與 WSL 的來源相關測試各 20 項通過。
- WSL Python 3.14.4 的 217 項 unittest 全通過；Windows Python 3.13.15 在隔離副本通過 200 項、略過 17 項平台條件測試。兩端 full profile 的 unit-tests 與 framework-audit 均 PASS；WSL 的 profile 執行時因 PATH 未含 rg 略過 4 項，之後補上 rg 重跑全部 217 項通過。格式 audit 沒有錯誤或警告。遠端 CI runner 尚未執行。
- 六個 Skill 通過官方格式檢查。在隔離目標以 shared、copy 模式配置四個宿主的全部 Skill，兩種模式各 30 個 Skill 檔案與來源逐 bytes 相符，status 無 drift。這驗證部署檔案，不代表四種宿主都已實際載入。
- 獨立新上下文只讀 Skill 的名稱與描述，12 題正反選用均符合案例設計；另測 4 題複合邊界。慢 SQL 除錯、migration 審查及程式追蹤教學可能同時適用兩個 Skill，靜態核對未見互斥規則。這是小樣本選擇觀察，沒有執行任務或觀察宿主自動觸發，不能推估誤觸率、漏觸率或證明某功能無用。題目與原始結果位於本機忽略目錄 `.agf/qa/skill-routing-20261110/`。
- 文件核對修正 `--output-dir` 的完整性描述：設定 byte 上限後，超限輸出可能不完整。真 CLI 測試中無上限保存 10,001 bytes 且 PASS；設 64 bytes 上限時保存 64 bytes、FAIL 並標示擷取不完整。

MCP 部分提供宿主工具選用指引，沒有自建 MCP server；本輪沒有連線真實 MCP、資料庫或測量真實宿主觸發率。既有有／無框架試驗及其 token 限制見[成對結果](../evals/paired/results-2026-11-09.md)。

## App 教學筆記的選擇性採納（2026-11-10）

先讀 HTML 與文字參考，對照現有架構與規範；來源、雜湊、無法重讀的文字檔及不採納的固定流程，記於[參考材料取捨](skillkit-study.md)。本輪只補資料轉換、並行交易及 API／模型輸出的條件式核對，不新增技能、執行器或依賴，也未執行附件 JavaScript、範例或設定。

- **配置與檢查：** Windows Python 3.13.15、WSL Python 3.14.4 各從 `a7a7e97` 的舊版配置 shared、copy，再實際 update。四組 status ready；workflow、trace reference、review-sql 本文與 reference 逐 bytes 相符，未受管理檔案保留。相關 audit／manage 共 50 項 unittest，WSL 全通過，Windows 通過 42、平台略過 8；兩端 package audit 無錯誤及警告，review-sql 官方格式驗證通過。本輪沒有程式變更，未重跑完整 214 項。
- **資料流試用：** 新代理從部署入口完成三個原始合成請求，沒有觀察條件。它指出 `int()` 是前導零第一次消失的位置，保存與回應轉型不會恢復原值；沒有自動修程式或冒稱寫 DB。測試者另行實跑同一段合成程式，重現 `00042` → 42 → `42`。代理未回報讀取新增的 trace-contract 表列，因此這只支持任務結果，不能歸因為該新增內容的效果。
- **權限與交易試用：** 同一代理依分享規則拒絕 private_A、允許 shared_A，不將模型 allow=true 當作授權，也未執行模型 HTML。它依指定 PostgreSQL Read Committed 交錯指出兩邊都可能查無反向 like，提交後兩筆 like 仍可沒有 match，並區分方向性唯一鍵與業務條件。此為來源支持的靜態判讀，沒有真資料庫並行測試、真實 API 或安全成效驗收。
- **未新增的檢查：** 本機兩個 Python 版本的空 unittest discovery 均回 exit 5，full profile 為 FAIL；曾懷疑的誤報成功未重現，因此沒有增加包裝器。這沒有驗證 CI Python 3.11 或其他 runner，原始紀錄在 `.agf/qa/appnotes-tools-20261110/`。

一般案例增為 57、資料庫案例 7，ID、skill 參照及 JSON 靜態檢查通過；只有上述三項是本輪新代理試用。主驗證者已回讀答案，部署、測試、原始材料及程式重現在本機忽略目錄 `.agf/qa/appnotes-review-20261110/`。未比較無框架基準、所有案例、實際 token 或真人理解，不能宣稱品質或成本改善。

## Claude Code 參考附件的選擇性採納（2026-11-09）

本輪只閱讀使用者的 agent-skillkit 附件；清單、識別雜湊、重複能力與靜態風險見[套件取捨](skillkit-study.md)。未執行附件 installer／scripts，也未複製其程式。採納三個窄改進：專案術語的情境判讀、清理副本回查原文，以及偶發失敗的安全重跑；沒有新增技能、核心程式或外部依賴。

- **配置與更新：** Windows Python 3.13.15、WSL Python 3.14.4，各從 `e0fbd8a` 的舊指引配置 shared／copy 隔離目標，再以修改版實際 update。四組 status ready，writing、tools、debug-root-cause 本文逐 bytes 相符，未受管理檔案保留。
- **相關檢查：** audit／manage 的 50 項既有 unittest，WSL 全通過；Windows 通過 42、平台／symlink 條件略過 8。兩端 package audit PASS、零錯誤與警告；debug-root-cause 通過官方 skill-creator 格式驗證，案例 ID 與 skill 參照核對通過。這輪沒有程式變更，未重跑完整 214 項核心測試。
- **獨立行為：** 新上下文代理從部署後入口讀取指引與兩個已安裝 skills，只取得三個原始請求及合成材料，沒有評分條件。術語稿只修應用消息，保留物理量、識別字、引述與真實 AI 揭露。規格核對辨認清理稿漏失 B 類暫存要求，使用材料字串行號，未冒稱取得 PDF、hash 或正式頁碼。debug 判讀保留零次未執行、首次失敗與各次條件，提出唯讀下一步，沒有重跑付款；它的後續重跑建議列次數與時間，未另列輸出量上限，不能由此認定所有觀察項均滿足或已可執行重跑。

主驗證者已回讀實際答案。一般案例增為 55、中文改寫 11；只有上述三項是本輪行為試用，不把案例總數或格式通過當作全數執行。原始命令、測試輸出、配置核對與答案保存在本機忽略目錄 `.agf/qa/skillkit-review-20261109/`。

以上未比較無框架基準、真人閱讀、實際 token、所有宿主或附件腳本的動態行為；沒有宣稱消除 AI 味、改善故障率或已驗證附件安全。

## 輸出預算、記憶及來源取捨（2026-11-09）

本輪新增可選的原始輸出 byte 預算，並在本框架品質設定啟用；六個 skills 的入口與標準庫核心不增加外部依賴。記憶、白話教學、少量示例、歌詞標記與運鏡補在既有位置，全部來源、採納與無法取得的文章見[取捨紀錄](memory-prompt-study.md)。

- **回歸與品質流程：** 新增八項真實程序回歸，涵蓋雙 pipe 共用上限、恰好等於上限、持續大量輸出、UTF-8 邊界、無效參數啟動前拒絕、逾時及品質設定；既有 check／hook 的無效設定案例另補 byte 上限。先加入的五項回歸在修改前因缺少參數失敗，修改後完整 214 項在 WSL 全通過，Windows 通過 197、平台略過 17。兩端另實跑有 byte 上限的 full profile，unit-tests 與 audit 皆 PASS、capture_complete 為 true。原始輸出在本機 `.agf/qa/next-step-20261109/`。
- **部署與真 CLI：** Windows／WSL 各配置 shared、copy 的隔離目標，指引、guide-learning reference、outputs 與來源逐 bytes 核對。四組實際從部署入口執行超限命令，CLI 退出 1、結果 125、不完整擷取，保存的 stdout＋stderr 恰為 64 bytes。沒有將子程序的 0 或檔案存在當作完整成功。
- **並行與清理邊界：** 獨立審查在兩端各三次同時高壓寫兩個 pipe，合計保存量皆為 100001 bytes，結果 FAIL／125。父程序先結束、後代持管線的情境兩端都未誤報成功；WSL 清除同 process group，Windows 未保證清除後代，測試者另清除自己的測試程序。這個限制已寫入 CLI，記錄在 `.agf/qa/bounded-review-20261109/`。
- **記憶與教學：** 新上下文先做一組按指引的文字試用，再做同材料有／無框架各一次的新代理對照。兩組都回查原始事件、撤回 timeout／網路原因的過度結論，並保留 mutex 所有條件；匿名審查未判出實質勝者。測試者另實跑兩份 Python 範例，正常及例外釋鎖檢查通過。方法、措辭小缺點與限制見[成對結果](../evals/paired/results-memory-2026-11-09.md)，不能據此宣稱跨供應商、真人理解或 token 改善。
- **工具實測：** Windows／WSL 各在 203 個合成 Python 檔比較 rg 與 context；皆找出五個文字位置，AST 只證實一個靜態呼叫。結果數、字元截斷、無結果與超長輸出失敗均符合約定；此樣本 rg 較快、AGF JSON 較短，沒有實際 token。離線資料庫替身兩端各九項契約通過，未驗證真實 MCP 協定或服務。腳本和摘要在 `.agf/qa/tool-eval-20261109/`。
- **發布掃描：** 隔離下載 Gitleaks v8.30.1，核對官方 SHA256。追蹤檔案快照及全部可達 refs 的掃描均零發現；隨機產生、未發行的合成權杖正向控制偵測到一項。最初過於明顯的序列假值未被偵測，保留了控制修正紀錄。這是工具規則範圍的結果，不是無秘密保證，也未全域安裝或啟用 hook。

本輪沒有新增模型帳號、外部記憶、圖譜或爬蟲服務。PawSQL／Bytebase／Inspector 真實連線、跨供應商交接、大規模原生用量對照、真人教學及實際歌曲／影片仍未驗；不能用離線替身、描述稿或 Python 範例取代這些驗收。

## 推送前品質檢查（2026-11-09）

以本地 `1411fda` 執行 GitHub CI 同一個 full profile：WSL Python 3.14.4 的 206 項 unittest 全部通過；Windows Python 3.13.15 在隔離來源副本通過 189 項、因平台條件略過 17 項。兩端 package audit 通過且無警告，六個 skills 均通過 skill-creator 格式檢查。full profile 截斷了測試細節，因此另行重跑 unittest 保存完整輸出，才確認上述數量；原始輸出保存在本機忽略的 `.agf/qa/release-review/`。

獨立審查對照現有 CLI、技能與文件，修正既有專案新增技能應用 update、學習文件的技能數量及 micro-os 教學漏列技能。Windows 另實跑九條文件命令，均成功；53 個一般案例的 ID、指定 artifacts 與技能參照通過靜態核對。這些檢查不能證明所有案例已執行，也不能保證所有文件都沒有錯誤。

逐筆檢查待推送五個提交的新增文字及目前受追蹤檔案，有限規則未發現明顯憑證、私人路徑或誤追蹤的私鑰與快取；未執行專用秘密掃描器，也不能排除其他格式。實際 GitHub main 當時與本機 origin/main 一致。此次沒有連線真實 PawSQL／Bytebase MCP 或資料庫、沒有驗證遠端 CI，也沒有推送；本機檢查與外部整合驗收分開看。

## 寫作重述、簡報重點與媒體驗收（2026-11-09）

先讀 repository 規範、CLI 分派與配置流程。需求邊界、版本、來源、敏感資料、測試及停止條件已有處理，這輪只補既有 writing 與兩份格式參考的缺口：跨段重述、無依據的正反平衡、簡報篇幅與頁序，以及圖片／影音的具體驗收線索。圖片入口接回原有規則；保留刻意畫風和中性對照，不規定每篇都表態或用固定結語。六個 skills、核心、相依與 CI 未改。

- **配置與更新：** Windows 原生 Python 3.13.15、WSL Python 3.14.4，各在隔離來源先配置 `536fde0` 的四份舊指引，再以本地修改版實際 update shared、copy 目標。四組 status ready、clean；writing 本文、project rules 前綴及兩份按需參考與來源逐 bytes 核對，保留未受管理檔案。新專案仍未預設安裝 skill，沒有新增服務。
- **相關檢查：** 既有 audit、manage 共 50 項 unittest，Windows 通過 42、因平台／symlink 條件略過 8，WSL 50 項全部通過。兩端 package audit 均 PASS，零錯誤與警告；案例 ID、技能參照與 JSON 檢查通過。本輪是指引及案例修改，未重跑完整 206 項核心測試，前輪結果保留於下方。
- **文字行為：** 無本輪對話歷史的新代理從部署後入口讀 writing，僅取得原始請求、事實與草稿。決策稿依未達上線條件判斷本週不啟用，保留回歸失敗與效率未量測，刪去空泛重述。案例初稿另要求修復下一步，但原始請求只問是否啟用；已移除這個額外觀察條件，保留修改前案例與原始成稿，沒有追加提示或重試。中性對照保留兩個方案的價格、保存期間與需求未知，未擅自選方案或為去除對稱句改寫清楚原文。
- **簡報與媒體文字審查：** 另一新代理從同一部署入口讀到兩份格式參考，交付四頁含封面及逐頁講稿。內容以費用決策、成本／測試表、尖峰限制及核准問題安排，保留第 95 百分位與金額，未將暫緩建議寫成已核准決定。媒體任務依剪輯人員文字紀錄只列第二鏡外套錯色與招牌錯字，保留四指、漂浮設定；聲音及同步列待驗，未假稱看圖、聆聽、播放或生成成品。引述的 `pilot-oct.md` 僅來自提供材料，代理明示沒有直接讀到原檔。主驗證者已回讀兩份實際答案。

一般案例增為 53 項、中文改寫 10 項；只將本輪四項原始請求交給代理，觀察條件未放入隔離目標，不能以案例總數宣稱全數經宿主實測。本機命令、原始測試輸出及配置核對保存在忽略的 `.agf/qa/writing-media-20261109/`。

本輪沒有新圖片、音訊、影片或實際投影片成品，未作視覺／聆聽驗收、真人理解研究、無框架對照或完整 usage 量測；文字審查與靜態通過不能證明作品已消除 AI 味，也不能證明 token 改善。沒有需要人工決定的新架構或權限變更。

## 最小工具選型與 SQL 審查（2026-11-09）

先盤點現有 skills、CLI、宿主工具、Docker 與 CI，再新增一個可選的 [review-sql](../skills/review-sql/SKILL.md)，合併效能分析與資料庫變更審查；跨來源選型放入[按需參考](../templates/tool-selection/README.md)。其餘領域沿用既有能力或延後，理由與盤點範圍見[能力取捨](capability-decisions.md)。沒有增加核心依賴、通用 router、查詢執行器或部署服務。

- **格式與核心：** 六個 skills 均通過官方 skill-creator validator，以 UTF-8 執行；Windows／WSL package audit 均 PASS，零錯誤與警告。完整 unittest 仍為 206 項：Windows 原生 Python 3.13.15 在 C 槽來源副本通過 189、因平台／symlink 條件略過 17；WSL Python 3.14.4 配既有 QA Node 通過全部 206，零略過。沒有把平台略過列為通過。
- **配置與移除：** Windows／WSL 各實際配置 shared、copy 隔離目標，`status` ready；部署 skill 本文、metadata、reference 與來源逐 bytes 相符，copy runtime 包含選型參考。四組 rollback 實際套用後移除該次技能配置，保留預先建立的未受管理檔案。這驗證的是整筆配置回復，不是任意移除單一 skill 的功能。
- **替身工具：** [fixture_host.py](../evals/database-review/fixture_host.py) 完全離線、永遠 dry-run。兩端各跑九項 smoke：四種能力狀態、無效狀態、未知工具、拒絕 query／deploy，以及只回傳未核准草稿。退出碼與 `deployed: false` 均符合約定；替身不代表真實服務或權限邊界。
- **六項工具選擇：** 新代理只取得原始合成材料、候選描述及選型參考，沒有預期答案。它用 `rg` 區分定義與呼叫，以 SQLite 唯讀連線、參數化條件、有限欄位及台北日期邊界找當日失敗工作；架構關係與產品介紹回查原檔。慢 SQL 與 production 索引選到 `review-sql` 候選，沒有假稱載入當時未提供的完整 skill，也未冒稱呼叫 RAGFlow、GraphRAG、PawSQL 或 Bytebase。
- **部署後 SQL 行為：** 另一新代理從已部署 copy 入口讀取 skill，針對 PostgreSQL 合成慢查詢，實際只呼叫三次能力 probe 與一次未核准的草稿提案，沒有呼叫 query／deploy。它將授權受限的 PawSQL 改為解讀既有估計計畫，保留索引為待驗證建議，交付 Migration／Rollback、排序語意、索引副作用及前後測試路線，沒有宣稱已改善效能。初稿曾混淆包覆命令與內層 Python 退出碼，經一次證據追問後保留「內層未捕捉」；獨立 preflight 才有原始 exit 3，不能視為整次零返工。
- **唯讀與材料不足：** 獨立代理判讀 production 的 `EXPLAIN ANALYZE UPDATE`，指出它會實際更新且沒有 WHERE，未執行，也未宣稱 rollback 能消除所有影響。只有 SQL、缺引擎與 Schema 的請求得到待驗證假設和必要缺口，沒有「最佳索引」或執行成功的結論。
- **審查警告與負例：** 同一代理續測「Bytebase 因大小略過檢查、無 approver、但有 rollout 權限」的原始請求，未將 Warning 或部署權限當作核准，僅列變更與審查缺口。一般 Python 差異則排除 `review-sql`，指出自訂型別的乘法與加法可能不同；未假稱執行測試或載入其他 skill。

一般案例增為 51 項，另有六項資料庫案例；ID、技能參照與 JSON 靜態檢查通過。案例檔與上述實際觀察分開，不以案例數宣稱全部經完整宿主執行。原始命令、完整測試輸出、部署核對及替身 smoke 位於本機忽略目錄 `.agf/qa/capability-mvp-20261109/`；代理使用的隔離來源與成果位置另列於該輪本機紀錄。

本輪未連線真實 RAGFlow、GraphRAG、PawSQL、Bytebase 或正式資料庫，沒有啟用碼、方案或端到端服務驗收。六種工具選擇與少量代理試用只支持這些合成案例；未量測本輪完整 token、延遲或無框架差異，也未驗遠端 CI、正式權限強制隔離及所有模型的自動選用。

## 繼續驗證：桌面代理、不同模型交接及 WSL Node（2026-11-09）

WSL 沿用先前保存在專案 QA 的 Linux Node，僅調整測試子程序 PATH，Python 3.14.4 的完整 **206 項 unittest 全部通過、零略過**；原先兩項 OpenCode plugin 語法及模擬宿主測試已執行。首次補跑曾因臨時 PATH 漏掉 `rg` 而略過四項，修正後重跑得到上述結果；真 OpenCode 宿主載入仍未測。

現有桌面代理在隔離合成目錄完成 trace、debug、中文改寫與交接的有／無框架各一組。兩組結果在主要正確性條件上均通過；debug 修法相同，主驗證者另跑隱藏案例通過，接手者均辨認設定變更與過期驗證。框架組交接產生時自行回報一次失敗的寫檔命令，之後改用另一命令成功；沒有追加使用者修正。代理完整工具事件和個別 usage 不可取得，不能完整核算工具式對照的越界、重試或 token，也不能推成所有任務無差異。

另將先前 `gpt-6.1-sol` 產生的交接文字由測試者置入隔離目錄，再由新對話的 `gpt-6.1-terra` 代理接手；它實際核對來源並重跑過期檢查，指出原始 observer 檔缺少。這是單次同供應商跨模型觀察，未驗證不同供應商。

方法、結果與限制見[桌面代理驗證](../evals/paired/results-native-2026-11-09.md)。WSL Linux CLI 尚未登入，使用者目前無法完成登入；未更動帳號或繞過 sandbox。原生 CLI 的成對工具軌跡及 usage、不同供應商接手、真人理解與長期學習保留仍未測。

## 公開教學、hook 設定與有／無框架對照（2026-11-09）

這輪修正公開後仍寫「尚未發布」的教學，讓 Git hook 安裝與執行共用設定驗證，並實跑 trace、debug、中文改寫與跨對話交接的[小型文字層對照](../evals/paired/results-2026-11-09.md)。未增加 skill 或外部相依。

Windows 原生 Python 3.13.15（C 槽隔離來源副本）與 WSL Python 3.14.4（原工作目錄）各跑完整 **206 項**測試，零失敗；Windows 通過 189、略過 17 項平台／symlink 條件，WSL 通過 204、因缺少 Node 略過 2 項。新增三項回歸涵蓋 18 組無效設定、安裝時不執行檢查，以及先驗證所有選定設定才啟動第一條命令。Package audit 與 `git diff --check` 通過。

Git hook 的 `--apply` 現在重用 `check` 的非執行式設定驗證，檢查名稱、argv、profiles、cwd 範圍及存在性、timeout、encoding 與整數版本；無效設定不留下 hook／紀錄。獨立審查另從 WSL 真實 CLI 跑一個合法案例與 12 個不合法案例，確認無效設定為 exit 2，第一條命令的 marker 未建立。安裝時不執行配置中的命令；執行檔是否存在與命令能否通過仍於執行時確認。既有 shared／copy、來源移走與 Git 真正呼叫 hook 的測試持續通過，原始證據在本機 `.agf/qa/hook-validation-20261109/`、`followup-20261109/`。

GitHub metadata 確認儲存庫 public；Windows／WSL 各實際完成公開網址 clone，並以目前來源執行教學的 task record／check／handoff 和 profile show，共各五條命令。教學新增可照做的交接範例及偏好／決策記憶的來源、適用範圍、日期與更正位置。未對真實 micro-os 套用配置；clone 與 CLI 證據在本機 `.agf/qa/published-guide-20261109/`。

對照固定 Codex CLI `0.167.0-alpha.3.2`、指定 `gpt-6.1-sol`、medium reasoning、框架 `ffa02b1`。原生工具模式因宿主拒絕命令而中止，沒有把受阻呼叫算成任務成功；改為兩組同材料、同無工具限制，框架組直接取得相關既有指引。10 個新 thread 包含交接產生與接手，獨立匿名審查的五個階段皆為兩組 8／8；沒有觀察到越界產物或需要外部補正的返工。Debug 兩份相同最小修法由評分者另跑回歸與隱藏案例通過；接手者都辨認設定改變、過期驗證與記憶範圍。模型沒有冒稱執行這些檢查。

原始 `turn.completed.usage` 重新核算：無框架 input＋output 為 **123,445**、有框架為 **141,226**；本次增加 **17,781（約 14.4%）**，有效試驗 cache 均為 0。設定失敗的已知 CLI 用量另列 input 548,250、cached 443,392、output 2,209；一筆中止用量及主對話／評分代理用量未知。不能將受測呼叫或已知設定成本冒充整次開發的總成本。

完整條件、每項用量、盲審方法、失敗嘗試及限制見上方對照結果；本機原始證據在 `.agf/qa/paired-20261109/`、`paired-blind-grade-20261109/`。單次小樣本、明確提示與整份原文輸入有侷限；這次沒有證明原生選用、工具執行、context 選讀、跨供應商模型或真人學習效果，也不因此繼續增加框架規則。

## 工具缺陷修正、中文改寫與續接（2026-11-09）

這輪保留五個 skills、標準庫核心與既有部署模式，補強現有指引及工具，沒有新增模型 orchestrator、索引服務或相依套件。先由獨立代理唯讀找出可重現問題，再修正並加入 13 項回歸，完整測試由 190 增為 203 項。

| 環境 | 完整測試 | 實際結果 |
|---|---:|---|
| Windows 原生 Python 3.13.15，C 槽暫存來源副本 | 203 項 | 186 通過、17 略過，零失敗；略過 POSIX、symlink 權限等平台條件。既有 Node plugin 測試實際通過 |
| Ubuntu-26.04／WSL Python 3.14.4，原工作目錄 | 203 項 | 201 通過、2 略過，零失敗；缺少 Node，未跑 JS syntax／fake-host contract 兩項 |

兩端 package audit 均 PASS，零錯誤與警告；`git diff --check` 通過。Windows 初次直接從 UNC 跑完整測試，在 180 秒上限內未完成，不能列為通過；後來將相同程式、測試及套件資料複製到 C 槽暫存目錄，以原生 Windows Python 重跑完成。原始結果與中斷時的測試資料保存在本機 `.agf/qa/optimization-20261109/`，沒有變更 Git 全域信任設定。

Windows／WSL 各以 shared、copy 隔離配置，四組 install／status 均為 ready、clean。部署後四份指引與 trace-code 本文、reference 與當前來源逐 bytes 相符；從目標工作目錄實際執行 task record／check／handoff，確認新欄位與來源過期檢查可用。copy 模式另將來源快照移開，仍能執行。重跑腳本及原始命令在上述本機目錄的 `deployment/`；這只驗證檔案配置與 CLI，不代表宿主已載入技能。

已修正的行為及限制：

- `context search` 原本只限筆數，單筆仍可回傳逾十萬字元；現在 `--max-chars` 預設限制匹配文字合計 16,000 字元，保留來源行號及單筆截短標示。超長行使底層 JSON 在第一筆匹配前截斷時，改為明確錯誤，不回傳容易被誤讀為查無結果的空陣列。這是輸出界線，未量測模型 token；完整長行片段仍需縮小來源或用原生搜尋定位。
- `context extract` 拒絕 FIFO／裝置／目錄；POSIX 非阻塞開檔後再次檢查類型，從同一 descriptor 計算雜湊，避免為雜湊重開已被替換的路徑。回歸涵蓋一般檔、原始 bytes 雜湊、FIFO 及開檔競態；不宣稱內容是原子快照，也未限制單行記憶體或全檔雜湊 I/O。
- `run`／`check` 在啟動命令前拒絕非文字 codec 與不支援 replacement 的 codec。反例為 `rot_13`、`base64_codec`、`hex_codec`、`idna`；回歸確認命令 marker 與輸出目錄都未建立，避免執行有副作用的命令後才因解碼錯誤丟失結果。UTF-8、CP950、非法 bytes、逾時及原始輸出保存的既有測試持續通過。
- `task record`／`handoff` 保留 `verification`、`next_steps`、`boundaries`，加入紀錄建立時間；舊版 v1 缺少新欄位仍可用。格式錯誤不再拆成字元條列，repository 缺少或錯誤型別的 `head` 會給可處理的錯誤。

另由未讀預期答案的獨立代理執行兩組有限行為試用：

- 中文寫作四項原始請求：長修飾與主體不明的互斥鎖說明、重試規範、單一錯字及 commit 草稿。成果保留責任人、先後、否定、2 秒與一次的條件；沒有補造入列元件、效能資料或作者歷史動機。單一錯字只改「服物」為「服務」。這些是另設材料的觀察，不代表新收錄的 8 組 [writing-cases](../evals/writing-cases.json) 全數執行。
- WSL 真實 CLI 交接：記錄、檢查及產生交接保留新欄位；移除新欄位的 v1 副本仍可用。改動證據來源後，check 為 exit 1、handoff 為 exit 2，沒有產生新交接；重新執行原本驗證也確實失敗。對舊權限、舊圖解偏好與當次指示衝突的續接請求，代理沿用本次本地測試授權及純文字偏好，沒有承接部署權限。

原始命令及產物在本機 `writing-forward.md`、`handoff-forward/`。一般行為案例增為 45 項，另有 8 項中文改寫材料，ID、skill 參照與 JSON 靜態檢查通過；這不表示全部案例都經實際宿主測試。兩篇論文的英文證據、預測閱讀時間與中文編輯選擇見[研究範圍](writing-research.md)。

尚未實際啟動不同供應商模型作配對交接，未量測真人理解、教學保留或完整任務 usage，不能宣稱可讀性或 token 改善比例。CI／hooks 只沿用本地相應測試，遠端 runner、正式部署與權限強制隔離仍不在本輪證據範圍。

## 中文表達、交接與學習法（2026-11-09）

閱讀兩篇英文預印本後，將中文表達的採用範圍與限制記在 [research.md](research.md)。本輪只修改既有指引與教學參考，沒有新增 skill、腳本或依賴。

- Windows 原生 Python 3.13.15（工作目錄位於 WSL UNC）及 WSL Python 3.14.4：以隔離測試來源和目標，分別執行 shared／copy 的 install、改變三份來源後 update，以及 status；部署後的寫作、交接指引和 `guide-learning` 本文及兩份參考均與目前來源逐 bytes 相符，status ready。結果不代表宿主一定會選用或載入這些內容。
- Windows／WSL 靜態 audit 通過，沒有錯誤或警告；`guide-learning` 通過官方 skill-creator 格式檢查。獨立代理用容量不足與重複識別碼的合成例子檢查中文改寫，保留了檢查先後、兩種失敗條件及否定；這是一個例子，不是讀者理解度研究。

未重跑完整單元測試，也未測量真實學習成效、不同模型的交接成功率或 token 用量。論文對英文的結果不能直接視為中文規則的驗證。

## 使用者連結去重與融合（2026-11-09）

來源閱讀、固定版本、授權觀察與取捨見 [link-study.md](link-study.md)，未安裝或執行任何上游工具。五個 skills 與四份部署指引的數量不變；`read-research` 增加聚焦文獻比較，跨格式成果放一份按需參考。核心程式只擴充既有 audit 的 templates Markdown 掃描，沒有新依賴、索引器、記憶引擎、renderer 或 provider。

- **可重現的腳本修正：** 新增 nested template 相鄰參考缺檔測試。修正前 Windows／WSL 各 4 通過、1 失敗，證明舊版錯誤回 PASS；修正後兩端各 5 項全通過、無跳過。補回檔案恢復 PASS，正常外部／頁內／mailto 連結不誤判。掃描仍只查本地檔案存在，不驗錨點、外部網址或完整 Markdown 語法。未重跑完整單元測試；前一輪 187 案另列於下方。
- **配置與更新：** Windows Python 3.13.15 與 WSL Python 3.14.4，各自實際 install／update／status，含 shared、copy 及單獨選取 `read-research`。規則、四份 guides、技能本文及兩份 references 與本地修改版逐 bytes 相符；從目標執行正確 CLI 的 audit 皆通過，status ready。copy 有新成果參考及有效相鄰連結，沒有將維護者研究清單帶入 runtime。結果在本機 `.agf/qa/link-study-*/result.json`；Windows 仍於 WSL UNC 工作目錄測試。
- **發布檔案核對：** 新參考最初命名為 `templates/artifacts/`，被既有 `artifacts/` 忽略規則排除；於提交前發現並改名 `templates/outputs/`，保留原忽略規則。內容未變，更名後兩端重新配置與更新核對；檔案也列入待提交清單，沒有以本機檔案存在冒充發布完整。
- **獨立行為觀察：** 無本輪對話歷史的新代理，使用已部署的更名前同內容快照、候選 metadata 與原始合成材料，完成五項文字工作。僅文獻問題實際載入 `read-research`；R1 正式版取代預印本、部落格不算新研究，R2 僅摘要且條件不同，不編普遍有效結論。擷取任務辨認 caption 沒有圖表數字；空 caller 查詢結合未提交變更、截斷與函式指標引用判斷不可據此刪除，也正確指出 `#ifdef` 的已定義零值不等於停用。
- **表達與創作觀察：** 同一代理保留 64 bytes、「必須／禁止／不得」與否定，沒有執行樣本內的上傳指令；依已定設定直接交付四行副歌及合計三十秒的估計分鏡，未捏造演唱或 MP4。答案與所讀來源在本機 `.agf/qa/link-behavior/answer.md`。本次限制不執行外部工具，因此未跑 profile show，也未假稱取得有效偏好。

以上是少量 qualitative smoke，沒有無框架 baseline、真實 host 自動觸發率、真人風格／學習／觀眾評估或 provider usage；沒有真實 PDF／HTML／PPTX／音訊／歌曲／影片產出驗收。不能由代理自評、來源數或靜態 PASS 推論一般品質、完整安全性或 token 節省。

Windows／WSL package audit 皆 PASS，零錯誤與警告；受影響的 `read-research` 通過官方 skill-creator validator；43 個案例的 ID 與 skill 參照靜態核對通過，`git diff --check` 無錯誤。案例數不表示全數已執行，來源回饋也不等於自行重現。

## 按需簡報指引（2026-11-09）

本輪新增一份 `templates/presentations/README.md`，在既有規則、writing／tools 指引接上條件入口；五個 skills、四份部署指引與 Python 核心不變，未新增依賴、YAML schema、排版引擎或媒體服務。只改文字及行為案例，未重跑完整單元測試；下方 187 案屬前一輪二進位變更的證據。

- **配置與更新：** Windows 原生 Python 3.13.15 與 WSL Python 3.14.4，在各自的隔離目標實際 install／update／status。shared 仍為 6 個受管理檔案、零個預設 skills；copy 包含新簡報參考，兩端指引與來源逐 bytes 相符、status ready，且相鄰圖解連結可解析。本機核對結果在 `.agf/qa/presentations-*/result.json`；Windows 測試仍位於 WSL UNC 工作目錄。
- **獨立行為觀察：** 沒有本輪對話歷史的新代理，只取得部署入口、按需參考、原始合成 CSV 與本地替身工具，完成四項任務。月報正確呈現 81%、77%、70%、65%，區分月差與百分點，未提供目標時不判達標或補零，亦未編造下降原因。作品先讀實際頁面 ID，只改第三頁標題與三欄配置；一次 update 後讀回 version 8，其他頁、原欄位內容、主題與 private 分享設定保持不變，已另行比對。
- **缺能力時的成果：** 缺 YAML schema／renderer、音訊與影片工具時，交付內容稿和講稿，沒有編造 YAML 規格、PPTX、MP4 或作品 URL。流程圖保留 Mermaid 文字與原始分支，明確區分圖源、SVG 嵌入與 PowerPoint 原生節點編輯；未渲染、未分享，也沒有將內部成本資料上傳。四項答案、產物及替身 action log 留在本機 `.agf/qa/presentation-behavior/`，不隨公開來源散布。

這是少量合成任務的定性 smoke，沒有無框架 baseline，不代表所有 host／模型都會照做，也不證明簡報設計品質或 token 改善。Pandoc、Marp、Slidev、PptxGenJS 只查一手文件及原始回報，本輪未安裝／執行；沒有真實 PPTX 排版、PowerPoint 開啟、配音、MP4、離線 HTML 或帳號分享驗收。

本輪 Windows／WSL package audit 均 PASS、零錯誤與警告；另核對新參考的本地連結與 38 個案例的 ID／skill 參照，`git diff --check` 通過。這些靜態結果不等於 38 案全數已執行，也不保證沒有其他缺陷或私人資料。

## 有界二進位讀取（2026-11-09）

沿用五個 skills 與既有 CLI，新增純標準庫的 `binary bytes|bits|dump`；沒有新增獨立 skill、依賴或安裝步驟。預設數值為無號 little-endian、bits 為 LSB-first，`bytes --endian big` 需明示；不因欄位名稱猜測檔案 offset，也不把檔案讀取擴張成硬體連線。

- **測試：** 新增 14 項二進位測試，WSL 全通過；Windows 12 通過、2 跳過（POSIX FIFO 與缺少 symlink 權限）。WSL Python 3.14.4 配既有隔離 Node 24.22.1 的完整 187 項皆通過；Windows Python 3.13.15 本輪只重跑這 14 項，沒有重跑全部 187 項。Windows 仍在 WSL UNC 工作目錄執行。
- **讀取行為：** 用已知 bytes 驗證 uint24 兩種端序、uint64／uint512 十進位字串精度、跨 byte 欄位，以及 bit offset 7／寬度 64 需讀 9 bytes 的案例。選定片段的 hash 與整檔 hash 分開，控制字元不會原樣出現在 dump 的 ASCII 區。
- **錯誤與副作用：** 負數、零／過大長度及越界位置在接觸來源前拒絕；檔尾不足的數值讀取回 ERROR／非零退出，dump 回 PARTIAL／退出 1。另驗證 descriptor 類型重驗、短讀累積、失敗後關閉，以及合成來源內容保持不變。一般檔案類型檢查不是沙箱或原子快照，也不證明虛擬檔案系統內容是靜態資料。
- **真實 CLI 與配置：** Windows／WSL 各以教學用合成 bytes 執行六種命令，核對 LE／BE、位元欄位、dump、部分讀取及錯誤的值與退出碼。兩端各自實際配置 shared／copy 隔離目標，從目標目錄執行新命令並確認部署 tools 指引包含新規則。另把教學建立檔案的原始命令交給 PowerShell／Bash 執行，確認 bytes 正確，重複執行會拒絕覆寫。沒有讀取真實韌體、記憶體裝置或硬體暫存器。
- **審查：** 獨立唯讀審查核對數值順序、讀取上限、檔案類型與資源關閉，沒有發現需修正的實質問題；靜態 package audit 通過。這些合成案例不能保證沒有其他 bug 或所有平台皆相容。

本機原始紀錄放在忽略的 `.agf/qa/binary-qa-*.json`、`binary-wsl-tests.log` 與 `binary-windows-tests.log`；教學與參數見 [CLI 二進位操作](cli.md)。

## 圖源、樣板與轉移統計（2026-11-09）

本輪沿用五個 skills、四份部署指引和既有 `diagram` 命令，增加八份文字樣板及一個有界的 `diagram transitions` 統計子命令，沒有新增依賴、技能或服務。一般圖解直接寫 `.mmd`，渲染交 mermaid-cli；這是代理工作指引，不是強制宿主攔截器，也未重新驗證四種真實 AI session 的選用行為。

- **完整測試：** WSL Python 3.14.4，既有隔離 Node 24.22.1，173 項全部通過；Windows Python 3.13.15，173 項中 160 通過、13 項平台相關測試跳過。Windows 仍從 WSL UNC 路徑執行，不代表所有 NTFS／ACL 情境通過。受影響的圖解測試共 22 項，兩端皆通過。
- **計數與失敗行為：** 驗證不同裝置的交錯紀錄不相接、不依 timestamp 偷排序、重複狀態保留自轉移、BOM／引號／三種分隔符號，以及錯誤資料、超限與既有輸出被拒絕。統計 JSON 可直接產生狀態 `.mmd`；圖中只含觀察到的相鄰轉移，不補起點、終點或重試路徑。
- **輸入邊界：** 審查發現換行標記可能使原始狀態改名或分支顯示空白，已拒絕表格狀態中的換行標記，並按顯示文字檢查分支；無效 JSON `shape`／`kind` 也改為受控錯誤。模型產圖會檢查 15 節點、12 字標籤及判斷出線標籤；手寫 `.mmd` 不由簡單宣告檢查器全面驗證。
- **既有引擎驗證：** 八份樣板、同步後的交易範例，以及含換行與特殊字元的三類模型，共 12 份圖源由既有官方 Mermaid 12.3.0 bundle 經 Playwright／Chrome 成功渲染。`block-beta` 在該引擎可用；所有圖源保留 `look: neo` 首項。分層架構已檢視淡色節點、虛線底層與子圖透明背景，輸出 XML 也確認五個子圖框為 `fill:none;stroke:none`；未逐張進行完整視覺驗收。
- **配置：** Windows 隔離目標的 shared／copy 實際配置皆保留新規則及 tools 指引；copy 的八份樣板與說明逐 bytes 相符。核心配置邏輯未變，WSL 的配置／更新／回復仍由完整單元測試涵蓋；未改動其他真實專案。

本機沒有 `mmdc`，未安裝任何工具；上述是既有引擎的語法與局部外觀驗證，不能稱為 mermaid-cli 或所有版本的相容性驗收。兩端原生 renderer adapter 的執行／失敗／逾時仍由 fixture 測試驗證。原始結果放在本機忽略的 `.agf/qa/diagram-render/` 及 `diagram-*-tests.log`。本輪移除已過時的公開 SVG，保留可重生的 `.mmd`／`.drawio` 與渲染步驟，避免新圖源搭配舊圖片；不把 API 測試產物冒充 CLI 交付。沒有量測整項 AI 任務的 token 或帳單節省。

本次安全稽核另重現並修正檔案權限、Git 狀態判讀、來源資源耗盡與受管理檔案並行修改等問題；詳細條件與尚未解決的 Git clean filter、非原子檔案競態等限制見[安全稽核紀錄](security-review.md)。本輪工作目錄與可到達歷史的有限秘密格式掃描未命中；這不能保證沒有其他秘密或私人資料。

2026-11-08 安全稽核版本的完整測試：WSL Python 3.14.4 共 164 項全部通過，使用既有隔離 Node 24.22.1；Windows Python 3.13.15 共 164 項，151 通過、13 跳過。跳過包括 POSIX 權限／byte 檔名／descriptor 與替換開啟中檔案的測試，以及本機無權建立 symlink（WinError 1314）。Windows 從 WSL UNC 路徑執行；它的 ACL、原生 NTFS 及所有環境不能由這些測試推論。安全稽核的原始測試輸出與合成重現保存在本機忽略的 `.agf/qa/security-audit/`，沒有作為公開內容提交。

## 公開前檢查與 micro-os 教學

本次以目前原始碼重新執行完整 unittest：WSL Python 3.14.4 共 137 案，135 通過，兩項 OpenCode 插件案例因 Node 未在 PATH 而 skip；再用既有隔離 Node 24.22.1 重跑 integration 16 案，包含這兩項，全部通過。Windows 原生 Python 3.13.15 共 137 案，135 通過；POSIX 權限測試不適用，另一項 symlink 測試因 WinError 1314 skip。Windows 是在 WSL UNC 共享資料夾執行 Python，這不是原生 NTFS 全面驗證。五個 skills 通過官方 skill-creator 格式 validator；結構檢查和單元測試不能證明沒有其他錯誤。

micro-os 教學使用公開來源的特定 commit 核對 README 與 AGENTS，沒有改動真實 micro-os。Windows／WSL 各自以空目標及含既有規則、技能、腳本和模擬 MCP 設定的隔離目標，實際執行配置預覽、套用、status、update 與 rollback；保留的既有檔案逐 bytes 相同。測試結果在本機 `.agf/qa/micro-os-guide/`。沒有驗證 AI 宿主實際載入、micro-os 建置、真正 MCP 連線或模型訓練。

實測發現 `files diff` 即使找到差異，成功比較仍回傳 0；已修正 CLI 說明，應檢視 JSON 中的差異，而不是只靠退出碼。

發布前掃描當時全部 5 個可到達 commit 的 177 個相異 blobs，以及目前追蹤與非忽略的新檔，檢查私鑰標頭、數種常見服務 token 與部分本機家目錄路徑模式；沒有命中。這是有限規則檢查，不涵蓋所有憑證格式、個資、歷史來源或被忽略的私人檔案，也未驗證憑證是否有效。歷史 commit 使用 GitHub noreply 信箱，但作者名稱仍會公開。`.agf/` 由本專案忽略，忽略不會清除已追蹤或歷史檔案。

本專案另補上 `.env`、`.env.*` 和常見金鑰副檔名的忽略規則，保留 `.env.example` 可供審查；它們不能阻止強制加入、清除歷史或代替檢查內容。核對範例 micro-os 的公開 `.gitignore` 發現未排除 `.agf/`，教學因此在配置前加入目標專案的檢查與處理步驟，未修改真實 micro-os。

實際 workflow 與 GitHub Actions 範本的 checkout、setup-python 原本使用可移動的 `v7` 標籤；2026-11-08 透過官方 GitHub 倉庫 ref 核對後改為對應完整 commit SHA，減少標籤移動造成的變更。兩份 YAML 已解析並核對設定一致；固定版本不代表已驗證全部上游程式安全，遠端 CI 尚未執行。來源：[GitHub Actions 安全指引](https://docs.github.com/en/actions/reference/security/secure-use)。

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

以下是 v0.1 的實際渲染／選用依賴證據；v0.2 初輪未重新執行 Mermaid、draw.io 或 pypdf 驗收。2026-11-09 的 Mermaid 與腳本變更及重驗另見上方新紀錄。

| 能力 | 既有證據 | 範圍 |
|---|---|---|
| Mermaid | 官方 12.3.0 bundle，透過既有 Playwright／Chrome 執行實際 render；flowchart、sequence、state 皆成功 | Flowchart 的中文字與分支標籤已檢視；包含特殊字元的三類圖做語法 probe。這不是所有版本的 mmdc 相容性保證 |
| draw.io | 產生未壓縮 XML，檢查 cell／parent／edge 引用 | 桌面 app 未安裝，未做原生 draw.io 匯出或視覺驗收 |
| PDF | pypdf 7.0.0 置於專案內隔離測試目錄；Windows／WSL 實際抽取自製單頁 PDF，確認文字與 page:1 錨點 | 核心環境缺少 pypdf 時仍正確回報 UNAVAILABLE；表格、公式、OCR 與大型真實 spec 未驗證 |
| 靜態網頁 | 10 個 localhost HTTPServer 案例，兩端通過 | 預覽、byte 上限、robots、redirect、覆寫與回傳 metadata；外部 example.com HTTPS 試抓遇到環境憑證鏈驗證失敗，工具回報錯誤且沒有發布頁面。外部成功擷取、登入及動態 JS 未驗證 |

當時實際 Mermaid 渲染找出了 sequence 標籤中 HTML entity 與分號的相容性問題；已改用官方語法的 Mermaid entity codes，再以同一引擎重驗。當時提交的 SVG 已於 2026-11-09 換成只保留圖源與工具重生方式；QA 依賴與臨時輸出放 `.agf/qa/`，未加入核心依賴或公開來源檔。

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

上述都是少量 behavior smoke。佇列原始檔已包含故障提示及正確對照，不能當成盲測 RCA benchmark。真人理解、長期保留、一般化觸發率、成本及 token 改善比例皆未量測。[行為驗收](../evals/README.md)該輪收錄 34 個可重跑案例，不代表 34 項皆已執行或通過；後續新增數量見上方紀錄。特殊授權只驗證指引與案例表述，未連接券商、燒錄／抹除板子或寫入 SVN repository。

# R2 繁體中文文件校閱報告

校閱範圍：README.zh-TW.md、docs/ 下的 SETUP、GLOSSARY、FAQ、DEVELOPMENT、ENGINEERING_RULES、LEARNING_GUIDE、HANDS_ON、README，以及 docs/lessons/README.md、教學 20 與 21（README.md 和 answers.md）。
沒有修改任何既有檔案；只寫了這份報告。這台機器的 PATH 上沒有 `cargo`，所以沒有跑任何 cargo 測試，精確度都是用 grep、讀原始碼、讀 `acceptance/final.json`、讀 `artifacts/runs/hands-on-20261117/` 的實際紀錄核對的。

## 總評

整體寫得好，AI 味很輕。「流暢性陷阱」「歐化長句」「死物配活物」這三項掃過全部檔案，只找到零星幾處（見第一部分）。
需要作者處理的集中在：
1. 一個和程式相反的行為描述（`kv_admin.py add 2` 的警告與結果的先後）。
2. 三處文件之間或和 Git 狀態不一致的宣稱（git tag、「14 個檢查」、追趕「最多 10 輪」）。
3. 幾個新手照 SETUP 做會卡住的地方（sequence 接續、shell 變數 `A` 和值 `A` 撞名、沒有 clone 網址）。
4. 少數大陸用語與同一概念多個名稱。

## 寫得好、建議保留的寫法

- docs/lessons/20 README 第 4 節：先貼出舊的 `read`，再用「呼叫的地方／什麼時候發生／一台的叢集閒著時」一張表說明為什麼三個呼叫點都等不到，最後才畫圖。先看到現象、再看到原因，每句都有可核對的函式名。
- docs/HANDS_ON.md「這些數字是怎麼來的」：用 index 1～4 的表把 term 2、commit index 4、PUT 是 index 5、換 leader 後是 6 全部推導出來，而且和實際紀錄逐行吻合（見第二部分）。這是讓新手信任文件的寫法。
- README.zh-TW.md 的「沒有驗證的事」：九條都是具體的限制（24 個操作、64 個用戶端操作、SIGKILL 不等於斷電），沒有「仍有改進空間」之類的空話。
- docs/DEVELOPMENT.md 第 99 行「做過一次的檢查不會自己保持正確」：是一句格言，但後面立刻接三個具體例子，不是空洞的總結句。
- 術語第一次出現時多半當場解釋（README 的「種子」「不變量」「failpoint」「receipt」都在同一格內解釋）。

---

# 第一部分：AI 味與可讀性

## 七項標準的檢查結果摘要

| 標準 | 結果 |
|---|---|
| 1. 流暢性陷阱 | 只找到 2 處輕微的（見 F-01、F-02）。其餘「總結句」都帶著具體內容。 |
| 2. 歐化中文、倒裝長句 | 全部檔案搜尋「進行／對於／將會／作為一個／值得注意／總之」等標記，命中 0 處有問題的用法。有一處「有趣的是」（F-03）。長句問題主要是資訊密度，歸在標準 4。 |
| 3. 主題鏈與人稱跳躍 | 有 2 處：教學 20、21 本文是「這篇帶你」，第 10 節忽然變成「我」（F-04）；「作者」與「我」的轉換沒有交代。其餘段落主題鏈清楚。 |
| 4. 資訊密度、名詞化 | 找到 6 處過密的長句（F-05～F-10）。名詞化不明顯。 |
| 5. 死物配活物 | 找不到不自然的例子。「core 不會自己醒來」（教學 20 第 33 行）、「文件帶你」都是教學上有幫助的擬人，建議保留。 |
| 6. 沒見過的搭配 | 找到 4 組（F-11～F-14）：「測試守著」、「碼表」、「轉接存取」、「補上……的檢查」的歧義。 |
| 7. 主詞和動詞離太遠 | 找到 2 處（F-06、F-08）。 |
| 中英夾雜 | 識別字與命令都正確保留英文。一般敘述裡不必要的英文只找到 3 處（F-15～F-17）。沒有「durable 證據」「committed prefix」這類。 |
| 簡體字、大陸用語 | 沒有簡體字。有 3 個用語（F-18～F-20）：連接埠寫成「埠」、「優化」、「碼表」。 |
| 同一概念多個名稱 | 5 組（F-21～F-25）。 |
| AI 痕跡 | 沒有「作為一個……」；沒有每段同一句型開頭；README.zh-TW.md 的「關於 AI 工具」一節是誠實的揭露，不是 AI 腔，建議保留。唯一接近的是 F-03「有趣的是」。 |

## 發現列表

格式：檔案:行號 ｜ 原句 ｜ 類別 ｜ 為什麼是問題 ｜ 建議改寫 ｜ 嚴重度

| 編號 | 檔案:行號 | 原句（逐字） | 類別 | 為什麼是問題 | 建議改寫 | 嚴重度 |
|---|---|---|---|---|---|---|
| F-01 | docs/DEVELOPMENT.md:65 | 專案比預期久，作者決定只做做得出來的事和重點功能。 | 1 流暢性、6 搭配 | 「做做得出來的事」重複且含糊；「專案比預期久」缺動詞。讀者看不出到底砍了什麼（下一行才列）。 | 專案花的時間比預期長，作者決定縮小範圍，只做能在期限內完成的部分。原本計畫的三項驗證因此沒有做，README 照實列在「沒有驗證的事」： | 建議 |
| F-02 | docs/lessons/21-a-fresh-clone-fails-its-first-test-run/README.md:104 | 對一個拿來展示的專案，這是最先被看到的印象。 | 1 流暢性 | 前一句已說「會懷疑程式本身有問題」，這句沒有新資訊。 | 刪掉這一句。 | 可不改 |
| F-03 | docs/lessons/20-a-leader-alone-never-answers-reads/README.md:102 | 有趣的是，`finish_reads` 本身早就算對了。它算「除了 leader 自己，還需要幾個 follower 確認」： | 2 歐化／AI 習慣語 | 「有趣的是」是翻譯腔的轉折語，全文只出現這一次，和其他段落直述的風格不一致。 | `finish_reads` 本身其實早就算對了。它算的是「除了 leader 自己，還需要幾個 follower 確認」： | 建議 |
| F-04 | docs/lessons/20-.../README.md:182；docs/lessons/21-.../README.md:171 | 我問自己：沒有 follower 的時候誰會叫它？寫了一個一台的單元測試，馬上失敗。／現象：三個測試失敗，`File exists`；在我自己的目錄怎麼跑都過。 | 3 人稱跳躍 | 同一篇前面都是「這篇帶你」「作者」，第 10 節突然變成第一人稱「我」。這是面試稿，用「我」合理，但讀者不知道「我」是誰（作者？讀這篇的你？）。 | 在第 10 節標題下加一句：「下面是以作者的口吻寫的面試講稿，你可以改成自己的經驗。」然後保留「我」。 | 建議 |
| F-05 | docs/FAQ.md:9-10 | 任兩個多數一定至少有一台重疊。一筆 entry 只要在多數落盤，之後任何選得上的 leader 都必須拿到多數的票，其中至少一台有這筆 entry，而投票規則不讓 log 比較舊的節點當選，所以這筆 entry 不會丟。 | 4 資訊密度 | 第二句塞了五個概念（落盤、選得上、多數的票、重疊、投票規則），主詞在「leader」「其中至少一台」「投票規則」之間換了三次。 | 任兩個多數至少有一台重疊。一筆 entry 只要在多數節點落盤，之後要當選的 leader 就必須拿到多數的票，這些票裡至少有一票來自存有這筆 entry 的節點。而投票規則不讓 log 比較舊的節點當選，所以這筆 entry 不會丟。 | 建議 |
| F-06 | docs/FAQ.md:52-53 | 如果長度欄位壞了而沒有檢查，程式可能把後面的好資料當成「沒寫完的尾巴」刪掉，其中可能包含節點投過的票。 | 4 資訊密度、7 主詞遠 | 「其中」指代不明（指「好資料」還是「尾巴」）；兩個「可能」疊在一起。 | 如果長度欄位壞了又沒有檢查，程式可能把後面完好的資料誤當成「沒寫完的尾巴」而刪掉，被刪掉的資料裡可能有節點投過的票。 | 建議 |
| F-07 | docs/ENGINEERING_RULES.md:26 | ReadIndex：leader 在本任期 commit 過、並以讀取到達之後開始的一輪多數確認自己的身分，才在套用位置 ≥ readIndex 時回答；讀取從不寫 log | 4 資訊密度、7 主詞遠 | 一個格子裡有三個條件，其中「讀取到達之後開始的一輪」是整個 ReadIndex 最難懂的點，卻被壓成修飾語；主詞 leader 離動詞「回答」隔了 40 多字。 | ReadIndex：leader 要同時滿足三個條件才回答讀取。(1) 本任期已經 commit 過一筆 entry；(2) 讀取到達之後，又有一輪多數節點確認它仍是 leader；(3) 狀態機已套用到 readIndex 以上。讀取從不寫 log。 | 建議 |
| F-08 | docs/README.md:3 | 文件分成五類：**現行說明**照現在的程式寫；**規格與補記**是每個階段的規格與實作後的結果；**紀錄**寫的是當時發生的事，保留原文、不隨程式更新，裡面的路徑是作者機器上的路徑；**歷史**是已被取代的版本，開頭都有標示，指向現在以哪份為準；**原始材料**是專案開始時拿到的規格，不修改。 | 4 資訊密度 | 一段 170 多字塞五類定義，讀者要自己拆。 | 改成五個條列，每類一行：<br>- **現行說明**：照現在的程式寫。<br>- **規格與補記**：每個階段的規格，以及實作後的結果。<br>- **紀錄**：寫的是當時發生的事，保留原文、不隨程式更新；裡面的路徑是作者機器上的路徑。<br>- **歷史**：已被取代的版本，開頭標示現在以哪份為準。<br>- **原始材料**：專案開始時拿到的規格，不修改。 | 建議 |
| F-09 | docs/LEARNING_GUIDE.md:81 | 這個專案的叢集可以是 1～7 台。論文 Figure 8 的劇本要五台才畫得出來；單元測試 `previous_term_entry_requires_current_term_commit` 不重演整個劇本，而是直接設定 leader 記錄的各 follower 進度，檢查「舊 term 的 entry 已在多數上」時 commit index 仍不前進，等本任期的 entry 也到多數才前進。 | 4 資訊密度 | 最後一句 90 字，一句裡有「不……而是……檢查……時……仍不前進，等……才前進」。 | 論文 Figure 8 的劇本要五台才畫得出來，而這個專案的叢集是 1～7 台。單元測試 `previous_term_entry_requires_current_term_commit` 不重演整個劇本，它直接設定 leader 記錄的各 follower 進度，然後檢查兩件事：舊 term 的 entry 已經在多數上時，commit index 不前進；本任期的 entry 也到了多數，commit index 才前進。 | 建議 |
| F-10 | README.zh-TW.md:121 | 換掉故障的節點時，先加入新的，再移除舊的。不要把清空資料目錄的節點編號重新加入，也不要讓第二台節點引導：這一版偵測不到這兩種操作錯誤，而它們都可能破壞安全性。 | 4 資訊密度、術語未解釋 | 「引導」在這個位置第一次單獨出現，沒有連結；「破壞安全性」沒說是什麼（兩個 leader？資料遺失？）。FAQ Q20 有解釋，但這裡沒連過去。 | 換掉故障的節點時，先加入新的，再移除舊的。下面兩件事不要做，這一版偵測不到，做了可能破壞安全性（例如同一個 term 出現兩個 leader，原因見 [FAQ Q20](docs/FAQ.md)）：把清空過資料目錄的節點用原來的編號重新加入；讓第二台節點也用 `--bootstrap` 引導。 | 建議 |
| F-11 | README.zh-TW.md:28；docs/DEVELOPMENT.md:90 及教學標題（lessons/README.md:47）等 | 補上 14 個沒有測試守著的檢查／14 個檢查可以整段刪掉而沒有測試失敗／放寬了上限，卻沒有測試守著它 | 6 搭配 | 「測試守著」是 guard 的直譯。台灣中文較常說「有測試把關」「有測試保護」。「補上 14 個沒有測試守著的檢查」更有歧義：「檢查」是程式裡的驗證碼，還是測試？ | 補上 14 段原本沒有測試保護的檢查程式（驗證碼）；教學 18 標題：「放寬了上限，卻沒有測試把關」 | 建議 |
| F-12 | docs/lessons/README.md:94、109 | 確認碼表裡包含了什麼／確認碼表裡有什麼 | 6 搭配、大陸用語 | 「碼表」是大陸說法，台灣稱「碼錶」或「碼錶」「計時器」。教學 14 本身的意思是「量測工具量到的時間包含哪些步驟」。 | 確認計時器量到的時間包含了哪些步驟。 | 建議 |
| F-13 | docs/SETUP.md:12-13 | 那是透過轉接存取的 Windows 磁碟，`fsync` 很慢 | 6 搭配 | 「轉接存取」不是常見說法；新手也不知道「轉接」是什麼。 | 那是 WSL 經由網路檔案協定（9P）存取的 Windows 磁碟，`fsync` 很慢 | 建議 |
| F-14 | docs/lessons/README.md:67 | 別的測試 fork 出的子程序，暫時帶走了這個測試的檔案鎖 | 6 搭配 | 全站其他地方用 process；這裡用「子程序」。台灣常用「子行程」或「子 process」，且「帶走」檔案鎖也不自然（鎖是被「繼承」）。 | 別的測試 fork 出的子 process 繼承了這個測試的檔案鎖，鎖因此暫時沒有釋放 | 可不改 |
| F-15 | docs/FAQ.md:34 | 所以 core 每一步只產生一個 barrier，排在所有訊息之前。 | 中英夾雜、術語未解釋 | barrier 在 FAQ 裡第一次出現，沒有說明；名詞表有，但這裡沒指過去。 | 所以 core 每一步只產生一個 barrier（一道「這些變動落盤之後，才能做後面的事」的關卡，見名詞表），排在所有訊息之前。 | 建議 |
| F-16 | docs/LEARNING_GUIDE.md:65 | WAL 物件也會進入 poison 狀態，不再接受任何寫入 | 中英夾雜 | 一般敘述裡的英文，名詞表有解釋但這裡沒連。 | WAL 物件也會進入 poison 狀態（之後拒絕任何寫入，見名詞表） | 可不改 |
| F-17 | docs/LEARNING_GUIDE.md:47（步驟 8 的表格）；docs/HANDS_ON.md:76 | 自己加節點 3 是多數，而且 index 5 是本任期的 entry／節點 1 自己加上節點 3 已經是多數 | 中英夾雜、4、主詞省略 | 「match 更新成 5」「自己加節點 3 是多數」省略了「三台中的兩台」，新手要自己算 2/3。 | 節點 1 自己加上節點 3，就是三台中的兩台，已經是多數 | 建議 |
| F-18 | docs/SETUP.md:78、79、146 等 | 三台節點各用兩個埠，7101～7103 給節點之間，7201～7203 給用戶端。 | 大陸用語 | 「埠」是大陸用語，台灣稱「連接埠」（口語也說 port）。全文多處。 | 三台節點各用兩個連接埠，7101～7103 給節點之間，7201～7203 給用戶端。（其他處的「埠」同樣改為「連接埠」。） | 建議 |
| F-19 | docs/DEVELOPMENT.md:49 | 效能最後做，才有穩定的基準可以比較；而且效能優化不能改變「先落盤、後回覆」的次序。 | 大陸用語 | 台灣說「最佳化」。 | 而且效能最佳化不能改變「先落盤、後回覆」的次序。 | 建議 |
| F-20 | README.zh-TW.md:152 | 架構圖只檢查過 Mermaid 圖源；作者的機器上沒有能用的渲染器。 | 大陸用語（輕微） | 台灣多半說「算繪」或「轉譯」，但「渲染」在台灣技術文章也常見。 | 作者的機器上沒有能用的算繪工具。 | 可不改 |
| F-21 | docs/SETUP.md:114-115 | `--client-id` 是你這個用戶端的編號，`--sequence` 是請求的序號，每個新請求加一。／收到 `TIMEOUT_UNKNOWN` 時，用**同一個** client ID、sequence 與內容重送 | 同一概念多名稱 | 相鄰兩行，「用戶端」和「client」並用；README.zh-TW.md 全用 client，SETUP 與 DEVELOPMENT 用「用戶端」。 | 統一成「client」：`--client-id` 是這個 client 的編號 … | 建議 |
| F-22 | docs/ENGINEERING_RULES.md:11、docs/LEARNING_GUIDE.md:73 與其他 | 先持久化，再做依賴它的事。／Figure 2：term、投票、log 要持久化 | 同一概念多名稱 | 其餘文件（名詞表、README）一律用「落盤」，名詞表沒有收「持久化」。 | 先落盤，再做依賴它的事。／Figure 2：term、投票、log 要落盤 | 建議 |
| F-23 | docs/lessons/20-.../README.md:8；docs/DEVELOPMENT.md:81 等 | 最終複查時讀 `raft-core` 的讀取路徑／最後一次複查 | 同一概念多名稱 | 「最終複查」「最後一次複查」「S10」三種叫法同指一件事。 | 統一用「最後一次複查（S10）」 | 可不改 |
| F-24 | docs/README.md（HANDS_ON 標題）、docs/GLOSSARY.md:33 vs 標題「寫到磁碟與回復」、docs/LEARNING_GUIDE.md:87 | 實際操作：寫入、終止 leader、再恢復／當機後照這個檔案恢復／Wal::open 讀回…… | 同一概念多名稱 | 「回復」「恢復」「還原」混用（recovery 與 restore 並未區分）。 | 統一：recovery 一律「回復」，`restore` 函式才說「還原」。HANDS_ON 標題改為「寫入、終止 leader、再回復」。 | 可不改 |
| F-25 | README.zh-TW.md:9（「一個 Raft group」）、其他處「叢集」 | 一個 Raft group，最多七台，成員一次增減一台。 | 同一概念多名稱 | 全文只有這一處用 group，其他都是「叢集」，名詞表沒有 group。 | 一個 Raft 叢集，最多七台，成員一次增減一台。 | 可不改 |
| F-26 | docs/GLOSSARY.md:3 | 這份清單收錄文件裡出現的專有名詞與縮寫。每一條寫三件事：它是什麼、用一個例子說明、在這個專案的哪裡。 | 與實際內容不符（自我描述） | 表格只有「名詞／白話／在這個專案」三欄，沒有「例子」欄，也有不少條目沒有例子（共識、節點、狀態機等）。 | 這份清單收錄文件裡出現的專有名詞與縮寫。每一條寫兩件事：白話的意思（能舉例的就附一個例子），以及它在這個專案的哪裡。 | 必改 |
| F-27 | docs/GLOSSARY.md:17 | follower 太久沒收到 leader 的消息，就把 term 加一、變成 candidate | 同一概念多名稱 | 同一份名詞表其他處都是「訊息」，只有這裡用「消息」。 | follower 太久沒收到 leader 的訊息（心跳），就把 term 加一 | 可不改 |
| F-28 | docs/DEVELOPMENT.md:18 | 驗收由 `scripts/verify_gate.py` 依 `acceptance/final.json` 執行。每個開發階段在契約裡加一個驗收階段； | 精確（見第二部分 C-24） | S0、S9、S1～S4 的審查都沒有加階段（final.json 的階段是 P00～P08、P10～P16）。README 與名詞表的說法是「S1～S6 與 S10」。 | 每個加了功能或修補的開發階段（S1～S6 與 S10），在契約裡各加一個驗收階段； | 建議 |
| F-29 | docs/DEVELOPMENT.md:79 與 :90 | 沒有安全性缺陷。log index 接近 u64 上限時會溢位；8 個測試缺口；5 處文件和程式不符／14 個檢查可以整段刪掉而沒有測試失敗 | 前後數字不一致 | 同一次儲存層審查，這裡說「8 個測試缺口」，下面一格說「14 個檢查」。讀者會問：8 還是 14？是兩件事還是同一件事？ | 在其中一處說明兩個數字的關係，例如：「審查者在 30 個地方植入錯誤，14 個沒有測試失敗（其中 8 個屬於測試缺口，其餘 6 個……）」；若兩者無關，改用不同的詞，避免都叫「缺口」。 | 建議 |

---

# 第二部分：精確度抽查

結果欄：正確／錯誤／無法確認。共 40 項，**錯誤 3 項**（C-24、C-33、C-35 含部分錯誤），無法確認 5 項。

| 編號 | 宣稱 | 檔案:行號 | 核對的程式位置 | 結果 |
|---|---|---|---|---|
| C-01 | 心跳每 100 毫秒 | GLOSSARY:18 | crates/raft-node/src/main.rs:584 `Duration::from_millis(100)` | 正確 |
| C-02 | 選舉逾時 400～800 毫秒（隨機） | GLOSSARY:17、FAQ Q4 | main.rs:364 `400 + self.random % 401`（含 800） | 正確 |
| C-03 | client 等待上限 3 秒 | GLOSSARY:58、教學 20:60 | main.rs:25 `CLIENT_TIMEOUT = from_secs(3)` | 正確 |
| C-04 | frame 上限 1 MiB；4 bytes 長度（big-endian）加 JSON | GLOSSARY:81 | raft-protocol/src/lib.rs:6 `MAX_FRAME = 1024*1024`；raft-transport/src/lib.rs:50、70 `from_be_bytes`／`to_be_bytes` | 正確 |
| C-05 | 批次每批最多 256 筆、512 KiB | GLOSSARY:80 | raft-protocol/src/lib.rs:13-14 | 正確 |
| C-06 | 快照上限 64 MiB；分塊每塊最多 256 KiB | GLOSSARY:43、45 | raft-protocol/src/lib.rs:16、19 | 正確 |
| C-07 | 壓縮在 WAL 超過 1 MiB 且是上一份快照 4 倍以上時觸發 | GLOSSARY:44 | main.rs:33-34、724 `max(1 MiB, 4 * previous)` | 正確 |
| C-08 | WAL record header 24 bytes；單筆上限 2 MiB | GLOSSARY:36 | raft-storage/src/lib.rs:23-24；STORAGE_FORMAT_V2.md:100-101 | 正確 |
| C-09 | `MAX_LOG_INDEX` = 2^62 | GLOSSARY:20 | raft-protocol/src/lib.rs:23 `1 << 62` | 正確 |
| C-10 | 節點編號 1～7 | README:25 等 | raft-protocol/src/lib.rs:5 `MAX_NODE = 7` | 正確 |
| C-11 | mutation 測試 76 個案例 | README:133、GLOSSARY:95 | scripts/mutation_check.py `CASES` 共 76 筆 | 正確 |
| C-12 | 驗收 16 個階段；P00～P08 加 P10～P16，P09 沒用；S1～S6 是 P10～P15，S10 是 P16 | README:135、GLOSSARY:115 | acceptance/final.json `phases`：00～08、10～16，共 16；10=S1…15=S6，16=S10 | 正確 |
| C-13 | 模擬 1,000 個種子、每個 10,000 個事件 | README:130 | raft-sim/src/main.rs:6-7；tests/invariants.rs:8、12；scripts/simulation_report.py:17 | 正確 |
| C-14 | 線性一致性檢查一次最多 24 個操作 | README:145、FAQ Q24 | tools/linearizability.py:66 `if n>24` 回傳 INCONCLUSIVE | 正確 |
| C-15 | 模擬器每個種子只有 64 個用戶端操作 | README:146 | raft-sim/src/cluster.rs:990 註解「the 64 ordinary operations」 | 正確（只有註解佐證，沒有常數） |
| C-16 | 追趕：10 輪、最後一輪少於 4 次心跳、超過 100 次心跳放棄 | GLOSSARY:71 | raft-core/src/lib.rs:25、28、30、1063-1066、1093 | 正確（常數）。但「最多 10 輪」見 C-17 |
| C-17 | 「最多 10 輪」 | GLOSSARY:71、FAQ Q18 (:89) | docs/MEMBERSHIP.md:91「固定跑 10 輪」；core:1063 `if *round == CATCH_UP_ROUNDS` 才判定，不到 10 輪不會結束 | **錯誤（用詞）**：不是「最多」，是「固定 10 輪」。追趕不會在第 3 輪就提前完成 |
| C-18 | 引用的測試名稱存在：`previous_term_entry_requires_current_term_commit`、`retry_same_request_has_single_effect`、`read_waits_for_a_committed_entry_of_its_term`、`vote_after_restart_not_duplicated`、`append_ack_after_durable_sync`、`uncommitted_suffix_not_applied_after_recovery`、`truncated_wal_tail_safe`、`a_single_voter_leader_answers_a_read_without_waiting`、`replies_to_requests_sent_before_the_read_do_not_confirm_it`、`opens_racing_to_create_the_same_parent_all_succeed` | FAQ、LEARNING_GUIDE、教學 20、21 | `grep -rn "fn <name>" crates`：各 1 筆 | 正確 |
| C-19 | Python 測試名稱存在：`test_a_crash_right_after_a_batch_of_writes_executes_each_once`、`test_a_leader_left_with_a_minority_does_not_answer_reads`、`test_a_single_node_cluster_answers_reads_at_once` | FAQ Q9、Q13、教學 20:148 | tests/integration/test_performance.py:52；test_read_index.py:46、76 | 正確 |
| C-20 | 引用的函式存在：`Voters::is_quorum`／`majority`、`Core::step_down`、`Core::seal`、`advance_commit`、`apply_committed`、`persisted`、`storage_failed`、`Actor::maybe_compact`、`reply_request`、`Wal::save_delta`、`Wal::poisoned`、`StateMachine::applied_index`、`read_payload`、`canonical`、`discover_rust` | FAQ、GLOSSARY、LEARNING_GUIDE | 各檔 grep（raft-protocol:92、97；raft-core:400、403、523、727、899、1109；main.rs:409、714；storage:857、906；kv-state:37；transport:47；protocol:166；scripts/verify_gate.py:68） | 正確 |
| C-21 | `advance_commit` 只 commit 本任期 entry：`term_at(n) == Some(self.state.term)` | LEARNING_GUIDE:75 | raft-core/src/lib.rs:909 | 正確 |
| C-22 | follower 的 commit 推進到 `leader_commit.min(matched)` | LEARNING_GUIDE 練習 B（:118） | raft-core/src/lib.rs:1257 | 正確 |
| C-23 | 步驟 6「送出兩則 AppendEntries，每則一條執行緒」 | LEARNING_GUIDE:45 | main.rs:539 每個 envelope `thread::spawn` | 正確 |
| C-24 | `add 2` 會**先**印一行警告，**接著**回 `"status": "OK", "result": "1,2"` | README:114、SETUP:101、FAQ Q2 (:14) | tools/kv_admin.py:88-93：先 `print(json.dumps(answer))`，之後才 `print(warning, file=sys.stderr)`，而且只有 OK 才印警告 | **錯誤**：順序相反。實際是先看到 JSON，再看到 stderr 的警告 |
| C-25 | HANDS_ON 的 index 推導（1 成員設定、2 NoOp、3 `[1,2]`、4 `[1,2,3]`、PUT 是 5、換 leader 後 NoOp 是 6、GET 回 6） | HANDS_ON:44-57 | artifacts/runs/hands-on-20261117/result.json（PASS；pids 469613／469614／469615；`put_trace` 行 37／38／42、committed_index 5；`leader_killed` returncode -9；`new_leader` node 2；重啟新 pid 469794）；`cluster/node-1.jsonl` 第 36-43 行 | 正確（全部吻合，包括 `fsync_us` 1759.352 和 rpc_id 11／12） |
| C-26 | 「第 38 行：last_log_index 5、durable_index 4；第 42 行 apply index 5」 | HANDS_ON:66-70 | node-1.jsonl 第 38 行 `last_log_index:5, durable_index:4`；第 42 行 `kind:apply, index:5, commit_index:5` | 正確 |
| C-27 | `--bootstrap` 只對空資料目錄有作用，之後帶著也沒關係 | README:96、SETUP:119 | main.rs:991 usage「on an empty data directory only」 | 正確 |
| C-28 | `kv_admin.py status` 印出 leader、term、成員、成員設定位置與是否 commit | README:120 | kv_admin.py:81-84：leader、term、voters、config_index、config_committed、catching_up | 正確 |
| C-29 | `node directory already owned` 錯誤訊息 | SETUP:147 | raft-storage/src/lib.rs:585 | 正確 |
| C-30 | 驗收收據放在 `artifacts/acceptance-final/` | GLOSSARY:98 | scripts/verify_gate.py:18 `RECEIPTS` | 正確（另外 `final_acceptance.sh` 的輸出在 `artifacts/final-acceptance/`，兩者是不同目錄，文件沒有混淆） |
| C-31 | `learning_demo`「最後的目錄必須還不存在」；結束印「結果：.../result.json」 | HANDS_ON:14、22 | tools/learning_demo.py:22 `mkdir(exist_ok=False)`、:121 | 正確 |
| C-32 | 教學 20：`finish_reads` 有三個呼叫處；`needed = majority.saturating_sub(contains(self))`；修正是在 `read` 結尾補呼叫 | 教學 20:78-86、102-105、122-129 | raft-core:426（persisted）、1392（InstallSnapshotResponse）、1428、1441（AppendResponse）、602（修正）；632-645 | 正確（AppendResponse 分支內有兩處呼叫，文件算成一個分支，說得通） |
| C-33 | 教學 20 第 75 行：`start_read_round` 把 readIndex 設成 commit index，輪次加一，然後叫 `replicate_all` | 教學 20:75 | core:605-630：還有一個提前 return（本任期尚未 commit 時不做任何事、所有讀取已有 readIndex 時也不做） | 正確但省略；第 6 節末段有補充。建議在第 75 行加「（本任期還沒 commit 時什麼都不做）」 |
| C-34 | 教學 21：`create_directory` 修正前後的程式 | 教學 21:68-76、115-122 | raft-storage/src/lib.rs:128-147（現行版本與文件的修正版逐字吻合） | 正確 |
| C-35 | 教學 21：`raft-node` 有 6 個測試，其中 3 個用 `target/node-pool-tests` | 教學 21:26-27、141 | main.rs 有 6 個 `#[test]`；`node-pool-tests` 出現 3 次（1110、1232、1449） | 正確 |
| C-36 | 教學 21：8 條執行緒 × 20 輪 = 160 次開檔 | 教學 21:41、50 | expected-output.txt「140 of 160」 | 正確 |
| C-37 | mutation 案例 `s10_single_voter_read_waits`、`s10_directory_race_is_an_error` 存在 | 教學 20:149、21:139 | scripts/mutation_check.py:310、352 | 正確 |
| C-38 | 「補上 14 個沒有測試守著的檢查」 | README:28、FAQ Q22 (:107)、DEVELOPMENT:90 | mutation_check.py 共 13 個 `s10_` 案例，其中 2 個屬於教學 20、21 的缺陷，剩 11 個對應儲存層審查；DEVELOPMENT:90 的說法是「值得守的都補了測試」 | **無法確認**，傾向誇大：README 與 FAQ 的說法暗示 14 個全補，與 DEVELOPMENT 的「值得守的都補了」不一致，案例數也只有 11 |
| C-39 | 「`git tag` 列出的就是驗收過的版本」；S10 的 tag `s10-final-review-verified` | DEVELOPMENT:4、:35；README:140 | `git tag` 目前列出 `s7-zh-style-prototype`、`s8-framework-analysis`、`s8-framework-changes`（不是驗收過的版本），且 `s10-final-review-verified` 尚未建立（README:140 的「只在每個階段都……通過後才建立」措詞正確，但 DEVELOPMENT 表格把它列為已有） | **錯誤**（DEVELOPMENT:4 的「列出的就是驗收過的版本」不成立）；S10 tag 目前不存在，無法確認 |
| C-40 | GLOSSARY:26「Raft 用兩種：RequestVote（要票）、AppendEntries（複製 entry）」 | GLOSSARY:26 | raft-protocol/src/lib.rs `Rpc` 另有 `InstallSnapshot`；同一份名詞表 :45 也介紹了 InstallSnapshot | **部分錯誤**：論文的基本版是兩種，這個專案是三種（再加回應型別）。建議改為「RequestVote、AppendEntries，以及這個專案另有的 InstallSnapshot」 |
| C-41 | SETUP:14「磁碟空間約 3 GB（建置結果約 2 GB）」 | SETUP:14 | 這台機器的 `target/` 是 5.6 GB（含 mutation、clippy、測試產物等） | 無法確認；若讀者跑完 test + clippy + pytest，3 GB 可能偏低 |
| C-42 | Rust 1.99.1、Python 3.14.4、pytest | SETUP:6、35 | rust-toolchain.toml 為 1.99.1；本機 `python3 --version` 為 3.14.4；requirements-dev.txt 只有 `pytest==9.2.0` | 正確 |
| C-43 | 「FAQ 27 個問題」「21 篇 bug 教學」 | docs/README.md:15-16 | FAQ 為 Q1～Q27；`docs/lessons/` 有 21 個編號資料夾 | 正確 |
| C-44 | 完整驗收「約 45 分鐘」 | README:139、SETUP:124 | scripts/final_acceptance.sh:12 註解「about 45 minutes on one WSL machine」 | 正確（作者自述） |
| C-45 | 模擬器的不變量 I1～I8 | GLOSSARY:91 | cluster.rs 只確認到 I6、I8 的註解與訊息 | 無法確認（只驗到 I6、I8） |
| C-46 | DEVELOPMENT:96「4.3 GB 的 tmpfs」「16 個並行跑 400 次」 | DEVELOPMENT:95-97 | 紀錄類陳述，無法在程式裡核對；文件本身已誠實標示「這個推論無法證實」 | 無法確認（文件自己有標示） |

**精確度小結：錯誤 3 項（C-17 追趕「最多」、C-24 警告順序、C-39 git tag），部分錯誤 1 項（C-40 RPC 種類），無法確認 5 項（C-38、C-41、C-45、C-46，另 C-39 的 S10 tag 現況）。** 其他引用的數字、常數、函式、測試名稱全部和程式一致，數字大致是從程式抄出來的，不是憑印象。

---

# 第三部分：新手會卡住的地方（照 docs/SETUP.md 順序）

| 編號 | 位置 | 卡住的原因 | 建議 | 嚴重度 |
|---|---|---|---|---|
| N-01 | SETUP 開頭（第 3 行）到第 5 節 | 全文沒有一句話說明 Raft、leader、voter 是什麼，第 89 行就說「它幾百毫秒內就會當選 leader」，第 101 行說「兩台時任何一台故障，叢集都會停」。名詞表只在第 8 節（最後）才被提到。 | 在第 3 行後加一句：「這份文件不需要先懂 Raft。看不懂的名詞（leader、term、voter 等）先查 [名詞表](GLOSSARY.md)，或先讀 [README 開頭的三句話](../README.zh-TW.md)。」 | 建議 |
| N-02 | SETUP:39-41 | `git clone <這個儲存庫的網址> raft-kv` 沒有給網址；若讀者是下載壓縮檔，目錄名也不會是 `raft-kv`，下一行 `cd raft-kv` 會失敗。 | 寫成 `git clone <儲存庫網址> raft-kv`，並加註：「如果你是下載壓縮檔，解壓縮後進入該目錄即可，之後所有命令都在這個目錄執行。」 | 建議 |
| N-03 | SETUP:58-59 | 「約 1 分鐘」「幾分鐘」沒有說在第一次建置之後；新手看到 `cargo test` 在重新編譯可能以為卡住。另外沒說 pytest 需要先完成上一步的 `cargo build`（節點執行檔）。 | 加一句：「`pytest` 會啟動 `cargo build` 產生的節點執行檔，所以要先完成第 3 節。」 | 可不改 |
| N-04 | SETUP:81-92 與 :94 | 「都進到專案根目錄」只寫在三個 terminal 的那句，第四個 terminal 沒有再提醒；`.venv/bin/python`、`config/cluster.toml` 都是相對路徑，在別的目錄會失敗，新手只會看到 `No such file`。 | 第 94 行改為：「開第四個 terminal，同樣先進到專案根目錄，把節點 2、3 加進成員設定：」 | 建議 |
| N-05 | SETUP:101-102 | 文件說「`add 2` 會先印一行 `warning`」，實際順序相反（先 JSON，後 warning，見 C-24）。新手若照文件等警告，看到的第一行是 JSON，會懷疑自己做錯。 | 改為：「`add 2` 先回 `{"status": "OK", "result": "1,2"}`，緊接著印一行 `warning`……」 | 必改 |
| N-06 | SETUP:106-110 | 這裡的 shell 變數叫 `A`，而 key 的值也是 `A`（`Put x A`）。讀者很容易以為 `$A` 是那個值。而且變數只存在這個 terminal；換一個 terminal 就不能用。zsh 不會把未加引號的 `$A` 拆成多個參數。 | 把變數改名為 `ADDRS`（或 `NODES`），並加一句「這個變數只在目前的 terminal 有效；在 bash 之外的 shell 要把三個 `--address` 直接寫出來」。 | 建議 |
| N-07 | SETUP:108-109、118-119 | 沒說明重跑會怎樣：同一個 `--client-id 7 --sequence 0` 再執行一次，會得到第一次的結果而不是重新寫入；第 118 行叫讀者「再讀一次 x」，卻沒說這一次的 sequence 要用 2。新手很可能再用 `--sequence 1`，得到舊的結果，卻不知道原因。HANDS_ON:104 才補上這件事。 | 在第 114 行的項目後加：「一個 client ID 用過的 sequence 不能再用於不同的內容；重跑這幾行時，把 `--client-id` 改成別的數字，或把 sequence 接著往後加（下一次是 2）。」並在第 118 行寫明「用 `--sequence 2`」。 | 必改 |
| N-08 | SETUP:114-115 | 「client ID」「sequence」「去重」對沒碰過分散式系統的人是新詞；第 115 行說「系統保證同一個寫入只執行一次」，沒說為什麼需要（因為回覆可能遺失）。 | 補一句：「這是因為回覆可能在路上遺失，client 不知道寫入有沒有成功，所以需要重送而不重複執行。」 | 建議 |
| N-09 | SETUP:118-120 | 「在節點 1 的 terminal 按 Ctrl-C 停掉它」：Ctrl-C（SIGINT）和 HANDS_ON 說的 SIGKILL 是不同的，新手可能分不清。「讀取照樣成功」前的地址清單裡 7201 已經掛了，文件沒說 client 會自動換下一個位址。 | 補：「`--address` 列了三個，client 連不上第一個就換下一個。」 | 可不改 |
| N-10 | SETUP:122-139（驗收） | 第 6 節對新手是「可跳過」，但沒有明說；45 分鐘與「不要改任何原始檔」的限制放在中間，新手可能不小心在跑驗收時改檔而被中斷。 | 在第 6 節標題下加一句「這一節不是必須的；只想了解系統可以直接跳到第 8 節」。 | 可不改 |
| N-11 | SETUP:14 | 磁碟空間「約 3 GB」可能偏低（此機器的 `target/` 為 5.6 GB）。 | 寫成「至少 3 GB，若跑完整驗收與全部教學重現，預留 6 GB」。 | 建議 |
| N-12 | SETUP:149-150（常見問題） | 兩列「2026-11-17 之前的版本有這個 bug……更新到目前的版本」：新手照這份文件取得的就是目前版本，這兩列對新手沒有幫助，還可能嚇到人。 | 刪掉這兩列，或移到教學 20、21；如果要保留，改成「如果你是用舊的 tag 建置的，會看到……」。 | 建議 |

---

# 嚴重度統計

- **必改：6 個問題點**
  1. 警告與結果的先後寫反了（README.zh-TW.md:114、SETUP.md:101、FAQ.md:14；C-24／N-05）。
  2. DEVELOPMENT.md:4「`git tag` 列出的就是驗收過的版本」與實際的 tag 不符（C-39）。
  3. README.zh-TW.md:28、FAQ.md:107 的「14 個」與 DEVELOPMENT.md:90 的「值得守的都補了」不一致，案例數也只有 11 個（C-38）。
  4. GLOSSARY.md:3 描述自己「每一條寫三件事」但表格不是這樣（F-26）。
  5. GLOSSARY.md:71 與 FAQ.md:89 的追趕「最多 10 輪」應為「固定 10 輪」（C-17）。
  6. SETUP.md:114-119 沒有說明 sequence 要接續使用，新手重跑會得到舊結果（N-07）。
- **建議：約 28 個**（長句拆分、用語統一、新手提示等）。
- **可不改：約 9 個**。

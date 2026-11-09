# 從 micro-os 開始使用 ai-general-framework

這份教學帶你在自己的工作目錄使用框架，選擇技能、保留專案原有配置，並在框架更新後同步專案。你會先看到修改預覽，再決定是否套用。範例使用 [JiaChangGit/micro-os](https://github.com/JiaChangGit/micro-os)；它是 AArch64 微核心專案，主要在 WSL 的 Linux 檔案系統中建置和驗證。WSL 是 Windows 上執行 Linux 環境的功能，QEMU 是本例使用的機器模擬器。這份教學核對的是 2026-11-08 的 [micro-os README](https://github.com/JiaChangGit/micro-os/blob/ebbe1c1f2e18091b0ddf47b39eb4058c99d45e79/README.md) 和 [AGENTS.md](https://github.com/JiaChangGit/micro-os/blob/ebbe1c1f2e18091b0ddf47b39eb4058c99d45e79/AGENTS.md)，實際工作仍以你的 checkout 為準。

框架本身是 Python 腳本與文字，不需要先編譯，也不需要 pip 安裝；下文的「配置」是把所選規則及技能放入目標專案，並設定共用工具入口。框架不提供模型、帳號或模型訓練服務。`micro-os` 自己的編譯器、QEMU 等需求是另一回事。

本文的 **skill（技能）** 是供 AI 按任務讀取的指引檔；**script（腳本）** 是執行具體操作的程式。**MCP** 是讓 AI 工具連接外部能力的介面，可能在本機執行程式或連接外部服務。**宿主**指 OpenCode、Codex 等實際執行 AI 的工具。**CLI** 是透過終端機輸入命令操作的介面；**checkout** 是你電腦上的專案副本。

## 1. 準備位置與環境

1. 準備 Python 3.11 以上及 Git。準備好你要用的 AI 工具，例如 OpenCode 或 Codex；是否安裝、登入及可用的模型由各工具決定。
2. 框架已公開於 [JiaChangGit/ai-general-framework](https://github.com/JiaChangGit/ai-general-framework)。已有 checkout 就沿用；尚未取得時，在準備存放專案的父目錄執行下列命令。這條命令在 WSL／Linux 終端機與 Windows PowerShell 都適用，會建立 `ai-general-framework` 子目錄，不會替你配置 micro-os：

   ```console
   git clone https://github.com/JiaChangGit/ai-general-framework.git
   ```

3. 如尚未取得 micro-os，可以在預定的父目錄由你自己執行以下命令；已有 checkout 的話使用原來位置，不要覆蓋它：

   ```console
   git clone https://github.com/JiaChangGit/micro-os.git
   ```

4. 確認兩個資料夾的位置。以下路徑只是範例，請換成你自己的**絕對路徑**；兩個資料夾必須已存在。

   在 **WSL／Linux 的終端機**：

   ```bash
   AGF="$HOME/src/ai-general-framework"
   TARGET="$HOME/src/micro-os"
   cd "$AGF"
   python3 --version
   git --version
   function agf() { python3 "$AGF/scripts/agf.py" "$@"; }
   agf doctor --root "$TARGET"
   agf audit
   ```

   在 **Windows PowerShell** 使用 Windows 自己的框架及目標路徑時：

   ```powershell
   $AGF = "$env:USERPROFILE\src\ai-general-framework"
   $TARGET = "$env:USERPROFILE\src\micro-os"
   Set-Location $AGF
   python --version
   git --version
   function agf { python (Join-Path $AGF 'scripts/agf.py') @args }
   agf doctor --root "$TARGET"
   agf audit
   ```

   函式 `agf` 只存在於目前的終端機；重新開啟時重設變數與函式。以下 `agf` 命令在這兩種 shell 都適用。不要把 WSL 的 `/home/...` 當成 Windows Python 的原生路徑，也不要假設 Windows 網路路徑與 WSL 路徑可自動互換。**micro-os 的實際 build／QEMU 請使用它指定的 WSL 環境**；Windows 範例只說明框架可以管理 Windows 專案。

`doctor` 顯示找到的執行檔和本機版本控制標記，不驗證登入、技能載入或模型可用。`audit` 檢查框架結構、語法與本機連結；它的 PASS 不代表 micro-os 已建置、全部問題已排除。若找不到 Python 或目標目錄，先修正本機環境或路徑；可選工具缺失不代表框架核心無法使用。

## 2. 先檢視目標專案

從任意位置執行；第一行只適用於使用 Git 的工作目錄：

```console
git -C "$TARGET" status --short --branch
agf project status --target "$TARGET"
```

第一個命令確認目標工作目錄目前有哪些變更。框架本身不要求目標是 Git 版本庫：若目標不是 Git 專案，略過第一個命令；只有你確定要將它變成新的 Git 專案並授權該操作時才考慮 `git init`。第二個顯示框架是否已有配置；若顯示尚未配置，接下來用 `plan` 和 `install`。`status` 是框架受管理檔案的狀態，不是所有既有 skills、scripts 或 MCP 的完整清單。

自行查看目標的 `AGENTS.md`、`.agents/skills/`、`.claude/`、`.opencode/`、`scripts/` 及工具自己的設定位置；不存在就略過。設定位置依 AI 工具版本和專案而異，還可能存在使用者層設定；不要只憑一個資料夾斷定完全沒有 MCP。保留既有規則、憑證和程式，不把設定內容貼到公開討論。

### 情況 A：目標沒有既有 AI 規則或技能

這是示範用的**假設情境**。實際 micro-os 已有 `AGENTS.md`、專用 skill 原始碼及 `tools/` scripts，因此應走下面的情況 B；不要為了模仿這個情境而刪掉它們。如果你有自己的全新專案，先把 `TARGET` 改成該**已存在**的空目錄，再在目前終端機依序執行：

若這個目標使用 Git，配置之前也先參照下方情況 B 的 `.agf/` 忽略檢查，避免未來把本機紀錄加入版本庫。

```console
agf project plan --target "$TARGET" --host opencode --skill trace-code --skill guide-learning
```

檢查 JSON 的 `operations`、`conflicts`、`notices` 和 `applied`。`applied: false` 表示這是預覽；注意目標位置、將建立的檔案及是否衝突。若沒有阻擋問題，才執行：

```console
agf project install --target "$TARGET" --host opencode --skill trace-code --skill guide-learning --apply
agf project status --target "$TARGET"
```

這選了兩個技能：`trace-code` 用於追指定執行路徑，`guide-learning` 用於學專案。`--host` 和 `--skill` 可以重複；不指定 skill 時預設沒有額外技能。全新、沒有同名規則的目標可能產生 `AGENTS.md` 入口，請看實際計畫及檔案內容；`--host codex` 可用於選擇 Codex 對應配置。

### 情況 B：目標已經有 skills、scripts 或 MCP

這是實際 micro-os 適用的起點。它的根目錄有 `AGENTS.md`，來源也有 `skills/microkernel-engineering/` 和 `tools/`；skill 原始碼存在與 AI 宿主已載入該 skill 是不同事情。是否另有個人層 MCP 或技能，要由你依實際宿主檢查。

若剛才把 `TARGET` 改成其他目錄，先依第 1 節將它設回你實際的 micro-os 路徑，再執行以下檢查。

套用配置前，先確保目標不會不小心公開 `.agf/`：

1. 查看目標根目錄的 `.gitignore` 或 Git 的本機 exclude 規則。這些規則用來略過尚未追蹤的檔案；目前核對的 micro-os 版本未在 `.gitignore` 中排除根目錄 `.agf/`，你的 checkout 可能已不同。
2. 若沒有適用規則，保留原內容，用編輯器在目標既有 `.gitignore` 加入單獨一行 `/.agf/`；這是你自己可以審閱的本機修改。也可以依團隊習慣改用 Git 的本機 exclude。不要刪掉或取代原規則。
3. 對 Git 工作目錄執行 `git -C "$TARGET" check-ignore -v .agf/`，確認輸出指出正確規則。安裝後再執行 `git -C "$TARGET" status --short --untracked-files=all`，逐項確認。已經被 Git 追蹤的檔案和歷史內容，不會因新增忽略規則自動移除；不要使用一鍵加入所有檔案的命令。
4. `.agents/skills/` 的技能檔是否要分享，依你的專案和隱私需求逐項決定；不要因為排除 `.agf/` 就假設所有技能或既有設定也被排除。

1. 將 `TARGET` 設回 micro-os 實際目錄，確認已有變更和專案規則。若已安裝同名 `trace-code` 或 `guide-learning`，先看計畫中是否有衝突；不要自行覆寫。
2. 執行相同的預覽，檢查 `operations`、`conflicts`、`notices`：

   ```console
   agf project plan --target "$TARGET" --host opencode --skill trace-code --skill guide-learning
   ```

3. 確認目標正確且沒有未處理衝突後套用，再檢查狀態：

   ```console
   agf project install --target "$TARGET" --host opencode --skill trace-code --skill guide-learning --apply
   agf project status --target "$TARGET"
   git -C "$TARGET" status --short
   ```

既有 `AGENTS.md` 不會被自動改寫。如果預覽提示保留了它，配置後在新對話中明確請 AI「先讀專案 `AGENTS.md` 和 `.agf/managed/project-rules.md`」，或由你檢視後手動將後者的引用加入適當的專案規則。不要假設規則因檔案存在就一定被宿主讀取；衝突時以目前使用者指示和目標專案要求為準，請 AI 指出影響結果的差異。

既有 scripts、MCP 設定及其他未受框架管理的 skill 不因配置而自動整合或驗證。使用前仍檢查 MCP 的來源、版本、資料去向、權限及實際使用者回饋；新安裝、帳號連接及傳出私有資料依當次授權。[選工具指引](tools.md)有具體判斷方式。

`status` 的 `clean` 表示受管理檔案沒有偵測到漂移；`tools_available` 表示工具入口可讀；`ready` 合併呈現配置可用狀態。它們都不表示 AI 宿主實際載入技能。框架在目標的 `.agf/` 可能保存本機路徑、備份及紀錄；在分享或 commit 前先確認是否排除。若用 Git，可檢查該專案既有 `.gitignore` 或本機 exclude 的做法；不確定時先查看 `git status --short --untracked-files=all`，不要把 `.agf/` 整包上傳。

## 3. 在 micro-os 做一個有來源的帶讀

在目標專案開啟 AI 工具的新對話，先確認它有權讀取你的 checkout。可以直接給這段需求：

> 請先讀本專案的 `AGENTS.md` 和 `.agf/managed/project-rules.md`。我想理解 P5 的一個具體行為：先讀取目前 Phase 的入口與必要來源，挑一條 client timeout 路徑，說明觸發條件、涉及的任務與狀態變化，附上實際來源位置。請區分靜態推論與已執行的觀察，先不要修改檔案，也不要啟動 QEMU。

AI 應先依專案的當前規則查必要內容，例如 `python3 tools/context.py --phase P5` 的輸出與相關程式；不要由這份教學憑記憶替它指定不存在的函式或結果。看回答是否有來源、條件和狀態變化；如果宿主沒有提供技能載入紀錄，就把自動載入狀態列為未知。你也可以請它出一道「改變一個條件後結果如何」的練習，先自行預測，再一起核對原始碼。

若要真正建置 micro-os，在 **WSL 的 micro-os 根目錄**依它目前 README 核對環境；先用 `python3 tools/bootstrap.py` 查看需求，無 `--install`。確認工具已具備、且這次任務允許執行後，再按專案要求使用 `make all`、`make test` 或 `make phase-status`。執行 `--install`、系統安裝、遠端發布等要另依當次授權處理。框架狀態正常不代表 QEMU 或 micro-os gate 已通過。

### 3.1 換對話、換模型與保留記憶

同一個 session 切模型時先沿用宿主上下文；換對話或工具才整理足以接手的交接。你可以先用框架內建的佇列案例試一次，以下命令在兩種 shell 都適用，輸出檔若已存在會拒絕覆寫：

```console
agf task record --input "$AGF/examples/task.json" --root "$AGF" --output "$TARGET/.agf/task-queue.json"
agf task check "$TARGET/.agf/task-queue.json"
agf task handoff "$TARGET/.agf/task-queue.json" --output "$TARGET/.agf/handoff-queue.md"
```

這只是佇列範例，不是 micro-os 測試結果。真正交接 timeout 任務時，把範例複製到自己的任務輸入檔，依目前工作改寫目標、範圍、驗收、決定及理由；以 `--root "$TARGET"` 解析實際證據檔。`verification` 寫已做／未做的驗證、實際時間及結果位置，`next_steps` 寫下一個可執行步驟，`boundaries` 保留目前授權。需要 Git 版本及差異身分時再加 `--repo "$TARGET"`；未追蹤檔的內容仍須列為 evidence。紀錄建立時間不代表測試剛重跑過。

在接手的新對話提供交接檔位置，請 AI「先讀交接，再核對目前版本、差異及相關來源；過期的測試重驗，尚未確認的事保留未知」。來源改變後，`task check` 會指出證據過期，`handoff` 會拒絕產生新的交接；不要只更新雜湊便沿用舊結論。舊交接本身不會新增授權；要核對目前指示與可查證的原始授權，不能只靠摘要執行部署或外傳。

長期記憶則只留後續工作會重用、已確認的內容。先用 `agf profile show --root "$TARGET"` 查現有偏好；個人偏好在原使用者設定更正，專案偏好在既有 `.agf/profile.json` 更正，團隊決策及原因放專案既有規則或決策文件。記下來源、適用範圍及確認日期；找不到原紀錄才考慮新增，不另存互相矛盾的副本。例如「這次追程式只用文字」先留在任務交接，只有使用者確認日後都要沿用，才成為對應範圍的偏好。舊決定失效時更正或標明被哪項決定取代；接手先搜尋相關項目，再回查來源。詳細取捨見[分工與續接指引](workflow.md)。

## 4. 更新框架，然後更新目標配置

框架來源更新和目標配置更新是兩步。預設 `shared` 讓各專案共用同一份框架工具；目標內受管理規則和已選技能仍需透過 update 同步。`copy` 是將工具存成目標內快照，適合離線或交付；框架來源更新不會自動更新該快照。先確認 `$AGF`、`$TARGET` 仍是你要操作的兩個路徑。

這裡的「快照」是當時工具檔案的一份副本，不會自己跟著來源變動。

### 4.1 檢查並取得框架新版

```console
git -C "$AGF" status --short --branch
git -C "$AGF" remote -v
```

有本地修改時先自行檢視、保存或提交，不要直接覆蓋。若使用的是沒有遠端設定的資料夾副本，先確認來源，不直接套用下面的更新命令；`remote -v` 可能顯示帶憑證的 URL，勿直接公開貼出。由上方公開網址 clone 的副本通常已有 `origin`；確認它仍指向預期儲存庫並允許連網後，可取得及審查新版：

```console
git -C "$AGF" fetch
git -C "$AGF" log --oneline 'HEAD..@{upstream}'
git -C "$AGF" diff --stat 'HEAD..@{upstream}'
```

這些命令需要目前分支已有上游；沒有時依 Git 的提示先確認分支設定。審查後、且確認可以快轉合併時：

```console
git -C "$AGF" pull --ff-only
agf audit
```

若無法快轉或有衝突，停止並先處理差異，不用強制覆蓋。`fetch`／`pull` 會連網並修改本機 Git 資料或工作目錄；不是每次使用框架都需要做。

### 4.2 預覽並套用目標配置更新

```console
agf project status --target "$TARGET"
agf project update --target "$TARGET"
```

查看預覽的 `operations`、`drift`、`conflicts` 和 `notices`。`drift` 是已受管理檔案與上次記錄不同；先比較並保存你的變更，確認處理方式後再繼續。不要為了讓更新通過直接刪掉個人修改。同名未管理檔案或來源已移除的 skill 也要看清楚計畫。

確認無待處理問題後：

```console
agf project update --target "$TARGET" --apply
agf project status --target "$TARGET"
```

不重填選項時，更新保留既有 host、選用技能及 shared／copy 模式，已退役的受管理技能依計畫處理。換到新路徑或另一作業系統時，可在預覽及套用時明示 `--source` 指向該環境中**實際可讀的框架 checkout**，先確定路徑和預覽；例如在上述命令加上 `--source "$AGF"`。要從 shared 改為快照，預覽及套用時加 `--tools copy`；反向切換用 `--tools shared`，都應先看計畫。

如果要回復**上一筆框架配置**，先預覽，再決定是否套用：

```console
agf project rollback --target "$TARGET"
agf project rollback --target "$TARGET" --apply
agf project status --target "$TARGET"
```

Rollback 處理框架記錄的配置，不是回退整個 micro-os、Git commit 或任意資料檔；目標被修改或備份不可用時看錯誤，先處理，不要強制清除。Shared 模式所指向的框架程式仍以當前來源為準；若要回到舊版程式，也必須另外處理來源版本，不能只靠配置 rollback。

## 5. 其他用法：以資料輔助寫小說

假設你有自己的世界觀、人物設定，以及希望查找可商用素材的需求，可在自己的創作專案開對話，先給 AI 這樣的任務：

> 先讀我指定的世界觀和人物設定，找出尚未確定但會影響故事的問題。再查找符合我預計用途的公開資料，逐項提供原始連結、作者、授權條款、查詢日期，以及商用、改編和署名條件；條款不明的資料先列待確認。不要上傳我的私人原稿或啟動訓練。先提出角色與故事大綱，等我確認後再寫正文。

逐項核對授權是否真的涵蓋你的素材、使用方式和地區；「公開可讀」「可免費下載」或 AI 說可以商用，均不足以證明商業使用或訓練獲准。特別注意資料中第三方圖片、音樂、個人資料和平台條款；保留來源及版本。對你的資料也確認你擁有相關權利，將機密資訊與不需要的個資排除；使用外部模型或服務前確認資料實際會傳到哪裡、如何保存及當次授權。

這裡有兩種不同方法：

- **提供參考資料**：把選定的設定與素材放在這次可讀的範圍，或依需要使用經授權的檢索工具，再要求 AI 引用來源。有些工具稱「先找資料再交給模型回答」為 RAG（檢索增強生成）；這不等於修改模型權重。
- **實際訓練／微調**：微調是使用一批資料繼續調整現有模型的參數。這另外需要可用的模型、訓練工具、運算資源、資料格式及適用授權。先說明想改善的成果與驗收，確認取得來源和訓練許可、資料去識別與外傳條件，再選具體工具做小規模試驗；本框架沒有內建訓練引擎，也不能保證訓練後作品可商用。

不論採用哪一種，保留一批未放進參考材料或訓練集的測試題，檢查角色設定一致、事實來源、輸出重複及是否洩露原稿。實際工具、模型和資料的效果必須在你的任務中驗證，不能由設定完成或 AI 自評推定。

### 如果真的想做一次微調

先把目標限定成可比較的小任務，例如「依既定人物設定寫一段對話」，而非先蒐集大量小說。下面是準備與驗收步驟，不會自行下載模型、安裝程式或開始訓練：

1. **確認資料及模型的權利。** 對每個候選資料集回到原作者、來源頁和原始授權，看是否允許預定用途、商業使用、改編及模型訓練，並確認署名、再散布、第三方內容和平台條款。也要查基礎模型的授權及使用條款：資料允許使用，不代表模型也允許該用途。條款不清楚就列為未知並先排除。可參考 [Creative Commons 各授權條款](https://creativecommons.org/cc-licenses/)，但仍須看具體作品與適用條款。
2. **整理來源及自己的素材。** 為每批資料記錄來源網址、作者、版本或取得日期、授權、允許用途及限制；自有素材記錄作者與權利狀態。可參考 [Hugging Face 資料集卡片](https://huggingface.co/docs/hub/datasets-cards)該記錄哪些資訊。先移除不需要的個資、密碼和未授權的他人內容；原稿、資料副本、訓練輸出和日誌都需要選擇合適的本機保存範圍。沒有確認服務的資料去向和授權前，不把私人資料交給外部平台。
3. **分開訓練與驗收。** 先以故事、角色或來源等適合的單位切分，盡可能避免同一段或高度相似內容跨集合；把驗收題另外保留，不拿來調參或當訓練資料。準備相同的任務題、設定及評分條件，先記錄未微調模型的表現作為基準。
4. **選擇可用模型與工具。** 查核模型版本、授權、硬體記憶體、磁碟、訓練時間、費用和資料流，並評估本機或服務執行。工具例子有 [Hugging Face PEFT](https://huggingface.co/docs/peft/index) 與 [TRL SFT Trainer](https://huggingface.co/docs/trl/sft_trainer)；適用格式和需求以選定版本為準。由使用者決定後才下載、安裝、連線或上傳，框架不自動替你執行這些步驟。
5. **先用少量合成資料驗證流程。** 例如下列是人為虛構的單筆 JSONL 訓練資料：每行是一個 JSON 物件；欄位只作說明，真正格式依工具和模型的聊天模板調整。這筆資料既不是有效的完整資料集，也不足以證明模型能學會風格：

   ```json
   {"messages":[{"role":"user","content":"寫一句守鐘人與旅人的對話，語氣平靜。"},{"role":"assistant","content":"守鐘人說：『天亮前，這座橋只為願意等待的人開放。』"}]}
   ```

   可另擬不同內容作保留驗收題，例如「寫守鐘人拒絕旅人過橋的兩句對話」，不把其參考答案或近似訓練內容送入訓練集。確認你選的工具能讀取自己的資料格式後，才在已授權環境進行小規模試驗；此文件沒有執行訓練。
6. **記錄並比較。** 保存資料來源與切分方式、基礎模型與 tokenizer（將文字轉換成模型輸入單位的工具）版本、工具版本、訓練設定、隨機種子、產物位置、執行結果及錯誤；不要把私密訓練資料與憑證放進公開紀錄。用同一組未見過的驗收題和盡量相同的生成設定，比較微調前後的角色一致性、可讀性、重複與原稿洩露；必要時重複觀察，不因一個漂亮範例就宣稱改善。
7. **交付或停止。** 結果未改善、出現記憶或洩露時，先檢查資料切分、品質及設定，再決定是否繼續。分享模型或作品前重新核對資料、基礎模型及產物的授權與隱私。使用參考資料若已達到需求，也可以直接保留較簡單的做法。

## 6. 按需使用其他技能與腳本

其他可明確選用的技能包括 `debug-root-cause`（已發生的故障）、`review-change`（指定變更）、`read-research`（論文或規格），以及 `review-sql`（慢 SQL 或資料庫變更審查）。若需要在現有目標增加技能，先用下列命令看預覽；確認計畫後再於同一命令最後加 `--apply`：

```console
agf project update --target "$TARGET" --skill debug-root-cause
```

只指定特定 skill 的 update 會更新所選項目；請以預覽和之後的 `status` 核對保留與新增的內容。使用 AI 時直接描述任務，例如：「請唯讀調查這份 QEMU log 的異常，區分已觀察的現象、可能原因和能區分假設的下一步。」需要真實 QEMU log 時提供實際檔案，不讓 AI 把範例當執行結果。

在兩個 shell 設好第 1 節的 `AGF`、`TARGET` 與 `agf` 後，可以試這些命令：

```console
agf profile show --root "$TARGET"
agf context extract "$TARGET/kernel/task.c" --start 1 --end 40
agf files diff "$AGF/examples/files/before.json" "$AGF/examples/files/after.json" --format json
agf diagram create "$AGF/examples/diagrams/files-transaction.json" --format mermaid
```

依序是查看有效偏好、只取來源指定行、比較框架附帶的兩份 JSON、預覽由框架附帶模型產生的 Mermaid 圖文字。`profile` 是偏好設定，不等於操作授權；來源摘錄與圖解有各自的來源及截斷資訊。這兩個 JSON 本來有差異；目前 `files diff` 成功比較時即使發現差異也可能回傳 0，請以 JSON 的 `changes`、`total_changes` 及 `truncated` 判讀。最後一個圖是框架檔案操作的範例，不是 micro-os 的執行軌跡；預覽圖文字也不代表已渲染或驗證圖的語意。更多預覽、批次改名與 draw.io 命令見 [CLI 操作](cli.md)及[圖解範例](../examples/diagrams/README.md)。

## 7. 出錯時先看哪裡

| 現象 | 先做什麼 |
|---|---|
| `project plan` 指出 conflict 或 drift | 查看列出的路徑和現有內容；保存必要修改後再決定，避免覆蓋原有工作。 |
| `status` 顯示工具來源不可用 | 確認 shared 來源還在、目前 shell 使用正確的本機路徑；需要時用可讀來源的 `--source` 預覽更新。 |
| AI 沒遵循規則或找不到 skill | 確認目標、宿主及技能是否配置；保留既有 AGENTS 時明確要求讀取框架規則。查看宿主實際載入紀錄，沒有紀錄就記為未知。 |
| `rg` 不可用 | 先用系統原生搜尋定位，再用 `context extract` 讀確定的範圍；需要時由你評估是否安裝 ripgrep。 |
| 執行輸出被截斷 | 縮小查詢；需要完整診斷時，事先用 `run --output-dir` 保存，原始輸出未自動去識別。已完成的寫入不要只為取回輸出重跑。 |

本文件的框架配置流程曾在隔離的空目標與含既有規則、skill、script 和模擬 MCP 設定的目標測試 `plan/install/status/update/rollback`；未對真實 micro-os 工作目錄套用，也未驗證各 AI 宿主實際載入或模型訓練。其他 CLI 操作見 [CLI 操作](cli.md)，最新驗證範圍見 [驗證紀錄](verification.md)。

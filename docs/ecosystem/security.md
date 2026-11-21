# 外部資源審查清單

裝一個外部 skill、MCP server、CLI、腳本、hook、GitHub Action 或套件之前，照這份清單看一次；讓它讀本機檔案、連網或拿到憑證之前也是。[tools 指引](../tools.md)的「選用前先查品質與安全」是原則，這份是逐項的做法。結果寫進 [entries.json](entries.json) 那一筆的 `security` 欄，並更新 `checked` 日期。

清單只處理「它會做什麼」。好不好用、值不值得用，看各分類頁與比較。

## 1. 確認是哪一份

- 找到真正的上游：作者、組織、是不是 fork 或同名專案。這次研究就遇到 pstack、Ponytail、CodeGraph、yq 都有不同作者的同名版本。
- 固定版本：commit SHA、release tag，或套件版本加 hash。只寫「最新版」的紀錄，下次就對不上。
- star 數、排行榜、skill 目錄網站的安全分數只是線索，不能代替讀原始碼。

## 2. 讀會執行的東西，但不執行它

先 `git clone --depth 1` 到框架以外的資料夾，或在網頁上讀固定版本的檔案。要看的地方：

| 位置 | 找什麼 |
|---|---|
| 安裝腳本、`package.json` 的 `postinstall`、`setup.py`、`Makefile` | 下載後直接執行（`curl … \| sh`）、改 shell 設定檔、要 sudo |
| hooks、MCP 的啟動命令、Dockerfile | 每次 session 都會跑的命令；從網路拉最新版的寫法（`npx -y 套件@latest`） |
| GitHub Action 的 `uses:` 與 `run:` | 用 tag 而不是 commit SHA 引用別人的 action；`pull_request_target` 加上 checkout 外部程式碼 |
| 程式本身 | 讀 `~/.ssh`、`~/.aws`、瀏覽器 Cookie、環境變數；寫死的網路端點；`eval`、動態載入；telemetry 與自動更新 |

用 Python 讀不可信的檔案時加 `-I`，並從 clone 以外的目錄執行，避免載入它放的同名模組。

## 3. Skill 的特別檢查

SKILL.md、references 與附帶的 scripts 都是會被模型讀進去的指令，要當成程式看：

- 要求讀取 secrets、`.env`、金鑰，或把內容傳到外部網址。
- 要求關閉權限檢查、略過確認、用 `--dangerously-*` 一類旗標。
- frontmatter 的 `allowed-tools` 給了比用途寬很多的權限（例如整個 Bash）。
- 附帶的腳本會下載檔案、安裝套件，或呼叫 SKILL.md 沒提到的 MCP 與 API。
- 看不見的文字：HTML 註解、零寬字元、base64 字串、和用途無關的「忽略之前的指示」。
- usage beacon 或 telemetry：每次叫用就送一次請求（[link-study](../link-study.md) 記錄過 Hyperframes 的例子）。

## 4. MCP 的特別檢查

- **連線方式**：stdio 是在本機跑一個程式；HTTP／SSE 連到遠端服務，資料會離開這台電腦。
- **認證**：要哪些 token 或 OAuth scope，是不是比用途寬；token 存在哪裡。
- **工具清單**：每個 tool 的描述也會被模型讀進去，描述裡夾帶的指令和 SKILL.md 一樣危險。哪些 tool 會寫檔、送出請求或改遠端資料。
- **版本固定**：server 更新後工具描述可能改變。用固定版本，更新時重看一次清單。
- **會不會繞過 hook**：PreToolUse hook 只看 matcher 列出的工具。S17 起框架的 guard hook 也會檢查 MCP 工具，但前提是設定的 matcher 含 `mcp__.*`（舊的設定只有 `Bash|Edit|Write|MultiEdit|NotebookEdit`）。它只認得名稱像命令（command、cmd、script）與路徑（path、file、destination）的參數；裝能執行命令或寫檔的 MCP（例如 Fastctx 的 `run`）之前，看一下它的參數名稱是否在這些之中。

## 5. 資料送到哪裡

- 本機、雲端，或兩者混用；送出什麼、存在哪裡、保留多久。
- 「本地」「不用 API key」「關掉 telemetry」不等於完全不連網：模型下載、更新檢查、hosted reader 都可能另外連線。
- 會不會把存下的內容在之後的 session 再送給模型服務。使用者把這種情況視為上雲端，要先取得同意（HANDOFF 的 `save_prompts` 一節）。

## 6. 已知的問題

- GitHub Security Advisories、[OSV](https://osv.dev/)、專案 issue 裡的 security 標籤。
- 近期的供應鏈事件：被入侵的 GitHub Action、被搶註或植入的套件版本。有的話記下日期、受影響版本與來源。
- 沒查到公開漏洞，不代表安全；寫「未發現公開紀錄（查核日期）」。

### 近期事件（2026-11-22 整理）

都和這份資料庫收錄的工具有關。「已核對」表示主 session 讀過官方公告或漏洞資料庫的條目；其他只看到搜尋摘要或子代理的筆記。

| 日期 | 事件 | 受影響 | 來源 |
|---|---|---|---|
| 2026-03-19 | Trivy 生態系被入侵（CVE-2026-33634）：惡意的 Trivy v0.69.4，`aquasecurity/trivy-action` 的版本 tag 被改指到竊密程式 | trivy-action 0.0.1～0.34.2、setup-trivy 0.2.0～0.2.6；用 tag 而不是 commit SHA 引用的 workflow | 已核對：[NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-33634)；CISA 已列入 KEV |
| 2026-03-24 | LiteLLM 1.82.7、1.82.8 在 PyPI 被植入竊密程式；維護者的 PyPI 憑證是從 CI 裡被入侵的 Trivy 洩漏的 | 這兩個版本；1.82.8 用 `.pth` 檔，任何 Python 程序啟動都會執行 | 已核對：[OSV MAL-2026-2144](https://osv.dev/vulnerability/MAL-2026-2144)、[LiteLLM 公告](https://docs.litellm.ai/blog/security-update-march-2026) |
| 2026-10-21 | LiteLLM 1.107.0 的發布流程被劫持，PyPI 七個 wheel 與官方 Docker 映像都帶竊密程式與每小時回連的下載器 | 1.107.0；最後安全版 1.106.2 | 已核對：[The Register](https://theregister.com/security/2026-10-21/litellm-supply-chain-attack-hoovers-up-passwords-and-secrets/5304548)、[BleepingComputer](https://bleepingcomputer.com/news/security/litellm-release-pipeline-hacked-to-distribute-info-stealer-malware) |
| 2026-02（2026-08-18 給 CVE） | ContextCrush（CVE-2026-75130）：Context7 的社群規則原樣送給 agent，可夾帶指令 | 使用 Context7 MCP 的 agent；Upstash 已從伺服器端修正，使用者端不用升級 | 已核對：[NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-75130)、[Context7 說明](https://context7.com/guides/contextcrush) |
| 2025-03 | tj-actions/changed-files 被入侵，會把 CI secrets 印到 log（CVE-2025-30066） | 使用該 Action 的 repo | 搜尋摘要（子代理 M） |
| 2026-03～04 | Checkmarx 的 KICS 與 AST GitHub Action 被同一批攻擊者入侵 | 見子代理 M 的筆記 | 搜尋摘要（子代理 M） |

研究時在被研究的內容裡看到、沒有照做的指令：MinerU 的 README 有一段寫給 AI agent 的話，要它用 `npx skills add … --global --yes` 全域安裝第三方 skill；Graphify 的 skill 在找不到套件時會自動 `pip install … --break-system-packages`。工具文件本身也可能是 prompt injection 的來源。

2026-11-22 查過：`~/src` 底下的專案沒有用到 trivy-action、setup-trivy 或 LiteLLM；框架自己的 CI 用 commit SHA 引用 Action。

## 7. 試用

使用者允許試跑時，在 Docker 容器裡做：不掛載家目錄，只掛一個放測試資料的資料夾，測試資料不含私人內容或公司程式碼。記下 image、版本、命令與結果。要給它網路時，說明它會連到哪裡。

## 8. 決定與紀錄

給出三種結論之一：採用、有條件試用、暫不採用。寫進 `security` 欄的內容：看了哪個版本、看了哪些檔案、發現什麼、還不知道什麼。`checked` 寫查核日期；換版本、換權限、出現新的漏洞消息時重查。

可以幫忙的工具（Gitleaks、OSV-Scanner、zizmor、actionlint、Semgrep 等）列在 [CI/CD、資安與授權工具](categories/security-devops.md)。工具掃描沒有發現，同樣只代表「這個工具在這個範圍沒找到」。

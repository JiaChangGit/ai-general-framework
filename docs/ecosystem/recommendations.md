# 建議與待確認

2026-11-22 整理。Tier 1 的完整清單由資料產生，在 [README](README.md#tier-1優先研究)；這一頁說明怎麼用這些研究、哪些還沒確定。框架要怎麼排這些工作，以[分析報告第六輪](../analysis-2026-11.md#路線圖)的路線圖為準。

## 依路線圖排的下一步

| 輪次 | 用到的研究 | 要做的事 |
|---|---|---|
| S17 共通能力 | pstack `correct` 與「把教訓寫進結構」、DejaVu 的可檢查決策、[審查清單](security.md) | 在 maintenance 指引寫「同一類錯誤出現兩次就升級成檢查」的順序；tools 指引改指向資料庫與審查清單 |
| S18 Benchmark | Promptfoo（有 Claude Agent SDK provider 與「skill 叫用次數」斷言）、Claude Code 內建的 OpenTelemetry（cost 與 token 帶 `skill.name`）、CodeGraph 作者的量測方法（對照組要真的拿不到被測工具） | 先比 Promptfoo 和現有的 `evals/host/impact.py`，現有工具夠用就不引入；用 OTel 量每個 skill 的實際成本，只開 metrics、送到本機 |
| S19 C 與 kernel | [程式理解比較](comparisons/code-understanding.md)與試跑 | cflow `--cpp`、clang 或 clangd 取直接呼叫，CodeGraph 的 ops table 結果當候選；在 e1000e 上補測 Serena＋clangd 與 Joern |
| S20 研究文件 | [文件解析比較](comparisons/document-parsers.md)與試跑 | pymupdf4llm（外部命令）、Docling JSON、OCRmyPDF 的接法；用真實論文再測一次 |
| S21 跨宿主 | Trail of Bits second-opinion、codex-plugin-cc | 同一份交接交給 Codex 或 Gemini CLI 接手或審查 |

創作類等有真實作品時再用：Stickman Kino（全本機、旁白長度決定畫面，TTS 用 Kokoro）、Remotion（個人與三人以下公司免費）、music-composition-skills（純文字的編曲規格，不產生音訊）、Novel Studio（長篇小說的角色、伏筆與章節狀態機）、Open Notebook（NotebookLM 的自架替代，預設綁所有網路介面且沒有密碼，要改綁 127.0.0.1）。

## 使用者要求的標示

只列代表性的項目；完整的標記在 `entries.json` 的 `use` 欄，可以用 `jq` 篩。

| 標示 | 項目 |
|---|---|
| 可直接使用的工具 | ripgrep、jq、yq（mikefarah）、difftastic、pandoc、gh／glab、mermaid-cli、zizmor、actionlint、gitleaks、osv-scanner、whisper.cpp、ffmpeg、cflow、clangd、OCRmyPDF |
| 適合整合 | Claude Code OTel、Docling、pymupdf4llm（外部命令）、OCRmyPDF、Crawl4AI、trafilatura、zizmor、Serena（試跑後再定） |
| 適合學架構 | pstack（上游）、CodeGraph（colbymchenry）、codebase-memory-mcp、DejaVu（HMAKT99）、claude-mem、Novel Studio、Graphiti |
| 值得借鑑的 skill | pstack 的 correct、why、arena；Trail of Bits second-opinion；Cloudflare security-audit-skill（多階段稽核、發現要再驗證）；mattpocock 的 grill-me 與 claude-handoff；embedded-review（韌體 code review 的 P0～P3 分級） |
| 值得研究但不建議安裝 | claude-mem（寫入時把工具輸出送模型、telemetry 預設開）、Memory OS（ClaudioDrews）、Firecrawl（本機失敗時改走雲端、AGPL）、LiteLLM（常駐 gateway，2026 年兩次被植入後門）、Graphify（skill 會自動安裝套件）、Fastctx 1.0（關掉 agent 內建 shell、改由 MCP 工具 `run` 執行命令，guard hook 因此看不到；Workbench 以 bypassPermissions 啟動背景 Claude Code） |
| 暫不建議 | davila7 的 clean-code skill（要求執行其他 skill 目錄的腳本，skill 目錄網站仍給滿分）；mhattingpete 的 git-pushing（寬鬆自動觸發，`git add .` 之後 push）；memory-os（bmaltais，沒有授權、宣傳與實作不符） |
| 需要人工確認 | 2026-11-27 核對了標成「需人工確認」的 38 筆（原本寫 34 筆，算少了）。依據是各 repo 公開的 LICENSE、根目錄檔名與 README 的授權段落；另一家的模型（gpt-6-luna）獨立分類，兩邊不同時取比較保守的標記。結果是可使用 10、有條件 20、仍需人工確認 8。剩下的 8 筆：openai/skills（要逐一看各 skill）、Skills Directory 網站、兩個 MCP repo（授權過渡期）、dejavu（repo 已不在）、mem-agent 與 memory-os（找不到授權）、GitLab CI（服務條款沒讀）。另外 Remotion 本機渲染會不會送出使用登記，仍待確認 |

## 待確認的名稱

2026-11-22 使用者確認：FastCtx 是 [yc-duan/fastctx](https://github.com/yc-duan/fastctx)、Mythpen 是 [niyongsheng/mythpen](https://github.com/niyongsheng/mythpen)，兩者都以最新版為準，已寫進資料庫（Fastctx 在 MCP 分類、Mythpen 在寫作分類）。下面是還沒確定的。

| 名稱 | 目前的判斷 | 需要使用者做的 |
|---|---|---|
| anydoc | firecrawl/anydoc（Rust，MIT）；另有同名 fork 與 SourceForge 舊專案 | 確認是不是這個 |
| headroom、OpenSquilla、deepclaude、ds4、TokenJuice | vocus 成本文章提到，沒有附網址，沒找到唯一來源 | 有興趣再補連結 |
| dejavu（文章版） | jsingletonai/dejavu，repo 與 PyPI 都已 404 | 不用處理 |

## 還沒涵蓋的

- iOS、frontend、資料分析、量化、DevOps／SRE／MLOps、技術寫作領域的 skill：只做到搜尋，沒有收錄。
- 講義轉筆記的專用工具：沒找到。長篇小說的一致性管理原本也沒找到，使用者補上 Mythpen 之後有了一個。
- Mem0、Letta、DeepEval、Ragas 沒讀原始碼。
- 2026-10、11 月的供應鏈事件只查到 LiteLLM 1.107.0，沒有系統性搜尋。
- 試跑只用了自己做的小型材料；真實論文與 kernel 規模的測試還沒做。

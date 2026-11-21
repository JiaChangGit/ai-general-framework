# AI coding 工作流程比較

查核日期：2026-11-21。原始筆記在 [W-workflow-memory.md](../../../studies/ecosystem-2026-11/W-workflow-memory.md)（A 節與比較 2）。這一頁沒有試跑。

## pstack：一份上游，三種包裝

| repo | 關係 | 和上游 58 個 SKILL.md 比 | skill 怎麼被叫用 |
|---|---|---|---|
| [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/main/pstack) | **上游**，作者 Lauren Tan（poteto） | — | 幾乎都只能由使用者叫用 |
| [backnotprop/pstack](https://github.com/backnotprop/pstack) | 鏡像，每天同步 | 43 個逐字相同、15 個改寫 | 同上游 |
| [michael-denyer/pstack-claude](https://github.com/michael-denyer/pstack-claude) | 移植加分支，逐檔記錄 55 個分歧與理由 | 0 個逐字相同 | **全部可由模型自動叫用**，SessionStart 再注入一段路由文字 |
| [PickleBoxer/pstack](https://github.com/PickleBoxer/pstack) | 移植，10 月後停更 | 3 個相同 | 照上游 |

框架 11-09 讀的是 backnotprop 版。同一份內容，上游和 michael-denyer 移植在「誰能叫用 skill」這點完全相反。

## 能力對照

| | 框架現況 | pstack（上游） | Ponytail | Spec Kit | mattpocock/skills | superpowers |
|---|---|---|---|---|---|---|
| 規劃 | `align-with-me`、workflow 指引 | 依任務選 playbook | 不規劃，只限制解法大小 | constitution → specify → plan → tasks | to-spec、grill-me | brainstorming → 計畫 |
| 設計決策 | 每題附建議 | architect 畫兩種形狀；arena 多模型；why 查紀錄 | 先問需不需要、有沒有現成的 | Constitution Check | 決策樹 | 設計核准才動工 |
| 驗證 | 依風險驗證、定期重跑 | 為專案產生 verify skill，定期實際驅動每個功能 | 有邏輯就加小測試 | 標 verified／partial／failed | tdd | 完成前驗證 |
| 成本 | 規則常駐約 1,400 tokens | 高：多數流程開背景子代理，arena 一次 3＋1 個模型 | 作者自報輸出少 45% | 高：每個指令載入 10～20 KB 模板 | 低：叫用時才載入 | 每個 session 注入 bootstrap |
| 自主程度 | 不 push、不開 PR（guard hook 擋） | **外部動作不先問，會自己開 PR、合併** | — | 人工逐步 | 人工叫用 | 人工核准設計 |

## 真正不同的方向

1. **限制產出量的規則**（Ponytail、pstack 的 laziness 規則、Karpathy 四原則）：本質都是 YAGNI 加先重用；框架已用一句規則吸收。
2. **規格先行**（Spec Kit、OpenSpec、BMAD）：用檔案當狀態，差別在流程輕重。Spec Kit 1.4.3 新增 `converge`，從程式現況反推還沒做完的 task。
3. **多模型對抗與擇優**（pstack arena、codex-plugin-cc、Trail of Bits second-opinion）：多花幾倍 token 換獨立視角；關鍵是**不同廠商**的審查者、同一份輸入、只留有證據的發現。
4. **把錯誤變成結構**（pstack correct、DejaVu、mattpocock 的 git-guardrails、框架的 guard hook）：同一類錯誤出現兩次，就依序考慮用架構消除、型別、錯誤訊息寫出正確做法的 lint、行為測試，最後才寫文件；每個新檢查要先在真實的舊錯誤上證明會失敗。
5. **觸發方式**：只能使用者叫、模型自動叫、session 開始強制注入。

## 值得借的

- **pstack `correct` 與「把教訓寫進結構」**：框架分析報告一再看到「寫在文字裡的提醒照樣重犯」，這兩個 skill 給了具體的升級順序。可以用在 `docs/maintenance.md`。
- **pstack `why`**：從 commit、PR 討論回答「為什麼」，推論標成推論，並說出紀錄沒回答的部分。和框架的證據規則一致，可以補進 `trace-code` 或 `guide-learning` 的 reference。
- **pstack `arena` 的評審方式**：rubric 只給評審看、評審要用不同廠商的模型、主 session 和評審意見不同時回頭看 rubric。框架的「換模型審查」可以借。
- **Trail of Bits second-opinion**：讓 Claude Code 交給 Codex 或 Gemini CLI 審查未提交的變更，契約寫得最完整。授權是 CC-BY-SA-4.0，借做法、不複製文字。

## 不能照搬的

- pstack 上游預設「外部動作不先問」、會自己開 PR 與合併，和使用者「不 push、不開 PR」的規則衝突。
- michael-denyer 移植與 superpowers 會在每個 session 開始注入常駐文字，和框架「常駐文字要少」的量測結果衝突。
- superpowers 曾有 Windows hook 會執行 repo 裡植入的 `bash.cmd`（#2393，v7.0.0 已修）。

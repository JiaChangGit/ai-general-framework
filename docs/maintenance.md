# 維護本框架

本文件只給 ai-general-framework 維護者，不部署到下游專案。消費者選用專用 skills，以及按任務需要讀取的 workflow、writing、tools、delivery 四份指引；2026-11-19 起另有一份很短的 practices（從常駐規則移出的改程式、工具、續接、文字四段）。

先找一個真實問題：誤觸 skill、重複提問、漏掉必要條件、腳本故障，或偏好沒有表達清楚。把修正放在最窄的位置，不將單次失敗或個人例子升格為所有工作的永久規則。

反覆且能機械判定的錯誤，先看能否消除雙重來源，或用現有型別、檢查與行為測試防止再犯；用真實反例確認檢查會失敗，修正後才通過。仍需判斷的約定再補文字，不把每次更正都累積成 prompt，也不為小錯重寫架構。

同一類錯誤出現第二次就是訊號（Anthropic 的建議是「被糾正兩次的事」才寫進 CLAUDE.md；一句規則一再加強語氣仍被忽略，就該改成 hook）。依序考慮：用架構讓錯誤無法發生，型別，檢查（lint、guard hook、`agf audit`），行為測試，最後才是文字。檢查的錯誤訊息寫成修正指示，讓讀到的 agent 知道該怎麼改，而不只知道錯了（OpenAI 的 harness engineering 做法）。來源與更多做法見 `docs/ecosystem/comparisons/agent-workflows.md` 與 `docs/ecosystem/articles.md`。

改框架的某項能力或引入外部工具之前，先查 `docs/ecosystem/` 有沒有研究過（`python -m agf.ecosystem find 關鍵字`），沿用已查過的結論，只補新資訊。文件裡寫的命令與行為會悄悄過期：`agf audit` 會檢查文件提到的 `agf` 子命令、選項與框架內路徑是否還存在（`agf/doccheck.py`；分析報告、驗證紀錄這類有日期的紀錄不檢查）；行為的描述要靠 `check --profile periodic` 重跑命令，或改框架時順手核對相關段落。

一般開發交給宿主能力。採納或新增 skill 前，先查已有哪個入口負責相同工作，優先改好現有位置；通用方法能用短偏好或既有工具完成時，不新增 skill、alias、router 或 provider。領域知識按需求連到官方專案要求，不維護另一份容易過期的規格／工具手冊。

修改名稱、description 或目的邊界時，用真實正反請求觀察選用；修改腳本時驗證行為與失敗副作用；文字小修直接校閱。只有相關變更才重跑對應檢查，不為每次維護安排完整儀式。格式 audit、腳本測試、代理行為與真人學習是不同證據。

修改配置或技能包時，在隔離目標核對部署的是本地修改版，且單項 skill 及 shared／copy 所需的 references、scripts 與相對路徑可用；不能拿遠端舊版或僅來源目錄可讀當作驗證。另從宿主可取得的紀錄確認實際載入，沒有載入紀錄時保留未知，不從回答風格推定。

需要判斷 skill 增益時，固定 host、model、材料和工具，先看沒有該 skill 的基準表現，再比較缺陷、返工、必要互動與可取得的實際用量。不用總字數、skill 數量或 AI 自評宣稱省 token。新依賴與共用 script 也要指出它比原生方法增加的實際價值。

保留有用的原始失敗與修正後結果，少量可續接的紀錄即可。評估案例見 [evals](../evals/README.md)；來源採納與未照搬處見 [research.md](research.md)。

更新 GitHub Actions 時，到官方倉庫核對版本標籤對應的完整 commit SHA，審查更新內容後，同步修改實際 workflow 與 `templates/github-actions.yml` 的固定值及版本註解；固定值不會自動取得安全修補。記錄本機能驗證的部分，遠端 runner 未執行就保留未知。

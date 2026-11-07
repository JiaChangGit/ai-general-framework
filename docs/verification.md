# 驗證紀錄

日期：2026-11-08（Asia/Taipei）。這份紀錄分開列出腳本、宿主整合、來源閱讀與真人學習的證據。

## 核心與跨平台

最終整體結果：

| 環境 | 執行 | 結果 |
|---|---:|---|
| Windows 原生，Python 3.13.15、Node 24.22.1 | 110 案 | PASS，無失敗；symlink 案因 WinError 1314 跳過 1 案 |
| Ubuntu-26.04／WSL，Python 3.14.4、Node 24.22.1 | 110 案 | PASS，無失敗、無跳過；symlink 案實際通過 |

Windows 用現有 Node；WSL 的 Node 來自官方 checksum 核對過的 tarball，只放在專案 `.agf/qa/node-linux/`，在該次測試程序的 PATH 使用。它不是核心依賴，也沒有修改全域 PATH。缺少 Node 時，兩個 plugin syntax／contract 案會明確 skip，其餘核心仍可測試。原始測試輸出與 JSON 結果保留在本機 `.agf/qa/`。

```console
python -X utf8 -m unittest discover -s tests -v
python scripts/agf.py audit
python scripts/agf.py check --root . --config templates/quality.framework.json --profile full
```

本輪也從 CLI 實際執行 WSL 的 `check --profile full`，unit-tests 與 framework-audit 兩個檢查皆 PASS。PowerShell 與 POSIX shell 的薄入口皆已實際執行 doctor。

案例涵蓋批次操作的預覽、碰撞、來源漂移、失敗回復、特殊字元與編碼；來源頁行、截斷與解碼狀態；task freshness；選擇性配置／更新／回復與既有檔保留；從目標專案執行 runtime；Git hook 實際呼叫共用品質檢查。

Windows 原生測試使用該平台的檔案 API，WSL 測試則使用 Linux API。這支持核心行為的跨平台證據，不能把某一端成功延伸成所有跨檔案系統、硬體或遠端環境都相容。Windows Git 對 WSL-owned UNC 目錄的信任限制仍由使用者判斷，工具不修改全域 safe.directory。

## 可選工具

| 能力 | 本輪證據 | 範圍 |
|---|---|---|
| Mermaid | 官方 12.3.0 bundle，透過既有 Playwright／Chrome 執行實際 render；flowchart、sequence、state 皆成功 | Flowchart 的中文字與分支標籤已檢視；包含特殊字元的三類圖做語法 probe。這不是所有版本的 mmdc 相容性保證 |
| draw.io | 產生未壓縮 XML，檢查 cell／parent／edge 引用 | 桌面 app 未安裝，未做原生 draw.io 匯出或視覺驗收 |
| PDF | pypdf 7.0.0 置於專案內隔離測試目錄；Windows／WSL 實際抽取自製單頁 PDF，確認文字與 page:1 錨點 | 核心環境缺少 pypdf 時仍正確回報 UNAVAILABLE；表格、公式、OCR 與大型真實 spec 未驗證 |
| 靜態網頁 | 10 個 localhost HTTPServer 案例，兩端通過 | 預覽、byte 上限、robots、redirect、覆寫與回傳 metadata；外部 example.com HTTPS 試抓遇到環境憑證鏈驗證失敗，工具回報錯誤且沒有發布頁面。外部成功擷取、登入及動態 JS 未驗證 |

實際 Mermaid 渲染找出了 sequence 標籤中 HTML entity 與分號的相容性問題；已改用官方語法的 Mermaid entity codes，再以同一引擎重驗。SVG 範例放在 `examples/diagrams/`。QA 依賴與臨時輸出放 `.agf/qa/`，未加入核心依賴或公開來源檔。

## Host、hooks 與 CI

四個 host 的 skills／規則部署以檔案配置及 target-runtime 測試驗證；未在四種真實模型 session 中量測自動觸發率。Doctor 的 executable discovery 不代表已登入或模型可用。

Git pre-commit 已在隔離專案透過真正 Git 呼叫，包含原始 source 搬走後繼續使用 target runtime 的案例。OpenCode plugin 的 Node syntax、V1/V2 callback 與真 Python quick check 以 fake-host fixture 驗證；真 OpenCode 內載入仍為 NOT_TESTED。其他 AI-host hooks 為版本相關的 review plan。它們不是 OS 或服務權限邊界。

GitHub Actions 與 GitLab CI 已提供共用檢查範本；遠端執行、runner 配置與受保護分支未驗證。Docker、K8s、QEMU、GDB 與 kernel upstream 流程提供範例／指引，未宣稱本輪完成相應部署、實機或 upstream 驗收。

## Skills 與學習

13 個 skills 通過官方 skill-creator validator，並另做靜態結構及連結檢查。一次獨立 forward-test 使用適當 skills 與最少原始材料，沒有讀教材解答：

- 佇列問題：實際重現錯誤回傳後仍留下工作的現象，提出最小修法，在記憶體中驗證七種情境。
- Spec 帶讀：依條文確認 duplicate 與 capacity 同時成立時的順序，直接提供完整情境說明。
- 小拼字修改：辨認為局部工作，沒有啟動 Grill Me、角色團隊或無關測試。

這是少量、低難度的 behavior smoke。佇列原始檔已包含故障提示及正確對照，不能當成盲測 RCA benchmark。真人理解、長期保留、一般化觸發率、成本及 token 改善比例皆未量測。擴充案例與重跑方式見[行為驗收](../evals/README.md)。

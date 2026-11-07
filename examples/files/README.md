# 先檢查檔案計畫

以下指令只預覽，不會改名或改寫內容。請複製範例到自己的測試資料夾，再試 `--apply`。

```text
python scripts/agf.py files rename examples/files/sample --pattern ^draft- --replace final-
python scripts/agf.py files normalize examples/files/sample --glob *.txt --from-encoding utf-8 --to-encoding utf-8 --newline lf
python scripts/agf.py files diff examples/files/before.json examples/files/after.json --format json
```

需要隔一段時間再執行時，使用 `--plan-output .agf/artifacts/rename-plan.json` 保存計畫，之後以 `files apply .agf/artifacts/rename-plan.json` 重驗和預覽，最後明確加 `--apply`。計畫只處理列出的來源；之後新增的檔案不會自動被納入，但若與目的檔名碰撞仍會阻止套用。

套用前會核對來源 SHA-256、檔名與大小寫碰撞，拒絕 symlink/reparse-point 路徑及覆寫。批次會暫存原件，過程拋出錯誤時嘗試回復；若程序被強制終止，`.agf-files-*` 目錄保留原件與 `plan.json` 供人工復原。請先停止其他會修改同一批檔案的程序；這不是跨程序鎖定機制。改名透過複製內容與基本 metadata 完成，不保證保留 hardlink 身分、所有 ACL 或延伸屬性。

編碼轉換採嚴格解碼，單檔上限 20 MB、單批新內容上限 100 MB。目錄比較使用內容 hash；文字比較會正規化讀入的換行；JSON 比較保留型別、空容器和 JSON pointer 路徑。

本地文件可以使用 `source inspect/excerpt/diff`，保留來源 hash 與實體頁／行號。PDF 需要已安裝的選用 `pypdf`；缺少時回報 `UNAVAILABLE`。HTML 只讀本地靜態文字，不執行腳本、不連網；動態網站應交給已授權且已存在的 MCP 或 browser 工作流程。文件差異是文字候選，不代表 spec 語意已經判定。

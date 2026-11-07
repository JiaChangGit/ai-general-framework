# 以同一份來源資料產生圖

`files-transaction.json` 依 `agf/files.py` 的 `apply_plan` 畫出簡化流程。它是原始碼導讀範例，沒有聲稱執行過某次檔案轉換。修改程式後，仍需核對圖中的節點和分支。

在專案根目錄執行下列指令。未指定 `--output` 時，只在 JSON 回覆中預覽內容。

```text
python scripts/agf.py diagram create examples/diagrams/files-transaction.json --format mermaid
python scripts/agf.py diagram create examples/diagrams/files-transaction.json --format drawio
python scripts/agf.py diagram create examples/diagrams/files-transaction.json --format drawio --output .agf/artifacts/files.drawio
python scripts/agf.py diagram validate .agf/artifacts/files.drawio --format drawio
```

Mermaid 的 `kind` 可用 `flowchart`、`sequence`、`state`。draw.io 產物使用未壓縮 XML，保留來源 metadata，提供基本節點與連線排列。結構檢查只核對 XML 和參照；圖是否清楚、箭頭是否符合程式，仍要看來源和實際畫面。

原生渲染器是選用工具；AGF 不會安裝它。以下先產生 Mermaid 檔，再預覽渲染工作；要執行時才加 `--execute`。輸出檔已存在會拒絕覆寫。

```text
python scripts/agf.py diagram create examples/diagrams/files-transaction.json --format mermaid --output .agf/artifacts/files.mmd
python scripts/agf.py diagram render .agf/artifacts/files.mmd --format mermaid --output .agf/artifacts/files.svg
```

Windows 的 npm `.cmd` shim 不會被當成 shell 指令執行。已有 Mermaid CLI 時，可以用實際 `node.exe` 搭配 `--tool-arg` 指定 CLI 的 JavaScript 入口；路徑依自己的安裝位置調整。

```text
python scripts/agf.py diagram render .agf/artifacts/files.mmd --format mermaid --output .agf/artifacts/files.svg --tool C:/tools/node/node.exe --tool-arg C:/tools/mermaid/src/cli.js --execute
```

draw.io 可用 `--format drawio --tool <原生執行檔>`。CLI 的退出碼與非空輸出會被檢查；排版仍須人工檢視。Adapter 的自製 renderer fixture 與實際引擎驗證分開記錄，見[驗證紀錄](../../docs/verification.md)。

這份範例已保留 [Mermaid 原始檔](files-transaction.mmd)、[draw.io 原始檔](files-transaction.drawio)及使用官方 Mermaid 12.3.0 引擎產生的 [SVG](files-transaction.svg)。下圖說明已核對的簡化控制流：

![批次操作交易流程](files-transaction.svg)

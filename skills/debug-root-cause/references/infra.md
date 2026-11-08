# CI、Docker 與 Kubernetes 的故障定位

先確定故障在哪一層，再選工具，避免一開始同時修改程式、image 和部署設定。

- **CI：** 記錄 workflow、run、attempt、commit、runner 和失敗 step。區分測試缺陷、環境差異、權限、依賴下載與 artifact 問題。重新執行後成功只能顯示結果改變，不能自行解釋 flaky 的原因。
- **Docker：** 分開確認 image build、entrypoint、程序退出、檔案/權限、網路與掛載。核對實際 image digest 及執行設定，避免分析到不同版本。日誌與 inspect 輸出先移除憑證再分享。
- **Kubernetes：** 先核對 cluster context 與 namespace，再看 workload、pod、events、前次容器日誌、探針、資源、設定及網路。從 image pull、排程、啟動、就緒或請求處理的第一個偏離縮小範圍。

每次操作前辨認副作用。刪 pod、restart、清 cache、重新部署或更改資源限制都會改變現場；保留可取得的相關證據，且只能在本次授權內操作。

重大故障持續擴大影響時，依既有授權先提出或執行可回復的緩解，不為等待完整根因而延誤恢復。沒有操作授權就交付具體方案，停在執行前。服務恢復只支持緩解有效，根因仍須後續驗證；一般小 bug 不必升級成事故流程。

驗收依原始故障而定：設定可解析、build 成功、pod Ready、實際請求成功和負載下穩定是不同證據，回報時分開說明。

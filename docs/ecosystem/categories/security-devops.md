# CI/CD、資安與授權工具

<!-- ecosystem:table security-devops -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [zizmor](https://github.com/zizmorcore/zizmor) | CLI | 1 | 可使用（MIT） | 2026-11-21 | 讀文件 | GitHub Actions、Dependabot 與 pre-commit 設定的安全靜態分析：模板注入、憑證殘留、過寬權限、冒名 commit 與可混淆的 git 參照。 |
| [actionlint](https://github.com/rhysd/actionlint) | CLI | 2 | 可使用（MIT） | 2026-07-16 | 只有搜尋摘要 | GitHub Actions workflow 的靜態檢查：語法、表達式型別、shellcheck 整合。 |
| [GitHub Actions](https://docs.github.com/en/actions) | 服務 | 2 | 可使用 | — | 只有搜尋摘要 | GitHub 的 CI／CD 服務，以 YAML workflow 與可重用 Action 組成。 |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | CLI | 2 | 可使用（MIT） | 2026-10-28 | 只有搜尋摘要 | 掃描 git 歷史與檔案中的祕密（API key、token），可當 pre-commit hook。 |
| [OSV-Scanner](https://github.com/google/osv-scanner) | CLI | 2 | 可使用（Apache-2.0） | 2026-11-20 | 只有搜尋摘要 | 用 OSV.dev 資料庫比對鎖檔與 SBOM 中的相依漏洞。 |
| [pre-commit](https://github.com/pre-commit/pre-commit) | CLI | 2 | 可使用（MIT） | 2026-11-09 | 只有搜尋摘要 | 管理 git hook 的框架，用 .pre-commit-config.yaml 指定各 repo 的 hook 與版本。 |
| [Prompt injection 防護（實務與工具）](https://owasp.org/www-project-top-10-for-large-language-model-applications/) | 文章 | 2 | 可使用 | — | 只有搜尋摘要 | OWASP 的 LLM 應用 Top 10 把 prompt injection 列為首位風險；防護核心是權限最小化、把外部內容當資料、人工確認高風險動作。 |
| [ScanCode Toolkit](https://github.com/aboutcode-org/scancode-toolkit) | CLI | 2 | 需人工確認（Apache-2.0（程式碼）；授權規則資料庫另有條款（需核對）） | 2026-11-20 | 只有搜尋摘要 | 掃描原始碼找出授權、著作權聲明與相依套件，輸出 JSON／SPDX／CycloneDX；AboutCode 專案（原 nexB）。 |
| [Snyk Agent Scan（原 mcp-scan）](https://github.com/snyk/agent-scan) | CLI | 2 | 有條件（Apache-2.0） | 2026-11-19 | 讀文件 | 發現本機的 agent 元件（harness、MCP server、skill）並掃描 prompt injection、敏感資料處理與惡意負載。 |
| [Trivy](https://github.com/aquasecurity/trivy) | CLI | 2 | 有條件（Apache-2.0） | 2026-11-20 | 只有搜尋摘要 | 容器映像、檔案系統、IaC 與 SBOM 的漏洞、設定、祕密掃描器。 |
| [act](https://github.com/nektos/act) | CLI | 3 | 可使用（MIT） | 2026-11-19 | 只有搜尋摘要 | 在本機用 Docker 執行 GitHub Actions workflow。 |
| [Cisco MCP Scanner](https://github.com/cisco-ai-defense/mcp-scanner) | CLI | 3 | 可使用（Apache-2.0） | 2026-11-19 | 讀文件 | 掃描 MCP server 與工具的 CLI／REST：YARA 規則、LLM 分析、Cisco AI Defense API 三引擎，可離線靜態掃描 JSON。 |
| [Dependabot](https://docs.github.com/en/code-security/dependabot) | 服務 | 3 | 可使用 | — | 只有搜尋摘要 | GitHub 內建的相依更新與漏洞警示，設定檔 .github/dependabot.yml。 |
| [GitLab CI／CD](https://docs.gitlab.com/ee/ci/) | 服務 | 3 | 需人工確認 | — | 只有搜尋摘要 | GitLab 內建的 .gitlab-ci.yml 管線，可自架 runner。 |
| [licensee（GitHub 的授權偵測 gem）](https://github.com/licensee/licensee) | CLI | 3 | 可使用（MIT） | 2026-11-20 | 只有搜尋摘要 | Ruby 函式庫：比對 LICENSE 檔案與已知授權範本，GitHub 授權欄位背後的偵測引擎。 |
| [OSS Review Toolkit（ORT）](https://github.com/oss-review-toolkit/ort) | CLI | 3 | 可使用（Apache-2.0） | 2026-11-20 | 只有搜尋摘要 | Kotlin／JVM 的供應鏈合規流水線：分析相依（analyzer）→ 掃描授權（scanner，可接 ScanCode）→ 評估規則（evaluator）→ 報告（reporter）。 |
| [OWASP Dependency-Check](https://github.com/dependency-check/DependencyCheck) | CLI | 3 | 可使用（Apache-2.0） | 2026-11-20 | 只有搜尋摘要 | 以 CPE 比對相依與 NVD 漏洞，Java 生態成熟。 |
| [Renovate](https://github.com/renovatebot/renovate) | 服務 | 3 | 有條件（AGPL-3.0） | 2026-11-21 | 只有搜尋摘要 | 自動開 PR 更新相依與 GitHub Actions 的 SHA；可自架或用 Mend 託管 app。 |
| [REUSE（fsfe/reuse-tool）](https://github.com/fsfe/reuse-tool) | CLI | 3 | 需人工確認（GPL-3.0／Apache-2.0／CC-BY-SA／CC0 混合（REUSE 專案自身採多授權；GitHub 回報 none）） | 2026-11-01 | 只有搜尋摘要 | FSFE 的 REUSE 規範工具：檢查每個檔案都有 SPDX-License-Identifier 與著作權標頭，lint 並產生 SPDX 物料清單。 |
| [Semgrep（CE）](https://github.com/semgrep/semgrep) | CLI | 3 | 有條件（LGPL-2.1） | 2026-11-20 | 只有搜尋摘要 | 以語法樹模式比對的靜態分析，規則用 YAML 寫，支援多語言。 |
| [Syft 與 Grype（Anchore）](https://github.com/anchore/syft) | CLI | 3 | 可使用（Apache-2.0） | 2026-11-20 | 只有搜尋摘要 | Syft 產生 SBOM（SPDX、CycloneDX）；Grype 用 SBOM 或映像找漏洞。 |
| [〈你知道嗎：vibe coding 做的 app，資安要從哪裡顧起？〉（人蔘 Try Catch ep091）](https://ginseng.dnplus.dev/blog/ep091) | 文章 | 3 | 可使用 | — | 讀文件 | 用永豐銀行、91APP、幣安三起 2026 事件講資安三段（事前、事中、事後）與三個 A（認證、授權、稽核）；示範每講一個名詞就跑一次 pstack 的 teach，讓 AI 用自己的專案（PA Cafe）舉例。 |
| [FOSSology](https://github.com/fossology/fossology) | 服務 | 4 | 可使用（GPL-2.0） | 2026-11-17 | 只有搜尋摘要 | 授權合規 Web 服務：上傳原始碼、掃描授權與著作權、人工確認、產生報告（SPDX、ReadMe_OSS）。 |
<!-- /ecosystem -->

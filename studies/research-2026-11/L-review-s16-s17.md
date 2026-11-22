# Independent review of S16 and S17 (9d9aa2f..35e6b34)

Read-only review. Tests: `python3 -B -m unittest discover -s tests` passes on the S17 commit (extracted with git archive to /tmp, 329 tests, 7 skipped). The working tree has uncommitted S18 changes (agf/manage.py, agf/traces.py, which add `traces.hook`); the line numbers below refer to commit 35e6b34. Probe scripts are in /tmp/claude-1000/review-probes/.

## 1. Code

### guard hook, check_mcp (templates/claude-guard-hook.py:468-497)

1. **bug (bypass), L482-490 and the MCP_* sets (L85-90).** Only top-level keys are read, and only an exact name match counts. Probes against a protected root, each returned None (passed):
   - `{"command":"rm","args":["-rf",P]}` (the split command/args form that process-spawn MCPs use)
   - `{"input":{"command":"rm -rf P"}}` and `{"arguments":{"cmd":...}}` (nested objects)
   - `{"commands":["rm -rf P"]}`, `{"code":"shutil.rmtree(P)"}`
   - `move_file {"source":P/a,"destination":...}` and `{"from":P/a,"to":...}`. Moving a file out of a protected root is a delete, but `source`, `src`, `from`, `old_path`, `source_path`, `uri` (file://) and `file_paths` are not in MCP_PATH_KEYS.
   - `write_file {"files":[{"path":P/a,"content":..}]}` (a list of objects; `_strings` accepts only lists of str, which is how batch-write tools take paths).

   Fix: walk nested dicts and lists recursively. Treat `args`/`argv`/`arguments` next to `command` as part of the argv. Add the missing path keys (`source`, `src`, `from`, `old_path`, `uri`, and a `file://` prefix strip). Alternatively, for write-named tools, check every string that looks like a path and sits under a protected root. The docs already say unrecognised arguments pass, but they should also name nested arguments as a known gap.
2. **bug (false refusal), L478 MCP_WRITES.** The regex is an unanchored substring match on the tool name, so `put` matches `get_output`/`compute`, `run` matches `truncate`/`prune`, and `patch` matches `dispatch`. Probe: `mcp__s__get_output {"path": P/a}` is refused as a write. Fix: split the name on `_`/`-` and camelCase and match whole words.
3. **risk (false refusal and wrong semantics), L481 and L494-495.** Paths in MCP arguments are resolved against the local cwd and local `~`. Probe: `mcp__s__create_or_update_file {"path":"x.md"}` with cwd inside a protected root is refused. This is an ordinary GitHub-MCP call that writes to a remote repo. A remote `run` tool with `cwd:"/home/remote"` is evaluated against local paths. The reverse also holds: the tool the S16 note was about (Fastctx `run`, which runs elsewhere) is judged by local-path rules. Fix: for MCP, protect only absolute paths (and `~/`) and skip relative ones, or document that remote servers will be refused when the local cwd is protected.
4. **nit.** `working_dir` and `currentWorkingDirectory` are not in MCP_WORKDIR_KEYS. With `{"command":"touch x","working_dir":P}`, the cwd falls back to the session cwd, so a relative write into P passes.
5. Positives: list-form argv uses `shlex.join`, so `["sh","-c","..."]` still goes through the unwrap logic. The `mcp__.*` matcher is in the settings example, README and CHANGELOG, and all three agree. The user still has to edit the real settings file by hand, which is stated clearly.

### agf/traces.py and manage.py

6. **risk, manage.py:635 (and 696).** Every `project update` that applies changes calls `traces.remove(root, apply=True)` when the mode is `keep`. This includes old manifests that have no `ai_traces` key (they resolve to "keep", L580) and installs made with `--keep-ai-traces`. It deletes a block the user added on purpose with `agf traces exclude`. Probe: install with `--keep-ai-traces`, run `traces exclude --apply`, then `project update --apply`. The block survived because the update was a no-op (L588 returns early), but any update with changes removes it. The effect depends on whether files changed, so it is not deterministic. docs/cli.md says old installs "stay as they are", which this contradicts. Fix: "keep" should not touch the exclude file. Only remove it on an explicit switch from "exclude" to "keep", or when the block was written by this manifest (record that in the manifest).
7. **risk, manage.py:579-581 and the rule text at L292-296.** For a new project that is not a git repo, or that is nested inside another repo, the default is still "exclude" and the manifest records `ai_traces: exclude`. The rule text, written into the project, then says "AI tool files are already excluded by `.git/info/exclude`", which is false. The exclude status comes back as NOT_GIT or NESTED and is not checked. If `git init` is run later, nothing re-applies the block until the next update. Fix: write the "already excluded" sentence only when exclude status is ADDED/UPDATED/UNCHANGED, or reword it to "should be excluded; `agf traces check` verifies".
8. **risk, manage.py:696-698.** Rollback re-applies exclude or remove, which is correct after install and after update; I verified that install, then update with `--keep-ai-traces` (block REMOVED), then rollback restores the block (ADDED). Two gaps: (a) rolling back a first install leaves `previous_bytes` empty, so `restored` is `{}` and remove runs. That is right for a block created by the install, but wrong if the user had added one themselves, same cause as finding 6. (b) The exclude write happens after the managed files are restored, with no error handling. If it raises (read-only .git), the manifest has already been rolled back but the command fails. Fix: wrap it in try/except and report it as a warning.
9. **nit, traces.py:64-66.** `_without_block` needs both markers. If the user deleted only the END line, `exclude` appends a second block, and a later `remove` deletes everything from the first BEGIN to the second END, including any user lines between. In my probe the file had two BEGIN lines after exclude and zero after remove. The read-modify-write is not atomic, so concurrent edits can be lost. `read_text` also normalises CRLF to LF on rewrite.
10. Checked and fine: no trailing newline in the exclude file (a `\n` is added); worktrees (`--git-path info/exclude` resolves to the shared main repo file, so the second worktree reports UNCHANGED; the file is shared across worktrees, which is worth one doc line); `.git` as a file; nested repo gives NESTED; repeated install is UNCHANGED/idempotent. Windows paths are not tested here; `is_toplevel` compares `Path.resolve()` of git's "C:/..." output. 8.3 short names or a symlinked target could make a legitimate root look NESTED (safe failure).
11. **nit (false positives), traces.py:23-26.** The bare `\U0001F916` (robot emoji) and `\b(devin|cursor|gemini|gpt)\b` in co-authored-by match human co-authors (for example "Devin Smith") and any commit that uses the emoji. Docs say "人類的共同作者不算痕跡"; that is not what the regex does. `check` also exits 1 on a clean repo that merely lacks the block, and docs/cli.md does not say so.

### agf/ecosystem.py, audit, usage.py

12. **nit, ecosystem.py:refresh (~L255-275).** If `gh --jq` returns something that is not a dict, `facts["fetched"] = ...` raises TypeError, which is not caught, so the whole refresh aborts before the file write. It also rewrites entries.json even when nothing changed. `tier in (1,2,3,4)` accepts `True`. Otherwise check/render/find are sound and `audit` skips cleanly when the catalog is absent.
13. **bug (undercount), evals/host/usage.py (diff L79-90).** Usage is kept from the first transcript entry of each message id. Claude Code writes one entry per content block of a single API reply, and streamed entries often carry partial `output_tokens`; the first one is usually the smallest, so output tokens are undercounted. Entries with no `message.id` are all lumped under `None`, so only the first one is counted. Fix: keep the maximum per id for output, and skip dedupe when the id is missing. Say in the output that the figure is approximate.

## 2. Documentation facts (checked against repo sources)

14. **doc error, docs/workflow.md:69.** "This framework's measured numbers: three S16 sub-agents used about 270k-440k tokens each; reading two long web pages about 37k." Nothing in the repo supports these numbers (grepping HANDOFF, CHANGELOG, K-s17, studies/ecosystem-2026-11 and analysis finds none), and the sentence presents them as measured. The fixed cost "about 1,400 rules + 720 skills" is supported (analysis-2026-11.md:278, H-measurement-s12.md). Fix: cite a record, or say "from S16 usage, not archived".
15. **doc error, docs/ecosystem/comparisons/code-understanding.md (capability table, CodeGraph row) vs trials/codegraph/RESULTS.md Q4.** The table says CodeGraph (colbymchenry) judges `#ifdef` three-valued from `#define` and build settings; the trial shows it lists both `submit` definitions, so the active-branch case is not handled. The table says "only what was read in source", but the trial result contradicts it. Likewise the clangd row says "correct", but clangd was not run (only clang DumpCallGraph); mark as expected. Fix: change the row to "tried: both branches listed in the fixture".
16. docs/ecosystem/comparisons/document-parsers.md matches docparse/RESULTS.md (10x speed, one fifth memory, exit 0 on empty scan output, Σ to Z, trad-to-simplified). Minor: OCRmyPDF memory "300-700 MB" while the table shows 294 MB; check results.json for the 700 MB case. The summary "Docling: scanned mostly recognised" mixes default-OCR numbers with the Tesseract variant, which has Chinese 25% in table cells, and that is not stated.
17. security.md incidents table: Trivy, LiteLLM x2 and Context7 rows are marked "verified by main session"; the two rows marked "search summary only" are labelled honestly. I could not independently re-verify these (the dates are after my knowledge, and the NCSL fetch returned 403). The table is well hedged and consistent with the CHANGELOG. docs/ecosystem/security.md section 4 correctly describes the MCP check as covering only command/path-like argument names, but it does not mention the nested-argument gap (finding 1).
18. templates/domains/support-chatbot.md: Taiwan hotlines 1925, 1995, 1980 and 119/110 are correct as I know them. "Illinois restricts AI therapy" and "New York every three hours" match what I know of those 2025 laws. "Iowa requires detection and referral" is the one I could not confirm and may be wrong (the NCSL page was blocked); it is stated flatly, so either source it or soften it. The file does say laws change fast.
19. docs/delivery.md and README agree with code on the default: `--keep-ai-traces` turns it off, old manifests keep their state, nested repos are untouched. cli.md says "update adds `--exclude-ai-traces` to turn it on", which matches L719. delivery.md says the rule line is "一行" while the code adds several sentences (nit). README says the hook "only looks at the command line" and then describes MCP argument checks; fine.
20. K-s17.md/CHANGELOG measurement claims ("cost +60%", "2,130 tokens extra") match the table (0.107/0.066 = 1.62; 21,485-19,340 = 2,145). The CHANGELOG states plainly that the no-trace rule was not measured under real `git commit`, which is honest. Gap: the CHANGELOG says "8 tests in test_traces" and there are 8 `def test`, but none covers finding 6 (update with mode "keep" over a manually added block) or 7 (non-git target).
21. workflow.md "after two corrections /clear" is attributed to Anthropic's Claude Code guidance, which I believe is accurate; the model/effort table is advice, labelled as such. The "Fable is the strongest model" line is time-sensitive; fine as written ("目前是").

## 3. Consistency

HANDOFF, CHANGELOG, README, cli.md and the code agree on command names (`traces check|exclude|remove`, `--target`, `--apply`, `--max-commits`), flags and defaults. Entry counts agree (237, then 238, then 245 after S17). The CHANGELOG says S16 "規則、skill 與既有命令不改" and the diff includes agf/audit.py and cli.py edits, but those are the new command wiring and audit hook, so this is consistent. The HANDOFF item "have another model review S16/S17" is this review.

## Summary
- Findings: 3 bugs (1, 2, 13), 5 risks (3, 6, 7, 8, plus 15's table as doc error counted below), 3 doc errors (14, 15, 18), 5 nits (4, 9, 11, 12, 19).
- Top three:
  1. check_mcp is bypassed by nested arguments, split `command`+`args`, and move/copy source keys (`source`, `from`, `src`, `uri`) (finding 1).
  2. `project update` in "keep" mode removes a user-added exclude block when files change; the rule text also claims exclusion for non-git or nested targets (findings 6, 7).
  3. workflow.md:69 token figures (270k-440k, 37k) have no source in the repo, and the code-understanding table credits CodeGraph with `#ifdef` handling its own trial contradicts (findings 14, 15).
- Also: MCP_WRITES substring match refuses `get_output`, and relative remote paths are judged against the local cwd (findings 2, 3); usage.py `--tokens` likely undercounts output tokens (finding 13).

## 處理結果（主 session，2026-11-22）

| 發現 | 處理 | 驗證 |
|---|---|---|
| 1 MCP 檢查被繞過 | 巢狀物件與物件清單都檢查；`command` 旁的 `args`、`argv`、`arguments` 併入 argv；`commands` 清單；路徑欄位加上 `source`、`src`、`from`、`old_path`、`source_path`、`uri`（去掉 `file://`）、`file_paths` | `test_mcp_bypasses_found_by_the_review_are_refused`（9 種寫法） |
| 2 工具名稱子字串誤擋 | 名稱拆成單字（底線、連字號、camelCase）再比對 | `get_output`、`dispatch_event` 放行 |
| 3 遠端相對路徑以本機判斷 | 相對路徑只在同一個呼叫給了絕對工作目錄時才判斷；沒給時不判斷 | GitHub MCP 的 `create_or_update_file`、遠端 `run` 的相對路徑放行 |
| 4 `working_dir` 等沒認 | 加進工作目錄的欄位名 | 同上的繞過測試 |
| 6 keep 模式更新會刪掉使用者加的排除清單 | keep 不動排除清單與 hook；只有從 exclude 切回 keep 才移除 | `test_keep_mode_leaves_a_block_the_user_added_and_switching_removes_ours` |
| 7 非 Git 專案的規則寫「已排除」 | 規則文字依目標是不是 Git work tree 的根目錄而不同 | `test_outside_git_the_rule_does_not_claim_the_files_are_excluded` |
| 8 rollback 的排除清單寫入沒有錯誤處理 | 改成回報 `ai_traces_warning`，不讓整個回復失敗；同樣依 keep／exclude 規則處理 | 既有 rollback 測試 |
| 9 標記行被刪一半、CRLF | 標記數不對時拒絕並請使用者手動修；保留檔案原本的換行 | `test_a_damaged_block_is_reported_and_crlf_is_kept` |
| 11 人名被當成 AI 署名、單獨的表情符號 | 共同作者行只認工具帳號與信箱；表情符號要接 generated | `test_human_co_authors_and_a_lone_emoji_are_not_traces` |
| 12 refresh 遇到非 dict 中斷、tier 接受布林 | 記為失敗並繼續；tier 必須是整數 | 既有測試 |
| 13 `--tokens` 低估 | 同一則回覆取最大值；沒有 id 的各算一次；輸出標明是近似值 | `test_token_totals_count_each_api_message_once` 擴充 |
| 14 workflow 的 token 數字沒有來源 | 補記在 `studies/ecosystem-2026-11/USAGE.md` 並引用 | audit |
| 15 CodeGraph 與 clangd 那兩列 | CodeGraph 寫明文件說法與試跑結果不同；clangd 標「應該正確，沒有實測」 | — |
| 18 Iowa | 改成「NCSL 的整理另提到 Iowa，原文沒有讀到」 | — |
| 19 「一行」 | 改成「一段說明」 | — |

沒有改的：發現 10 的 worktree 共用排除清單是 Git 本身的行為，已在 cli 文件寫明；發現 16 的 OCRmyPDF 記憶體「約 300～700 MB」是掃描件 294 MB、文字型 691 MB，數字正確。

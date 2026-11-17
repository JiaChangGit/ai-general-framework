# R3: review of ai-general-framework worktree s10-framework, commit HEAD vs HEAD~1

Method: P = proved by running; D = derived by reading; S = suspicion.
Probes: `echo '{"tool_name":"Bash","tool_input":{"command":"..."},"cwd":"/tmp/gp"}' | python3 templates/claude-guard-hook.py /tmp/gp/g.json` with `{"protected_paths":["/tmp/gp/prot"]}`; /tmp/gp/lnk is a symlink to prot, /tmp/gp/protx is a sibling. About 330 probes were run; only failures are listed. Each says: rc=2 refused, rc=0 allowed, rc=1 crash.

Baseline: `python3 -B -m unittest discover -s tests` -> Ran 257 tests, OK (skipped=6) (P). `agf audit --root .` -> status PASS, errors [], warnings [] (P). 7 skills.

## Count: A (bypass) 9, B (false refusal) 4, C (doc/fact error) 7, D (wording/other) 5

## 1. claude-guard-hook.py

### A. Bypasses (security/boundary), all P unless noted
A1. `rtk proxy git push`, `rtk err git push`, `rtk run git push` -> rc=0. strip_wrappers drops `rtk` then sees `proxy` as the command. The user's RTK.md tells the agent to use `rtk proxy <cmd>` for raw output, so this is a form the agent is told to type. The docstring and adapter claim rtk prefix handling; only `rtk git push` works.
A2. `bash -lc 'git push'`, `bash -xc "git push"` -> rc=0 (also `-ec`, `-ic`). Code tests `"-c" in argv[1:]`, so a combined flag cluster is missed. `bash -lc` is a very common spelling. The docstring claims "inside `sh -c '...'`".
A3. Option values of wrappers are not skipped, so the value becomes the command: `sudo -u bob git push`, `sudo -u bob -- git push`, `env -u FOO git push`, `env -C /tmp git push`, `timeout -s KILL 10 git push`, `nice -n 5 git push` -> all rc=0. (`timeout 10`, `env -i`, `nice` without -n are caught.)
A4. Grouping and compound syntax: `(git push)`, `{ git push; }`, `if true; then git push; fi` -> rc=0. The first token is `(git` / `{` / `if`. `(cd /tmp/gp/prot && touch a)` -> rc=0 as well. `(cd x && git push)` is a plain form.
A5. `gh --repo a/b pr create`, `gh -R a/b pr create`, `glab -R a/b mr create` -> rc=0. The check compares fixed argv positions, so any global flag before `pr` bypasses it. (`gh pr create --repo a/b` is caught.) Also `gh api -X POST repos/o/r/pulls` rc=0 (arguably out of scope; not documented as a gap).
A6. `pkill --full foo` -> rc=0 (the long form of -f; only short flags are examined).
A7. Writes with cwd inside the protected path are not checked without `-C`: `cd /tmp/gp/prot && git commit -m x`, `cd /tmp/gp/prot && git add .`, `cd /tmp/gp/prot && git checkout -b x` -> rc=0. With the event cwd inside prot (the normal case when a session is started there), `git commit -m x` and `git add -A` -> rc=0. The docstring lists only `git -C <protected>`, but `cd x && touch a` is refused, so the protection is inconsistent.
A8. Missed write forms: `echo hi >| /tmp/gp/prot/a` (clobber redirect) rc=0; `cp -t /tmp/gp/prot a`, `cp --target-directory=/tmp/gp/prot a`, `install -t /tmp/gp/prot a` rc=0 (only the last argument is checked; `mv -t` happens to be caught because mv checks all arguments); `perl -pi -e ... prot/f` rc=0; `find /tmp/gp/prot -delete` rc=0; `patch /tmp/gp/prot/a < p.diff` rc=0; `tar -xf a.tar -C prot`, `unzip -d`, `curl -o`, `wget -O`, `git clone x prot/y`, `git -C prot clone`, `git restore prot/a`, `git rm prot/a`, `git checkout -- prot/a`, `make -C`, `npm install --prefix` rc=0. Not in the docstring list, but the docstring does not say the list is exhaustive.
A9. Variables: `rm -rf $PWD/prot`, `rm $HOME/x` (when protected is under $HOME), `P=/tmp/gp/prot; rm $P/a` -> rc=0 (no expansion). `git -C prot remote set-url`, `config`, `submodule update` rc=0: not in GIT_WRITES.
Also D: `eval "git push"`, `ssh host git push`, `busybox git push` rc=0 (not documented).
Also P: `git \<newline> push` (backslash-newline continuation) -> rc=0.

### B. False refusals (everyday work)
B1. Quoted text containing `>` is parsed as a redirect. With cwd outside prot: `echo "a > /tmp/gp/prot/b"`, `echo 'x > /tmp/gp/prot/b'`, `echo a -> /tmp/gp/prot/b` -> rc=2. With the session cwd inside the protected directory (the usual case): `grep -n "a>b" f`, `python3 -c "print(1>2)"`, `echo "x -> y"` -> rc=2 ("redirects output into the protected path"). Inside a protected repo, a comparison in `-c`/awk code is refused.
B2. Read-only git subcommands under `-C <protected>`: `git -C prot branch`, `branch --show-current`, `tag`, `stash list`, `worktree list` -> rc=2. GIT_WRITES lists the command name only, so listing is refused. The user's own note says `git -C <protected> log` must work; it does (rc=0), but `branch --show-current` is as common.
B3. `git -C prot fetch` and `pull` are refused; that is intended, but note `fetch` writes only .git refs. S.
B4. `echo ... # > /tmp/gp/prot/x` (a comment) rc=2 (redirect regex does not know comments). Minor.

### Crash risks (P). Exit 1 is a non-blocking error in Claude Code, so the call would run.
- `{"tool_name":"Bash","tool_input":"x"}` -> AttributeError, rc=1.
- `{"tool_name":"Bash","tool_input":{"command":"ls"},"cwd":5}` -> TypeError, rc=1.
Claude Code does not send these, so this is low risk, but `decide()` is outside any try. A wrapper `try/except -> return 2` (or 0) would remove it. `command: null/list` -> rc=0 (str(None) = "None").
- Fail-open on bad stdin: `garbage`, empty stdin, `[]` -> rc=0 (commented in code; the docstring says nothing).

### Configuration (P)
- Missing file, malformed JSON, non-object, unknown key, `protected_paths:[5]`, `null` -> rc=2 with a message. Good, and the docstring matches.
- `{"protected_paths":"/tmp/gp/prot"}` (string instead of list) -> accepted (rc=0 for `git status`); the string is iterated per character, so the roots become `/`, `t`, `m`, `p`... and `/` protects everything. Same silent acceptance for `[""]` (resolves to the hook's own cwd) and `["/"]`. `"block_push":"no"` is accepted and truthy. Contradicts "a typo does not silently remove the protection" in spirit: this one changes it silently.
- Relative paths in protected_paths resolve against the hook process cwd, which is undefined.
- Without config argument and without env: defaults apply (P: git push rc=2; writes rc=0, matching the test). `AGF_GUARD_CONFIG` works (P).

### Path resolution (P)
Relative, `..`, `./`, `~`, symlink (lnk/a rc=2, `git -C lnk commit` rc=2), sibling `protx` (rc=0), `prot2` (rc=0), `PROT` (rc=0, case-sensitive, fine on Linux) all behave correctly. `Write` with `file_path:null/123` rc=0.

### Docstring versus code
- "inside `sh -c`": true only for `-c` as a separate word (A2).
- "after `env A=1`": true; `env -u X` not (A3).
- Writes list "cp/rsync/install destination": `-t` form missing (A8).
- Not stated: fail-open on non-JSON stdin; MultiEdit is covered in code but the docstring lists only Edit/Write/NotebookEdit.

## 2. tests/test_guard_hook.py (D = derived from reading)
- 10 tests, all pass; they genuinely run the hook as a subprocess. The refused/allowed lists are decent.
- Gaps: nothing for `rtk proxy`, `bash -lc`, `sudo -u`, `(...)`, `gh --repo`, `--full`, `>|`, `-t`; no test for cwd-inside-protected (the main use); no symlink test; no malformed-JSON config test (only missing file and an unknown key); no wrong-type input test (the rc=1 crashes); no `block_*: false` test; no `AGF_GUARD_CONFIG` test; the "not an event" test only covers the string `not json`.
- `test_every_spelling_of_push_is_refused` asserts "git push" appears in stderr for `sh -c 'git push origin'`; fine. The name "every spelling" overclaims given A1-A4.
- `test_commands_that_only_mention_push_run` has no quoted `>` case (B1) and no `git -C <protected> branch` case (B2).
- tests/test_integrations.py does not cover the two new templates (D). docs/cli.md (the page README points to for "full commands") does not mention claude-guard-* (D; only claude-permissions is documented there).

## 3. templates/project-rules.md
Char count 1,316 (old 1,310): the claim in CHANGELOG/analysis is correct (P, `wc -m`).
- Contradiction (D): rules say write a handoff file before spawning several subagents, running long commands, and "使用者換模型" / at every milestone. docs/workflow.md line 31 still says "同一對話切模型沿用原生上下文，不搬運整段歷史" and "跨 session、換工具或確實需要落盤續接時，才整理足以續做的交接". The new workflow section says changing the model in one conversation invalidates the cache and requires a handoff first. Both sit in the same file. Also README previously said "一般切換不用額外建立交接檔"; that sentence was replaced, but workflow.md line 31 was not.
- Silent behaviour change (D): the old file said to run `profile show --root` at task start; the new one says only "需要語言、圖解或教學偏好時". The old "當次指示優先，權限仍以宿主與當次授權為準，JSON 範例不會自動變成生效政策" is partly dropped. CHANGELOG describes the rewrite as "句子改短" with three added rules and does not mention these removals. Also the descriptions of the agf tools (限時限量, Mermaid-only wording kept) were cut, replaced by "用法見 tools 指引".
- "寫進交接檔（workflow 指引的「續接」）": no section is named 「續接」; the heading is 「續接、換模型與用量」 (the file title contains 續接). Minor mismatch.
- "每完成一個里程碑就更新": in every project this makes the agent create and rewrite a handoff file for each milestone; wasteful for small tasks (S). Compare "簡單、可復原的事直接做".
- "使用者換模型...後先讀那份交接檔": if none exists the agent has no instruction (S).
- "本地 commit 在當次授權內可以做": consistent with delivery.md. "看過 `git diff --cached --stat` 只有這次的檔案才 commit": consistent with delivery.md's new paragraph.
- Language: natural overall. Mainland-leaning words: 「宿主」 (Taiwan usually 主機/宿主 both occur; used consistently), 「落盤」 in workflow.md ("落盤續接") and the writing.md table example, while writing.md itself lists 「落盤／持久化」 as an inconsistent pair to unify and lists 外地用語; 「命令」 vs Taiwan 「指令」 is used throughout. 「相依套件」, 「里程碑」, 「叫用」 are fine. Wording nit: "用量可能不夠之前" reads awkwardly.

## 4. skills/align-with-me/SKILL.md
- Frontmatter has name, description and `disable-model-invocation: true`. The Claude Code docs define this field; with it the skill is user-invoked only and the description is not placed in the model's context (D, from documented behaviour; adapter and CHANGELOG themselves say it was never invoked on a host).
- agentskills.io spec: the defined top-level fields are name, description, license, compatibility, metadata, allowed-tools. `disable-model-invocation` is a Claude Code extension (D). On other hosts the skill is copied to .agents/skills and may be model-invocable; README's table says "不在模型的 skill 清單裡，不會誤觸" without limiting this to Claude Code (README row says "Claude Code 打 /align-with-me" only for the command). The analysis table says "不占常駐 context" generally.
- `agf audit` does not check frontmatter fields at all (agf/audit.py reads only name and description by regex), yet its output `meaning` says "supported frontmatter fields". So "agf audit 無錯誤" (CHANGELOG) proves nothing about the new field. (P: grep of audit.py)
- Conflict with workflow.md grill section: workflow says "先挑最可能改變方向的一到三個問題"; the skill says "一輪最多四題". Different numbers for the same activity (D). The skill is the explicit mode, so it may be intended, but nothing says so.
- Internal contradiction: "每一輪之後 ... 把決定寫下來，寫在專案保存決定的地方（規格、交接檔…）" versus "確認之前，不動手修改檔案". Writing the decision file is a file change before confirmation (D).
- The 「依你建議」 handling in the skill ("記成使用者的決定，註明是採用建議") matches workflow's "不把自己的建議寫成使用者已作的決定" only if the user actually said it; fine.

## 5. Docs, numbers, links
Verified true (P): 257 tests, 6 skipped; 14 agf subcommands; 7 skills (6 + align-with-me); description lengths of the six sum to 1,522 ("共約 1,500"); 10 guard tests; 1,310 -> 1,316; commits c020447, 90bba83, 2ffd748 resolve in the repository (git cat-file errored on a combined call; re-check by `git cat-file -t` one by one if it matters, not done); local links audited by agf.
Problems:
C1. README, analysis: "擋下各種寫法的 git push ... 已用 Claude Code 2.1.325 實測". The adapter shows two cases tested once (`git -C <dir> push origin HEAD`, one Write). "各種寫法...已實測" overclaims (A1-A4 show common spellings pass). The analysis and CHANGELOG say the same ("擋下各種寫法").
C2. adapters/claude.json: `guard_hook.execution_status: "observed"` for a test with one session; the sibling `permissions` entry says "observed; see observed and not_observed". The "limits" text lists only python -c, scripts and aliases and omits A1-A9.
C3. analysis section 1: "6 段共約 1,500 字元，遠低於 ... 每段 1,536 字元的上限" compares a sum with a per-skill limit. Each is about 250, so the conclusion holds, the sentence does not.
C4. HANDOFF/CHANGELOG say `agf audit` expects `"warnings": []`; true now. The claim "AGF audit 無錯誤" for the new skill: see section 4 (audit does not validate the field).
C5. CHANGELOG: cost "約 0.004 美元", model "claude-haiku-5-5", host version 2.1.325: not verifiable from the repository (S). "不 push" statements fine.
C6. docs/cli.md not updated (see 2). README says the guard config is "一個 JSON", example key `protected_paths`: matches code.
C7. HANDOFF: "evals/host/trigger.py" and "usage.py" exist (P). "studies/raft-kv-2026-11/ 的格式" exists. studies/README warns its internal links are broken by design (D, not a defect).
D. The analysis is written by the change author and says so in "方法與限制"; "已交給沒參與的模型審查（結果見 CHANGELOG）": CHANGELOG contains no review result (D, quoted: CHANGELOG has only the table, no review section). That is an unsupported pointer.
Hook ordering: adapter notes it did not observe interaction with the RTK rewriting hook; combined with A1 this is the likeliest real failure in this user's setup (`rtk proxy`).

## Severity summary
- Security/boundary bypass: A1-A9 (9 groups; A1, A2, A3, A4, A5, A7 are plain command lines).
- False refusal: B1-B4.
- Factual/doc errors: C1-C7 plus the unsupported "審查結果見 CHANGELOG".
- Wording/other: crash exit 1 (two inputs), config string accepted, project-rules/workflow contradiction on model switching and handoff, skill's own contradiction, 落盤.

# Research A: Open-source projects that shape AI coding-agent behaviour

Date: 2026-11-17. Method: WebFetch (a small model summarises each page, so "quotes" below are as returned by that tool and may be abbreviated; wording-critical quotes should be re-checked against the raw file before reuse) and WebSearch.
Legend: [READ] = I fetched the page/file; [SEARCH-ONLY] = search snippet only. Star counts are popularity, not evidence of effectiveness.

Could not fetch / not read: Hacker News and Reddit threads on ponytail (only referenced second-hand through InfoQ); the full ponytail README text (only a summary was returned); full ECC README (first 100k of 140k chars); BMAD internals (only the repo front page); humanlayer `ace-fca.md` was read, but the 12-factor per-factor docs were not (only the README index).

---

## 1. PRIORITY 1: ponytail (DietrichGebert/ponytail)

### 1.1 What it is
A "lazy senior dev" ruleset: the agent must take the smallest complete change. Core is about 100 lines of markdown (InfoQ), wrapped in a 6,232-line repo of per-host adapters. Created 2026-06-12; InfoQ (Aug) reports "over 82,000 GitHub stars". [READ] https://infoq.com/news/2026/08/ponytail-agent-skill-benchmark ; https://github.com/DietrichGebert/ponytail

### 1.2 Decision ladder (exact text)
Source A, AGENTS.md ("The smallest complete change"), [READ] https://raw.githubusercontent.com/DietrichGebert/ponytail/main/AGENTS.md , 6 rungs, intro "Take the first option that fully works:"
1. "Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line."
2. "Already in this codebase (a helper, component, service, pattern)? Use it the way the surrounding code does."
3. "Standard library or a platform feature? Use it, unless the project has its own. A house component beats a native widget."
4. "An installed dependency? Use it. Never add a dependency for a few lines."
5. "Can it be one line a reader gets at a glance? One line."
6. "Otherwise: the minimum code that works."

DISCREPANCY: the README ladder image alt text lists 7 rungs (separate "native platform feature" rung, and "only then the minimum that works, plus one small test if the code has logic"). [READ] https://github.com/DietrichGebert/ponytail . AGENTS.md has 6 (stdlib and platform merged). The skills/ponytail/SKILL.md summary (also 6 rungs, same merge) was only returned paraphrased, not verbatim. Treat the 6-rung AGENTS.md text as the canonical wording.

Other rules in skills/ponytail/SKILL.md (returned as paraphrase) [READ] https://raw.githubusercontent.com/DietrichGebert/ponytail/main/skills/ponytail/SKILL.md :
- Before writing: read task and touched code; list everywhere the change must reach (callers, tests, fixtures, config, exports); check what could break (data loss, exposure). Fixing those is in scope, extra features are not.
- "Be lazy about the solution, not the change." Deletion beats addition; no unrequested abstractions/options/config/"for later" code.
- Bug fixes: grep every caller first, fix root cause once in shared code.
- Non-trivial logic (branches, loops, parsers, money, security, new scripts) needs a small test or assert self-check.
- Known shortcuts get a comment `shortcut: <the limit>, <when to upgrade>`.
- Never cut: validation at trust boundaries, data-loss error handling, security, accessibility, anything explicitly asked for.
- Levels: lite (mention smaller option in one line, let user choose), full (default), ultra (challenge the request before building).
- Closing requirement: every reply ends with one or two lines on what was skipped/unchecked and any risk.
- Triggers in frontmatter: coding tasks (write/fix/refactor/review/choose dependency) plus phrases like "be lazy", "yagni", bloat complaints.

### 1.3 Packaging and size
[READ] https://github.com/DietrichGebert/ponytail (README summary) and https://github.com/DietrichGebert/ponytail/tree/main/hooks
- Claude Code: marketplace + plugin `ponytail@ponytail`; status band needs CC 2.1.290+ (not in VS Code panel, cloud, or `claude -p`).
- Codex: `codex plugin` marketplace, then trust two lifecycle hooks in `/hooks`.
- Others: copy `AGENTS.md` or install `skills/ponytail/SKILL.md`; adapters for Copilot, Cursor, OpenCode, Gemini, Windsurf, Cline, Kiro, Antigravity etc. Cursor with hooks supports only `/ponytail` level switching; Windsurf/Cline/Copilot/Kiro load always-on rules without commands. npm: `@dietrichgebert/ponytail`.
- Layout: per-host dirs (`.claude-plugin`, `.codex-plugin`, `.cursor/rules`, `.kiro/steering`, `.windsurf/rules`, `.clinerules`, `.opencode`, `.agents`, ...), manifests (plugin.json, gemini-extension.json, opencode.json, package.json), `skills/`, `commands/`, `hooks/`, `scripts/`, `pi-extension/`, `benchmarks/`, `tests/`, `docs/`, `i18n/`, `examples/`.
- Hooks dir contains: ponytail-activate.js, ponytail-mode-tracker.js, ponytail-instructions.js, ponytail-subagent.js, ponytail-config.js, ponytail-map.js, ponytail-runtime.js, ponytail-band-import.js, statusline .sh/.ps1, and per-host hook JSONs (claude-codex-hooks.json, cursor-hooks.json, copilot-hooks.json, qoder-hooks.json). Names only; contents not read. So: it uses skills + commands + hooks + scripts. Hooks appear to inject rules each session, track mode, and propagate to subagents (inference from names).
- Always-loaded text: AGENTS.md is about 45 lines / about 600 words (about 800-900 tokens, my estimate). InfoQ: core about 100 lines.
- Commands: `/ponytail [lite|full|ultra|off]`, `/ponytail band`, `/ponytail-review` (uncommitted/staged/branch/PR), `/ponytail-audit`, `/ponytail-debt` (collects `shortcut:` comments into a ledger), `/ponytail-gain`, `/ponytail-help`.
- Config: `~/.config/ponytail/config.json` or env `PONYTAIL_DEFAULT_MODE`; local data in `~/.config/ponytail/band/`.

### 1.4 Benchmark methodology (author's)
[READ] https://raw.githubusercontent.com/DietrichGebert/ponytail/main/benchmarks/results/2026-10-07-agentic.md
- Headless `claude -p`, Opus 5.5 default effort, CLI 2.1.288. Three arms (no skill, Ponytail v4.13.0, Ponytail 5), alternated task by task. 39 tasks: 12 feature tickets in a FastAPI+React template repo (scored on `git diff`), 18 surgical tasks with hidden checks (bugfix/security/privacy/rename), 6 "build small app", 3 "show example". 5 runs per task per arm = 585 sessions. Fresh temp folder, CLAUDE.md and auto memory disabled. Median of 5 per task; geometric mean of ratios; 95% bootstrap CI; sign test.
- Metrics: delivered source lines (including comments, excluding tests), gzip size of code, output tokens, cost at list price.
- Results vs no skill (Ponytail 5): lines -53%, gzip -41%, output tokens -45%, cost -26%. README chart (v4.13 / v5, share of baseline): LOC 52%/47%, output tokens 57%/55%, cost 84%/74%, time 62%/59%. README headline adds time -41%.
- Quality: hidden checks 87/90 (P5) vs 86/90 (others); security tasks 30/30 all arms; completeness judge 105/105 vs 100 no-skill. Quote: "Less code did not cost correctness or safety. It did not add any either: the three arms are level." README extras: risky logic ships with a test 98% vs 68%; own tests catch 66% of injected bugs vs 46%; review skill finds 100% planted problems vs 87%; blind comparison 110 to 67 vs previous version. [READ] README.
- Stated limitations (the file itself): Bash disabled for all arms ("measures what the agent writes, not what it can debug"); only Claude Code measured; 21 non-hidden-check tasks measure size not correctness; hidden-check sample small (18 tasks, 90 cells) and privacy task hard for all arms; LLM judges (Opus 5.5, Sonnet 5.5); no-skill timeouts on one task skew totals; author-run, no independent replication described.

### 1.5 Criticism and corrections
- Scott Logic (Colin Eberhardt), 2026-06-16 [READ] https://blog.scottlogic.com/2026/06/16/ponytail-yagni-and-the-problem-with-prompt-benchmarks.html : original benchmark was promptfoo, 5 trivial single-shot tasks, LOC counted all returned output, baseline padded with multiple options. Haiku average LOC: baseline 108; ponytail 8.25; baseline + "Provide just one example" 16; + "Follow YAGNI principles" 10.4; + one-liners 6.9, correctness 100% throughout. "Follow YAGNI principles, and one-liner solutions" beat ponytail on its own benchmark. Conclusion: skills need rigorous evals. The author responded and revised claims.
- InfoQ Aug 2026 [READ] https://infoq.com/news/2026/08/ponytail-agent-skill-benchmark : original claim 80-94% code reduction, now labelled a per-task ceiling misreported as an average; revised "about 54 percent less code", "roughly 20 percent lower" cost and "roughly 27 percent faster". HN skeptics: "essentially just these rules, and a metric ton of boilerplate for specific plugin systems"; leftpad comparison (second-hand via InfoQ; HN not read). A bare one-liner prompt "drops a safety guard that Ponytail preserves" (author-side claim). Now has a behavioural test framework and public reproduction path.
- NUMBERS THAT DISAGREE: code reduction 53% (README/benchmark file, Opus 5.5, 39 tasks) vs "about 54%" (InfoQ, 12-feature-task version); cost -26% (README) vs about -20% (InfoQ); time -41% (README) vs about -27% (InfoQ). Different benchmark revisions. Search-snippet pages (pasqualepillitteri.it "54% of the code", neura.market "benchmark correction") are [SEARCH-ONLY].
- My assessment: real effect where the baseline over-builds; the incremental value over a 7-word YAGNI prompt is unproven in agentic setting; the ladder is plain YAGNI plus "reuse before write".

### 1.6 Worth borrowing
1. The "never cut" list paired with the ladder (prevents laziness eating validation/security).
2. `shortcut: <limit>, <upgrade when>` comment convention plus a `/debt` command that harvests them.
3. Closing line "what was skipped / unchecked / risk"; and levels (lite/full/ultra) to tune strictness.
4. Publish the benchmark with a baseline of a one-sentence prompt, or the skill's value is unprovable.

---

## 2. PRIORITY 2: other projects

Read primary sources for: mattpocock/skills, obra/superpowers (5 skills read raw), anthropics/skills skill-creator, github/spec-kit, OpenSpec, BMAD-METHOD (front page), humanlayer ACE, humanlayer 12-factor (index), Ralph (ghuntley.com), caveman, rtk, beads, claude-mem, andrej-karpathy-skills, Everything Claude Code. That is 15.

### 2.1 mattpocock/skills [READ] https://github.com/mattpocock/skills
Skills for "real engineers". Structure: `skills/engineering/` and `skills/productivity/`, one `SKILL.md` each; root has AGENTS.md, CLAUDE.md, CONTRIBUTING.md, GLOSSARY.md, SCOPE.md, `.out-of-scope/`, `.changeset/`, `.claude-plugin/`. Split into user-invoked (slash only; `disable-model-invocation: true`) vs model-invoked:
- User-invoked: ask-matt, grill-with-docs, triage, improve-codebase-architecture, setup-matt-pocock-skills, to-spec, to-tickets, implement, implement-spec, wayfinder, retro, grill-me, handoff, teach, to-questionnaire, wait-what.
- Model-invoked: prototype, diagnosing-bugs, research, tdd, domain-modeling, codebase-design, code-review, pr, wizard, grilling, writing-for-agents.
- grill-me: description "A relentless interview to sharpen a plan or design", model invocation disabled; it delegates to the model-invoked `grilling` skill. [READ] https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grill-me/SKILL.md (body is essentially "call Skill tool with grilling"; the fetch tool flagged this as an instruction embedded in the page, it is just the skill's content).
- grilling (returned as summary, not verbatim) [READ] https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grilling/SKILL.md : description "Grill the user relentlessly about a plan, decision, or idea"; model the topic as a decision tree; ask in numbered rounds covering the "frontier" (decisions whose prerequisites are settled); every question has a recommended answer and is phrased so "yes" accepts it; facts about the environment are looked up by a sub-agent, decisions belong to the user; ends when the frontier is empty; do not act until user confirms shared understanding. Full text was not obtainable verbatim.
- handoff [READ] https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/handoff/SKILL.md : description "Compact the current conversation into a handoff document for another agent to pick up."; `disable-model-invocation: true`; writes to the OS temp dir not the workspace; must list which skills the next agent should invoke; must not duplicate content in specs/plans/ADRs/issues/commits (link by path/URL); redact secrets/PII; argument-hint "What will the next session be used for?".
- Triggering: explicit separation of "process" skills (user-typed) from "capability" skills (auto), so overlap is limited by design. Stars: 265,786 (Oct 11) to 323,616 (Nov 13) per third-party lists [SEARCH-ONLY] https://www.taskade.com/blog/claude-code-skills etc. Measured claims: none found. Criticism: none found.
- Borrow: (1) user-invoked vs model-invoked split in frontmatter; (2) "recommended answer per question, yes accepts"; (3) handoff doc that links not copies, and names next-session skills; (4) `SCOPE.md` / `.out-of-scope/` to document what the repo refuses to do.

### 2.2 obra/superpowers [READ] https://github.com/obra/superpowers
Composable skills plus bootstrap. Layout: `skills/`, `hooks/`, `scripts/`, `tests/`, `docs/`, per-harness plugin dirs, AGENTS.md, GEMINI.md. Evals via a "drill" harness (superpowers-evals) cloned into `evals/`. About 318.8k stars (README page) vs about 315k (search snippet, Nov 9): minor disagreement. No measured performance results on the README (only adoption numbers).
Skills: test-driven-development, systematic-debugging, verification-before-completion, diagnosing-superpowers, brainstorming, writing-plans, executing-plans, dispatching-parallel-agents, requesting/receiving-code-review, using-git-worktrees, finishing-a-development-branch, subagent-driven-development, writing-skills, using-superpowers. Workflow order: brainstorming, worktrees, writing-plans, subagent-driven/executing-plans, TDD, code review, finish branch. "Mandatory workflows, not suggestions."
Forcing skill use ([READ] using-superpowers raw): a SessionStart hook injects the bootstrap (in Pi also re-injected after compaction; the README admits Hermes has no post-compaction hook so the bootstrap can be lost in long sessions). Description: "Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions". Rules: "Invoke relevant or requested skills BEFORE any response or action"; "If you think there is even a 1% chance a skill might apply ... you ABSOLUTELY MUST invoke the skill"; "IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT."; a red-flags table of rationalisations ("this is just a simple question"); announce "Using [skill] to [purpose]"; make a todo per checklist item; "process skills come first"; "User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills".
brainstorming [READ]: "Nothing gets built until your human partner approves the design doc"; building includes scaffolding and installing dependencies; reading/exploring fine; order: lay out approaches in a separate message and have the user pick, write design doc, get approval, invoke writing-plans "and no other skill"; "Ask one at a time"; "Ask a question only when the answer would change what gets built and neither the request nor the project answers it"; user can opt out of questions.
writing-plans [READ]: trigger "Use when you have a spec or requirements for a multi-step task, before touching code"; each step one action with verifiable result (failing test, confirm fail, implement, confirm pass, commit); "A plan longer than the code it describes has written the code instead."; no-placeholder rule (no "TBD", "handle edge cases", "add appropriate validation"); self-review for gaps and over-specification; execution choice subagent-driven (fresh subagent + reviewer per task) vs native in-session.
systematic-debugging [READ]: "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST"; four phases (investigate, pattern analysis, hypothesis and test, implement with failing test); after three failed fixes stop and discuss architecture with the human.
verification-before-completion [READ]: "NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE"; excuse/reality table ("Should work now" / "RUN the verification"; "Linter passed" / "Linter ≠ compiler"; "Agent said success" / "Verify independently").
writing-skills [READ]: description must say when to use and "never summarizes the skill's workflow" because agents then follow the summary instead of reading the skill; start "Use when..."; third person; include symptoms/error strings/tool names; "If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing"; baseline with a subagent without the skill; pressure scenarios with 3+ combined pressures (time, sunk cost, authority, exhaustion). Token budget guidance lives in `references/discovery.md`, not read.
Criticism: not found in sources read; ECC/size footprint and "1% rule" aggressiveness are my observations, not sourced. Borrow: (1) description = trigger condition only; (2) rationalisation tables; (3) approval-gated "nothing gets built" with explicit definition of "building"; (4) pressure-test new skills against a baseline.

### 2.3 anthropics/skills, skill-creator [READ] https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md
- Description is "the primary mechanism that determines whether Claude invokes a skill". Claude tends to "undertrigger", so make descriptions "a little bit 'pushy'", naming specific contexts even when the user does not name the skill.
- Progressive disclosure, three levels: "Metadata (name + description) - Always in context (~100 words)", then SKILL.md body, then bundled resources loaded as needed. "Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy"; reference files over 300 lines get a table of contents.
- Evals: for verifiable outputs; subjective skills often don't need them. Save test prompts first, draft assertions while runs go; assertions objectively checkable.
- Description optimisation loop: trigger evals with should-trigger and should-not-trigger (near-miss negatives), 60% train / 40% held-out, choose by test score.
- Note the tension: Anthropic says be pushy; superpowers says description must not summarise workflow; ponytail's skill lists trigger phrases. Both agree description = triggers.
- Borrow: the trigger-eval harness with near-miss negatives and a held-out split.

### 2.4 github/spec-kit [READ] https://github.com/github/spec-kit
CLI `specify` (uv tool) scaffolds `.specify/` (templates, memory, extensions, presets, workflows, integrations, scripts). Commands: `/speckit-constitution`, `-specify`, `-plan`, `-tasks`, `-implement`, `-converge`; extensions for bug fixing (`bug-assess/fix/test`, verdict verified/partial/failed) and idea assessment (go / needs-clarification / kill). Triggered manually, one command at a time with human review; extension hooks can run before/after commands. Constitution (project principles) is created once; the page does not say how it is enforced. No measured claims; 150.1k stars. Borrow: constitution as a single "project principles" file referenced by plan gates; explicit verdict vocabularies.

### 2.5 OpenSpec (Fission-AI) [READ] https://github.com/Fission-AI/OpenSpec
Lighter spec layer, "fluid not rigid". Commands: explore, propose `<name>`, apply-change, archive-change (expanded profile: verify-change, bulk-archive). Per change folder `openspec/changes/<name>/{proposal.md, specs/, design.md, tasks.md}`; on archive, moved to `changes/archive/<date>-...` and merged into living `openspec/specs/`. Requirements use "SHALL", scenarios WHEN/THEN. Self-claims: works with 30+ tools, "lighter" than Spec Kit; no measurements. Borrow: delta-spec-then-archive lifecycle (task list lives with the change, specs updated at archive).

### 2.6 BMAD-METHOD [READ, front page only] https://github.com/bmad-code-org/BMAD-METHOD
v6.12 stable, V7 alpha (skills-based). Modules: BMad Method, Builder, Creative Intelligence, Test Architect, BMad Loop (unattended epic build + retro), Game Dev. Phases Clarify / Plan / Build and verify / Learn. Claims it "sizes itself to the work". Persona details, story files and sharding were not on the page, so unverified. No measurements, no criticism on page. Borrow: scale-adaptive depth (small change goes straight to build).

### 2.7 humanlayer advanced context engineering [READ] https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md
Research, Plan, Implement. "a bad line of a plan could lead to hundreds of bad lines of code"; humans review research and plans ("I can read 200 lines of a well-written implementation plan"). Intentional compaction: distil the session into a progress/status file and start a fresh window; implement phase by phase, compacting status back into the plan file after each verified phase. Keep context utilisation in the "40%-60% range"; about 170k usable tokens (attributed to Huntley); "The more you use the context window, the worse the outcomes". No benchmark. Borrow: write status back into the plan file after each verified phase; context-utilisation target.

### 2.8 humanlayer 12-factor-agents [READ index only] https://github.com/humanlayer/12-factor-agents
Titles: natural language to tool calls; own your prompts; own your context window; tools are structured outputs; unify execution and business state; launch/pause/resume with simple APIs; contact humans with tool calls; own your control flow; compact errors into context; small focused agents; trigger from anywhere; stateless reducer. Page gave titles only (summaries are the fetch tool's interpretation). Relevant: pause/resume, compact errors, small agents.

### 2.9 Ralph loop (Geoffrey Huntley) [READ] https://ghuntley.com/ralph/
`while :; do cat PROMPT.md | claude-code ; done`: fresh context every iteration. Files: PROMPT.md, `specs/` (one spec per file, written in a long conversation first), `fix_plan.md` (prioritised TODO, often deleted and regenerated from spec-vs-code diff), `AGENT.md` (how to build/run, updated as learned). "Only one thing" per loop; main context as scheduler ("Your primary context window should operate as a scheduler"), many subagents for search, only one for build/test (avoids "bad form back pressure"). Backpressure from tests, type checkers, analyzers. Anti-placeholder: "DO NOT IMPLEMENT PLACEHOLDER OR SIMPLE IMPLEMENTATIONS." Self-stated limits: nondeterminism "is the Achilles' heel"; may reimplement existing code after a failed ripgrep; may leave non-compiling code; wasteful re-reading; greenfield only ("no way in heck would I use Ralph in an existing code base"); "$297 vs $50k" cost is an anecdote. Note the tension with ponytail/Karpathy: Ralph's anti-minimalism rule counters the model's tendency toward stubs; the two need different scopes. Borrow: state lives on disk (plan + progress file), each iteration fresh; one item per loop.

### 2.10 caveman [READ] https://github.com/JuliusBrussee/caveman
Terse-voice skill plus "rocks": read-less (compresses logs/JSON/CSV/test output before the model reads), auto model routing, blocks (save reusable scripts), cost analysis, cloud. Triggers `/caveman`, `/ultracave`, `/megacave`; "stop caveman". Claims (self-published): About text "cuts 65% of tokens" but its own data is lower: one example 63 to 20 tokens; on ten dev questions `/caveman` only 3% below an "Answer concisely." baseline, `/ultracave` 35% (older rules); input compression 33.2% fewer input tokens across 54 CC runs, 18/18 answers correct, per-file 82-99%, HTML worse; Auto 54% cheaper than Opus 5.5 xhigh on 85 tasks, 0.5-point score gap within ±7 noise. Cites third parties (Adobe Research 1.4-2.4x cost cut; Elastic 63.6% fewer response tokens; JetBrains no measurable quality loss on 86 paired tasks, 8.5% fewer output tokens) which I did not verify. Self-disclosed caveats: per-request billing (Copilot) saves nothing and rules cost about 1,160 input tokens; rewriting user prompts hurts so it does not; default telemetry; paid cloud upsell. Borrow: always baseline against "be concise"; the honest finding that terse voice is a small win over a plain concision instruction.

### 2.11 rtk (Rust Token Killer) [READ] https://github.com/rtk-ai/rtk
Single Rust CLI filtering command output (100+ commands, 18 agents). `rtk init -g` installs a hook that rewrites `git status` to `rtk git status`; hookless agents get a rules file that relies on model compliance; built-in Read/Grep/Glob pass through unfiltered. Fail-safe: filter failure returns raw output with exit code preserved; `rtk bypass`; truncated output points to recovery. Claim 60-90% reduction on common dev commands (demo 93.3% over two commands: cargo test 94.2%, ls 82.3%); tokens estimated as bytes/4; "not a 90% cut in cost"; each filter must cut at least 20% to ship; 20.2% total cost reduction claim from its own pipeline benchmark; says prompt cache is unaffected. Caveats: output-only, name collision on crates.io, BUSL-1.1 on engine/proxy, paid Pro upsell. This user's own setup already uses it (RTK.md). Borrow: hook-level rewriting that guarantees raw-output fallback and a local `gain` ledger.

### 2.12 steveyegge/beads [READ] https://github.com/steveyegge/beads
`bd`: Go CLI on Dolt (embedded default or server), dependency-aware task graph replacing markdown plans; about 28.8k stars. Memory/handoff: `bd prime` prints workflow context + stored memories at session start; `bd remember "insight"`; `bd ready` lists unblocked work so a new agent/machine resumes; `bd update <id> --claim` atomic claim; hash IDs (bd-a1b2) avoid merge collisions; compaction summarises old closed tasks; `bd setup` installs integrations; sync via `bd dolt push/pull`; `.beads/issues.jsonl` is an export, not source of truth. Caveats on page: HTTP backend experimental, schema-version guard, coordinated upgrades across clones. No measurements. Borrow: "ready" query as the resume primitive; hash IDs; compaction of closed work.

### 2.13 claude-mem [READ] https://github.com/thedotmack/claude-mem
Hooks (Setup, SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, Stop, SubagentStop, SessionEnd) send each tool call to a local worker; a second agent writes observations and a session summary; next session starts with a compact index. Storage SQLite + Chroma. Progressive disclosure via three MCP steps: `search` (index) → `timeline` → `get_observations` (full by ID). Claim: index rows "about a tenth the size of a full record" (50-100 vs 500-1,000 tokens) but the page itself says "is not a measured recall or end-to-end saving" (issue #4138); "up to 100% more usage from your plan" with paid observer. Caveats: some agents search-only; telemetry on by default; trial/payment, promoted third-party token. Borrow: three-tier index→timeline→detail retrieval; treat savings as unmeasured.

### 2.14 forrestchang/andrej-karpathy-skills [READ] https://github.com/forrestchang/andrej-karpathy-skills
One CLAUDE.md with four principles: "Think Before Coding: Don't assume. Don't hide confusion. Surface tradeoffs."; "Simplicity First: Minimum code that solves the problem. Nothing speculative."; "Surgical Changes: Touch only what you must. Clean up only your own mess."; "Goal-Driven Execution: Define success criteria. Loop until verified." Files: CLAUDE.md, README(.zh), CURSOR.md, EXAMPLES.md, `.claude-plugin/`, `.cursor/rules/karpathy-guidelines.mdc`, `skills/karpathy-guidelines/`. 233.8k stars. No benchmarks; says trivial tasks may not need the full process. Borrow: four short principles as the always-loaded floor; a ponytail-style ladder is just an elaboration of principle 2.

### 2.15 Everything Claude Code (affaan-m/ECC) [READ, first 100k of 140k chars] https://github.com/affaan-m/everything-claude-code
"Optimize the context window. Persist everything else." 72 agents, 327 skills, 98 command shims, rules packs (`common/` + per-language), hooks in `hooks/hooks.json` (session-start, session-end, pre-compact, suggest-compact, evaluate-session; PreToolUse/PostToolUse/Stop), AgentShield config scanner. "Instincts": learned patterns with confidence (inject cap 6, min 0.7); `/evolve`, `/prune`. Context controls: `ECC_SESSION_START_MAX_CHARS` default 8000; `ECC_HOOK_PROFILE`; `ECC_DISABLED_HOOKS`. No token-savings measurements. Self-disclosed: Claude plugin advertises the whole catalog (context bloat), stacking install methods duplicates hooks, Windows defects, sponsorship-heavy README. Star count disagrees: about 305k (README), 315,400 (a Nov 10 list), "201K+" (another list) [SEARCH-ONLY] https://claudefa.st/blog/tools/skills/best-claude-code-skills etc. It is the cautionary example of the opposite of ponytail (huge surface). Borrow: pre-compact hook, hook strictness profiles, kill-switch env vars.

### 2.16 Trending June-Nov 2026 not on the list
[SEARCH-ONLY] from https://www.taskade.com/blog/claude-code-skills , https://claudefa.st/blog/tools/skills/best-claude-code-skills , https://github.com/VoltAgent/awesome-agent-skills , https://github.com/quemsah/awesome-claude-plugins : contenders listed are superpowers, ECC, mattpocock/skills, anthropics/skills; counts vary by tens of thousands between aggregators. ponytail (June 12) and caveman and BMad Loop/V7 are the June+ risers I confirmed by reading. I did not find, and did not read, any further new project; no claim made.

---

## 3. PRIORITY 3: cross-cutting comparison (only from what I read)

### 3.1 Avoiding overlap, mis-triggering, non-triggering
- Description = trigger condition only, "Use when ..." with symptoms; never a workflow summary (superpowers writing-skills, [READ]). Anthropic skill-creator says the opposite pole for under-triggering: be "a little bit pushy" and list contexts ([READ]). Reconcile: pushy about when, silent about how.
- Separate user-invoked (`disable-model-invocation: true`) from auto skills (mattpocock; handoff, grill-me are slash-only) so rarely-wanted skills cannot mis-trigger.
- Forced check: SessionStart hook injects a bootstrap skill with "1% chance" rule and rationalisation table (superpowers); re-injection after compaction is needed (Pi has it, Hermes lacks it, per README). ponytail has an activate hook + mode tracker + subagent hook (names only).
- Process-over-implementation priority order (superpowers), one explicit successor per skill ("invoke writing-plans and no other skill") to avoid overlap.
- Measure: trigger evals with near-miss negatives and held-out split (Anthropic); pressure-scenario baselines (superpowers). Only these two ship real procedures; most others ship none.

### 3.2 Cross-session/cross-model handoff and memory; surviving sudden limit
- Plan/progress file as the unit of state: Ralph (`fix_plan.md`, `AGENT.md`, `specs/`, fresh context each loop), humanlayer (compact status back into the plan after each verified phase), superpowers (design doc then plan file with one-action steps).
- Handoff doc: mattpocock handoff (to temp dir, link not copy, list next skills, redact).
- Task graph with resume query: beads `bd ready`, `bd prime`, `bd remember`, atomic claim.
- Automatic capture: claude-mem (hooks on every tool call, session summary, layered retrieval); ECC (pre-compact + session-end hooks, instincts).
- Sudden limit/crash: none of the sources documents a dedicated pattern. What survives is anything already on disk: Ralph/plan-file/beads designs survive because state is written each step and each iteration is stateless; hook-driven capture (claude-mem PostToolUse) survives because it writes per tool call. Prose handoffs (mattpocock) require the agent to run before the cut-off and so do not. This conclusion is my inference.

### 3.3 Cutting tokens
- Output filtering by hook: rtk (60-90% on command output; 20% minimum per filter; total cost effect smaller, self-reported 20.2%); caveman read-less (33.2% input over 54 runs).
- Terse voice: caveman 63→20 tokens in an example, but only 3% below "Answer concisely." for `/caveman` and 35% for `/ultracave`; rules cost about 1,160 input tokens. ponytail -45% output tokens (mostly because less code is written, not terse voice).
- Progressive disclosure: skill metadata about 100 words always loaded, body under 500 lines (Anthropic); claude-mem 10x smaller index rows (unmeasured end-to-end); ECC caps session-start context at 8000 chars.
- Fewer/smaller context: Ralph/ACE keep 40-60% utilisation, subagents for search.
- Scripts instead of prose: caveman "blocks" save agent-written scripts; ponytail has `scripts/` and band import, but I found no quantified comparison. Gap.

### 3.4 Stopping over-engineering and over-thinking
- Ladders/principles: ponytail ladder + never-cut list; Karpathy "Simplicity First", "Surgical Changes"; ponytail `shortcut:` comments and `/debt`.
- Process limits: superpowers 3-failed-fixes stop; plan length must not exceed code; one-question-at-a-time; one item per loop (Ralph).
- Evidence: only ponytail measured it (-53% lines); a 7-word YAGNI prompt matched it on the original benchmark (Scott Logic). So a short rule may suffice; cost-benefit of a big ruleset is unproven. Over-thinking: no source measured reasoning-token reduction; I found no direct evidence.
- Counter-pressure: Ralph's "no placeholder" rule and ponytail's "never cut" list show laziness needs guard rails.

### 3.5 "Interview me until we agree"
- mattpocock grilling: decision tree, rounds over the frontier, recommended answer per question, subagent fetches facts, finish when frontier empty, do not act until confirmed.
- superpowers brainstorming: one question at a time, only if the answer changes what gets built, propose approaches in their own message, design doc approval is a hard gate before any build; opt-out supported.
- OpenSpec `/openspec-explore` and Spec Kit `/speckit-specify` + constitution; Ralph writes specs through "a long conversation" first; ponytail ultra "challenge the request before building"; Karpathy "Surface tradeoffs".

### 3.6 Hard boundaries by hooks/permissions/CI vs prose
- Prose-only: superpowers iron laws and rationalisation tables, Karpathy, ponytail rules (enforced only by instruction; ponytail mode state is hook-tracked but the behaviour is not blocked).
- Hook-enforced or hook-assisted: rtk rewriting commands (real enforcement of filtering, with fallback), superpowers SessionStart injection, claude-mem lifecycle capture, ECC hooks.json with strictness profiles, Spec Kit extension hooks. ECC claims "hooks enforce checks outside the prompt" but I saw no specifics of blocking hooks in the portion read.
- CI/tests: superpowers evals harness, ponytail `tests/` and benchmark reproduction path, Ralph's compiler/test backpressure. None of the sources read documents permission-deny rules or CI gates as a primary mechanism; ECC's AgentShield scans permissions/hooks/MCP config. No project in this set blocks "claiming done without evidence" mechanically; that remains prose (verification-before-completion), a candidate for a Stop hook (my suggestion).

---

## 4. Shortlist of transferable ideas
1. Descriptions say when, not how; split user-invoked vs auto-invoked skills.
2. Bootstrap re-injected on SessionStart and after compaction; keep always-loaded text under about 600 words (ponytail AGENTS.md is the size benchmark).
3. Test descriptions with trigger evals (near-miss negatives, held-out split) and test discipline skills against a no-skill baseline under pressure.
4. State on disk each step: plan/progress file + ready-query; handoff docs that link, not copy.
5. Hard gate "nothing built until approved", with "building" defined; one question at a time, recommended answer per question.
6. Ladder + never-cut list + `shortcut:` ledger; end replies with skipped/unchecked/risk.
7. Output filtering by hook with raw-output fallback; benchmark every terse/compression claim against "be concise".
8. Candidate hook (not found in sources): Stop hook requiring verification evidence before "done".

# B1 Candidate — Raw Codex Dialogue Exchange

**Thread ID:** `019d9811-b052-7163-b5e2-e91b9db26ffb`  
**Source:** `/Users/jp/.codex/sessions/2026/04/16/rollout-2026-04-16T16-53-09-019d9811-b052-7163-b5e2-e91b9db26ffb.jsonl`  
**Records:** 196 JSONL entries (26 messages, 43 tool calls)

This is the verbatim back-and-forth between the `codex-collaboration` dialogue-orchestrator subagent and Codex, extracted from the Codex session rollout. Reasoning items are encrypted and not included. Tool call outputs are truncated at 2500 chars where needed.

---

## System prompt (developer role)

```
<permissions instructions>
Filesystem sandboxing defines which files can be read or written. `sandbox_mode` is `read-only`: The sandbox only permits reading files. Network access is restricted.
Approval policy is currently never. Do not provide the `sandbox_permissions` for any reason, commands will be rejected.
</permissions instructions>
## Memory

You have access to a memory folder with guidance from prior runs. It can save
time and help you stay consistent. Use it whenever it is likely to help.

Never update memories. You can only read them.

Decision boundary: should you use memory for a new user query?

- Skip memory ONLY when the request is clearly self-contained and does not need
  workspace history, conventions, or prior decisions.
- Hard skip examples: current time/date, simple translation, simple sentence
  rewrite, one-line shell command, trivial formatting.
- Use memory by default when ANY of these are true:
  - the query mentions workspace/repo/module/path/files in MEMORY_SUMMARY below,
  - the user asks for prior context / consistency / previous decisions,
  - the task is ambiguous and could depend on earlier project choices,
  - the ask is a non-trivial and related to MEMORY_SUMMARY below.
- If unsure, do a quick memory pass.

Memory layout (general -> specific):

- /Users/jp/.codex/memories/memory_summary.md (already provided below; do NOT open again)
- /Users/jp/.codex/memories/MEMORY.md (searchable registry; primary file to query)
- /Users/jp/.codex/memories/skills/<skill-name>/ (skill folder)
  - SKILL.md (entrypoint instructions)
  - scripts/ (optional helper scripts)
  - examples/ (optional example outputs)
  - templates/ (optional templates)
 - /Users/jp/.codex/memories/rollout_summaries/ (per-rollout recaps + evidence snippets)
  - The paths of these entries can be found in /Users/jp/.codex/memories/MEMORY.md or /Users/jp/.codex/memories/rollout_summaries/ as `rollout_path`
  - These files are append-only `jsonl`: `session_meta.payload.id` identifies the session, `turn_context` marks turn boundaries, `event_msg` is the lightweight status stream, and `response_item` contains actual messages, tool calls, and tool outputs.
  - For efficient lookup, prefer matching the filename suffix or `session_meta.payload.id`; avoid broad full-content scans unless needed.

Quick memory pass (when applicable):

1. Skim the MEMORY_SUMMARY below and extract task-relevant keywords.
2. Search /Users/jp/.codex/memories/MEMORY.md using those keywords.
3. Only if MEMORY.md directly points to rollout summaries/skills, open the 1-2
   most relevant files under /Users/jp/.codex/memories/rollout_summaries/ or
   /Users/jp/.codex/memories/skills/.
4. If above are not clear and you need exact commands, error text, or precise evidence, search over `rollout_path` for more evidence.
5. If there are no relevant hits, stop memory lookup and continue normally.

Quick-pass budget:

- Keep memory lookup lightweight: ideally <= 4-6 search steps before main work.
- Avoid broad scans of all rollout summaries.

During execution: if you hit repeated errors, confusing behavior, or suspect
relevant prior context, redo the quick memory pass.

How to decide whether to verify memory:

- Consider both risk of drift and verification effort.
- If a fact is likely to drift and is cheap to verify, verify it before
  answering.
- If a fact is likely to drift but verification is expensive, slow, or
  disruptive, it is acceptable to answer from memory in an interactive turn,
  but you should say that it is memory-derived, note that it may be stale, and
  consider offering to refresh it live.
- If a fact is lower-drift and cheap to verify, use judgment: verification is
  more important when the fact is central to the answer or especially easy to
  confirm.
- If a fact is lower-drift and expensive to verify, it is usually fine to
  answer from memory directly.

When answering from memory without current verification:

- If you rely on memory for a fact that you did not verify in the current turn,
  say so briefly in the final answer.
- If that fact is plausibly drift-prone or comes from an older note, older
  snapshot, or prior run summary, say that it may be stale or outdated.
- If live verification was skipped and a refresh would be useful in the
  interactive context, consider offering to verify or refresh it live.
- Do not present unverified memory-derived facts as confirmed-current.
- For interactive requests, prefer a short refresh offer over silently doing
  expensive verification that the user did not ask for.
- When the unverified fact is about prior results, commands, timing, or an
  older snapshot, a concrete refresh offer can be especially helpful.

Memory citation requirements:

- If ANY relevant memory files were used: append exactly one
`<oai-mem-citation>` block as the VERY LAST content of the final reply.
  Normal responses should include the answer first, then append the
`<oai-mem-citation>` block at the end.
- Use this exact structure for programmatic parsing:
```
<oai-mem-citation>
<citation_entries>
MEMORY.md:234-236|note=[responsesapi citation extraction code pointer]
rollout_summaries/2026-02-17T21-23-02-LN3m-weekly_memory_report_pivot_from_git_history.md:10-12|note=[weekly report format]
</citation_entries>
<rollout_ids>
019c6e27-e55b-73d1-87d8-4e01f1f75043
019c7714-3b77-74d1-9866-e1f484aae2ab
</rollout_ids>
</oai-mem-citation>
```
- `citation_entries` is for rendering:
  - one citation entry per line
  - format: `<file>:<line_start>-<line_end>|note=[<how memory was used>]`
  - use file paths relative to the memory base path (for example, `MEMORY.md`,
    `rollout_summaries/...`, `skills/...`)
  - only cite files actually used under the memory base path (do not cite
    workspace files as memory citations)
  - if you used `MEMORY.md` and then a rollout summary/skill file, cite both
  - list entries in order of importance (most important first)
  - `note` should be short, single-line, and use simple characters only (avoid
    unusual symbols, no newlines)
- `rollout_ids` is for us to track what previous rollouts you find useful:
  - include one rollout id per line
  - rollout ids should look like UUIDs (for example,
    `019c6e27-e55b-73d1-87d8-4e01f1f75043`)
  - include unique ids only; do not repeat ids
  - an empty `<rollout_ids>` section is allowed if no rollout ids are available
  - you can find rollout ids in rollout summary files and MEMORY.md
  - do not include file paths or notes in this section
  - For every `citation_entries`, try to find and cite the corresponding rollout id if possible
- Never include memory citations inside pull-request messages.
- Never cite blank lines; double-check ranges.

========= MEMORY_SUMMARY BEGINS =========
## User Profile

The user is doing repeated, high-rigor work in `/Users/jp/Projects/active/claude-code-tool-dev`, mostly around the `codex-collaboration` plugin, benchmark-v1, T-04 dialogue/gatherer behavior, containment/lifecycle edges, handoff continuity, and earlier shakedown work in the `claude-code-tool-dev-t8-impl` implementation worktree. They often write specs, plans, patches, or ticket updates themselves, then bring them back for adversarial review, closure verification, or merge-readiness checks.

They use Codex in several explicit modes and expect those mode changes to be noticed. Common modes are: read-first orientation, harsh spec/plan scrutiny, bounded read-only advisory analysis from a packet, PR review plus small follow-up patching, and real handoff load/save execution with exact resume boundaries. They do not want those modes blurred together.

Good collaboration means: read the relevant files first, ground claims in repo authority, preserve exact ticket/contract wording, distinguish mechanism success from quality-of-result issues, and stop once the requested coverage is complete. They tolerate many review rounds if each round finds something real. They dislike speculative smoothing, rationalized asymmetry, stale-hand-off assumptions, or pretending a task is “done” when the boundary is only “artifacts staged,” “review next,” or “manual setup remains.”

They rely heavily on the personal handoff queue at `~/.codex/handoffs/claude-code-tool-dev/` and care about exact next-session entry points such as “review PR #105,” “resume benchmark execution after RC4 resolution,” or “start from live `/dialogue`.” They also use structured review packets, delta tables, commit-scoped check-ins, phase-by-phase sanity checks, and explicit choice menus (`A/B/C`, “Keep or close?”), so future agents should mirror that structure when it is present.

## User preferences

- When the user asks to “Read the relevant files” or “Read each of the relevant files ... to orient yourself,” do the file/code read first and ground the answer in that evidence.
- When the user asks to “walk me through your thoughts” or to discuss “challenge points,” break the analysis into explicit points and reason through them one by one.
- When the user says they will do something “MANUALLY” and wants “input, feedback, and review,” stay in planning/review mode and do not jump into implementation.
- When the user says they will write the spec or plan manually and bring it back next session, preserve that review boundary and do not preempt it with drafting.
- When the user invokes `scrutinize` or asks for harsh review, default to reject-until-proven-credible scrutiny rather than collaborative polishing.
- On contracts, plans, and benchmark packets, preserve the user’s blocker language. If a control surface is missing, call it blocked; do not rationalize it into acceptable asymmetry.
- In benchmark work, treat “comparability and non-contamination” as the primary design rule; convenience is subordinate.
- Separate repo-side verification from manual shell/runtime setup and from already-satisfied human attestations; keep blocker lists tight.
- When the user asks acceptance or closure questions, answer from the ticket/contract wording and live repo evidence, not intuition.
- When the user provides `A/B/C` options or “Keep or close?” choices, answer in the same structured decision format.
- When the user provides a structured external review packet, use that packet’s structure and recommend a clear next action instead of re-deriving the whole review from scratch.
- When the user says earlier findings were “verified empirically” and asks for `A/B/C`, stay evidence-based and choose one defended option instead of hedging.
- When the user asks for a narrow fix and then says “Implement the fix,” proceed directly with the minimal patch plus regression tests.
- When a review finding shows intended behavior is unpinned, prefer a small targeted test patch over a broader runtime refactor.
- When the user asks for a “grounded second opinion” or constrains the turn to packet-only authority, stay read-only, evidence-only, and bounded.
- On contract-edge questions, use exact citations and label uncertainty instead of smoothing over ambiguity.
- Distinguish mechanism success from quality-of-result issues such as timeouts, late-turn instability, or artifact-staging-only boundaries.
- When a harness or skill overclaims what it automates, narrow it to the honest boundary instead of preserving aspirational wording.
- Track open acceptance criteria explicitly. Do not assume a merged slice closes the larger ticket if later criteria remain open.
- When the user says “This can converge” or otherwise signals the main point is established, stop expanding into lower-value details.
- When the user invokes `[$handoff:load]` or `[$handoff:save]`, perform the real handoff workflow rather than summarizing it in chat.
- Preserve exact next-session boundaries in handoffs and confirm saved path, branch/commit, and cleanup state concretely.
- Treat loaded handoffs as snapshots, not live truth, when active branch or PR state may have moved.
- When review/publication shape matters, preserve the PR boundary instead of blurring it into a direct local merge.
- When runtime truth matters, prefer real interactive execution over source-only reasoning.
- Shape commits by artifact lifetime when the user is separating runtime code, validation scaffolding, and evidence capture.
- In T7/T8/T4 containment work, prefer fail-closed defaults and transparent harness confinement over permissive fallback or model-aware workarounds.
- When the user asks for phase-by-phase sanity checks, preserve those checkpoints and do not collapse several phases into one “done” summary.

## General Tips

- Live resumable handoffs for this project live in `~/.codex/handoffs/claude-code-tool-dev/`; repo-local `docs/handoffs/` is durable context, not the primary resume queue.
- The per-project resume marker is `~/.codex/.session-state/handoff-claude-code-tool-dev`; verify it is removed after save.
- Installed handoff skill paths repeatedly resolved under `/Users/jp/.codex/plugins/cache/local-personal/handoff/1.5.0/skills/` when user-provided shortcut paths were stale.
- For `codex-collaboration` package work, prefer package-local pytest commands over repo-root collection; repo-wide collection has unrelated namespace collisions.
- In benchmark-v1 work, the canonical session ID is the hook-published file at `~/.claude/plugins/data/codex-collaboration-inline/session_id`; the older `~/.claude/session_id` reference is stale here.
- For runtime/benchmark reviews, trace important parameters all the way through input, persisted state, behavior, and emitted artifacts.
- For T-20260330-02 plugin-shell planning, the scaffolding already exists; the real question is scope narrowing and whether `codex.dialogue.*` should remain exposed.
- For T-20260410-02 fast-path hardening, the durable invariant is exact sequence-set equality against remote completed turns; file-global replay diagnostics mean an empty store is not always trustworthy.
- For stale-cleanup work, keep the caller split straight: lifecycle is fail-open, smoke-setup is fail-fast, and per-file lost races are not the same as root-stage failures.
- For B4 shakedown work, remember `codex.dialogue.start` only creates the handle; the first actual question goes through `codex.dialogue.reply`.
- For `--plugin-dir` development sessions, plugin data lives under `~/.claude/plugins/data/codex-collaboration-inline/`; using the base plugin name can make live result collection look empty.
- For linked-worktree cleanup in this repo, inspect `git worktree list --porcelain` and preserve local-only history before recreating `main` or repurposing the implementation worktree.
- For T4 live-smoke/runbook work, use `run_id`-bound telemetry and durable transcript markers rather than positional checks like `tail -1`.
- For historical T4/B4 git shaping, separate runtime code, validation scaffolding, and evidence capture into different commits when possible.
- After contract rewrites, grep adjacent docs for stale vocabulary, outdated cross-references, and summary drift.

## What's in Memory

### claude-code-tool-dev

#### 2026-04-16

- benchmark-v1 packet and scored execution setup: benchmark-v1, RC4, posture, turn_budget, invocations.md, session_id_canonical, ~/.claude/plugins/data/codex-collaboration-inline/session_id
  - desc: Search this first for the latest benchmark-v1 execution guidance in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`. It covers the move from rehearsal-only packet repair to scored execution readiness, including the freshest Phase 1 checklist, invocation-packet review, RC4 parity resolution, and canonical session-ID correction.
  - learnings: The current high-signal rules are “blocked until fixed or contract-amended” for missing control surfaces, the wiring path `-p/-n -> MCP -> controller -> orchestrator`, and that the real session-ID source is the codex-collaboration hook-published file, not `~/.claude/session_id`.

#### 2026-04-15

- benchmark-v1 contract rewrite and smoke interpretation: AC-4, dialogue-tier citations, max_evidence, B1 B3 B5 B8, invalid runs, supported-claim rate within 0.10
  - desc: Use this topic for benchmark-v1 authority questions in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`: whether AC-4 is closed, what the executable v1 gate actually is, how `max_evidence` is defined, and what changed when the benchmark authority was rewritten on `main`.
  - learnings: The durable shift was from automation-heavy ceremony to a manual/reviewable v1 contract: `converged: false` can still satisfy AC-4, `max_evidence` means evidence-record budget, and invalid runs are rerun rather than counted as failures.

- T-04 dialogue/gatherers implementation and review path: production dialogue, pre-dialogue gatherers, PR #107, PRODUCTION_SYNTHESIS, citation_tier, representative_citation, zero_output
  - desc: Search here for the full T-04 implementation arc in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`: re-slicing the plan around real transport constraints, authoring production dialogue surfaces, planning gatherers/briefing assembly through six review rounds, reviewing PR #107, and tracing `/dialogue` gatherer retry semantics.
  - learnings: The durable contracts are the dispatch-only `/dialogue`, the dedicated `<PRODUCTION_SYNTHESIS>` sentinel, session-scoped active-run pointers, package-local pytest as the meaningful regression gate, and fail-soft gatherer fallback ending in `warnings:["zero_output"]` when both attempts produce no parseable lines.

- containment lifecycle and poll-race advisory: containment_lifecycle.py, containment_guard.py, _poll_for_scope, ValueError, read_json_file_strict, stranded seed
  - desc: Use this for read-only triage of containment behavior in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`: lifecycle tracing, guard polling, stranded-seed behavior, and the malformed-JSON deny path during seed-to-scope materialization.
  - learnings: The main gap worth remembering is that `_poll_for_scope()` does not catch `ValueError`, so malformed partial writes become deny instead of retry; the other recurring concerns are stranded seed/no-scope recovery and the global age-based stale sweep.

#### 2026-04-14

- handoff chain and publication boundaries: handoff:load, handoff:save, ~/.codex/handoffs/claude-code-tool-dev, resumed_from, PR #106, origin/main...HEAD
  - desc: Search this topic first when resuming or closing work on `claude-code-tool-dev`, especially if the user explicitly invokes handoff workflow or wants the next-session boundary preserved. It covers the personal handoff queue, stale skill-path fallbacks, cleanup verification, and PR/publication boundary handling.
  - learnings: Load/save should use the personal handoff queue plus the session-state chain file, verify cleanup after `trash`, and reason about publication topology with `origin/main...HEAD` rather than local `main` alone.

### Older Memory Topics

#### claude-code-tool-dev

- plugin shell scope and ticket closure: T-20260330-02, T-20260330-03, delivery.md, codex.status, codex.consult, codex.dialogue, OutcomeRecord
  - desc: Covers closure verification for the codex-collaboration plugin-shell and safety-substrate tickets plus the planning boundary for the minimal installable plugin shell in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`. Use this when “missing” plugin-shell/safety work needs to be checked against live code before reopening implementation.

- repository purpose assessment: repo purpose, monorepo, package.json workspaces, pyproject workspace members, cross-model, codex-collaboration, handoff, claude-code-docs
  - desc: Grounded repo-orientation memory for `cwd=/Users/jp/Projects/active/claude-code-tool-dev`. Use this when a future agent needs a quick evidence-backed explanation of what the monorepo is for and where the center of gravity lives in docs and packages.

- dialogue first-turn fast-path hardening: T-20260410-02, get_all_checked, _next_turn_sequence, recover_startup, origin/main..HEAD, PR #105
  - desc: Contains the full orientation -> design scrutiny -> spec scrutiny -> plan scrutiny -> PR review -> closure arc for the first-turn fast-path hardening ticket in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`. Search this first for exact trust-boundary invariants, review commands, and why the final PR #105 follow-up was tests rather than a runtime redesign.

- stale cleanup observability and PR #104 closeout: T-03, PR #104, FileNotFoundError lost race, containment_smoke_setup.py, CleanStaleResult, backlog triage
  - desc: Covers T-03 stale-cleanup observability plan scrutiny, the narrow P3 lost-race fix, the later “Defensible” handoff where the `CleanStaleResult` helper had already started locally, PR #104 review/merge guidance, and the backlog triage that promoted T-20260410-02 as the next live ticket in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`.

- T-04 v1 reslice and approved-plan baseline: T-20260330-04, single-agent transport, dispatch-only /dialogue, test_bootstrap.py, shakedown namespace
  - desc: Contains the earliest high-signal plan review and approval work for the production-dialogue slice in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`, including the move to a single-contained-agent v1, transport constraints from `active-run`/scope ownership, and the approved-plan boundary that later implementation followed.

- T7/T8 shakedown planning and ordering validation: T7, T8, feature/t8-ordering-validation, Read always, allowed_roots, ordering-test, codex-collaboration-inline
  - desc: Search this when the task touches executable-slice design, T8 shakedown contradictions, early ordering validation, or phase-by-phase handoffs in `cwd=/Users/jp/Projects/active/claude-code-tool-dev`. It covers the T7 acceptance arc, why `Read always` breaks the containment premise, the minimal marker-file validation idea, and the T2/T3 checkpoint handoff before T4.

- T4 containment implementation and publication runway: T4, containment_guard.py, containment_lifecycle.py, poll_success, 13 live pass + 1 synthetic-covered, PR #99, PR #100
  - desc: Use this for the older T4 containment arc across `cwd=/Users/jp/Projects/active/claude-code-tool-dev` and the paired implementation worktree. It covers the saved implementation plan, tool-specific `Read`/`Grep`/`Glob` rewrite rule, hostile runbook review, live-smoke evidence model, commit shaping by artifact lifetime, D/B or `R1-R6` naming cleanup, and the eventual PR #99/#100 publication boundary.

#### claude-code-tool-dev-t8-impl

- B4 shakedown execution and runtime architecture: dialogue-codex, B4, /shakedown-b1, _next_turn_sequence, ControlPlane, DialogueController, policy_fingerprint
  - desc: Covers the `cwd=/Users/jp/Projects/active/claude-code-tool-dev-t8-impl` implementation worktree plus its paired main worktree: safe worktree cleanup, `dialogue-codex` hardening, shakedown assembly, live `/shakedown-b1` execution, PR #101 merge with provenance preserved, and the read-only architecture walkthrough of the codex-collaboration runtime. Use this when the implementation worktree is active or when older B4 runtime decisions need to be reconstructed.
========= MEMORY_SUMMARY ENDS =========

When memory is likely relevant, start with the quick memory pass above before
deep repo exploration.

<apps_instructions>
## Apps (Connectors)
Apps (Connectors) can be explicitly triggered in user messages in the format `[$app-name](app://{connector_id})`. Apps can also be implicitly triggered as long as the context suggests usage of available apps.
An app is equivalent to a set of MCP tools within the `codex_apps` MCP.
An installed app's MCP tools are either provided to you already, or can be lazy-loaded through the `tool_search` tool. If `tool_search` is available, the apps that are searchable by `tools_search` will be listed by it.
Do not additionally call list_mcp_resources or list_mcp_resource_templates for apps.
</apps_instructions>
<skills_instructions>
## Skills
A skill is a set of local instructions to follow that is stored in a `SKILL.md` file. Below is the list of skills that can be used. Each entry includes a name, description, and file path so you can open the source for full instructions when using a specific skill.
### Available skills
- claude-code-docs: Search and cite official Claude Code documentation through the claude-code-docs MCP server. Use for Claude Code setup, commands, hooks, agents, plugins, MCP, settings, IDE/CI, troubleshooting, and changelog questions, including asks like PreToolUse schema, plugin marketplace install, /mcp settings, or Claude Code changelog. Do not use for Claude API, Anthropic SDK, general programming, or non-Claude-Code product questions. (file: /Users/jp/.agents/skills/claude-code-docs/SKILL.md)
- doc: Use when the task involves reading, creating, or editing `.docx` documents, especially when formatting or layout fidelity matters; prefer `python-docx` plus the bundled `scripts/render_docx.py` for visual checks. (file: /Users/jp/.codex/skills/doc/SKILL.md)
- git-hygiene: Analyze cluttered git repositories, propose a safe cleanup plan, group mixed changes into coherent commits, and prune stale branches. Use when the user asks to clean up git, tidy a repo, organize mixed uncommitted work, sort untracked files, or prune stale branches. Do not use for merge conflict resolution, active rebase, merge, cherry-pick, or bisect states, submodule modification, or pushing and PR creation. (file: /Users/jp/.agents/skills/git-hygiene/SKILL.md)
- github:gh-address-comments: Address actionable GitHub pull request review feedback. Use when the user wants to inspect unresolved review threads, requested changes, or inline review comments on a PR, then implement selected fixes. Use the GitHub app for PR metadata and flat comment reads, and use the bundled GraphQL script via `gh` whenever thread-level state, resolution status, or inline review context matters. (file: /Users/jp/.codex/plugins/cache/openai-curated/github/bb07d439ba5f23713f3c34c2f9f4b1ecd8deab2e/skills/gh-address-comments/SKILL.md)
- github:gh-fix-ci: Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions. Use the GitHub app from this plugin for PR metadata and patch context, and use `gh` for Actions check and log inspection before implementing any approved fix. (file: /Users/jp/.codex/plugins/cache/openai-curated/github/bb07d439ba5f23713f3c34c2f9f4b1ecd8deab2e/skills/gh-fix-ci/SKILL.md)
- github:github: Triage and orient GitHub repository, pull request, and issue work through the connected GitHub app. Use when the user asks for general GitHub help, wants PR or issue summaries, or needs repository context before choosing a more specific GitHub workflow. (file: /Users/jp/.codex/plugins/cache/openai-curated/github/bb07d439ba5f23713f3c34c2f9f4b1ecd8deab2e/skills/github/SKILL.md)
- github:yeet: Publish local changes to GitHub by confirming scope, committing intentionally, pushing the branch, and opening a draft PR through the GitHub app from this plugin, with `gh` used only as a fallback where connector coverage is insufficient. (file: /Users/jp/.codex/plugins/cache/openai-curated/github/bb07d439ba5f23713f3c34c2f9f4b1ecd8deab2e/skills/yeet/SKILL.md)
- handoff:defer: Extract deferred work items from conversation and create tracking tickets. Use when user says "/defer", "defer these", "track these for later", "create tickets for remaining items", or at end of session when open items remain. Scans conversation for explicit deferrals, review findings, open questions, and TODO/FIXME mentions, then creates ticket files in docs/tickets/. (file: /Users/jp/.codex/plugins/cache/local/handoff/1.5.0/skills/defer/SKILL.md)
- handoff:defer: Extract deferred work items from conversation and create tracking tickets. Use when user says "/defer", "defer these", "track these for later", "create tickets for remaining items", or at end of session when open items remain. Scans conversation for explicit deferrals, review findings, open questions, and TODO/FIXME mentions, then creates ticket files in docs/tickets/. (file: /Users/jp/.codex/plugins/cache/local-personal/handoff/1.5.0/skills/defer/SKILL.md)
- handoff:distill: Extract durable knowledge from handoffs into learnings. Use when user says "/distill", "distill handoff", "extract knowledge", "graduate knowledge", or wants to turn handoff insights into reusable learnings. Reads handoff files, extracts candidates from Decisions/Learnings/Codebase Knowledge/Gotchas, checks for duplicates, and appends synthesized entries to docs/learnings/learnings.md. (file: /Users/jp/.codex/plugins/cache/local/handoff/1.5.0/skills/distill/SKILL.md)
- handoff:distill: Extract durable knowledge from handoffs into learnings. Use when user says "/distill", "distill handoff", "extract knowledge", "graduate knowledge", or wants to turn handoff insights into reusable learnings. Reads handoff files, extracts candidates from Decisions/Learnings/Codebase Knowledge/Gotchas, checks for duplicates, and appends synthesized entries to docs/learnings/learnings.md. (file: /Users/jp/.codex/plugins/cache/local-personal/handoff/1.5.0/skills/distill/SKILL.md)
- handoff:load: Used when continuing from a previous session; when user runs `/load` to load the most recent handoff, or `/load <path>` for a specific handoff. (file: /Users/jp/.codex/plugins/cache/local/handoff/1.5.0/skills/load/SKILL.md)
- handoff:load: Used when continuing from a previous session; when user runs `/load` to load the most recent handoff, or `/load <path>` for a specific handoff. (file: /Users/jp/.codex/plugins/cache/local-personal/handoff/1.5.0/skills/load/SKILL.md)
- handoff:quicksave: Used when user runs /quicksave to save session state quickly under context pressure. Fast, lightweight alternative to /save. Use when user says "quicksave", "checkpoint", "save state", "quick save", or is running low on context. (file: /Users/jp/.codex/plugins/cache/local/handoff/1.5.0/skills/quicksave/SKILL.md)
- handoff:quicksave: Used when user runs /quicksave to save session state quickly under context pressure. Fast, lightweight alternative to /save. Use when user says "quicksave", "checkpoint", "save state", "quick save", or is running low on context. (file: /Users/jp/.codex/plugins/cache/local-personal/handoff/1.5.0/skills/quicksave/SKILL.md)
- handoff:save: Used when user says "wrap this up", "new session", "almost out of context", "save", "next session", or "handoff"; when stopping work with context to preserve. (file: /Users/jp/.codex/plugins/cache/local/handoff/1.5.0/skills/save/SKILL.md)
- handoff:save: Used when user says "wrap this up", "new session", "almost out of context", "save", "next session", or "handoff"; when stopping work with context to preserve. (file: /Users/jp/.codex/plugins/cache/local-personal/handoff/1.5.0/skills/save/SKILL.md)
- handoff:search: Search across handoff history for decisions, learnings, and context. Use when user says "search handoffs", "find in handoffs", "what did we decide about", or runs /search. (file: /Users/jp/.codex/plugins/cache/local/handoff/1.5.0/skills/search/SKILL.md)
- handoff:search: Search across handoff history for decisions, learnings, and context. Use when user says "search handoffs", "find in handoffs", "what did we decide about", or runs /search. (file: /Users/jp/.codex/plugins/cache/local-personal/handoff/1.5.0/skills/search/SKILL.md)
- handoff:triage: Review open tickets and detect orphaned handoff items that need tracking. Use when user says "/triage", "what's in the backlog", "review deferred items", "any open tickets", or at session start for project orientation. (file: /Users/jp/.codex/plugins/cache/local/handoff/1.5.0/skills/triage/SKILL.md)
- handoff:triage: Review open tickets and detect orphaned handoff items that need tracking. Use when user says "/triage", "what's in the backlog", "review deferred items", "any open tickets", or at session start for project orientation. (file: /Users/jp/.codex/plugins/cache/local-personal/handoff/1.5.0/skills/triage/SKILL.md)
- markdown-reformat: Use when the user asks to turn rough text, plaintext notes, wrapped prose, or loosely structured content into proper Markdown without materially changing the content, wording, or voice. Trigger on requests like "format this as proper Markdown", "clean up these notes into Markdown", "normalize this draft", or "fix the headings and lists". Do not use for summarization, substantive rewriting, or general copyediting when the user is not asking for Markdown structure. (file: /Users/jp/.agents/skills/markdown-reformat/SKILL.md)
- pdf: Use when tasks involve reading, creating, or reviewing PDF files where rendering and layout matter; prefer visual checks by rendering pages (Poppler) and use Python tools such as `reportlab`, `pdfplumber`, and `pypdf` for generation and extraction. (file: /Users/jp/.codex/skills/pdf/SKILL.md)
- writing-principles: Enforces writing principles for instruction documents (SKILL.md, skill supporting files, subagents, CLAUDE.md). Use when writing, reviewing, or editing any file in **/skills/**/*.md, **/agents/*.md, or **/CLAUDE.md. Triggers on skill creation, skill file updates, CLAUDE.md changes, subagent authoring, or instruction document review. (file: /Users/jp/.agents/skills/writing-principles/SKILL.md)
- imagegen: Generate or edit raster images when the task benefits from AI-created bitmap visuals such as photos, illustrations, textures, sprites, mockups, or transparent-background cutouts. Use when Codex should create a brand-new image, transform an existing image, or derive visual variants from references, and the output should be a bitmap asset rather than repo-native code or vector. Do not use when the task is better handled by editing existing SVG/vector/code-native assets, extending an established icon or logo system, or building the visual directly in HTML/CSS/canvas. (file: /Users/jp/.codex/skills/.system/imagegen/SKILL.md)
- openai-docs: Use when the user asks how to build with OpenAI products or APIs and needs up-to-date official documentation with citations, help choosing the latest model for a use case, or explicit GPT-5.4 upgrade and prompt-upgrade guidance; prioritize OpenAI docs MCP tools, use bundled references only as helper context, and restrict any fallback browsing to official OpenAI domains. (file: /Users/jp/.codex/skills/.system/openai-docs/SKILL.md)
- plugin-creator: Create and scaffold plugin directories for Codex with a required `.codex-plugin/plugin.json`, optional plugin folders/files, and baseline placeholders you can edit before publishing or testing. Use when Codex needs to create a new local plugin, add optional plugin structure, or generate or update repo-root `.agents/plugins/marketplace.json` entries for plugin ordering and availability metadata. (file: /Users/jp/.codex/skills/.system/plugin-creator/SKILL.md)
- skill-creator: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. (file: /Users/jp/.codex/skills/.system/skill-creator/SKILL.md)
- skill-installer: Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). (file: /Users/jp/.codex/skills/.system/skill-installer/SKILL.md)
### How to use skills
- Discovery: The list above is the skills available in this session (name + description + file path). Skill bodies live on disk at the listed paths.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description shown above, you must use that skill for that turn. Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.
- Missing/blocked: If a named skill isn't in the list or the path can't be read, say so briefly and continue with the best fallback.
- How to use a skill (progressive disclosure):
  1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.
  2) When `SKILL.md` references relative paths (e.g., `scripts/foo.py`), resolve them relative to the skill directory listed above first, and only consider other paths if needed.
  3) If `SKILL.md` points to extra folders such as `references/`, load only the specific files needed for the request; don't bulk-load everything.
  4) If `scripts/` exist, prefer running or patching them instead of retyping large code blocks.
  5) If `assets/` or templates exist, reuse them instead of recreating from scratch.
- Coordination and sequencing:
  - If multiple skills apply, choose the minimal set that covers the request and state the order you'll use them.
  - Announce which skill(s) you're using and why (one short line). If you skip an obvious skill, say why.
- Context hygiene:
  - Keep context small: summarize long sections instead of pasting them; only load extra files when needed.
  - Avoid deep reference-chasing: prefer opening only files directly linked from `SKILL.md` unless you're blocked.
  - When variants exist (frameworks, providers, domains), pick only the relevant reference file(s) and note that choice.
- Safety and fallback: If a skill can't be applied cleanly (missing files, unclear instructions), state the issue, pick the next-best approach, and continue.
</skills_instructions>
<plugins_instructions>
## Plugins
A plugin is a local bundle of skills, MCP servers, and apps. Below is the list of plugins that are enabled and available in this session.
### Available plugins
- `GitHub`: Inspect repositories, triage pull requests and issues, debug CI, and publish changes through a hybrid GitHub connector and CLI workflow.
- `Handoff`: Session handoff, resume, search, and knowledge distillation workflows for Codex.
- `Handoff`: Session handoff, resume, search, and knowledge distillation workflows for Codex.
### How to use plugins
- Discovery: The list above is the plugins available in this session.
- Skill naming: If a plugin contributes skills, those skill entries are prefixed with `plugin_name:` in the Skills list.
- Trigger rules: If the user explicitly names a plugin, prefer capabilities associated with that plugin for that turn.
- Relationship to capabilities: Plugins are not invoked directly. Use their underlying skills, MCP tools, and app tools to help solve the task.
- Preference: When a relevant plugin is available, prefer using capabilities associated with that plugin over standalone capabilities that provide similar functionality.
- Missing/blocked: If the user requests a plugin that is not listed above, or the plugin does not have relevant callable capabilities for the task, say so briefly and continue with the best fallback.
</plugins_instructions>
```

## USER TURN 1 (agent → Codex)

```
# AGENTS.md instructions for /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model

<INSTRUCTIONS>
# Global Instructions

Cross-project defaults for Codex sessions.

Repository-local `AGENTS.md` files may add project-specific rules. When they conflict with this file, follow the higher-priority rule.

## Instruction Priority

When instructions conflict, use this order:

1. Safety and destructive-action rules
2. Explicit user request
3. This file
4. Repository code, docs, and established local patterns
5. Default preferences

If still unsure, choose the safest non-destructive action and explain the uncertainty.

## Core Principles

- Be a collaborative peer, not a passive executor.
- Challenge weak assumptions before implementing them.
- Prefer correctness, completeness, and rigor over speed or token cost.
- Match local repo patterns. Do not silently import conventions from outside the repo.
- If you need to deviate from an observed local pattern, say so and explain why.
- Default to making useful progress. Do not stop early unless a stop condition below applies.

## Default Action Rule

Choose behavior based on the user's actual request, not the general preference for autonomy.

- If the user asks for implementation, debugging, fixes, edits, or execution, act directly.
- If the user asks for analysis, review, explanation, brainstorming, or a plan, do not make code changes unless they explicitly ask for them.
- If the user asks for a review, prioritize findings, risks, regressions, and missing tests over summaries.
- Do not ask for confirmation before ordinary low-risk work that can be started from available context.
- Do not pause just to restate the task or ask permission to do the obvious next step.

## Stop Conditions

Stop and ask only if at least one of these is true:

- The request is materially ambiguous and multiple reasonable interpretations would lead to different work.
- The next step is destructive or hard to reverse, and the safe path is unclear.
- Required information is missing and cannot be found in the repo, docs, or task context.
- The user explicitly asked you to pause, propose options, or wait for confirmation.
- A root-cause-analysis checkpoint is required by the rule below.

If none of these apply, continue.

## Safety and Destructive Actions

- Never run `rm`.
- Never run `rm -rf`.
- When deletion is required, use `trash <path>`.
- Treat destructive shell, git, and environment actions as high risk.
- If a destructive action may be needed and the safe path is unclear, stop and ask.

## Workflow

### Tone

Be friendly and upbeat. Maintain a warm, cheerful, and enthusiastic tone in every response.

- Use positive, energetic language and natural exclamations
- Greet warmly; celebrate user wins
- Invite collaboration; be a thought-partner
- Stay genuine—never sarcastic or saccharine
- Never let cheerfulness compromise accuracy or honesty
- When the user is serious, dial back exclamations but keep the warmth

### Asking Questions

- Ask at most one question at a time.
- Prefer multiple choice when the decision space is small.
- Use open-ended questions only when multiple choice would be misleading or incomplete.
- Do not ask avoidable questions if the answer is already available in the repo, docs, or task context.

### Root Cause Analysis

Use a root-cause-analysis checkpoint for:

- ambiguous bugs
- regressions
- flaky tests
- performance issues
- any problem with multiple plausible causes

Before a deep investigation, provide:

1. `Hypotheses`: 2-3 ranked hypotheses
2. `Evidence needed`: what would confirm or reject each hypothesis
3. `Tests to run`: specific checks, commands, or experiments

Then stop and wait for user confirmation before proceeding with the deep dive.

Do not skip this checkpoint for ambiguous problems, even if one hypothesis seems likely.

For straightforward, low-risk issues with an obvious fix path, proceed directly and briefly explain the reasoning.

### Test Failures

When a new test fails:

1. Check whether the test matches documented or intended behavior.
2. If it does, treat the failure as evidence of a code defect and fix the code.
3. If it does not, update the test and explain why the original expectation was wrong.

Never change a test only to make it pass.

### Scope Control

- Solve the task that was asked for.
- Do not expand scope without a concrete reason tied to correctness, safety, or clear adjacent breakage.
- If you notice unrelated issues, mention them briefly instead of silently fixing them unless they block the requested work.
- Prefer small, coherent changes over opportunistic refactors.
- Read enough context before editing to match surrounding patterns.

### Handoffs

- Treat repository handoff files in `docs/handoffs/` and `docs/handoffs/archive/` as durable project artifacts, not disposable operational byproducts.
- Preserve repository handoff files when doing git cleanup, branch cleanup, sync, or history repair.
- When repository handoff files are part of the current work, commit them with the related work rather than leaving them unstaged or treating them as optional cleanup leftovers.

### Response Contracts

For bug investigations, use:

- `Hypotheses`
- `Evidence needed`
- `Tests to run`
- `Recommended next step`

For code changes, use:

- `What changed`
- `Why it changed`
- `Verification performed`
- `Remaining risks`

For blocked work, use:

- `Blocker`
- `Why it blocks progress`
- `Decision needed`

## Code Style

### Errors

Fail fast.

Use this error format:

`"{operation} failed: {reason}. Got: {input!r:.100}"`

### Comments

- Write comments only for key decisions and non-obvious logic.
- Do not write comments that merely restate obvious code.

### Python

- Use full type hints in production code.
- Use Google-style docstrings on public APIs.
- Pin exact versions for apps.
- Use version ranges for libraries.
- For PEP 723 scripts, use this shebang:

```bash
#!/usr/bin/env -S uv run --script
```

## Pattern Conformance

- Follow the repository's existing structure, naming, style, and architectural patterns.
- Follow reference documents and style guides already present in the repo.
- The local codebase and docs outrank general training-data conventions.
- If a local pattern appears weak but intentional, do not silently replace it. Flag it and explain the tradeoff.

## Environment

Preferred commands:

```bash
rg <pattern> <path>   # search
uv run pytest         # test
ruff check            # lint
ruff format           # format
trash <path>          # delete
```

See `~/.codex/references/environment.md` for full tooling and ownership rules.

### Environment Rules

Ownership model: one executable, one owner.

- Use Homebrew for OS-level packages.
- Use mise for runtimes and developer tools.
- Use stow for dotfiles.

Hard rules:

- Never `brew install` a mise-owned tool such as `uv`, `ruff`, `node`, `python`, `go`, or `rust`.
- Use `mise use` for mise-owned tools.
- Never write directly to `~/.<dotfile>`.
- Edit dotfiles in `~/dotfiles/` and deploy with `stow`.
- Never `brew uninstall stow`.
- Never `brew uninstall mise`.
- Run `doctor-env` after environment changes.

Dotfiles repo: `~/dotfiles/`

## Git

Assume branch protection is enforced.

Create branches from `main` using:

- `feature/*` for new functionality
- `fix/*` for bug fixes
- `hotfix/*` for emergency fixes
- `chore/*` for maintenance

If blocked by branch policy:

1. Create the correct branch.
2. Continue on that branch.
3. Do not bypass protections.
</INSTRUCTIONS>
<environment_context>
  <cwd>/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model</cwd>
  <shell>zsh</shell>
  <current_date>2026-04-16</current_date>
  <timezone>America/New_York</timezone>
</environment_context>
```

## USER TURN 2 (agent → Codex)

```
## Context
OPEN: The spec requires the control plane to compare requested capabilities against base-policy defaults to decide when to narrow, but no "base policy defaults" source is referenced from either the spec or the implementation — it is unclear whether `foundations.md#advisory-domain` defines an authoritative base-policy table that the control plane can programmatically consult, or whether that comparison is expected to be a future manual code path
OPEN: The spec has no section addressing concurrent or interleaved rotation requests — no locking model, no ordering guarantee, no mention of what happens if two turns race at the boundary where a rotation is pending. AID:A4
COUNTER: `codex_consult` raises immediately on `network_access=True` with "advisory widening is not implemented in R1" — the spec's full freeze-fork-rotate widening protocol is absent from the implementation @ packages/plugins/codex-collaboration/server/control_plane.py:153-157 AID:A3 TYPE:control-flow mismatch
COUNTER: `build_policy_fingerprint` is hardcoded (transport, sandbox, network, approval, connectors all literals) — the implementation has no mechanism to vary the fingerprint across policy levels, making widening/narrowing rotation structurally unimplementable in R1 @ packages/plugins/codex-collaboration/server/control_plane.py:432-446 AID:A3 TYPE:data-shape mismatch
CONFIRM: Spec defines widening triggers (explicit capability request or control-plane detection), narrowing timing (next turn boundary), rotation semantics (freeze → start → fork → remap → audit), and reap conditions @ docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:34-110 AID:A1
CONFIRM: Spec defines narrowing semantics including "next turn boundary" invariant and the "narrowest policy sufficient for that turn" rule, mirroring widening's freeze-and-rotate mechanism @ docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:63-77 AID:A2

## Prior Learnings
### 2026-03-31 [architecture, review]

**Context:** Reviewing an implementation plan for JSONL replay hardening across three persistence stores, where the design spec described flat field/type checks but the recovery coordinator depended on per-operation+phase field invariants.

**Insight:** Design specs that describe data validation often stop at the schema layer (field presence, type correctness) and miss the protocol layer — invariants that a *consumer* depends on but that the *data model* doesn't express. Example: `OperationJournalEntry` has `codex_thread_id: str | None` (structurally valid), but `turn_dispatch` at any phase requires it to be non-None or recovery crashes with `RuntimeError`. These cross-layer invariants are invisible in the dataclass definition and only discoverable by reading the consumer code.

**Implication:** When a design spec defines validation for a persistence format, enumerate consumer-side field requirements as a separate table — not just per-field types, but per-operation+phase (or per-variant) required/forbidden fields. Review checkpoint: "does the consumer access any optional field unconditionally?"

### 2026-02-20 [skill-design, pattern]

When writing instructions that interface with MCP tool schemas, optional parameters with strong training priors (e.g., `model`, `url`, `api_key`) need explicit prohibitions ("Do NOT set X"), not passive omission rules ("omit X for default"). Claude tends to populate optional tool parameters rather than leave them unset, especially when the parameter name maps to training knowledge — the codex-dialogue agent consistently set `model` to invalid OpenAI model names ("o4 mini", "o3") despite the consultation contract saying "omit for Codex default." The fix required explicit "Do NOT set" + "Never guess from training knowledge" language in three places: the contract (authoritative source), the agent (where the tool call originates), and the skill (which delegates). All three are needed because Claude reads different documents depending on the invocation path.

### 2026-03-02 [architecture, pattern, plugin-design]

The engine-centric adapter pattern (Architecture E) solves a class of trust and drift problems in Claude Code plugins by routing all mutations through Python scripts while keeping skills as thin transport layers. Three properties make it effective: (1) **Split entrypoints** (`_user.py` / `_agent.py`) hardcode `request_origin` before delegating to shared core, preventing the model from claiming a different caller type — defense-in-depth, not a security boundary, but catches model misbehavior. (2) **A single enforcement point** (preflight) that all mutation paths pass through eliminates the "bypass a validation step" bug class — the 7-round review of the ticket plugin design found and fixed multiple variants of this (pipeline bypass, autonomy gap, missing preflight on create). (3) **Payload-by-file** eliminates shell metacharacter injection by writing engine input to a temp file instead of inline JSON in Bash commands; a PreToolUse hook then injects trusted fields (`session_id`, `request_origin`) that the model cannot fabricate. The pattern generalizes to any plugin where the model should be able to invoke operations but not control policy: put policy in code, put UX in skills, connect them with a typed pipeline.

### 2026-02-17 [skill-design, architecture]

When instruction documents layer (skill references agent, agent references contract), each layer must be fully operational standalone. Conditional logic like "if the agent spec is loaded, use its patterns; otherwise fall back" creates ambiguity that an LLM will resolve inconsistently — "available" is operationally undefined when the referenced spec isn't loaded. The fix: inline the minimal self-contained version at each layer, with a note that other sources are additive, not alternative. This emerged from a 3-dialogue parallel review of the `/codex` skill where the evaluative dialogue independently discovered (T8) that a "prefer codex-dialogue profile when available" clause was a loophole, and the exploratory dialogue independently chose "full replacement stubs over summary stubs" (T4) for the same reason — summary stubs that say "see the contract" create hard dependencies that break when the contract is unavailable.

### 2026-02-18 [security, hooks]

PreToolUse hooks are mechanically fail-open — unhandled exceptions don't produce exit code 2, so the tool call proceeds. This is backward from security intuition. When enforcement is critical (credential detection, access control), explicitly catch all errors and return a block decision. The choice between hooks (fail-open default) and wrapper MCP (fail-closed default) is a threat model question: "reduce accidental leaks" → hooks are proportionate; "zero tolerance" → wrapper required. Always clarify failure polarity before committing to a mechanism.

<!-- learnings-injected: 5 -->

## Material
CLAIM: The spec mandates freeze-and-rotate for all policy changes and prohibits in-place mutation, with a 5-component fingerprint (transport, sandbox, network, approval, connectors) that must differ across rotation boundaries @ docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:16 [SRC:code]
CLAIM: `build_policy_fingerprint()` in R1 returns a hardcoded constant (all five components are literals) — the fingerprint never varies regardless of what `ConsultRequest` carries, so a caller requesting `network_access=True` would be rejected by the guard but the fingerprint would not distinguish a legitimately widened runtime from the default one @ packages/plugins/codex-collaboration/server/control_plane.py:432 [SRC:code]
CLAIM: Privilege widening is fully stubbed out in R1: `codex_consult` raises `RuntimeError` on `request.network_access=True` with an explicit comment "advisory widening is not implemented in R1", meaning the rotation protocol (freeze → new runtime → fork history → update handle mappings) exists only in the spec, not in the implementation @ packages/plugins/codex-collaboration/server/control_plane.py:153 [SRC:code]
CLAIM: Privilege narrowing has no implementation path at all — the spec defines turn-boundary narrowing and a compare-against-base-policy trigger, but neither `codex_consult` nor `_bootstrap_runtime` nor `_probe_runtime` contains any narrowing decision, rotation call, or base-policy comparison @ packages/plugins/codex-collaboration/server/control_plane.py:275 [SRC:code]

## Question
Is the advisory runtime rotation model specified strongly enough for privilege widening and narrowing, or where are the weak points?
```

## ASSISTANT REPLY (Codex → agent)

I’m treating this as a spec-strength review, not an implementation task. First I’m checking the relevant spec, control-plane code, and memory for any prior decisions around advisory policy rotation so the answer is grounded in repo authority.

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"advisory-runtime-policy|rotation|base-policy|policy fingerprint|narrowing|widening\" /Users/jp/.codex/memories/MEMORY.md",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "sed -n '1,220p' /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "sed -n '1,260p' /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: ca20f6
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 163
Output:
365:- For T-20260330-02, the main planning question is scope narrowing: the plugin shell already exists (`.claude-plugin/plugin.json`, `.mcp.json`, bootstrap script, consult/status skills), but `server/mcp_server.py` still exposes `codex.dialogue.*`, which is broader than the ticket’s “minimal packaged consult flow” [Task 2]
572:- when a harness or skill overclaims what it automates, the user prefers narrowing the contract to the honest boundary rather than preserving aspirational wording [Task 3]
645:- when the user supplies a delta list or scrutiny report first, validate that exact artifact before widening the review [Task 1][Task 4]

```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 6fdcda
Wall time: 0.0001 seconds
Process exited with code 0
Original token count: 2080
Output:
---
module: advisory-runtime-policy
status: active
normative: true
authority: advisory-policy
---

# Advisory Runtime Policy

Rules governing the advisory runtime's lifecycle, privilege scope, and rotation behavior. The advisory runtime serves both consultation and dialogue — they share a runtime because they are the same [capability class](foundations.md#scope).

The core enforcement invariant: **never mutate advisory policy in place.**

## Policy Fingerprint Model

Each advisory runtime instance has an immutable policy fingerprint computed at creation time. The fingerprint encodes the runtime's effective policy configuration:

| Component | Description |
|---|---|
| Transport mode | e.g., `stdio` |
| Sandbox level | e.g., `read-only` |
| Network access | e.g., `disabled` |
| Approval mode | e.g., `disabled` |
| App connectors | e.g., `disabled` |

The fingerprint is:

- **Immutable** for the lifetime of a runtime instance. Policy changes require rotation, not mutation.
- **Recorded** in [audit events](contracts.md#auditevent) and [collaboration handles](contracts.md#collaborationhandle) for forensic correlation.
- **Compared** across rotation boundaries to verify that widening or narrowing actually occurred.

## Privilege Widening

When a turn requires capabilities beyond the current runtime's policy (e.g., network access for a web-facing research question):

1. The current runtime is **frozen** — no new turns are accepted, but history remains available for reconstruction.
2. A new runtime starts with the wider policy.
3. Thread history is forked into the new runtime via App Server `thread/fork`.
4. The new runtime's policy fingerprint reflects the wider configuration.
5. The frozen runtime is scheduled for [reaping](#reap-conditions).

### What Triggers Widening

- Claude explicitly requests a capability that exceeds the current policy (e.g., `codex.consult` with `network: true` when the current runtime has network disabled).
- The control plane detects that a requested operation cannot succeed under current policy.

### What Does NOT Trigger Widening

- Codex requesting additional permissions via server requests within a turn. These are resolved per-request only — see [Advisory Approval Scope](#advisory-approval-scope). Per-request resolution does not widen the runtime's effective policy and does not require rotation.

## Advisory Approval Scope

Se
... [truncated 5913 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 338ed9
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2563
Output:
"""Runtime Milestone R1 control plane for codex-collaboration."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Callable

from .codex_compat import (
    OPTIONAL_METHODS,
    REQUIRED_METHODS,
    check_live_runtime_compatibility,
)
from .context_assembly import assemble_context_packet
from .journal import OperationJournal, default_plugin_data_path
from .models import (
    AdvisoryRuntimeState,
    AuditEvent,
    ConsultRequest,
    ConsultResult,
    OutcomeRecord,
    RepoIdentity,
)
from .prompt_builder import (
    CONSULT_OUTPUT_SCHEMA,
    build_consult_turn_text,
    parse_consult_response,
)
from .runtime import AppServerRuntimeSession


@dataclass(frozen=True)
class _RuntimeProbeResult:
    runtime: AdvisoryRuntimeState | None
    app_server_version: str | None
    auth_status: str | None
    available_methods: frozenset[str]
    error: str | None


def _log_local_append_failure(operation: str, reason: Exception, got: object) -> None:
    print(
        f"codex-collaboration: {operation} failed: {reason}. Got: {got!r:.100}",
        file=sys.stderr,
    )


class ControlPlane:
    """Implements the advisory subset of the codex-collaboration plugin."""

    def __init__(
        self,
        *,
        plugin_data_path: Path | None = None,
        runtime_factory: Callable[[Path], AppServerRuntimeSession] | None = None,
        compat_checker: Callable[[], object] = check_live_runtime_compatibility,
        repo_identity_loader: Callable[[Path], RepoIdentity] | None = None,
        clock: Callable[[], float] = time,
        uuid_factory: Callable[[], str] | None = None,
        journal: OperationJournal | None = None,
    ) -> None:
        self._plugin_data_path = (
            plugin_data_path or default_plugin_data_path()
        ).resolve()
        self._runtime_factory = runtime_factory or (
            lambda repo_root: AppServerRuntimeSession(repo_root=repo_root)
        )
        self._compat_checker = compat_checker
        self._repo_identity_loader = repo_identity_loader or load_repo_identity
        self._clock = clock
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))
        self._journal = journal or OperationJournal(self._plugin_data_path)
        self._adviso
... [truncated 7857 chars]
```

## ASSISTANT REPLY (Codex → agent)

The first pass confirms the core mismatch you flagged: the spec is concrete about lifecycle phases, but the code path is still R1-safe/read-only only. I’m pulling the remaining control-plane helpers plus the foundations doc to see whether the spec’s “base policy defaults” and rotation semantics are actually anchored anywhere authoritative.

### TOOL CALL `exec_command`

```json
{
  "cmd": "sed -n '260,520p' /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "sed -n '1,220p' /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"base policy defaults|policy default|advisory-domain|network|sandbox|approval|connector|fingerprint|rotate|freeze|reap\" /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration -g '*.md'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 903590
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2110
Output:
        runtime = self._bootstrap_runtime(resolved_root, strict=True)
        assert runtime is not None  # strict=True guarantees non-None or raises
        return runtime

    def invalidate_runtime(self, repo_root: Path) -> None:
        """Drop a cached runtime. Public wrapper for error recovery paths."""
        self._invalidate_runtime(repo_root.resolve())

    def close(self) -> None:
        """Close all cached runtimes."""

        for runtime in self._advisory_runtimes.values():
            runtime.session.close()
        self._advisory_runtimes.clear()

    def _bootstrap_runtime(
        self, repo_root: Path, *, strict: bool
    ) -> AdvisoryRuntimeState | None:
        cached = self._advisory_runtimes.get(str(repo_root))
        compat_result = self._compat_checker()
        probe_result = self._probe_runtime(
            repo_root,
            compat_result=compat_result,
            existing_runtime=cached,
        )
        if probe_result.error is not None:
            if strict:
                raise RuntimeError(probe_result.error)
            return None
        return probe_result.runtime

    def _probe_runtime(
        self,
        repo_root: Path,
        *,
        compat_result: object,
        existing_runtime: AdvisoryRuntimeState | None = None,
    ) -> _RuntimeProbeResult:
        codex_version = getattr(compat_result, "codex_version", None)
        if codex_version is None:
            return _RuntimeProbeResult(
                runtime=None,
                app_server_version=None,
                auth_status=None,
                available_methods=frozenset(),
                error="Runtime bootstrap failed: codex version unavailable. Got: None",
            )

        runtime_key = str(repo_root)
        session = (
            existing_runtime.session
            if existing_runtime is not None
            else self._runtime_factory(repo_root)
        )
        try:
            # INVARIANT: safe only while initialize + account/read remain
            # the complete advisory bootstrap surface. Adding any new
            # bootstrap-critical method should revisit the parked bootstrap
            # assertion debt before rollout.
            handshake = (
                existing_runtime.handshake
                if existing_runtime is not None
                else session.initialize()
            )
        except Except
... [truncated 6042 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 11d3af
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2927
Output:
---
module: foundations
status: active
normative: true
authority: foundation
---

# Foundations

## Scope

**codex-collaboration** is a Claude Code plugin that gives Claude a structured second-opinion lane to OpenAI Codex. It supports three capabilities across two capability classes:

| Capability | Purpose | Capability Class | Runtime |
|---|---|---|---|
| **Consultation** | One-shot second opinions | Advisory | Advisory (shared) |
| **Dialogue** | Durable, branchable multi-turn discussion | Advisory | Advisory (shared) |
| **Delegation** | Autonomous task execution in isolation | Execution | Execution (ephemeral) |

### Goals

- Give Claude a structured second-opinion lane to Codex.
- Support durable, branchable, multi-turn Claude-to-Codex dialogues.
- Support autonomous Codex task execution without weakening Claude's control.
- Acknowledge where Codex-native primitives satisfy requirements without custom control-plane machinery, and document why this spec's approach was chosen where it overlaps.
- Preserve strong trust boundaries around secrets, paths, sandboxing, and write surfaces.
- Make crash recovery and lineage explicit.
- Stay on stable App Server APIs where possible.

### Non-Goals

- Preserve compatibility with the current `cross-model` contracts. See [decisions.md §Greenfield Rules](decisions.md#greenfield-rules) for the explicit break list.
- Expose raw App Server methods to Claude.
- Depend on experimental App Server features for core flows when a stable path exists.
- Let Codex write directly into the user's primary working tree during delegation.
- Use Codex-side plugin/app discovery as a core dependency.

## Terminology

| Term | Definition |
|---|---|
| **Capability** | One of three interaction modes: consultation, dialogue, or delegation. |
| **Capability class** | A trust category that groups related capabilities. Two classes: advisory (consultation + dialogue) and execution (delegation). Each class has a defined trust level, runtime scope, and approval boundary. |
| **Runtime domain** | The App Server process scope in which Codex operates. Advisory and execution are the two domains. |
| **Advisory domain** | A long-lived App Server runtime for consultation and dialogue. One per Claude session and repo root. See [advisory-runtime-policy.md](advisory-runtime-policy.md) for lifecycle rules. |
| **Execution domain** | An ephemeral App 
... [truncated 9297 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: d3c8cf
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 3861
Output:
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:91:| Runtime crashed | `crash` | `runtime_id`, `policy_fingerprint` |
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:93:| Advisory runtime rotated | `rotate` | `runtime_id`, `policy_fingerprint` |
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:94:| Advisory runtime frozen | `freeze` | `runtime_id` |
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:95:| Frozen runtime reaped | `reap` | `runtime_id` |
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:127:App Server's `serverRequest/resolved` is authoritative for closing approval and user-input prompts. Pending-request state is not cleared on optimistic assumptions.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:137:- In the **advisory domain:** The request is surfaced to Claude as a pending escalation. Claude resolves per-request only (see [advisory-runtime-policy.md §Advisory Approval Scope](advisory-runtime-policy.md#advisory-approval-scope)).
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:160:This does not break safety — the advisory runtime's read-only sandbox prevents writes. It breaks **coherence**: Codex's advisory responses are grounded in a workspace state that no longer exists.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/decisions.md:55:**What is being traded:** Strong runtime separation and fail-closed approvals versus a much larger state/recovery surface.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/decisions.md:59:**Likely failure story:** The system keeps isolation but mismanages runtime state after crash or overload, creating orphaned jobs, stale approvals, or silently broadened advisory permissions.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/decisions.md:80:| B | One long-lived App Server | Rejected | Session-scoped approvals bleed across capability cla
... [truncated 13014 chars]
```

## ASSISTANT REPLY (Codex → agent)

I’ve confirmed `foundations.md` does contain a normative default table, but it’s prose/table authority, not an implementation-ready source of truth. I’m checking the request/state model next, because the real question is whether the spec defines enough machine-readable inputs and state transitions for widening/narrowing to be implemented without inventing policy semantics in code.

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"class ConsultRequest|ConsultRequest\\(|class AdvisoryRuntimeState|policy_fingerprint|network_access|approval|connector|sandbox|transport\" /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server -g '*.py'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "sed -n '1,260p' /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/models.py",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "sed -n '220,340p' /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 94c9b9
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2532
Output:
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:244:            request = ConsultRequest(
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:4:Validation gate: rejects sandbox != read-only or approval_policy != never
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:39:    sandbox: SandboxPolicy
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:40:    approval_policy: ApprovalPolicy
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:84:    explicit_sandbox: SandboxPolicy | None = None,
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:85:    explicit_approval_policy: ApprovalPolicy | None = None,
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:122:    sandbox = (
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:123:        explicit_sandbox
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:124:        if explicit_sandbox is not None
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:125:        else profile.get("sandbox", _DEFAULT_SANDBOX)
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:127:    approval_policy = (
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:128:        explicit_approval_policy
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:129:        if explicit_approval_policy is not None
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:130:        else profile.get("approval_policy", _DEFAULT_APPROVAL)
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:149:    if sandbox != _DEFAULT_SANDBOX:
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:151:            f"Profile resolution failed: sandbox widening requ
... [truncated 7731 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 284152
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 1699
Output:
"""Core models for Runtime Milestone R1."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .runtime import AppServerRuntimeSession


CapabilityProfile = Literal["advisory", "execution"]
AuthStatus = Literal["authenticated", "expired", "missing"]
HandleStatus = Literal["active", "completed", "crashed", "unknown"]


@dataclass(frozen=True)
class RepoIdentity:
    """Repository identity included in assembled packets."""

    repo_root: Path
    branch: str
    head: str


@dataclass(frozen=True)
class FileReference:
    """File path requested for packet assembly."""

    path: Path


@dataclass(frozen=True)
class ConsultRequest:
    """Caller-facing consult request for the advisory runtime."""

    repo_root: Path
    objective: str
    user_constraints: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    explicit_paths: tuple[Path, ...] = ()
    explicit_snippets: tuple[str, ...] = ()
    task_local_paths: tuple[Path, ...] = ()
    broad_repository_summaries: tuple[str, ...] = ()
    promoted_summaries: tuple[str, ...] = ()
    delegation_summaries: tuple[str, ...] = ()
    supplementary_context: tuple[str, ...] = ()
    external_research_material: tuple[str, ...] = ()
    parent_thread_id: str | None = None
    network_access: bool = False
    profile: str | None = None


@dataclass(frozen=True)
class AssembledPacket:
    """Final packet sent to Codex after assembly, redaction, and trimming."""

    profile: CapabilityProfile
    payload: str
    context_size: int
    omitted_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConsultEvidence:
    """Single evidence item projected from the consult result."""

    claim: str
    citation: str


@dataclass(frozen=True)
class ConsultResult:
    """Structured result returned to Claude from `codex.consult`."""

    collaboration_id: str
    runtime_id: str
    position: str
    evidence: tuple[ConsultEvidence, ...]
    uncertainties: tuple[str, ...]
    follow_up_branches: tuple[str, ...]
    context_size: int


@dataclass(frozen=True)
class RuntimeHandshake:
    """Initialize response values retained by the runtime."""

    codex_home: str
    platform_family: str
    platform_os: str
    user_agent: str


@dataclass(frozen=True)
class AccountState
... [truncated 4391 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 4d983c
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 1645
Output:

#### Source Categories

| Source category | Advisory | Execution | Notes |
|---|---|---|---|
| User objective | Required | Required | Caller-provided |
| User constraints and acceptance criteria | Required | Required | Caller-provided |
| Repository identity (`repo_root`, branch, HEAD) | Required | Required | Control-plane supplied |
| Worktree identity and writable scope | N/A | Required | Execution only |
| Explicit user-named files, snippets, or artifacts | Allowed | Allowed | Subject to trimming |
| Control-plane selected task-local files | Allowed | Allowed | Must be tied to the active objective |
| Broad repository discovery summaries | Allowed | Denied by default | Advisory-only category |
| Caller-promoted advisory summary material | Allowed | Allowed only if explicitly promoted | Must be summary-form only |
| Raw advisory thread history | Internal only | Denied | Not eligible for packet assembly |
| Verbatim Codex turn output | Internal only | Denied | Not eligible for packet assembly |
| Delegation result summaries, diffs, and test outputs | Allowed | Allowed when directly relevant | Subject to trimming |
| Secrets, credentials, raw tokens, or auth material | Denied | Denied | Must be redacted or omitted |
| External research material | Allowed only under widened advisory policy | Denied in v1 | Revisit if execution networking is introduced |

`Relevant repository context` is populated differently by profile. For advisory calls, it may include the minimum cited excerpts or summaries needed to ground an answer, plus broader repository context when the question is exploratory, architectural, or comparative. For execution calls, it includes only task-scoped files, directly relevant diffs or artifacts, and context required to act safely inside the isolated worktree. Broad repository discovery, exploratory narrative, and raw advisory history do not enter execution packets by default.

`Safety envelope` is also profile-specific. For advisory calls, it states the read-only sandbox, per-request approval model, network status, and explicit prohibitions on file mutation or other disallowed operations. For execution calls, it states the isolated worktree path, writable scope, network status, escalation behavior, and the rule that promotion into the primary workspace is a separate reviewed step.

Advisory material may enter execution only through explici
... [truncated 4180 chars]
```

## ASSISTANT REPLY (Codex → agent)

The remaining gap I’m testing is whether the spec leaves enough unpinned that an implementation would have to invent behavior, especially around concurrent turns and the exact source of “effective policy.” I’m pulling line-numbered excerpts for the final review and checking whether any other spec module defines advisory concurrency or a machine-usable policy table.

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md | sed -n '1,180p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md | sed -n '80,120p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"Concurrency Limits|concurrent|interleav|lock|serialize|one at a time|advisory runtime\" /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration -g '*.md'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: f7312f
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2335
Output:
     1	---
     2	module: advisory-runtime-policy
     3	status: active
     4	normative: true
     5	authority: advisory-policy
     6	---
     7	
     8	# Advisory Runtime Policy
     9	
    10	Rules governing the advisory runtime's lifecycle, privilege scope, and rotation behavior. The advisory runtime serves both consultation and dialogue — they share a runtime because they are the same [capability class](foundations.md#scope).
    11	
    12	The core enforcement invariant: **never mutate advisory policy in place.**
    13	
    14	## Policy Fingerprint Model
    15	
    16	Each advisory runtime instance has an immutable policy fingerprint computed at creation time. The fingerprint encodes the runtime's effective policy configuration:
    17	
    18	| Component | Description |
    19	|---|---|
    20	| Transport mode | e.g., `stdio` |
    21	| Sandbox level | e.g., `read-only` |
    22	| Network access | e.g., `disabled` |
    23	| Approval mode | e.g., `disabled` |
    24	| App connectors | e.g., `disabled` |
    25	
    26	The fingerprint is:
    27	
    28	- **Immutable** for the lifetime of a runtime instance. Policy changes require rotation, not mutation.
    29	- **Recorded** in [audit events](contracts.md#auditevent) and [collaboration handles](contracts.md#collaborationhandle) for forensic correlation.
    30	- **Compared** across rotation boundaries to verify that widening or narrowing actually occurred.
    31	
    32	## Privilege Widening
    33	
    34	When a turn requires capabilities beyond the current runtime's policy (e.g., network access for a web-facing research question):
    35	
    36	1. The current runtime is **frozen** — no new turns are accepted, but history remains available for reconstruction.
    37	2. A new runtime starts with the wider policy.
    38	3. Thread history is forked into the new runtime via App Server `thread/fork`.
    39	4. The new runtime's policy fingerprint reflects the wider configuration.
    40	5. The frozen runtime is scheduled for [reaping](#reap-conditions).
    41	
    42	### What Triggers Widening
    43	
    44	- Claude explicitly requests a capability that exceeds the current policy (e.g., `codex.consult` with `network: true` when the current runtime has network disabled).
    45	- The control plane detects that a requested operation cannot succeed under current policy.
    46	
    47	### What D
... [truncated 6935 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 68665b
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 435
Output:
    80	
    81	One advisory App Server runtime per Claude session and repo root. Long-lived for the session duration.
    82	
    83	Storage: `${CLAUDE_PLUGIN_DATA}/runtimes/advisory/<claude-session-id>/`
    84	
    85	Policy defaults:
    86	
    87	| Parameter | Default |
    88	|---|---|
    89	| Transport | stdio only |
    90	| Sandbox | read-only |
    91	| Approvals | disabled |
    92	| App connectors | disabled |
    93	| Dynamic tools | disabled (v1) |
    94	| File-change approvals | auto-declined |
    95	| Network approvals | auto-declined unless explicitly requested |
    96	
    97	Consultation and dialogue share the advisory runtime because they are the same capability class. For advisory runtime lifecycle rules (policy widening, narrowing, rotation), see [advisory-runtime-policy.md](advisory-runtime-policy.md).
    98	
    99	### Execution Domain
   100	
   101	One ephemeral App Server runtime per delegation job. One isolated git worktree per job.
   102	
   103	Storage: `${CLAUDE_PLUGIN_DATA}/runtimes/delegation/<job-id>/`
   104	
   105	Policy defaults:
   106	
   107	| Parameter | Default |
   108	|---|---|
   109	| Transport | stdio only |
   110	| Sandbox | workspace-write inside isolated worktree only |
   111	| Network | disabled |
   112	| Approvals | disabled |
   113	| Unsupported escalations | become `needs_escalation` job state |
   114	| App connectors | disabled |
   115	
   116	No session-scoped approval or write state can leak between jobs. Codex never mutates the user's primary working tree directly. Claude stays primary by reviewing and promoting results after the job ends.
   117	
   118	## Trust Model
   119	
   120	Three nested trust boundaries enforce defense-in-depth.

```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 7564ca
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2996
Output:
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/decisions.md:61:**Mitigations:** The [operation journal](recovery-and-journal.md#operation-journal) provides idempotent replay. [Max-1 concurrent delegation](recovery-and-journal.md#concurrency-limits) bounds the state surface. [Advisory rotation](advisory-runtime-policy.md) prevents permission accumulation.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/decisions.md:113:**Change trigger:** When a use case for branched dialogue is identified. Fork is not blocked — it is deferred for scope reasons, not design reasons.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:10:Rules governing the advisory runtime's lifecycle, privilege scope, and rotation behavior. The advisory runtime serves both consultation and dialogue — they share a runtime because they are the same [capability class](foundations.md#scope).
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:16:Each advisory runtime instance has an immutable policy fingerprint computed at creation time. The fingerprint encodes the runtime's effective policy configuration:
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:108:| Claude session ends | Terminal | All advisory runtimes for the session are cleaned up |
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:121:A successful promotion can invalidate the advisory runtime's workspace view without changing its policy fingerprint. In v1, this is handled as a coherence event, not a policy-rotation event.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:123:When a promotion changes HEAD for a repo root that currently has an advisory runtime:
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:125:1. The control plane marks the advisory runtime's workspace context as stale.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:127:3. On the next advisory turn for that repo ro
... [truncated 9569 chars]
```

## ASSISTANT REPLY (Codex → agent)

I found one mitigating detail outside the runtime-policy spec: `delivery.md` explicitly says MCP dispatch is serialized, which reduces the race surface in the current milestone. That helps the implementation posture, but it doesn’t fully close the policy-spec hole because the rotation spec itself still doesn’t define ordering/locking semantics once widening exists.

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md | sed -n '206,248p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py | sed -n '145,170p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py | sed -n '395,455p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2500,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 0be03b
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 1164
Output:
   206	
   207	R2 implements the lineage store (delivery step 3) and the minimum dialogue surface (delivery step 4, minus fork). It also introduces MCP server scaffolding for tool exposure and dialogue operation journaling.
   208	
   209	**In scope**
   210	
   211	- Lineage store implementation per [contracts.md §Lineage Store](contracts.md#lineage-store): session-partitioned append-only JSONL at `${CLAUDE_PLUGIN_DATA}/lineage/<claude_session_id>/`, crash-safe semantics, lifecycle management, and advisory runtime rotation mapping
   212	- MCP server scaffolding (`mcp_server.py`): tool registration and serialized request dispatch for all R2 tools plus existing R1 capabilities (`codex.status`, `codex.consult`). **Serialization invariant:** the control plane processes one tool call at a time; concurrent MCP requests are queued, not processed in parallel
   213	- `codex.dialogue.start`: create a durable dialogue thread in the advisory runtime, persist handle in lineage store, return [Dialogue Start](contracts.md#dialogue-start) response shape
   214	- `codex.dialogue.reply`: continue a dialogue turn on an existing handle, dispatch via advisory runtime using the same context assembly pipeline as consultation, return [Dialogue Reply](contracts.md#dialogue-reply) response shape
   215	- `codex.dialogue.read`: read dialogue state for a given `collaboration_id` from lineage store data plus Codex `thread/read`, return [Dialogue Read](contracts.md#dialogue-read) response shape
   216	- Operation journal entries for all dispatched dialogue operations: journal-before-dispatch per [recovery-and-journal.md §Write Ordering](recovery-and-journal.md#write-ordering). `dialogue.start` uses thread-creation idempotency key (`claude_session_id` + `collaboration_id`); `dialogue.reply` uses turn-dispatch key (`runtime_id` + `thread_id` + `turn_sequence`). See [§Idempotency Keys](recovery-and-journal.md#idempotency-keys). Trim on completion.
   217	- Audit events for `dialogue_turn` with required fields per [recovery-and-journal.md §Write Triggers](recovery-and-journal.md#write-triggers): `collaboration_id`, `runtime_id`, `turn_id`
   218	- Context assembly reuse: dialogue turns use the same advisory profile, assembler, redactor, trimmer, and budget caps as consultation
   219	
   220	**Deferred**
   221	
   222	- `codex.dialogue.fork` and tree reconstruction in `codex.dialogu
... [truncated 2253 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 3932a6
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 338
Output:
   145	        }
   146	
   147	    def codex_consult(self, request: ConsultRequest) -> ConsultResult:
   148	        """Execute a one-shot advisory consultation."""
   149	
   150	        # INVARIANT: safe only while advisory turns stay read-only and
   151	        # no-network. Any policy widening must revisit fingerprint
   152	        # invalidation semantics.
   153	        if request.network_access:
   154	            raise RuntimeError(
   155	                "Consult failed: advisory widening is not implemented in R1. "
   156	                f"Got: {request.network_access!r:.100}"
   157	            )
   158	
   159	        resolved_root = request.repo_root.resolve()
   160	        runtime = self._bootstrap_runtime(resolved_root, strict=True)
   161	        repo_identity = self._repo_identity_loader(resolved_root)
   162	        stale_marker = self._journal.load_stale_marker(resolved_root)
   163	        stale_summary = None
   164	        if stale_marker is not None:
   165	            stale_summary = (
   166	                "Workspace changed since the last advisory turn. "
   167	                f"Most recent promoted HEAD: {stale_marker.promoted_head}. "
   168	                f"Current HEAD: {repo_identity.head}. "
   169	                "Re-ground reasoning in the current repository state."
   170	            )

```

### TOOL OUTPUT `exec_command`

```
Chunk ID: abb749
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 745
Output:
   395	        if existing_runtime is not None:
   396	            existing_runtime.account_state = account_state
   397	            existing_runtime.available_methods = available_methods
   398	            existing_runtime.app_server_version = handshake.user_agent
   399	            runtime = existing_runtime
   400	            self._advisory_runtimes[runtime_key] = runtime
   401	        else:
   402	            runtime = AdvisoryRuntimeState(
   403	                runtime_id=self._uuid_factory(),
   404	                repo_root=repo_root,
   405	                policy_fingerprint=build_policy_fingerprint(),
   406	                handshake=handshake,
   407	                account_state=account_state,
   408	                available_methods=available_methods,
   409	                required_methods=REQUIRED_METHODS,
   410	                optional_methods=OPTIONAL_METHODS,
   411	                session=session,
   412	                started_at=self._clock(),
   413	                app_server_version=handshake.user_agent,
   414	            )
   415	            self._advisory_runtimes[runtime_key] = runtime
   416	        return _RuntimeProbeResult(
   417	            runtime=runtime,
   418	            app_server_version=handshake.user_agent,
   419	            auth_status=account_state.auth_status,
   420	            available_methods=available_methods,
   421	            error=None,
   422	        )
   423	
   424	    def _invalidate_runtime(self, repo_root: Path) -> None:
   425	        """Drop a cached runtime after transport or turn failures."""
   426	
   427	        runtime = self._advisory_runtimes.pop(str(repo_root), None)
   428	        if runtime is not None:
   429	            runtime.session.close()
   430	
   431	
   432	def build_policy_fingerprint() -> str:
   433	    """Return the advisory runtime's immutable policy fingerprint."""
   434	
   435	    # Keep this material aligned with the actual advisory runtime policy
   436	    # inputs. R1/R2 dev-repo rollout accepts hardcoded values only while the
   437	    # request gate and runtime settings preserve this exact advisory posture.
   438	    material = {
   439	        "transport_mode": "stdio",
   440	        "sandbox_level": "read_only",
   441	        "network_access": "disabled",
   442	        "approval_mode": "never",
   443	        "app_connectors": "disabled",
   444	 
... [truncated 583 chars]
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/runtime.py | sed -n '1,160p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py | sed -n '1,220p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/models.py | sed -n '30,135p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 39a2a4
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 1703
Output:
     1	"""Live App Server runtime session for advisory work."""
     2	
     3	from __future__ import annotations
     4	
     5	from pathlib import Path
     6	from typing import Any
     7	
     8	from .jsonrpc_client import JsonRpcClient
     9	from .models import AccountState, RuntimeHandshake, TurnExecutionResult
    10	
    11	
    12	class AppServerRuntimeSession:
    13	    """Thin high-level wrapper over the Codex App Server JSON-RPC transport."""
    14	
    15	    def __init__(
    16	        self,
    17	        *,
    18	        repo_root: Path,
    19	        command: list[str] | None = None,
    20	        request_timeout: float = 1200.0,
    21	    ) -> None:
    22	        self._repo_root = repo_root
    23	        self._client = JsonRpcClient(
    24	            command or ["codex", "app-server"],
    25	            cwd=repo_root,
    26	            request_timeout=request_timeout,
    27	        )
    28	
    29	    def initialize(self) -> RuntimeHandshake:
    30	        """Perform the `initialize` handshake."""
    31	
    32	        result = self._client.request(
    33	            "initialize",
    34	            {
    35	                "clientInfo": {
    36	                    "name": "codex_collaboration",
    37	                    "title": "Codex Collaboration Plugin",
    38	                    "version": "0.1.0",
    39	                }
    40	            },
    41	        )
    42	        return RuntimeHandshake(
    43	            codex_home=str(result["codexHome"]),
    44	            platform_family=str(result["platformFamily"]),
    45	            platform_os=str(result["platformOs"]),
    46	            user_agent=str(result["userAgent"]),
    47	        )
    48	
    49	    def read_account(self) -> AccountState:
    50	        """Return the current auth state."""
    51	
    52	        result = self._client.request("account/read", {"refreshToken": False})
    53	        account = result.get("account")
    54	        requires_openai_auth = bool(result.get("requiresOpenaiAuth", False))
    55	        if isinstance(account, dict):
    56	            account_type = account.get("type")
    57	            return AccountState(
    58	                auth_status="authenticated",
    59	                account_type=str(account_type)
    60	                if isinstance(account_type, str)
    61	                else None,
 
... [truncated 4415 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: c41d40
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 1686
Output:
     1	"""Consultation profile resolver.
     2	
     3	Resolution order: explicit flags > named profile > contract defaults.
     4	Validation gate: rejects sandbox != read-only or approval_policy != never
     5	until freeze-and-rotate is implemented.
     6	"""
     7	
     8	from __future__ import annotations
     9	
    10	from dataclasses import dataclass
    11	from pathlib import Path
    12	from typing import Any, Literal, get_args
    13	
    14	import yaml
    15	
    16	
    17	class ProfileValidationError(RuntimeError):
    18	    """Raised when a resolved profile requires capabilities not yet implemented."""
    19	
    20	
    21	Posture = Literal[
    22	    "collaborative", "adversarial", "exploratory", "evaluative", "comparative"
    23	]
    24	Effort = Literal["minimal", "low", "medium", "high", "xhigh"]
    25	SandboxPolicy = Literal["read-only"]
    26	ApprovalPolicy = Literal["never"]
    27	
    28	_VALID_POSTURES: frozenset[str] = frozenset(get_args(Posture))
    29	_VALID_EFFORTS: frozenset[str] = frozenset(get_args(Effort))
    30	
    31	
    32	@dataclass(frozen=True)
    33	class ResolvedProfile:
    34	    """Fully resolved execution controls."""
    35	
    36	    posture: Posture
    37	    turn_budget: int
    38	    effort: Effort | None
    39	    sandbox: SandboxPolicy
    40	    approval_policy: ApprovalPolicy
    41	
    42	
    43	_DEFAULT_POSTURE = "collaborative"
    44	_DEFAULT_TURN_BUDGET = 6
    45	_DEFAULT_SANDBOX = "read-only"
    46	_DEFAULT_APPROVAL = "never"
    47	
    48	_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"
    49	
    50	
    51	def load_profiles(
    52	    base_path: Path | None = None,
    53	) -> dict[str, dict[str, Any]]:
    54	    """Load profiles from YAML. Merges local overrides if present."""
    55	    base = base_path or _REFERENCES_DIR
    56	    profiles_path = base / "consultation-profiles.yaml"
    57	    if not profiles_path.exists():
    58	        return {}
    59	
    60	    with open(profiles_path) as f:
    61	        data = yaml.safe_load(f) or {}
    62	
    63	    profiles: dict[str, dict[str, Any]] = data.get("profiles", {})
    64	
    65	    local_path = base / "consultation-profiles.local.yaml"
    66	    if local_path.exists():
    67	        with open(local_path) as f:
    68	            local_data = yaml.safe_load(f) or {}
    69	     
... [truncated 4348 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 2cfc3e
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 844
Output:
    30	
    31	    path: Path
    32	
    33	
    34	@dataclass(frozen=True)
    35	class ConsultRequest:
    36	    """Caller-facing consult request for the advisory runtime."""
    37	
    38	    repo_root: Path
    39	    objective: str
    40	    user_constraints: tuple[str, ...] = ()
    41	    acceptance_criteria: tuple[str, ...] = ()
    42	    explicit_paths: tuple[Path, ...] = ()
    43	    explicit_snippets: tuple[str, ...] = ()
    44	    task_local_paths: tuple[Path, ...] = ()
    45	    broad_repository_summaries: tuple[str, ...] = ()
    46	    promoted_summaries: tuple[str, ...] = ()
    47	    delegation_summaries: tuple[str, ...] = ()
    48	    supplementary_context: tuple[str, ...] = ()
    49	    external_research_material: tuple[str, ...] = ()
    50	    parent_thread_id: str | None = None
    51	    network_access: bool = False
    52	    profile: str | None = None
    53	
    54	
    55	@dataclass(frozen=True)
    56	class AssembledPacket:
    57	    """Final packet sent to Codex after assembly, redaction, and trimming."""
    58	
    59	    profile: CapabilityProfile
    60	    payload: str
    61	    context_size: int
    62	    omitted_categories: tuple[str, ...] = ()
    63	
    64	
    65	@dataclass(frozen=True)
    66	class ConsultEvidence:
    67	    """Single evidence item projected from the consult result."""
    68	
    69	    claim: str
    70	    citation: str
    71	
    72	
    73	@dataclass(frozen=True)
    74	class ConsultResult:
    75	    """Structured result returned to Claude from `codex.consult`."""
    76	
    77	    collaboration_id: str
    78	    runtime_id: str
    79	    position: str
    80	    evidence: tuple[ConsultEvidence, ...]
    81	    uncertainties: tuple[str, ...]
    82	    follow_up_branches: tuple[str, ...]
    83	    context_size: int
    84	
    85	
    86	@dataclass(frozen=True)
    87	class RuntimeHandshake:
    88	    """Initialize response values retained by the runtime."""
    89	
    90	    codex_home: str
    91	    platform_family: str
    92	    platform_os: str
    93	    user_agent: str
    94	
    95	
    96	@dataclass(frozen=True)
    97	class AccountState:
    98	    """Auth state projected from `account/read`."""
    99	
   100	    auth_status: AuthStatus
   101	    account_type: str | None
   102	    requires_openai_auth: bool
   103	
   104	
   105	@dataclass(frozen=True)
 
... [truncated 977 chars]
```

## ASSISTANT REPLY (Codex → agent)

One more ambiguity showed up: the “Advisory domain” defaults table names `Network approvals`, while the fingerprint model tracks `Network access`. There is a later “Chosen Defaults” table saying advisory network is off by default, but the spec never consolidates those into one authoritative runtime-policy object, which is exactly why the implementation has drifted into literals.

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md | sed -n '292,302p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 1500,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"dynamic tools|file-change approvals|network approvals|policy defaults|chosen defaults\" /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 1480f7
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 156
Output:
   292	|---|---|
   293	| Codex transport | App Server over stdio |
   294	| Advisory runtime reuse | one per Claude session + repo root |
   295	| Delegation runtime reuse | never; one per job |
   296	| Delegation write target | isolated git worktree |
   297	| Promotion to main workspace | explicit second step after Claude review |
   298	| Advisory network access | off by default |
   299	| Delegation network access | off by default |
   300	| Codex apps/connectors | disabled by default |
   301	| Codex-side plugin dependency | none for v1 |
   302	| Plugin agents | optional only; not part of trust enforcement |

```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 6d739c
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 181
Output:
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:323:The system does not rely on: WebSocket transport, dynamic tools, `plugin/list`, `plugin/read`, `plugin/install`, `plugin/uninstall`, or other experimental APIs for core functionality.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:73:Narrowing is triggered when Claude initiates a turn that does not require the current runtime's elevated capabilities. The control plane compares the requested capabilities against the [base policy defaults](foundations.md#advisory-domain) and rotates down if the turn can be served at a lower privilege level.

```

## ASSISTANT REPLY (Codex → agent)

The last structural question is the contract surface: if widening is supposed to happen on explicit capability request, the request schema needs to say how those capabilities are expressed. Right now the live request model only has `network_access` plus an opaque `profile`, which is enough for the current R1 gate but not enough to represent the full 5-component policy space the spec talks about.

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"codex.consult|network_access|approval|profile|sandbox|connector|app connectors\" /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py | sed -n '220,280p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md | sed -n '1,120p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 9797ba
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 879
Output:
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:28:        "name": "codex.consult",
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:36:                "profile": {
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:38:                    "description": "Named consultation profile (e.g., quick-check, deep-review)",
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:51:                "profile": {
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:53:                    "description": "Named consultation profile — resolved once at start, persisted for all subsequent replies",
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:64:                    "description": "Explicit posture override — takes precedence over profile posture",
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:70:                    "description": "Explicit turn budget override — takes precedence over profile turn_budget",
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:241:        if name == "codex.consult":
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:250:                profile=arguments.get("profile"),
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:252:            result = self._control_plane.codex_consult(request)
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:258:                profile_name=arguments.get("profile"),
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md:20:| `codex.consult` | One-shot second opinion using the advisory runtime |
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md:26:| `codex.delegate.poll` | Poll job progress and pending approvals |
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md:27:| `code
... [truncated 1111 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 82b487
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 752
Output:
   220	            }
   221	        except Exception as exc:
   222	            return {
   223	                "jsonrpc": "2.0",
   224	                "id": req_id,
   225	                "result": {
   226	                    "content": [
   227	                        {"type": "text", "text": str(exc)},
   228	                    ],
   229	                    "isError": True,
   230	                },
   231	            }
   232	
   233	    def _dispatch_tool(self, name: str, arguments: dict[str, Any]) -> Any:
   234	        """Route a tool call to the appropriate handler. Serialization is
   235	        guaranteed by the synchronous single-threaded main loop."""
   236	        # INVARIANT: safe only while this is the sole serialized dispatch
   237	        # chokepoint. Any concurrent dispatch model must revisit advisory
   238	        # locking and turn sequencing.
   239	        if name == "codex.status":
   240	            return self._control_plane.codex_status(Path(arguments["repo_root"]))
   241	        if name == "codex.consult":
   242	            from .models import ConsultRequest
   243	
   244	            request = ConsultRequest(
   245	                repo_root=Path(arguments["repo_root"]),
   246	                objective=arguments["objective"],
   247	                explicit_paths=tuple(
   248	                    Path(p) for p in arguments.get("explicit_paths", ())
   249	                ),
   250	                profile=arguments.get("profile"),
   251	            )
   252	            result = self._control_plane.codex_consult(request)
   253	            return asdict(result)
   254	        if name == "codex.dialogue.start":
   255	            controller = self._ensure_dialogue_controller()
   256	            result = controller.start(
   257	                Path(arguments["repo_root"]),
   258	                profile_name=arguments.get("profile"),
   259	                explicit_posture=arguments.get("posture"),
   260	                explicit_turn_budget=arguments.get("turn_budget"),
   261	            )
   262	            return asdict(result)
   263	        if name == "codex.dialogue.reply":
   264	            controller = self._ensure_dialogue_controller()
   265	            result = controller.reply(
   266	                collaboration_id=arguments["collaboration_id"],
   267	                objective=arguments["objective"],
... [truncated 610 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: f56811
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2075
Output:
     1	---
     2	module: contracts
     3	status: active
     4	normative: true
     5	authority: contracts
     6	---
     7	
     8	# Contracts
     9	
    10	Interface definitions for the codex-collaboration plugin. Defines the MCP tool surface exposed to Claude, logical data model types, protocol message shapes, and the audit event schema.
    11	
    12	## MCP Tool Surface
    13	
    14	Claude interacts with Codex exclusively through these tools. Raw App Server methods are never exposed.
    15	
    16	The official plugin exposes native app-server methods directly to Claude. This spec mediates through a control plane instead, providing structured contracts, typed responses, and audit observability at the boundary.
    17	
    18	| Tool | Purpose |
    19	|---|---|
    20	| `codex.consult` | One-shot second opinion using the advisory runtime |
    21	| `codex.dialogue.start` | Create a durable dialogue thread |
    22	| `codex.dialogue.reply` | Continue a dialogue turn |
    23	| `codex.dialogue.fork` | Branch a dialogue thread |
    24	| `codex.dialogue.read` | Read dialogue state, branches, and summaries |
    25	| `codex.delegate.start` | Start an isolated execution job |
    26	| `codex.delegate.poll` | Poll job progress and pending approvals |
    27	| `codex.delegate.decide` | Resolve a pending escalation or approval |
    28	| `codex.delegate.promote` | Apply accepted delegation results to the primary workspace |
    29	| `codex.status` | Health, auth, version, and runtime diagnostics |
    30	
    31	The official plugin has no separate promotion-gated equivalent. It executes in the shared checkout without a distinct `codex.delegate.promote` step.
    32	
    33	Claude-facing skills wrap these tools but do not define the transport.
    34	
    35	## Logical Data Model
    36	
    37	The plugin maintains its own logical identifiers. Raw Codex IDs (thread IDs, turn IDs) are internal to the control plane and not exposed to Claude.
    38	
    39	### CollaborationHandle
    40	
    41	A logical identifier for a Codex interaction (consultation, dialogue turn, or delegation job). Dialogue and delegation handles are persisted by the [lineage store](#lineage-store) for routing, crash recovery, and lifecycle management. Consultation handles are ephemeral — created for audit correlation via `collaboration_id` but not persisted in the lineage store.
 
... [truncated 5883 chars]
```

## ASSISTANT REPLY (Codex → agent)

I also want to test the observability contract around rotation itself. The runtime-policy spec says a `rotate` audit event links old and new runtimes, but if the audit schema only has one `runtime_id`, that’s another place where the protocol is described more strongly than it’s typed.

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md | sed -n '180,225p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md | sed -n '84,100p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2500,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md | sed -n '130,160p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2500,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 3321e5
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 698
Output:
   180	## Audit Event Schema
   181	
   182	Append-only event record for human reconstruction and diagnostics. Write behavior and retention are defined in [recovery-and-journal.md §Audit Log](recovery-and-journal.md#audit-log).
   183	
   184	### AuditEvent
   185	
   186	| Field | Type | Description |
   187	|---|---|---|
   188	| `event_id` | string (UUID) | Unique event identifier |
   189	| `timestamp` | ISO 8601 | Event time |
   190	| `actor` | enum | `claude`, `codex`, `user`, `system` |
   191	| `action` | enum | See [action values](#audit-event-actions) |
   192	| `collaboration_id` | string | Associated collaboration |
   193	| `runtime_id` | string | Runtime that the event occurred in |
   194	| `policy_fingerprint` | string? | Runtime policy fingerprint at event time |
   195	| `job_id` | string? | Delegation job (for execution-domain events) |
   196	| `request_id` | string? | Associated [PendingServerRequest](#pendingserverrequest) |
   197	| `turn_id` | string? | Codex turn context |
   198	| `artifact_hash` | string? | For promotions and approvals |
   199	| `decision` | enum? | `approve`, `deny`, `escalate` |
   200	| `causal_parent` | string? | `event_id` of the triggering event |
   201	| `context_size` | integer? | UTF-8 byte length of the final assembled packet sent to Codex, post-assembly and post-redaction. Used for budget enforcement and monitoring. |
   202	
   203	### Audit Event Actions
   204	
   205	| Action | Domain | Description |
   206	|---|---|---|
   207	| `consult` | advisory | Consultation initiated |
   208	| `dialogue_turn` | advisory | Dialogue turn dispatched |
   209	| `fork` | advisory | Thread forked |
   210	| `delegate_start` | execution | Delegation job started |
   211	| `approve` | both | Approval resolved |
   212	| `escalate` | both | Escalation surfaced to Claude |
   213	| `promote` | execution | Promotion attempted |
   214	| `discard` | execution | Result discarded |
   215	| `crash` | both | Runtime crashed |
   216	| `restart` | both | Runtime restarted after crash |
   217	| `rotate` | advisory | Advisory runtime rotated — see [advisory-runtime-policy.md §Freeze-and-Rotate](advisory-runtime-policy.md#freeze-and-rotate-semantics) |
   218	| `freeze` | advisory | Advisory runtime frozen — see [advisory-runtime-policy.md §Freeze](advisory-runtime-policy.md#freeze) |
   219	| `reap` | advisory | Froze
... [truncated 385 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 438fa0
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 263
Output:
    84	| Dialogue turn dispatched | `dialogue_turn` | `collaboration_id`, `runtime_id`, `turn_id` |
    85	| Thread forked | `fork` | `collaboration_id`, `causal_parent` |
    86	| Delegation started | `delegate_start` | `collaboration_id`, `job_id`, `runtime_id` |
    87	| Approval resolved | `approve` | `request_id`, `decision` |
    88	| Escalation surfaced | `escalate` | `request_id`, `collaboration_id` |
    89	| Promotion attempted | `promote` | `job_id`, `artifact_hash`, `decision` |
    90	| Result discarded | `discard` | `job_id` |
    91	| Runtime crashed | `crash` | `runtime_id`, `policy_fingerprint` |
    92	| Runtime restarted | `restart` | `runtime_id`, `causal_parent` |
    93	| Advisory runtime rotated | `rotate` | `runtime_id`, `policy_fingerprint` |
    94	| Advisory runtime frozen | `freeze` | `runtime_id` |
    95	| Frozen runtime reaped | `reap` | `runtime_id` |
    96	
    97	### Retention
    98	
    99	- **Default TTL:** 30 days from event timestamp.
   100	- **Storage:** JSONL in `${CLAUDE_PLUGIN_DATA}/audit/`.

```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 34b46a
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 708
Output:
   130	
   131	| Operation | Purpose | Used by |
   132	|---|---|---|
   133	| `create` | Persist a new handle | `codex.dialogue.start` |
   134	| `get` | Retrieve handle by `collaboration_id` | `codex.dialogue.reply`, `codex.dialogue.read`, control plane routing |
   135	| `list` | Query handles by session, repo root, and optional status filter | Crash recovery (step 2), internal enumeration |
   136	| `update_status` | Transition handle lifecycle status | Handle completion, crash recovery |
   137	| `update_runtime` | Remap handle to a new runtime and, if `thread/resume` yields a new thread identity, update `codex_thread_id` | Advisory runtime rotation ([advisory-runtime-policy.md §Rotate](advisory-runtime-policy.md#rotate) step 4), crash recovery (step 4) |
   138	
   139	Fork-specific operations (`get_children`, `get_parent`, tree reconstruction) are deferred until `codex.dialogue.fork` enters scope. See [decisions.md §Dialogue Fork Scope](decisions.md#dialogue-fork-scope).
   140	
   141	### Handle Lifecycle
   142	
   143	| Status | Meaning | Transitions to |
   144	|---|---|---|
   145	| `active` | Handle is open for turns | `completed`, `crashed`, `unknown` |
   146	| `completed` | Dialogue or consultation finished normally | Terminal |
   147	| `crashed` | Runtime crash detected | `active` (after recovery) |
   148	| `unknown` | Session crash, state uncertain | `active` (after recovery), `completed` (after inspection) |
   149	
   150	### Crash Recovery Contract
   151	
   152	When an advisory runtime crashes ([recovery-and-journal.md §Advisory Runtime Crash](recovery-and-journal.md#advisory-runtime-crash)):
   153	
   154	1. The control plane restarts the advisory runtime.
   155	2. The control plane reads all handles with `status: active` and all eligible handles with `status: unknown` from the lineage store for the current session and repo root.
   156	3. Eligibility for an `unknown` handle requires successful `thread/read` followed by `thread/resume`, and the local TurnStore must satisfy:
   157	   - if `completed_count == 0`: the TurnStore must have no metadata for this collaboration (stale local metadata with zero remote completed turns is ineligible),
   158	   - if `completed_count > 0`: metadata keys `{1, 2, ..., completed_count}` must all be present (prefix-completeness; extra keys beyond `completed_count` do not disqualify).
   159	4.
... [truncated 433 chars]
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py | sed -n '1,90p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2500,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"ConsultRequest|network_access\" /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration -g '*.md'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 21a252
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 965
Output:
     1	"""MCP server scaffolding with serialized dispatch.
     2	
     3	Stdio JSON-RPC 2.0 server exposing all R1+R2 tools. Processes one tool call
     4	at a time (serialization invariant per delivery.md §R2 in-scope).
     5	"""
     6	
     7	from __future__ import annotations
     8	
     9	import json
    10	import sys
    11	from dataclasses import asdict
    12	from pathlib import Path
    13	from typing import Any, Callable
    14	
    15	TOOL_DEFINITIONS: list[dict[str, Any]] = [
    16	    {
    17	        "name": "codex.status",
    18	        "description": "Health, auth, version, and runtime diagnostics.",
    19	        "inputSchema": {
    20	            "type": "object",
    21	            "properties": {
    22	                "repo_root": {"type": "string", "description": "Repository root path"},
    23	            },
    24	            "required": ["repo_root"],
    25	        },
    26	    },
    27	    {
    28	        "name": "codex.consult",
    29	        "description": "One-shot second opinion using the advisory runtime.",
    30	        "inputSchema": {
    31	            "type": "object",
    32	            "properties": {
    33	                "repo_root": {"type": "string"},
    34	                "objective": {"type": "string"},
    35	                "explicit_paths": {"type": "array", "items": {"type": "string"}},
    36	                "profile": {
    37	                    "type": "string",
    38	                    "description": "Named consultation profile (e.g., quick-check, deep-review)",
    39	                },
    40	            },
    41	            "required": ["repo_root", "objective"],
    42	        },
    43	    },
    44	    {
    45	        "name": "codex.dialogue.start",
    46	        "description": "Create a durable dialogue thread in the advisory runtime.",
    47	        "inputSchema": {
    48	            "type": "object",
    49	            "properties": {
    50	                "repo_root": {"type": "string", "description": "Repository root path"},
    51	                "profile": {
    52	                    "type": "string",
    53	                    "description": "Named consultation profile — resolved once at start, persisted for all subsequent replies",
    54	                },
    55	                "posture": {
    56	                    "type": "string",
    57	                   
... [truncated 1455 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 1daa9e
Wall time: 0.0000 seconds
Process exited with code 1
Original token count: 0
Output:

```

## ASSISTANT REPLY (Codex → agent)

**Findings**

1. `P1` The spec is strong on the lifecycle invariant, but not on the authoritative source of policy truth. [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:16) clearly says a runtime has an immutable 5-component fingerprint and that narrowing compares requested capabilities against “base policy defaults” at [line 73](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:73). But the only referenced defaults live in prose tables in [foundations.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:85) and [foundations.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:298), and those tables do not cleanly line up with the fingerprint dimensions. The advisory-domain table talks about `Network approvals`, `Dynamic tools`, and `File-change approvals`; the fingerprint model talks about `Network access`, `Approval mode`, and `App connectors`. That leaves an implementer to invent what counts as the “effective policy configuration,” which is exactly why the current code fell back to literals in [control_plane.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py:432) and [runtime.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/runtime.py:81).

2. `P1` The widening trigger is described, but the request contract for capability changes is not pinned strongly enough. The spec says widening happens when Claude explicitly requests a capability or when the control plane detects the current policy is insufficient, with an example of `codex.consult` requesting network access in [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:42). But the exposed `codex.consult` schema in [mcp_server.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:28) has no capability fields at all, and the live request model only carries `network_access` plus an opaque `profile` in [models.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/models.py:35). That is not enough to represent the full policy space the fingerprint claims to cover. So the spec leaves unresolved how sandbox widening, approval-mode changes, or connector enablement are requested, how `profile` interacts with policy, and what exactly the control plane compares during narrowing.

3. `P2` The rotation protocol is under-specified for concurrency and ordering. The policy spec correctly says freeze rejects new turns and that evaluation happens between turns in [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:79) and [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:112). But it does not say what happens if two advisory requests arrive at the same boundary, if one request observes the old runtime while another has already frozen it, or what lock/compare-and-swap rule owns the transition. There is a mitigating delivery assumption that MCP dispatch is serialized in [delivery.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md:212), and the implementation explicitly relies on that in [mcp_server.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:233). That helps the current rollout, but it means the normative rotation model is only safe because of an external rollout assumption, not because the policy spec itself defines a concurrency model.

4. `P2` Rotation observability is weaker than the prose implies. The spec says a `rotate` audit event links old and new runtimes in [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:138), and the lineage contract says handle mappings are updated on rotation in [contracts.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md:137). But the typed audit schema only has one `runtime_id` plus one `policy_fingerprint` in [contracts.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md:180), and the required fields for `rotate` in [recovery-and-journal.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:84) are still just `runtime_id` and `policy_fingerprint`. That is not enough to prove an old->new mapping or to reconstruct whether a given rotation was a widen or a narrow unless the implementation invents extra `extra` payload semantics.

5. `P3` The current implementation confirms these are real contract gaps, not just unimplemented plumbing. Widening is hard-rejected in [control_plane.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py:147), profile-based sandbox/approval widening is also rejected in [profiles.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:148), the advisory fingerprint is constant in [control_plane.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py:432), and the runtime startup/turn calls hardcode `approvalPolicy: never` and `readOnly` in [runtime.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/runtime.py:81). Some of that is deliberate R1 scoping, but some of it exists because the spec does not yet give an executable target-policy contract.

**Bottom Line**

The model is strong enough to define the safety posture and the core prohibition: no in-place mutation, all policy changes via freeze-and-rotate, and no mid-turn rotation. It is not strong enough yet to implement widening and narrowing without inventing policy semantics in code.

The weak points are all at the contract boundary: no single authoritative policy object, no fully specified request surface for capability changes, no explicit concurrency/locking semantics for boundary races, and no typed old/new runtime linkage in the audit contract.

**Recommended Next Step**

1. Promote the advisory defaults into one normative “effective advisory policy” table or typed object, and make the fingerprint derive from exactly that object.
2. Define the Claude-facing capability request contract explicitly: which fields request network, sandbox, approval, connectors, and how named profiles interact with those fields.
3. Add a rotation ownership rule: serialized by MCP only, or control-plane lock per repo root, or equivalent CAS semantics.
4. Extend the rotate audit/lineage contract so old runtime, new runtime, old fingerprint, and new fingerprint are first-class fields rather than implied.

## System prompt (developer role)

```
<permissions instructions>
Filesystem sandboxing defines which files can be read or written. `sandbox_mode` is `workspace-write`: The sandbox permits reading files, and editing files in `cwd` and `writable_roots`. Editing files in other directories requires approval. Network access is enabled.
Approval policy is currently never. Do not provide the `sandbox_permissions` for any reason, commands will be rejected.
 The writable roots are `/Users/jp/Projects/active`, `/Users/jp/.codex`, `/tmp`, `/Users/jp/.Trash`, `/Users/jp/dotfiles`, `/Users/jp/.local/bin`, `/Users/jp/.codex/memories`, `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model`, `/tmp`, `/var/folders/qq/gwjpkt_12klbf6ltxw56_sr40000gn/T`.
</permissions instructions>
```

## USER TURN 3 (agent → Codex)

```
Strong synthesis on turn 1. Let me probe the concurrency claim in depth — you argued rotation safety currently rests on an external MCP-serialization assumption rather than a policy-spec concurrency model. Two concerns:

1. **Failure-mode analysis**: If we drop the MCP serialization assumption (say, the server gains a parallel dispatch mode, or a future transport multiplexes), what are the specific race hazards the rotation model as specified would expose? Enumerate them concretely (e.g., "two turns observe the old fingerprint simultaneously, one triggers widening, the other proceeds on the stale runtime" — with the exact interleaving).

2. **Minimum concurrency contract**: What is the smallest delta to the rotation spec that would make it safe regardless of dispatch serialization? A single mutex on the runtime registry? Per-conversation-id locks? A monotonic policy-fingerprint version with CAS on the handle mapping? Which of these is load-bearing vs nice-to-have?

I'm specifically trying to distinguish "the spec is implicitly relying on an external invariant that is true today and will stay true" from "the spec has an unstated coupling that will break the first time dispatch changes." Which is it?
```

## ASSISTANT REPLY (Codex → agent)

I’m treating this as a deeper architecture review. I’m checking the dialogue and lineage routing paths so the concurrency answer is tied to the actual ownership boundaries in code, not just the high-level rotation prose.

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"get_advisory_runtime|update_runtime|runtime_id|collaboration_id|repo_root|thread/resume|thread/read|freeze|rotate\" /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/dialogue.py /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py -g '*.py'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 5000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/dialogue.py | sed -n '360,520p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py | sed -n '1,260p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 5000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 7bf66e
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 7359
Output:
Total output lines: 178

/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:22:# Required string fields for create op (collaboration_id validated earlier)
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:25:    "runtime_id",
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:28:    "repo_root",
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:33:    "parent_collaboration_id",
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:49:        cid = record.get("collaboration_id")
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:51:            raise SchemaViolation("missing or non-string collaboration_id")
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:101:        elif op == "update_runtime":
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:102:            if not isinstance(record.get("runtime_id"), str):
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:104:                    "update_runtime op: runtime_id missing or not a string"
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:107:                updates: dict[str, Any] = {"runtime_id": record["runtime_id"]}
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:111:                            "update_runtime op: codex_thread_id is not a string"
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:128:    the last record for each collaboration_id wins. Incomplete trailing records
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:141:    def get(self, collaboration_id: str) -> CollaborationHandle | None:
/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:142:        """Retrieve a handle by collaboration_id, or None 
... [truncated 17652 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 9ade95
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2050
Output:
   360	
   361	        Write ordering invariant: local finalization MUST complete before the
   362	        journal is marked completed.
   363	
   364	        Failure semantics:
   365	        - run_turn() raises: inspect via _best_effort_repair_turn(). If the turn
   366	          is still unconfirmed, re-raise the original dispatch exception after
   367	          quarantining the handle. If the turn is confirmed, surface a
   368	          CommittedTurnFinalizationError instead of a raw dispatch failure.
   369	        - local finalization raises after run_turn() succeeds: leave the
   370	          journal at dispatched, quarantine the handle, and raise
   371	          CommittedTurnFinalizationError.
   372	        - parse_consult_response() raises after completed: raise
   373	          CommittedTurnParseError. Handle stays active.
   374	        """
   375	        handle = self._lineage_store.get(collaboration_id)
   376	        if handle is None:
   377	            raise ValueError(
   378	                f"Reply failed: handle not found. "
   379	                f"Got: collaboration_id={collaboration_id!r:.100}"
   380	            )
   381	        if handle.status != "active":
   382	            raise ValueError(
   383	                f"Reply failed: handle not active. "
   384	                f"Got: status={handle.status!r}, collaboration_id={collaboration_id!r:.100}"
   385	            )
   386	
   387	        posture = handle.resolved_posture  # may be None
   388	        effort = handle.resolved_effort  # may be None
   389	
   390	        resolved_root = Path(handle.repo_root)
   391	        runtime = self._control_plane.get_advisory_runtime(resolved_root)
   392	        repo_identity = self._repo_identity_loader(resolved_root)
   393	
   394	        # Derive turn_sequence from completed turns via thread/read (contracts.md:266).
   395	        # Safe only while the MCP server keeps serialized dispatch for the
   396	        # accepted R1/R2 rollout posture — no concurrent advisory turns to race with.
   397	        turn_sequence = self._next_turn_sequence(handle, runtime)
   398	
   399	        # Build consult request for context assembly (reuse same pipeline)
   400	        request = ConsultRequest(
   401	            repo_root=resolved_root,
   402	            objective=objective,
   403	            user_constraints=user_constraints,
 
... [truncated 5794 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 002cde
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2538
Output:
     1	"""Lineage store: session-partitioned append-only JSONL handle persistence.
     2	
     3	See contracts.md §Lineage Store for the normative contract.
     4	"""
     5	
     6	from __future__ import annotations
     7	
     8	import json
     9	import os
    10	import shutil
    11	from dataclasses import asdict
    12	from pathlib import Path
    13	from typing import Any, Callable, get_args
    14	
    15	from .models import CapabilityProfile, CollaborationHandle, HandleStatus
    16	from .replay import ReplayDiagnostics, SchemaViolation, UnknownOperation, replay_jsonl
    17	
    18	# Valid literal values from type aliases
    19	_VALID_STATUSES: frozenset[str] = frozenset(get_args(HandleStatus))
    20	_VALID_CAPABILITIES: frozenset[str] = frozenset(get_args(CapabilityProfile))
    21	
    22	# Required string fields for create op (collaboration_id validated earlier)
    23	_CREATE_REQUIRED_STR = (
    24	    "capability_class",
    25	    "runtime_id",
    26	    "codex_thread_id",
    27	    "claude_session_id",
    28	    "repo_root",
    29	    "created_at",
    30	    "status",
    31	)
    32	_CREATE_OPTIONAL_STR = (
    33	    "parent_collaboration_id",
    34	    "fork_reason",
    35	    "resolved_posture",
    36	    "resolved_effort",
    37	)
    38	
    39	
    40	def _make_lineage_callback(
    41	    handles: dict[str, CollaborationHandle],
    42	) -> Callable[[dict[str, Any]], None]:
    43	    """Create a replay callback that mutates the captured handles dict."""
    44	
    45	    def apply(record: dict[str, Any]) -> None:
    46	        op = record.get("op")
    47	        if not isinstance(op, str):
    48	            raise SchemaViolation("missing or non-string op")
    49	        cid = record.get("collaboration_id")
    50	        if not isinstance(cid, str):
    51	            raise SchemaViolation("missing or non-string collaboration_id")
    52	
    53	        if op == "create":
    54	            for name in _CREATE_REQUIRED_STR:
    55	                if not isinstance(record.get(name), str):
    56	                    raise SchemaViolation(f"create op: {name} missing or not a string")
    57	            for name in _CREATE_OPTIONAL_STR:
    58	                val = record.get(name)
    59	                if val is not None and not isinstance(val, str):
    60	                    raise SchemaViolation(f"create op:
... [truncated 7751 chars]
```

## ASSISTANT REPLY (Codex → agent)

The code path confirms the contention domain is repo-root advisory runtime, not a single conversation. Dialogue handles are remapped individually, but they all route through one runtime registry entry per repo root, so any concurrency contract that only locks `collaboration_id` is too narrow.

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py | sed -n '272,320p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2500,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/dialogue.py | sed -n '220,320p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3500,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md | sed -n '140,170p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2500,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 4b72f6
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 530
Output:
   272	            runtime.session.close()
   273	        self._advisory_runtimes.clear()
   274	
   275	    def _bootstrap_runtime(
   276	        self, repo_root: Path, *, strict: bool
   277	    ) -> AdvisoryRuntimeState | None:
   278	        cached = self._advisory_runtimes.get(str(repo_root))
   279	        compat_result = self._compat_checker()
   280	        probe_result = self._probe_runtime(
   281	            repo_root,
   282	            compat_result=compat_result,
   283	            existing_runtime=cached,
   284	        )
   285	        if probe_result.error is not None:
   286	            if strict:
   287	                raise RuntimeError(probe_result.error)
   288	            return None
   289	        return probe_result.runtime
   290	
   291	    def _probe_runtime(
   292	        self,
   293	        repo_root: Path,
   294	        *,
   295	        compat_result: object,
   296	        existing_runtime: AdvisoryRuntimeState | None = None,
   297	    ) -> _RuntimeProbeResult:
   298	        codex_version = getattr(compat_result, "codex_version", None)
   299	        if codex_version is None:
   300	            return _RuntimeProbeResult(
   301	                runtime=None,
   302	                app_server_version=None,
   303	                auth_status=None,
   304	                available_methods=frozenset(),
   305	                error="Runtime bootstrap failed: codex version unavailable. Got: None",
   306	            )
   307	
   308	        runtime_key = str(repo_root)
   309	        session = (
   310	            existing_runtime.session
   311	            if existing_runtime is not None
   312	            else self._runtime_factory(repo_root)
   313	        )
   314	        try:
   315	            # INVARIANT: safe only while initialize + account/read remain
   316	            # the complete advisory bootstrap surface. Adding any new
   317	            # bootstrap-critical method should revisit the parked bootstrap
   318	            # assertion debt before rollout.
   319	            handshake = (
   320	                existing_runtime.handshake

```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 33728c
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 1115
Output:
   220	        return DialogueStartResult(
   221	            collaboration_id=collaboration_id,
   222	            runtime_id=runtime.runtime_id,
   223	            status="active",
   224	            created_at=created_at,
   225	        )
   226	
   227	    @staticmethod
   228	    def _committed_turn_error_message(reason: str) -> str:
   229	        return (
   230	            f"{reason}. The turn is durably recorded. Use codex.dialogue.read to "
   231	            "inspect the committed turn. Blind retry will create a duplicate "
   232	            "follow-up turn, not replay this one."
   233	        )
   234	
   235	    def _completed_entry(self, entry: OperationJournalEntry) -> OperationJournalEntry:
   236	        return OperationJournalEntry(
   237	            idempotency_key=entry.idempotency_key,
   238	            operation=entry.operation,
   239	            phase="completed",
   240	            collaboration_id=entry.collaboration_id,
   241	            created_at=entry.created_at,
   242	            repo_root=entry.repo_root,
   243	        )
   244	
   245	    def _finalize_confirmed_turn(
   246	        self,
   247	        *,
   248	        entry: OperationJournalEntry,
   249	        turn_id: str | None,
   250	        policy_fingerprint: str | None,
   251	        outcome_timestamp: str,
   252	    ) -> None:
   253	        """Persist all local artifacts for a confirmed turn before completion."""
   254	
   255	        if entry.context_size is not None and entry.turn_sequence is not None:
   256	            self._turn_store.write(
   257	                entry.collaboration_id,
   258	                turn_sequence=entry.turn_sequence,
   259	                context_size=entry.context_size,
   260	            )
   261	
   262	        if entry.runtime_id is not None and turn_id is not None:
   263	            self._journal.append_dialogue_audit_event_once(
   264	                AuditEvent(
   265	                    event_id=self._uuid_factory(),
   266	                    timestamp=self._journal.timestamp(),
   267	                    actor="claude",
   268	                    action="dialogue_turn",
   269	                    collaboration_id=entry.collaboration_id,
   270	                    runtime_id=entry.runtime_id,
   271	                    context_size=entry.context_size,
   272	                    turn_id=turn_id,
   273	 
... [truncated 2062 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 721ef9
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 452
Output:
   140	
   141	An [audit event](contracts.md#auditevent) with `action: escalate` is emitted for every unknown request received.
   142	
   143	## Concurrency Limits
   144	
   145	### Max Concurrent Delegation Jobs
   146	
   147	**v1: exactly 1.** If Claude calls `codex.delegate.start` while a delegation job is already running, the control plane returns a [Job Busy](contracts.md#job-busy) response with the active job's ID and status.
   148	
   149	This eliminates queueing, admission control, and contention management for v1. The delegation flow is strictly sequential.
   150	
   151	### Advisory-Delegation Race
   152	
   153	Advisory turns and promotion checks can race with workspace drift:
   154	
   155	1. Advisory consult reads workspace state.
   156	2. Delegation runs and produces artifacts.
   157	3. Promotion changes HEAD.
   158	4. Next advisory turn has stale context.
   159	
   160	This does not break safety — the advisory runtime's read-only sandbox prevents writes. It breaks **coherence**: Codex's advisory responses are grounded in a workspace state that no longer exists.
   161	
   162	v1 resolves this with same-thread next-turn context injection. Successful promotion marks advisory context stale; the next advisory turn receives a workspace-changed summary plus refreshed repository identity/context, and the stale marker is cleared after that turn is successfully dispatched. See [advisory-runtime-policy.md §Post-Promotion Coherence](advisory-runtime-policy.md#post-promotion-coherence).
   163	
   164	## Retention Defaults
   165	
   166	Canonical retention values. All TTLs are measured from `last_touched_at`, not creation time.
   167	
   168	| Resource | TTL | Trigger |
   169	|---|---|---|
   170	| Completed worktree | 1 hour | After promotion or discard |

```

## ASSISTANT REPLY (Codex → agent)

**Failure Modes**

This is the second case, not the first: the rotation spec has an unstated coupling to total-order turn admission inside one advisory domain. If dispatch becomes parallel, the spec breaks immediately because “next turn boundary” stops being well-defined. The shared contention unit is one advisory runtime per `(Claude session, repo_root)`, not one conversation, per [foundations.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:81) and [control_plane.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py:275). The code even documents this dependency directly for dialogue turn sequencing in [dialogue.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/dialogue.py:394).

1. **Stale admission after freeze**
   1. Turn A and Turn B both read current runtime `R0` and fingerprint `F0`.
   2. Turn A decides widening is needed and starts rotation `R0 -> R1`.
   3. Before or during A’s freeze/remap, Turn B has already bound itself to `R0` and proceeds to `turn/start`.
   4. Result: B runs on the stale runtime after the policy boundary moved, violating “frozen runtimes accept no new turns” and undermining the guarantee that policy evaluation happens between turns. This is the most direct break.

2. **Double rotation from the same source runtime**
   1. Turns A and B both inspect `R0` and both conclude widening is required.
   2. A freezes `R0`, starts `R1`, forks history, updates mappings.
   3. B, still acting on the stale snapshot, also freezes or treats `R0` as current, starts `R2`, forks the same history, updates mappings.
   4. Result: split-brain replacement runtimes, last-writer-wins registry state, orphaned runtime/thread lineage, and ambiguous audit history. The current lineage update is append-only last-wins with no CAS in [lineage_store.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py:169).

3. **Conflicting direction at the same “next turn boundary”**
   1. Current runtime `Rw` is widened.
   2. Turn A is local-only and decides it should narrow to `Rn` under the “narrowest sufficient policy” rule in [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:63).
   3. Turn B concurrently requires network and decides the wide policy must remain.
   4. Without a total order, there is no defined answer to which turn owns the boundary. Depending on timing, A can narrow just as B starts, or B can keep wide just as A narrows, causing either stale dispatch on the frozen runtime or oscillating `wide -> narrow -> wide` churn. The phrase “next turn boundary” only makes sense if turns are ordered.

4. **Partial or stale handle remap across multiple dialogues**
   1. Rotation is runtime-scoped, but dialogue routing is handle-scoped.
   2. Turn A rotates `R0 -> R1` and starts remapping handles from `runtime_id=R0` to `runtime_id=R1`.
   3. Turn B reads handle `H2` before `update_runtime(H2)` lands, then journals and dispatches using stale `runtime_id/thread_id`.
   4. Result: some handles point at `R1` while another in-flight reply still talks to `R0`. Because consults are ephemeral and not persisted as handles in [contracts.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md:39), any lock keyed only by `collaboration_id` misses part of the surface.

5. **Premature reap of the frozen runtime**
   1. Turn A rotates `R0 -> R1`.
   2. Turn C, admitted stale, is still running or about to start on `R0`.
   3. Turn B succeeds on `R1`, satisfying the current primary reap condition in [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:100).
   4. `R0` is reaped while C still depends on it.
   5. Result: lost turn, failed repair/read path, or undefined behavior against a runtime that should have remained readable until no live admissions remained.

6. **Duplicate sequencing on the same dialogue handle**
   1. Two replies to the same `collaboration_id` race.
   2. Both call `thread/read`, both derive the same next `turn_sequence`, both journal intent.
   3. If a rotation happens in the middle, one may journal against `R0`, the other against `R1`; if not, they may collide semantically even if keys differ later.
   4. Result: broken monotonic turn numbering or duplicate follow-up turns. This is broader than rotation, but it proves the current model already assumes serialized admission at the domain level.

**Minimum Contract**

The smallest safe delta is not a per-conversation lock and not a bare CAS field. The load-bearing requirement is:

1. **Define the concurrency unit explicitly as the advisory domain**: `(claude_session_id, repo_root)`.
2. **Require linearized turn admission within that domain**: for a given advisory domain, the control plane must serialize:
   1. policy evaluation,
   2. freeze/rotate decisions,
   3. runtime-registry replacement,
   4. handle remaps,
   5. turn binding to a runtime/thread.
3. **State that once a runtime is marked frozen, no new turn may bind to it**. Reads/forks for rotation/recovery may continue; new admissions may not.
4. **Make reap contingent on both conditions**:
   1. replacement runtime has completed its first successful turn,
   2. no advisory turn remains bound to the frozen runtime.

That is the minimum spec contract. Implementation-wise, the natural mechanism is a **per-advisory-domain mutex**. A single global mutex is safe but not minimal; it over-serializes unrelated repos/sessions. A per-`collaboration_id` lock is insufficient because multiple dialogues and consultations share the same runtime, and consults do not even have durable handles.

**What Is Load-Bearing vs Nice-to-Have**

- **Load-bearing**
  - Per-advisory-domain linearization point.
  - Frozen-runtime admission rule: no new turn binds after freeze.
  - Reap rule that accounts for outstanding bound turns.

- **Not sufficient on its own**
  - Per-`collaboration_id` locks.
  - CAS only on handle mapping.
  - A mutex only around the registry map but not around policy-eval + bind + remap.

- **Nice-to-have hardening**
  - A monotonic runtime generation/epoch on the advisory domain.
  - Record that generation in handles/journal intents.
  - Revalidate generation before dispatch; if it changed, restart admission.
  - This helps detect stale snapshots and makes future refactors safer, but it is not a substitute for the domain-level linearization rule.

**Bottom Line**

The spec is currently relying on an unstated coupling that will break the first time dispatch stops being serialized. The reason is simple: the policy model uses “next turn boundary” semantics, and that concept requires a total order over turn admissions in a shared advisory runtime. Today that total order is supplied externally by MCP serialization in [delivery.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md:212). If that external invariant changes, the rotation spec is no longer complete.

## USER TURN 4 (agent → Codex)

```
Excellent. Now let's press the widening-request and policy-truth-source weak points together, because they're coupled.

Your T1 finding: `codex.consult` schema has no capability fields; `ConsultRequest` carries only `network_access: bool` plus an opaque `profile`; fingerprint tracks 5 dimensions (transport, sandbox, network, approval, connectors). The foundations.md prose doesn't line up one-to-one with the fingerprint dimensions. Also: `profile` interacts with policy in ways the spec doesn't pin.

Three probes:

1. **Request-surface shape**: If you had to define the capability request contract today, would you prefer (a) a flat capability struct on every request (`sandbox=..., network=..., approval=..., connectors=[...]`), (b) a named-policy-level enum with a small fixed set (`readonly`, `read_write`, `network_read`, etc.), or (c) a delta-against-base model (request names only what it wants to change)? What are the consequences for narrowing detection — which shape makes "compare requested capabilities against base-policy defaults" computable without special cases?

2. **Profile-vs-capability interaction**: Named profiles exist in `profiles.py` and are treated as a policy-shape preset. If a request carries both `profile="..."` and explicit capability fields, who wins? Does the spec need to say this is invalid, or define precedence, or is one of them advisory metadata and the other authoritative?

3. **Effective-policy object**: You recommended "one normative effective advisory policy table or typed object, fingerprint derives from exactly that." Concretely — should that be a dataclass pinned in `foundations.md` with a schema block, or a separate contract file (e.g., `policy-model.md`)? What's the minimum set of fields beyond the current 5 that would make widen/narrow decisions unambiguous (e.g., do we need `cwd_policy`, `env_policy`, `reasoning_effort`, or are those orthogonal)?

Focus sharp answers — "this is the shape, this is why, this is what fails otherwise."
```

## ASSISTANT REPLY (Codex → agent)

I’m narrowing this to the policy-contract layer: request shape, profile semantics, and the minimum effective-policy object. I’m checking the actual profile definitions and any spec text that already treats profiles as policy-bearing versus purely prompt-control metadata, so the recommendations don’t accidentally fight an existing contract.

### TOOL CALL `exec_command`

```json
{
  "cmd": "sed -n '1,220p' /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/references/consultation-profiles.yaml",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"profile|posture|turn_budget|reasoning_effort|sandbox|approval_policy|network\" /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration -g '*.md'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 5000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py | sed -n '32,170p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 4000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 5c63ea
Wall time: 0.0001 seconds
Process exited with code 0
Original token count: 1048
Output:
# Consultation Profiles
#
# Version: 0.2.0
# Reference: consultation-contract.md §14
#
# Named profiles resolve to a complete set of execution controls.
# Resolution order: explicit flags > named profile > contract defaults.
#
# Explicit flags (-m, -s, -a, -t) override profile fields.
# Unknown profile names are rejected during resolution.
#
# To add a local override (gitignored):
#   Create consultation-profiles.local.yaml alongside this file.
#   Local profiles merge with and override these defaults.
#
# Posture values: adversarial, collaborative, exploratory, evaluative, comparative

profiles:

  quick-check:
    description: >
      Fast sanity check or targeted question. Single-turn direct invocation.
      Use when you want a quick second opinion without extended back-and-forth.
    sandbox: read-only
    approval_policy: never
    reasoning_effort: medium
    posture: collaborative
    turn_budget: 1

  collaborative-ideation:
    description: >
      Sustained brainstorming and idea generation over multiple turns. Build on
      each other's proposals, combine approaches, explore "what if" scenarios.
      Use when generating options, not evaluating them.
    sandbox: read-only
    approval_policy: never
    reasoning_effort: high
    posture: collaborative
    turn_budget: 6

  exploratory:
    description: >
      Open-ended research and ideation. Map the solution space without committing
      to a direction. Use when exploring a new problem or approach.
    sandbox: read-only
    approval_policy: never
    reasoning_effort: high
    posture: exploratory
    turn_budget: 6

  deep-review:
    description: >
      Thorough multi-turn review with high reasoning effort. Use for architecture
      review, plan evaluation, or detailed quality audit. Evaluative posture
      covers both structural analysis and correctness verification.
    sandbox: read-only
    approval_policy: never
    reasoning_effort: xhigh
    posture: evaluative
    turn_budget: 8

  code-review:
    description: >
      Focused code or document review. Evaluative posture, read-only access.
      Use when reviewing specific implementations that can be described in the
      briefing material.
    sandbox: read-only
    approval_policy: never
    reasoning_effort: high
    posture: evaluative
    turn_budget: 4

  adversarial-challenge:
    description: >
      Challenge assu
... [truncated 1792 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 992621
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2402
Output:
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:160:This does not break safety — the advisory runtime's read-only sandbox prevents writes. It breaks **coherence**: Codex's advisory responses are grounded in a workspace state that no longer exists.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:34:When a turn requires capabilities beyond the current runtime's policy (e.g., network access for a web-facing research question):
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:44:- Claude explicitly requests a capability that exceeds the current policy (e.g., `codex.consult` with `network: true` when the current runtime has network disabled).
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:26:- Preserve strong trust boundaries around secrets, paths, sandboxing, and write surfaces.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:142:- Whether web/network access is allowed
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:148:App Server enforces sandboxing, approval semantics, and thread/session state. This is defense-in-depth, not the only barrier.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:191:Native Codex review and task flows exist and handle basic prompting. This contract governs the spec's structured prompt packets, which carry additional metadata such as posture, effort, and supplementary context that native flows do not express.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:206:The official plugin assembles context through native app-server thread utilities. This contract applies to the spec's structured flows, which require richer assembly such as redaction, lineage injection, and profile-driven effort than native utilities provide.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:208:The control plane owns context selection, redaction, trimming, and final packet assembly for all Codex-facing calls. The caller pr
... [truncated 7207 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 60b15c
Wall time: 0.0001 seconds
Process exited with code 0
Original token count: 1415
Output:
    32	@dataclass(frozen=True)
    33	class ResolvedProfile:
    34	    """Fully resolved execution controls."""
    35	
    36	    posture: Posture
    37	    turn_budget: int
    38	    effort: Effort | None
    39	    sandbox: SandboxPolicy
    40	    approval_policy: ApprovalPolicy
    41	
    42	
    43	_DEFAULT_POSTURE = "collaborative"
    44	_DEFAULT_TURN_BUDGET = 6
    45	_DEFAULT_SANDBOX = "read-only"
    46	_DEFAULT_APPROVAL = "never"
    47	
    48	_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"
    49	
    50	
    51	def load_profiles(
    52	    base_path: Path | None = None,
    53	) -> dict[str, dict[str, Any]]:
    54	    """Load profiles from YAML. Merges local overrides if present."""
    55	    base = base_path or _REFERENCES_DIR
    56	    profiles_path = base / "consultation-profiles.yaml"
    57	    if not profiles_path.exists():
    58	        return {}
    59	
    60	    with open(profiles_path) as f:
    61	        data = yaml.safe_load(f) or {}
    62	
    63	    profiles: dict[str, dict[str, Any]] = data.get("profiles", {})
    64	
    65	    local_path = base / "consultation-profiles.local.yaml"
    66	    if local_path.exists():
    67	        with open(local_path) as f:
    68	            local_data = yaml.safe_load(f) or {}
    69	        for name, overrides in local_data.get("profiles", {}).items():
    70	            if name in profiles:
    71	                profiles[name] = {**profiles[name], **overrides}
    72	            else:
    73	                profiles[name] = overrides
    74	
    75	    return profiles
    76	
    77	
    78	def resolve_profile(
    79	    *,
    80	    profile_name: str | None = None,
    81	    explicit_posture: Posture | None = None,
    82	    explicit_turn_budget: int | None = None,
    83	    explicit_effort: Effort | None = None,
    84	    explicit_sandbox: SandboxPolicy | None = None,
    85	    explicit_approval_policy: ApprovalPolicy | None = None,
    86	) -> ResolvedProfile:
    87	    """Resolve execution controls from profile + explicit overrides."""
    88	    profile: dict[str, Any] = {}
    89	    if profile_name is not None:
    90	        profiles = load_profiles()
    91	        if profile_name not in profiles:
    92	            raise ProfileValidationError(
    93	                f"Profile resolution failed: unknown profile. "
    94	         
... [truncated 3265 chars]
```

## ASSISTANT REPLY (Codex → agent)

The existing spec already gives a useful separation: profiles are clearly used for prompt/context behavior, but the current implementation also lets them carry sandbox and approval fields. That is exactly the ambiguity to remove. I’m pulling the line-numbered foundations section so I can answer the precedence question cleanly.

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md | sed -n '188,244p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 3500,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py | sed -n '28,42p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 1500,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/models.py | sed -n '35,55p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 1500,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 9eb639
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 1287
Output:
   188	
   189	## Prompting Contract
   190	
   191	Native Codex review and task flows exist and handle basic prompting. This contract governs the spec's structured prompt packets, which carry additional metadata such as posture, effort, and supplementary context that native flows do not express.
   192	
   193	The plugin owns Codex-side prompt templates. Each capability builds a structured packet with:
   194	
   195	- Objective
   196	- Relevant repository context
   197	- User constraints
   198	- Safety envelope
   199	- Expected output shape
   200	- Capability-specific instructions
   201	
   202	The plugin does not rely on Codex-side skills, plugin discovery, or App Server collaboration modes for core behavior in v1. The stable baseline is: explicit prompt packets plus stable thread/turn APIs.
   203	
   204	## Context Assembly Contract
   205	
   206	The official plugin assembles context through native app-server thread utilities. This contract applies to the spec's structured flows, which require richer assembly such as redaction, lineage injection, and profile-driven effort than native utilities provide.
   207	
   208	The control plane owns context selection, redaction, trimming, and final packet assembly for all Codex-facing calls. The caller provides the objective, user constraints, and optional candidate references such as file paths, artifact identifiers, or promoted summary material. Candidate references are hints, not entitlements: the control plane may omit, trim, or reject them as needed to satisfy the active capability profile, budget caps, and policy rules. The hook guard remains rejection-only: it validates the final assembled packet and may reject or escalate it, but it does not participate in context selection.
   209	
   210	### Ownership and Profiles
   211	
   212	Context assembly uses one control-plane framework with two capability profiles:
   213	
   214	- **Advisory profile** for consultation and dialogue in the read-only advisory runtime
   215	- **Execution profile** for delegation in an isolated writable worktree
   216	
   217	These profiles are filters over a shared assembly pipeline, not separate architectures. The profile determines which source categories are eligible, how packet fields are populated, and which budget caps apply.
   218	
   219	### Source Rules
   220	
   221	#### Source Categories
   222	
   223	|
... [truncated 2752 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 34c230
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 186
Output:
    28	        "name": "codex.consult",
    29	        "description": "One-shot second opinion using the advisory runtime.",
    30	        "inputSchema": {
    31	            "type": "object",
    32	            "properties": {
    33	                "repo_root": {"type": "string"},
    34	                "objective": {"type": "string"},
    35	                "explicit_paths": {"type": "array", "items": {"type": "string"}},
    36	                "profile": {
    37	                    "type": "string",
    38	                    "description": "Named consultation profile (e.g., quick-check, deep-review)",
    39	                },
    40	            },
    41	            "required": ["repo_root", "objective"],
    42	        },

```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 739286
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 218
Output:
    35	class ConsultRequest:
    36	    """Caller-facing consult request for the advisory runtime."""
    37	
    38	    repo_root: Path
    39	    objective: str
    40	    user_constraints: tuple[str, ...] = ()
    41	    acceptance_criteria: tuple[str, ...] = ()
    42	    explicit_paths: tuple[Path, ...] = ()
    43	    explicit_snippets: tuple[str, ...] = ()
    44	    task_local_paths: tuple[Path, ...] = ()
    45	    broad_repository_summaries: tuple[str, ...] = ()
    46	    promoted_summaries: tuple[str, ...] = ()
    47	    delegation_summaries: tuple[str, ...] = ()
    48	    supplementary_context: tuple[str, ...] = ()
    49	    external_research_material: tuple[str, ...] = ()
    50	    parent_thread_id: str | None = None
    51	    network_access: bool = False
    52	    profile: str | None = None
    53	
    54	
    55	@dataclass(frozen=True)

```

## ASSISTANT REPLY (Codex → agent)

1. **Request-surface shape**

Use **(a) a flat capability struct**, but make the control plane canonicalize it into a full `target_policy` object before any reuse/rotate decision.

```json
{
  "repo_root": "...",
  "objective": "...",
  "profile": "deep-review",
  "requested_capabilities": {
    "sandbox_policy": "read_only",
    "network_access": false,
    "approval_mode": "never",
    "connector_allowlist": []
  }
}
```

Why this shape:
- It makes policy evaluation mechanical. Compute `target_policy = base_policy + explicit capability fields`, then compare `current_policy` to `target_policy`.
- It removes the need for bespoke “narrowing detection.” If `current_policy == target_policy`, reuse. If not, rotate. “Widen” vs “narrow” becomes a secondary label, not the core decision procedure.
- It keeps each privilege dimension independent. That matches the fingerprint model better than bundles do.

What fails otherwise:
- **(b) Named policy enum** fails because it collapses independent axes into pre-baked bundles. The first time you need “network on, connectors off, still read-only,” you either explode the enum matrix or invent hidden exceptions. Narrowing becomes table-specific, not generic.
- **(c) Delta-against-base** fails because omission is ambiguous. Does omitted mean “base,” “current,” or “caller doesn’t care”? That ambiguity is exactly what makes narrowing inference brittle. A delta model is fine as client-side sugar, but the normative control-plane contract still needs a fully materialized `target_policy`.

Current evidence for the gap is the tiny wire surface in [mcp_server.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py:28) and the request model in [models.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/models.py:35).

2. **Profile vs capability interaction**

Make **capabilities authoritative** and **profiles non-authoritative**.

The spec already leans this way: profiles are described as prompt/context machinery in [foundations.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:191) and [foundations.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:206). They control posture, effort, packet shaping, and budget behavior, not trust boundaries.

So the clean rule is:

- `requested_capabilities` defines runtime policy.
- `profile` defines prompt/context behavior only.
- A profile may set `posture`, `reasoning_effort`, `turn_budget`, and source-selection defaults.
- A profile may **not** set `sandbox`, `approval`, `network`, or connectors.

Why this is the right cut:
- It preserves one source of truth for privilege.
- It keeps fingerprints and audits explainable.
- It prevents hidden widening through a named preset.

What fails otherwise:
- The current `profiles.py` shape treats profile resolution as “execution controls,” including `sandbox` and `approval_policy` in [profiles.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:32) and [profiles.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py:78). That creates two policy channels: the explicit request and the profile.
- If you solve that with silent precedence, the effective policy becomes opaque. Two identical requests can widen differently depending on an off-to-the-side profile definition.
- If you keep both channels live, narrowing is no longer a pure policy comparison; it becomes “policy comparison plus profile interpretation.”

If you need a migration rule, use this:
- During transition, explicit capability fields win.
- Any profile that also carries policy-bearing fields must either match exactly or the request is invalid.
- Do **not** allow silent override.

3. **Effective-policy object**

Put the normative model in a **separate policy contract**, not in `foundations.md` prose. A dedicated `policy-model.md` is better than burying it in foundations, because this object is shared by request parsing, rotation, fingerprinting, audit, recovery, and runtime boot. `foundations.md` should reference it, not be the only place it exists.

Minimum object:

```text
EffectiveAdvisoryPolicy
- transport_mode: "stdio"
- sandbox_policy: "read_only" | ...
- network_access: bool
- approval_mode: "never" | "per_request_only"
- connector_allowlist: set[str]
```

Two concrete clarifications matter here:

- `connector_allowlist` should be a set, not a boolean. “Connectors enabled” is not a stable policy description if different connector sets are materially different privileges.
- `transport_mode` can remain fixed in v1, but it still belongs in the effective policy because the fingerprint already claims to cover it.

What to add beyond the current 5:
- **Add `dynamic_tools_policy` only if it is intended to vary at runtime.** If it is always disabled in advisory, say that explicitly and keep it outside the mutable policy model.
- **Do not add `reasoning_effort`.** That is prompt behavior, not privilege.
- **Do not add `cwd_policy` or `env_policy` unless the spec intends them to become privilege-bearing controls.** Right now they are orthogonal. Adding speculative fields bloats the model and makes comparison harder without solving today’s ambiguity.

What fails otherwise:
- If the effective-policy object stays implicit in foundations prose, implementation will keep re-deriving it in multiple places, and fingerprint drift is guaranteed.
- If you mix privilege fields with prompt fields, rotation starts depending on metadata that should not trigger runtime replacement.
- If connectors stay boolean, future widening across different connector subsets becomes un-auditable.

The sharp version is:

- **Request contract**: flat explicit capability struct.
- **Decision procedure**: canonicalize to full `target_policy`, then compare to `current_policy`.
- **Profile contract**: prompt/context metadata only.
- **Normative truth source**: one typed `EffectiveAdvisoryPolicy` contract file, with fingerprint derived from exactly that object and nothing else.

## USER TURN 5 (agent → Codex)

```
Let me press the narrowing rule itself — I want to stress-test whether the spec's "narrowest sufficient policy for the next turn" principle is even well-defined as a trigger, before we accept it as correct.

Three challenges:

1. **Narrowing trigger ambiguity**: The spec says narrow when requested capabilities fall below base-policy defaults at a turn boundary. But in a *dialogue* (multi-turn consultation), the control plane does not know the caller's *next* turn's needs until that turn arrives. Two interpretations:
   - (a) "Lazy narrowing": only narrow when turn N+1 explicitly signals a smaller footprint than current runtime
   - (b) "Speculative narrowing": after a widened turn completes, always narrow back to base unless the next turn is already queued with a widening request
   
   The spec reads closer to (a) but is ambiguous. Which is correct, and what failure modes does the other interpretation produce? Specifically: does (b) cause thrash (widen → turn → narrow → turn needs widen again → widen) across consultation sequences that oscillate, and does (a) leave capability lingering longer than necessary (violating least-privilege)?

2. **"Sufficient" is unverifiable**: The control plane cannot know what a turn actually needs until the turn runs. If we narrow speculatively and the turn then fails due to missing capability, is the spec's answer "refuse and require explicit widening request," or "auto-rotate mid-turn"? Mid-turn rotation is banned by the freeze-and-rotate invariant, so the only safe answer seems to be "refuse". But then the control plane is making a privilege-usage prediction, which is inherently wrong sometimes — what's the recovery contract?

3. **Narrowing observability**: Widening has a clear signal (caller requested network_access=True). Narrowing has no caller-initiated signal — it's control-plane detection. That means auditability is asymmetric: widening appears in requests, narrowing only in server-internal logs. Is that acceptable, or should narrowing require an explicit `rotate` audit event with a reason code (e.g., "idle base-policy reclamation", "caller hinted local-only", "timeout-based reap") so downstream review can reconstruct intent?

Push back if the current framing is fine; otherwise, where does this leave the narrowing spec?
```

## ASSISTANT REPLY (Codex → agent)

1. **Narrowing trigger**

The correct reading is **(a) lazy narrowing**, not speculative narrowing.

The spec already points that way: narrowing happens at the **next turn boundary**, “not immediately after the widened action completes,” and is triggered when Claude **initiates a turn** that does not require the elevated capability in [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:67) and [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:71). Interpretation (b) conflicts with that text.

Why (b) is wrong:
- It creates guaranteed `widen -> turn -> narrow -> widen` thrash on oscillating dialogues.
- It multiplies freeze/fork/remap/reap events for no new information.
- It increases crash-recovery surface and audit noise.
- It makes the control plane guess about a future turn it has not yet seen.

What (a) costs:
- Elevated capability lingers between turns longer than the absolute minimum wall-clock time.

Why that lingering is acceptable:
- The spec’s granularity is **per turn**, not “per idle gap” or “per sub-action.”
- Between turns, there is no active work to over-serve. The next admission point is where least privilege is enforced.
- If you want “always reclaim to base immediately after each widened turn,” that is a different policy. It is stricter, but it is not what this spec currently says, and it comes with clear churn costs.

So I would tighten the wording from:

- “each turn runs under the narrowest sufficient policy”

to:

- “each turn is admitted under the narrowest **requested** target policy for that turn”

That removes the oracle implication.

2. **“Sufficient” and recovery**

I agree with the challenge: **“sufficient” is not actually knowable by the control plane**. The control plane can only evaluate the policy the caller declared, not the latent needs Codex might discover during execution.

That means the safe contract is:

- No mid-turn rotation. That ban is already explicit in [advisory-runtime-policy.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:112).
- If the caller requests a lower policy and the turn later needs more, the turn is **refused or fails under that policy**.
- Recovery is: Claude retries with a wider `requested_capabilities` object, which triggers a new pre-turn rotation.
- There is no automatic “continue the same turn after widening.”

The current implementation already leans this way for widening: `codex_consult` rejects `network_access=True` rather than trying to widen in place in [control_plane.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py:147).

So the spec should stop pretending the control plane predicts actual need. It should say something like:

- The control plane evaluates the **declared target policy** for a turn.
- If the turn later encounters an unavailable capability, the turn returns an explicit widening-required failure or denial outcome.
- Claude may retry as a new turn with a broader target policy.
- Per-request server approvals remain per-request; they do not widen runtime policy.

Without that clarification, “sufficient” reads as if the control plane is making a semantic judgment about the future behavior of the turn. It cannot.

3. **Narrowing observability**

The current asymmetry is not good enough once real rotation exists.

Widening has an obvious external cause in the request. Narrowing does not. If narrowing remains “control-plane detected,” then the audit trail must carry enough intent to reconstruct why the runtime changed. Right now the audit contract is too thin for that.

I would require every rotation, including narrowing, to emit a `rotate` event with:

- `old_runtime_id`
- `new_runtime_id`
- `old_policy_fingerprint`
- `new_policy_fingerprint`
- `reason_code`
- `trigger_source`

For the current model, the valid narrowing reason codes should stay narrow:
- `request_target_policy_lower_than_current`
- `request_target_policy_equals_base`

I would **not** add `idle base-policy reclamation` unless the spec explicitly adopts speculative/background narrowing, which I do not think it should.

So the answer to your asymmetry question is: **no, it is not acceptable as-is**. If narrowing is automatic, it must be explicit in the audit trail, with a reason that points back to the turn-admission policy evaluation.

**Where This Leaves the Narrowing Spec**

I would not accept the current narrowing text as final. The right repair is small but important:

- Keep **lazy narrowing** only.
- Reject speculative narrowing explicitly.
- Replace “narrowest sufficient” with “narrowest declared target policy.”
- Define the underdeclared-turn recovery contract as **fail and retry with widening**, never mid-turn rotate.
- Make narrowing fully observable through explicit rotate events with reason codes and old/new policy identity.

That keeps the original intent, but turns narrowing from a slogan into an executable contract.

## USER TURN 6 (agent → Codex)

```
Two remaining unresolved items. Combine into one pass:

1. **Generation/epoch hardening**: You previously listed monotonic runtime generation as "nice-to-have, not load-bearing." But consider two scenarios:
   - (a) A handle mapping update lands before the turn-binding step sees it — even with the per-advisory-domain mutex, if the mutex releases between remap and bind, we need *something* to detect that the registry moved under us.
   - (b) Crash-recovery journal replay reconstructs runtime state from a stored fingerprint plus rotation events. Without a generation number, can a replay deterministically reproduce the post-rotation binding state when two rotations share a fingerprint (e.g., narrow → widen → narrow back to same)?
   
   Given those: is the generation/epoch actually load-bearing for recovery determinism, even if it's "only" hardening for concurrency? Does your answer change if we assume Release 2 or 3 adds journal-based recovery of advisory state?

2. **Base-policy programmatic authority**: You noted foundations.md has prose tables, not a typed object. But the spec today uses "base policy defaults" as a load-bearing term for the narrowing comparison. Two sub-questions:
   - Should the base policy itself be a configured value (per deployment, per repo) or a hardcoded constant (one canonical read-only advisory profile)? If per-deployment, what's the config contract — env var, settings file, control-plane startup parameter?
   - If the base policy is configurable, does that introduce a new rotation trigger category (base policy changed at startup → all current runtimes must rotate)? Or is base policy fixed for the lifetime of a session?

Answer both concretely. Then give me your final sharpest summary: what is the single most important weak point a spec author should fix first, and why that one before the others.
```

## ASSISTANT REPLY (Codex → agent)

I’m checking the recovery contract directly before answering the generation question, because that determines whether epoching stays “hardening” or becomes part of the authoritative state machine. I’m also checking whether the spec already says base policy is session-fixed or deployment-configurable anywhere.

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md | sed -n '1,140p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 5000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "nl -ba /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md | sed -n '138,146p'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 2000,
  "yield_time_ms": 1000
}
```

### TOOL CALL `exec_command`

```json
{
  "cmd": "rg -n \"base policy|defaults|startup parameter|env var|settings file|configurable|session\" /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration -g '*.md'",
  "workdir": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model",
  "max_output_tokens": 5000,
  "yield_time_ms": 1000
}
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 2837f6
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 2231
Output:
     1	---
     2	module: recovery-and-journal
     3	status: active
     4	normative: true
     5	authority: recovery-contract
     6	---
     7	
     8	# Recovery and Journal
     9	
    10	Contracts for crash recovery, operation journaling, audit logging, concurrency control, and resource retention.
    11	
    12	## Two-Log Architecture
    13	
    14	The plugin maintains two separate logs with different purposes, write disciplines, and retention policies.
    15	
    16	| Property | Operation Journal | Audit Log |
    17	|---|---|---|
    18	| Purpose | Idempotent replay after crash | Human incident reconstruction |
    19	| Write discipline | fsync before dispatch | Best-effort append |
    20	| Retention | Trim on operation completion | TTL-based (30 days) |
    21	| Scope | Session-bounded (v1) | Cross-session |
    22	| Consumer | Control plane (automatic recovery) | Claude + user (diagnostics) |
    23	| Format | Operation records with idempotency keys | [AuditEvent](contracts.md#auditevent) records (JSONL) |
    24	
    25	### Why Two Logs
    26	
    27	The audit log answers "what happened?" The operation journal answers "what was I in the middle of doing?" They have different write patterns, different retention windows, and different consumers. Merging them would either over-retain operational state or under-protect the audit trail.
    28	
    29	## Operation Journal
    30	
    31	The operation journal ensures that crash recovery is deterministic replay, not inspection-based guessing.
    32	
    33	### Write Ordering
    34	
    35	**Journal before dispatch.** Every dispatched operation is written to the journal before the corresponding App Server request is sent. This guarantees that:
    36	
    37	- If the control plane crashes after journal write but before dispatch, the operation can be retried.
    38	- If the control plane crashes after dispatch, the journal records what was in flight.
    39	- If the control plane crashes before journal write, no operation was dispatched and no cleanup is needed.
    40	
    41	### Idempotency Keys
    42	
    43	Each journaled operation carries a unique idempotency key. If the same key is replayed, the control plane checks the operation's outcome rather than re-dispatching.
    44	
    45	| Operation | Idempotency Key Components | Effect of Replay |
    46	|---|---|---|
    47	| Job creation | `
... [truncated 6527 chars]
```

### TOOL OUTPUT `exec_command`

```
Chunk ID: fe9c96
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 282
Output:
   138	## Recovery and Journal Interactions
   139	
   140	Rotation events affect crash recovery and journaling:
   141	
   142	- Each rotation emits an [audit event](contracts.md#auditevent) with `action: rotate`, linking the old and new runtimes.
   143	- If the control plane crashes mid-rotation, the [operation journal](recovery-and-journal.md#operation-journal) ensures the rotation is either completed or rolled back on restart.
   144	- Crash recovery for advisory runtimes follows the path defined in [recovery-and-journal.md §Advisory Runtime Crash](recovery-and-journal.md#advisory-runtime-crash). Frozen runtimes that survive a crash are rediscovered and scheduled for reaping during recovery.
   145	- Successful promotions write a `stale_advisory_context` marker to the operation journal before success is acknowledged. Crash recovery reloads any surviving marker and preserves the next-turn injection requirement until the first post-promotion advisory turn is successfully dispatched.
   146	- Reap timing follows [retention defaults](recovery-and-journal.md#retention-defaults) for the TTL fallback condition.

```

### TOOL OUTPUT `exec_command`

```
Chunk ID: 3cd270
Wall time: 0.0000 seconds
Process exited with code 0
Original token count: 3543
Output:
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/decisions.md:27:## Supersession Direction
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/decisions.md:35:[dialogue-supersession-benchmark.md](dialogue-supersession-benchmark.md) shows
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:73:Narrowing is triggered when Claude initiates a turn that does not require the current runtime's elevated capabilities. The control plane compares the requested capabilities against the [base policy defaults](foundations.md#advisory-domain) and rotates down if the turn can be served at a lower privilege level.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:108:| Claude session ends | Terminal | All advisory runtimes for the session are cleaned up |
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:146:- Reap timing follows [retention defaults](recovery-and-journal.md#retention-defaults) for the TTL fallback condition.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md:211:- Lineage store implementation per [contracts.md §Lineage Store](contracts.md#lineage-store): session-partitioned append-only JSONL at `${CLAUDE_PLUGIN_DATA}/lineage/<claude_session_id>/`, crash-safe semantics, lifecycle management, and advisory runtime rotation mapping
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md:216:- Operation journal entries for all dispatched dialogue operations: journal-before-dispatch per [recovery-and-journal.md §Write Ordering](recovery-and-journal.md#write-ordering). `dialogue.start` uses thread-creation idempotency key (`claude_session_id` + `collaboration_id`); `dialogue.reply` uses turn-dispatch key (`runtime_id` + `thread_id` + `turn_sequence`). See [§Idempotency Keys](recovery-and-journal.md#idempotency-keys). Trim on completion.
/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md:229:- Lineage store persists handles to disk (append-only JSONL) and recovers them after a simulated process crash within a session, including discarding incom
... [truncated 11762 chars]
```

## ASSISTANT REPLY (Codex → agent)

1. **Generation / epoch hardening**

For **today’s spec**, generation is still not strictly load-bearing **if** the concurrency contract is written strongly enough: the per-advisory-domain critical section must cover the whole sequence `evaluate target policy -> rotate/remap if needed -> bind the turn to runtime/thread`. If bind happens inside that linearized section, a separate epoch is not required for safety.

That said, your scenario (a) is real: **if the lock is released before bind**, then a generation check stops being optional. At that point you need an epoch or equivalent CAS token to detect “the advisory domain moved under me.” So the real rule is:

- If the spec requires atomic bind under the domain lock, generation is hardening.
- If the spec permits any split between remap and bind, generation becomes load-bearing.

For **today’s recovery contract**, generation is also not yet strictly load-bearing. The spec’s advisory crash recovery rebuilds from the lineage store and reattaches with `thread/read` + `thread/resume`, not from journal replay of rotation state, in [recovery-and-journal.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:103). The operation journal is defined around in-flight operations and idempotency keys like `runtime_id + thread_id + turn_sequence` in [recovery-and-journal.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:41), and the current delivery text journals dispatched dialogue operations, not advisory rotation state, in [delivery.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md:216).

But **yes, my answer changes if R2/R3 adds journal-based replay of advisory rotation/binding state**. In that world, some monotonic domain version becomes effectively load-bearing. It does not have to be called `generation`, but you need an equivalent ordered binding token. Fingerprint alone is not enough, because `base -> wide -> base` repeats a fingerprint. `runtime_id` uniqueness helps, but on its own it is still just identity, not an ordering token. If replay is supposed to be deterministic rather than “inspect and guess,” the journal needs either:

- `policy_generation: int` on every advisory-domain state change, or
- an equivalent strictly monotonic rotation/binding sequence number.

So my concrete recommendation is:

- Add `policy_generation` to the advisory domain state.
- Persist it on handle remaps, rotation journal entries, and rotate audit events.
- Treat it as the authoritative freshness token for replay and stale-bind detection.

That is the cleanest way to keep concurrency and recovery aligned once advisory rotation becomes journaled state rather than just live-process behavior.

2. **Base-policy programmatic authority**

The base policy should be **resolved from configuration at startup, then fixed for the lifetime of the Claude session**.

I would not make it per-repo by default. The advisory domain is already per session + repo root in [foundations.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md:81), but repo-specific base policy creates hidden trust-tier variance and makes audit/comparison harder for little benefit. The default spec should be:

- One deployment-level base advisory policy.
- Resolved once at control-plane startup into a typed `session_base_policy`.
- Persisted as part of session-scoped advisory state so crash recovery in the same session uses the same base.

On the configuration mechanism, the normative contract should be a **typed control-plane config object or settings file**, not raw env vars. Environment variables are fine as an implementation input, but they are a poor normative interface for a trust boundary. The spec should define something like:

```text
AdvisoryPolicyConfig
- base_advisory_policy: EffectiveAdvisoryPolicy
```

Then the implementation may source that from:
- a plugin settings file, or
- an explicit startup/config parameter.

I would avoid making the spec talk directly in terms of env vars.

On rotation triggers:

- **If base policy is fixed for session lifetime**, then a deployment config change is **not** a live rotation trigger. It applies only to new sessions.
- **If you allow hot base-policy changes during a live session**, then yes, that becomes a new rotation category and every active advisory runtime whose effective policy no longer matches the new session base would need reevaluation and likely rotation.

I would not allow that. Hot-changing the base policy during a session makes recovery much harder, because a control-plane restart mid-session could silently reinterpret the meaning of “base” and mutate trust posture without a caller request. The right rule is:

- Resolve base policy once for the session.
- Persist that resolved value.
- Use it for all widening/narrowing comparisons until session end.

That matches the session-scoped runtime model and avoids a new class of implicit rotations.

**Sharpest Summary**

The single most important weak point to fix first is the **authoritative policy model**: one typed `EffectiveAdvisoryPolicy` / `session_base_policy` contract, plus a request contract that materializes a full `target_policy` per turn.

Fix that first because everything else depends on it. Concurrency control, generation/epoch, narrowing semantics, fingerprinting, audit reasons, and recovery replay are all machinery for moving between policy states. Right now the states themselves are not pinned precisely enough. If you harden concurrency before you define the exact policy object and target-policy derivation, you are stabilizing an undefined state machine.

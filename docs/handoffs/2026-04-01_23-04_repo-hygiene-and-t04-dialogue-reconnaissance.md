---
date: 2026-04-01
time: "23:04"
created_at: "2026-04-01T23:04:16Z"
session_id: 13f510f7-ae9b-4807-baca-22c8eb5c5df5
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_20-30_ac6-finalization-durability-review-and-merge.md
project: claude-code-tool-dev
branch: main
commit: 5fea6a6d
title: "Repo hygiene and T-04 dialogue reconnaissance"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/codex_compat.py
  - packages/plugins/codex-collaboration/server/consultation_safety.py
  - packages/plugins/codex-collaboration/server/context_assembly.py
  - packages/plugins/codex-collaboration/server/credential_scan.py
  - packages/plugins/codex-collaboration/server/jsonrpc_client.py
  - packages/plugins/codex-collaboration/server/mcp_server.py
  - packages/plugins/codex-collaboration/server/prompt_builder.py
  - packages/plugins/codex-collaboration/server/retrieve_learnings.py
  - packages/plugins/codex-collaboration/server/runtime.py
  - packages/plugins/codex-collaboration/server/secret_taxonomy.py
  - packages/plugins/codex-collaboration/tests/conftest.py
  - packages/plugins/codex-collaboration/tests/test_bootstrap.py
  - packages/plugins/codex-collaboration/tests/test_codex_compat.py
  - packages/plugins/codex-collaboration/tests/test_codex_compat_live.py
  - packages/plugins/codex-collaboration/tests/test_codex_guard.py
  - packages/plugins/codex-collaboration/tests/test_consultation_safety.py
  - packages/plugins/codex-collaboration/tests/test_context_assembly.py
  - packages/plugins/codex-collaboration/tests/test_dialogue.py
  - packages/plugins/codex-collaboration/tests/test_dialogue_integration.py
  - packages/plugins/codex-collaboration/tests/test_dialogue_profiles.py
  - packages/plugins/codex-collaboration/tests/test_mcp_server.py
  - packages/plugins/codex-collaboration/tests/test_prompt_builder.py
  - packages/plugins/codex-collaboration/tests/test_retrieve_learnings.py
  - packages/plugins/codex-collaboration/tests/test_secret_taxonomy.py
  - .git-blame-ignore-revs
  - packages/plugins/cross-model/skills/dialogue/SKILL.md
  - packages/plugins/cross-model/agents/codex-dialogue.md
  - packages/plugins/cross-model/agents/context-gatherer-code.md
  - packages/plugins/cross-model/agents/context-gatherer-falsifier.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md
  - docs/tickets/2026-03-30-codex-collaboration-execution-domain-foundation.md
---

# Repo hygiene and T-04 dialogue reconnaissance

## Goal

Transition from the completed AC6 analytics work (sessions 1-10) to the next codex-collaboration packet: T-20260330-04 (dialogue parity and scouting retirement). This session had two phases: (1) clear accumulated repo debt from the 10-session build chain — push 50 local commits, format divergence, stale remote branches — and (2) read the cross-model dialogue architecture as semantic source material for T-04, establishing what needs to be built and what can be simplified.

**Trigger:** Session 10 handoff identified three next steps: verify test count, consider bulk ruff format, and proceed with T-04/T-05. This session executed the first two and began reconnaissance for the third.

**Stakes:** Medium. The repo hygiene work was low-risk maintenance. The T-04 reconnaissance is preparatory — no code written, but the architectural understanding gained here is load-bearing for the next session's design work. T-04 is the "adoption gate" for codex-collaboration: until the dialogue surface ships, codex-collaboration cannot replace cross-model for `/dialogue` workflows.

**Success criteria:** (1) origin/main up to date. (2) codex-collaboration passes `ruff format --check`. (3) Stale remote branches deleted. (4) `.git-blame-ignore-revs` in place. (5) Cross-model dialogue architecture understood and documented for T-04 planning.

**Connection to project arc:** Eleventh session in the codex-collaboration build chain. Sessions 1-10 built and hardened the dialogue runtime (journal, TurnStore, recovery, repair, analytics). This session transitions from runtime to user surface — the T-04 packet wraps the runtime in a dialogue skill, gatherer agents, convergence detection, and benchmark execution.

## Session Narrative

Resumed from the session 10 handoff (`2026-04-01_20-30_ac6-finalization-durability-review-and-merge.md`). Session 10 left a clean stopping point: AC6 complete, all work merged to main, no work in flight. The handoff identified three next steps.

**Phase 1: Verification and cleanup.** Started with the lowest-risk item: verifying the test count. Ran `uv run pytest packages/plugins/codex-collaboration/tests/ -q` — 460 passed in 2.33s, matching the handoff's prediction (459 base + 1 timestamp fallback regression test added late in session 10).

Checked git state: `main` was 50 commits ahead of `origin/main`, spanning all 10 sessions of the codex-collaboration build chain. The user verified with `git push --dry-run` that a fast-forward from `43fa3ba5` to `db13ea3a` was clean. Pushed all 50 commits.

**Phase 2: Formatting campaign.** Checked ruff formatting divergence: 24 files would be reformatted, 26 already compliant (down from the session 9 handoff's estimate of ~28 — session 9's AC6 formatting commit cleaned some up). The user raised three practical issues before proceeding:

1. Two remote feature branches (`origin/feature/codex-collaboration-r2-dialogue` and `origin/feature/codex-collaboration-safety-substrate`) overlap heavily with the same files. If still live, the format commit would create rebase churn.

2. No existing `.git-blame-ignore-revs` file, and the SHA can't be populated until the formatter commit exists and is stable. Requires two commits: format first, then blame-ignore with the SHA.

3. No pre-commit or CI enforcement for `ruff format --check`. Without a guardrail, the cleanup is one-time with no ratchet.

Investigated both remote branches. Neither was a direct ancestor of `main` (`git merge-base --is-ancestor` returned false for both), but their work had landed on main through different merge paths:
- `feature/codex-collaboration-r2-dialogue`: squash-merged as `f5fc5aab` ("R2 dialogue foundation with crash recovery and reply failure handling"), then 10 sessions of persistence hardening built on top. Remote branch is a stale pre-merge snapshot.
- `feature/codex-collaboration-safety-substrate`: merged to main at `664fc249`, then received additional commits that also landed via `43fa3ba5` ("T-03 safety substrate") and subsequent type-narrowing fixes. Remote branch is a stale post-merge snapshot.

The user confirmed both are attached to merged PRs (#89 and #90, both `closed` and `merged`). Deleted both remote branches. Then executed the formatting campaign:
- Created `chore/ruff-format-codex-collaboration` branch from main
- Applied `ruff format` (24 files, +490/-277)
- Verified 460 tests passing, all 50 files compliant
- Committed as `f69b0484` ("chore: ruff format codex-collaboration")
- Created `.git-blame-ignore-revs` referencing `f69b0484`
- Committed as `5fea6a6d` ("chore: add .git-blame-ignore-revs for format commit")
- Merged via `--ff-only` to preserve the formatter SHA (critical — squash/rebase would invalidate the SHA in `.git-blame-ignore-revs`)
- Deleted branch, pushed to origin

The user explicitly chose to skip enforcement (pre-commit hook or CI check) for now: "Without CI/pre-commit already in place, adding enforcement here would turn a scoped cleanup into process work."

**Phase 3: Ticket triage and T-04 reconnaissance.** Read both candidate tickets:
- T-20260330-04: Dialogue parity and scouting retirement (adoption gate — skill, agents, benchmark)
- T-20260330-05: Execution-domain foundation (infrastructure — worktree, delegation job state)

Both are blocked by T-03 (now complete) and can run in parallel. Recommended T-04 first: higher immediate user value (adoption gate), better leverage of the 10-session dialogue runtime foundation, and the benchmark execution is a strategic fork that should resolve early. The user agreed and confirmed with their own analysis: T-04 contains the benchmark execution and context-injection retirement decision, which is "a strategic fork in the road."

Read the cross-model dialogue architecture as semantic source material — four files comprising the full dialogue pipeline:
1. `SKILL.md` (523 lines) — the pipeline orchestrator: question shaping, gatherer launch, deterministic briefing assembly, health check, delegation, synthesis relay, analytics
2. `context-gatherer-code.md` (112 lines) — code explorer agent using Glob/Grep/Read, emitting CLAIM lines with citations and provenance
3. `context-gatherer-falsifier.md` (158 lines) — assumption tester, emitting COUNTER/CONFIRM/OPEN with assumption IDs and contradiction types
4. `codex-dialogue.md` (522 lines) — multi-turn conversation manager with 7-step per-turn loop, context injection server integration, convergence detection, scope breach handling, phase tracking

Also read the benchmark contract (`dialogue-supersession-benchmark.md`, 207 lines) — fixed 8-task corpus with pass rule: safety=0, false_claims ≤ baseline, supported_rate within 0.10, convergence within 1 run. The contract is already authored (T-03 AC7) and lives at the expected path.

Shared architectural findings with the user. Session ended with the user stating they will explore the cross-model architecture in greater depth in the next session.

## Decisions

### T-04 before T-05

**Choice:** Prioritize T-20260330-04 (dialogue parity and scouting retirement) over T-20260330-05 (execution-domain foundation).

**Driver:** T-04 is the adoption gate — until it ships, codex-collaboration cannot replace cross-model for `/dialogue` workflows. It also contains the benchmark execution and context-injection retirement decision, which the user characterized as "a strategic fork in the road: if the benchmark passes, you can keep Claude-side scouting as the default and move forward with confidence; if it fails, the contract says to create a focused follow-up rather than porting more machinery opportunistically."

**Alternatives considered:**
- **T-05 first** — would unblock T-06 (promotion flow) earlier. Rejected because T-05 is the "completion gate" (lower urgency than adoption gate), is pure greenfield infrastructure with no existing foundation, and its scope/priority may be influenced by the T-04 benchmark result.

**Trade-offs accepted:** T-06 (promotion flow) remains blocked until T-05 lands. Accepted because T-04 and T-05 can run in parallel once T-04's design is stable, and the benchmark result from T-04 is more informative for project direction.

**Confidence:** High (E1) — both tickets are well-specified with clear scope. The ordering follows the ticket dependency graph (T-04 blocks T-07, T-05 blocks T-06) and the project's stated adoption-before-completion priority.

**Reversibility:** High — no code written. Can switch to T-05 at any time.

**Change trigger:** If something external prioritized unblocking T-06 over shipping the dialogue surface.

### Bulk ruff format with two-commit approach and blame-ignore

**Choice:** Apply `ruff format` across all 24 divergent codex-collaboration files, committed as two separate commits: formatting first (`f69b0484`), then `.git-blame-ignore-revs` referencing that SHA (`5fea6a6d`). Merged via `--ff-only` to preserve the formatter commit hash.

**Driver:** The user identified the "mixed-diff tax" — every future feature branch touching these files would have formatting changes interleaved with logic changes. Session 9 had already formatted the AC6-touched files, establishing a partial ratchet. Completing the format pass eliminates the tax for all 50 files.

**Alternatives considered:**
- **Format incrementally per feature** — format only files touched by each feature branch. Rejected because it perpetuates the mixed-diff problem on untouched files and creates inconsistent formatting state.
- **Single commit with blame-ignore in same commit** — simpler but the `.git-blame-ignore-revs` file needs the formatter commit's SHA, which doesn't exist until the commit is made. Would require amending.

**Trade-offs accepted:** 24-file diff is review-heavy but pure formatting (zero behavior changes, verified by 460 tests). `git blame` on those files loses original annotations until developers configure `git config blame.ignoreRevsFile .git-blame-ignore-revs` (GitHub UI honors it automatically).

**Confidence:** High (E2) — 460 tests passing before and after, `ruff format --check` clean across all 50 files.

**Reversibility:** Low practical need to reverse — formatting is permanent improvement. But could `git revert` both commits if needed.

**Change trigger:** N/A — formatting is a one-way improvement.

### Skip ruff format enforcement for now

**Choice:** Do not add pre-commit hook or CI check for `ruff format --check`. Rely on convention (format touched files per session, as session 9 established).

**Driver:** The user stated: "Without CI/pre-commit already in place, adding enforcement here would turn a scoped cleanup into process work." The repo has no CI infrastructure to hook into.

**Alternatives considered:**
- **Add pre-commit hook** — would enforce the ratchet automatically. Rejected for scope creep — the formatting campaign is a standalone chore, not a process change.

**Trade-offs accepted:** Drift can reoccur if future sessions don't format touched files. Mitigated by the precedent set in sessions 9 and 11 (format as you go).

**Confidence:** Medium (E1) — convention-based enforcement is weaker than automated, but the repo's single-contributor model makes convention sufficient for now.

**Reversibility:** High — can add enforcement later without any code changes.

**Change trigger:** Multiple contributors, or drift detected in future sessions.

### Delete stale remote branches

**Choice:** Delete `origin/feature/codex-collaboration-r2-dialogue` and `origin/feature/codex-collaboration-safety-substrate`.

**Driver:** Both branches' work has landed on main through different merge paths (squash merge and direct merge respectively). The user verified both are attached to merged PRs (#89 and #90, both `closed` and `merged`). The remote refs are dead pointers with no further value.

**Alternatives considered:**
- **Keep for reference** — rejected because PR history is preserved on GitHub regardless of branch existence. The branches would create rebase confusion if anyone tried to use them.

**Trade-offs accepted:** None meaningful — merged PRs retain full history.

**Confidence:** High (E2) — verified via `git merge-base --is-ancestor` (not direct ancestors of main, but content confirmed on main via commit message search), PR status confirmed via user's GitHub check.

**Reversibility:** Medium — branches can be recreated from the PR merge commits if needed, but the exact remote branch tips are lost. This is acceptable because the tips contained only stale work superseded by main.

**Change trigger:** N/A — branches were dead.

## Changes

### Modified files (formatting only)

| File | What Changed |
|------|-------------|
| 24 files in `packages/plugins/codex-collaboration/` | Pure `ruff format` — 10 server files, 14 test files. +490/-277 net. No behavior changes. 460 tests passing before and after. |

### Created files

| File | Purpose |
|------|---------|
| `.git-blame-ignore-revs` | Contains formatter commit SHA `f69b0484`. GitHub UI honors automatically; local `git blame` requires `git config blame.ignoreRevsFile .git-blame-ignore-revs`. |

### Commit history (this session)

| SHA | Message |
|-----|---------|
| `f69b0484` | chore: ruff format codex-collaboration |
| `5fea6a6d` | chore: add .git-blame-ignore-revs for format commit |

### Remote branch deletions

| Branch | Reason |
|--------|--------|
| `origin/feature/codex-collaboration-r2-dialogue` | Squash-merged to main as `f5fc5aab`. Attached to merged PR #89. |
| `origin/feature/codex-collaboration-safety-substrate` | Merged to main at `664fc249`. Attached to merged PR #90. Post-merge commits also landed via `43fa3ba5` and subsequent fixes. |

## Codebase Knowledge

### Cross-Model Dialogue Architecture (Semantic Source for T-04)

The cross-model `/dialogue` system has four layers. This architecture is the semantic source for T-04 — codex-collaboration needs to replicate or simplify each layer.

#### Layer 1: Dialogue Skill (SKILL.md, 523 lines)

The pipeline orchestrator at `packages/plugins/cross-model/skills/dialogue/SKILL.md`. Owns:

| Step | Operation | Key Detail |
|------|-----------|------------|
| 0 | Question shaping (`--plan`) | Claude-local decomposition into planning_question, assumptions, key_terms. Has debug gate (skips for debugging questions) and tri-state `question_shaped`. |
| 1 | Resolve assumptions | From Step 0 output or extracted from raw question. Sequential IDs (A1, A2...). |
| 2 | Launch gatherers | Two agents in parallel with 120s timeout each. |
| §17 | Learning retrieval | Script-based keyword/tag scoring via `retrieve_learnings.py`. Injected into briefing. |
| 3 | Briefing assembly | Deterministic, non-LLM. 9 sub-steps (parse, retry, zero-output fallback, discard, cap, sanitize, dedup, provenance validation, group). Produces `<!-- dialogue-orchestrated-briefing -->`. |
| 4/4b | Health check + seed_confidence | Metrics (citations ≥ 8, unique files ≥ 5) feed into seed_confidence composition. 4b collects reasons from all stages. |
| 5 | Delegate to codex-dialogue | Passes assembled briefing, posture, budget, seed_confidence, reasoning_effort, scope_envelope. |
| 6 | Present synthesis | Relay narrative + Synthesis Checkpoint (RESOLVED/UNRESOLVED/EMERGED). |
| 7 | Emit analytics | dialogue_outcome event to JSONL via `emit_analytics.py`. 30+ pipeline fields. |

**Argument parsing:** `--posture` (5 values), `--turns` (1-15), `--profile` (named preset), `--plan` (boolean). Resolution: explicit flags > profile > defaults.

**MCP tool dependencies:** `codex`, `codex-reply` (Codex server), `process_turn`, `execute_scout` (context-injection server). All 4 required as precondition.

#### Layer 2: Context Gatherers (Two agents, Sonnet model)

**Gatherer A (code explorer)** at `packages/plugins/cross-model/agents/context-gatherer-code.md` (112 lines):
- Tools: Glob, Grep, Read only
- Emits: `CLAIM` lines with `@ path:line` citations and `[SRC:code]` provenance
- Target: 15-30 tagged lines, max 40
- Domain restriction: code, tests, config only — no docs
- Failure mode: emits 1-2 `OPEN` lines describing what was searched

**Gatherer B (falsifier)** at `packages/plugins/cross-model/agents/context-gatherer-falsifier.md` (158 lines):
- Tools: Glob, Grep, Read only
- Emits: `COUNTER` (with `AID:` + `TYPE:`), `CONFIRM` (with `AID:`), `OPEN`
- Max 3 COUNTERs per consultation
- Domain restriction: docs/decisions/plans/learnings, architectural files — no code
- No-assumptions fallback: emits `CLAIM [SRC:docs]` from rationale surfaces only
- TYPE whitelist: interface mismatch, control-flow mismatch, data-shape mismatch, ownership/boundary mismatch, docs-vs-code drift

**Key design:** complementary domains. Code explorer owns code, falsifier owns docs. Neither crosses the boundary. This prevents duplicate citations and ensures the briefing has both implementation facts and design rationale.

#### Layer 3: Codex-Dialogue Agent (Opus model, 522 lines)

At `packages/plugins/cross-model/agents/codex-dialogue.md`. Three phases:

**Phase 1 (Setup):** Parse prompt, detect `<!-- dialogue-orchestrated-briefing -->` sentinel (if present, use briefing verbatim — skip reassembly), choose posture, read contract extract for safety pipeline (§7), sanitize outbound.

**Phase 2 (Conversation Loop):** 7-step per-turn loop:
1. Extract semantic data (position, claims with status, delta, tags, unresolved)
2. Call `process_turn` (context-injection server) — sends extraction, receives action directive
3. Process response — data capture to `turn_history`, budget gate, error handling
4. Scout (optional) — select from `template_candidates`, execute via `execute_scout`
5. Act on action (`continue_dialogue`, `closing_probe`, `conclude`)
6. Compose follow-up — priority: scout evidence > unresolved > unknown-provenance > unprobed claims > weakest claim > posture-driven
7. Send via `codex-reply`

State: threadId, conversation_id, state_checkpoint, checkpoint_id, current_turn, evidence_count, turn_history, seed_confidence, scope_envelope, scope_breach_count, unknown_claim_paths.

**Phase 3 (Synthesis):** Defined in separate `dialogue-synthesis-format.md`. Produces confidence-annotated output with RESOLVED/UNRESOLVED/EMERGED checkpoint and pipeline data epilogue.

**manual_legacy fallback:** When context-injection server is unavailable, uses simplified 3-step loop (extract, evaluate continue/conclude manually, compose follow-up). No server-side ledger, no scouts, no entity resolution. Agent manages its own convergence detection.

**Multi-phase profiles:** When delegation envelope includes `phases` array, tracks phase progression with posture transitions at `target_turns` boundaries.

#### Layer 4: Context Injection Server (MCP)

Plugin-side Python server providing `process_turn` and `execute_scout`. Manages:
- Conversation ledger (claim counts, plateau detection, closing probe state)
- Convergence detection (server decides continue/conclude)
- Entity extraction (from focus and claims, used for scout candidate ranking)
- Scout execution (evidence gathering with budget tracking)
- State checkpoints (opaque, passed between turns)

### Benchmark Contract (207 lines)

At `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`. Already authored as T-03 AC7.

**Systems under test:**
- `baseline`: Cross-model `/dialogue` with plugin-side context-injection
- `candidate`: Codex-collaboration dialogue with Claude-side scouting (Glob, Grep, Read only)

**Fixed corpus:** 8 tasks (B1-B8), all drawn from codex-collaboration repo itself:

| ID | Type | Posture | Budget | Focus |
|----|------|---------|--------|-------|
| B1 | Architecture review | evaluative | 6 | MCP tool surface alignment with spec |
| B2 | Runtime reasoning | evaluative | 6 | Serialized dispatch and turn sequencing |
| B3 | Code review | adversarial | 6 | Redaction coverage gaps |
| B4 | Productization planning | comparative | 6 | Plugin artifact readiness |
| B5 | Policy audit | evaluative | 6 | Advisory runtime rotation model |
| B6 | Audit/schema analysis | evaluative | 6 | AuditEvent shape sufficiency |
| B7 | Forward-compatibility | comparative | 6 | dialogue.fork without breaking lineage |
| B8 | Supersession analysis | comparative | 8 | Claude-side scouting vs context-injection |

**Pass rule (ALL must hold):**
1. `safety_violations == 0`
2. Candidate `false_claim_count` ≤ baseline
3. Candidate `supported_claim_rate` within 0.10 of baseline
4. Candidate `converged_within_budget` ≥ baseline - 1

**Required artifacts:** `manifest.json`, `runs.json`, `adjudication.json`, `summary.md`.

**Decision consequences:** Pass → Claude-side scouting is default, context-injection stays retired. Fail → focused follow-up packet naming the measured deficiency, no opportunistic porting.

### Key Architectural Insight for T-04

The cross-model dialogue system's complexity is driven by its dependency on the context-injection MCP server (Layer 4). The 7-step per-turn loop in the codex-dialogue agent is largely orchestration glue for that server's `process_turn`/`execute_scout` API.

In codex-collaboration's candidate system, there is no context-injection server. Scouting is Claude-side (Glob/Grep/Read from gatherer agents). This means:

**Can be carried over almost verbatim:**
- Gatherer agents (already use only Glob/Grep/Read)
- Tagged-line grammar and briefing assembly pipeline (deterministic, non-LLM)
- Safety pipeline (credential scanning, sanitization)
- Posture selection and argument parsing

**Must be simplified or redesigned:**
- Conversation loop: no `process_turn` → agent manages its own ledger (similar to `manual_legacy` mode)
- Scouting: no `execute_scout` with tokens/entities → agent uses Glob/Grep/Read directly during the conversation
- Convergence detection: no server-side detection → agent needs its own mechanism (could be based on `manual_legacy`'s plateau detection)
- Entity resolution: eliminated entirely — no scout candidates, no entity-to-path matching

**Must be built new:**
- Analytics emission using codex-collaboration's own journal/outcome model (already built in sessions 8-10)
- Benchmark execution harness (corpus runner, adjudicator, artifact generator)

### Codex-Collaboration Spec Structure

At `docs/superpowers/specs/codex-collaboration/`:

| File | Purpose |
|------|---------|
| `spec.yaml` | Authority model and module manifest |
| `contracts.md` | Data models (MCP tools, state shapes) |
| `delivery.md` | Build sequence and delivery packets |
| `foundations.md` | Core architecture |
| `advisory-runtime-policy.md` | Runtime rotation and privilege model |
| `recovery-and-journal.md` | Journal, recovery, concurrency |
| `promotion-protocol.md` | Delegation promotion flow |
| `decisions.md` | Architecture decisions |
| `dialogue-supersession-benchmark.md` | Fixed benchmark contract |
| `official-plugin-rewrite-map.md` | Cross-model to codex-collaboration mapping |

### Ticket Dependency Graph (T-04/T-05 context)

```
T-20260330-03 (safety substrate) — COMPLETE
├── T-20260330-04 (dialogue parity) — NEXT
│   └── T-20260330-07 (unknown)
└── T-20260330-05 (execution domain)
    └── T-20260330-06 (promotion flow)
```

T-04 and T-05 can run in parallel once T-03's shared substrate is stable. T-04 blocks T-07; T-05 blocks T-06.

### codex-collaboration Test Landscape

| Test File | Count | Area |
|-----------|-------|------|
| `test_dialogue.py` | ~73 | Dialogue lifecycle, finalization, repair, timestamps |
| `test_journal.py` | ~25 | Journal operations, replay-safe helpers |
| `test_control_plane.py` | ~20 | Control plane, consult best-effort |
| `test_mcp_server.py` | ~12 | MCP tool surface |
| `test_dialogue_integration.py` | ~11 | Integration tests |
| `test_outcome_record.py` | 8 | Outcome record models (AC6) |
| `test_outcome_shape_consistency.py` | 1 | Shape consistency (AC6) |
| Other test files | ~310 | Bootstrap, codex compat, safety, context assembly, etc. |
| **Total** | **460** | All passing, lint clean |

## Context

### Mental Model

This session was a **transition session** — crossing the boundary from runtime hardening (sessions 1-10) to user surface work (T-04). The runtime is proven and stable (460 tests, finalization durability, replay safety). The next challenge is building the user-facing layer that wraps it.

The key architectural insight is that codex-collaboration's dialogue can be significantly simpler than cross-model's. Cross-model's complexity comes from the context-injection server: a separate MCP server that manages conversation ledgers, extracts entities, generates scout candidates, and tracks evidence budgets. In codex-collaboration, scouting is Claude-side — the gatherer agents already use only Glob/Grep/Read, and the conversation agent can manage its own ledger without a server intermediary.

This is the fundamental bet T-04's benchmark tests: is the simpler architecture (Claude-side scouting without plugin-side context-injection) sufficient for production-quality dialogue?

### Execution Methodology

The user drove all decisions in this session. I executed the repo hygiene tasks and read the semantic source files. The user raised the three practical issues with the formatting campaign (stale branches, blame-ignore, enforcement), verified the remote branch state independently, and provided the two-commit approach recommendation. The user also confirmed T-04 priority with their own analysis.

For T-04 reconnaissance, the user asked me to read and share findings; they stated they will "explore in greater depth in the next session."

### Project State

- **Branch:** `main` at `5fea6a6d` (52 commits: 50 from sessions 1-10 + 2 from this session's formatting)
- **Tests:** 460 passing (verified)
- **Lint:** Clean (`ruff format --check` passes all 50 files)
- **Remote:** `origin/main` up to date. Two stale remote branches deleted.
- **AC6 status:** Complete (sessions 8-10)
- **T-03 status:** Complete (sessions 1-10)
- **T-04 status:** Reconnaissance complete, no code written

### Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1 | 2026-03-31 | Design spec | `archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |
| 2 | 2026-03-31 | Implementation plan | `archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |
| 3 | 2026-03-31 | Review rounds 1-3 | `archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md` |
| 4 | 2026-04-01 | Review round 4 + merge | `archive/2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md` |
| 5 | 2026-04-01 | Execute Tasks 0-3 | `archive/2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md` |
| 6 | 2026-04-01 | Execute Task 4 | `archive/2026-04-01_12-25_persistence-hardening-task-4-journal-migration.md` |
| 7 | 2026-04-01 | Merge + Tasks 5-6 | `archive/2026-04-01_12-58_persistence-hardening-tasks-5-6-and-merge.md` |
| 8 | 2026-04-01 | AC6 plan | `archive/2026-04-01_13-38_ac6-analytics-emission-plan.md` |
| 9 | 2026-04-01 | AC6 execution | `archive/2026-04-01_18-15_ac6-analytics-emission-execution.md` |
| 10 | 2026-04-01 | AC6 durability review + merge | `archive/2026-04-01_20-30_ac6-finalization-durability-review-and-merge.md` |
| **11** | **2026-04-01** | **Repo hygiene + T-04 recon** | **This handoff** |

## Learnings

### --ff-only merge is required when .git-blame-ignore-revs references a commit SHA

**Mechanism:** `.git-blame-ignore-revs` contains raw commit SHAs. If the formatting branch is squash-merged or rebased, the SHA changes and the blame-ignore file points at a phantom commit — silently broken. Fast-forward is the only merge strategy that guarantees SHA preservation.

**Evidence:** This session used `git merge --ff-only chore/ruff-format-codex-collaboration` to land the two-commit sequence (formatter at `f69b0484`, blame-ignore at `5fea6a6d`). The blame-ignore file references `f69b0484` which is now directly on main's history.

**Implication:** Future bulk formatting commits should always use `--ff-only` when paired with blame-ignore entries. If the branch has diverged and can't fast-forward, rebase first (which preserves the two-commit structure) rather than squash-merging.

**Watch for:** `.git-blame-ignore-revs` entries that reference SHAs not on main — this indicates a prior non-ff merge that broke the ignore.

### Stale remote branches accumulate silently in session-based handoff workflows

**Mechanism:** Each session creates a feature branch, merges to local main, pushes main, but does not delete the remote feature branch. Over 10 sessions, these stale refs accumulate. They create confusion when exploring the repo state and can cause rebase churn if someone tries to update them.

**Evidence:** Two remote branches (`feature/codex-collaboration-r2-dialogue`, `feature/codex-collaboration-safety-substrate`) persisted across 10+ sessions despite their work being fully on main. Both were attached to merged PRs but the remote refs were never cleaned up.

**Implication:** Consider adding a branch cleanup step to the merge-branch or handoff workflow. At minimum, check for stale remote branches at session start when `origin/main` divergence is detected.

**Watch for:** Any `git branch -r` output with branches whose names match completed handoff chain work.

### Cross-model dialogue complexity is dominated by context-injection server integration

**Mechanism:** The codex-dialogue agent's 7-step per-turn loop exists primarily to orchestrate `process_turn` and `execute_scout` MCP calls. Steps 2 (call process_turn), 3 (process response), and 4 (scout) are entirely about the context-injection server. Steps 5-7 (act, compose, send) depend on the server's action directive and template candidates.

**Evidence:** Removing the context-injection dependency would collapse the 7-step loop to roughly 3 steps (extract, compose, send) — similar to the agent's own `manual_legacy` fallback mode at lines 204-218 of `codex-dialogue.md`.

**Implication:** codex-collaboration's dialogue agent can be significantly simpler than cross-model's. The benchmark is testing whether this simplification loses quality. If it doesn't (pass), the context-injection server's complexity was solving a problem that Claude-side scouting solves adequately.

**Watch for:** The benchmark's `supported_claim_rate` metric — this is where plugin-side scouting's richer entity resolution might outperform Claude-side. If the candidate fails, `supported_claim_rate` gap is the most likely failure mode (thin evidence vs rich evidence).

### Benchmark corpus self-referentiality is both strength and limitation

**Mechanism:** All 8 benchmark tasks (B1-B8) are drawn from the codex-collaboration repository itself. This means both systems are being tested on the same codebase familiarity surface, which ensures fairness. But it doesn't measure generalization to unfamiliar repositories.

**Evidence:** The benchmark contract explicitly acknowledges this at lines 73-80: "All 8 corpus tasks are drawn from the codex-collaboration repository itself... does not measure dialogue quality on unfamiliar repositories."

**Implication:** A passing benchmark validates the architecture for known-codebase dialogue. If cross-repository generalization matters later, a separate corpus expansion under a new contract revision is needed.

**Watch for:** Overinterpreting a benchmark pass as "Claude-side scouting is always sufficient." The contract only covers the codex-collaboration repo's complexity surface.

## Next Steps

### 1. Deep exploration of cross-model dialogue for T-04 design

**Dependencies:** None — reconnaissance from this session provides the starting point.

**What to read first:** The user stated they will "explore in greater depth in the next session." Start from the architectural summary in this handoff's Codebase Knowledge section. Key files to explore deeper:
- `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md` — full tagged-line grammar for briefing assembly
- `packages/plugins/cross-model/agents/references/dialogue-synthesis-format.md` — synthesis assembly process
- `packages/plugins/cross-model/agents/references/contract-agent-extract.md` — agent-relevant consultation contract sections
- `docs/superpowers/specs/codex-collaboration/contracts.md` — codex-collaboration data models (what dialogue tools already exist)
- `docs/superpowers/specs/codex-collaboration/delivery.md` — delivery packet structure for T-04

**Approach:** Map the semantic gap between cross-model's dialogue surface and what codex-collaboration needs. Identify which components can be ported verbatim, which need adaptation, and which are new. The user will lead this exploration.

**Acceptance criteria:** Design understanding sufficient to write a T-04 implementation plan.

### 2. T-04 implementation plan

**Dependencies:** Deep exploration (step 1).

**What to read first:** T-04 ticket (`docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`), benchmark contract, delivery spec.

**Approach:** Author a plan covering: dialogue skill, gatherer agents, orchestration agent, convergence detection, synthesis format, benchmark execution harness, analytics wiring. The plan should address which cross-model components are ported, adapted, or built new.

**Acceptance criteria:** Plan reviewed and approved. Clear task breakdown with dependencies.

**Potential obstacles:** Benchmark execution harness is novel — no existing cross-model equivalent. This needs design attention in the plan.

### 3. Consider bulk ruff format enforcement

**Dependencies:** None — standalone chore, lower priority.

**What to read first:** Check whether any pre-commit or CI infrastructure exists in the repo.

**Approach:** If CI exists, add `ruff format --check` step. If not, consider a pre-commit hook.

**Acceptance criteria:** Automated enforcement of `ruff format` on the codex-collaboration package.

## In Progress

Clean stopping point. All repo hygiene complete and pushed to origin. T-04 reconnaissance complete — cross-model architecture read and documented. No code written, no design decisions made for T-04 implementation.

## Open Questions

### Convergence detection without context-injection server

Cross-model's convergence detection is server-side (`process_turn` returns `action: conclude`). codex-collaboration won't have that server. The `manual_legacy` fallback uses simple plateau detection (2+ consecutive `static` delta turns). Is that sufficient for production, or does the dialogue agent need a more sophisticated mechanism?

**Relevant references:** `codex-dialogue.md:204-218` (manual_legacy), `codex-dialogue.md:307-337` (process_turn error handling), benchmark pass rule #4 (`converged_within_budget`).

### Benchmark execution tooling

The benchmark contract defines what to measure and how to score, but not the execution harness. Who runs the 8 tasks? How are transcripts captured? How is adjudication automated or structured? The T-04 plan needs to address this.

### Scope of codex-collaboration dialogue analytics

Sessions 8-10 built outcome record emission for dialogue turns. T-04's dialogue skill will need analytics emission similar to cross-model's Step 7 (30+ pipeline fields). How much of that pipeline state is relevant when there's no context-injection server (no scout metrics, no entity resolution, no process_turn state)?

## Risks

### Benchmark may fail on supported_claim_rate

Low-medium risk. The benchmark tests whether Claude-side scouting produces evidence quality comparable to plugin-side context-injection. The context-injection server has entity resolution and scout tokens that focus evidence gathering on specific code locations. Without those, the dialogue agent relies on its own Glob/Grep/Read skills. If the agent's evidence is thinner, `supported_claim_rate` drops below the 0.10 tolerance.

**Mitigation:** The benchmark contract has a clear failure path — don't port context-injection opportunistically, create a focused follow-up naming the measured deficiency.

### T-04 scope creep into T-05 territory

Low risk but worth watching. T-04 (dialogue surface) and T-05 (execution domain) are adjacent and both "large." The T-04 benchmark execution harness might naturally expand toward execution runtime concerns if not scoped carefully.

**Mitigation:** T-04 explicitly excludes "Delegation and promotion" and "Any change to the execution-domain runtime." Keep the benchmark harness as a skill-level tool, not a runtime component.

## References

| What | Where |
|------|-------|
| T-04 ticket | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` |
| T-05 ticket | `docs/tickets/2026-03-30-codex-collaboration-execution-domain-foundation.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Cross-model dialogue skill | `packages/plugins/cross-model/skills/dialogue/SKILL.md` |
| Code explorer agent | `packages/plugins/cross-model/agents/context-gatherer-code.md` |
| Falsifier agent | `packages/plugins/cross-model/agents/context-gatherer-falsifier.md` |
| Codex-dialogue agent | `packages/plugins/cross-model/agents/codex-dialogue.md` |
| Tag grammar | `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md` |
| Synthesis format | `packages/plugins/cross-model/agents/references/dialogue-synthesis-format.md` |
| Contract agent extract | `packages/plugins/cross-model/agents/references/contract-agent-extract.md` |
| Codex-collaboration spec | `docs/superpowers/specs/codex-collaboration/` |
| Delivery spec | `docs/superpowers/specs/codex-collaboration/delivery.md` |
| Finalization helper | `packages/plugins/codex-collaboration/server/dialogue.py:206-254` |
| Replay-safe audit helper | `packages/plugins/codex-collaboration/server/journal.py:169-181` |
| .git-blame-ignore-revs | `.git-blame-ignore-revs` (contains `f69b0484`) |
| Prior handoff (session 10) | `docs/handoffs/archive/2026-04-01_20-30_ac6-finalization-durability-review-and-merge.md` |

## Gotchas

### .git-blame-ignore-revs only works with local config

GitHub's blame UI honors `.git-blame-ignore-revs` automatically. But local `git blame` requires a one-time per-repo config: `git config blame.ignoreRevsFile .git-blame-ignore-revs`. Without this, local blame still shows the formatting commit as the author of every reformatted line.

### Cross-model context-injection tools are named differently than codex-collaboration tools

Cross-model MCP tools: `mcp__plugin_cross-model_codex__codex`, `mcp__plugin_cross-model_context-injection__process_turn`. Codex-collaboration MCP tools: `mcp__plugin_codex-collaboration_codex-collaboration__codex_*`. The naming convention differs — skills and agents ported from cross-model need their `allowed-tools` and `tools` frontmatter updated. Wrong names in `tools` (hard allowlist) means the tool is unavailable; wrong names in `allowed-tools` (auto-approval) means permission prompts instead of auto-approval.

### Benchmark candidate must not use plugin-side scouting

The benchmark contract explicitly states: "The candidate system must not use plugin-side scouting during the benchmark. If plugin-side scouting is enabled, the run is invalid." This means the codex-collaboration dialogue agent cannot call `process_turn`/`execute_scout` MCP tools during benchmark runs, even if they were available. Scouting must be Claude-side only.

### Manual_legacy mode in codex-dialogue is the closest existing reference for codex-collaboration's design

The `manual_legacy` fallback (codex-dialogue.md:204-218) is what the codex-dialogue agent uses when the context-injection server is unavailable. It manages its own ledger, convergence detection (2+ consecutive `static` delta turns), and turn budget. This is architecturally close to what codex-collaboration's dialogue agent will need — but it's a fallback mode, not a designed-for-purpose primary mode. The T-04 design should treat it as inspiration, not a template.

## User Preferences

**Practical issue identification:** The user raised three practical concerns about the formatting campaign before execution (stale branches, blame-ignore SHA stability, enforcement gap). Each was specific, actionable, and backed by verification. This is the same review rigor seen in sessions 1-10 — the user probes for gaps before approving execution.

**Two-commit approach for blame-ignore:** The user recommended the structural separation (format commit first, blame-ignore second) and explicitly noted the SHA stability requirement: "If you later squash or rewrite the branch, that SHA changes and the ignore entry becomes wrong."

**Scope discipline on enforcement:** The user explicitly chose to skip enforcement: "Skipping enforcement for now is reasonable. Without CI/pre-commit already in place, adding enforcement here would turn a scoped cleanup into process work." Consistent with previous sessions' pattern of scoping each piece of work tightly.

**User-led exploration for T-04:** The user stated they will "explore in greater depth" in the next session, and asked me to "start by reading the cross-model dialogue skill and gatherer agents, then share what you find." The user will lead the T-04 design process as they did with sessions 1-10.

**Thoroughness preference confirmed:** The user requested `ultrathink` on multiple turns, consistent with session 10's pattern. For design-adjacent work, the user values exhaustive analysis over quick answers.

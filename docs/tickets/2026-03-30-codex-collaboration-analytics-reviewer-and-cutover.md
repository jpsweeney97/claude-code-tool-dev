# T-20260330-07: Codex-collaboration analytics, review, and cross-model cutover

```yaml
id: T-20260330-07
date: 2026-03-30
status: closed
priority: medium
tags: [codex-collaboration, analytics, review, cutover, supersession]
blocked_by: [T-20260330-04, T-20260330-06]
blocks: []
effort: medium
```

## Context

After dialogue parity and delegation completion, codex-collaboration still
needs the observability and migration layer that lets the repo actually remove
cross-model:

- analytics skill
- review skill
- migration and verification docs
- removal of cross-model and context-injection from the repo

This is the final cutover packet.

## Design Reconciliation (2026-04-21)

T-04 and T-06 are now closed. This reconciliation maps the original T-07 scope
against actual predecessor evidence and records design decisions made during
the T-07 scope reconciliation session.

### Predecessor Status

| Ticket | Status | Final test count | Key evidence |
|--------|--------|------------------|--------------|
| T-02 | Closed (2026-04-13) | 566 | Plugin shell, consult/status skills |
| T-03 | Closed (2026-04-13) | 566 | Safety substrate, profiles, learnings, benchmark contract |
| T-04 | Closed (2026-04-17) | 566 | Dialogue parity, demonstrated-not-scored benchmark, retirement decision |
| T-05 | Closed (2026-04-19, retroactive hygiene) | 698 | Execution-domain foundation, 51 commits (`6ed5f731..271f23aa`) |
| T-06 | Closed (2026-04-21) | 845 | Promotion flow, delegate UX, PRs #109–#114 |

### Parity Matrix

| Cross-model workflow | Codex-collaboration replacement | Status |
|---|---|---|
| `/codex` (consult) | `consult-codex` skill | Delivered (T-02) |
| `/codex` status | `codex-status` skill | Delivered (T-02) |
| `/dialogue` (orchestrated) | `dialogue-codex`/`dialogue` skills + `dialogue-orchestrator` + gatherers | Delivered (T-04) |
| `/delegate` (autonomous exec) | `delegate` skill + `start`/`poll`/`decide`/`promote` tools | Delivered (T-06) |
| `/consultation-stats` | `codex-analytics` skill | **T-07 (net-new)** |
| `codex-reviewer` agent | `codex-review` skill | **T-07 (net-new)** |
| `codex_guard.py` (PreToolUse) | `codex_guard.py` in codex-collaboration | Delivered (T-03) |
| `context-injection` | Claude-side scouting (retired by T-04 decision) | **T-07 removal** |
| `nudge_codex.py` | No port planned (leaf, opt-in) | Dropped |
| `event_schema.py` / `event_log.py` | Operation journal + lineage store + audit/outcome streams | Delivered (T-03/R2) |

### Analytics Design

Analytics are computed from codex-collaboration's existing observability
projections, not from cross-model's flat event log and not from raw recovery
stores.

**Primary sources:**

- `analytics/outcomes.jsonl` for outcome-level metrics (consult, dialogue,
  delegation terminal).
- `audit/events.jsonl` for trust-boundary, lifecycle, and security metrics.

**Schema changes required:**

- Add `workflow: ConsultWorkflow` discriminator to `OutcomeRecord` so
  `codex-review` invocations are visible as review-sourced consult outcomes.
  `ConsultWorkflow = Literal["consult", "review"]` for T-07. Existing rows
  without `workflow` default to `"consult"` during reads.
- Add `DelegationOutcomeRecord` as a separate typed analytics record for
  terminal execution outcomes only. Fields: `outcome_id`, `timestamp`,
  `outcome_type` (`"delegation_terminal"`), `job_id`, `collaboration_id`,
  `runtime_id`, `repo_root`, `terminal_status` (`completed`/`failed`/`unknown`),
  `base_commit`. No `promotion_state` (disposition is audit-derived via
  `promote`/`discard` events). No `artifact_hash` (not reliably available at
  terminal-observation time).
- Both shapes written to `analytics/outcomes.jsonl`. Reader dispatches on
  `outcome_type`; unknown types skipped gracefully with metadata counting.

**Emission timing:** `DelegationOutcomeRecord` emitted at the first
authoritative observation of terminal job status, with startup recovery as an
append-once catch-up path. Keyed on `(outcome_type, job_id)` for idempotency,
following the same pattern as `append_dialogue_outcome_once`.

**`workflow` plumbing:** Add optional `workflow` field to `codex.consult` tool
input. MCP dispatch validates and passes through to control plane. Control
plane records in `OutcomeRecord` without branching on it. Analytics interprets.

**Documented limitation:** Delegation terminal outcomes for jobs that reach
terminal status in a session that crashes before poll, where the next session
has a different session ID, may be missing from analytics. The job store
retains the data; analytics coverage is best-effort for abandoned jobs outside
the recovered session boundary.

**Analytics views (T-07 scope):**

- Usage: consult, dialogue turns, delegate starts, reviews.
- Reliability/security: credential blocks/shadows, escalation count,
  promotion rejections.
- Context/runtime: context size, policy fingerprint distribution.
- Delegation: started/completed/failed/unknown, promoted/discarded,
  escalation count.
- Review: count, workflow source (`"review"` vs `"consult"`).

### Review Design

The `codex-reviewer` agent in cross-model is replaced by a `codex-review`
skill in codex-collaboration. Review is a workflow over the advisory runtime,
not a separate runtime primitive.

**Shape:** `packages/plugins/codex-collaboration/skills/codex-review/SKILL.md`.
The skill gathers review scope from git, performs local review preparation,
calls `codex.consult` with `workflow="review"`, and synthesizes findings with
Claude-side review judgment. The server records review invocations as consult
outcomes with the `workflow` discriminator.

**Delegate integration:** `codex-review` can review delegation output
(materialized artifacts from `codex.delegate.poll`), but this remains advisory
in T-07. It is not a hard promotion precondition. The promotion contract
continues to require Claude-reviewed artifact hash, not a separate reviewer
workflow approval.

**Architecture decision:** See `decisions.md` §Analytics and Review Cutover
Model.

### Context-Injection Adjudication

Context-injection is removed as part of the cross-model cutover. The removal
gate is satisfied by `T-20260330-04`'s explicit retirement decision
(demonstrated-not-scored adjudication, not a formal aggregate benchmark pass).

Three caveats travel with this decision and do not block removal:

1. `T-20260416-01` (reply-path extraction mismatch) remains open.
2. Three mechanism losses acknowledged: L1 scout integrity, L2 plateau/budget
   control, L3 per-scout redaction of raw host-tool output.
3. Capture sequence spans multiple documentation-only benchmark-history commits
   (audit fact, not a blocker).

Git history preserves all context-injection code if a future rollback is
warranted.

### Slice Boundaries

| Slice | Work | Dependencies |
|---|---|---|
| 7a | Analytics skill + `DelegationOutcomeRecord` + `ConsultWorkflow` type + `workflow` field on `codex.consult` input and `OutcomeRecord` + control-plane threading | None |
| 7b | `codex-review` skill consuming `workflow="review"` plumbing from 7a | 7a (shared `workflow` contract) |
| 7c | Migration docs + parity matrix document | 7a + 7b |
| 7d | Context-injection removal | 7c |
| 7e | Cross-model removal + verification + live delegate smoke | 7c + 7d |

7a owns the shared `workflow` contract that both analytics and review depend
on. 7b depends on 7a because it consumes the `workflow` plumbing through
`codex.consult`. 7c through 7e are sequential.

### 7a Closeout (2026-04-22)

Slice 7a landed in PR #116 and merged to `main` at `61eaa590`.

Delivered scope:

- `codex-analytics` skill and standalone analytics script over
  `analytics/outcomes.jsonl` and `audit/events.jsonl`.
- `ConsultWorkflow` and `workflow` plumbing through `codex.consult`,
  `ConsultRequest`, `ControlPlane.codex_consult`, and `OutcomeRecord`.
- `DelegationOutcomeRecord` for terminal delegation outcomes, including
  append-once journal helpers, terminal emission paths, same-session recovery
  catch-up, and malformed-line-tolerant analytics reads.
- Section-aware analytics tests for usage, reliability/security,
  context/runtime, delegation lifecycle, and review views.

Final slice verification before merge: `881` codex-collaboration tests passed;
`ruff check` passed; PR-scoped Python formatting passed; `git diff --check`
passed. GitHub reported no branch checks.

Known 7a limitation preserved intentionally: credential blocks/shadows and
promotion rejections are surfaced as `unavailable (not emitted to audit stream)`
because their audit emission points are deferred follow-up work. This does not
block 7a closure, but it must not be treated as implemented metric coverage.

Next slice: 7b, the `codex-review` skill consuming `workflow="review"` from the
shared 7a contract.

### Live `/delegate` Smoke Placement

T-06 deferred the live delegate smoke (requires Codex App Server). Placed as
a pre-removal verification gate in 7e: before cross-model removal, run the
full delegation lifecycle through the skill. If App Server is not available at
7e time, document the gap explicitly as in T-06.

## Scope

**In scope:**

- Add a codex-collaboration analytics skill computing over
  `analytics/outcomes.jsonl` and `audit/events.jsonl`
- Add `DelegationOutcomeRecord` and `ConsultWorkflow` discriminator to the
  analytics schema
- Add a `codex-review` skill that reviews diffs through `codex.consult` with
  `workflow="review"`
- Add optional `workflow` field to `codex.consult` tool input, threaded to
  `OutcomeRecord`
- Write migration documentation from cross-model to codex-collaboration
- Write parity verification matrix covering all cross-model workflows
- Remove cross-model packaging and code after parity matrix is complete
- Remove context-injection per T-04 retirement decision

**Explicitly out of scope:**

- New advisory or execution capabilities beyond the codex-collaboration spec
- Reintroducing the `codex exec` shim or cross-model event schema
- Making `codex-review` a hard promotion precondition
- Rich dialogue-quality analytics beyond what the current `OutcomeRecord`
  schema supports

## Acceptance Criteria

- [x] An analytics skill exists and can compute usage, reliability/security,
      context/runtime, delegation, and review views from
      `analytics/outcomes.jsonl` and `audit/events.jsonl`

      **Deferred metrics (7a):** Credential blocks/shadows and promotion
      rejections require new audit emission points in the credential
      interception path and promotion precondition checks, respectively.
      These are not satisfied by the analytics skill — the recipe surfaces
      them as `unavailable (not emitted to audit stream)`. Tracked as a
      follow-up enhancement; does not block 7a closure.

- [x] A `codex-review` skill exists in the codex-collaboration package, can
      review a real diff through `codex.consult` with `workflow="review"`,
      synthesizes Codex findings with Claude-side review judgment, and records
      review usage distinctly in analytics

      **Closed (7b):** PR #117, merged at `f681094a`. Skill at
      `skills/codex-review/SKILL.md` (270 lines, 9-step procedure). Smoke
      passed: `codex.consult` dispatched with `workflow="review"`,
      `profile="code-review"`; `outcomes.jsonl` row confirmed
      `"workflow": "review"` + `"outcome_type": "consult"`. Review feedback
      addressed in follow-up commit `90c6ff9a`.
- [x] Migration docs show how to replace each cross-model workflow with the new
      plugin surface
- [x] A parity matrix exists and covers consult, dialogue, delegate, analytics,
      and review workflows

      **Closed (7c):** PR #120, merged at `c59dbf11`. Migration and parity
      artifact at `docs/plans/2026-04-22-t07-cross-model-migration-and-parity-7c.md`
      (325 lines). Covers: 5-workflow parity matrix with functional-replacement
      qualifiers, complete 17/17 script removal inventory, per-workflow
      command-level migration guide, infrastructure comparison. 3 scrutiny
      rounds before commit. This document is migration evidence — removal
      authorization stays in 7d/7e.
- [x] Cross-model is removed from the repo once the parity matrix is complete
      and the live `/delegate` smoke has passed (or an explicit App Server
      deferral is recorded with the same transparency as T-06's deferral)

      **Closed (7e):** PR #123. `packages/plugins/cross-model/` deleted
      (79 files, 21,113 lines). Live `/delegate` smoke attempted: App Server
      available, delegation pipeline functional through start/escalate/decide/
      complete/poll/inspect, but sandbox execution blocked by two
      codex-collaboration defects (`includePlatformDefaults: False` in
      `build_workspace_write_sandbox_policy`, cancel-then-prompt approval
      loop). Recorded as execution-domain deferral, not App Server
      unavailability. Job `23347703-673a-419f-b1f5-01ca16cfe1f6` discarded
      (empty diff). See `docs/plans/2026-04-23-t07-cross-model-removal-7e.md`
      §Delegate Smoke Deferral for full evidence.
- [x] Context-injection is removed as part of the cross-model cutover.
      `T-20260330-04` explicitly resolved the retirement decision in favor of
      keeping context-injection retired by default. This is a
      demonstrated-not-scored adjudication, not a formal aggregate benchmark
      pass. Caveats: `T-20260416-01` open, mechanism losses L1/L2/L3
      acknowledged, capture sequence spans multiple doc commits

      **Closed (7d):** PR #122, merged at `1f458bcf`. Context-injection
      package deleted (54 files, ~19,487 lines). Dialogue skill and agent
      retired with stubs. `/codex` delegation branch patched. All 825
      cross-model tests passing post-removal.

## Verification

- Run the analytics skill against codex-collaboration-generated artifacts
- Run `codex-review` on a real diff and, separately, on a materialized
  delegate artifact snapshot if delegate-review integration is included
- Execute the parity checklist before removal
- Confirm that no supported cross-model workflow remains without a
  codex-collaboration replacement at removal time
- Run the live `/delegate` smoke before cross-model removal (or document
  explicit deferral if App Server is unavailable)

## Dependencies

This ticket depends on both the dialogue adoption packet (`T-20260330-04`) and
the delegation completion packet (`T-20260330-06`). Both are now closed.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Cross-model analytics skill | `packages/plugins/cross-model/skills/consultation-stats/SKILL.md` | Semantic source only |
| Cross-model reviewer agent | `packages/plugins/cross-model/agents/codex-reviewer.md` | Semantic source only |
| Cross-model README | `packages/plugins/cross-model/README.md` | Migration inventory |
| Analytics/review cutover decision | `docs/superpowers/specs/codex-collaboration/decisions.md` | Architecture decision |
| T-04 retirement decision | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | Context-injection evidence |
| T-06 closed ticket | `docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md` | Delegate evidence |
| Capability analysis | `docs/reviews/2026-03-17-cross-model-capability-analysis.md` | Migration inventory |

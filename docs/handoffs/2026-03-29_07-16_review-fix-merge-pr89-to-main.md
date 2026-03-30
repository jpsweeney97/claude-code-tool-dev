---
date: 2026-03-29
time: "07:16"
created_at: "2026-03-29T07:16:40Z"
session_id: fd4908ab-6ee4-4d38-b8e4-64a541dd2d5b
resumed_from: /Users/jp/.claude/handoffs/claude-code-tool-dev/.archive/2026-03-29_02-45_plan-executed-pr89-pushed-ready-for-merge.md
project: claude-code-tool-dev
branch: main
commit: 225fe8fa
title: "Review fix, squash-merge PR #89 to main, post-R2 next-steps"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py
  - docs/learnings/learnings.md
---

# Handoff: Review fix, squash-merge PR #89 to main, post-R2 next-steps

## Goal

Fix a P1 blocking review finding in PR #89's startup recovery, then squash-merge the entire R2 dialogue foundation to main.

**Trigger:** The prior session executed a 7-task TDD plan and pushed PR #89 with 28 commits, 209 tests. The handoff declared "ready for merge." But between sessions, the user ran an implementation review that found two issues: (1) `turn_dispatch` reconciliation in phase 1 unconditionally suppressed phase-2 reattach, violating the Option C contract, and (2) the existing `test_journal_reconciled_before_reattach` still encoded pre-Task-5 semantics, masking the regression.

**Stakes:** R2 is the second runtime milestone for codex-collaboration — durable dialogues with crash recovery. PR #89 had 28 commits ahead of main, 209 tests. The recovery bug would leave handles in stale state after a crash with an unresolved `turn_dispatch` journal entry: unconfirmed handles would stay `unknown` without reattach, confirmed handles would keep stale runtime/thread identity without resume.

**Success criteria:** Fix the regression, pass 210+ tests, squash-merge to main, clean repo state.

**Connection to project arc:** Spec compiled (`bf8e69e3`) -> T1 (`f53cd6c8`) -> R1 (`3490718a`) -> Post-R1 amendments (`2ae76ed1`) -> R2 plan (`5c000672`) -> R2 implementation (`7b0e3de8`) -> R2 fix plan+implementation (`4eeadd69`..`b7086954`) -> **review fix + squash-merge (this session)** -> post-R2 hardening.

## Session Narrative

### Loaded handoff and received review findings

Loaded the prior handoff (`2026-03-29_02-45_plan-executed-pr89-pushed-ready-for-merge.md`) which reported all 7 tasks executed, 209 tests passing, PR #89 pushed. The user immediately presented two review findings that blocked merge:

**P1 (confidence 0.98):** `recover_pending_operations()` unconditionally adds every `turn_dispatch` collaboration ID to `recovered`, but `_recover_turn_dispatch()` never calls `resume_thread()` or `update_runtime()`. Phase 2 then skips those handles, leaving them with stale runtime state.

**P2 (confidence 0.95):** `test_journal_reconciled_before_reattach` still asserts `h1.status == "unknown"` after `recover_startup()`, even though Option C says an `unknown` handle with zero completed turns is eligible for reattach. This stale assertion masks the P1 bug.

The user also provided a full requirements ledger (R1-R9), where R5 was `violated` — the only failing requirement.

### Analyzed the asymmetry between recovery methods

Read four code sections to understand the exact mechanics:

1. `recover_startup()` at `dialogue.py:341-389` — phase 1 reconciles journal, phase 2 enumerates active + unknown handles, skips those in `recovered_cids`
2. `recover_pending_operations()` at `dialogue.py:391-409` — the unconditional append at line 409
3. `_recover_thread_creation()` at `dialogue.py:412-476` — **does full reattach**: `read_thread` + `resume_thread` + `update_runtime` (lines 440-463)
4. `_recover_turn_dispatch()` at `dialogue.py:478-538` — **only reconciles**: `read_thread` for confirmation, metadata repair or quarantine, journal resolution. No resume.

This revealed the root cause: `_recover_thread_creation dispatched` performs a full reattach (so adding to `recovered` correctly prevents double-resume in phase 2), but `_recover_turn_dispatch` only does journal reconciliation + metadata repair — adding to `recovered` was wrong because phase 2 is still needed for the actual reattach.

The Task 5 implementer's original reasoning ("prevent phase 2 from immediately reattaching a quarantined handle") was correct under pre-Task-5 semantics where phase 2 only listed `active` handles. Under Option C, which extends phase 2 to also enumerate `unknown` handles, that reattach attempt is exactly what should happen.

### Proposed fix and got user alignment

Presented the fix approach: remove the unconditional append at `dialogue.py:409`, update the stale test, add a regression test. The user confirmed and provided precise scope guidance:

- User: "The minimal correct fix is to stop treating `turn_dispatch` reconciliation as a phase-1 reattach."
- User: "Leave `test_does_not_double_resume_handles_from_phase_1` semantically unchanged. Its setup writes `thread_creation` entries, so it is still testing the only phase-1 path that actually resumes."
- User: "That is the right boundary: one code fix, one expectation update, one regression test."

### TDD execution: RED → GREEN → REFACTOR

**RED (tests first):**

1. Updated `test_journal_reconciled_before_reattach` — changed h1 assertion from `status == "unknown"` to `status == "active"` with `codex_thread_id == "thr-start-resumed"`. Updated docstring to describe Option C flow.

2. Added `test_confirmed_turn_dispatch_does_not_suppress_phase_2_reattach` — new test with 1 completed turn visible. Asserts both metadata repair (phase 1 confirmed turn) AND resumed thread identity (phase 2 reattached).

Initial regression test had a setup error: asserted `metadata.context_size == 4096` but `TurnStore.get()` returns `int | None` (just the context_size value), not an object. Fixed to `context_size == 4096`.

Verified RED:
- Test 1 failed: `assert 'unknown' == 'active'` — h1 stays unknown because phase 2 skips it (in `recovered_cids`)
- Test 2 failed: `assert 'thr-start' == 'thr-start-resumed'` — metadata was repaired (context_size passed) but thread never resumed

Both failures trace to the unconditional append at `dialogue.py:409`.

**GREEN (minimal fix):**

Deleted one line: `recovered.append(entry.collaboration_id)` from the `turn_dispatch` path. All 210 tests passed.

**REFACTOR:**

1. Tightened `recover_pending_operations()` docstring: "Returns collaboration_ids of handles that were fully reattached (resume_thread + update_runtime) by phase 1. Handles only reconciled (journal resolved, metadata repaired, or quarantined) are NOT included."

2. Tightened `test_does_not_double_resume_handles_from_phase_1` docstring: "thread_creation recovered by phase 1 (full reattach with resume_thread) is skipped during phase 2."

### User ran follow-up implementation review

The user ran a second implementation review against the uncommitted fix. Requirements ledger: R1-R5 all satisfied. Zero findings. Verdict: "Commit these changes + the plan document, then merge PR #89 to main."

### Committed, pushed, and squash-merged

Two commits on the branch:
1. `b1b7a0a3` — docs: plan and adversarial review artifacts from prior sessions
2. `d2d0df56` — fix: stop turn_dispatch reconciliation from suppressing phase-2 reattach

Pushed to PR #89 (now 30 commits). Then discussed merge strategy.

User's guidance on merge: "I would not regular-merge this branch as-is. Best option: rebase into logical commits, then merge linearly. If your actual choice is only squash vs regular merge, choose squash." Reasoning: "main should optimize for readability, revertability, and bisectability, not preserve every task checkpoint."

User also required: (1) tag the branch tip before squash so task-by-task history stays reachable, (2) write a real squash commit message naming three substantive areas.

Tagged `r2-dialogue-branch-tip` at `d2d0df56`, pushed tag. Drafted squash commit message covering: dialogue foundation (models, stores, controller, MCP server), reply() failure handling, startup recovery with Option C reattach. User approved with one wording tweak: "MCP server scaffolding" → "MCP server surface."

Squash-merged via `gh pr merge 89 --squash`. Landed as `f5fc5aab` on main.

### Reconciled local main

Local main had 9 commits ahead of origin (the post-R1 spec amendments from ec6b3d61..2ae76ed1, which were also the first 9 commits of the feature branch). The squash merge subsumed them all.

User caught a safety issue: "I would not use `git reset --hard origin/main` on main right now, because your worktree is dirty." Suggested the `branch -f` technique: switch away, move the ref, switch back. This avoids `reset --hard` which can discard uncommitted work.

Applied: `git switch feature/codex-collaboration-r2-dialogue`, `git branch -f main origin/main`, `git switch main`. Local main now at `f5fc5aab`, up to date with origin.

Ran full test suite on main: 210 passed.

### Post-R2 next-steps discussion

User presented a structured 4-task next-steps framework:
- T1: Set the post-R2 hardening bar (live-runtime validation needed?)
- T2: Decide on residual recovery debt (audit parity, recovery noise)
- T3: Decide on context-assembly trust gaps (redaction, UTF-8)
- T4: Freeze the next work package based on T1-T3

I analyzed T1's resolution path: the controller logic is stable (210 tests, deterministic journal-based recovery). The real uncertainty is Codex's wire behavior for `thread/resume` — that's integration testing, not hardening. A lightweight smoke test against a live runtime would close the gap, but blocking on it isn't necessary.

If T1 resolves that way, I recommended T3 (context-assembly trust gaps) over T2 (recovery polish) because the context-assembly gaps affect the existing production consult path, not just the new dialogue path.

## Decisions

### Remove unconditional append vs. make _recover_turn_dispatch do full reattach

**Choice:** Remove the unconditional `recovered.append(entry.collaboration_id)` from the `turn_dispatch` path in `recover_pending_operations()`. One line deleted.

**Driver:** The user's implementation review identified the exact root cause with two reproduction scenarios (unconfirmed and confirmed turn_dispatch). User stated: "The minimal correct fix is to stop treating `turn_dispatch` reconciliation as a phase-1 reattach."

**Rejected:**
- **Make `_recover_turn_dispatch()` perform full reattach** — would widen scope beyond the fix. The user explicitly noted: "I do not see a better fix direction unless you want to widen scope and make `_recover_turn_dispatch` perform full reattach itself, which this patch does not need." The method's purpose is journal reconciliation, not runtime management.

**Trade-offs accepted:** Phase 2 now calls `read_thread` on handles that phase 1 already called `read_thread` on (for confirmation). This is a redundant API call but is idempotent and correct — the first call is for journal reconciliation, the second for reattach.

**Confidence:** High (E2) — both the unconfirmed and confirmed turn_dispatch paths verified by dedicated tests (210 total, 0 regressions). The asymmetry between `_recover_thread_creation` (full reattach) and `_recover_turn_dispatch` (reconciliation only) is now explicit in code and docstrings.

**Reversibility:** High — one line, pure behavioral change, fully test-covered.

**Change trigger:** If `_recover_turn_dispatch` is later extended to perform full reattach (resume + update_runtime), then it should be added back to `recovered`. But that's a scope expansion, not a fix.

### Squash-merge over regular merge

**Choice:** Squash-merge PR #89 (30 commits → 1 commit on main).

**Driver:** User stated: "main should optimize for readability, revertability, and bisectability, not preserve every task checkpoint. A 30-commit merge carries too much planning/fix churn into permanent history."

**Rejected:**
- **Regular merge** — preserves per-task commit history on main. User rejected: "I would not regular-merge this branch as-is."
- **Rebase into logical commits** — user's preferred option but acknowledged it wasn't offered as a choice. User: "If your actual choice is only squash vs regular merge, choose squash."

**Trade-offs accepted:** Per-task commit history (archaeological value) is no longer on main. Mitigated by: (1) tag `r2-dialogue-branch-tip` at `d2d0df56` preserves the full branch, (2) PR #89 preserves the commit list, (3) plan and review docs committed to main.

**Confidence:** High (E1) — user's explicit preference with clear reasoning.

**Reversibility:** N/A — merge is done.

**Change trigger:** N/A.

### branch -f for local main reconciliation

**Choice:** Used `git branch -f main origin/main` from another branch instead of `git reset --hard origin/main`.

**Driver:** User caught the safety risk: "I would not use `git reset --hard origin/main` on main right now, because your worktree is dirty." The `branch -f` technique moves the ref without touching the worktree.

**Rejected:**
- **`git reset --hard origin/main`** — would work if worktree is clean but silently discards uncommitted changes if dirty. User flagged the risk even though worktree was clean: "Safer approach."
- **`git pull --rebase`** — won't work when histories have diverged (the 9 local commits are subsumed by the squash merge, not ancestors of it).

**Trade-offs accepted:** Requires temporarily switching branches (one extra checkout). Negligible cost for the safety guarantee.

**Confidence:** High (E2) — applied successfully, verified local main matches origin.

**Reversibility:** N/A — completed.

**Change trigger:** N/A. Captured as a learning in `docs/learnings/learnings.md`.

## Changes

### `packages/plugins/codex-collaboration/server/dialogue.py` — Remove turn_dispatch from recovered set

**Purpose:** Fix the P1 regression where `recover_pending_operations()` unconditionally added `turn_dispatch` collaboration IDs to the returned set.

**Changes:**
- Deleted line `recovered.append(entry.collaboration_id)` from the `turn_dispatch` branch (was line 409, now line 408 is just `self._recover_turn_dispatch(entry)`)
- Updated `recover_pending_operations()` docstring at lines 392-398: "Returns collaboration_ids of handles that were fully reattached (resume_thread + update_runtime) by phase 1. Handles only reconciled (journal resolved, metadata repaired, or quarantined) are NOT included — they still need phase-2 reattach."

**Key detail:** The fix restores the semantic distinction: `recovered` means "fully reattached by phase 1" (only `_recover_thread_creation dispatched`), not "touched by phase 1" (which would include `_recover_turn_dispatch`).

### `packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py` — Updated + new test

**Purpose:** Fix stale test assertion and add regression coverage for confirmed turn_dispatch.

**Changes:**
- `test_journal_reconciled_before_reattach` (line 69): h1 assertion changed from `status == "unknown"` to `status == "active"` with `codex_thread_id == "thr-start-resumed"`. Docstring updated to describe the full Option C flow: phase 1 quarantines, phase 2 reattaches.
- New `test_confirmed_turn_dispatch_does_not_suppress_phase_2_reattach` (line 117): Sets up 1 completed turn, writes `turn_dispatch intent` journal entry with `context_size=4096`. Asserts phase 1 confirmed and repaired metadata (`context_size == 4096`) AND phase 2 resumed the handle (`codex_thread_id == "thr-start-resumed"`).
- `test_does_not_double_resume_handles_from_phase_1` (line 167): Docstring tightened to scope it explicitly to `thread_creation` — removes ambiguity about which operation type the test covers.

### `docs/learnings/learnings.md` — New learning entry

**Purpose:** Captured the `git branch -f` technique for safely reconciling a diverged local branch after squash-merge.

### `docs/superpowers/plans/2026-03-29-reply-failure-quarantine-and-parse-finalization.md` — Plan artifact

**Purpose:** The 7-task TDD plan that drove the prior session's implementation. Committed to main as reference artifact.

### `docs/reviews/2026-03-29-reply-failure-quarantine-and-parse-finalization-adversarial-review.md` — Review artifact

**Purpose:** The 3-round adversarial review that amended the plan. Committed to main as reference artifact.

## Codebase Knowledge

### Key Code Locations (Verified This Session)

| What | Location | Why verified |
|------|----------|-------------|
| `recover_startup()` | `dialogue.py:317-389` | Phase 1 + phase 2 flow, skip logic at line 352 |
| `recover_pending_operations()` | `dialogue.py:391-409` | The unconditional append that was removed |
| `_recover_thread_creation()` | `dialogue.py:412-476` | Full reattach path (lines 440-463): read_thread + resume_thread + update_runtime |
| `_recover_turn_dispatch()` | `dialogue.py:478-538` | Journal-only reconciliation: read_thread for confirmation, metadata repair or quarantine |
| `TurnStore.get()` | `turn_store.py:41-44` | Returns `int | None` (context_size), not an object |
| `FakeRuntimeSession` | `test_control_plane.py:21-125` | `start_thread()` returns "thr-start", `resume_thread(id)` returns `f"{id}-resumed"` |
| `_recovery_stack` | `test_recovery_coordinator.py:18-48` | UUID factory: "rt-1", "id-0", "id-1"...; collaboration IDs: "collab-0", "collab-1"... |
| Crash Recovery Contract | `contracts.md:141-156` | Option C eligibility: zero completed OR complete TurnStore metadata |

### Architecture: recover_startup() Phase 1 → Phase 2 Handoff

```
Phase 1: recover_pending_operations()
  ├── thread_creation intent → no-op, resolve journal, return None
  ├── thread_creation dispatched → FULL REATTACH (read + resume + update_runtime)
  │     → return cid → added to recovered_cids ✓
  ├── turn_dispatch (any phase) → RECONCILE ONLY (confirm/quarantine + metadata repair)
  │     → return nothing → NOT added to recovered_cids ✓ (fixed this session)
  └── Returns: set of fully-reattached cids

Phase 2: enumerate active + unknown handles
  ├── Skip handles in recovered_cids (already resumed by phase 1)
  ├── For each remaining handle:
  │     ├── read_thread → metadata completeness check
  │     ├── If incomplete → quarantine to unknown, continue
  │     ├── resume_thread → update_runtime
  │     └── If unknown and successful → upgrade to active
  └── Exception → quarantine to unknown
```

### Test Infrastructure

| Helper | File | Behavior |
|--------|------|----------|
| `_recovery_stack` | `test_recovery_coordinator.py:18-48` | 6-tuple: controller, plane, store, journal, turn_store, session |
| `FakeRuntimeSession.start_thread()` | `test_control_plane.py:80-82` | Always returns `"thr-start"` |
| `FakeRuntimeSession.resume_thread(id)` | `test_control_plane.py:123-124` | Returns `f"{id}-resumed"` |
| `FakeRuntimeSession.read_thread(id)` | `test_control_plane.py:109-121` | Returns `read_thread_response` if set, else dynamic based on `completed_turn_count` |
| `TurnStore.get(cid, turn_sequence=N)` | `turn_store.py:41-44` | Returns `int | None` (context_size), NOT an object |

### FakeRuntimeSession Gotchas (Updated)

- `read_thread_response` overrides dynamic behavior globally — set it before calling recovery, and know that both phase 1 and phase 2 will see the same response.
- `start_thread()` always returns `"thr-start"` — all handles share this thread ID in tests. This means `resume_thread` also always yields `"thr-start-resumed"`.
- The UUID factory in `_recovery_stack` starts at `"rt-1"` (runtime ID) then `"id-0"`, `"id-1"`... The collaboration ID factory starts at `"collab-0"`.

## Context

### Mental Model

This session's core problem is distinguishing "journal reconciliation touched this handle" from "this handle has been fully reattached" in the `recovered_cids` set. Only full reattach (resume + update_runtime) should suppress phase 2. The original one-liner conflated these two semantics because it was written when phase 2 only listed `active` handles — under that assumption, quarantining to `unknown` was terminal. Task 5's extension to `unknown` handles made the conflation visible.

### Project State

| Milestone | Status | Commit/PR |
|-----------|--------|-----------|
| Spec compiled and merged | Complete | `bf8e69e3` |
| T1: Compatibility baseline | Complete | `f53cd6c8` (PR #87) |
| R1: First runtime milestone | Complete | `3490718a` on main |
| Post-R1 spec amendments | Complete | `078e5a39`..`2ae76ed1` on main |
| R2 implementation + fixes | Complete | PR #89 (30 commits) |
| **Review fix + squash-merge** | **Complete** | `f5fc5aab` on main |
| Post-R2 hardening | **Next** | Not started |

210 tests passing on main. Branch `feature/codex-collaboration-r2-dialogue` still exists (tagged at `r2-dialogue-branch-tip` → `d2d0df56`).

## Learnings

### Only add to recovered_cids when phase 1 performs full reattach

**Mechanism:** `recover_pending_operations()` returns collaboration IDs that phase 2 should skip. The skip is correct only when phase 1 performed `resume_thread` + `update_runtime`. Journal reconciliation (confirm/quarantine + metadata repair) is necessary but insufficient — the handle still needs phase-2 reattach.

**Evidence:** `_recover_thread_creation dispatched` (dialogue.py:440-463) calls `resume_thread` and `update_runtime`. `_recover_turn_dispatch` (dialogue.py:478-538) only calls `read_thread` for confirmation. The one-liner that added `turn_dispatch` to recovered was introduced in Task 5 (`3791a81f`) to "prevent phase 2 from immediately reattaching a quarantined handle" — correct under pre-Task-5 semantics, wrong under Option C.

**Implication:** When extending a skip/filter set, verify that the skip condition holds for all items in the extended set, not just the original items. The filter that was correct for `active`-only phase 2 was wrong for `active + unknown` phase 2.

### TurnStore.get() returns int, not an object

**Mechanism:** `TurnStore.get(collaboration_id, turn_sequence=N)` returns `int | None` — just the `context_size` value. It's a thin key-value wrapper, not a record store. `get_all(collaboration_id)` returns `dict[int, int]` (turn_sequence → context_size).

**Evidence:** `turn_store.py:41-44`. Discovered when the regression test asserted `metadata.context_size == 4096` and got `AttributeError: 'int' object has no attribute 'context_size'`.

**Implication:** Always check return types before writing assertions. Pyright flagged this, but the test was written before running the type checker.

### Use branch -f over reset --hard for post-squash-merge reconciliation

**Mechanism:** After squash-merge, local main may have commits that are subsumed by the squash. `git branch -f main origin/main` (run from another branch) moves the ref without touching the worktree. `git reset --hard origin/main` works but silently discards uncommitted changes.

**Evidence:** Applied in this session. Local main had 9 ahead / 1 behind. `branch -f` reconciled cleanly. Also captured in `docs/learnings/learnings.md`.

**Implication:** Prefer `branch -f` as the default post-squash-merge reconciliation. It's one extra `switch` but eliminates worktree risk entirely.

## Next Steps

### T1: Set the post-R2 hardening bar

**Dependencies:** None — this is a decision, not implementation.

**What to read first:** The "Unverified Areas" from the implementation reviews: real Codex runtime behavior for `thread/read` and `thread/resume` remains unverified. All 210 tests use FakeRuntimeSession.

**Approach:** Decide whether live-runtime crash/restart validation is required before treating startup recovery as stable. My analysis: the controller logic is deterministic (journal-based), the FakeRuntimeSession faithfully models the contract surface, and the real uncertainty is Codex's wire behavior — which is validated the first time someone uses `codex.dialogue.reply` in a session where a runtime restart happens. A lightweight smoke test (start → reply → kill runtime → recover → reply) would close the gap if evidence is needed.

**Potential obstacles:** If live testing reveals Codex's `thread/resume` behaves differently from the contract (e.g., doesn't return a new thread ID), the recovery logic would need adjustment.

### T2: Decide on residual recovery debt

**Dependencies:** None, but sequencing after T1 is recommended (T1 determines if the next cycle stays in hardening).

**What to read first:** The two inherited follow-ups from the prior handoff:
1. `_recover_turn_dispatch()` audit parity — `dialogue.py:478-538` doesn't emit `dialogue_turn` audit events on confirmed turns, while `_best_effort_repair_turn` does (best-effort). Pre-existing asymmetry.
2. Chronically unreachable unknown handles — no TTL or escalation for handles where the underlying infrastructure is permanently broken.

**Approach:** Decide whether these are immediate hardening work or explicit follow-up debt. The audit parity fix would mirror `_best_effort_repair_turn()`'s pattern at `dialogue.py:558-599`. The TTL question is architectural.

### T3: Decide on context-assembly trust gaps

**Dependencies:** None, parallel with T2.

**What to read first:** [T-20260327-01](docs/tickets/2026-03-27-r1-carry-forward-debt.md) — the R1 carry-forward debt ticket tracking redaction coverage and non-UTF-8 handling gaps.

**Approach:** Decide whether these trust-boundary gaps should be promoted ahead of new feature work. These affect the existing production consult path, not just the new dialogue path.

### T4: Freeze the next work package

**Dependencies:** T1, T2, T3.

**What to read first:** Outcomes of T1-T3.

**Approach:** Select one next work item, agree on scope boundary, create the starting artifact for the next session.

## In Progress

Clean stopping point. All work merged to main. Post-R2 next-steps framework discussed and analyzed but no decisions made. T1-T4 are decision tasks for the next session, not implementation.

**User's next step:** Start with T1 (set the hardening bar), then resolve T2 and T3 in parallel.

## Open Questions

### MCP consumer retry behavior for CommittedTurnParseError (inherited)

The error message says "Blind retry will create a duplicate follow-up turn." But Claude (the MCP consumer) has no programmatic mechanism to distinguish this error from a generic tool failure. Will it retry? Task 6's test verifies the guidance is in the error text, but wire-level retry prevention is out of scope.

### Chronically unreachable unknown handles (inherited)

Startup recovery will retry `unknown` handles every restart. If the underlying infrastructure is permanently broken (deleted repo, revoked credentials), the handle never recovers and never gets evicted. No TTL or escalation mechanism exists. Tracked as part of T2.

### Pre-existing _recover_turn_dispatch audit gap (inherited, tracked as T2)

The existing startup recovery method at `dialogue.py:478-538` doesn't emit `dialogue_turn` audit on confirmed turns. The new `_best_effort_repair_turn` does (best-effort). This asymmetry is documented in the plan's Key Invariants and out-of-scope sections.

### Feature branch cleanup

`feature/codex-collaboration-r2-dialogue` still exists on remote. The branch tip is tagged as `r2-dialogue-branch-tip`. Can be deleted once the tag is confirmed pushed (it was pushed this session).

## Risks

### No live-runtime validation of recovery path

All 210 tests use FakeRuntimeSession. The recovery logic's correctness against real Codex `thread/resume` behavior is assumed, not verified. This is the subject of T1.

### 30-commit history compressed to 1

The squash merge loses per-task bisectability on main. If a subtle regression is found later, bisecting within the R2 change requires checking out the branch via the tag. Mitigated by: (1) tag `r2-dialogue-branch-tip`, (2) PR #89 history, (3) 210 tests.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Squash merge commit | `f5fc5aab` on main | The R2 landing commit |
| Branch tip tag | `r2-dialogue-branch-tip` → `d2d0df56` | Per-task commit archaeology |
| PR #89 | jpsweeney97/claude-code-tool-dev#89 | Full PR with 30-commit history |
| Implementation plan | `docs/superpowers/plans/2026-03-29-reply-failure-quarantine-and-parse-finalization.md` | 7-task TDD plan (executed by prior session) |
| Adversarial review | `docs/reviews/2026-03-29-reply-failure-quarantine-and-parse-finalization-adversarial-review.md` | 3-round review that amended the plan |
| Modular spec | `docs/superpowers/specs/codex-collaboration/` | Normative v1 contract (9 files) |
| contracts.md | `docs/superpowers/specs/codex-collaboration/contracts.md` | Handle lifecycle, crash recovery (Option C at lines 146-156) |
| R1 carry-forward debt | `docs/tickets/2026-03-27-r1-carry-forward-debt.md` | Context-assembly trust gaps (T3) |
| Prior handoff (plan execution) | `.archive/2026-03-29_02-45_plan-executed-pr89-pushed-ready-for-merge.md` | Full execution context |
| `git branch -f` learning | `docs/learnings/learnings.md` (bottom) | Captured technique for post-squash reconciliation |

## Gotchas

### TurnStore.get() returns int, not an object

`turn_store.get(collaboration_id, turn_sequence=N)` returns `int | None` — the raw context_size value. Not a dataclass, not a dict. Pyright catches this but if you write tests before checking types, you'll get `AttributeError: 'int' object has no attribute 'context_size'`.

### recover_pending_operations() return set is semantic, not exhaustive

The returned list means "handles fully reattached by phase 1" — not "handles touched by phase 1." `_recover_turn_dispatch` touches handles (reconciles journal, repairs metadata, quarantines) but doesn't reattach, so it correctly does NOT add to the return set. The docstring at `dialogue.py:392-398` now documents this explicitly.

### FakeRuntimeSession.start_thread() always returns "thr-start"

All handles in tests share the same thread ID. When `read_thread_response` is set globally, both phase 1 and phase 2 see the same response. This means test assertions about thread IDs can't distinguish which phase did the resume — only that resume happened. For tests that need to distinguish phases, use the `tracking_resume` pattern from `test_does_not_double_resume_handles_from_phase_1`.

### Local main can diverge after squash-merge

If commits were on local main before the branch was created, and the branch includes those commits, the squash merge on remote main subsumes them. Local main ends up "ahead" of origin with commits that are already in the squash. Use `git branch -f` to reconcile (see Learnings section).

## Conversation Highlights

**Review presentation style:**
User presented the implementation review in a structured format: code comments with priority/confidence, requirements ledger (R1-R9) with status and falsification attempts, findings section, and verdict. This is the established review workflow for this project.

**Scope precision:**
User: "That is the right boundary: one code fix, one expectation update, one regression test."
— Clear scope containment. No feature creep, no "while we're here" cleanups.

**Merge strategy reasoning:**
User: "main should optimize for readability, revertability, and bisectability, not preserve every task checkpoint."
User: "The archaeological value is still available in the branch, PR, and the saved plan/review docs."
— Explicit hierarchy: main's commit history serves different goals than the branch's.

**Safety catch on git operations:**
User: "I would not use `git reset --hard origin/main` on main right now, because your worktree is dirty. Safer approach: [branch -f technique]."
— Even when the worktree turned out to be clean, the user preferred the safer approach. Risk-averse with git operations.

**Next-steps framing:**
User presented a 4-task dependency map with a sequenced plan and decision gates. The structure separates "what to decide" (T1-T3) from "what to do" (T4), ensuring decisions are explicit before implementation begins.

## User Preferences

**Review-then-fix workflow:** User runs implementation reviews between sessions, presents findings with evidence, and expects the fix to be scoped precisely to the findings. No additional cleanup or improvements.

**Merge hygiene:** Squash over regular merge for branches with many commits. Tag the branch tip for archaeology. Write substantive squash commit messages that name the areas of change.

**Git safety:** Prefer safe alternatives to destructive operations even when the destructive version would work. `branch -f` over `reset --hard`.

**Decision-first planning:** Separate decision tasks (T1-T3) from implementation tasks (T4). Resolve decisions before freezing scope.

**Scope discipline:** User: "That is the right boundary: one code fix, one expectation update, one regression test." — Explicit, minimal scope for fixes. No bundled improvements.

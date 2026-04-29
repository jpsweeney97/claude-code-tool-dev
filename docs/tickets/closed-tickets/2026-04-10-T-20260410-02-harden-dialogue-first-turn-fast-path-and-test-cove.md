# T-20260410-02: Harden dialogue first-turn fast path and test coverage

```yaml
id: T-20260410-02
date: '2026-04-10'
status: closed
closed_date: '2026-04-13'
resolution: completed
resolution_ref: 'PR #105'
summary: Harden dialogue first-turn fast path and test coverage
priority: high
source_type: pr-review
source_ref: 'PR #101'
effort: M
branch: fix/t02-dialogue-first-turn-hardening
files:
- packages/plugins/codex-collaboration/server/dialogue.py
- packages/plugins/codex-collaboration/server/turn_store.py
- packages/plugins/codex-collaboration/tests/test_dialogue.py
- packages/plugins/codex-collaboration/tests/test_turn_store.py
```

## Problem

The first-turn fast path in DialogueController._next_turn_sequence currently treats TurnStore.get_all() returning an empty mapping as definitive proof that no turns have completed. That is correct on the verified happy path, but it is not robust against replay corruption, path mismatches, or partial metadata state. The current tests also do not force read_thread to raise on turn 1 or exercise TurnStore-gap cases, so a future refactor could quietly weaken the safety boundary around the original bug fix.

## Proposed Approach

Revisit the first-turn fast-path predicate so it distinguishes 'no local metadata yet' from 'metadata unreadable or structurally suspect'. Preserve the verified happy path, but add explicit tests for turn-1 read_thread failure, TurnStore gap/corruption scenarios, and error-context surfacing when the fallback read_thread path fails.

## Acceptance Criteria

- DialogueController no longer treats an empty TurnStore replay result as sufficient proof of zero completed turns when replay diagnostics indicate corruption or structural ambiguity
- A regression test proves turn 1 succeeds without calling read_thread on the healthy path
- A regression test forces read_thread to raise on turn 1 and verifies the fast path does not mask the failure mode being tested
- A regression test covers _next_turn_sequence behavior when turn metadata is partial, gapped, or otherwise inconsistent
- Failure messages around turn-sequence derivation include enough context to distinguish local metadata ambiguity from remote thread-read failure

## Evidence

> Fast path trusts TurnStore.get_all() returning empty as proof of 'no turns completed' ... concern is 'what happens under corruption or concurrent writers?' — which is a hardening question, not a runtime-correctness question.

## Resolution

Merged PR #105 (`fix/t02-dialogue-first-turn-hardening`, 8 commits, `9cbcb8a3`).

**What shipped:**
- `_local_metadata_complete_for_completed_turns()` shared prefix-completeness helper replacing the old `len(metadata) < completed_count` cardinality check
- `_next_turn_sequence()` rewritten with three-phase trust policy (empty+clean → fast path; empty+diagnostics or non-empty → remote validation; prefix-completeness gate)
- `recover_startup()` restructured to use the shared helper unconditionally
- `TurnStore.get_all_checked()` for single-pass metadata + diagnostics
- 17 new tests: 3 turn_store, 9 fast-path hardening, 3 recovery completeness, 2 recovery-diagnostics pinning
- Spec and contract docs updated

All 5 acceptance criteria met. 563 tests passing.

<!-- defer-meta {"created_by":"defer-skill","source_ref":"PR #101","source_session":"","source_type":"pr-review","v":1} -->

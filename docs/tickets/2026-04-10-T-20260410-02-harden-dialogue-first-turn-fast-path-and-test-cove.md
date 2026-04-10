# T-20260410-02: Harden dialogue first-turn fast path and test coverage

```yaml
id: T-20260410-02
date: '2026-04-10'
status: deferred
summary: Harden dialogue first-turn fast path and test coverage
priority: high
source_type: pr-review
source_ref: 'PR #101'
effort: M
branch: feature/b4-agent-skill-harness-assembly
files:
- packages/plugins/codex-collaboration/server/dialogue.py
- packages/plugins/codex-collaboration/tests/test_dialogue.py
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

<!-- defer-meta {"created_by":"defer-skill","source_ref":"PR #101","source_session":"","source_type":"pr-review","v":1} -->

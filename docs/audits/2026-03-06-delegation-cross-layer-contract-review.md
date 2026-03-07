# Delegation Cross-Layer Contract Review

Date: 2026-03-06
Scope: `docs/plans/2026-03-06-delegation-capability-design.md`, `docs/plans/2026-03-06-delegation-implementation-plan.md`, `packages/plugins/cross-model/skills/delegate/SKILL.md`
Mode: Rigorous

## Entry Gate

Assumptions:
- The design spec is the authoritative contract for field names and safety behavior.
- The implementation plan code listings are intended to be directly implemented.
- `packages/plugins/cross-model/skills/delegate/SKILL.md` is the current runtime instruction file.

Stakes:
- Moderate blast radius: this touches execution, repo-state safety, and analytics.
- Moderate-to-high cost of error: contract drift can produce unsafe delegation, misleading review output, or unusable metrics.
- Moderate uncertainty: several behaviors depend on ordering across Tasks 5, 6, and 7.

Stopping criteria:
- Primary: yield-based.
- Threshold: <10% new meaningful findings per pass.

## Summary

Findings:
- P1: 7
- P2: 10
- P3: 6

Key issues:
- The review contract is incomplete: `git diff` alone cannot review staged or newly created files.
- The rollout graph is unsafe: Task 7 can emit `delegation_outcome` before Tasks 5 and 6 can consume it.
- Several user-visible contracts drift between layers: `blocked_paths`, non-zero `exit_code` on `status=ok`, temp-file permissions, and validation messages.

## Findings

1. P1: Task 7 rollout order is unsafe. The plan says Task 7 depends only on Tasks 1 and 3, but it emits `delegation_outcome` before Task 5 (`read_events.py`) and Task 6 (`compute_stats.py`) are guaranteed to recognize it.
2. P1: `blocked_paths` exists only in the adapter stdout plan. The spec output schema and the skill do not define or consume it, even though blocked secret/dirty-tree paths are supposed to be reported.
3. P1: The skill treats `status=ok` as success even when `exit_code != 0`, despite the spec explicitly allowing non-zero exit codes in the `ok` state.
4. P1: `_check_clean_tree()` and `_check_secret_files()` map git command failures to gate blocks. That mislabels infrastructure failure as dirty-tree or secret-file policy failure.
5. P1: The review procedure cannot actually satisfy "Claude reviews all changes" because it inspects `git diff` only. That misses staged-only changes and all untracked file contents.
6. P1: The skill owns the input temp file after F6, but the skill contract never requires secure `0600` creation even though the prompt may contain credentials before the scan runs.
7. P1: The spec/skill validation flow is stale in places. The design's skill-flow block still branches only on `status`, while the detailed output contract and current skill rely on `dispatched`.
8. P2: `_check_clean_tree()` still misparses rename/copy NUL records when `R`/`C` is in the Y column. It still blocks, but the blocked path list can be wrong or truncated.
9. P2: The skill says "include only explicitly set fields" while also showing defaults in the example, and the adapter always applies defaults anyway.
10. P2: `_KNOWN_EVENT_TYPES` omits `turn.started` and `item.started`, contradicting the spec's "ignored" table and causing misleading "no usable JSONL events" failures.
11. P2: The adapter import fallback can still crash at module import time if the second bare import fails.
12. P2: Validation message strings drift between layers for `danger-full-access` and `--full-auto` + `read-only`.
13. P2: The analytics/stats schema conflates scanner failures with actual credential detections through `credential_blocked` / `credential_block_count`.
14. P2: The spec says runtime step-10 timeout/signal errors include signal/exit details, but the plan pins a different `"exec failed: process timeout"` message and does not model signal termination.
15. P2: The spec text says `reasoning_effort` is nullable in `delegation_outcome`, but the planned emitter defaults missing values to `"high"`.
16. P2: The spec says `runtime_failures` captures `turn.failed` events, but the plan also stores top-level `error` events there without updating the contract text.
17. P3: `_emit_analytics(parsed["thread_id"])` is not a current bug under the listed parser contract, but `.get()` would be the correct defensive form.
18. P3: `ok/dispatched=false` is undocumented. It should be forbidden as an invariant or handled defensively by the skill.
19. P3: The prompt is scanned before trimming but executed after trimming. This is a weak semantic mismatch, not an exploitable gap.
20. P3: The dirty-tree precondition is documented as if it were checked before Step 2, but enforcement actually happens inside the adapter after the input temp file is written.
21. P3: The test plan's `test_success_path` can leak a file descriptor if the test aborts before the adapter closes it.
22. P3: The skill troubleshooting still recommends `git checkout --`, which is stale and incomplete for staged or untracked outputs.
23. P3: The skill promises case-insensitive flag values but never explicitly instructs normalization before writing JSON.

## Recommended Fix Order

1. Fix rollout/dependency ordering for Tasks 5, 6, and 7.
2. Fix the review contract: staged diff, untracked-file inspection, and non-zero `exit_code` handling.
3. Fix stdout contract drift: decide whether `blocked_paths` is part of the public adapter schema.
4. Fix gate-failure classification so git command failures return `status=error`.
5. Fix temp-file permission guidance for the skill-owned input JSON.
6. Sweep message and schema drift (`danger-full-access`, conflict wording, timeout wording, runtime_failures semantics).

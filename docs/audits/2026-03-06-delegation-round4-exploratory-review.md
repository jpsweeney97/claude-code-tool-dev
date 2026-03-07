# Delegation Round 4 Exploratory Review

**Date:** 2026-03-06
**Thread:** `019cc4f5-e732-7a03-89ee-14aed9411789`
**Posture:** Exploratory (5/10 turns, converged)
**Targets:** `docs/plans/2026-03-06-delegation-capability-design.md`, `docs/plans/2026-03-06-delegation-implementation-plan.md`, `packages/plugins/cross-model/skills/delegate/SKILL.md`
**Thoroughness:** Rigorous
**Status:** All 16 findings integrated into plan, spec, and SKILL.md.

## Entry Gate

**Inputs**
- Design spec: `docs/plans/2026-03-06-delegation-capability-design.md`
- Implementation plan: `docs/plans/2026-03-06-delegation-implementation-plan.md`
- User-facing skill: `packages/plugins/cross-model/skills/delegate/SKILL.md`
- Current integration surfaces: `packages/plugins/cross-model/scripts/compute_stats.py`, `packages/plugins/cross-model/scripts/read_events.py`, `packages/plugins/cross-model/scripts/emit_analytics.py`, `packages/plugins/cross-model/skills/consultation-stats/SKILL.md`, `packages/plugins/cross-model/README.md`

**Assumptions**
- The design spec is the authoritative behavior contract.
- The implementation plan is intended to be implementable as written.
- Current `compute_stats.py`, `read_events.py`, and analytics tests are relevant because the plan explicitly modifies them.

**Stakes**
- Reversibility: moderate
- Blast radius: moderate to wide
- Cost of error: high
- Uncertainty: moderate

**Stopping criterion**
- Rigorous review with yield below 10% after cross-checking spec, plan, skill, and current integration surfaces.

## Summary Table

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 1 | Safety/correctness gap that can suppress review of post-dispatch changes |
| P1 | 5 | Material implementation or integration gaps likely to cause defects or drift |
| P2 | 1 | Important documentation/flow polish gap |

## Findings

### P0-1: The adapter output contract is missing the one field the skill needs to safely handle post-dispatch errors

**Why this matters**
- The skill says `status=error` means "do not attempt review — there are no changes to inspect".
- The plan and spec both allow `error` after Codex has already run: parse failure after `codex exec`, subprocess timeout, output-file read failure, and generic post-dispatch failures.
- In those cases the repo may already contain Codex-authored changes, but the skill has no `dispatched` signal in stdout to distinguish pre-dispatch errors from post-dispatch errors.

**Evidence**
- Spec output schema omits `dispatched`: `docs/plans/2026-03-06-delegation-capability-design.md:288-305`
- Spec still defines `error` broadly enough to include post-dispatch failures: `docs/plans/2026-03-06-delegation-capability-design.md:309-314`
- Planned adapter stdout similarly omits `dispatched`: `docs/plans/2026-03-06-delegation-implementation-plan.md:2168-2172`, `docs/plans/2026-03-06-delegation-implementation-plan.md:2261-2304`
- Skill says blocked/error paths have no changes to inspect: `packages/plugins/cross-model/skills/delegate/SKILL.md:120-128`

**Required change**
- Add `dispatched` to the adapter stdout schema, or require the skill to run a review probe on `status=error` before concluding that no changes exist.
- Add contract tests that assert the exact stdout schema on `ok`, `blocked`, and `error`.

### P1-1: The plan's sibling-import instructions are incomplete for Task 2 and Task 4

**Why this matters**
- The plan tells implementers to use bare sibling imports in `codex_guard.py` and `emit_analytics.py`.
- Those files are executed in more than one way: directly as scripts and imported by tests. Bare sibling imports only reliably work in the direct-script case.

**Evidence**
- Task 2 instructs `from credential_scan import scan_text`: `docs/plans/2026-03-06-delegation-implementation-plan.md:415-426`
- Task 4 instructs `from event_log import ...`: `docs/plans/2026-03-06-delegation-implementation-plan.md:667-671`
- Current code already uses import-fallback patterns for sibling scripts in this repo: `packages/plugins/cross-model/scripts/compute_stats.py:23-29`
- The adapter task explicitly adds a fallback path, which implies the import surface is not uniform: `docs/plans/2026-03-06-delegation-implementation-plan.md:1769-1776`

**Required change**
- Use the same fallback import pattern in Tasks 2 and 4, not only in Task 7.
- Add a direct invocation/import smoke test for `codex_guard.py` and `emit_analytics.py` after the refactor.

### P1-2: Phase B validation still has untested wrong-type paths that will raise `TypeError`, not deterministic validation errors

**Why this matters**
- The spec promises deterministic Step 5 failures like `validation failed: invalid sandbox value`.
- The planned `_validate_input()` checks set membership before confirming types for `sandbox` and `reasoning_effort`, and it never validates `model` is a string.
- Non-string JSON values can therefore escape into generic exception handling or command building.

**Evidence**
- Planned validation logic: `docs/plans/2026-03-06-delegation-implementation-plan.md:1883-1905`
- Failure table requires deterministic validation failures: `docs/plans/2026-03-06-delegation-capability-design.md:258-260`
- Planned tests only cover invalid enum strings, not wrong JSON types: `docs/plans/2026-03-06-delegation-implementation-plan.md:1347-1379`

**Required change**
- Add explicit type checks for `sandbox`, `reasoning_effort`, and `model`.
- Add tests for `sandbox=[]`, `reasoning_effort={}`, and `model=123`.

### P1-3: Step 10 failure handling is still weaker than the spec, and the tests do not pin the required behavior

**Why this matters**
- The spec defines deterministic Step 10 messages for subprocess spawn failure and timeout/signal failure.
- The planned `run()` implementation does not catch `subprocess.TimeoutExpired` or spawn errors around `codex exec` specifically; those fall into the generic `internal error` path.
- The existing timeout test only checks exit code, not the required error contract or analytics shape.

**Evidence**
- Spec failure modes for Step 10: `docs/plans/2026-03-06-delegation-capability-design.md:266-269`
- Planned `run()` wraps `subprocess.run(...)` without a step-specific `except`: `docs/plans/2026-03-06-delegation-implementation-plan.md:2242-2247`, `docs/plans/2026-03-06-delegation-implementation-plan.md:2298-2304`
- Planned timeout test asserts only `exit_code == 1`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1650-1675`

**Required change**
- Add explicit Step 10 exception handling for timeout and spawn failure with the spec message shapes.
- Add tests that assert the returned JSON `error` field, not only the process exit code.

### P1-4: The new delegation stats surface changes the report contract, but the plan does not version or fully update the consumers

**Why this matters**
- Task 6 adds a new top-level `delegation` section, a new `--type delegation` option, and a new usage key.
- The plan leaves `report_version` untouched and only updates the plugin README for `/delegate`; it does not update the consultation-stats skill or README sections that still describe a four-section report with four type values.

**Evidence**
- Task 6 changes output shape: `docs/plans/2026-03-06-delegation-implementation-plan.md:1118-1185`
- Current report version is `1.0.0`: `packages/plugins/cross-model/scripts/compute_stats.py:449`
- Current consultation-stats skill still documents only `security`, `dialogue`, `consultation`, `all`: `packages/plugins/cross-model/skills/consultation-stats/SKILL.md:18-27`, `packages/plugins/cross-model/skills/consultation-stats/SKILL.md:54-69`
- Current README still describes four report sections and four `--type` values: `packages/plugins/cross-model/README.md:153-156`, `packages/plugins/cross-model/README.md:216-218`

**Required change**
- Decide whether `report_version` should bump for this envelope change. If not, document why.
- Update `consultation-stats/SKILL.md` and the README analytics sections to include delegation reporting and `--type delegation`.
- Add a report-contract test that asserts the expected top-level sections and report version.

### P1-5: There is no schema-parity guard between `codex_delegate.py` emission and `read_events.py` validation

**Why this matters**
- The repo already protects `dialogue_outcome` and `consultation_outcome` against reader/emitter drift with parity tests.
- Delegation adds a third structured event type, but the plan only adds presence tests for `_REQUIRED_FIELDS`; it does not add the same parity protection for the new emitter.

**Evidence**
- Existing reader/emitter parity tests cover only dialogue and consultation: `tests/test_read_events.py:243-286`
- Task 5 adds delegation schema presence/validation tests but no emitter parity test: `docs/plans/2026-03-06-delegation-implementation-plan.md:698-809`
- Task 7 emits a new structured event directly from the adapter: `docs/plans/2026-03-06-delegation-implementation-plan.md:2123-2159`

**Required change**
- Add a parity test asserting `read_events._REQUIRED_FIELDS["delegation_outcome"]` is a subset of the fields emitted by `_emit_analytics()` in `codex_delegate.py`.
- Extend the "emitter event types covered by reader" test to include `delegation_outcome`.

### P2-1: `SKILL.md` still omits the input-tempfile cleanup that the design now depends on

**Why this matters**
- The design explicitly moved input-file cleanup to the skill as part of the creation-ownership fix.
- The current skill flow writes the input JSON and runs the adapter, but never says to delete the input tempfile afterward.

**Evidence**
- Design cleanup contract: `docs/plans/2026-03-06-delegation-capability-design.md:315-319`
- Skill writes the input file and runs the adapter but has no cleanup step: `packages/plugins/cross-model/skills/delegate/SKILL.md:68-95`

**Required change**
- Add an explicit cleanup step in `SKILL.md` for the input tempfile after the adapter returns, regardless of adapter status.

## Open Items Assessment

### `token_usage` last-turn-only
- Does **not** need design resolution before implementation.
- It is already an explicit Step 1 limitation in the plan and spec.
- It **does** need a test that feeds multiple `turn.completed` events and asserts the chosen behavior so the limitation stays intentional.

### Shadow-tier observability
- Does **not** need scope expansion before implementation if Step 1 intentionally accepts the asymmetry.
- It **does** need two things before coding starts:
  - an explicit non-blocking test proving broad/shadow matches do not block delegation
  - a clearly carried residual-risk note in the release/docs surfaces, not only an inline code comment

### `avg_commands_run` defaulting to `0.0`
- This **should** be resolved before implementation.
- The rest of `compute_stats.py` uses observed-denominator semantics where "no observations" is `None`, not `0.0`.
- Leaving this unresolved will make delegation metrics inconsistent with the rest of the report and will hide the difference between "no dispatched delegations" and "delegations ran zero commands".

## Integration Status

All 7 findings (P0-1 through P2-1) plus 9 additional findings from the Codex dialogue (I1-I5, D1-D4) have been integrated into the plan, spec, and SKILL.md. 19 new tests added across 7 test classes.

| Audit Finding | Dialogue Finding | Integration |
|--------------|-----------------|-------------|
| P0-1 | B1 | Plan (output JSON), Spec (schema), SKILL.md (Step 4 table) |
| P1-1 | B2 | Plan (Tasks 2, 4 import patterns) |
| P1-2 | B3 | Plan (Task 7 `_validate_input`), Spec (validation note) |
| P1-3 | B4 | Plan (Task 7 `run()` Step 10 catches) |
| P1-4 | I2, I3 | Plan (Task 6 report_version, Task 9 consultation-stats) |
| P1-5 | I1 | Plan (Task 7 `TestSchemaParity` test) |
| P2-1 | I4 | SKILL.md (Step 4b cleanup) |
| — | B5 | Plan (Task 7 `_emit_analytics` derivation), Spec (derivation rules) |
| — | B6 | Plan (Task 6 template + compute), Spec (template) |
| — | B7 | Plan (Task 8 verification scope) |
| — | I5 | Plan (Task 7 `_parse_jsonl` type guards) |
| — | D1-D4 | Plan (Task 7 `TestParseJsonlDeferredCoverage`) |

## Exit Gate

All findings integrated. The plan is implementation-ready — 69 total findings across 4 review rounds, all applied.

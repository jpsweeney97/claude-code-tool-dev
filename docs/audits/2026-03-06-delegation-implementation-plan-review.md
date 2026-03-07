# Delegation Implementation Plan Review

**Date:** 2026-03-06
**Target:** `docs/plans/2026-03-06-delegation-implementation-plan.md`
**Authoritative source:** `docs/plans/2026-03-06-delegation-capability-design.md`
**Thoroughness:** Rigorous

## Entry Gate

**Inputs**
- Target document: `docs/plans/2026-03-06-delegation-implementation-plan.md`
- Source document: `docs/plans/2026-03-06-delegation-capability-design.md`
- User focus: weaknesses, gaps, inconsistencies with design spec, missing error handling, test coverage gaps, incorrect assumptions

**Assumptions**
- The design spec is the current authoritative contract.
- The implementation plan is intended to be executable as written, including code snippets and task ordering.
- Current repository code and tests are relevant for validating whether the plan would integrate cleanly.

**Stakes**
- Reversibility: moderate
- Blast radius: moderate to wide (`codex_guard.py`, analytics, stats, new execution adapter)
- Cost of error: high (security gating, analytics correctness, review workflow)
- Uncertainty: moderate

**Stopping criterion**
- Rigorous review with yield below 10% after adversarial pass and cross-check against current code/tests.

## Summary Table

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 3 | Issues that break specified behavior or execution ordering |
| P1 | 13 | Material correctness, safety, or coverage gaps |
| P2 | 5 | Lower-risk drift, brittleness, or polish gaps |

## Coverage Tracker

| ID | Status | Priority | Evidence | Confidence | Notes |
|----|--------|----------|----------|------------|-------|
| D1 Source coverage | [x] | P0 | E2 | High | Compared plan task-by-task to the design spec failure tables, pipeline steps, and analytics requirements. |
| D4 Behavioral completeness | [x] | P0 | E2 | High | Checked adapter pipeline, classifier routing, and analytics semantics for end-to-end behavior. |
| D7 Implementation readiness | [x] | P0 | E2 | High | Reviewed exact code snippets and task ordering for buildability. |
| D12 Consistency | [x] | P0 | E2 | High | Cross-checked plan snippets against current `compute_stats.py`, `read_events.py`, `emit_analytics.py`, `codex_guard.py`, and tests. |
| D13-D19 Document quality | [~] | P1 | E1 | Medium | Plan is generally implementable, but several snippets are underspecified or internally inconsistent. |

## Iteration Log

### Pass 1
- Verified user-supplied claims against exact plan sections.
- Compared spec failure table and JSONL parsing requirements to the proposed adapter code.
- Yield: high.

### Pass 2
- Cross-checked current code/test surfaces for integration breakage and hidden assumptions.
- Looked for places where the plan claims a fix but the insertion point is ambiguous or incomplete.
- Yield: moderate.

### Pass 3
- Adversarial pass focused on false-positive tests, fail-open gates, and branch coverage holes.
- Yield: low enough to stop.

## Findings

### P0-1: Scanner exceptions still violate the spec's fail-closed contract

**Why this matters**
- The spec is explicit: scanner failure must block dispatch with `status=blocked` and exit `0`, not surface as an adapter error.

**Evidence**
- Spec requires scanner error to return `blocked / 0`: `docs/plans/2026-03-06-delegation-capability-design.md:257`
- Planned adapter calls `scan_text(prompt)` directly with no narrow exception handling: `docs/plans/2026-03-06-delegation-implementation-plan.md:2006-2011`
- Generic exceptions fall through to `status=error`, exit `1`: `docs/plans/2026-03-06-delegation-implementation-plan.md:2088-2095`

**Impact**
- A regex/runtime error in credential scanning becomes an adapter error instead of a clean block, violating governance rule 4 and the failure table.

**Required change**
- Wrap step 4 in a dedicated scanner-exception path that emits `status=blocked`, exit `0`, and analytics with `termination_reason="blocked"`.

### P0-2: Root-level test fix ordering is still wrong relative to Task 8

**Why this matters**
- The plan acknowledges root-level test breakage from the `_compute_usage()` signature change, but schedules the fix as an appendix-like subtask after Task 8 already depends on a passing root suite.

**Evidence**
- Task 8 step 1b requires the root-level suite: `docs/plans/2026-03-06-delegation-implementation-plan.md:2153-2156`
- Dependency graph says Task 8 depends on Task 6 including root-level tests, but the repair is documented later as `Task 6 Step 3b`: `docs/plans/2026-03-06-delegation-implementation-plan.md:2188-2190`, `2205-2222`
- The plan text itself says "Update root-level tests first if they fail" while also placing the concrete edits afterward: `docs/plans/2026-03-06-delegation-implementation-plan.md:2156`, `2205-2222`

**Impact**
- Execution order is ambiguous. A literal implementer can finish Task 6 main edits, move to Task 8, and only then discover required root-level changes that were not part of the verified path.

**Required change**
- Move the root-level test edits into Task 6 proper, before Task 6 verification and before any Task 8 dependency references.

### P0-3: The period-filtering test in Task 6 is wrong as written

**Why this matters**
- This is not just weak coverage. The test uses the wrong argument order for `compute()`, so it does not test period filtering at all.

**Evidence**
- Current signature is `compute(events, skipped_count, period_days, section_type)`: `packages/plugins/cross-model/scripts/compute_stats.py:340-345`
- Planned test passes `compute(events, 30, 0, "delegation")`: `docs/plans/2026-03-06-delegation-implementation-plan.md:938-945`

**Impact**
- `30` is passed as `skipped_count`, while `period_days` remains `0`. The test either fails against correct code or gets "fixed" incorrectly during implementation.

**Required change**
- Correct the call to `compute(events, 0, 30, "delegation")` and freeze or inject `now` so the test is deterministic.

### P1-1: The classifier-loop concern is valid, even though the plan gestures at the fix

**Assessment**
- Agree with the substance of the finding. The plan correctly notes the need for a `delegation_outcome` classifier branch, but the code snippet is underspecified and easy to apply incompletely.

**Evidence**
- Current classifier has no delegation branch, so such events become unclassified: `packages/plugins/cross-model/scripts/compute_stats.py:376-397`
- Plan adds a detached snippet for `delegation_outcomes` and the `elif event_type == "delegation_outcome"` branch, but does not anchor it to the exact classifier block: `docs/plans/2026-03-06-delegation-implementation-plan.md:1066-1073`
- `_validate_events()` and classification are separate code paths; fixing one does not fix the other: current validation at `packages/plugins/cross-model/scripts/compute_stats.py:307-329`

**Impact**
- An implementer can apply F2 and still ship broken delegation analytics if they miss the classifier insertion.

**Required change**
- Replace the snippet with explicit edit instructions against the classifier block and add a test that asserts `meta.unclassified_event_count == 0` for a valid delegation event.

### P1-2: `test_success_path` does not cover the spec's output-file summary path

**Assessment**
- Agree.

**Evidence**
- Planned test pre-creates `tmp_path / "codex_output.txt"`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1556-1557`
- Planned adapter allocates its own tempfile via `tempfile.mkstemp(...)`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1997-2001`
- The test only asserts analytics fields, not `summary`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1575-1580`

**Impact**
- Step 12 can be broken and the success-path test still passes.

**Required change**
- Patch `tempfile.mkstemp` or `_build_command`/output path selection so the adapter reads a known file, then assert returned `summary`.

### P1-3: The adapter plan drops the spec-required `error` JSONL event handling

**Why this matters**
- The design spec explicitly lists `error` events as a known family that must be captured for reporting.

**Evidence**
- Spec JSONL tolerance table includes `error` event handling: `docs/plans/2026-03-06-delegation-capability-design.md:232-234`
- Planned `_KNOWN_EVENT_TYPES` excludes `error`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1864-1868`
- No test covers `error` events in `_parse_jsonl()`: only `thread.started`, `item.completed`, malformed lines, unknown events, and zero usable events are tested at `docs/plans/2026-03-06-delegation-implementation-plan.md:1434-1466`

**Impact**
- Real Codex error streams can be misclassified as "no usable JSONL events" or lose the runtime detail the spec says to preserve.

**Required change**
- Add `error` to the known event set, define how it populates output, and add tests for streams containing `error` events with and without other usable events.

### P1-4: Repo-resolution failure is routed through the generic internal-error path, not the specified error path

**Why this matters**
- Step 1 has a deterministic failure contract in the spec; the plan code does not preserve it.

**Evidence**
- Spec requires `"repo resolution failed: not a git repository"`: `docs/plans/2026-03-06-delegation-capability-design.md:252`
- Planned `_resolve_repo_root()` raises `RuntimeError`, not `DelegationError`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1668-1676`
- Generic exceptions are wrapped as `"internal error: {exc}"`: `docs/plans/2026-03-06-delegation-implementation-plan.md:2088-2095`

**Impact**
- The user-facing error string is wrong, and step-1 failures are mischaracterized as internal errors.

**Required change**
- Raise `DelegationError` from `_resolve_repo_root()` or catch `RuntimeError` separately and preserve the spec message.

### P1-5: The plan still has fail-open safety gates on `git status` and `git ls-files` command failure

**Why this matters**
- Safety gates must not silently pass when their underlying git command fails.

**Evidence**
- `_check_clean_tree()` only inspects `stdout`; it does not check `returncode` or subprocess exceptions beyond whatever falls out generically: `docs/plans/2026-03-06-delegation-implementation-plan.md:1776-1788`
- `_check_secret_files()` likewise ignores `returncode`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1791-1830`

**Impact**
- A failing git invocation with empty stdout is treated as "clean/no secrets", which is the wrong polarity for safety gates.

**Required change**
- Treat non-zero exit codes from these gate commands as adapter errors or blocks; do not allow execution to proceed.

### P1-6: `test_delegation_excluded_from_aggregate_metrics` can pass for the wrong reason

**Assessment**
- Agree.

**Evidence**
- Current classifier would send delegation events to `unclassified_count`, so usage aggregates remain zero even if F7/F9 are never implemented: `packages/plugins/cross-model/scripts/compute_stats.py:384-397`
- Planned test only uses delegation events and asserts zeros: `docs/plans/2026-03-06-delegation-implementation-plan.md:911-917`

**Impact**
- The test does not prove delegation is excluded from aggregates; it only proves the report stayed zero.

**Required change**
- Use a mixed fixture containing consultation/dialogue outcomes plus delegation events, then assert delegation changes `delegations_completed_total` without widening aggregate metrics.

### P1-7: Timeout analytics still underreport `dispatched`

**Why this matters**
- The plan claims B8 fixes dispatched analytics, but the implementation only sets `did_dispatch = True` after `subprocess.run(...)` returns.

**Evidence**
- `did_dispatch` is set after the subprocess call: `docs/plans/2026-03-06-delegation-implementation-plan.md:2035-2037`
- Timeout path test exists, but it only asserts exit code, not analytics payload: `docs/plans/2026-03-06-delegation-implementation-plan.md:1511-1534`
- Spec defines `dispatched=true` when Codex actually ran (steps 10+), not only when the Python call returned cleanly: `docs/plans/2026-03-06-delegation-capability-design.md:412-416`

**Impact**
- A timed-out Codex process may be logged as `dispatched=false`, corrupting `delegations_completed_total` and delegation termination analytics.

**Required change**
- Set dispatch state before or around process start, and add a timeout-path test that inspects the emitted event.

### P1-8: The plan is missing the unparseable-version-output test the spec explicitly calls for

**Assessment**
- Agree.

**Evidence**
- Spec has a dedicated failure row for unparseable version output: `docs/plans/2026-03-06-delegation-capability-design.md:263`
- Planned tests cover valid version, old version, and `codex` not found, but not unparseable output: `docs/plans/2026-03-06-delegation-implementation-plan.md:1300-1321`

**Impact**
- The most likely format-drift failure case at the version boundary is untested.

**Required change**
- Add a test with output like `codex dev-build` or `codex unknown` that asserts the exact spec message.

### P1-9: SKILL.md adapter path construction is a brittle string-replacement heuristic

**Why this matters**
- The skill is using a path-derivation trick, not a stable file-relative path. That is fragile by construction.

**Evidence**
- Skill instructs: replace trailing `skills/delegate` with `scripts/codex_delegate.py`: `packages/plugins/cross-model/skills/delegate/SKILL.md:83`

**Impact**
- This works only as long as the runtime notion of "skill base directory" is exactly the installed on-disk path and contains that suffix. Any packaging, relocation, or alternate invocation model that changes the base path semantics breaks adapter resolution.

**Required change**
- Use a deterministic relative path from the skill file location, not substring replacement. For example: resolve plugin root as two parents above the skill directory, then append `scripts/codex_delegate.py`.

### P1-10: Clean-tree path extraction is incorrect for rename/copy records under `--porcelain=v1 -z`

**Why this matters**
- The clean-tree gate is part of the safety contract. Misparsing rename records means incorrect or confusing block output.

**Evidence**
- Planned parser splits all NUL-delimited fields independently and slices each entry with `[3:]`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1782-1786`
- `git status --porcelain=v1 -z` encodes rename/copy records as multi-field NUL-delimited entries, not single-path records.

**Impact**
- Rename/copy entries will be misreported. The second pathname can be treated as a standalone dirty entry, and the first field's status-prefix slicing is not sufficient to reconstruct the affected path set correctly.

**Required change**
- Parse `git status -z` according to porcelain v1 rules, including two-path rename/copy records, and add a test covering at least one rename entry.

### P1-11: `_build_command()` is missing a `--` separator before the prompt

**Why this matters**
- The prompt is user-controlled positional text. If it begins with `-`, the downstream CLI can parse it as an option rather than as prompt content.

**Evidence**
- Planned builder appends the prompt directly as the final argv element: `docs/plans/2026-03-06-delegation-implementation-plan.md:1842-1853`
- No test covers a prompt beginning with `-`: builder tests only cover normal prompts and flags at `docs/plans/2026-03-06-delegation-implementation-plan.md:1403-1431`

**Impact**
- A legitimate prompt like `-fix flaky auth test` can be misparsed by `codex exec`, producing incorrect behavior or flag injection.

**Required change**
- Insert `--` before the prompt positional and add a builder test for a dash-prefixed prompt.

### P1-12: SKILL.md argument-parse error format can echo credentials before any scan

**Why this matters**
- The skill performs argument validation before the adapter runs. Its documented error format includes the raw user input, which can leak secrets before the delegation credential scan ever executes.

**Evidence**
- Skill error format: `argument parsing failed: {reason}. Got: {input!r:.100}` at `packages/plugins/cross-model/skills/delegate/SKILL.md:52`
- The skill validates in Step 1 and only runs the adapter in Step 3: `packages/plugins/cross-model/skills/delegate/SKILL.md:62-87`
- Governance rule requires no user content echoed before credential scan: `docs/plans/2026-03-06-delegation-capability-design.md:130-132`

**Impact**
- Invalid flags combined with a prompt containing credentials can cause the skill itself to echo sensitive user content, violating the delegation safety rule at the human-visible layer.

**Required change**
- Remove raw-input echoing from skill-side validation errors or add a credential scan before any error path that can quote user input.

### P1-13: `_check_codex_version()` ignores timeout and nonzero exit-code failure semantics

**Why this matters**
- The plan wants deterministic version-check failures, but the implementation only handles a subset of subprocess failure modes.

**Evidence**
- Planned version check catches only `FileNotFoundError`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1757-1763`
- It ignores `result.returncode` entirely and proceeds purely by regex on stdout: `docs/plans/2026-03-06-delegation-implementation-plan.md:1765-1773`

**Impact**
- A hanging `codex --version` becomes a generic internal error instead of a deterministic step-6 failure.
- A nonzero returncode with a parseable version string can incorrectly pass the version gate.

**Required change**
- Catch `subprocess.TimeoutExpired` explicitly and convert it to a `DelegationError`.
- Treat nonzero returncode as a version-check failure regardless of stdout contents.

### P2-1: `_SECTION_MATRIX`, `_SECTION_TYPE`, and `argparse` choices are still too easy to update inconsistently

**Assessment**
- Agree with the risk. This is a coordination hazard, not yet a proven defect.

**Evidence**
- These updates are described as separate edits: `docs/plans/2026-03-06-delegation-implementation-plan.md:1052-1064`, `1145-1156`
- Current code keeps them in separate locations: `packages/plugins/cross-model/scripts/compute_stats.py:294-299`, `337`, `492-496`

**Impact**
- Missing any one of the three creates a runtime/type drift that unit tests may not fully catch.

**Required change**
- Add a dedicated test that invokes the CLI with `--type delegation` and asserts `compute(..., "delegation")` works end-to-end.

### P2-2: The `thread_id` access in `_emit_analytics()` is brittle

**Assessment**
- Agree.

**Evidence**
- Planned code uses `parsed["thread_id"] if parsed else None`: `docs/plans/2026-03-06-delegation-implementation-plan.md:1945`

**Impact**
- Any future drift in parser output shape turns a recoverable degraded path into a `KeyError`.

**Required change**
- Use `parsed.get("thread_id") if parsed else None`.

### P2-3: `fnmatch` lazy-import inside `_check_secret_files()` is needless inconsistency

**Assessment**
- Agree, low severity.

**Evidence**
- Planned code imports `fnmatch` inside the function: `docs/plans/2026-03-06-delegation-implementation-plan.md:1797`

**Impact**
- No behavioral issue today, but it makes stdlib import failures surface late and is inconsistent with the rest of the module.

### P2-4: The `if period_days:` guard is redundant and makes the code path less uniform

**Assessment**
- Agree, low severity.

**Evidence**
- Planned delegation filtering uses a special guard: `docs/plans/2026-03-06-delegation-implementation-plan.md:1137-1143`
- Current code filters other event lists unconditionally through `stats_common.filter_by_period(...)`: `packages/plugins/cross-model/scripts/compute_stats.py:402-406`

**Impact**
- Minimal. It is mostly a maintainability inconsistency.

## Additional Observations

1. The plan says `append_log()` is an "atomic append" API, but the proposed implementation is only a normal append-mode write with no test for interprocess semantics: `docs/plans/2026-03-06-delegation-implementation-plan.md:557`, `577-586`. The wording overclaims what is implemented.

2. The period-filtering test is also time-brittle even after fixing the argument order. It hardcodes a March 2026 "recent" timestamp without freezing `now`: `docs/plans/2026-03-06-delegation-implementation-plan.md:938-945`.

3. The current delegate skill document contains a destructive revert suggestion (`git checkout --`) that conflicts with the repository's safety rules, though that is in the skill file rather than this plan: `packages/plugins/cross-model/skills/delegate/SKILL.md:175-177`.

4. Task 4's migration note is internally wrong. It says to update an `_LOG_PATH` reference in the `emit_analytics.py` `finally` block, but the actual `finally` block cleans up `input_path`, not the log path: `packages/plugins/cross-model/scripts/emit_analytics.py:690-696`. This is a plan accuracy bug, not an implementation bug.

5. `token_usage` handling in `_parse_jsonl()` is under-specified for multi-turn runs. The planned code overwrites the field on each `turn.completed`, keeping only the last turn's usage: `docs/plans/2026-03-06-delegation-implementation-plan.md:1899-1905`. The spec names a singular `token_usage` field but does not say whether it should be per-last-turn or cumulative.

## Disconfirmation Attempts

### On the classifier-loop finding
- Technique: counterexample search
- Result: confirmed. Current `compute_stats.py` has no delegation branch, so fixing only `_validate_events()` would still misclassify delegation events.

### On the scanner fail-closed finding
- Technique: alternative-hypothesis check
- Result: rejected. There is no dedicated scanner-exception path in the planned adapter; exceptions flow to the generic error handler.

### On the root-level test ordering finding
- Technique: adversarial read of dependency graph
- Result: confirmed. The dependency notes mention the root-level updates, but the concrete execution order is still easy to misread and apply incorrectly.

## Exit Gate

- [x] Entry Gate recorded
- [x] Source coverage checked against authoritative design
- [x] Adversarial pass completed
- [x] P0 findings disconfirmed where possible
- [x] Findings grounded in file/line evidence
- [x] Report written

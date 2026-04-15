# Benchmark v1 Summary

**Contract:** `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`
**Commit:** _(fill after fixing run commit)_
**Operator:** _(fill)_
**Date:** _(fill)_

## Run-Condition Status

| Control | Status | Detail |
|---------|--------|--------|
| Commit (RC 1) | Matched | |
| Working tree (RC 2) | Matched | All staging outside repo; batch import in Phase 5 |
| Prompt (RC 3) | Matched | Same corpus prompt with scope instructions |
| Posture (RC 4) | **Blocked** | Candidate has no posture control surface |
| Turn budget (RC 4) | **Blocked** | Candidate hardcodes DIALOGUE_TURN_BUDGET = 10 |
| Model/effort/timeout (RC 5) | Matched | |
| Supplemental context (RC 6) | _(fill: Verified / Operator-attested)_ | Fresh session per run. Fill "Verified" if all runs have `session_id_canonical: true`; "Operator-attested" otherwise. |
| Scouting tools (RC 7) | Matched | Glob/Grep/Read for both |
| Transcript retention (RC 8) | Matched | Staged externally, imported at end |
| `allowed_roots` (RC 10-11) | Prompt-only | Neither system uses mechanical scope_envelope enforcement |
| `max_evidence` | Asymmetric (deliberate) | Baseline: 5 (procedural; overflow invalidates). Candidate: 15 (native) |

**Scoring blockers:** Posture and turn-budget controls (RC 4) must be
resolved before results in this table are scored. See operator procedure
§Scoring Prerequisites.

## Aggregate Metrics

| Metric | Baseline | Candidate |
|--------|----------|-----------|
| `safety_violations` | | |
| `false_claim_count` | | |
| `supported_claim_rate` | | |
| `citation_count` (diagnostic) | | |
| `distinct_cited_files` (diagnostic) | | |
| `converged_within_budget` (diagnostic) | | |

## Per-Row Results

| Row | System | Claims | Supported | Unsupported | False | Safety | Converged | Evidence | Citations | Cited Files | Actual Turns |
|-----|--------|--------|-----------|-------------|-------|--------|-----------|----------|-----------|-------------|--------------|
| B1 | baseline | | | | | | | | | | |
| B1 | candidate | | | | | | | | | | |
| B3 | baseline | | | | | | | | | | |
| B3 | candidate | | | | | | | | | | |
| B5 | baseline | | | | | | | | | | |
| B5 | candidate | | | | | | | | | | |
| B8 | baseline | | | | | | | | | | |
| B8 | candidate | | | | | | | | | | |

## Execution Mode

**Mode:** _(SCORED / REHEARSAL)_

If REHEARSAL: all runs below are non-evidentiary per T4-BR-08(b). Skip the
Pass Rule Evaluation and Retirement Decision sections. The remaining
sections (Diagnostic Notes, Benchmark Exceptions) are still useful for
operator playbook validation.

**Reason for rehearsal (if applicable):** _(e.g., "RC4 blocker: candidate
system lacks posture and turn-budget controls")_

## Pass Rule Evaluation

_(Skip this section for rehearsal runs.)_

| # | Condition | Result | Detail |
|---|-----------|--------|--------|
| 1 | `safety_violations == 0` | | |
| 2 | Candidate `false_claim_count` <= baseline | | |
| 3 | Candidate `supported_claim_rate` within 0.10 of baseline | | |

**Verdict:** _(PASS / FAIL / INCOMPLETE — scored runs only)_

## Diagnostic Notes

_(Observations about convergence, evidence usage patterns, scouting behavior
differences, posture/turn-budget asymmetry effects, or other patterns that
inform interpretation but are not pass/fail gates. Applicable to both scored
and rehearsal runs.)_

## Benchmark Exceptions

_(Any runs that were invalidated and rerun, scope violations discovered during
adjudication, deviations from the operator procedure, or session isolation
failures. If none, write "None." Include superseded_by chain for any reruns.)_

## Retirement Decision

_(Skip this section for rehearsal runs.)_

_(Based on the verdict above, state the context-injection retirement decision
per the contract's Decision Consequences section.)_

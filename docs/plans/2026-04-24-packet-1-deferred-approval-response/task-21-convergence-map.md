# Task 21 Convergence Map — `discard()` gate expansion (admit canceled)

**Task:** Phase H Task 21 — `discard()` gate expansion
**Branch:** `feature/delegate-deferred-approval-response`
**HEAD at drafting:** `47628f20`
**Scope:** One-line production change in `discard()` + new test file. No helper changes, no contracts.md edits, no poll/start/decide edits.

---

## Stale Anchor Corrections

| Plan reference | Plan value | Live value (HEAD `47628f20`) | Note |
|---|---|---|---|
| Plan §Task 21 `discard()` line range | `delegation_controller.py:1404-1406` | `delegation_controller.py:2324-2326` | Line numbers shifted by Tasks 15-20 insertions |
| Plan §Task 21 test fixtures | `delegation_controller_fixture`, `simple_job_factory`, `audit_event_spy` | Non-existent — package uses `_build_promote_scenario(tmp_path)` + `update_status_and_promotion` per existing discard test pattern at `:3307-3393` | Plan placeholder names must not appear in tests |
| Plan §Task 21 test filename | `test_discard_canceled.py` | Acceptable, but should include `_integration.py` suffix to remain consistent with Task 20 decision and the `-k integration` gate at manifest `:174` | See L5 |

## Live Anchors

| Anchor | Path | Line(s) | Content |
|---|---|---|---|
| `discard()` method def | `delegation_controller.py` | `:2309` | `def discard(self, *, job_id: str) -> DiscardResult \| DiscardRejectedResponse:` |
| `_discardable` gate | `delegation_controller.py` | `:2324-2326` | `_discardable = job.promotion_state in ("pending", "prechecks_failed") or (job.status in ("failed", "unknown") and job.promotion_state is None)` |
| Audit event emission | `delegation_controller.py` | `:2344-2354` | `self._journal.append_audit_event(AuditEvent(..., action="discard", ...))` |
| `update_promotion_state` call | `delegation_controller.py` | `:2338-2341` | `self._job_store.update_promotion_state(job_id, promotion_state="discarded")` |
| Existing discard test: failed+null | `test_delegation_controller.py` | `:3338-3348` | `test_discard_accepts_failed_null_promotion` — pattern reference for new tests |
| Existing discard test: failed+applied | `test_delegation_controller.py` | `:3365-3376` | `test_discard_rejects_failed_with_applied_promotion` — rejection pattern reference |
| `_build_promote_scenario` | `test_delegation_controller.py` | `:2850` | Returns 7-tuple; used by all discard tests |
| `update_status_and_promotion` | `delegation_job_store.py` | `:110` | Sets both `status` and `promotion_state` in one call |
| Audit JSONL path | `journal.py` | `:202, :251-255` | `self._audit_path = self._audit_dir / "events.jsonl"` — written via `append_audit_event` |

## Locks

| # | Lock | Rationale |
|---|---|---|
| L1 | Production change is ONLY adding `"canceled"` to the status tuple at `:2325`. No other line in `discard()` changes. | Spec §1377: "Expand the status branch to `status in ('failed', 'unknown', 'canceled')`." Minimal change. |
| L2 | Post-mutation promotion states (`applied`, `rollback_needed`) still reject regardless of status. The `promotion_state in ("pending", "prechecks_failed")` branch and the `promotion_state is None` predicate are untouched. | Spec §1377: "a canceled job that has somehow acquired a non-null promotion_state still rejects with `job_not_discardable` under the existing rule." |
| L3 | Tests follow the established `_build_promote_scenario` + `update_status_and_promotion` pattern. No plan-placeholder fixture names. | Package convention per existing discard tests at `:3307-3393`. |
| L4 | No modifications to `poll()`, `start()`, `decide()`, `_finalize_turn`, or any helper. | Task 21 boundary — `discard()` is independent of the projection/signal path (L9 from Task 20). |
| L5 | New test file uses `_integration.py` suffix: `test_discard_canceled_integration.py`. | Preserves `-k integration` smoke gate at manifest `:174`, consistent with Task 20 filename decision. |
| L6 | No modifications to `contracts.md`. | Task 22 boundary. |
| L7 | Existing discard tests at `:3307-3393` must not regress. | Regression guard. |

## Watchpoints

| # | Watchpoint | What to check |
|---|---|---|
| W1 | `docstring` at `:2312-2314` should be updated to include `canceled` in the list of statuses. | Currently says "status in (failed, unknown)". After the change, it should say "status in (failed, unknown, canceled)". |
| W2 | Audit event test: verify the JSONL file contains an `action="discard"` record after discarding a canceled job. Read `<journal.plugin_data_path>/audit/events.jsonl` and parse. | No existing discard test checks audit events — this is new coverage. |
| W3 | Full suite ≥ 1043 + N new. | Suite count must not decrease. |

## Test Strategy

Three tests, all synchronous:

| Test | Setup | Assertion |
|---|---|---|
| `test_discard_canceled_with_null_promotion_state_succeeds` | `_build_promote_scenario(tmp_path)` → override to `status="canceled", promotion_state=None` | `isinstance(result, DiscardResult)` + `result.job.promotion_state == "discarded"` |
| `test_discard_canceled_with_applied_promotion_state_rejects` | Same setup → override to `status="canceled", promotion_state="applied"` | `isinstance(result, DiscardRejectedResponse)` + `result.reason == "job_not_discardable"` |
| `test_discard_canceled_writes_audit_event` | Same setup → override to `status="canceled", promotion_state=None` → discard | Read `journal._audit_path`, parse JSONL, find `action="discard"` record with matching `job_id` |

## Acceptance Criteria

| Check | Expected |
|---|---|
| `discard(canceled_job)` with null promotion_state returns `DiscardResult` | Pass |
| `discard(canceled_job)` with applied promotion_state returns `DiscardRejectedResponse` | Pass |
| Audit event written for canceled discard | Pass |
| Existing discard tests pass unchanged | Pass (L7) |
| Full suite ≥ 1043 + N new | Pass |
| `contracts.md` diff = 0 lines | L6 |
| `docstring` updated to include canceled | W1 |

# Task 20 Convergence Map — `poll()` UnknownKindInEscalationProjection Catch

**Task:** Phase H Task 20 — `poll()` projection guard
**Branch:** `feature/delegate-deferred-approval-response`
**HEAD at drafting:** `c53a5199`
**Scope:** Single callsite catch in `poll()` + new test file. No helper changes, no discard/contracts edits.

---

## Stale Anchor Corrections

| Plan reference | Plan value | Live value (HEAD `c53a5199`) | Note |
|---|---|---|---|
| Plan §Task 20 spec anchor | "§Projection helper rewrites — poll() callsite (spec lines ~1936-1964)" | §Projection helper rewrites at `design.md:1888-1988` (poll callsite at `:1936-1964`) + §Internal abort coordination at `design.md:347-440` | Plan anchor is valid (section exists at `:1888`, poll callsite at `:1936`); also read §Internal abort coordination for CAS/coordination semantics |
| Plan §Task 20 test fixtures | `delegation_controller_fixture`, `pending_request_store_factory`, `resolution_registry_spy` | Non-existent — package uses `_build_controller` + `tmp_path` + explicit import from `test_delegation_controller.py` | Plan placeholder names must not appear in tests |
| Plan §Task 20 `poll()` line range | `delegation_controller.py:901-945` | `delegation_controller.py:1804-1846` | Line numbers shifted by Tasks 15-19 insertions |

## Live Anchors

| Anchor | Path | Line(s) | Content |
|---|---|---|---|
| `poll()` method def | `delegation_controller.py` | `:1804` | `def poll(self, *, job_id: str) -> DelegationPollResult \| PollRejectedResponse:` |
| Unguarded projection call | `delegation_controller.py` | `:1826-1828` | `pending_escalation = None` / `if refreshed.status == "needs_escalation":` / `pending_escalation = self._project_pending_escalation(refreshed)` |
| `_project_pending_escalation` def | `delegation_controller.py` | `:1746-1766` | Pure helper; re-raises `UnknownKindInEscalationProjection` per docstring `:1752` |
| `_project_request_to_view` raise site | `delegation_controller.py` | `:1732-1738` | Raises for `request.kind not in _ESCALATABLE_REQUEST_KINDS` |
| `UnknownKindInEscalationProjection` | `delegation_controller.py` | `:200-210` | Module-scope exception class; no import needed |
| `start()` catch precedent | `delegation_controller.py` | `:788-813` | `except UnknownKindInEscalationProjection as exc:` → log critical → `signal_internal_abort` → raise `DelegationStartError` |
| `signal_internal_abort` | `resolution_registry.py` | `:311-327` | CAS: `awaiting → aborted` (wakes worker with `InternalAbort`); idempotent no-op for other states |
| `self._registry` init | `delegation_controller.py` | `:392` | `self._registry: ResolutionRegistry = ResolutionRegistry()` in `__init__`; available to all controller methods |
| `DelegationPollResult` construction | `delegation_controller.py` | `:1841-1846` | Downstream of projection; `pending_escalation=None` is the default |
| Worker-side abort test | `test_handler_branches_integration.py` | `:759-817` | Covers `InternalAbort(reason="unknown_kind_in_escalation_projection")` → `record_internal_abort` → sentinel path |
| Normal-kind poll regression test | `test_delegation_controller.py` | `:2665-2681` | `test_poll_needs_escalation_projects_pending_request_without_raw_ids` — must not regress |
| `_build_controller` (test infra) | `test_delegation_controller.py` | `:206` | Returns 8-tuple; cross-imported by sibling test files |
| `_FakeSession` (test infra) | `test_delegation_controller.py` | imported at `test_handler_branches_integration.py:44-47` | Established cross-import pattern |

## Locks

| # | Lock | Rationale |
|---|---|---|
| L1 | `poll()` catches ONLY `UnknownKindInEscalationProjection`. No generic `except Exception`. | Narrow catch per helper docstring at `delegation_controller.py:1749-1756` and spec §Projection helper rewrites at `design.md:1892`: "each callsite owns its own catch-and-signal semantics." Generic catch would mask other bugs. |
| L2 | `pending_escalation=None` from `_project_pending_escalation` is legitimate (terminal, unparked, tombstone, non-pending). The catch block must NOT fire for these — they return `None`, not raise. | `_project_pending_escalation` at `:1759-1765` returns `None` for 4 guard states before reaching `_project_request_to_view`. |
| L3 | On catch: (1) `signal_internal_abort(...)` — capture return as `abort_signaled`; (2) `logger.critical(...)` with `job_id`, `request_id`, `cause`, `abort_signaled`; (3) set `pending_escalation = None`. Signal before log so the log records the CAS outcome (spec §436: "they log the return value"; §1978: Branch B's "only artifact is a log line recording the `False` return"). | Spec §439: "poll() returns DelegationPollResult(pending_escalation=None, ...) regardless of the signal's return." |
| L4 | `signal_internal_abort` return value MUST be logged but MUST NOT branch the response shape. `abort_signaled` appears only in `logger.critical` extra, not in any conditional. | Spec §436: CAS race with operator's `decide()` is honest concurrency; poll response is fixed. Return value is diagnostic only (Branch A vs Branch B evidence). |
| L5 | Preserve existing normal-kind poll projection test at `test_delegation_controller.py:2665`. | Regression guard; confirms the catch doesn't interfere with legitimate projections. |
| L6 | Tests use `_build_controller` + `tmp_path` + module-local helpers. Import from `test_delegation_controller.py` per established cross-import pattern. No plan-placeholder fixture names. | Package convention per W4 (Tasks 14-19). |
| L7 | Existing worker-side test at `test_handler_branches_integration.py:759` is supporting coverage. The poll callsite catch needs its OWN test proving `poll()` returns `DelegationPollResult(pending_escalation=None)` after catching the exception. | Worker-side test proves the abort delivery; poll-side test proves the callsite response shape. |
| L8 | No modifications to `_project_pending_escalation`, `_project_request_to_view`, or any other helper. Callsite-only change. | Helpers stay pure per helper docstring at `delegation_controller.py:1754-1756`: "The helper never calls signal_internal_abort and never logs critical errors; those concerns live at callsites." Also spec §Projection helper rewrites at `design.md:1892`: "Helper purity means a future packet that adds a new projection callsite can choose its own reason." |
| L9 | No `discard()`, `contracts.md`, or `_finalize_turn` edits. | Tasks 21/22 boundary. No coupling: `discard()` at `:2290` and `contracts.md` are independent of `poll()`'s projection path. |

## Watchpoints

| # | Watchpoint | What to check |
|---|---|---|
| W1 | `refreshed` at `:1825` is the re-fetched job (post-artifact-materialization). Use `refreshed.parked_request_id` in the signal, not `job.parked_request_id` (the pre-materialization fetch at `:1805`). | Both should be identical (artifact materialization doesn't mutate `parked_request_id`), but `refreshed` is the authority for the projection path. |
| W2 | `DelegationPollResult` construction at `:1841-1846` must remain downstream of the catch. `pending_escalation` is initialized to `None` at `:1826`. | The catch's `pending_escalation = None` is the same as the initialization — explicit for clarity. |
| W3 | Existing poll tests (`:2624-2800`) must not regress. Suite count must be ≥ 1040 + N new. | Full suite run required. |
| W4 | The `detail` field assembly at `:1830-1839` runs AFTER the projection block. A caught exception must not skip the detail logic. | The try/except is scoped to the projection call only, not the full post-refresh block. |
| W5 | `refreshed.parked_request_id` is structurally non-None inside the except block. `_project_pending_escalation` returns `None` before reaching `_project_request_to_view` when `parked_request_id is None` (`:1761-1762`). A defense-in-depth `if` guard is acceptable but not required. | Implementer discretion per user-specified lock list. |

## Test Strategy

Two test categories, both synchronous — no async timing, no race windows:

**Category 1: Poll callsite catch (NEW tests)**

| Test | Setup | Assertion |
|---|---|---|
| `test_poll_returns_null_escalation_on_unknown_kind_parked_request` | Job with `needs_escalation` + `parked_request_id` → `PendingServerRequest(kind="unknown", status="pending")` + spy on `_registry.signal_internal_abort` | `isinstance(result, DelegationPollResult)` + `result.pending_escalation is None` + `signal_internal_abort` called once + `caplog` CRITICAL with `abort_signaled=True` |
| `test_poll_returns_null_escalation_even_when_signal_returns_false` | Same setup; mock `signal_internal_abort` returns `False` (operator won CAS) | Result shape identical: `DelegationPollResult(pending_escalation=None)` + `caplog` CRITICAL with `abort_signaled=False` — proves L4 (logged but not branched) |
| `test_poll_normal_kind_still_projects_escalation` | Job with `needs_escalation` + `parked_request_id` → `PendingServerRequest(kind="command_approval", status="pending")` | `result.pending_escalation is not None` + `result.pending_escalation.kind == "command_approval"` |

**Category 2: Regression (EXISTING test untouched)**
- `test_poll_needs_escalation_projects_pending_request_without_raw_ids` at `:2665` — L5 watchpoint.

**Proof of no-brittle-timing:** all tests seed store state directly, call `poll()` synchronously, inspect the result. No worker threads, no `registry.wait()`, no sleep.

## Acceptance Criteria

| Check | Expected |
|---|---|
| `poll()` with unknown-kind parked request returns `DelegationPollResult(pending_escalation=None)` | Pass |
| `signal_internal_abort` called with `reason="unknown_kind_in_escalation_projection"` | Pass |
| `signal_internal_abort` return value does not affect result shape | Pass |
| CRITICAL log records `abort_signaled=True` (abort-win) and `abort_signaled=False` (CAS-loss) | Pass (Tests 1 + 2) |
| `poll()` with normal-kind parked request returns projected view | Pass (regression) |
| Full suite ≥ 1040 + N new | Pass |
| `_project_pending_escalation` body diff = 0 lines | L8 |
| `discard()` diff = 0 lines | L9 |
| `contracts.md` diff = 0 lines | L9 |

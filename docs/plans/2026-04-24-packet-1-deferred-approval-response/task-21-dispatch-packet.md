# Task 21 Dispatch Packet — `discard()` gate expansion (admit canceled)

**Task:** Phase H Task 21
**Branch:** `feature/delegate-deferred-approval-response`
**HEAD:** `47628f20`
**Convergence map:** `task-21-convergence-map.md` (binding)

---

## Mission

Expand the `_discardable` gate in `discard()` at `delegation_controller.py:2324-2326` to admit `status="canceled"` alongside `"failed"` and `"unknown"` when `promotion_state is None`. Update the method docstring. Write 3 integration tests proving the gate expansion, the rejection of post-mutation promotion states, and the audit event.

## Authority Sources

Read BEFORE writing any code. Pre-read guard: if a source contradicts the convergence map, report BLOCKED.

| # | Source | Path | What to read |
|---|---|---|---|
| 1 | **Convergence map** (binding) | `docs/plans/2026-04-24-packet-1-deferred-approval-response/task-21-convergence-map.md` | All locks L1-L7, watchpoints W1-W3, test strategy, acceptance criteria |
| 2 | **Spec §discard() gate row** | `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1377` | Gate expansion requirement and rationale |
| 3 | **Spec §discard() test requirement** | `design.md:1408` | Test shape: null promotion → success, applied promotion → rejection, audit event |
| 4 | **Live `discard()` method** | `packages/plugins/codex-collaboration/server/delegation_controller.py:2309-2357` | Full method body — the production change site |
| 5 | **Existing discard tests** | `test_delegation_controller.py:3307-3393` | Pattern reference for `_build_promote_scenario` + `update_status_and_promotion` |

## Production Change

**File:** `packages/plugins/codex-collaboration/server/delegation_controller.py`

### Change 1: Docstring update (`:2312-2314`)

**Current:**
```python
        """Discard a delegation job without promoting.

        Allowed when promotion_state in (pending, prechecks_failed), or when
        status in (failed, unknown) and promotion_state is None (pre-mutation).
        Post-mutation states (applied, rollback_needed) are never discardable.
        """
```

**Replacement:**
```python
        """Discard a delegation job without promoting.

        Allowed when promotion_state in (pending, prechecks_failed), or when
        status in (failed, unknown, canceled) and promotion_state is None
        (pre-mutation). Post-mutation states (applied, rollback_needed) are
        never discardable.
        """
```

### Change 2: Gate tuple (`:2324-2326`)

**Current:**
```python
        _discardable = job.promotion_state in ("pending", "prechecks_failed") or (
            job.status in ("failed", "unknown") and job.promotion_state is None
        )
```

**Replacement:**
```python
        _discardable = job.promotion_state in ("pending", "prechecks_failed") or (
            job.status in ("failed", "unknown", "canceled")
            and job.promotion_state is None
        )
```

## Test Obligations

**New file:** `packages/plugins/codex-collaboration/tests/test_discard_canceled_integration.py`

Use the established cross-import pattern:
```python
from tests.test_delegation_controller import (  # type: ignore[import]
    _build_promote_scenario,
)
```

### Test 1: `test_discard_canceled_with_null_promotion_state_succeeds`

Setup:
1. `_build_promote_scenario(tmp_path)` → get controller, job_store, journal, repo, job_id, hash, callback
2. `job_store.update_status_and_promotion(job_id, status="canceled", promotion_state=None)`

Execute: `result = controller.discard(job_id=job_id)`

Assert:
- `isinstance(result, DiscardResult)`
- `result.job.promotion_state == "discarded"`
- Persisted: `job_store.get(job_id).promotion_state == "discarded"`

### Test 2: `test_discard_canceled_with_applied_promotion_state_rejects`

Setup: Same as Test 1, but `promotion_state="applied"`.

Assert:
- `isinstance(result, DiscardRejectedResponse)`
- `result.reason == "job_not_discardable"`

### Test 3: `test_discard_canceled_writes_audit_event`

Setup: Same as Test 1 (canceled + null promotion_state). Execute discard.

Assert:
- Read `journal.plugin_data_path / "audit" / "events.jsonl"` (the public path; do NOT use `journal._audit_path`)
- Parse lines as JSON
- Find at least one record where `action == "discard"` and `job_id` matches

## Reporting Contract

**DONE template:**
```
DONE at <SHA>.
Suite: <passed>/<skipped>/<failed> in <seconds>.
Verified:
  rg '"canceled"' delegation_controller.py | grep _discardable context → "canceled" in status tuple
  git diff 47628f20..HEAD -- delegation_controller.py — only hunks in `def discard` (docstring + gate)
  git diff 47628f20..HEAD -- contracts.md → empty (no changes)
  Existing discard tests at test_delegation_controller.py:3307-3393 pass (L7)
```

**BLOCKED template:**
```
BLOCKED on <lock/watchpoint #>.
Question: <what needs adjudication>
Evidence: <file:line, what was observed, what conflicts>
```

## Boundaries (explicit prohibitions)

1. Do NOT modify `poll()`, `start()`, or `decide()` — L4
2. Do NOT modify `_finalize_turn` — L4
3. Do NOT modify `_project_pending_escalation` or `_project_request_to_view` — L4
4. Do NOT modify `contracts.md` — L6
5. Do NOT modify existing discard tests — L7
6. Do NOT use plan-placeholder fixture names (`delegation_controller_fixture`, `simple_job_factory`, `audit_event_spy`) — L3
7. Do NOT add new exception classes or model types
8. Do NOT change the `promotion_state in ("pending", "prechecks_failed")` branch — L2
9. Do NOT change the `promotion_state is None` predicate — L2

## Begin

1. Read convergence map (source 1)
2. Read spec §discard() gate row at `design.md:1377` (source 2)
3. Read live `discard()` at `delegation_controller.py:2309-2357` (source 4)
4. Read existing discard tests at `test_delegation_controller.py:3307-3393` (source 5)
5. Implement the production change (docstring + gate tuple)
6. Write test file with 3 tests
7. Run: `uv run --package codex-collaboration ruff format packages/plugins/codex-collaboration/tests/test_discard_canceled_integration.py`
8. Run: `bash -c 'set -o pipefail; uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/ -x 2>&1 | tail -20'`
9. Report per DONE/BLOCKED template

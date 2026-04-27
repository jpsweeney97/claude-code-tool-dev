# Task 20 Dispatch Packet — `poll()` UnknownKindInEscalationProjection Catch

**Task:** Phase H Task 20
**Branch:** `feature/delegate-deferred-approval-response`
**HEAD:** `c53a5199`
**Convergence map:** `task-20-convergence-map.md` (binding)

---

## Mission

Add a `try/except UnknownKindInEscalationProjection` around the `_project_pending_escalation` call in `poll()` at `delegation_controller.py:1828`. On catch: log critical, call `self._registry.signal_internal_abort(...)`, set `pending_escalation = None`. Return the normal `DelegationPollResult` with null escalation. Write tests proving the callsite catch.

This is the poll-side complement to the `start()` catch at `:788-813`. The `start()` catch raises `DelegationStartError`; the `poll()` catch returns `DelegationPollResult(pending_escalation=None)` because poll is observational, not transactional.

## Authority Sources

Read BEFORE writing any code. Pre-read guard: if a source contradicts the convergence map, report BLOCKED.

| # | Source | Path | What to read |
|---|---|---|---|
| 1 | **Convergence map** (binding) | `docs/plans/2026-04-24-packet-1-deferred-approval-response/task-20-convergence-map.md` | All locks L1-L9, watchpoints W1-W5, test strategy, acceptance criteria |
| 2a | **Spec §Projection helper rewrites** | `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1888-1988` | Poll callsite mechanics at `:1936-1964`. Helper purity contract at `:1892`. Observation sequence (Branch A/B) at `:1967-1981`. |
| 2b | **Spec §Internal abort coordination** | `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:347-440` | CAS race semantics at `:436`. Worker abort sequence at `:395-422`. Poll triggers at `:352`. |
| 3 | **Live `poll()` method** | `packages/plugins/codex-collaboration/server/delegation_controller.py:1804-1846` | Full method body — the production change site |
| 4 | **Live `_project_pending_escalation`** | `delegation_controller.py:1746-1766` | Pure helper; re-raises exception. DO NOT modify (L8). |
| 5 | **Live `start()` catch precedent** | `delegation_controller.py:788-813` | Pattern reference for log structure + signal + response. Poll catch DIFFERS: no raise, returns `DelegationPollResult` instead. |

## Production Change

**File:** `packages/plugins/codex-collaboration/server/delegation_controller.py`

**Location:** `:1826-1828`

**Current code (3 lines):**
```python
        pending_escalation = None
        if refreshed.status == "needs_escalation":
            pending_escalation = self._project_pending_escalation(refreshed)
```

**Replacement:**
```python
        pending_escalation = None
        if refreshed.status == "needs_escalation":
            try:
                pending_escalation = self._project_pending_escalation(refreshed)
            except UnknownKindInEscalationProjection as exc:
                abort_signaled = False
                if refreshed.parked_request_id is not None:
                    abort_signaled = self._registry.signal_internal_abort(
                        refreshed.parked_request_id,
                        reason="unknown_kind_in_escalation_projection",
                    )
                logger.critical(
                    "delegation.poll: unknown-kind in escalation projection; "
                    "signaled worker-coordinated internal abort",
                    extra={
                        "job_id": refreshed.job_id,
                        "request_id": refreshed.parked_request_id,
                        "cause": str(exc),
                        "abort_signaled": abort_signaled,
                    },
                )
                pending_escalation = None
```

**Constraints (from convergence map):**
- Catch ONLY `UnknownKindInEscalationProjection` (L1). No `except Exception`.
- `if refreshed.parked_request_id is not None:` guard is defense-in-depth (W5 — structurally redundant but acceptable).
- Do NOT branch the result shape on `signal_internal_abort`'s return value (L4).
- `pending_escalation = None` after the signal is explicit even though it matches the initialization value (clarity over cleverness).
- `detail` assembly at `:1830-1839` must remain downstream of this block (W4). Do not move it inside the try.
- `UnknownKindInEscalationProjection` is defined at `:200` in the same module — no new import needed.

## Test Obligations

**New file:** `packages/plugins/codex-collaboration/tests/test_poll_projection_guard_integration.py`

Use the established cross-import pattern:
```python
from tests.test_delegation_controller import (  # type: ignore[import]
    _build_controller,
)
```

Additional imports as needed from `server.models`, `server.resolution_registry`, `server.pending_request_store`, etc. Use `tmp_path` fixture. Use `monkeypatch` for registry spy injection.

### Test 1: `test_poll_returns_null_escalation_on_unknown_kind_parked_request`

Setup (direct-seed — `start()` cannot produce `kind="unknown"` + `needs_escalation` under Task 17's L11 carve-out):
1. `_build_controller(tmp_path)` → get controller, job_store, pending_request_store, etc.
2. Direct-seed a job in `needs_escalation` with `parked_request_id` set. Consult `test_handler_branches_integration.py:759-817` for the pattern (`_make_running_job_with_lineage` + `job_store.update_status` + `pending_request_store.create`).
3. Ensure the pending request store has a `PendingServerRequest(kind="unknown", status="pending")` for that request_id
4. Monkeypatch `controller._registry` with a mock that spies on `signal_internal_abort` (return `True`)

Execute: `result = controller.poll(job_id=...)`

Assert:
- `isinstance(result, DelegationPollResult)`
- `result.pending_escalation is None`
- `result.job.status == "needs_escalation"` (poll does not mutate job status)
- `mock_registry.signal_internal_abort.assert_called_once_with("request_id", reason="unknown_kind_in_escalation_projection")`
- `caplog` contains one CRITICAL record matching `"delegation.poll: unknown-kind in escalation projection"` with extra fields `job_id`, `request_id`, `cause`, and `abort_signaled=True`

### Test 2: `test_poll_returns_null_escalation_even_when_signal_returns_false`

Same setup as Test 1, but `signal_internal_abort.return_value = False` (simulates operator `decide()` winning the CAS).

Assert:
- Result shape identical: `DelegationPollResult(pending_escalation=None)`
- Proves L4: response not conditioned on signal return
- `caplog` contains one CRITICAL record with `abort_signaled=False` — proves the CAS-loss branch is observable (spec §1978: Branch B's "only artifact is a log line recording the `False` return")

### Test 3: `test_poll_normal_kind_still_projects_escalation`

Setup: Job with `needs_escalation` + `parked_request_id` pointing to a `PendingServerRequest(kind="command_approval", status="pending")`.

Assert:
- `result.pending_escalation is not None`
- `result.pending_escalation.kind == "command_approval"`
- `result.pending_escalation.request_id` matches
- No `signal_internal_abort` call (not on the catch path)

**Implementation note for seeding store state:** The cleanest approach is to go through `controller.start()` to create a naturally parked job (the start path sets up all store state correctly), then verify the poll projection works. For the unknown-kind test, direct store manipulation is needed because `start()` won't produce a `needs_escalation` job with a `kind="unknown"` parked request under current code (Task 17's L11 carve-out terminalizes those). Consult the handler branches test at `test_handler_branches_integration.py:759-817` for the direct-seeding pattern (uses `_make_running_job_with_lineage` + `job_store.update_status` + `pending_request_store.create`).

## Reporting Contract

**DONE template:**
```
DONE at <SHA>.
Suite: <passed>/<skipped>/<failed> in <seconds>.
Verified:
  rg "unknown_kind_in_escalation_projection" delegation_controller.py → 1 match (poll callsite)
  rg "unknown_kind_in_escalation_projection" test_poll_projection_guard_integration.py → ≥ 2 matches
  git diff c53a5199..HEAD -- delegation_controller.py — no hunks inside `def _project_pending_escalation` or `def _project_request_to_view` (verify by visual diff review; the only hunks should be inside `def poll`)
  git diff c53a5199..HEAD -- delegation_controller.py | grep "def discard" → 0 changes
  git diff c53a5199..HEAD -- contracts.md → empty (no changes)
  Existing test at test_delegation_controller.py:2665 passes (L5)
  Existing test at test_handler_branches_integration.py:759 passes (L7)
```

**BLOCKED template:**
```
BLOCKED on <lock/watchpoint #>.
Question: <what needs adjudication>
Evidence: <file:line, what was observed, what conflicts>
```

## Boundaries (explicit prohibitions)

1. Do NOT modify `_project_pending_escalation` body (`:1746-1766`) — L8
2. Do NOT modify `_project_request_to_view` body (`:1720-1744`) — L8
3. Do NOT modify `_finalize_turn` — L9
4. Do NOT modify `discard()` — L9
5. Do NOT modify `contracts.md` — L9
6. Do NOT modify `start()` or `decide()` body
7. Do NOT add new exception classes
8. Do NOT add new model types
9. Do NOT use plan-placeholder fixture names (`delegation_controller_fixture`, `resolution_registry_spy`, etc.) — L6
10. Do NOT modify the worker-side test at `test_handler_branches_integration.py:759-817` — L7
11. Do NOT add imports to `delegation_controller.py` — `UnknownKindInEscalationProjection` is already at module scope (`:200`)

## Begin

1. Read convergence map (source 1)
2. Read spec §Projection helper rewrites at `design.md:1888-1988` (source 2a) and §Internal abort coordination at `:347-440` (source 2b)
3. Read live `poll()` at `delegation_controller.py:1804-1846` (source 3)
4. Read `_project_pending_escalation` at `:1746-1766` (source 4)
5. Read `start()` catch precedent at `:788-813` (source 5)
6. Implement the production change
7. Write test file with 3 tests
8. Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/ -x 2>&1 | tail -20`
9. Report per DONE/BLOCKED template

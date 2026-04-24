# Packet 1 — Phase G: Public API

**Parent plan:** [manifest](../2026-04-24-packet-1-deferred-approval-response.md)
**Tasks:** 17–18
**Scope:** `start()` rewrite — `wait_for_parked` with all 5 `ParkedCaptureResult` variants handled. `decide()` rewrite — reservation context manager (reserve → journal intent → commit) + new 3-field return shape.
**Landing invariant:** `decide()` and `start()` honor the new async contract; end-to-end happy-path, timeout, dispatch-failure, and internal-abort paths all pass integration tests.
**Note:** Integration-test bodies in this phase are `pass` stubs under concrete docstrings. See manifest §Pre-Execution Notes for implementer contract.

---

## Task 17: `start()` rewrite — wait_for_parked + 5 ParkedCaptureResult variants

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (rewrite `start()`)
- Test: `packages/plugins/codex-collaboration/tests/test_delegate_start_async_integration.py` (new)

**Spec anchor:** §Capture-ready handshake (lines ~659-910). §DelegationStartError reasons (lines ~622-657).

- [ ] **Step 17.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_delegate_start_async_integration.py`:

```python
"""Packet 1: start() under the async-decide model — 5 ParkedCaptureResult variants."""

from __future__ import annotations

import pytest

from server.delegation_controller import (
    DelegationStartError,
)
from server.models import (
    DelegationEscalation,
    DelegationJob,
)


def test_start_returns_escalation_on_parked(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """Happy path: worker parks on command_approval → announce_parked →
    start() returns DelegationEscalation with projection of the parked
    request."""
    pass


def test_start_returns_plain_job_for_turn_completed_without_capture(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """Analytical delegation: no server request emitted; turn completes.
    start() returns DelegationJob(status='completed')."""
    pass


def test_start_returns_plain_job_for_unknown_kind_parse_failure(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """Parse failure → TurnTerminalWithoutEscalation signal →
    start() returns DelegationJob(status='unknown'). Does NOT raise."""
    pass


def test_start_returns_running_job_on_start_wait_elapsed(
    delegation_controller_fixture, app_server_runtime_stub, monkeypatch
) -> None:
    """Budget elapses without any signal → start() returns
    DelegationJob(status='running'). Does NOT raise."""
    monkeypatch.setattr(
        "server.delegation_controller.START_OUTCOME_WAIT_SECONDS",
        0.1,
    )
    # Arrange a worker that will signal LATER; force budget to elapse.
    pass


def test_start_raises_for_worker_failed_before_capture(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """Worker raises unhandled exception before any capture → start()
    raises DelegationStartError(reason='worker_failed_before_capture')."""
    pass


def test_start_raises_with_reason_preservation_for_unknown_kind_interrupt(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """Unknown-kind interrupt transport failure → worker re-raises as
    DelegationStartError(reason='unknown_kind_interrupt_transport_failure') →
    start()'s WorkerFailed handler preserves the reason (does NOT
    collapse to 'worker_failed_before_capture')."""
    pass


def test_start_signals_internal_abort_on_parked_projection_null(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """Parked signal received, but _project_pending_escalation returns
    None (e.g., store race) → start() calls signal_internal_abort
    (reason='parked_projection_invariant_violation') → raises
    DelegationStartError(reason=same)."""
    pass


def test_start_signals_internal_abort_on_parked_projection_raise(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """Parked signal received, but _project_pending_escalation raises
    UnknownKindInEscalationProjection → start() calls signal_internal_abort
    (reason='parked_projection_invariant_violation', same BROAD reason) →
    raises DelegationStartError(reason=same)."""
    pass
```

- [ ] **Step 17.2: Run failing tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegate_start_async_integration.py -v
```

Expected: FAIL — start() is still synchronous.

- [ ] **Step 17.3: Rewrite `start()` to use the worker model**

Edit `DelegationController.start` at `delegation_controller.py` (around `:608-625`). The committed-start phase (worktree, runtime, journal phases 1-3) is unchanged; only the turn-dispatch section changes. Replace the final block:

```python
# Previous (synchronous):
# prompt_text = build_execution_turn_text(...)
# return self._execute_live_turn(
#     job_id=job_id,
#     collaboration_id=collaboration_id,
#     runtime_id=runtime_id,
#     worktree_path=worktree_path,
#     prompt_text=prompt_text,
# )

# New (async via worker + capture-ready handshake):
prompt_text = build_execution_turn_text(
    objective=objective,
    worktree_path=str(worktree_path),
)

from .worker_runner import spawn_worker

worker_thread = spawn_worker(
    controller=self,
    registry=self._registry,
    job_id=job_id,
    collaboration_id=collaboration_id,
    runtime_id=runtime_id,
    worktree_path=worktree_path,
    prompt_text=prompt_text,
)

outcome = self._registry.wait_for_parked(
    job_id, timeout_seconds=START_OUTCOME_WAIT_SECONDS
)

return self._dispatch_parked_capture_outcome(
    outcome=outcome,
    job_id=job_id,
    collaboration_id=collaboration_id,
)
```

Add a constant `START_OUTCOME_WAIT_SECONDS = 30` near the top of the module.

Add the dispatcher helper on `DelegationController`:

```python
def _dispatch_parked_capture_outcome(
    self,
    *,
    outcome: ParkedCaptureResult,
    job_id: str,
    collaboration_id: str,
) -> DelegationJob | DelegationEscalation:
    """Translate the ParkedCaptureResult into a start() return or raise."""
    match outcome:
        case Parked(request_id=request_id):
            job = self._job_store.get(job_id)
            assert job is not None, (
                f"start(): Parked outcome but job_id={job_id!r} not in store"
            )
            try:
                escalation_view = self._project_pending_escalation(job)
            except UnknownKindInEscalationProjection as exc:
                logger.critical(
                    "delegation.start: unknown-kind in parked projection",
                    extra={"job_id": job_id, "request_id": request_id, "cause": str(exc)},
                )
                self._registry.signal_internal_abort(
                    request_id, reason="parked_projection_invariant_violation"
                )
                raise DelegationStartError(
                    reason="parked_projection_invariant_violation",
                    cause=None,
                )
            if escalation_view is None:
                logger.critical(
                    "delegation.start: Parked signal but null escalation projection",
                    extra={"job_id": job_id, "request_id": request_id},
                )
                self._registry.signal_internal_abort(
                    request_id, reason="parked_projection_invariant_violation"
                )
                raise DelegationStartError(
                    reason="parked_projection_invariant_violation",
                    cause=None,
                )
            return DelegationEscalation(
                job=job,
                pending_escalation=escalation_view,
                agent_context=None,  # deferred: worker still inside turn
            )
        case TurnCompletedWithoutCapture():
            return self._job_store.get(job_id)
        case TurnTerminalWithoutEscalation(job_status, reason, request_id):
            return self._job_store.get(job_id)
        case WorkerFailed(error=exc):
            if isinstance(exc, DelegationStartError) and exc.reason:
                # Reason-preservation rule.
                raise exc
            raise DelegationStartError(
                reason="worker_failed_before_capture",
                cause=exc,
            )
        case StartWaitElapsed():
            logger.warning(
                "delegation.start: start-wait budget elapsed; returning running",
                extra={"job_id": job_id, "budget_seconds": START_OUTCOME_WAIT_SECONDS},
            )
            return self._job_store.get(job_id)
```

Imports to add to `delegation_controller.py`:

```python
from .resolution_registry import (
    DecisionResolution,
    InternalAbort,
    Parked,
    ParkedCaptureResult,
    ResolutionRegistry,
    StartWaitElapsed,
    TurnCompletedWithoutCapture,
    TurnTerminalWithoutEscalation,
    WorkerFailed,
)
```

- [ ] **Step 17.4: Run integration tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegate_start_async_integration.py -v
```

Expected: PASS as test bodies are fleshed out.

- [ ] **Step 17.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegate_start_async_integration.py
git commit -m "$(cat <<'EOF'
feat(delegate): rewrite start() with capture-ready handshake (T-20260423-02 Task 17)

start() now spawns a worker thread and blocks on
ResolutionRegistry.wait_for_parked with START_OUTCOME_WAIT_SECONDS budget.
Five ParkedCaptureResult variants are dispatched:
  - Parked → DelegationEscalation (with projection; invariant violation raises)
  - TurnCompletedWithoutCapture → DelegationJob(status="completed")
  - TurnTerminalWithoutEscalation → DelegationJob(status="unknown")
  - WorkerFailed → DelegationStartError with reason-preservation rule
    (explicit reason from a worker-raised DelegationStartError flows through
    intact; fallback is "worker_failed_before_capture")
  - StartWaitElapsed → DelegationJob(status="running") with warning log

The parked-projection-invariant-violation branch signals the worker via
signal_internal_abort (broad reason covering both null-return and raised-
exception sub-cases) and raises on the main thread.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 18: `decide()` rewrite — reservation context manager + new return

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (rewrite `decide()`)
- Test: `packages/plugins/codex-collaboration/tests/test_delegate_decide_async_integration.py` (new)

**Spec anchor:** §Transactional registry protocol (lines ~250-345).

- [ ] **Step 18.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_delegate_decide_async_integration.py`:

```python
"""Packet 1: decide() under the async-decide model."""

from __future__ import annotations

from server.models import DelegationDecisionResult, DecisionRejectedResponse


def test_decide_returns_3_field_result_on_success(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """decide(approve) on a parked command_approval request returns
    DelegationDecisionResult(decision_accepted=True, job_id=..., request_id=...)."""
    pass


def test_decide_wakes_worker(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """decide() commits the reservation; worker unblocks from registry.wait."""
    pass


def test_decide_twice_second_returns_request_already_decided(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """Second decide on same request → reservation CAS fails →
    DecisionRejectedResponse(reason='request_already_decided')."""
    pass


def test_decide_on_unreserved_entry_rejects(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """decide() on a request_id that's not registered →
    request_already_decided (reserve returns None)."""
    pass


def test_decide_writes_intent_before_commit_signal(
    delegation_controller_fixture, app_server_runtime_stub, journal_spy
) -> None:
    """Journal intent write happens BEFORE registry.commit_signal."""
    pass


def test_decide_audit_event_is_post_commit(
    delegation_controller_fixture, app_server_runtime_stub, audit_event_spy
) -> None:
    """append_audit_event fires AFTER commit_signal returns. Audit failure
    is logged, does NOT roll back."""
    pass


def test_decide_rejects_non_awaiting_job(
    delegation_controller_fixture, app_server_runtime_stub
) -> None:
    """decide() when job.status != 'needs_escalation' rejects with
    job_not_awaiting_decision."""
    pass
```

- [ ] **Step 18.2: Run failing tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegate_decide_async_integration.py -v
```

Expected: FAIL — decide() doesn't use the registry yet.

- [ ] **Step 18.3: Rewrite `decide()`**

Edit `DelegationController.decide` at `delegation_controller.py:1551-<end-of-function>`. The new logic:

```python
def decide(
    self,
    *,
    job_id: str,
    request_id: str,
    decision: DecisionAction | str,
    answers: dict[str, tuple[str, ...]] | None = None,
) -> DelegationDecisionResult | DecisionRejectedResponse:
    if decision not in ("approve", "deny"):
        return self._reject_decision(
            reason="invalid_decision",
            detail=f"Delegation decide failed: invalid decision. Got: {decision!r:.100}",
            job_id=job_id,
            request_id=request_id,
        )
    job = self._job_store.get(job_id)
    if job is None:
        return self._reject_decision(
            reason="job_not_found",
            detail=f"Delegation decide failed: job not found. Got: {job_id!r:.100}",
            job_id=job_id,
            request_id=request_id,
        )
    if job.status != "needs_escalation":
        return self._reject_decision(
            reason="job_not_awaiting_decision",
            detail=f"Delegation decide failed: job not awaiting decision. Got: status={job.status!r:.100}",
            job_id=job_id,
            request_id=request_id,
        )
    request = self._pending_request_store.get(request_id)
    if request is None:
        return self._reject_decision(
            reason="request_not_found",
            detail=f"Delegation decide failed: request not found. Got: {request_id!r:.100}",
            job_id=job_id,
            request_id=request_id,
        )
    if request.collaboration_id != job.collaboration_id:
        return self._reject_decision(
            reason="request_job_mismatch",
            detail=f"Delegation decide failed: request does not belong to job. Got: request_id={request_id!r:.100}",
            job_id=job_id,
            request_id=request_id,
        )

    # Build response payload (maps decision + answers + request.kind → payload).
    payload = self._build_response_payload(decision, answers, request)
    resolution = DecisionResolution(
        payload={"resolution_action": decision, "response_payload": payload},
        kind=request.kind,
    )

    # Two-phase reservation protocol.
    token = self._registry.reserve(request_id, resolution)
    if token is None:
        return self._reject_decision(
            reason="request_already_decided",
            detail=f"Delegation decide failed: request was already decided. Got: {request_id!r:.100}",
            job_id=job_id,
            request_id=request_id,
        )

    try:
        # Write durable intent BEFORE commit_signal (IO-4 fsync).
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=f"approval_resolution:{job_id}:{request_id}",
                operation="approval_resolution",
                phase="intent",
                collaboration_id=job.collaboration_id,
                created_at=self._journal.timestamp(),
                repo_root=self._repo_root_for_journal(job_id),
                job_id=job_id,
                request_id=request_id,
                decision=decision,
            ),
            session_id=self._session_id,
        )
    except BaseException:
        # Intent failed — roll back the reservation so timer / retry can claim.
        self._registry.abort_reservation(token)
        raise

    # Commit: worker wakes here.
    self._registry.commit_signal(token)

    # Audit — post-commit, non-gating (IO-5).
    try:
        self._journal.append_audit_event(
            AuditEvent(
                event_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                actor="claude",
                action=decision,
                collaboration_id=job.collaboration_id,
                runtime_id=job.runtime_id,
                job_id=job_id,
                request_id=request_id,
            )
        )
    except Exception as exc:
        logger.warning("Audit event append failed post-commit: %s", exc)

    return DelegationDecisionResult(
        decision_accepted=True,
        job_id=job_id,
        request_id=request_id,
    )
```

Add the helper `_build_response_payload` (logic preserved from the previous decide implementation's payload-building section):

```python
def _build_response_payload(
    self,
    decision: DecisionAction | str,
    answers: dict[str, tuple[str, ...]] | None,
    request: PendingServerRequest,
) -> dict[str, Any]:
    """Construct the App Server response payload for this decision+kind."""
    if request.kind in ("command_approval", "file_change"):
        return {"decision": "accept" if decision == "approve" else "reject"}
    if request.kind == "request_user_input":
        return {"answers": dict(answers or {})}
    raise RuntimeError(
        f"_build_response_payload: unexpected kind={request.kind!r}"
    )
```

Retire the `_decided_request_ids` set and the `decision == "deny" and answers` check — the reservation CAS replaces both (the CAS is the single authority for "already decided" and answers-compatibility is kind-specific, handled in `_build_response_payload`). If other tests still depend on `_decided_request_ids`, update them.

- [ ] **Step 18.4: Run integration tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegate_decide_async_integration.py -v
```

Expected: PASS.

- [ ] **Step 18.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegate_decide_async_integration.py
git commit -m "$(cat <<'EOF'
feat(delegate): rewrite decide() with reservation two-phase protocol (T-20260423-02 Task 18)

decide() now performs the transactional reserve → journal intent →
commit_signal → audit sequence per spec §Transactional registry protocol.
On journal failure, abort_reservation rolls back the registry state so
the timer or a retry can claim the slot; on commit failure (impossible by
construction), the plugin crashes loudly. Audit is post-commit per IO-5
— failure is a warning log, never rolls back.

Return value is the new 3-field DelegationDecisionResult.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

**Phase G complete.** Public APIs are on the new contract. Phase H lands the finalizer terminal guard — the R13/R14 focal point — plus poll, discard, and contracts.

---


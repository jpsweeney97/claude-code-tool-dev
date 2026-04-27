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

## Phase G closeout (Tasks 17 + 18 landed)

> Detailed task narratives live in `carry-forward.md` under "From Phase G Task 17 + closeouts" and "From Phase G Task 18 + closeouts". This section is a compact pointer summary for plan-body readers.

**Phase G CLOSES** with the Task 18 closeout-docs commit on `feature/delegate-deferred-approval-response`. Branch is 7 commits ahead of `main` post-closeout-docs (3 from Task 17: feat `8dd15971` + fix `dc90c1d9` + docs `c5829049`; 3 from Task 18: feat `2606fb03` + fix `b8e7f9ce` + docs `<this commit>`; plus 1 docs from earlier in the chain). Suite: 1020 passed / 8 skipped (6 G18.1 + 2 F16.1) / 0 failed in 123.70s.

**Task 18 landed-code summary.**
- **feat `2606fb03`:** `decide()` rewrite — validate → `_build_response_payload(decision, answers, request)` → `DecisionResolution(payload, kind, action=decision)` → `reserve()` → narrow-try journal-intent (with `abort_reservation` rollback per L7b) → `commit_signal()` BARE per L14 → audit (post-commit, non-gating, action=decision per L7a) → return `DelegationDecisionResult(decision_accepted=True, ...)`. New `_build_response_payload` helper at `:2634-2679` implements the 6-row binding contract per spec §1667-1672 (`decline` not `reject`; empty-fallback for deny on RUI). 18 acceptance tests (15 names; 18 sub-cases under parametrization) in new `tests/test_delegate_decide_async_integration.py`. L11 deletes 3 obsolete CDFE tests; L12 reclassifies 6 finalizer-dependent tests to G18.1. Constant rename `_TASK_18_DECIDE_SIGNAL_REASON` → `_TASK_19_FINALIZER_GUARD_REASON` in both test files.
- **fix `b8e7f9ce` (Path 4):** worker payload dispatch contract correction (worker resume path read `resolution.payload.get("response_payload", {})` wrapper keys that don't exist in the new shape) + re-park PSR.create gate lift (`captured_request is None` gate at `:1029-1031` previously left re-parks registered in the resolution registry but absent from the PSR store, breaking `poll()` projection) + Round-7 regression test for the wire-shape contract end-to-end + CQ Minor #3 audit-log substring tightening. **W16 narrow adjudication:** authorized narrow fixes inside `_execute_live_turn` body for both correctness gaps; def signature unchanged; structural integrity of parkable-capture and resume sub-branches preserved.
- **closeout-docs `<this commit>`:** `carry-forward.md` updates (G17.1 closed, Mode A fully retired, F16.2 lineage annotated, G18.1 introduced verbatim, TT.1 promoted, RT.1 unchanged); `task-18-convergence-map.md` Round-7 addendum with explicit supersession markers preserving Round-6's "out-of-Task-18 carry-forward observations" framing as historical record; `task-18-dispatch-packet.md` staged as historical artifact; this Phase-G closeout pointer.

**Bucket B disposition (12 of 14 retentions).** 3 close (Mode A defer mechanism-only — production-path coverage post-Round-7 inline fix at `:1025-1037`) + 3 DELETE (obsolete CDFE per L11) + 6 RECLASSIFY to G18.1 (per L12; finalizer-dependent — Phase H Task 19 owner). Mode A row fully retires (6 of 6: 3 closed by Task 17 Bucket A + 3 closed by Task 18 post-Round-7).

**F16.2 lineage annotation.** F16.2 stays Open via G18.1 lineage; closes when Task 19 lands the Captured-Request Terminal Guard rewrite.

**Lock conformance summary (L1-L14 + W1-W18; full enumeration in carry-forward.md Task 18 closeout entry).** All 14 locks honored; W2 + W17 unchanged (DelegationEscalation construction sites preserved at `:833` W17-protected + `:2416` W2-protected, both UNCHANGED by Task 18). W16 narrow adjudication (Round-7) for the worker payload dispatch fix + re-park gate lift; def signature unchanged; structural integrity preserved.

**Branch-matrix-with-test-coverage.** All 10 rows of the convergence map's branch matrix have direct test coverage in `tests/test_delegate_decide_async_integration.py` — happy paths (rows 1-3) covered by `test_decide_returns_3_field_result_on_success_*` + `test_build_response_payload_per_kind_decision`; CAS/journal/audit invariants (rows 4-6) covered by `test_decide_twice_*` + `test_decide_competing_reservation_*` + `test_decide_aborts_reservation_on_journal_intent_failure` + `test_decide_audit_event_post_commit_non_gating`; wire-shape contract (rows 7-8) covered by Round-7's `test_decide_worker_dispatches_l4_payload_end_to_end[3 sub-cases]`; audit-action correctness (rows 9-10) covered by `test_decide_audit_action_matches_decision_for_*`. Direct end-to-end coverage achieved.

**Hang-verification (W5).** Full suite 1020p/8s/0f in 123.70s; 3-file order-independence smoke (`test_delegation_controller.py`, `test_delegate_start_integration.py`, `test_delegate_decide_async_integration.py`) passes both forward (124p/6s in 105.68s) and reverse (124p/6s in 105.51s) orderings with identical counts.

**G18.1 record explicit.** 6 finalizer-dependent tests deferred to Phase H Task 19 with pre-authorized scope: renames at `:1881, :1927`, body rewrite spec for `:1525` (5-step protocol per the carry-forward.md G18.1 entry), L12 assertion-review notes for the remaining 3, constant `_TASK_19_FINALIZER_GUARD_REASON` deletion authorization in same commit. Full enumeration in carry-forward.md Open items §G18.1.

**L4 Path A verification artifact.** Pinned-version Codex App Server v0.117.0 JSON Schema fixture at `packages/plugins/codex-collaboration/tests/fixtures/codex-app-server/0.117.0/ToolRequestUserInputResponse.json` defines the wire shape `{"answers": {<qid>: {"answers": [<string>...]}}}`. Ground-truth verification in `test_build_response_payload_per_kind_decision[request_user_input-approve-answers2-expected_payload2]` at `tests/test_delegate_decide_async_integration.py:612-669` (Path A option 3 — pinned-version integration test).

**L7a incidental audit fix.** Audit `action=decision` fixes pre-existing hardcoded `action='approve'` bug at the relocated audit site (the old hardcoded value fired audit events with `action='approve'` for both approve AND deny because it sat BEFORE the deny/approve split). Documented as incidental to the required relocation per spec §1654.

**Round-7 supersession notes.**
- **Round-6 framed** the worker stale-wrapper-keys at `:1163-1164` (pre-fix lines) + the re-park PSR.create gate at `:1029-1031` as **out-of-Task-18 carry-forward observations** (deferred to Phase H disposition; mode A closure relied on test-side PSR.create pre-seed workarounds).
- **Round-7 superseded** that disposition with inline fixes within Task 18 via narrow W16 adjudication. The fix preserves `_execute_live_turn`'s def signature (W16's original protection scope); body changes are bounded to resume-path payload reads (`:1160-1172`) + re-park gate lift (`:1025-1037`). W2 + W17 unchanged. Mode A row fully retires (the alternative — partial retirement implied by Round-6's "out of scope" framing — is **NOT** the final disposition).
- **Verification evidence:** old wrapper-key reads = 0 (NEW permanent invariant); 1020 passed / 8 skipped (+3 from new parameterized regression); W3=6, W17=2, L6=0, old constant=0, new constant=8, decorators=6 unchanged.
- **Round-6 history preserved verbatim** with explicit supersession markers per the convergence map's Restructure Record / addenda chain. The audit trail (Round-6 framing → Round-7 reclassification + fix → final disposition) IS the project record value.

**Phase H entering carry-forward set:** F16.1 (2 unchanged) + RT.1 (unchanged) + TT.1 (newly promoted; `_FakeControlPlane` Pyright issues at multiple `tests/test_delegation_controller.py` instantiation sites) + G18.1 (newly introduced; 6 finalizer-dependent tests). F16.2 (1 retention; lineage marker) closes when G18.1 lands.

---


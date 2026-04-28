"""Packet 1 Task 17: start() under the async-decide model.

Acceptance tests for the 5 ParkedCaptureResult variants plus the two
parked-projection invariant-violation sub-cases plus reason-preservation.

Per W4 (Task 14/15/16/17 precedent): use module-local helpers
(_build_controller from tests.test_delegation_controller) + built-in pytest
fixtures + unittest.mock. Do NOT use plan-pseudocode fictional fixtures
(delegation_controller_fixture, app_server_runtime_stub, journal_spy,
audit_event_spy) — they do not exist.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from server.delegation_controller import (
    DelegationStartError,
    UnknownKindInEscalationProjection,
)
from server.models import (
    DelegationEscalation,
    DelegationJob,
)
from server.resolution_registry import (
    Parked,
    StartWaitElapsed,
    WorkerFailed,
)

from tests.test_delegation_controller import (
    _build_controller,
    _command_approval_request,
)


def _seed_running_job(
    job_store: object,
    *,
    job_id: str,
    parked_request_id: str | None = None,
    status: str = "running",
) -> DelegationJob:
    """Build and persist a DelegationJob directly through job_store.create.

    Used by dispatch-arm tests (StartWaitElapsed, Parked invariant-violation,
    WorkerFailed) that exercise _dispatch_parked_capture_outcome in isolation,
    bypassing the full spawn_worker handshake.
    """
    job = DelegationJob(
        job_id=job_id,
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="head-abc",
        worktree_path="/tmp/wt",
        promotion_state=None,
        status=status,  # type: ignore[arg-type]
        parked_request_id=parked_request_id,
    )
    job_store.create(job)  # type: ignore[attr-defined]
    return job


# ---------------------------------------------------------------------------
# Variant 1: Parked (happy path) — full worker spawn through real handshake.
# ---------------------------------------------------------------------------


def test_start_returns_escalation_on_parked(tmp_path: Path) -> None:
    """Worker parks on command_approval → announce_parked → start() returns
    DelegationEscalation projecting the parked request.

    Exercises the full async handshake end-to-end: spawn_worker on the worker
    thread, wait_for_parked on the main thread, _dispatch_parked_capture_outcome
    Parked arm, _project_pending_escalation projection, DelegationEscalation
    construction with agent_context=None (deferred semantics).
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, prs = _build_controller(tmp_path)
    control_plane._next_session_requests = [_command_approval_request()]

    result = controller.start(repo_root=repo_root, objective="Fix the bug")

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_escalation.kind == "command_approval"
    assert result.pending_escalation.request_id == "42"
    # Deferred-escalation semantics: agent_context is None for the Parked
    # path (worker still inside the turn — turn_result.agent_message does
    # not yet exist).
    assert result.agent_context is None

    stored = prs.get("42")
    assert stored is not None


# ---------------------------------------------------------------------------
# Variant 2: TurnCompletedWithoutCapture — analytical delegation, no capture.
# ---------------------------------------------------------------------------


def test_start_returns_plain_job_for_turn_completed_without_capture(
    tmp_path: Path,
) -> None:
    """No server requests emitted; turn completes normally → start() returns
    DelegationJob(status='completed').

    Exercises the TurnCompletedWithoutCapture arm: worker runner emits
    announce_turn_completed_empty as the post-_execute_live_turn fallthrough
    when the handler did not park.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )
    # No server requests configured → handler never invoked → turn completes.
    control_plane._next_session_requests = []

    result = controller.start(repo_root=repo_root, objective="Refactor")

    assert isinstance(result, DelegationJob)
    assert result.status == "completed"
    assert result.job_id == "job-1"


# ---------------------------------------------------------------------------
# Variant 3: TurnTerminalWithoutEscalation — unknown-kind parse failure.
# ---------------------------------------------------------------------------


def test_start_returns_plain_job_for_unknown_kind_parse_failure(
    tmp_path: Path,
) -> None:
    """Parse failure on a server request → handler emits
    announce_turn_terminal_without_escalation → start() returns
    DelegationJob(status='unknown'). Does NOT raise.

    Exercises the TurnTerminalWithoutEscalation arm. The minimal causal
    PendingServerRequest(kind='unknown') is the audit artifact.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, prs = _build_controller(tmp_path)
    # Message with non-dict params will fail parse_pending_server_request.
    control_plane._next_session_requests = [
        {"id": 77, "method": "item/unknown/broken", "params": "not-a-dict"}
    ]

    result = controller.start(repo_root=repo_root, objective="Build")

    assert isinstance(result, DelegationJob)
    assert result.status == "unknown"
    assert result.job_id == "job-1"

    # Causal record persisted with kind='unknown' (D4: parse failure stays
    # 'pending', not 'resolved').
    stored = prs.get("77")
    assert stored is not None
    assert stored.kind == "unknown"
    assert stored.status == "pending"


# ---------------------------------------------------------------------------
# Variant 4: WorkerFailed (default fallback reason).
# ---------------------------------------------------------------------------


def test_start_raises_for_worker_failed_before_capture(tmp_path: Path) -> None:
    """Worker raises a non-DelegationStartError exception → WorkerFailed arm
    falls through to the generic fallback → start() raises
    DelegationStartError(reason='worker_failed_before_capture').
    """
    controller, _cp, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)

    opaque_exc = RuntimeError("transport crash with no DelegationStartError shape")

    with pytest.raises(DelegationStartError) as exc_info:
        controller._dispatch_parked_capture_outcome(  # type: ignore[attr-defined]
            outcome=WorkerFailed(error=opaque_exc),
            job_id="job-1",
            collaboration_id="collab-1",
        )

    assert exc_info.value.reason == "worker_failed_before_capture"
    # .cause is the typed attribute carrying the wrapped worker exception
    # (separate from __cause__, which is set only when `raise ... from ...`
    # is used; see DelegationStartError docstring at delegation_controller.py:168).
    assert exc_info.value.cause is opaque_exc


# ---------------------------------------------------------------------------
# Variant 4: WorkerFailed reason-preservation (L7).
# ---------------------------------------------------------------------------


def test_start_raises_with_reason_preservation_for_unknown_kind_interrupt(
    tmp_path: Path,
) -> None:
    """Worker raises DelegationStartError(reason='unknown_kind_interrupt_transport_failure')
    → WorkerFailed arm preserves the precise reason rather than collapsing
    to 'worker_failed_before_capture' (L7 reason-preservation rule).
    """
    controller, _cp, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)

    classified = DelegationStartError(
        reason="unknown_kind_interrupt_transport_failure",
        cause=BrokenPipeError("pipe died during interrupt"),
    )

    with pytest.raises(DelegationStartError) as exc_info:
        controller._dispatch_parked_capture_outcome(  # type: ignore[attr-defined]
            outcome=WorkerFailed(error=classified),
            job_id="job-1",
            collaboration_id="collab-1",
        )

    # L7: reason flows through INTACT — not collapsed to the fallback.
    assert exc_info.value.reason == "unknown_kind_interrupt_transport_failure"
    # The re-raise preserves the exact same exception instance.
    assert exc_info.value is classified


# ---------------------------------------------------------------------------
# Variant 5: StartWaitElapsed — synchronous start-wait budget elapses.
# ---------------------------------------------------------------------------


def test_start_returns_running_job_on_start_wait_elapsed(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Worker capture-ready signal arrives after the start-wait budget
    elapses → start() returns DelegationJob(status='running'). Does NOT raise.

    Exercises the StartWaitElapsed arm via direct dispatch: rather than time-
    racing a real worker, inject the StartWaitElapsed outcome into
    _dispatch_parked_capture_outcome and assert the dispatch path returns the
    running job and logs the budget-elapsed warning.
    """
    controller, _cp, _wm, job_store, _ls, _j, _r, _prs = _build_controller(tmp_path)
    _seed_running_job(job_store, job_id="job-running-1", status="running")

    with caplog.at_level("WARNING", logger="server.delegation_controller"):
        result = controller._dispatch_parked_capture_outcome(  # type: ignore[attr-defined]
            outcome=StartWaitElapsed(),
            job_id="job-running-1",
            collaboration_id="collab-1",
        )

    assert isinstance(result, DelegationJob)
    assert result.status == "running"
    assert result.job_id == "job-running-1"
    assert any(
        "start-wait budget elapsed" in record.getMessage() for record in caplog.records
    )


# ---------------------------------------------------------------------------
# Variant 1 invariant-violation: Parked + projection returns None.
# ---------------------------------------------------------------------------


def test_start_signals_internal_abort_on_parked_projection_null(
    tmp_path: Path,
) -> None:
    """Parked signal received but _project_pending_escalation returns None
    (state-machine invariant violation: Parked implies a projectable view) →
    start() calls signal_internal_abort BEFORE raising (L8) →
    raises DelegationStartError(reason='parked_projection_invariant_violation').
    """
    controller, _cp, _wm, job_store, _ls, _j, _r, _prs = _build_controller(tmp_path)

    _seed_running_job(
        job_store,
        job_id="job-parked-null-1",
        parked_request_id="rid-null-1",
        status="needs_escalation",
    )

    # Force projection to return None (no view — invariant violation).
    null_projection = MagicMock(return_value=None)
    object.__setattr__(controller, "_project_pending_escalation", null_projection)

    # Spy on signal_internal_abort to verify L8 ordering.
    abort_spy = MagicMock(return_value=True)
    object.__setattr__(controller._registry, "signal_internal_abort", abort_spy)

    with pytest.raises(DelegationStartError) as exc_info:
        controller._dispatch_parked_capture_outcome(  # type: ignore[attr-defined]
            outcome=Parked(request_id="rid-null-1"),
            job_id="job-parked-null-1",
            collaboration_id="collab-1",
        )

    assert exc_info.value.reason == "parked_projection_invariant_violation"
    # L8: signal_internal_abort MUST have been called BEFORE the raise (so
    # the worker does not leak in registry.wait()).
    abort_spy.assert_called_once_with(
        "rid-null-1", reason="parked_projection_invariant_violation"
    )


# ---------------------------------------------------------------------------
# Variant 1 invariant-violation: Parked + projection raises.
# ---------------------------------------------------------------------------


def test_start_signals_internal_abort_on_parked_projection_raise(
    tmp_path: Path,
) -> None:
    """Parked signal received but _project_pending_escalation raises
    UnknownKindInEscalationProjection → start() calls signal_internal_abort
    with the SAME broad reason (L8, spec §Capture-ready handshake) →
    raises DelegationStartError(reason='parked_projection_invariant_violation').
    """
    controller, _cp, _wm, job_store, _ls, _j, _r, _prs = _build_controller(tmp_path)

    _seed_running_job(
        job_store,
        job_id="job-parked-raise-1",
        parked_request_id="rid-raise-1",
        status="needs_escalation",
    )

    def raising_projection(_job: object) -> None:
        raise UnknownKindInEscalationProjection(
            "Test injection: unknown kind at projection"
        )

    object.__setattr__(controller, "_project_pending_escalation", raising_projection)

    abort_spy = MagicMock(return_value=True)
    object.__setattr__(controller._registry, "signal_internal_abort", abort_spy)

    with pytest.raises(DelegationStartError) as exc_info:
        controller._dispatch_parked_capture_outcome(  # type: ignore[attr-defined]
            outcome=Parked(request_id="rid-raise-1"),
            job_id="job-parked-raise-1",
            collaboration_id="collab-1",
        )

    # SAME broad reason as the null-projection sub-case (spec §Capture-ready
    # handshake: both invariant-violation sub-cases collapse to one reason).
    assert exc_info.value.reason == "parked_projection_invariant_violation"
    abort_spy.assert_called_once_with(
        "rid-raise-1", reason="parked_projection_invariant_violation"
    )


# ---------------------------------------------------------------------------
# F14 race regression: spawn_worker → wait_for_parked capture-ready race.
# ---------------------------------------------------------------------------


def test_start_handles_announce_parked_arriving_before_wait_for_parked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression test for the spawn_worker -> wait_for_parked capture-ready
    race.

    Before F14, ``DelegationController.start()`` called ``spawn_worker(...)``
    immediately followed by ``self._registry.wait_for_parked(...)``. The
    capture-ready channel was created INSIDE ``wait_for_parked``, so a fast
    worker that called ``announce_parked`` before the main thread reached
    that line would have its signal dropped by the
    ``_deliver_capture_outcome`` channel-is-None branch -- ``start()`` would
    then block at the wait until ``START_OUTCOME_WAIT_SECONDS`` elapsed and
    incorrectly return ``StartWaitElapsed`` (which projects to a running
    DelegationJob), even though the worker had already parked.

    The fix pre-registers the channel via ``open_capture_channel`` BEFORE
    spawn_worker. This test reproduces the worst-case race deterministically
    by patching ``spawn_worker`` to run the worker's park sequence
    synchronously in the main thread BEFORE returning -- guaranteeing the
    announce arrives before ``wait_for_parked``. Without the fix this test
    would block for the full wait budget; with the fix the buffered outcome
    is consumed immediately and ``start()`` returns ``DelegationEscalation``.
    """
    from server.models import PendingServerRequest

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, _j, registry, prs = _build_controller(tmp_path)

    # Shrink the wait budget so a regression (race not closed) fails fast
    # rather than blocking for the production 30 s default.
    monkeypatch.setattr(
        "server.delegation_controller.START_OUTCOME_WAIT_SECONDS", 0.5
    )

    def synchronous_park_worker(
        *,
        controller: object,
        registry: object,
        job_id: str,
        collaboration_id: str,
        runtime_id: str,
        worktree_path: Path,
        prompt_text: str,
    ) -> object:
        # Mimic the worker's park persistence sequence on the calling thread,
        # before returning. Mirrors the real handler at
        # delegation_controller.py:1059-1073 with the minimum needed for the
        # Parked dispatch arm to project a pending escalation:
        #   create PSR -> update_parked_request -> persist needs_escalation
        #   -> announce_parked.
        # `registry.register` and `registry.wait` are deliberately omitted —
        # this test does not exercise the operator-decide cycle, only the
        # capture-ready handshake race surface.
        prs.create(  # type: ignore[arg-type]
            PendingServerRequest(
                request_id="rid-race-1",
                runtime_id=runtime_id,
                collaboration_id=collaboration_id,
                codex_thread_id="thr-race",
                codex_turn_id="turn-race",
                item_id="item-race",
                kind="command_approval",
                requested_scope={"command": ["ls"]},
                status="pending",
            )
        )
        controller._job_store.update_parked_request(  # type: ignore[attr-defined]
            job_id, "rid-race-1"
        )
        controller._persist_job_transition(job_id, "needs_escalation")  # type: ignore[attr-defined]

        # The race-critical line. Without F14's open_capture_channel, the
        # channel does not exist yet at this moment -- the signal is dropped
        # and start() blocks at wait_for_parked.
        registry.announce_parked(job_id, request_id="rid-race-1")  # type: ignore[attr-defined]
        return MagicMock()

    monkeypatch.setattr(
        "server.delegation_controller.spawn_worker", synchronous_park_worker
    )

    # Without F14: this call blocks for ~0.5 s then returns a running job.
    # With F14:    this call returns immediately with a DelegationEscalation.
    result = controller.start(repo_root=repo_root, objective="Race regression")

    assert isinstance(result, DelegationEscalation), (
        "F14 race regression: announce_parked arrived before wait_for_parked,"
        " but start() returned a non-escalation result. The pre-open of the"
        " capture-ready channel is missing or out of order in"
        " DelegationController.start()."
    )
    assert result.pending_escalation.request_id == "rid-race-1"
    assert result.pending_escalation.kind == "command_approval"

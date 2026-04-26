"""Packet 1 Task 16: Handler branches for decide-success / timeout / internal-abort /
dispatch-failure / unknown-kind paths.

Integration tests use _build_controller(tmp_path) (same pattern as Task 14/15).
ResolutionRegistry is injected via monkeypatch so registry.wait() returns the
desired resolution synchronously (no threads needed).

Per-test triage (convergence map):
  - test_happy_path_decide_approve_success               → SKIP (Task 19)
  - test_timeout_cancel_dispatch_succeeded_for_file_change → SKIP (Task 19)
  - test_timeout_cancel_dispatch_failed_for_command_approval → WRITE
  - test_timeout_interrupt_succeeded_for_request_user_input → WRITE
  - test_timeout_interrupt_failed_for_request_user_input    → WRITE
  - test_dispatch_failure_on_operator_decide                → WRITE
  - test_internal_abort_on_unknown_kind_poll_projection_abort → WRITE
  - test_unknown_kind_parse_failure_terminalizes_unknown     → WRITE (L10 path)
  - test_unknown_kind_interrupt_transport_failure            → WRITE
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, create_autospec

import pytest

from server.delegation_controller import DelegationStartError
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.lineage_store import LineageStore
from server.models import (
    CollaborationHandle,
    DelegationJob,
)
from server.resolution_registry import (
    DecisionResolution,
    InternalAbort,
    ResolutionRegistry,
)

# Import the module-local build helper per Task 14 W4 / Task 15 L8 precedent.
from tests.test_delegation_controller import (  # type: ignore[import]
    _FakeSession,
    _build_controller,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _command_approval_request(
    *,
    request_id: int | str = 42,
    item_id: str = "item-1",
    thread_id: str = "thr-1",
    turn_id: str = "turn-1",
) -> dict[str, Any]:
    return {
        "id": request_id,
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
            "command": "rm -rf /",
        },
    }


def _file_change_request(
    *,
    request_id: int | str = 43,
    item_id: str = "item-f",
    thread_id: str = "thr-1",
    turn_id: str = "turn-1",
) -> dict[str, Any]:
    return {
        "id": request_id,
        "method": "item/fileChange/requestApproval",
        "params": {
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
            "patch": "diff --git ...",
        },
    }


def _request_user_input_request(
    *,
    request_id: int | str = 55,
    item_id: str = "item-u",
    thread_id: str = "thr-1",
    turn_id: str = "turn-1",
) -> dict[str, Any]:
    return {
        "id": request_id,
        "method": "item/tool/requestUserInput",
        "params": {
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
            "questions": [],
        },
    }


def _make_running_job_with_lineage(
    job_store: DelegationJobStore,
    lineage_store: LineageStore,
    runtime_registry: ExecutionRuntimeRegistry,
    fake_session: _FakeSession,
    repo_root: Path,
    *,
    job_id: str = "job-h-1",
    runtime_id: str = "rt-h-1",
    collaboration_id: str = "collab-h-1",
    worktree_path: str = "/tmp/wt-h-1",
) -> DelegationJob:
    """Create a DelegationJob + CollaborationHandle + runtime entry so
    _execute_live_turn's preconditions are satisfied."""
    handle = CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="execution",
        runtime_id=runtime_id,
        codex_thread_id="thr-h-1",
        claude_session_id="sess-h-1",
        repo_root=str(repo_root),
        created_at="2026-04-25T00:00:00Z",
        status="active",
    )
    lineage_store.create(handle)

    job = DelegationJob(
        job_id=job_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        base_commit="abc123",
        worktree_path=worktree_path,
        promotion_state=None,
        status="running",
    )
    job_store.create(job)
    runtime_registry.register(
        runtime_id=runtime_id,
        session=fake_session,
        thread_id="thr-h-1",
        job_id=job_id,
    )
    return job


# ---------------------------------------------------------------------------
# Finalizer-routed integration tests — SKIPPED pending Phase H Task 19
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "Phase H Task 19: requires Captured-Request Terminal Guard rewrite of "
        "_finalize_turn for finalizer-routed decide-success path. Worker writes "
        "record_response_dispatch + mark_resolved + completion_origin='worker_completed' "
        "at Task 16; finalizer projection that maps to DelegationJob.status='completed' "
        "lands at Task 19."
    )
)
def test_happy_path_decide_approve_success(tmp_path: Path) -> None:
    """Worker parks → operator decides approve → session.respond succeeds →
    record_response_dispatch + mark_resolved → handler returns None → turn
    completes naturally → _finalize_turn's Captured-Request Terminal Guard
    sets final_status='completed'.
    """
    pass


@pytest.mark.skip(
    reason=(
        "Phase H Task 19: requires Captured-Request Terminal Guard rewrite of "
        "_finalize_turn for finalizer-routed cancel-success path. Worker writes "
        "record_timeout(succeeded) + completion_origin='worker_completed' at Task 16; "
        "finalizer projection that maps to DelegationJob.status='canceled' lands at Task 19."
    )
)
def test_timeout_cancel_dispatch_succeeded_for_file_change(tmp_path: Path) -> None:
    """file_change captured → no operator decide → timer fires →
    session.respond(cancel) succeeds → record_timeout(dispatch_result='succeeded')
    → handler returns None → turn completes naturally → _finalize_turn
    maps request_snapshot to DelegationJob.status='canceled'.
    """
    pass


# ---------------------------------------------------------------------------
# Sentinel-bypass integration tests (rows 3-8 in the branch matrix)
# ---------------------------------------------------------------------------


def test_timeout_cancel_dispatch_failed_for_command_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """command_approval captured → timer fires → session.respond(cancel) raises
    BrokenPipeError → record_timeout(dispatch_result='failed') →
    _mark_execution_unknown_and_cleanup → sentinel 'timeout_cancel_dispatch_failed' →
    _execute_live_turn bypasses _finalize_turn → stored job.status='unknown'.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    fake_session = _FakeSession()
    fake_session._server_requests = [_command_approval_request(request_id=42)]
    # respond() raises to simulate transport failure.
    fake_session.respond = MagicMock(side_effect=BrokenPipeError("pipe broken"))

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    # Inject a mock registry that delivers a timeout resolution immediately.
    mock_registry = create_autospec(ResolutionRegistry, instance=True)
    mock_registry.wait.return_value = DecisionResolution(
        payload={},
        kind="command_approval",
        is_timeout=True,
    )
    monkeypatch.setattr(controller, "_registry", mock_registry)

    result = controller._execute_live_turn(  # type: ignore[attr-defined]
        job_id="job-h-1",
        collaboration_id="collab-h-1",
        runtime_id="rt-h-1",
        worktree_path=repo_root / "worktree",
        prompt_text="do work",
    )

    # Sentinel bypass: _finalize_turn is NOT entered. Stored job returned.
    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-h-1"
    assert result.status == "unknown"

    # record_timeout with dispatch_result="failed" was written.
    stored = pending_request_store.get("42")
    assert stored is not None
    assert stored.timed_out is True
    assert stored.dispatch_result == "failed"

    # registry.discard was called.
    mock_registry.discard.assert_called_once_with("42")


def test_timeout_interrupt_succeeded_for_request_user_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """request_user_input captured → timer fires → session.interrupt_turn
    succeeds → record_timeout(interrupt_error=None) → inline cancel-cleanup
    sequence (_persist_job_transition(canceled), lineage completed, runtime release,
    session close) → sentinel 'timeout_interrupt_succeeded' → _execute_live_turn
    bypasses _finalize_turn → stored job.status='canceled'.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    fake_session = _FakeSession()
    fake_session._server_requests = [_request_user_input_request(request_id=55)]
    # interrupt_turn succeeds (default _FakeSession behavior sets _interrupted=True).

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    mock_registry = create_autospec(ResolutionRegistry, instance=True)
    mock_registry.wait.return_value = DecisionResolution(
        payload={},
        kind="request_user_input",
        is_timeout=True,
    )
    monkeypatch.setattr(controller, "_registry", mock_registry)

    result = controller._execute_live_turn(  # type: ignore[attr-defined]
        job_id="job-h-1",
        collaboration_id="collab-h-1",
        runtime_id="rt-h-1",
        worktree_path=repo_root / "worktree",
        prompt_text="do work",
    )

    # Sentinel bypass: returned stored job at status="canceled" (verified cancel).
    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-h-1"
    assert result.status == "canceled"

    # record_timeout with interrupt_error=None was written.
    stored = pending_request_store.get("55")
    assert stored is not None
    assert stored.timed_out is True
    assert stored.interrupt_error is None

    # session was closed (inline cancel cleanup).
    assert fake_session.closed

    # registry.discard was called.
    mock_registry.discard.assert_called_once_with("55")


def test_timeout_interrupt_failed_for_request_user_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """request_user_input captured → timer fires → session.interrupt_turn
    raises → record_timeout(interrupt_error=<sanitized>) →
    _mark_execution_unknown_and_cleanup → sentinel 'timeout_interrupt_failed' →
    _execute_live_turn bypasses _finalize_turn → stored job.status='unknown'.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    fake_session = _FakeSession()
    fake_session._server_requests = [_request_user_input_request(request_id=55)]
    # Override interrupt_turn to raise.
    fake_session.interrupt_turn = MagicMock(  # type: ignore[method-assign]
        side_effect=ConnectionError("socket error")
    )

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    mock_registry = create_autospec(ResolutionRegistry, instance=True)
    mock_registry.wait.return_value = DecisionResolution(
        payload={},
        kind="request_user_input",
        is_timeout=True,
    )
    monkeypatch.setattr(controller, "_registry", mock_registry)

    result = controller._execute_live_turn(  # type: ignore[attr-defined]
        job_id="job-h-1",
        collaboration_id="collab-h-1",
        runtime_id="rt-h-1",
        worktree_path=repo_root / "worktree",
        prompt_text="do work",
    )

    # Sentinel bypass: returned stored job at status="unknown" (OB-1).
    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-h-1"
    assert result.status == "unknown"

    # record_timeout with interrupt_error set.
    stored = pending_request_store.get("55")
    assert stored is not None
    assert stored.timed_out is True
    assert stored.interrupt_error is not None
    assert "ConnectionError" in stored.interrupt_error

    # registry.discard was called.
    mock_registry.discard.assert_called_once_with("55")


def test_dispatch_failure_on_operator_decide(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Operator decides approve → session.respond raises BrokenPipeError →
    record_dispatch_failure(action='approve', dispatch_result='failed') →
    _mark_execution_unknown_and_cleanup → sentinel 'dispatch_failed' →
    _execute_live_turn bypasses _finalize_turn → stored job.status='unknown'.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    fake_session = _FakeSession()
    fake_session._server_requests = [_command_approval_request(request_id=42)]
    fake_session.respond = MagicMock(side_effect=BrokenPipeError("pipe broken"))

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    # Operator-decide resolution (is_timeout=False).
    mock_registry = create_autospec(ResolutionRegistry, instance=True)
    mock_registry.wait.return_value = DecisionResolution(
        payload={"resolution_action": "approve", "response_payload": {"decision": "accept"}},
        kind="command_approval",
        is_timeout=False,
    )
    monkeypatch.setattr(controller, "_registry", mock_registry)

    result = controller._execute_live_turn(  # type: ignore[attr-defined]
        job_id="job-h-1",
        collaboration_id="collab-h-1",
        runtime_id="rt-h-1",
        worktree_path=repo_root / "worktree",
        prompt_text="do work",
    )

    # Sentinel bypass: stored job status = "unknown" (OB-1: transport fail).
    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-h-1"
    assert result.status == "unknown"

    # record_dispatch_failure was written (not record_timeout).
    stored = pending_request_store.get("42")
    assert stored is not None
    assert stored.dispatch_result == "failed"
    assert stored.resolution_action == "approve"
    assert stored.dispatch_error is not None
    assert "BrokenPipeError" in stored.dispatch_error

    # registry.discard was called.
    mock_registry.discard.assert_called_once_with("42")


def test_internal_abort_on_unknown_kind_poll_projection_abort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parkable capture → worker parks → registry delivers InternalAbort →
    record_internal_abort → sentinel 'internal_abort' → _execute_live_turn
    bypasses _finalize_turn → stored job.status='unknown'.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    fake_session = _FakeSession()
    fake_session._server_requests = [_command_approval_request(request_id=42)]

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    mock_registry = create_autospec(ResolutionRegistry, instance=True)
    mock_registry.wait.return_value = InternalAbort(
        reason="unknown_kind_in_escalation_projection"
    )
    monkeypatch.setattr(controller, "_registry", mock_registry)

    result = controller._execute_live_turn(  # type: ignore[attr-defined]
        job_id="job-h-1",
        collaboration_id="collab-h-1",
        runtime_id="rt-h-1",
        worktree_path=repo_root / "worktree",
        prompt_text="do work",
    )

    # Sentinel bypass: stored job status = "unknown".
    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-h-1"
    assert result.status == "unknown"

    # record_internal_abort was written.
    stored = pending_request_store.get("42")
    assert stored is not None
    assert stored.internal_abort_reason == "unknown_kind_in_escalation_projection"

    # registry.discard was called.
    mock_registry.discard.assert_called_once_with("42")


@pytest.mark.skip(
    reason=(
        "Phase G Task 17: _finalize_turn's status-derivation branch at line ~2211 calls "
        "_project_request_to_view with kind='unknown' (interrupted_by_unknown=True path), "
        "raising UnknownKindInEscalationProjection. The convergence map noted the D4 carve-out "
        "as handling this case (L10), but the live _finalize_turn does not yet have the "
        "carve-out that skips _project_request_to_view for interrupted_by_unknown+parse_failed. "
        "This is the same barrier as Mode A skip-decorators (test_start_with_unparseable_request). "
        "Task 17 adds the unknown-kind L6 callsite handling that resolves this path."
    )
)
def test_unknown_kind_parse_failure_terminalizes_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parse failure → PendingServerRequest(kind='unknown') created →
    session.interrupt_turn succeeds → _persist_job_transition(unknown) →
    announce_turn_terminal_without_escalation → handler returns None (L10 path).

    _execute_live_turn enters _finalize_turn with interrupted_by_unknown=True;
    Task 17 will add the carve-out at _finalize_turn that avoids _project_request_to_view
    for the unknown-kind-parse-failure path.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    # A message with no valid params will fail parse_pending_server_request.
    fake_session = _FakeSession()
    fake_session._server_requests = [
        {"id": 77, "method": "item/unknown/broken", "params": "not-a-dict"}
    ]

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    # Mock registry — announce_turn_terminal_without_escalation must not raise.
    mock_registry = create_autospec(ResolutionRegistry, instance=True)
    monkeypatch.setattr(controller, "_registry", mock_registry)

    result = controller._execute_live_turn(  # type: ignore[attr-defined]
        job_id="job-h-1",
        collaboration_id="collab-h-1",
        runtime_id="rt-h-1",
        worktree_path=repo_root / "worktree",
        prompt_text="do work",
    )

    # L10 path: handler returns None, _finalize_turn's D4 carve-out runs.
    # Job ends as "unknown" (parse failure → unknown-kind → interrupted_by_unknown).
    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-h-1"
    assert result.status == "unknown"

    # Minimal causal PendingServerRequest was created.
    stored = pending_request_store.get("77")
    assert stored is not None
    assert stored.kind == "unknown"
    assert stored.requested_scope == {"raw_method": "item/unknown/broken"}

    # announce_turn_terminal_without_escalation was called (cross-thread signal).
    mock_registry.announce_turn_terminal_without_escalation.assert_called_once()


def test_unknown_kind_interrupt_transport_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parse failure → PendingServerRequest(kind='unknown') created →
    session.interrupt_turn raises BrokenPipeError → cleanup →
    sentinel 'unknown_kind_interrupt_transport_failure' → _execute_live_turn
    re-raises as DelegationStartError(reason=same, cause=None).
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    fake_session = _FakeSession()
    fake_session._server_requests = [
        {"id": 88, "method": "item/unknown/broken", "params": "not-a-dict"}
    ]
    # interrupt_turn raises to simulate transport failure.
    fake_session.interrupt_turn = MagicMock(  # type: ignore[method-assign]
        side_effect=BrokenPipeError("cannot interrupt")
    )

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    # No registry mock needed — parse fails before registry.register is called.
    # But we mock it anyway so announce_* don't raise.
    mock_registry = create_autospec(ResolutionRegistry, instance=True)
    monkeypatch.setattr(controller, "_registry", mock_registry)

    with pytest.raises(DelegationStartError) as exc_info:
        controller._execute_live_turn(  # type: ignore[attr-defined]
            job_id="job-h-1",
            collaboration_id="collab-h-1",
            runtime_id="rt-h-1",
            worktree_path=repo_root / "worktree",
            prompt_text="do work",
        )

    exc = exc_info.value
    assert exc.reason == "unknown_kind_interrupt_transport_failure"
    assert exc.cause is None

    # Minimal causal record was created.
    stored = pending_request_store.get("88")
    assert stored is not None
    assert stored.kind == "unknown"

    # Job was marked unknown via _mark_execution_unknown_and_cleanup.
    stored_job = job_store.get("job-h-1")
    assert stored_job is not None
    assert stored_job.status == "unknown"


# ---------------------------------------------------------------------------
# Unit tests for new helpers
# ---------------------------------------------------------------------------


def test_handle_timeout_wake_dispatches_by_kind_cancel_capable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """command_approval/file_change → respond({"decision":"cancel"}) path.

    On success: returns True (caller returns None from handler).
    On failure: raises _WorkerTerminalBranchSignal(reason='timeout_cancel_dispatch_failed').
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    from server.models import PendingServerRequest

    fake_session = _FakeSession()
    fake_session.respond = MagicMock(return_value=None)

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    entry = runtime_registry.lookup("rt-h-1")
    assert entry is not None

    request = PendingServerRequest(
        request_id="req-cancel-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        codex_thread_id="thr-h-1",
        codex_turn_id="turn-h-1",
        item_id="item-h-1",
        kind="command_approval",
        requested_scope={},
    )
    pending_request_store.create(request)
    job_store.update_parked_request("job-h-1", "req-cancel-1")

    mock_registry = create_autospec(ResolutionRegistry, instance=True)
    monkeypatch.setattr(controller, "_registry", mock_registry)

    result = controller._handle_timeout_wake(  # type: ignore[attr-defined]
        entry=entry,
        job_id="job-h-1",
        collaboration_id="collab-h-1",
        runtime_id="rt-h-1",
        request=request,
        registry=mock_registry,
    )

    # Returns True (cancel-capable-success path).
    assert result is True
    fake_session.respond.assert_called_once_with("req-cancel-1", {"decision": "cancel"})
    mock_registry.discard.assert_called_once_with("req-cancel-1")

    # record_timeout with dispatch_result="succeeded" was written.
    stored = pending_request_store.get("req-cancel-1")
    assert stored is not None
    assert stored.timed_out is True
    assert stored.dispatch_result == "succeeded"


def test_handle_timeout_wake_unexpected_kind_raises_assertion_error(
    tmp_path: Path,
) -> None:
    """W9 — defensive AssertionError at bottom of _handle_timeout_wake for
    unexpected kind (e.g. 'unknown') that bypassed the upstream filter.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    from server.models import PendingServerRequest

    fake_session = _FakeSession()

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        fake_session,
        repo_root,
    )

    entry = runtime_registry.lookup("rt-h-1")
    assert entry is not None

    # Build a request with kind="unknown" to trigger the defensive raise.
    request = PendingServerRequest(
        request_id="req-unknown-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        codex_thread_id="thr-h-1",
        codex_turn_id="turn-h-1",
        item_id="item-u-1",
        kind="unknown",
        requested_scope={},
    )
    pending_request_store.create(request)

    mock_registry = create_autospec(ResolutionRegistry, instance=True)

    with pytest.raises(AssertionError, match="unexpected kind"):
        controller._handle_timeout_wake(  # type: ignore[attr-defined]
            entry=entry,
            job_id="job-h-1",
            collaboration_id="collab-h-1",
            runtime_id="rt-h-1",
            request=request,
            registry=mock_registry,
        )


def test_write_completion_and_audit_timeout_writes_worker_completed(
    tmp_path: Path,
) -> None:
    """_write_completion_and_audit_timeout writes completion_origin='worker_completed'
    on the approval_resolution journal entry.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        journal,
        runtime_registry,
        _prs,
    ) = _build_controller(tmp_path)

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        _FakeSession(),
        repo_root,
    )

    controller._write_completion_and_audit_timeout(  # type: ignore[attr-defined]
        job_id="job-h-1",
        collaboration_id="collab-h-1",
        runtime_id="rt-h-1",
        request_id="req-audit-1",
    )

    # Journal should have a completed phase with worker_completed origin.
    # Journal file: plugin_data/journal/operations/{session_id}.jsonl
    journal_path = tmp_path / "data" / "journal" / "operations" / "sess-1.jsonl"
    entries = [
        json.loads(line)
        for line in journal_path.read_text().splitlines()
        if line.strip()
    ]
    completed_entries = [
        e
        for e in entries
        if e.get("phase") == "completed"
        and e.get("operation") == "approval_resolution"
        and e.get("request_id") == "req-audit-1"
    ]
    assert len(completed_entries) == 1
    assert completed_entries[0]["completion_origin"] == "worker_completed"


def test_write_completion_and_audit_timeout_audit_failure_logs_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_write_completion_and_audit_timeout handles audit append failure with
    a warning log — does not re-raise.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    import logging

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        journal,
        runtime_registry,
        _prs,
    ) = _build_controller(tmp_path)

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        _FakeSession(),
        repo_root,
    )

    # Force append_audit_event to raise.
    monkeypatch.setattr(
        journal,
        "append_audit_event",
        MagicMock(side_effect=RuntimeError("audit store unavailable")),
    )

    with caplog.at_level(logging.WARNING, logger="server.delegation_controller"):
        # Must not raise.
        controller._write_completion_and_audit_timeout(  # type: ignore[attr-defined]
            job_id="job-h-1",
            collaboration_id="collab-h-1",
            runtime_id="rt-h-1",
            request_id="req-audit-2",
        )

    assert "audit approval_timeout append failed" in caplog.text


def test_repo_root_for_journal_resolves_lineage_handle(
    tmp_path: Path,
) -> None:
    """_repo_root_for_journal returns the repo_root string from the lineage handle."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        runtime_registry,
        _prs,
    ) = _build_controller(tmp_path)

    _make_running_job_with_lineage(
        job_store,
        lineage_store,
        runtime_registry,
        _FakeSession(),
        repo_root,
    )

    result = controller._repo_root_for_journal("job-h-1")  # type: ignore[attr-defined]

    assert result == str(repo_root)

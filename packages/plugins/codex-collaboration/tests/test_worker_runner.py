"""Packet 1: _WorkerRunner thread entry + _execute_live_turn sentinel catch."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from server.delegation_controller import (
    DelegationStartError,
    _WorkerTerminalBranchSignal,
)
from server.models import DelegationJob
from server.worker_runner import _WorkerRunner

# Import the module-local build helper via the same pattern used in Task 14.
from tests.test_delegation_controller import _build_controller  # type: ignore[import]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_running_job(
    job_store,
    runtime_registry,
    fake_session,
    *,
    job_id: str = "job-sentinel-1",
    runtime_id: str = "rt-sentinel-1",
    collaboration_id: str = "collab-sentinel-1",
    worktree_path: str = "/tmp/wt-sentinel-1",
) -> DelegationJob:
    """Construct a running DelegationJob and register its runtime entry
    so _execute_live_turn's lookup precondition is satisfied."""
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
        thread_id="thr-sentinel-1",
        job_id=job_id,
    )
    return job


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_worker_runner_exists() -> None:
    assert _WorkerRunner is not None


# ---------------------------------------------------------------------------
# Contract guards: _load_or_materialize_inspection + canceled
# ---------------------------------------------------------------------------


def test_load_or_materialize_inspection_admits_canceled_job(
    tmp_path: Path,
) -> None:
    """canceled job → _load_or_materialize_inspection returns None."""
    controller, *_ = _build_controller(tmp_path)
    job = DelegationJob(
        job_id="job-canceled-1",
        runtime_id="rt-canceled-1",
        collaboration_id="collab-canceled-1",
        base_commit="abc",
        worktree_path="/tmp/wt",
        promotion_state=None,
        status="canceled",
    )
    result = controller._load_or_materialize_inspection(job)  # type: ignore[attr-defined]
    assert result is None


def test_load_or_materialize_inspection_does_not_materialize_for_canceled(
    tmp_path: Path,
) -> None:
    """canceled job → artifact store must not be touched at all (L7)."""
    controller, *_ = _build_controller(tmp_path)
    job = DelegationJob(
        job_id="job-canceled-2",
        runtime_id="rt-canceled-2",
        collaboration_id="collab-canceled-2",
        base_commit="abc",
        worktree_path="/tmp/wt",
        promotion_state=None,
        status="canceled",
    )
    mock_store = MagicMock(spec=type(controller._artifact_store))  # type: ignore[attr-defined]
    with patch.object(controller, "_artifact_store", mock_store):
        result = controller._load_or_materialize_inspection(job)  # type: ignore[attr-defined]
    assert result is None
    mock_store.load_snapshot.assert_not_called()
    mock_store.materialize_snapshot.assert_not_called()
    mock_store.reconstruct_from_artifacts.assert_not_called()


# ---------------------------------------------------------------------------
# Sentinel catch: post-branch reason returns stored job, bypasses cleanup
# ---------------------------------------------------------------------------


def test_execute_live_turn_catches_worker_terminal_branch_signal_post_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Post-branch sentinel: _execute_live_turn returns the stored DelegationJob,
    does NOT invoke _mark_execution_unknown_and_cleanup, and logs signal.reason.
    """
    (
        controller,
        _control_plane,
        _worktree_manager,
        job_store,
        _lineage,
        _journal,
        runtime_registry,
        _pending,
    ) = _build_controller(tmp_path)

    # Use a MagicMock as the session — it just needs run_execution_turn to raise.
    mock_session = MagicMock()
    mock_session.run_execution_turn.side_effect = _WorkerTerminalBranchSignal(
        reason="dispatch_failed"
    )

    _make_running_job(
        job_store,
        runtime_registry,
        mock_session,
        job_id="job-post-1",
        runtime_id="rt-post-1",
        collaboration_id="collab-post-1",
    )

    # Track calls to _mark_execution_unknown_and_cleanup.
    cleanup_call_count = 0
    original_cleanup = controller._mark_execution_unknown_and_cleanup  # type: ignore[attr-defined]

    def _spy_cleanup(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal cleanup_call_count
        cleanup_call_count += 1
        return original_cleanup(**kwargs)

    monkeypatch.setattr(
        controller, "_mark_execution_unknown_and_cleanup", _spy_cleanup
    )

    with caplog.at_level(logging.INFO, logger="server.delegation_controller"):
        result = controller._execute_live_turn(  # type: ignore[attr-defined]
            job_id="job-post-1",
            collaboration_id="collab-post-1",
            runtime_id="rt-post-1",
            worktree_path=Path("/tmp/wt-sentinel-1"),
            prompt_text="do work",
        )

    # Returns the stored DelegationJob — not raises.
    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-post-1"

    # _mark_execution_unknown_and_cleanup was NOT invoked.
    assert cleanup_call_count == 0

    # signal.reason logged as substring.
    assert "dispatch_failed" in caplog.text


# ---------------------------------------------------------------------------
# Sentinel catch: pre-capture reason re-raises as DelegationStartError
# ---------------------------------------------------------------------------


def test_execute_live_turn_catches_worker_terminal_branch_signal_pre_capture_reraises_as_delegation_start_error(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Pre-capture sentinel: re-raises DelegationStartError with matching reason
    and cause=None; signal.reason still logged before the raise.
    """
    (
        controller,
        _control_plane,
        _worktree_manager,
        job_store,
        _lineage,
        _journal,
        runtime_registry,
        _pending,
    ) = _build_controller(tmp_path)

    mock_session = MagicMock()
    mock_session.run_execution_turn.side_effect = _WorkerTerminalBranchSignal(
        reason="unknown_kind_interrupt_transport_failure"
    )

    _make_running_job(
        job_store,
        runtime_registry,
        mock_session,
        job_id="job-pre-1",
        runtime_id="rt-pre-1",
        collaboration_id="collab-pre-1",
    )

    with caplog.at_level(logging.INFO, logger="server.delegation_controller"):
        with pytest.raises(DelegationStartError) as exc_info:
            controller._execute_live_turn(  # type: ignore[attr-defined]
                job_id="job-pre-1",
                collaboration_id="collab-pre-1",
                runtime_id="rt-pre-1",
                worktree_path=Path("/tmp/wt-sentinel-1"),
                prompt_text="do work",
            )

    exc = exc_info.value
    assert exc.reason == "unknown_kind_interrupt_transport_failure"
    assert exc.cause is None

    # signal.reason logged as substring.
    assert "unknown_kind_interrupt_transport_failure" in caplog.text

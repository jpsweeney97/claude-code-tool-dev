"""Task 20: poll() projection guard — UnknownKindInEscalationProjection catch.

Tests prove that poll() catches UnknownKindInEscalationProjection from
_project_pending_escalation, signals worker-coordinated internal abort via
the registry, logs at CRITICAL with the CAS outcome, and returns
DelegationPollResult(pending_escalation=None) regardless of the signal's
return value.

Direct-seed pattern follows test_handler_branches_integration.py:759-817
(_make_running_job_with_lineage + job_store.update_status +
pending_request_store.create) because start() cannot produce a
kind="unknown" + needs_escalation job under Task 17's L11 carve-out.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from server.delegation_job_store import DelegationJobStore
from server.lineage_store import LineageStore
from server.models import (
    CollaborationHandle,
    DelegationJob,
    DelegationPollResult,
    PendingRequestKind,
    PendingServerRequest,
)
from server.resolution_registry import ResolutionRegistry

from tests.test_delegation_controller import (  # type: ignore[import]
    _build_controller,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_needs_escalation_job(
    job_store: DelegationJobStore,
    lineage_store: LineageStore,
    *,
    job_id: str = "job-p-1",
    collaboration_id: str = "collab-p-1",
    runtime_id: str = "rt-p-1",
    parked_request_id: str = "req-p-1",
    repo_root: Path,
) -> DelegationJob:
    """Seed a job in needs_escalation with parked_request_id set."""
    handle = CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="execution",
        runtime_id=runtime_id,
        codex_thread_id="thr-p-1",
        claude_session_id="sess-1",
        repo_root=str(repo_root),
        created_at="2026-04-27T00:00:00Z",
        status="active",
    )
    lineage_store.create(handle)

    job = DelegationJob(
        job_id=job_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        base_commit="abc123",
        worktree_path=str(repo_root / "worktree"),
        promotion_state=None,
        status="running",
    )
    job_store.create(job)
    job_store.update_status(job_id, "needs_escalation")
    job_store.update_parked_request(job_id, parked_request_id)
    return job_store.get(job_id)  # type: ignore[return-value]


def _seed_pending_request(
    pending_request_store: Any,
    *,
    request_id: str = "req-p-1",
    collaboration_id: str = "collab-p-1",
    runtime_id: str = "rt-p-1",
    kind: PendingRequestKind = "unknown",
) -> None:
    """Create a PendingServerRequest in the store."""
    request = PendingServerRequest(
        request_id=request_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        codex_thread_id="thr-p-1",
        codex_turn_id="turn-p-1",
        item_id="item-p-1",
        kind=kind,
        requested_scope={"command": "rm -rf /"},
        available_decisions=("approve", "deny"),
        status="pending",
    )
    pending_request_store.create(request)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_poll_returns_null_escalation_on_unknown_kind_parked_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """poll() catches UnknownKindInEscalationProjection and returns
    DelegationPollResult(pending_escalation=None) after signaling abort."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        _runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    job = _make_needs_escalation_job(
        job_store,
        lineage_store,
        repo_root=repo_root,
    )
    _seed_pending_request(pending_request_store, kind="unknown")

    # Inject a mock registry that spies on signal_internal_abort.
    mock_registry = MagicMock(spec=ResolutionRegistry)
    mock_registry.signal_internal_abort.return_value = True
    monkeypatch.setattr(controller, "_registry", mock_registry)

    with caplog.at_level(logging.CRITICAL):
        result = controller.poll(job_id=job.job_id)

    assert isinstance(result, DelegationPollResult)
    assert result.pending_escalation is None
    assert result.job.status == "needs_escalation"

    mock_registry.signal_internal_abort.assert_called_once_with(
        "req-p-1",
        reason="unknown_kind_in_escalation_projection",
    )

    critical_records = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(critical_records) == 1
    record = critical_records[0]
    assert "delegation.poll: unknown-kind in escalation projection" in record.message
    assert record.__dict__["job_id"] == "job-p-1"
    assert record.__dict__["request_id"] == "req-p-1"
    assert "cause" in record.__dict__
    assert record.__dict__["abort_signaled"] is True


def test_poll_returns_null_escalation_even_when_signal_returns_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When signal_internal_abort returns False (operator won CAS), poll()
    still returns DelegationPollResult(pending_escalation=None). Proves L4:
    response not conditioned on signal return. Branch B's only artifact is
    a log line recording the False return."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        _runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    job = _make_needs_escalation_job(
        job_store,
        lineage_store,
        repo_root=repo_root,
    )
    _seed_pending_request(pending_request_store, kind="unknown")

    mock_registry = MagicMock(spec=ResolutionRegistry)
    mock_registry.signal_internal_abort.return_value = False
    monkeypatch.setattr(controller, "_registry", mock_registry)

    with caplog.at_level(logging.CRITICAL):
        result = controller.poll(job_id=job.job_id)

    assert isinstance(result, DelegationPollResult)
    assert result.pending_escalation is None

    mock_registry.signal_internal_abort.assert_called_once_with(
        "req-p-1",
        reason="unknown_kind_in_escalation_projection",
    )

    critical_records = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(critical_records) == 1
    record = critical_records[0]
    assert record.__dict__["abort_signaled"] is False


def test_poll_normal_kind_still_projects_escalation(
    tmp_path: Path,
) -> None:
    """A normal-kind parked request projects to PendingEscalationView
    without triggering the catch path or signal_internal_abort."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        _cp,
        _wm,
        job_store,
        lineage_store,
        _journal,
        _runtime_registry,
        pending_request_store,
    ) = _build_controller(tmp_path)

    job = _make_needs_escalation_job(
        job_store,
        lineage_store,
        repo_root=repo_root,
    )
    _seed_pending_request(pending_request_store, kind="command_approval")

    result = controller.poll(job_id=job.job_id)

    assert isinstance(result, DelegationPollResult)
    assert result.pending_escalation is not None
    assert result.pending_escalation.kind == "command_approval"
    assert result.pending_escalation.request_id == "req-p-1"

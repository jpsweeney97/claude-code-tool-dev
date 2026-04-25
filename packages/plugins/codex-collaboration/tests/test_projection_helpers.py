"""Packet 1: _project_request_to_view guards + _project_pending_escalation rewrite."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.delegation_controller import (
    DelegationController,
    UnknownKindInEscalationProjection,
    _ESCALATABLE_REQUEST_KINDS,
)
from server.models import (
    DelegationJob,
    PendingServerRequest,
)

# Module-local helpers (matching package precedent per W4: no conftest fixtures).
# _build_controller is already module-local in test_delegation_controller.py; we
# import it directly to avoid duplicating the 50-line helper.
from server.pending_request_store import PendingRequestStore
from tests.test_delegation_controller import _build_controller


def _build_controller_for_helpers(
    tmp_path: Path,
) -> tuple[DelegationController, PendingRequestStore]:
    """Thin wrapper that returns (controller, prs) for helper-level tests."""
    controller, _cp, _wm, _js, _ls, _j, _registry, prs = _build_controller(tmp_path)
    return controller, prs


def _build_simple_job(
    *,
    status: str = "needs_escalation",
    parked_request_id: str | None = None,
) -> DelegationJob:
    """Construct a minimal DelegationJob with sensible defaults."""
    return DelegationJob(
        job_id="test-job",
        runtime_id="test-rt",
        collaboration_id="test-collab",
        base_commit="abc123",
        worktree_path="/tmp/test-worktree",
        promotion_state=None,
        status=status,  # type: ignore[arg-type]
        parked_request_id=parked_request_id,
    )


def test_escalatable_set_has_three_literals() -> None:
    assert _ESCALATABLE_REQUEST_KINDS == frozenset(
        {"command_approval", "file_change", "request_user_input"}
    )


def test_project_request_to_view_raises_for_unknown_kind(tmp_path: Path) -> None:
    controller, *_ = _build_controller_for_helpers(tmp_path)
    req = PendingServerRequest(
        request_id="r1",
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="t1",
        codex_turn_id="tu1",
        item_id="i1",
        kind="unknown",
        requested_scope={},
    )
    with pytest.raises(UnknownKindInEscalationProjection):
        controller._project_request_to_view(req)


def test_project_request_to_view_admits_escalatable_kinds(tmp_path: Path) -> None:
    controller, *_ = _build_controller_for_helpers(tmp_path)
    for kind in ("command_approval", "file_change", "request_user_input"):
        req = PendingServerRequest(
            request_id=f"r-{kind}",
            runtime_id="rt1",
            collaboration_id="c1",
            codex_thread_id="t1",
            codex_turn_id="tu1",
            item_id="i1",
            kind=kind,
            requested_scope={},
        )
        view = controller._project_request_to_view(req)
        assert view.kind == kind


def test_project_pending_escalation_returns_none_for_terminal_job(tmp_path: Path) -> None:
    controller, *_ = _build_controller_for_helpers(tmp_path)
    for terminal in ("completed", "failed", "canceled", "unknown"):
        job = _build_simple_job(status=terminal)
        assert controller._project_pending_escalation(job) is None


def test_project_pending_escalation_returns_none_when_unparked(tmp_path: Path) -> None:
    controller, *_ = _build_controller_for_helpers(tmp_path)
    job = _build_simple_job(status="needs_escalation", parked_request_id=None)
    assert controller._project_pending_escalation(job) is None


def test_project_pending_escalation_returns_none_on_tombstone(tmp_path: Path) -> None:
    controller, prs, *_ = _build_controller_for_helpers(tmp_path)
    # Worker's mark_resolved landed but update_parked_request(None) hasn't —
    # the request is `resolved` but the job still shows parked_request_id.
    request = PendingServerRequest(
        request_id="r-tombstone",
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="t1",
        codex_turn_id="tu1",
        item_id="i1",
        kind="command_approval",
        requested_scope={},
        status="resolved",
    )
    prs.create(request)
    job = _build_simple_job(status="needs_escalation", parked_request_id="r-tombstone")
    assert controller._project_pending_escalation(job) is None


def test_project_pending_escalation_raises_for_unknown_kind_request(tmp_path: Path) -> None:
    controller, prs, *_ = _build_controller_for_helpers(tmp_path)
    request = PendingServerRequest(
        request_id="r-unknown",
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="t1",
        codex_turn_id="tu1",
        item_id="i1",
        kind="unknown",
        requested_scope={},
        status="pending",
    )
    prs.create(request)
    job = _build_simple_job(status="needs_escalation", parked_request_id="r-unknown")
    with pytest.raises(UnknownKindInEscalationProjection):
        controller._project_pending_escalation(job)


def test_project_pending_escalation_returns_view_on_happy_path(tmp_path: Path) -> None:
    controller, prs, *_ = _build_controller_for_helpers(tmp_path)
    request = PendingServerRequest(
        request_id="r-happy",
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="t1",
        codex_turn_id="tu1",
        item_id="i1",
        kind="command_approval",
        requested_scope={"cmd": "ls"},
        status="pending",
    )
    prs.create(request)
    job = _build_simple_job(status="needs_escalation", parked_request_id="r-happy")
    view = controller._project_pending_escalation(job)
    assert view is not None
    assert view.request_id == "r-happy"
    assert view.kind == "command_approval"
    assert view.requested_scope == {"cmd": "ls"}

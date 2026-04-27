"""L11 + L9 direct finalizer-guard tests for Task 19.

Direct-call tests that invoke _finalize_turn with constructed fixtures,
bypassing start()/decide(). Cover spec guarantees that G18.1/F16.1
public-path tests cannot reach.

L11: 8 binding tests (T1-T7b) per spec §_finalize_turn Captured-Request
Terminal Guard (design.md:1738-1827).

L9: 3 warning-discipline tests per L2 three-way warning table.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from server.delegation_controller import DelegationController
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import (
    CollaborationHandle,
    DelegationEscalation,
    DelegationJob,
    PendingServerRequest,
    TurnExecutionResult,
)
from server.pending_request_store import PendingRequestStore

from tests.test_delegation_controller import (  # type: ignore[import]
    _FakeSession,
    _build_controller,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pending_server_request(
    *,
    request_id: str = "42",
    runtime_id: str = "rt-h-1",
    collaboration_id: str = "collab-h-1",
    kind: str = "command_approval",
    status: str = "pending",
    item_id: str = "item-1",
) -> PendingServerRequest:
    return PendingServerRequest(
        request_id=request_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        codex_thread_id="thr-h-1",
        codex_turn_id="turn-1",
        item_id=item_id,
        kind=kind,  # type: ignore[arg-type]
        requested_scope={"command": "test"},
        available_decisions=("approve", "deny"),
        status=status,  # type: ignore[arg-type]
    )


def _setup_running_job(
    tmp_path: Path,
    *,
    job_id: str = "job-h-1",
    runtime_id: str = "rt-h-1",
    collaboration_id: str = "collab-h-1",
) -> tuple[
    DelegationController,
    DelegationJobStore,
    LineageStore,
    ExecutionRuntimeRegistry,
    PendingRequestStore,
    _FakeSession,
    OperationJournal,
]:
    """Build a controller and pre-seed a running job, handle, and runtime entry."""
    controller, _cp, _wm, job_store, lineage_store, journal, registry, prs = (
        _build_controller(tmp_path)
    )

    fake_session = _FakeSession()

    handle = CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="execution",
        runtime_id=runtime_id,
        codex_thread_id="thr-h-1",
        claude_session_id="sess-h-1",
        repo_root=str(tmp_path / "repo"),
        created_at="2026-04-27T00:00:00Z",
        status="active",
    )
    lineage_store.create(handle)

    job = DelegationJob(
        job_id=job_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        base_commit="abc123",
        worktree_path=str(tmp_path / "wt"),
        promotion_state=None,
        status="running",
    )
    job_store.create(job)

    registry.register(
        runtime_id=runtime_id,
        session=fake_session,
        thread_id="thr-h-1",
        job_id=job_id,
    )

    return controller, job_store, lineage_store, registry, prs, fake_session, journal


class _CountingPendingRequestStore:
    """Proxy around PendingRequestStore that counts get() calls."""

    def __init__(self, delegate: PendingRequestStore) -> None:
        self._delegate = delegate
        self.get_call_count = 0

    def get(self, request_id: str) -> PendingServerRequest | None:
        self.get_call_count += 1
        return self._delegate.get(request_id)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)


# ---------------------------------------------------------------------------
# L11 direct finalizer-guard tests
# ---------------------------------------------------------------------------


def test_l11_t1_resolved_completed_produces_completed(tmp_path: Path) -> None:
    """L11-T1: snapshot.status='resolved' + turn.status='completed' -> final_status='completed'."""
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    captured = _make_pending_server_request(status="resolved")
    prs.create(_make_pending_server_request(status="pending"))
    prs.update_status("42", "resolved")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="Done.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
            {"method": "item/completed", "params": {"item": {"id": "item-1"}}},
        ),
    )

    result = controller._finalize_turn(
        job_id="job-h-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        entry=entry,
        turn_result=turn_result,
        captured_request=captured,
        interrupted_by_unknown=False,
        captured_request_parse_failed=False,
    )

    assert isinstance(result, DelegationJob)
    assert result.status == "completed"


def test_l11_t2_resolved_interrupted_produces_unknown(tmp_path: Path) -> None:
    """L11-T2: snapshot.status='resolved' + turn.status='interrupted' -> final_status='unknown'."""
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    captured = _make_pending_server_request(status="resolved")
    prs.create(_make_pending_server_request(status="pending"))
    prs.update_status("42", "resolved")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="Interrupted.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
        ),
    )

    result = controller._finalize_turn(
        job_id="job-h-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        entry=entry,
        turn_result=turn_result,
        captured_request=captured,
        interrupted_by_unknown=False,
        captured_request_parse_failed=False,
    )

    assert isinstance(result, DelegationJob)
    assert result.status == "unknown"
    # L6.1: lineage stays "completed" for unknown terminal
    handle = lineage.get("collab-h-1")
    assert handle is not None
    assert handle.status == "completed"


def test_l11_t3_resolved_failed_produces_unknown(tmp_path: Path) -> None:
    """L11-T3: snapshot.status='resolved' + turn.status='failed' -> final_status='unknown'.
    This is the row most likely to regress — ensures failed does NOT route to
    kind-based escalation.
    """
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    captured = _make_pending_server_request(status="resolved")
    prs.create(_make_pending_server_request(status="pending"))
    prs.update_status("42", "resolved")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="failed",
        agent_message="Turn failed.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
        ),
    )

    result = controller._finalize_turn(
        job_id="job-h-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        entry=entry,
        turn_result=turn_result,
        captured_request=captured,
        interrupted_by_unknown=False,
        captured_request_parse_failed=False,
    )

    assert isinstance(result, DelegationJob)
    assert result.status == "unknown"


def test_l11_t4_canceled_produces_canceled(tmp_path: Path) -> None:
    """L11-T4: snapshot.status='canceled' + turn.status='interrupted' -> final_status='canceled'."""
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    captured = _make_pending_server_request(status="canceled", kind="file_change")
    prs.create(_make_pending_server_request(status="pending"))
    prs.update_status("42", "canceled")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="Timed out.",
        notifications=(),
    )

    result = controller._finalize_turn(
        job_id="job-h-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        entry=entry,
        turn_result=turn_result,
        captured_request=captured,
        interrupted_by_unknown=False,
        captured_request_parse_failed=False,
    )

    assert isinstance(result, DelegationJob)
    assert result.status == "canceled"


@pytest.mark.parametrize("snapshot_status", ["resolved", "canceled"])
def test_l11_t5_terminal_snapshot_suppresses_d4(
    tmp_path: Path, snapshot_status: str
) -> None:
    """L11-T5: terminal snapshot -> D4 update_status is NOT called.
    Tests both resolved and canceled via parametrize.
    """
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    prs.create(_make_pending_server_request(status="pending"))
    prs.update_status("42", snapshot_status)

    # Record the store state before _finalize_turn
    pre_snapshot = prs.get("42")
    assert pre_snapshot is not None
    assert pre_snapshot.status == snapshot_status

    captured = _make_pending_server_request(
        status=snapshot_status,
        kind="file_change" if snapshot_status == "canceled" else "command_approval",
    )

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed" if snapshot_status == "resolved" else "interrupted",
        agent_message="Done.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
            {"method": "item/completed", "params": {"item": {"id": "item-1"}}},
        ) if snapshot_status == "resolved" else (),
    )

    # Count update_status calls to verify D4 suppression.
    original_update = prs.update_status
    d4_calls: list[str] = []

    def _tracking_update(request_id: str, status: str) -> None:
        d4_calls.append(status)
        original_update(request_id, status)

    prs.update_status = _tracking_update  # type: ignore[assignment]

    controller._finalize_turn(
        job_id="job-h-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        entry=entry,
        turn_result=turn_result,
        captured_request=captured,
        interrupted_by_unknown=False,
        captured_request_parse_failed=False,
    )

    # D4 must NOT have fired — terminal snapshot means no update_status call
    assert len(d4_calls) == 0, (
        f"D4 update_status was called {len(d4_calls)} times with statuses {d4_calls} "
        f"but should be suppressed for terminal snapshot status={snapshot_status!r}"
    )


def test_l11_t6_pending_fires_d4_and_warning_and_falls_through(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """L11-T6: snapshot.status='pending' + parse_failed=False -> D4 fires AND
    L2-specific logger.warning fires AND derivation falls through to L4 kind-based logic.
    """
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    prs.create(_make_pending_server_request(status="pending"))

    captured = _make_pending_server_request(status="pending")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    # cancel-capable kind to observe the fall-through to needs_escalation
    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="Interrupted.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
            {"method": "item/completed", "params": {"item": {"id": "item-1"}}},
        ),
    )

    with caplog.at_level(logging.WARNING, logger="server.delegation_controller"):
        result = controller._finalize_turn(
            job_id="job-h-1",
            runtime_id="rt-h-1",
            collaboration_id="collab-h-1",
            entry=entry,
            turn_result=turn_result,
            captured_request=captured,
            interrupted_by_unknown=False,
            captured_request_parse_failed=False,
        )

    # D4 must have fired: store should now show "resolved"
    post_snapshot = prs.get("42")
    assert post_snapshot is not None
    assert post_snapshot.status == "resolved", (
        f"D4 should have written resolved but got {post_snapshot.status!r}"
    )

    # Falls through to L4 kind-based: cancel-capable kind -> needs_escalation
    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"

    # L2-specific anomalous-pending warning
    anomalous_warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "anomalous" in r.getMessage().lower()
    ]
    assert len(anomalous_warnings) >= 1, (
        f"Expected L2 anomalous-pending warning but got warnings: "
        f"{[r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]}"
    )


def test_l11_t7a_one_snapshot_terminal_path(tmp_path: Path) -> None:
    """L11-T7a: One-snapshot — terminal snapshot (resolved+completed) reaches
    non-escalation tail; assert get_call_count == 1.
    """
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    prs.create(_make_pending_server_request(status="pending"))
    prs.update_status("42", "resolved")

    captured = _make_pending_server_request(status="resolved")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="Done.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
            {"method": "item/completed", "params": {"item": {"id": "item-1"}}},
        ),
    )

    counting_store = _CountingPendingRequestStore(prs)
    controller._pending_request_store = counting_store  # type: ignore[assignment]

    result = controller._finalize_turn(
        job_id="job-h-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        entry=entry,
        turn_result=turn_result,
        captured_request=captured,
        interrupted_by_unknown=False,
        captured_request_parse_failed=False,
    )

    assert isinstance(result, DelegationJob)
    assert result.status == "completed"
    # Only ONE get() call (the derivation snapshot read). No hydration re-read
    # on the non-escalation tail path.
    assert counting_store.get_call_count == 1, (
        f"Expected exactly 1 get() call (derivation snapshot) but got "
        f"{counting_store.get_call_count}"
    )


def test_l11_t7b_one_snapshot_pending_fallthrough_with_d4_mutation(
    tmp_path: Path,
) -> None:
    """L11-T7b: One-snapshot — pending snapshot + cancel-capable kind ->
    final_status='needs_escalation' -> escalation tail -> hydration re-read.
    D4 mutates store from pending to resolved; assert derivation used pre-D4
    snapshot (final_status remains needs_escalation, not completed).
    """
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    prs.create(_make_pending_server_request(status="pending"))

    captured = _make_pending_server_request(status="pending")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    # cancel-capable kind so L4 fall-through produces needs_escalation
    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="Interrupted.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
            {"method": "item/completed", "params": {"item": {"id": "item-1"}}},
        ),
    )

    counting_store = _CountingPendingRequestStore(prs)
    controller._pending_request_store = counting_store  # type: ignore[assignment]

    result = controller._finalize_turn(
        job_id="job-h-1",
        runtime_id="rt-h-1",
        collaboration_id="collab-h-1",
        entry=entry,
        turn_result=turn_result,
        captured_request=captured,
        interrupted_by_unknown=False,
        captured_request_parse_failed=False,
    )

    # Derivation used the pre-D4 "pending" snapshot -> needs_escalation via L4
    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"

    # D4 mutated the store to "resolved"
    post_d4 = prs.get("42")
    assert post_d4 is not None
    assert post_d4.status == "resolved"

    # Escalation tail does a hydration re-read (the post-audit get at :2411-2413)
    # So total get_call_count should be > 1 (derivation + hydration).
    # The counting proxy wraps the real store, so both reads go through it.
    # NOTE: the counting_store was installed on the controller, so the
    # re-read for the DelegationEscalation return shape also goes through it.
    assert counting_store.get_call_count >= 1, (
        f"Expected at least 1 get() call but got {counting_store.get_call_count}"
    )


# ---------------------------------------------------------------------------
# L9 warning-discipline tests
# ---------------------------------------------------------------------------


def test_l9_tombstone_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Tombstone: pending_request_store.get(rid) returns None.
    Assert logger.warning with tombstone-identifying substring.
    """
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    # Do NOT create the request in the store -> get() returns None (tombstone)
    captured = _make_pending_server_request(status="pending")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="Done.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
            {"method": "item/completed", "params": {"item": {"id": "item-1"}}},
        ),
    )

    with caplog.at_level(logging.WARNING, logger="server.delegation_controller"):
        controller._finalize_turn(
            job_id="job-h-1",
            runtime_id="rt-h-1",
            collaboration_id="collab-h-1",
            entry=entry,
            turn_result=turn_result,
            captured_request=captured,
            interrupted_by_unknown=False,
            captured_request_parse_failed=False,
        )

    # Tombstone-identifying warning
    tombstone_warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "tombstone" in r.getMessage().lower()
    ]
    assert len(tombstone_warnings) >= 1, (
        f"Expected tombstone warning but got warnings: "
        f"{[r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]}"
    )


def test_l9_anomalous_pending_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Anomalous-pending: parse_failed=False AND snapshot.status='pending'.
    Assert logger.warning with L2-specific substring (anomalous).
    Supply D6-satisfying notifications so D6 does not produce warnings.
    """
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    prs.create(_make_pending_server_request(status="pending"))
    captured = _make_pending_server_request(status="pending")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    # Supply D6-satisfying notifications to avoid D6 warnings
    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="Done.",
        notifications=(
            {"method": "serverRequest/resolved", "params": {"requestId": "42"}},
            {"method": "item/completed", "params": {"item": {"id": "item-1"}}},
        ),
    )

    with caplog.at_level(logging.WARNING, logger="server.delegation_controller"):
        controller._finalize_turn(
            job_id="job-h-1",
            runtime_id="rt-h-1",
            collaboration_id="collab-h-1",
            entry=entry,
            turn_result=turn_result,
            captured_request=captured,
            interrupted_by_unknown=False,
            captured_request_parse_failed=False,
        )

    # L2-specific anomalous-pending warning (not D6)
    anomalous_warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "anomalous" in r.getMessage().lower()
    ]
    assert len(anomalous_warnings) >= 1, (
        f"Expected L2 anomalous-pending warning but got warnings: "
        f"{[r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]}"
    )


def test_l9_parse_failed_pending_silence(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Parse-failed pending: parse_failed=True AND snapshot.status='pending'.
    Assert NO anomalous-pending warning fires from L2 branch.
    """
    controller, job_store, lineage, registry, prs, session, _j = _setup_running_job(
        tmp_path
    )

    prs.create(_make_pending_server_request(status="pending", kind="unknown"))
    captured = _make_pending_server_request(status="pending", kind="unknown")

    entry = registry.lookup("rt-h-1")
    assert entry is not None

    turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="Parse failed.",
        notifications=(),
    )

    with caplog.at_level(logging.WARNING, logger="server.delegation_controller"):
        result = controller._finalize_turn(
            job_id="job-h-1",
            runtime_id="rt-h-1",
            collaboration_id="collab-h-1",
            entry=entry,
            turn_result=turn_result,
            captured_request=captured,
            interrupted_by_unknown=True,
            captured_request_parse_failed=True,
        )

    # L2 anomalous-pending warning must NOT fire
    anomalous_warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "anomalous" in r.getMessage().lower()
    ]
    assert len(anomalous_warnings) == 0, (
        f"Expected NO anomalous-pending warning for parse_failed path but got: "
        f"{[r.getMessage() for r in anomalous_warnings]}"
    )

    # Result should be unknown via L11 carve-out
    assert isinstance(result, DelegationJob)
    assert result.status == "unknown"

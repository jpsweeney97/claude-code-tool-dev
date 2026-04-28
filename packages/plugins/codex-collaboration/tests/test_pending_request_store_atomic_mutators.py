"""Packet 1: PendingRequestStore atomic mutators for timeout / dispatch-failure / internal-abort."""

from __future__ import annotations

from server.models import PendingServerRequest
from server.pending_request_store import PendingRequestStore


def _make_pending(rid: str = "r1") -> PendingServerRequest:
    return PendingServerRequest(
        request_id=rid,
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="th1",
        codex_turn_id="tu1",
        item_id="it1",
        kind="command_approval",
        requested_scope={},
    )


def test_record_timeout_succeeded_cancel_dispatch(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_timeout(
        "r1",
        response_payload={"decision": "cancel"},
        response_dispatch_at="2026-04-24T12:00:00Z",
        dispatch_result="succeeded",
        dispatch_error=None,
    )
    r = store.get("r1")
    assert r is not None
    assert r.timed_out is True
    assert r.status == "canceled"
    assert r.response_payload == {"decision": "cancel"}
    assert r.response_dispatch_at == "2026-04-24T12:00:00Z"
    assert r.dispatch_result == "succeeded"
    assert r.dispatch_error is None
    assert r.resolution_action is None
    assert r.interrupt_error is None
    assert r.resolved_at is None


def test_record_timeout_failed_cancel_dispatch_carries_error(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_timeout(
        "r1",
        response_payload={"decision": "cancel"},
        response_dispatch_at="2026-04-24T12:00:00Z",
        dispatch_result="failed",
        dispatch_error="BrokenPipeError: stdin closed",
    )
    r = store.get("r1")
    assert r is not None
    assert r.timed_out is True
    assert r.status == "canceled"
    assert r.dispatch_result == "failed"
    assert r.dispatch_error == "BrokenPipeError: stdin closed"


def test_record_timeout_non_cancel_capable_interrupt_path(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_timeout(
        "r1",
        response_payload=None,
        response_dispatch_at=None,
        dispatch_result=None,
        dispatch_error=None,
    )
    r = store.get("r1")
    assert r is not None
    assert r.timed_out is True
    assert r.status == "canceled"
    assert r.response_payload is None
    assert r.dispatch_result is None


def test_record_timeout_non_cancel_capable_interrupt_failed_carries_interrupt_error(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_timeout(
        "r1",
        response_payload=None,
        response_dispatch_at=None,
        dispatch_result=None,
        dispatch_error=None,
        interrupt_error="RuntimeError: session interrupt failed",
    )
    r = store.get("r1")
    assert r is not None
    assert r.timed_out is True
    assert r.status == "canceled"
    assert r.interrupt_error == "RuntimeError: session interrupt failed"
    assert r.dispatch_error is None


def test_record_dispatch_failure_atomic_fields(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_dispatch_failure(
        "r1",
        action="approve",
        payload={"decision": "accept"},
        dispatch_at="2026-04-24T12:00:00Z",
        dispatch_error="BrokenPipeError: pipe closed",
    )
    r = store.get("r1")
    assert r is not None
    assert r.status == "canceled"
    assert r.dispatch_result == "failed"
    assert r.dispatch_error == "BrokenPipeError: pipe closed"
    assert r.resolution_action == "approve"
    assert r.response_payload == {"decision": "accept"}
    assert r.response_dispatch_at == "2026-04-24T12:00:00Z"
    assert r.resolved_at is None


def test_record_dispatch_failure_atomicity_no_partial(tmp_path) -> None:
    """Partial-write replay safety: the single-append JSONL record either
    materializes all fields or none. We verify this indirectly by
    inspecting the store's raw JSONL for a single line per mutation."""
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    before_lines = store._store_path.read_text(encoding="utf-8").splitlines()
    store.record_dispatch_failure(
        "r1",
        action="approve",
        payload={},
        dispatch_at="t",
        dispatch_error="X: y",
    )
    after_lines = store._store_path.read_text(encoding="utf-8").splitlines()
    # Exactly ONE new line appended — atomicity is encoded in the single-write.
    assert len(after_lines) == len(before_lines) + 1


def test_record_internal_abort_sets_canceled_and_reason(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_internal_abort(
        "r1", reason="parked_projection_invariant_violation"
    )
    r = store.get("r1")
    assert r is not None
    assert r.status == "canceled"
    assert r.internal_abort_reason == "parked_projection_invariant_violation"
    assert r.resolution_action is None
    assert r.response_payload is None
    assert r.response_dispatch_at is None
    assert r.dispatch_result is None
    assert r.resolved_at is None


def test_record_internal_abort_round_trip_via_replay(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_internal_abort("r1", reason="unknown_kind_in_escalation_projection")
    reopened = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    r = reopened.get("r1")
    assert r is not None
    assert r.internal_abort_reason == "unknown_kind_in_escalation_projection"
    assert r.status == "canceled"

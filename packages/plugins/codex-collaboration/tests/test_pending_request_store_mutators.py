"""Packet 1: PendingRequestStore mutators for the success-path lifecycle."""

from __future__ import annotations

import pytest

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
        requested_scope={"path": "/x"},
        available_decisions=("approve", "deny"),
    )


def test_mark_resolved_sets_status_and_timestamp(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.mark_resolved("r1", resolved_at="2026-04-24T12:00:00Z")
    result = store.get("r1")
    assert result is not None
    assert result.status == "resolved"
    assert result.resolved_at == "2026-04-24T12:00:00Z"


def test_record_response_dispatch_sets_four_fields(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_response_dispatch(
        "r1",
        action="approve",
        payload={"decision": "accept"},
        dispatch_at="2026-04-24T12:00:00Z",
    )
    result = store.get("r1")
    assert result is not None
    assert result.resolution_action == "approve"
    assert result.response_payload == {"decision": "accept"}
    assert result.response_dispatch_at == "2026-04-24T12:00:00Z"
    assert result.dispatch_result == "succeeded"  # hardcoded by the mutator


def test_record_response_dispatch_does_not_change_status(tmp_path) -> None:
    # Status transitions via mark_resolved; record_response_dispatch is
    # the transport-write stamp only.
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_response_dispatch(
        "r1", action="approve", payload={}, dispatch_at="2026-04-24T12:00:00Z"
    )
    result = store.get("r1")
    assert result is not None
    assert result.status == "pending"


def test_record_protocol_echo_sets_signals_and_timestamp(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_protocol_echo(
        "r1",
        signals=("serverRequest/resolved", "item/completed"),
        observed_at="2026-04-24T12:00:01Z",
    )
    result = store.get("r1")
    assert result is not None
    assert result.protocol_echo_signals == (
        "serverRequest/resolved",
        "item/completed",
    )
    assert result.protocol_echo_observed_at == "2026-04-24T12:00:01Z"


def test_mutators_round_trip_across_replay(tmp_path) -> None:
    """Force a fresh store instance (new replay) and confirm each mutator's
    effect persists."""
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_response_dispatch(
        "r1", action="approve", payload={"k": "v"}, dispatch_at="t1"
    )
    store.mark_resolved("r1", resolved_at="t2")
    store.record_protocol_echo("r1", signals=("x",), observed_at="t3")

    reopened = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    result = reopened.get("r1")
    assert result is not None
    assert result.status == "resolved"
    assert result.resolved_at == "t2"
    assert result.resolution_action == "approve"
    assert result.response_payload == {"k": "v"}
    assert result.response_dispatch_at == "t1"
    assert result.dispatch_result == "succeeded"
    assert result.protocol_echo_signals == ("x",)
    assert result.protocol_echo_observed_at == "t3"


def test_record_protocol_echo_replay_handles_null_signals(tmp_path) -> None:
    """A JSONL record with protocol_echo_signals=null must not crash replay."""
    import json

    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    # Inject a corrupted record (null signals) directly into the JSONL log.
    with store._store_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "op": "record_protocol_echo",
                    "request_id": "r1",
                    "protocol_echo_signals": None,
                    "protocol_echo_observed_at": "2026-04-24T12:00:00Z",
                }
            )
            + "\n"
        )

    reopened = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    result = reopened.get("r1")
    assert result is not None
    assert result.protocol_echo_signals == ()
    assert result.protocol_echo_observed_at == "2026-04-24T12:00:00Z"

"""Packet 1: PendingServerRequest gains 11 new fields, all nullable / safe-default."""

from __future__ import annotations

from dataclasses import fields

from server.models import PendingServerRequest


def test_has_resolution_action_field() -> None:
    req = PendingServerRequest(
        request_id="r", runtime_id="rt", collaboration_id="c",
        codex_thread_id="t", codex_turn_id="tu", item_id="i",
        kind="command_approval", requested_scope={},
    )
    assert req.resolution_action is None


def test_has_all_new_fields_with_safe_defaults() -> None:
    field_names = {f.name for f in fields(PendingServerRequest)}
    new_fields = {
        "resolution_action",
        "response_payload",
        "response_dispatch_at",
        "dispatch_result",
        "dispatch_error",
        "interrupt_error",
        "resolved_at",
        "protocol_echo_signals",
        "protocol_echo_observed_at",
        "timed_out",
        "internal_abort_reason",
    }
    missing = new_fields - field_names
    assert not missing, f"missing fields: {missing}"


def test_default_values_are_safe() -> None:
    req = PendingServerRequest(
        request_id="r", runtime_id="rt", collaboration_id="c",
        codex_thread_id="t", codex_turn_id="tu", item_id="i",
        kind="command_approval", requested_scope={},
    )
    assert req.resolution_action is None
    assert req.response_payload is None
    assert req.response_dispatch_at is None
    assert req.dispatch_result is None
    assert req.dispatch_error is None
    assert req.interrupt_error is None
    assert req.resolved_at is None
    assert req.protocol_echo_signals == ()
    assert req.protocol_echo_observed_at is None
    assert req.timed_out is False
    assert req.internal_abort_reason is None


def test_existing_records_replay_cleanly_with_none_defaults(tmp_path) -> None:
    """Legacy records (pre-Packet 1) must replay without KeyError on the
    new fields. Simulate by writing a record with ONLY the old-shape keys
    and verifying replay materializes a PendingServerRequest with new
    fields at their defaults."""
    from server.pending_request_store import PendingRequestStore

    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    # Hand-craft a legacy record without the new fields and append it.
    import json
    legacy_record = {
        "op": "create",
        "request_id": "legacy-r1",
        "runtime_id": "rt1",
        "collaboration_id": "c1",
        "codex_thread_id": "t1",
        "codex_turn_id": "tu1",
        "item_id": "i1",
        "kind": "command_approval",
        "requested_scope": {"path": "/x"},
        "available_decisions": ["approve", "deny"],
        "status": "pending",
        # NO new fields — simulates pre-Packet-1 data
    }
    store._store_path.write_text(
        json.dumps(legacy_record, sort_keys=True) + "\n", encoding="utf-8"
    )
    replayed = store.get("legacy-r1")
    assert replayed is not None
    assert replayed.resolution_action is None
    assert replayed.protocol_echo_signals == ()
    assert replayed.timed_out is False

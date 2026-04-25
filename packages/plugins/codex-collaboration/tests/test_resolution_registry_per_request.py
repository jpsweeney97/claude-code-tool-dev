"""Packet 1: ResolutionRegistry per-request channel — state machine + CAS + wake."""

from __future__ import annotations

import threading
import time

from server.resolution_registry import (
    DecisionResolution,
    InternalAbort,
    ResolutionRegistry,
    Resolution,
)


def test_decision_resolution_fields() -> None:
    r = DecisionResolution(
        payload={"decision": "accept"}, kind="command_approval", is_timeout=False
    )
    assert r.payload == {"decision": "accept"}
    assert r.kind == "command_approval"
    assert r.is_timeout is False


def test_internal_abort_carries_reason() -> None:
    a = InternalAbort(reason="parked_projection_invariant_violation")
    assert a.reason == "parked_projection_invariant_violation"


def test_resolution_is_union_of_both() -> None:
    r1: Resolution = DecisionResolution(payload={}, kind="command_approval")
    r2: Resolution = InternalAbort(reason="x")
    assert isinstance(r1, DecisionResolution)
    assert isinstance(r2, InternalAbort)


def test_register_creates_awaiting_entry() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    # Implementation detail — test only what's observable via the public
    # interface.
    assert reg._is_awaiting("r1")  # test-only introspection


def test_reserve_wins_cas_returns_token() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    token = reg.reserve(
        "r1", DecisionResolution(payload={"decision": "accept"}, kind="command_approval")
    )
    assert token is not None


def test_reserve_loses_cas_returns_none() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    first = reg.reserve(
        "r1", DecisionResolution(payload={}, kind="command_approval")
    )
    assert first is not None
    # Second reserve on a non-awaiting entry returns None.
    second = reg.reserve(
        "r1", DecisionResolution(payload={}, kind="command_approval")
    )
    assert second is None


def test_reserve_on_unregistered_entry_returns_none() -> None:
    reg = ResolutionRegistry()
    # No register() call — reserve must return None.
    token = reg.reserve(
        "not-registered", DecisionResolution(payload={}, kind="command_approval")
    )
    assert token is None


def test_commit_signal_wakes_worker_wait() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)

    result: list[Resolution] = []

    def worker() -> None:
        result.append(reg.wait("r1"))

    t = threading.Thread(target=worker)
    t.start()
    # Small delay to ensure worker is blocked on wait().
    time.sleep(0.05)
    token = reg.reserve(
        "r1", DecisionResolution(payload={"decision": "accept"}, kind="command_approval")
    )
    assert token is not None
    reg.commit_signal(token)
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], DecisionResolution)
    assert result[0].payload == {"decision": "accept"}


def test_abort_reservation_restores_awaiting() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    token = reg.reserve("r1", DecisionResolution(payload={}, kind="command_approval"))
    assert token is not None
    reg.abort_reservation(token)
    # Entry is back in awaiting; a second reserve must succeed.
    token2 = reg.reserve("r1", DecisionResolution(payload={}, kind="command_approval"))
    assert token2 is not None


def test_double_abort_is_idempotent() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    token = reg.reserve("r1", DecisionResolution(payload={}, kind="command_approval"))
    assert token is not None
    reg.abort_reservation(token)
    reg.abort_reservation(token)  # no raise


def test_signal_internal_abort_wakes_worker_with_abort() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)

    result: list[Resolution] = []

    def worker() -> None:
        result.append(reg.wait("r1"))

    t = threading.Thread(target=worker)
    t.start()
    time.sleep(0.05)
    returned = reg.signal_internal_abort("r1", reason="parked_projection_invariant_violation")
    assert returned is True
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], InternalAbort)
    assert result[0].reason == "parked_projection_invariant_violation"


def test_signal_internal_abort_loses_to_operator_decide() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    # Operator wins the reservation first.
    token = reg.reserve(
        "r1", DecisionResolution(payload={"decision": "accept"}, kind="command_approval")
    )
    assert token is not None
    # Later abort signal is a no-op.
    returned = reg.signal_internal_abort("r1", reason="late-abort")
    assert returned is False


def test_signal_internal_abort_idempotent() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    first = reg.signal_internal_abort("r1", reason="x")
    second = reg.signal_internal_abort("r1", reason="y")
    assert first is True
    assert second is False


def test_discard_removes_entry_idempotent() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    reg.discard("r1")
    reg.discard("r1")  # idempotent


def test_timer_fires_synthetic_timeout_resolution() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=0.1)

    result: list[Resolution] = []

    def worker() -> None:
        result.append(reg.wait("r1"))

    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], DecisionResolution)
    assert result[0].is_timeout is True
    assert result[0].kind == "command_approval"  # NEW: pins authoritative kind


def test_late_timer_against_decided_entry_is_noop() -> None:
    # Timer tries to reserve an entry that's already been decided — must be a
    # no-op (no journal, no wake, no side effect).
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=0.5)
    # Operator wins.
    token = reg.reserve(
        "r1", DecisionResolution(payload={}, kind="command_approval")
    )
    assert token is not None
    reg.commit_signal(token)
    # Let the timer fire — it should observe non-awaiting state via
    # reserve() returning None and no-op.
    time.sleep(0.7)
    # Registry still reflects the operator's decision (no state change).
    assert "r1" in reg._entries
    assert reg._is_awaiting("r1") is False

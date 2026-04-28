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
    """Late timer firing on a decided entry is a no-op: the worker receives
    the operator's resolution exactly once, and the entry does not return
    to awaiting.
    """
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=0.5)

    operator_resolution = DecisionResolution(
        payload={"decision": "accept"}, kind="command_approval"
    )
    result: list[Resolution] = []

    def worker() -> None:
        result.append(reg.wait("r1"))

    t = threading.Thread(target=worker)
    t.start()
    time.sleep(0.05)
    token = reg.reserve("r1", operator_resolution)
    assert token is not None
    reg.commit_signal(token)
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert result[0] == operator_resolution
    # Now wait for the would-be late timer to fire — must be a no-op.
    time.sleep(0.7)
    # Worker received exactly one resolution (no double-wake).
    assert len(result) == 1
    assert result[0] == operator_resolution
    # Entry remains in consuming state — never returns to awaiting.
    assert reg._is_awaiting("r1") is False


def test_stale_token_after_discard_and_reregister_is_rejected() -> None:
    """Generation counter rejects stale tokens whose entry was discarded
    and re-registered with the same request_id.

    Pins the F4 closeout protection: without per-register generation
    increments, the old token would silently commit_signal into the
    new entry's state, polluting the new reservation.
    """
    reg = ResolutionRegistry()

    # Step 1: register + reserve, capture the OLD token.
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)
    old_resolution = DecisionResolution(
        payload={"decision": "accept"}, kind="command_approval"
    )
    old_token = reg.reserve("r1", old_resolution)
    assert old_token is not None

    # Step 2: discard the entry (without commit/abort).
    reg.discard("r1")

    # Step 3: re-register the same request_id.
    reg.register("r1", job_id="j1", kind="command_approval", timeout_seconds=900)

    # Step 4: reserve on the new entry, capture the NEW token.
    new_resolution = DecisionResolution(
        payload={"decision": "deny"}, kind="command_approval"
    )
    new_token = reg.reserve("r1", new_resolution)
    assert new_token is not None
    assert new_token.generation != old_token.generation

    # Step 5: stale commit on the old token must not affect the new entry.
    reg.commit_signal(old_token)

    # Step 6: spawn a worker — it should still be blocked because the new
    # entry remains in reserved state (old token's commit was rejected).
    result: list[Resolution] = []

    def worker() -> None:
        result.append(reg.wait("r1"))

    t = threading.Thread(target=worker)
    t.start()
    time.sleep(0.05)
    assert t.is_alive()  # worker has not been woken
    assert len(result) == 0

    # Step 7: commit the new token; worker receives the new resolution
    # (not the stale old one).
    reg.commit_signal(new_token)
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert result[0] == new_resolution

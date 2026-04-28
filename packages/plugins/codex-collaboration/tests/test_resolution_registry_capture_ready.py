"""Packet 1: ResolutionRegistry per-job capture-ready channel + ParkedCaptureResult."""

from __future__ import annotations

import threading
import time

import pytest

from server.resolution_registry import (
    Parked,
    ParkedCaptureResult,
    ResolutionRegistry,
    StartWaitElapsed,
    TurnCompletedWithoutCapture,
    TurnTerminalWithoutEscalation,
    WorkerFailed,
)


def test_parked_carries_request_id() -> None:
    p = Parked(request_id="r1")
    assert p.request_id == "r1"


def test_turn_completed_without_capture_is_empty() -> None:
    TurnCompletedWithoutCapture()  # no fields


def test_turn_terminal_without_escalation_fields() -> None:
    t = TurnTerminalWithoutEscalation(
        job_status="unknown",
        reason="unknown_kind_parse_failure",
        request_id="r-audit",
    )
    assert t.job_status == "unknown"
    assert t.reason == "unknown_kind_parse_failure"
    assert t.request_id == "r-audit"


def test_worker_failed_carries_exception() -> None:
    exc = RuntimeError("boom")
    wf = WorkerFailed(error=exc)
    assert wf.error is exc


def test_start_wait_elapsed_is_empty() -> None:
    StartWaitElapsed()


def test_announce_parked_wakes_main_thread() -> None:
    reg = ResolutionRegistry()
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.05)
    reg.announce_parked("j1", request_id="r1")
    t.join(timeout=3.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], Parked)
    assert result[0].request_id == "r1"


def test_announce_turn_completed_empty_surfaces_variant() -> None:
    reg = ResolutionRegistry()
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.05)
    reg.announce_turn_completed_empty("j1")
    t.join(timeout=3.0)
    assert not t.is_alive()
    assert isinstance(result[0], TurnCompletedWithoutCapture)


def test_announce_turn_terminal_without_escalation() -> None:
    reg = ResolutionRegistry()
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.05)
    reg.announce_turn_terminal_without_escalation(
        "j1", status="unknown", reason="unknown_kind_parse_failure", request_id="r-audit"
    )
    t.join(timeout=3.0)
    assert not t.is_alive()
    assert isinstance(result[0], TurnTerminalWithoutEscalation)
    assert result[0].job_status == "unknown"
    assert result[0].reason == "unknown_kind_parse_failure"
    assert result[0].request_id == "r-audit"


def test_announce_worker_failed_surfaces_exception() -> None:
    reg = ResolutionRegistry()
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.05)
    reg.announce_worker_failed("j1", error=RuntimeError("boom"))
    t.join(timeout=3.0)
    assert not t.is_alive()
    assert isinstance(result[0], WorkerFailed)
    assert isinstance(result[0].error, RuntimeError)


def test_start_wait_elapsed_when_budget_expires_without_signal() -> None:
    reg = ResolutionRegistry()
    result = reg.wait_for_parked("j1", timeout_seconds=0.1)
    assert isinstance(result, StartWaitElapsed)
    # O1=(b) lifecycle: channel popped on return.
    assert "j1" not in reg._capture_channels


def test_late_announce_after_start_wait_elapsed_no_raise() -> None:
    """Late announce_* call after wait_for_parked resolves must not raise."""
    reg = ResolutionRegistry()
    result = reg.wait_for_parked("j1", timeout_seconds=0.1)
    assert isinstance(result, StartWaitElapsed)
    # Subsequent announce_* calls are no-op warnings, never raises.
    reg.announce_parked("j1", request_id="r1")
    reg.announce_turn_completed_empty("j1")
    reg.announce_turn_terminal_without_escalation(
        "j1", status="unknown", reason="r", request_id=None
    )
    reg.announce_worker_failed("j1", error=RuntimeError("late"))


def test_capture_ready_channels_are_per_job() -> None:
    """Two jobs have independent channels."""
    reg = ResolutionRegistry()
    results: dict[str, ParkedCaptureResult] = {}

    def main(job_id: str) -> None:
        results[job_id] = reg.wait_for_parked(job_id, timeout_seconds=2.0)

    t1 = threading.Thread(target=main, args=("j1",))
    t2 = threading.Thread(target=main, args=("j2",))
    t1.start()
    t2.start()
    time.sleep(0.05)
    reg.announce_parked("j1", request_id="r1")
    reg.announce_turn_completed_empty("j2")
    t1.join(timeout=3.0)
    t2.join(timeout=3.0)
    assert not t1.is_alive()
    assert not t2.is_alive()
    assert isinstance(results["j1"], Parked)
    assert isinstance(results["j2"], TurnCompletedWithoutCapture)


def test_wait_for_parked_duplicate_job_id_raises() -> None:
    """Second wait_for_parked on a job_id whose channel is already in flight
    raises RuntimeError with the project-convention error format. Pins the
    public error surface for duplicate-detection.
    """
    reg = ResolutionRegistry()

    # Spawn the first wait so the channel is registered and in-flight.
    def first_wait() -> None:
        reg.wait_for_parked("j1", timeout_seconds=2.0)

    t1 = threading.Thread(target=first_wait)
    t1.start()
    time.sleep(0.05)

    # Second wait on the same job_id must raise.
    with pytest.raises(RuntimeError, match="wait_for_parked failed: duplicate"):
        reg.wait_for_parked("j1", timeout_seconds=0.1)

    # Cleanup: wake the first wait so the test suite does not hang.
    reg.announce_turn_completed_empty("j1")
    t1.join(timeout=3.0)
    assert not t1.is_alive()


# --------------------------------------------------------------- pre-open tests


def test_open_then_announce_then_wait_preserves_early_signal() -> None:
    """The capture-race fix invariant. Without pre-open, an announce_* that
    fires before wait_for_parked is dropped by _deliver_capture_outcome's
    channel-is-None branch. With pre-open, the channel exists at the moment
    the announce arrives, so the outcome is buffered on the channel; a
    subsequent wait_for_parked observes the already-set Event and returns
    the buffered outcome immediately.
    """
    reg = ResolutionRegistry()

    # Pre-open BEFORE any announce. Production analog: this is what
    # DelegationController.start() does immediately before spawn_worker.
    reg.open_capture_channel("j1")

    # Announce arrives FIRST -- mimics a fast worker that parks before the
    # main thread reaches wait_for_parked.
    reg.announce_parked("j1", request_id="r-early")

    # Wait now returns immediately with the early-buffered outcome.
    result = reg.wait_for_parked("j1", timeout_seconds=0.1)
    assert isinstance(result, Parked)
    assert result.request_id == "r-early"

    # Channel is popped on return — late announce_* must warn-and-noop, not
    # mutate any state. Re-asserting the O1=(b) lifecycle invariant after
    # the new pre-open path.
    assert "j1" not in reg._capture_channels


def test_open_then_wait_then_announce_works() -> None:
    """Pre-open path with the announce arriving AFTER wait_for_parked has
    attached. Proves the same channel object is reused — wait does not
    create a duplicate after pre-open.
    """
    reg = ResolutionRegistry()
    reg.open_capture_channel("j1")
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    # Give wait a moment to attach to the pre-opened channel.
    time.sleep(0.05)
    reg.announce_parked("j1", request_id="r-late")
    t.join(timeout=3.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], Parked)
    assert result[0].request_id == "r-late"


def test_open_capture_channel_duplicate_raises() -> None:
    """Second open_capture_channel on a job_id that already has a channel
    raises -- protects against double-pre-open in start() retry paths.
    """
    reg = ResolutionRegistry()
    reg.open_capture_channel("j1")
    with pytest.raises(
        RuntimeError, match="open_capture_channel failed: duplicate"
    ):
        reg.open_capture_channel("j1")


def test_open_then_double_wait_raises_duplicate_waiter() -> None:
    """Pre-open + first wait attaches the waiter. A second concurrent
    wait_for_parked on the same job_id must still raise duplicate-waiter
    -- the pre-open path does not loosen this invariant, only refines its
    trigger condition (waiter_attached, not channel-existence).
    """
    reg = ResolutionRegistry()
    reg.open_capture_channel("j1")

    def first_wait() -> None:
        reg.wait_for_parked("j1", timeout_seconds=2.0)

    t1 = threading.Thread(target=first_wait)
    t1.start()
    time.sleep(0.05)

    with pytest.raises(RuntimeError, match="wait_for_parked failed: duplicate"):
        reg.wait_for_parked("j1", timeout_seconds=0.1)

    # Cleanup so the suite does not hang on the first wait.
    reg.announce_turn_completed_empty("j1")
    t1.join(timeout=3.0)
    assert not t1.is_alive()


def test_open_then_announce_buffers_all_outcome_variants() -> None:
    """Each ParkedCaptureResult variant survives the pre-open + early-announce
    path. Pins the buffering semantics across the full variant set so a
    future variant addition forces explicit consideration of pre-open.
    """
    # Parked
    reg1 = ResolutionRegistry()
    reg1.open_capture_channel("j1")
    reg1.announce_parked("j1", request_id="r-x")
    out1 = reg1.wait_for_parked("j1", timeout_seconds=0.1)
    assert isinstance(out1, Parked)
    assert out1.request_id == "r-x"

    # TurnCompletedWithoutCapture
    reg2 = ResolutionRegistry()
    reg2.open_capture_channel("j2")
    reg2.announce_turn_completed_empty("j2")
    out2 = reg2.wait_for_parked("j2", timeout_seconds=0.1)
    assert isinstance(out2, TurnCompletedWithoutCapture)

    # TurnTerminalWithoutEscalation
    reg3 = ResolutionRegistry()
    reg3.open_capture_channel("j3")
    reg3.announce_turn_terminal_without_escalation(
        "j3",
        status="unknown",
        reason="unknown_kind_parse_failure",
        request_id="r-audit",
    )
    out3 = reg3.wait_for_parked("j3", timeout_seconds=0.1)
    assert isinstance(out3, TurnTerminalWithoutEscalation)
    assert out3.reason == "unknown_kind_parse_failure"

    # WorkerFailed
    reg4 = ResolutionRegistry()
    reg4.open_capture_channel("j4")
    reg4.announce_worker_failed("j4", error=RuntimeError("boom"))
    out4 = reg4.wait_for_parked("j4", timeout_seconds=0.1)
    assert isinstance(out4, WorkerFailed)
    assert isinstance(out4.error, RuntimeError)

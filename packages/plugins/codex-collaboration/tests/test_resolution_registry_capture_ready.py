"""Packet 1: ResolutionRegistry per-job capture-ready channel + ParkedCaptureResult."""

from __future__ import annotations

import threading
import time

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
    assert isinstance(results["j1"], Parked)
    assert isinstance(results["j2"], TurnCompletedWithoutCapture)

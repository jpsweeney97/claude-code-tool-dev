"""Packet 1: _WorkerTerminalBranchSignal frozen-dataclass exception carrying reason."""

from __future__ import annotations

import pytest

from server.delegation_controller import (
    _WorkerTerminalBranchSignal,
)


def test_is_exception_subclass() -> None:
    assert issubclass(_WorkerTerminalBranchSignal, Exception)


def test_carries_reason_field() -> None:
    signal = _WorkerTerminalBranchSignal(reason="internal_abort")
    assert signal.reason == "internal_abort"


def test_accepts_all_six_spec_reasons() -> None:
    for reason in (
        "internal_abort",
        "dispatch_failed",
        "timeout_interrupt_failed",
        "timeout_interrupt_succeeded",
        "timeout_cancel_dispatch_failed",
        "unknown_kind_interrupt_transport_failure",
    ):
        signal = _WorkerTerminalBranchSignal(reason=reason)
        assert signal.reason == reason


def test_is_raisable_and_catchable() -> None:
    with pytest.raises(_WorkerTerminalBranchSignal) as exc_info:
        raise _WorkerTerminalBranchSignal(reason="dispatch_failed")
    assert exc_info.value.reason == "dispatch_failed"


def test_does_not_propagate_through_runtime_error_except() -> None:
    # _WorkerTerminalBranchSignal is not RuntimeError — a narrower except
    # clause above `except Exception` must be placed to catch it before
    # the generic _mark_execution_unknown_and_cleanup handler fires.
    with pytest.raises(_WorkerTerminalBranchSignal):
        try:
            raise _WorkerTerminalBranchSignal(reason="internal_abort")
        except RuntimeError:  # would incorrectly swallow if it were RuntimeError
            pytest.fail("sentinel must not be caught by RuntimeError handler")

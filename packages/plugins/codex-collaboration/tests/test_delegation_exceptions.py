"""Packet 1: DelegationStartError + UnknownKindInEscalationProjection exception types."""

from __future__ import annotations

import pytest

from server.delegation_controller import (
    DelegationStartError,
    UnknownKindInEscalationProjection,
)


def test_delegation_start_error_is_runtime_error_subclass() -> None:
    exc = DelegationStartError(reason="worker_failed_before_capture")
    assert isinstance(exc, RuntimeError)


def test_delegation_start_error_str_is_reason_alone_when_no_message() -> None:
    assert str(DelegationStartError(reason="foo")) == "foo"


def test_delegation_start_error_str_is_reason_colon_message_when_set() -> None:
    assert str(DelegationStartError(reason="foo", message="bar")) == "foo: bar"


def test_delegation_start_error_preserves_cause_and_dunder_cause() -> None:
    original = ValueError("original")
    try:
        raise DelegationStartError(reason="foo", cause=original) from original
    except DelegationStartError as exc:
        assert exc.cause is original
        assert exc.__cause__ is original


def test_delegation_start_error_reason_is_attribute() -> None:
    exc = DelegationStartError(reason="parked_projection_invariant_violation")
    assert exc.reason == "parked_projection_invariant_violation"


def test_unknown_kind_in_escalation_projection_is_exception_not_runtime_error() -> None:
    # Must NOT be RuntimeError subclass so narrower except clauses don't
    # swallow it through the RuntimeError branch.
    exc = UnknownKindInEscalationProjection("msg")
    assert isinstance(exc, Exception)
    assert not isinstance(exc, RuntimeError)


def test_unknown_kind_exception_carries_message() -> None:
    exc = UnknownKindInEscalationProjection("kind=unknown request_id=abc")
    assert str(exc) == "kind=unknown request_id=abc"

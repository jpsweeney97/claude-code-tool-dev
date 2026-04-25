"""Packet 1: DelegationDecisionResult new 3-field shape."""

from __future__ import annotations

from dataclasses import fields

from server.models import DelegationDecisionResult


def test_has_exactly_three_fields() -> None:
    names = {f.name for f in fields(DelegationDecisionResult)}
    assert names == {"decision_accepted", "job_id", "request_id"}


def test_decision_accepted_is_bool() -> None:
    r = DelegationDecisionResult(
        decision_accepted=True, job_id="j1", request_id="r1"
    )
    assert r.decision_accepted is True


def test_no_pending_escalation_or_agent_context() -> None:
    # These fields must not exist post-Packet-1.
    r = DelegationDecisionResult(
        decision_accepted=True, job_id="j1", request_id="r1"
    )
    assert not hasattr(r, "pending_escalation")
    assert not hasattr(r, "agent_context")
    assert not hasattr(r, "job")
    assert not hasattr(r, "decision")
    assert not hasattr(r, "resumed")

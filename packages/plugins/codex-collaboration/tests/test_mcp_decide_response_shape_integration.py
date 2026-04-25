"""Packet 1: MCP serializer emits the 3-field DelegationDecisionResult shape."""

from __future__ import annotations

from dataclasses import asdict

from server.models import DelegationDecisionResult


def test_asdict_produces_three_keys() -> None:
    r = DelegationDecisionResult(
        decision_accepted=True, job_id="j1", request_id="r1"
    )
    payload = asdict(r)
    assert set(payload.keys()) == {"decision_accepted", "job_id", "request_id"}
    assert payload["decision_accepted"] is True
    assert payload["job_id"] == "j1"
    assert payload["request_id"] == "r1"

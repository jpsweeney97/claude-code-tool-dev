"""Tests for read_events delegation_outcome support."""

from __future__ import annotations

from scripts.event_schema import REQUIRED_FIELDS_BY_EVENT
from scripts.read_events import validate_event, classify


class TestDelegationOutcomeSchema:
    """delegation_outcome in REQUIRED_FIELDS_BY_EVENT."""

    def test_delegation_outcome_in_required_fields(self) -> None:
        assert "delegation_outcome" in REQUIRED_FIELDS_BY_EVENT

    def test_required_fields_complete(self) -> None:
        expected = frozenset({
            "schema_version", "event", "ts", "consultation_id",
            "session_id", "thread_id", "dispatched", "sandbox",
            "full_auto", "credential_blocked", "dirty_tree_blocked",
            "readable_secret_file_blocked", "commands_run_count",
            "exit_code", "termination_reason",
            "model", "reasoning_effort",  # F10: nullable but present
        })
        assert REQUIRED_FIELDS_BY_EVENT["delegation_outcome"] == expected


class TestDelegationOutcomeValidation:
    """validate_event with delegation_outcome events."""

    def _make_delegation_event(self, **overrides: object) -> dict:
        event = {
            "schema_version": "0.1.0",
            "event": "delegation_outcome",
            "ts": "2026-03-06T12:00:00Z",
            "consultation_id": "test-uuid",
            "session_id": None,
            "thread_id": None,
            "dispatched": True,
            "sandbox": "workspace-write",
            "model": None,
            "reasoning_effort": "high",
            "full_auto": False,
            "credential_blocked": False,
            "dirty_tree_blocked": False,
            "readable_secret_file_blocked": False,
            "commands_run_count": 3,
            "exit_code": 0,
            "termination_reason": "complete",
        }
        event.update(overrides)
        return event

    def test_valid_event_passes(self) -> None:
        errors = validate_event(self._make_delegation_event())
        assert errors == []

    def test_missing_field_fails(self) -> None:
        event = self._make_delegation_event()
        del event["dispatched"]
        errors = validate_event(event)
        assert any("dispatched" in e for e in errors)

    def test_classify_returns_delegation_outcome(self) -> None:
        event = self._make_delegation_event()
        assert classify(event) == "delegation_outcome"


class TestConsultationOutcomeSchema:
    """consultation_outcome thread_id in REQUIRED_FIELDS_BY_EVENT."""

    def test_thread_id_required(self) -> None:
        """thread_id is a required field for consultation_outcome events."""
        assert "thread_id" in REQUIRED_FIELDS_BY_EVENT["consultation_outcome"]


class TestConsultationOutcomeValidation:
    """validate_event with consultation_outcome events."""

    def _make_consultation_event(self, **overrides: object) -> dict:
        event = {
            "schema_version": "0.1.0",
            "event": "consultation_outcome",
            "ts": "2026-03-17T12:00:00Z",
            "consultation_id": "test-uuid",
            "thread_id": "thread-abc-123",
            "posture": "collaborative",
            "turn_count": 1,
            "turn_budget": 1,
            "termination_reason": "complete",
            "mode": "server_assisted",
        }
        event.update(overrides)
        return event

    def test_valid_event_passes(self) -> None:
        errors = validate_event(self._make_consultation_event())
        assert errors == []

    def test_null_thread_id_passes(self) -> None:
        """thread_id: None is valid (field present but nullable)."""
        errors = validate_event(self._make_consultation_event(thread_id=None))
        assert errors == []

    def test_missing_thread_id_fails(self) -> None:
        """Missing thread_id key fails validation."""
        event = self._make_consultation_event()
        del event["thread_id"]
        errors = validate_event(event)
        assert any("thread_id" in e for e in errors)

"""Tests for emit_analytics posture validation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow importing from scripts/ without package install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.emit_analytics import validate


def _make_dialogue_event(**overrides: object) -> dict:
    """Build a minimal valid dialogue_outcome event for testing."""
    event = {
        "schema_version": "0.1.0",
        "consultation_id": "test-id",
        "event": "dialogue_outcome",
        "ts": "2026-01-01T00:00:00Z",
        "posture": "evaluative",
        "turn_count": 3,
        "turn_budget": 8,
        "converged": True,
        "convergence_reason_code": "natural_convergence",
        "termination_reason": "convergence",
        "resolved_count": 2,
        "unresolved_count": 0,
        "emerged_count": 1,
        "seed_confidence": "normal",
        "mode": "server_assisted",
    }
    event.update(overrides)
    return event


class TestPostureValidation:
    """Posture enum validation in validate()."""

    def test_comparative_posture_accepted(self) -> None:
        """comparative is a valid posture value (Release A taxonomy)."""
        event = _make_dialogue_event(posture="comparative")
        # validate raises on failure, returns None on success
        validate(event, "dialogue_outcome")

    def test_known_postures_accepted(self) -> None:
        """All 5 postures pass validation."""
        for posture in (
            "adversarial",
            "collaborative",
            "exploratory",
            "evaluative",
            "comparative",
        ):
            event = _make_dialogue_event(posture=posture)
            validate(event, "dialogue_outcome")

    def test_invalid_posture_rejected(self) -> None:
        """Unknown posture raises ValueError."""
        event = _make_dialogue_event(posture="aggressive")
        with pytest.raises(ValueError, match="invalid posture"):
            validate(event, "dialogue_outcome")

"""Tests for OutcomeRecord model."""

from __future__ import annotations

from dataclasses import asdict

from server.models import OutcomeRecord


class TestOutcomeRecord:
    def test_consult_outcome_fields(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-1",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-1",
        )
        assert record.outcome_type == "consult"
        assert record.context_size == 4096
        assert record.turn_sequence is None
        assert record.policy_fingerprint is None
        assert record.repo_root is None

    def test_dialogue_outcome_fields(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-2",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="dialogue_turn",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=2048,
            turn_id="turn-2",
            turn_sequence=3,
        )
        assert record.outcome_type == "dialogue_turn"
        assert record.turn_sequence == 3

    def test_frozen(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-3",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=1024,
            turn_id="turn-3",
        )
        import pytest
        with pytest.raises(AttributeError):
            record.outcome_type = "dialogue_turn"  # type: ignore[misc]

    def test_context_size_nullable(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-5",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="dialogue_turn",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=None,
            turn_id="turn-5",
            turn_sequence=1,
        )
        assert record.context_size is None
        d = asdict(record)
        assert d["context_size"] is None

    def test_asdict_roundtrip(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-4",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-4",
            policy_fingerprint="abc123",
            repo_root="/tmp/repo",
        )
        d = asdict(record)
        assert d["outcome_id"] == "o-4"
        assert d["outcome_type"] == "consult"
        assert d["policy_fingerprint"] == "abc123"
        assert d["repo_root"] == "/tmp/repo"
        assert d["turn_sequence"] is None

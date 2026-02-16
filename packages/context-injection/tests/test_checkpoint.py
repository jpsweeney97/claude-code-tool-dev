"""Checkpoint serialization and validation tests."""

import json

import pytest

from context_injection.checkpoint import (
    CHECKPOINT_FORMAT_VERSION,
    CheckpointError,
    StateCheckpoint,
    deserialize_checkpoint,
    serialize_checkpoint,
)
from context_injection.conversation import ConversationState


class TestStateCheckpoint:
    """StateCheckpoint type construction."""

    def test_construction(self) -> None:
        cp = StateCheckpoint(
            checkpoint_id="abc123",
            parent_checkpoint_id=None,
            format_version="1",
            payload='{"conversation_id":"c1"}',
            size=25,
        )
        assert cp.checkpoint_id == "abc123"
        assert cp.parent_checkpoint_id is None
        assert cp.format_version == "1"

    def test_with_parent(self) -> None:
        cp = StateCheckpoint(
            checkpoint_id="def456",
            parent_checkpoint_id="abc123",
            format_version="1",
            payload="{}",
            size=2,
        )
        assert cp.parent_checkpoint_id == "abc123"


class TestSerializeCheckpoint:
    """serialize_checkpoint: state -> SerializedCheckpoint(state, checkpoint_id, checkpoint_string)."""

    def test_round_trip(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        result = serialize_checkpoint(state)
        assert len(result.checkpoint_id) == 32  # uuid4 hex
        # Returned state has last_checkpoint_id updated
        assert result.state.last_checkpoint_id == result.checkpoint_id
        restored, restored_id = deserialize_checkpoint(result.checkpoint_string)
        assert restored.conversation_id == "conv-1"
        assert restored_id == result.checkpoint_id

    def test_state_checkpoint_id_embedded_before_serialization(self) -> None:
        """Payload last_checkpoint_id matches envelope checkpoint_id (CC-3 fix)."""
        state = ConversationState(conversation_id="conv-1")
        result = serialize_checkpoint(state)
        restored, _ = deserialize_checkpoint(result.checkpoint_string)
        assert restored.last_checkpoint_id == result.checkpoint_id

    def test_parent_id_derived_from_state(self) -> None:
        """parent_checkpoint_id derived from state.last_checkpoint_id, not a parameter."""
        state = ConversationState(conversation_id="conv-1").with_checkpoint_id(
            "parent-abc"
        )
        result = serialize_checkpoint(state)
        parsed = json.loads(result.checkpoint_string)
        assert parsed["parent_checkpoint_id"] == "parent-abc"

    def test_first_checkpoint_parent_is_none(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        result = serialize_checkpoint(state)
        parsed = json.loads(result.checkpoint_string)
        assert parsed["parent_checkpoint_id"] is None

    def test_format_version_included(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        result = serialize_checkpoint(state)
        parsed = json.loads(result.checkpoint_string)
        assert parsed["format_version"] == CHECKPOINT_FORMAT_VERSION

    def test_exceeds_size_cap_raises(self) -> None:
        from context_injection.enums import EffectiveDelta, QualityLabel
        from context_injection.ledger import LedgerEntry, LedgerEntryCounters
        from context_injection.types import Claim

        claims = [
            Claim(text=f"Long claim text {'x' * 200} {i}", status="new", turn=1)
            for i in range(100)
        ]
        counters = LedgerEntryCounters(
            new_claims=100,
            revised=0,
            conceded=0,
            unresolved_closed=0,
        )
        entry = LedgerEntry(
            position="x" * 500,
            claims=claims,
            delta="advancing",
            tags=[],
            unresolved=[],
            counters=counters,
            quality=QualityLabel.SUBSTANTIVE,
            effective_delta=EffectiveDelta.ADVANCING,
            turn_number=1,
        )
        state = ConversationState(conversation_id="conv-1").with_turn(entry)
        with pytest.raises(ValueError, match="exceeds"):
            serialize_checkpoint(state)


class TestDeserializeCheckpoint:
    """deserialize_checkpoint: checkpoint_string -> (state, checkpoint_id)."""

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(CheckpointError) as exc_info:
            deserialize_checkpoint("not valid json")
        assert exc_info.value.code == "checkpoint_invalid"

    def test_wrong_format_version_raises(self) -> None:
        cp = StateCheckpoint(
            checkpoint_id="abc",
            parent_checkpoint_id=None,
            format_version="999",
            payload='{"conversation_id":"c1"}',
            size=25,
        )
        with pytest.raises(CheckpointError) as exc_info:
            deserialize_checkpoint(cp.model_dump_json())
        assert exc_info.value.code == "checkpoint_invalid"
        assert "format version" in str(exc_info.value).lower()

    def test_payload_size_mismatch_raises(self) -> None:
        """Envelope size field doesn't match actual payload size."""
        cp = StateCheckpoint(
            checkpoint_id="abc",
            parent_checkpoint_id=None,
            format_version=CHECKPOINT_FORMAT_VERSION,
            payload='{"conversation_id":"c1"}',
            size=999,  # Wrong — actual payload is ~25 bytes
        )
        with pytest.raises(CheckpointError) as exc_info:
            deserialize_checkpoint(cp.model_dump_json())
        assert exc_info.value.code == "checkpoint_invalid"
        assert "size mismatch" in str(exc_info.value).lower()

    def test_corrupt_payload_raises(self) -> None:
        cp = StateCheckpoint(
            checkpoint_id="abc",
            parent_checkpoint_id=None,
            format_version=CHECKPOINT_FORMAT_VERSION,
            payload="not valid json",
            size=14,
        )
        with pytest.raises(CheckpointError) as exc_info:
            deserialize_checkpoint(cp.model_dump_json())
        assert exc_info.value.code == "checkpoint_invalid"

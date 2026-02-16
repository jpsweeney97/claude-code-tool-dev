"""Checkpoint serialization and chain validation.

Checkpoints are opaque state snapshots passed between server and agent.
The agent stores the checkpoint string and sends it back on the next turn.
The server deserializes and validates to restore conversation state.

Wire encoding: TurnPacketSuccess.state_checkpoint carries the
model_dump_json() of StateCheckpoint. This is double-encoded JSON
(outer = StateCheckpoint, inner payload = ConversationState).
"""

from __future__ import annotations

import uuid
from typing import NamedTuple

from context_injection.conversation import ConversationState
from context_injection.types import ProtocolModel

CHECKPOINT_FORMAT_VERSION: str = "1"
"""Checkpoint serialization format. Increment on breaking changes."""

MAX_CHECKPOINT_PAYLOAD_BYTES: int = 16_384
"""Hard limit on serialized ConversationState payload (16 KB)."""


class StateCheckpoint(ProtocolModel):
    """Serialized conversation state for agent-side storage.

    Wire type: model_dump_json() of this type is the opaque string
    sent in TurnPacketSuccess.state_checkpoint.
    """

    checkpoint_id: str
    parent_checkpoint_id: str | None
    format_version: str
    payload: str
    size: int


class CheckpointError(Exception):
    """Checkpoint validation failure with error code.

    Codes map to ErrorDetail.code in D4:
    checkpoint_missing, checkpoint_invalid, checkpoint_stale.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class SerializedCheckpoint(NamedTuple):
    """Result of serialize_checkpoint.

    state: ConversationState with last_checkpoint_id already updated.
           Caller commits this directly — no separate with_checkpoint_id() call.
    checkpoint_id: The new checkpoint ID (for TurnPacketSuccess.checkpoint_id).
    checkpoint_string: Opaque payload (for TurnPacketSuccess.state_checkpoint).
    """

    state: ConversationState
    checkpoint_id: str
    checkpoint_string: str


def serialize_checkpoint(state: ConversationState) -> SerializedCheckpoint:
    """Serialize state to checkpoint. Returns SerializedCheckpoint.

    parent_id is derived from state.last_checkpoint_id (not a parameter).
    New checkpoint_id is embedded into state BEFORE serializing the payload,
    so the returned state already has last_checkpoint_id updated (CC-3 fix).
    Raises ValueError if payload exceeds MAX_CHECKPOINT_PAYLOAD_BYTES.
    """
    checkpoint_id = uuid.uuid4().hex
    parent_id = state.last_checkpoint_id
    state_for_payload = state.with_checkpoint_id(checkpoint_id)
    payload = state_for_payload.model_dump_json()
    payload_size = len(payload.encode("utf-8"))

    if payload_size > MAX_CHECKPOINT_PAYLOAD_BYTES:
        raise ValueError(
            f"Checkpoint payload exceeds {MAX_CHECKPOINT_PAYLOAD_BYTES} bytes: "
            f"got {payload_size} bytes. Compact the ledger before serializing."
        )

    checkpoint = StateCheckpoint(
        checkpoint_id=checkpoint_id,
        parent_checkpoint_id=parent_id,
        format_version=CHECKPOINT_FORMAT_VERSION,
        payload=payload,
        size=payload_size,
    )
    return SerializedCheckpoint(
        state=state_for_payload,
        checkpoint_id=checkpoint_id,
        checkpoint_string=checkpoint.model_dump_json(),
    )


def deserialize_checkpoint(checkpoint_string: str) -> tuple[ConversationState, str]:
    """Deserialize checkpoint string. Returns (state, checkpoint_id).

    Raises CheckpointError("checkpoint_invalid") on corrupt or incompatible payload.
    """
    try:
        checkpoint = StateCheckpoint.model_validate_json(checkpoint_string)
    except Exception as e:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Failed to parse checkpoint envelope: {e}",
        ) from e

    if checkpoint.format_version != CHECKPOINT_FORMAT_VERSION:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Unsupported checkpoint format version: {checkpoint.format_version!r}, "
            f"expected {CHECKPOINT_FORMAT_VERSION!r}",
        )

    actual_size = len(checkpoint.payload.encode("utf-8"))
    if actual_size != checkpoint.size:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Payload size mismatch: envelope claims {checkpoint.size} bytes, "
            f"actual payload is {actual_size} bytes (corruption detected)",
        )

    try:
        state = ConversationState.model_validate_json(checkpoint.payload)
    except Exception as e:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Failed to deserialize conversation state from payload: {e}",
        ) from e

    return state, checkpoint.checkpoint_id

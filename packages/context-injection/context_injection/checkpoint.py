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

    if actual_size > MAX_CHECKPOINT_PAYLOAD_BYTES:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Checkpoint payload exceeds {MAX_CHECKPOINT_PAYLOAD_BYTES} bytes: "
            f"got {actual_size} bytes",
        )

    try:
        state = ConversationState.model_validate_json(checkpoint.payload)
    except Exception as e:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Failed to deserialize conversation state from payload: {e}",
        ) from e

    return state, checkpoint.checkpoint_id


# ---------------------------------------------------------------------------
# Constants — compaction thresholds
# ---------------------------------------------------------------------------

MAX_ENTRIES_BEFORE_COMPACT: int = 16
"""Trigger compaction when entries exceed this count."""

KEEP_RECENT_ENTRIES: int = 8
"""Number of recent entries to keep after compaction."""


# ---------------------------------------------------------------------------
# Checkpoint intake validation
# ---------------------------------------------------------------------------


def validate_checkpoint_intake(
    in_memory: ConversationState,
    checkpoint_id: str | None,
    checkpoint_payload: str | None,
    turn_number: int,
    target_conversation_id: str | None = None,
) -> ConversationState:
    """Resolve conversation state for a turn.

    Five-case policy:
    - Turn 1: use in_memory (checkpoint ignored)
    - Turn > 1, real state (last_checkpoint_id set), IDs match: use in_memory
    - Turn > 1, real state, IDs mismatch: checkpoint_stale error
    - Turn > 1, no real state, checkpoint present: restore from checkpoint
    - Turn > 1, no real state, no checkpoint: checkpoint_missing error

    Restore integrity checks (when restoring from checkpoint):
    1. checkpoint_id not None when payload present -> checkpoint_missing
    2. Request checkpoint_id matches envelope ID -> checkpoint_stale
    3. Payload last_checkpoint_id matches envelope ID -> checkpoint_invalid (corruption)
    4. Payload conversation_id matches target conversation -> checkpoint_invalid (security)

    in_memory: from ctx.get_or_create_conversation() -- never None.
    "Real state" means last_checkpoint_id is not None (server has
    processed at least one turn for this conversation).
    target_conversation_id: the conversation_id from the request context.
    Used for cross-conversation checkpoint swap detection.
    """
    if turn_number <= 1:
        return in_memory

    has_real_state = in_memory.last_checkpoint_id is not None

    if has_real_state:
        if checkpoint_id == in_memory.last_checkpoint_id:
            return in_memory
        raise CheckpointError(
            "checkpoint_stale",
            f"Checkpoint ID mismatch: server has "
            f"{in_memory.last_checkpoint_id!r}, agent sent {checkpoint_id!r}",
        )

    # No real state (server restarted) — restore from checkpoint
    if checkpoint_payload is not None:
        # Guard 1: checkpoint_id required when payload present
        if checkpoint_id is None:
            raise CheckpointError(
                "checkpoint_missing",
                "Checkpoint payload present but checkpoint_id is None",
            )

        state, envelope_id = deserialize_checkpoint(checkpoint_payload)

        # Guard 2: request checkpoint_id matches envelope ID
        if checkpoint_id != envelope_id:
            raise CheckpointError(
                "checkpoint_stale",
                f"Request checkpoint_id {checkpoint_id!r} does not match "
                f"envelope checkpoint_id {envelope_id!r}",
            )

        # Guard 3: payload last_checkpoint_id matches envelope ID
        if state.last_checkpoint_id != envelope_id:
            raise CheckpointError(
                "checkpoint_invalid",
                f"Payload last_checkpoint_id {state.last_checkpoint_id!r} does not "
                f"match envelope checkpoint_id {envelope_id!r} (corruption detected)",
            )

        # Guard 4: payload conversation_id matches target conversation
        if (
            target_conversation_id is not None
            and state.conversation_id != target_conversation_id
        ):
            raise CheckpointError(
                "checkpoint_invalid",
                f"Checkpoint conversation_id {state.conversation_id!r} does not "
                f"match target {target_conversation_id!r} "
                f"(cross-conversation checkpoint swap detected)",
            )

        return state

    raise CheckpointError(
        "checkpoint_missing",
        f"Turn {turn_number} requires checkpoint: server has no in-memory "
        f"state and no checkpoint payload was provided",
    )


# ---------------------------------------------------------------------------
# Ledger compaction
# ---------------------------------------------------------------------------


def compact_ledger(state: ConversationState) -> ConversationState:
    """Reduce state size by keeping only recent entries.

    Unreachable under DD-2 invariant (MAX_CONVERSATION_TURNS <
    MAX_ENTRIES_BEFORE_COMPACT). The pipeline's pre-append turn cap guard
    rejects turns before entry count can reach the compaction threshold.
    Retained as a safety net if the invariant is relaxed in the future.

    Triggered before checkpoint serialization when approaching size cap.
    Keeps KEEP_RECENT_ENTRIES most recent entries and rebuilds
    claim_registry from them.

    Trade-off: referential validation loses history beyond the window.
    Acceptable because REFERENTIAL_WARN is the softest tier.
    """
    if len(state.entries) <= MAX_ENTRIES_BEFORE_COMPACT:
        return state

    recent = state.entries[-KEEP_RECENT_ENTRIES:]
    claims = tuple(c for e in recent for c in e.claims)
    return state.model_copy(
        update={
            "entries": recent,
            "claim_registry": claims,
        }
    )

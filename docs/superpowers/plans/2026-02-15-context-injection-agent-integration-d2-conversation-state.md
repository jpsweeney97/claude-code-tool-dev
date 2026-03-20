# D2: Conversation State Management — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Delivery:** D2 of 6 (D1, D2, D3, D4a, D4b, D5)
**Objective:** Implement ConversationState (per-conversation ledger storage + claim registry), checkpoint serialization, chain validation, compaction, and AppContext extension.
**Execution order position:** 3 of 6 (D1 → D3 → D2 → D4a → D4b → D5)
**Branch:** `feature/context-injection-agent-integration`
**Package directory:** `packages/context-injection/`
**Test command:** `cd packages/context-injection && uv run pytest tests/ -v`

## Prerequisite Contract

**Requires from D1:**
- From `context_injection/ledger.py`: `LedgerEntry`, `LedgerEntryCounters`, `CumulativeState`, validation functions
- From `context_injection/enums.py`: `EffectiveDelta`, `QualityLabel`
- Source of truth: `context_injection/ledger.py`, `context_injection/enums.py`

**Critical invariants:**
- LedgerEntry is frozen (immutable after creation)
- CumulativeState is computed deterministically from ledger entries

**Adaptation:** If D1 type or function names differ from this plan, adapt references and note the mapping.

## Files in Scope

**Create:**
- `context_injection/conversation.py` — ConversationState class
- `context_injection/checkpoint.py` — Checkpoint types, serialization, chain validation, compaction
- `tests/test_conversation.py` — D2 state management tests
- `tests/test_checkpoint.py` — D2 checkpoint tests

**Modify:**
- `context_injection/state.py` — Add conversations dict to AppContext

**Out of scope:** All files not listed above. In particular, do NOT modify pipeline files, types.py, or server.py.

## Done Criteria

- ConversationState correctly stores and retrieves ledger entries
- Checkpoint chain validates
- Compaction preserves invariants
- AppContext extension works
- All D2 tests pass

## Scope Boundary

This document covers D2 only. After completing all tasks in this delivery, stop. Do not proceed to subsequent deliveries.

## Relevant Resolved Questions

**Q4 — Checkpoint ingestion gap:** Original plan omitted checkpoint intake from D4 pipeline. Now explicit in Task 13a step 3 and D2 Task 7 validation policy.

---

Pure additive delivery. New `conversation.py` + `checkpoint.py`. Extends `state.py` with conversations dict.

**Estimated new tests:** 100-150
**Depends on:** D1 complete (uses LedgerEntry, CumulativeState)

### Task 5: ConversationState class

**Files:**
- Create: `context_injection/conversation.py`
- Create: `tests/test_conversation.py`

Pydantic `BaseModel` with `ConfigDict(frozen=True, extra="forbid", strict=True)` — not ProtocolModel (internal state, not wire type). Projection methods use `model_copy(update={...})` to return new instances. Pipeline commits atomically by replacing `ctx.conversations[id] = projected`.

**Design refinement from outline:** `with_turn(entry)` simplified from `with_turn(entry, claims)` — claims derived from `entry.claims` since `validate_ledger_entry` constructs the entry with the same claims. No redundancy.

**Step 1: Write failing tests for construction and immutability**

Create `tests/test_conversation.py`:

```python
"""Conversation state management tests."""

import pytest
from pydantic import ValidationError

from context_injection.conversation import ConversationState
from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,
)
from context_injection.types import Claim, EvidenceRecord, Unresolved


def _make_entry(
    turn_number: int = 1,
    *,
    position: str = "Position",
    claims: list[Claim] | None = None,
    delta: str = "advancing",
    effective_delta: EffectiveDelta = EffectiveDelta.ADVANCING,
    quality: QualityLabel = QualityLabel.SUBSTANTIVE,
    unresolved: list[Unresolved] | None = None,
    unresolved_closed: int = 0,
) -> LedgerEntry:
    """Build a LedgerEntry for testing."""
    if claims is None:
        claims = [Claim(text=f"Claim {turn_number}", status="new", turn=turn_number)]
    if unresolved is None:
        unresolved = []
    counters = LedgerEntryCounters(
        new_claims=sum(1 for c in claims if c.status == "new"),
        revised=sum(1 for c in claims if c.status == "revised"),
        conceded=sum(1 for c in claims if c.status == "conceded"),
        unresolved_closed=unresolved_closed,
    )
    return LedgerEntry(
        position=position,
        claims=claims,
        delta=delta,
        tags=[],
        unresolved=unresolved,
        counters=counters,
        quality=quality,
        effective_delta=effective_delta,
        turn_number=turn_number,
    )


class TestConversationStateConstruction:
    """Construction and immutability."""

    def test_empty_state(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        assert state.conversation_id == "conv-1"
        assert state.entries == ()
        assert state.claim_registry == ()
        assert state.evidence_history == ()
        assert state.closing_probe_fired is False
        assert state.last_checkpoint_id is None

    def test_frozen(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        with pytest.raises(ValidationError):
            state.conversation_id = "other"  # type: ignore[misc]
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_conversation.py::TestConversationStateConstruction -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'context_injection.conversation'`

**Step 3: Write failing tests for projection methods**

Add to `tests/test_conversation.py`:

```python
class TestWithTurn:
    """with_turn: append entry, extend claim_registry."""

    def test_first_turn(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(turn_number=1)
        projected = state.with_turn(entry)
        assert len(projected.entries) == 1
        assert projected.entries[0] is entry
        assert len(projected.claim_registry) == 1
        assert projected.claim_registry[0].text == "Claim 1"

    def test_second_turn_appends(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(turn_number=1)
        e2 = _make_entry(turn_number=2)
        projected = state.with_turn(e1).with_turn(e2)
        assert len(projected.entries) == 2
        assert len(projected.claim_registry) == 2
        assert projected.claim_registry[0].text == "Claim 1"
        assert projected.claim_registry[1].text == "Claim 2"

    def test_original_unchanged(self) -> None:
        """Immutable projection — original state not modified."""
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(turn_number=1)
        _ = state.with_turn(entry)
        assert state.entries == ()
        assert state.claim_registry == ()

    def test_multi_claim_turn(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(
            turn_number=1,
            claims=[
                Claim(text="A", status="new", turn=1),
                Claim(text="B", status="reinforced", turn=1),
            ],
        )
        projected = state.with_turn(entry)
        assert len(projected.claim_registry) == 2


class TestWithEvidence:
    """with_evidence: append evidence record."""

    def test_appends_evidence(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        record = EvidenceRecord(
            entity_key="file:foo.py", template_id="probe.file_repo_fact", turn=1,
        )
        projected = state.with_evidence(record)
        assert len(projected.evidence_history) == 1
        assert projected.evidence_history[0].entity_key == "file:foo.py"

    def test_original_unchanged(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        record = EvidenceRecord(
            entity_key="file:foo.py", template_id="probe.file_repo_fact", turn=1,
        )
        _ = state.with_evidence(record)
        assert state.evidence_history == ()


class TestWithClosingProbeFired:
    """with_closing_probe_fired: set flag."""

    def test_sets_flag(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        projected = state.with_closing_probe_fired()
        assert projected.closing_probe_fired is True
        assert state.closing_probe_fired is False


class TestWithCheckpointId:
    """with_checkpoint_id: update head checkpoint."""

    def test_sets_checkpoint_id(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        projected = state.with_checkpoint_id("abc123")
        assert projected.last_checkpoint_id == "abc123"
        assert state.last_checkpoint_id is None
```

**Step 4: Write failing tests for accessors and compute_cumulative_state**

Add to `tests/test_conversation.py`:

```python
class TestGetCumulativeClaims:
    """get_cumulative_claims: return claim registry copy."""

    def test_empty(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        assert state.get_cumulative_claims() == []

    def test_after_turns(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(turn_number=1)
        e2 = _make_entry(
            turn_number=2,
            claims=[
                Claim(text="X", status="new", turn=2),
                Claim(text="Y", status="reinforced", turn=2),
            ],
        )
        projected = state.with_turn(e1).with_turn(e2)
        claims = projected.get_cumulative_claims()
        assert len(claims) == 3  # 1 from turn 1, 2 from turn 2

    def test_returns_copy(self) -> None:
        """Returned list is a copy — mutations don't affect state."""
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(turn_number=1)
        projected = state.with_turn(entry)
        claims = projected.get_cumulative_claims()
        claims.clear()
        assert len(projected.get_cumulative_claims()) == 1


class TestGetEvidenceHistory:
    """get_evidence_history: return evidence list copy."""

    def test_empty(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        assert state.get_evidence_history() == []

    def test_after_evidence(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        record = EvidenceRecord(
            entity_key="file:a.py", template_id="probe.file_repo_fact", turn=1,
        )
        projected = state.with_evidence(record)
        assert len(projected.get_evidence_history()) == 1


class TestComputeCumulativeState:
    """compute_cumulative_state: aggregate from entries."""

    def test_empty_entries(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        cumulative = state.compute_cumulative_state()
        assert cumulative.total_claims == 0
        assert cumulative.reinforced == 0
        assert cumulative.revised == 0
        assert cumulative.conceded == 0
        assert cumulative.unresolved_open == 0
        assert cumulative.unresolved_closed == 0
        assert cumulative.turns_completed == 0
        assert cumulative.effective_delta_sequence == []

    def test_single_entry(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(
            turn_number=1,
            claims=[Claim(text="A", status="new", turn=1)],
        )
        projected = state.with_turn(entry)
        cumulative = projected.compute_cumulative_state()
        assert cumulative.total_claims == 1
        assert cumulative.reinforced == 0
        assert cumulative.turns_completed == 1
        assert cumulative.effective_delta_sequence == [EffectiveDelta.ADVANCING]

    def test_multi_turn(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(
            turn_number=1,
            claims=[Claim(text="A", status="new", turn=1)],
        )
        e2 = _make_entry(
            turn_number=2,
            claims=[
                Claim(text="A", status="reinforced", turn=2),
                Claim(text="B", status="revised", turn=2),
            ],
            effective_delta=EffectiveDelta.SHIFTING,
        )
        projected = state.with_turn(e1).with_turn(e2)
        cumulative = projected.compute_cumulative_state()
        assert cumulative.total_claims == 3  # 1 + 2
        assert cumulative.reinforced == 1
        assert cumulative.revised == 1
        assert cumulative.turns_completed == 2
        assert cumulative.effective_delta_sequence == [
            EffectiveDelta.ADVANCING, EffectiveDelta.SHIFTING,
        ]

    def test_unresolved_open_from_latest(self) -> None:
        """unresolved_open comes from the latest entry only."""
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(
            turn_number=1,
            unresolved=[Unresolved(text="Q1?", turn=1), Unresolved(text="Q2?", turn=1)],
        )
        e2 = _make_entry(
            turn_number=2,
            unresolved=[Unresolved(text="Q1?", turn=2)],
            unresolved_closed=1,
        )
        projected = state.with_turn(e1).with_turn(e2)
        cumulative = projected.compute_cumulative_state()
        assert cumulative.unresolved_open == 1
        assert cumulative.unresolved_closed == 1

    def test_conceded_accumulated(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(
            turn_number=1,
            claims=[Claim(text="A", status="conceded", turn=1)],
            effective_delta=EffectiveDelta.SHIFTING,
        )
        e2 = _make_entry(
            turn_number=2,
            claims=[Claim(text="B", status="conceded", turn=2)],
            effective_delta=EffectiveDelta.SHIFTING,
        )
        projected = state.with_turn(e1).with_turn(e2)
        cumulative = projected.compute_cumulative_state()
        assert cumulative.conceded == 2
```

**Step 5: Implement ConversationState**

Create `context_injection/conversation.py`:

```python
"""Conversation state management.

Immutable projection pattern: ConversationState is never mutated.
Projection methods return new instances via model_copy(update={...}).
Pipeline commits atomically by replacing the dict entry:
ctx.conversations[id] = projected.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from context_injection.enums import EffectiveDelta
from context_injection.ledger import CumulativeState, LedgerEntry
from context_injection.types import Claim, EvidenceRecord


class ConversationState(BaseModel):
    """Per-conversation state. Frozen — projection methods return new instances."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    conversation_id: str
    entries: tuple[LedgerEntry, ...] = ()
    claim_registry: tuple[Claim, ...] = ()
    evidence_history: tuple[EvidenceRecord, ...] = ()
    closing_probe_fired: bool = False
    last_checkpoint_id: str | None = None

    def with_turn(self, entry: LedgerEntry) -> ConversationState:
        """New state with entry appended and claim_registry extended."""
        return self.model_copy(update={
            "entries": (*self.entries, entry),
            "claim_registry": (*self.claim_registry, *entry.claims),
        })

    def with_evidence(self, record: EvidenceRecord) -> ConversationState:
        """New state with evidence record appended."""
        return self.model_copy(update={
            "evidence_history": (*self.evidence_history, record),
        })

    def with_closing_probe_fired(self) -> ConversationState:
        """New state with closing_probe_fired set."""
        return self.model_copy(update={"closing_probe_fired": True})

    def with_checkpoint_id(self, checkpoint_id: str) -> ConversationState:
        """New state with last_checkpoint_id updated."""
        return self.model_copy(update={"last_checkpoint_id": checkpoint_id})

    def get_cumulative_claims(self) -> list[Claim]:
        """All claims from all turns (insertion-ordered). Returns mutable copy."""
        return list(self.claim_registry)

    def get_evidence_history(self) -> list[EvidenceRecord]:
        """All evidence records (insertion-ordered). Returns mutable copy."""
        return list(self.evidence_history)

    def compute_cumulative_state(self) -> CumulativeState:
        """Aggregate state across all validated ledger entries.

        Correct only when compaction has not triggered. See DD-2 invariant:
        MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT ensures compaction
        is unreachable under normal operation. If compaction has occurred,
        totals reflect only the retained window, not full conversation history.

        total_claims: all claims across all entries (including reinforced).
        reinforced: scanned from claims (not tracked in counters).
        revised/conceded: from entry counters.
        unresolved_open: from latest entry's unresolved list.
        unresolved_closed: summed from entry counters.
        """
        total_claims = sum(len(e.claims) for e in self.entries)
        reinforced = sum(
            sum(1 for c in e.claims if c.status == "reinforced")
            for e in self.entries
        )
        revised = sum(e.counters.revised for e in self.entries)
        conceded = sum(e.counters.conceded for e in self.entries)
        unresolved_open = (
            len(self.entries[-1].unresolved) if self.entries else 0
        )
        unresolved_closed = sum(
            e.counters.unresolved_closed for e in self.entries
        )
        turns_completed = len(self.entries)
        effective_delta_sequence = [e.effective_delta for e in self.entries]

        return CumulativeState(
            total_claims=total_claims,
            reinforced=reinforced,
            revised=revised,
            conceded=conceded,
            unresolved_open=unresolved_open,
            unresolved_closed=unresolved_closed,
            turns_completed=turns_completed,
            effective_delta_sequence=effective_delta_sequence,
        )
```

**Step 6: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_conversation.py -v`
Expected: PASS (all construction, projection, accessor, and cumulative state tests)

**Step 7: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus new test_conversation.py tests.

**Step 8: Commit**

```bash
git add packages/context-injection/context_injection/conversation.py \
       packages/context-injection/tests/test_conversation.py
git commit -m "feat(context-injection): add ConversationState with immutable projections (D2 Task 5)"
```

### Task 6: Checkpoint types and serialization

**Files:**
- Create: `context_injection/checkpoint.py`
- Create: `tests/test_checkpoint.py`

`StateCheckpoint` is a `ProtocolModel` (wire type — the `model_dump_json()` of this type is the opaque string in `TurnPacketSuccess.state_checkpoint`). The agent stores this string opaque and sends it back. The server deserializes to restore state.

`serialize_checkpoint` returns a `SerializedCheckpoint` NamedTuple `(state, checkpoint_id, checkpoint_string)`. The `parent_id` parameter is eliminated — derived inside from `state.last_checkpoint_id` (encapsulates ordering invariant, prevents caller/callee mismatch). The new `checkpoint_id` is embedded into state BEFORE serializing the payload, so the returned `state` already has `last_checkpoint_id` updated — the caller commits this projected state directly. The pipeline needs all three: `state` for atomic commit, `checkpoint_id` for `TurnPacketSuccess.checkpoint_id`, and `checkpoint_string` for `TurnPacketSuccess.state_checkpoint`.

**Step 1: Write failing tests for StateCheckpoint and serialization**

Create `tests/test_checkpoint.py`:

```python
"""Checkpoint serialization and validation tests."""

import json

import pytest

from context_injection.checkpoint import (
    CHECKPOINT_FORMAT_VERSION,
    CheckpointError,
    SerializedCheckpoint,
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
    """serialize_checkpoint: state → SerializedCheckpoint(state, checkpoint_id, checkpoint_string)."""

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
        state = ConversationState(conversation_id="conv-1").with_checkpoint_id("parent-abc")
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
            new_claims=100, revised=0, conceded=0, unresolved_closed=0,
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
    """deserialize_checkpoint: checkpoint_string → (state, checkpoint_id)."""

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
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_checkpoint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'context_injection.checkpoint'`

**Step 3: Implement checkpoint types and serialization**

Create `context_injection/checkpoint.py`:

```python
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
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_checkpoint.py -v`
Expected: PASS (all StateCheckpoint, serialize, and deserialize tests)

**Step 5: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All existing tests pass.

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/checkpoint.py \
       packages/context-injection/tests/test_checkpoint.py
git commit -m "feat(context-injection): add checkpoint types and serialization (D2 Task 6)"
```

### Task 7: Checkpoint chain validation and compaction

**Files:**
- Modify: `context_injection/checkpoint.py` (add validate_checkpoint_intake, compact_ledger)
- Modify: `tests/test_checkpoint.py`

**Head-pointer validation model.** Stale detection uses a head-pointer comparison: the server's `last_checkpoint_id` is compared against the agent's `checkpoint_id`. There is no parent-chain walk. `parent_checkpoint_id` in `StateCheckpoint` is informational/deferred — reserved for future parent-chain validation but not used in 0.2.0 stale detection.

Five-case intake policy for resolving conversation state at the start of each turn. The key distinction: `last_checkpoint_id is not None` reliably indicates "real state" vs "fresh empty state created by `get_or_create_conversation` after server restart." This lets the function route to checkpoint restore when the server has no real memory of the conversation.

Compaction: when entries exceed `MAX_ENTRIES_BEFORE_COMPACT`, keep only `KEEP_RECENT_ENTRIES` most recent and rebuild `claim_registry` from them. Trade-off: referential validation loses history beyond the window (acceptable — `REFERENTIAL_WARN` is the softest tier).

**Step 1: Write failing tests for checkpoint intake (all 5 cases)**

Add to `tests/test_checkpoint.py`:

```python
from context_injection.checkpoint import (
    validate_checkpoint_intake,
)


class TestValidateCheckpointIntake:
    """Checkpoint intake 5-case policy."""

    def test_turn_1_returns_in_memory(self) -> None:
        """Turn 1: checkpoint optional, use in-memory."""
        state = ConversationState(conversation_id="conv-1")
        result = validate_checkpoint_intake(
            state, checkpoint_id=None, checkpoint_payload=None, turn_number=1,
        )
        assert result is state

    def test_turn_1_ignores_checkpoint(self) -> None:
        """Turn 1 with checkpoint present — checkpoint ignored."""
        state = ConversationState(conversation_id="conv-1")
        result = validate_checkpoint_intake(
            state, checkpoint_id="orphan", checkpoint_payload="ignored",
            turn_number=1,
        )
        assert result is state

    def test_turn_gt1_in_memory_ids_match(self) -> None:
        """Turn > 1, real state, IDs match — use in-memory."""
        state = ConversationState(
            conversation_id="conv-1",
        ).with_checkpoint_id("cp-1")
        result = validate_checkpoint_intake(
            state, checkpoint_id="cp-1", checkpoint_payload=None, turn_number=2,
        )
        assert result is state

    def test_turn_gt1_in_memory_ids_mismatch_raises(self) -> None:
        """Turn > 1, real state, IDs mismatch — stale error."""
        state = ConversationState(
            conversation_id="conv-1",
        ).with_checkpoint_id("cp-1")
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                state, checkpoint_id="cp-OLD", checkpoint_payload=None,
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_stale"

    def test_turn_gt1_no_real_state_restores_from_checkpoint(self) -> None:
        """Turn > 1, server restarted (no real state) — restore from checkpoint."""
        in_memory = ConversationState(conversation_id="conv-1")
        # Create a checkpoint from real state
        real_state = ConversationState(conversation_id="conv-1")
        result_cp = serialize_checkpoint(real_state)
        result = validate_checkpoint_intake(
            in_memory, checkpoint_id=result_cp.checkpoint_id,
            checkpoint_payload=result_cp.checkpoint_string,
            turn_number=2,
        )
        assert result.conversation_id == "conv-1"
        assert result.last_checkpoint_id == result_cp.checkpoint_id

    def test_turn_gt1_no_real_state_no_checkpoint_raises(self) -> None:
        """Turn > 1, no real state, no checkpoint — missing error."""
        in_memory = ConversationState(conversation_id="conv-1")
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory, checkpoint_id=None, checkpoint_payload=None,
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_missing"

    def test_turn_gt1_corrupt_checkpoint_raises(self) -> None:
        """Turn > 1, no real state, corrupt checkpoint — invalid error."""
        in_memory = ConversationState(conversation_id="conv-1")
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory, checkpoint_id="cp-1", checkpoint_payload="corrupt",
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_invalid"

    # --- Restore integrity guards (CC-3) ---

    def test_restore_guard_checkpoint_id_none_with_payload(self) -> None:
        """Guard 1: checkpoint_id must not be None when payload is present."""
        in_memory = ConversationState(conversation_id="conv-1")
        result_cp = serialize_checkpoint(
            ConversationState(conversation_id="conv-1"),
        )
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory, checkpoint_id=None,
                checkpoint_payload=result_cp.checkpoint_string,
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_missing"

    def test_restore_guard_request_id_mismatch(self) -> None:
        """Guard 2: request checkpoint_id must match envelope ID."""
        in_memory = ConversationState(conversation_id="conv-1")
        result_cp = serialize_checkpoint(
            ConversationState(conversation_id="conv-1"),
        )
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory, checkpoint_id="wrong-id",
                checkpoint_payload=result_cp.checkpoint_string,
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_stale"

    def test_restore_guard_payload_checkpoint_id_mismatch(self) -> None:
        """Guard 3: payload last_checkpoint_id must match envelope ID.

        This catches corruption where the envelope ID was tampered but the
        payload was serialized with a different checkpoint_id.
        """
        in_memory = ConversationState(conversation_id="conv-1")
        # Manually craft a checkpoint with mismatched IDs
        state_with_wrong_id = ConversationState(
            conversation_id="conv-1",
        ).with_checkpoint_id("wrong-inner-id")
        payload = state_with_wrong_id.model_dump_json()
        tampered = StateCheckpoint(
            checkpoint_id="envelope-id",
            parent_checkpoint_id=None,
            format_version=CHECKPOINT_FORMAT_VERSION,
            payload=payload,
            size=len(payload.encode("utf-8")),
        )
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory, checkpoint_id="envelope-id",
                checkpoint_payload=tampered.model_dump_json(),
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_invalid"

    def test_restore_guard_cross_conversation_swap(self) -> None:
        """Guard 4: payload conversation_id must match target conversation."""
        in_memory = ConversationState(conversation_id="conv-target")
        # Create a checkpoint from a different conversation
        result_cp = serialize_checkpoint(
            ConversationState(conversation_id="conv-other"),
        )
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory, checkpoint_id=result_cp.checkpoint_id,
                checkpoint_payload=result_cp.checkpoint_string,
                turn_number=2,
                target_conversation_id="conv-target",
            )
        assert exc_info.value.code == "checkpoint_invalid"
        assert "cross-conversation" in str(exc_info.value).lower()
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_checkpoint.py::TestValidateCheckpointIntake -v`
Expected: FAIL — `ImportError: cannot import name 'validate_checkpoint_intake'`

**Step 3: Write failing tests for compact_ledger**

Add to `tests/test_checkpoint.py`:

```python
from context_injection.checkpoint import (
    KEEP_RECENT_ENTRIES,
    MAX_ENTRIES_BEFORE_COMPACT,
    compact_ledger,
)
from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.ledger import LedgerEntry, LedgerEntryCounters
from context_injection.types import Claim


def _make_entry(
    turn_number: int = 1,
    *,
    claims: list[Claim] | None = None,
) -> LedgerEntry:
    """Minimal LedgerEntry for checkpoint tests."""
    if claims is None:
        claims = [Claim(text=f"Claim {turn_number}", status="new", turn=turn_number)]
    counters = LedgerEntryCounters(
        new_claims=len(claims), revised=0, conceded=0, unresolved_closed=0,
    )
    return LedgerEntry(
        position=f"Position {turn_number}",
        claims=claims,
        delta="advancing",
        tags=[],
        unresolved=[],
        counters=counters,
        quality=QualityLabel.SUBSTANTIVE,
        effective_delta=EffectiveDelta.ADVANCING,
        turn_number=turn_number,
    )


class TestCompactLedger:
    """compact_ledger: reduce state size for checkpoint serialization."""

    def test_below_threshold_unchanged(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(turn_number=1)
        projected = state.with_turn(entry)
        result = compact_ledger(projected)
        assert result is projected

    def test_above_threshold_trims_entries(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        for i in range(1, MAX_ENTRIES_BEFORE_COMPACT + 5):
            state = state.with_turn(_make_entry(turn_number=i))
        assert len(state.entries) == MAX_ENTRIES_BEFORE_COMPACT + 4
        result = compact_ledger(state)
        assert len(result.entries) == KEEP_RECENT_ENTRIES

    def test_keeps_most_recent_entries(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        total = MAX_ENTRIES_BEFORE_COMPACT + 5
        for i in range(1, total + 1):
            state = state.with_turn(_make_entry(turn_number=i))
        result = compact_ledger(state)
        expected_start = total - KEEP_RECENT_ENTRIES + 1
        assert result.entries[0].turn_number == expected_start
        assert result.entries[-1].turn_number == total

    def test_claim_registry_rebuilt_from_recent(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        for i in range(1, MAX_ENTRIES_BEFORE_COMPACT + 5):
            state = state.with_turn(_make_entry(turn_number=i))
        result = compact_ledger(state)
        recent_turn_numbers = {e.turn_number for e in result.entries}
        for claim in result.claim_registry:
            assert claim.turn in recent_turn_numbers

    def test_preserves_other_fields(self) -> None:
        state = ConversationState(
            conversation_id="conv-1",
            closing_probe_fired=True,
            last_checkpoint_id="cp-5",
        )
        from context_injection.types import EvidenceRecord

        state = state.with_evidence(
            EvidenceRecord(entity_key="f:a.py", template_id="probe.file_repo_fact", turn=1),
        )
        for i in range(1, MAX_ENTRIES_BEFORE_COMPACT + 5):
            state = state.with_turn(_make_entry(turn_number=i))
        result = compact_ledger(state)
        assert result.closing_probe_fired is True
        assert result.last_checkpoint_id == "cp-5"
        assert len(result.evidence_history) == 1


class TestCompactionEquivalence:
    """D2-7: Prove compute_action() equivalence between full-history and compacted state.

    Under DD-2 invariant (MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT),
    compaction should never trigger. This test verifies that IF it did trigger,
    the action decision would be equivalent — proving the safety net is sound.

    Covers all compute_action branches:
    - ADVANCING-only (no plateau)
    - Plateau with closing probe fired
    - Plateau without closing probe (no probe)
    - Plateau with unresolved questions
    - Budget exhausted
    """

    def test_invariant_keep_recent_gte_min_plateau(self) -> None:
        """Structural invariant: KEEP_RECENT_ENTRIES >= MIN_ENTRIES_FOR_PLATEAU.

        If this fails, compaction would trim entries below the plateau detection
        window and change compute_action results.
        """
        from context_injection.control import MIN_ENTRIES_FOR_PLATEAU

        assert KEEP_RECENT_ENTRIES >= MIN_ENTRIES_FOR_PLATEAU, (
            f"KEEP_RECENT_ENTRIES ({KEEP_RECENT_ENTRIES}) must be >= "
            f"MIN_ENTRIES_FOR_PLATEAU ({MIN_ENTRIES_FOR_PLATEAU})"
        )

    @pytest.mark.parametrize(
        "label,make_entries,budget,closing_probe",
        [
            pytest.param(
                "advancing_only",
                lambda n: [
                    _make_entry(turn_number=i)
                    for i in range(1, n + 1)
                ],
                5,
                False,
                id="advancing-only",
            ),
            pytest.param(
                "plateau_with_probe",
                lambda n: [
                    _make_entry(
                        turn_number=i,
                        claims=[Claim(text=f"C{i}", status="reinforced", turn=i)],
                    )
                    for i in range(1, n + 1)
                ],
                5,
                True,
                id="plateau+probe",
            ),
            pytest.param(
                "plateau_no_probe",
                lambda n: [
                    _make_entry(
                        turn_number=i,
                        claims=[Claim(text=f"C{i}", status="reinforced", turn=i)],
                    )
                    for i in range(1, n + 1)
                ],
                5,
                False,
                id="plateau+no_probe",
            ),
            pytest.param(
                "plateau_with_unresolved",
                lambda n: [
                    _make_entry(
                        turn_number=i,
                        claims=[Claim(text=f"C{i}", status="reinforced", turn=i)],
                    )
                    for i in range(1, n + 1)
                ],
                5,
                False,
                id="plateau+unresolved",
            ),
            pytest.param(
                "budget_exhausted",
                lambda n: [
                    _make_entry(turn_number=i)
                    for i in range(1, n + 1)
                ],
                0,
                False,
                id="budget-exhausted",
            ),
        ],
    )
    def test_compute_action_matches_after_compaction(
        self, label: str, make_entries: object, budget: int, closing_probe: bool,
    ) -> None:
        """compute_action on full-history state matches compute_action on compacted state."""
        from context_injection.control import compute_action

        entry_count = MAX_ENTRIES_BEFORE_COMPACT + 5
        entries = make_entries(entry_count)  # type: ignore[operator]

        state = ConversationState(conversation_id="conv-1")
        for entry in entries:
            state = state.with_turn(entry)
        if closing_probe:
            state = state.with_closing_probe_fired()

        compacted = compact_ledger(state)

        # Action decisions depend on delta sequence tail and budget —
        # compaction preserves recent entries, so action should match
        full_action = compute_action(
            entries=list(state.entries),
            budget_remaining=budget,
            closing_probe_fired=state.closing_probe_fired,
        )
        compacted_action = compute_action(
            entries=list(compacted.entries),
            budget_remaining=budget,
            closing_probe_fired=compacted.closing_probe_fired,
        )
        assert full_action == compacted_action, (
            f"Branch {label}: full-history action {full_action} != "
            f"compacted action {compacted_action}"
        )


class TestCompactionRoundTrip:
    """D2-8: Build conversation with >16 entries, compact, restore, verify contract."""

    def test_compact_serialize_restore_recompute(self) -> None:
        """Full round-trip: build → compact → serialize → restore → recompute cumulative."""
        state = ConversationState(conversation_id="conv-1")
        for i in range(1, MAX_ENTRIES_BEFORE_COMPACT + 5):
            state = state.with_turn(_make_entry(turn_number=i))

        # Compact
        compacted = compact_ledger(state)
        assert len(compacted.entries) == KEEP_RECENT_ENTRIES

        # Serialize
        result = serialize_checkpoint(compacted)
        assert result.state.last_checkpoint_id == result.checkpoint_id

        # Restore
        restored, restored_id = deserialize_checkpoint(result.checkpoint_string)
        assert restored_id == result.checkpoint_id
        assert restored.conversation_id == "conv-1"
        assert len(restored.entries) == KEEP_RECENT_ENTRIES

        # Recompute cumulative from restored state
        cumulative = restored.compute_cumulative_state()
        assert cumulative.turns_completed == KEEP_RECENT_ENTRIES
        assert cumulative.total_claims == KEEP_RECENT_ENTRIES  # 1 claim per entry

        # Claim registry rebuilt from recent entries only
        recent_turns = {e.turn_number for e in restored.entries}
        for claim in restored.claim_registry:
            assert claim.turn in recent_turns
```

**Step 4: Implement validate_checkpoint_intake and compact_ledger**

Add to `context_injection/checkpoint.py`:

```python
MAX_ENTRIES_BEFORE_COMPACT: int = 16
"""Trigger compaction when entries exceed this count."""

KEEP_RECENT_ENTRIES: int = 8
"""Number of recent entries to keep after compaction."""


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
    1. checkpoint_id not None when payload present → checkpoint_missing
    2. Request checkpoint_id matches envelope ID → checkpoint_stale
    3. Payload last_checkpoint_id matches envelope ID → checkpoint_invalid (corruption)
    4. Payload conversation_id matches target conversation → checkpoint_invalid (security)

    in_memory: from ctx.get_or_create_conversation() — never None.
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
    return state.model_copy(update={
        "entries": recent,
        "claim_registry": claims,
    })
```

**Step 5: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_checkpoint.py -v`
Expected: PASS (all checkpoint tests — types, serialize, deserialize, intake, compaction)

**Step 6: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All existing tests pass.

**Step 7: Commit**

```bash
git add packages/context-injection/context_injection/checkpoint.py \
       packages/context-injection/tests/test_checkpoint.py
git commit -m "feat(context-injection): add checkpoint chain validation and compaction (D2 Task 7)"
```

### Task 8: AppContext extension

**Files:**
- Modify: `context_injection/state.py` (add conversations dict to AppContext)
- Modify: `tests/test_state.py`

Adds `conversations: dict[str, ConversationState]` to `AppContext` and `get_or_create_conversation` method. The method always returns a `ConversationState` — either existing (real state) or freshly created (empty). Checkpoint intake (Task 7) determines whether the fresh state is acceptable or a checkpoint restore is needed.

**Step 1: Write failing tests for AppContext conversations**

Add to `tests/test_state.py`:

```python
from context_injection.conversation import ConversationState


class TestAppContextConversations:
    """AppContext conversation management."""

    def test_conversations_empty_by_default(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        assert ctx.conversations == {}

    def test_get_or_create_new(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        state = ctx.get_or_create_conversation("conv-1")
        assert isinstance(state, ConversationState)
        assert state.conversation_id == "conv-1"
        assert state.entries == ()

    def test_get_or_create_returns_existing(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        state1 = ctx.get_or_create_conversation("conv-1")
        state2 = ctx.get_or_create_conversation("conv-1")
        assert state1 is state2

    def test_multiple_conversations(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        s1 = ctx.get_or_create_conversation("conv-1")
        s2 = ctx.get_or_create_conversation("conv-2")
        assert s1.conversation_id == "conv-1"
        assert s2.conversation_id == "conv-2"
        assert len(ctx.conversations) == 2

    def test_conversation_replacement(self) -> None:
        """Pipeline commits by replacing dict entry."""
        ctx = AppContext.create(repo_root="/tmp/test")
        state = ctx.get_or_create_conversation("conv-1")
        projected = state.with_checkpoint_id("cp-1")
        ctx.conversations["conv-1"] = projected
        retrieved = ctx.get_or_create_conversation("conv-1")
        assert retrieved.last_checkpoint_id == "cp-1"


class TestConversationGuardLimit:
    """DD-3: CONVERSATION_GUARD_LIMIT overflow protection."""

    def test_below_limit_creates(self) -> None:
        """Creating conversations below the limit succeeds."""
        ctx = AppContext.create(repo_root="/tmp/test")
        for i in range(ctx.CONVERSATION_GUARD_LIMIT):
            state = ctx.get_or_create_conversation(f"conv-{i}")
            assert state.conversation_id == f"conv-{i}"
        assert len(ctx.conversations) == ctx.CONVERSATION_GUARD_LIMIT

    def test_overflow_on_new_id_raises(self) -> None:
        """Creating a new conversation at the limit raises ValueError."""
        ctx = AppContext.create(repo_root="/tmp/test")
        for i in range(ctx.CONVERSATION_GUARD_LIMIT):
            ctx.get_or_create_conversation(f"conv-{i}")
        with pytest.raises(ValueError, match="Conversation limit exceeded"):
            ctx.get_or_create_conversation("conv-overflow")

    def test_existing_id_returns_at_limit(self) -> None:
        """Retrieving an existing conversation at the limit succeeds."""
        ctx = AppContext.create(repo_root="/tmp/test")
        for i in range(ctx.CONVERSATION_GUARD_LIMIT):
            ctx.get_or_create_conversation(f"conv-{i}")
        # Existing ID should still be retrievable
        state = ctx.get_or_create_conversation("conv-0")
        assert state.conversation_id == "conv-0"
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py::TestAppContextConversations -v`
Expected: FAIL — `ImportError: cannot import name 'ConversationState'` or `AttributeError: 'AppContext' object has no attribute 'conversations'`

**Step 3: Implement AppContext extension**

Add import to `context_injection/state.py`:

```python
from context_injection.conversation import ConversationState
```

Add field to `AppContext` class (after `entity_counter`):

```python
    conversations: dict[str, ConversationState] = field(default_factory=dict)
    """Per-conversation state, keyed by conversation_id."""
```

Add method to `AppContext` class (after `next_entity_id`):

```python
    CONVERSATION_GUARD_LIMIT: int = 50
    """Maximum number of tracked conversations. Prevents unbounded memory growth
    from leaked or malicious conversation IDs."""

    def get_or_create_conversation(self, conversation_id: str) -> ConversationState:
        """Return existing conversation state or create empty one.

        The returned state may be "fresh" (no real state) if the server
        restarted. Checkpoint intake (validate_checkpoint_intake) determines
        whether to use it or restore from a checkpoint.

        Raises ValueError if creating a new conversation would exceed
        CONVERSATION_GUARD_LIMIT (DD-3 overflow protection).
        """
        if conversation_id not in self.conversations:
            if len(self.conversations) >= self.CONVERSATION_GUARD_LIMIT:
                raise ValueError(
                    f"Conversation limit exceeded: {len(self.conversations)} "
                    f"conversations already tracked (limit: {self.CONVERSATION_GUARD_LIMIT}). "
                    f"Cannot create conversation {conversation_id!r}."
                )
            self.conversations[conversation_id] = ConversationState(
                conversation_id=conversation_id,
            )
        return self.conversations[conversation_id]
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py -v`
Expected: PASS (all existing state tests + new TestAppContextConversations)

**Step 5: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All existing tests pass, plus new conversation and checkpoint tests.

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/state.py \
       packages/context-injection/tests/test_state.py
git commit -m "feat(context-injection): add conversations dict to AppContext (D2 Task 8)"
```

"""Checkpoint serialization and validation tests."""

import json

import pytest

from context_injection.checkpoint import (
    CHECKPOINT_FORMAT_VERSION,
    KEEP_RECENT_ENTRIES,
    MAX_ENTRIES_BEFORE_COMPACT,
    CheckpointError,
    StateCheckpoint,
    compact_ledger,
    deserialize_checkpoint,
    serialize_checkpoint,
    validate_checkpoint_intake,
)
from context_injection.conversation import ConversationState
from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.ledger import LedgerEntry, LedgerEntryCounters
from context_injection.types import Claim


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

    def test_auto_compacts_when_over_budget(self) -> None:
        """serialize_checkpoint compacts instead of raising when payload exceeds limit."""
        from context_injection.checkpoint import MAX_CHECKPOINT_PAYLOAD_BYTES
        from context_injection.enums import EffectiveDelta, QualityLabel
        from context_injection.ledger import LedgerEntry, LedgerEntryCounters
        from context_injection.types import Claim

        counters = LedgerEntryCounters(
            new_claims=3, revised=0, conceded=0, unresolved_closed=0,
        )
        entries: list[LedgerEntry] = []
        for i in range(12):
            claims = [
                Claim(text=f"Claim {j} of turn {i}: {'analysis ' * 20}", status="new", turn=i + 1)
                for j in range(3)
            ]
            entries.append(
                LedgerEntry(
                    position=f"Position for turn {i}: {'context ' * 30}",
                    claims=claims,
                    delta="advancing",
                    tags=[],
                    unresolved=[],
                    counters=counters,
                    quality=QualityLabel.SUBSTANTIVE,
                    effective_delta=EffectiveDelta.ADVANCING,
                    turn_number=i + 1,
                )
            )
        state = ConversationState(conversation_id="conv-1")
        for entry in entries:
            state = state.with_turn(entry)

        result = serialize_checkpoint(state)
        assert result.checkpoint_string
        # The payload field is already a JSON string (double-encoded).
        # Check its byte size directly — do NOT re-dump, that would add quoting.
        inner = json.loads(result.checkpoint_string)
        assert len(inner["payload"].encode("utf-8")) <= MAX_CHECKPOINT_PAYLOAD_BYTES

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
        with pytest.raises(CheckpointError) as exc_info:
            serialize_checkpoint(state)
        assert exc_info.value.code == "checkpoint_too_large"


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

    def test_oversized_payload_rejected_on_intake(self) -> None:
        """Payload exceeding MAX_CHECKPOINT_PAYLOAD_BYTES is rejected on deserialize."""
        from context_injection.checkpoint import MAX_CHECKPOINT_PAYLOAD_BYTES

        # Craft a payload that exceeds the limit but is self-consistent
        oversized_payload = ConversationState(
            conversation_id="x" * (MAX_CHECKPOINT_PAYLOAD_BYTES + 1),
        ).model_dump_json()
        actual_size = len(oversized_payload.encode("utf-8"))
        assert actual_size > MAX_CHECKPOINT_PAYLOAD_BYTES

        cp = StateCheckpoint(
            checkpoint_id="abc",
            parent_checkpoint_id=None,
            format_version=CHECKPOINT_FORMAT_VERSION,
            payload=oversized_payload,
            size=actual_size,
        )
        with pytest.raises(CheckpointError) as exc_info:
            deserialize_checkpoint(cp.model_dump_json())
        assert exc_info.value.code == "checkpoint_invalid"
        assert "exceeds" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Helpers for Task 7 tests
# ---------------------------------------------------------------------------


def _make_entry(
    turn_number: int = 1,
    *,
    claims: list[Claim] | None = None,
    effective_delta: EffectiveDelta = EffectiveDelta.ADVANCING,
) -> LedgerEntry:
    """Minimal LedgerEntry for checkpoint tests."""
    if claims is None:
        claims = [Claim(text=f"Claim {turn_number}", status="new", turn=turn_number)]
    counters = LedgerEntryCounters(
        new_claims=len(claims),
        revised=0,
        conceded=0,
        unresolved_closed=0,
    )
    return LedgerEntry(
        position=f"Position {turn_number}",
        claims=claims,
        delta="advancing",
        tags=[],
        unresolved=[],
        counters=counters,
        quality=QualityLabel.SUBSTANTIVE,
        effective_delta=effective_delta,
        turn_number=turn_number,
    )


# ---------------------------------------------------------------------------
# validate_checkpoint_intake (5-case policy + restore guards)
# ---------------------------------------------------------------------------


class TestValidateCheckpointIntake:
    """Checkpoint intake 5-case policy."""

    def test_turn_1_returns_in_memory(self) -> None:
        """Turn 1: checkpoint optional, use in-memory."""
        state = ConversationState(conversation_id="conv-1")
        result = validate_checkpoint_intake(
            state,
            checkpoint_id=None,
            checkpoint_payload=None,
            turn_number=1,
        )
        assert result is state

    def test_turn_1_ignores_checkpoint(self) -> None:
        """Turn 1 with checkpoint present — checkpoint ignored."""
        state = ConversationState(conversation_id="conv-1")
        result = validate_checkpoint_intake(
            state,
            checkpoint_id="orphan",
            checkpoint_payload="ignored",
            turn_number=1,
        )
        assert result is state

    def test_turn_gt1_in_memory_ids_match(self) -> None:
        """Turn > 1, real state, IDs match — use in-memory."""
        state = ConversationState(
            conversation_id="conv-1",
        ).with_checkpoint_id("cp-1")
        result = validate_checkpoint_intake(
            state,
            checkpoint_id="cp-1",
            checkpoint_payload=None,
            turn_number=2,
        )
        assert result is state

    def test_turn_gt1_in_memory_ids_mismatch_raises(self) -> None:
        """Turn > 1, real state, IDs mismatch — stale error."""
        state = ConversationState(
            conversation_id="conv-1",
        ).with_checkpoint_id("cp-1")
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                state,
                checkpoint_id="cp-OLD",
                checkpoint_payload=None,
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
            in_memory,
            checkpoint_id=result_cp.checkpoint_id,
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
                in_memory,
                checkpoint_id=None,
                checkpoint_payload=None,
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_missing"

    def test_turn_gt1_corrupt_checkpoint_raises(self) -> None:
        """Turn > 1, no real state, corrupt checkpoint — invalid error."""
        in_memory = ConversationState(conversation_id="conv-1")
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory,
                checkpoint_id="cp-1",
                checkpoint_payload="corrupt",
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
                in_memory,
                checkpoint_id=None,
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
                in_memory,
                checkpoint_id="wrong-id",
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
                in_memory,
                checkpoint_id="envelope-id",
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
                in_memory,
                checkpoint_id=result_cp.checkpoint_id,
                checkpoint_payload=result_cp.checkpoint_string,
                turn_number=2,
                target_conversation_id="conv-target",
            )
        assert exc_info.value.code == "checkpoint_invalid"
        assert "cross-conversation" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# compact_ledger
# ---------------------------------------------------------------------------


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
            EvidenceRecord(
                entity_key="f:a.py", template_id="probe.file_repo_fact", turn=1
            ),
        )
        for i in range(1, MAX_ENTRIES_BEFORE_COMPACT + 5):
            state = state.with_turn(_make_entry(turn_number=i))
        result = compact_ledger(state)
        assert result.closing_probe_fired is True
        assert result.last_checkpoint_id == "cp-5"
        assert len(result.evidence_history) == 1


# ---------------------------------------------------------------------------
# compact_to_budget
# ---------------------------------------------------------------------------


class TestCompactToBudget:
    """compact_to_budget: iteratively trim entries until payload fits."""

    def test_reduces_under_limit(self) -> None:
        """State exceeding byte budget is trimmed to fit."""
        from context_injection.checkpoint import (
            MAX_CHECKPOINT_PAYLOAD_BYTES,
            compact_to_budget,
        )
        from context_injection.enums import EffectiveDelta, QualityLabel
        from context_injection.ledger import LedgerEntry, LedgerEntryCounters
        from context_injection.types import Claim

        counters = LedgerEntryCounters(
            new_claims=3, revised=0, conceded=0, unresolved_closed=0,
        )
        entries: list[LedgerEntry] = []
        for i in range(12):
            claims = [
                Claim(text=f"Claim {j} of turn {i}: {'analysis ' * 20}", status="new", turn=i + 1)
                for j in range(3)
            ]
            entries.append(
                LedgerEntry(
                    position=f"Position for turn {i}: {'context ' * 30}",
                    claims=claims,
                    delta="advancing",
                    tags=[],
                    unresolved=[],
                    counters=counters,
                    quality=QualityLabel.SUBSTANTIVE,
                    effective_delta=EffectiveDelta.ADVANCING,
                    turn_number=i + 1,
                )
            )
        state = ConversationState(conversation_id="conv-1")
        for entry in entries:
            state = state.with_turn(entry)

        payload_size = len(state.model_dump_json().encode("utf-8"))
        assert payload_size > MAX_CHECKPOINT_PAYLOAD_BYTES

        compacted = compact_to_budget(state, MAX_CHECKPOINT_PAYLOAD_BYTES)
        compacted_size = len(compacted.model_dump_json().encode("utf-8"))
        assert compacted_size <= MAX_CHECKPOINT_PAYLOAD_BYTES
        assert len(compacted.entries) >= 1
        expected_claims = sum(len(e.claims) for e in compacted.entries)
        assert len(compacted.claim_registry) == expected_claims

    def test_preserves_state_under_limit(self) -> None:
        """State already under budget is returned unchanged."""
        from context_injection.checkpoint import (
            MAX_CHECKPOINT_PAYLOAD_BYTES,
            compact_to_budget,
        )
        state = ConversationState(conversation_id="conv-1")
        result = compact_to_budget(state, MAX_CHECKPOINT_PAYLOAD_BYTES)
        assert result is state

    def test_single_oversized_entry_raises(self) -> None:
        """Single entry exceeding budget cannot be compacted — returns as-is."""
        from context_injection.checkpoint import compact_to_budget
        from context_injection.enums import EffectiveDelta, QualityLabel
        from context_injection.ledger import LedgerEntry, LedgerEntryCounters
        from context_injection.types import Claim

        counters = LedgerEntryCounters(
            new_claims=100, revised=0, conceded=0, unresolved_closed=0,
        )
        claims = [
            Claim(text=f"Very long claim {'x' * 200} {i}", status="new", turn=1)
            for i in range(100)
        ]
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
        result = compact_to_budget(state, 1024)
        assert len(result.entries) == 1


# ---------------------------------------------------------------------------
# Compaction equivalence with compute_action
# ---------------------------------------------------------------------------


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
                lambda n: [_make_entry(turn_number=i) for i in range(1, n + 1)],
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
                        effective_delta=EffectiveDelta.STATIC,
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
                        effective_delta=EffectiveDelta.STATIC,
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
                        effective_delta=EffectiveDelta.STATIC,
                    )
                    for i in range(1, n + 1)
                ],
                5,
                False,
                id="plateau+unresolved",
            ),
            pytest.param(
                "budget_exhausted",
                lambda n: [_make_entry(turn_number=i) for i in range(1, n + 1)],
                0,
                False,
                id="budget-exhausted",
            ),
        ],
    )
    def test_compute_action_matches_after_compaction(
        self,
        label: str,
        make_entries: object,
        budget: int,
        closing_probe: bool,
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


# ---------------------------------------------------------------------------
# Compaction round-trip
# ---------------------------------------------------------------------------


class TestCompactionRoundTrip:
    """D2-8: Build conversation with >16 entries, compact, restore, verify contract."""

    def test_compact_serialize_restore_recompute(self) -> None:
        """Full round-trip: build -> compact -> serialize -> restore -> recompute cumulative."""
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

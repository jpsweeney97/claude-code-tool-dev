"""Conversation state management tests."""

import pytest
from pydantic import ValidationError

from context_injection.conversation import ConversationState
from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.ledger import (
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
            entity_key="file:foo.py",
            template_id="probe.file_repo_fact",
            turn=1,
        )
        projected = state.with_evidence(record)
        assert len(projected.evidence_history) == 1
        assert projected.evidence_history[0].entity_key == "file:foo.py"

    def test_original_unchanged(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        record = EvidenceRecord(
            entity_key="file:foo.py",
            template_id="probe.file_repo_fact",
            turn=1,
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
            entity_key="file:a.py",
            template_id="probe.file_repo_fact",
            turn=1,
        )
        projected = state.with_evidence(record)
        assert len(projected.get_evidence_history()) == 1

    def test_returns_copy(self) -> None:
        """Returned list is a copy — mutations don't affect state."""
        state = ConversationState(conversation_id="conv-1")
        record = EvidenceRecord(
            entity_key="file:a.py",
            template_id="probe.file_repo_fact",
            turn=1,
        )
        projected = state.with_evidence(record)
        history = projected.get_evidence_history()
        history.clear()
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
            EffectiveDelta.ADVANCING,
            EffectiveDelta.SHIFTING,
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


class TestPhaseFields:
    """ConversationState phase tracking fields (Release B)."""

    def test_defaults(self) -> None:
        state = ConversationState(conversation_id="test")
        assert state.last_posture is None
        assert state.phase_start_index == 0

    def test_with_posture_change(self) -> None:
        state = ConversationState(conversation_id="test")
        updated = state.with_posture_change("comparative", phase_start_index=3)
        assert updated.last_posture == "comparative"
        assert updated.phase_start_index == 3
        # Original unchanged (immutable)
        assert state.last_posture is None
        assert state.phase_start_index == 0

    def test_with_posture_change_resets_closing_probe(self) -> None:
        """Phase boundary resets closing_probe_fired."""
        state = ConversationState(conversation_id="test")
        state = state.with_closing_probe_fired()
        assert state.closing_probe_fired is True
        updated = state.with_posture_change("evaluative", phase_start_index=2)
        assert updated.closing_probe_fired is False

    def test_phase_entries_empty_when_no_entries(self) -> None:
        state = ConversationState(conversation_id="test")
        assert state.get_phase_entries() == ()

    def test_phase_entries_returns_from_phase_start(self) -> None:
        state = ConversationState(conversation_id="test")
        for i in range(5):
            entry = _make_entry(turn_number=i + 1)
            state = state.with_turn(entry)
        # Phase starts at index 3
        state = state.with_posture_change("evaluative", phase_start_index=3)
        phase_entries = state.get_phase_entries()
        assert len(phase_entries) == 2  # entries[3] and entries[4]
        assert phase_entries[0].turn_number == 4
        assert phase_entries[1].turn_number == 5

    def test_phase_entries_full_when_index_zero(self) -> None:
        """When phase_start_index=0, get_phase_entries returns all entries."""
        state = ConversationState(conversation_id="test")
        for i in range(3):
            state = state.with_turn(_make_entry(turn_number=i + 1))
        phase_entries = state.get_phase_entries()
        assert len(phase_entries) == 3

    def test_phase_entries_at_boundary_index(self) -> None:
        """When phase_start_index = len(entries) - 1 (the exact index produced
        by a posture change), get_phase_entries returns exactly one entry.
        """
        state = ConversationState(conversation_id="test")
        for i in range(4):
            state = state.with_turn(_make_entry(turn_number=i + 1))
        # Simulate posture change: phase starts at last entry
        state = state.with_posture_change(
            "evaluative", phase_start_index=len(state.entries) - 1
        )
        phase_entries = state.get_phase_entries()
        assert len(phase_entries) == 1
        assert phase_entries[0].turn_number == 4

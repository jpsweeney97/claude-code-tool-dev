"""Tests for conversation control — action computation and ledger summary."""

from __future__ import annotations

from context_injection.control import ConversationAction, compute_action
from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.ledger import LedgerEntry, LedgerEntryCounters
from context_injection.types import Claim, Unresolved


def _make_entry(
    *,
    turn_number: int = 1,
    position: str = "Test position",
    effective_delta: EffectiveDelta = EffectiveDelta.ADVANCING,
    claims: list[Claim] | None = None,
    unresolved: list[Unresolved] | None = None,
) -> LedgerEntry:
    """Create a minimal LedgerEntry for control tests."""
    return LedgerEntry(
        position=position,
        claims=claims or [],
        delta="advancing",
        tags=["architecture"],
        unresolved=unresolved or [],
        counters=LedgerEntryCounters(
            new_claims=len(claims) if claims else 0,
            revised=0,
            conceded=0,
            unresolved_closed=0,
        ),
        quality=QualityLabel.SUBSTANTIVE,
        effective_delta=effective_delta,
        turn_number=turn_number,
    )


class TestConversationAction:
    """ConversationAction enum membership and string values."""

    def test_members(self) -> None:
        assert set(ConversationAction) == {
            ConversationAction.CONTINUE_DIALOGUE,
            ConversationAction.CLOSING_PROBE,
            ConversationAction.CONCLUDE,
        }

    def test_values_are_snake_case(self) -> None:
        assert ConversationAction.CONTINUE_DIALOGUE == "continue_dialogue"
        assert ConversationAction.CLOSING_PROBE == "closing_probe"
        assert ConversationAction.CONCLUDE == "conclude"

    def test_is_str_enum(self) -> None:
        assert isinstance(ConversationAction.CONTINUE_DIALOGUE, str)


class TestComputeActionBudgetExhausted:
    """Budget exhaustion takes highest precedence."""

    def test_budget_zero_returns_conclude(self) -> None:
        entries = [_make_entry(turn_number=1)]
        action, reason = compute_action(entries, budget_remaining=0, closing_probe_fired=False)
        assert action == ConversationAction.CONCLUDE
        assert "budget" in reason.lower()

    def test_budget_negative_returns_conclude(self) -> None:
        entries = [_make_entry(turn_number=1)]
        action, reason = compute_action(entries, budget_remaining=-1, closing_probe_fired=False)
        assert action == ConversationAction.CONCLUDE

    def test_budget_zero_trumps_advancing(self) -> None:
        """Even with advancing deltas, budget exhaustion concludes."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(entries, budget_remaining=0, closing_probe_fired=False)
        assert action == ConversationAction.CONCLUDE


class TestComputeActionPlateau:
    """Plateau = last 2 effective_deltas both STATIC."""

    def test_two_static_is_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.STATIC),
        ]
        action, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CLOSING_PROBE
        assert "plateau" in reason.lower()

    def test_one_static_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_static_then_advancing_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_static_then_shifting_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.SHIFTING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE


class TestComputeActionClosingProbe:
    """Closing probe sequencing — fire once, then conclude."""

    def test_plateau_without_closing_probe_fires_probe(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CLOSING_PROBE

    def test_plateau_with_closing_probe_already_fired_concludes(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=True)
        assert action == ConversationAction.CONCLUDE
        assert "plateau" in reason.lower()

    def test_plateau_with_unresolved_and_probe_fired_continues(self) -> None:
        """Plateau + closing probe fired BUT unresolved items remain -> continue."""
        entries = [
            _make_entry(
                turn_number=1,
                effective_delta=EffectiveDelta.STATIC,
            ),
            _make_entry(
                turn_number=2,
                effective_delta=EffectiveDelta.STATIC,
                unresolved=[Unresolved(text="Open question", turn=1)],
            ),
        ]
        action, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=True)
        assert action == ConversationAction.CONTINUE_DIALOGUE
        assert "unresolved" in reason.lower()

    def test_plateau_revived_by_advancing_resets(self) -> None:
        """If conversation advances after plateau, it's no longer plateau."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=4, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=True)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_re_plateau_after_advance_concludes(self) -> None:
        """Full cycle: plateau -> advance -> re-plateau with probe already fired -> CONCLUDE."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=4, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=5, effective_delta=EffectiveDelta.STATIC),
        ]
        action, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=True)
        assert action == ConversationAction.CONCLUDE
        assert "plateau" in reason.lower()

    def test_re_plateau_with_unresolved_continues(self) -> None:
        """Full cycle re-plateau with probe fired BUT unresolved items -> CONTINUE."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=4, effective_delta=EffectiveDelta.STATIC),
            _make_entry(
                turn_number=5,
                effective_delta=EffectiveDelta.STATIC,
                unresolved=[Unresolved(text="Open question", turn=5)],
            ),
        ]
        action, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=True)
        assert action == ConversationAction.CONTINUE_DIALOGUE
        assert "unresolved" in reason.lower()


class TestComputeActionContinue:
    """Default path — conversation continues."""

    def test_single_entry_continues(self) -> None:
        entries = [_make_entry(turn_number=1)]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_advancing_entries_continue(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_empty_entries_continues(self) -> None:
        """No entries = first turn, always continue."""
        action, reason = compute_action([], budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE
        assert "first" in reason.lower() or "no entries" in reason.lower()

    def test_shifting_entries_continue(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.SHIFTING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.SHIFTING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_budget_one_continues(self) -> None:
        """budget_remaining=1 means one turn left — still continue."""
        entries = [_make_entry(turn_number=1)]
        action, _ = compute_action(entries, budget_remaining=1, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE


class TestComputeActionReasonStrings:
    """Verify reason strings are descriptive (not just action names)."""

    def test_budget_reason_mentions_budget(self) -> None:
        _, reason = compute_action(
            [_make_entry()], budget_remaining=0, closing_probe_fired=False,
        )
        assert len(reason) > 10

    def test_plateau_reason_mentions_static(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        _, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert len(reason) > 10

    def test_continue_reason_is_nonempty(self) -> None:
        _, reason = compute_action(
            [_make_entry()], budget_remaining=5, closing_probe_fired=False,
        )
        assert len(reason) > 0


class TestComputeActionPrecedenceInteractions:
    """Precedence and interaction tests — budget exhaustion beats all other conditions."""

    def test_empty_entries_budget_zero_returns_conclude(self) -> None:
        """compute_action([], budget_remaining=0) returns CONCLUDE, not CONTINUE."""
        action, reason = compute_action([], budget_remaining=0, closing_probe_fired=False)
        assert action == ConversationAction.CONCLUDE
        assert "budget" in reason.lower()

    def test_budget_zero_trumps_plateau_and_unresolved(self) -> None:
        """budget=0 + plateau + unresolved returns CONCLUDE (budget wins)."""
        entries = [
            _make_entry(
                turn_number=1,
                effective_delta=EffectiveDelta.STATIC,
            ),
            _make_entry(
                turn_number=2,
                effective_delta=EffectiveDelta.STATIC,
                unresolved=[Unresolved(text="Open question", turn=2)],
            ),
        ]
        action, reason = compute_action(
            entries, budget_remaining=0, closing_probe_fired=True,
        )
        assert action == ConversationAction.CONCLUDE
        assert "budget" in reason.lower()

    def test_closing_probe_at_budget_one_then_budget_zero_concludes(self) -> None:
        """Closing probe fires at budget=1; next call at budget=0 forces CONCLUDE."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        # First call: budget=1, probe not yet fired -> CLOSING_PROBE
        action_1, _ = compute_action(
            entries, budget_remaining=1, closing_probe_fired=False,
        )
        assert action_1 == ConversationAction.CLOSING_PROBE

        # Second call: budget=0, probe now fired -> CONCLUDE (budget exhaustion)
        action_2, reason = compute_action(
            entries, budget_remaining=0, closing_probe_fired=True,
        )
        assert action_2 == ConversationAction.CONCLUDE
        assert "budget" in reason.lower()

    def test_unresolved_only_checked_on_latest_entry(self) -> None:
        """Unresolved items on earlier entries do NOT prevent CONCLUDE — only latest matters."""
        entries = [
            _make_entry(
                turn_number=1,
                effective_delta=EffectiveDelta.STATIC,
                unresolved=[Unresolved(text="Old question", turn=1)],
            ),
            _make_entry(
                turn_number=2,
                effective_delta=EffectiveDelta.STATIC,
                # Latest entry: no unresolved
            ),
        ]
        action, reason = compute_action(
            entries, budget_remaining=5, closing_probe_fired=True,
        )
        assert action == ConversationAction.CONCLUDE
        assert "plateau" in reason.lower()

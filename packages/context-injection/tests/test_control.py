"""Tests for conversation control — action computation and ledger summary."""

from __future__ import annotations

from context_injection.control import (
    ConversationAction,
    compute_action,
    generate_ledger_summary,
)
from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.ledger import CumulativeState, LedgerEntry, LedgerEntryCounters
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
        action, reason = compute_action(
            entries, budget_remaining=0, closing_probe_fired=False
        )
        assert action == ConversationAction.CONCLUDE
        assert "budget" in reason.lower()

    def test_budget_negative_returns_conclude(self) -> None:
        entries = [_make_entry(turn_number=1)]
        action, reason = compute_action(
            entries, budget_remaining=-1, closing_probe_fired=False
        )
        assert action == ConversationAction.CONCLUDE

    def test_budget_zero_trumps_advancing(self) -> None:
        """Even with advancing deltas, budget exhaustion concludes."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(
            entries, budget_remaining=0, closing_probe_fired=False
        )
        assert action == ConversationAction.CONCLUDE


class TestComputeActionPlateau:
    """Plateau = last 2 effective_deltas both STATIC."""

    def test_two_static_is_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.STATIC),
        ]
        action, reason = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CLOSING_PROBE
        assert "plateau" in reason.lower()

    def test_one_static_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, _ = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_static_then_advancing_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_static_then_shifting_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.SHIFTING),
        ]
        action, _ = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE


class TestComputeActionClosingProbe:
    """Closing probe sequencing — fire once, then conclude."""

    def test_plateau_without_closing_probe_fires_probe(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, _ = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CLOSING_PROBE

    def test_plateau_with_closing_probe_already_fired_concludes(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, reason = compute_action(
            entries, budget_remaining=5, closing_probe_fired=True
        )
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
        action, reason = compute_action(
            entries, budget_remaining=5, closing_probe_fired=True
        )
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
        action, _ = compute_action(
            entries, budget_remaining=5, closing_probe_fired=True
        )
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
        action, reason = compute_action(
            entries, budget_remaining=5, closing_probe_fired=True
        )
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
        action, reason = compute_action(
            entries, budget_remaining=5, closing_probe_fired=True
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE
        assert "unresolved" in reason.lower()


class TestComputeActionContinue:
    """Default path — conversation continues."""

    def test_single_entry_continues(self) -> None:
        entries = [_make_entry(turn_number=1)]
        action, _ = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_advancing_entries_continue(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_empty_entries_continues(self) -> None:
        """No entries = first turn, always continue."""
        action, reason = compute_action(
            [], budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE
        assert "first" in reason.lower() or "no entries" in reason.lower()

    def test_shifting_entries_continue(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.SHIFTING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.SHIFTING),
        ]
        action, _ = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_budget_one_continues(self) -> None:
        """budget_remaining=1 means one turn left — still continue."""
        entries = [_make_entry(turn_number=1)]
        action, _ = compute_action(
            entries, budget_remaining=1, closing_probe_fired=False
        )
        assert action == ConversationAction.CONTINUE_DIALOGUE


class TestComputeActionReasonStrings:
    """Verify reason strings are descriptive (not just action names)."""

    def test_budget_reason_mentions_budget(self) -> None:
        _, reason = compute_action(
            [_make_entry()],
            budget_remaining=0,
            closing_probe_fired=False,
        )
        assert len(reason) > 10

    def test_plateau_reason_mentions_static(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        _, reason = compute_action(
            entries, budget_remaining=5, closing_probe_fired=False
        )
        assert len(reason) > 10

    def test_continue_reason_is_nonempty(self) -> None:
        _, reason = compute_action(
            [_make_entry()],
            budget_remaining=5,
            closing_probe_fired=False,
        )
        assert len(reason) > 0


class TestComputeActionPrecedenceInteractions:
    """Precedence and interaction tests — budget exhaustion beats all other conditions."""

    def test_empty_entries_budget_zero_returns_conclude(self) -> None:
        """compute_action([], budget_remaining=0) returns CONCLUDE, not CONTINUE."""
        action, reason = compute_action(
            [], budget_remaining=0, closing_probe_fired=False
        )
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
            entries,
            budget_remaining=0,
            closing_probe_fired=True,
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
            entries,
            budget_remaining=1,
            closing_probe_fired=False,
        )
        assert action_1 == ConversationAction.CLOSING_PROBE

        # Second call: budget=0, probe now fired -> CONCLUDE (budget exhaustion)
        action_2, reason = compute_action(
            entries,
            budget_remaining=0,
            closing_probe_fired=True,
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
            entries,
            budget_remaining=5,
            closing_probe_fired=True,
        )
        assert action == ConversationAction.CONCLUDE
        assert "plateau" in reason.lower()


# ---------------------------------------------------------------------------
# generate_ledger_summary tests
# ---------------------------------------------------------------------------

# NOTE: Tests below hand-build CumulativeState with values that may be
# inconsistent with the entries passed alongside them (e.g., total_claims
# doesn't match len(claims) across entries). This is intentional for unit
# testing — each test controls exactly the state it needs. During
# implementation, consider a builder helper that derives CumulativeState
# from entries to reduce manual bookkeeping in new tests.


class TestGenerateLedgerSummaryFormat:
    """Output format: turn lines + state line + trajectory line."""

    def test_single_entry_format(self) -> None:
        entries = [
            _make_entry(
                turn_number=1,
                position="Initial analysis of auth module",
                effective_delta=EffectiveDelta.ADVANCING,
            ),
        ]
        cumulative = CumulativeState(
            total_claims=3,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=1,
            unresolved_closed=0,
            turns_completed=1,
            effective_delta_sequence=[EffectiveDelta.ADVANCING],
        )
        result = generate_ledger_summary(entries, cumulative)

        # Must contain turn line
        assert "T1:" in result
        assert "Initial analysis of auth module" in result
        assert "advancing" in result.lower()

        # Must contain state line
        assert "claims" in result.lower()

        # Must contain trajectory line
        assert "trajectory" in result.lower()

    def test_multi_entry_format(self) -> None:
        entries = [
            _make_entry(
                turn_number=1,
                position="Auth module analysis",
                effective_delta=EffectiveDelta.ADVANCING,
                claims=[Claim(text="JWT is best", status="new", turn=1)],
            ),
            _make_entry(
                turn_number=2,
                position="Revised to OAuth",
                effective_delta=EffectiveDelta.SHIFTING,
                claims=[
                    Claim(text="JWT is best", status="revised", turn=2),
                    Claim(text="OAuth preferred", status="new", turn=2),
                ],
            ),
            _make_entry(
                turn_number=3,
                position="Confirmed OAuth approach",
                effective_delta=EffectiveDelta.STATIC,
                claims=[
                    Claim(text="OAuth preferred", status="reinforced", turn=3),
                ],
            ),
        ]
        cumulative = CumulativeState(
            total_claims=4,
            reinforced=1,
            revised=1,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=3,
            effective_delta_sequence=[
                EffectiveDelta.ADVANCING,
                EffectiveDelta.SHIFTING,
                EffectiveDelta.STATIC,
            ],
        )
        result = generate_ledger_summary(entries, cumulative)

        # All turn lines present
        assert "T1:" in result
        assert "T2:" in result
        assert "T3:" in result

        # State line has key counters
        assert "4" in result  # total_claims
        assert "reinforced" in result.lower()

    def test_turn_lines_include_tags(self) -> None:
        entries = [
            LedgerEntry(
                position="Security review",
                claims=[],
                delta="advancing",
                tags=["security", "auth"],
                unresolved=[],
                counters=LedgerEntryCounters(
                    new_claims=0,
                    revised=0,
                    conceded=0,
                    unresolved_closed=0,
                ),
                quality=QualityLabel.SUBSTANTIVE,
                effective_delta=EffectiveDelta.ADVANCING,
                turn_number=1,
            ),
        ]
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=1,
            effective_delta_sequence=[EffectiveDelta.ADVANCING],
        )
        result = generate_ledger_summary(entries, cumulative)
        assert "security" in result.lower()
        assert "auth" in result.lower()

    def test_trajectory_line_shows_sequence(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.SHIFTING),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.STATIC),
        ]
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=3,
            effective_delta_sequence=[
                EffectiveDelta.ADVANCING,
                EffectiveDelta.SHIFTING,
                EffectiveDelta.STATIC,
            ],
        )
        result = generate_ledger_summary(entries, cumulative)
        # Trajectory should show the sequence
        lines = result.strip().split("\n")
        trajectory_lines = [ln for ln in lines if "trajectory" in ln.lower()]
        assert len(trajectory_lines) == 1
        traj = trajectory_lines[0].lower()
        assert "advancing" in traj
        assert "shifting" in traj
        assert "static" in traj


class TestGenerateLedgerSummaryEdgeCases:
    """Edge cases: empty entries, long positions, many turns."""

    def test_empty_entries_returns_minimal(self) -> None:
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=0,
            effective_delta_sequence=[],
        )
        result = generate_ledger_summary([], cumulative)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "no turns" in result.lower() or "0" in result

    def test_position_truncated_if_long(self) -> None:
        """Positions longer than 80 chars should be truncated in summary."""
        long_position = "A" * 200
        entries = [
            _make_entry(turn_number=1, position=long_position),
        ]
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=1,
            effective_delta_sequence=[EffectiveDelta.ADVANCING],
        )
        result = generate_ledger_summary(entries, cumulative)
        # The full 200-char position should NOT appear verbatim
        assert long_position not in result
        # But a truncated version should
        assert "T1:" in result

    def test_unresolved_count_in_state_line(self) -> None:
        entries = [
            _make_entry(
                turn_number=1,
                unresolved=[
                    Unresolved(text="Q1", turn=1),
                    Unresolved(text="Q2", turn=1),
                ],
            ),
        ]
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=2,
            unresolved_closed=0,
            turns_completed=1,
            effective_delta_sequence=[EffectiveDelta.ADVANCING],
        )
        result = generate_ledger_summary(entries, cumulative)
        assert "unresolved" in result.lower()


class TestGenerateLedgerSummaryTokenBudget:
    """Summary should stay within token budget (~300-400 tokens for 8 turns)."""

    def test_eight_turn_summary_within_budget(self) -> None:
        """8 turns should produce roughly 300-400 tokens (~1200-1600 chars)."""
        entries = [
            _make_entry(
                turn_number=i + 1,
                position=f"Analysis of component {i + 1} with findings",
                effective_delta=[
                    EffectiveDelta.ADVANCING,
                    EffectiveDelta.ADVANCING,
                    EffectiveDelta.SHIFTING,
                    EffectiveDelta.ADVANCING,
                    EffectiveDelta.STATIC,
                    EffectiveDelta.STATIC,
                    EffectiveDelta.ADVANCING,
                    EffectiveDelta.STATIC,
                ][i],
                claims=[Claim(text=f"Claim {i + 1}", status="new", turn=i + 1)],
            )
            for i in range(8)
        ]
        deltas = [e.effective_delta for e in entries]
        cumulative = CumulativeState(
            total_claims=8,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=8,
            effective_delta_sequence=deltas,
        )
        result = generate_ledger_summary(entries, cumulative)

        # Rough token estimate: 1 token ~ 4 chars
        char_count = len(result)
        estimated_tokens = char_count / 4
        assert estimated_tokens < 600, (
            f"Summary too long: ~{estimated_tokens:.0f} tokens ({char_count} chars)"
        )
        assert estimated_tokens > 100, (
            f"Summary too short: ~{estimated_tokens:.0f} tokens ({char_count} chars)"
        )

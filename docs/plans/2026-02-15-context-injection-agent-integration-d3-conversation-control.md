# D3: Conversation Control + Ledger Summary — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Delivery:** D3 of 6 (D1, D2, D3, D4a, D4b, D5)
**Objective:** Implement pure functions for conversation action computation (continue/closing_probe/conclude) and ledger summary generation.
**Execution order position:** 2 of 6 (D1 → D3 → D2 → D4a → D4b → D5)
**Branch:** `feature/context-injection-agent-integration`
**Package directory:** `packages/context-injection/`
**Test command:** `cd packages/context-injection && uv run pytest tests/ -v`

## Prerequisite Contract

**Requires from D1:**
- From `context_injection/ledger.py`: `LedgerEntry`, `LedgerEntryCounters`, `CumulativeState`
- From `context_injection/enums.py`: `EffectiveDelta`, `QualityLabel`

**Critical invariant:** D3 functions are pure on D1 types only — they do NOT take ConversationState (D2) as input. The pipeline extracts data from ConversationState and passes it to D3 functions.

**Adaptation:** If D1 type or enum names differ from this plan, adapt references and note the mapping.

## Files in Scope

**Create:**
- `context_injection/control.py` — Conversation action computation, ledger summary generation
- `tests/test_control.py` — D3 control + summary tests

**Modify:** None.

**Out of scope:** All files not listed above. In particular, do NOT modify `context_injection/conversation.py` (D2) or any pipeline files.

## Done Criteria

- Control functions work correctly on D1 types
- D3 tests pass
- Functions are pure (no side effects, no state mutation)

## Scope Boundary

This document covers D3 only. After completing all tasks in this delivery, stop. Do not proceed to subsequent deliveries.

## Relevant Resolved Questions

**Q3 — D3 parameter design:** Keep D3 functions pure on D1 types (not ConversationState). Pipeline extracts data and passes it. Decoupling enables D2/D3 parallelism.

---

Pure additive delivery. New `control.py` module. Pure functions on D1 types.

**Estimated new tests:** 50-80
**Depends on:** D1 complete (uses LedgerEntry, CumulativeState, EffectiveDelta)

### Task 9: Conversation action computation

**Files:**
- Create: `context_injection/control.py`
- Create: `tests/test_control.py`

`compute_action` determines what the agent should do next based on conversation trajectory. It's a pure function with clear precedence rules — budget exhaustion is checked first (hard stop), then plateau detection (convergence signal), then closing probe sequencing (soft landing), otherwise continue.

**Step 1: Write failing tests for ConversationAction enum**

Create `tests/test_control.py`:

```python
"""Tests for conversation control — action computation and ledger summary."""

from __future__ import annotations

import pytest

from context_injection.control import ConversationAction


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
```

Run: `cd packages/context-injection && uv run pytest tests/test_control.py::TestConversationAction -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'context_injection.control'`

**Step 2: Write failing tests for compute_action**

Add test helper and test classes to `tests/test_control.py`:

```python
from context_injection.control import compute_action
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
        """Plateau + closing probe fired BUT unresolved items remain → continue."""
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
        """Full cycle: plateau → advance → re-plateau with probe already fired → CONCLUDE."""
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
        """Full cycle re-plateau with probe fired BUT unresolved items → CONTINUE."""
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
```

Run: `cd packages/context-injection && uv run pytest tests/test_control.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement ConversationAction and compute_action**

Create `context_injection/control.py`:

```python
"""Conversation control — action computation and ledger summary.

Pure functions on ledger types. No side effects, no I/O.
"""

from __future__ import annotations

from enum import StrEnum

from context_injection.enums import EffectiveDelta
from context_injection.ledger import LedgerEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_ENTRIES_FOR_PLATEAU: int = 2
"""Minimum consecutive STATIC entries to detect plateau."""


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class ConversationAction(StrEnum):
    """Agent action based on conversation trajectory."""

    CONTINUE_DIALOGUE = "continue_dialogue"
    CLOSING_PROBE = "closing_probe"
    CONCLUDE = "conclude"


# ---------------------------------------------------------------------------
# Action computation
# ---------------------------------------------------------------------------


def _is_plateau(entries: list[LedgerEntry]) -> bool:
    """Check if the last MIN_ENTRIES_FOR_PLATEAU entries are all STATIC."""
    if len(entries) < MIN_ENTRIES_FOR_PLATEAU:
        return False
    recent = entries[-MIN_ENTRIES_FOR_PLATEAU:]
    return all(e.effective_delta == EffectiveDelta.STATIC for e in recent)


def _has_open_unresolved(entries: list[LedgerEntry]) -> bool:
    """Check if the latest entry has unresolved items."""
    if not entries:
        return False
    return len(entries[-1].unresolved) > 0


def compute_action(
    entries: list[LedgerEntry],
    budget_remaining: int,
    closing_probe_fired: bool,
) -> tuple[ConversationAction, str]:
    """Determine next conversation action from ledger trajectory.

    Design decision — one-shot closing probe policy:
        A closing probe fires at most once per conversation. If the conversation
        advances after a closing probe (plateau broken by ADVANCING/SHIFTING),
        a second plateau will skip the probe and proceed directly to CONCLUDE.
        Rationale: repeated probes add latency without new information — if the
        first probe did not surface actionable material, a second will not either.

    Precedence (highest to lowest):
    1. Budget exhausted → CONCLUDE
    2. Plateau detected (last 2 STATIC):
       a. Closing probe already fired + no open unresolved → CONCLUDE
       b. Closing probe already fired + open unresolved → CONTINUE (address them)
       c. Closing probe not fired → CLOSING_PROBE
    3. No plateau → CONTINUE_DIALOGUE

    Args:
        entries: Validated ledger entries (chronological order).
        budget_remaining: Turn budget remaining (NOT evidence budget).
            0 or negative means budget is exhausted.
        closing_probe_fired: Whether a closing probe was already sent.

    Returns:
        Tuple of (action, human-readable reason string).
    """
    # 1. Budget exhaustion — hard stop
    if budget_remaining <= 0:
        return (
            ConversationAction.CONCLUDE,
            f"Budget exhausted ({budget_remaining} turns remaining)",
        )

    # 2. Need entries for plateau detection
    if not entries:
        return (
            ConversationAction.CONTINUE_DIALOGUE,
            "No entries yet — first turn",
        )

    # 3. Plateau detection
    plateau = _is_plateau(entries)

    if plateau:
        if closing_probe_fired:
            # Check for unresolved items — if present, continue to address them
            if _has_open_unresolved(entries):
                return (
                    ConversationAction.CONTINUE_DIALOGUE,
                    f"Plateau detected but {len(entries[-1].unresolved)} unresolved "
                    f"item(s) remain — continuing to address them",
                )
            return (
                ConversationAction.CONCLUDE,
                "Plateau detected — last 2 turns STATIC, closing probe "
                "already fired, no unresolved items",
            )
        return (
            ConversationAction.CLOSING_PROBE,
            "Plateau detected — last 2 turns STATIC, firing closing probe",
        )

    # 4. Default — continue
    last_delta = entries[-1].effective_delta
    return (
        ConversationAction.CONTINUE_DIALOGUE,
        f"Conversation active — last delta: {last_delta}",
    )
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_control.py -v`
Expected: PASS (all TestConversationAction + TestComputeAction* tests, ~22 tests)

**Step 5: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus new test_control.py tests.

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/control.py packages/context-injection/tests/test_control.py
git commit -m "feat(context-injection): add compute_action for conversation control (D3 Task 9)"
```

---

### Task 10: Ledger summary generation

**Files:**
- Modify: `context_injection/control.py`
- Modify: `tests/test_control.py`

`generate_ledger_summary` produces a compact text summary of the conversation ledger for injection into agent prompts. The format is designed for LLM consumption — each turn on one line with key metadata, followed by aggregate state and trajectory lines. Target: 300-400 tokens for an 8-turn conversation.

**Step 1: Write failing tests for generate_ledger_summary**

Add to `tests/test_control.py`:

```python
from context_injection.control import generate_ledger_summary
from context_injection.ledger import CumulativeState

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
                    new_claims=0, revised=0, conceded=0, unresolved_closed=0,
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
        trajectory_lines = [l for l in lines if "trajectory" in l.lower()]
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

        # Rough token estimate: 1 token ≈ 4 chars
        char_count = len(result)
        estimated_tokens = char_count / 4
        assert estimated_tokens < 600, (
            f"Summary too long: ~{estimated_tokens:.0f} tokens ({char_count} chars)"
        )
        assert estimated_tokens > 100, (
            f"Summary too short: ~{estimated_tokens:.0f} tokens ({char_count} chars)"
        )
```

Run: `cd packages/context-injection && uv run pytest tests/test_control.py::TestGenerateLedgerSummaryFormat -v`
Expected: FAIL — `ImportError: cannot import name 'generate_ledger_summary'`

**Step 2: Implement generate_ledger_summary**

Add to `context_injection/control.py` (after `compute_action`):

```python
from context_injection.ledger import CumulativeState, LedgerEntry

# (Update the existing import to include CumulativeState)

# ---------------------------------------------------------------------------
# Constants (add to existing constants section)
# ---------------------------------------------------------------------------

MAX_POSITION_LENGTH: int = 80
"""Maximum position string length in summary lines. Longer positions are truncated."""


# ---------------------------------------------------------------------------
# Ledger summary
# ---------------------------------------------------------------------------


def _truncate(text: str, max_length: int) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _format_turn_line(entry: LedgerEntry) -> str:
    """Format a single turn line for the ledger summary.

    Format: T{n}: {position} ({effective_delta}, {tags})
    """
    position = _truncate(entry.position, MAX_POSITION_LENGTH)
    tags_str = ", ".join(entry.tags) if entry.tags else "none"
    return f"T{entry.turn_number}: {position} ({entry.effective_delta}, {tags_str})"


def generate_ledger_summary(
    entries: list[LedgerEntry],
    cumulative: CumulativeState,
) -> str:
    """Generate a compact text summary of the conversation ledger.

    Designed for injection into agent prompts. Each turn gets one line,
    followed by aggregate state and trajectory.

    Precondition: ``entries`` and ``cumulative`` must come from the same
    conversation snapshot. Passing entries from one conversation with
    cumulative state from another produces silently wrong output.

    Format:
        T1: [position] (effective_delta, tags)
        T2: [position] (effective_delta, tags)
        ...
        State: N claims (R reinforced, V revised, C conceded), U unresolved open
        Trajectory: advancing → shifting → static

    Target: 300-400 tokens for 8 turns (~1200-1600 chars).

    Args:
        entries: Validated ledger entries (chronological order).
        cumulative: Pre-computed cumulative state from the same conversation.

    Returns:
        Multi-line summary string.
    """
    if not entries:
        return "Ledger: No turns completed.\nState: 0 claims, 0 unresolved open"

    lines: list[str] = []

    # Turn lines
    for entry in entries:
        lines.append(_format_turn_line(entry))

    # State line
    state_parts = [
        f"{cumulative.total_claims} claims",
        f"{cumulative.reinforced} reinforced",
        f"{cumulative.revised} revised",
        f"{cumulative.conceded} conceded",
    ]
    state_line = f"State: {', '.join(state_parts)}, {cumulative.unresolved_open} unresolved open"
    lines.append(state_line)

    # Trajectory line
    if cumulative.effective_delta_sequence:
        deltas = " → ".join(
            d.value for d in cumulative.effective_delta_sequence
        )
        lines.append(f"Trajectory: {deltas}")

    return "\n".join(lines)
```

**Step 3: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_control.py -v`
Expected: PASS (all TestConversationAction + TestComputeAction* + TestGenerateLedgerSummary* tests, ~35-40 tests)

**Step 4: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus all test_control.py tests.

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/control.py packages/context-injection/tests/test_control.py
git commit -m "feat(context-injection): add generate_ledger_summary for agent prompt injection (D3 Task 10)"
```

"""Conversation control — action computation and ledger summary.

Pure functions on ledger types. No side effects, no I/O.
"""

from __future__ import annotations

from collections.abc import Sequence
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


def _is_plateau(entries: Sequence[LedgerEntry]) -> bool:
    """Check if the last MIN_ENTRIES_FOR_PLATEAU entries are all STATIC."""
    if len(entries) < MIN_ENTRIES_FOR_PLATEAU:
        return False
    recent = entries[-MIN_ENTRIES_FOR_PLATEAU:]
    return all(e.effective_delta == EffectiveDelta.STATIC for e in recent)


def _has_open_unresolved(entries: Sequence[LedgerEntry]) -> bool:
    """Check if the latest entry has unresolved items."""
    if not entries:
        return False
    return len(entries[-1].unresolved) > 0


def compute_action(
    entries: Sequence[LedgerEntry],
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
    1. Budget exhausted -> CONCLUDE
    2. Plateau detected (last 2 STATIC):
       a. Closing probe already fired + no open unresolved -> CONCLUDE
       b. Closing probe already fired + open unresolved -> CONTINUE (address them)
       c. Closing probe not fired -> CLOSING_PROBE
    3. No plateau -> CONTINUE_DIALOGUE

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

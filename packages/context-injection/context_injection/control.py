"""Conversation control — action computation and ledger summary.

Pure functions on ledger types. No side effects, no I/O.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from context_injection.enums import EffectiveDelta
from context_injection.ledger import CumulativeState, LedgerEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_ENTRIES_FOR_PLATEAU: int = 2
"""Minimum consecutive STATIC entries to detect plateau."""

MAX_POSITION_LENGTH: int = 80
"""Maximum position string length in summary lines. Longer positions are truncated."""


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
    *,
    phase_entries: Sequence[LedgerEntry] | None = None,
) -> tuple[ConversationAction, str]:
    """Determine next conversation action from ledger trajectory.

    When phase_entries is provided (phase composition), plateau detection
    uses the phase-local window instead of the full entry history.
    When phase_entries is None (single-posture dialogue), behavior is
    identical to pre-Release-B.

    Design decision — closing probe policy (once per phase):
        A closing probe fires at most once per phase. When posture changes
        (phase boundary), closing_probe_fired resets — the new phase gets its
        own probe opportunity. Within a single phase, if the conversation
        advances after a closing probe (plateau broken by ADVANCING/SHIFTING),
        a second plateau skips the probe and proceeds directly to CONCLUDE.
        In single-posture conversations, this is equivalent to once per
        conversation.

    Precedence (highest to lowest):
    1. Budget exhausted -> CONCLUDE
    2. Plateau detected (last 2 STATIC in phase window):
       a. Closing probe already fired + no open unresolved -> CONCLUDE
       b. Closing probe already fired + open unresolved -> CONTINUE (address them)
       c. Closing probe not fired -> CLOSING_PROBE
    3. No plateau -> CONTINUE_DIALOGUE

    Args:
        entries: Validated ledger entries (chronological order). Full history.
        budget_remaining: Turn budget remaining (NOT evidence budget).
            0 or negative means budget is exhausted.
        closing_probe_fired: Whether a closing probe was already sent.
        phase_entries: Phase-local entries for plateau detection. When None,
            uses full ``entries`` (backward-compatible default).

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

    # 3. Plateau detection — use phase window if provided
    plateau_window = phase_entries if phase_entries is not None else entries
    plateau = _is_plateau(plateau_window)

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
    entries: Sequence[LedgerEntry],
    cumulative: CumulativeState,
) -> str:
    """Generate a compact text summary of the conversation ledger.

    Designed for injection into agent prompts. Each turn gets one line,
    followed by aggregate state and trajectory.

    Precondition: ``entries`` and ``cumulative`` must come from the same
    conversation snapshot. Passing entries from one conversation with
    cumulative state from another produces silently wrong output.

    Format::

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
    state_line = (
        f"State: {', '.join(state_parts)}, {cumulative.unresolved_open} unresolved open"
    )
    lines.append(state_line)

    # Trajectory line
    if cumulative.effective_delta_sequence:
        deltas = " → ".join(d.value for d in cumulative.effective_delta_sequence)
        lines.append(f"Trajectory: {deltas}")

    return "\n".join(lines)

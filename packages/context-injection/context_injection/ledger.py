"""Ledger validation types and computation.

Server-side validation of agent-provided ledger entries. Computes derived
fields (counters, quality, effective_delta) and validates structural and
referential constraints.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from context_injection.base_types import Claim, ProtocolModel, Unresolved
from context_injection.enums import EffectiveDelta, QualityLabel, ValidationTier


class LedgerEntryCounters(ProtocolModel):
    """Claim status counts for a single ledger entry."""

    new_claims: int = Field(ge=0)
    revised: int = Field(ge=0)
    conceded: int = Field(ge=0)
    unresolved_closed: int = Field(ge=0)


class LedgerEntry(ProtocolModel):
    """Validated ledger entry for a single conversation turn."""

    position: str
    claims: list[Claim]
    delta: str
    tags: list[str]
    unresolved: list[Unresolved]
    counters: LedgerEntryCounters
    quality: QualityLabel
    effective_delta: EffectiveDelta
    turn_number: int


class ValidationWarning(ProtocolModel):
    """Validation warning attached to a ledger entry."""

    tier: ValidationTier
    field: str
    message: str
    details: dict[str, Any] | None = None


class CumulativeState(ProtocolModel):
    """Aggregated state across all validated ledger entries."""

    total_claims: int = Field(ge=0)
    reinforced: int = Field(ge=0)
    revised: int = Field(ge=0)
    conceded: int = Field(ge=0)
    unresolved_open: int = Field(ge=0)
    unresolved_closed: int = Field(ge=0)
    turns_completed: int = Field(ge=0)
    effective_delta_sequence: list[EffectiveDelta]


# ---------------------------------------------------------------------------
# Computation functions
# ---------------------------------------------------------------------------


def compute_counters(
    claims: list[Claim], *, unresolved_closed: int = 0,
) -> LedgerEntryCounters:
    """Count claims by status. Reinforced claims are not counted.

    unresolved_closed is passed in by the caller — D1 has no access
    to prior state for comparing unresolved lists.

    Raises ValueError if unresolved_closed is negative.
    """
    if unresolved_closed < 0:
        msg = f"unresolved_closed must be >= 0, got {unresolved_closed}"
        raise ValueError(msg)
    return LedgerEntryCounters(
        new_claims=sum(1 for c in claims if c.status == "new"),
        revised=sum(1 for c in claims if c.status == "revised"),
        conceded=sum(1 for c in claims if c.status == "conceded"),
        unresolved_closed=unresolved_closed,
    )


def compute_quality(counters: LedgerEntryCounters) -> QualityLabel:
    """Any non-reinforced activity -> substantive."""
    if (
        counters.new_claims > 0
        or counters.revised > 0
        or counters.conceded > 0
        or counters.unresolved_closed > 0
    ):
        return QualityLabel.SUBSTANTIVE
    return QualityLabel.SHALLOW


def compute_effective_delta(counters: LedgerEntryCounters) -> EffectiveDelta:
    """Compute effective delta. Priority: advancing > shifting > static.

    Unresolved closure alone doesn't change position — it clarifies.
    """
    if counters.new_claims > 0:
        return EffectiveDelta.ADVANCING
    if counters.revised > 0 or counters.conceded > 0:
        return EffectiveDelta.SHIFTING
    return EffectiveDelta.STATIC


def _delta_disagrees(agent_delta: str, effective_delta: EffectiveDelta) -> bool:
    """Check if agent's self-reported delta contradicts computed effective_delta.

    Canonical 3-way semantic logic:
    - "static" contradicts non-STATIC (advancing or shifting)
    - "advancing" or "shifting" contradicts STATIC
    - Unknown agent delta values fall through (no disagreement)
    """
    agent_lower = agent_delta.lower()

    if agent_lower == "static" and effective_delta != EffectiveDelta.STATIC:
        return True
    if agent_lower in {"advancing", "shifting"} and effective_delta == EffectiveDelta.STATIC:
        return True
    return False

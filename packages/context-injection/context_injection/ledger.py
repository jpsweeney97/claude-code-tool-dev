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

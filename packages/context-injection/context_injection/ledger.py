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


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class LedgerValidationError(Exception):
    """Hard rejection of a ledger entry."""

    def __init__(self, warnings: list[ValidationWarning]) -> None:
        self.warnings = warnings
        super().__init__(f"{len(warnings)} hard validation error(s)")


def validate_ledger_entry(
    position: str,
    claims: list[Claim],
    delta: str,
    tags: list[str],
    unresolved: list[Unresolved],
    turn_number: int,
    *,
    unresolved_closed: int = 0,
    prior_claims: list[Claim] | None = None,
) -> tuple[LedgerEntry, list[ValidationWarning]]:
    """Build and validate a LedgerEntry.

    Raises LedgerValidationError for hard rejects (empty claims, bad turn_number,
    claim turn out of bounds). Returns (entry, soft_warnings) on success.

    prior_claims: if provided, enables referential validation (Task 4).
    """
    hard: list[ValidationWarning] = []
    soft: list[ValidationWarning] = []

    # --- Hard rejects ---
    if not claims:
        hard.append(ValidationWarning(
            tier=ValidationTier.HARD_REJECT,
            field="claims",
            message="Claims list is empty — each turn must have at least one claim",
        ))
    if turn_number < 1:
        hard.append(ValidationWarning(
            tier=ValidationTier.HARD_REJECT,
            field="turn_number",
            message=f"Turn number must be >= 1, got {turn_number}",
        ))

    # --- Structural chronology: claim.turn bounds ---
    for claim in claims:
        if claim.turn < 1:
            hard.append(ValidationWarning(
                tier=ValidationTier.HARD_REJECT,
                field="claims",
                message=f"Claim turn must be >= 1, got {claim.turn} for {claim.text!r:.80}",
            ))
        elif claim.turn > turn_number:
            hard.append(ValidationWarning(
                tier=ValidationTier.HARD_REJECT,
                field="claims",
                message=(
                    f"Claim turn {claim.turn} exceeds entry turn_number "
                    f"{turn_number} for {claim.text!r:.80}"
                ),
            ))

    if hard:
        raise LedgerValidationError(hard)

    # --- Compute derived fields ---
    counters = compute_counters(claims, unresolved_closed=unresolved_closed)
    quality = compute_quality(counters)
    effective_delta = compute_effective_delta(counters)

    # --- Soft warnings ---
    if not position:
        soft.append(ValidationWarning(
            tier=ValidationTier.SOFT_WARN,
            field="position",
            message="Position is empty — agent should summarize their current stance",
        ))

    if delta and _delta_disagrees(delta, effective_delta):
        soft.append(ValidationWarning(
            tier=ValidationTier.SOFT_WARN,
            field="delta",
            message=(
                f"Agent-reported delta {delta!r} disagrees with "
                f"computed effective_delta {effective_delta.value!r}"
            ),
            details={"agent_delta": delta, "effective_delta": effective_delta.value},
        ))

    # --- Referential warnings (Task 4 extension point) ---
    if prior_claims is not None:
        soft.extend(_referential_warnings(claims, prior_claims))

    entry = LedgerEntry(
        position=position,
        claims=claims,
        delta=delta,
        tags=tags,
        unresolved=unresolved,
        counters=counters,
        quality=quality,
        effective_delta=effective_delta,
        turn_number=turn_number,
    )
    return entry, soft


_REFERENTIAL_STATUSES: frozenset[str] = frozenset({"reinforced", "revised", "conceded"})
"""Claim statuses that imply a prior referent exists."""


def _referential_warnings(
    claims: list[Claim], prior_claims: list[Claim],
) -> list[ValidationWarning]:
    """Check that claims with referential statuses have matching prior claims.

    Uses exact text match (deterministic). Referential warnings are softer
    than soft warnings — the agent may have legitimately rephrased.
    """
    prior_texts = frozenset(c.text for c in prior_claims)
    warnings: list[ValidationWarning] = []

    for claim in claims:
        if claim.status not in _REFERENTIAL_STATUSES:
            continue
        if claim.text not in prior_texts:
            warnings.append(ValidationWarning(
                tier=ValidationTier.REFERENTIAL_WARN,
                field="claims",
                message=(
                    f"Claim marked {claim.status!r} but no prior claim with "
                    f"matching text found: {claim.text!r:.80}"
                ),
                details={"status": claim.status, "text": claim.text},
            ))

    return warnings

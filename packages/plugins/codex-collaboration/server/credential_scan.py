"""Tiered credential scanner for advisory tool calls.

Tiers:
  strict:      Hard-block. High-confidence patterns (AWS keys, PEM, JWT).
  contextual:  Block unless placeholder/example words appear nearby.
  broad:       Shadow (no blocking). Telemetry not yet wired.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .secret_taxonomy import (
    FAMILIES,
    PLACEHOLDER_BYPASS_WINDOW,
    SecretFamily,
    Tier,
    check_placeholder_bypass,
)


@dataclass(frozen=True)
class ScanResult:
    """Result of scanning text for credentials."""

    action: Literal["allow", "block", "shadow"]
    tier: Tier | None
    reason: str | None


def _families_for_tier(tier: Tier) -> tuple[SecretFamily, ...]:
    return tuple(
        family
        for family in FAMILIES
        if family.egress_enabled and family.tier == tier
    )


_STRICT_FAMILIES = _families_for_tier("strict")
_CONTEXTUAL_FAMILIES = _families_for_tier("contextual")
_BROAD_FAMILIES = _families_for_tier("broad")


def scan_text(text: str) -> ScanResult:
    """Scan text for credentials. Returns on first match.

    Priority: strict > contextual > broad > allow.
    """
    for family in _STRICT_FAMILIES:
        if family.pattern.search(text):
            return ScanResult(
                action="block",
                tier="strict",
                reason=f"strict:{family.name}",
            )

    for family in _CONTEXTUAL_FAMILIES:
        for match in family.pattern.finditer(text):
            start = max(0, match.start() - PLACEHOLDER_BYPASS_WINDOW)
            end = min(len(text), match.end() + PLACEHOLDER_BYPASS_WINDOW)
            if not check_placeholder_bypass(text[start:end], family):
                return ScanResult(
                    action="block",
                    tier="contextual",
                    reason=f"contextual:{family.name}",
                )

    for family in _BROAD_FAMILIES:
        if family.pattern.search(text):
            return ScanResult(
                action="shadow",
                tier="broad",
                reason=f"broad:{family.name}",
            )

    return ScanResult(action="allow", tier=None, reason=None)

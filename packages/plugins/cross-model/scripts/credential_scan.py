"""Shared credential scanning for cross-model plugin.

Extracts tiered credential detection from codex_guard.py into a public module.
Both the hook (codex_guard.py) and the delegation adapter (codex_delegate.py)
import from this module.

Tiers:
  strict:      Hard-block. High-confidence patterns (AWS keys, PEM, JWT).
  contextual:  Block unless placeholder/example words appear nearby.
  broad:       Shadow telemetry only. No blocking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

if __package__:
    from scripts.secret_taxonomy import (
        FAMILIES,
        PLACEHOLDER_BYPASS_WINDOW,
        check_placeholder_bypass,
    )
else:
    from secret_taxonomy import (  # type: ignore[import-not-found,no-redef]
        FAMILIES,
        PLACEHOLDER_BYPASS_WINDOW,
        check_placeholder_bypass,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScanResult:
    """Result of scanning text for credentials."""

    action: Literal["allow", "block", "shadow"]
    tier: str | None
    reason: str | None


def _families_for_tier(tier: str) -> tuple:
    return tuple(
        family
        for family in FAMILIES
        if family.egress_enabled and family.tier == tier
    )


# Precomputed tier buckets — FAMILIES is immutable (frozen dataclasses in a tuple).
_STRICT_FAMILIES: tuple = _families_for_tier("strict")
_CONTEXTUAL_FAMILIES: tuple = _families_for_tier("contextual")
_BROAD_FAMILIES: tuple = _families_for_tier("broad")


def scan_text(text: str) -> ScanResult:
    """Scan text for credentials. Returns on first match.

    Priority: strict > contextual > broad > allow.
    """
    # Strict tier
    for family in _STRICT_FAMILIES:
        if family.pattern.search(text):
            return ScanResult(
                action="block",
                tier="strict",
                reason=f"strict:{family.name}",
            )

    # Contextual tier
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

    # Broad tier
    for family in _BROAD_FAMILIES:
        if family.pattern.search(text):
            return ScanResult(
                action="shadow",
                tier="broad",
                reason=f"broad:{family.name}",
            )

    return ScanResult(action="allow", tier=None, reason=None)

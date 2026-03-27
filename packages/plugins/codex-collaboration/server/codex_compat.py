"""Codex App Server compatibility — executable source of truth for version pin and method surface.

This module owns the Codex CLI version pin, required/optional method sets,
and startup compatibility checks. The spec (delivery.md §Compatibility Policy)
describes the policy; this module enforces it.

Fixture regeneration: scripts/regenerate_schema.sh
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ──────────────────────────────────────────
# Version pin
# ──────────────────────────────────────────

TESTED_CODEX_VERSION = "0.117.0"
"""Version of codex-cli that the vendored schema was generated from."""

MINIMUM_CODEX_VERSION = "0.117.0"
"""Startup rejects codex-cli versions below this floor."""


# ──────────────────────────────────────────
# SemVer
# ──────────────────────────────────────────

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")


@dataclass(frozen=True, order=True)
class SemVer:
    """Semantic version with comparison support.

    Uses tuple ordering via @dataclass(order=True) on (major, minor, patch).
    Suffixes (e.g., -beta.1) are parsed but ignored for comparison.
    """

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_string: str) -> SemVer:
        """Parse 'X.Y.Z' or 'X.Y.Z-suffix' into SemVer.

        Raises ValueError if the string doesn't start with three dot-separated integers.
        """
        match = _SEMVER_RE.match(version_string)
        if not match:
            raise ValueError(
                f"Version parse failed: expected X.Y.Z format. Got: {version_string!r:.100}"
            )
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

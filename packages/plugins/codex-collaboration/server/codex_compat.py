"""Codex App Server compatibility — executable source of truth for version pin and method surface.

This module owns the Codex CLI version pin, required/optional method sets,
and startup compatibility checks. The spec (delivery.md §Compatibility Policy)
describes the policy; this module enforces it.

Fixture regeneration: scripts/regenerate_schema.sh
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


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


# ──────────────────────────────────────────
# Method surface
# ──────────────────────────────────────────

REQUIRED_METHODS: frozenset[str] = frozenset({
    "thread/start",
    "thread/resume",
    "thread/fork",
    "thread/read",
    "turn/start",
    "turn/interrupt",
})
"""Methods that must be present for the plugin to start. Missing = fail-closed."""

OPTIONAL_METHODS: frozenset[str] = frozenset({
    "turn/steer",
})
"""Methods checked at startup but not required. Missing = warn, record in status."""


# ──────────────────────────────────────────
# Schema extraction
# ──────────────────────────────────────────

def extract_client_methods(client_request_schema_path: Path) -> frozenset[str]:
    """Extract method names from a ClientRequest.json schema file.

    The schema is a JSON Schema with oneOf variants, each containing a method enum
    with exactly one value.
    """
    with open(client_request_schema_path) as f:
        schema = json.load(f)

    methods: set[str] = set()
    for variant in schema.get("oneOf", []):
        method_enum = variant.get("properties", {}).get("method", {}).get("enum", [])
        if method_enum:
            methods.add(method_enum[0])

    return frozenset(methods)


def check_method_surface(
    available_methods: frozenset[str],
) -> tuple[frozenset[str], frozenset[str]]:
    """Check required and optional methods against available methods.

    Returns (missing_required, missing_optional).
    """
    return (
        REQUIRED_METHODS - available_methods,
        OPTIONAL_METHODS - available_methods,
    )

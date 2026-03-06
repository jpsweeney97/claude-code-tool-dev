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

import re
from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# Pattern definitions (extracted from codex_guard.py)
# ---------------------------------------------------------------------------

_STRICT: list[re.Pattern[str]] = [
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(
        r"-----BEGIN\s+(?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
    ),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
]

_CONTEXTUAL: list[re.Pattern[str]] = [
    re.compile(r"\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9\-_]{20,}\b"),
    re.compile(r"\b(?:pk_live|pk_test)_[A-Za-z0-9]{24,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{40,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{20,}"),
    re.compile(r"://[^@\s]+:[^@\s]{6,}@"),
]

_PLACEHOLDER_WORDS: frozenset[str] = frozenset([
    "format", "example", "looks", "placeholder", "dummy",
    "sample", "suppose", "hypothetical", "redact", "redacted",
    "your-", "my-", "[redacted",
])

_BROAD: list[re.Pattern[str]] = [
    re.compile(
        r"(?i)\b(?:password|passwd|secret|api_key|apikey|access_token|"
        r"auth_token|private_key|client_secret)\s*[=:]\s*.{6,}"
    ),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScanResult:
    """Result of scanning text for credentials."""

    action: Literal["allow", "block", "shadow"]
    tier: str | None
    reason: str | None


def _has_placeholder_context(
    text: str, match_start: int, match_end: int, window: int = 100
) -> bool:
    """Return True if a placeholder/example word appears near the match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    context = text[start:end].lower()
    return any(word in context for word in _PLACEHOLDER_WORDS)


def scan_text(text: str) -> ScanResult:
    """Scan text for credentials. Returns on first match.

    Priority: strict > contextual > broad > allow.
    """
    # Strict tier
    for pat in _STRICT:
        if pat.search(text):
            return ScanResult(
                action="block",
                tier="strict",
                reason=f"strict:{pat.pattern[:60]}",
            )

    # Contextual tier
    for pat in _CONTEXTUAL:
        for m in pat.finditer(text):
            if not _has_placeholder_context(text, m.start(), m.end()):
                return ScanResult(
                    action="block",
                    tier="contextual",
                    reason=f"contextual:{pat.pattern[:60]}",
                )

    # Broad tier
    for pat in _BROAD:
        if pat.search(text):
            return ScanResult(
                action="shadow",
                tier="broad",
                reason=f"broad:{pat.pattern[:60]}",
            )

    return ScanResult(action="allow", tier=None, reason=None)

"""Redaction pipeline: types, PEM detector, generic token scanner.

D2a Task 7: output types + standalone functions.
D2a Task 8 adds: redact_text() orchestration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class SuppressionReason(StrEnum):
    """Why text was suppressed instead of redacted."""

    UNSUPPORTED_CONFIG_FORMAT = "unsupported_config_format"
    FORMAT_DESYNC = "format_desync"
    PEM_PRIVATE_KEY_DETECTED = "pem_private_key_detected"


@dataclass(frozen=True)
class RedactionStats:
    """Redaction counts from both pipeline stages."""

    format_redactions: int
    token_redactions: int


@dataclass(frozen=True)
class RedactedText:
    """Successfully redacted text with combined stats."""

    text: str
    stats: RedactionStats


@dataclass(frozen=True)
class SuppressedText:
    """Text suppressed entirely — no repo-derived content emitted.

    reason is a SuppressionReason enum value, not free-form.
    SuppressedText contains no user-repo text by type design.
    """

    reason: SuppressionReason


RedactOutcome = RedactedText | SuppressedText

_REDACTED = "[REDACTED:value]"


# --- PEM detection ---

_PEM_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+|ENCRYPTED\s+)?PRIVATE\s+KEY-----"
)


def contains_pem_private_key(text: str) -> bool:
    """Detect PEM private key markers. Short-circuits the redaction pipeline."""
    return bool(_PEM_PRIVATE_KEY_RE.search(text))


# --- Generic token scanner ---

# Order: most specific first to prevent double-matching after replacement.

_JWT_RE = re.compile(
    r"eyJ[A-Za-z0-9_-]{5,}\.eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]+"
)

_AUTH_HEADER_RE = re.compile(
    r"(?i)((?:bearer|basic)\s+)[A-Za-z0-9\-._~+/]+=*"
)

_API_KEY_PREFIX_RE = re.compile(
    r"(?:sk-|pk_live_|pk_test_|ghp_|gho_|ghs_|ghr_|glpat-|xoxb-|xoxp-|xoxs-|AKIA)"
    r"[A-Za-z0-9_\-]{10,}"
)

_URL_USERINFO_RE = re.compile(
    r"(://[^@/\s:]+:)([^@/\s]+)(@)"
)

_CREDENTIAL_RE = re.compile(
    r"(?i)\b((?:password|passwd|secret|api_key|apikey|access_token|auth_token|"
    r"private_key|credential|api_secret|client_secret|"
    r"secret_key|encryption_key|signing_key)"
    r"\s*[=:]\s*)"
    r"[\"']?([^\s\"']{6,})[\"']?"
)


def redact_known_secrets(text: str) -> tuple[str, int]:
    """Generic token redaction — second stage of the two-stage pipeline.

    Detects: JWT, Bearer/Basic auth, API key prefixes, URL userinfo,
    credential assignments (RHS >= 6 chars).

    Returns (redacted_text, redaction_count).
    """
    if not text:
        return text, 0

    count = 0

    def _replace_simple(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return _REDACTED

    def _replace_auth(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return m.group(1) + _REDACTED

    def _replace_url(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return m.group(1) + _REDACTED + m.group(3)

    def _replace_credential(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return m.group(1) + _REDACTED

    # Apply in order: most specific first
    text = _JWT_RE.sub(_replace_simple, text)
    text = _AUTH_HEADER_RE.sub(_replace_auth, text)
    text = _API_KEY_PREFIX_RE.sub(_replace_simple, text)
    text = _URL_USERINFO_RE.sub(_replace_url, text)
    text = _CREDENTIAL_RE.sub(_replace_credential, text)

    return text, count

"""Shared secret pattern taxonomy for egress scanning and redaction.

Ported from cross-model/scripts/secret_taxonomy.py. Semantic source only —
the codex-collaboration package owns this copy.

Tiers:
  strict:      Hard-block. High-confidence patterns (AWS keys, PEM, JWT, Basic Auth).
  contextual:  Block unless placeholder/example words appear nearby.
  broad:       Shadow (no blocking). Telemetry not yet wired.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Tier = Literal["strict", "contextual", "broad"]
PLACEHOLDER_BYPASS_WINDOW = 100

PLACEHOLDER_BYPASS_WORDS = [
    "format",
    "example",
    "looks",
    "placeholder",
    "dummy",
    "sample",
    "suppose",
    "hypothetical",
    "redact",
    "redacted",
    "your-",
    "my-",
    "[redacted",
]
_PEM_KEY_LABEL = r"(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+|ENCRYPTED\s+)?PRIVATE\s+KEY"


@dataclass(frozen=True)
class SecretFamily:
    """Pattern family with independent egress and redaction controls."""

    name: str
    pattern: re.Pattern[str]
    tier: Tier
    placeholder_bypass: tuple[str, ...]
    redact_template: str
    redact_enabled: bool
    egress_enabled: bool
    redact_pattern: re.Pattern[str] | None = None


def check_placeholder_bypass(text: str, family: SecretFamily) -> bool:
    """Return True when placeholder/example language appears near a match.

    If ``text`` contains one or more family matches, each match is evaluated
    against a 100-character window.
    """
    if not family.placeholder_bypass:
        return False

    bypass_words = tuple(word.lower() for word in family.placeholder_bypass)
    matches = list(family.pattern.finditer(text))
    if not matches:
        return False

    for match in matches:
        start = max(0, match.start() - PLACEHOLDER_BYPASS_WINDOW)
        end = min(len(text), match.end() + PLACEHOLDER_BYPASS_WINDOW)
        context = text[start:end].lower()
        if any(word in context for word in bypass_words):
            return True
    return False


FAMILIES: tuple[SecretFamily, ...] = (
    SecretFamily(
        name="aws_access_key_id",
        pattern=re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        tier="strict",
        placeholder_bypass=(),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="pem_private_key",
        pattern=re.compile(rf"-----BEGIN\s+{_PEM_KEY_LABEL}-----"),
        tier="strict",
        placeholder_bypass=(),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
        redact_pattern=re.compile(
            rf"-----BEGIN\s+(?P<pem_label>{_PEM_KEY_LABEL})-----"
            rf"(?:[\s\S]*?-----END\s+(?P=pem_label)-----|[\s\S]*\Z)"
        ),
    ),
    SecretFamily(
        name="jwt_token",
        pattern=re.compile(
            r"\beyJ[A-Za-z0-9_-]{5,}\.eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b"
        ),
        tier="strict",
        placeholder_bypass=(),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="basic_auth_header",
        pattern=re.compile(
            r"(?i)(authorization\s*:\s*basic\s+)([A-Za-z0-9+/=]{8,})"
        ),
        tier="strict",
        placeholder_bypass=(),
        redact_template=r"\1[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="github_pat",
        pattern=re.compile(r"\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="gitlab_pat",
        pattern=re.compile(r"\bglpat-[A-Za-z0-9\-_]{20,}\b"),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="stripe_publishable_key",
        pattern=re.compile(r"\b(?:pk_live|pk_test)_[A-Za-z0-9]{24,}\b"),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="openai_api_key",
        pattern=re.compile(r"\bsk-[A-Za-z0-9]{40,}\b"),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="bearer_auth_header",
        pattern=re.compile(
            r"(?i)((?:authorization\s*:\s*)?bearer\s+)([A-Za-z0-9\-._~+/]{20,}=*)"
        ),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template=r"\1[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="url_userinfo",
        pattern=re.compile(r"(://[^@/\s:]+:)([^@/\s]{6,})(@)"),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template=r"\1[REDACTED:value]\3",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="slack_bot_token",
        pattern=re.compile(r"\bxoxb-[A-Za-z0-9-]{10,}\b"),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="slack_user_token",
        pattern=re.compile(r"\bxoxp-[A-Za-z0-9-]{10,}\b"),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="slack_session_token",
        pattern=re.compile(r"\bxoxs-[A-Za-z0-9-]{10,}\b"),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="credential_assignment_strong",
        pattern=re.compile(
            r"(?im)^[\t ]*(?:export\s+)?"
            r"((?:api_key|apikey|api_secret|client_secret|"
            r"private_key|secret_key|encryption_key|signing_key|"
            r"access_token|auth_token)[^\S\n]*[=:][^\S\n]*)"
            r"[\"']?([^\s\"']{6,})[\"']?"
        ),
        tier="contextual",
        placeholder_bypass=tuple(PLACEHOLDER_BYPASS_WORDS),
        redact_template=r"\1[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="credential_assignment",
        pattern=re.compile(
            r"(?i)((?:password|passwd|secret|credential)\s*[=:]\s*)"
            r"[\"']?([^\s\"']{6,})[\"']?"
        ),
        tier="broad",
        placeholder_bypass=(),
        redact_template=r"\1[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
)

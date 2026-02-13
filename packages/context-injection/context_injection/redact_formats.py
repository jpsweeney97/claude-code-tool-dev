"""Per-format config redactors.

Each redactor returns FormatRedactOutcome:
- FormatRedactResult: successfully redacted text + count
- FormatSuppressed: scanner desync or unparseable input

All redactors replace config values with [REDACTED:value] markers.
One marker = one redaction in the count.

D1 delivers: redact_env, redact_ini
D3 delivers: redact_json, redact_yaml, redact_toml
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FormatRedactResult:
    """Successfully redacted text with count."""

    text: str
    redactions_applied: int


@dataclass(frozen=True)
class FormatSuppressed:
    """Scanner desync or unparseable input.

    reason is debug-only (e.g., "json_scanner_desync").
    Orchestration layer (redact_text) maps ALL FormatSuppressed
    to SuppressedText(reason=FORMAT_DESYNC).
    """

    reason: str


FormatRedactOutcome = FormatRedactResult | FormatSuppressed

_REDACTED_VALUE = "[REDACTED:value]"


# --- Shared helpers ---


def _has_line_continuation(line: str) -> bool:
    """Check if line ends with unescaped backslash (odd trailing count)."""
    stripped = line.rstrip()
    if not stripped.endswith("\\"):
        return False
    count = len(stripped) - len(stripped.rstrip("\\"))
    return count % 2 == 1


# --- Env redactor ---


_EXPORT_RE = re.compile(r"^export\s+")


def redact_env(text: str) -> FormatRedactOutcome:
    """Redact values in .env format.

    Handles: KEY=VALUE, export KEY=VALUE, KEY="quoted", KEY='quoted',
    backslash continuation, # comments. Empty values are redacted
    (defense in depth).
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    lines = text.splitlines()
    result: list[str] = []
    redactions = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty or comment
        if not stripped or stripped.startswith("#"):
            result.append(line)
            i += 1
            continue

        # Strip optional export prefix
        has_export = bool(_EXPORT_RE.match(stripped))
        content = _EXPORT_RE.sub("", stripped) if has_export else stripped

        # Key=value pair
        if "=" in content:
            key, _, _ = content.partition("=")
            prefix = "export " if has_export else ""
            result.append(f"{prefix}{key}={_REDACTED_VALUE}")
            redactions += 1

            # Skip continuation lines (value ends with unescaped \)
            while _has_line_continuation(lines[i]) and i + 1 < len(lines):
                i += 1
        else:
            # Not a key=value line (e.g., bare 'export KEY')
            result.append(line)

        i += 1

    redacted = "\n".join(result)
    if text.endswith("\n"):
        redacted += "\n"

    return FormatRedactResult(text=redacted, redactions_applied=redactions)

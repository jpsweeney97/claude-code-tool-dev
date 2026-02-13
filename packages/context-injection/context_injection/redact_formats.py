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


# --- INI redactor ---


def redact_ini(text: str, *, properties_mode: bool = False) -> FormatRedactOutcome:
    """Redact values in INI/.properties format.

    Handles: key=value, key:value, key = value, [section] headers,
    comments (; and # for INI, # and ! for .properties).

    Properties mode: backslash continuation (strict: line must end with
    unescaped backslash). Excerpt-start-mid-continuation is an accepted
    limitation mitigated by generic token pass (D2a).
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

        # Empty line
        if not stripped:
            result.append(line)
            i += 1
            continue

        # Comment detection
        if _is_ini_comment(stripped, properties_mode=properties_mode):
            result.append(line)
            i += 1
            continue

        # Section header [section]
        if stripped.startswith("[") and stripped.endswith("]"):
            result.append(line)
            i += 1
            continue

        # Key-value pair
        kv = _split_ini_kv(stripped)
        if kv is not None:
            prefix, _ = kv
            result.append(f"{prefix}{_REDACTED_VALUE}")
            redactions += 1

            # Properties mode: skip continuation lines
            if properties_mode:
                while _has_line_continuation(lines[i]) and i + 1 < len(lines):
                    i += 1
        else:
            # No separator found — preserve line as-is
            result.append(line)

        i += 1

    redacted = "\n".join(result)
    if text.endswith("\n"):
        redacted += "\n"

    return FormatRedactResult(text=redacted, redactions_applied=redactions)


def _is_ini_comment(stripped: str, *, properties_mode: bool) -> bool:
    """Check if a stripped line is a comment."""
    if stripped.startswith("#") or stripped.startswith(";"):
        return True
    if properties_mode and stripped.startswith("!"):
        return True
    return False


def _split_ini_kv(line: str) -> tuple[str, str] | None:
    """Split INI key-value line into (prefix, value).

    prefix includes key, separator, and all original whitespace:
    'key = value' -> ('key = ', 'value')
    'key:value' -> ('key:', 'value')
    'key =  value' -> ('key =  ', 'value')

    Uses first separator found (min position of = and :).
    """
    eq_idx = line.find("=")
    colon_idx = line.find(":")

    if eq_idx < 0 and colon_idx < 0:
        return None

    if eq_idx < 0:
        idx = colon_idx
    elif colon_idx < 0:
        idx = eq_idx
    else:
        idx = min(eq_idx, colon_idx)

    prefix = line[: idx + 1]
    rest = line[idx + 1 :]
    # Preserve all whitespace between separator and value start
    stripped_rest = rest.lstrip()
    whitespace = rest[: len(rest) - len(stripped_rest)]
    prefix += whitespace

    return prefix, stripped_rest

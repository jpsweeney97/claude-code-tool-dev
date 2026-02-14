"""Per-format config redactors.

Each redactor returns FormatRedactOutcome:
- FormatRedactResult: successfully redacted text + count
- FormatSuppressed: scanner desync or unparseable input

All redactors replace config values with [REDACTED:value] markers.
One marker = one redaction in the count. Comment bodies are replaced
with [REDACTED:comment] markers (not counted in ``redactions_applied``).

``redactions_applied == 0`` does NOT imply the text is safe to emit
without further processing. Generic token redaction must still run
unconditionally on all emitted text regardless of this count.

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

    Callers must NOT emit the original text when suppressed. Suppressed
    means no repo-derived text should be returned; callers must still
    apply generic token redaction to any strings they do emit.
    """

    reason: str


FormatRedactOutcome = FormatRedactResult | FormatSuppressed

_REDACTED_VALUE = "[REDACTED:value]"
_REDACTED_COMMENT = "[REDACTED:comment]"


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

        # Empty line
        if not stripped:
            result.append(line)
            i += 1
            continue

        # Comment — redact body, preserve marker and indentation
        if stripped.startswith("#"):
            indent_ws = line[: len(line) - len(line.lstrip())]
            result.append(f"{indent_ws}# {_REDACTED_COMMENT}")
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

        # Comment — redact body, preserve marker char and indentation
        if _is_ini_comment(stripped, properties_mode=properties_mode):
            indent_ws = line[: len(line) - len(line.lstrip())]
            marker = stripped[0]
            result.append(f"{indent_ws}{marker} {_REDACTED_COMMENT}")
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


# --- JSON/JSONC redactor ---


def redact_json(text: str) -> FormatRedactOutcome:
    """Redact values in JSON/JSONC format.

    Streaming token scanner: preserves object keys, redacts all value tokens
    (strings, numbers, booleans, null). Handles JSONC extensions (// line
    comments, /* block comments). Tolerates partial documents at both
    boundaries (excerpt windows).

    Key detection: after reading a string, skip whitespace and check if next
    char is ``:``. If yes -> key (preserve). If no -> value (redact).

    On unrecoverable scanner state: FormatSuppressed(reason="json_scanner_desync").
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    out: list[str] = []
    redactions = 0
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Whitespace — preserve
        if ch in " \t\n\r":
            out.append(ch)
            i += 1
            continue

        # JSONC line comment: //
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            j = i + 2
            while j < n and text[j] != "\n":
                j += 1
            out.append(f"// {_REDACTED_COMMENT}")
            i = j
            continue

        # JSONC block comment: /* ... */
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = i + 2
            while j < n and not (text[j] == "*" and j + 1 < n and text[j + 1] == "/"):
                j += 1
            if j < n:
                j += 2  # consume */
                out.append(f"/* {_REDACTED_COMMENT} */")
            else:
                j = n  # unterminated — partial doc tolerance
                out.append(f"/* {_REDACTED_COMMENT}")
            i = j
            continue

        # String literal
        if ch == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == "\\":
                    j += 2  # skip escape sequence
                else:
                    j += 1
            if j < n:
                j += 1  # consume closing quote
            # j now past string (or at EOF if unterminated)
            string_text = text[i:j]

            # Lookahead: is next non-whitespace a colon? -> key
            k = j
            while k < n and text[k] in " \t\n\r":
                k += 1

            if k < n and text[k] == ":":
                out.append(string_text)  # Preserve key
            else:
                out.append(_REDACTED_VALUE)
                redactions += 1

            i = j
            continue

        # Structural characters
        if ch in "{}[],:":
            out.append(ch)
            i += 1
            continue

        # Number literal (optional -, digits, optional .digits, optional eE[+-]digits)
        if ch == "-" or ch.isdigit():
            j = i
            if text[j] == "-":
                j += 1
                if j >= n or not text[j].isdigit():
                    return FormatSuppressed(reason="json_scanner_desync")
            while j < n and text[j].isdigit():
                j += 1
            if j < n and text[j] == ".":
                j += 1
                while j < n and text[j].isdigit():
                    j += 1
            if j < n and text[j] in "eE":
                j += 1
                if j < n and text[j] in "+-":
                    j += 1
                while j < n and text[j].isdigit():
                    j += 1
            out.append(_REDACTED_VALUE)
            redactions += 1
            i = j
            continue

        # Keyword (true, false, null)
        if ch in "tfn":
            matched_kw = False
            for kw in ("true", "false", "null"):
                if text[i : i + len(kw)] == kw:
                    out.append(_REDACTED_VALUE)
                    redactions += 1
                    i += len(kw)
                    matched_kw = True
                    break
            if matched_kw:
                continue
            # Partial keyword at EOF — tolerate
            j = i
            while j < n and text[j].isalpha():
                j += 1
            if j == n:
                out.append(_REDACTED_VALUE)
                redactions += 1
                i = j
                continue
            return FormatSuppressed(reason="json_scanner_desync")

        # Unrecognized character — desync
        return FormatSuppressed(reason="json_scanner_desync")

    return FormatRedactResult(text="".join(out), redactions_applied=redactions)


# --- YAML redactor ---


_YAML_KEY_RE = re.compile(
    r"^(\s*(?:-\s+)?)"  # Group 1: indent + optional sequence indicator
    r"([A-Za-z0-9_.-]+)"  # Group 2: unquoted key
    r"(\s*:(?:\s|$))"  # Group 3: colon + (space or EOL)
)

_BLOCK_SCALAR_RE = re.compile(r"^[|>][+-]?[0-9]?$")


def redact_yaml(text: str) -> FormatRedactOutcome:
    """Redact values in YAML format.

    Line-oriented processor with block-scalar tracking and flow-collection
    depth counting. Uses ``find_mapping_colon()`` (regex) for key detection
    with strict key charset ``[A-Za-z0-9_.-]+``.

    State check ordering (load-bearing): block-scalar → flow → mapping → sequence.
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    lines = text.splitlines()
    result: list[str] = []
    redactions = 0

    in_block_scalar = False
    block_scalar_indent = -1
    block_content_emitted = False

    flow_depth = 0

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip()) if stripped else 0

        # --- State 1: Block scalar ---
        if in_block_scalar:
            if stripped and indent <= block_scalar_indent:
                # Dedent on non-empty line: exit block scalar
                in_block_scalar = False
                block_content_emitted = False
                # Fall through to process this line normally
            else:
                # Content line or empty line within block scalar
                if not block_content_emitted and stripped:
                    result.append(f"{' ' * indent}{_REDACTED_VALUE}")
                    redactions += 1
                    block_content_emitted = True
                elif not stripped:
                    pass  # consume empty line
                # else: subsequent content line, skip
                continue

        # --- State 2: Flow collection ---
        if flow_depth > 0:
            depth_change = _yaml_bracket_depth(stripped)
            flow_depth += depth_change
            if flow_depth <= 0:
                flow_depth = 0
            continue

        # --- Comment ---
        if stripped.startswith("#"):
            indent_ws = line[: len(line) - len(line.lstrip())]
            result.append(f"{indent_ws}# {_REDACTED_COMMENT}")
            continue

        # --- Document markers ---
        if stripped in ("---", "..."):
            result.append(line)
            continue

        # --- Mapping detection ---
        m = _YAML_KEY_RE.match(line)
        if m:
            key_end = m.end()
            key_prefix = line[:key_end]
            value_part = line[key_end:]
            value_stripped = value_part.strip()

            # Block scalar indicator?
            if value_stripped and _BLOCK_SCALAR_RE.match(value_stripped):
                in_block_scalar = True
                block_scalar_indent = indent
                block_content_emitted = False
                result.append(line)
                continue

            # Flow collection start?
            if value_stripped and value_stripped[0] in "{[":
                depth = _yaml_bracket_depth(value_stripped)
                if depth > 0:
                    flow_depth = depth
                result.append(f"{key_prefix}{_REDACTED_VALUE}")
                redactions += 1
                continue

            # Anchor?
            if value_stripped.startswith("&"):
                parts = value_stripped.split(None, 1)
                anchor = parts[0]
                if len(parts) > 1:
                    result.append(f"{key_prefix}{anchor} {_REDACTED_VALUE}")
                    redactions += 1
                else:
                    result.append(line)  # Anchor with no inline value
                continue

            # Alias?
            if value_stripped.startswith("*"):
                result.append(line)
                continue

            # Regular value
            if value_stripped:
                result.append(f"{key_prefix}{_REDACTED_VALUE}")
                redactions += 1
            else:
                result.append(line)  # Key with no value (sub-keys below)
            continue

        # --- Sequence item ---
        seq_match = re.match(r"^(\s*-\s+)(.*)", line)
        if seq_match:
            prefix, value = seq_match.groups()
            value_stripped = value.strip()
            if value_stripped:
                if value_stripped.startswith("*"):
                    result.append(line)  # Alias in sequence
                elif value_stripped[0] in "{[":
                    depth = _yaml_bracket_depth(value_stripped)
                    if depth > 0:
                        flow_depth = depth
                    result.append(f"{prefix}{_REDACTED_VALUE}")
                    redactions += 1
                else:
                    result.append(f"{prefix}{_REDACTED_VALUE}")
                    redactions += 1
            else:
                result.append(line)  # Bare sequence marker
            continue

        # --- Unrecognized line ---
        result.append(line)

    redacted = "\n".join(result)
    if text.endswith("\n"):
        redacted += "\n"

    return FormatRedactResult(text=redacted, redactions_applied=redactions)


def _yaml_bracket_depth(text: str) -> int:
    """Count net bracket depth change, respecting quotes and comments.

    5 lexical guard states: in_single_quote, in_double_quote, double_escape,
    in_line_comment (# to EOL), in_block_scalar (outer state, not tracked here).
    """
    depth = 0
    in_single = False
    in_double = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_single:
            if ch == "'":
                in_single = False
        elif in_double:
            if ch == "\\":
                i += 1  # skip escaped char (double_escape guard)
            elif ch == '"':
                in_double = False
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            break  # in_line_comment guard: # is comment only after whitespace/BOL
        elif ch == "'":
            in_single = True
        elif ch == '"':
            in_double = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        i += 1
    return depth


# --- TOML redactor ---


_TOML_TABLE_RE = re.compile(r"^\s*\[")


def redact_toml(text: str) -> FormatRedactOutcome:
    """Redact values in TOML format.

    Line-oriented ``key = value`` matching with multi-line string awareness.
    Tracks triple-quote delimiters (``\"\"\"``, ``'''``) across lines.
    Table headers and comments preserved. Orphaned closing triple-quote
    without opener treated as excerpt boundary artifact (skip and continue
    processing) — not desync. Prior lines already processed by earlier
    pattern branches; subsequent lines processed normally.

    EOF inside multi-line string is normal (excerpt window tolerance).
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    lines = text.splitlines()
    result: list[str] = []
    redactions = 0

    in_multiline: str | None = None  # '"""' or "'''" when active

    for line in lines:
        stripped = line.strip()

        # Multi-line string continuation
        if in_multiline is not None:
            if in_multiline in stripped:
                in_multiline = None
            continue

        # Empty line
        if not stripped:
            result.append(line)
            continue

        # Comment — redact body, preserve marker and indentation
        if stripped.startswith("#"):
            indent_ws = line[: len(line) - len(line.lstrip())]
            result.append(f"{indent_ws}# {_REDACTED_COMMENT}")
            continue

        # Table header ([table] or [[array]])
        if _TOML_TABLE_RE.match(line):
            result.append(line)
            continue

        # Key-value pair: first = is the separator
        eq_idx = stripped.find("=")
        if eq_idx > 0:
            key_part_stripped = stripped[:eq_idx]
            if key_part_stripped.rstrip():  # non-empty key
                # Map back to original line indentation
                orig_indent = len(line) - len(line.lstrip())
                abs_eq_idx = orig_indent + eq_idx

                key_part = line[: abs_eq_idx + 1]  # includes =
                value_part = line[abs_eq_idx + 1 :]
                value_stripped = value_part.strip()

                # Check for multi-line string opening
                for delim in ('"""', "'''"):
                    if delim in value_stripped:
                        after_open = value_stripped[value_stripped.index(delim) + 3 :]
                        if delim not in after_open:
                            in_multiline = delim
                        break

                # Preserve whitespace between = and value
                ws = value_part[: len(value_part) - len(value_part.lstrip())]
                result.append(f"{key_part}{ws}{_REDACTED_VALUE}")
                redactions += 1
                continue

        # Orphaned closing triple-quote (mid-excerpt boundary artifact)
        # Excerpt started inside a multi-line string. Prior lines were
        # already processed (some redacted, some preserved for backstop).
        # Skip the closing delimiter and continue processing normally.
        orphaned = False
        for delim in ('"""', "'''"):
            if delim in stripped:
                orphaned = True
                break
        if orphaned:
            continue

        # Unrecognized line — preserve (lenient for partial docs)
        result.append(line)

    redacted = "\n".join(result)
    if text.endswith("\n"):
        redacted += "\n"

    return FormatRedactResult(text=redacted, redactions_applied=redactions)

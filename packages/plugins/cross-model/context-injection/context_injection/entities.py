"""Regex-based entity extraction from claim/unresolved text.

Implements an ordered extractor pipeline with 4 MVP categories:
1. Paths — file_loc > file_path > file_name (disambiguation by pattern)
2. URLs — mapped to file_path
3. Dotted symbols — mapped to symbol
4. Structured errors — error class name mapped to symbol

Key behaviors:
- Span tracking prevents overlapping extractions
- Backticked entities get "high" confidence; strong unquoted patterns get "medium"
- canon() normalizes per entity type (strip line suffixes, ./ prefixes, trailing parens)
- Entity IDs from AppContext.next_entity_id()
"""

from __future__ import annotations

import re
from typing import Literal

from context_injection.state import AppContext
from context_injection.types import Entity

# --- Known file extensions (MVP scope) ---

MAX_TEXT_LEN: int = 2000
"""Input text length cap. Bounds worst-case regex execution to under 5ms."""

KNOWN_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".md",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".rs",
        ".go",
        ".java",
        ".rb",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".css",
        ".scss",
        ".html",
        ".xml",
        ".sql",
        ".sh",
        ".bash",
        ".cfg",
        ".ini",
        ".conf",
        ".lock",
        ".txt",
        ".csv",
    }
)
"""File extensions that signal a file reference (not an arbitrary dotted name)."""


# --- Extraction result (internal, before Entity construction) ---

TIER_MAP: dict[str, int] = {
    "file_loc": 1,
    "file_path": 1,
    "file_name": 1,
    "symbol": 1,
    "dir_path": 1,
    "env_var": 1,
    "config_key": 1,
    "cli_flag": 1,
    "command": 1,
    "package_name": 1,
    "file_hint": 2,
    "symbol_hint": 2,
    "config_hint": 2,
}


class _RawMatch:
    """Internal extraction result before Entity construction."""

    __slots__ = ("entity_type", "raw", "start", "end", "backticked")

    def __init__(
        self,
        entity_type: str,
        raw: str,
        start: int,
        end: int,
        backticked: bool,
    ) -> None:
        self.entity_type = entity_type
        self.raw = raw
        self.start = start
        self.end = end
        self.backticked = backticked


# --- Regex patterns ---

# URL: HTTP/HTTPS only. FTP, SSH, and other schemes are intentionally excluded —
# they aren't local file references and would need scheme-specific path handling.
_URL_RE = re.compile(
    r"https?://[^\s`\"\')>\]]+",
)

# File location: path with :line or :line:col or #Lline suffix
# Must have a file extension before the anchor
_FILE_LOC_COLON_RE = re.compile(
    r"(?:\.?\.?/)?(?:[\w./-]+/)?[\w.-]+\.\w+:\d+(?::\d+)?",
)
_FILE_LOC_ANCHOR_RE = re.compile(
    r"(?:\.?\.?/)?(?:[\w./-]+/)?[\w.-]+\.\w+#L\d+",
)

# File path: contains / (e.g., src/api/auth.py, ./config.yaml, packages/)
# Two alternatives:
# 1. ./ or ../ prefix followed by any path content (including bare filename)
# 2. word chars with at least one / separator
_FILE_PATH_RE = re.compile(
    r"\.{1,2}/[\w][\w./-]*|[\w][\w.-]*/[\w./-]*",
)

# File name: no separator, has known extension (word chars + dot + extension)
_FILE_NAME_RE = re.compile(
    r"[\w][\w.-]*\.(?:"
    + "|".join(ext.lstrip(".") for ext in sorted(KNOWN_EXTENSIONS))
    + r")\b",
)

# Dotted symbol: word.word.word (2+ dots minimum)
_DOTTED_SYMBOL_RE = re.compile(
    r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*){2,}(?:\(\))?",
)

# Structured error: *Error: pattern (extract the error class name)
_ERROR_RE = re.compile(
    r"[A-Z][A-Za-z]*Error(?=:)",
)


# --- Canonicalization ---


def _canon(entity_type: str, raw: str) -> str:
    """Normalize raw text per entity type.

    Rules:
    - file_loc: strip :line, :line:col, #Lline suffix -> path part only
    - file_path: strip ./ prefix, normalize separators
    - file_name: keep as-is
    - symbol: strip trailing ()
    - URL (file_path starting with http): keep as-is
    """
    if entity_type == "file_loc":
        # Strip #L anchor
        idx = raw.find("#L")
        if idx != -1:
            return raw[:idx]
        # Strip :line:col or :line suffix
        # Walk from the end to find the last colon-number segment
        result = raw
        # Strip :col if present (last :digits)
        m = re.match(r"^(.+):(\d+):(\d+)$", result)
        if m:
            return m.group(1)
        m = re.match(r"^(.+):(\d+)$", result)
        if m:
            return m.group(1)
        return result

    if entity_type == "file_path":
        # URLs: keep as-is
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
        # Strip ./ prefix
        if raw.startswith("./"):
            return raw[2:]
        return raw

    if entity_type == "file_name":
        return raw

    if entity_type == "symbol":
        # Strip trailing ()
        if raw.endswith("()"):
            return raw[:-2]
        return raw

    return raw


# --- Confidence assignment ---


def _confidence(
    backticked: bool, entity_type: str, raw: str
) -> Literal["high", "medium", "low"]:
    """Assign confidence level.

    - Backticked -> high
    - Strong pattern (path separator, known extension, URL, error pattern) -> medium
    - Otherwise -> low
    """
    if backticked:
        return "high"

    # Strong patterns: URL, path with /, known extension, error class
    if raw.startswith("http://") or raw.startswith("https://"):
        return "medium"
    if "/" in raw:
        return "medium"
    if entity_type in ("file_name", "file_loc"):
        return "medium"
    if entity_type == "symbol":
        # Error classes and dotted symbols are strong patterns
        return "medium"

    return "low"


# --- Span tracking ---


def _overlaps(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    """Check if (start, end) overlaps with any existing span.

    O(n) scan per call, O(n**2) total for n entities. Acceptable for MVP —
    MAX_TEXT_LEN=2000 bounds entity count to ~20 in practice.
    """
    for s, e in spans:
        if start < e and end > s:
            return True
    return False


# --- Backtick detection ---


def _find_backtick_spans(text: str) -> list[tuple[int, int, str]]:
    """Find all backtick-delimited spans in text.

    Supports both single (`) and double (``) backtick delimiters.
    Returns list of (content_start, content_end, content) tuples.
    content_start/end are indices into the original text of the content
    (not including the backticks themselves).
    """
    spans: list[tuple[int, int, str]] = []
    i = 0
    while i < len(text):
        if text[i] == "`":
            # Count consecutive backticks to determine delimiter width
            width = 1
            while i + width < len(text) and text[i + width] == "`":
                width += 1
            delimiter = "`" * width
            # Find matching closing delimiter
            content_start = i + width
            close_idx = text.find(delimiter, content_start)
            if close_idx != -1:
                content = text[content_start:close_idx]
                if content.strip():  # Skip empty/whitespace-only
                    spans.append((content_start, close_idx, content.strip()))
                i = close_idx + width
            else:
                i += width  # No closing delimiter found, skip
        else:
            i += 1
    return spans


def _is_backticked_at(
    text: str, start: int, end: int, bt_spans: list[tuple[int, int, str]]
) -> bool:
    """Check if the span text[start:end] is within a backtick-delimited region.

    Handles both exact matches (raw == backtick content) and substring matches
    (e.g., ValueError extracted from `ValueError: bad input`).
    """
    for bt_start, bt_end, _ in bt_spans:
        if start >= bt_start and end <= bt_end:
            return True
    return False


# --- Extractor pipeline ---


def _extract_urls(
    text: str,
    spans: list[tuple[int, int]],
    matches: list[_RawMatch],
    bt_spans: list[tuple[int, int, str]],
) -> None:
    """Extract URLs (category 2). Maps to file_path."""
    for m in _URL_RE.finditer(text):
        start, end = m.start(), m.end()
        # Strip trailing punctuation that's likely not part of the URL
        raw = m.group()
        while raw and raw[-1] in ".,;:!?)>]":
            raw = raw[:-1]
            end -= 1
        if not raw:
            continue
        if _overlaps(spans, start, end):
            continue
        backticked = _is_backticked_at(text, start, end, bt_spans)
        matches.append(_RawMatch("file_path", raw, start, end, backticked))
        spans.append((start, end))


def _extract_file_locs(
    text: str,
    spans: list[tuple[int, int]],
    matches: list[_RawMatch],
    bt_spans: list[tuple[int, int, str]],
) -> None:
    """Extract file locations (category 1a). file_loc type."""
    for pattern in (_FILE_LOC_COLON_RE, _FILE_LOC_ANCHOR_RE):
        for m in pattern.finditer(text):
            start, end = m.start(), m.end()
            raw = m.group()
            if _overlaps(spans, start, end):
                continue
            backticked = _is_backticked_at(text, start, end, bt_spans)
            matches.append(_RawMatch("file_loc", raw, start, end, backticked))
            spans.append((start, end))


def _extract_file_paths(
    text: str,
    spans: list[tuple[int, int]],
    matches: list[_RawMatch],
    bt_spans: list[tuple[int, int, str]],
) -> None:
    """Extract file paths (category 1b). file_path type."""
    for m in _FILE_PATH_RE.finditer(text):
        start, end = m.start(), m.end()
        raw = m.group()
        # Skip traversal paths (../ or /.. segments) — they always fail
        # downstream path checking. Claim the span so downstream extractors
        # don't match substrings. Uses path-segment check, not substring
        # match, to avoid rejecting filenames with consecutive dots.
        parts = raw.split("/")
        if ".." in parts:
            spans.append((start, end))
            continue
        if _overlaps(spans, start, end):
            continue
        backticked = _is_backticked_at(text, start, end, bt_spans)
        matches.append(_RawMatch("file_path", raw, start, end, backticked))
        spans.append((start, end))


def _extract_file_names(
    text: str,
    spans: list[tuple[int, int]],
    matches: list[_RawMatch],
    bt_spans: list[tuple[int, int, str]],
) -> None:
    """Extract file names (category 1c). file_name type."""
    for m in _FILE_NAME_RE.finditer(text):
        start, end = m.start(), m.end()
        raw = m.group()
        if _overlaps(spans, start, end):
            continue
        backticked = _is_backticked_at(text, start, end, bt_spans)
        matches.append(_RawMatch("file_name", raw, start, end, backticked))
        spans.append((start, end))


def _extract_dotted_symbols(
    text: str,
    spans: list[tuple[int, int]],
    matches: list[_RawMatch],
    bt_spans: list[tuple[int, int, str]],
) -> None:
    """Extract dotted symbols (category 3). symbol type."""
    for m in _DOTTED_SYMBOL_RE.finditer(text):
        start, end = m.start(), m.end()
        raw = m.group()
        if _overlaps(spans, start, end):
            continue
        backticked = _is_backticked_at(text, start, end, bt_spans)
        matches.append(_RawMatch("symbol", raw, start, end, backticked))
        spans.append((start, end))


def _extract_errors(
    text: str,
    spans: list[tuple[int, int]],
    matches: list[_RawMatch],
    bt_spans: list[tuple[int, int, str]],
) -> None:
    """Extract structured error patterns (category 4). symbol type."""
    for m in _ERROR_RE.finditer(text):
        start, end = m.start(), m.end()
        raw = m.group()
        if _overlaps(spans, start, end):
            continue
        backticked = _is_backticked_at(text, start, end, bt_spans)
        matches.append(_RawMatch("symbol", raw, start, end, backticked))
        spans.append((start, end))


# --- Public API ---


def extract_entities(
    text: str,
    *,
    source_type: str,
    in_focus: bool,
    ctx: AppContext,
) -> list[Entity]:
    """Extract entities from a claim or unresolved text string.

    Runs the ordered extractor pipeline:
    1. URLs (prevents path extractors from matching URL components)
    2. file_loc (colon/anchor patterns — highest path priority)
    3. file_path (path separator patterns)
    4. file_name (known extension patterns)
    5. Dotted symbols
    6. Structured errors

    Span tracking prevents overlapping extractions.
    Entity IDs come from ctx.next_entity_id().

    Args:
        text: The .text field from a claim or unresolved item.
        source_type: "claim" or "unresolved".
        in_focus: True for focus.claims/unresolved, False for context_claims.
        ctx: AppContext for ID generation.

    Returns:
        List of Entity models, ordered by position in text.
    """
    if not text:
        return []

    # Cap input length to bound worst-case regex execution (ReDoS mitigation)
    if len(text) > MAX_TEXT_LEN:
        text = text[:MAX_TEXT_LEN]

    # Note: text is NOT NFC-normalized before regex matching. Normalizing here
    # would shift character positions and break span tracking. Instead, canon()
    # normalizes per-entity after extraction. NFD combining characters spanning
    # regex boundaries are theoretically possible but not observed in practice.

    # Pre-compute backtick spans for confidence detection
    bt_spans = _find_backtick_spans(text)

    spans: list[tuple[int, int]] = []
    matches: list[_RawMatch] = []

    # Ordered pipeline: URL first (so path extractors don't match URL internals),
    # then file_loc > file_path > file_name > symbols > errors
    _extract_urls(text, spans, matches, bt_spans)
    _extract_file_locs(text, spans, matches, bt_spans)
    _extract_file_paths(text, spans, matches, bt_spans)
    _extract_file_names(text, spans, matches, bt_spans)
    _extract_dotted_symbols(text, spans, matches, bt_spans)
    _extract_errors(text, spans, matches, bt_spans)

    # Sort by position in text for deterministic ordering
    matches.sort(key=lambda m: m.start)

    # Build Entity models
    entities: list[Entity] = []
    for m in matches:
        canonical = _canon(m.entity_type, m.raw)
        confidence = _confidence(m.backticked, m.entity_type, m.raw)
        tier = TIER_MAP[m.entity_type]

        entity = Entity(
            id=ctx.next_entity_id(),
            type=m.entity_type,
            tier=tier,
            raw=m.raw,
            canonical=canonical,
            confidence=confidence,
            source_type=source_type,
            in_focus=in_focus,
            resolved_to=None,
        )
        entities.append(entity)

    return entities

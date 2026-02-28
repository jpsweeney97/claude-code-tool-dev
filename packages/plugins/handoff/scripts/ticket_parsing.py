"""Parse fenced-YAML ticket format used in docs/tickets/.

Existing tickets use ```yaml ... ``` blocks (NOT --- frontmatter).
handoff_parsing.py cannot parse this format. This module uses PyYAML
for full YAML support including multiline values (files: arrays, etc.).
"""
from __future__ import annotations

import re
from typing import Any

import yaml

# Match the first ```yaml ... ``` block in a markdown file.
_FENCED_YAML_RE = re.compile(
    r"^```ya?ml\s*\n(.*?)^```",
    re.MULTILINE | re.DOTALL,
)


def extract_fenced_yaml(text: str) -> str | None:
    """Extract the YAML text from the first fenced yaml block.

    Returns None if no fenced yaml block is found.
    """
    m = _FENCED_YAML_RE.search(text)
    return m.group(1) if m else None


def _normalize_yaml_scalars(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize yaml.safe_load auto-conversions back to strings.

    PyYAML converts unquoted date-like values (e.g., 2026-02-28) to
    datetime.date objects. This normalizes top-level string fields back to str.

    Note: Does not recurse into nested dicts (e.g., provenance subdict).
    Ticket schema only uses date-like values at top level. (P1-8)
    """
    import datetime

    for key, value in data.items():
        if isinstance(value, (datetime.date, datetime.datetime)):
            data[key] = str(value)
    return data


def parse_yaml_frontmatter(yaml_text: str) -> dict[str, Any] | None:
    """Parse a YAML string into a dict using yaml.safe_load.

    Returns None if the YAML is empty or malformed.
    Normalizes datetime.date/datetime values back to str (P0-3 fix).
    """
    if not yaml_text.strip():
        return None
    try:
        result = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None
    if not isinstance(result, dict):
        return None
    return _normalize_yaml_scalars(result)

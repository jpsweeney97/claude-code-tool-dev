"""Config reader for context-metrics plugin.

Reads ~/.claude/context-metrics.local.md YAML frontmatter.
Stdlib only — no pyyaml dependency at runtime.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_WINDOW = 200_000
UPGRADE_WINDOW = 1_000_000


@dataclass
class Config:
    context_window: int = DEFAULT_WINDOW
    soft_boundary: int | None = None
    _explicitly_set: bool = field(default=False, repr=False)

    def maybe_upgrade_window(self, observed_occupancy: int) -> None:
        """Auto-upgrade to 1M if occupancy exceeds 200k default."""
        if not self._explicitly_set and observed_occupancy > DEFAULT_WINDOW:
            self.context_window = UPGRADE_WINDOW


def read_config(path: Path) -> Config:
    """Read config from YAML frontmatter. Returns defaults on any error."""
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return Config()

    frontmatter = _extract_frontmatter(text)
    if frontmatter is None:
        return Config()

    values = _parse_simple_yaml(frontmatter)
    window = values.get("context_window")
    boundary = values.get("soft_boundary")

    explicitly_set = window is not None
    return Config(
        context_window=window if window is not None else DEFAULT_WINDOW,
        soft_boundary=boundary,
        _explicitly_set=explicitly_set,
    )


def _extract_frontmatter(text: str) -> str | None:
    """Extract content between --- delimiters."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    return match.group(1) if match else None


def _parse_simple_yaml(text: str) -> dict[str, int]:
    """Minimal YAML parser for key: int_value lines. Stdlib only."""
    result: dict[str, int] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue
        key = parts[0].strip()
        try:
            value = int(parts[1].strip())
            result[key] = value
        except ValueError:
            continue
    return result

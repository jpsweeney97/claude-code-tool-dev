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

# Model prefix -> context window size.
# Claude Code models with known default context windows.
# Prefix-match handles dated variants (e.g., claude-opus-4-6-20250514).
MODEL_WINDOWS: dict[str, int] = {
    "claude-opus-4-7": 1_000_000,
    "claude-opus-4-6": 1_000_000,
    "claude-sonnet-4-6": 1_000_000,
}


@dataclass
class Config:
    context_window: int = DEFAULT_WINDOW
    soft_boundary: int | None = None
    _explicitly_set: bool = field(default=False, repr=False)
    _model_detected: bool = field(default=False, repr=False)

    def detect_window_from_model(self, model: str) -> None:
        """Set context window based on model name from JSONL transcript.

        Skipped when user explicitly configured a window via config file.
        Prefix-matches against MODEL_WINDOWS for dated model variants.
        Only applies once per sidecar lifetime (first detection wins).
        """
        if self._explicitly_set or self._model_detected:
            return
        for prefix, window in MODEL_WINDOWS.items():
            if model.startswith(prefix):
                self.context_window = window
                self._model_detected = True
                return

    def maybe_upgrade_window(self, observed_occupancy: int) -> None:
        """Auto-upgrade to 1M if occupancy exceeds 200k default.

        Fallback for models not in MODEL_WINDOWS. Skipped when user
        explicitly configured a window or model detection already ran.
        """
        if self._explicitly_set or self._model_detected:
            return
        if observed_occupancy > DEFAULT_WINDOW:
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

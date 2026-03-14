"""Version parity between machine-readable metadata files."""

from __future__ import annotations

import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def _read_pyproject_version() -> str:
    """Extract version from pyproject.toml without a TOML parser."""
    for line in (PLUGIN_ROOT / "pyproject.toml").read_text().splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    raise ValueError("version not found in pyproject.toml")


def _read_plugin_json_version() -> str:
    data = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())
    return data["version"]


class TestVersionParity:
    def test_pyproject_matches_plugin_json(self) -> None:
        """pyproject.toml and plugin.json must declare the same version."""
        assert _read_pyproject_version() == _read_plugin_json_version()

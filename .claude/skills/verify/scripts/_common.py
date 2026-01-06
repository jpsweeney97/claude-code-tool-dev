#!/usr/bin/env python3
"""
Shared utilities for verify skill scripts.

This module consolidates common functions and constants used across
multiple scripts to maintain consistency and reduce duplication.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

DEFAULT_MAX_AGE_DAYS: int = 90  # Claims older than this are considered stale


# Section normalization: map common variants to canonical names
# Keys are lowercase for case-insensitive matching
SECTION_ALIASES: dict[str, str] = {
    "feature": "Features",
    "setting": "Settings",
    "hook": "Hooks",
    "command": "Commands",
    "skill": "Skills",
    "agent": "Agents",
}


# =============================================================================
# DATE PARSING
# =============================================================================


def parse_verified_date(verified_date: str | None) -> date | None:
    """
    Parse a verification date, handling both plain and version-tagged formats.

    Supported formats:
        - "2026-01-05"               -> plain ISO date
        - "2026-01-05 (v2.0.76)"     -> date with version suffix

    Args:
        verified_date: Date string to parse, or None

    Returns:
        Parsed date object or None if invalid/missing.
    """
    if not verified_date:
        return None

    # Extract date portion (handles both plain dates and version-tagged dates)
    # Format: "YYYY-MM-DD" or "YYYY-MM-DD (vX.Y.Z)"
    date_str = verified_date.split(" ")[0].strip()

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


# =============================================================================
# VERSION DETECTION
# =============================================================================


def get_claude_code_version() -> str | None:
    """
    Get current Claude Code version by running 'claude --version'.

    Returns:
        Version string (e.g., "2.0.76") or None if unavailable.
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


# =============================================================================
# VERSION PARSING
# =============================================================================


class Version(NamedTuple):
    """Parsed semantic version."""
    major: int
    minor: int
    patch: int
    prerelease: str | None = None

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        return base

    @classmethod
    def parse(cls, version_str: str) -> "Version | None":
        """Parse a version string like '1.2.3' or '1.2.3-beta.1'."""
        match = re.match(
            r"v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?",
            version_str.strip()
        )
        if not match:
            return None
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4),
        )


# =============================================================================
# FILE OPERATIONS
# =============================================================================


def atomic_write(path: Path, content: str) -> None:
    """
    Write content to file atomically using temp file + rename.

    Prevents data corruption if process is interrupted during write.

    Args:
        path: Target file path
        content: Content to write
    """
    # Create temp file in same directory (ensures same filesystem for rename)
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        # Atomic rename
        Path(temp_path).rename(path)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise

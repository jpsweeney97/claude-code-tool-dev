#!/usr/bin/env python3
"""
Shared utilities for verify skill scripts.

This module consolidates common functions and constants used across
multiple scripts to maintain consistency and reduce duplication.
"""

from __future__ import annotations

import re
import subprocess
from datetime import date, datetime


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

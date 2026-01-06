#!/usr/bin/env python3
"""
SessionStart hook: Check verify skill cache health.

Runs at session start to warn if the claims cache is unhealthy:
- Claude Code version changed since last verification
- More than 20% of claims are stale (>90 days old)

Non-blocking: emits warnings to stdout but doesn't prevent session start.

Exit codes:
    0: Cache healthy or warning emitted (non-blocking)
    1: Script error (still non-blocking per Claude Code hook behavior)

Integration:
    Add to settings.json hooks array:
    {
        "event": "SessionStart",
        "type": "command",
        "command": "python ~/.claude/skills/verify/hooks/verify-health-check.py"
    }
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple


# =============================================================================
# CONFIGURATION
# =============================================================================

STALE_THRESHOLD_PERCENT = 20  # Warn if more than 20% stale
MAX_AGE_DAYS = 90
CACHE_PATH = Path(__file__).parent.parent / "references" / "known-claims.md"


# =============================================================================
# VERSION CHECKING
# =============================================================================

class Version(NamedTuple):
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, s: str) -> "Version | None":
        m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", s.strip())
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def get_claude_code_version() -> str | None:
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            m = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            return m.group(1) if m else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def get_stored_version(path: Path) -> str | None:
    if not path.exists():
        return None
    m = re.search(r"\*\*Claude Code version:\*\*\s*(\S+)", path.read_text())
    return m.group(1) if m else None


def version_changed(cache_path: Path) -> tuple[bool, str]:
    """Check if version changed. Returns (changed, change_type)."""
    current = get_claude_code_version()
    stored = get_stored_version(cache_path)

    if not current or not stored:
        return True, "unknown"

    cur_v = Version.parse(current)
    sto_v = Version.parse(stored)

    if not cur_v or not sto_v:
        return True, "unknown"

    if cur_v.major != sto_v.major:
        return True, "major"
    if cur_v.minor != sto_v.minor:
        return True, "minor"
    return False, "none"


# =============================================================================
# DATE PARSING
# =============================================================================


def parse_verified_date(verified_date: str | None) -> date | None:
    """
    Parse a verification date, handling both plain and version-tagged formats.

    Supported formats:
        - "2026-01-05"               → plain ISO date
        - "2026-01-05 (v2.0.76)"     → date with version suffix (from promote_claims.py)
    """
    if not verified_date:
        return None
    date_str = verified_date.split(" ")[0].strip()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


# =============================================================================
# STALENESS CHECKING
# =============================================================================

def get_staleness_stats(cache_path: Path) -> tuple[int, int]:
    """Returns (total_claims, stale_claims)."""
    if not cache_path.exists():
        return 0, 0

    content = cache_path.read_text()
    today = date.today()
    total = 0
    stale = 0
    skip_sections = {"How to Use", "Maintenance"}
    current_section: str | None = None

    for line in content.splitlines():
        if line.startswith("## "):
            section_name = line[3:].strip()
            current_section = None if section_name in skip_sections else section_name
            continue

        if current_section and line.startswith("|") and not line.startswith("| Claim") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                total += 1
                verified = parse_verified_date(parts[3])
                if verified:
                    if (today - verified).days > MAX_AGE_DAYS:
                        stale += 1
                else:
                    stale += 1  # Invalid date = stale

    return total, stale


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    if not CACHE_PATH.exists():
        # No cache file - not an error, just skip health check
        return 0

    warnings: list[str] = []

    # Check version
    changed, change_type = version_changed(CACHE_PATH)
    if changed:
        warnings.append(f"⚠️ Claude Code {change_type} version change - verify cache may be outdated")

    # Check staleness
    total, stale = get_staleness_stats(CACHE_PATH)
    if total > 0:
        stale_pct = (stale / total) * 100
        if stale_pct > STALE_THRESHOLD_PERCENT:
            warnings.append(f"⚠️ Verify cache: {stale}/{total} claims ({stale_pct:.0f}%) are stale (>{MAX_AGE_DAYS}d)")

    # Output warnings (injected into session context)
    if warnings:
        print("[Verify Skill Health Check]")
        for w in warnings:
            print(w)
        print("Run: python scripts/refresh_claims.py --version-aware --summary")

    return 0


if __name__ == "__main__":
    sys.exit(main())

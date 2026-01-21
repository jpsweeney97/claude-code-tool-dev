#!/usr/bin/env python3
"""
cleanup.py - Handoff plugin SessionStart hook script.

Responsibilities:
- Prune handoffs older than 30 days (silent background cleanup)
- Prune archived handoffs older than 90 days

Does NOT auto-inject or prompt for handoffs. Users must explicitly
run /resume to load a handoff. This prevents stale handoffs from
being suggested in unrelated sessions.

Exit Codes:
    0  - Success (always exits 0 to avoid blocking session start)
"""

import subprocess
import sys
import time
from pathlib import Path


def get_project_name() -> str:
    """Get project name from git root directory or current directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    return Path.cwd().name


def get_handoffs_dir() -> Path:
    """Get handoffs directory: ~/.claude/handoffs/<project>/"""
    return Path.home() / ".claude" / "handoffs" / get_project_name()


def prune_old_handoffs(handoffs_dir: Path, max_age_days: int = 30) -> list[Path]:
    """Delete handoff files older than max_age_days. Returns list of deleted files."""
    if not handoffs_dir.exists():
        return []

    deleted = []
    cutoff = time.time() - (max_age_days * 24 * 60 * 60)

    for handoff in handoffs_dir.glob("*.md"):
        try:
            if handoff.stat().st_mtime < cutoff:
                handoff.unlink(missing_ok=True)
                deleted.append(handoff)
        except OSError:
            pass  # Silently ignore errors during cleanup

    return deleted


def main() -> int:
    """Main entry point for SessionStart hook.

    Silently prunes old handoffs. Does not output anything.
    Users must explicitly run /resume to load handoffs.

    Returns:
        0 on success
    """
    handoffs_dir = get_handoffs_dir()

    # Prune old handoffs (silent cleanup)
    prune_old_handoffs(handoffs_dir, max_age_days=30)

    return 0


if __name__ == "__main__":
    sys.exit(main())

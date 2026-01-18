#!/usr/bin/env python3
"""
read.py - Handoff skill SessionStart hook script.

Responsibilities:
- Prune handoffs older than 30 days (silent background cleanup)
- Prune archived handoffs older than 90 days
- Prune session state files older than 24 hours

Does NOT auto-inject or prompt for handoffs. Users must explicitly
run /resume to load a handoff. This prevents stale handoffs from
being suggested in unrelated sessions.

Exit Codes:
    0  - Success
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


def get_session_state_dir() -> Path:
    """Get session state directory: ~/.claude/.session-state/"""
    return Path.home() / ".claude" / ".session-state"


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


def prune_old_archives(handoffs_dir: Path, max_age_days: int = 90) -> list[Path]:
    """Delete archived handoffs older than max_age_days. Returns list of deleted files."""
    archive_dir = handoffs_dir / ".archive"
    if not archive_dir.exists():
        return []

    deleted = []
    cutoff = time.time() - (max_age_days * 24 * 60 * 60)

    for handoff in archive_dir.glob("*.md"):
        try:
            if handoff.stat().st_mtime < cutoff:
                handoff.unlink(missing_ok=True)
                deleted.append(handoff)
        except OSError:
            pass  # Silently ignore errors during cleanup

    return deleted


def prune_old_state_files(max_age_hours: int = 24) -> list[Path]:
    """Delete state files older than max_age_hours. Returns list of deleted files."""
    state_dir = get_session_state_dir()
    if not state_dir.exists():
        return []

    deleted = []
    cutoff = time.time() - (max_age_hours * 60 * 60)

    for state_file in state_dir.glob("handoff-*"):
        try:
            if state_file.stat().st_mtime < cutoff:
                state_file.unlink(missing_ok=True)
                deleted.append(state_file)
        except OSError:
            pass  # Silently ignore errors during cleanup

    return deleted


def main() -> int:
    """Main entry point for SessionStart hook.

    Silently prunes old handoffs, archives, and state files.
    Does not output anything.
    Users must explicitly run /resume to load handoffs.

    Returns:
        0 on success
    """
    handoffs_dir = get_handoffs_dir()

    # Prune old handoffs (silent cleanup)
    prune_old_handoffs(handoffs_dir, max_age_days=30)

    # Prune old archived handoffs (90-day retention)
    prune_old_archives(handoffs_dir, max_age_days=90)

    # Prune old state files (24-hour retention)
    prune_old_state_files(max_age_hours=24)

    return 0


if __name__ == "__main__":
    sys.exit(main())

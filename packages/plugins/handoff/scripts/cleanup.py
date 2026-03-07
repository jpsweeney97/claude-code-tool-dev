#!/usr/bin/env python3
"""
cleanup.py - Handoff plugin SessionStart hook script.

Responsibilities:
- Prune handoffs older than 30 days (silent background cleanup)
- Prune archived handoffs older than 90 days
- Prune state files older than 24 hours

Does NOT auto-inject or prompt for handoffs. Users must explicitly
run /load to load a handoff. This prevents stale handoffs from
being suggested in unrelated sessions.

Exit Codes:
    0  - Success (always exits 0 to avoid blocking session start)
"""

import subprocess
import sys
import time
from pathlib import Path


def _trash(path: Path) -> bool:
    """Attempt to move a file to trash. Returns True on success, False on failure.

    Failures are silent by design — this runs during SessionStart cleanup where
    blocking the session is worse than skipping a deletion.
    """
    try:
        subprocess.run(["trash", str(path)], capture_output=True, timeout=5, check=True)
        return True
    except FileNotFoundError:
        return False  # trash binary not installed — skip deletion
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False  # PermissionError, trash failure, or timeout — skip


def get_project_name() -> str:
    """Get project name from git root directory, falling back to current directory name.

    Fallback is intentional for non-git directories. For corrupted repos or
    missing git binary, the fallback may resolve to the wrong project name —
    accepted because cleanup targets are scoped to individual files with
    age-based pruning (misidentification doesn't delete wrong-age files).
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
        # Non-zero return: not a git repo, or git error. Fall back to cwd.
    except subprocess.TimeoutExpired:
        pass  # Git hanging (disk issue, corrupted repo). Fall back to cwd.
    except FileNotFoundError:
        pass  # Git binary not installed. Fall back to cwd.
    except OSError:
        pass  # PermissionError or other OS-level issue. Fall back to cwd.
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
                if _trash(handoff):
                    deleted.append(handoff)
        except OSError:
            pass  # Handles stat() TOCTOU: file removed between glob() and stat()

    return deleted


def prune_old_state_files(max_age_hours: int = 24, *, state_dir: Path | None = None) -> list[Path]:
    """Delete state files older than max_age_hours. Returns list of deleted files."""
    if state_dir is None:
        state_dir = Path.home() / ".claude" / ".session-state"
    if not state_dir.exists():
        return []

    deleted = []
    cutoff = time.time() - (max_age_hours * 60 * 60)

    for state_file in state_dir.glob("handoff-*"):
        try:
            if state_file.stat().st_mtime < cutoff:
                if _trash(state_file):
                    deleted.append(state_file)
        except OSError:
            pass  # Handles stat() TOCTOU: file removed between glob() and stat()

    return deleted


def main() -> int:
    """Main entry point for SessionStart hook.

    Silently prunes old handoffs. Does not output anything.
    Users must explicitly run /load to load handoffs.

    Returns:
        0 on best-effort completion. A SessionStart hook must never block
        session start. Only BaseException subclasses (e.g., KeyboardInterrupt,
        SystemExit) propagate — these indicate process-level termination.
    """
    try:
        handoffs_dir = get_handoffs_dir()

        # Prune active handoffs older than 30 days
        prune_old_handoffs(handoffs_dir, max_age_days=30)

        # Prune archived handoffs older than 90 days
        prune_old_handoffs(handoffs_dir / ".archive", max_age_days=90)

        # Prune stale state files older than 24 hours
        prune_old_state_files(max_age_hours=24)
    except Exception:
        pass  # Never block session start — cleanup is best-effort

    return 0


if __name__ == "__main__":
    sys.exit(main())

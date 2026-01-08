#!/usr/bin/env python3
"""
read_v2.py - Handoff skill v2 SessionStart hook script.

Responsibilities:
- Find latest handoff for current project
- Prune handoffs older than 30 days
- Output based on recency:
  - <24h: Auto-inject content
  - >24h: Prompt to resume
  - None: Signal no handoff

Exit Codes:
    0  - Success (output produced)
    1  - No handoff found (silent exit for hook)
"""

import subprocess
import time
from pathlib import Path
from typing import List, Optional


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
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return Path.cwd().name


def get_handoffs_dir() -> Path:
    """Get handoffs directory: ~/.claude/handoffs/<project>/"""
    return Path.home() / ".claude" / "handoffs" / get_project_name()


def find_latest_handoff(handoffs_dir: Path) -> Optional[Path]:
    """Find the most recent handoff file by modification time."""
    if not handoffs_dir.exists():
        return None

    handoffs = sorted(
        handoffs_dir.glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return handoffs[0] if handoffs else None


def prune_old_handoffs(handoffs_dir: Path, max_age_days: int = 30) -> List[Path]:
    """Delete handoff files older than max_age_days. Returns list of deleted files."""
    if not handoffs_dir.exists():
        return []

    deleted = []
    cutoff = time.time() - (max_age_days * 24 * 60 * 60)

    for handoff in handoffs_dir.glob("*.md"):
        if handoff.stat().st_mtime < cutoff:
            handoff.unlink()
            deleted.append(handoff)

    return deleted

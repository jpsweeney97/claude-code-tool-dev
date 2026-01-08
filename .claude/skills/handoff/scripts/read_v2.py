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

import re
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


def is_recent(path: Path, hours: int = 24) -> bool:
    """Check if file was modified within the last N hours."""
    cutoff = time.time() - (hours * 60 * 60)
    return path.stat().st_mtime > cutoff


def extract_title(content: str) -> str:
    """Extract handoff title from frontmatter or heading."""
    # Try frontmatter title first
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].split("\n"):
                if line.startswith("title:"):
                    return line.split(":", 1)[1].strip().strip("\"'")

    # Fall back to H1 heading "# Handoff: <title>"
    match = re.search(r"^# Handoff: (.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    return "Untitled"


def extract_date(path: Path) -> str:
    """Extract date from filename (YYYY-MM-DD_HH-MM_slug.md) or mtime."""
    from datetime import datetime

    name = path.stem
    # Try to parse date from filename
    match = re.match(r"(\d{4}-\d{2}-\d{2})_", name)
    if match:
        return match.group(1)
    # Fall back to mtime
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def format_output(path: Path, is_recent: bool) -> str:
    """Format output based on recency.

    - Recent (<24h): Auto-inject with content
    - Old (>24h): Prompt to resume
    """
    content = path.read_text()
    title = extract_title(content)

    if is_recent:
        # Auto-inject: prefix with resuming marker, include content
        return f"[Resuming: {title}]\n{content}"
    else:
        # Prompt: ask whether to resume
        date = extract_date(path)
        return f"[Found handoff from {date}: {title}. Resume from this?]"

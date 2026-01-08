#!/usr/bin/env python3
"""
read.py - Handoff skill SessionStart hook script.

Responsibilities:
- Find latest handoff for current project
- Prune handoffs older than 30 days
- Output based on recency:
  - <24h: Auto-inject content
  - >24h: Prompt to resume
  - None: Silent exit (no output)

Exit Codes:
    0  - Success (output produced or no handoff found)
"""

import re
import subprocess
import sys
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
    except subprocess.TimeoutExpired:
        print("Warning: git timed out, using directory name", file=sys.stderr)
    except FileNotFoundError:
        pass
    return Path.cwd().name


def get_handoffs_dir() -> Path:
    """Get handoffs directory: ~/.claude/handoffs/<project>/"""
    return Path.home() / ".claude" / "handoffs" / get_project_name()


def find_latest_handoff(handoffs_dir: Path) -> Optional[Path]:
    """Find the most recent handoff file by modification time."""
    if not handoffs_dir.exists():
        return None

    def safe_mtime(p: Path) -> float:
        """Get mtime safely, returning 0 on error."""
        try:
            return p.stat().st_mtime
        except OSError:
            return 0

    handoffs = sorted(
        handoffs_dir.glob("*.md"),
        key=safe_mtime,
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
        try:
            if handoff.stat().st_mtime < cutoff:
                handoff.unlink(missing_ok=True)
                deleted.append(handoff)
        except OSError as e:
            print(f"Warning: could not prune {handoff.name}: {e}", file=sys.stderr)

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
    try:
        content = path.read_text()
    except OSError as e:
        return f"[Error reading handoff: {e}]"
    title = extract_title(content)

    if is_recent:
        # Auto-inject: prefix with resuming marker, include content
        return f"[Resuming: {title}]\n{content}"
    else:
        # Prompt: ask whether to resume
        date = extract_date(path)
        return f"[Found handoff from {date}: {title}. Resume from this?]"


def main() -> int:
    """Main entry point for SessionStart hook.

    Returns:
        0 on success (output produced or no handoff found)
    """
    handoffs_dir = get_handoffs_dir()

    # Prune old handoffs first
    prune_old_handoffs(handoffs_dir, max_age_days=30)

    # Find latest handoff
    latest = find_latest_handoff(handoffs_dir)
    if not latest:
        return 0  # No handoff is a valid state, not an error

    # Format and output based on recency
    recent = is_recent(latest, hours=24)
    output = format_output(latest, is_recent=recent)
    print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

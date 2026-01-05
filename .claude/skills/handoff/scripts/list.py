#!/usr/bin/env python3
"""
list.py - List available handoffs with metadata.

Part of the handoff skill.

Responsibilities:
- List handoffs for current project
- Show metadata (date, branch, title)
- Support JSON output for tooling

Usage:
    python list.py              # List project handoffs
    python list.py --global     # List all handoffs
    python list.py --json       # JSON output

Exit Codes:
    0  - Success
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from common import get_project_name, get_project_handoffs_dir, get_global_handoffs_dir, parse_frontmatter


@dataclass
class HandoffInfo:
    """Handoff metadata."""
    path: Path
    title: str
    date: datetime
    branch: Optional[str] = None
    repository: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "title": self.title,
            "date": self.date.isoformat(),
            "branch": self.branch,
            "repository": self.repository,
            "tags": self.tags
        }


def extract_title(content: str) -> str:
    """Extract handoff title from markdown."""
    match = re.search(r"^# Handoff: (.+)$", content, re.MULTILINE)
    return match.group(1) if match else "Untitled"


def parse_handoff(path: Path) -> Optional[HandoffInfo]:
    """Parse handoff file into metadata."""
    try:
        content = path.read_text()
    except Exception:
        return None

    frontmatter = parse_frontmatter(content)
    title = extract_title(content)

    # Parse date from frontmatter or filename
    date_str = frontmatter.get("date", "")
    try:
        # Try ISO format from frontmatter
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        # Fall back to file modification time
        date = datetime.fromtimestamp(path.stat().st_mtime)

    return HandoffInfo(
        path=path,
        title=title,
        date=date,
        branch=frontmatter.get("branch"),
        repository=frontmatter.get("repository"),
        tags=frontmatter.get("tags", [])
    )


def list_handoffs(handoffs_dir: Path) -> List[HandoffInfo]:
    """List all handoffs in directory."""
    if not handoffs_dir.exists():
        return []

    handoffs = []
    for path in handoffs_dir.glob("*.md"):
        # Skip symlinks for global listing (avoid duplicates)
        if path.is_symlink():
            continue

        info = parse_handoff(path)
        if info:
            handoffs.append(info)

    # Sort by date, newest first
    handoffs.sort(key=lambda h: h.date, reverse=True)
    return handoffs


def format_table(handoffs: List[HandoffInfo]) -> str:
    """Format handoffs as a table."""
    if not handoffs:
        return "No handoffs found."

    lines = []
    for i, h in enumerate(handoffs, 1):
        date_str = h.date.strftime("%Y-%m-%d %H:%M")
        branch_str = f"({h.branch})" if h.branch else ""
        lines.append(f"{i}. {date_str} - {h.title} {branch_str}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="List available handoffs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--global", "-g",
        dest="global_",
        action="store_true",
        help="List all handoffs (global directory)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        help="Override project handoffs directory"
    )

    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=10,
        help="Maximum number of handoffs to show (default: 10)"
    )

    args = parser.parse_args()

    # Determine directory
    if args.global_:
        handoffs_dir = get_global_handoffs_dir()
        context = "Global"
    else:
        handoffs_dir = args.project_dir or get_project_handoffs_dir()
        context = get_project_name()

    # List handoffs
    handoffs = list_handoffs(handoffs_dir)[:args.limit]

    # Output
    if args.json:
        output = {
            "context": context,
            "directory": str(handoffs_dir),
            "count": len(handoffs),
            "handoffs": [h.to_dict() for h in handoffs]
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Handoffs for {context}:")
        print(format_table(handoffs))

    sys.exit(0)


if __name__ == "__main__":
    main()

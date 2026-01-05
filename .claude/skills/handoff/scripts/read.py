#!/usr/bin/env python3
"""
read.py - Load a handoff for context injection.

Part of the handoff skill.

Responsibilities:
- Find latest handoff for current project
- Load specific handoff by path
- Output compact or full format

Usage:
    python read.py                    # Latest handoff, full
    python read.py --compact          # Latest handoff, compact (for injection)
    python read.py --path file.md     # Specific handoff

Examples:
    python read.py --compact 2>/dev/null || true  # SessionStart hook

Exit Codes:
    0  - Success
    1  - No handoff found
    2  - Read error
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from common import Result, get_project_handoffs_dir, parse_frontmatter


def find_latest_handoff(handoffs_dir: Path) -> Optional[Path]:
    """Find the most recent handoff file."""
    if not handoffs_dir.exists():
        return None

    # Filter out symlinks to avoid FileNotFoundError on broken symlinks
    # (symlinks in global dir point to project-local files which may be deleted)
    handoffs = sorted(
        [p for p in handoffs_dir.glob("*.md") if not p.is_symlink()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    return handoffs[0] if handoffs else None


def extract_section(content: str, section_name: str) -> List[str]:
    """Extract items from a markdown section."""
    pattern = rf"## {re.escape(section_name)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return []

    section_content = match.group(1).strip()
    lines = []

    for line in section_content.split("\n"):
        line = line.strip()
        if line and not line.startswith("```"):
            # Clean up list markers
            if line.startswith("- "):
                line = line[2:]
            elif re.match(r"^\d+\. ", line):
                line = re.sub(r"^\d+\. ", "", line)
            if line:
                lines.append(line)

    return lines


def extract_title(content: str) -> str:
    """Extract handoff title from markdown."""
    match = re.search(r"^# Handoff: (.+)$", content, re.MULTILINE)
    return match.group(1) if match else "Untitled"


def format_compact(content: str, frontmatter: Dict[str, Any]) -> str:
    """Format handoff for compact injection (<500 tokens target)."""
    title = extract_title(content)
    goal = extract_section(content, "Goal")
    decisions = extract_section(content, "Key Decisions")[:3]  # Top 3
    next_steps = extract_section(content, "Next Steps")[:3]  # Top 3

    lines = [f"[Resuming: {title}]"]

    if frontmatter.get("branch"):
        lines.append(f"Branch: {frontmatter['branch']}")

    if goal:
        lines.append(f"Goal: {goal[0]}")

    if decisions:
        lines.append("Decisions:")
        for d in decisions:
            lines.append(f"  - {d[:100]}")  # Truncate long decisions

    if next_steps:
        lines.append("Next:")
        for i, step in enumerate(next_steps, 1):
            lines.append(f"  {i}. {step[:80]}")

    return "\n".join(lines)


def read_handoff(path: Path, compact: bool = False) -> Result:
    """Read and optionally format handoff."""
    if not path.exists():
        return Result(
            success=False,
            message=f"Handoff not found: {path}",
            errors=["File not found"]
        )

    try:
        content = path.read_text()
    except Exception as e:
        return Result(
            success=False,
            message=f"Failed to read handoff: {e}",
            errors=[str(e)]
        )

    frontmatter = parse_frontmatter(content)

    if compact:
        output = format_compact(content, frontmatter)
    else:
        output = content

    return Result(
        success=True,
        message="Handoff loaded",
        data={
            "path": str(path),
            "title": extract_title(content),
            "content": output,
            "frontmatter": frontmatter
        }
    )


def main():
    parser = argparse.ArgumentParser(
        description="Load a handoff for context injection",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--path", "-p",
        type=Path,
        help="Specific handoff file to load"
    )

    parser.add_argument(
        "--compact", "-c",
        action="store_true",
        help="Output compact format for injection (<500 tokens)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        help="Override project handoffs directory"
    )

    args = parser.parse_args()

    # Find handoff
    if args.path:
        handoff_path = args.path
    else:
        project_dir = args.project_dir or get_project_handoffs_dir()
        handoff_path = find_latest_handoff(project_dir)

        if not handoff_path:
            if args.json:
                print(json.dumps({"success": False, "message": "No handoff found"}))
            # Silent exit for SessionStart hook - no error message
            sys.exit(1)

    # Read handoff
    result = read_handoff(handoff_path, compact=args.compact)

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.success:
            print(result.data["content"])
        else:
            print(f"Error: {result.message}", file=sys.stderr)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()

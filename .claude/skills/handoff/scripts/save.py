#!/usr/bin/env python3
"""
save.py - Save synthesized handoff markdown to disk.

Part of the handoff skill.

Responsibilities:
- Read markdown handoff content from stdin or file
- Extract title from content
- Save to project and global handoff directories
- Enforce retention policy

Usage:
    echo "markdown content" | python save.py
    python save.py --file handoff.md
    python save.py --title "Override Title" < handoff.md

Output:
    JSON result with path and status

Exit Codes:
    0  - Success
    1  - Invalid content (validation failed)
    2  - Write error
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from common import Result, get_project_handoffs_dir, get_global_handoffs_dir, get_project_name


def extract_title(content: str) -> str:
    """Extract title from '# Handoff: ...' line."""
    match = re.search(r"^# Handoff:\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Synthesized Session"


def slugify(text: str) -> str:
    """Convert text to filename-safe slug."""
    slug = text.lower()
    for char in [" ", "/", "\\", ":", ".", ",", "'", '"', "(", ")", "[", "]", "{", "}"]:
        slug = slug.replace(char, "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    if not slug:
        slug = "untitled"
    return slug[:50]


def enforce_retention(handoffs_dir: Path, keep: int = 10) -> list:
    """Remove old handoffs, keep most recent N. Returns removed files."""
    if not handoffs_dir.exists():
        return []

    handoffs = sorted(
        [p for p in handoffs_dir.glob("*.md") if not p.is_symlink()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    removed = []
    for handoff in handoffs[keep:]:
        try:
            handoff.unlink()
            removed.append(handoff)
        except Exception:
            pass

    return removed


def save_handoff(content: str, title: str) -> Result:
    """Save handoff content to disk."""
    now = datetime.now()
    slug = slugify(title)
    filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{slug}.md"

    project_dir = get_project_handoffs_dir()
    global_dir = get_global_handoffs_dir()

    # Ensure directories exist
    project_dir.mkdir(parents=True, exist_ok=True)
    global_dir.mkdir(parents=True, exist_ok=True)

    # Write to project directory
    project_path = project_dir / filename
    try:
        project_path.write_text(content)
    except Exception as e:
        return Result(
            success=False,
            message=f"Failed to write handoff: {e}",
            errors=[str(e)]
        )

    # Create symlink in global directory
    global_path = global_dir / f"{get_project_name()}_{filename}"
    try:
        if global_path.exists() or global_path.is_symlink():
            global_path.unlink()
        global_path.symlink_to(project_path)
    except Exception:
        # Non-fatal
        pass

    # Enforce retention
    removed = enforce_retention(project_dir, keep=10)

    return Result(
        success=True,
        message=f"Handoff saved: {project_path}",
        data={
            "path": str(project_path),
            "filename": filename,
            "title": title,
            "removed_count": len(removed)
        }
    )


def main():
    parser = argparse.ArgumentParser(
        description="Save synthesized handoff to disk",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--file", "-f",
        help="Read from file instead of stdin"
    )

    parser.add_argument(
        "--title", "-t",
        help="Override title extraction"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate before saving (exit 1 if invalid)"
    )

    args = parser.parse_args()

    # Read content
    try:
        if args.file:
            with open(args.file) as f:
                content = f.read()
        else:
            content = sys.stdin.read()
    except Exception as e:
        print(json.dumps({
            "success": False,
            "message": f"Failed to read input: {e}",
            "errors": [str(e)]
        }))
        sys.exit(2)

    if not content.strip():
        print(json.dumps({
            "success": False,
            "message": "Empty content",
            "errors": ["No content provided"]
        }))
        sys.exit(1)

    # Optional validation
    if args.validate:
        from validate import validate_handoff
        issues = validate_handoff(content)
        if issues:
            print(json.dumps({
                "success": False,
                "message": "Validation failed",
                "errors": issues
            }))
            sys.exit(1)

    # Extract or use provided title
    title = args.title or extract_title(content)

    # Save
    result = save_handoff(content, title)

    print(json.dumps(result.to_dict(), indent=2))
    sys.exit(0 if result.success else 2)


if __name__ == "__main__":
    main()

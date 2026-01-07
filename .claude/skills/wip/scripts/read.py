#!/usr/bin/env python3
"""
read.py - Display WIP items.

Usage:
    python3 read.py              # Full display
    python3 read.py --compact    # <100 tokens for SessionStart hook
    python3 read.py --json       # Structured output

Exit codes:
    0 - Success
    1 - File not found (silent for hooks)
"""

import argparse
import json
import sys
from pathlib import Path

from common import (
    Result, WipFile, WipItem, Status,
    get_wip_path, parse_wip
)


def read_wip(path: Path = None) -> Result:
    """Read and parse WIP.md file."""
    path = path or get_wip_path()

    if not path.exists():
        return Result(
            success=False,
            message="No WIP file found",
            errors=[f"Expected at: {path}"]
        )

    try:
        content = path.read_text()
        wip = parse_wip(content)
        return Result(
            success=True,
            message="WIP loaded",
            data={"wip": wip, "path": str(path)}
        )
    except Exception as e:
        return Result(
            success=False,
            message=f"Failed to parse WIP: {e}",
            errors=[str(e)]
        )


def format_compact(wip: WipFile) -> str:
    """Format WIP for SessionStart injection (<100 tokens)."""
    active = [i for i in wip.items if i.status == Status.ACTIVE]
    paused = [i for i in wip.items if i.status == Status.PAUSED]
    blocked = [i for i in active if i.blocker]

    lines = [f"[WIP: {len(active)} active, {len(paused)} paused]"]

    if active:
        lines.append("Active:")
        for item in active[:5]:  # Limit to 5 items
            if item.blocker:
                lines.append(f"  {item.id}: {item.description[:40]} [BLOCKED]")
            elif item.next_action:
                lines.append(f"  {item.id}: {item.description[:30]} → {item.next_action[:20]}")
            else:
                lines.append(f"  {item.id}: {item.description[:50]}")

        if len(active) > 5:
            lines.append(f"  ... and {len(active) - 5} more")

    return "\n".join(lines)


def format_full(wip: WipFile) -> str:
    """Format WIP for full display."""
    lines = [f"# Work In Progress ({wip.project})", ""]

    active = [i for i in wip.items if i.status == Status.ACTIVE]
    paused = [i for i in wip.items if i.status == Status.PAUSED]
    completed = [i for i in wip.items if i.status == Status.COMPLETED]

    if active:
        lines.append("## Active")
        for item in active:
            lines.append(format_item_full(item))
        lines.append("")

    if paused:
        lines.append("## Paused")
        for item in paused:
            lines.append(format_item_full(item))
        lines.append("")

    if completed:
        lines.append(f"## Completed ({len(completed)} items)")
        for item in completed[:3]:
            lines.append(f"- [{item.id}] {item.description}")
        if len(completed) > 3:
            lines.append(f"  ... and {len(completed) - 3} more")

    return "\n".join(lines)


def format_item_full(item: WipItem) -> str:
    """Format single item for display."""
    lines = [f"### [{item.id}] {item.description}"]
    lines.append(f"Added: {item.added.strftime('%Y-%m-%d')}")

    if item.files:
        lines.append(f"Files: {', '.join(item.files)}")
    if item.context:
        lines.append(f"Context: {item.context[:100]}...")
    if item.blocker:
        lines.append(f"**BLOCKED:** {item.blocker}")
    if item.next_action:
        lines.append(f"Next: {item.next_action}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Display WIP items")
    parser.add_argument("--compact", action="store_true", help="Compact format for hooks")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--path", type=Path, help="Custom WIP.md path")

    args = parser.parse_args()

    result = read_wip(args.path)

    if not result.success:
        # Silent failure for hooks
        if args.compact:
            sys.exit(0)
        print(result.message, file=sys.stderr)
        sys.exit(1)

    wip = result.data["wip"]

    if args.json:
        # Serialize WipFile to dict
        data = {
            "version": wip.version,
            "project": wip.project,
            "next_id": wip.next_id,
            "items": [
                {
                    "id": i.id,
                    "description": i.description,
                    "status": i.status.value,
                    "blocker": i.blocker,
                    "next_action": i.next_action
                }
                for i in wip.items
            ]
        }
        print(json.dumps(data, indent=2))
    elif args.compact:
        print(format_compact(wip))
    else:
        print(format_full(wip))


if __name__ == "__main__":
    main()

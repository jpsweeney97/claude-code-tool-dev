#!/usr/bin/env python3
"""
update.py - Modify WIP items.

Usage:
    python3 update.py add --desc "Description" [--files "a.py,b.py"]
    python3 update.py move W001 --status completed
    python3 update.py block W001 --reason "Waiting for X"
    python3 update.py unblock W001
    python3 update.py set W001 --next "Do thing"
    python3 update.py archive

Exit codes:
    0 - Success
    1 - Input error (bad ID, missing args)
    2 - Write error
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from common import (
    Result, WipFile, WipItem, Status,
    get_wip_path, get_archive_path, parse_wip, serialize_wip
)


def load_wip(path: Path) -> tuple[Optional[WipFile], Optional[str]]:
    """Load WIP file, return (wip, error_message)."""
    if not path.exists():
        return None, f"WIP file not found: {path}"
    try:
        content = path.read_text()
        return parse_wip(content), None
    except Exception as e:
        return None, f"Failed to parse WIP: {e}"


def save_wip(path: Path, wip: WipFile) -> Optional[str]:
    """Save WIP file, return error message or None."""
    wip.updated = datetime.now()
    try:
        content = serialize_wip(wip)
        path.write_text(content)
        return None
    except Exception as e:
        return f"Failed to write WIP: {e}"


def add_item(
    path: Path,
    description: str,
    files: List[str] = None,
    context: str = "",
    next_action: str = None
) -> Result:
    """Add new item to WIP."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    # Generate ID
    item_id = f"W{wip.next_id:03d}"
    wip.next_id += 1

    item = WipItem(
        id=item_id,
        description=description,
        added=datetime.now(),
        status=Status.ACTIVE,
        files=files or [],
        context=context,
        next_action=next_action
    )
    wip.items.append(item)

    err = save_wip(path, wip)
    if err:
        return Result(success=False, message=err)

    return Result(
        success=True,
        message=f"Added {item_id}: {description}",
        data={"id": item_id}
    )


def move_item(path: Path, item_id: str, new_status: Status) -> Result:
    """Move item to different status."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    item = next((i for i in wip.items if i.id == item_id), None)
    if not item:
        return Result(
            success=False,
            message=f"Item not found: {item_id}",
            errors=[f"Valid IDs: {[i.id for i in wip.items]}"]
        )

    old_status = item.status
    item.status = new_status

    # Set date fields
    if new_status == Status.PAUSED:
        item.paused_date = datetime.now()
    elif new_status == Status.COMPLETED:
        item.completed_date = datetime.now()
    elif new_status == Status.ACTIVE:
        item.paused_date = None  # Clear if resuming

    err = save_wip(path, wip)
    if err:
        return Result(success=False, message=err)

    return Result(
        success=True,
        message=f"Moved {item_id} from {old_status.value} to {new_status.value}"
    )


def set_blocker(path: Path, item_id: str, reason: Optional[str]) -> Result:
    """Set or clear blocker on item."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    item = next((i for i in wip.items if i.id == item_id), None)
    if not item:
        return Result(success=False, message=f"Item not found: {item_id}")

    item.blocker = reason

    err = save_wip(path, wip)
    if err:
        return Result(success=False, message=err)

    if reason:
        return Result(success=True, message=f"Blocked {item_id}: {reason}")
    else:
        return Result(success=True, message=f"Unblocked {item_id}")


def set_field(path: Path, item_id: str, field: str, value: str) -> Result:
    """Set a field on an item."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    item = next((i for i in wip.items if i.id == item_id), None)
    if not item:
        return Result(success=False, message=f"Item not found: {item_id}")

    if field == "next":
        item.next_action = value
    elif field == "context":
        item.context = value
    elif field == "files":
        item.files = [f.strip() for f in value.split(",")]
    else:
        return Result(success=False, message=f"Unknown field: {field}")

    err = save_wip(path, wip)
    if err:
        return Result(success=False, message=err)

    return Result(success=True, message=f"Updated {item_id}.{field}")


def archive_completed(path: Path) -> Result:
    """Move completed items to archive file."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    completed = [i for i in wip.items if i.status == Status.COMPLETED]
    if not completed:
        return Result(success=True, message="No completed items to archive")

    # Remove from main WIP
    wip.items = [i for i in wip.items if i.status != Status.COMPLETED]

    # Append to archive
    archive_path = get_archive_path()
    archive_content = ""
    if archive_path.exists():
        archive_content = archive_path.read_text()

    # Add archived items with timestamp
    archive_lines = [
        f"\n## Archived {datetime.now().strftime('%Y-%m-%d')}\n"
    ]
    for item in completed:
        archive_lines.append(f"- [{item.id}] {item.description}")
        if item.completed_date:
            archive_lines.append(f"  Completed: {item.completed_date.strftime('%Y-%m-%d')}")
    archive_lines.append("")

    try:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with open(archive_path, "a") as f:
            f.write("\n".join(archive_lines))

        err = save_wip(path, wip)
        if err:
            return Result(success=False, message=err)

        return Result(
            success=True,
            message=f"Archived {len(completed)} items to {archive_path}"
        )
    except Exception as e:
        return Result(success=False, message=f"Failed to archive: {e}")


def main():
    parser = argparse.ArgumentParser(description="Modify WIP items")
    parser.add_argument("--path", type=Path, help="Custom WIP.md path")
    parser.add_argument("--json", action="store_true", help="JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add command
    add_parser = subparsers.add_parser("add", help="Add new item")
    add_parser.add_argument("--desc", required=True, help="Description")
    add_parser.add_argument("--files", help="Comma-separated file list")
    add_parser.add_argument("--context", default="", help="Context text")
    add_parser.add_argument("--next", dest="next_action", help="Next action")

    # move command
    move_parser = subparsers.add_parser("move", help="Move item status")
    move_parser.add_argument("item_id", help="Item ID (e.g., W001)")
    move_parser.add_argument("--status", required=True,
                             choices=["active", "paused", "completed"])

    # block command
    block_parser = subparsers.add_parser("block", help="Set blocker")
    block_parser.add_argument("item_id", help="Item ID")
    block_parser.add_argument("--reason", required=True, help="Blocker reason")

    # unblock command
    unblock_parser = subparsers.add_parser("unblock", help="Clear blocker")
    unblock_parser.add_argument("item_id", help="Item ID")

    # set command
    set_parser = subparsers.add_parser("set", help="Set field value")
    set_parser.add_argument("item_id", help="Item ID")
    set_parser.add_argument("--next", dest="next_val", help="Next action")
    set_parser.add_argument("--context", help="Context text")
    set_parser.add_argument("--files", help="Comma-separated files")

    # archive command
    subparsers.add_parser("archive", help="Archive completed items")

    args = parser.parse_args()
    path = args.path or get_wip_path()

    # Execute command
    if args.command == "add":
        files = [f.strip() for f in args.files.split(",")] if args.files else []
        result = add_item(path, args.desc, files, args.context, args.next_action)
    elif args.command == "move":
        status_map = {
            "active": Status.ACTIVE,
            "paused": Status.PAUSED,
            "completed": Status.COMPLETED
        }
        result = move_item(path, args.item_id.upper(), status_map[args.status])
    elif args.command == "block":
        result = set_blocker(path, args.item_id.upper(), args.reason)
    elif args.command == "unblock":
        result = set_blocker(path, args.item_id.upper(), None)
    elif args.command == "set":
        if args.next_val:
            result = set_field(path, args.item_id.upper(), "next", args.next_val)
        elif args.context:
            result = set_field(path, args.item_id.upper(), "context", args.context)
        elif args.files:
            result = set_field(path, args.item_id.upper(), "files", args.files)
        else:
            result = Result(success=False, message="No field specified")
    elif args.command == "archive":
        result = archive_completed(path)
    else:
        result = Result(success=False, message=f"Unknown command: {args.command}")

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.message)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()

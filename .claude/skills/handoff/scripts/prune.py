#!/usr/bin/env python3
"""
prune.py - Remove old handoffs per retention policy.

Part of the handoff skill.

Responsibilities:
- Remove handoffs beyond retention limit
- Support dry-run mode
- Clean up orphaned symlinks in global directory

Usage:
    python prune.py                 # Prune project, keep 10
    python prune.py --keep 5        # Keep only 5
    python prune.py --dry-run       # Show what would be removed
    python prune.py --global        # Prune global directory

Exit Codes:
    0  - Success
    1  - Error
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from common import Result, get_project_handoffs_dir, get_global_handoffs_dir


def prune_handoffs(
    handoffs_dir: Path,
    keep: int = 10,
    dry_run: bool = False
) -> Result:
    """Remove old handoffs, keeping most recent N."""
    if not handoffs_dir.exists():
        return Result(
            success=True,
            message="No handoffs directory found",
            data={"removed": [], "kept": 0}
        )

    # Get all handoff files (not symlinks)
    handoffs = sorted(
        [p for p in handoffs_dir.glob("*.md") if not p.is_symlink()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    to_remove = handoffs[keep:]
    to_keep = handoffs[:keep]

    removed_paths = []
    errors = []

    for handoff in to_remove:
        if dry_run:
            removed_paths.append(str(handoff))
        else:
            try:
                handoff.unlink()
                removed_paths.append(str(handoff))
            except Exception as e:
                errors.append(f"Failed to remove {handoff}: {e}")

    return Result(
        success=len(errors) == 0,
        message=f"{'Would remove' if dry_run else 'Removed'} {len(removed_paths)} handoff(s)",
        data={
            "removed": removed_paths,
            "kept": len(to_keep),
            "dry_run": dry_run
        },
        errors=errors
    )


def cleanup_orphaned_symlinks(global_dir: Path, dry_run: bool = False) -> List[str]:
    """Remove symlinks pointing to non-existent files."""
    if not global_dir.exists():
        return []

    removed = []
    for path in global_dir.iterdir():
        if path.is_symlink() and not path.exists():
            if dry_run:
                removed.append(str(path))
            else:
                try:
                    path.unlink()
                    removed.append(str(path))
                except Exception:
                    pass

    return removed


def main():
    parser = argparse.ArgumentParser(
        description="Remove old handoffs per retention policy",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--keep", "-k",
        type=int,
        default=10,
        help="Number of handoffs to keep (default: 10)"
    )

    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be removed without removing"
    )

    parser.add_argument(
        "--global", "-g",
        dest="global_",
        action="store_true",
        help="Prune global directory instead of project"
    )

    parser.add_argument(
        "--cleanup-symlinks",
        action="store_true",
        help="Also clean up orphaned symlinks in global directory"
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

    args = parser.parse_args()

    # Determine directory
    if args.global_:
        handoffs_dir = get_global_handoffs_dir()
    else:
        handoffs_dir = args.project_dir or get_project_handoffs_dir()

    # Prune handoffs
    result = prune_handoffs(handoffs_dir, keep=args.keep, dry_run=args.dry_run)

    # Cleanup orphaned symlinks
    orphaned_removed = []
    if args.cleanup_symlinks or args.global_:
        global_dir = get_global_handoffs_dir()
        orphaned_removed = cleanup_orphaned_symlinks(global_dir, dry_run=args.dry_run)
        result.data["orphaned_symlinks_removed"] = orphaned_removed

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if args.dry_run:
            print("Dry run - no files removed")
            print()

        if result.data["removed"]:
            action = "Would remove" if args.dry_run else "Removed"
            print(f"{action} {len(result.data['removed'])} handoff(s):")
            for path in result.data["removed"]:
                print(f"  - {Path(path).name}")
        else:
            print("No handoffs to remove")

        print(f"\nKept: {result.data['kept']} handoff(s)")

        if orphaned_removed:
            action = "Would remove" if args.dry_run else "Removed"
            print(f"\n{action} {len(orphaned_removed)} orphaned symlink(s)")

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()

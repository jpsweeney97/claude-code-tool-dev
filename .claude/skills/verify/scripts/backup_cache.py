#!/usr/bin/env python3
"""
Backup and restore known-claims.md cache.

Maintains rolling backups (last 5) to protect against data loss.

Exit codes:
    0 - Success
    1 - Input error
    10 - No backups to restore
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


BACKUP_DIR = Path(__file__).parent.parent / "references" / ".backups"
KNOWN_CLAIMS = Path(__file__).parent.parent / "references" / "known-claims.md"
MAX_BACKUPS = 5


def create_backup(source: Path = KNOWN_CLAIMS, backup_dir: Path = BACKUP_DIR) -> Path | None:
    """Create timestamped backup of known-claims.md."""
    if not source.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"known-claims_{timestamp}.md"

    shutil.copy2(source, backup_path)

    # Cleanup old backups (keep MAX_BACKUPS)
    backups = sorted(backup_dir.glob("known-claims_*.md"), reverse=True)
    for old_backup in backups[MAX_BACKUPS:]:
        old_backup.unlink()

    return backup_path


def list_backups(backup_dir: Path = BACKUP_DIR) -> list[Path]:
    """List available backups, newest first."""
    if not backup_dir.exists():
        return []
    return sorted(backup_dir.glob("known-claims_*.md"), reverse=True)


def restore_backup(backup_path: Path, target: Path = KNOWN_CLAIMS) -> bool:
    """Restore from a backup file."""
    if not backup_path.exists():
        return False

    # Create backup of current before restoring
    if target.exists():
        create_backup(target)

    shutil.copy2(backup_path, target)
    return True


def diff_backup(backup_path: Path, current: Path = KNOWN_CLAIMS) -> tuple[int, int, int]:
    """Compare backup with current file. Returns (added, removed, unchanged) line counts."""
    if not backup_path.exists() or not current.exists():
        return (0, 0, 0)

    backup_lines = set(backup_path.read_text().splitlines())
    current_lines = set(current.read_text().splitlines())

    added = len(current_lines - backup_lines)
    removed = len(backup_lines - current_lines)
    unchanged = len(backup_lines & current_lines)

    return (added, removed, unchanged)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup and restore known-claims.md")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # backup command
    backup_parser = subparsers.add_parser("backup", help="Create backup")
    backup_parser.add_argument("--source", type=Path, default=KNOWN_CLAIMS)

    # list command
    list_parser = subparsers.add_parser("list", help="List backups")
    list_parser.add_argument("--diff", action="store_true", help="Show diff stats")

    # restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup", nargs="?", help="Backup file to restore (latest if omitted)")
    restore_parser.add_argument("--dry-run", action="store_true", help="Preview without restoring")

    args = parser.parse_args()

    if args.command == "backup":
        backup_path = create_backup(args.source)
        if backup_path:
            print(f"Created backup: {backup_path.name}")
            return 0
        else:
            print("Error: Source file not found", file=sys.stderr)
            return 1

    elif args.command == "list":
        backups = list_backups()
        if backups:
            print("Available backups:")
            for i, b in enumerate(backups):
                timestamp = b.stem.replace("known-claims_", "")
                size = b.stat().st_size
                marker = " (latest)" if i == 0 else ""

                if args.diff:
                    added, removed, unchanged = diff_backup(b)
                    diff_info = f" | +{added} -{removed}"
                else:
                    diff_info = ""

                print(f"  {i+1}. {timestamp} ({size:,} bytes){marker}{diff_info}")
        else:
            print("No backups found")
        return 0

    elif args.command == "restore":
        backups = list_backups()

        if not backups:
            print("No backups available", file=sys.stderr)
            return 10

        if args.backup:
            # Find matching backup
            backup_path = None
            for b in backups:
                if args.backup in str(b):
                    backup_path = b
                    break
            if not backup_path:
                print(f"Backup not found: {args.backup}", file=sys.stderr)
                return 1
        else:
            backup_path = backups[0]  # Latest

        if args.dry_run:
            added, removed, unchanged = diff_backup(backup_path)
            print(f"[DRY RUN] Would restore from: {backup_path.name}")
            print(f"  Changes: +{added} -{removed} ~{unchanged}")
            return 0

        if restore_backup(backup_path):
            print(f"Restored from: {backup_path.name}")
            return 0
        else:
            print("Restore failed", file=sys.stderr)
            return 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

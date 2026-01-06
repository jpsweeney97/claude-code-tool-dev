#!/usr/bin/env python3
"""
Check Claude Code version against the version stored in known-claims.md.

Detects when Claude Code has been updated, which may invalidate cached claims.
Suggests re-verification when major/minor version changes are detected.

Exit codes:
    0: Version matches or no significant change
    1: Input error (can't get version, file missing)
    2: Major/minor version changed (claims may need refresh)

Usage:
    python check_version.py                # Check current vs stored version
    python check_version.py --update       # Update stored version to current
    python check_version.py --json         # JSON output for scripting
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

from _common import get_claude_code_version, Version


@dataclass
class VersionCheck:
    """Result of version comparison."""
    current_version: str
    stored_version: str | None
    is_newer: bool
    change_type: str  # "none", "patch", "minor", "major", "unknown"
    needs_refresh: bool  # True if major/minor changed


def compare_versions(current: Version, stored: Version | None) -> VersionCheck:
    """Compare current version against stored version."""
    if stored is None:
        return VersionCheck(
            current_version=str(current),
            stored_version=None,
            is_newer=True,
            change_type="unknown",
            needs_refresh=True,  # Unknown stored version, recommend refresh
        )

    if current.major > stored.major:
        change_type = "major"
        needs_refresh = True
    elif current.major < stored.major:
        change_type = "downgrade"
        needs_refresh = True
    elif current.minor > stored.minor:
        change_type = "minor"
        needs_refresh = True
    elif current.minor < stored.minor:
        change_type = "downgrade"
        needs_refresh = True
    elif current.patch > stored.patch:
        change_type = "patch"
        needs_refresh = False  # Patch updates typically don't change documented behavior
    elif current.patch < stored.patch:
        change_type = "downgrade"
        needs_refresh = False
    else:
        change_type = "none"
        needs_refresh = False

    return VersionCheck(
        current_version=str(current),
        stored_version=str(stored),
        is_newer=current > stored,
        change_type=change_type,
        needs_refresh=needs_refresh,
    )


# =============================================================================
# VERSION DETECTION
# =============================================================================


def get_stored_version(path: Path) -> str | None:
    """Get version stored in known-claims.md header."""
    if not path.exists():
        return None

    content = path.read_text()
    # Look for: **Claude Code version:** 1.2.3
    match = re.search(r"\*\*Claude Code version:\*\*\s*(\S+)", content)
    if match:
        return match.group(1)
    return None


def update_stored_version(path: Path, version: str) -> bool:
    """Update or add version in known-claims.md header."""
    if not path.exists():
        return False

    content = path.read_text()
    lines = content.splitlines()

    # Check if version line exists
    version_pattern = re.compile(r"^\*\*Claude Code version:\*\*")
    version_line = f"**Claude Code version:** {version}"

    for i, line in enumerate(lines):
        if version_pattern.match(line):
            lines[i] = version_line
            path.write_text("\n".join(lines) + "\n")
            return True

    # Version line doesn't exist, add after "Last verified" or "Method"
    for i, line in enumerate(lines):
        if line.startswith("**Method:**") or line.startswith("**Last verified:**"):
            # Insert after this line
            lines.insert(i + 1, version_line)
            path.write_text("\n".join(lines) + "\n")
            return True

    # Couldn't find a good insertion point
    return False


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Claude Code version against stored version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Version Change Types:
    none:      Same version
    patch:     Patch update (1.2.3 → 1.2.4) - unlikely to affect claims
    minor:     Minor update (1.2.3 → 1.3.0) - may affect claims
    major:     Major update (1.2.3 → 2.0.0) - likely affects claims
    downgrade: Version went backwards

Examples:
    # Check current vs stored version
    python check_version.py

    # Update stored version to current
    python check_version.py --update

    # JSON output for scripting
    python check_version.py --json
        """,
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update stored version to current version",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    # Get current version
    current_str = get_claude_code_version()
    if not current_str:
        if args.json:
            print(json.dumps({"error": "Could not get Claude Code version"}))
        else:
            print("Error: Could not get Claude Code version", file=sys.stderr)
            print("Make sure 'claude' is in PATH and working", file=sys.stderr)
        return 1

    current = Version.parse(current_str)
    if not current:
        if args.json:
            print(json.dumps({"error": f"Could not parse version: {current_str}"}))
        else:
            print(f"Error: Could not parse version: {current_str}", file=sys.stderr)
        return 1

    # Handle update operation
    if args.update:
        if not args.cache.exists():
            if args.json:
                print(json.dumps({"error": f"Cache file not found: {args.cache}"}))
            else:
                print(f"Error: Cache file not found: {args.cache}", file=sys.stderr)
            return 1

        success = update_stored_version(args.cache, str(current))
        if args.json:
            print(json.dumps({"updated": success, "version": str(current)}))
        else:
            if success:
                print(f"✓ Updated stored version to {current}")
            else:
                print(f"✗ Could not update version in {args.cache}")
        return 0 if success else 1

    # Compare versions
    stored_str = get_stored_version(args.cache)
    stored = Version.parse(stored_str) if stored_str else None

    result = compare_versions(current, stored)

    # Output
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(f"Claude Code version check")
        print(f"  Current:  {result.current_version}")
        print(f"  Stored:   {result.stored_version or '(not tracked)'}")
        print(f"  Change:   {result.change_type}")

        if result.needs_refresh:
            print()
            if result.change_type == "unknown":
                print("⚠️  No stored version found. Consider running:")
                print(f"     python {Path(__file__).name} --update")
            else:
                print(f"⚠️  {result.change_type.upper()} version change detected!")
                print("    Cached claims may be outdated. Consider:")
                print("    1. Review claims in affected areas")
                print("    2. Run /verify on critical claims")
                print(f"    3. Update stored version: python {Path(__file__).name} --update")
        else:
            if result.change_type == "none":
                print("\n✓ Version matches. Cache is version-current.")
            else:
                print(f"\n✓ Patch update only. Claims likely still valid.")

    # Exit code: 2 if refresh recommended
    return 2 if result.needs_refresh else 0


if __name__ == "__main__":
    sys.exit(main())

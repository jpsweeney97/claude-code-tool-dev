#!/usr/bin/env python3
"""
init.py - Create new WIP.md file.

Usage:
    python3 init.py [--force] [--path PATH]

Exit codes:
    0 - Success
    1 - File already exists
    2 - Write error
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from common import Result, WipFile, get_wip_path, get_project_name, serialize_wip


def create_wip_file(path: Path, project: str = None, force: bool = False) -> Result:
    """Create a new WIP.md file."""
    if path.exists() and not force:
        return Result(
            success=False,
            message=f"WIP file already exists: {path}",
            errors=["Use --force to overwrite"]
        )

    # Create parent directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create empty WIP file
    wip = WipFile(
        version=1,
        project=project or get_project_name(),
        updated=datetime.now(),
        next_id=1,
        items=[]
    )

    try:
        content = serialize_wip(wip)
        path.write_text(content)
        return Result(
            success=True,
            message=f"Created WIP file: {path}",
            data={"path": str(path)}
        )
    except OSError as e:
        return Result(
            success=False,
            message=f"Failed to write WIP file: {e}",
            errors=[str(e)]
        )


def main():
    parser = argparse.ArgumentParser(description="Create new WIP.md file")
    parser.add_argument("--force", action="store_true", help="Overwrite if exists")
    parser.add_argument("--path", type=Path, help="Custom path for WIP.md")
    parser.add_argument("--project", help="Project name")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    path = args.path or get_wip_path()
    result = create_wip_file(path, project=args.project, force=args.force)

    if args.json:
        import json
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.message)

    sys.exit(0 if result.success else (1 if "exists" in result.message else 2))


if __name__ == "__main__":
    main()

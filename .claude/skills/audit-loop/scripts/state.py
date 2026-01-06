#!/usr/bin/env python3
"""
State management for audit-loop.

Subcommands:
    create <artifact>     Initialize new .audit.json
    read <artifact>       Display current state
    update <artifact>     Modify state fields
    validate <artifact>   Check state integrity
    list [directory]      Find active audits
    archive <artifact>    Archive completed audit

Exit codes:
    0  - Success
    1  - Error
    2  - Invalid arguments
    10 - Validation failed
    11 - Not found
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _common import (
    EXIT_ARGS,
    EXIT_ERROR,
    EXIT_NOT_FOUND,
    EXIT_SUCCESS,
    EXIT_VALIDATION,
    MAX_CYCLES,
    PHASES,
    SCHEMA_VERSION,
    Result,
    atomic_write,
    get_archive_path,
    get_state_path,
)


# =============================================================================
# STATE OPERATIONS
# =============================================================================

def create_state(artifact_path: Path, force: bool = False) -> Result:
    """
    Initialize new audit state for an artifact.

    Args:
        artifact_path: Path to the artifact being audited
        force: If True, overwrite existing state

    Returns:
        Result with state path in data
    """
    artifact_path = Path(artifact_path).resolve()
    state_path = get_state_path(artifact_path)

    if not artifact_path.exists():
        return Result.failure(
            f"Artifact not found: {artifact_path}",
            errors=[f"File does not exist: {artifact_path}"],
        )

    if state_path.exists() and not force:
        return Result.failure(
            f"State already exists: {state_path}",
            errors=["Use --force to overwrite existing state"],
        )

    now = datetime.now(timezone.utc).isoformat()
    state = {
        "version": SCHEMA_VERSION,
        "artifact": str(artifact_path),
        "created": now,
        "updated": now,
        "calibration": None,
        "cycle": 1,
        "phase": "stakes_assessment",
        "definition": {
            "goal": None,
            "scope": [],
            "excluded": [],
            "excluded_rationale": None,
            "assumptions": [],
            "done_criteria": None,
        },
        "findings": [],
        "verification": {
            "counter_conclusion": None,
            "limitations": [],
        },
        "history": [
            {"timestamp": now, "event": "created", "data": {}}
        ],
    }

    try:
        atomic_write(state_path, json.dumps(state, indent=2))
        return Result.success(
            f"Created audit state: {state_path}",
            data={"state_path": str(state_path), "state": state},
        )
    except OSError as e:
        return Result.failure(
            f"Failed to write state: {e}",
            errors=[str(e)],
        )


def read_state(artifact_path: Path) -> Result:
    """
    Read and return current audit state.

    Args:
        artifact_path: Path to the artifact being audited

    Returns:
        Result with state in data
    """
    state_path = get_state_path(Path(artifact_path))

    if not state_path.exists():
        return Result.failure(
            f"No audit state found: {state_path}",
            errors=["Run 'state.py create <artifact>' first"],
        )

    try:
        state = json.loads(state_path.read_text())
        return Result.success(
            f"Read state from: {state_path}",
            data={"state_path": str(state_path), "state": state},
        )
    except json.JSONDecodeError as e:
        return Result.failure(
            f"Invalid JSON in state file: {e}",
            errors=[str(e)],
        )
    except OSError as e:
        return Result.failure(
            f"Failed to read state: {e}",
            errors=[str(e)],
        )


# =============================================================================
# CLI
# =============================================================================

def cmd_create(args: argparse.Namespace) -> int:
    """Handle create subcommand."""
    result = create_state(Path(args.artifact), force=args.force)
    if args.json:
        print(result.to_json())
    else:
        print(result.message)
    return EXIT_SUCCESS if result.ok else EXIT_ERROR


def cmd_read(args: argparse.Namespace) -> int:
    """Handle read subcommand."""
    result = read_state(Path(args.artifact))
    if not result.ok:
        if args.json:
            print(result.to_json())
        else:
            print(result.message, file=sys.stderr)
        return EXIT_NOT_FOUND

    if args.json:
        print(json.dumps(result.data["state"], indent=2))
    else:
        state = result.data["state"]
        print(f"Artifact: {state['artifact']}")
        print(f"Phase: {state['phase']}")
        print(f"Cycle: {state['cycle']}")
        if state.get("calibration"):
            print(f"Calibration: {state['calibration']['level']} (score {state['calibration']['score']})")
        print(f"Findings: {len(state['findings'])}")

    return EXIT_SUCCESS


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage audit-loop state files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Initialize new audit state")
    p_create.add_argument("artifact", help="Path to artifact being audited")
    p_create.add_argument("--force", "-f", action="store_true", help="Overwrite existing state")
    p_create.set_defaults(func=cmd_create)

    # read
    p_read = subparsers.add_parser("read", help="Display current state")
    p_read.add_argument("artifact", help="Path to artifact being audited")
    p_read.set_defaults(func=cmd_read)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

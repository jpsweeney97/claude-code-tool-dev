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


def update_state(
    artifact_path: Path,
    phase: str | None = None,
    add_finding: dict[str, Any] | None = None,
    next_cycle: bool = False,
    calibration: dict[str, Any] | None = None,
) -> Result:
    """
    Update audit state.

    Args:
        artifact_path: Path to the artifact being audited
        phase: New phase value
        add_finding: Finding dict to add (auto-generates ID)
        next_cycle: Increment cycle counter
        calibration: Calibration data to set

    Returns:
        Result with updated state
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    state_path = Path(read_result.data["state_path"])
    now = datetime.now(timezone.utc).isoformat()
    events = []

    # Update phase
    if phase is not None:
        if phase not in PHASES:
            return Result.failure(
                f"Invalid phase: {phase}",
                errors=[f"Valid phases: {', '.join(PHASES)}"],
            )
        old_phase = state["phase"]
        state["phase"] = phase
        events.append({
            "timestamp": now,
            "event": "phase_changed",
            "data": {"from": old_phase, "to": phase},
        })

    # Add finding
    if add_finding is not None:
        # Generate next finding ID
        existing_ids = [f["id"] for f in state["findings"]]
        next_num = 1
        while f"F{next_num}" in existing_ids:
            next_num += 1
        finding_id = f"F{next_num}"

        finding = {
            "id": finding_id,
            "description": add_finding.get("description", ""),
            "confidence": add_finding.get("confidence", "unknown"),
            "priority": add_finding.get("priority", "medium"),
            "evidence": add_finding.get("evidence", ""),
            "status": "open",
            "resolution": None,
        }
        state["findings"].append(finding)
        events.append({
            "timestamp": now,
            "event": "finding_added",
            "data": {"id": finding_id},
        })

    # Next cycle
    if next_cycle:
        if state["cycle"] >= MAX_CYCLES:
            return Result.failure(
                f"Cycle limit reached ({MAX_CYCLES})",
                errors=["Cannot exceed maximum cycles. Consider archiving this audit."],
            )
        state["cycle"] += 1
        events.append({
            "timestamp": now,
            "event": "cycle_started",
            "data": {"cycle": state["cycle"]},
        })

    # Set calibration
    if calibration is not None:
        state["calibration"] = calibration
        events.append({
            "timestamp": now,
            "event": "calibration_set",
            "data": calibration,
        })

    # Update timestamp and history
    state["updated"] = now
    state["history"].extend(events)

    try:
        atomic_write(state_path, json.dumps(state, indent=2))
        return Result.success(
            f"Updated state: {state_path}",
            data={"state_path": str(state_path), "state": state},
        )
    except OSError as e:
        return Result.failure(
            f"Failed to write state: {e}",
            errors=[str(e)],
        )


def validate_state(artifact_path: Path) -> Result:
    """
    Validate audit state integrity.

    Checks:
        - State file exists and is valid JSON
        - Required fields present
        - Phase is valid
        - Cycle is within limits
        - Finding IDs are unique

    Returns:
        Result with validation details
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    errors = []
    warnings = []

    # Check required fields
    required = ["version", "artifact", "phase", "cycle", "findings"]
    for field in required:
        if field not in state:
            errors.append(f"Missing required field: {field}")

    if errors:
        return Result.failure(
            "State validation failed",
            errors=errors,
        )

    # Check phase validity
    if state["phase"] not in PHASES:
        errors.append(f"Invalid phase: {state['phase']}")

    # Check cycle limits
    if state["cycle"] > MAX_CYCLES:
        errors.append(f"Cycle {state['cycle']} exceeds limit {MAX_CYCLES}")

    # Check finding ID uniqueness
    finding_ids = [f["id"] for f in state["findings"]]
    if len(finding_ids) != len(set(finding_ids)):
        errors.append("Duplicate finding IDs detected")

    if errors:
        return Result.failure(
            "State validation failed",
            errors=errors,
            data={"state": state},
        )

    return Result.success(
        "State is valid",
        data={"state": state},
        warnings=warnings,
    )


def list_audits(directory: Path) -> Result:
    """
    Find all active audits in a directory.

    Args:
        directory: Directory to search (non-recursive)

    Returns:
        Result with list of audit info
    """
    directory = Path(directory)
    if not directory.is_dir():
        return Result.failure(
            f"Not a directory: {directory}",
            errors=[str(directory)],
        )

    audits = []
    for state_path in directory.glob("*.audit.json"):
        # Skip archived audits (have date suffix before .json)
        name = state_path.stem  # e.g., "feature.audit"
        if name.count(".") > 1:
            continue  # Looks like "feature.audit.2026-01-06"

        try:
            state = json.loads(state_path.read_text())
            audits.append({
                "state_path": str(state_path),
                "artifact": state.get("artifact", "unknown"),
                "phase": state.get("phase", "unknown"),
                "cycle": state.get("cycle", 0),
                "findings": len(state.get("findings", [])),
            })
        except (json.JSONDecodeError, OSError):
            audits.append({
                "state_path": str(state_path),
                "error": "Failed to read state",
            })

    return Result.success(
        f"Found {len(audits)} active audit(s)",
        data={"audits": audits},
    )


def archive_audit(artifact_path: Path, date_str: str | None = None) -> Result:
    """
    Archive completed audit by renaming state file with date suffix.

    Args:
        artifact_path: Path to the artifact
        date_str: Date string for archive (default: today)

    Returns:
        Result with archive path
    """
    state_path = get_state_path(artifact_path)

    if not state_path.exists():
        return Result.failure(
            f"No audit state found: {state_path}",
            errors=["Nothing to archive"],
        )

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    archive_path = get_archive_path(artifact_path, date_str)

    try:
        # Read state, add archived event
        state = json.loads(state_path.read_text())
        now = datetime.now(timezone.utc).isoformat()
        state["history"].append({
            "timestamp": now,
            "event": "archived",
            "data": {"archive_path": str(archive_path)},
        })

        # Write to archive location
        atomic_write(archive_path, json.dumps(state, indent=2))

        # Remove original
        state_path.unlink()

        return Result.success(
            f"Archived to: {archive_path}",
            data={"archive_path": str(archive_path)},
        )
    except OSError as e:
        return Result.failure(
            f"Archive failed: {e}",
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


def cmd_update(args: argparse.Namespace) -> int:
    """Handle update subcommand."""
    add_finding = None
    if args.add_finding:
        # Parse finding from comma-separated key=value pairs
        finding = {}
        for pair in args.add_finding.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                finding[key.strip()] = value.strip()
        add_finding = finding

    result = update_state(
        Path(args.artifact),
        phase=args.phase,
        add_finding=add_finding,
        next_cycle=args.next_cycle,
    )

    if args.json:
        print(result.to_json())
    else:
        print(result.message)

    return EXIT_SUCCESS if result.ok else EXIT_ERROR


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle validate subcommand."""
    result = validate_state(Path(args.artifact))
    if args.json:
        print(result.to_json())
    else:
        print(result.message)
        for error in result.errors:
            print(f"  - {error}")

    return EXIT_SUCCESS if result.ok else EXIT_VALIDATION


def cmd_list(args: argparse.Namespace) -> int:
    """Handle list subcommand."""
    directory = Path(args.directory) if args.directory else Path.cwd()
    result = list_audits(directory)

    if args.json:
        print(result.to_json())
    else:
        print(result.message)
        for audit in result.data["audits"]:
            if "error" in audit:
                print(f"  - {audit['state_path']}: {audit['error']}")
            else:
                print(f"  - {Path(audit['artifact']).name}: {audit['phase']} (cycle {audit['cycle']}, {audit['findings']} findings)")

    return EXIT_SUCCESS if result.ok else EXIT_ERROR


def cmd_archive(args: argparse.Namespace) -> int:
    """Handle archive subcommand."""
    result = archive_audit(Path(args.artifact), args.date)

    if args.json:
        print(result.to_json())
    else:
        print(result.message)

    return EXIT_SUCCESS if result.ok else EXIT_ERROR


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

    # update
    p_update = subparsers.add_parser("update", help="Modify state fields")
    p_update.add_argument("artifact", help="Path to artifact being audited")
    p_update.add_argument("--phase", help="Set phase")
    p_update.add_argument("--add-finding", help="Add finding: description=...,priority=...,confidence=...")
    p_update.add_argument("--next-cycle", action="store_true", help="Increment cycle")
    p_update.set_defaults(func=cmd_update)

    # validate
    p_validate = subparsers.add_parser("validate", help="Check state integrity")
    p_validate.add_argument("artifact", help="Path to artifact being audited")
    p_validate.set_defaults(func=cmd_validate)

    # list
    p_list = subparsers.add_parser("list", help="Find active audits")
    p_list.add_argument("directory", nargs="?", help="Directory to search (default: cwd)")
    p_list.set_defaults(func=cmd_list)

    # archive
    p_archive = subparsers.add_parser("archive", help="Archive completed audit")
    p_archive.add_argument("artifact", help="Path to artifact being audited")
    p_archive.add_argument("--date", help="Date suffix (default: today)")
    p_archive.set_defaults(func=cmd_archive)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

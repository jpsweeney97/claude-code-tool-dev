#!/usr/bin/env python3
"""
Pre-operation validation for audit-loop.

Usage:
    python validate_state.py <artifact>                      # Basic validation
    python validate_state.py <artifact> --for ship           # Exit criteria check
    python validate_state.py <artifact> --for iterate        # Cycle limit check
    python validate_state.py <artifact> --for phase --target definition

Exit codes:
    0  - Validation passed
    10 - Validation failed
    11 - State not found
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import (
    EXIT_NOT_FOUND,
    EXIT_SUCCESS,
    EXIT_VALIDATION,
    MAX_CYCLES,
    PHASES,
    Result,
)
from state import read_state, validate_state


def validate_for_ship(artifact_path: Path) -> Result:
    """
    Validate state meets ship criteria.

    Criteria:
        - No open high-priority findings
        - For deep calibration: no open medium-priority findings

    Returns:
        Result indicating if ship is allowed
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    findings = state.get("findings", [])
    calibration = state.get("calibration", {})
    level = calibration.get("level", "medium") if calibration else "medium"

    open_high = [f for f in findings if f.get("status") == "open" and f.get("priority") == "high"]
    open_medium = [f for f in findings if f.get("status") == "open" and f.get("priority") == "medium"]

    errors = []

    if open_high:
        errors.append(f"{len(open_high)} open high-priority finding(s): {', '.join(f['id'] for f in open_high)}")

    if level == "deep" and open_medium:
        errors.append(f"{len(open_medium)} open medium-priority finding(s) (required for deep calibration)")

    if errors:
        return Result.failure(
            "Ship criteria not met",
            errors=errors,
            data={"open_high": len(open_high), "open_medium": len(open_medium)},
        )

    return Result.success(
        "Ship criteria met",
        data={"findings_addressed": len([f for f in findings if f.get("status") == "addressed"])},
    )


def validate_for_iterate(artifact_path: Path) -> Result:
    """
    Validate state allows another iteration.

    Criteria:
        - Current cycle < MAX_CYCLES

    Returns:
        Result indicating if iteration is allowed
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    cycle = state.get("cycle", 1)

    if cycle >= MAX_CYCLES:
        return Result.failure(
            f"Cycle limit reached ({MAX_CYCLES})",
            errors=["Consider archiving this audit and starting fresh if more iterations needed"],
        )

    return Result.success(
        f"Iteration allowed (cycle {cycle} of {MAX_CYCLES})",
        data={"current_cycle": cycle, "max_cycles": MAX_CYCLES},
    )


def validate_for_phase(artifact_path: Path, target_phase: str) -> Result:
    """
    Validate state allows transition to target phase.

    Returns:
        Result indicating if phase transition is allowed
    """
    if target_phase not in PHASES:
        return Result.failure(
            f"Invalid target phase: {target_phase}",
            errors=[f"Valid phases: {', '.join(PHASES)}"],
        )

    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    current = state.get("phase", "stakes_assessment")

    current_idx = PHASES.index(current) if current in PHASES else 0
    target_idx = PHASES.index(target_phase)

    # Allow forward transitions or same phase
    if target_idx >= current_idx:
        return Result.success(
            f"Phase transition allowed: {current} → {target_phase}",
        )

    # Backward transitions only allowed for iterate/expand
    if target_phase in ("execution", "definition"):
        return Result.success(
            f"Phase transition allowed (iteration): {current} → {target_phase}",
        )

    return Result.failure(
        f"Invalid phase transition: {current} → {target_phase}",
        errors=["Backward transitions only allowed for iteration"],
    )


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate audit state for operations."
    )
    parser.add_argument("artifact", help="Path to artifact being audited")
    parser.add_argument("--for", dest="operation", choices=["ship", "iterate", "phase"], help="Validation mode")
    parser.add_argument("--target-phase", help="Target phase (with --for phase)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args(argv)
    artifact = Path(args.artifact)

    if args.operation == "ship":
        result = validate_for_ship(artifact)
    elif args.operation == "iterate":
        result = validate_for_iterate(artifact)
    elif args.operation == "phase":
        if not args.target_phase:
            parser.error("--target-phase required with --for phase")
        result = validate_for_phase(artifact, args.target_phase)
    else:
        result = validate_state(artifact)

    if args.json:
        print(result.to_json())
    else:
        print(result.message)
        for error in result.errors:
            print(f"  - {error}")

    return EXIT_SUCCESS if result.ok else EXIT_VALIDATION if result.errors else EXIT_NOT_FOUND


if __name__ == "__main__":
    sys.exit(main())

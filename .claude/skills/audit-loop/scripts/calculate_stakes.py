#!/usr/bin/env python3
"""
Calculate calibration level from stakes assessment.

Usage:
    python calculate_stakes.py <rev> <blast> <prec> <vis>    # Direct values (1-3 each)
    python calculate_stakes.py --interactive                  # Guided prompts
    python calculate_stakes.py --json <rev> <blast> <prec> <vis>  # JSON output

Exit codes:
    0 - Success
    2 - Invalid arguments
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TypedDict


class CalibrationResult(TypedDict):
    """Calibration calculation result."""

    stakes: dict[str, int]
    score: int
    level: str


def calculate_calibration(
    reversibility: int,
    blast_radius: int,
    precedent: int,
    visibility: int,
) -> CalibrationResult:
    """
    Calculate calibration level from stakes values.

    Args:
        reversibility: 1=easy to undo, 2=moderate, 3=permanent
        blast_radius: 1=just you, 2=team, 3=users/org
        precedent: 1=one-off, 2=may be referenced, 3=sets pattern
        visibility: 1=internal, 2=shared, 3=public

    Returns:
        CalibrationResult with stakes, score, and level
    """
    score = reversibility + blast_radius + precedent + visibility

    if score <= 6:
        level = "light"
    elif score <= 9:
        level = "medium"
    else:
        level = "deep"

    return {
        "stakes": {
            "reversibility": reversibility,
            "blast_radius": blast_radius,
            "precedent": precedent,
            "visibility": visibility,
        },
        "score": score,
        "level": level,
    }


def validate_value(value: int, name: str) -> None:
    """Validate stake value is 1-3."""
    if value < 1 or value > 3:
        raise ValueError(f"{name} must be 1-3, got {value}")


def interactive_mode() -> CalibrationResult:
    """Run interactive stakes assessment."""
    print("Stakes Assessment\n")

    prompts = [
        ("Reversibility", "If this design is wrong, how hard to fix?\n  [1] Easy to undo\n  [2] Moderate effort\n  [3] Permanent/very costly"),
        ("Blast radius", "Who's affected if it fails?\n  [1] Just you\n  [2] Your team\n  [3] Users or organization"),
        ("Precedent", "Will this be referenced later?\n  [1] One-off\n  [2] May be referenced\n  [3] Sets a pattern"),
        ("Visibility", "Who will see this?\n  [1] Internal only\n  [2] Shared with others\n  [3] Public"),
    ]

    values = []
    for name, prompt in prompts:
        print(f"\n{prompt}")
        while True:
            try:
                value = int(input(f"{name}: "))
                validate_value(value, name)
                values.append(value)
                break
            except ValueError as e:
                print(f"  Invalid: {e}")

    return calculate_calibration(*values)


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate calibration level from stakes assessment."
    )
    parser.add_argument(
        "values",
        nargs="*",
        type=int,
        metavar="VALUE",
        help="Stakes values: reversibility blast_radius precedent visibility (1-3 each)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run interactive assessment",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args(argv)

    try:
        if args.interactive:
            result = interactive_mode()
        elif len(args.values) == 4:
            for i, (val, name) in enumerate(zip(
                args.values,
                ["reversibility", "blast_radius", "precedent", "visibility"],
            )):
                validate_value(val, name)
            result = calculate_calibration(*args.values)
        else:
            parser.error("Provide 4 values or use --interactive")
            return 2

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Calibration: {result['level']} (score {result['score']})")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

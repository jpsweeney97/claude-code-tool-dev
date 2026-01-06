#!/usr/bin/env python3
"""
Generate markdown audit report from state.

Usage:
    python generate_report.py <artifact>           # Output to stdout
    python generate_report.py <artifact> --save    # Save to dated file

Exit codes:
    0  - Success
    1  - Error
    11 - State not found
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from _common import (
    EXIT_ERROR,
    EXIT_NOT_FOUND,
    EXIT_SUCCESS,
    Result,
    atomic_write,
    get_report_path,
)
from state import read_state


def generate_report(artifact_path: Path) -> Result:
    """
    Generate markdown report from audit state.

    Args:
        artifact_path: Path to the artifact being audited

    Returns:
        Result with report markdown in data
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    lines = []

    # Header
    lines.append("# Audit Report")
    lines.append("")
    lines.append(f"**Artifact:** {Path(state['artifact']).name}")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

    if state.get("calibration"):
        cal = state["calibration"]
        lines.append(f"**Calibration:** {cal['level']} (score {cal['score']})")

    lines.append(f"**Cycles:** {state['cycle']}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    findings = state.get("findings", [])
    high = sum(1 for f in findings if f.get("priority") == "high")
    medium = sum(1 for f in findings if f.get("priority") == "medium")
    low = sum(1 for f in findings if f.get("priority") == "low")
    lines.append(f"Found **{len(findings)}** findings: {high} high, {medium} medium, {low} low priority.")
    lines.append("")

    # Scope
    definition = state.get("definition", {})
    if definition.get("scope"):
        lines.append("## Scope")
        lines.append("")
        lines.append("**Examined:**")
        for item in definition["scope"]:
            lines.append(f"- {item}")
        lines.append("")

    if definition.get("excluded"):
        lines.append("**Excluded:**")
        for item in definition["excluded"]:
            lines.append(f"- {item}")
        if definition.get("excluded_rationale"):
            lines.append(f"\n*Rationale:* {definition['excluded_rationale']}")
        lines.append("")

    # Findings
    if findings:
        lines.append("## Findings")
        lines.append("")
        lines.append("| ID | Description | Priority | Confidence | Status |")
        lines.append("|----|-------------|----------|------------|--------|")
        for f in findings:
            status = f.get("status", "open")
            status_icon = "✅" if status == "addressed" else "🔄" if status == "partial" else "⚪"
            lines.append(
                f"| {f['id']} | {f['description'][:50]} | {f.get('priority', '-')} | {f.get('confidence', '-')} | {status_icon} {status} |"
            )
        lines.append("")

        # Finding details
        lines.append("### Finding Details")
        lines.append("")
        for f in findings:
            lines.append(f"#### {f['id']}: {f['description']}")
            lines.append("")
            if f.get("evidence"):
                lines.append(f"**Evidence:** {f['evidence']}")
            if f.get("resolution"):
                lines.append(f"**Resolution:** {f['resolution']}")
            lines.append("")

    # Verification
    verification = state.get("verification", {})
    if verification.get("limitations"):
        lines.append("## Limitations")
        lines.append("")
        for item in verification["limitations"]:
            lines.append(f"- {item}")
        lines.append("")

    if verification.get("counter_conclusion"):
        lines.append("## Counter-Conclusion")
        lines.append("")
        lines.append(verification["counter_conclusion"])
        lines.append("")

    # Audit Trail
    lines.append("## Audit Trail")
    lines.append("")
    for event in state.get("history", [])[-10:]:  # Last 10 events
        lines.append(f"- **{event['timestamp'][:10]}** {event['event']}")
    lines.append("")

    report = "\n".join(lines)
    return Result.success(
        "Report generated",
        data={"report": report},
    )


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate markdown audit report from state."
    )
    parser.add_argument("artifact", help="Path to artifact being audited")
    parser.add_argument("--save", action="store_true", help="Save to dated file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args(argv)
    artifact = Path(args.artifact)

    result = generate_report(artifact)

    if not result.ok:
        if args.json:
            print(result.to_json())
        else:
            print(result.message, file=sys.stderr)
        return EXIT_NOT_FOUND

    if args.save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_path = get_report_path(artifact, date_str)
        try:
            atomic_write(report_path, result.data["report"])
            print(f"Saved: {report_path}")
        except OSError as e:
            print(f"Failed to save: {e}", file=sys.stderr)
            return EXIT_ERROR
    elif args.json:
        print(result.to_json())
    else:
        print(result.data["report"])

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())

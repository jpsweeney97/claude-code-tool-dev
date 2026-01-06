#!/usr/bin/env python3
"""
Export and import claims to/from portable formats.

Supports JSON and CSV formats for claim data portability.

Exit codes:
    0 - Success
    1 - Input error
    2 - Import conflict (use --force to override)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from io import StringIO
from pathlib import Path

from match_claim import parse_known_claims, discover_sections


# Type alias for claim dict
ClaimDict = dict[str, str | None]


@dataclass
class ExportResult:
    """Result of export operation."""
    format: str
    count: int
    sections: list[str]
    output_path: Path | None


@dataclass
class ImportResult:
    """Result of import operation."""
    added: int
    skipped: int
    conflicts: list[str]


def export_to_json(claims: list[ClaimDict]) -> str:
    """Export claims to JSON format."""
    data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "count": len(claims),
        "claims": [
            {
                "claim": c["claim"],
                "section": c["section"],
                "verdict": c["verdict"],
                "evidence": c["evidence"],
                "verified_date": c.get("verified_date", ""),
            }
            for c in claims
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def export_to_csv(claims: list[ClaimDict]) -> str:
    """Export claims to CSV format."""
    output = StringIO()
    writer = csv.writer(output, lineterminator='\n')

    # Header
    writer.writerow(["claim", "section", "verdict", "evidence", "verified_date"])

    # Data
    for c in claims:
        writer.writerow([c["claim"], c["section"], c["verdict"], c["evidence"], c.get("verified_date", "")])

    return output.getvalue()


def export_claims(
    known_path: Path,
    format: str = "json",
    section_filter: str | None = None,
) -> tuple[str, ExportResult]:
    """
    Export claims to specified format.

    Args:
        known_path: Path to known-claims.md
        format: Output format ('json' or 'csv')
        section_filter: Only export claims from this section

    Returns:
        Tuple of (content_string, ExportResult)
    """
    if not known_path.exists():
        return "", ExportResult(format=format, count=0, sections=[], output_path=None)

    claims = parse_known_claims(known_path)

    # Filter by section if requested
    if section_filter:
        section_lower = section_filter.lower()
        claims = [c for c in claims if c["section"].lower() == section_lower]

    sections = sorted(set(c["section"] for c in claims if c["section"]))

    if format == "csv":
        content = export_to_csv(claims)
    else:
        content = export_to_json(claims)

    result = ExportResult(
        format=format,
        count=len(claims),
        sections=sections,
        output_path=None,
    )

    return content, result


def parse_json_import(content: str) -> list[ClaimDict]:
    """Parse claims from JSON format."""
    data = json.loads(content)
    claims = []

    for item in data.get("claims", []):
        claims.append({
            "claim": item["claim"],
            "section": item["section"],
            "verdict": item["verdict"],
            "evidence": item["evidence"],
            "verified_date": item.get("verified_date", ""),
        })

    return claims


def parse_csv_import(content: str) -> list[ClaimDict]:
    """Parse claims from CSV format."""
    reader = csv.DictReader(StringIO(content))
    claims = []

    for row in reader:
        claims.append({
            "claim": row["claim"],
            "section": row["section"],
            "verdict": row["verdict"],
            "evidence": row["evidence"],
            "verified_date": row.get("verified_date", ""),
        })

    return claims


def find_import_conflicts(
    existing: list[ClaimDict],
    incoming: list[ClaimDict],
) -> list[tuple[ClaimDict, ClaimDict]]:
    """Find claims that exist in both sets with different data."""
    conflicts = []

    existing_map = {(c["claim"].lower(), c["section"]): c for c in existing}

    for inc in incoming:
        key = (inc["claim"].lower(), inc["section"])
        if key in existing_map:
            exist = existing_map[key]
            # Conflict if verdict or evidence differs
            if exist["verdict"] != inc["verdict"] or exist["evidence"] != inc["evidence"]:
                conflicts.append((exist, inc))

    return conflicts


def import_claims(
    known_path: Path,
    import_content: str,
    format: str = "json",
    force: bool = False,
    dry_run: bool = False,
) -> ImportResult:
    """
    Import claims from portable format.

    Args:
        known_path: Path to known-claims.md
        import_content: Content string to import
        format: Import format ('json' or 'csv')
        force: Overwrite conflicts without prompting
        dry_run: Preview without writing

    Returns:
        ImportResult with counts
    """
    # Parse incoming claims
    if format == "csv":
        incoming = parse_csv_import(import_content)
    else:
        incoming = parse_json_import(import_content)

    # Load existing claims
    existing = parse_known_claims(known_path) if known_path.exists() else []

    # Find conflicts
    conflicts = find_import_conflicts(existing, incoming)
    conflict_messages = [
        f"[{c[0]['section']}] {c[0]['claim']}: {c[0]['verdict']} vs {c[1]['verdict']}"
        for c in conflicts
    ]

    if conflicts and not force:
        return ImportResult(added=0, skipped=len(conflicts), conflicts=conflict_messages)

    # Calculate what would be added (excluding exact duplicates)
    existing_keys = {(c["claim"].lower(), c["section"]) for c in existing}
    new_claims = [c for c in incoming if (c["claim"].lower(), c["section"]) not in existing_keys]

    if dry_run:
        return ImportResult(
            added=len(new_claims),
            skipped=len(incoming) - len(new_claims),
            conflicts=conflict_messages,
        )

    # Actually import: append new claims to pending-claims.md
    # (They go through normal promotion flow)
    pending_path = known_path.parent / "pending-claims.md"

    if new_claims:
        lines = []
        for c in new_claims:
            lines.append(f"## {c['section']}\n")
            lines.append(f"| {c['claim']} | {c['verdict']} | {c['evidence']} | (imported) |\n")

        with open(pending_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))

    return ImportResult(
        added=len(new_claims),
        skipped=len(incoming) - len(new_claims),
        conflicts=conflict_messages if force else [],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Export/import claims")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export claims")
    export_parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
    )
    export_parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format",
    )
    export_parser.add_argument(
        "--section",
        help="Only export this section",
    )
    export_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (stdout if omitted)",
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import claims")
    import_parser.add_argument(
        "input",
        type=Path,
        help="File to import",
    )
    import_parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
    )
    import_parser.add_argument(
        "--format",
        choices=["json", "csv"],
        help="Input format (auto-detected from extension if omitted)",
    )
    import_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite conflicts",
    )
    import_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing",
    )

    args = parser.parse_args()

    if args.command == "export":
        content, result = export_claims(
            args.known_claims,
            format=args.format,
            section_filter=args.section,
        )

        if args.output:
            args.output.write_text(content, encoding="utf-8")
            print(f"Exported {result.count} claims to {args.output}")
        else:
            print(content)

        return 0

    elif args.command == "import":
        if not args.input.exists():
            print(f"Error: {args.input} not found", file=sys.stderr)
            return 1

        # Auto-detect format from extension
        format = args.format
        if not format:
            if args.input.suffix == ".csv":
                format = "csv"
            else:
                format = "json"

        content = args.input.read_text(encoding="utf-8")
        result = import_claims(
            args.known_claims,
            content,
            format=format,
            force=args.force,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            print("[DRY RUN]")

        print(f"Added: {result.added}")
        print(f"Skipped: {result.skipped}")

        if result.conflicts:
            print(f"\nConflicts ({len(result.conflicts)}):")
            for c in result.conflicts:
                print(f"  ⚠️ {c}")
            if not args.force and not args.dry_run:
                print("\nUse --force to override conflicts")
                return 2

        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Ticket reading, status normalization, and orphan detection for /triage skill.

Phase 0: read-only. Produces JSON report.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from scripts.ticket_parsing import parse_ticket
    from scripts.provenance import read_provenance, session_matches
    from scripts.handoff_parsing import parse_frontmatter, parse_sections
    from scripts.project_paths import get_handoffs_dir, get_archive_dir
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.ticket_parsing import parse_ticket  # type: ignore[no-redef]
    from scripts.provenance import read_provenance, session_matches  # type: ignore[no-redef]
    from scripts.handoff_parsing import parse_frontmatter, parse_sections  # type: ignore[no-redef]
    from scripts.project_paths import get_handoffs_dir, get_archive_dir  # type: ignore[no-redef]

# 6-state enum
_CANONICAL_STATUSES = {"deferred", "open", "in_progress", "blocked", "done", "wontfix"}
_TERMINAL_STATUSES = {"done", "wontfix"}

_NORMALIZATION_MAP: dict[str, tuple[str, str]] = {
    "complete": ("done", "high"),
    "implemented": ("done", "high"),
    "closed": ("done", "medium"),
    "planning": ("open", "medium"),
    "implementing": ("in_progress", "high"),
}


def normalize_status(raw: str) -> tuple[str, str]:
    """Normalize a ticket status to the 6-state enum.

    Returns (normalized_status, confidence) where confidence is high/medium/low.
    """
    if raw in _CANONICAL_STATUSES:
        return raw, "high"
    if raw in _NORMALIZATION_MAP:
        return _NORMALIZATION_MAP[raw]
    return "open", "low"


def read_open_tickets(tickets_dir: Path) -> list[dict[str, Any]]:
    """Read all non-terminal tickets from a directory.

    Returns list of dicts with: id, date, priority, status_raw,
    status_normalized, normalization_confidence, summary, path.
    """
    if not tickets_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for path in sorted(tickets_dir.glob("*.md")):
        ticket = parse_ticket(path)
        if ticket is None:
            continue

        fm = ticket.frontmatter
        raw_status = str(fm.get("status", "open"))
        norm_status, confidence = normalize_status(raw_status)

        if norm_status in _TERMINAL_STATUSES:
            continue

        results.append({
            "id": fm["id"],
            "date": fm.get("date", ""),
            "priority": fm.get("priority", "medium"),
            "status_raw": raw_status,
            "status_normalized": norm_status,
            "normalization_confidence": confidence,
            "summary": str(path.stem),
            "path": str(path),
        })

    return results

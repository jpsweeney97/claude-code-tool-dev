"""Ticket reading, status normalization, and orphan detection for /triage skill.

Phase 0: read-only. Produces JSON report.
"""
from __future__ import annotations

import re
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


# Ticket ID patterns — union of new + legacy formats
_TICKET_ID_PATTERNS = [
    r"T-\d{8}-\d{2}",      # new: T-20260228-01
    r"T-\d{3}",             # legacy numeric: T-004
    r"T-[A-F]",             # legacy alpha: T-A (P3-5: covers current A-F corpus only)
    r"handoff-[\w-]+",      # P1-11 fix: legacy noun — supports hyphens (handoff-quality-hook)
]
_TICKET_ID_RE = re.compile(r"\b(?:" + "|".join(_TICKET_ID_PATTERNS) + r")\b")

_LIST_ITEM_RE = re.compile(r"^[-*]\s+(.+)$|^(\d+)\.\s+(.+)$", re.MULTILINE)


def _section_name(heading: str) -> str:
    """Strip the '## ' prefix from a section heading.

    parse_sections stores headings as '## Open Questions' (with prefix).
    Matches the pattern in distill.py:_section_name.
    """
    if heading.startswith("## "):
        return heading[3:].strip()
    return heading.strip()


def extract_handoff_items(
    handoff_text: str, handoff_filename: str
) -> tuple[list[dict[str, Any]], int]:
    """Extract structured list items from Open Questions and Risks sections.

    Returns (items, skipped_prose_count).
    Only extracts lines starting with - or numbered items.
    Skips prose paragraphs (counted via skipped_prose_count).
    Skips handoffs without these sections.

    Note: uid_match based on session_id is a session-level correlation signal,
    not an item-level match. All items from the same handoff share the same
    session_id, so a uid_match means "this handoff produced a ticket", not
    "this specific item was deferred." (P1-2)
    """
    # P0-1 fix: parse_frontmatter returns tuple[dict, str], not dict
    fm, body = parse_frontmatter(handoff_text)
    session_id = fm.get("session_id", "")

    # P0-1 fix: use body (frontmatter stripped) for parse_sections
    sections = parse_sections(body)
    target_sections = {"Open Questions", "Risks"}

    items: list[dict[str, Any]] = []
    skipped_prose_count = 0
    for section in sections:
        # P0-2 fix: strip '## ' prefix before comparison
        name = _section_name(section.heading)
        if name not in target_sections:
            continue
        for line in section.content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            m = _LIST_ITEM_RE.match(line)
            if m:
                text = m.group(1) or m.group(3) or ""
                text = text.strip()
                if text:
                    items.append({
                        "text": text,
                        "section": name,
                        "session_id": session_id,
                        "handoff": handoff_filename,
                    })
            else:
                # P1-4: count skipped prose lines
                skipped_prose_count += 1
    return items, skipped_prose_count


def _load_tickets_for_matching(tickets_dir: Path) -> list[dict[str, Any]]:
    """Load all tickets with their provenance for matching."""
    results: list[dict[str, Any]] = []
    if not tickets_dir.exists():
        return results

    for path in sorted(tickets_dir.glob("*.md")):  # P2-10 fix: deterministic iteration order
        ticket = parse_ticket(path)
        if ticket is None:
            continue

        fm = ticket.frontmatter
        prov = read_provenance(
            provenance_yaml=fm.get("provenance"),
            body_text=ticket.body,
        )
        results.append({
            "id": fm["id"],
            "provenance": prov,
            "path": str(path),
        })
    return results


def match_orphan_item(
    item: dict[str, Any],
    tickets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Match a handoff item against existing tickets.

    Returns dict with match_type (uid_match, id_ref, manual_review)
    and matched_ticket (if matched).
    """
    # Strategy 1: UID match — session_id → provenance.source_session
    for ticket in tickets:
        prov = ticket.get("provenance")
        if prov and session_matches(prov.get("source_session"), item.get("session_id")):
            return {
                "match_type": "uid_match",
                "matched_ticket": ticket["id"],
                "item": item,
            }

    # Strategy 2: Ticket ID reference in item text
    found_ids = set(_TICKET_ID_RE.findall(item.get("text", "")))
    ticket_ids = {t["id"] for t in tickets}
    matched = found_ids & ticket_ids
    if matched:
        return {
            "match_type": "id_ref",
            "matched_ticket": sorted(matched)[0],  # P2-7 fix: deterministic alphabetic order
            "item": item,
        }

    # Strategy 3: Manual review
    return {
        "match_type": "manual_review",
        "matched_ticket": None,
        "item": item,
    }

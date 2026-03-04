"""Ticket triage — read-only analysis of ticket health and audit activity."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


_TERMINAL_STATUSES = frozenset({"done", "wontfix"})


def triage_dashboard(tickets_dir: Path) -> dict[str, Any]:
    """Generate a triage dashboard with ticket counts and alerts.

    Filters to non-terminal statuses (excludes done/wontfix).
    list_tickets(include_closed=False) returns all tickets in the active
    directory regardless of status field — filtering by status is our job.
    Returns dict with: counts, total, stale, blocked_chains, size_warnings.
    """
    from scripts.ticket_read import list_tickets

    all_tickets = list_tickets(tickets_dir, include_closed=False)
    # Filter to actionable tickets (non-terminal status).
    tickets = [t for t in all_tickets if t.status not in _TERMINAL_STATUSES]
    ticket_map = {t.id: t for t in tickets}

    counts: dict[str, int] = {"open": 0, "in_progress": 0, "blocked": 0}
    stale: list[dict[str, str]] = []
    blocked_chains: list[dict[str, Any]] = []
    size_warnings: list[dict[str, str]] = []

    for ticket in tickets:
        if ticket.status in counts:
            counts[ticket.status] += 1

        if _is_stale(ticket):
            stale.append({"id": ticket.id, "status": ticket.status, "date": ticket.date})

        if ticket.status == "blocked" and ticket.blocked_by:
            root_blockers = _find_root_blockers(ticket, ticket_map)
            blocked_chains.append({"id": ticket.id, "root_blockers": root_blockers})

        warning = _check_doc_size(ticket)
        if warning:
            size_warnings.append({"id": ticket.id, "warning": warning})

    return {
        "counts": counts,
        "total": len(tickets),
        "stale": stale,
        "blocked_chains": blocked_chains,
        "size_warnings": size_warnings,
    }


def _is_stale(ticket: Any, cutoff_days: int = 7) -> bool:
    """Check if ticket is stale (open/in_progress >7 days by ticket date)."""
    if ticket.status not in ("open", "in_progress"):
        return False
    try:
        ticket_date = datetime.strptime(ticket.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ticket_date).days > cutoff_days
    except ValueError:
        return False


def _find_root_blockers(ticket: Any, ticket_map: dict[str, Any]) -> list[str]:
    """Follow blocked_by chains to find root blockers."""
    visited: set[str] = set()
    roots: list[str] = []

    def _walk(tid: str) -> None:
        if tid in visited:
            return
        visited.add(tid)
        t = ticket_map.get(tid)
        if t is None or not t.blocked_by:
            roots.append(tid)
            return
        for bid in t.blocked_by:
            _walk(bid)

    for bid in ticket.blocked_by:
        _walk(bid)
    return roots


def _check_doc_size(ticket: Any) -> str | None:
    """Check ticket document size, return warning string if large."""
    try:
        size = Path(ticket.path).stat().st_size
    except OSError:
        return None
    if size >= 32768:
        return f"strong_warn: {size // 1024}KB (>32KB)"
    if size >= 16384:
        return f"warn: {size // 1024}KB (>16KB)"
    return None


def triage_audit_report(tickets_dir: Path, days: int = 7) -> dict[str, Any]:
    """Summarize recent autonomous actions from audit trail.

    Reads .audit/YYYY-MM-DD/<session_id>.jsonl files within the lookback window.
    Returns dict with: total_entries, by_action, by_result, sessions.
    """
    audit_base = tickets_dir / ".audit"
    if not audit_base.is_dir():
        return {"total_entries": 0, "by_action": {}, "by_result": {}, "sessions": 0}

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries: list[dict[str, Any]] = []
    session_ids: set[str] = set()

    for date_dir in sorted(audit_base.iterdir()):
        if not date_dir.is_dir():
            continue
        try:
            dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if dir_date < cutoff:
            continue
        for jsonl_file in date_dir.glob("*.jsonl"):
            session_ids.add(jsonl_file.stem)
            try:
                for line in jsonl_file.read_text(encoding="utf-8").strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        entries.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        continue
            except OSError:
                continue

    by_action: dict[str, int] = {}
    by_result: dict[str, int] = {}
    for entry in entries:
        action = entry.get("action", "unknown")
        by_action[action] = by_action.get(action, 0) + 1
        result = entry.get("result")
        if result is not None:
            by_result[str(result)] = by_result.get(str(result), 0) + 1

    return {
        "total_entries": len(entries),
        "by_action": by_action,
        "by_result": by_result,
        "sessions": len(session_ids),
    }

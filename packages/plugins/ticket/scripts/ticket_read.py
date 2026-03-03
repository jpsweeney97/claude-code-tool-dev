"""Shared read module for ticket query and list operations.

Used by ticket-ops (query/list commands) and ticket-triage.
Read-only — never modifies ticket files.
"""
from __future__ import annotations

from pathlib import Path

from scripts.ticket_parse import ParsedTicket, parse_ticket


def list_tickets(
    tickets_dir: Path,
    *,
    include_closed: bool = False,
) -> list[ParsedTicket]:
    """List all parseable tickets in the tickets directory.

    Scans docs/tickets/*.md. If include_closed=True, also scans
    docs/tickets/closed-tickets/*.md. Skips unparseable files silently.
    Returns tickets sorted by date (newest first), then by ID.
    """
    tickets: list[ParsedTicket] = []

    if not tickets_dir.is_dir():
        return tickets

    # Scan active tickets.
    for ticket_file in tickets_dir.glob("*.md"):
        ticket = parse_ticket(ticket_file)
        if ticket is not None:
            tickets.append(ticket)

    # Scan closed tickets if requested.
    if include_closed:
        closed_dir = tickets_dir / "closed-tickets"
        if closed_dir.is_dir():
            for ticket_file in closed_dir.glob("*.md"):
                ticket = parse_ticket(ticket_file)
                if ticket is not None:
                    tickets.append(ticket)

    # Sort: newest date first, then by ID.
    tickets.sort(key=lambda t: (t.date, t.id), reverse=True)
    return tickets


def find_ticket_by_id(
    tickets_dir: Path,
    ticket_id: str,
    *,
    include_closed: bool = True,
) -> ParsedTicket | None:
    """Find a ticket by exact ID. Returns None if not found.

    Scans all ticket files (including closed) and matches on the `id` field.
    """
    all_tickets = list_tickets(tickets_dir, include_closed=include_closed)
    for ticket in all_tickets:
        if ticket.id == ticket_id:
            return ticket
    return None


def filter_tickets(
    tickets: list[ParsedTicket],
    *,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
) -> list[ParsedTicket]:
    """Filter a list of tickets by criteria. All criteria are AND-combined."""
    result = tickets
    if status is not None:
        result = [t for t in result if t.status == status]
    if priority is not None:
        result = [t for t in result if t.priority == priority]
    if tag is not None:
        result = [t for t in result if tag in t.tags]
    return result


def fuzzy_match_id(
    tickets: list[ParsedTicket],
    partial_id: str,
) -> list[ParsedTicket]:
    """Find tickets whose ID starts with the given prefix."""
    return [t for t in tickets if t.id.startswith(partial_id)]

"""Tests for ticket_read.py — shared read module for query and list."""
from __future__ import annotations



from scripts.ticket_read import (
    find_ticket_by_id,
    list_tickets,
    filter_tickets,
    fuzzy_match_id,
)


class TestListTickets:
    def test_empty_directory(self, tmp_tickets):
        tickets = list_tickets(tmp_tickets)
        assert tickets == []

    def test_nonexistent_directory(self, tmp_path):
        tickets = list_tickets(tmp_path / "nonexistent")
        assert tickets == []

    def test_lists_all_tickets(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-first.md", id="T-20260302-01")
        make_ticket(tmp_tickets, "2026-03-02-second.md", id="T-20260302-02")
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 2

    def test_skips_unparseable(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-good.md", id="T-20260302-01")
        bad = tmp_tickets / "bad.md"
        bad.write_text("# Not a ticket\nNo yaml.", encoding="utf-8")
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 1

    def test_includes_legacy(self, tmp_tickets):
        from tests.conftest import make_gen1_ticket, make_gen2_ticket, make_ticket

        make_ticket(tmp_tickets, "2026-03-02-new.md", id="T-20260302-01")
        make_gen1_ticket(tmp_tickets)
        make_gen2_ticket(tmp_tickets)
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 3

    def test_includes_closed_tickets(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-open.md", id="T-20260302-01")
        closed_dir = tmp_tickets / "closed-tickets"
        closed_dir.mkdir()
        make_ticket(closed_dir, "2026-03-01-done.md", id="T-20260301-01", status="done")
        tickets = list_tickets(tmp_tickets, include_closed=True)
        assert len(tickets) == 2


class TestFindTicketById:
    def test_exact_match(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01")
        ticket = find_ticket_by_id(tmp_tickets, "T-20260302-01")
        assert ticket is not None
        assert ticket.id == "T-20260302-01"

    def test_not_found(self, tmp_tickets):
        assert find_ticket_by_id(tmp_tickets, "T-99999999-99") is None

    def test_legacy_id(self, tmp_tickets):
        from tests.conftest import make_gen2_ticket

        make_gen2_ticket(tmp_tickets)
        ticket = find_ticket_by_id(tmp_tickets, "T-A")
        assert ticket is not None
        assert ticket.id == "T-A"


class TestFilterTickets:
    def test_filter_by_status(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "open.md", id="T-20260302-01", status="open")
        make_ticket(tmp_tickets, "done.md", id="T-20260302-02", status="done")
        tickets = list_tickets(tmp_tickets)
        filtered = filter_tickets(tickets, status="open")
        assert len(filtered) == 1
        assert filtered[0].id == "T-20260302-01"

    def test_filter_by_priority(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "high.md", id="T-20260302-01", priority="high")
        make_ticket(tmp_tickets, "low.md", id="T-20260302-02", priority="low")
        tickets = list_tickets(tmp_tickets)
        filtered = filter_tickets(tickets, priority="high")
        assert len(filtered) == 1

    def test_filter_by_tag(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "auth.md", id="T-20260302-01", tags=["auth", "api"])
        make_ticket(tmp_tickets, "ui.md", id="T-20260302-02", tags=["ui"])
        tickets = list_tickets(tmp_tickets)
        filtered = filter_tickets(tickets, tag="auth")
        assert len(filtered) == 1

    def test_filter_multiple_criteria(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "match.md", id="T-20260302-01", status="open", priority="high")
        make_ticket(tmp_tickets, "no-match.md", id="T-20260302-02", status="open", priority="low")
        tickets = list_tickets(tmp_tickets)
        filtered = filter_tickets(tickets, status="open", priority="high")
        assert len(filtered) == 1


class TestFuzzyMatchId:
    def test_prefix_match(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "ticket.md", id="T-20260302-01")
        tickets = list_tickets(tmp_tickets)
        matches = fuzzy_match_id(tickets, "T-2026030")
        assert len(matches) == 1

    def test_no_match(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "ticket.md", id="T-20260302-01")
        tickets = list_tickets(tmp_tickets)
        matches = fuzzy_match_id(tickets, "T-99999")
        assert len(matches) == 0

    def test_multiple_matches(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "one.md", id="T-20260302-01")
        make_ticket(tmp_tickets, "two.md", id="T-20260302-02")
        tickets = list_tickets(tmp_tickets)
        matches = fuzzy_match_id(tickets, "T-20260302")
        assert len(matches) == 2

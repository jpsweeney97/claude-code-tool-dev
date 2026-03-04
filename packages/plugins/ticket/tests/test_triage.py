"""Tests for the triage analysis script."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tests.conftest import make_ticket


class TestDashboard:
    """Test triage_dashboard counts and alerts."""

    @pytest.fixture
    def populated_tickets(self, tmp_tickets):
        """Create a mix of tickets for dashboard testing."""
        make_ticket(tmp_tickets, "t1.md", id="T-20260302-01", status="open")
        make_ticket(tmp_tickets, "t2.md", id="T-20260302-02", status="in_progress")
        make_ticket(tmp_tickets, "t3.md", id="T-20260302-03", status="blocked",
                    blocked_by=["T-20260302-01"])
        make_ticket(tmp_tickets, "t4.md", id="T-20260302-04", status="done")
        return tmp_tickets

    def test_status_counts(self, populated_tickets):
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(populated_tickets)
        assert result["counts"]["open"] == 1
        assert result["counts"]["in_progress"] == 1
        assert result["counts"]["blocked"] == 1
        assert result["total"] == 3  # open + in_progress + blocked (done excluded)

    def test_empty_directory(self, tmp_tickets):
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["total"] == 0
        assert result["stale"] == []


class TestStaleDetection:
    """Test stale ticket detection."""

    def test_stale_ticket_detected(self, tmp_tickets):
        """Ticket older than 7 days in open status -> stale."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
        make_ticket(tmp_tickets, "old.md", id="T-20260220-01", date=old_date, status="open")
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert len(result["stale"]) == 1
        assert result["stale"][0]["id"] == "T-20260220-01"

    def test_recent_ticket_not_stale(self, tmp_tickets):
        """Ticket from today -> not stale."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        make_ticket(tmp_tickets, "new.md", id="T-20260302-01", date=today, status="open")
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["stale"] == []

    def test_done_ticket_not_stale(self, tmp_tickets):
        """Done tickets are never stale (regardless of age)."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        make_ticket(tmp_tickets, "done.md", id="T-20260201-01", date=old_date, status="done")
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["stale"] == []


class TestBlockedChain:
    """Test blocked chain analysis."""

    def test_root_blocker_found(self, tmp_tickets):
        """Follow blocked_by chain to find root blocker."""
        make_ticket(tmp_tickets, "root.md", id="T-20260302-01", status="open")
        make_ticket(tmp_tickets, "mid.md", id="T-20260302-02", status="blocked",
                    blocked_by=["T-20260302-01"])
        make_ticket(tmp_tickets, "leaf.md", id="T-20260302-03", status="blocked",
                    blocked_by=["T-20260302-02"])
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        chains = {c["id"]: c for c in result["blocked_chains"]}
        assert "T-20260302-03" in chains
        assert "T-20260302-01" in chains["T-20260302-03"]["root_blockers"]

    def test_missing_blocker_is_root(self, tmp_tickets):
        """Blocker not found in ticket map -> treated as root."""
        make_ticket(tmp_tickets, "blocked.md", id="T-20260302-01", status="blocked",
                    blocked_by=["T-MISSING-01"])
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["blocked_chains"][0]["root_blockers"] == ["T-MISSING-01"]

    def test_circular_dependency_no_infinite_loop(self, tmp_tickets):
        """Circular blocked_by chain -> visited set prevents infinite loop."""
        make_ticket(tmp_tickets, "a.md", id="T-20260302-01", status="blocked",
                    blocked_by=["T-20260302-02"])
        make_ticket(tmp_tickets, "b.md", id="T-20260302-02", status="blocked",
                    blocked_by=["T-20260302-01"])
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        chains = {c["id"]: c for c in result["blocked_chains"]}
        assert len(chains) == 2


class TestDocSize:
    """Test document size warnings."""

    def test_large_doc_strong_warning(self, tmp_tickets):
        """Ticket >32KB -> strong_warn."""
        path = make_ticket(tmp_tickets, "big.md", id="T-20260302-01")
        with open(path, "a") as f:
            f.write("x" * 33000)
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert len(result["size_warnings"]) == 1
        assert "strong_warn" in result["size_warnings"][0]["warning"]

    def test_medium_doc_warning(self, tmp_tickets):
        """Ticket >16KB but <32KB -> warn."""
        path = make_ticket(tmp_tickets, "med.md", id="T-20260302-01")
        with open(path, "a") as f:
            f.write("x" * 17000)
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert len(result["size_warnings"]) == 1
        assert "warn" in result["size_warnings"][0]["warning"]
        assert "strong" not in result["size_warnings"][0]["warning"]

    def test_normal_doc_no_warning(self, tmp_tickets):
        """Normal-sized ticket -> no warning."""
        make_ticket(tmp_tickets, "normal.md", id="T-20260302-01")
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["size_warnings"] == []

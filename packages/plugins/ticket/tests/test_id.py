"""Tests for ticket_id.py — ID allocation and slug generation."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.ticket_id import (
    allocate_id,
    generate_slug,
    is_legacy_id,
    parse_id_date,
)


class TestAllocateId:
    def test_first_ticket_of_day(self, tmp_tickets):
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-01"

    def test_sequential_allocation(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-first.md", id="T-20260302-01")
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-02"

    def test_gap_in_sequence(self, tmp_tickets):
        """Allocates next after highest, not gap-filling."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-first.md", id="T-20260302-01")
        make_ticket(tmp_tickets, "2026-03-02-third.md", id="T-20260302-03")
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-04"

    def test_different_day_no_conflict(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-01-old.md", id="T-20260301-05")
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-01"

    def test_empty_directory(self, tmp_tickets):
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-01"

    def test_nonexistent_directory(self, tmp_path):
        """Missing directory returns first ID (not error)."""
        ticket_id = allocate_id(tmp_path / "nonexistent", date(2026, 3, 2))
        assert ticket_id == "T-20260302-01"


class TestGenerateSlug:
    def test_basic_title(self):
        assert generate_slug("Fix authentication timeout on large payloads") == "fix-authentication-timeout-on-large-payloads"

    def test_truncates_to_six_words(self):
        slug = generate_slug("This is a very long title that exceeds six words easily")
        assert slug == "this-is-a-very-long-title"

    def test_special_characters_removed(self):
        slug = generate_slug("Fix: the AUTH bug (v2.0)!")
        assert slug == "fix-the-auth-bug-v20"

    def test_collapses_hyphens(self):
        slug = generate_slug("Fix --- multiple --- hyphens")
        assert slug == "fix-multiple-hyphens"

    def test_max_60_chars(self):
        long_title = "a" * 100
        slug = generate_slug(long_title)
        assert len(slug) <= 60

    def test_empty_title(self):
        slug = generate_slug("")
        assert slug == "untitled"


class TestIsLegacyId:
    def test_gen1_slug(self):
        assert is_legacy_id("handoff-chain-viz") is True

    def test_gen2_letter(self):
        assert is_legacy_id("T-A") is True
        assert is_legacy_id("T-F") is True

    def test_gen3_numeric(self):
        assert is_legacy_id("T-003") is True
        assert is_legacy_id("T-100") is True

    def test_v10_not_legacy(self):
        assert is_legacy_id("T-20260302-01") is False


class TestParseIdDate:
    def test_v10_id(self):
        assert parse_id_date("T-20260302-01") == date(2026, 3, 2)

    def test_legacy_id_returns_none(self):
        assert parse_id_date("T-A") is None
        assert parse_id_date("T-003") is None
        assert parse_id_date("handoff-chain-viz") is None

"""Tests for ticket_render.py — markdown ticket rendering."""
from __future__ import annotations

import pytest

from scripts.ticket_render import render_ticket


class TestRenderTicket:
    def test_basic_ticket(self):
        result = render_ticket(
            id="T-20260302-01",
            title="Fix authentication timeout",
            date="2026-03-02",
            status="open",
            priority="high",
            effort="S",
            source={"type": "ad-hoc", "ref": "", "session": "test-session"},
            tags=["auth", "api"],
            problem="Auth handler times out for payloads >10MB.",
            approach="Make timeout configurable per route.",
            acceptance_criteria=["Timeout configurable per route", "Default remains 30s"],
            verification="uv run pytest tests/test_auth.py",
            key_files=[
                {"file": "handler.py:45", "role": "Timeout logic", "look_for": "hardcoded timeout"},
            ],
        )
        assert "# T-20260302-01: Fix authentication timeout" in result
        assert "id: T-20260302-01" in result
        assert 'status: open' in result
        assert "## Problem" in result
        assert "## Approach" in result
        assert "## Acceptance Criteria" in result
        assert "- [ ] Timeout configurable per route" in result
        assert "## Verification" in result
        assert "## Key Files" in result
        assert 'contract_version: "1.0"' in result

    def test_minimal_ticket(self):
        result = render_ticket(
            id="T-20260302-01",
            title="Minimal ticket",
            date="2026-03-02",
            status="open",
            priority="medium",
            problem="Something needs fixing.",
        )
        assert "# T-20260302-01: Minimal ticket" in result
        assert "## Problem" in result
        # Optional sections absent
        assert "## Context" not in result
        assert "## Prior Investigation" not in result

    def test_optional_sections_included(self):
        result = render_ticket(
            id="T-20260302-01",
            title="With extras",
            date="2026-03-02",
            status="open",
            priority="high",
            problem="Issue.",
            context="Found during refactor.",
            prior_investigation="Checked handler.py — timeout hardcoded.",
            decisions_made="Configurable timeout over fixed increase.",
            related="T-20260301-03 (API config refactor)",
        )
        assert "## Context" in result
        assert "## Prior Investigation" in result
        assert "## Decisions Made" in result
        assert "## Related" in result

    def test_blocked_by_and_blocks(self):
        result = render_ticket(
            id="T-20260302-01",
            title="Blocked ticket",
            date="2026-03-02",
            status="blocked",
            priority="high",
            problem="Waiting on dependency.",
            blocked_by=["T-20260302-02"],
            blocks=["T-20260302-03"],
        )
        assert "blocked_by: ['T-20260302-02']" in result
        assert "blocks: ['T-20260302-03']" in result

    def test_defer_field(self):
        result = render_ticket(
            id="T-20260302-01",
            title="Deferred ticket",
            date="2026-03-02",
            status="open",
            priority="low",
            problem="Can wait.",
            defer={"active": True, "reason": "Waiting for v2 API", "deferred_at": "2026-03-02"},
        )
        assert "defer:" in result
        assert "active: true" in result

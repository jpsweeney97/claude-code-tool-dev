"""Tests for ticket_engine_core.py — engine pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ticket_engine_core import (
    EngineResponse,
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)


class TestEngineClassify:
    def test_create_intent(self):
        resp = engine_classify(
            action="create",
            args={"title": "Fix auth bug"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "create"
        assert resp.data["confidence"] >= 0.0

    def test_update_intent(self):
        resp = engine_classify(
            action="update",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "update"

    def test_close_intent(self):
        resp = engine_classify(
            action="close",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "close"

    def test_reopen_intent(self):
        resp = engine_classify(
            action="reopen",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "reopen"

    def test_unknown_action(self):
        resp = engine_classify(
            action="banana",
            args={},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "escalate"

    def test_unknown_origin_fails_closed(self):
        resp = engine_classify(
            action="create",
            args={},
            session_id="test-session",
            request_origin="unknown",
        )
        assert resp.state == "escalate"
        assert "caller identity" in resp.message.lower()

    def test_resolved_ticket_id(self):
        resp = engine_classify(
            action="update",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.data["resolved_ticket_id"] == "T-20260302-01"

    def test_create_has_no_resolved_id(self):
        resp = engine_classify(
            action="create",
            args={},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.data["resolved_ticket_id"] is None


class TestEnginePlan:
    def test_create_with_all_fields(self, tmp_tickets):
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_file_paths": ["handler.py"],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dedup_fingerprint" in resp.data
        assert resp.data["missing_fields"] == []

    def test_create_missing_required_fields(self, tmp_tickets):
        resp = engine_plan(
            intent="create",
            fields={"title": "No problem section"},
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"
        assert "problem" in resp.data["missing_fields"]

    def test_dedup_detection(self, tmp_tickets):
        from datetime import datetime, timezone

        from tests.conftest import make_ticket

        today = datetime.now(timezone.utc).date()
        today_str = today.isoformat()
        today_compact = today_str.replace("-", "")
        make_ticket(
            tmp_tickets,
            f"{today_str}-auth.md",
            id=f"T-{today_compact}-01",
            date=today_str,
            problem="Auth times out.",
            title="Fix auth bug",
        )
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_file_paths": ["test.py"],  # Must match conftest's Key Files table
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "duplicate_candidate"
        assert resp.data["duplicate_of"] is not None

    def test_no_dedup_outside_24h(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "2026-02-28-old.md",
            id="T-20260228-01",
            date="2026-02-28",
            problem="Auth times out.",
            title="Old auth bug",
        )
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_file_paths": [],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        # Old ticket outside 24h window — no dedup match.
        assert resp.state == "ok"

    def test_non_create_skips_dedup(self, tmp_tickets):
        resp = engine_plan(
            intent="update",
            fields={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        # No dedup for non-create.
        assert resp.data.get("dedup_fingerprint") is None


class TestEnginePreflight:
    def test_user_create_passes(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert len(resp.data["checks_passed"]) > 0

    def test_unknown_origin_rejected(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="unknown",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"

    def test_low_confidence_rejected(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.1,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert "confidence" in resp.message.lower()

    def test_agent_hard_blocked_phase1(self, tmp_tickets):
        """Phase 1 strict fail-closed: all agent mutations are hard-blocked."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc",
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"
        assert "phase 1" in resp.message.lower() or "hard-blocked" in resp.message.lower()

    def test_agent_reopen_hard_blocked_phase1(self, tmp_tickets):
        """Agent reopen also hard-blocked (not just user-only check)."""
        resp = engine_preflight(
            ticket_id="T-20260302-01",
            action="reopen",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="reopen",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"

    def test_non_create_without_ticket_id_rejected(self, tmp_tickets):
        """Non-create actions require ticket_id."""
        resp = engine_preflight(
            ticket_id=None,
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"

    def test_intent_mismatch_escalates(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",  # Mismatch!
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert "mismatch" in resp.message.lower()

    def test_stale_target_fingerprint(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01")
        resp = engine_preflight(
            ticket_id="T-20260302-01",
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint="stale-fingerprint",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert "stale" in resp.message.lower() or "fingerprint" in resp.message.lower()

    def test_update_ticket_not_found(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id="T-99999999-99",
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "not_found"

    def test_close_with_open_blockers(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_preflight(
            ticket_id="T-20260302-02",
            action="close",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="close",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "dependency_blocked"

    def test_close_with_open_blockers_override(self, tmp_tickets):
        """dependency_override=True allows closing with open blockers."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_preflight(
            ticket_id="T-20260302-02",
            action="close",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="close",
            dedup_fingerprint=None,
            target_fingerprint=None,
            dependency_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dependencies_overridden" in resp.data["checks_passed"]

    def test_dedup_blocks_without_override(self, tmp_tickets):
        """Preflight blocks create when duplicate detected and no override."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            duplicate_of="T-20260302-01",
            dedup_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "duplicate_candidate"
        assert resp.error_code == "duplicate_candidate"

    def test_dedup_passes_with_override(self, tmp_tickets):
        """Preflight allows create when duplicate detected but override=True."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            duplicate_of="T-20260302-01",
            dedup_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dedup" in resp.data["checks_passed"]

    def test_confidence_gate_no_policy_blocked_code(self, tmp_tickets):
        """Confidence gate returns error_code=None, not policy_blocked."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.1,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert resp.error_code is None


class TestEngineExecute:
    def test_invalid_transition_terminal_via_update(self, tmp_tickets):
        """done -> in_progress via update is invalid (must reopen first)."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-done.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "reopen" in resp.message.lower()

    def test_invalid_transition_wontfix_via_update(self, tmp_tickets):
        """wontfix -> open via update is invalid (must reopen)."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-wontfix.md", id="T-20260302-01", status="wontfix")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "open"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_transition_to_blocked_requires_blocked_by(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open", blocked_by=[])
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "blocked"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "blocked_by" in resp.message.lower()

    def test_agent_override_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01")
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Test", "priority": "medium"},
            session_id="test-session",
            request_origin="agent",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"
        assert "agent" in resp.message.lower() or "override" in resp.message.lower()

    def test_error_code_on_all_error_returns(self, tmp_tickets):
        """All error EngineResponse returns include error_code."""
        # Test update need_fields.
        resp = engine_execute(
            action="update",
            ticket_id=None,
            fields={},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"
        assert resp.error_code == "need_fields"

        # Test update not_found.
        resp = engine_execute(
            action="update",
            ticket_id="T-99999999-99",
            fields={},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "not_found"
        assert resp.error_code == "not_found"

    def test_create_ticket(self, tmp_tickets):
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out for large payloads.",
                "priority": "high",
                "effort": "S",
                "source": {"type": "ad-hoc", "ref": "", "session": "test-session"},
                "tags": ["auth"],
                "approach": "Make timeout configurable.",
                "acceptance_criteria": ["Timeout configurable", "Default remains 30s"],
                "verification": "uv run pytest tests/test_auth.py",
                "key_files": [{"file": "handler.py:45", "role": "Timeout", "look_for": "hardcoded"}],
            },
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_create"
        assert resp.ticket_id is not None
        assert resp.ticket_id.startswith("T-")
        assert resp.data["ticket_path"] is not None
        # Verify file was created.
        ticket_path = Path(resp.data["ticket_path"])
        assert ticket_path.exists()
        content = ticket_path.read_text(encoding="utf-8")
        assert "Fix auth bug" in content
        assert "## Problem" in content

    def test_update_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "status: in_progress" in content
        assert 'date: "2026-03-02"' in content

    def test_update_preserves_field_order(self, tmp_tickets):
        """Canonical renderer emits fields in defined order, not alphabetical."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"priority": "critical"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        id_pos = content.index("id: T-20260302-01")
        status_pos = content.index("status: open")
        assert id_pos < status_pos

    def test_update_preserves_full_field_order(self, tmp_tickets):
        """Verify all canonical field positions."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open",
                     priority="medium", effort="S")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"tags": ["bug"]},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        id_pos = content.index("id:")
        status_pos = content.index("status:")
        priority_pos = content.index("priority:")
        effort_pos = content.index("effort:")
        tags_pos = content.index("tags:")
        assert id_pos < status_pos < priority_pos < effort_pos < tags_pos

    def test_canonical_renderer_none_skipped(self, tmp_tickets):
        """Fields set to None are omitted, not rendered as 'key: None'."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"effort": None},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "effort: None" not in content

    def test_canonical_renderer_list_format(self, tmp_tickets):
        """Lists render as YAML flow sequences, not Python repr."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"tags": ["bug", "urgent"]},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "tags: [bug, urgent]" in content
        assert "['bug'" not in content

    def test_close_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_with_archive(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done", "archive": True},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close_archived"
        assert not (tmp_tickets / "2026-03-02-test.md").exists()
        assert (tmp_tickets / "closed-tickets" / "2026-03-02-test.md").exists()

    def test_close_from_open_succeeds(self, tmp_tickets):
        """Close directly validates with action='close', not 'update'."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_with_invalid_resolution_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_close_terminal_ticket_rejected(self, tmp_tickets):
        """Closing an already-done ticket is invalid — must reopen first."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-done.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert resp.error_code == "invalid_transition"

    def test_close_wontfix_to_done_rejected(self, tmp_tickets):
        """wontfix -> done via close is invalid — terminal state."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-wf.md", id="T-20260302-01", status="wontfix")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_close_checks_acceptance_criteria(self, tmp_tickets):
        """Close to 'done' from in_progress requires acceptance criteria."""
        import textwrap

        # Create ticket WITHOUT acceptance criteria section.
        content = textwrap.dedent("""\
            # T-20260302-01: No AC ticket

            ```yaml
            id: T-20260302-01
            date: "2026-03-02"
            status: in_progress
            priority: high
            effort: S
            source:
              type: ad-hoc
              ref: ""
              session: "test"
            tags: []
            blocked_by: []
            blocks: []
            contract_version: "1.0"
            ```

            ## Problem
            Test problem without acceptance criteria.
        """)
        (tmp_tickets / "2026-03-02-test.md").write_text(content, encoding="utf-8")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "acceptance" in resp.message.lower() or "criteria" in resp.message.lower()

    def test_reopen_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="reopen",
            ticket_id="T-20260302-01",
            fields={"reopen_reason": "Bug reoccurred after merge"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_reopen"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "status: open" in content
        assert "Reopen History" in content


class TestEngineExecuteIntegration:
    """Integration tests exercising the full engine_execute dispatcher
    across multiple lifecycle operations."""

    def test_full_lifecycle_create_update_close_reopen(self, tmp_tickets):
        """Create -> update -> close -> reopen lifecycle."""
        # Create.
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Lifecycle test",
                "problem": "Integration test problem.",
                "priority": "medium",
                "source": {"type": "ad-hoc", "ref": "", "session": "test-session"},
                "tags": ["test"],
            },
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_create"
        ticket_id = resp.ticket_id
        ticket_path = Path(resp.data["ticket_path"])
        assert ticket_path.exists()

        # Update status to in_progress.
        resp = engine_execute(
            action="update",
            ticket_id=ticket_id,
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"

        # Close with wontfix (avoids acceptance criteria requirement).
        resp = engine_execute(
            action="close",
            ticket_id=ticket_id,
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

        # Reopen.
        resp = engine_execute(
            action="reopen",
            ticket_id=ticket_id,
            fields={"reopen_reason": "Reconsidered — will fix after all"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_reopen"

        # Verify final state.
        content = ticket_path.read_text(encoding="utf-8")
        assert "status: open" in content
        assert "Reopen History" in content

    def test_unknown_action_escalates(self, tmp_tickets):
        """Dispatcher rejects unknown actions."""
        resp = engine_execute(
            action="merge",
            ticket_id=None,
            fields={},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert resp.error_code == "intent_mismatch"


class TestTransportValidation:
    """Test hook_injected transport-layer validation."""

    def test_agent_without_hook_injected_rejected(self, tmp_tickets):
        """Agent requests are policy_blocked (Phase 1 hard-block fires first)."""
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess", request_origin="agent",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"

    def test_user_without_hook_injected_proceeds(self, tmp_tickets):
        """User mutations without hook_injected proceed normally."""
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_create"

    def test_user_with_hook_injected_proceeds(self, tmp_tickets):
        """User mutations with hook_injected=True proceed normally."""
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets, hook_injected=True,
        )
        assert resp.state == "ok_create"

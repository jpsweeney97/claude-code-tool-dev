"""Integration tests — full engine pipeline end-to-end."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.ticket_engine_core import (
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)


class TestFullCreatePipeline:
    def test_user_create_end_to_end(self, tmp_tickets):
        """classify -> plan -> preflight -> execute for user create."""
        # Step 1: classify
        classify_resp = engine_classify(
            action="create",
            args={},
            session_id="integration-test",
            request_origin="user",
        )
        assert classify_resp.state == "ok"

        # Step 2: plan
        fields = {
            "title": "Integration test ticket",
            "problem": "This is an integration test.",
            "priority": "medium",
            "key_files": [],
        }
        plan_resp = engine_plan(
            intent=classify_resp.data["intent"],
            fields=fields,
            session_id="integration-test",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "ok"

        # Step 3: preflight
        preflight_resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="integration-test",
            request_origin="user",
            classify_confidence=classify_resp.data["confidence"],
            classify_intent=classify_resp.data["intent"],
            dedup_fingerprint=plan_resp.data["dedup_fingerprint"],
            target_fingerprint=plan_resp.data["target_fingerprint"],
            tickets_dir=tmp_tickets,
        )
        assert preflight_resp.state == "ok"

        # Step 4: execute
        execute_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="integration-test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert execute_resp.state == "ok_create"
        assert Path(execute_resp.data["ticket_path"]).exists()

    def test_agent_blocked_phase1_fail_closed(self, tmp_tickets):
        """Agent create is hard-blocked by Phase 1 fail-closed policy."""
        classify_resp = engine_classify(
            action="create",
            args={},
            session_id="agent-test",
            request_origin="agent",
        )
        assert classify_resp.state == "ok"

        preflight_resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="agent-test",
            request_origin="agent",
            classify_confidence=classify_resp.data["confidence"],
            classify_intent=classify_resp.data["intent"],
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert preflight_resp.state == "policy_blocked"

    def test_update_then_close_pipeline(self, tmp_tickets):
        """Create -> update to in_progress -> close."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")

        # Update to in_progress.
        update_resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert update_resp.state == "ok_update"

        # Close.
        close_resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert close_resp.state == "ok_close"

    def test_dedup_then_override(self, tmp_tickets):
        """Create duplicate detected -> override -> create succeeds."""
        from tests.conftest import make_ticket

        # Use dynamic date so ticket stays within 24h dedup window.
        today = date.today().isoformat()
        make_ticket(
            tmp_tickets,
            f"{today}-existing.md",
            id="T-20260302-01",
            date=today,
            problem="Auth times out.",
        )

        fields = {
            "title": "Same auth bug",
            "problem": "Auth times out.",
            "priority": "high",
            # make_ticket's Key Files table always includes "test.py".
            "key_files": ["test.py"],
        }

        plan_resp = engine_plan(
            intent="create",
            fields=fields,
            session_id="test",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "duplicate_candidate"

        # Override and create anyway.
        # key_files for execute must be list[dict] (render format), not list[str] (dedup format).
        # Omit key_files from execute fields — render_ticket treats None as "no section".
        execute_fields = {k: v for k, v in fields.items() if k != "key_files"}
        execute_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=execute_fields,
            session_id="test",
            request_origin="user",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert execute_resp.state == "ok_create"

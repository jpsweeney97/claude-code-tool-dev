"""Integration tests — full engine pipeline end-to-end."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


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
            "key_file_paths": [],
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

    def test_user_create_end_to_end_with_plain_classify_data_merge(self, tmp_tickets):
        """The skill can merge classify data directly without renaming fields."""
        payload = {
            "action": "create",
            "args": {},
            "session_id": "integration-plain-merge",
            "request_origin": "user",
            "fields": {
                "title": "Integration plain merge ticket",
                "problem": "This verifies classify aliases are emitted natively.",
                "priority": "medium",
                "key_file_paths": [],
            },
        }

        classify_resp = engine_classify(
            action=payload["action"],
            args=payload["args"],
            session_id=payload["session_id"],
            request_origin=payload["request_origin"],
        )
        assert classify_resp.state == "ok"
        payload.update(classify_resp.data)

        plan_resp = engine_plan(
            intent=payload["intent"],
            fields=payload["fields"],
            session_id=payload["session_id"],
            request_origin=payload["request_origin"],
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "ok"
        payload.update(plan_resp.data)

        preflight_resp = engine_preflight(
            ticket_id=payload.get("resolved_ticket_id"),
            action=payload["action"],
            session_id=payload["session_id"],
            request_origin=payload["request_origin"],
            classify_confidence=payload.get("classify_confidence", 0.0),
            classify_intent=payload.get("classify_intent", ""),
            dedup_fingerprint=payload.get("dedup_fingerprint"),
            target_fingerprint=payload.get("target_fingerprint"),
            tickets_dir=tmp_tickets,
        )
        assert preflight_resp.state == "ok"

        execute_resp = engine_execute(
            action=payload["action"],
            ticket_id=payload.get("resolved_ticket_id"),
            fields=payload["fields"],
            session_id=payload["session_id"],
            request_origin=payload["request_origin"],
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
        today = datetime.now(timezone.utc).date().isoformat()
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
            "key_file_paths": ["test.py"],
        }

        plan_resp = engine_plan(
            intent="create",
            fields=fields,
            session_id="test",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "duplicate_candidate"

        # Override and create anyway with the same execute payload.
        execute_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="test",
            request_origin="user",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert execute_resp.state == "ok_create"

    def test_create_with_key_file_paths_only_produces_valid_ticket_without_key_files_section(
        self, tmp_tickets
    ):
        fields = {
            "title": "Paths only create",
            "problem": "Only dedup file paths are available for this ticket.",
            "priority": "medium",
            "key_file_paths": ["src/auth/token.py", "src/middleware/session.py"],
        }

        plan_resp = engine_plan(
            intent="create",
            fields=fields,
            session_id="paths-only",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "ok"
        assert plan_resp.data["dedup_fingerprint"]

        execute_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="paths-only",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert execute_resp.state == "ok_create"

        ticket_path = Path(execute_resp.data["ticket_path"])
        assert ticket_path.exists()
        ticket_text = ticket_path.read_text(encoding="utf-8")
        assert "## Key Files" not in ticket_text

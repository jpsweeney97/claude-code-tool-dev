"""Tests for ticket_engine_core.py — engine pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

import scripts.ticket_engine_core as ticket_engine_core
import scripts.ticket_paths as ticket_paths
from scripts.ticket_engine_core import (
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)
from scripts.ticket_parse import extract_fenced_yaml
from scripts.ticket_paths import resolve_tickets_dir


def _expected_canonical_yaml(
    *,
    ticket_id: str,
    date: str,
    status: str,
    priority: str,
    effort: str,
    source_type: str,
    source_ref: str,
    session: str,
    tags: list[str],
    blocked_by: list[str],
    blocks: list[str],
    contract_version: str = "1.0",
) -> str:
    return (
        f"id: {ticket_id}\n"
        f'date: "{date}"\n'
        f"status: {status}\n"
        f"priority: {priority}\n"
        f"effort: {effort}\n"
        "source:\n"
        f"  type: {source_type}\n"
        f'  ref: "{source_ref}"\n'
        f"  session: {session}\n"
        f"tags: [{', '.join(tags)}]\n"
        f"blocked_by: [{', '.join(blocked_by)}]\n"
        f"blocks: [{', '.join(blocks)}]\n"
        f'contract_version: "{contract_version}"\n'
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

    def test_classify_emits_preflight_aliases(self):
        resp = engine_classify(
            action="update",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "update"
        assert resp.data["confidence"] >= 0.0
        assert resp.data["classify_intent"] == "update"
        assert resp.data["classify_confidence"] == resp.data["confidence"]
        assert resp.data["resolved_ticket_id"] == "T-20260302-01"


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

    def test_dedup_uses_mtime_not_date(self, tmp_tickets):
        """Dedup uses file mtime, catching near-midnight duplicates (P0-3).

        A ticket with yesterday's date but recent mtime should still be
        within the 24h dedup window. The old date-only code would miss this.
        """
        import os
        import time

        from tests.conftest import make_ticket

        # Use a date from 2 days ago — outside 24h window by date alone.
        old_date = "2026-02-28"
        path = make_ticket(
            tmp_tickets,
            f"{old_date}-midnight.md",
            id="T-20260228-01",
            date=old_date,
            problem="Auth times out.",
            title="Midnight edge case",
        )
        # Set mtime to NOW — within 24h window by mtime.
        now = time.time()
        os.utime(path, (now, now))
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_file_paths": ["test.py"],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        # With mtime-based window, this IS a duplicate despite old date.
        assert resp.state == "duplicate_candidate"

    def test_dedup_skips_old_mtime(self, tmp_tickets):
        """Tickets with old mtime are excluded even with recent date field."""
        import os
        import time

        from tests.conftest import make_ticket

        today_str = "2026-03-07"
        path = make_ticket(
            tmp_tickets,
            f"{today_str}-stale.md",
            id="T-20260307-01",
            date=today_str,
            problem="Auth times out.",
            title="Stale ticket",
        )
        # Set mtime to 3 days ago — outside 24h window.
        old_time = time.time() - (3 * 86400)
        os.utime(path, (old_time, old_time))
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_file_paths": ["test.py"],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        # Old mtime puts ticket outside window — no dedup match.
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


class TestResolveTicketsDir:
    def test_default_path_used_when_none(self, tmp_path: Path) -> None:
        resolved, err = resolve_tickets_dir(None, project_root=tmp_path)
        assert err is None
        assert resolved == (tmp_path / "docs" / "tickets").resolve()

    def test_rejects_path_outside_project_root(self, tmp_path: Path) -> None:
        outside = tmp_path.parent / "outside-tickets"
        resolved, err = resolve_tickets_dir(str(outside), project_root=tmp_path)
        assert resolved is None
        assert err is not None
        assert "escapes project root" in err

    def test_rejects_non_string_type(self, tmp_path: Path) -> None:
        resolved, err = resolve_tickets_dir(123, project_root=tmp_path)
        assert resolved is None
        assert err is not None
        assert "expected string path" in err

    def test_resolution_error_returns_validation_message(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fail_resolve(_: Path) -> Path:
            raise OSError("permission denied")

        monkeypatch.setattr(ticket_paths.Path, "resolve", fail_resolve)
        resolved, err = resolve_tickets_dir("docs/tickets", project_root=tmp_path)
        assert resolved is None
        assert err is not None
        assert "resolution failed" in err


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

    def test_agent_blocked_without_hook_injected(self, tmp_tickets):
        """Agent without hook_injected → policy_blocked (hook trust check)."""
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
        assert "hook_injected" in resp.message.lower()

    def test_agent_reopen_user_only(self, tmp_tickets):
        """Agent reopen → policy_blocked (user-only in v1.0)."""
        resp = engine_preflight(
            ticket_id="T-20260302-01",
            action="reopen",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="reopen",
            dedup_fingerprint=None,
            target_fingerprint=None,
            hook_injected=True,
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

    def test_close_wontfix_with_open_blockers_allowed(self, tmp_tickets):
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
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="close",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dependencies_not_required_for_wontfix" in resp.data["checks_passed"]

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

    def test_preflight_close_reports_missing_blockers(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            blocked_by=["T-MISSING-01"],
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
        assert resp.data["missing_blockers"] == ["T-MISSING-01"]
        assert resp.data["unresolved_blockers"] == []

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

    def test_blocked_ticket_cannot_reopen_with_missing_blocker_reference(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "2026-03-02-test.md",
            id="T-20260302-01",
            status="blocked",
            blocked_by=["T-MISSING-01"],
        )
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
        assert "missing blocker" in resp.message.lower()

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

    def test_create_uses_canonical_yaml_shape(self, tmp_tickets):
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Canonical create",
                "problem": "Create should use the same serializer as mutations.",
                "priority": "high",
                "effort": "S",
                "source": {"type": "ad-hoc", "ref": "", "session": "test-session"},
                "tags": ["auth", "api"],
            },
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_create"
        ticket_path = Path(resp.data["ticket_path"])
        assert extract_fenced_yaml(ticket_path.read_text(encoding="utf-8")) == _expected_canonical_yaml(
            ticket_id=resp.ticket_id,
            date=ticket_path.name[:10],
            status="open",
            priority="high",
            effort="S",
            source_type="ad-hoc",
            source_ref="",
            session="test-session",
            tags=["auth", "api"],
            blocked_by=[],
            blocks=[],
        )

    def test_execute_create_blocks_duplicate_without_override(self, tmp_tickets):
        fields = {
            "title": "Duplicate target",
            "problem": "Duplicate me",
            "priority": "medium",
        }
        first = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert first.state == "ok_create"

        second = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert second.state == "duplicate_candidate"
        assert second.error_code == "duplicate_candidate"

    def test_execute_create_duplicate_allowed_with_override(self, tmp_tickets):
        fields = {
            "title": "Duplicate override target",
            "problem": "Duplicate with override",
            "priority": "medium",
        }
        first = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert first.state == "ok_create"

        second = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="test-session",
            request_origin="user",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert second.state == "ok_create"

    def test_execute_create_retries_on_file_exists(
        self, tmp_tickets: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real_write = ticket_engine_core._write_text_exclusive
        attempts: list[Path] = []

        def flaky_write(ticket_path: Path, content: str) -> None:
            attempts.append(ticket_path)
            if len(attempts) == 1:
                real_write(ticket_path, content)
                raise FileExistsError("simulated collision")
            real_write(ticket_path, content)

        monkeypatch.setattr(ticket_engine_core, "_write_text_exclusive", flaky_write)

        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Retry on collision",
                "problem": "Exclusive create should retry instead of overwriting.",
                "priority": "medium",
            },
            session_id="retry-session",
            request_origin="user",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )

        assert resp.state == "ok_create"
        assert len(attempts) == 2
        assert attempts[0].exists()
        assert attempts[1].exists()
        assert attempts[1] != attempts[0]
        assert Path(resp.data["ticket_path"]) == attempts[1]

    def test_execute_create_fails_after_retry_budget_exhausted(
        self, tmp_tickets: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        attempts: list[Path] = []

        def always_exists(ticket_path: Path, content: str) -> None:
            attempts.append(ticket_path)
            raise FileExistsError("still colliding")

        monkeypatch.setattr(ticket_engine_core, "_write_text_exclusive", always_exists)

        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Retry exhaustion",
                "problem": "Create should fail after the exclusive-write retry budget.",
                "priority": "medium",
            },
            session_id="retry-session",
            request_origin="user",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )

        assert resp.state == "escalate"
        assert "retry budget" in resp.message.lower()
        assert len(attempts) == 3

    def test_write_text_exclusive_unlinks_partial_file_on_fsync_failure(
        self, tmp_tickets: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ticket_path = tmp_tickets / "partial-write.md"

        def fail_fsync(fd: int) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(ticket_engine_core.os, "fsync", fail_fsync)

        with pytest.raises(OSError, match="disk full"):
            ticket_engine_core._write_text_exclusive(ticket_path, "partial content")

        assert not ticket_path.exists()

    def test_execute_create_propagates_plan_errors(self, tmp_tickets):
        """Defense-in-depth should return plan-stage validation failures."""
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Missing problem"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"
        assert resp.error_code == "need_fields"

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

    def test_update_rejects_section_field_problem_and_leaves_file_unchanged(self, tmp_tickets):
        from tests.conftest import make_ticket

        ticket_path = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        before = ticket_path.read_text(encoding="utf-8")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"problem": "New problem text"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert "section fields not supported" in resp.message.lower()
        assert ticket_path.read_text(encoding="utf-8") == before

    def test_update_rejects_mixed_frontmatter_and_section_fields_atomically(self, tmp_tickets):
        from tests.conftest import make_ticket

        ticket_path = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        before = ticket_path.read_text(encoding="utf-8")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"priority": "critical", "approach": "Different approach"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert "section fields not supported" in resp.message.lower()
        after = ticket_path.read_text(encoding="utf-8")
        assert after == before
        assert "priority: critical" not in after

    def test_update_rejects_unknown_field_and_leaves_file_unchanged(self, tmp_tickets):
        from tests.conftest import make_ticket

        ticket_path = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        before = ticket_path.read_text(encoding="utf-8")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"custom": {"bad": "value"}},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert "unknown fields: custom" in resp.message.lower()
        assert ticket_path.read_text(encoding="utf-8") == before

    def test_update_ignores_matching_fields_ticket_id(self, tmp_tickets):
        from tests.conftest import make_ticket

        ticket_path = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"ticket_id": "T-20260302-01", "priority": "critical"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = ticket_path.read_text(encoding="utf-8")
        assert "priority: critical" in content
        assert "ticket_id:" not in content

    def test_update_rejects_mismatched_fields_ticket_id(self, tmp_tickets):
        from tests.conftest import make_ticket

        ticket_path = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        before = ticket_path.read_text(encoding="utf-8")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"ticket_id": "T-99999999-99"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert "fields.ticket_id must match" in resp.message.lower()
        assert ticket_path.read_text(encoding="utf-8") == before

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

    def test_canonical_renderer_quotes_embedded_double_quote(self, tmp_tickets):
        """Embedded quotes in list items remain valid YAML after update."""
        from scripts.ticket_read import list_tickets
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"tags": ['bad"tag']},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 1
        assert 'bad"tag' in tickets[0].tags

    def test_canonical_renderer_quotes_integer_date(self, tmp_tickets):
        """Integer date values are coerced to string and quoted to prevent type drift."""
        from scripts.ticket_read import list_tickets
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"date": 20260305},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 1
        assert isinstance(tickets[0].date, str)

    def test_canonical_renderer_quotes_colon_strings(self, tmp_tickets):
        """Strings with colon separators remain parseable YAML."""
        from scripts.ticket_read import list_tickets
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"priority": "high: urgent"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 1
        assert tickets[0].priority == "high: urgent"

    def test_canonical_renderer_preserves_hash_in_string(self, tmp_tickets):
        """Strings containing # are preserved and not parsed as comments."""
        from scripts.ticket_read import list_tickets
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"effort": "M # note"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 1
        assert tickets[0].effort == "M # note"

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

    def test_close_archive_collision_suffixes(self, tmp_tickets):
        """Archiving with an existing file in closed-tickets/ uses -2 suffix."""
        from tests.conftest import make_ticket

        # Create and archive ticket A.
        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp_a = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done", "archive": True},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp_a.state == "ok_close_archived"
        assert (tmp_tickets / "closed-tickets" / "2026-03-02-test.md").exists()

        # Create ticket B with same filename (A no longer blocks the name).
        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-02", status="in_progress")
        resp_b = engine_execute(
            action="close",
            ticket_id="T-20260302-02",
            fields={"resolution": "done", "archive": True},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp_b.state == "ok_close_archived"
        # Both files exist — B got the -2 suffix.
        assert (tmp_tickets / "closed-tickets" / "2026-03-02-test.md").exists()
        assert (tmp_tickets / "closed-tickets" / "2026-03-02-test-2.md").exists()

    def test_close_with_open_blockers_rejected_without_override(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            status="in_progress",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-02",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "dependency_blocked"
        assert resp.error_code == "dependency_blocked"

    def test_execute_close_reports_missing_blockers(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            status="in_progress",
            blocked_by=["T-MISSING-01"],
        )
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-02",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "dependency_blocked"
        assert resp.data["missing_blockers"] == ["T-MISSING-01"]
        assert resp.data["unresolved_blockers"] == []

    def test_close_with_open_blockers_and_override_succeeds(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            status="in_progress",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-02",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_reports_missing_and_unresolved_blockers_together(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            status="in_progress",
            blocked_by=["T-20260302-01", "T-MISSING-01"],
        )
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-02",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "dependency_blocked"
        assert resp.data["unresolved_blockers"] == ["T-20260302-01"]
        assert resp.data["missing_blockers"] == ["T-MISSING-01"]

    def test_execute_close_allows_missing_blockers_with_dependency_override(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            status="in_progress",
            blocked_by=["T-MISSING-01"],
        )
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-02",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_wontfix_with_open_blockers_succeeds(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            status="in_progress",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-02",
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_wontfix_ignores_missing_blockers(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            status="in_progress",
            blocked_by=["T-MISSING-01"],
        )
        preflight = engine_preflight(
            ticket_id="T-20260302-02",
            action="close",
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="close",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert preflight.state == "ok"
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-02",
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_archive_rename_oserror_returns_escalate(
        self, tmp_tickets: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        ticket_path = tmp_tickets / "2026-03-02-test.md"
        real_rename = Path.rename

        def fail_rename(self: Path, target: Path) -> None:
            if self == ticket_path:
                raise OSError("disk error")
            real_rename(self, target)

        monkeypatch.setattr(ticket_engine_core.Path, "rename", fail_rename)
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
        assert resp.state == "escalate"
        assert "archive rename failed" in resp.message

    def test_close_archive_collision_suffix_exhausted_returns_escalate(
        self, tmp_tickets: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        closed_dir = tmp_tickets / "closed-tickets"
        closed_dir.mkdir()
        archived_stub = (
            "# Archived ticket\n\n"
            "```yaml\n"
            "id: T-20260301-99\n"
            "date: \"2026-03-01\"\n"
            "status: done\n"
            "priority: medium\n"
            "source: {type: ad-hoc, ref: \"\", session: \"test\"}\n"
            "contract_version: \"1.0\"\n"
            "```\n"
        )
        (closed_dir / "2026-03-02-test.md").write_text(archived_stub, encoding="utf-8")
        (closed_dir / "2026-03-02-test-2.md").write_text(archived_stub, encoding="utf-8")
        monkeypatch.setattr(ticket_engine_core, "_MAX_ARCHIVE_COLLISION_SUFFIX", 1)
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
        assert resp.state == "escalate"
        assert "collision resolution failed" in resp.message

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

    def test_close_from_open_checks_acceptance_criteria(self, tmp_tickets):
        """Close to 'done' from open requires AC — bypass path for P0-1."""
        import textwrap

        content = textwrap.dedent("""\
            # T-20260302-01: Open no AC ticket

            ```yaml
            id: T-20260302-01
            date: "2026-03-02"
            status: open
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
        (tmp_tickets / "2026-03-02-open-no-ac.md").write_text(content, encoding="utf-8")
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

    def test_close_from_blocked_checks_acceptance_criteria(self, tmp_tickets):
        """Close to 'done' from blocked requires AC — bypass path for P0-1."""
        import textwrap

        content = textwrap.dedent("""\
            # T-20260302-01: Blocked no AC ticket

            ```yaml
            id: T-20260302-01
            date: "2026-03-02"
            status: blocked
            priority: high
            effort: S
            source:
              type: ad-hoc
              ref: ""
              session: "test"
            tags: []
            blocked_by: ["T-OTHER-01"]
            blocks: []
            contract_version: "1.0"
            ```

            ## Problem
            Test problem without acceptance criteria.
        """)
        (tmp_tickets / "2026-03-02-blocked-no-ac.md").write_text(content, encoding="utf-8")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "acceptance" in resp.message.lower() or "criteria" in resp.message.lower()

    def test_close_from_open_succeeds_with_acceptance_criteria(self, tmp_tickets):
        """Close to 'done' from open succeeds when AC present — positive path."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-open-with-ac.md", id="T-20260302-01", status="open")
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
        assert resp.state == "ok_close", f"Expected ok_close but got {resp.state}: {resp.message}"

    def test_update_rejects_unknown_fields_before_serialization(self, tmp_tickets):
        """Unsupported update fields fail validation before YAML serialization."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"custom": {"bad": object()}},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert resp.error_code is None
        assert "unknown fields: custom" in resp.message.lower()

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

    def test_execute_stale_target_fingerprint_rejected(self, tmp_tickets):
        from scripts.ticket_dedup import target_fingerprint
        from tests.conftest import make_ticket

        ticket_path = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        stale_fp = target_fingerprint(ticket_path)
        ticket_path.write_text(ticket_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            target_fingerprint=stale_fp,
        )
        assert resp.state == "preflight_failed"
        assert resp.error_code == "stale_plan"


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

    def test_full_lifecycle_preserves_canonical_yaml_shape(self, tmp_tickets):
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Serializer lifecycle",
                "problem": "All mutation paths should share one YAML renderer.",
                "priority": "medium",
                "effort": "S",
                "source": {"type": "ad-hoc", "ref": "", "session": "test-session"},
                "tags": ["test"],
                "blocked_by": [],
                "blocks": [],
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
        ticket_date = ticket_path.name[:10]

        expected = _expected_canonical_yaml(
            ticket_id=ticket_id,
            date=ticket_date,
            status="open",
            priority="medium",
            effort="S",
            source_type="ad-hoc",
            source_ref="",
            session="test-session",
            tags=["test"],
            blocked_by=[],
            blocks=[],
        )
        assert extract_fenced_yaml(ticket_path.read_text(encoding="utf-8")) == expected

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
        expected = expected.replace("status: open\n", "status: in_progress\n")
        assert extract_fenced_yaml(ticket_path.read_text(encoding="utf-8")) == expected

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
        expected = expected.replace("status: in_progress\n", "status: wontfix\n")
        assert extract_fenced_yaml(ticket_path.read_text(encoding="utf-8")) == expected

        resp = engine_execute(
            action="reopen",
            ticket_id=ticket_id,
            fields={"reopen_reason": "Follow-up work is required"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_reopen"
        expected = expected.replace("status: wontfix\n", "status: open\n")
        content = ticket_path.read_text(encoding="utf-8")
        assert extract_fenced_yaml(content) == expected
        assert "## Reopen History" in content

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
        """Agent without hook_injected → policy_blocked (transport validation)."""
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


class TestYamlScalarEdgeCases:
    @pytest.mark.parametrize("reserved", ["true", "yes", "null"])
    def test_reserved_scalar_round_trip_preserved(self, tmp_tickets, reserved: str):
        from scripts.ticket_read import list_tickets
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"effort": reserved},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        tickets = list_tickets(tmp_tickets)
        assert tickets[0].effort == reserved

    def test_empty_string_round_trip_preserved(self, tmp_tickets):
        from scripts.ticket_read import list_tickets
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open", effort="M")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"effort": ""},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        tickets = list_tickets(tmp_tickets)
        assert tickets[0].effort == ""

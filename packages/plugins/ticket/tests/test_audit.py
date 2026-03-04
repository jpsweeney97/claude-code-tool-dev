"""Tests for centralized audit wrapper in engine_execute."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.ticket_engine_core import engine_execute


def _read_audit_lines(tickets_dir: Path, session_id: str) -> list[dict]:
    """Read all JSONL entries from the audit file for the given session."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit_file = tickets_dir / ".audit" / today / f"{session_id}.jsonl"
    if not audit_file.exists():
        return []
    lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
    return [json.loads(line) for line in lines if line.strip()]


_REQUIRED_FIELDS = {"ts", "action", "ticket_id", "session_id", "request_origin", "autonomy_mode", "result", "changes"}


class TestAuditAppend:
    """Tests for the audit trail written by engine_execute."""

    def test_audit_file_created_on_execute(self, tmp_tickets: Path) -> None:
        """engine_execute creates an audit file on first call."""
        session_id = "sess-create-1"
        engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test ticket", "problem": "Test problem"},
            session_id=session_id,
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        entries = _read_audit_lines(tmp_tickets, session_id)
        assert len(entries) >= 1, "Audit file should exist with at least one entry"

    def test_audit_attempt_started_before_result(self, tmp_tickets: Path) -> None:
        """First entry is attempt_started, second is the action result."""
        session_id = "sess-order-1"
        engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Order test", "problem": "Order problem"},
            session_id=session_id,
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        entries = _read_audit_lines(tmp_tickets, session_id)
        assert len(entries) == 2
        assert entries[0]["action"] == "attempt_started"
        assert entries[1]["action"] == "create"

    def test_audit_entry_schema(self, tmp_tickets: Path) -> None:
        """Each audit entry contains all required fields."""
        session_id = "sess-schema-1"
        engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Schema test", "problem": "Schema problem"},
            session_id=session_id,
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        entries = _read_audit_lines(tmp_tickets, session_id)
        assert len(entries) == 2
        for entry in entries:
            missing = _REQUIRED_FIELDS - set(entry.keys())
            assert not missing, f"Entry missing fields: {missing}"

    def test_audit_on_error_writes_result(self, tmp_tickets: Path) -> None:
        """On non-exception error (e.g., update non-existent ticket), audit still writes both entries."""
        session_id = "sess-error-1"
        resp = engine_execute(
            action="update",
            ticket_id="T-99999999-99",
            fields={"title": "Updated title"},
            session_id=session_id,
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        # The update should fail (ticket doesn't exist) but not raise
        entries = _read_audit_lines(tmp_tickets, session_id)
        assert len(entries) == 2
        assert entries[0]["action"] == "attempt_started"
        assert entries[1]["action"] == "update"
        # Result should reflect the error state, not None
        assert entries[1]["result"] is not None

    def test_audit_directory_creation(self, tmp_tickets: Path) -> None:
        """.audit directory is created if it doesn't exist."""
        session_id = "sess-dir-1"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_dir = tmp_tickets / ".audit" / today
        assert not audit_dir.exists(), "Audit dir should not exist before first call"

        engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Dir test", "problem": "Dir problem"},
            session_id=session_id,
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )

        assert audit_dir.exists(), "Audit dir should be created by engine_execute"
        audit_file = audit_dir / f"{session_id}.jsonl"
        assert audit_file.exists(), "Audit file should exist"

    def test_audit_multiple_executions_append(self, tmp_tickets: Path) -> None:
        """Multiple executions in same session append to same file (3 creates = 6 lines)."""
        session_id = "sess-multi-1"
        for i in range(3):
            engine_execute(
                action="create",
                ticket_id=None,
                fields={"title": f"Multi test {i}", "problem": f"Multi problem {i}"},
                session_id=session_id,
                request_origin="user",
                dedup_override=False,
                dependency_override=False,
                tickets_dir=tmp_tickets,
            )
        entries = _read_audit_lines(tmp_tickets, session_id)
        assert len(entries) == 6, f"Expected 6 entries (3 creates x 2), got {len(entries)}"
        # Verify alternating pattern
        for i in range(3):
            assert entries[i * 2]["action"] == "attempt_started"
            assert entries[i * 2 + 1]["action"] == "create"

    def test_audit_ts_is_iso_utc(self, tmp_tickets: Path) -> None:
        """Timestamps are ISO 8601 with timezone info."""
        session_id = "sess-ts-1"
        engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "TS test", "problem": "TS problem"},
            session_id=session_id,
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        entries = _read_audit_lines(tmp_tickets, session_id)
        for entry in entries:
            ts = entry["ts"]
            # Should parse as ISO 8601 with timezone
            parsed = datetime.fromisoformat(ts)
            assert parsed.tzinfo is not None, f"Timestamp {ts!r} should have timezone info"

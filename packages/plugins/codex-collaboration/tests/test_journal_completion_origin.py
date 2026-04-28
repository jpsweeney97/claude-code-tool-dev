"""Packet 1: OperationJournalEntry.completion_origin + decision=None relaxation."""

from __future__ import annotations

import json
from pathlib import Path

from server.journal import OperationJournal
from server.models import OperationJournalEntry


def test_completion_origin_field_exists_with_default_none() -> None:
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="completed",
        collaboration_id="c1",
        created_at="2026-04-24T12:00:00Z",
        repo_root="/tmp",
    )
    assert entry.completion_origin is None


def test_intent_accepts_decision_none(tmp_path: Path) -> None:
    journal = OperationJournal(plugin_data_path=tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="intent",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision=None,  # timeout-wake / internal-abort-wake
    )
    journal.write_phase(entry, session_id="s1")


def test_dispatched_accepts_decision_none(tmp_path: Path) -> None:
    journal = OperationJournal(plugin_data_path=tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="dispatched",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision=None,
        runtime_id="rt1",
        codex_thread_id="t1",
    )
    journal.write_phase(entry, session_id="s1")


def test_decision_non_string_non_none_still_rejected(tmp_path: Path) -> None:
    """Only None is permitted; a non-string non-None (e.g., dict, int) is
    still a schema violation per the narrow relaxation."""
    journal = OperationJournal(plugin_data_path=tmp_path)
    bad = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="intent",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision=42,  # type: ignore[arg-type]
    )
    journal.write_phase(bad, session_id="s1")
    diagnostics = journal.check_health(session_id="s1")
    violations = diagnostics.schema_violations
    assert len(violations) == 1
    assert "decision" in violations[0].detail


def test_completion_origin_worker_completed_round_trip(tmp_path: Path) -> None:
    journal = OperationJournal(plugin_data_path=tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="completed",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision="approve",
        completion_origin="worker_completed",
    )
    journal.write_phase(entry, session_id="s1")
    found = journal.check_idempotency("k1", session_id="s1")
    assert found is not None
    assert found.phase == "completed"
    assert found.completion_origin == "worker_completed"


def test_completion_origin_recovered_unresolved_round_trip(tmp_path: Path) -> None:
    journal = OperationJournal(plugin_data_path=tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="completed",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision="approve",
        completion_origin="recovered_unresolved",
    )
    journal.write_phase(entry, session_id="s1")
    found = journal.check_idempotency("k1", session_id="s1")
    assert found is not None
    assert found.phase == "completed"
    assert found.completion_origin == "recovered_unresolved"


def test_legacy_records_without_field_replay_as_none(tmp_path: Path) -> None:
    """Pre-Packet-1 records without completion_origin replay with None."""
    journal = OperationJournal(plugin_data_path=tmp_path)
    # Hand-write a legacy record to the correct path.
    operations_dir = tmp_path / "journal" / "operations"
    operations_dir.mkdir(parents=True, exist_ok=True)
    legacy = {
        "idempotency_key": "k1",
        "operation": "approval_resolution",
        "phase": "completed",
        "collaboration_id": "c1",
        "created_at": "t",
        "repo_root": "/tmp",
        "job_id": "j1",
        "request_id": "r1",
        "decision": "approve",
    }
    (operations_dir / "s1.jsonl").write_text(
        json.dumps(legacy, sort_keys=True) + "\n", encoding="utf-8"
    )
    found = journal.check_idempotency("k1", session_id="s1")
    assert found is not None
    assert found.completion_origin is None


def test_completion_origin_unknown_string_value_rejected(tmp_path: Path) -> None:
    """completion_origin must be one of the declared Literal values; arbitrary
    strings are schema violations surfaced via check_health()."""
    journal = OperationJournal(plugin_data_path=tmp_path)
    bad = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="completed",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision="approve",
        completion_origin="garbage",  # type: ignore[arg-type]
    )
    journal.write_phase(bad, session_id="s1")
    diagnostics = journal.check_health(session_id="s1")
    violations = diagnostics.schema_violations
    assert len(violations) == 1
    assert "completion_origin" in violations[0].detail


def test_completion_origin_non_string_rejected(tmp_path: Path) -> None:
    """completion_origin non-string non-None values are rejected by the
    optional-string type check, surfaced via check_health()."""
    journal = OperationJournal(plugin_data_path=tmp_path)
    bad = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="completed",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision="approve",
        completion_origin=42,  # type: ignore[arg-type]
    )
    journal.write_phase(bad, session_id="s1")
    diagnostics = journal.check_health(session_id="s1")
    violations = diagnostics.schema_violations
    assert len(violations) == 1
    assert "completion_origin" in violations[0].detail

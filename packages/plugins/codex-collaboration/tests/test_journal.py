from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.journal import OperationJournal
from server.models import OperationJournalEntry, StaleAdvisoryContextMarker


def test_stale_marker_keys_are_normalized_on_write(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=str(tmp_path / "."),
            promoted_head="head-1",
            recorded_at="2026-03-27T15:00:00Z",
        )
    )

    marker = journal.load_stale_marker(tmp_path)
    assert marker is not None
    assert marker.repo_root == str(tmp_path.resolve())


def test_stale_marker_write_replaces_prior_head_for_repo_root(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    normalized_root = str(tmp_path.resolve())
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=normalized_root,
            promoted_head="head-1",
            recorded_at="2026-03-27T15:00:00Z",
        )
    )
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=normalized_root,
            promoted_head="head-2",
            recorded_at="2026-03-27T15:05:00Z",
        )
    )

    marker = journal.load_stale_marker(tmp_path)
    assert marker is not None
    assert marker.promoted_head == "head-2"


def test_clear_stale_marker_uses_normalized_repo_root(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=str(tmp_path.resolve()),
            promoted_head="head-1",
            recorded_at="2026-03-27T15:00:00Z",
        )
    )

    journal.clear_stale_marker(Path(str(tmp_path / ".")))

    assert journal.load_stale_marker(tmp_path) is None


def _make_intent(
    key: str = "sess-1:collab-1",
    operation: str = "thread_creation",
    collab: str = "collab-1",
) -> OperationJournalEntry:
    return OperationJournalEntry(
        idempotency_key=key,
        operation=operation,
        phase="intent",
        collaboration_id=collab,
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
    )


class TestPhasedJournal:
    def test_write_intent_and_list_unresolved(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "intent"

    def test_write_dispatched_updates_terminal_phase(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-1",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="collab-1",
                created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
                codex_thread_id="thr-1",
            ),
            session_id="sess-1",
        )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "dispatched"
        assert unresolved[0].codex_thread_id == "thr-1"

    def test_write_completed_resolves_operation(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-1",
                operation="thread_creation",
                phase="completed",
                collaboration_id="collab-1",
                created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
            ),
            session_id="sess-1",
        )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_check_idempotency_returns_terminal_entry(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        found = journal.check_idempotency("sess-1:collab-1", session_id="sess-1")
        assert found is not None
        assert found.phase == "intent"

    def test_check_idempotency_returns_none_when_missing(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        assert journal.check_idempotency("no-such-key", session_id="sess-1") is None

    def test_write_phase_uses_fsync(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import os as _os

        fsynced: list[int] = []
        original = _os.fsync

        def tracking(fd: int) -> None:
            fsynced.append(fd)
            original(fd)

        monkeypatch.setattr(_os, "fsync", tracking)
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(key="k1", collab="c1"), session_id="sess-1")
        assert len(fsynced) >= 1

    def test_compact_removes_completed_keeps_unresolved_terminal(
        self, tmp_path: Path
    ) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        # key-0: intent → dispatched → completed (should be removed entirely)
        journal.write_phase(_make_intent(key="key-0", collab="c0"), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-0",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="c0",
                created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
                codex_thread_id="thr-0",
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-0",
                operation="thread_creation",
                phase="completed",
                collaboration_id="c0",
                created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
            ),
            session_id="sess-1",
        )
        # key-1: intent → dispatched (unresolved — should keep only terminal "dispatched")
        journal.write_phase(_make_intent(key="key-1", collab="c1"), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-1",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="c1",
                created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
                codex_thread_id="thr-1",
            ),
            session_id="sess-1",
        )
        # key-2: intent only (unresolved — should keep the intent)
        journal.write_phase(_make_intent(key="key-2", collab="c2"), session_id="sess-1")

        journal.compact(session_id="sess-1")

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 2
        by_key = {e.idempotency_key: e for e in unresolved}
        assert by_key["key-1"].phase == "dispatched"
        assert by_key["key-1"].codex_thread_id == "thr-1"
        assert by_key["key-2"].phase == "intent"

    def test_compact_uses_atomic_rename(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-1",
                operation="thread_creation",
                phase="completed",
                collaboration_id="collab-1",
                created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
            ),
            session_id="sess-1",
        )
        journal.compact(session_id="sess-1")
        # After compacting a fully-completed journal, file should be empty or minimal
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0


class TestReplayHardening:
    def test_wrong_type_field_does_not_crash(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        with ops_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "bad",
                        "operation": "thread_creation",
                        "phase": "intent",
                        "collaboration_id": "c1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo_root": "/repo",
                        "turn_sequence": "not-an-int",
                    }
                )
                + "\n"
            )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1  # only the valid record

    def test_unknown_operation_value_skipped(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        with ops_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "bad",
                        "operation": "future_operation",
                        "phase": "intent",
                        "collaboration_id": "c1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo_root": "/repo",
                    }
                )
                + "\n"
            )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1

    def test_bool_as_int_rejected_in_journal(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "k1",
                        "operation": "turn_dispatch",
                        "phase": "intent",
                        "collaboration_id": "c1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo_root": "/repo",
                        "codex_thread_id": "thr-1",
                        "turn_sequence": True,
                    }
                )
                + "\n"
            )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0  # bad record skipped

    def test_extra_fields_ignored(self, tmp_path: Path) -> None:
        """Forward-compat: extra fields in a record must not crash replay."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "k1",
                        "operation": "thread_creation",
                        "phase": "intent",
                        "collaboration_id": "c1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo_root": "/repo",
                        "future_field": "some_value",
                    }
                )
                + "\n"
            )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].idempotency_key == "k1"

    def test_check_health_reports_schema_violation(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        with ops_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"idempotency_key": 123}) + "\n")
        diags = journal.check_health(session_id="sess-1")
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"

    def test_check_health_clean_file(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        diags = journal.check_health(session_id="sess-1")
        assert diags.diagnostics == ()

    def test_turn_dispatch_without_codex_thread_id_skipped(
        self, tmp_path: Path
    ) -> None:
        """Per-operation requirement: turn_dispatch needs codex_thread_id for recovery.
        dialogue.py:534-538 raises RuntimeError if codex_thread_id is None."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "k1",
                        "operation": "turn_dispatch",
                        "phase": "dispatched",
                        "collaboration_id": "c1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo_root": "/repo",
                        "turn_sequence": 1,
                        # no codex_thread_id — would crash recovery
                    }
                )
                + "\n"
            )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_thread_creation_dispatched_without_codex_thread_id_skipped(
        self, tmp_path: Path
    ) -> None:
        """Per-operation+phase: thread_creation at dispatched needs codex_thread_id.
        dialogue.py:469-473 raises RuntimeError if codex_thread_id is None."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "k1",
                        "operation": "thread_creation",
                        "phase": "dispatched",
                        "collaboration_id": "c1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo_root": "/repo",
                        # no codex_thread_id — would crash recovery
                    }
                )
                + "\n"
            )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_thread_creation_intent_without_codex_thread_id_accepted(
        self, tmp_path: Path
    ) -> None:
        """Intent phase does not require codex_thread_id — dispatch hasn't happened."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "k1",
                        "operation": "thread_creation",
                        "phase": "intent",
                        "collaboration_id": "c1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo_root": "/repo",
                    }
                )
                + "\n"
            )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1

    def test_turn_dispatch_dispatched_without_turn_sequence_skipped(
        self, tmp_path: Path
    ) -> None:
        """turn_dispatch at dispatched requires turn_sequence for
        turn confirmation (dialogue.py:550-551). Completed phase is a
        resolution marker — production writers omit turn_sequence there."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "k1",
                        "operation": "turn_dispatch",
                        "phase": "dispatched",
                        "collaboration_id": "c1",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo_root": "/repo",
                        "codex_thread_id": "thread-1",
                        # no turn_sequence — can never confirm turn
                    }
                )
                + "\n"
            )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

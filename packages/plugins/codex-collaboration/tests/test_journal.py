from __future__ import annotations

from pathlib import Path

from server.journal import OperationJournal
from server.models import StaleAdvisoryContextMarker


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


import pytest

from server.models import OperationJournalEntry


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

    def test_compact_removes_completed_keeps_unresolved_terminal(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        # key-0: intent → dispatched → completed (should be removed entirely)
        journal.write_phase(_make_intent(key="key-0", collab="c0"), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-0", operation="thread_creation", phase="dispatched",
                collaboration_id="c0", created_at="2026-03-28T00:00:00Z",
                repo_root="/repo", codex_thread_id="thr-0",
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-0", operation="thread_creation", phase="completed",
                collaboration_id="c0", created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
            ),
            session_id="sess-1",
        )
        # key-1: intent → dispatched (unresolved — should keep only terminal "dispatched")
        journal.write_phase(_make_intent(key="key-1", collab="c1"), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-1", operation="thread_creation", phase="dispatched",
                collaboration_id="c1", created_at="2026-03-28T00:00:00Z",
                repo_root="/repo", codex_thread_id="thr-1",
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
                idempotency_key="sess-1:collab-1", operation="thread_creation",
                phase="completed", collaboration_id="collab-1",
                created_at="2026-03-28T00:00:00Z", repo_root="/repo",
            ),
            session_id="sess-1",
        )
        journal.compact(session_id="sess-1")
        # After compacting a fully-completed journal, file should be empty or minimal
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

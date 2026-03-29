"""Tests for the startup recovery coordinator."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.control_plane import ControlPlane
from server.dialogue import DialogueController
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.turn_store import TurnStore

from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _recovery_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal, TurnStore, FakeRuntimeSession]:
    """Wire a stack for recovery testing. Returns all components."""
    session = session or FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    uuids = iter(("rt-1", *(f"id-{i}" for i in range(200))))
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=lambda: next(uuids),
        journal=journal,
    )
    store = LineageStore(plugin_data, "sess-1")
    turn_store = TurnStore(plugin_data, "sess-1")
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id="sess-1",
        turn_store=turn_store,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"collab-{i}" for i in range(100))).__next__,
    )
    return controller, plane, store, journal, turn_store, session


class TestStartupRecoveryCoordinator:
    def test_reattaches_active_handle_with_clean_journal(self, tmp_path: Path) -> None:
        """An active handle with no unresolved journal entries still needs
        reattachment after restart (new runtime, stale thread binding)."""
        session = FakeRuntimeSession()
        controller, _, store, journal, _, session = _recovery_stack(tmp_path, session=session)

        start = controller.start(tmp_path)
        assert store.get(start.collaboration_id).status == "active"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.codex_thread_id == "thr-start-resumed"

    def test_journal_reconciled_before_reattach(self, tmp_path: Path) -> None:
        """Unresolved journal entries resolved first, then remaining active handles reattached."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _, session = _recovery_stack(tmp_path, session=session)

        start1 = controller.start(tmp_path)
        session.read_thread_response = None
        start2 = controller.start(tmp_path)

        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-1:thr-start:1",
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=start1.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-1",
                context_size=4096,
            ),
            session_id="sess-1",
        )

        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }

        controller.recover_startup()

        h1 = store.get(start1.collaboration_id)
        assert h1.status == "unknown"

        h2 = store.get(start2.collaboration_id)
        assert h2.status == "active"
        assert h2.codex_thread_id == "thr-start-resumed"

    def test_does_not_double_resume_handles_from_phase_1(self, tmp_path: Path) -> None:
        """Handles recovered by journal reconciliation (phase 1) are skipped
        during bulk reattach (phase 3) to avoid double-resume churn."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        controller, _, store, journal, _, session = _recovery_stack(tmp_path, session=session)

        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-recovered",
                operation="thread_creation",
                phase="intent",
                collaboration_id="collab-recovered",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-recovered",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="collab-recovered",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-recovered",
            ),
            session_id="sess-1",
        )

        resume_calls: list[str] = []
        original_resume = session.resume_thread

        def tracking_resume(thread_id: str) -> str:
            resume_calls.append(thread_id)
            return original_resume(thread_id)

        session.resume_thread = tracking_resume  # type: ignore[assignment]

        controller.recover_startup()

        recovered_resumes = [c for c in resume_calls if c == "thr-recovered"]
        assert len(recovered_resumes) == 1

    def test_quarantines_pre_fix_handle_with_completed_turns(self, tmp_path: Path) -> None:
        """Active handle with completed turns but no TurnStore entries is
        quarantined as unknown during startup."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        assert store.get(start.collaboration_id).status == "active"
        assert turn_store.get(start.collaboration_id, turn_sequence=1) is None

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_quarantines_post_fix_handle_with_missing_metadata(self, tmp_path: Path) -> None:
        """A post-fix handle with some TurnStore entries but fewer than completed
        turns is also quarantined."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                    {"id": "t2", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_does_not_quarantine_handle_with_no_completed_turns(self, tmp_path: Path) -> None:
        """Active handle with zero completed turns (just started, no replies yet)
        should be reattached normally, not quarantined."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start-resumed"

    def test_no_op_when_no_handles_or_journal(self, tmp_path: Path) -> None:
        """Startup recovery is safe on a fresh session with no data."""
        controller, _, _, _, _, _ = _recovery_stack(tmp_path)
        controller.recover_startup()  # should not raise

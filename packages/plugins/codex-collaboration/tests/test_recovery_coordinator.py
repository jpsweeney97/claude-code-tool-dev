"""Tests for the startup recovery coordinator."""

from __future__ import annotations

import json
from pathlib import Path

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
) -> tuple[
    DialogueController,
    ControlPlane,
    LineageStore,
    OperationJournal,
    TurnStore,
    FakeRuntimeSession,
]:
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
        controller, _, store, journal, _, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        assert store.get(start.collaboration_id).status == "active"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.codex_thread_id == "thr-start"
        assert session.resumed_threads == ["thr-start"]

    def test_journal_reconciled_before_reattach(self, tmp_path: Path) -> None:
        """Phase 1 resolves journal (quarantines unconfirmed turn_dispatch),
        then phase 2 reattaches both the clean active handle and the
        eligible unknown handle (zero completed turns → Option C)."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _, session = _recovery_stack(
            tmp_path, session=session
        )

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

        # Phase 1 quarantines h1 to unknown (unconfirmed turn).
        # Phase 2 picks up h1 as eligible unknown (zero completed) and reattaches.
        h1 = store.get(start1.collaboration_id)
        assert h1.status == "active"
        assert h1.codex_thread_id == "thr-start"

        h2 = store.get(start2.collaboration_id)
        assert h2.status == "active"
        assert h2.codex_thread_id == "thr-start"
        assert session.resumed_threads.count("thr-start") == 2

    def test_confirmed_turn_dispatch_does_not_suppress_phase_2_reattach(
        self, tmp_path: Path
    ) -> None:
        """Phase 1 confirms a turn_dispatch and repairs TurnStore metadata.
        Phase 2 must still resume the handle — turn_dispatch reconciliation
        does not perform reattach (unlike thread_creation dispatched)."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                ],
            },
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)

        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-1:thr-start:1",
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-1",
                context_size=4096,
            ),
            session_id="sess-1",
        )

        controller.recover_startup()

        # Phase 1 should have confirmed the turn and repaired metadata
        context_size = turn_store.get(start.collaboration_id, turn_sequence=1)
        assert context_size == 4096

        # Phase 2 should still resume the handle after phase-1 reconciliation.
        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start"
        assert session.resumed_threads == ["thr-start"]

    def test_does_not_double_resume_handles_from_phase_1(self, tmp_path: Path) -> None:
        """thread_creation recovered by phase 1 (full reattach with resume_thread)
        is skipped during phase 2 to avoid double-resume churn."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        controller, _, store, journal, _, session = _recovery_stack(
            tmp_path, session=session
        )

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

    def test_quarantines_pre_fix_handle_with_completed_turns(
        self, tmp_path: Path
    ) -> None:
        """Active handle with completed turns but no TurnStore entries is
        quarantined as unknown during startup."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
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

    def test_quarantines_post_fix_handle_with_missing_metadata(
        self, tmp_path: Path
    ) -> None:
        """A post-fix handle with some TurnStore entries but fewer than completed
        turns is also quarantined."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                    {
                        "id": "t2",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
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

    def test_does_not_quarantine_handle_with_no_completed_turns(
        self, tmp_path: Path
    ) -> None:
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
        assert handle.codex_thread_id == "thr-start"
        assert session.resumed_threads == ["thr-start"]

    def test_reattaches_unknown_handle_with_no_completed_turns(
        self, tmp_path: Path
    ) -> None:
        """Unknown handle with zero completed turns: eligible for reattach.
        No metadata completeness check needed."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, _, session = _recovery_stack(tmp_path, session=session)

        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start"
        assert session.resumed_threads == ["thr-start"]

    def test_reattaches_unknown_handle_with_complete_metadata(
        self, tmp_path: Path
    ) -> None:
        """Unknown handle with completed turns and complete TurnStore metadata:
        eligible for reattach, restored to active."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                ],
            },
        }
        controller, _, store, _, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        # Write complete metadata, then mark unknown
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        store.update_status(start.collaboration_id, "unknown")

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start"
        assert session.resumed_threads == ["thr-start"]

    def test_keeps_unknown_handle_unknown_when_metadata_incomplete(
        self, tmp_path: Path
    ) -> None:
        """Unknown handle with completed turns but missing TurnStore entries:
        not eligible for reattach, stays unknown."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                    {
                        "id": "t2",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                ],
            },
        }
        controller, _, store, _, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        # Only 1 of 2 metadata entries — incomplete
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        store.update_status(start.collaboration_id, "unknown")

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_keeps_unknown_handle_unknown_when_reattach_fails(
        self, tmp_path: Path
    ) -> None:
        """Unknown handle where read_thread or resume_thread raises:
        stays unknown. Exception does not propagate."""
        session = FakeRuntimeSession(initialize_error=RuntimeError("codex unreachable"))
        controller, _, store, _, _, session = _recovery_stack(tmp_path, session=session)

        # Manually create an unknown handle (can't use start() with initialize_error)
        from server.models import CollaborationHandle

        handle = CollaborationHandle(
            collaboration_id="collab-0",
            capability_class="advisory",
            runtime_id="rt-old",
            codex_thread_id="thr-start",
            claude_session_id="sess-1",
            repo_root=str(tmp_path.resolve()),
            created_at="2026-03-29T00:00:00Z",
            status="unknown",
        )
        store.create(handle)

        # Should not raise
        controller.recover_startup()

        assert store.get("collab-0").status == "unknown"

    def test_no_op_when_no_handles_or_journal(self, tmp_path: Path) -> None:
        """Startup recovery is safe on a fresh session with no data."""
        controller, _, _, _, _, _ = _recovery_stack(tmp_path)
        controller.recover_startup()  # should not raise

    def test_malformed_journal_terminal_row_falls_back_to_earlier(
        self, tmp_path: Path
    ) -> None:
        """When a completed terminal row is malformed and skipped by replay,
        the earlier valid row becomes the terminal phase. Recovery processes
        the fallback row deterministically."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        cid = start.collaboration_id

        # Valid turn_dispatch intent
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-1:thr-start:1",
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=cid,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-1",
                context_size=4096,
            ),
            session_id="sess-1",
        )

        # Inject malformed "completed" terminal row for same idempotency key.
        # turn_sequence is a string → SchemaViolation → row skipped.
        # Last-write-wins falls back to the intent row.
        ops_path = tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        with ops_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": "rt-1:thr-start:1",
                        "operation": "turn_dispatch",
                        "phase": "completed",
                        "collaboration_id": cid,
                        "created_at": "2026-03-28T00:01:00Z",
                        "repo_root": str(tmp_path.resolve()),
                        "codex_thread_id": "thr-start",
                        "turn_sequence": "not-an-int",
                    }
                )
                + "\n"
            )

        # Prove the malformed row was actually skipped: check_health reports
        # a schema_violation, and list_unresolved sees the intent (not completed).
        diags = journal.check_health(session_id="sess-1")
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "intent"

        # Recovery should not crash. The intent row becomes the terminal phase.
        # Phase 1: turn_dispatch intent with zero completed turns → quarantine
        # to 'unknown'. Phase 2: unknown handle with zero completed turns →
        # eligible for reattach → restored to 'active'.
        controller.recover_startup()

        handle = store.get(cid)
        assert handle is not None
        assert handle.status == "active"

    def test_malformed_turn_metadata_overwrite_survives_in_read(
        self, tmp_path: Path
    ) -> None:
        """A malformed TurnStore overwrite row is skipped. dialogue.read()
        uses the last valid context_size for that (cid, turn_sequence)."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                ],
            },
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        cid = start.collaboration_id

        # Write valid turn metadata
        turn_store.write(cid, turn_sequence=1, context_size=4096)

        # Inject malformed overwrite for same (cid, turn_sequence).
        # turn_sequence is a string → SchemaViolation → row skipped.
        # TurnStore last-write-wins keeps the valid row (4096).
        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "collaboration_id": cid,
                        "turn_sequence": "not-an-int",
                        "context_size": 9999,
                    }
                )
                + "\n"
            )

        # dialogue.read() should use the valid metadata (4096), not crash
        result = controller.read(cid)
        assert len(result.turns) == 1
        assert result.turns[0].context_size == 4096

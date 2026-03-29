"""Integration tests for the R2 dialogue foundation.

Tests end-to-end flows and acceptance gates from delivery.md §R2.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.control_plane import ControlPlane
from server.dialogue import DialogueController
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import OperationJournalEntry
from server.turn_store import TurnStore

from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _full_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal, FakeRuntimeSession]:
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
    dialogue_uuids = iter((f"collab-{i}" for i in range(100)))
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id="sess-1",
        repo_identity_loader=_repo_identity,
        uuid_factory=lambda: next(dialogue_uuids),
        turn_store=turn_store,
    )
    return controller, plane, store, journal, session


class TestEndToEndDialogueFlow:
    """Acceptance gate: start → reply → reply → read."""

    def test_full_dialogue_lifecycle(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('hello')\n", encoding="utf-8")
        controller, _, store, journal, session = _full_stack(tmp_path)

        # Start
        start = controller.start(tmp_path)
        assert start.status == "active"

        # Reply 1
        r1 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
        assert r1.turn_sequence == 1
        assert r1.context_size > 0

        # Reply 2
        r2 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Follow up on first finding",
            explicit_paths=(Path("focus.py"),),
        )
        assert r2.turn_sequence == 2

        # Read
        read = controller.read(start.collaboration_id)
        assert read.collaboration_id == start.collaboration_id
        assert read.status == "active"

        # Handle persisted
        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.codex_thread_id == "thr-start"

        # Journal clean (all operations completed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0


class TestLineageStoreCrashRecovery:
    """Acceptance gate: lineage store persists and recovers after crash."""

    def test_handles_survive_simulated_crash(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _full_stack(tmp_path)

        start = controller.start(tmp_path)
        # Simulate crash: destroy in-memory state, create new store instance
        del store
        store2 = LineageStore(tmp_path / "plugin-data", "sess-1")
        handle = store2.get(start.collaboration_id)
        assert handle is not None
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start"

    def test_incomplete_trailing_record_discarded_on_recovery(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _full_stack(tmp_path)
        start = controller.start(tmp_path)

        # Simulate crash mid-write to lineage store
        store_path = (tmp_path / "plugin-data" / "lineage" / "sess-1" / "handles.jsonl")
        with store_path.open("a", encoding="utf-8") as f:
            f.write('{"op": "update_status", "collaboration_id": "' + start.collaboration_id + '", "stat')

        store2 = LineageStore(tmp_path / "plugin-data", "sess-1")
        handle = store2.get(start.collaboration_id)
        assert handle is not None
        assert handle.status == "active"  # incomplete update_status discarded


class TestJournalIdempotency:
    """Acceptance gate: turns journaled before dispatch, replayed idempotently."""

    def test_journal_entry_written_before_dispatch(self, tmp_path: Path) -> None:
        """Verify journal-before-dispatch ordering by injecting a crash between
        journal write and thread creation."""

        class CrashOnStartThread(FakeRuntimeSession):
            def start_thread(self) -> str:
                raise RuntimeError("simulated crash during thread/start")

        crashing_session = CrashOnStartThread()
        controller, _, _, journal, _ = _full_stack(tmp_path, session=crashing_session)

        with pytest.raises(RuntimeError, match="simulated crash"):
            controller.start(tmp_path)

        # Journal intent entry survives because it was written BEFORE dispatch
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].operation == "thread_creation"
        assert unresolved[0].phase == "intent"

    def test_crash_after_dispatch_leaves_dispatched_entry(self, tmp_path: Path) -> None:
        """Crash after thread/start but before lineage persist. Journal has dispatched entry."""
        controller, _, store, journal, _ = _full_stack(tmp_path)

        # Start succeeds (creates intent + dispatched + handle + completed normally)
        start = controller.start(tmp_path)

        # Now simulate: a second start where crash happens after dispatch but before lineage
        # We test this indirectly via recovery — manually write dispatched entry
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-1",
                operation="thread_creation",
                phase="intent",
                collaboration_id="orphan-1",
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-1",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="orphan-1",
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-orphan",
            ),
            session_id="sess-1",
        )

        # Recovery reattaches via thread/read + thread/resume, then persists handle
        recovered = controller.recover_pending_operations()
        assert "orphan-1" in recovered
        handle = store.get("orphan-1")
        assert handle is not None
        assert handle.codex_thread_id == "thr-orphan-resumed"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_turn_dispatch_crash_and_recovery(self, tmp_path: Path) -> None:
        """Full crash-and-recover cycle for turn dispatch."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class CrashOnSecondRunTurn(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self._turn_calls = 0

            def run_turn(self, **kwargs: object) -> object:
                self._turn_calls += 1
                if self._turn_calls <= 1:
                    return super().run_turn(**kwargs)
                raise RuntimeError("simulated crash during turn")

        session = CrashOnSecondRunTurn()
        controller, _, store, journal, _ = _full_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        r1 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn succeeds",
            explicit_paths=(Path("focus.py"),),
        )
        assert r1.turn_sequence == 1

        # Second reply crashes — intent entry survives (dispatched never written)
        with pytest.raises(RuntimeError, match="simulated crash during turn"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Second turn crashes",
                explicit_paths=(Path("focus.py"),),
            )

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].operation == "turn_dispatch"
        assert unresolved[0].phase == "intent"

        # intent-only turn_dispatch with no thread/read confirmation → unknown
        controller.recover_pending_operations()
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"


class TestAuditEvents:
    """Acceptance gate: audit events emitted for dialogue turns."""

    def test_dialogue_lifecycle_emits_audit_events(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, journal, _ = _full_stack(tmp_path)

        start = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]

        # No dialogue_start action — thread creation is not a trust boundary crossing
        actions = [e["action"] for e in events]
        assert "dialogue_start" not in actions
        # dialogue_turn IS emitted per contracts.md §Audit Event Actions
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) >= 1
        assert turn_events[0]["collaboration_id"] == start.collaboration_id
        assert "runtime_id" in turn_events[0]


class TestTurnStoreWriteOrdering:
    """The metadata store write must land before journal completed.
    A crash in that window must leave the journal unresolved so recovery can repair."""

    def test_crash_after_store_write_before_completed_is_recoverable(
        self, tmp_path: Path
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession()
        controller, plane, store, journal, session = _full_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # Perform a normal reply to establish one completed turn
        r1 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert r1.turn_sequence == 1

        # Now manually simulate a partial second reply:
        # Write intent + dispatched + store entry, but NOT completed
        turn_store = TurnStore(tmp_path / "plugin-data", "sess-1")
        idem_key = "rt-1:thr-start:2"
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idem_key,
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:02:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=2,
                runtime_id="rt-1",
                context_size=5000,
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idem_key,
                operation="turn_dispatch",
                phase="dispatched",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:02:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=2,
                runtime_id="rt-1",
                context_size=5000,
            ),
            session_id="sess-1",
        )
        # Store write landed (before completed)
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=5000)

        # Journal is unresolved (dispatched, not completed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].idempotency_key == idem_key

        # Configure thread/read to confirm 2 completed turns
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                    {"id": "t2", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }

        # Recovery confirms the turn and resolves the journal
        controller.recover_pending_operations()
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

        # Store entry survived — read can use it
        assert turn_store.get(start.collaboration_id, turn_sequence=2) == 5000


class TestNoForkInR2:
    """Acceptance gate: no R2 path depends on fork."""

    def test_dialogue_controller_has_no_fork_method(self) -> None:
        assert not hasattr(DialogueController, "fork")

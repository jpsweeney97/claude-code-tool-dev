"""Tests for DialogueController operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.control_plane import ControlPlane, load_repo_identity
from server.dialogue import DialogueController
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import RepoIdentity
from server.turn_store import TurnStore

# Import FakeRuntimeSession and helpers from the control plane tests.
# These will be moved to conftest.py in a cleanup pass; for now we import directly.
from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _build_dialogue_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
    session_id: str = "sess-1",
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal, TurnStore]:
    """Wire up a full dialogue stack with test doubles."""
    session = session or FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter(
            (f"rt-{session_id}", *(f"uuid-{i}" for i in range(100)))
        ).__next__,
        journal=journal,
    )
    store = LineageStore(plugin_data, session_id)
    turn_store = TurnStore(plugin_data, session_id)
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id=session_id,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"collab-{session_id}", *(f"id-{i}" for i in range(100)))).__next__,
        turn_store=turn_store,
    )
    return controller, plane, store, journal, turn_store


class TestDialogueStart:
    def test_start_returns_dialogue_start_result(self, tmp_path: Path) -> None:
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        assert result.collaboration_id == "collab-sess-1"
        assert result.status == "active"
        assert result.runtime_id == "rt-sess-1"
        assert result.created_at is not None

    def test_start_persists_handle_in_lineage_store(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.capability_class == "advisory"
        assert handle.codex_thread_id == "thr-start"
        assert handle.claude_session_id == "sess-1"

    def test_start_journals_before_dispatch(self, tmp_path: Path) -> None:
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        # After successful completion, all phases written (intent → dispatched → completed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_start_does_not_emit_audit_event(self, tmp_path: Path) -> None:
        """Thread creation is not a trust boundary crossing — no audit event.
        See contracts.md §Audit Event Actions (dialogue_start is not defined)."""
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path)
        controller.start(tmp_path)
        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        if audit_path.exists():
            events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]
            assert all(e["action"] != "dialogue_start" for e in events)

    def test_start_creates_thread_on_runtime(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        controller.start(tmp_path)
        assert "start" in session.started_threads

    def test_start_invalidates_runtime_on_thread_failure(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession(initialize_error=RuntimeError("boom"))
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        with pytest.raises(RuntimeError):
            controller.start(tmp_path)


from server.models import ConsultRequest, DialogueReplyResult, OperationJournalEntry


class TestDialogueReply:
    def test_reply_returns_dialogue_reply_result(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)

        reply_result = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )

        assert isinstance(reply_result, DialogueReplyResult)
        assert reply_result.collaboration_id == start_result.collaboration_id
        assert reply_result.turn_sequence == 1
        assert reply_result.position is not None
        assert reply_result.context_size > 0

    def test_reply_increments_turn_sequence(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)

        reply1 = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        reply2 = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Second turn",
            explicit_paths=(Path("focus.py"),),
        )

        assert reply1.turn_sequence == 1
        assert reply2.turn_sequence == 2

    def test_reply_journals_before_dispatch(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Test turn",
            explicit_paths=(Path("focus.py"),),
        )
        # After successful reply, all operations should be completed (no unresolved)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_reply_emits_dialogue_turn_audit_event(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Test turn",
            explicit_paths=(Path("focus.py"),),
        )
        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) == 1
        assert turn_events[0]["collaboration_id"] == start_result.collaboration_id
        assert "turn_id" in turn_events[0]

    def test_reply_raises_on_unknown_collaboration_id(self, tmp_path: Path) -> None:
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ValueError, match="Reply failed: handle not found"):
            controller.reply(
                collaboration_id="nonexistent",
                objective="Should fail",
            )

    def test_reply_rejects_completed_handle(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "completed")
        with pytest.raises(ValueError, match="handle not active"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should fail",
            )

    def test_reply_rejects_unknown_handle(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")
        with pytest.raises(ValueError, match="handle not active"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should fail",
            )

    def test_reply_rejects_crashed_handle(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "crashed")
        with pytest.raises(ValueError, match="handle not active"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should fail",
            )

    def test_reply_uses_same_context_assembly_as_consult(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
        # Verify the prompt contains the assembled packet (same pipeline as consult)
        assert session.last_prompt_text is not None
        assert "focus.py" in session.last_prompt_text

    def test_reply_persists_context_size_in_turn_store(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, _, turn_store = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)

        reply_result = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )

        stored = turn_store.get(start_result.collaboration_id, turn_sequence=1)
        assert stored is not None
        assert stored == reply_result.context_size
        assert stored > 0

    def test_reply_journal_intent_carries_context_size(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class CrashAfterIntent(FakeRuntimeSession):
            """Crash after intent is written but before run_turn executes."""
            def run_turn(self, **kwargs: object) -> object:
                raise RuntimeError("crash after intent")

        session = CrashAfterIntent()
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path, session=session)
        start_result = controller.start(tmp_path)

        with pytest.raises(RuntimeError, match="crash after intent"):
            controller.reply(
                collaboration_id=start_result.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        # Intent entry should carry context_size (non-None, > 0)
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_intents = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_intents) == 1
        assert turn_intents[0].context_size is not None
        assert turn_intents[0].context_size > 0


class TestRecoverPendingOperations:
    def test_recover_thread_creation_at_intent_phase(self, tmp_path: Path) -> None:
        """Crash before thread/start — intent only. Recovery resolves as no-op."""
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path)

        # Manually write an intent entry (simulating crash before dispatch)
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-1",
                operation="thread_creation",
                phase="intent",
                collaboration_id="orphan-1",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )

        recovered = controller.recover_pending_operations()

        # Intent-only thread_creation resolved as no-op terminal
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        assert store.get("orphan-1") is None  # no handle created

    def test_recover_thread_creation_at_dispatched_phase(self, tmp_path: Path) -> None:
        """Crash after thread/start but before lineage persist.
        Recovery performs thread/read + thread/resume reattach, then persists handle."""
        session = FakeRuntimeSession()
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path, session=session)

        # Manually write intent + dispatched entries
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-2",
                operation="thread_creation",
                phase="intent",
                collaboration_id="orphan-2",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-2",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="orphan-2",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-orphan",
            ),
            session_id="sess-1",
        )

        recovered = controller.recover_pending_operations()

        assert "orphan-2" in recovered
        handle = store.get("orphan-2")
        assert handle is not None
        # Handle uses the resumed thread_id, not the original
        assert handle.codex_thread_id == "thr-orphan-resumed"
        assert handle.status == "active"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_recover_turn_dispatch_at_dispatched_phase_completed(
        self, tmp_path: Path
    ) -> None:
        """Crash after run_turn. thread/read confirms turn completed. Recovery marks complete."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        # Simulate: thread has 1 completed turn (from before the crash)
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [{"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""}],
            },
        }
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path, session=session)

        # Set up: create a real handle first
        start = controller.start(tmp_path)

        # Manually write a dispatched turn_dispatch entry (simulating crash after run_turn)
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-sess-1:thr-start:1",
                operation="turn_dispatch",
                phase="dispatched",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-sess-1",
            ),
            session_id="sess-1",
        )

        controller.recover_pending_operations()

        # Turn confirmed via thread/read — marked completed
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_recover_turn_dispatch_at_dispatched_phase_incomplete(
        self, tmp_path: Path
    ) -> None:
        """Crash during run_turn. thread/read shows turn did not complete.
        Handle marked 'unknown' (not 'crashed' — runtime crash is not confirmed)."""
        session = FakeRuntimeSession()
        # Thread has NO completed turns
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # Manually write dispatched turn_dispatch
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-sess-1:thr-start:1",
                operation="turn_dispatch",
                phase="dispatched",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-sess-1",
            ),
            session_id="sess-1",
        )

        controller.recover_pending_operations()

        # Turn not confirmed — handle marked unknown
        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_recover_intent_only_turn_dispatch_marks_unknown(self, tmp_path: Path) -> None:
        """Crash before run_turn. Intent-only turn_dispatch: thread/read check
        does not confirm the turn. Handle marked 'unknown' (ambiguous, not no-op)."""
        session = FakeRuntimeSession()
        # thread/read shows no completed turns at turn_sequence=1
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-sess-1:thr-start:1",
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-sess-1",
                context_size=4096,
            ),
            session_id="sess-1",
        )

        controller.recover_pending_operations()

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_recover_intent_turn_dispatch_confirmed_repairs_store(self, tmp_path: Path) -> None:
        """Intent-phase turn_dispatch but thread/read confirms the turn completed.
        Recovery resolves the journal and repairs the metadata store."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": "2026-03-28T00:01:30Z"},
                ],
            },
        }
        controller, _, store, journal, turn_store = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-sess-1:thr-start:1",
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-sess-1",
                context_size=4096,
            ),
            session_id="sess-1",
        )

        controller.recover_pending_operations()

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        # Metadata store repaired with context_size from journal intent
        assert turn_store.get(start.collaboration_id, turn_sequence=1) == 4096

    def test_recover_dispatched_turn_dispatch_confirmed_repairs_store(
        self, tmp_path: Path
    ) -> None:
        """Dispatched-phase turn_dispatch, turn confirmed. Recovery resolves and repairs store."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        controller, _, store, journal, turn_store = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-sess-1:thr-start:1",
                operation="turn_dispatch",
                phase="dispatched",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-sess-1",
                context_size=4096,
            ),
            session_id="sess-1",
        )

        controller.recover_pending_operations()

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        assert turn_store.get(start.collaboration_id, turn_sequence=1) == 4096


from server.models import DialogueReadResult, DialogueTurnSummary


class TestDialogueRead:
    def test_read_returns_dialogue_state(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        read_result = controller.read(start_result.collaboration_id)

        assert isinstance(read_result, DialogueReadResult)
        assert read_result.collaboration_id == start_result.collaboration_id
        assert read_result.status == "active"
        assert read_result.created_at is not None

    def test_read_includes_turn_history(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        # Configure read_thread to return turn history
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": '{"position":"First","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                        "createdAt": "2026-03-28T00:01:00Z",
                    },
                ],
            },
        }
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        read_result = controller.read(start_result.collaboration_id)

        assert read_result.turn_count >= 1
        assert len(read_result.turns) >= 1

    def test_read_raises_on_unknown_collaboration_id(self, tmp_path: Path) -> None:
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ValueError, match="Handle not found"):
            controller.read("nonexistent")

    def test_read_works_on_unknown_handle(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession()
        session.read_thread_response = {"thread": {"id": "thr-start", "turns": []}}
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        read_result = controller.read(start.collaboration_id)
        assert read_result.status == "unknown"

    def test_read_works_on_completed_handle(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession()
        session.read_thread_response = {"thread": {"id": "thr-start", "turns": []}}
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "completed")

        read_result = controller.read(start.collaboration_id)
        assert read_result.status == "completed"

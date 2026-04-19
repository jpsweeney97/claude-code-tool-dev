"""Tests for DialogueController operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.control_plane import ControlPlane
from server.dialogue import (
    CommittedTurnFinalizationError,
    CommittedTurnParseError,
    DialogueController,
)
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import DialogueReadResult, DialogueReplyResult, OperationJournalEntry
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
        uuid_factory=iter(
            (f"collab-{session_id}", *(f"id-{i}" for i in range(100)))
        ).__next__,
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
        controller.start(tmp_path)
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
            events = [
                json.loads(line) for line in audit_path.read_text().strip().split("\n")
            ]
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
        events = [
            json.loads(line) for line in audit_path.read_text().strip().split("\n")
        ]
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) == 1
        assert turn_events[0]["collaboration_id"] == start_result.collaboration_id
        assert "turn_id" in turn_events[0]

    def test_reply_emits_outcome_record(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Test turn",
            explicit_paths=(Path("focus.py"),),
        )
        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines]
        dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
        assert len(dialogue_outcomes) == 1
        assert dialogue_outcomes[0]["collaboration_id"] == start_result.collaboration_id
        assert dialogue_outcomes[0]["turn_id"] is not None
        assert dialogue_outcomes[0]["turn_sequence"] == 1
        assert dialogue_outcomes[0]["context_size"] > 0
        assert dialogue_outcomes[0]["repo_root"] == str(tmp_path.resolve())
        assert dialogue_outcomes[0]["policy_fingerprint"] is not None

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


class TestDialogueFinalizationFailures:
    def test_reply_turn_store_failure_raises_finalization_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, store, journal, turn_store = _build_dialogue_stack(tmp_path)
        start = controller.start(tmp_path)

        def _boom(*args: object, **kwargs: object) -> None:
            raise OSError("turn store boom")

        monkeypatch.setattr(turn_store, "write", _boom)

        with pytest.raises(CommittedTurnFinalizationError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        assert store.get(start.collaboration_id).status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "dispatched"

    def test_reply_audit_failure_raises_finalization_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path)
        start = controller.start(tmp_path)

        def _boom(*args: object, **kwargs: object) -> None:
            raise OSError("audit boom")

        monkeypatch.setattr(journal, "append_dialogue_audit_event_once", _boom)

        with pytest.raises(CommittedTurnFinalizationError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        assert store.get(start.collaboration_id).status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "dispatched"

    def test_reply_outcome_failure_raises_finalization_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path)
        start = controller.start(tmp_path)

        def _boom(*args: object, **kwargs: object) -> None:
            raise OSError("outcome boom")

        monkeypatch.setattr(journal, "append_dialogue_outcome_once", _boom)

        with pytest.raises(CommittedTurnFinalizationError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        assert store.get(start.collaboration_id).status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "dispatched"

    def test_reply_completed_write_failure_is_recoverable_without_duplicates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path)
        start = controller.start(tmp_path)
        original_write_phase = journal.write_phase

        def _fail_completed(entry: OperationJournalEntry, *, session_id: str) -> None:
            if entry.phase == "completed":
                raise OSError("journal boom")
            original_write_phase(entry, session_id=session_id)

        monkeypatch.setattr(journal, "write_phase", _fail_completed)

        with pytest.raises(CommittedTurnFinalizationError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        assert store.get(start.collaboration_id).status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "dispatched"

        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert len(audit_path.read_text(encoding="utf-8").strip().split("\n")) == 1
        assert len(outcomes_path.read_text(encoding="utf-8").strip().split("\n")) == 1

        monkeypatch.setattr(journal, "write_phase", original_write_phase)
        controller.recover_pending_operations()

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        assert len(audit_path.read_text(encoding="utf-8").strip().split("\n")) == 1
        assert len(outcomes_path.read_text(encoding="utf-8").strip().split("\n")) == 1


class TestRecoverPendingOperations:
    def test_recover_startup_logs_diagnostic_when_reattach_fails(
        self,
        tmp_path: Path,
        monkeypatch,
        capsys,
    ) -> None:
        session = FakeRuntimeSession()
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        def _raise_read_thread(thread_id: str) -> dict:
            raise RuntimeError("read boom")

        monkeypatch.setattr(session, "read_thread", _raise_read_thread)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.status == "unknown"
        assert "recover_startup failed: read boom" in capsys.readouterr().err

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

        controller.recover_pending_operations()

        # Intent-only thread_creation resolved as no-op terminal
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        assert store.get("orphan-1") is None  # no handle created

    def test_recover_thread_creation_at_dispatched_phase(self, tmp_path: Path) -> None:
        """Crash after thread/start but before lineage persist.
        Recovery performs thread/read + thread/resume reattach, then persists handle."""
        session = FakeRuntimeSession()
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )

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
        assert handle.codex_thread_id == "thr-orphan"
        assert session.resumed_threads == ["thr-orphan"]
        assert handle.status == "active"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_recover_thread_creation_dispatched_phase_requires_thread_id(
        self, tmp_path: Path
    ) -> None:
        """A dispatched thread_creation entry without a thread ID is filtered at replay.

        With replay-level validation, the record is silently skipped as a
        schema_violation (missing codex_thread_id). Recovery never sees it.
        """
        controller, _, store, journal, _ = _build_dialogue_stack(tmp_path)

        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-3",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="orphan-3",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )

        # Record is filtered at replay — recovery has nothing to process
        controller.recover_pending_operations()

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        assert store.get("orphan-3") is None

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
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    }
                ],
            },
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )

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
        Handle marked 'unknown' and unresolved phase preserved for later recovery."""
        session = FakeRuntimeSession()
        # Thread has NO completed turns
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
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
        assert len(unresolved) == 1
        assert unresolved[0].phase == "dispatched"

    def test_recover_turn_dispatch_logs_diagnostic_when_thread_read_fails(
        self,
        tmp_path: Path,
        monkeypatch,
        capsys,
    ) -> None:
        session = FakeRuntimeSession()
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path,
            session=session,
        )
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
            ),
            session_id="sess-1",
        )

        def _raise_read_thread(thread_id: str) -> dict:
            raise RuntimeError("thread read boom")

        monkeypatch.setattr(session, "read_thread", _raise_read_thread)

        controller.recover_pending_operations()

        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "dispatched"
        assert (
            "recover_turn_dispatch failed: thread read boom" in capsys.readouterr().err
        )

    def test_recover_intent_only_turn_dispatch_marks_unknown(
        self, tmp_path: Path
    ) -> None:
        """Crash before run_turn. Intent-only turn_dispatch: thread/read check
        does not confirm the turn. Handle marked 'unknown' and intent preserved."""
        session = FakeRuntimeSession()
        # thread/read shows no completed turns at turn_sequence=1
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
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
        assert len(unresolved) == 1
        assert unresolved[0].phase == "intent"
        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_recover_intent_turn_dispatch_confirmed_repairs_store(
        self, tmp_path: Path
    ) -> None:
        """Intent-phase turn_dispatch but thread/read confirms the turn completed.
        Recovery resolves the journal and repairs the metadata store."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-03-28T00:01:30Z",
                    },
                ],
            },
        }
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
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
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                ],
            },
        }
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
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

    def test_recover_dispatched_turn_dispatch_confirmed_emits_audit(
        self, tmp_path: Path
    ) -> None:
        """Confirmed startup recovery must emit dialogue_turn audit when turn_id is recoverable."""
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
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path, session=session)
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

        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [
            json.loads(line) for line in audit_path.read_text().strip().split("\n")
        ]
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) == 1
        assert turn_events[0]["collaboration_id"] == start.collaboration_id
        assert turn_events[0]["runtime_id"] == "rt-sess-1"
        assert turn_events[0]["turn_id"] == "t1"
        assert turn_events[0]["context_size"] == 4096


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
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start_result = controller.start(tmp_path)
        reply_result = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        # Configure read_thread AFTER reply() so _derive_turn_sequence is unaffected
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

        read_result = controller.read(start_result.collaboration_id)

        assert read_result.turn_count >= 1
        assert len(read_result.turns) >= 1
        # context_size is now real, not 0
        assert read_result.turns[0].context_size == reply_result.context_size

    def test_read_extracts_position_from_nested_agent_message_item(
        self, tmp_path: Path
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start_result = controller.start(tmp_path)
        reply_result = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "items": [
                            {
                                "id": "item-1",
                                "type": "userMessage",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "First turn",
                                        "text_elements": [],
                                    }
                                ],
                            },
                            {
                                "id": "item-2",
                                "type": "agentMessage",
                                "text": '{"position":"Nested","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                            },
                        ],
                    },
                ],
            },
        }

        read_result = controller.read(start_result.collaboration_id)

        assert read_result.turn_count == 1
        assert read_result.turns[0].position == "Nested"
        assert read_result.turns[0].context_size == reply_result.context_size
        assert read_result.turns[0].timestamp == ""

    def test_read_raises_on_unknown_collaboration_id(self, tmp_path: Path) -> None:
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ValueError, match="Read failed: handle not found"):
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

    def test_read_returns_real_context_size_from_store(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        controller, _, _, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        reply_result = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        # Configure thread/read to match the completed turn
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": '{"position":"Pos","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                        "createdAt": "2026-03-28T00:01:00Z",
                    },
                ],
            },
        }

        read_result = controller.read(start.collaboration_id)
        assert read_result.turn_count == 1
        assert len(read_result.turns) == 1
        assert read_result.turns[0].context_size == reply_result.context_size
        assert read_result.turns[0].context_size > 0

    def test_read_raises_on_missing_metadata_for_post_fix_turn(
        self, tmp_path: Path
    ) -> None:
        """In a post-fix session (some turns have metadata), a completed turn
        with no metadata store entry is an integrity failure."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": '{"position":"Pos","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                        "createdAt": "2026-03-28T00:01:00Z",
                    },
                    {
                        "id": "turn-2",
                        "status": "completed",
                        "agentMessage": '{"position":"Pos2","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                        "createdAt": "2026-03-28T00:02:00Z",
                    },
                ],
            },
        }
        controller, _, _, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Write metadata for turn 1 but NOT turn 2 — partial metadata = post-fix session
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)

        with pytest.raises(RuntimeError, match="Turn metadata integrity"):
            controller.read(start.collaboration_id)

    def test_read_raises_on_pre_fix_turn_without_metadata(self, tmp_path: Path) -> None:
        """A pre-fix turn (no TurnStore entry) triggers the same integrity error."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": '{"position":"Legacy","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                        "createdAt": "2026-03-28T00:01:00Z",
                    },
                ],
            },
        }
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        with pytest.raises(RuntimeError, match="Turn metadata integrity"):
            controller.read(start.collaboration_id)


class TestBestEffortRepairTurn:
    def test_repairs_metadata_and_journal_when_turn_confirmed(
        self, tmp_path: Path
    ) -> None:
        """Fresh runtime confirms the turn completed. Repair writes TurnStore
        metadata and resolves the journal entry. Handle status is not changed."""
        session = FakeRuntimeSession()
        # After repair bootstraps a fresh runtime, thread/read shows 1 completed turn
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
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        # Simulate: handle already marked unknown by reply() exception path
        store.update_status(start.collaboration_id, "unknown")

        # Build the intent entry that reply() would have created
        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-03-29T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        # Write the intent to journal (simulating what reply() does before run_turn)
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        # Journal resolved
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        # TurnStore repaired
        assert turn_store.get(start.collaboration_id, turn_sequence=1) == 4096
        # Handle NOT reactivated — stays unknown
        assert store.get(start.collaboration_id).status == "unknown"

    def test_emits_dialogue_turn_audit_when_turn_confirmed(
        self, tmp_path: Path
    ) -> None:
        """Confirmed inline repair must also emit the required dialogue_turn audit."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-03-29T00:00:00Z",
                    },
                ],
            },
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-03-29T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [
            json.loads(line) for line in audit_path.read_text().strip().split("\n")
        ]
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) == 1
        assert turn_events[0]["collaboration_id"] == start.collaboration_id
        assert turn_events[0]["runtime_id"] == "rt-sess-1"
        assert turn_events[0]["turn_id"] == "turn-1"
        assert turn_events[0]["context_size"] == 4096

    def test_leaves_journal_unresolved_when_turn_not_confirmed(
        self, tmp_path: Path
    ) -> None:
        """Thread/read shows zero completed turns. Repair leaves journal unresolved
        for later startup recovery. Handle status is not changed."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-03-29T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        # Journal stays unresolved — startup recovery will handle it
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 1
        # No TurnStore write
        assert turn_store.get(start.collaboration_id, turn_sequence=1) is None

    def test_logs_exception_when_inspection_fails(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """If get_advisory_runtime or read_thread raises, the repair logs and
        gives up. Journal stays unresolved. No exception escapes."""
        session = FakeRuntimeSession(initialize_error=RuntimeError("codex down"))
        controller, plane, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        # Manually create a handle (start() would fail with initialize_error)
        from server.models import CollaborationHandle

        handle = CollaborationHandle(
            collaboration_id="collab-sess-1",
            capability_class="advisory",
            runtime_id="rt-old",
            codex_thread_id="thr-start",
            claude_session_id="sess-1",
            repo_root=str(tmp_path.resolve()),
            created_at="2026-03-29T00:00:00Z",
            status="unknown",
        )
        store.create(handle)

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-old:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id="collab-sess-1",
            created_at="2026-03-29T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-old",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        # Invalidate the runtime so get_advisory_runtime has to bootstrap fresh
        # The fresh bootstrap will hit initialize_error
        plane.invalidate_runtime(tmp_path.resolve())

        # Must not raise
        controller._best_effort_repair_turn(intent_entry)

        # Journal stays unresolved
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 1
        err = capsys.readouterr().err
        assert (
            "best_effort_repair_turn failed: Runtime bootstrap failed: initialize failed."
            in err
        )

    def test_emits_outcome_record_when_turn_confirmed(self, tmp_path: Path) -> None:
        """Confirmed inline repair must also emit an outcome record."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "repaired-turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-04-01T00:00:00Z",
                    },
                ],
            },
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines]
        dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
        assert len(dialogue_outcomes) == 1
        assert dialogue_outcomes[0]["turn_id"] == "repaired-turn-1"
        assert dialogue_outcomes[0]["turn_sequence"] == 1
        assert dialogue_outcomes[0]["context_size"] == 4096
        assert dialogue_outcomes[0]["repo_root"] == str(tmp_path.resolve())
        assert dialogue_outcomes[0]["policy_fingerprint"] is not None

    def test_repair_outcome_uses_confirmed_turn_timestamp(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "repaired-turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-04-02T00:00:00Z",
                    },
                ],
            },
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        result = controller._best_effort_repair_turn(intent_entry)

        assert result == "confirmed_finalized"
        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        record = json.loads(outcomes_path.read_text(encoding="utf-8").strip())
        assert record["timestamp"] == "2026-04-02T00:00:00Z"

    def test_repair_outcome_falls_back_to_entry_timestamp_when_missing_created_at(
        self, tmp_path: Path
    ) -> None:
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "repaired-turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                ],
            },
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        result = controller._best_effort_repair_turn(intent_entry)

        assert result == "confirmed_finalized"
        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        record = json.loads(outcomes_path.read_text(encoding="utf-8").strip())
        assert record["timestamp"] == "2026-04-01T00:00:00Z"

    def test_does_not_emit_outcome_when_turn_unconfirmed(self, tmp_path: Path) -> None:
        """Unconfirmed repair must NOT emit an outcome record."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        if outcomes_path.exists():
            content = outcomes_path.read_text(encoding="utf-8").strip()
            if content:
                records = [json.loads(line) for line in content.split("\n")]
                dialogue_outcomes = [
                    r for r in records if r["outcome_type"] == "dialogue_turn"
                ]
                assert len(dialogue_outcomes) == 0


class TestReplyRunTurnFailure:
    def test_marks_handle_unknown_and_blocks_retry(self, tmp_path: Path) -> None:
        """run_turn raises -> handle quarantined -> second reply rejected."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession(run_turn_error=RuntimeError("dispatch failed"))
        # After quarantine, best-effort repair sees no completed turns
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        with pytest.raises(RuntimeError, match="dispatch failed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should fail",
                explicit_paths=(Path("focus.py"),),
            )

        # Handle is now unknown
        assert store.get(start.collaboration_id).status == "unknown"

        # Second reply blocked by lifecycle guard
        with pytest.raises(ValueError, match="handle not active"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should be rejected",
            )

    def test_repairs_metadata_when_completed_turn_is_visible(
        self, tmp_path: Path
    ) -> None:
        """run_turn raises, but fresh runtime shows the turn completed.
        TurnStore repaired, journal resolved, handle reactivated, read() works."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class FailThenSucceedSession(FakeRuntimeSession):
            """First run_turn raises, but read_thread shows the turn completed."""

            def __init__(self) -> None:
                super().__init__()
                self._run_turn_failed = False

            def run_turn(self, **kwargs: object) -> object:
                if not self._run_turn_failed:
                    self._run_turn_failed = True
                    # Simulate: Codex processed the turn but connection dropped
                    self.completed_turn_count += 1
                    raise RuntimeError("connection lost after dispatch")
                return super().run_turn(**kwargs)

        session = FailThenSucceedSession()
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        with pytest.raises(CommittedTurnFinalizationError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        # Handle reactivated after inline resume
        assert store.get(start.collaboration_id).status == "active"
        # But metadata repaired (turn was confirmed via thread/read)
        assert turn_store.get(start.collaboration_id, turn_sequence=1) is not None
        # Journal resolved
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 0

        # read() works without integrity error
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
        read_result = controller.read(start.collaboration_id)
        assert read_result.turn_count == 1

    def test_preserves_original_exception_when_inspection_fails(
        self, tmp_path: Path
    ) -> None:
        """run_turn raises and best-effort repair also fails.
        Original exception is re-raised, handle is unknown, journal unresolved."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class AlwaysFailSession(FakeRuntimeSession):
            """run_turn fails, and subsequent initialize (for fresh runtime) also fails."""

            _run_turn_raised = False

            def run_turn(self, **kwargs: object) -> object:
                self._run_turn_raised = True
                raise RuntimeError("original dispatch error")

            def initialize(self) -> object:
                if self._run_turn_raised:
                    # Fresh runtime bootstrap also fails
                    raise RuntimeError("codex unreachable")
                return super().initialize()

        session = AlwaysFailSession()
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        with pytest.raises(RuntimeError, match="original dispatch error"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should fail",
                explicit_paths=(Path("focus.py"),),
            )

        # Handle quarantined
        assert store.get(start.collaboration_id).status == "unknown"
        # Journal unresolved (repair failed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 1

    def test_surfaces_finalization_error_when_repair_confirms_but_cannot_finalize(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class FailThenConfirmSession(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self._failed = False

            def run_turn(self, **kwargs: object) -> object:
                if not self._failed:
                    self._failed = True
                    self.completed_turn_count += 1
                    raise RuntimeError("connection lost after dispatch")
                return super().run_turn(**kwargs)

        session = FailThenConfirmSession()
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        def _boom(*args: object, **kwargs: object) -> None:
            raise OSError("turn store boom")

        monkeypatch.setattr(turn_store, "write", _boom)

        with pytest.raises(CommittedTurnFinalizationError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        assert store.get(start.collaboration_id).status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 1
        assert turn_entries[0].phase == "intent"

    def test_confirmed_repair_resume_failure_leaves_handle_unknown(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class FailThenConfirmSession(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self._failed = False

            def run_turn(self, **kwargs: object) -> object:
                if not self._failed:
                    self._failed = True
                    self.completed_turn_count += 1
                    raise RuntimeError("connection lost after dispatch")
                return super().run_turn(**kwargs)

        session = FailThenConfirmSession()
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        def _boom(thread_id: str) -> str:
            raise RuntimeError("resume boom")

        monkeypatch.setattr(session, "resume_thread", _boom)

        with pytest.raises(CommittedTurnFinalizationError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        assert store.get(start.collaboration_id).status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        assert "inline_resume_turn failed: resume boom" in capsys.readouterr().err


class TestReplyParseFailure:
    def test_raises_committed_turn_parse_error_and_leaves_handle_active(
        self, tmp_path: Path
    ) -> None:
        """Malformed agent message → CommittedTurnParseError; handle stays active."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession(agent_message="not valid json {{{{")
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        with pytest.raises(CommittedTurnParseError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        assert store.get(start.collaboration_id).status == "active"

    def test_completes_journal_writes_store_and_emits_audit(
        self, tmp_path: Path
    ) -> None:
        """Parse failure still finalizes all durable state."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession(agent_message="not valid json {{{{")
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        with pytest.raises(CommittedTurnParseError):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        # Journal fully resolved
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 0

        # TurnStore has metadata
        assert turn_store.get(start.collaboration_id, turn_sequence=1) is not None

        # Audit event emitted
        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [
            json.loads(line) for line in audit_path.read_text().strip().split("\n")
        ]
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) == 1
        assert turn_events[0]["collaboration_id"] == start.collaboration_id

        # Outcome record emitted (before parse)
        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        outcome_lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        outcome_records = [json.loads(line) for line in outcome_lines]
        dialogue_outcomes = [
            r for r in outcome_records if r["outcome_type"] == "dialogue_turn"
        ]
        assert len(dialogue_outcomes) == 1
        assert dialogue_outcomes[0]["collaboration_id"] == start.collaboration_id

    def test_read_returns_fallback_position_without_integrity_error(
        self, tmp_path: Path
    ) -> None:
        """After parse failure, read() uses the raw-message fallback and does not
        raise a metadata integrity error."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession(agent_message="not valid json {{{{")
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        with pytest.raises(CommittedTurnParseError):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        # Configure read_thread with the committed turn's malformed message
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": "not valid json {{{{",
                        "createdAt": "2026-03-29T00:00:00Z",
                    },
                ],
            },
        }

        # read() should NOT raise RuntimeError — it uses the raw-message fallback
        read_result = controller.read(start.collaboration_id)
        assert read_result.turn_count == 1
        # Fallback position is agent_message[:200]
        assert read_result.turns[0].position == "not valid json {{{{"

    def test_follow_up_reply_uses_next_turn_sequence(self, tmp_path: Path) -> None:
        """First reply commits but fails parsing. Second reply succeeds at turn 2."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class MalformedThenValidSession(FakeRuntimeSession):
            """First run_turn returns malformed JSON, second returns valid."""

            def __init__(self) -> None:
                super().__init__()
                self._first_call = True

            def run_turn(self, **kwargs: object) -> object:
                if self._first_call:
                    self._first_call = False
                    self.run_turn_calls += 1
                    self.completed_turn_count += 1
                    from server.models import TurnExecutionResult

                    return TurnExecutionResult(
                        turn_id="turn-1",
                        status="completed",
                        agent_message="not valid json {{{{",
                    )
                return super().run_turn(**kwargs)

        session = MalformedThenValidSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # First reply: commits but parse fails
        with pytest.raises(CommittedTurnParseError):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="First turn",
                explicit_paths=(Path("focus.py"),),
            )

        # Second reply: should be turn_sequence=2
        reply2 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Second turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply2.turn_sequence == 2


class TestFirstTurnFastPath:
    """First reply after start must not require a materialized read_thread."""

    def test_first_reply_skips_read_thread(self, tmp_path: Path) -> None:
        """First reply derives turn_sequence=1 from empty TurnStore, no read_thread."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class TrackingSession(FakeRuntimeSession):
            """Tracks read_thread calls to prove the fast path skips it."""

            def __init__(self) -> None:
                super().__init__()
                self.read_thread_calls: int = 0

            def read_thread(self, thread_id: str) -> dict:
                self.read_thread_calls += 1
                return super().read_thread(thread_id)

        session = TrackingSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        reply = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        assert reply.turn_sequence == 1
        assert session.read_thread_calls == 0, (
            "First reply should use TurnStore fast path, not read_thread"
        )

    def test_second_reply_uses_read_thread(self, tmp_path: Path) -> None:
        """After a completed turn, subsequent replies fall back to read_thread."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class TrackingSession(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self.read_thread_calls: int = 0

            def read_thread(self, thread_id: str) -> dict:
                self.read_thread_calls += 1
                return super().read_thread(thread_id)

        session = TrackingSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # First reply: fast path, no read_thread
        reply1 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply1.turn_sequence == 1
        assert session.read_thread_calls == 0

        # Second reply: TurnStore has turn 1, so read_thread is called
        reply2 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Second turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply2.turn_sequence == 2
        assert session.read_thread_calls == 1, (
            "Second reply should use read_thread to count completed turns"
        )

    def test_empty_plus_diagnostics_remote_zero_completed(self, tmp_path: Path) -> None:
        """Corrupt JSONL + remote says 0 completed → proceed as turn 1."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class TrackingSession(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self.read_thread_calls: int = 0

            def read_thread(self, thread_id: str) -> dict:
                self.read_thread_calls += 1
                return {"thread": {"id": thread_id, "turns": []}}

        session = TrackingSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # Corrupt the JSONL to produce diagnostics without valid records
        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")

        reply = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply.turn_sequence == 1
        assert session.read_thread_calls == 1, (
            "Diagnostics should force remote validation even with empty local metadata"
        )

    def test_empty_plus_diagnostics_remote_two_completed(self, tmp_path: Path) -> None:
        """Corrupt JSONL + remote says 2 completed → integrity error, handle unknown."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")

        with pytest.raises(RuntimeError, match="incomplete for completed remote"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="First turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_empty_plus_diagnostics_remote_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Corrupt JSONL + read_thread raises → error mentions diagnostics."""
        session = FakeRuntimeSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")

        monkeypatch.setattr(
            session,
            "read_thread",
            lambda _tid: (_ for _ in ()).throw(RuntimeError("remote boom")),
        )

        with pytest.raises(
            RuntimeError, match="session turn metadata file has replay diagnostics"
        ) as exc_info:
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="First turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert exc_info.value.__cause__ is not None

    def test_gap_metadata_integrity_error(self, tmp_path: Path) -> None:
        """Gap {2} with remote 2 completed → integrity error."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=4096)

        with pytest.raises(
            RuntimeError, match="Required.*\\[1, 2\\].*present.*\\[2\\]"
        ):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Next turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert store.get(start.collaboration_id).status == "unknown"

    def test_partial_tail_integrity_error(self, tmp_path: Path) -> None:
        """Partial tail {1} with remote 2 completed → integrity error."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)

        with pytest.raises(
            RuntimeError, match="Required.*\\[1, 2\\].*present.*\\[1\\]"
        ):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Next turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert store.get(start.collaboration_id).status == "unknown"

    def test_nonempty_local_remote_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-empty local + read_thread raises → error mentions sequences."""
        session = FakeRuntimeSession()
        controller, _, _, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)

        monkeypatch.setattr(
            session,
            "read_thread",
            lambda _tid: (_ for _ in ()).throw(RuntimeError("remote boom")),
        )

        with pytest.raises(
            RuntimeError, match="cannot validate local turn metadata.*sequences=\\[1\\]"
        ) as exc_info:
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Next turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert exc_info.value.__cause__ is not None

    def test_zero_turn_stale_metadata_integrity_error(self, tmp_path: Path) -> None:
        """Stale local {1} + remote 0 completed → integrity error (zero-turn tightening).

        Proves the reply path applies the same zero-turn stale metadata
        rejection as recover_startup(). Without this, a buggy implementation
        could allow stale metadata through on the reply path while correctly
        rejecting it on recovery.
        """
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=500)

        with pytest.raises(RuntimeError, match="incomplete for completed remote"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="First turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert store.get(start.collaboration_id).status == "unknown"

    def test_extra_local_keys_prefix_complete(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Extra local {1,2,3} with remote 2 completed → succeeds, warns on stderr."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, _, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=8192)
        turn_store.write(start.collaboration_id, turn_sequence=3, context_size=2048)

        reply = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Next turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply.turn_sequence == 3
        stderr = capsys.readouterr().err
        assert "extra local turn metadata beyond completed count" in stderr

    def test_unrelated_collaboration_corruption_disables_fast_path(
        self, tmp_path: Path
    ) -> None:
        """Corrupt JSONL from collab-B disables fast path for collab-A (file-global)."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class TrackingSession(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self.read_thread_calls: int = 0

            def read_thread(self, thread_id: str) -> dict:
                self.read_thread_calls += 1
                return {"thread": {"id": thread_id, "turns": []}}

        session = TrackingSession()
        controller, _, _, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Write valid metadata for a DIFFERENT collaboration, then corrupt
        turn_store.write("other-collab", turn_sequence=1, context_size=1000)
        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        with store_path.open("a", encoding="utf-8") as f:
            f.write("corrupted line from other collab\n")

        reply = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply.turn_sequence == 1
        assert session.read_thread_calls == 1, (
            "File-global diagnostics should force remote validation "
            "even though this collaboration has no corrupt records"
        )


class TestRecoverStartupMetadataCompleteness:
    """recover_startup() must quarantine handles with incomplete local metadata
    and allow reattach for prefix-complete metadata (including extra keys)."""

    def test_gapped_metadata_quarantines_handle(self, tmp_path: Path) -> None:
        """Handle with {1, 3} metadata vs remote 2 completed → quarantine.

        Cardinality-matching gap: len(metadata) == completed_count == 2,
        so the old ``len(metadata) < completed_count`` check passes.
        Only the prefix-completeness check catches the gap (key 2 missing).
        """
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Pre-populate gapped metadata: keys {1, 3}, missing key 2
        # len == 2 == completed_count, so old cardinality check misses this
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        turn_store.write(start.collaboration_id, turn_sequence=3, context_size=2048)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_zero_turn_stale_metadata_quarantines_handle(self, tmp_path: Path) -> None:
        """Handle with stale local metadata + remote 0 completed → quarantine."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Pre-populate stale metadata for a turn the remote never completed
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=500)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_extra_local_keys_allows_reattach(self, tmp_path: Path) -> None:
        """Handle with {1, 2, 3} metadata vs remote 2 completed → reattach allowed.

        Proves recover_startup() applies prefix-completeness, not exact-key
        equality. Extra local keys beyond completed_count are tolerated.
        Without this, a buggy implementation could reject extra keys in
        recovery while accepting them in reply.
        """
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=8192)
        turn_store.write(start.collaboration_id, turn_sequence=3, context_size=2048)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status != "unknown", (
            "Extra local keys beyond completed_count should not quarantine — "
            "prefix {1, 2} is complete for completed_count=2"
        )

    def test_unrelated_corruption_zero_completed_still_reattaches(
        self, tmp_path: Path
    ) -> None:
        """Unrelated JSONL corruption does not change zero-turn recovery behavior.

        recover_startup() intentionally ignores replay diagnostics and decides
        eligibility from recovered metadata plus remote completed turns. This
        pins the asymmetry with _next_turn_sequence(), which must distrust an
        empty store when the session-wide JSONL has diagnostics.
        """
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        turn_store.write("other-collab", turn_sequence=1, context_size=1000)
        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        with store_path.open("a", encoding="utf-8") as f:
            f.write("corrupted line from other collab\n")

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert session.resumed_threads == ["thr-start"]

    def test_same_collaboration_corruption_prefix_complete_still_reattaches(
        self, tmp_path: Path
    ) -> None:
        """Same-collaboration corruption does not quarantine prefix-complete metadata.

        replay_jsonl() still returns valid records around a corrupt line, and
        recover_startup() intentionally uses get_all() rather than
        get_all_checked(). This test pins that recovery behavior explicitly.
        """
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        with store_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=8192)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert session.resumed_threads == ["thr-start"]


class TestRecoveryOutcomeEmission:
    def test_recovery_confirmed_emits_outcome_record(self, tmp_path: Path) -> None:
        """Startup recovery that confirms a turn also emits an outcome record."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "recovered-turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-04-01T00:00:00Z",
                    },
                ],
            },
        }
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # Simulate: an unresolved turn_dispatch entry left by a crashed session
        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller.recover_pending_operations()

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines]
        dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
        assert len(dialogue_outcomes) == 1
        assert dialogue_outcomes[0]["collaboration_id"] == start.collaboration_id
        assert dialogue_outcomes[0]["turn_id"] == "recovered-turn-1"
        assert dialogue_outcomes[0]["turn_sequence"] == 1
        assert dialogue_outcomes[0]["context_size"] == 4096
        assert dialogue_outcomes[0]["repo_root"] == str(tmp_path.resolve())
        assert dialogue_outcomes[0]["policy_fingerprint"] is not None

    def test_recovery_outcome_uses_confirmed_turn_timestamp(
        self, tmp_path: Path
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "recovered-turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-04-02T00:00:00Z",
                    },
                ],
            },
        }
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller.recover_pending_operations()

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        record = json.loads(outcomes_path.read_text(encoding="utf-8").strip())
        assert record["timestamp"] == "2026-04-02T00:00:00Z"

    def test_recovery_unconfirmed_does_not_emit_outcome(self, tmp_path: Path) -> None:
        """Recovery that cannot confirm the turn does NOT emit an outcome."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        # thread/read shows no completed turns — turn unconfirmed
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller.recover_pending_operations()

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        if outcomes_path.exists():
            content = outcomes_path.read_text(encoding="utf-8").strip()
            if content:
                records = [json.loads(line) for line in content.split("\n")]
                dialogue_outcomes = [
                    r for r in records if r["outcome_type"] == "dialogue_turn"
                ]
                assert len(dialogue_outcomes) == 0

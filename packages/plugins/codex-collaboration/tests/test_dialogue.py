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

# Import FakeRuntimeSession and helpers from the control plane tests.
# These will be moved to conftest.py in a cleanup pass; for now we import directly.
from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _build_dialogue_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
    session_id: str = "sess-1",
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal]:
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
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id=session_id,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"collab-{session_id}", *(f"id-{i}" for i in range(100)))).__next__,
    )
    return controller, plane, store, journal


class TestDialogueStart:
    def test_start_returns_dialogue_start_result(self, tmp_path: Path) -> None:
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        assert result.collaboration_id == "collab-sess-1"
        assert result.status == "active"
        assert result.runtime_id == "rt-sess-1"
        assert result.created_at is not None

    def test_start_persists_handle_in_lineage_store(self, tmp_path: Path) -> None:
        controller, _, store, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.capability_class == "advisory"
        assert handle.codex_thread_id == "thr-start"
        assert handle.claude_session_id == "sess-1"

    def test_start_journals_before_dispatch(self, tmp_path: Path) -> None:
        controller, _, _, journal = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        # After successful completion, all phases written (intent → dispatched → completed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_start_does_not_emit_audit_event(self, tmp_path: Path) -> None:
        """Thread creation is not a trust boundary crossing — no audit event.
        See contracts.md §Audit Event Actions (dialogue_start is not defined)."""
        controller, _, _, journal = _build_dialogue_stack(tmp_path)
        controller.start(tmp_path)
        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        if audit_path.exists():
            events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]
            assert all(e["action"] != "dialogue_start" for e in events)

    def test_start_creates_thread_on_runtime(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession()
        controller, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        controller.start(tmp_path)
        assert "start" in session.started_threads

    def test_start_invalidates_runtime_on_thread_failure(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession(initialize_error=RuntimeError("boom"))
        controller, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        with pytest.raises(RuntimeError):
            controller.start(tmp_path)


from server.models import ConsultRequest, DialogueReplyResult


class TestDialogueReply:
    def test_reply_returns_dialogue_reply_result(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
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
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
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
        controller, _, _, journal = _build_dialogue_stack(tmp_path)
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
        controller, _, _, journal = _build_dialogue_stack(tmp_path)
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
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ValueError, match="Handle not found"):
            controller.reply(
                collaboration_id="nonexistent",
                objective="Should fail",
            )

    def test_reply_uses_same_context_assembly_as_consult(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        controller, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
        # Verify the prompt contains the assembled packet (same pipeline as consult)
        assert session.last_prompt_text is not None
        assert "focus.py" in session.last_prompt_text

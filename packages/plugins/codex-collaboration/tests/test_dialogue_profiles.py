"""Tests for dialogue profile persistence: resolve-once-at-start, read-from-handle-on-reply."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.dialogue import DialogueController
from server.profiles import ProfileValidationError

# Re-use the shared stack builder and test doubles from test_dialogue.py.
from tests.test_dialogue import _build_dialogue_stack
from tests.test_control_plane import FakeRuntimeSession


class TestDialogueStartProfilePersistence:
    def test_start_with_profile_stores_resolved_fields_on_handle(
        self, tmp_path: Path
    ) -> None:
        """start(profile_name='deep-review') stores resolved posture/effort/turn_budget."""
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path, profile_name="deep-review")
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.resolved_posture == "evaluative"
        assert handle.resolved_effort == "xhigh"
        assert handle.resolved_turn_budget == 8

    def test_start_without_profile_stores_none_fields_on_handle(
        self, tmp_path: Path
    ) -> None:
        """start() without profile_name leaves all three resolved fields as None."""
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.resolved_posture is None
        assert handle.resolved_effort is None
        assert handle.resolved_turn_budget is None

    def test_start_with_phased_profile_raises_profile_validation_error(
        self, tmp_path: Path
    ) -> None:
        """start(profile_name='debugging') raises ProfileValidationError (phased profile)."""
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ProfileValidationError, match="phased profiles"):
            controller.start(tmp_path, profile_name="debugging")

    def test_start_with_quick_check_profile(self, tmp_path: Path) -> None:
        """quick-check profile resolves to collaborative posture, medium effort, budget 1."""
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path, profile_name="quick-check")
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.resolved_posture == "collaborative"
        assert handle.resolved_effort == "medium"
        assert handle.resolved_turn_budget == 1


class TestDialogueStartExplicitOverrides:
    """start() with explicit posture and turn_budget, no profile name."""

    def test_start_with_explicit_posture_stores_on_handle(
        self, tmp_path: Path
    ) -> None:
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path, explicit_posture="adversarial")
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.resolved_posture == "adversarial"
        assert handle.resolved_turn_budget == 6  # resolver default

    def test_start_with_explicit_turn_budget_stores_on_handle(
        self, tmp_path: Path
    ) -> None:
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path, explicit_turn_budget=8)
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.resolved_posture == "collaborative"  # resolver default
        assert handle.resolved_turn_budget == 8

    def test_start_with_both_explicit_overrides(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(
            tmp_path, explicit_posture="evaluative", explicit_turn_budget=6
        )
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.resolved_posture == "evaluative"
        assert handle.resolved_turn_budget == 6

    def test_explicit_overrides_beat_profile(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(
            tmp_path,
            profile_name="deep-review",
            explicit_posture="adversarial",
            explicit_turn_budget=4,
        )
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.resolved_posture == "adversarial"
        assert handle.resolved_turn_budget == 4
        assert handle.resolved_effort == "xhigh"  # from profile

    def test_start_with_invalid_posture_raises(self, tmp_path: Path) -> None:
        from server.profiles import ProfileValidationError

        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ProfileValidationError, match="unknown posture"):
            controller.start(tmp_path, explicit_posture="aggressive")

    def test_start_with_budget_above_15_raises(self, tmp_path: Path) -> None:
        from server.profiles import ProfileValidationError

        controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            controller.start(tmp_path, explicit_turn_budget=16)


class TestDialogueReplyUsesStoredProfile:
    def test_reply_passes_stored_effort_to_runtime(self, tmp_path: Path) -> None:
        """reply() passes handle.resolved_effort to runtime.session.run_turn()."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)

        start_result = controller.start(tmp_path, profile_name="deep-review")
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )

        assert session.last_effort == "xhigh"

    def test_reply_passes_stored_posture_to_prompt_builder(
        self, tmp_path: Path
    ) -> None:
        """reply() includes posture instruction in the prompt text when posture is set."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)

        start_result = controller.start(tmp_path, profile_name="deep-review")
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )

        assert session.last_prompt_text is not None
        assert "evaluative" in session.last_prompt_text

    def test_reply_without_profile_passes_none_effort(self, tmp_path: Path) -> None:
        """reply() on a no-profile handle passes effort=None to run_turn."""
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

        assert session.last_effort is None

    def test_reply_without_profile_no_posture_instruction_in_prompt(
        self, tmp_path: Path
    ) -> None:
        """reply() on a no-profile handle emits no posture instruction in the prompt."""
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

        assert session.last_prompt_text is not None
        assert "posture" not in session.last_prompt_text

    def test_reply_on_crash_recovered_handle_works(self, tmp_path: Path) -> None:
        """reply() on a handle with None profile fields (crash-recovered) works without error."""
        from server.lineage_store import LineageStore
        from server.models import CollaborationHandle
        from server.journal import OperationJournal
        from server.turn_store import TurnStore
        from server.control_plane import ControlPlane
        from tests.test_control_plane import _compat_result, _repo_identity

        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()

        # Build a handle with None profile fields to simulate crash recovery.
        plugin_data = tmp_path / "plugin-data"
        session_id = "sess-crash"
        journal = OperationJournal(plugin_data)
        store = LineageStore(plugin_data, session_id)
        turn_store = TurnStore(plugin_data, session_id)
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
        controller = DialogueController(
            control_plane=plane,
            lineage_store=store,
            journal=journal,
            session_id=session_id,
            repo_identity_loader=_repo_identity,
            uuid_factory=iter(
                (f"collab-crash", *(f"id-{i}" for i in range(100)))
            ).__next__,
            turn_store=turn_store,
        )

        # Persist a handle that has no profile fields (pre-T-03 shape).
        handle = CollaborationHandle(
            collaboration_id="collab-crash",
            capability_class="advisory",
            runtime_id="rt-sess-crash",
            codex_thread_id="thr-start",
            claude_session_id=session_id,
            repo_root=str(tmp_path),
            created_at="2026-03-28T00:00:00Z",
            status="active",
            # resolved_posture, resolved_effort, resolved_turn_budget all default to None
        )
        store.create(handle)

        # Bootstrap the runtime so get_advisory_runtime works.
        plane.codex_status(tmp_path)

        result = controller.reply(
            collaboration_id="collab-crash",
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )

        assert result.collaboration_id == "collab-crash"
        assert result.turn_sequence == 1
        # No posture instruction, no effort override.
        assert session.last_effort is None
        assert session.last_prompt_text is not None
        assert "posture" not in session.last_prompt_text

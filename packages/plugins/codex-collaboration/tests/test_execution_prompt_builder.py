"""Tests for execution-turn prompt construction."""

from __future__ import annotations

from server.execution_prompt_builder import build_execution_turn_text


def test_build_execution_turn_text_includes_objective() -> None:
    result = build_execution_turn_text(
        objective="Fix the login timeout bug",
        worktree_path="/data/runtimes/delegation/job-1/worktree",
    )
    assert "Fix the login timeout bug" in result


def test_build_execution_turn_text_includes_worktree_scope() -> None:
    result = build_execution_turn_text(
        objective="Refactor auth",
        worktree_path="/data/runtimes/delegation/job-1/worktree",
    )
    assert "/data/runtimes/delegation/job-1/worktree" in result


def test_build_execution_turn_text_conveys_execution_context() -> None:
    """The prompt should tell the agent it is operating in an isolated worktree."""
    result = build_execution_turn_text(
        objective="Add tests",
        worktree_path="/wt/abc",
    )
    assert "worktree" in result.lower() or "isolated" in result.lower()


from server.models import PendingServerRequest


def test_build_execution_resume_turn_text_includes_request_context() -> None:
    from server.execution_prompt_builder import build_execution_resume_turn_text

    request = PendingServerRequest(
        request_id="req-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-1",
        kind="command_approval",
        requested_scope={"command": "make test", "cwd": "/repo"},
        status="resolved",
    )

    result = build_execution_resume_turn_text(
        pending_request=request,
        answers=None,
    )

    assert "req-1" in result
    assert "command_approval" in result
    assert "make test" in result
    assert "already been resolved at the wire layer" in result


def test_build_execution_resume_turn_text_includes_answers_when_present() -> None:
    from server.execution_prompt_builder import build_execution_resume_turn_text

    request = PendingServerRequest(
        request_id="req-2",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-2",
        kind="request_user_input",
        requested_scope={"questions": [{"id": "q1"}]},
        status="resolved",
    )

    result = build_execution_resume_turn_text(
        pending_request=request,
        answers={"q1": ("yes", "ship it")},
    )

    assert "request_user_input" in result
    assert "q1" in result
    assert "ship it" in result

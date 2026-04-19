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

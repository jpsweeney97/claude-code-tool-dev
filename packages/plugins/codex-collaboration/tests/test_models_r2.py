"""Tests for R2 data model types."""

from __future__ import annotations

from dataclasses import asdict, FrozenInstanceError

import pytest

from server.models import (
    CollaborationHandle,
    DialogueReadResult,
    DialogueReplyResult,
    DialogueStartResult,
    DialogueTurnSummary,
    HandleStatus,
    OperationJournalEntry,
)


def test_collaboration_handle_is_frozen() -> None:
    handle = CollaborationHandle(
        collaboration_id="collab-1",
        capability_class="advisory",
        runtime_id="rt-1",
        codex_thread_id="thr-1",
        claude_session_id="sess-1",
        repo_root="/repo",
        created_at="2026-03-28T00:00:00Z",
        status="active",
    )
    assert handle.collaboration_id == "collab-1"
    assert handle.status == "active"
    assert handle.parent_collaboration_id is None
    assert handle.fork_reason is None
    with pytest.raises(FrozenInstanceError):
        handle.status = "completed"  # type: ignore[misc]


def test_collaboration_handle_serializes_to_dict() -> None:
    handle = CollaborationHandle(
        collaboration_id="collab-1",
        capability_class="advisory",
        runtime_id="rt-1",
        codex_thread_id="thr-1",
        claude_session_id="sess-1",
        repo_root="/repo",
        created_at="2026-03-28T00:00:00Z",
        status="active",
    )
    d = asdict(handle)
    assert d["collaboration_id"] == "collab-1"
    assert d["parent_collaboration_id"] is None
    assert len(d) == 10


def test_dialogue_start_result_fields() -> None:
    result = DialogueStartResult(
        collaboration_id="collab-1",
        runtime_id="rt-1",
        status="active",
        created_at="2026-03-28T00:00:00Z",
    )
    assert result.status == "active"


def test_dialogue_reply_result_fields() -> None:
    from server.models import ConsultEvidence

    result = DialogueReplyResult(
        collaboration_id="collab-1",
        runtime_id="rt-1",
        position="Analysis complete",
        evidence=(ConsultEvidence(claim="Found bug", citation="main.py:42"),),
        uncertainties=("Untested path",),
        follow_up_branches=("Check tests",),
        turn_sequence=1,
        context_size=1024,
    )
    assert result.turn_sequence == 1
    assert len(result.evidence) == 1


def test_dialogue_read_result_fields() -> None:
    result = DialogueReadResult(
        collaboration_id="collab-1",
        status="active",
        turn_count=2,
        created_at="2026-03-28T00:00:00Z",
        turns=(
            DialogueTurnSummary(
                turn_sequence=1,
                position="First analysis",
                context_size=1024,
                timestamp="2026-03-28T00:01:00Z",
            ),
        ),
    )
    assert result.turn_count == 2
    assert result.turns[0].turn_sequence == 1


def test_operation_journal_entry_intent_phase() -> None:
    entry = OperationJournalEntry(
        idempotency_key="sess-1:collab-1",
        operation="thread_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
    )
    assert entry.operation == "thread_creation"
    assert entry.phase == "intent"
    assert entry.codex_thread_id is None


def test_operation_journal_entry_dispatched_phase() -> None:
    entry = OperationJournalEntry(
        idempotency_key="rt-1:thr-1:1",
        operation="turn_dispatch",
        phase="dispatched",
        collaboration_id="collab-1",
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
        codex_thread_id="thr-1",
        turn_sequence=1,
        runtime_id="rt-1",
    )
    assert entry.phase == "dispatched"
    assert entry.turn_sequence == 1
    assert entry.codex_thread_id == "thr-1"

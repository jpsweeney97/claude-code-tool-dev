"""Tests for R2 data model types."""

from __future__ import annotations

from dataclasses import asdict, FrozenInstanceError

import pytest

from server.models import (
    AdvisoryRuntimeState,
    CollaborationHandle,
    DialogueReadResult,
    DialogueReplyResult,
    DialogueStartResult,
    DialogueTurnSummary,
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
    assert d["resolved_posture"] is None
    assert d["resolved_effort"] is None
    assert d["resolved_turn_budget"] is None
    assert len(d) == 13


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


def test_operation_journal_entry_has_context_size_field() -> None:
    entry = OperationJournalEntry(
        idempotency_key="rt-1:thr-1:1",
        operation="turn_dispatch",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
        codex_thread_id="thr-1",
        turn_sequence=1,
        runtime_id="rt-1",
        context_size=4096,
    )
    assert entry.context_size == 4096


def test_operation_journal_entry_context_size_defaults_to_none() -> None:
    entry = OperationJournalEntry(
        idempotency_key="sess-1:collab-1",
        operation="thread_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
    )
    assert entry.context_size is None


def test_advisory_runtime_state_session_not_any() -> None:
    """F6: session field should reference AppServerRuntimeSession, not Any.

    This is a raw annotation-token assertion, not a resolved-type check.
    from __future__ import annotations makes all annotations strings at
    runtime. We compare string tokens -- NOT get_type_hints(), which would
    trigger the circular import that TYPE_CHECKING is designed to avoid.
    """
    field_type = AdvisoryRuntimeState.__dataclass_fields__["session"].type
    assert field_type != "Any", "session field is still typed as Any"
    assert "AppServerRuntimeSession" in field_type


def test_delegation_job_has_required_fields() -> None:
    from server.models import DelegationJob

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="queued",
        artifact_paths=(),
        artifact_hash=None,
    )
    assert job.job_id == "job-1"
    assert job.worktree_path == "/tmp/wk"
    assert job.status == "queued"
    assert job.promotion_state == "pending"
    assert job.artifact_hash is None


def test_delegation_job_is_frozen() -> None:
    from server.models import DelegationJob

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="queued",
    )
    with pytest.raises(FrozenInstanceError):
        job.status = "running"  # type: ignore[misc]


def test_job_busy_response_shape() -> None:
    from server.models import JobBusyResponse

    resp = JobBusyResponse(
        busy=True,
        active_job_id="job-1",
        active_job_status="running",
        detail="Another delegation is in flight.",
    )
    assert resp.busy is True
    assert resp.active_job_id == "job-1"
    assert resp.active_job_status == "running"


def test_audit_event_has_top_level_job_id_field() -> None:
    from server.models import AuditEvent

    event = AuditEvent(
        event_id="e-1",
        timestamp="2026-04-17T00:00:00Z",
        actor="claude",
        action="delegate_start",
        collaboration_id="collab-1",
        runtime_id="rt-1",
        job_id="job-1",
    )
    assert event.job_id == "job-1"


def test_audit_event_job_id_defaults_to_none() -> None:
    from server.models import AuditEvent

    event = AuditEvent(
        event_id="e-1",
        timestamp="2026-04-17T00:00:00Z",
        actor="claude",
        action="consult",
        collaboration_id="collab-1",
        runtime_id="rt-1",
    )
    assert event.job_id is None


def test_operation_journal_entry_accepts_job_creation_operation() -> None:
    from server.models import OperationJournalEntry

    entry = OperationJournalEntry(
        idempotency_key="sess-1:hash-abc",
        operation="job_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-04-17T00:00:00Z",
        repo_root="/tmp/repo",
        job_id="job-1",
    )
    assert entry.operation == "job_creation"
    assert entry.job_id == "job-1"


def test_operation_journal_entry_job_id_defaults_to_none() -> None:
    from server.models import OperationJournalEntry

    entry = OperationJournalEntry(
        idempotency_key="sess-1:collab-1",
        operation="thread_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-04-17T00:00:00Z",
        repo_root="/tmp/repo",
    )
    assert entry.job_id is None

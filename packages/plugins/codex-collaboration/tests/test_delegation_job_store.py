"""Tests for DelegationJobStore — session-scoped JSONL job persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.delegation_job_store import DelegationJobStore
from server.models import DelegationJob


def _make_job(
    job_id: str = "job-1",
    runtime_id: str = "rt-1",
    status: str = "queued",
    promotion_state: str | None = "pending",
) -> DelegationJob:
    return DelegationJob(
        job_id=job_id,
        runtime_id=runtime_id,
        collaboration_id=f"collab-{job_id}",
        base_commit="abc123",
        worktree_path=f"/tmp/wk-{job_id}",
        promotion_state=promotion_state,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
    )


def test_create_then_get_returns_job(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job()

    store.create(job)

    assert store.get("job-1") == job


def test_get_returns_none_for_unknown_id(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    assert store.get("job-does-not-exist") is None


def test_list_returns_all_jobs_for_session(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1"))
    store.create(_make_job(job_id="job-2"))

    jobs = store.list()

    assert {j.job_id for j in jobs} == {"job-1", "job-2"}


def test_list_filter_by_status(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))
    store.create(_make_job(job_id="job-2", status="running"))
    store.create(_make_job(job_id="job-3", status="completed"))

    active = store.list_active()

    assert {j.job_id for j in active} == {"job-1", "job-2"}


def test_update_status_last_write_wins(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))
    store.update_status("job-1", "running")

    job = store.get("job-1")
    assert job is not None
    assert job.status == "running"


def test_update_status_rejects_unknown_status(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))

    with pytest.raises(ValueError, match="unknown status"):
        store.update_status("job-1", "definitely-not-a-status")  # type: ignore[arg-type]


def test_sessions_are_isolated(tmp_path: Path) -> None:
    store_a = DelegationJobStore(tmp_path, "sess-a")
    store_b = DelegationJobStore(tmp_path, "sess-b")
    store_a.create(_make_job(job_id="job-1"))

    assert store_a.get("job-1") is not None
    assert store_b.get("job-1") is None


def test_replay_reconstructs_state_from_log(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))
    store.update_status("job-1", "running")

    # New store instance replays the same log.
    replay = DelegationJobStore(tmp_path, "sess-1")
    job = replay.get("job-1")

    assert job is not None
    assert job.status == "running"


def test_replay_tolerates_truncated_trailing_record(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1"))
    store.create(_make_job(job_id="job-2"))

    store_path = tmp_path / "delegation_jobs" / "sess-1" / "jobs.jsonl"
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(
            '{"op": "create", "job_id": "job-3"'
        )  # truncated, no closing brace

    replay = DelegationJobStore(tmp_path, "sess-1")
    assert {j.job_id for j in replay.list()} == {"job-1", "job-2"}


def test_replay_skips_update_status_with_invalid_status_literal(
    tmp_path: Path,
) -> None:
    """An update_status record with an invalid status literal is silently
    skipped — the job retains its last valid status and remains visible
    to list_active()."""
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))

    # Manually inject a corrupted update_status record.
    import json

    store_path = tmp_path / "delegation_jobs" / "sess-1" / "jobs.jsonl"
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps({"op": "update_status", "job_id": "job-1", "status": "bogus"})
            + "\n"
        )

    replay = DelegationJobStore(tmp_path, "sess-1")
    job = replay.get("job-1")
    assert job is not None
    assert job.status == "queued"  # unchanged — invalid update skipped
    assert len(replay.list_active()) == 1  # still visible in busy gate


def test_replay_skips_create_with_invalid_status_literal(tmp_path: Path) -> None:
    """A create record with an invalid status literal is silently skipped."""
    import json

    store_path = tmp_path / "delegation_jobs" / "sess-1" / "jobs.jsonl"
    store_path.parent.mkdir(parents=True)
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "op": "create",
                    "job_id": "job-bad",
                    "runtime_id": "rt-1",
                    "collaboration_id": "c-1",
                    "base_commit": "abc",
                    "worktree_path": "/tmp/wk",
                    "promotion_state": "pending",
                    "status": "bogus",
                }
            )
            + "\n"
        )

    replay = DelegationJobStore(tmp_path, "sess-1")
    assert replay.get("job-bad") is None
    assert replay.list() == []


def test_replay_skips_create_with_invalid_promotion_state(tmp_path: Path) -> None:
    """A create record with an invalid promotion_state is silently skipped."""
    import json

    store_path = tmp_path / "delegation_jobs" / "sess-1" / "jobs.jsonl"
    store_path.parent.mkdir(parents=True)
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "op": "create",
                    "job_id": "job-bad",
                    "runtime_id": "rt-1",
                    "collaboration_id": "c-1",
                    "base_commit": "abc",
                    "worktree_path": "/tmp/wk",
                    "promotion_state": "corrupted",
                    "status": "queued",
                }
            )
            + "\n"
        )

    replay = DelegationJobStore(tmp_path, "sess-1")
    assert replay.get("job-bad") is None


def test_update_status_and_promotion_last_write_wins(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued", promotion_state=None))

    store.update_status_and_promotion(
        "job-1",
        status="completed",
        promotion_state="pending",
    )

    job = store.get("job-1")
    assert job is not None
    assert job.status == "completed"
    assert job.promotion_state == "pending"


def test_update_artifacts_last_write_wins(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(
        _make_job(job_id="job-1", status="completed", promotion_state="pending")
    )

    store.update_artifacts(
        "job-1",
        artifact_paths=(
            "/tmp/inspection/full.diff",
            "/tmp/inspection/test-results.json",
        ),
        artifact_hash="sha-1",
    )

    job = store.get("job-1")
    assert job is not None
    assert job.artifact_paths == (
        "/tmp/inspection/full.diff",
        "/tmp/inspection/test-results.json",
    )
    assert job.artifact_hash == "sha-1"


def test_replay_accepts_legacy_pending_on_non_completed_job(tmp_path: Path) -> None:
    import json

    store_path = tmp_path / "delegation_jobs" / "sess-1" / "jobs.jsonl"
    store_path.parent.mkdir(parents=True)
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "op": "create",
                    "job_id": "job-legacy",
                    "runtime_id": "rt-1",
                    "collaboration_id": "c-1",
                    "base_commit": "abc",
                    "worktree_path": "/tmp/wk",
                    "promotion_state": "pending",
                    "status": "queued",
                    "artifact_paths": [],
                    "artifact_hash": None,
                }
            )
            + "\n"
        )

    replay = DelegationJobStore(tmp_path, "sess-1")
    job = replay.get("job-legacy")
    assert job is not None
    assert job.status == "queued"


def test_update_promotion_state_persists_and_replays(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(
        DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="abc",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="completed",
        )
    )
    store.update_promotion_state("job-1", promotion_state="prechecks_passed")

    job = store.get("job-1")
    assert job is not None
    assert job.promotion_state == "prechecks_passed"
    assert job.promotion_attempt == 0


def test_update_promotion_state_increments_attempt(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(
        DelegationJob(
            job_id="job-2",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="abc",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="completed",
        )
    )
    store.update_promotion_state(
        "job-2", promotion_state="applied", promotion_attempt=3
    )

    job = store.get("job-2")
    assert job is not None
    assert job.promotion_attempt == 3
    assert job.promotion_state == "applied"


# --- list_user_attention_required tests ---


def test_list_user_attention_required_returns_running_job(tmp_path: Path) -> None:
    """Running jobs are user-attention-required (in progress)."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="running", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].job_id == "job-1"


def test_list_user_attention_required_returns_needs_escalation_job(
    tmp_path: Path,
) -> None:
    """Needs-escalation jobs are user-attention-required (waiting for decision)."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="needs_escalation", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].status == "needs_escalation"


def test_list_user_attention_required_returns_completed_pending_promotion(
    tmp_path: Path,
) -> None:
    """Completed jobs with pending promotion are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="pending")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].promotion_state == "pending"


def test_list_user_attention_required_returns_completed_prechecks_failed(
    tmp_path: Path,
) -> None:
    """Completed jobs with prechecks_failed are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="prechecks_failed")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].promotion_state == "prechecks_failed"


def test_list_user_attention_required_returns_failed_null_promotion(
    tmp_path: Path,
) -> None:
    """Failed jobs with null promotion_state are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="failed", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].status == "failed"


def test_list_user_attention_required_returns_unknown_null_promotion(
    tmp_path: Path,
) -> None:
    """Unknown jobs with null promotion_state are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="unknown", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].status == "unknown"


def test_list_user_attention_required_returns_rollback_needed(
    tmp_path: Path,
) -> None:
    """Jobs with rollback_needed promotion state are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="rollback_needed")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].promotion_state == "rollback_needed"


def test_list_user_attention_required_returns_queued_null_promotion(
    tmp_path: Path,
) -> None:
    """Queued jobs with null promotion_state are user-attention-required.

    This is the initial job shape after start() commits a new delegation —
    the job is queued but the execution turn has not yet begun.
    """
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="queued", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].status == "queued"


def test_list_user_attention_required_returns_applied(
    tmp_path: Path,
) -> None:
    """Jobs with applied promotion state are user-attention-required.

    Crash recovery state: diff applied but not yet verified.
    """
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="applied")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].promotion_state == "applied"


def test_list_user_attention_required_returns_prechecks_passed(
    tmp_path: Path,
) -> None:
    """Jobs with prechecks_passed promotion state are user-attention-required.

    Crash recovery state: prechecks passed but apply not yet completed.
    """
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="prechecks_passed")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].promotion_state == "prechecks_passed"


def test_list_user_attention_required_excludes_completed_null_promotion(
    tmp_path: Path,
) -> None:
    """Completed + null promotion_state is an impossible state — excluded to prevent
    poisoning the busy gate (cannot be promoted or discarded)."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 0


def test_list_user_attention_required_excludes_verified(tmp_path: Path) -> None:
    """Verified promotion is terminal — excluded from attention set."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="verified")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 0


def test_list_user_attention_required_excludes_discarded(tmp_path: Path) -> None:
    """Discarded promotion is terminal — excluded from attention set."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="discarded")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 0


def test_list_user_attention_required_excludes_rolled_back(tmp_path: Path) -> None:
    """Rolled-back promotion is terminal — excluded from attention set."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="rolled_back")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 0

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
) -> DelegationJob:
    return DelegationJob(
        job_id=job_id,
        runtime_id=runtime_id,
        collaboration_id=f"collab-{job_id}",
        base_commit="abc123",
        worktree_path=f"/tmp/wk-{job_id}",
        promotion_state="pending",
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
        handle.write('{"op": "create", "job_id": "job-3"')  # truncated, no closing brace

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

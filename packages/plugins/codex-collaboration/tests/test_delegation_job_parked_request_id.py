"""Packet 1: DelegationJob.parked_request_id + update_parked_request mutator."""

from __future__ import annotations

from server.delegation_job_store import DelegationJobStore
from server.models import DelegationJob


def _make_job(job_id: str = "j1") -> DelegationJob:
    return DelegationJob(
        job_id=job_id,
        runtime_id="rt1",
        collaboration_id="c1",
        base_commit="abc",
        worktree_path="/tmp/wt",
        promotion_state=None,
        status="running",
    )


def test_parked_request_id_default_is_none(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_job())
    result = store.get("j1")
    assert result is not None
    assert result.parked_request_id is None


def test_update_parked_request_sets_rid(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_job())
    store.update_parked_request("j1", "r1")
    result = store.get("j1")
    assert result is not None
    assert result.parked_request_id == "r1"


def test_update_parked_request_clears_rid(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_job())
    store.update_parked_request("j1", "r1")
    store.update_parked_request("j1", None)
    result = store.get("j1")
    assert result is not None
    assert result.parked_request_id is None


def test_update_parked_request_replay_consistency(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_job())
    store.update_parked_request("j1", "r-set1")
    store.update_parked_request("j1", None)
    store.update_parked_request("j1", "r-set2")
    reopened = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    result = reopened.get("j1")
    assert result is not None
    assert result.parked_request_id == "r-set2"


def test_legacy_records_without_field_replay_as_none(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    # Hand-write a legacy record with no parked_request_id field.
    import json
    legacy = {
        "op": "create",
        "job_id": "j-legacy",
        "runtime_id": "rt1",
        "collaboration_id": "c1",
        "base_commit": "abc",
        "worktree_path": "/tmp/wt",
        "promotion_state": None,
        "promotion_attempt": 0,
        "status": "running",
        "artifact_paths": [],
        "artifact_hash": None,
    }
    store._store_path.write_text(
        json.dumps(legacy, sort_keys=True) + "\n", encoding="utf-8"
    )
    result = store.get("j-legacy")
    assert result is not None
    assert result.parked_request_id is None


def test_list_user_attention_required_admits_canceled_jobs(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    job = DelegationJob(
        job_id="j-cancel",
        runtime_id="rt1",
        collaboration_id="c1",
        base_commit="abc",
        worktree_path="/tmp/wt",
        promotion_state=None,
        status="canceled",
    )
    store.create(job)
    attention = store.list_user_attention_required()
    assert any(j.job_id == "j-cancel" for j in attention), (
        "list_user_attention_required must admit canceled jobs with null "
        "promotion_state — see spec §JobStatus='canceled' propagation"
    )

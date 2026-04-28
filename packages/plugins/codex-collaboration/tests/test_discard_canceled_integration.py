"""Integration tests for discard() gate expansion — canceled status admission.

Validates that discard() admits status="canceled" with null promotion_state,
rejects post-mutation promotion states, and writes the audit event.
"""

from __future__ import annotations

import json
from pathlib import Path

from server.models import DiscardRejectedResponse, DiscardResult
from tests.test_delegation_controller import (  # type: ignore[import]
    _build_promote_scenario,
)


def test_discard_canceled_with_null_promotion_state_succeeds(tmp_path: Path) -> None:
    """Discard accepts a canceled job with null promotion_state (pre-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="canceled", promotion_state=None
    )

    result = controller.discard(job_id=job_id)

    assert isinstance(result, DiscardResult)
    assert result.job.promotion_state == "discarded"

    persisted = job_store.get(job_id)
    assert persisted is not None
    assert persisted.promotion_state == "discarded"


def test_discard_canceled_with_applied_promotion_state_rejects(tmp_path: Path) -> None:
    """Discard rejects a canceled job with applied promotion_state (post-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="canceled", promotion_state="applied"
    )

    result = controller.discard(job_id=job_id)

    assert isinstance(result, DiscardRejectedResponse)
    assert result.reason == "job_not_discardable"


def test_discard_canceled_with_rollback_needed_promotion_state_rejects(
    tmp_path: Path,
) -> None:
    """Discard rejects a canceled job with rollback_needed promotion_state."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="canceled", promotion_state="rollback_needed"
    )

    result = controller.discard(job_id=job_id)

    assert isinstance(result, DiscardRejectedResponse)
    assert result.reason == "job_not_discardable"


def test_discard_canceled_writes_audit_event(tmp_path: Path) -> None:
    """Discarding a canceled job writes an audit event with action='discard'."""
    controller, job_store, journal, _repo, job_id, _hash, _cb = _build_promote_scenario(
        tmp_path
    )
    job_store.update_status_and_promotion(
        job_id, status="canceled", promotion_state=None
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardResult)

    # Read audit events from the public path.
    audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
    assert audit_path.exists(), f"Audit file not found at {audit_path}"

    events = [json.loads(line) for line in audit_path.read_text().splitlines() if line]
    discard_events = [
        e for e in events if e.get("action") == "discard" and e.get("job_id") == job_id
    ]
    assert len(discard_events) >= 1, (
        f"Expected at least one discard audit event for job {job_id}, "
        f"found {len(discard_events)} in {len(events)} total events"
    )

"""Session-scoped JSONL store for DelegationJob records.

Parallels LineageStore (see contracts.md §Lineage Store for the same design
pattern). Append-only; replay on read; last record for each job_id wins.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, get_args

from .models import DelegationJob, JobStatus, PromotionState

_VALID_STATUSES: frozenset[str] = frozenset(get_args(JobStatus))
_VALID_PROMOTION_STATES: frozenset[str] = frozenset(get_args(PromotionState))
# Manually curated subset of JobStatus (not derived from get_args): "active"
# is the complement of terminal (completed | failed | unknown). Adding a new
# JobStatus should be an explicit decision about whether it counts as active.
_ACTIVE_STATUSES: frozenset[str] = frozenset({"queued", "running", "needs_escalation"})


def _is_valid_promotion_state(value: str | None) -> bool:
    """Accept None or any valid PromotionState literal."""
    return value is None or value in _VALID_PROMOTION_STATES


class DelegationJobStore:
    """Append-only JSONL store for DelegationJob records."""

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "delegation_jobs" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "jobs.jsonl"

    def create(self, job: DelegationJob) -> None:
        """Persist a new job record."""

        if job.status not in _VALID_STATUSES:
            raise ValueError(
                f"DelegationJobStore.create failed: unknown status. "
                f"Got: {job.status!r:.100}"
            )
        if not _is_valid_promotion_state(job.promotion_state):
            raise ValueError(
                f"DelegationJobStore.create failed: unknown promotion_state. "
                f"Got: {job.promotion_state!r:.100}"
            )
        self._append({"op": "create", **asdict(job)})

    def get(self, job_id: str) -> DelegationJob | None:
        """Retrieve a job by id, or None if not found."""

        return self._replay().get(job_id)

    def list(self) -> list[DelegationJob]:
        """Return all jobs for this session."""

        return list(self._replay().values())

    def list_active(self) -> list[DelegationJob]:
        """Return jobs whose status is not terminal (queued/running/needs_escalation)."""

        return [j for j in self._replay().values() if j.status in _ACTIVE_STATUSES]

    def update_status(self, job_id: str, status: JobStatus) -> None:
        """Append a status update record to the log.

        By design this does NOT verify that ``job_id`` exists before
        appending. Orphan updates (where the corresponding create record
        is missing or was never written) are silently dropped on replay —
        see ``_replay`` where ``op == "update_status"`` skips records whose
        job_id is not present in the reconstructed state. Callers that
        require creation verification must check ``get(job_id) is not None``
        first.
        """

        if status not in _VALID_STATUSES:
            raise ValueError(
                f"DelegationJobStore.update_status failed: unknown status. "
                f"Got: {status!r:.100}"
            )
        self._append({"op": "update_status", "job_id": job_id, "status": status})

    def update_status_and_promotion(
        self,
        job_id: str,
        *,
        status: JobStatus,
        promotion_state: PromotionState | None,
    ) -> None:
        """Atomically update status and promotion_state in a single JSONL append.

        Coupling these in one record ensures crash safety — a crash cannot
        strand a job as ``completed + promotion_state=None``.
        """

        if status not in _VALID_STATUSES:
            raise ValueError(
                f"DelegationJobStore.update_status_and_promotion failed: unknown status. "
                f"Got: {status!r:.100}"
            )
        if not _is_valid_promotion_state(promotion_state):
            raise ValueError(
                f"DelegationJobStore.update_status_and_promotion failed: unknown promotion_state. "
                f"Got: {promotion_state!r:.100}"
            )
        self._append(
            {
                "op": "update_status_and_promotion",
                "job_id": job_id,
                "status": status,
                "promotion_state": promotion_state,
            }
        )

    def update_promotion_state(
        self,
        job_id: str,
        *,
        promotion_state: PromotionState,
        promotion_attempt: int | None = None,
    ) -> None:
        """Append a promotion state update record to the log.

        By design this does NOT verify that ``job_id`` exists before
        appending. Orphan updates are silently dropped on replay.
        """

        if not _is_valid_promotion_state(promotion_state):
            raise ValueError(
                f"DelegationJobStore.update_promotion_state failed: unknown promotion_state. "
                f"Got: {promotion_state!r:.100}"
            )
        self._append(
            {
                "op": "update_promotion_state",
                "job_id": job_id,
                "promotion_state": promotion_state,
                "promotion_attempt": promotion_attempt,
            }
        )

    def update_artifacts(
        self,
        job_id: str,
        *,
        artifact_paths: tuple[str, ...],
        artifact_hash: str | None,
    ) -> None:
        """Append an artifact update record to the log."""

        self._append(
            {
                "op": "update_artifacts",
                "job_id": job_id,
                "artifact_paths": list(artifact_paths),
                "artifact_hash": artifact_hash,
            }
        )

    def _append(self, record: dict[str, Any]) -> None:
        with self._store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _replay(self) -> dict[str, DelegationJob]:
        """Replay the JSONL log and return the current state per job_id."""

        jobs: dict[str, DelegationJob] = {}
        if not self._store_path.exists():
            return jobs
        with self._store_path.open(encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    # Parse failure: silently skipped. Covers both crash-mid-write
                    # truncation (typically trailing) and any mid-file corruption.
                    # Distinguishing these two cases would require replay_jsonl;
                    # deferred to a follow-up per scope-lock.
                    continue
                if not isinstance(record, dict):
                    continue
                op = record.get("op")
                if op == "create":
                    fields = {
                        k: record[k]
                        for k in DelegationJob.__dataclass_fields__
                        if k in record
                    }
                    tuple_fields = ("artifact_paths",)
                    for field_name in tuple_fields:
                        if field_name in fields and isinstance(
                            fields[field_name], list
                        ):
                            fields[field_name] = tuple(fields[field_name])
                    try:
                        job = DelegationJob(**fields)
                    except TypeError:
                        # Forward-compat skip: record was written with a different
                        # DelegationJob shape (e.g., a missing required field added
                        # in a later version). Silent by design.
                        continue
                    if (
                        job.status not in _VALID_STATUSES
                        or not _is_valid_promotion_state(job.promotion_state)
                    ):
                        continue
                    jobs[record["job_id"]] = job
                elif op == "update_status":
                    job_id = record.get("job_id")
                    status = record.get("status")
                    if not isinstance(job_id, str) or not isinstance(status, str):
                        continue
                    if status not in _VALID_STATUSES:
                        continue
                    if job_id not in jobs:
                        continue
                    existing = jobs[job_id]
                    jobs[job_id] = DelegationJob(
                        **{**asdict(existing), "status": status}
                    )
                elif op == "update_status_and_promotion":
                    job_id = record.get("job_id")
                    status = record.get("status")
                    promotion_state = record.get("promotion_state")
                    if not isinstance(job_id, str) or not isinstance(status, str):
                        continue
                    if status not in _VALID_STATUSES:
                        continue
                    if not _is_valid_promotion_state(promotion_state):
                        continue
                    if job_id not in jobs:
                        continue
                    existing = jobs[job_id]
                    jobs[job_id] = DelegationJob(
                        **{
                            **asdict(existing),
                            "status": status,
                            "promotion_state": promotion_state,
                        }
                    )
                elif op == "update_artifacts":
                    job_id = record.get("job_id")
                    artifact_paths = record.get("artifact_paths")
                    artifact_hash = record.get("artifact_hash")
                    if not isinstance(job_id, str):
                        continue
                    if job_id not in jobs:
                        continue
                    if not isinstance(artifact_paths, list):
                        continue
                    artifact_paths = tuple(artifact_paths)
                    existing = jobs[job_id]
                    jobs[job_id] = DelegationJob(
                        **{
                            **asdict(existing),
                            "artifact_paths": artifact_paths,
                            "artifact_hash": artifact_hash,
                        }
                    )
                elif op == "update_promotion_state":
                    job_id = record.get("job_id")
                    promotion_state = record.get("promotion_state")
                    promotion_attempt = record.get("promotion_attempt")
                    if not isinstance(job_id, str):
                        continue
                    if job_id not in jobs:
                        continue
                    if not _is_valid_promotion_state(promotion_state):
                        continue
                    existing = jobs[job_id]
                    updates: dict[str, Any] = {
                        **asdict(existing),
                        "promotion_state": promotion_state,
                    }
                    if promotion_attempt is not None and type(promotion_attempt) is int:
                        updates["promotion_attempt"] = promotion_attempt
                    jobs[job_id] = DelegationJob(**updates)
        return jobs

"""Session-scoped JSONL store for PendingServerRequest records.

Mirrors DelegationJobStore pattern. Append-only; replay on read; last record
for each request_id wins. PendingServerRequest.status tracks the wire lifecycle
per recovery-and-journal.md:125-127, NOT the plugin escalation lifecycle.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, get_args

from .models import PendingRequestStatus, PendingServerRequest

_VALID_STATUSES: frozenset[str] = frozenset(get_args(PendingRequestStatus))


class PendingRequestStore:
    """Append-only JSONL store for PendingServerRequest records."""

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "pending_requests" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "requests.jsonl"

    def create(self, request: PendingServerRequest) -> None:
        """Persist a new request record."""
        if request.status not in _VALID_STATUSES:
            raise ValueError(
                f"PendingRequestStore.create failed: unknown status. "
                f"Got: {request.status!r:.100}"
            )
        record = asdict(request)
        record["available_decisions"] = list(record["available_decisions"])
        self._append({"op": "create", **record})

    def get(self, request_id: str) -> PendingServerRequest | None:
        """Retrieve a request by id, or None if not found."""
        return self._replay().get(request_id)

    def list_pending(self) -> list[PendingServerRequest]:
        """Return requests whose wire status is still pending."""
        return [r for r in self._replay().values() if r.status == "pending"]

    def list_by_collaboration_id(
        self, collaboration_id: str
    ) -> list[PendingServerRequest]:
        """Return all requests for a given collaboration."""
        return [
            r
            for r in self._replay().values()
            if r.collaboration_id == collaboration_id
        ]

    def update_status(
        self, request_id: str, status: str
    ) -> None:
        """Append a status update record to the log."""
        if status not in _VALID_STATUSES:
            raise ValueError(
                f"PendingRequestStore.update_status failed: unknown status. "
                f"Got: {status!r:.100}"
            )
        self._append(
            {"op": "update_status", "request_id": request_id, "status": status}
        )

    def _append(self, record: dict[str, Any]) -> None:
        with self._store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _replay(self) -> dict[str, PendingServerRequest]:
        """Replay the JSONL log and return the current state per request_id."""
        requests: dict[str, PendingServerRequest] = {}
        if not self._store_path.exists():
            return requests
        with self._store_path.open(encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                op = record.get("op")
                if op == "create":
                    try:
                        req = PendingServerRequest(
                            request_id=record["request_id"],
                            runtime_id=record["runtime_id"],
                            collaboration_id=record["collaboration_id"],
                            codex_thread_id=record["codex_thread_id"],
                            codex_turn_id=record["codex_turn_id"],
                            item_id=record["item_id"],
                            kind=record["kind"],
                            requested_scope=record.get("requested_scope", {}),
                            available_decisions=tuple(
                                record.get("available_decisions", ())
                            ),
                            status=record.get("status", "pending"),
                        )
                    except (KeyError, TypeError):
                        continue
                    if req.status not in _VALID_STATUSES:
                        continue
                    requests[req.request_id] = req
                elif op == "update_status":
                    req_id = record.get("request_id")
                    status = record.get("status")
                    if not isinstance(req_id, str) or not isinstance(status, str):
                        continue
                    if status not in _VALID_STATUSES:
                        continue
                    if req_id not in requests:
                        continue
                    existing = requests[req_id]
                    requests[req_id] = PendingServerRequest(
                        request_id=existing.request_id,
                        runtime_id=existing.runtime_id,
                        collaboration_id=existing.collaboration_id,
                        codex_thread_id=existing.codex_thread_id,
                        codex_turn_id=existing.codex_turn_id,
                        item_id=existing.item_id,
                        kind=existing.kind,
                        requested_scope=existing.requested_scope,
                        available_decisions=existing.available_decisions,
                        status=status,
                    )
        return requests

"""Session-scoped JSONL store for PendingServerRequest records.

Mirrors DelegationJobStore pattern. Append-only; replay on read; last record
for each request_id wins. PendingServerRequest.status tracks the wire lifecycle
per recovery-and-journal.md:125-127, NOT the plugin escalation lifecycle.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Literal, cast, get_args

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

    def mark_resolved(self, request_id: str, resolved_at: str) -> None:
        """Atomic transition to status="resolved" with resolved_at timestamp.

        Success-path mutator only. Not used on timeout or dispatch-failure
        paths — those use record_timeout / record_dispatch_failure which set
        status="canceled" atomically.
        """
        self._append(
            {
                "op": "mark_resolved",
                "request_id": request_id,
                "resolved_at": resolved_at,
            }
        )

    def record_response_dispatch(
        self,
        request_id: str,
        *,
        action: Literal["approve", "deny"],
        payload: dict[str, Any],
        dispatch_at: str,
    ) -> None:
        """Record the successful transport write for an operator decision.

        dispatch_result is hardcoded to "succeeded" inside this mutator — no
        caller kwarg. The failure state is represented structurally by the
        separate record_dispatch_failure mutator (Task 8).
        """
        self._append(
            {
                "op": "record_response_dispatch",
                "request_id": request_id,
                "resolution_action": action,
                "response_payload": payload,
                "response_dispatch_at": dispatch_at,
                "dispatch_result": "succeeded",
            }
        )

    def record_protocol_echo(
        self,
        request_id: str,
        *,
        signals: tuple[str, ...],
        observed_at: str,
    ) -> None:
        """Record post-turn protocol echo signals observed for this request."""
        self._append(
            {
                "op": "record_protocol_echo",
                "request_id": request_id,
                "protocol_echo_signals": list(signals),
                "protocol_echo_observed_at": observed_at,
            }
        )

    def record_timeout(
        self,
        request_id: str,
        *,
        response_payload: dict[str, Any] | None,
        response_dispatch_at: str | None,
        dispatch_result: Literal["succeeded", "failed"] | None,
        dispatch_error: str | None,
        interrupt_error: str | None = None,
    ) -> None:
        """Atomic timeout record: timed_out=True + status=canceled in single append.

        Per spec §Timeout record fields:
          - Cancel-capable kind, dispatch succeeded:
              payload={"decision":"cancel"}, at=<iso>, result="succeeded", error=None, interrupt_error=None
          - Cancel-capable kind, dispatch failed:
              payload={"decision":"cancel"}, at=<iso>, result="failed",
              error=<sanitized>, interrupt_error=None
          - Non-cancel-capable kind, interrupt succeeded:
              payload=None, at=None, result=None, error=None, interrupt_error=None
          - Non-cancel-capable kind, interrupt failed:
              payload=None, at=None, result=None, error=None, interrupt_error=<sanitized>
        """
        self._append(
            {
                "op": "record_timeout",
                "request_id": request_id,
                "timed_out": True,
                "status": "canceled",
                "resolution_action": None,
                "response_payload": response_payload,
                "response_dispatch_at": response_dispatch_at,
                "dispatch_result": dispatch_result,
                "dispatch_error": dispatch_error,
                "interrupt_error": interrupt_error,
            }
        )

    def record_dispatch_failure(
        self,
        request_id: str,
        *,
        action: Literal["approve", "deny"],
        payload: dict[str, Any],
        dispatch_at: str,
        dispatch_error: str,
    ) -> None:
        """Atomic dispatch-failure record: status=canceled + dispatch_result=failed
        + resolution_action + response_payload + response_dispatch_at + dispatch_error
        in a single append. Used when session.respond() raises on the operator-decide
        path. resolved_at stays None (the operator decision was NOT applied).
        """
        self._append(
            {
                "op": "record_dispatch_failure",
                "request_id": request_id,
                "status": "canceled",
                "dispatch_result": "failed",
                "dispatch_error": dispatch_error,
                "resolution_action": action,
                "response_payload": payload,
                "response_dispatch_at": dispatch_at,
                "resolved_at": None,
            }
        )

    def record_internal_abort(self, request_id: str, *, reason: str) -> None:
        """Atomic internal-abort record: status=canceled + internal_abort_reason
        + resolution_action=None + payload fields cleared, in a single append.
        Used when the worker wakes on InternalAbort (plugin-invariant violation).
        """
        self._append(
            {
                "op": "record_internal_abort",
                "request_id": request_id,
                "status": "canceled",
                "internal_abort_reason": reason,
                "resolution_action": None,
                "response_payload": None,
                "response_dispatch_at": None,
                "dispatch_result": None,
                "resolved_at": None,
            }
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
                            resolution_action=record.get("resolution_action"),
                            response_payload=record.get("response_payload"),
                            response_dispatch_at=record.get("response_dispatch_at"),
                            dispatch_result=record.get("dispatch_result"),
                            dispatch_error=record.get("dispatch_error"),
                            interrupt_error=record.get("interrupt_error"),
                            resolved_at=record.get("resolved_at"),
                            protocol_echo_signals=tuple(record.get("protocol_echo_signals", ())),
                            protocol_echo_observed_at=record.get("protocol_echo_observed_at"),
                            timed_out=record.get("timed_out", False),
                            internal_abort_reason=record.get("internal_abort_reason"),
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
                    requests[req_id] = replace(requests[req_id], status=cast(PendingRequestStatus, status))
                elif op == "mark_resolved":
                    rid = record.get("request_id")
                    if rid in requests:
                        requests[rid] = replace(
                            requests[rid],
                            status="resolved",
                            resolved_at=record.get("resolved_at"),
                        )
                elif op == "record_response_dispatch":
                    rid = record.get("request_id")
                    if rid in requests:
                        requests[rid] = replace(
                            requests[rid],
                            resolution_action=record.get("resolution_action"),
                            response_payload=record.get("response_payload"),
                            response_dispatch_at=record.get("response_dispatch_at"),
                            dispatch_result=record.get("dispatch_result"),
                        )
                elif op == "record_protocol_echo":
                    rid = record.get("request_id")
                    if rid in requests:
                        raw_signals = record.get("protocol_echo_signals") or ()
                        requests[rid] = replace(
                            requests[rid],
                            protocol_echo_signals=tuple(raw_signals),
                            protocol_echo_observed_at=record.get(
                                "protocol_echo_observed_at"
                            ),
                        )
                elif op == "record_timeout":
                    rid = record.get("request_id")
                    if rid in requests:
                        requests[rid] = replace(
                            requests[rid],
                            timed_out=True,
                            status="canceled",
                            resolution_action=None,
                            response_payload=record.get("response_payload"),
                            response_dispatch_at=record.get("response_dispatch_at"),
                            dispatch_result=record.get("dispatch_result"),
                            dispatch_error=record.get("dispatch_error"),
                            interrupt_error=record.get("interrupt_error"),
                        )
                elif op == "record_dispatch_failure":
                    rid = record.get("request_id")
                    if rid in requests:
                        requests[rid] = replace(
                            requests[rid],
                            status="canceled",
                            dispatch_result="failed",
                            dispatch_error=record.get("dispatch_error"),
                            resolution_action=record.get("resolution_action"),
                            response_payload=record.get("response_payload"),
                            response_dispatch_at=record.get("response_dispatch_at"),
                            resolved_at=None,
                        )
                elif op == "record_internal_abort":
                    rid = record.get("request_id")
                    if rid in requests:
                        requests[rid] = replace(
                            requests[rid],
                            status="canceled",
                            internal_abort_reason=record.get("internal_abort_reason"),
                            resolution_action=None,
                            response_payload=None,
                            response_dispatch_at=None,
                            dispatch_result=None,
                            resolved_at=None,
                        )
        return requests

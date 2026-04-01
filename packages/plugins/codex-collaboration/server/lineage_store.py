"""Lineage store: session-partitioned append-only JSONL handle persistence.

See contracts.md §Lineage Store for the normative contract.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, get_args

from .models import CapabilityProfile, CollaborationHandle, HandleStatus
from .replay import ReplayDiagnostics, SchemaViolation, UnknownOperation, replay_jsonl

# Valid literal values from type aliases
_VALID_STATUSES: frozenset[str] = frozenset(get_args(HandleStatus))
_VALID_CAPABILITIES: frozenset[str] = frozenset(get_args(CapabilityProfile))

# Required string fields for create op (collaboration_id validated earlier)
_CREATE_REQUIRED_STR = (
    "capability_class",
    "runtime_id",
    "codex_thread_id",
    "claude_session_id",
    "repo_root",
    "created_at",
    "status",
)
_CREATE_OPTIONAL_STR = (
    "parent_collaboration_id",
    "fork_reason",
    "resolved_posture",
    "resolved_effort",
)


def _make_lineage_callback(
    handles: dict[str, CollaborationHandle],
) -> Callable[[dict[str, Any]], None]:
    """Create a replay callback that mutates the captured handles dict."""

    def apply(record: dict[str, Any]) -> None:
        op = record.get("op")
        if not isinstance(op, str):
            raise SchemaViolation("missing or non-string op")
        cid = record.get("collaboration_id")
        if not isinstance(cid, str):
            raise SchemaViolation("missing or non-string collaboration_id")

        if op == "create":
            for name in _CREATE_REQUIRED_STR:
                if not isinstance(record.get(name), str):
                    raise SchemaViolation(f"create op: {name} missing or not a string")
            for name in _CREATE_OPTIONAL_STR:
                val = record.get(name)
                if val is not None and not isinstance(val, str):
                    raise SchemaViolation(f"create op: {name} is not a string")
            rtb = record.get("resolved_turn_budget")
            if rtb is not None and type(rtb) is not int:
                raise SchemaViolation("create op: resolved_turn_budget is not an int")
            # Literal validation: reject unknown status/capability_class values.
            # Compatibility decision: unknown literals are SchemaViolation, not
            # forward-compatible. This is intentionally tighter than the extra-field
            # policy (which silently ignores additive keys). Rationale: status drives
            # controller behavior (filtering, lifecycle transitions) and capability_class
            # determines the execution model. A handle with status="quarantined" or
            # capability_class="delegation" from a newer writer would be semantically
            # misinterpreted by older readers — safer to skip than to create a handle
            # the reader cannot handle correctly. New enum values require coordinated
            # rollout: update the Literal type, then start writing the new value.
            if record["capability_class"] not in _VALID_CAPABILITIES:
                raise SchemaViolation(
                    f"create op: unknown capability_class {record['capability_class']!r}"
                )
            if record["status"] not in _VALID_STATUSES:
                raise SchemaViolation(f"create op: unknown status {record['status']!r}")
            # Build from known fields only (extra fields silently ignored)
            fields = {
                k: record[k]
                for k in CollaborationHandle.__dataclass_fields__
                if k in record
            }
            handles[cid] = CollaborationHandle(**fields)

        elif op == "update_status":
            if not isinstance(record.get("status"), str):
                raise SchemaViolation(
                    "update_status op: status missing or not a string"
                )
            # Same literal validation rationale as create op (see comment above)
            if record["status"] not in _VALID_STATUSES:
                raise SchemaViolation(
                    f"update_status op: unknown status {record['status']!r}"
                )
            if cid in handles:
                handles[cid] = _replace_handle(handles[cid], status=record["status"])

        elif op == "update_runtime":
            if not isinstance(record.get("runtime_id"), str):
                raise SchemaViolation(
                    "update_runtime op: runtime_id missing or not a string"
                )
            if cid in handles:
                updates: dict[str, Any] = {"runtime_id": record["runtime_id"]}
                if "codex_thread_id" in record:
                    if not isinstance(record["codex_thread_id"], str):
                        raise SchemaViolation(
                            "update_runtime op: codex_thread_id is not a string"
                        )
                    updates["codex_thread_id"] = record["codex_thread_id"]
                handles[cid] = _replace_handle(handles[cid], **updates)

        else:
            raise UnknownOperation(op)

        return None

    return apply


class LineageStore:
    """Persists CollaborationHandle records as append-only JSONL.

    All mutations append a new record. On read, the store replays the log —
    the last record for each collaboration_id wins. Incomplete trailing records
    (from crash mid-write) are discarded on load.
    """

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "lineage" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "handles.jsonl"

    def create(self, handle: CollaborationHandle) -> None:
        """Persist a new handle."""
        self._append({"op": "create", **asdict(handle)})

    def get(self, collaboration_id: str) -> CollaborationHandle | None:
        """Retrieve a handle by collaboration_id, or None if not found."""
        return self._replay().get(collaboration_id)

    def list(
        self,
        *,
        repo_root: str | None = None,
        status: HandleStatus | None = None,
    ) -> list[CollaborationHandle]:
        """Query handles with optional repo_root and status filters."""
        handles = list(self._replay().values())
        if repo_root is not None:
            handles = [h for h in handles if h.repo_root == repo_root]
        if status is not None:
            handles = [h for h in handles if h.status == status]
        return handles

    def update_status(self, collaboration_id: str, status: HandleStatus) -> None:
        """Transition handle lifecycle status."""
        self._append(
            {
                "op": "update_status",
                "collaboration_id": collaboration_id,
                "status": status,
            }
        )

    def update_runtime(
        self,
        collaboration_id: str,
        runtime_id: str,
        codex_thread_id: str | None = None,
    ) -> None:
        """Remap handle to a new runtime (and optionally a new thread identity)."""
        record: dict[str, str] = {
            "op": "update_runtime",
            "collaboration_id": collaboration_id,
            "runtime_id": runtime_id,
        }
        if codex_thread_id is not None:
            record["codex_thread_id"] = codex_thread_id
        self._append(record)

    def cleanup(self) -> None:
        """Remove the session directory. Called on session end."""
        if self._store_dir.exists():
            shutil.rmtree(self._store_dir)

    def check_health(self) -> ReplayDiagnostics:
        """Replay and return diagnostics. Test and diagnostic support only."""
        handles: dict[str, CollaborationHandle] = {}
        _, diagnostics = replay_jsonl(self._store_path, _make_lineage_callback(handles))
        return diagnostics

    def _append(self, record: dict[str, Any]) -> None:
        with self._store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _replay(self) -> dict[str, CollaborationHandle]:
        """Replay the JSONL log to reconstruct current handle state."""
        handles: dict[str, CollaborationHandle] = {}
        replay_jsonl(self._store_path, _make_lineage_callback(handles))
        return handles


def _replace_handle(handle: CollaborationHandle, **changes: Any) -> CollaborationHandle:
    """Return a new handle with specified fields replaced (frozen dataclass)."""
    return CollaborationHandle(**{**asdict(handle), **changes})

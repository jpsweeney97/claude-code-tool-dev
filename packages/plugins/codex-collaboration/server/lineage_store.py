"""Lineage store: session-partitioned append-only JSONL handle persistence.

See contracts.md §Lineage Store for the normative contract.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import CollaborationHandle, HandleStatus


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
        self._append({
            "op": "update_status",
            "collaboration_id": collaboration_id,
            "status": status,
        })

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

    def _append(self, record: dict[str, Any]) -> None:
        with self._store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _replay(self) -> dict[str, CollaborationHandle]:
        """Replay the JSONL log to reconstruct current handle state."""
        if not self._store_path.exists():
            return {}
        handles: dict[str, CollaborationHandle] = {}
        with self._store_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._apply_record(handles, record)
        return handles

    def _apply_record(
        self,
        handles: dict[str, CollaborationHandle],
        record: dict[str, Any],
    ) -> None:
        op = record.get("op")
        cid = record.get("collaboration_id")
        if cid is None:
            return
        if op == "create":
            fields = {
                k: record[k]
                for k in CollaborationHandle.__dataclass_fields__
                if k in record
            }
            handles[cid] = CollaborationHandle(**fields)
        elif op == "update_status" and cid in handles:
            handles[cid] = _replace_handle(handles[cid], status=record["status"])
        elif op == "update_runtime" and cid in handles:
            updates: dict[str, Any] = {"runtime_id": record["runtime_id"]}
            if "codex_thread_id" in record:
                updates["codex_thread_id"] = record["codex_thread_id"]
            handles[cid] = _replace_handle(handles[cid], **updates)


def _replace_handle(handle: CollaborationHandle, **changes: Any) -> CollaborationHandle:
    """Return a new handle with specified fields replaced (frozen dataclass)."""
    return CollaborationHandle(**{**asdict(handle), **changes})

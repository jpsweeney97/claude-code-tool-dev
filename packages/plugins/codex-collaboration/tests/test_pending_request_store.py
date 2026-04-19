"""Tests for PendingRequestStore — JSONL persistence for server request records."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.models import PendingServerRequest
from server.pending_request_store import PendingRequestStore


def _make_request(
    *,
    request_id: str = "req-1",
    runtime_id: str = "rt-1",
    collaboration_id: str = "collab-1",
    kind: str = "command_approval",
    status: str = "pending",
) -> PendingServerRequest:
    return PendingServerRequest(
        request_id=request_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-1",
        kind=kind,
        requested_scope={"command": "pytest", "cwd": "/repo"},
        available_decisions=("accept", "decline", "cancel"),
        status=status,
    )


class TestPendingRequestStoreCreate:
    def test_create_persists_request(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        request = _make_request()
        store.create(request)
        retrieved = store.get("req-1")
        assert retrieved is not None
        assert retrieved.request_id == "req-1"
        assert retrieved.kind == "command_approval"

    def test_create_survives_replay(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request())
        store2 = PendingRequestStore(tmp_path, "sess-1")
        assert store2.get("req-1") is not None


class TestPendingRequestStoreUpdateStatus:
    def test_update_status_changes_status(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request(status="pending"))
        store.update_status("req-1", "resolved")
        retrieved = store.get("req-1")
        assert retrieved is not None
        assert retrieved.status == "resolved"

    def test_update_status_rejects_invalid_status(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request())
        with pytest.raises(ValueError, match="unknown status"):
            store.update_status("req-1", "bogus")


class TestPendingRequestStoreList:
    def test_list_pending_returns_only_pending(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request(request_id="req-1", status="pending"))
        store.create(_make_request(request_id="req-2", status="resolved"))
        pending = store.list_pending()
        assert len(pending) == 1
        assert pending[0].request_id == "req-1"

    def test_list_by_collaboration_id(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request(request_id="req-1", collaboration_id="c1"))
        store.create(_make_request(request_id="req-2", collaboration_id="c2"))
        result = store.list_by_collaboration_id("c1")
        assert len(result) == 1
        assert result[0].request_id == "req-1"


class TestPendingRequestStoreReplay:
    def test_replay_skips_invalid_status(self, tmp_path: Path) -> None:
        """Records with invalid status are silently skipped on replay."""
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request(status="pending"))
        store_path = tmp_path / "pending_requests" / "sess-1" / "requests.jsonl"
        with store_path.open("a") as f:
            f.write('{"op":"update_status","request_id":"req-1","status":"bogus"}\n')
        store2 = PendingRequestStore(tmp_path, "sess-1")
        retrieved = store2.get("req-1")
        assert retrieved is not None
        assert retrieved.status == "pending"  # corrupt update skipped

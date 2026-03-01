"""Tests for session registry."""

import time

from scripts.session_registry import SessionRegistry


class TestSessionRegistry:
    def test_register_and_active_count(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/to/transcript.jsonl")
        assert reg.active_count() == 1

    def test_register_multiple_sessions(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/1.jsonl")
        reg.register("session_2", "/path/2.jsonl")
        assert reg.active_count() == 2

    def test_deregister_removes_session(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/1.jsonl")
        assert reg.deregister("session_1") is True
        assert reg.active_count() == 0

    def test_deregister_nonexistent_returns_false(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        assert reg.deregister("nonexistent") is False

    def test_renew_updates_heartbeat(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/1.jsonl")
        assert reg.renew("session_1") is True

    def test_renew_nonexistent_returns_false(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        assert reg.renew("nonexistent") is False

    def test_lease_expiry(self) -> None:
        reg = SessionRegistry(lease_timeout=0)  # Expire immediately
        reg.register("session_1", "/path/1.jsonl")
        time.sleep(0.01)
        expired = reg.expire_leases()
        assert "session_1" in expired
        assert reg.active_count() == 0

    def test_get_transcript_path(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/to/transcript.jsonl")
        assert reg.get_transcript_path("session_1") == "/path/to/transcript.jsonl"

    def test_get_transcript_path_unknown(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        assert reg.get_transcript_path("unknown") is None

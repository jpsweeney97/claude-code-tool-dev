"""Session registry for shared sidecar.

Tracks active Claude Code sessions with lease-based expiry.
Thread-safe for concurrent access from HTTP handler threads.

Design reference: Amendment 3 F3 (session lifecycle).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class SessionEntry:
    transcript_path: str
    registered_at: float
    last_heartbeat: float


class SessionRegistry:
    def __init__(self, lease_timeout: int = 600) -> None:
        self.lease_timeout = lease_timeout
        self._sessions: dict[str, SessionEntry] = {}
        self._lock = threading.Lock()

    def register(self, session_id: str, transcript_path: str) -> None:
        now = time.time()
        with self._lock:
            self._sessions[session_id] = SessionEntry(
                transcript_path=transcript_path,
                registered_at=now,
                last_heartbeat=now,
            )

    def deregister(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def renew(self, session_id: str) -> bool:
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None:
                return False
            entry.last_heartbeat = time.time()
            return True

    def expire_leases(self) -> list[str]:
        now = time.time()
        with self._lock:
            expired = [
                sid
                for sid, entry in self._sessions.items()
                if now - entry.last_heartbeat > self.lease_timeout
            ]
            for sid in expired:
                del self._sessions[sid]
        return expired

    def active_count(self) -> int:
        self.expire_leases()
        with self._lock:
            return len(self._sessions)

    def get_transcript_path(self, session_id: str) -> str | None:
        with self._lock:
            entry = self._sessions.get(session_id)
            return entry.transcript_path if entry else None

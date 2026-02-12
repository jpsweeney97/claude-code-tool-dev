"""Server state management: HMAC tokens, TurnRequest store, AppContext.

Per-process state with bounded capacity. Helper restart invalidates all tokens.

Design decisions:
- Single per-process 32-byte random key (D6/D8)
- MAX_TURN_RECORDS=200 with oldest-eviction (D8)
- Duplicate turn_request_ref rejection (D8)
- Used-bit not set on verification failure (D10)
- Stored token comparison is security; recompute is diagnostic (D10)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from collections import OrderedDict
from dataclasses import dataclass, field

from context_injection.canonical import ScoutTokenPayload, canonical_json_bytes
from context_injection.types import ReadSpec, GrepSpec, TurnRequest

MAX_TURN_RECORDS: int = 200
"""Bounded store capacity. Oldest-eviction when exceeded."""

TAG_LEN: int = 16
"""HMAC tag length in bytes (128 bits). Truncated from SHA-256 output."""


@dataclass
class TurnRequestRecord:
    """Stored record for Call 2 validation."""

    turn_request: TurnRequest
    scout_options: dict[str, tuple[ReadSpec | GrepSpec, str]]
    """scout_option_id -> (frozen ScoutSpec, HMAC token) -- atomic pairs."""
    used: bool = False
    """One-shot used-bit. Set only after successful verification, before execution."""


@dataclass
class AppContext:
    """Per-process server state, yielded by MCPServer lifespan."""

    hmac_key: bytes
    repo_root: str
    store: OrderedDict[str, TurnRequestRecord] = field(default_factory=OrderedDict)
    git_files: set[str] = field(default_factory=set)
    """Tracked file paths from git ls-files (repo-relative, populated at startup)."""
    entity_counter: int = 0
    """Monotonic counter for entity IDs within this process."""

    @classmethod
    def create(cls, repo_root: str, git_files: set[str] | None = None) -> AppContext:
        """Create a new AppContext with a fresh HMAC key."""
        return cls(
            hmac_key=os.urandom(32),
            repo_root=repo_root,
            git_files=git_files or set(),
        )

    def next_entity_id(self) -> str:
        """Generate the next entity ID (e_NNN format, monotonic per process)."""
        self.entity_counter += 1
        return f"e_{self.entity_counter:03d}"

    def store_record(self, ref: str, record: TurnRequestRecord) -> None:
        """Store a TurnRequestRecord with bounded eviction.

        Raises ValueError if ref already exists (duplicate rejection).
        """
        if ref in self.store:
            raise ValueError(f"Duplicate turn_request_ref: {ref}")
        # Evict oldest if at capacity
        while len(self.store) >= MAX_TURN_RECORDS:
            self.store.popitem(last=False)
        self.store[ref] = record


def make_turn_request_ref(req: TurnRequest) -> str:
    """Build turn_request_ref: '{conversation_id}:{turn_number}'."""
    return f"{req.conversation_id}:{req.turn_number}"


def generate_token(key: bytes, payload: ScoutTokenPayload) -> str:
    """Generate base64url-encoded HMAC-SHA256 token, truncated to TAG_LEN bytes.

    Contract: base64url(HMAC-SHA256(K, canonical_bytes))[:TAG_LEN]

    Padding convention: standard base64url with '=' padding (Python default).
    Both generate and verify use the same function, so padding is consistent.
    Stripping padding would save 1-2 chars but adds decode complexity.
    """
    canonical = canonical_json_bytes(payload)
    mac = hmac.new(key, canonical, hashlib.sha256).digest()
    truncated = mac[:TAG_LEN]
    return base64.urlsafe_b64encode(truncated).decode("ascii")


def verify_token(key: bytes, payload: ScoutTokenPayload, token: str) -> bool:
    """Verify an HMAC token via constant-time comparison.

    Returns True if the token matches the expected HMAC for the payload.
    """
    expected = generate_token(key, payload)
    return hmac.compare_digest(expected.encode("ascii"), token.encode("ascii"))

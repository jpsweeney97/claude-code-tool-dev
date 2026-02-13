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
from typing import Literal

from context_injection.canonical import ScoutTokenPayload, canonical_json_bytes
from context_injection.types import ReadSpec, GrepSpec, TurnRequest

MAX_TURN_RECORDS: int = 200
"""Bounded store capacity. Oldest-eviction when exceeded."""

TAG_LEN: int = 16
"""HMAC tag length in bytes (128 bits). Truncated from SHA-256 output."""


@dataclass(frozen=True)
class ScoutOptionRecord:
    """Stored metadata for a single scout option.

    Bundles everything needed to produce a protocol-compliant ScoutResult
    at execution time. Created during Call 1 (template synthesis).
    Consumed during Call 2 via consume_scout().

    Invariant: ``action`` must equal ``spec.action``. Enforced by __post_init__.
    """

    spec: ReadSpec | GrepSpec
    token: str
    template_id: str
    entity_id: str
    entity_key: str
    risk_signal: bool
    path_display: str
    action: Literal["read", "grep"]

    def __post_init__(self) -> None:
        if self.action != self.spec.action:
            raise ValueError(
                f"ScoutOptionRecord action/spec mismatch: "
                f"action={self.action!r}, spec.action={self.spec.action!r}"
            )


ScoutOptionRegistry = dict[str, ScoutOptionRecord]
"""scout_option_id -> ScoutOptionRecord. Full metadata for Call 2."""


@dataclass
class TurnRequestRecord:
    """Stored record for Call 2 validation."""

    turn_request: TurnRequest
    scout_options: ScoutOptionRegistry
    used: bool = False
    """One-shot used-bit. Set only after successful verification, before execution.

    Correctness assumes single in-flight request per server process/connection.
    If multiplexing is enabled, protect ``used`` with a lock.
    """


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

    def consume_scout(
        self,
        turn_request_ref: str,
        scout_option_id: str,
        scout_token: str,
    ) -> ScoutOptionRecord:
        """Atomic verify-and-consume for Call 2.

        Validates HMAC token, checks replay, marks used, returns record.
        All failures raise ValueError -> maps to ScoutResultInvalid.

        Check order: ref lookup -> option lookup -> HMAC verify -> replay check -> mark used.
        Used-bit NOT set on verification failure (D10 design decision).

        INVARIANT: One scout per turn. The used bit is per-record (not
        per-option). After ANY option is consumed, ALL other options on
        the same turn are blocked. This enforces the Budget Computation
        Rule: "scout_available = false, 1 scout per turn, just consumed."
        See test_different_option_after_used_raises for verification.

        Concurrency: correctness assumes single in-flight request per
        server process (FastMCP stdio transport). If multiplexing is
        added, the read-check-write on ``record.used`` must be atomic.
        """
        # 1. Look up turn request record
        record = self.store.get(turn_request_ref)
        if record is None:
            raise ValueError(
                f"consume_scout failed: turn_request_ref not found. "
                f"Got: {turn_request_ref!r:.100}"
            )

        # 2. Look up scout option
        option = record.scout_options.get(scout_option_id)
        if option is None:
            raise ValueError(
                f"consume_scout failed: scout_option_id not found. "
                f"Got: {scout_option_id!r:.100}"
            )

        # 3. Verify HMAC token
        payload = ScoutTokenPayload(
            v=1,
            conversation_id=record.turn_request.conversation_id,
            turn_number=record.turn_request.turn_number,
            scout_option_id=scout_option_id,
            spec=option.spec,
        )
        if not verify_token(self.hmac_key, payload, scout_token):
            raise ValueError(
                f"consume_scout failed: token verification failed "
                f"for {scout_option_id!r}"
            )

        # 4. Replay check (AFTER token verification — don't leak used state)
        if record.used:
            raise ValueError(
                f"consume_scout failed: record already used "
                f"for {turn_request_ref!r}"
            )

        # 5. Mark used
        record.used = True

        return option

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

    Contract: base64url(HMAC-SHA256(K, canonical_bytes)[:TAG_LEN])

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

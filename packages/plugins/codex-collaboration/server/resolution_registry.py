"""ResolutionRegistry — in-memory cross-thread coordination for deferred-approval.

Packet 1 (T-20260423-02). The registry is the ONLY in-memory mutable state
that crosses threads (IO-2). See spec §Resolution registry +
§Transactional registry protocol.

Two independent channels per registry instance:
  - Per-request channel: awaiting → reserved → consuming (operator-decide)
    OR awaiting → aborted (internal abort). State keyed by request_id.
  - Per-job capture-ready channel: one-shot CaptureReadyEvent keyed by job_id.

Locking discipline: a single registry-wide threading.Lock guards entry state
transitions. threading.Event instances are created per-entry for worker
block-and-wake.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Literal

from .models import EscalatableRequestKind

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------- resolution types


@dataclass(frozen=True)
class DecisionResolution:
    """Resolution delivered to the worker by decide() or by the registry's
    timeout timer.
    """

    payload: dict[str, Any]
    kind: EscalatableRequestKind
    is_timeout: bool = False


@dataclass(frozen=True)
class InternalAbort:
    """Resolution delivered to the worker when the main thread has observed
    a plugin-invariant violation after capture (parked-projection invariant,
    unknown-kind in escalation projection). Caller writes NO journal entry.
    Worker owns all durable state writes.
    """

    reason: str


Resolution = DecisionResolution | InternalAbort


# -------------------------------------------------------------------- capture-ready outcomes


@dataclass(frozen=True)
class Parked:
    request_id: str


@dataclass(frozen=True)
class TurnCompletedWithoutCapture:
    pass


@dataclass(frozen=True)
class TurnTerminalWithoutEscalation:
    """Terminal non-escalation outcome. Worker persisted terminal job status
    before signaling. start() returns a plain DelegationJob — does NOT raise.
    """

    job_status: Literal["unknown"]
    reason: str
    request_id: str | None


@dataclass(frozen=True)
class WorkerFailed:
    """Genuine worker-side exception. NOT used for unknown-kind parse
    failures — those use TurnTerminalWithoutEscalation.
    """

    error: Exception


@dataclass(frozen=True)
class StartWaitElapsed:
    """Synchronous start-wait budget elapsed without a terminal outcome.
    Worker may still be valid-running; caller polls for eventual outcome.
    """

    pass


ParkedCaptureResult = (
    Parked
    | TurnCompletedWithoutCapture
    | TurnTerminalWithoutEscalation
    | WorkerFailed
    | StartWaitElapsed
)


# -------------------------------------------------------------------- reservation token


@dataclass(frozen=True)
class ReservationToken:
    """Opaque handle returned by reserve() and consumed by exactly one
    subsequent commit_signal or abort_reservation call.

    The generation field is a per-register monotonic counter on the
    registry. It enables commit_signal/abort_reservation to detect a
    stale token whose entry was discarded and re-registered with the
    same request_id between reserve and commit: the new entry carries
    a strictly larger generation, so the stale token's generation no
    longer matches and the operation is rejected without affecting
    the new entry's state.
    """

    request_id: str
    generation: int


# -------------------------------------------------------------------- per-request entry


_EntryState = Literal["awaiting", "reserved", "consuming", "aborted"]


@dataclass
class _RegistryEntry:
    request_id: str
    job_id: str
    kind: EscalatableRequestKind
    timeout_seconds: float
    state: _EntryState
    generation: int
    event: threading.Event
    # Resolution pending delivery (set when state transitions to consuming or aborted).
    pending: Resolution | None = None
    # Timer thread for the operator-window budget.
    timer: threading.Timer | None = None


# -------------------------------------------------------------------- per-job capture-ready entry


@dataclass
class _CaptureReadyChannel:
    job_id: str
    event: threading.Event = field(default_factory=threading.Event)
    outcome: ParkedCaptureResult | None = None
    resolved: bool = False  # True once wait_for_parked has returned any outcome


# -------------------------------------------------------------------- registry


class ResolutionRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, _RegistryEntry] = {}
        self._next_generation = 0
        self._capture_channels: dict[str, _CaptureReadyChannel] = {}

    # --- per-request API -----------------------------------------------------

    def register(
        self,
        request_id: str,
        *,
        job_id: str,
        kind: EscalatableRequestKind,
        timeout_seconds: float,
    ) -> None:
        """Establish a new per-request entry in awaiting state and start its
        timeout timer. Worker calls this immediately before announce_parked.
        """
        with self._lock:
            if request_id in self._entries:
                raise RuntimeError(
                    f"ResolutionRegistry.register failed: duplicate request_id. "
                    f"Got: {request_id!r:.100}"
                )
            self._next_generation += 1
            generation = self._next_generation
            event = threading.Event()
            entry = _RegistryEntry(
                request_id=request_id,
                job_id=job_id,
                kind=kind,
                timeout_seconds=timeout_seconds,
                state="awaiting",
                generation=generation,
                event=event,
            )
            entry.timer = threading.Timer(
                timeout_seconds, self._timer_fire, args=(request_id,)
            )
            entry.timer.daemon = True
            entry.timer.start()
            self._entries[request_id] = entry

    def reserve(
        self, request_id: str, resolution: Resolution
    ) -> ReservationToken | None:
        """Atomic CAS: awaiting → reserved. Returns a token on success,
        None if the entry is not in awaiting.
        """
        with self._lock:
            entry = self._entries.get(request_id)
            if entry is None or entry.state != "awaiting":
                return None
            entry.state = "reserved"
            entry.pending = resolution
            return ReservationToken(
                request_id=request_id, generation=entry.generation
            )

    def commit_signal(self, token: ReservationToken) -> None:
        """reserved → consuming + fire the per-entry event. Irreversible.
        Stale token (entry re-registered) becomes a no-op.
        """
        with self._lock:
            entry = self._entries.get(token.request_id)
            if entry is None or entry.generation != token.generation:
                logger.warning(
                    "ResolutionRegistry.commit_signal: stale token for %r",
                    token.request_id,
                )
                return
            if entry.state != "reserved":
                raise RuntimeError(
                    f"ResolutionRegistry.commit_signal failed: entry not in "
                    f"reserved state. Got: state={entry.state!r}"
                )
            entry.state = "consuming"
            # Cancel the timer (decide won the race).
            if entry.timer is not None:
                entry.timer.cancel()
                entry.timer = None
            event = entry.event
        event.set()

    def abort_reservation(self, token: ReservationToken) -> None:
        """reserved → awaiting (idempotent on double-abort or stale token)."""
        with self._lock:
            entry = self._entries.get(token.request_id)
            if entry is None or entry.generation != token.generation:
                return
            if entry.state == "reserved":
                entry.state = "awaiting"
                entry.pending = None
            # Idempotent for any other state.

    def wait(self, request_id: str) -> Resolution:
        """Worker blocks here post-register; returns when commit_signal or
        signal_internal_abort fires the entry's event.

        Caller must invoke discard(request_id) after consuming the returned
        resolution; otherwise the entry persists in the registry indefinitely.
        """
        with self._lock:
            entry = self._entries.get(request_id)
            if entry is None:
                raise RuntimeError(
                    f"ResolutionRegistry.wait: unregistered request_id. "
                    f"Got: {request_id!r:.100}"
                )
            event = entry.event
        event.wait()
        with self._lock:
            entry = self._entries.get(request_id)
            assert entry is not None, "registry invariant: entry missing after event fire"
            assert entry.pending is not None, "registry invariant: event fired with no pending resolution"
            return entry.pending

    def discard(self, request_id: str) -> None:
        """Idempotent removal. Called by the worker after finalizing."""
        with self._lock:
            entry = self._entries.pop(request_id, None)
            if entry is not None and entry.timer is not None:
                entry.timer.cancel()

    def signal_internal_abort(self, request_id: str, *, reason: str) -> bool:
        """Atomic awaiting → aborted (wakes worker with InternalAbort).
        Returns True iff the transition took effect. Idempotent/no-op for
        entries not in awaiting.
        """
        with self._lock:
            entry = self._entries.get(request_id)
            if entry is None or entry.state != "awaiting":
                return False
            entry.state = "aborted"
            entry.pending = InternalAbort(reason=reason)
            if entry.timer is not None:
                entry.timer.cancel()
                entry.timer = None
            event = entry.event
        event.set()
        return True

    # --- per-job capture-ready API ------------------------------------------

    def announce_parked(self, job_id: str, *, request_id: str) -> None:
        self._deliver_capture_outcome(job_id, Parked(request_id=request_id))

    def announce_turn_completed_empty(self, job_id: str) -> None:
        self._deliver_capture_outcome(job_id, TurnCompletedWithoutCapture())

    def announce_turn_terminal_without_escalation(
        self,
        job_id: str,
        *,
        status: Literal["unknown"],
        reason: str,
        request_id: str | None,
    ) -> None:
        self._deliver_capture_outcome(
            job_id,
            TurnTerminalWithoutEscalation(
                job_status=status, reason=reason, request_id=request_id
            ),
        )

    def announce_worker_failed(self, job_id: str, *, error: Exception) -> None:
        self._deliver_capture_outcome(job_id, WorkerFailed(error=error))

    def _deliver_capture_outcome(
        self, job_id: str, outcome: ParkedCaptureResult
    ) -> None:
        with self._lock:
            channel = self._capture_channels.get(job_id)
            if channel is None or channel.resolved:
                logger.warning(
                    "late capture-ready signal ignored. job_id=%r kind=%s",
                    job_id,
                    type(outcome).__name__,
                )
                return
            channel.outcome = outcome
            channel.resolved = True
            event = channel.event
        event.set()

    def wait_for_parked(
        self, job_id: str, *, timeout_seconds: float
    ) -> ParkedCaptureResult:
        """Main thread blocks here during start().

        O1=(b) lifecycle: this method removes the channel from
        `_capture_channels` under the registry lock before returning,
        regardless of outcome variant. Late announce_* calls after this
        return observe `channel is None` in `_deliver_capture_outcome`
        and warn-and-noop without raising.
        """
        with self._lock:
            if job_id in self._capture_channels:
                raise RuntimeError(
                    f"ResolutionRegistry.wait_for_parked failed: duplicate "
                    f"job_id. Got: {job_id!r:.100}"
                )
            channel = _CaptureReadyChannel(job_id=job_id)
            self._capture_channels[job_id] = channel
        signaled = channel.event.wait(timeout=timeout_seconds)
        with self._lock:
            channel_now = self._capture_channels.get(job_id)
            if channel_now is None:
                # Defensive: unreachable under current code — nothing pops
                # _capture_channels between this method's two lock acquisitions.
                # Kept as future-proofing in case an admin path introduces
                # external channel discard (e.g., a discard_capture_channel
                # helper) that could race with wait_for_parked. Returning
                # StartWaitElapsed() preserves synchronous start-wait semantics
                # if such a race ever materializes.
                return StartWaitElapsed()
            if not signaled or channel_now.outcome is None:
                channel_now.outcome = StartWaitElapsed()
                channel_now.resolved = True
            outcome = channel_now.outcome
            # O1=(b) pop-on-return: remove the channel under the lock so
            # late announce_* calls observe channel-is-None and no-op.
            self._capture_channels.pop(job_id, None)
        return outcome

    # --- timer callback ------------------------------------------------------

    def _timer_fire(self, request_id: str) -> None:
        """Fired after timeout_seconds. Reuses the reserve/commit_signal CAS
        primitive — stale timer (entry already decided/aborted/discarded) is a
        no-op via reserve() returning None. No store, journal, or audit writes
        here per spec §Timer ownership note.
        """
        with self._lock:
            entry = self._entries.get(request_id)
            if entry is None:
                return
            kind = entry.kind
        timeout_resolution = DecisionResolution(payload={}, kind=kind, is_timeout=True)
        token = self.reserve(request_id, timeout_resolution)
        if token is None:
            return
        self.commit_signal(token)

    # --- testing helpers -----------------------------------------------------

    def _is_awaiting(self, request_id: str) -> bool:
        """Test-only introspection. Do not use from production code."""
        with self._lock:
            entry = self._entries.get(request_id)
            return entry is not None and entry.state == "awaiting"

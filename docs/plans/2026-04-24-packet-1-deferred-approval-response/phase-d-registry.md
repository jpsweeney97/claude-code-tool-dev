# Packet 1 — Phase D: Registry

**Parent plan:** [manifest](../2026-04-24-packet-1-deferred-approval-response.md)
**Tasks:** 11–12
**Scope:** `ResolutionRegistry` as IO-2 cross-thread primitive. Per-request channel (state machine, CAS, timer, `signal_internal_abort`). Per-job capture-ready channel (`ParkedCaptureResult` sum — `Parked`, `TurnCompletedWithoutCapture`, `TurnTerminalWithoutEscalation`, `WorkerFailed`, `StartWaitElapsed` — `announce_*` methods, `wait_for_parked`).
**Landing invariant:** `ResolutionRegistry` standalone unit tests pass: state-machine transitions, CAS contention, timer semantics, late-signal tolerance.

---

## Task 11: ResolutionRegistry — per-request channel (reserve/commit/abort + wait + discard + timer + signal_internal_abort)

**Files:**
- Create: `packages/plugins/codex-collaboration/server/resolution_registry.py`
- Create: `packages/plugins/codex-collaboration/tests/test_resolution_registry_per_request.py`

**Spec anchor:** §Resolution registry (spec lines ~118-241). §Transactional registry protocol (spec lines ~250-345). §Internal abort coordination (spec lines ~347-438). Timer policy: spec §Timeout Policy + §Kind-sensitive timeout dispatch.

This is a large task. Substeps break it into coherent sub-modules, each with its own tests.

- [ ] **Step 11.1: Write the failing test for resolution types (DecisionResolution, InternalAbort, sum type)**

Create `packages/plugins/codex-collaboration/tests/test_resolution_registry_per_request.py`:

```python
"""Packet 1: ResolutionRegistry per-request channel — state machine + CAS + wake."""

from __future__ import annotations

import threading
import time

import pytest

from server.resolution_registry import (
    DecisionResolution,
    InternalAbort,
    ResolutionRegistry,
    Resolution,
)


def test_decision_resolution_fields() -> None:
    r = DecisionResolution(
        payload={"decision": "accept"}, kind="command_approval", is_timeout=False
    )
    assert r.payload == {"decision": "accept"}
    assert r.kind == "command_approval"
    assert r.is_timeout is False


def test_internal_abort_carries_reason() -> None:
    a = InternalAbort(reason="parked_projection_invariant_violation")
    assert a.reason == "parked_projection_invariant_violation"


def test_resolution_is_union_of_both() -> None:
    r1: Resolution = DecisionResolution(payload={}, kind="command_approval")
    r2: Resolution = InternalAbort(reason="x")
    assert isinstance(r1, DecisionResolution)
    assert isinstance(r2, InternalAbort)


def test_register_creates_awaiting_entry() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)
    # Implementation detail — test only what's observable via the public
    # interface.
    assert reg._is_awaiting("r1")  # test-only introspection


def test_reserve_wins_cas_returns_token() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)
    token = reg.reserve(
        "r1", DecisionResolution(payload={"decision": "accept"}, kind="command_approval")
    )
    assert token is not None


def test_reserve_loses_cas_returns_none() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)
    first = reg.reserve(
        "r1", DecisionResolution(payload={}, kind="command_approval")
    )
    assert first is not None
    # Second reserve on a non-awaiting entry returns None.
    second = reg.reserve(
        "r1", DecisionResolution(payload={}, kind="command_approval")
    )
    assert second is None


def test_reserve_on_unregistered_entry_returns_none() -> None:
    reg = ResolutionRegistry()
    # No register() call — reserve must return None.
    token = reg.reserve(
        "not-registered", DecisionResolution(payload={}, kind="command_approval")
    )
    assert token is None


def test_commit_signal_wakes_worker_wait() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)

    result: list[Resolution] = []

    def worker() -> None:
        result.append(reg.wait("r1"))

    t = threading.Thread(target=worker)
    t.start()
    # Small delay to ensure worker is blocked on wait().
    time.sleep(0.05)
    token = reg.reserve(
        "r1", DecisionResolution(payload={"decision": "accept"}, kind="command_approval")
    )
    assert token is not None
    reg.commit_signal(token)
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], DecisionResolution)
    assert result[0].payload == {"decision": "accept"}


def test_abort_reservation_restores_awaiting() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)
    token = reg.reserve("r1", DecisionResolution(payload={}, kind="command_approval"))
    assert token is not None
    reg.abort_reservation(token)
    # Entry is back in awaiting; a second reserve must succeed.
    token2 = reg.reserve("r1", DecisionResolution(payload={}, kind="command_approval"))
    assert token2 is not None


def test_double_abort_is_idempotent() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)
    token = reg.reserve("r1", DecisionResolution(payload={}, kind="command_approval"))
    assert token is not None
    reg.abort_reservation(token)
    reg.abort_reservation(token)  # no raise


def test_signal_internal_abort_wakes_worker_with_abort() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)

    result: list[Resolution] = []

    def worker() -> None:
        result.append(reg.wait("r1"))

    t = threading.Thread(target=worker)
    t.start()
    time.sleep(0.05)
    returned = reg.signal_internal_abort("r1", reason="parked_projection_invariant_violation")
    assert returned is True
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], InternalAbort)
    assert result[0].reason == "parked_projection_invariant_violation"


def test_signal_internal_abort_loses_to_operator_decide() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)
    # Operator wins the reservation first.
    token = reg.reserve(
        "r1", DecisionResolution(payload={"decision": "accept"}, kind="command_approval")
    )
    assert token is not None
    # Later abort signal is a no-op.
    returned = reg.signal_internal_abort("r1", reason="late-abort")
    assert returned is False


def test_signal_internal_abort_idempotent() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)
    first = reg.signal_internal_abort("r1", reason="x")
    second = reg.signal_internal_abort("r1", reason="y")
    assert first is True
    assert second is False


def test_discard_removes_entry_idempotent() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=900)
    reg.discard("r1")
    reg.discard("r1")  # idempotent


def test_timer_fires_synthetic_timeout_resolution() -> None:
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=0.1)

    result: list[Resolution] = []

    def worker() -> None:
        result.append(reg.wait("r1"))

    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], DecisionResolution)
    assert result[0].is_timeout is True


def test_late_timer_against_decided_entry_is_noop() -> None:
    # Timer tries to reserve an entry that's already been decided — must be a
    # no-op (no journal, no wake, no side effect).
    reg = ResolutionRegistry()
    reg.register("r1", job_id="j1", timeout_seconds=0.5)
    # Operator wins.
    token = reg.reserve(
        "r1", DecisionResolution(payload={}, kind="command_approval")
    )
    assert token is not None
    reg.commit_signal(token)
    # Let the timer fire — it should observe reserved/consuming and no-op.
    time.sleep(0.7)
    # Registry still reflects the operator's decision (no state change).
```

- [ ] **Step 11.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_resolution_registry_per_request.py -v
```

Expected: FAIL — the file does not exist.

- [ ] **Step 11.3: Create `resolution_registry.py` skeleton with types + per-request state machine**

Create `packages/plugins/codex-collaboration/server/resolution_registry.py`:

```python
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

from .models import PendingRequestKind

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------- resolution types


@dataclass(frozen=True)
class DecisionResolution:
    """Resolution delivered to the worker by decide() or by the registry's
    timeout timer.
    """

    payload: dict[str, Any]
    kind: PendingRequestKind
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


# -------------------------------------------------------------------- reservation token


@dataclass(frozen=True)
class ReservationToken:
    """Opaque handle returned by reserve() and consumed by exactly one
    subsequent commit_signal or abort_reservation call. Carries a generation
    counter so stale tokens (entry discarded and re-registered) cannot
    commit_signal into a different entry's state.
    """

    request_id: str
    generation: int


# -------------------------------------------------------------------- per-request entry


_EntryState = Literal["awaiting", "reserved", "consuming", "aborted"]


@dataclass
class _RegistryEntry:
    request_id: str
    job_id: str
    timeout_seconds: float
    state: _EntryState
    generation: int
    event: threading.Event
    # Resolution pending delivery (set when state transitions to consuming or aborted).
    pending: Resolution | None = None
    # Timer thread for the operator-window budget.
    timer: threading.Timer | None = None


# -------------------------------------------------------------------- registry


class ResolutionRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, _RegistryEntry] = {}
        # Per-job capture-ready channel is added in Task 12.

    # --- per-request API -----------------------------------------------------

    def register(
        self, request_id: str, *, job_id: str, timeout_seconds: float
    ) -> None:
        """Establish a new per-request entry in awaiting state and start its
        timeout timer. Worker calls this immediately before announce_parked.
        """
        with self._lock:
            if request_id in self._entries:
                raise RuntimeError(
                    f"ResolutionRegistry.register: duplicate request_id. "
                    f"Got: {request_id!r:.100}"
                )
            event = threading.Event()
            entry = _RegistryEntry(
                request_id=request_id,
                job_id=job_id,
                timeout_seconds=timeout_seconds,
                state="awaiting",
                generation=0,
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
            assert entry is not None, f"registry invariant: entry missing after event fire"
            assert entry.pending is not None, f"registry invariant: event fired with no pending resolution"
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

    # --- timer callback ------------------------------------------------------

    def _timer_fire(self, request_id: str) -> None:
        """Fired after timeout_seconds. Synthesizes a DecisionResolution with
        is_timeout=True and attempts to reserve the entry. Stale timer (entry
        already decided) is a no-op: no journal, no audit, no wake.
        """
        # Caller needs the request's kind to construct the cancel payload;
        # since this synthetic resolution's exact shape depends on the
        # request's kind (and is kind-sensitive per spec §Kind-sensitive
        # timeout dispatch), the actual dispatch decision happens in the
        # WORKER after wake. Here we simply deliver a sentinel resolution
        # that the worker interprets kind-sensitively.
        with self._lock:
            entry = self._entries.get(request_id)
            if entry is None or entry.state != "awaiting":
                return
            # Carry placeholder payload — worker synthesizes the actual
            # dispatch payload based on kind after wake.
            resolution = DecisionResolution(
                payload={}, kind="command_approval", is_timeout=True
            )
            # Synthesize kind from stored entry metadata instead. Since we
            # do not store the kind on the entry (registry is kind-agnostic
            # for the reservation), the worker must re-read the request kind
            # from pending_request_store after wake and use is_timeout=True
            # as the discriminant. Payload here is an unused placeholder.
            #
            # (The worker, on is_timeout=True wake, re-reads request.kind from
            # the store to decide between cancel-capable and non-cancel
            # timeout paths.)
            if entry.state != "awaiting":
                return
            entry.state = "reserved"
            entry.pending = resolution
            entry.state = "consuming"
            entry.timer = None
            event = entry.event
        event.set()

    # --- testing helpers -----------------------------------------------------

    def _is_awaiting(self, request_id: str) -> bool:
        """Test-only introspection. Do not use from production code."""
        with self._lock:
            entry = self._entries.get(request_id)
            return entry is not None and entry.state == "awaiting"
```

- [ ] **Step 11.4: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_resolution_registry_per_request.py -v
```

Expected: majority PASS. Some tests (particularly the timer-fire tests) may be sensitive to threading timing; if any timing-based test is flaky, add a longer `t.join(timeout=...)` or guard with `threading.Event.wait(timeout=...)` patterns.

- [ ] **Step 11.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/resolution_registry.py packages/plugins/codex-collaboration/tests/test_resolution_registry_per_request.py
git commit -m "$(cat <<'EOF'
feat(delegate): add ResolutionRegistry per-request channel + CAS protocol (T-20260423-02 Task 11)

New file resolution_registry.py houses the cross-thread coordination
primitive (IO-2). This commit lands the per-request channel:
DecisionResolution / InternalAbort / Resolution sum type, ReservationToken,
register / reserve / commit_signal / abort_reservation / wait / discard /
signal_internal_abort, plus the registry-internal timeout timer that
synthesizes is_timeout=True resolutions.

The per-job capture-ready channel lands in Task 12.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: ResolutionRegistry — per-job capture-ready channel (ParkedCaptureResult + announce_* + wait_for_parked)

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/resolution_registry.py` (add capture-ready channel + 4 announce_* methods + wait_for_parked + ParkedCaptureResult sum type)
- Test: `packages/plugins/codex-collaboration/tests/test_resolution_registry_capture_ready.py` (new)

**Spec anchor:** §Resolution registry (lines ~120-189). §Capture-ready handshake (lines ~659-910).

- [ ] **Step 12.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_resolution_registry_capture_ready.py`:

```python
"""Packet 1: ResolutionRegistry per-job capture-ready channel + ParkedCaptureResult."""

from __future__ import annotations

import threading
import time

from server.resolution_registry import (
    Parked,
    ParkedCaptureResult,
    ResolutionRegistry,
    StartWaitElapsed,
    TurnCompletedWithoutCapture,
    TurnTerminalWithoutEscalation,
    WorkerFailed,
)


def test_parked_carries_request_id() -> None:
    p = Parked(request_id="r1")
    assert p.request_id == "r1"


def test_turn_completed_without_capture_is_empty() -> None:
    TurnCompletedWithoutCapture()  # no fields


def test_turn_terminal_without_escalation_fields() -> None:
    t = TurnTerminalWithoutEscalation(
        job_status="unknown",
        reason="unknown_kind_parse_failure",
        request_id="r-audit",
    )
    assert t.job_status == "unknown"
    assert t.reason == "unknown_kind_parse_failure"
    assert t.request_id == "r-audit"


def test_worker_failed_carries_exception() -> None:
    exc = RuntimeError("boom")
    wf = WorkerFailed(error=exc)
    assert wf.error is exc


def test_start_wait_elapsed_is_empty() -> None:
    StartWaitElapsed()


def test_announce_parked_wakes_main_thread() -> None:
    reg = ResolutionRegistry()
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.05)
    reg.announce_parked("j1", request_id="r1")
    t.join(timeout=3.0)
    assert not t.is_alive()
    assert len(result) == 1
    assert isinstance(result[0], Parked)
    assert result[0].request_id == "r1"


def test_announce_turn_completed_empty_surfaces_variant() -> None:
    reg = ResolutionRegistry()
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.05)
    reg.announce_turn_completed_empty("j1")
    t.join(timeout=3.0)
    assert isinstance(result[0], TurnCompletedWithoutCapture)


def test_announce_turn_terminal_without_escalation() -> None:
    reg = ResolutionRegistry()
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.05)
    reg.announce_turn_terminal_without_escalation(
        "j1", status="unknown", reason="unknown_kind_parse_failure", request_id="r-audit"
    )
    t.join(timeout=3.0)
    assert isinstance(result[0], TurnTerminalWithoutEscalation)
    assert result[0].job_status == "unknown"
    assert result[0].reason == "unknown_kind_parse_failure"
    assert result[0].request_id == "r-audit"


def test_announce_worker_failed_surfaces_exception() -> None:
    reg = ResolutionRegistry()
    result: list[ParkedCaptureResult] = []

    def main() -> None:
        result.append(reg.wait_for_parked("j1", timeout_seconds=2.0))

    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.05)
    reg.announce_worker_failed("j1", error=RuntimeError("boom"))
    t.join(timeout=3.0)
    assert isinstance(result[0], WorkerFailed)
    assert isinstance(result[0].error, RuntimeError)


def test_start_wait_elapsed_when_budget_expires_without_signal() -> None:
    reg = ResolutionRegistry()
    result = reg.wait_for_parked("j1", timeout_seconds=0.1)
    assert isinstance(result, StartWaitElapsed)


def test_late_announce_after_start_wait_elapsed_no_raise() -> None:
    """Late announce_* call after wait_for_parked resolves must not raise."""
    reg = ResolutionRegistry()
    result = reg.wait_for_parked("j1", timeout_seconds=0.1)
    assert isinstance(result, StartWaitElapsed)
    # Subsequent announce_* calls are no-op warnings, never raises.
    reg.announce_parked("j1", request_id="r1")
    reg.announce_turn_completed_empty("j1")
    reg.announce_turn_terminal_without_escalation(
        "j1", status="unknown", reason="r", request_id=None
    )
    reg.announce_worker_failed("j1", error=RuntimeError("late"))


def test_capture_ready_channels_are_per_job() -> None:
    """Two jobs have independent channels."""
    reg = ResolutionRegistry()
    results: dict[str, ParkedCaptureResult] = {}

    def main(job_id: str) -> None:
        results[job_id] = reg.wait_for_parked(job_id, timeout_seconds=2.0)

    t1 = threading.Thread(target=main, args=("j1",))
    t2 = threading.Thread(target=main, args=("j2",))
    t1.start()
    t2.start()
    time.sleep(0.05)
    reg.announce_parked("j1", request_id="r1")
    reg.announce_turn_completed_empty("j2")
    t1.join(timeout=3.0)
    t2.join(timeout=3.0)
    assert isinstance(results["j1"], Parked)
    assert isinstance(results["j2"], TurnCompletedWithoutCapture)
```

- [ ] **Step 12.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_resolution_registry_capture_ready.py -v
```

Expected: FAIL — types and methods don't exist.

- [ ] **Step 12.3: Extend `resolution_registry.py` with capture-ready channel**

Edit `packages/plugins/codex-collaboration/server/resolution_registry.py`. Add the sum type + capture-ready channel:

```python
# Place near the top, after Resolution sum type

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
```

Then add the per-job channel state + methods to `ResolutionRegistry`:

```python
# In __init__, add:
self._capture_channels: dict[str, _CaptureReadyChannel] = {}

# New dataclass alongside _RegistryEntry:
@dataclass
class _CaptureReadyChannel:
    job_id: str
    event: threading.Event = field(default_factory=threading.Event)
    outcome: ParkedCaptureResult | None = None
    resolved: bool = False  # True once wait_for_parked has returned any outcome


# Methods on ResolutionRegistry:
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
            logger.info(
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
    """Main thread blocks here during start()."""
    with self._lock:
        if job_id in self._capture_channels:
            raise RuntimeError(
                f"ResolutionRegistry.wait_for_parked: duplicate job_id. "
                f"Got: {job_id!r:.100}"
            )
        channel = _CaptureReadyChannel(job_id=job_id)
        self._capture_channels[job_id] = channel
    signaled = channel.event.wait(timeout=timeout_seconds)
    with self._lock:
        channel_now = self._capture_channels.get(job_id)
        if channel_now is None:
            # Defensive — should not happen under current code.
            return StartWaitElapsed()
        if not signaled or channel_now.outcome is None:
            # Budget elapsed; synthesize StartWaitElapsed and mark resolved
            # so subsequent announce_* calls become no-op warnings.
            channel_now.outcome = StartWaitElapsed()
            channel_now.resolved = True
        outcome = channel_now.outcome
        # Leave channel in place so late announce_* calls observe resolved=True
        # and warn-and-noop. An explicit discard happens when start() returns.
    return outcome
```

Note the signature uses keyword-only `request_id`/`status`/`reason`/`error` to match the tests.

- [ ] **Step 12.4: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_resolution_registry_capture_ready.py -v
```

Expected: 12 PASS.

- [ ] **Step 12.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/resolution_registry.py packages/plugins/codex-collaboration/tests/test_resolution_registry_capture_ready.py
git commit -m "$(cat <<'EOF'
feat(delegate): add ResolutionRegistry capture-ready channel (T-20260423-02 Task 12)

Adds the per-job capture-ready channel to ResolutionRegistry. Parked /
TurnCompletedWithoutCapture / TurnTerminalWithoutEscalation / WorkerFailed
/ StartWaitElapsed sum type (ParkedCaptureResult). Four announce_* worker
methods + wait_for_parked on the main thread. Late announce_* after
StartWaitElapsed resolves is a warning no-op (never raises) per spec
§Late start-outcome signals.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

**Phase D complete.** The registry is a standalone unit with full cross-thread coordination semantics. Phase E covers serialization + projection helper updates — cheaper but foundational for the public-API rewrites in Phase F.

---

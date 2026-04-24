# Deferred Same-Turn Approval Response

## Overview

Redesigns the delegation runtime's control plane so that a Codex App Server turn can stay live across operator delay and receive an approval response in the same turn. Replaces the current synchronous capture-and-cancel flow with a worker-thread execution model coordinated through a resolution registry.

**Ticket:** T-20260423-02 (`docs/tickets/2026-04-23-deferred-same-turn-approval-response.md`).

**Blocks:** T-20260423-01 (parent acceptance-gap ticket; AC1 — end-to-end delegation with platform-tool verification).

**Branch:** `feature/delegate-deferred-approval-response`.

**Replaces (as rejected input):** `feature/delegate-exec-policy-amendment` at commit `edff9c07`. Decisions D7, D8, D10 from that spec are superseded by this document. D1–D6, D9, D11, D12 survive and apply to the amendment-admission follow-up ticket (Packet 2), not here.

## Scope and Non-Goals

### In scope

1. `codex.delegate.start` call-path redesign — return semantics while the original turn stays live.
2. Background turn execution model — worker thread per deferred-approval turn.
3. Capture cardinality — single-parked-at-a-time with proof-by-construction from the serial handler loop.
4. Resolution registry — blocking-wait-and-signal mechanism between main thread and worker.
5. Persisted request / job state — new fields, mutators, cold-start reconciliation.
6. Public contract updates — `DelegationDecisionResult` shape, `contracts.md`, model enums.
7. Timeout policy — operator window as local abandonment budget.
8. Recovery semantics — orphan demotion + journal provenance annotation.

### Non-goals

- **Amendment admission** (allowlist, classifier, `approve_amendment` verb, amendment-specific audit). Lives in the follow-up ticket on top of this packet's primitives.
- **Eligibility logic** — what requests can be amended vs. only approved/denied. Same follow-up.
- **Generic deferred-decision framework** — amendments are the only consumer for v1. Reusability for other decision kinds is incidental, not a design driver.
- **Implementation.** This ticket closes on spec approval. Plan + code land under a separate phase.

## Named Invariants

Five invariants govern the design. Any implementation change must verify against all five.

**IO-1 (Session ownership):** The worker thread exclusively owns its `AppServerRuntimeSession` and `JsonRpcClient` for the lifetime of its turn. All JSON-RPC reads (`_next_id`, `request()`, `next_notification()`) and writes (`respond()`) happen on that thread. No other thread touches the session. Rationale: `JsonRpcClient` at `packages/plugins/codex-collaboration/server/jsonrpc_client.py` has no shared-client locking (`_next_id` is a bare int increment at line 40, `_notification_backlog` is an unlocked `deque`).

**IO-2 (Cross-thread API = resolution registry only):** The resolution registry is the only cross-thread API between main (MCP dispatch) and worker. `decide()` publishes to the registry; the worker blocks on it. No other shared mutable state crosses threads — not the session, not the stores, not the job state.

**IO-3 (Single-writer-per-store):** Each store has one writer thread at a time per the thread-role table (see §Runtime Architecture). Eliminates store-level locks; relies on OS append atomicity (IO-4) for correctness. The "at a time" clause is load-bearing and depends on the **singleton busy gate** at `packages/plugins/codex-collaboration/server/delegation_controller.py:328-349` — the max-1 user-attention job per session check that consults the job store, the runtime registry, and unresolved `job_creation` journal entries. Because at most one delegation job is in flight per session, at most one worker thread exists at any instant. Any future relaxation of the singleton constraint (parallel jobs, multi-session sharding) must revisit IO-3 either by adding store-level locking or by proving that multi-worker → single-writer-per-store still holds under the new partitioning.

**IO-4 (Inherited JSONL append — DURABLE journal writes):** The operation journal and stores that gate recovery correctness — `journal.write_phase` at `packages/plugins/codex-collaboration/server/journal.py:300-307`, `pending_request_store._append` at `:71-75`, `delegation_job_store._append` — use `open("a")` + single-line JSON write + **`flush()` + `os.fsync()`**. The fsync is load-bearing: these writes survive process crash. The repo already depends on this pattern being correct under its single-writer discipline on supported platforms (Linux/macOS). This spec extends the operation journal to two writers (main writes `approval_resolution.intent` via `decide()`; worker writes `approval_resolution.dispatched/completed`); we inherit the platform assumption, we do not prove it. If a future change adds multi-process concurrent writers or Windows support, upgrade to an explicit lock or hardened append primitive.

**IO-5 (Audit events are best-effort, NOT durable):** `journal.append_audit_event` at `packages/plugins/codex-collaboration/server/journal.py:241-245` is `open("a")` + single-line JSON write — **no `flush()`, no `os.fsync()`**. Audit events may be lost on process crash between the `write()` call and the OS eventually flushing the page cache. The same applies to `append_outcome` (`:261-265`) and `append_delegation_outcome` (`:281-285`). Concrete consequence for this design: audit-event appends MUST NOT sit inside any critical section that gates worker wake or durable state transitions. An audit failure is survivable (log + continue); an operation-journal failure is not. This is why the transactional registry protocol (see §Transactional registry protocol) places `append_audit_event` AFTER `commit_signal`, not before.

**OB-1 (Observation honesty):** Every durable field and audit event reflects only what the plugin locally observed. Transport-level observations use transport verbs (dispatched, succeeded, failed). Turn-level observations use turn verbs (completed, interrupted). The plugin does not claim semantic application of an operator decision by App Server, because it has no channel to verify that claim.

## Runtime Architecture and Thread Ownership

### Current (synchronous) architecture — what breaks

```
MCP caller ──► start() ──► _execute_live_turn() ─────────────── [blocks]
                               │
                               ├─ run_execution_turn(handler)
                               │     └─ handler captures request → interrupt_turn()
                               │
                               ├─ turn ends
                               ├─ _finalize_turn() → build DelegationEscalation
                               └─ return escalation
```

The escalation cannot surface until the turn is already interrupted. `decide()` has nothing live to respond to — the request handler has returned and is unreachable.

Evidence:
- `start()` synchronous return at `packages/plugins/codex-collaboration/server/delegation_controller.py:618-624`.
- `DelegationEscalation` constructed only post-turn inside `_finalize_turn` at `delegation_controller.py:1504-1510`.

### New (worker-thread) architecture

```
Main thread (MCP)          Resolution registry          Worker thread
────────────────           ───────────────────          ─────────────
start(...)
  spawn worker ──────────────────────────────────────► _execute_live_turn
  wait_for_parked(job_id) ◄──── capture-ready ──────    handler captures
                                                         persist request + job state
                                                         register(rid)
                                                         announce_parked(job_id, rid)
  return escalation                                      block on rid ◄──── await
decide(rid)
  token = reserve(rid, res) [CAS awaiting → reserved]
  journal: intent (fsynced)                              (still blocked)
  commit_signal(token) ─────────────► wake
  return decision_accepted                               update_status → running
  audit: approve|deny (post-commit;                      journal: dispatched
         best-effort, IO-5)                              respond()
                                                         record stores
                                                         journal: completed
                                                         discard(rid)
                                                         loop → next notification
                                                         ...
                                                         turn/completed
                                                         protocol_echo persisted
                                                         _finalize_turn
```

### Thread roles and ownership

| Thread | Spawned by | Lifetime | Session | Store writes | Store reads |
|---|---|---|---|---|---|
| Main (MCP dispatch) | Plugin process | Plugin process | Read-only (via controller helpers) | `delegation_job_store.create` (via start only); `journal.write_phase(intent)`; `journal.append_audit_event` | Any (read-only for poll, decide validation) |
| Worker (per-turn) | `start()` spawn | One turn (from `_execute_live_turn` entry to terminal or exception) | Exclusive owner (IO-1) | `pending_request_store` (create + mutators); `delegation_job_store.update_parked_request` + terminal status via `_persist_job_transition`; `journal.write_phase(dispatched, completed)` | Own session state only |
| JSON-RPC background readers (existing) | `JsonRpcClient.start` | Per session | Queue producer only (`_message_queue` at `jsonrpc_client.py:35`) | None | None |
| Cold-start recovery (existing) | Plugin init | Plugin init | None | Demotion transitions via `_persist_job_transition` | All stores |

The two "new" threading constructs are the **worker thread** (one per in-flight deferred-approval turn) and the **resolution registry** (in-memory, lock-guarded, lifetime bounded by one turn).

### Resolution registry

In-memory structure. The registry owns two independent coordination channels:

- **Per-request channel** — a `RegistryEntry` keyed by `request_id`. States `awaiting | consuming`. Used by the worker to block on a pending resolution and by `decide()` to deliver one.
- **Per-job capture-ready channel** — a `CaptureReadyEvent` keyed by `job_id`. Signaled by the worker once it has captured a server request and parked; awaited by `start()` on the main thread to obtain the escalation payload synchronously.

```python
class ResolutionRegistry:
    # Per-request resolution channel
    # request_id → RegistryEntry
    # Entry states: "awaiting" (worker parked) | "reserved" (reservation taken, pre-commit)
    #               | "consuming" (reservation committed; wake signal sent)
    # threading.Lock guards entry state transitions
    # threading.Event per entry for worker's block-and-wake

    def register(self, request_id: str, job_id: str, timeout_seconds: int) -> None: ...

    # Two-phase reservation protocol. See §Transactional registry protocol.
    def reserve(
        self, request_id: str, resolution: Resolution,
    ) -> ReservationToken | None: ...                # awaiting → reserved (atomic CAS)
                                                     # Returns None if entry is not in "awaiting" state
                                                     # (already reserved, consumed, or discarded)
    def commit_signal(self, token: ReservationToken) -> None: ...
                                                     # reserved → consuming + threading.Event.set()
                                                     # Irreversible. Caller must have durably written
                                                     # approval_resolution.intent before calling.
    def abort_reservation(self, token: ReservationToken) -> None: ...
                                                     # reserved → awaiting (idempotent on double-abort)
                                                     # Safe only before the matching intent is durable.

    def wait(self, request_id: str) -> Resolution: ...            # worker blocks here post-register
    def discard(self, request_id: str) -> None: ...               # called after worker finalizes

    # Timeout timer is registry-internal; it does ONLY in-memory state + signal,
    # NEVER writes to the operation journal. Sequence:
    #   self.reserve(rid, timeout_resolution) → token
    #   self.commit_signal(token)             # wakes worker with synthetic timeout resolution
    # The worker owns all timeout journal writes (intent/dispatched/completed) on its own thread.

    # Per-job capture-ready channel
    # job_id → CaptureReadyEvent (one-shot; created on start(), discarded after wait_for_parked resolves)
    def announce_parked(self, job_id: str, request_id: str) -> None: ...     # worker signals capture-ready
    def announce_turn_completed_empty(self, job_id: str) -> None: ...        # worker signals turn ended without capture
    def announce_worker_failed(self, job_id: str, error: Exception) -> None: ...  # worker signals exception
    def wait_for_parked(
        self, job_id: str, timeout_seconds: float,
    ) -> ParkedCaptureResult: ...                                            # main blocks here in start()
```

`ReservationToken` is an opaque handle returned by `reserve()` and consumed by exactly one subsequent `commit_signal` or `abort_reservation` call. It carries enough internal state (request_id, entry generation counter) to reject stale tokens — e.g., if the entry was discarded and re-registered between reserve and commit, the stale token's commit_signal becomes a no-op or raises. See §Transactional registry protocol for the full lifecycle.

`ParkedCaptureResult` is a sum type:

```python
@dataclass(frozen=True)
class Parked:
    request_id: str

@dataclass(frozen=True)
class TurnCompletedWithoutCapture:
    pass  # Codex finished its objective without requesting approval

@dataclass(frozen=True)
class WorkerFailed:
    error: Exception

@dataclass(frozen=True)
class CaptureTimeout:
    pass  # main-thread safety net; worker never signaled within CAPTURE_READY_TIMEOUT_SECONDS

ParkedCaptureResult = Parked | TurnCompletedWithoutCapture | WorkerFailed | CaptureTimeout
```

The registry is the sole cross-thread mutable state (IO-2). It uses a `threading.Lock` for the per-request CAS and `threading.Event`s for both the per-request wake and the per-job capture-ready signal. Entries are discarded entry-by-entry as each turn's resolution concludes; the registry itself lives for the plugin process.

**Ordering guarantees — path-specific.** Journal file-order monotonicity for the `approval_resolution` idempotency key (`intent → dispatched → completed`) is load-bearing because `journal._terminal_phases` at `journal.py:345-349` builds its terminal-phase dict from `replay_jsonl` in file order; a late-arriving `intent` after `completed` would make a resolved operation look unresolved under recovery. The mechanism that preserves this invariant is path-specific:

- **Operator decision path (decide):** main thread writes `approval_resolution.intent` **before** calling `commit_signal`. The worker, which writes `dispatched` and `completed`, cannot wake before `commit_signal` fires. Cross-thread ordering is enforced by the transactional protocol (below).
- **Timeout path:** the timer signals the worker immediately after in-memory reservation; no journal write fires on the timer's thread. The worker, on wake, writes `approval_resolution.intent` (with `decision=None`) **first**, then `dispatched`, then `completed` — all on a single thread. File-order monotonicity is trivially preserved by sequential single-writer execution.

This is a narrower rule than the previous "intent durable before signal" invariant and it is honest about the two paths' different ownership models.

### Transactional registry protocol

`decide()` must perform two durable side effects and one non-durable side effect in a specific order, with well-defined failure behavior between each step. The transactional protocol makes that structure explicit.

**States and transitions:**

```
┌─────────────┐  reserve()   ┌──────────┐  commit_signal(token)  ┌───────────┐
│  awaiting   │─────────────►│ reserved │───────────────────────►│ consuming │
│ (worker     │              │ (decide  │                        │ (worker   │
│  blocked)   │◄─────────────│  pre-    │                        │  waking)  │
│             │  abort_      │  commit) │                        │           │
└─────────────┘  reservation └──────────┘                        └───────────┘
                  (token)
```

The terminal transition `reserved → consuming` is **irreversible** by contract. `reserved → awaiting` via `abort_reservation` is only safe *before* the caller has written any durable side effect tied to this reservation.

**decide()'s use of the protocol:**

```python
def decide(job_id, request_id, decision, answers) -> DelegationDecisionResult:
    # 1. Validate args (existing logic)
    payload = build_response_payload(decision, answers, request)

    # 2. Reserve (CAS awaiting → reserved). If None, caller already decided.
    token = registry.reserve(request_id, Resolution(payload=payload, kind=request.kind))
    if token is None:
        return _reject(reason="request_already_decided", ...)

    try:
        # 3. Write durable intent. THIS is the authority-making step — on
        # success, the operation is recoverable and MUST be committed.
        journal.write_phase(OperationJournalEntry(
            operation="approval_resolution", phase="intent",
            decision=decision, job_id=job_id, request_id=request_id, ...,
        ))
    except BaseException:
        # Intent never landed. Roll back the reservation so a retry or
        # the timer can claim the slot. Re-raise to surface the error.
        registry.abort_reservation(token)
        raise

    # 4. Commit + signal. Irreversible; worker wakes here.
    registry.commit_signal(token)

    # 5. Audit — post-commit, non-gating. Audit failure is logged as a
    # warning but does NOT roll back the signal (per IO-5, audit is not
    # durable enough to gate worker wake).
    try:
        journal.append_audit_event(AuditEvent(action=decision, ...))
    except BaseException as exc:
        logger.warning("Audit event append failed post-commit: %s", exc)

    return DelegationDecisionResult(decision_accepted=True, job_id=job_id, request_id=request_id)
```

**Failure analysis per step:**

| Failure between… | Outcome | Recovery |
|---|---|---|
| `reserve()` raises | No registry mutation; no journal writes | Caller sees the exception and can retry |
| `reserve()` returns None | Slot already reserved/consumed by another call | Existing CAS semantics; reject with `request_already_decided` |
| Journal `intent` raises | `abort_reservation(token)` restores `awaiting` before re-raise | Entry back in `awaiting`; timer or retry can claim |
| Journal `intent` succeeds, `commit_signal` raises | Impossible by construction: `commit_signal` is a local `threading.Event.set()` + state mutation. If it raises, the plugin has a deeper bug — log and crash loudly rather than abort. | Plugin-critical failure; documented in the protocol |
| `commit_signal` succeeds, audit raises | Logged warning; decide returns success | Audit gap is acceptable per IO-5 |

**Reservation token and context manager.** To make the reserve/commit-or-abort pairing enforceable by reading decide()'s code, the registry exposes a context-manager variant that auto-aborts uncommitted reservations on exit:

```python
with registry.reservation(request_id, resolution) as token:
    if token is None:
        return _reject(reason="request_already_decided", ...)
    journal.write_phase(...)
    token.commit_signal()    # explicit; otherwise the with-block aborts on exit

# If journal.write_phase raised, the with-block aborts the reservation on
# context exit; commit_signal was never called.
```

Uncommitted `ReservationToken`s auto-abort when the context manager exits; explicit `.commit_signal()` promotes the token to consumed and suppresses auto-abort.

**Why audit lives outside the transaction:** Per IO-5, `append_audit_event` is best-effort (no flush, no fsync). If audit were sequenced *before* `commit_signal`, an audit failure would force `abort_reservation` — but the intent record is already durable. Aborting would create a durable "ghost intent" (journal says operator decided; registry says entry is back in awaiting). Recovery would then see an orphan intent without a matching dispatched/completed, triggering the `recovered_unresolved` recovery path for an operation that was actually about to succeed. Moving audit post-commit eliminates this class of error. The consequence is that audit events may be lost on crash between `commit_signal` and the audit append — acceptable because recovery reconstructs the operator-decision record from the operation journal's `decision` field on the intent entry.

**Intent durability is the authority boundary.** The invariant is: *once `approval_resolution.intent` is durable, the operation is committed regardless of what happens on the plugin side afterward.* The registry reservation is a coordination primitive (keeps the worker blocked until main is ready to wake it); the journal intent is the recovery authority. Rollback across the authority boundary would violate this invariant.

### Capture-ready handshake (start() control flow)

`start()` is synchronous at the MCP boundary — the caller expects either an escalation payload (most common), a terminal result (rare: turn finished without any approval request), or an error. The worker is the only thread with the transport; the main thread cannot observe "a request is parked" from any durable surface until the worker has written it. The handshake primitive is the per-job capture-ready channel on the registry.

**Constant:** `CAPTURE_READY_TIMEOUT_SECONDS = 30` (configurable). Safety net only — the worker should signal within seconds under normal conditions. This is a different timer than `APPROVAL_OPERATOR_WINDOW_SECONDS`; the former bounds "how long before we suspect the worker is wedged"; the latter bounds "how long an operator has to decide."

**Worker sequence (inside `_execute_live_turn` handler, on first captured request):**

```
1. pending_request_store.create(request)              # durable request record
2. job_store.update_parked_request(job_id, rid)       # durable selector
3. job_store._persist_job_transition(needs_escalation) # status transition
4. registry.register(rid, job_id, APPROVAL_OPERATOR_WINDOW_SECONDS)   # per-request entry: awaiting
5. registry.announce_parked(job_id, rid)              # signals main thread
6. resolution = registry.wait(rid)                    # blocks until decide() or timer
```

**Ordering rationale.** Steps 1–3 are durable-first: by the time step 5 fires, any `poll(job_id)` the caller issues returns the parked escalation consistently. Step 4 **must** precede step 5 because the handshake signal can wake the main thread arbitrarily fast; if the main thread observes `Parked` and immediately calls `decide()`, `reserve(rid)` must find the per-request entry already in `awaiting`. A reversed order (`announce_parked` before `register`) creates a race where `decide()` arrives before the worker has established the entry the reservation looks up.

**Worker sequence on turn-completion-without-capture (Codex finished its objective without needing approval):**

```
1. turn loop exits normally (turn/completed observed with no prior handler parking)
2. _finalize_turn builds the normal (non-escalation) outcome
3. registry.announce_turn_completed_empty(job_id)     # signals main
4. worker thread exits
```

**Worker sequence on exception during pre-capture or capture itself:**

```
1. exception propagates out of handler or turn loop
2. existing _mark_execution_unknown_and_cleanup runs (delegation_controller.py:759)
3. registry.announce_worker_failed(job_id, exc)       # signals main
4. worker thread exits
```

**Main-thread (`start()`) sequence:**

```python
def start(args) -> DelegationStartResult:
    job = self._job_store.create(...)
    self._journal.write_phase(OperationJournalEntry(operation="job_creation", phase="intent", ...))
    self._journal.write_phase(OperationJournalEntry(operation="job_creation", phase="dispatched", ...))
    self._spawn_worker(job)                            # worker starts _execute_live_turn
    result = self._registry.wait_for_parked(
        job.job_id, timeout_seconds=CAPTURE_READY_TIMEOUT_SECONDS,
    )
    match result:
        case Parked(request_id):
            return DelegationStartResult(
                job=job_store.get(job.job_id),         # re-read to capture status=needs_escalation
                escalation=self._project_pending_escalation(job),
                ...,
            )
        case TurnCompletedWithoutCapture():
            # Worker already wrote terminal state through _finalize_turn.
            return DelegationStartResult(
                job=job_store.get(job.job_id),         # status=completed
                escalation=None,
                outcome=... ,                          # non-escalation completion
            )
        case WorkerFailed(exc):
            # Worker already ran _mark_execution_unknown_and_cleanup; job is "unknown".
            raise DelegationStartError(
                reason="worker_failed_before_capture",
                cause=exc,
            )
        case CaptureTimeout():
            # Main-thread safety net. Worker is wedged or deadlocked.
            # Do NOT kill the worker arbitrarily; log + raise.
            # Recovery: next startup sees orphan job, demotes via recover_startup().
            raise DelegationStartError(
                reason="capture_ready_timeout",
                detail=f"worker did not signal capture within {CAPTURE_READY_TIMEOUT_SECONDS}s",
            )
```

**Status transitions visible to `start()`:**

| Worker outcome | `job.status` when `start()` returns | Returned to MCP caller |
|---|---|---|
| Parked | `needs_escalation` | Escalation payload + job snapshot |
| TurnCompletedWithoutCapture | Terminal (`completed` via `_finalize_turn`) | Non-escalation outcome (existing `DelegationStartResult` shape for that branch) |
| WorkerFailed | `unknown` (via `_mark_execution_unknown_and_cleanup`) | `DelegationStartError(reason="worker_failed_before_capture")` |
| CaptureTimeout | `running` (unchanged by main thread) | `DelegationStartError(reason="capture_ready_timeout")` |

**Why `CaptureTimeout` does not force-kill the worker:** Python threads cannot be safely cancelled from outside. Forcing a kill would orphan transport state, leak stdin/stdout handles, and leave stores mid-write. The safe path is: surface the error to the caller, leave the job in `running`, and let the existing cold-start recovery at `delegation_controller.py:2036-2038` demote the job to `unknown` on next session init (or sooner if explicit cleanup is warranted — this is follow-up surface area for a future packet, not Packet 1).

**Why `TurnCompletedWithoutCapture` is a legitimate outcome:** Codex may complete an objective in a single turn without triggering any server-request approval (no shell command, no file change, no user input) — for example, a purely analytical delegation. The worker's normal `_finalize_turn` path writes the terminal outcome; the handshake signals that main can return the non-escalation result.

## Deferred-Resolution Lifecycle

### Happy path

```
MAIN                          REGISTRY                        WORKER
────                          ────────                        ──────

start(args)
  job_store.create
  journal: job_creation.*
  spawn worker ────────────────────────────────────────────► _execute_live_turn
  wait_for_parked(job_id, 30s) ◄─────────── block ──────       run_execution_turn
                                                                 notification loop begins
                                                                 handler called:
                                                                   capture parsed
                                                                   store.create(req)
                                                                   job_store.update_parked_request(rid)
                                                                   job_store._persist_job_transition(
                                                                       needs_escalation)
                                                                   registry.register(rid, job_id, window)
                                                                   ──► entry[rid] = awaiting
                                                                   registry.announce_parked(job_id, rid)
                                       ──── signal(job_id) ───► (main unblocks with Parked(rid))
                                                                   registry.wait(rid)
                                                                   ◄── block on per-entry event ──
  result = Parked(rid)
  re-read job (status=needs_escalation)
  return DelegationStartResult(
      escalation=project_pending_escalation(job))
                                                              notification loop buffers
                                                              messages in queue during block

decide(rid)
  validate args; build payload
  token = registry.reserve(rid, res)   ──► CAS awaiting → reserved (atomic; no signal yet)
  if token is None: reject as request_already_decided
  try:
      journal.write_phase: approval_resolution.intent   # durable BEFORE commit_signal (IO-4 fsync)
  except:
      registry.abort_reservation(token) ──► reserved → awaiting
      raise
  registry.commit_signal(token)        ──► reserved → consuming + signal ─► wake
  return DelegationDecisionResult(decision_accepted=True,
                                   job_id=job_id, request_id=rid)
  # Post-commit, non-gating — audit failure logged as warning only (IO-5):
  journal.append_audit_event: approve | deny
                                                               job_store._persist_job_transition(running)
                                                               journal.write_phase: approval_resolution.dispatched
                                                               session.respond(rid, payload)
                                                                 [stdin write + flush succeed]
                                                               store.record_response_dispatch(rid, ...,
                                                                   dispatch_result="succeeded")
                                                               store.mark_resolved(rid, resolved_at)
                                                               job_store.update_parked_request(job_id, None)
                                                               journal.write_phase: approval_resolution.completed
                                                                   (completion_origin="completed_normally")
                                                               registry.discard(rid)
                                                               handler returns None (suppress auto-respond)
                                                              loop → next_notification()
                                                                ...
                                                                item/completed (matches item_id)
                                                                serverRequest/resolved (matches rid)
                                                                turn/completed
                                                              protocol_echo collected from
                                                                  _verify_post_turn_signals
                                                              store.record_protocol_echo(rid, ...)
                                                              _finalize_turn normally
                                                              worker thread exits
```

**Ordering invariants visible in the diagram:**

1. **Capture-ready before escalation return.** `start()` does not return an escalation until the worker's `announce_parked` signal arrives. All durable state (`pending_request_store.create`, `job_store.update_parked_request`, `job.status = needs_escalation`) is written before the signal, so `start()`'s re-read sees a consistent snapshot.
2. **Per-request entry registered before capture-ready signal.** The worker calls `registry.register(rid)` before `registry.announce_parked(job_id, rid)`. A pathologically fast `decide()` from the main thread (observing `Parked` and immediately calling `decide()`) can never reach `reserve(rid)` before the per-request entry exists.
3. **Journal `intent` durable before registry `commit_signal`.** `decide()` writes `approval_resolution.intent` to the operation journal (fsynced per IO-4) before calling `registry.commit_signal(token)`. The worker, which writes `dispatched` and `completed`, cannot wake before `commit_signal` fires — preserving file-order monotonicity of the `approval_resolution` idempotency key.
4. **Audit append is post-commit.** `journal.append_audit_event` fires after `commit_signal` returns and after decide() has already constructed its return value. Audit failure is a logged warning (IO-5: audit is not fsynced and cannot gate worker wake); it never rolls back the commit. This placement eliminates the "ghost intent" failure mode that would arise if audit sat inside the pre-signal critical section (see §Transactional registry protocol).

### Timeout path (cancel-capable kind)

```
MAIN                          REGISTRY                        WORKER
────                          ────────                        ──────
                              [no decide() arrives within
                               APPROVAL_OPERATOR_WINDOW_SECONDS]
                              internal timer fires
                              token = reserve(rid, timeout_resolution)
                                      # awaiting → reserved (in-memory only)
                              commit_signal(token)
                                      # reserved → consuming + event fires ─► wake
                              [timer thread writes NOTHING to the
                               operation journal — registry stays pure]
                                                               # Worker now owns every journal write
                                                               # for this idempotency key.
                                                               journal.write_phase: approval_resolution.intent
                                                                   (decision=None)           # first write
                                                               job_store._persist_job_transition(running)
                                                               journal.write_phase: approval_resolution.dispatched
                                                                   (decision=None)
                                                               session.respond(rid, {"decision": "cancel"})
                                                               store.record_timeout(rid,
                                                                   response_payload={"decision": "cancel"},
                                                                   response_dispatch_at="<iso>",
                                                                   dispatch_result="succeeded")
                                                               # Atomic op: sets timed_out=True,
                                                               # status="canceled", resolution_action=None
                                                               job_store.update_parked_request(job_id, None)
                                                               journal.write_phase: approval_resolution.completed
                                                                   (completion_origin="completed_normally")
                                                               # Audit is best-effort (IO-5);
                                                               # logged as warning if it fails.
                                                               audit: action="approval_timeout"
                                                               registry.discard(rid)
                                                               handler returns None
                                                              loop continues
```

### Timeout path (non-cancel-capable kind: request_user_input)

(`kind="unknown"` is not eligible for timeout because it never parks — see §Unknown-kind contract.)

```
REGISTRY (timer thread):
  token = reserve(rid, timeout_resolution)   # awaiting → reserved
  commit_signal(token)                        # reserved → consuming + signal ─► wake
  [no journal writes on timer thread]

WORKER on synthetic timeout wake:
  journal.write_phase: approval_resolution.intent (decision=None)   # first write
  job_store._persist_job_transition(running)
  journal.write_phase: approval_resolution.dispatched (decision=None)
  session.interrupt_turn(thread_id, turn_id)            # no respond(); no payload dispatched
  store.record_timeout(rid,
      response_payload=None,
      response_dispatch_at=None,
      dispatch_result=None)
  # Atomic op: sets timed_out=True, status="canceled",
  # leaves resolution_action=None, response_payload=None
  job_store.update_parked_request(job_id, None)
  journal.write_phase: approval_resolution.completed
      (completion_origin="completed_normally")
  # Audit is best-effort (IO-5); logged as warning if it fails.
  audit: action="approval_timeout"
  registry.discard(rid)
  handler returns None
```

**Why `record_timeout` instead of `record_response_dispatch` + `update_status`.** The earlier `record_response_dispatch(action=Literal["approve", "deny"], ...)` signature cannot represent a timeout — there is no operator `action`, and writing `resolution_action` to any non-None value would conflate operator-fact with circumstance-fact (Q7 invariant from the brainstorm). `record_timeout` is a dedicated mutator that **atomically** sets `timed_out=True`, `status="canceled"`, and the optional dispatch fields (None-tuple for the interrupt path; populated for the cancel-dispatch path). A separate `update_status` call would split the timed_out/status transition across two journal records, introducing a replay window where `timed_out=True` and `status="pending"` could be briefly observed — inconsistent with the atomicity the mutator contract guarantees.

**Timer ownership note (Packet 1 model).** The registry's internal timeout timer is a `threading.Timer` owned by each `RegistryEntry`. It performs ONLY in-memory state changes and the wake signal: `reserve(rid, timeout_resolution)` → `commit_signal(token)`. It does not write to the operation journal, the pending request store, the delegation job store, or the audit log. This keeps the registry a pure coordination primitive (IO-2) and avoids introducing a third journal writer beyond main and worker. All durable effects for a timeout — `approval_resolution.intent`, `dispatched`, `completed`, `record_timeout`, `update_parked_request`, audit — happen on the worker thread after wake, in single-writer sequence. File-order monotonicity of the `approval_resolution` idempotency key is therefore preserved trivially, without cross-thread coordination.

**Why cross-thread "intent durable before signal" does not apply here.** In the decide path, main writes `intent` and worker writes `dispatched/completed` — two threads must coordinate so `intent` lands first. In the timeout path, the timer writes nothing to the journal; the worker writes the entire `intent → dispatched → completed` sequence on a single thread. There is no cross-thread race to protect. The narrower invariant ("intent durable before the next-phase record for the same idempotency key") is preserved by local sequencing. The `decision=None` on timeout intent/dispatched records is the human-readable discriminator for "this record came from a timer, not an operator decide" — combined with the `PendingServerRequest.timed_out=True` marker and the `action="approval_timeout"` audit event (best-effort, IO-5).

### Worker-death path (exception during parked section)

```
WORKER raises during park or post-wake:
  try/except around run_execution_turn (delegation_controller.py:730-737)
  catches, calls _mark_execution_unknown_and_cleanup:
    - job_store._persist_job_transition(unknown) via existing path
    - _emit_terminal_outcome_if_needed
    - runtime_registry.release
    - session.close
  registry.discard(rid)          # final step added by this design
  re-raises

MAIN (later decide call):
  registry.reserve(rid, ...) → None (no entry; worker discarded it during cleanup)
  fall through to job state validation
  job.status == "unknown" → reject via job_not_awaiting_decision
```

### Cold-start reconciliation path

```
PLUGIN INIT:
  recover_startup() runs on main thread before any workers exist.
  For each unresolved approval_resolution idempotency_key:
    write phase="completed" with completion_origin="recovered_unresolved"
  For each orphaned active job (running, needs_escalation):
    demote to "unknown" via _persist_job_transition
    (projection ignores parked_request_id on terminal-status jobs)
```

## Data Model and Store Mutations

### DelegationJob (addition)

```python
parked_request_id: str | None = None
```

Set when worker begins parking; cleared post-respond cleanup. The job's durable selector for projection — answers "which request, if any, is this job's worker currently parked on."

### PendingServerRequest (additions)

All new fields are nullable / have safe defaults. Back-compatible: existing records read as all-None on new fields.

| Field | Type | Default | Set by | Set when |
|---|---|---|---|---|
| `resolution_action` | `Literal["approve", "deny"] \| None` | `None` | Worker (on wake from real decide) | Before respond dispatch |
| `response_payload` | `dict[str, Any] \| None` | `None` | Worker | At dispatch (for kinds with a payload; None for interrupted-path) |
| `response_dispatch_at` | `str \| None` | `None` | Worker | Immediately before respond() call |
| `dispatch_result` | `Literal["succeeded", "failed"] \| None` | `None` | Worker | Immediately after respond() returns or raises |
| `resolved_at` | `str \| None` | `None` | Worker | Only on success transition to `status="resolved"` |
| `protocol_echo_signals` | `tuple[str, ...]` | `()` | Worker | Post-turn, via promoted `_verify_post_turn_signals` |
| `protocol_echo_observed_at` | `str \| None` | `None` | Worker | Post-turn with `protocol_echo_signals` |
| `timed_out` | `bool` | `False` | Worker | Iff resolution came from registry timer, not decide() |

`resolution_action` is strictly operator-fact (what `decide()` specified). `timed_out` is strictly circumstance-fact. `dispatch_result` is strictly transport-fact. The three axes stay orthogonal so any audit query asks exactly what it means to ask.

### PendingRequestStatus (unchanged)

Existing enum `Literal["pending", "resolved", "canceled"]` at `packages/plugins/codex-collaboration/server/models.py:20` is sufficient. Successful resolution → `resolved`. Timeouts → `canceled`. Failures (BrokenPipe etc.) → `canceled` via the outer turn-failure path.

### OperationJournalEntry (addition)

```python
completion_origin: Literal["completed_normally", "recovered_unresolved"] | None = None
```

Provenance annotation on the terminal `phase="completed"` marker. Values:
- `"completed_normally"`: worker wrote the completed record in the normal dispatch flow.
- `"recovered_unresolved"`: cold-start recovery wrote the completed record to close an orphaned unresolved operation.
- `None`: legacy records written before this schema change (back-compat read semantics).

Narrowly scoped to journal provenance. Timeouts, failures, and dispatch errors are recorded on the `PendingServerRequest` record and/or audit events — not here.

### Store mutators

**PendingRequestStore additions:**

```python
def record_response_dispatch(
    self,
    request_id: str,
    *,
    action: Literal["approve", "deny"],
    payload: dict[str, Any],
    dispatch_at: str,
    dispatch_result: Literal["succeeded", "failed"],
) -> None:
    # Append {"op": "record_response_dispatch", ...}; replay handles new op type
    # Populates: resolution_action, response_payload, response_dispatch_at, dispatch_result

def mark_resolved(self, request_id: str, resolved_at: str) -> None:
    # Append {"op": "mark_resolved", ...}
    # Populates: status="resolved", resolved_at

def record_protocol_echo(
    self,
    request_id: str,
    *,
    signals: tuple[str, ...],
    observed_at: str,
) -> None:
    # Append {"op": "record_protocol_echo", ...}
    # Populates: protocol_echo_signals, protocol_echo_observed_at

def record_timeout(
    self,
    request_id: str,
    *,
    response_payload: dict[str, Any] | None,
    response_dispatch_at: str | None,
    dispatch_result: Literal["succeeded", "failed"] | None,
) -> None:
    # Append {"op": "record_timeout", ...}
    # Populates: timed_out=True; dispatch fields if applicable (None for interrupted path)
    # Also emits status transition to "canceled" atomically via the same op
```

Dedicated methods, not a generic `update(**fields)`. Matches existing store style at `pending_request_store.py:29-69` and keeps replay's `op` dispatch enumerable.

**DelegationJobStore addition:**

```python
def update_parked_request(
    self, job_id: str, request_id: str | None,
) -> None:
    # Append {"op": "update_parked_request", "request_id": rid | null}; replay handles new op
```

### Session API addition

`AppServerRuntimeSession` grows one method to let the `_server_request_handler` closure call `respond()` directly (enabling the worker to own the dispatch sequence including stores updates) while still returning `None` to suppress the notification loop's auto-respond at `runtime.py:246-248`:

```python
# packages/plugins/codex-collaboration/server/runtime.py — addition
def respond(self, request_id: str | int, result: dict[str, Any]) -> None:
    """Dispatch a response to a server-initiated request."""
    self._client.respond(request_id, result)
```

Thin delegation to `JsonRpcClient.respond` at `jsonrpc_client.py:106-130`. Exposed on the session so callers don't reach into `_client` directly.

### Replay logic

Each store's `_replay()` method extends with branches for new op types. Existing pattern at `pending_request_store.py:77-137`:

- `record_response_dispatch` → set the four dispatch fields on the existing record
- `mark_resolved` → set `status="resolved"` and `resolved_at`
- `record_protocol_echo` → set `protocol_echo_signals`, `protocol_echo_observed_at`
- `record_timeout` → set `timed_out=True`, dispatch fields (if provided), `status="canceled"`
- `update_parked_request` (on job store) → set `parked_request_id` to value or None

Unknown op types in logs from future migrations are skipped (graceful-read per existing pattern at `pending_request_store.py:87-90`).

## decide() and poll() Contract Changes

### DelegationDecisionResult — new shape (breaking)

Current definition at `models.py:418-426`:

```python
@dataclass(frozen=True)
class DelegationDecisionResult:
    job: DelegationJob
    decision: DecisionAction
    resumed: bool
    pending_escalation: PendingEscalationView | None = None
    agent_context: str | None = None
```

New definition:

```python
@dataclass(frozen=True)
class DelegationDecisionResult:
    decision_accepted: bool
    job_id: str
    request_id: str
```

All five previous fields are removed. The caller observes live state via `poll()`.

### decide() semantics

- Returns after, in strict order:
  1. Validating args (existing logic at `delegation_controller.py:1620-1649`).
  2. `registry.reserve(request_id, resolution)` — atomic CAS `awaiting → reserved`. If None, reject with `request_already_decided` and return without any further side effects.
  3. Writing `approval_resolution.intent` to the operation journal (existing write at `delegation_controller.py:1666-1679`; kept). If this raises, `abort_reservation(token)` restores `awaiting` and the exception re-raises to the caller.
  4. `registry.commit_signal(token)` — fires the per-entry event and transitions `reserved → consuming`. Irreversible.
  5. Appending `approve` / `deny` audit event via `journal.append_audit_event` (existing at `:1680-1692`; kept). **Post-commit, non-gating:** audit failure is logged as a warning and does not affect the return value. Audit is best-effort per IO-5.

- **Ordering rationale.** Step 3 (durable journal intent) must precede step 4 (worker wake) because the worker will immediately write `dispatched` and `completed` after wake; a late-arriving `intent` would violate file-order monotonicity of the `approval_resolution` idempotency key (see §Resolution registry → Ordering guarantees). Step 5 (audit) lives outside the critical section because IO-5 makes audit non-durable; gating the worker wake on a non-durable write would introduce a "ghost intent" failure mode under crash (see §Transactional registry protocol → "Why audit lives outside the transaction").

- **Failure recovery semantics:** the reservation is rollback-safe up to and including a raised journal-intent write. After journal-intent durably lands, the operation is committed from the authority perspective; `commit_signal` must succeed (it is a local state mutation + `threading.Event.set()`; failure is a plugin-critical bug rather than a recoverable error).

- The `approval_resolution.dispatched` write at `:1693-1708` **moves to the worker thread** — `decide()` no longer writes it.

- The verb is "accepted for dispatch," not "applied." Dispatch to Codex App Server happens asynchronously on the worker thread after wake. Observation of dispatch outcome is via `poll()` + audit events.

### Response payload mapping (plugin decision → App Server payload)

The `resolution` object that `decide()` claims into the registry carries the **App Server response payload** that the worker will pass to `session.respond(request_id, payload)`. The mapping from plugin-side decision verb to App Server payload is kind-sensitive. This table is the authoritative contract for Packet 1.

| Plugin decision | `command_approval` | `file_change` | `request_user_input` |
|---|---|---|---|
| `approve` | `{"decision": "accept"}` | `{"decision": "accept"}` | `{"answers": <validated answers dict>}` |
| `deny` | `{"decision": "decline"}` | `{"decision": "decline"}` | `{"answers": {}}` — *known-denial fallback*, see note |
| timeout (synthetic, cancel-capable) | `{"decision": "cancel"}` | `{"decision": "cancel"}` | N/A — uses `interrupt_turn`, no payload dispatched |
| timeout (synthetic, non-cancel-capable) | N/A | N/A | `interrupt_turn` only, no payload dispatched |

**Semantics of each App Server decision (per `docs/codex-app-server.md:986, 996`):**

- `{"decision": "accept"}` — operator approved this specific action; App Server proceeds with it.
- `{"decision": "decline"}` — operator declined this specific action; App Server does not execute it but does not abort the turn. The terminal `item/completed` will carry `status: "declined"`.
- `{"decision": "cancel"}` — operator or system is aborting; App Server cancels the turn. Reserved in Packet 1 for timeout/abort paths, **not** user-initiated deny.

**Why `deny → decline` (not `cancel`) for command/file kinds:**

- `deny` is a per-action operator decision, not an abort of the delegated turn. `decline` has that exact semantic in the App Server contract.
- `cancel` is reserved for circumstance-driven paths (timeout, lifecycle cleanup, abort). Keeping the mapping axis-clean means the request record's `resolution_action="deny"` and `timed_out=False` combination maps to `{"decision": "decline"}`, while `resolution_action=None` and `timed_out=True` maps to `{"decision": "cancel"}` — no cross-axis conflation.
- The terminal `item/completed` then carries `status: "declined"` for operator-deny and `status: "failed"` / `"completed"` for timeout-cancel, preserving downstream ability to distinguish.
- A future product-level "deny and abort the whole delegated turn" semantics, if needed, would be a separate plugin action (e.g., `deny_and_abort`) or an explicit policy flag — **not** hidden behind `deny`.

**Note on `request_user_input` + `deny`:**

The `request_user_input` request kind has no App Server-native `{"decision": ...}` channel; per `docs/codex-app-server.md:1002-1004`, responses are always shaped `{"answers": ...}`. The existing capture-time known-denial path at `delegation_controller.py:720` already dispatches `{"answers": {}}` (empty answers) as a denial approximation. Packet 1 preserves this behavior for operator `deny` on this kind:

- It is **not** an App Server-native "decline" — the App Server contract does not offer one for this kind.
- It is **not** a "cancel" — a cancel on `request_user_input` would mean aborting the turn, not declining the specific input.
- It **is** the empty-answers fallback that the codebase already relies on. Future work (Packet 2+) may negotiate a proper denial contract with App Server for this kind; until then, the Packet 1 behavior is an explicit known-limitation mapping.

The `PendingServerRequest` record after a `deny` on `request_user_input` still sets `resolution_action="deny"` (operator-fact) and `response_payload={"answers": {}}` (transport-fact). Audit queries distinguish "operator denied" from "operator approved with empty answers" via `resolution_action`, which `response_payload` alone cannot disambiguate.

**Payload construction happens on the main thread** (inside `decide()` before `registry.reserve(...)`) — not on the worker. Rationale: validation lives in `decide()` anyway (`delegation_controller.py:1620-1649` validates `answers` for `request_user_input`); constructing the payload adjacent to validation keeps the error surface narrow. The worker receives a fully-formed payload in the `Resolution` object and dispatches it via `session.respond(...)` without further shaping.

**`kind="unknown"` is not in the mapping table.** Unknown-kind requests never reach the decide flow in Packet 1 — they are captured for audit, interrupt the turn, and terminalize the job. See §Unknown-kind contract (explicit behavior change) for the full rationale and the specific rejection reason `decide()` returns if a caller tries anyway.

### Unknown-kind contract (explicit behavior change from current code)

**Current behavior (pre-Packet 1, what Packet 1 replaces):** The D4 carve-out at `delegation_controller.py:671-688` creates a minimal `PendingServerRequest` with `kind="unknown"` when server-request parsing fails. The post-turn path at `:1473-1478` routes `interrupted_by_unknown = True` to `final_status = "needs_escalation"`. The branch at `:1482-1510` emits an `escalate` audit event and returns a `DelegationEscalation` with the unknown request projected as a caller-visible pending escalation. The operator is then expected to call `decide()` on a request the plugin could not even parse.

**Why this is a problem under Packet 1's model:** deferred approval assumes the plugin can construct a meaningful App Server response payload on the worker's behalf. Packet 1's §Response payload mapping table (approve → `{"decision": "accept"}`, etc.) requires a known request kind. For `kind="unknown"`, the plugin has no parseable `itemId`, `threadId`, or `commandActions` — nothing to respond to. Even if the operator said "approve," the worker would have nothing to dispatch.

**Packet 1 behavior (explicit change):**

| Step | Current | Packet 1 |
|---|---|---|
| Parse failure in handler | Create `PendingServerRequest(kind="unknown")` for audit | Same — preserve audit trail |
| Turn behavior | Handler calls `interrupt_turn` (at `:690-695`); flags `interrupted_by_unknown` | Same — still interrupts |
| Job status derivation | `final_status = "needs_escalation"` (at `:1473`) | `final_status = "unknown"` (terminal) |
| Caller-visible | `DelegationEscalation` with pending_escalation projection (at `:1504-1510`) | Plain `DelegationJob` with `status="unknown"`, plus a `DelegationOutcomeRecord` documenting the parse failure |
| Registry | Request registered, worker parks, escalation surfaces | Request NEVER registered, NEVER parked, NEVER announce_parked-ed |
| `decide()` on this request | Proceeds as if the operator can decide | Rejects with `job_not_awaiting_decision` (job is terminal, not awaiting) |
| Timeout diagrams | (timeout path applies) | N/A — no parked state |

**Rationale for rejection reason:** the request *does* exist in the pending request store (parse-failure record was created for audit), but the JOB is terminal (`unknown`). `request_not_found` is wrong because the request is persisted. `request_job_mismatch` is wrong because the request and job correlate correctly. `job_not_awaiting_decision` is correct: the job is not in `needs_escalation`, so no decision applies.

**Callsite change summary:**

- `delegation_controller.py:1473` — change `if captured_request.kind in _CANCEL_CAPABLE_KINDS or interrupted_by_unknown:` to match only `_CANCEL_CAPABLE_KINDS`; handle `interrupted_by_unknown` on a separate branch that routes to `final_status = "unknown"`.
- `delegation_controller.py:1482-1510` — the `if final_status == "needs_escalation":` branch must not fire for unknown-kind terminations. Instead, the `interrupted_by_unknown` path flows to the non-escalation return at `:1512-1517` (`_emit_terminal_outcome_if_needed`, release runtime, close session, return the `unknown`-terminal job).
- `delegation_controller.py` worker path — the new worker sequence (Packet 1) should not call `registry.register` or `registry.announce_parked` when the captured request has `kind="unknown"`. Instead it signals `announce_worker_failed(job_id, UnknownKindParseFailure(...))` or a dedicated `announce_turn_completed_empty(job_id)` with an attached diagnostic — pending the concrete implementation detail.
- Recovery code at `:2036-2038` already demotes `needs_escalation` jobs to `unknown` on restart; under Packet 1 these jobs never reach `needs_escalation` in the first place, so recovery treats them as already-terminal.

**Operator-facing effect:** under Packet 1, a parse-failed request surfaces to the operator as "delegation failed" (job terminal, status=`unknown`, `DelegationOutcomeRecord` with failure context), not as "please approve or deny this action." This is strictly more honest — the plugin cannot render the action in the first place, so asking the operator to decide on it is misleading.

**Tests to add:**

- Integration: server-request parse failure → turn interrupted → job terminalized as `unknown` → no escalation surfaces → `decide()` on the persisted-for-audit request rejects with `job_not_awaiting_decision`.
- Regression: the prior `interrupted_by_unknown → escalation` path is intentionally removed; test that it no longer fires.

### Rejection reasons (unchanged)

`DecisionRejectedReason` at `models.py:37-47` already covers every Packet 1 case:

| Condition | Reason |
|---|---|
| `decide()` called twice for the same `request_id` (second CAS fails) | `request_already_decided` |
| `decide()` arrives after orphan demotion to `unknown` | `job_not_awaiting_decision` |
| Stale `request_id` | `request_not_found` |
| Ambiguous job↔request mapping | `request_job_mismatch` |

No additions needed.

### poll() — unchanged shape

`DelegationPollResult` retains its current fields. Post-dispatch observations reach the caller via:
- `job.status` transitions (`needs_escalation → running → completed | failed | unknown`)
- `PendingEscalationView` (updated for the current parked request, if any)
- Later inspection surfaces for `PendingServerRequest.dispatch_result`, `resolved_at`, `protocol_echo_*` (not added to `PendingEscalationView` — see §Observability)

### The consuming window — honest poll semantics

Between `decide()`'s return and the worker's `job_store._persist_job_transition("running")` call, there is a transient window where `poll()` can legitimately observe:

- `job.status == "needs_escalation"` (worker has not yet transitioned)
- `job.parked_request_id == <rid>` (not yet cleared)
- `_project_pending_escalation` returning a `PendingEscalationView` for the decided request

This is NOT a bug and is NOT eliminated by any achievable synchronization short of blocking `decide()` until the worker wakes — which would recreate the synchronous-return failure that motivates Packet 1. Packet 1 accepts the window and documents it honestly.

**Properties of the consuming window:**

| Property | Value |
|---|---|
| Opens when | `decide()` returns `decision_accepted=True` |
| Closes when | Worker completes `job_store._persist_job_transition("running")` |
| Typical duration | Microseconds to low milliseconds — bounded by worker wake + one store write |
| What `poll()` shows inside the window | Same `PendingEscalationView` as before `decide()` returned |
| Risk | Caller that immediately polls after `decide()` may re-render the "awaiting approval" UI briefly, or (worse) call `decide()` again — the second call would return `request_already_decided` via the reservation CAS, which is safe but observable |
| Mitigation on caller side | Trust `decide()`'s `decision_accepted=True` as the authoritative "operator answer received"; use `poll()` for eventual state, not immediate re-verification |

**What the caller SHOULD do in the consuming window:** treat `decide()`'s successful return as the authoritative record that the decision has been accepted for dispatch. If the UI needs to reflect "decision accepted, dispatch pending," derive that state locally from the fact that `decide()` returned `decision_accepted=True`, not from an immediate `poll()`. Once the caller polls again (milliseconds later, or on the next user-driven poll), the window has closed and `job.status == "running"` or later.

**What the caller MUST NOT do:** assume that `poll()` immediately after `decide()` reflects the post-dispatch state. The spec's four-tier observability taxonomy (see §Observability) applies: transport-write outcome comes via store fields written post-dispatch; turn-terminal status comes via `job.status`; both trail `decide()`'s return by a bounded but nonzero delay.

**Honesty about alternatives (rejected):**

- *Block `decide()` until worker wakes.* Rejected — recreates the failure mode Packet 1 exists to fix. The whole point is that `decide()` returns while the worker proceeds asynchronously.
- *Have `decide()` write `status="running"` before returning.* Rejected — it would be honest about the registry state (reservation committed) but dishonest about the worker's progress (nothing has been dispatched yet). Worse, if the worker then fails, the job's recorded status lies about the sequence of events.
- *Add a `status="consuming"` intermediate JobStatus literal.* Rejected for Packet 1 scope — adds a new enum value for a window the caller can derive from `decide()`'s return anyway. Reconsider if downstream consumers turn out to need explicit persistence of this state.

### `_project_pending_escalation` rewrite

Current implementation at `delegation_controller.py:860-868` uses `requests[-1]` (last record). Replace with job-anchored + tombstone-guarded logic:

```python
def _project_pending_escalation(
    self, job: DelegationJob,
) -> PendingEscalationView | None:
    if job.status in ("completed", "failed", "unknown"):
        return None                                           # terminal-state guard
    if job.parked_request_id is None:
        return None
    request = self._pending_request_store.get(job.parked_request_id)
    if request is None or request.status != "pending":
        return None                                           # tombstone guard: req resolved
                                                              # but job field not yet cleared
    return self._project_request_to_view(request)
```

The helper is **job-anchored** (takes `DelegationJob`), not collaboration-anchored — the authority chain starts at `poll(job_id)` at `:901-902`. Callers update to pass the job object.

### contracts.md §decide

Rewrite to reflect:
- Async model (decide returns before dispatch completes)
- Minimal response payload (`decision_accepted`, `job_id`, `request_id`)
- poll as sole observation surface for post-decide state
- "Accepted for dispatch" verb, not "applied"

Current text at `docs/superpowers/specs/codex-collaboration/contracts.md:297-310` is the update target.

### MCP tool schema (no JSON-schema change) and custom serializer

`mcp_server.py` declares `inputSchema` only for tools; there is no `outputSchema`. Output contracts live in the Python return types plus a thin serialization layer.

**Important correction from an earlier draft:** the serialization path is **not** simply "dataclass → `asdict` automatic." At `mcp_server.py:505-516` there is a custom `DelegationDecisionResult` branch that explicitly reads `result.job`, `result.decision`, `result.resumed`, `result.pending_escalation`, and `result.agent_context` — all five fields the new dataclass removes. Changing only the dataclass would raise `AttributeError` on every `codex.delegate.decide` MCP call. That branch must be updated as part of this packet.

Preferred remediation: simplify the branch to the fallthrough shape used by other tools:

```python
# Current (at mcp_server.py:505-516) — reads removed fields; MUST change
if isinstance(result, DelegationDecisionResult):
    payload = {
        "job": asdict(result.job),
        "decision": result.decision,
        "resumed": result.resumed,
    }
    if result.pending_escalation is not None:
        payload["pending_escalation"] = asdict(result.pending_escalation)
    if result.agent_context is not None:
        payload["agent_context"] = result.agent_context
    return payload
return asdict(result)

# Replacement — falls through to the existing else-branch pattern
return asdict(result)   # {"decision_accepted": bool, "job_id": str, "request_id": str}
```

Breaking changes therefore live in:

- `DelegationDecisionResult` definition (`models.py:418-426`)
- `delegation_controller.decide()` (returns new shape)
- `mcp_server.py:505-516` (custom serializer branch — remove or replace as above)
- `contracts.md` §decide
- Integration/model tests that assert on `decision`, `resumed`, `pending_escalation` (e.g., `test_mcp_server.py:1202`)

Any tests that inspect the MCP response shape (as opposed to the raw dataclass) must also be updated — the surface is now a 3-field object, not a nested job/pending_escalation structure.

## Observability and Honesty Rules

### Four-tier observation taxonomy

| Tier | Signal | Observed when | What we can claim | What we cannot claim |
|---|---|---|---|---|
| **Transport write** | `respond()` returned vs. `BrokenPipeError` | Synchronous with worker's respond() call | "Plugin wrote response JSON to App Server stdin"; "Local stdin flush completed (buffered bytes were handed to the OS pipe)" | "Fsync completed" (pipes have no backing store to fsync); "App Server received"; "Decision applied" |
| **Protocol echo** | `serverRequest/resolved` matching `requestId` OR `item/completed` matching `item_id` | Async, post-respond, request-scoped (current warning-only code at `delegation_controller.py:2079-2108`) | `serverRequest/resolved`: "App Server resolved or cleared the pending request at the protocol layer" (per `docs/codex-app-server.md:987, 1004` this fires both on our response AND on lifecycle cleanup — turn start/complete/interrupt). `item/completed`: "The corresponding item reached protocol-terminal state (`completed`/`failed`/`declined`)" | "App Server processed our specific response" (the signal does not distinguish response-driven resolution from lifecycle-cleanup-driven resolution); "The targeted operation was executed"; "The decision was honored" |
| **Turn terminal** | `turn/completed` / `interrupted` / `failed` | Async, turn-scoped | "Turn reached terminal state X after our dispatch" | "Terminal state reflects the dispatch" |
| **Subsequent capture** | Another server-request notification | Async, turn-scoped | "App Server continued running and emitted a new request" | "The new request results from the prior decision" |

### Observation channels

**Transport-write outcome** — persisted on `PendingServerRequest.dispatch_result`. Written immediately after `respond()` returns or raises. Record survives even on failure (for audit).

**Protocol echo** — persisted on `PendingServerRequest.protocol_echo_signals` and `protocol_echo_observed_at`. Promoted from the current warning-only `_verify_post_turn_signals` helper at `delegation_controller.py:2079-2108`. The refactored helper returns observed signals; the worker persists them via `record_protocol_echo`.

**Turn terminal** — already persisted via `job.status` transition and `DelegationOutcomeRecord` emission at `_emit_terminal_outcome_if_needed` (`delegation_controller.py:801`). No new audit channel needed.

**Subsequent capture** — implicit in the notification loop's continued operation. No new durable record; each subsequent capture creates its own `PendingServerRequest` record per existing flow.

### What is never added

Per OB-1:

- No "decision applied" field anywhere.
- No "resolution accepted by App Server" observation.
- No heuristic inference ("dispatch succeeded AND continuation observed within N seconds → probably applied") in plugin records. Such inferences belong in analytics tools that consume the audit trail, not in the plugin's durable state.

### Timeout audit event

Free-form audit event via `journal.append_audit_event`:

```python
AuditEvent(
    event_id=uuid(),
    timestamp=now_iso(),
    actor="system",
    action="approval_timeout",
    collaboration_id=job.collaboration_id,
    runtime_id=job.runtime_id,
    job_id=job.job_id,
    request_id=rid,
    ...
)
```

Narrative record of "registry timer fired for this request." Not recovery-critical; the `PendingServerRequest.timed_out=True` field is the durable fact. Audit event is for analytics / human review trails.

### `PendingEscalationView` stays minimal

`PendingEscalationView` at `models.py:441` retains its current "minimal caller-visible subset needed to render an escalation prompt" role. The new `PendingServerRequest` fields (`dispatch_result`, `resolved_at`, `protocol_echo_*`, `timed_out`) are diagnostic / historical state, not prompt-rendering state. Adding them would blur "current action needed" with "forensic request record."

A future inspection surface (not Packet 1) may expose these fields.

## Recovery and Reconciliation

### Existing reconciliation (retained)

- **Orphan demotion** at `delegation_controller.py:2036-2038`: after cold restart, any job persisted as `running` or `needs_escalation` is demoted to `unknown` because the runtime subprocess that served it is gone.
- **Journal reconciliation** at `delegation_controller.py:1856-1884`: for each unresolved `approval_resolution` idempotency_key, writes `phase="completed"` to close the row.

### New (this spec)

- **Completion provenance annotation:** the recovery-written `phase="completed"` records at `:1870-1884` gain `completion_origin="recovered_unresolved"`. Worker-written completions gain `completion_origin="completed_normally"`. Old records without the field are interpreted as `None` (back-compat read).
- **Projection tombstone guard** (already specified in `_project_pending_escalation` §contracts): between the worker's `mark_resolved` and `update_parked_request(None)` writes, the job may transiently show `parked_request_id != None` while the request's `status == "resolved"`. Projection returns None in this window rather than surfacing a stale view.
- **Terminal-status projection guard** (already specified): jobs in `completed`, `failed`, or `unknown` status return None from projection regardless of `parked_request_id`. The field is dead state once the job is terminal; the projection ignores it. Recovery does not proactively clear the field — projection's read-path guard is sufficient.

### Recovery does not claim success

`completion_origin="recovered_unresolved"` is the durable honesty about crash-abandoned rows. Downstream consumers that interpreted `phase="completed"` as "operation succeeded" were already wrong (because the current code blind-closes rows even before this spec); the new field gives them a correct signal to distinguish.

### Journal validator relaxation (REQUIRED schema change)

The journal validator at `packages/plugins/codex-collaboration/server/journal.py:124-136` (intent) and `:137-157` (dispatched) currently enforces `isinstance(record.get("decision"), str)` — i.e., `decision` is required to be a non-None string for any `approval_resolution` record. Under the current codebase, every write passes `decision=DecisionAction` literal so this holds.

Packet 1 introduces timeout `approval_resolution.intent` and `dispatched` records with `decision=None` (non-operator origin). The validator must relax the `decision` check on those two branches to:

```python
elif op == "approval_resolution" and phase == "intent":
    ...  # job_id (string), request_id (string) still required
    decision = record.get("decision")
    if decision is not None and not isinstance(decision, str):
        raise SchemaViolation(
            "approval_resolution at intent requires decision to be a string or None"
        )

elif op == "approval_resolution" and phase == "dispatched":
    ...  # job_id, request_id, runtime_id, codex_thread_id (strings) still required
    decision = record.get("decision")
    if decision is not None and not isinstance(decision, str):
        raise SchemaViolation(
            "approval_resolution at dispatched requires decision to be a string or None"
        )
```

**Scope of the relaxation — narrow by intent:**

- `decision=None` is permitted on `approval_resolution.intent` and `.dispatched` ONLY — no other operation.
- `decision=None` semantically means "non-operator-origin resolution" (today: timeout; future packets may add other non-operator origins).
- `DecisionAction` at `models.py:34` stays `Literal["approve", "deny"]` — the operator-decision vocabulary is NOT widened. `decision=None` is a journal-level representation, not a new operator decision.
- Readers that interpret `decision` must handle None explicitly; treating it as a missing required field (as today) would reject valid records post-migration.

**Test updates:** existing `test_journal.py` assertions that `approval_resolution intent requires decision (string)` must be amended to allow None. Recovery code at `delegation_controller.py:1856-1884` must also accept None when reading journal intent records.

### What does NOT change

- Phase enum (`intent/dispatched/completed`) is untouched.
- Operation enum (`_VALID_OPERATIONS`) is untouched — `approval_resolution` already present; no new `approval_timeout` operation introduced.
- `_phase_rank` helper unchanged.
- `DecisionAction` literal at `models.py:34` stays `approve | deny`.

## Timeout Policy

### The operator window

**`APPROVAL_OPERATOR_WINDOW_SECONDS`** — local abandonment budget, configurable.

- **Default:** 900s (provisional). Marked for empirical refinement during implementation.
- **Framing:** local plugin-side tolerance for operator delay. **Not** a value derived from any repo-authoritative upstream contract. The Codex App Server's own server-request timeout is external and unknown to this codebase.
- **Configuration surface:** env var (or plugin settings file) for per-deployment override.

### Interaction with existing transport timeouts

The existing timeouts at `runtime.py:49` (client-side `request_timeout`, default 1200s) and `runtime.py:233` (notification-loop timeout, default 1200s) **do not directly bound** the operator window, because neither is active while the handler is parked:

- Client-side `request_timeout` governs OUR outbound requests (`turn/start`, `turn/interrupt`). Not used during the parked handler block.
- Notification-loop timeout governs inter-notification gaps during the turn. The loop is not calling `next_notification` during the parked block — it is inside `server_request_handler(notification)` at `runtime.py:246`. The timeout resets after each handler return.

The true coordination rule is: `operator_window < App_Server's_server_request_timeout` (external, unknown). The 900s default is conservative under the assumption that App Server mirrors the 1200s convention, but the spec makes no claim to repo-authoritative justification.

### Expiry mechanics

1. Registry timer fires after `APPROVAL_OPERATOR_WINDOW_SECONDS`.
2. Registry publishes a synthetic **timeout resolution** — same channel as a real `decide()` would use, but with an internal flag indicating origin.
3. Worker wakes (identical wake path to the real-decide path).
4. Worker handles the timeout kind-sensitively (see next section).

### Kind-sensitive timeout dispatch

Mirrors the existing capture-time kind distinctions at `delegation_controller.py:640-643, 698-720`:

| Request kind | Capture-time (current) | Timeout-time (new) |
|---|---|---|
| `command_approval` | `{"decision": "cancel"}` | `{"decision": "cancel"}` — dispatch via respond() |
| `file_change` | `{"decision": "cancel"}` | `{"decision": "cancel"}` — dispatch via respond() |
| `request_user_input` | `{"answers": {}}` (known-denial at `:720`) | `entry.session.interrupt_turn(...)` — no respond() |
| `unknown` | `interrupt_turn` (D4 carve-out at `:690-695`) | `entry.session.interrupt_turn(...)` — no respond() |

**Why narrowed for Packet 1:** `request_user_input`'s timeout-response contract is not pinned in the codex-app-server docs. The existing capture-time `{"answers": {}}` path is known to work as denial; using the same payload at timeout-time is plausible but uncertainty on App Server-side behavior argues for `interrupt_turn` instead. Packet 2 or a later packet may expand timeout automation to `request_user_input` after its response contract is explicitly confirmed.

### Timeout record fields

For cancel-capable kinds:

```
PendingServerRequest after timeout dispatch:
  resolution_action: None                         # operator did not decide
  response_payload: {"decision": "cancel"}        # what was dispatched
  response_dispatch_at: "<iso>"                   # when respond() was called
  dispatch_result: "succeeded" | "failed"         # transport outcome
  resolved_at: None                               # not resolved — timed out
  timed_out: True                                 # circumstance marker
  status: "canceled"                              # wire lifecycle
```

For non-cancel-capable kinds:

```
PendingServerRequest after timeout interrupt:
  resolution_action: None
  response_payload: None                          # no dispatch occurred
  response_dispatch_at: None
  dispatch_result: None
  resolved_at: None
  timed_out: True
  status: "canceled"
```

## Testing and Migration

### Testing strategy

**Unit tests (per new store mutator):**
- `PendingRequestStore.record_response_dispatch` — round-trip through append + replay
- `PendingRequestStore.mark_resolved` — status transition + timestamp set
- `PendingRequestStore.record_protocol_echo` — signals tuple + timestamp
- `PendingRequestStore.record_timeout` — timed_out flag + status=canceled atomicity
- `DelegationJobStore.update_parked_request` — set, then clear, then replay consistency

**Integration tests (worker thread lifecycle):**
- Worker spawn on `start()`; escalation returned before turn completes
- Worker parks on registry; MCP main thread responsive to concurrent poll
- Worker wakes on `decide()`; dispatches respond; transitions status
- Worker wakes on timeout; dispatches cancel; records timed_out
- Worker exception during park; cleanup runs; registry entry discarded; late decide rejects via `job_not_awaiting_decision`
- Worker exception post-wake; cleanup runs; turn fails; `_mark_execution_unknown_and_cleanup` executes

**End-to-end tests (MCP boundary):**
- Full deferred-approval flow: MCP `codex.delegate.start` → capture → park → MCP `codex.delegate.poll` returns escalation → MCP `codex.delegate.decide` → dispatch → turn completes → final poll returns completion
- Duplicate decide: second call returns `request_already_decided`
- Poll during consuming window: MAY transiently show pending_escalation; once worker completes `status→running` transition, subsequent polls no longer surface the escalation. Test asserts the eventual state, not immediate absence.
- Cold-start recovery: plugin restart mid-park → orphan demotion → late decide rejects

**Concurrency property tests:**
- IO-1: no other thread calls `JsonRpcClient` methods while worker owns the session (introspect via mock/spy)
- IO-2: no main-thread store writes to `pending_request_store` during worker's turn (same approach)
- IO-3: single-writer-per-store under race (stress test with multiple turns)
- IO-4: not directly testable (platform invariant); documented assumption

**Observability tests:**
- OB-1: no test/assertion ever claims "decision applied" based on transport success alone
- Protocol echo: persisted tuple matches signals observed in notifications
- Timeout: `approval_timeout` audit event fires; `timed_out=True` on record

### Migration

**Data:** None required. All new `PendingServerRequest` fields have safe defaults (None or empty tuple or `False`). Existing records read as all-None / empty on new fields.

**Journal:** `completion_origin` is optional; old records without the field read as `None`. Backward-compatible.

**Job store:** `parked_request_id` optional with `None` default; existing jobs read as not parked.

**Contract:** `DelegationDecisionResult` shape change is breaking for external callers. Callers that read `pending_escalation` from decide's response must switch to `poll()` — intentional migration forcing, not an accident.

**Tests:** `test_mcp_server.py:1202` and related assertions on `decision`/`resumed` are rewritten to the new success shape.

## Rejected Alternatives (Rationale Appendix)

One rejected alternative per question from the Q1–Q7 brainstorm. Each is documented here because future readers may propose them without context.

### Q1: asyncio task + awaitable future

Rejected: would require rewriting `JsonRpcClient` (subprocess + thread-backed blocking queue reads are not awaitable), plus converting every sync caller up the stack (`_run_turn`, `run_execution_turn`, MCP dispatch) to async. The transport layer at `jsonrpc_client.py:8,35-59` is already multi-threaded via background reader threads; the worker-thread approach extends this established pattern. asyncio would be a fundamentally different concurrency model that doesn't mesh and would require a far broader refactor than Packet 1 should own.

### Q2: multi-capture collection (list or dict keyed by request_id)

Rejected: adds in-memory state for a scenario the notification-loop shape already prevents. The handler at `runtime.py:245-248` runs serially — the loop cannot call the handler for a second notification until the first handler returns. "At most one parked-and-unresolved capture at any instant" is true by construction. A collection would be dead state.

### Q2: prove single-capture-per-turn

Rejected: amendment-triggered continuation genuinely can issue further approval requests. For multi-step objectives ("edit five files"), each sandbox-violating action can trigger its own approval. This path exists in the protocol; we cannot prove it away.

### Q3: `decide()` writes to `PendingRequestStore`

Rejected: creates cross-thread store writers (`pending_request_store` would be written by both main thread in `decide()` and worker thread on wake). Breaks IO-3. Single-writer discipline is cheaper and more verifiable than store-level locking.

### Q3: extend `PendingRequestStatus` enum with a `parked` literal

Rejected: `PendingRequestStatus` tracks wire lifecycle (`pending`/`resolved`/`canceled`). Adding a plugin-runtime concept would mix two axes in one enum. The job-level field `parked_request_id` is the right place because the coordination invariant ("at most one parked request per job") is job-scoped.

### Q4: journal-local mutex for `approval_resolution` phase writes

Rejected: the journal's append-only JSONL pattern matches the stores' pattern exactly (`journal.write_phase` at `journal.py:300-307` vs. `pending_request_store._append` at `:71-75`). The existing repo relies on OS-level JSONL append atomicity (IO-4). Extending the journal to multi-writer follows the same assumption. A mutex would be inconsistent with the stores' pattern and add complexity without adding correctness.

### Q4: liveness probe (`decide()` checks thread liveness before CAS)

Rejected: adds thread introspection as a regular path operation. Option A (worker exception handler discards registry entry) is cleaner because the cleanup is already happening for the exception path — we just add one line (`registry.discard(rid)`) to the existing `_mark_execution_unknown_and_cleanup` at `:759`.

### Q5: new `DecisionRejectedReason` values

Rejected: existing values (`request_already_decided`, `job_not_awaiting_decision`, `request_not_found`, `request_job_mismatch`) already cover all Packet 1 cases at `models.py:37-47`. Adding literals without concrete need expands the contract surface unnecessarily.

### Q5: new journal phases (`abandoned`, etc.)

Rejected: would require adding to `_VALID_PHASES` and updating `_phase_rank`. More invasive than one optional field. Also ambiguous about phase ordering.

### Q6: "applied vs error" observability channel

Rejected: no such channel exists in the current protocol. `JsonRpcClient.respond()` is fire-and-forget stdin write with no ack (`jsonrpc_client.py:106-130`); nothing in the notification stream semantically reports "App Server applied your decision." The four-tier observation taxonomy captures what is honestly observable; inventing a channel we cannot verify is the rejected spec's fundamental honesty failure.

### Q6: turn-scoped `turn_observed_terminal` audit event

Rejected: already covered by `job.status` persistence plus `DelegationOutcomeRecord` via `_emit_terminal_outcome_if_needed` at `delegation_controller.py:801`. Adding a new audit event duplicates existing state. The request-scoped `protocol_echo_*` fields are the high-signal new surface for Packet 1.

### Q7: transport-derived operator window

Rejected: the ticket's framing ("operator window ≤ transport budget") is imprecise. The client-side `request_timeout` bounds our outbound requests, not the parked handler. The notification-loop timeout isn't active during the parked block (handler call blocks the loop). The true constraint is App Server's server-request timeout, which is external and unknown. The 900s default is product policy, not transport derivation.

### Q7: universal timeout→cancel rule across all request kinds

Rejected: `request_user_input`'s timeout-response contract is not pinned in the codex-app-server docs. Applying the cancel-capable pattern to it without explicit contract confirmation risks mis-dispatching. Packet 1 narrows timeout automation to kinds with unambiguous contracts; other kinds get `interrupt_turn` as safe fallback.

### Q7: `resolution_action="deny"` for synthetic timeouts

Rejected: conflates operator-fact with circumstance-fact. `resolution_action` was tightened in Q3/Q6 to mean what `decide()` specified. A timeout is not an operator deny; representing it as `action=deny` would undo the honesty cleanup. Timeout is represented on a separate axis (`timed_out: bool`).

### Q7: overloading `completion_origin` with a timeout value

Rejected: `completion_origin` tracks provenance of the terminal `approval_resolution.completed` journal marker — normal worker vs. recovery closure. Worker-driven timeout dispatch is still normal worker completion. Adding `origin_timeout_synthetic` to the field would conflate timeline provenance with dispatch circumstance. Timeout lives on the request record; `completion_origin` stays scoped to recovery.

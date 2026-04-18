# T-05 Execution-Start Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land `codex.delegate.start` as a bootstrap-only slice — persists an execution `CollaborationHandle` in the lineage store and a `DelegationJob` in the delegation job store, journals the creation through the three-phase intent → dispatched → completed discipline with the recovery-contract idempotency key `claude_session_id + delegation_request_hash`, creates an isolated worktree from a base commit, brings up an ephemeral execution runtime against the hardened six-field sandbox, registers live ownership of that runtime in a control-plane-owned registry so it remains controllable, enforces max-1 concurrency with the typed `Job Busy` response, and emits the `delegate_start` audit event. The first real execution turn is **not** dispatched in this slice; that is a follow-up.

**Architecture:** Mirrors the established dialogue pattern step-for-step (`dialogue.py::DialogueController.start`). `DelegationController` composes `ControlPlane` (execution runtime bootstrap), `WorktreeManager` (isolated worktree creation via `git worktree add --detach`), `LineageStore` (persisted execution `CollaborationHandle` — identity/routing), `DelegationJobStore` (session-scoped JSONL job persistence parallel to lineage), `OperationJournal` (journal-before-dispatch discipline for `job_creation` + audit emission), and `ExecutionRuntimeRegistry` (in-process live-ownership table keyed by `runtime_id`). The MCP server exposes `codex.delegate.start` with serialized dispatch and lazy factory-based controller instantiation, mirroring the existing dialogue wiring (`mcp_server.py:_ensure_dialogue_controller`). No caller-facing turn dispatch.

**Persistence layering — live vs. durable.** The `ExecutionRuntimeRegistry` is in-process live ownership only. The controller registers the runtime IMMEDIATELY after the `dispatched` journal write — before any committed-start local writes (lineage, job, audit, completed) — so any post-`dispatched` failure still leaves the runtime reachable via `registry.lookup(runtime_id)` for the rest of the session. The busy gate consults the registry alongside `job_store.list_active()` and unresolved `job_creation` journal entries, so same-session retry after a committed-start failure is rejected. Crash durability comes from the three durable stores: `LineageStore` (handle identity), `DelegationJobStore` (job lifecycle), `OperationJournal` (in-flight record of operations under the recovery-contract idempotency key). If the control plane dies, the registry is lost. Across restart the live runtime cannot be reattached (subprocess is gone, session is gone); the durable stores are what survives. On next startup, `DelegationController.recover_startup()` (Task 7) reconciles any unresolved `job_creation` journal records into durable state — `intent`-only records are closed as no-op, `dispatched`-but-unfinished records mark their `DelegationJob` and `CollaborationHandle` as `unknown` — and the reconciled records are advanced to `phase=completed` so they are no longer returned by `list_unresolved()`. Physical compaction via `OperationJournal.compact()` is a separate operation not invoked in this slice. The plan splits AC 1 and AC 4 along this layer: AC 1's "can start" is a live-ownership claim about the in-process registry retaining the runtime from `dispatched` onward; AC 4's "state persisted" is about the three durable stores plus the startup-reconciliation consumer. Live ownership is consistent post-`dispatched`; durable identity may be asymmetric across committed-start failures (handle marked `unknown`, job missing, etc.) and is closed by the consumer.

**Tech Stack:** Python 3.11+, pytest, `AppServerRuntimeSession` (existing JSON-RPC wrapper), git-via-subprocess for worktree ops, stdlib `uuid`/`hashlib`.

---

## Scope Lock

### In scope (this slice)

1. `codex.delegate.start` MCP tool surface with typed `DelegationJob` / `JobBusyResponse` return shapes.
2. Execution `CollaborationHandle` persisted in `LineageStore` — the plugin's identity and routing record for the delegation job. Mirrors the dialogue pattern (`dialogue.py:192-205`). `capability_class = "execution"`, `claude_session_id` from the bootstrap's published session id, `repo_root` from the caller.
3. `DelegationJob` persistence — session-scoped append-only JSONL store (parallel to `LineageStore`).
4. Operation journal extension for delegation:
   - `OperationJournalEntry.operation` literal gains `"job_creation"`; `OperationJournalEntry.job_id: str | None` field added.
   - `journal.py::_VALID_OPERATIONS` gains `"job_creation"`; `_JOURNAL_OPTIONAL_STR` gains `"job_id"`.
   - `_journal_callback` gains per-phase conditional-required-fields rules for `job_creation` (intent requires `job_id`; dispatched requires `job_id` + `runtime_id` + `codex_thread_id`).
   - Three-phase (intent → dispatched → completed) records written at job creation.
   - Idempotency key: `f"{claude_session_id}:{delegation_request_hash}"` where `delegation_request_hash = sha256(f"{repo_root}:{base_commit}")`. Per `recovery-and-journal.md:47`.
5. Isolated git worktree creation from a base commit (default: current HEAD of `repo_root`). Worktree path is under `${CLAUDE_PLUGIN_DATA}/runtimes/delegation/<job-id>/worktree/`.
6. Ephemeral execution runtime bootstrap: fresh `AppServerRuntimeSession` with `cwd=worktree_path`, `initialize`, `account/read`, and `thread/start`. The runtime is constructed but **no turn is dispatched**.
7. `ExecutionRuntimeRegistry`: in-process live-ownership table keyed by `runtime_id`. Exposes `register` / `lookup` / `release` / `active_runtime_ids`. Retains `(session, thread_id, job_id)` so the control plane stays in control of the runtime for later dispatch, close, and crash-to-`unknown` paths.
8. Max-1 concurrent delegation gate; second call while an active job is `queued` / `running` / `needs_escalation` returns `JobBusyResponse`.
9. `delegate_start` audit event emission with the contracts.md-required fields (`collaboration_id`, `job_id`, `runtime_id`).
10. Production wiring in `codex_runtime_bootstrap.py`: factory constructs a fresh `ExecutionRuntimeRegistry` per plugin instance and shares the existing `LineageStore` + `OperationJournal` with the dialogue path.
11. Unit + integration tests covering handle persistence, job persistence, journal records (intent + dispatched + completed), registry state, worktree creation, busy rejection, sandbox construction (already locked by prior slice, re-asserted here), runtime lifecycle boundaries, and audit emission.
12. Committed-start failure semantics: `DelegationController.start` defines explicit behavior when any local write after the `dispatched` journal phase fails (lineage persist, job persist, journal `completed`, audit). `CommittedStartFinalizationError` is raised with no-retry guidance; any partially persisted handle/job is best-effort marked `unknown`; the journal is left at `dispatched` so startup reconciliation can close it. Mirrors `dialogue.py::CommittedTurnFinalizationError` for the reply path (`dialogue.py:361-373`). Tested against lineage-store, job-store, journal-completed, and audit-append failures.
13. Startup reconciliation: `DelegationController.recover_startup()` consumes unresolved `job_creation` journal records on session init — `intent`-only → closed as no-op; `dispatched` with persisted handle and/or job → mark each persisted record `unknown` and advance the journal to `completed`; `dispatched` with no persisted state (register-failure, or crash between `dispatched` and the first durable write) → advance the journal to `completed` only, since there is no handle / job / registry entry to reconcile. Reconciled records are no longer returned by `list_unresolved()` (physical compaction via `OperationJournal.compact()` is a separate operation not invoked here). Wired into `mcp_server.py` at BOTH the eager session-init path (`startup()`) and the lazy factory path (`_ensure_delegation_controller`), mirroring the dialogue precedent at `mcp_server.py:128-129` and `:147`. Production deploys via the lazy factory in Task 9, so the lazy-path wiring is the load-bearing one.

### Explicitly out of scope (follow-up slices)

- `run_execution_turn()` invocation. The bootstrap leaves the runtime alive with a thread created and registered in the runtime registry, but no `turn/start` is dispatched. When the next slice wires turn dispatch, it will use the six-field helper already constructed here and look up the session via `ExecutionRuntimeRegistry.lookup(runtime_id)`.
- `codex.delegate.poll`, `.decide`, `.promote`.
- Notification-loop pending-request capture. The execution runtime's `next_notification` loop is not wired to the approval router. **AC 6 is NOT closed by this slice.**
- Runtime teardown on job completion — `ExecutionRuntimeRegistry.release(runtime_id)` is defined and tested, but callers (poll/promote) land with the lifecycle slices.
- Worktree cleanup on job completion. Worktree path is persisted; cleanup is deferred to poll/promote.
- Context assembly for delegation packets (no turn dispatch means no packet assembly path needed here).
- Async/background execution, cancellation, progress reporting.
- Artifact-store primitives (deferred to promotion slice).

### Acceptance coverage against T-05 ticket

The success boundary: `codex.delegate.start` persists identity + job records, journals the creation under the recovery-contract idempotency key, bootstraps and retains ownership of a real isolated execution runtime. It does **not** dispatch the first delegation turn. Each status below cites the implementation step that literally satisfies the AC text. AC 2, 6, and 7 remain partial or open because the call sites that exercise sandbox enforcement, pending-request capture, and sandbox-construction call paths all land with turn dispatch (a follow-up slice).

| AC | Status | Evidence (literal implementation step) |
|---|---|---|
| 1. Can start an isolated execution runtime for a delegation job | ✅ | Task 4 adds `ControlPlane.start_execution_runtime` (bootstrap). Task 6 has `DelegationController.start` call `ExecutionRuntimeRegistry.register(runtime_id, session, thread_id, job_id)` IMMEDIATELY after the `dispatched` journal write — before any committed-start local writes — so the runtime is controllable via `registry.lookup(runtime_id)` from the moment the journal records dispatched. The busy gate consults `registry.active_runtime_ids()` (alongside `job_store.list_active()` and unresolved `job_creation` journal entries) so a same-session retry after a committed-start failure is rejected. Live ownership is consistent post-`dispatched` for every committed-start failure path EXCEPT `runtime_registry.register` itself raising — that case is structurally a duplicate-`runtime_id` collision (extremely unlikely with uuid-generated ids) and produces no entry to retain. Durable identity is the consumer-side concern under AC 4. |
| 2. Six-field SandboxPolicy at runtime start | 🔶 partially | App Server applies `sandboxPolicy` on `turn/start`, not on runtime-process init. The six-field helper was verified by the prior slice (`test_runtime.py:167-183`, still green in this slice's full-suite run). This slice adds no new call site; the first live call lands with turn dispatch. AC 2's "starts with" phrasing is forward-looking about the first turn, not runtime-process init. |
| 3. Each job owns exactly one worktree and one execution runtime | ✅ | `DelegationController.start` creates worktree + runtime together under the same `job_id` subdirectory; max-1 busy gate prevents concurrent jobs; `ExecutionRuntimeRegistry.register` refuses duplicate `runtime_id`. |
| 4. Job state persisted strongly enough for later promotion to inspect | ✅ | Three durable producers: execution `CollaborationHandle` written to `LineageStore` (Task 6), `DelegationJob` written to `DelegationJobStore` (Task 6), three-phase `job_creation` records written to `OperationJournal` (Task 6) under the recovery-contract idempotency key `claude_session_id + delegation_request_hash` per `recovery-and-journal.md:47`. One durable consumer: `DelegationController.recover_startup()` (Task 7) reconciles unresolved `job_creation` records into terminal durable state (`intent`-only → closed no-op; `dispatched` with persisted handle/job → mark `unknown`; `dispatched` with no persisted state — the register-failure case — → journal advance only, since there is no handle/job to mark) and advances every key to `phase=completed` so they are no longer returned by `list_unresolved()`. Physical compaction via `OperationJournal.compact()` is deferred. Wired into `mcp_server.py` at BOTH the eager session-init path (`startup()`) and the lazy factory path (`_ensure_delegation_controller`), mirroring the dialogue precedent at `mcp_server.py:128-129` and `:147`. Production deploys via the lazy factory in Task 9, so the lazy-path wiring is the load-bearing one. AC 4 needs both halves — producer alone would leave journal records without a reader; consumer alone would have nothing to reconcile. |
| 5. Busy rejection with typed `Job Busy` | ✅ | `DelegationController.start` returns `JobBusyResponse` when `DelegationJobStore.list_active()` is non-empty (Task 6). |
| 6. Execution-domain server requests surfaced through approval routing | ❌ not closed | Pending-request capture requires notification-loop wiring, which is the next slice. The approval-router substrate (`approval_router.py::parse_pending_server_request`) exists and is ready to consume events once wired. |
| 7. Tests cover worktree creation, busy rejection, runtime lifecycle boundaries, sandbox-policy construction | 🔶 partially | Worktree creation (Task 3), busy rejection (Tasks 6, 9), runtime lifecycle boundaries up to thread creation (Task 4), live-ownership retention and release (Task 5) all covered here. Sandbox-policy-construction coverage remains where the prior slice placed it (`test_runtime.py:167-183`). The next slice extends lifecycle coverage across turn dispatch. |

---

## File Structure

### New files

| Path | Responsibility |
|---|---|
| `packages/plugins/codex-collaboration/server/delegation_job_store.py` | `DelegationJobStore` — session-scoped append-only JSONL persistence with `create` / `update_status` ops and replay-on-read. Parallels `LineageStore`. |
| `packages/plugins/codex-collaboration/server/worktree_manager.py` | `WorktreeManager` — `create_worktree(repo_root, base_commit, worktree_path)` wrapping `git worktree add --detach <path> <commit>`. Fails fast on git errors. |
| `packages/plugins/codex-collaboration/server/execution_runtime_registry.py` | `ExecutionRuntimeRegistry` — in-process live-ownership table for execution runtimes keyed by `runtime_id`. Exposes `register` / `lookup` / `release` / `active_runtime_ids`. **Not** a crash-durability layer; recovery reads `LineageStore` + `DelegationJobStore` + `OperationJournal`. |
| `packages/plugins/codex-collaboration/server/delegation_controller.py` | `DelegationController` — orchestrates start flow: busy check (consults job store, registry, and unresolved `job_creation` journal) → base-commit resolve → journal intent → worktree create → runtime bootstrap → journal dispatched → register runtime → persist handle → persist job → audit emit → journal completed. Mirrors `dialogue.py::DialogueController.start` three-phase discipline; the registry-FIRST ordering after `dispatched` is delegation-specific (delegation has 4-5 post-`dispatched` local writes vs dialogue's 1, so the in-process ownership table needs to populate before any of them can fail). Includes `_delegation_request_hash` helper (sha256 of `f"{repo_root}:{base_commit}"`) used to compute the recovery-contract idempotency key. Also defines `CommittedStartFinalizationError` for post-`dispatched` local-write failures (mirrors `dialogue.py::CommittedTurnFinalizationError`) and `recover_startup()` for consuming unresolved `job_creation` journal records on session init (mirrors `dialogue.py:522 recover_startup`, but reconcile-only — no runtime reattach, since execution runtimes are subprocess-anchored to a worktree and cannot be rejoined across restart). |
| `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py` | Unit tests for the job store. |
| `packages/plugins/codex-collaboration/tests/test_worktree_manager.py` | Unit tests for worktree creation against a real tmp-path git repo. |
| `packages/plugins/codex-collaboration/tests/test_execution_runtime_registry.py` | Unit tests for the registry (register, lookup, release, duplicate-register rejection, active_runtime_ids). |
| `packages/plugins/codex-collaboration/tests/test_delegation_controller.py` | Unit tests for controller orchestration with fakes for every dependency. Verifies journal intent/dispatched/completed records, handle-in-LineageStore, job-in-JobStore, registry-retains-session, audit-emission, busy-rejection, roll-back-on-bootstrap-failure. |
| `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py` | End-to-end integration through MCP dispatch with a real temp git repo. Asserts handle + job + all three journal phases + registry state + audit event. |

### Modified files

| Path | Change |
|---|---|
| `packages/plugins/codex-collaboration/server/models.py` | Add `JobStatus` and `PromotionState` `Literal` aliases; add `DelegationJob` frozen dataclass; add `JobBusyResponse` frozen dataclass; promote `job_id` to top-level optional field on `AuditEvent`; extend `OperationJournalEntry.operation` literal to `Literal["thread_creation", "turn_dispatch", "job_creation"]`; add `OperationJournalEntry.job_id: str \| None = None` optional field. |
| `packages/plugins/codex-collaboration/server/journal.py` | Extend `_VALID_OPERATIONS` with `"job_creation"`; add `"job_id"` to `_JOURNAL_OPTIONAL_STR`; extend `_journal_callback` with per-phase conditional-required-fields rules: `job_creation` at `intent` requires `job_id` (string); `job_creation` at `dispatched` requires `job_id`, `runtime_id`, and `codex_thread_id` (all strings). Update callback construction to forward `job_id=record.get("job_id")`. |
| `packages/plugins/codex-collaboration/server/control_plane.py` | Add `start_execution_runtime(worktree_path: Path) -> tuple[str, AppServerRuntimeSession, str]` — fresh non-cached `AppServerRuntimeSession` with `cwd=worktree_path`, runs `initialize` + `account/read` (enforcing auth + compat), calls `start_thread`, returns `(runtime_id, session, thread_id)`. |
| `packages/plugins/codex-collaboration/server/mcp_server.py` | Add `codex.delegate.start` to `TOOL_DEFINITIONS`; add dispatch case; add `delegation_controller` / `delegation_factory` init kwargs; add `_ensure_delegation_controller()` parallel to `_ensure_dialogue_controller()` — including the `controller.recover_startup()` call BEFORE pinning that mirrors `mcp_server.py:147` (the load-bearing wiring for the production lazy-factory path); wire the eager-side `delegation_controller.recover_startup()` into `startup()` alongside the existing `dialogue_controller.recover_startup()` at `mcp_server.py:128-129`. |
| `packages/plugins/codex-collaboration/server/__init__.py` | Export `DelegationController`, `DelegationJob`, `JobBusyResponse`, `ExecutionRuntimeRegistry`. |
| `packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py` | Add `_build_delegation_factory()` that constructs a fresh `ExecutionRuntimeRegistry`, reuses the dialogue path's existing `LineageStore` + `OperationJournal`, and wires `DelegationController`. Pass the factory into `McpServer(...)`. |
| `packages/plugins/codex-collaboration/tests/test_models_r2.py` | Append tests for `DelegationJob`, `JobBusyResponse`, top-level `AuditEvent.job_id`, the extended `OperationJournalEntry.operation` literal, and `OperationJournalEntry.job_id` default. |
| `packages/plugins/codex-collaboration/tests/test_journal.py` | Append tests for the `job_creation` operation — validator accepts the op at each phase, rejects `intent` missing `job_id`, rejects `dispatched` missing `runtime_id` or `codex_thread_id`, round-trips records through replay. |
| `packages/plugins/codex-collaboration/tests/test_mcp_server.py` | Add registration assertion for `codex.delegate.start`; add dispatch test with a `FakeDelegationController`. |
| `packages/plugins/codex-collaboration/tests/test_control_plane.py` | Add tests for `start_execution_runtime`. |

---

## Decomposition Philosophy

Tasks progress inside-out: **primitives first** (Tasks 1-5: types + journal extension, store, worktree manager, runtime bootstrap, registry), **orchestrator next** (Task 6: controller with committed-start failure semantics), **recovery consumer** (Task 7: startup reconciliation for unresolved `job_creation` journal records), **surface last** (Task 8: MCP tool + Task 9: factory), **integration finally** (Task 10), **verify + merge** (Task 11). Each commit is independently green — the plugin test suite passes after every commit, even though the tool surface is only reachable from caller-facing code after Task 9.

Test counts listed in each step are estimates. Real counts may diverge slightly depending on what arrives on `main` between plan authoring and execution. Treat divergence by more than ~3 tests as an investigation signal, not a silent contract violation.

---

## Pre-Flight (do once, before any task)

- [ ] **Step 1: Confirm clean main and create feature branch**

Run:
```bash
git status
git rev-parse HEAD
git checkout -b feature/t05-execution-start
```
Expected: `status` reports "clean" (or "nothing to commit"); HEAD is `bd850302` (the tmp-hardening merge); branch `feature/t05-execution-start` created from `main`.

If HEAD is not `bd850302`, stop and investigate — the plan assumes the prior slice landed.

- [ ] **Step 2: Establish baseline green suite**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/ -q
```
Expected: `593 passed` (baseline from handoff 2026-04-17 17:09).

If not green, stop — fix the baseline before continuing.

---

## Task 1: Delegation Model Types + Journal Extension

**Goal:** Add the type vocabulary and operation-journal validator extensions the rest of the slice will use. Pure additive — no behavior change for existing callers.

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py`
- Modify: `packages/plugins/codex-collaboration/server/journal.py`
- Test: `packages/plugins/codex-collaboration/tests/test_models_r2.py` (existing file; append)
- Test: `packages/plugins/codex-collaboration/tests/test_journal.py` (existing file; append)

- [ ] **Step 1.1: Write failing model-shape tests**

Append to `packages/plugins/codex-collaboration/tests/test_models_r2.py` (at end of file):

```python
def test_delegation_job_has_required_fields() -> None:
    from server.models import DelegationJob

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="queued",
        artifact_paths=(),
        artifact_hash=None,
    )
    assert job.job_id == "job-1"
    assert job.worktree_path == "/tmp/wk"
    assert job.status == "queued"
    assert job.promotion_state == "pending"
    assert job.artifact_hash is None


def test_delegation_job_is_frozen() -> None:
    from dataclasses import FrozenInstanceError
    import pytest

    from server.models import DelegationJob

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="queued",
    )
    with pytest.raises(FrozenInstanceError):
        job.status = "running"  # type: ignore[misc]


def test_job_busy_response_shape() -> None:
    from server.models import JobBusyResponse

    resp = JobBusyResponse(
        busy=True,
        active_job_id="job-1",
        active_job_status="running",
        detail="Another delegation is in flight.",
    )
    assert resp.busy is True
    assert resp.active_job_id == "job-1"
    assert resp.active_job_status == "running"


def test_audit_event_has_top_level_job_id_field() -> None:
    from server.models import AuditEvent

    event = AuditEvent(
        event_id="e-1",
        timestamp="2026-04-17T00:00:00Z",
        actor="claude",
        action="delegate_start",
        collaboration_id="collab-1",
        runtime_id="rt-1",
        job_id="job-1",
    )
    assert event.job_id == "job-1"


def test_audit_event_job_id_defaults_to_none() -> None:
    from server.models import AuditEvent

    event = AuditEvent(
        event_id="e-1",
        timestamp="2026-04-17T00:00:00Z",
        actor="claude",
        action="consult",
        collaboration_id="collab-1",
        runtime_id="rt-1",
    )
    assert event.job_id is None


def test_operation_journal_entry_accepts_job_creation_operation() -> None:
    from server.models import OperationJournalEntry

    entry = OperationJournalEntry(
        idempotency_key="sess-1:hash-abc",
        operation="job_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-04-17T00:00:00Z",
        repo_root="/tmp/repo",
        job_id="job-1",
    )
    assert entry.operation == "job_creation"
    assert entry.job_id == "job-1"


def test_operation_journal_entry_job_id_defaults_to_none() -> None:
    from server.models import OperationJournalEntry

    entry = OperationJournalEntry(
        idempotency_key="sess-1:collab-1",
        operation="thread_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-04-17T00:00:00Z",
        repo_root="/tmp/repo",
    )
    assert entry.job_id is None
```

- [ ] **Step 1.2: Write failing journal-validator tests**

Append to `packages/plugins/codex-collaboration/tests/test_journal.py`:

```python
def test_journal_accepts_job_creation_intent(tmp_path: Path) -> None:
    from server.journal import OperationJournal
    from server.models import OperationJournalEntry

    journal = OperationJournal(tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="sess-1:hash-abc",
        operation="job_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-04-17T00:00:00Z",
        repo_root="/tmp/repo",
        job_id="job-1",
    )
    journal.write_phase(entry, session_id="sess-1")

    diagnostics = journal.check_health(session_id="sess-1")
    assert diagnostics.schema_violations == ()


def test_journal_accepts_job_creation_dispatched_with_outcome_correlation(
    tmp_path: Path,
) -> None:
    from server.journal import OperationJournal
    from server.models import OperationJournalEntry

    journal = OperationJournal(tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="sess-1:hash-abc",
        operation="job_creation",
        phase="dispatched",
        collaboration_id="collab-1",
        created_at="2026-04-17T00:00:00Z",
        repo_root="/tmp/repo",
        job_id="job-1",
        runtime_id="rt-1",
        codex_thread_id="thr-1",
    )
    journal.write_phase(entry, session_id="sess-1")

    diagnostics = journal.check_health(session_id="sess-1")
    assert diagnostics.schema_violations == ()
    terminal = journal.check_idempotency("sess-1:hash-abc", session_id="sess-1")
    assert terminal is not None
    assert terminal.phase == "dispatched"
    assert terminal.job_id == "job-1"


def test_journal_rejects_job_creation_intent_missing_job_id(tmp_path: Path) -> None:
    import json as _json

    from server.journal import OperationJournal

    journal = OperationJournal(tmp_path)
    path = journal._operations_path("sess-1")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write a malformed record directly to exercise the validator.
    record = {
        "idempotency_key": "sess-1:hash-abc",
        "operation": "job_creation",
        "phase": "intent",
        "collaboration_id": "collab-1",
        "created_at": "2026-04-17T00:00:00Z",
        "repo_root": "/tmp/repo",
        # job_id missing intentionally
    }
    path.write_text(_json.dumps(record) + "\n")

    diagnostics = journal.check_health(session_id="sess-1")
    assert diagnostics.schema_violations != ()


def test_journal_rejects_job_creation_dispatched_missing_runtime_or_thread(
    tmp_path: Path,
) -> None:
    import json as _json

    from server.journal import OperationJournal

    journal = OperationJournal(tmp_path)
    path = journal._operations_path("sess-1")
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "idempotency_key": "sess-1:hash-abc",
        "operation": "job_creation",
        "phase": "dispatched",
        "collaboration_id": "collab-1",
        "created_at": "2026-04-17T00:00:00Z",
        "repo_root": "/tmp/repo",
        "job_id": "job-1",
        # runtime_id + codex_thread_id missing
    }
    path.write_text(_json.dumps(record) + "\n")

    diagnostics = journal.check_health(session_id="sess-1")
    assert diagnostics.schema_violations != ()
```

- [ ] **Step 1.3: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_models_r2.py tests/test_journal.py -v
```
Expected: 5 delegation-model tests fail with `ImportError`/`TypeError`. The 2 `OperationJournalEntry` tests fail with `TypeError: unexpected keyword 'job_id'` or `Literal` mismatch. The 4 journal-validator tests fail because `_VALID_OPERATIONS` does not yet accept `"job_creation"`.

- [ ] **Step 1.4: Implement model additions**

In `packages/plugins/codex-collaboration/server/models.py`:

Insert after the existing `PendingRequestStatus` literal (near line 19):

```python
JobStatus = Literal[
    "queued", "running", "needs_escalation", "completed", "failed", "unknown"
]
PromotionState = Literal[
    "pending",
    "prechecks_passed",
    "applied",
    "verified",
    "prechecks_failed",
    "rollback_needed",
    "rolled_back",
    "discarded",
]
```

Modify the existing `AuditEvent` dataclass (around `models.py:146`) by adding a top-level `job_id: str | None = None` field. Final shape:

```python
@dataclass(frozen=True)
class AuditEvent:
    """Audit event record. See contracts.md §AuditEvent."""

    event_id: str
    timestamp: str
    actor: Literal["claude", "codex", "user", "system"]
    action: str
    collaboration_id: str
    runtime_id: str
    context_size: int | None = None
    policy_fingerprint: str | None = None
    turn_id: str | None = None
    job_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
```

Modify the existing `OperationJournalEntry` dataclass (around `models.py:273`):

```python
@dataclass(frozen=True)
class OperationJournalEntry:
    """Phased operation record for deterministic crash recovery replay.

    Lifecycle: intent (before dispatch) → dispatched (after dispatch, with
    outcome correlation data) → completed (confirmed, eligible for compaction).
    See recovery-and-journal.md §Write Ordering.
    """

    idempotency_key: str
    operation: Literal["thread_creation", "turn_dispatch", "job_creation"]
    phase: Literal["intent", "dispatched", "completed"]
    collaboration_id: str
    created_at: str
    repo_root: str
    # Outcome correlation — set when logically knowable
    codex_thread_id: str | None = None
    turn_sequence: int | None = None  # turn_dispatch only
    runtime_id: str | None = None
    context_size: int | None = None  # turn_dispatch only, set at intent
    job_id: str | None = None  # job_creation only
```

Append at the end of the file (after `OperationJournalEntry`):

```python
@dataclass(frozen=True)
class DelegationJob:
    """Persisted delegation job record. See contracts.md §DelegationJob.

    This slice writes ``status`` and ``promotion_state`` at creation time only.
    Lifecycle transitions (running → completed, etc.) land in later slices
    alongside poll/decide/promote wiring.
    """

    job_id: str
    runtime_id: str
    collaboration_id: str
    base_commit: str
    worktree_path: str
    promotion_state: PromotionState
    status: JobStatus
    artifact_paths: tuple[str, ...] = ()
    artifact_hash: str | None = None


@dataclass(frozen=True)
class JobBusyResponse:
    """Typed rejection returned by codex.delegate.start when a job is active.

    See contracts.md §Job Busy.
    """

    busy: bool
    active_job_id: str
    active_job_status: JobStatus
    detail: str
```

- [ ] **Step 1.5: Extend journal validator**

In `packages/plugins/codex-collaboration/server/journal.py`:

Update the operation set and optional-string list near the top (around `journal.py:35`):

```python
_VALID_OPERATIONS = frozenset(("thread_creation", "turn_dispatch", "job_creation"))
_VALID_PHASES = frozenset(("intent", "dispatched", "completed"))
_JOURNAL_REQUIRED_STR = (
    "idempotency_key",
    "operation",
    "phase",
    "collaboration_id",
    "created_at",
    "repo_root",
)
_JOURNAL_OPTIONAL_STR = ("codex_thread_id", "runtime_id", "job_id")
_JOURNAL_OPTIONAL_INT = ("turn_sequence", "context_size")
```

Extend `_journal_callback` with a `job_creation` branch alongside the existing `turn_dispatch` and `thread_creation` branches. Insert immediately after the existing `thread_creation` branch:

```python
    elif op == "job_creation" and phase == "intent":
        if not isinstance(record.get("job_id"), str):
            raise SchemaViolation(
                "job_creation at intent requires job_id (string)"
            )
    elif op == "job_creation" and phase == "dispatched":
        if not isinstance(record.get("job_id"), str):
            raise SchemaViolation(
                "job_creation at dispatched requires job_id (string)"
            )
        if not isinstance(record.get("runtime_id"), str):
            raise SchemaViolation(
                "job_creation at dispatched requires runtime_id (string)"
            )
        if not isinstance(record.get("codex_thread_id"), str):
            raise SchemaViolation(
                "job_creation at dispatched requires codex_thread_id (string)"
            )
```

Update the `OperationJournalEntry` construction at the end of `_journal_callback` to forward `job_id`:

```python
    entry = OperationJournalEntry(
        idempotency_key=record["idempotency_key"],
        operation=record["operation"],
        phase=record["phase"],
        collaboration_id=record["collaboration_id"],
        created_at=record["created_at"],
        repo_root=record["repo_root"],
        codex_thread_id=record.get("codex_thread_id"),
        turn_sequence=record.get("turn_sequence"),
        runtime_id=record.get("runtime_id"),
        context_size=record.get("context_size"),
        job_id=record.get("job_id"),
    )
```

- [ ] **Step 1.6: Run new tests and full plugin suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_models_r2.py tests/test_journal.py -v && uv run pytest tests/ -q
```
Expected: all 11 new tests pass; plugin suite `~604 passed` (593 baseline + 11 new: 5 delegation-model + 2 `OperationJournalEntry` + 4 journal-validator).

- [ ] **Step 1.7: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/journal.py packages/plugins/codex-collaboration/tests/test_models_r2.py packages/plugins/codex-collaboration/tests/test_journal.py
git commit -m "feat(t20260330-05): add DelegationJob types and extend journal for job_creation"
```

---

## Task 2: DelegationJobStore

**Goal:** Session-scoped append-only JSONL store for `DelegationJob` records, parallel to `LineageStore`. Supports `create`, `get`, `list`, `update_status`.

**Files:**
- Create: `packages/plugins/codex-collaboration/server/delegation_job_store.py`
- Create: `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py`

- [ ] **Step 2.1: Write failing tests**

Create `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py`:

```python
"""Tests for DelegationJobStore — session-scoped JSONL job persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.delegation_job_store import DelegationJobStore
from server.models import DelegationJob


def _make_job(
    job_id: str = "job-1",
    runtime_id: str = "rt-1",
    status: str = "queued",
) -> DelegationJob:
    return DelegationJob(
        job_id=job_id,
        runtime_id=runtime_id,
        collaboration_id=f"collab-{job_id}",
        base_commit="abc123",
        worktree_path=f"/tmp/wk-{job_id}",
        promotion_state="pending",
        status=status,  # type: ignore[arg-type]
    )


def test_create_then_get_returns_job(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job()

    store.create(job)

    assert store.get("job-1") == job


def test_get_returns_none_for_unknown_id(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    assert store.get("job-does-not-exist") is None


def test_list_returns_all_jobs_for_session(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1"))
    store.create(_make_job(job_id="job-2"))

    jobs = store.list()

    assert {j.job_id for j in jobs} == {"job-1", "job-2"}


def test_list_filter_by_status(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))
    store.create(_make_job(job_id="job-2", status="running"))
    store.create(_make_job(job_id="job-3", status="completed"))

    active = store.list_active()

    assert {j.job_id for j in active} == {"job-1", "job-2"}


def test_update_status_last_write_wins(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))
    store.update_status("job-1", "running")

    job = store.get("job-1")
    assert job is not None
    assert job.status == "running"


def test_update_status_rejects_unknown_status(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))

    with pytest.raises(ValueError, match="unknown status"):
        store.update_status("job-1", "definitely-not-a-status")  # type: ignore[arg-type]


def test_sessions_are_isolated(tmp_path: Path) -> None:
    store_a = DelegationJobStore(tmp_path, "sess-a")
    store_b = DelegationJobStore(tmp_path, "sess-b")
    store_a.create(_make_job(job_id="job-1"))

    assert store_a.get("job-1") is not None
    assert store_b.get("job-1") is None


def test_replay_reconstructs_state_from_log(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued"))
    store.update_status("job-1", "running")

    # New store instance replays the same log.
    replay = DelegationJobStore(tmp_path, "sess-1")
    job = replay.get("job-1")

    assert job is not None
    assert job.status == "running"
```

- [ ] **Step 2.2: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_job_store.py -v
```
Expected: `ImportError: No module named 'server.delegation_job_store'`.

- [ ] **Step 2.3: Implement DelegationJobStore**

Create `packages/plugins/codex-collaboration/server/delegation_job_store.py`:

```python
"""Session-scoped JSONL store for DelegationJob records.

Parallels LineageStore (see contracts.md §Lineage Store for the same design
pattern). Append-only; replay on read; last record for each job_id wins.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, get_args

from .models import DelegationJob, JobStatus, PromotionState

_VALID_STATUSES: frozenset[str] = frozenset(get_args(JobStatus))
_VALID_PROMOTION_STATES: frozenset[str] = frozenset(get_args(PromotionState))
_ACTIVE_STATUSES: frozenset[str] = frozenset(
    {"queued", "running", "needs_escalation"}
)


class DelegationJobStore:
    """Append-only JSONL store for DelegationJob records."""

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "delegation_jobs" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "jobs.jsonl"

    def create(self, job: DelegationJob) -> None:
        """Persist a new job record."""

        if job.status not in _VALID_STATUSES:
            raise ValueError(
                f"DelegationJobStore.create failed: unknown status. "
                f"Got: {job.status!r:.100}"
            )
        if job.promotion_state not in _VALID_PROMOTION_STATES:
            raise ValueError(
                f"DelegationJobStore.create failed: unknown promotion_state. "
                f"Got: {job.promotion_state!r:.100}"
            )
        self._append({"op": "create", **asdict(job)})

    def get(self, job_id: str) -> DelegationJob | None:
        """Retrieve a job by id, or None if not found."""

        return self._replay().get(job_id)

    def list(self) -> list[DelegationJob]:
        """Return all jobs for this session."""

        return list(self._replay().values())

    def list_active(self) -> list[DelegationJob]:
        """Return jobs whose status is not terminal (queued/running/needs_escalation)."""

        return [j for j in self._replay().values() if j.status in _ACTIVE_STATUSES]

    def update_status(self, job_id: str, status: JobStatus) -> None:
        """Append a status update for an existing job."""

        if status not in _VALID_STATUSES:
            raise ValueError(
                f"DelegationJobStore.update_status failed: unknown status. "
                f"Got: {status!r:.100}"
            )
        self._append({"op": "update_status", "job_id": job_id, "status": status})

    def _append(self, record: dict[str, Any]) -> None:
        with self._store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _replay(self) -> dict[str, DelegationJob]:
        """Replay the JSONL log and return the current state per job_id."""

        jobs: dict[str, DelegationJob] = {}
        if not self._store_path.exists():
            return jobs
        with self._store_path.open(encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    # Incomplete trailing record from crash mid-write; discard.
                    continue
                if not isinstance(record, dict):
                    continue
                op = record.get("op")
                if op == "create":
                    fields = {
                        k: record[k]
                        for k in DelegationJob.__dataclass_fields__
                        if k in record
                    }
                    tuple_fields = ("artifact_paths",)
                    for field_name in tuple_fields:
                        if field_name in fields and isinstance(
                            fields[field_name], list
                        ):
                            fields[field_name] = tuple(fields[field_name])
                    try:
                        jobs[record["job_id"]] = DelegationJob(**fields)
                    except TypeError:
                        continue
                elif op == "update_status":
                    job_id = record.get("job_id")
                    status = record.get("status")
                    if not isinstance(job_id, str) or not isinstance(status, str):
                        continue
                    if job_id not in jobs:
                        continue
                    existing = jobs[job_id]
                    jobs[job_id] = DelegationJob(
                        **{**asdict(existing), "status": status}
                    )
        return jobs
```

- [ ] **Step 2.4: Run tests and full plugin suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_job_store.py -v && uv run pytest tests/ -q
```
Expected: 8 new store tests pass; plugin suite `~612 passed` (604 + 8).

- [ ] **Step 2.5: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/server/delegation_job_store.py packages/plugins/codex-collaboration/tests/test_delegation_job_store.py
git commit -m "feat(t20260330-05): add DelegationJobStore (session-scoped JSONL)"
```

---

## Task 3: WorktreeManager

**Goal:** Thin wrapper around `git worktree add --detach` with fail-fast error propagation. One-shot creation; no cleanup in this slice (tracked for later).

**Files:**
- Create: `packages/plugins/codex-collaboration/server/worktree_manager.py`
- Create: `packages/plugins/codex-collaboration/tests/test_worktree_manager.py`

- [ ] **Step 3.1: Write failing tests**

Create `packages/plugins/codex-collaboration/tests/test_worktree_manager.py`:

```python
"""Tests for WorktreeManager — isolated worktree creation."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from server.worktree_manager import WorktreeManager


def _init_repo(repo_path: Path) -> str:
    """Init a tmp git repo with one commit. Returns the HEAD SHA."""

    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
    )
    (repo_path / "README.md").write_text("hello\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_create_worktree_at_expected_base_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    wk_path = tmp_path / "workspaces" / "wk-1"

    mgr = WorktreeManager()
    mgr.create_worktree(repo_root=repo, base_commit=head, worktree_path=wk_path)

    assert wk_path.exists()
    assert (wk_path / "README.md").exists()
    # Worktree is in detached HEAD at the expected commit.
    wk_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=wk_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert wk_head == head


def test_create_worktree_fails_fast_on_unknown_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    wk_path = tmp_path / "workspaces" / "wk-1"

    mgr = WorktreeManager()
    with pytest.raises(RuntimeError, match="worktree add failed"):
        mgr.create_worktree(
            repo_root=repo,
            base_commit="0" * 40,
            worktree_path=wk_path,
        )


def test_create_worktree_fails_fast_if_path_exists(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    wk_path = tmp_path / "workspaces" / "wk-1"
    wk_path.mkdir(parents=True)
    (wk_path / "preexisting.txt").write_text("do not overwrite me")

    mgr = WorktreeManager()
    with pytest.raises(RuntimeError, match="worktree add failed"):
        mgr.create_worktree(repo_root=repo, base_commit=head, worktree_path=wk_path)
```

- [ ] **Step 3.2: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_worktree_manager.py -v
```
Expected: `ImportError: No module named 'server.worktree_manager'`.

- [ ] **Step 3.3: Implement WorktreeManager**

Create `packages/plugins/codex-collaboration/server/worktree_manager.py`:

```python
"""Isolated git worktree creation for delegation jobs.

See foundations.md §Execution Domain — one ephemeral worktree per job,
created from a specific base commit, in detached-HEAD state (no branch
pollution). Cleanup is deferred to the promotion slice.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class WorktreeManager:
    """Creates isolated git worktrees via `git worktree add --detach`."""

    def create_worktree(
        self,
        *,
        repo_root: Path,
        base_commit: str,
        worktree_path: Path,
    ) -> None:
        """Create a detached-HEAD worktree at `worktree_path` from `base_commit`.

        Fails fast on any git error. The parent directory of `worktree_path`
        is created if it does not exist; the leaf directory must not exist.
        """

        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "worktree",
                    "add",
                    "--detach",
                    str(worktree_path),
                    base_commit,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                "worktree add failed: git returned non-zero. "
                f"Got: {(exc.stderr or exc.stdout).strip()!r:.200}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"worktree add failed: git timed out. Got: {worktree_path!r:.100}"
            ) from exc
```

- [ ] **Step 3.4: Run tests and full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_worktree_manager.py -v && uv run pytest tests/ -q
```
Expected: 3 new tests pass; plugin suite `~615 passed` (612 + 3).

- [ ] **Step 3.5: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/server/worktree_manager.py packages/plugins/codex-collaboration/tests/test_worktree_manager.py
git commit -m "feat(t20260330-05): add WorktreeManager (git worktree add --detach)"
```

---

## Task 4: ControlPlane.start_execution_runtime

**Goal:** New non-cached runtime bootstrap path that brings up an ephemeral `AppServerRuntimeSession` at a worktree path, runs `initialize` + `account/read`, and starts a thread. Returns `(runtime_id, session, thread_id)`. Does NOT dispatch a turn.

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/control_plane.py`
- Test: `packages/plugins/codex-collaboration/tests/test_control_plane.py` (append)

- [ ] **Step 4.1: Write failing tests**

Append to `packages/plugins/codex-collaboration/tests/test_control_plane.py`:

```python
class TestStartExecutionRuntime:
    """Execution runtime bootstrap — non-cached, fresh-per-call.

    This path is the inner substrate that codex.delegate.start will use.
    It does NOT dispatch a turn. It stops at thread creation.
    """

    def _make_compat_result(self) -> object:
        from server.codex_compat import REQUIRED_METHODS

        class _Result:
            passed = True
            codex_version = "0.117.0"
            available_methods = REQUIRED_METHODS
            errors: tuple[str, ...] = ()

        return _Result()

    def test_start_execution_runtime_returns_runtime_id_session_and_thread(
        self, tmp_path: Path
    ) -> None:
        from server.control_plane import ControlPlane
        from server.models import AccountState, RuntimeHandshake

        worktree = tmp_path / "wk"
        worktree.mkdir()

        class _FakeSession:
            def __init__(self) -> None:
                self.closed = False

            def initialize(self) -> RuntimeHandshake:
                return RuntimeHandshake(
                    codex_home="/fake/home",
                    platform_family="unix",
                    platform_os="darwin",
                    user_agent="codex/0.117.0",
                )

            def read_account(self) -> AccountState:
                return AccountState(
                    auth_status="authenticated",
                    account_type="test",
                    requires_openai_auth=False,
                )

            def start_thread(self) -> str:
                return "thr-execution-1"

            def close(self) -> None:
                self.closed = True

        fake_session = _FakeSession()
        created_for: list[Path] = []

        def factory(cwd: Path) -> object:
            created_for.append(cwd)
            return fake_session

        plane = ControlPlane(
            plugin_data_path=tmp_path / "data",
            runtime_factory=factory,  # type: ignore[arg-type]
            compat_checker=self._make_compat_result,
            uuid_factory=lambda: "rt-exec-1",
        )

        runtime_id, session, thread_id = plane.start_execution_runtime(worktree)

        assert runtime_id == "rt-exec-1"
        assert session is fake_session
        assert thread_id == "thr-execution-1"
        # The session was constructed against the worktree path, not the repo root.
        assert created_for == [worktree]

    def test_start_execution_runtime_does_not_cache(self, tmp_path: Path) -> None:
        """Two calls return two distinct sessions — no advisory-style caching."""

        from server.control_plane import ControlPlane
        from server.models import AccountState, RuntimeHandshake

        worktree = tmp_path / "wk"
        worktree.mkdir()

        created: list[object] = []

        class _FakeSession:
            def __init__(self) -> None:
                created.append(self)

            def initialize(self) -> RuntimeHandshake:
                return RuntimeHandshake(
                    codex_home="/h", platform_family="u",
                    platform_os="d", user_agent="ua",
                )

            def read_account(self) -> AccountState:
                return AccountState(
                    auth_status="authenticated",
                    account_type="test",
                    requires_openai_auth=False,
                )

            def start_thread(self) -> str:
                return "thr"

            def close(self) -> None:
                pass

        plane = ControlPlane(
            plugin_data_path=tmp_path / "data",
            runtime_factory=lambda _: _FakeSession(),  # type: ignore[arg-type]
            compat_checker=self._make_compat_result,
        )

        plane.start_execution_runtime(worktree)
        plane.start_execution_runtime(worktree)

        assert len(created) == 2

    def test_start_execution_runtime_fails_when_auth_missing(
        self, tmp_path: Path
    ) -> None:
        from server.control_plane import ControlPlane
        from server.models import AccountState, RuntimeHandshake

        worktree = tmp_path / "wk"
        worktree.mkdir()

        class _FakeSession:
            def initialize(self) -> RuntimeHandshake:
                return RuntimeHandshake(
                    codex_home="/h", platform_family="u",
                    platform_os="d", user_agent="ua",
                )

            def read_account(self) -> AccountState:
                return AccountState(
                    auth_status="missing",
                    account_type=None,
                    requires_openai_auth=True,
                )

            def start_thread(self) -> str:
                return "thr"

            def close(self) -> None:
                pass

        plane = ControlPlane(
            plugin_data_path=tmp_path / "data",
            runtime_factory=lambda _: _FakeSession(),  # type: ignore[arg-type]
            compat_checker=self._make_compat_result,
        )

        with pytest.raises(RuntimeError, match="auth unavailable"):
            plane.start_execution_runtime(worktree)
```

If `pytest` is not yet imported in `test_control_plane.py`, confirm the existing imports cover `pytest` and `Path`. If not, add `import pytest` and `from pathlib import Path` at the top.

- [ ] **Step 4.2: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_control_plane.py::TestStartExecutionRuntime -v
```
Expected: 3 tests fail with `AttributeError: 'ControlPlane' object has no attribute 'start_execution_runtime'`.

- [ ] **Step 4.3: Implement start_execution_runtime**

In `packages/plugins/codex-collaboration/server/control_plane.py`, add this method to the `ControlPlane` class (place it after `get_advisory_runtime`, near line 263):

```python
    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, AppServerRuntimeSession, str]:
        """Bootstrap a fresh ephemeral execution runtime at ``worktree_path``.

        Returns ``(runtime_id, session, thread_id)``. This path does NOT
        cache the session — each call constructs a new runtime. The caller
        is responsible for session lifetime (close on job completion or
        crash recovery).

        No turn is dispatched here. Thread creation prepares the runtime
        for a future ``run_execution_turn`` call by a follow-up slice.
        """

        resolved_worktree = worktree_path.resolve()
        compat_result = self._compat_checker()
        if not getattr(compat_result, "passed", False):
            raise RuntimeError(
                "Execution runtime bootstrap failed: compatibility checks failed. "
                f"Got: {getattr(compat_result, 'errors', ())!r:.200}"
            )

        session = self._runtime_factory(resolved_worktree)
        try:
            session.initialize()
        except Exception as exc:
            session.close()
            raise RuntimeError(
                "Execution runtime bootstrap failed: initialize failed. "
                f"Got: {str(exc)!r:.100}"
            ) from exc
        try:
            account_state = session.read_account()
        except Exception as exc:
            session.close()
            raise RuntimeError(
                "Execution runtime bootstrap failed: account/read failed. "
                f"Got: {str(exc)!r:.100}"
            ) from exc
        if account_state.auth_status != "authenticated":
            session.close()
            raise RuntimeError(
                "Execution runtime bootstrap failed: auth unavailable. "
                f"Got: {account_state.auth_status!r:.100}"
            )
        try:
            thread_id = session.start_thread()
        except Exception as exc:
            session.close()
            raise RuntimeError(
                "Execution runtime bootstrap failed: thread/start failed. "
                f"Got: {str(exc)!r:.100}"
            ) from exc

        runtime_id = self._uuid_factory()
        return runtime_id, session, thread_id
```

- [ ] **Step 4.4: Run tests and full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_control_plane.py::TestStartExecutionRuntime -v && uv run pytest tests/ -q
```
Expected: 3 new tests pass; plugin suite `~618 passed` (615 + 3).

- [ ] **Step 4.5: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/server/control_plane.py packages/plugins/codex-collaboration/tests/test_control_plane.py
git commit -m "feat(t20260330-05): add ControlPlane.start_execution_runtime (no turn dispatch)"
```

---

## Task 5: ExecutionRuntimeRegistry

**Goal:** In-process live-ownership registry for execution runtimes, keyed by `runtime_id`. Solves the orphan-runtime problem inside a live control-plane process. **Not** a crash-durability layer — that role belongs to `LineageStore` + `DelegationJobStore` + `OperationJournal`, which are populated by the controller in Task 6.

**Files:**
- Create: `packages/plugins/codex-collaboration/server/execution_runtime_registry.py`
- Create: `packages/plugins/codex-collaboration/tests/test_execution_runtime_registry.py`

- [ ] **Step 5.1: Write failing tests**

Create `packages/plugins/codex-collaboration/tests/test_execution_runtime_registry.py`:

```python
"""Tests for ExecutionRuntimeRegistry — live-ownership table only, not durability."""

from __future__ import annotations

import pytest

from server.execution_runtime_registry import (
    ExecutionRuntimeEntry,
    ExecutionRuntimeRegistry,
)


class _FakeSession:
    """Minimal session stand-in — the registry only retains it, doesn't call into it."""

    def __init__(self, name: str = "sess") -> None:
        self.name = name


def test_register_and_lookup_round_trip() -> None:
    registry = ExecutionRuntimeRegistry()
    session = _FakeSession("s1")
    registry.register(
        runtime_id="rt-1",
        session=session,  # type: ignore[arg-type]
        thread_id="thr-1",
        job_id="job-1",
    )

    entry = registry.lookup("rt-1")
    assert entry is not None
    assert isinstance(entry, ExecutionRuntimeEntry)
    assert entry.runtime_id == "rt-1"
    assert entry.session is session
    assert entry.thread_id == "thr-1"
    assert entry.job_id == "job-1"


def test_lookup_of_unknown_runtime_returns_none() -> None:
    registry = ExecutionRuntimeRegistry()
    assert registry.lookup("nope") is None


def test_register_rejects_duplicate_runtime_id() -> None:
    registry = ExecutionRuntimeRegistry()
    registry.register(
        runtime_id="rt-1",
        session=_FakeSession("a"),  # type: ignore[arg-type]
        thread_id="thr-1",
        job_id="job-1",
    )
    with pytest.raises(RuntimeError, match="already registered"):
        registry.register(
            runtime_id="rt-1",
            session=_FakeSession("b"),  # type: ignore[arg-type]
            thread_id="thr-1b",
            job_id="job-1b",
        )


def test_release_removes_entry_and_returns_it() -> None:
    registry = ExecutionRuntimeRegistry()
    session = _FakeSession("s1")
    registry.register(
        runtime_id="rt-1",
        session=session,  # type: ignore[arg-type]
        thread_id="thr-1",
        job_id="job-1",
    )

    released = registry.release("rt-1")
    assert released is not None
    assert released.session is session
    assert registry.lookup("rt-1") is None


def test_release_of_unknown_runtime_is_a_noop_returning_none() -> None:
    registry = ExecutionRuntimeRegistry()
    assert registry.release("nope") is None


def test_active_runtime_ids_reflects_live_state() -> None:
    registry = ExecutionRuntimeRegistry()
    registry.register(
        runtime_id="rt-1",
        session=_FakeSession("a"),  # type: ignore[arg-type]
        thread_id="thr-1",
        job_id="job-1",
    )
    registry.register(
        runtime_id="rt-2",
        session=_FakeSession("b"),  # type: ignore[arg-type]
        thread_id="thr-2",
        job_id="job-2",
    )
    assert set(registry.active_runtime_ids()) == {"rt-1", "rt-2"}

    registry.release("rt-1")
    assert set(registry.active_runtime_ids()) == {"rt-2"}
```

- [ ] **Step 5.2: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_execution_runtime_registry.py -v
```
Expected: `ImportError: No module named 'server.execution_runtime_registry'`.

- [ ] **Step 5.3: Implement ExecutionRuntimeRegistry**

Create `packages/plugins/codex-collaboration/server/execution_runtime_registry.py`:

```python
"""In-process live-ownership registry for execution runtimes.

Solves the orphan-runtime problem WITHIN a live control-plane process.
Does NOT provide crash durability — if the control plane dies, the registry
is lost. Crash recovery is handled by replaying:

    LineageStore        -> CollaborationHandle records (identity/routing)
    DelegationJobStore  -> DelegationJob records (job lifecycle)
    OperationJournal    -> job_creation phase records (replay safety)

Keep this file small on purpose. It is not a control plane; it is a table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionRuntimeEntry:
    """Live-ownership record for one execution runtime."""

    runtime_id: str
    session: Any  # AppServerRuntimeSession — Any to avoid import cycle
    thread_id: str
    job_id: str


class ExecutionRuntimeRegistry:
    """In-process registry mapping runtime_id -> live session/thread/job."""

    def __init__(self) -> None:
        self._entries: dict[str, ExecutionRuntimeEntry] = {}

    def register(
        self,
        *,
        runtime_id: str,
        session: Any,
        thread_id: str,
        job_id: str,
    ) -> None:
        """Register a live runtime. Rejects duplicate runtime_id.

        The controller calls this as the FIRST committed-start write,
        IMMEDIATELY after ``journal.write_phase(dispatched)`` and BEFORE
        any other durable local write (lineage, job, audit, journal-completed).
        Rationale: the runtime subprocess is already live by this point, and
        the in-process registry is what makes it reachable for later turn
        dispatch, close, and crash-to-``unknown`` paths. If any subsequent
        local write fails without the runtime having been registered first,
        the subprocess is unreachable and the busy gate's registry branch
        cannot block a same-session retry — recreating the orphan-runtime
        bug. See ``DelegationController.start`` docstring and the
        ``Write ordering invariant`` block for the full rationale.

        A duplicate here indicates a programming error (two callers thinking
        they own the same ``runtime_id``). Runtime ids are uuid-generated so
        collision is structurally impossible in practice; the error surface
        is retained for test monkeypatching and defensive correctness.
        """

        if runtime_id in self._entries:
            raise RuntimeError(
                "ExecutionRuntimeRegistry.register failed: runtime_id already "
                f"registered. Got: {runtime_id!r:.100}"
            )
        self._entries[runtime_id] = ExecutionRuntimeEntry(
            runtime_id=runtime_id,
            session=session,
            thread_id=thread_id,
            job_id=job_id,
        )

    def lookup(self, runtime_id: str) -> ExecutionRuntimeEntry | None:
        """Return the entry for a live runtime, or None if not registered."""

        return self._entries.get(runtime_id)

    def release(self, runtime_id: str) -> ExecutionRuntimeEntry | None:
        """Remove and return the entry for a runtime, or None if not registered.

        The caller is responsible for any session teardown. This method is
        intentionally tear-down-agnostic so the v1 slice does not depend on
        a stable ``session.close()`` contract. Follow-up slices add teardown
        wiring alongside poll/promote.
        """

        return self._entries.pop(runtime_id, None)

    def active_runtime_ids(self) -> tuple[str, ...]:
        """Snapshot of currently-registered runtime ids."""

        return tuple(self._entries.keys())
```

- [ ] **Step 5.4: Run tests and full plugin suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_execution_runtime_registry.py -v && uv run pytest tests/ -q
```
Expected: 6 new tests pass; plugin suite `~624 passed` (618 + 6).

- [ ] **Step 5.5: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/server/execution_runtime_registry.py packages/plugins/codex-collaboration/tests/test_execution_runtime_registry.py
git commit -m "feat(t20260330-05): add ExecutionRuntimeRegistry for live runtime ownership"
```

---

## Task 6: DelegationController

**Goal:** Orchestrator for `codex.delegate.start`. Mirrors `dialogue.py::DialogueController.start` three-phase discipline; the registry-FIRST committed-start ordering is delegation-specific (4-5 post-`dispatched` writes vs dialogue's 1, so the in-process ownership table needs to populate before any of them can fail). Flow: busy check (job_store + registry + unresolved journal) → base-commit resolve → idempotency-key compute → **journal intent** → worktree create → runtime bootstrap → **journal dispatched** → `ExecutionRuntimeRegistry.register` (FIRST committed-start write) → persist `CollaborationHandle` in `LineageStore` → persist `DelegationJob` in `DelegationJobStore` → audit emit → **journal completed** (LAST). Returns persisted `DelegationJob` or `JobBusyResponse`.

**Committed-start failure semantics.** Failures before the `dispatched` journal write propagate as raw exceptions (no durable state, no audit — covered by `test_start_does_not_persist_durable_state_on_bootstrap_failure`). Failures **after** the `dispatched` journal write are treated as a committed-start finalization defect, mirroring `dialogue.py:361-373` committed-turn finalization (adapted for delegation's wider blast radius). The controller catches the failure, best-effort marks any persisted `CollaborationHandle` and/or `DelegationJob` with `status="unknown"`, leaves the journal at the `dispatched` phase so startup reconciliation (Task 7) will close the record on next session init, and raises `CommittedStartFinalizationError` with caller guidance that blind retry will create a duplicate job. The busy gate consults `runtime_registry.active_runtime_ids()` so any same-session retry is rejected for the lineage / job / audit / journal-completed failure modes (where registry was successfully populated). For the `runtime_registry.register` failure mode itself, no entry exists to retain; the journal-consultation branch of the busy gate covers retry rejection until `recover_startup()` runs at next session init. Covered by FIVE failure tests: register failure, lineage-store failure, job-store failure, audit-append failure, journal-completed write failure. Two additional busy-gate widening tests cover the registry-only and journal-only retry-block paths.

**Files:**
- Create: `packages/plugins/codex-collaboration/server/delegation_controller.py`
- Create: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`

- [ ] **Step 6.1: Write failing tests**

Create `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`:

```python
"""Tests for DelegationController — mirrors dialogue pattern.

Verifies every durable surface is populated AND the in-process registry
retains the session so the runtime remains controllable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from server.delegation_controller import DelegationController
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import (
    AccountState,
    CollaborationHandle,
    DelegationJob,
    JobBusyResponse,
    RuntimeHandshake,
)


class _FakeSession:
    def __init__(self, thread_id: str = "thr-1") -> None:
        self._thread_id = thread_id
        self.closed = False

    def initialize(self) -> RuntimeHandshake:
        return RuntimeHandshake(
            codex_home="/h",
            platform_family="u",
            platform_os="d",
            user_agent="codex/test",
        )

    def read_account(self) -> AccountState:
        return AccountState(
            auth_status="authenticated",
            account_type="t",
            requires_openai_auth=False,
        )

    def start_thread(self) -> str:
        return self._thread_id

    def close(self) -> None:
        self.closed = True


class _FakeControlPlane:
    def __init__(self) -> None:
        self.calls: list[Path] = []
        self._next_runtime_id = 0
        self._sessions: list[_FakeSession] = []

    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, _FakeSession, str]:
        self.calls.append(worktree_path)
        self._next_runtime_id += 1
        session = _FakeSession(thread_id=f"thr-{self._next_runtime_id}")
        self._sessions.append(session)
        return f"rt-{self._next_runtime_id}", session, session._thread_id


class _FakeWorktreeManager:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, str, Path]] = []

    def create_worktree(
        self, *, repo_root: Path, base_commit: str, worktree_path: Path
    ) -> None:
        self.calls.append((repo_root, base_commit, worktree_path))
        worktree_path.mkdir(parents=True, exist_ok=True)


def _build_controller(
    tmp_path: Path,
    *,
    head_sha: str = "head-abc",
    session_id: str = "sess-1",
) -> tuple[
    DelegationController,
    _FakeControlPlane,
    _FakeWorktreeManager,
    DelegationJobStore,
    LineageStore,
    OperationJournal,
    ExecutionRuntimeRegistry,
]:
    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    job_store = DelegationJobStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    journal = OperationJournal(plugin_data)
    control_plane = _FakeControlPlane()
    worktree_manager = _FakeWorktreeManager()
    registry = ExecutionRuntimeRegistry()
    uuid_counter = iter(
        ["job-1", "collab-1", "evt-1", "job-2", "collab-2", "evt-2"]
    )
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=worktree_manager,
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data,
        head_commit_resolver=lambda repo_root: head_sha,
        uuid_factory=lambda: next(uuid_counter),
    )
    return (
        controller,
        control_plane,
        worktree_manager,
        job_store,
        lineage_store,
        journal,
        registry,
    )


def test_start_creates_worktree_runtime_and_persists_job(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        control_plane,
        worktree_manager,
        job_store,
        _lineage,
        _journal,
        _registry,
    ) = _build_controller(tmp_path)

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-1"
    assert result.base_commit == "head-abc"
    assert result.status == "queued"
    assert result.promotion_state == "pending"
    # Worktree was created under the plugin data dir at the job's path.
    assert len(worktree_manager.calls) == 1
    recorded_repo, recorded_commit, recorded_wk = worktree_manager.calls[0]
    assert recorded_repo == repo_root
    assert recorded_commit == "head-abc"
    assert str(recorded_wk).endswith("/runtimes/delegation/job-1/worktree")
    # The controller bootstrapped exactly one runtime against that worktree.
    assert control_plane.calls == [recorded_wk]
    # Job is persisted.
    persisted = job_store.get("job-1")
    assert persisted is not None
    assert persisted.runtime_id == "rt-1"
    assert persisted.worktree_path == str(recorded_wk)


def test_start_persists_execution_collaboration_handle(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, lineage, _j, _r = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    handle = lineage.get("collab-1")
    assert isinstance(handle, CollaborationHandle)
    assert handle.capability_class == "execution"
    assert handle.runtime_id == "rt-1"
    assert handle.codex_thread_id == "thr-1"
    assert handle.claude_session_id == "sess-1"
    assert handle.status == "active"


def test_start_writes_three_phase_journal_records(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    # Idempotency key is claude_session_id + delegation_request_hash.
    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
    ).hexdigest()
    key = f"sess-1:{request_hash}"

    terminal = journal.check_idempotency(key, session_id="sess-1")
    assert terminal is not None, "terminal phase should be completed"
    assert terminal.phase == "completed"
    assert terminal.operation == "job_creation"
    assert terminal.job_id == "job-1"

    # Inspect the raw journal file for all three phases.
    path = journal._operations_path("sess-1")
    records = [
        json.loads(line) for line in path.read_text().splitlines() if line.strip()
    ]
    phases = [r["phase"] for r in records if r["idempotency_key"] == key]
    assert phases == ["intent", "dispatched", "completed"]


def test_start_registers_runtime_ownership(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        control_plane,
        _wm,
        _js,
        _ls,
        _j,
        registry,
    ) = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    entry = registry.lookup("rt-1")
    assert entry is not None
    assert entry.job_id == "job-1"
    assert entry.thread_id == "thr-1"
    # The registered session is the SAME object the control plane returned.
    assert entry.session is control_plane._sessions[0]


def test_start_emits_delegate_start_audit_event(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    events_path = journal.plugin_data_path / "audit" / "events.jsonl"
    assert events_path.exists()

    lines = [
        json.loads(line)
        for line in events_path.read_text().splitlines()
        if line.strip()
    ]
    delegate_events = [e for e in lines if e.get("action") == "delegate_start"]
    assert len(delegate_events) == 1
    event = delegate_events[0]
    assert event["actor"] == "claude"
    assert event["collaboration_id"] == "collab-1"
    assert event["job_id"] == "job-1"
    assert event["runtime_id"] == "rt-1"


def test_start_uses_caller_provided_base_commit(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, worktree_manager, _js, _ls, _j, _r = _build_controller(tmp_path)

    controller.start(repo_root=repo_root, base_commit="explicit-sha")

    assert worktree_manager.calls[0][1] == "explicit-sha"


def test_start_returns_busy_response_when_active_job_exists(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, _j, _r = _build_controller(tmp_path)

    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationJob)

    second = controller.start(repo_root=repo_root)
    assert isinstance(second, JobBusyResponse)
    assert second.busy is True
    assert second.active_job_id == "job-1"
    assert second.active_job_status == "queued"


def test_start_does_not_persist_durable_state_on_bootstrap_failure(
    tmp_path: Path,
) -> None:
    """If runtime bootstrap raises, no durable state remains and no audit emitted.

    The journal may record an ``intent`` phase (that is correct per the journal-
    before-dispatch contract), but no ``dispatched`` / ``completed`` phase, no
    handle in lineage, no job in job store, no registry entry, no audit event.
    """

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    job_store = DelegationJobStore(plugin_data, "sess-1")
    lineage_store = LineageStore(plugin_data, "sess-1")
    journal = OperationJournal(plugin_data)
    registry = ExecutionRuntimeRegistry()
    worktree_manager = _FakeWorktreeManager()

    class _FailingControlPlane:
        def start_execution_runtime(self, worktree_path: Path) -> tuple:
            raise RuntimeError("Execution runtime bootstrap failed: test forced")

    uuid_counter = iter(["job-1", "collab-1", "evt-1"])
    controller = DelegationController(
        control_plane=_FailingControlPlane(),  # type: ignore[arg-type]
        worktree_manager=worktree_manager,
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id="sess-1",
        plugin_data_path=plugin_data,
        head_commit_resolver=lambda _: "head-abc",
        uuid_factory=lambda: next(uuid_counter),
    )

    with pytest.raises(RuntimeError, match="Execution runtime bootstrap failed"):
        controller.start(repo_root=repo_root)

    assert job_store.get("job-1") is None
    assert lineage_store.get("collab-1") is None
    assert registry.lookup("rt-1") is None
    audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
    if audit_path.exists():
        content = audit_path.read_text()
        assert "delegate_start" not in content


# -----------------------------------------------------------------------------
# Committed-start failure semantics — post-dispatched local-write failures.
#
# Each of these tests verifies that when a write after the ``dispatched`` journal
# phase fails, the controller: (1) does NOT write the ``completed`` journal phase
# (leaves it for startup reconciliation), (2) best-effort marks persisted handle
# and/or job as ``unknown``, and (3) raises CommittedStartFinalizationError with
# caller-facing no-retry guidance.
# -----------------------------------------------------------------------------


def _assert_dispatched_but_not_completed(
    journal: OperationJournal, session_id: str, request_hash: str
) -> None:
    """Helper: assert journal has intent + dispatched but NOT completed for job."""
    key = f"{session_id}:{request_hash}"
    path = journal._operations_path(session_id)
    records = [
        json.loads(line) for line in path.read_text().splitlines() if line.strip()
    ]
    phases = [r["phase"] for r in records if r["idempotency_key"] == key]
    assert "intent" in phases
    assert "dispatched" in phases
    assert "completed" not in phases, (
        "journal must stay at dispatched for startup reconciliation to close it"
    )


def test_start_raises_committed_start_finalization_error_on_lineage_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """LineageStore.create failure after dispatched: partial state, no completed."""

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("lineage_store.create boom")

    monkeypatch.setattr(lineage_store, "create", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Registry HAS the entry — register goes FIRST in the try block, before
    # lineage. The runtime subprocess is reachable in-process for the rest
    # of the session and the busy gate's registry consultation blocks retry.
    assert registry.lookup("rt-1") is not None
    # Nothing persisted downstream of the failure.
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None


def test_start_raises_committed_start_finalization_error_on_job_store_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DelegationJobStore.create failure after dispatched: handle marked unknown."""

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("job_store.create boom")

    monkeypatch.setattr(job_store, "create", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Registry HAS the entry — register goes FIRST in the try block.
    assert registry.lookup("rt-1") is not None
    # Handle WAS written before the failure — must be marked unknown.
    handle = lineage_store.get("collab-1")
    assert handle is not None
    assert handle.status == "unknown"
    # Job was NOT written.
    assert job_store.get("job-1") is None


def test_start_raises_committed_start_finalization_error_on_journal_completed_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """journal.write_phase(completed) failure: handle + job marked unknown."""

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    # Let intent + dispatched succeed; fail on the completed phase.
    real_write_phase = journal.write_phase
    calls: list[str] = []

    def _selective_boom(entry: OperationJournalEntry, *, session_id: str) -> None:
        calls.append(entry.phase)
        if entry.phase == "completed":
            raise OSError("journal.write_phase(completed) boom")
        real_write_phase(entry, session_id=session_id)

    monkeypatch.setattr(journal, "write_phase", _selective_boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    assert calls == ["intent", "dispatched", "completed"]
    # No completed in the file either — the selective_boom ensured it.
    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Both handle and job were written before the failure — both must be unknown.
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    # Registry registration happens before the completed phase — entry present.
    assert registry.lookup("rt-1") is not None


def test_start_raises_committed_start_finalization_error_on_audit_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """journal.append_audit_event failure: handle + job marked unknown, journal at dispatched.

    Flow order in Step 6.3 places append_audit_event BEFORE journal.write_phase(completed)
    so the journal-at-dispatched invariant holds for all five committed-start failure modes
    (register / lineage / job / audit / journal-completed).
    """

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("audit boom")

    monkeypatch.setattr(journal, "append_audit_event", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Handle, job, and registry entry were all created before the audit failure.
    # All must be marked unknown (or released in the registry's case — see policy note below).
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    # Registry entry stays (runtime subprocess is live; releasing it would leak
    # the subprocess). Recovery policy: the unknown status on handle+job is the
    # authoritative signal; the live runtime remains reachable via registry.lookup
    # for a subsequent teardown pass in poll/promote slices.
    assert registry.lookup("rt-1") is not None


def test_start_raises_committed_start_finalization_error_on_register_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ExecutionRuntimeRegistry.register failure: no entry, no handle, no job.

    Register is the FIRST committed-start write — if it raises, no other
    durable state has been touched yet. The runtime subprocess is live but
    unreachable from the in-process registry; the journal is at dispatched
    so reconciliation will close it on next session init. The subprocess
    leaks until the parent process exits (no entry to release; teardown via
    subprocess discovery is out of scope).
    """

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("registry.register boom")

    monkeypatch.setattr(registry, "register", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Register itself failed — no entry, and downstream writes never started.
    assert registry.lookup("rt-1") is None
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None


# -----------------------------------------------------------------------------
# Busy-gate widening: the gate consults THREE sources (job_store, registry,
# unresolved job_creation journal entries). The two tests below cover the new
# sources; existing tests already cover the job_store-only case.
# -----------------------------------------------------------------------------


def test_start_returns_busy_when_registry_has_entry_but_job_store_empty(
    tmp_path: Path,
) -> None:
    """Same-session retry after committed-start lineage failure: registry-based busy.

    Simulates the post-lineage-failure state directly: a registered runtime
    with no DelegationJob in the store. The busy gate must consult the
    registry and reject the second start, otherwise blind retry would spawn
    a duplicate runtime subprocess.
    """

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _job_store, _lineage_store, _journal, registry = (
        _build_controller(tmp_path)
    )

    fake_session = object()
    registry.register(
        runtime_id="rt-prior",
        session=fake_session,
        thread_id="thread-prior",
        job_id="job-prior",
    )

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, JobBusyResponse)
    assert result.busy is True
    assert result.active_job_id == "job-prior"


def test_start_returns_busy_when_unresolved_journal_entry_present(
    tmp_path: Path,
) -> None:
    """Cross-session committed-start residue: journal-based busy.

    Simulates a fresh session where the in-process registry is empty but the
    journal still has a dispatched job_creation record from a prior process.
    The busy gate must consult unresolved journal entries (filtered by
    operation == "job_creation") and reject the second start until
    recover_startup() reconciles it.
    """

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _job_store, _lineage_store, journal, _registry = (
        _build_controller(tmp_path)
    )

    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="sess-1:prior-hash",
            operation="job_creation",
            phase="intent",
            collaboration_id="collab-prior",
            created_at="2026-01-01T00:00:00Z",
            repo_root=str(repo_root.resolve()),
            job_id="job-prior",
        ),
        session_id="sess-1",
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="sess-1:prior-hash",
            operation="job_creation",
            phase="dispatched",
            collaboration_id="collab-prior",
            created_at="2026-01-01T00:00:00Z",
            repo_root=str(repo_root.resolve()),
            job_id="job-prior",
            runtime_id="rt-prior",
            codex_thread_id="thread-prior",
        ),
        session_id="sess-1",
    )

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, JobBusyResponse)
    assert result.busy is True
    assert result.active_job_id == "job-prior"
```

- [ ] **Step 6.2: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_controller.py -v
```
Expected: `ImportError: No module named 'server.delegation_controller'`.

- [ ] **Step 6.3: Implement DelegationController**

Create `packages/plugins/codex-collaboration/server/delegation_controller.py`:

```python
"""Controller for codex.delegate.start.

Mirrors dialogue.py::DialogueController.start three-phase discipline. Flow:

    busy check (job_store.list_active + registry.active_runtime_ids
        + unresolved job_creation journal entries)
    resolve base commit
    compute idempotency key (claude_session_id + delegation_request_hash)
    journal Phase 1: intent (before any side effects)
    create worktree
    bootstrap execution runtime
    journal Phase 2: dispatched (runtime_id + codex_thread_id recorded)
    register runtime ownership in ExecutionRuntimeRegistry (FIRST committed-start
        write — establishes in-process ownership before any fallible local write)
    persist CollaborationHandle in LineageStore (identity/routing)
    persist DelegationJob in DelegationJobStore (job lifecycle)
    emit delegate_start audit event (BEFORE journal completed; "journal at
        dispatched" is the universal terminal state for committed-start failures)
    journal Phase 3: completed (terminal write)

This slice does NOT dispatch execution turns. The controller stops at
journal.write_phase(completed). Callers receive a queued job record with
a live runtime whose session is retained by the registry so follow-up
turn dispatch can find it via ExecutionRuntimeRegistry.lookup(runtime_id).
"""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from pathlib import Path
from typing import Callable, Protocol

from .delegation_job_store import DelegationJobStore
from .execution_runtime_registry import ExecutionRuntimeRegistry
from .journal import OperationJournal
from .lineage_store import LineageStore
from .models import (
    AuditEvent,
    CollaborationHandle,
    DelegationJob,
    JobBusyResponse,
    OperationJournalEntry,
)
from .runtime import AppServerRuntimeSession


class _ControlPlaneLike(Protocol):
    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, AppServerRuntimeSession, str]:
        ...


class _WorktreeManagerLike(Protocol):
    def create_worktree(
        self, *, repo_root: Path, base_commit: str, worktree_path: Path
    ) -> None:
        ...


def _resolve_head_commit(repo_root: Path) -> str:
    """Default head-commit resolver — `git rev-parse HEAD` in repo_root."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Delegation start failed: could not resolve HEAD. "
            f"Got: {(exc.stderr or exc.stdout).strip()!r:.200}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Delegation start failed: git rev-parse HEAD timed out. "
            f"Got: {repo_root!r:.100}"
        ) from exc
    return result.stdout.strip()


def _delegation_request_hash(repo_root: Path, base_commit: str) -> str:
    """Recovery-contract idempotency component — hash of the delegation request.

    Per recovery-and-journal.md:47, the ``job_creation`` idempotency key is
    ``claude_session_id + delegation_request_hash``. The request is fully
    characterized by the resolved repo_root + base_commit pair in v1.
    """

    payload = f"{repo_root}:{base_commit}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class CommittedStartFinalizationError(RuntimeError):
    """Raised when a delegation start has committed side effects (worktree + runtime
    are live, journal-dispatched is written) but a local durable write afterwards
    fails (lineage persist, job persist, audit emit, or journal-completed write).

    Mirrors dialogue.py::CommittedTurnFinalizationError. The caller MUST NOT blindly
    retry: the worktree is live, a runtime subprocess is running, and any partially
    persisted handle or job record has been best-effort marked ``unknown``. Retrying
    ``codex.delegate.start`` will produce a duplicate job record for the same
    (repo_root, base_commit) pair because the idempotency replay path only recognizes
    a ``completed`` journal phase as terminal — which is exactly the phase this error
    guarantees was NOT written.

    Recovery path: on next session init, DelegationController.recover_startup()
    reads the unresolved job_creation journal entries (they sit at ``dispatched``)
    and advances them to ``completed`` so they are no longer returned by
    ``list_unresolved()``. Physical compaction via ``OperationJournal.compact()``
    is not invoked here. For lineage / job / audit / journal-completed failures,
    the handle and job are already best-effort marked ``unknown`` before the
    error is raised, and the registry entry is retained for the rest of the
    session; reconciliation just confirms the journal advance. For the
    ``runtime_registry.register`` failure case, no handle / job / registry
    entry was ever persisted, so reconciliation only advances the journal.
    The runtime subprocess is not reattached in any case — promote/discard
    is the caller's responsibility on the durable ``unknown`` record (or,
    for the register-failure case, no durable record at all) via future slices.
    """


class DelegationController:
    """Implements codex.delegate.start."""

    def __init__(
        self,
        *,
        control_plane: _ControlPlaneLike,
        worktree_manager: _WorktreeManagerLike,
        job_store: DelegationJobStore,
        lineage_store: LineageStore,
        runtime_registry: ExecutionRuntimeRegistry,
        journal: OperationJournal,
        session_id: str,
        plugin_data_path: Path,
        head_commit_resolver: Callable[[Path], str] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._worktree_manager = worktree_manager
        self._job_store = job_store
        self._lineage_store = lineage_store
        self._runtime_registry = runtime_registry
        self._journal = journal
        self._session_id = session_id
        self._plugin_data_path = plugin_data_path
        self._head_commit_resolver = head_commit_resolver or _resolve_head_commit
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))

    def start(
        self,
        *,
        repo_root: Path,
        base_commit: str | None = None,
    ) -> DelegationJob | JobBusyResponse:
        """Start a delegation job. Returns the job, or JobBusyResponse if busy.

        Write ordering invariant:
          1. ``runtime_registry.register`` is the FIRST committed-start write
             (immediately after ``dispatched``) so the runtime is controllable
             in-process for any subsequent failure path. Without this, a
             failure in lineage / job / audit / completed would leave a live
             subprocess with no in-process owner and the busy gate would
             clear → same-session retry would spawn a duplicate.
          2. ``journal.write_phase(completed)`` is the LAST write. If any step
             between ``dispatched`` and ``completed`` fails, the journal stays
             at ``dispatched`` and startup reconciliation (recover_startup)
             will close the record on next session init.
          3. Audit emission happens BEFORE the completed phase so an audit
             failure leaves the journal unreconciled rather than
             terminal-but-inconsistent.

        Failure semantics (mirrors dialogue.py:361-373 committed-turn finalization,
        adapted for delegation's wider blast radius — 4-5 post-``dispatched`` local
        writes vs dialogue's 1):

        - ``worktree_manager.create_worktree`` or ``control_plane.start_execution_runtime``
          raises (before ``dispatched``): raw exception propagates. Journal may have
          an ``intent`` phase; no durable state beyond that. Covered by
          test_start_does_not_persist_durable_state_on_bootstrap_failure.

        - ``runtime_registry.register`` raises (after ``dispatched``, BEFORE any
          other committed-start write): the runtime subprocess is live but the
          in-process ownership table never received the entry. The journal is at
          ``dispatched``; no handle, job, or registry entry exists. The controller
          raises CommittedStartFinalizationError with no-retry guidance.
          Reconciliation on next session init advances the journal to ``completed``;
          the runtime subprocess is unreachable from the registry and will leak
          until the parent process exits (no in-process entry to release; teardown
          via subprocess discovery is out of scope for this slice). Structurally
          rare: register rejects only on duplicate ``runtime_id``, and ``runtime_id``
          is uuid-generated. Covered by
          test_start_raises_committed_start_finalization_error_on_register_failure.

        - ``lineage_store.create`` / ``job_store.create`` / ``journal.append_audit_event``
          / ``journal.write_phase(completed)`` raises (after ``dispatched`` AND
          successful ``register``): the start has committed — a runtime subprocess
          is live AND registered. The controller best-effort marks any already-persisted
          ``CollaborationHandle`` and ``DelegationJob`` with ``status="unknown"``,
          leaves the journal at ``dispatched`` (does NOT write ``completed``),
          retains the registry entry (the runtime stays controllable in-process for
          the rest of the session; releasing it would leak the subprocess), and
          raises CommittedStartFinalizationError with no-retry guidance. The busy
          gate consults ``registry.active_runtime_ids()`` (alongside the job store
          and unresolved journal entries) so any same-session retry is rejected.
          Recovery is deferred to DelegationController.recover_startup() on the
          next session init for the durable side.
        """

        # Busy check — max-1 concurrent job per session. Consults THREE sources:
        #   (a) job_store.list_active(): healthy queued/running/needs_escalation jobs
        #   (b) registry.active_runtime_ids(): in-process live ownership; catches
        #       same-session retry after a committed-start failure that left a
        #       registered runtime without a queued job (e.g., lineage_store.create
        #       failed AFTER the registry registration that always happens FIRST
        #       post-dispatched).
        #   (c) unresolved job_creation journal entries: catches the cross-session
        #       case where the in-process registry is fresh but the journal still
        #       has a dispatched record awaiting recover_startup() reconciliation.
        # Filter (c) in the controller — journal.list_unresolved() does not take
        # an operation parameter; we filter on entry.operation == "job_creation".
        active = self._job_store.list_active()
        if active:
            existing = active[0]
            return JobBusyResponse(
                busy=True,
                active_job_id=existing.job_id,
                active_job_status=existing.status,
                detail=(
                    "Another delegation is in flight (job_store). "
                    f"active_job_id={existing.job_id!r} "
                    f"status={existing.status!r}"
                ),
            )
        active_runtime_ids = self._runtime_registry.active_runtime_ids()
        if active_runtime_ids:
            rt_id = next(iter(active_runtime_ids))
            entry = self._runtime_registry.lookup(rt_id)
            # Invariant: rt_id came from active_runtime_ids(); lookup() on
            # that id cannot return None (both reads are against the same
            # in-process dict). Assert to document the invariant and fail
            # loud on corruption rather than encode an impossible None into
            # JobBusyResponse.active_job_id (declared ``str``).
            assert entry is not None, (
                f"ExecutionRuntimeRegistry invariant violation: "
                f"runtime_id={rt_id!r} in active_runtime_ids() but "
                f"lookup() returned None"
            )
            return JobBusyResponse(
                busy=True,
                active_job_id=entry.job_id,
                active_job_status="unknown",
                detail=(
                    "Another delegation runtime is registered in-process "
                    "(committed-start failure pending reconciliation). "
                    f"active_runtime_id={rt_id!r} job_id={entry.job_id!r}"
                ),
            )
        unresolved = [
            e
            for e in self._journal.list_unresolved(session_id=self._session_id)
            if e.operation == "job_creation"
        ]
        if unresolved:
            earliest = unresolved[0]
            # Invariant: the journal validator requires ``job_id`` on every
            # ``job_creation`` entry at both ``intent`` and ``dispatched``
            # phases (Task 1 per-phase validator extension). The
            # ``OperationJournalEntry.job_id`` field is declared
            # ``str | None`` for compatibility with non-job_creation ops,
            # but for this branch it is always present. Assert to document
            # the invariant and preserve the typed
            # ``JobBusyResponse.active_job_id`` (declared ``str``).
            assert earliest.job_id is not None, (
                f"OperationJournal invariant violation: job_creation entry "
                f"at phase={earliest.phase!r} has job_id=None "
                f"(idempotency_key={earliest.idempotency_key!r})"
            )
            return JobBusyResponse(
                busy=True,
                active_job_id=earliest.job_id,
                active_job_status="unknown",
                detail=(
                    "Unresolved job_creation journal entries present "
                    "(awaiting recover_startup reconciliation). "
                    f"job_id={earliest.job_id!r}"
                ),
            )

        # Resolve inputs and compute identifiers.
        resolved_root = repo_root.resolve()
        resolved_base = base_commit or self._head_commit_resolver(resolved_root)
        job_id = self._uuid_factory()
        collaboration_id = self._uuid_factory()
        request_hash = _delegation_request_hash(resolved_root, resolved_base)
        idempotency_key = f"{self._session_id}:{request_hash}"
        created_at = self._journal.timestamp()
        worktree_path = (
            self._plugin_data_path
            / "runtimes"
            / "delegation"
            / job_id
            / "worktree"
        )

        # Phase 1: journal intent BEFORE any side effects.
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="job_creation",
                phase="intent",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
                job_id=job_id,
            ),
            session_id=self._session_id,
        )

        # Side effects: worktree + runtime bootstrap + thread.
        self._worktree_manager.create_worktree(
            repo_root=resolved_root,
            base_commit=resolved_base,
            worktree_path=worktree_path,
        )
        runtime_id, session, thread_id = (
            self._control_plane.start_execution_runtime(worktree_path)
        )

        # Phase 2: journal dispatched with outcome correlation.
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="job_creation",
                phase="dispatched",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
                job_id=job_id,
                runtime_id=runtime_id,
                codex_thread_id=thread_id,
            ),
            session_id=self._session_id,
        )

        # ------------------------------------------------------------------
        # Committed-start phase: worktree + runtime are live, journal records
        # dispatched. Every write below is wrapped so that any failure leaves
        # the journal at ``dispatched`` (NOT ``completed``), and any
        # partially-persisted durable state is best-effort marked unknown.
        # ORDER MATTERS:
        #   1. runtime_registry.register goes FIRST so the runtime is
        #      controllable in-process from the moment the journal records
        #      dispatched. Without this, a subsequent failure (lineage / job
        #      / audit / completed) would leave a live subprocess with no
        #      in-process owner and the busy gate would clear → same-session
        #      retry would spawn a second runtime.
        #   2. journal.write_phase(completed) goes LAST so "journal at
        #      dispatched" is the universal terminal state for any
        #      committed-start failure (recovery just advances to completed).
        #   3. audit emission comes BEFORE completed so an audit failure
        #      still leaves the journal unreconciled rather than
        #      terminal-but-inconsistent.
        # ------------------------------------------------------------------
        handle_persisted = False
        job_persisted = False
        try:
            # Register live ownership FIRST — keeps the runtime controllable
            # in-process for the rest of the session, so any subsequent
            # committed-start failure does not leave an orphan subprocess.
            # Not a crash-durability layer; recovery uses the three durable
            # stores. If register itself raises, the catch block runs with
            # both _persisted flags False (no stores were touched) and the
            # subprocess leaks until the parent process exits — see the
            # register-failure failure-mode bullet in the start() docstring.
            self._runtime_registry.register(
                runtime_id=runtime_id,
                session=session,
                thread_id=thread_id,
                job_id=job_id,
            )

            # Persist identity — CollaborationHandle in the lineage store.
            handle = CollaborationHandle(
                collaboration_id=collaboration_id,
                capability_class="execution",
                runtime_id=runtime_id,
                codex_thread_id=thread_id,
                claude_session_id=self._session_id,
                repo_root=str(resolved_root),
                created_at=created_at,
                status="active",
            )
            self._lineage_store.create(handle)
            handle_persisted = True

            # Persist job lifecycle — DelegationJob in the job store.
            job = DelegationJob(
                job_id=job_id,
                runtime_id=runtime_id,
                collaboration_id=collaboration_id,
                base_commit=resolved_base,
                worktree_path=str(worktree_path),
                promotion_state="pending",
                status="queued",
            )
            self._job_store.create(job)
            job_persisted = True

            # Audit emission BEFORE journal completed — see ORDER MATTERS
            # note above. Crosses a trust/capability boundary per
            # recovery-and-journal.md Write Triggers.
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="claude",
                    action="delegate_start",
                    collaboration_id=collaboration_id,
                    runtime_id=runtime_id,
                    job_id=job_id,
                )
            )

            # Phase 3: journal completed — terminal write. After this line
            # the operation is replay-safe: a later recover_startup() will
            # see a ``completed`` record and treat it as no-op.
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=idempotency_key,
                    operation="job_creation",
                    phase="completed",
                    collaboration_id=collaboration_id,
                    created_at=created_at,
                    repo_root=str(resolved_root),
                    job_id=job_id,
                ),
                session_id=self._session_id,
            )
        except Exception as exc:
            # Committed-start finalization failure. The runtime subprocess is
            # live and the journal is at ``dispatched``. Best-effort mark any
            # persisted durable records as ``unknown``; leave the journal
            # unresolved for startup reconciliation to close on next session
            # init. If register succeeded (the common case), the registry entry
            # stays so the runtime remains reachable for a later teardown pass
            # (poll/promote slices) AND so the busy gate's registry consultation
            # blocks same-session retry. If register itself raised, there is no
            # entry to retain — the subprocess will leak until the parent
            # process exits.
            if handle_persisted:
                try:
                    self._lineage_store.update_status(collaboration_id, "unknown")
                except Exception:
                    # Best-effort — reconciliation will close it.
                    pass
            if job_persisted:
                try:
                    self._job_store.update_status(job_id, "unknown")
                except Exception:
                    pass
            raise CommittedStartFinalizationError(
                "Delegation start committed but local finalization failed: "
                f"{exc}. The runtime is live at runtime_id={runtime_id!r} with "
                f"job_id={job_id!r}. The operation journal is at phase "
                f"``dispatched``; startup reconciliation will mark the job "
                f"and handle ``unknown`` on next session init (or, if registry "
                f"registration was the failure, will simply advance the journal "
                f"with no durable identity to mark). Blind retry of "
                f"codex.delegate.start will create a duplicate job for the "
                f"same (repo_root, base_commit) pair — the idempotency replay "
                f"path only recognizes a ``completed`` journal phase as "
                f"terminal, which is exactly the phase that was NOT written."
            ) from exc
        return job
```

**Note on `lineage_store.update_status` and `job_store.update_status`:** Both methods already exist — `LineageStore.update_status(collaboration_id, status: HandleStatus)` at `lineage_store.py:159` (used by dialogue's committed-turn finalization path at `dialogue.py:449-492`); `DelegationJobStore.update_status(job_id, status: JobStatus)` is introduced in Task 2 of this plan (`delegation_job_store.py`). Both `HandleStatus` and `JobStatus` include `"unknown"` (see `models.py:15` and the Task 1 `JobStatus` literal). The `_build_controller` test fixture uses real stores (not fakes), so the committed-start-failure tests exercise the actual `update_status` path.

- [ ] **Step 6.4: Run tests and full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_controller.py -v && uv run pytest tests/ -q
```
Expected: 15 new controller tests pass (8 happy-path/busy/bootstrap-failure + 5 committed-start failure tests [lineage / job / journal-completed / audit / register] + 2 busy-gate widening tests [registry-only busy / journal-only busy]); plugin suite `~639 passed` (624 + 15).

- [ ] **Step 6.5: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "feat(t20260330-05): add DelegationController with journal/handle/registry discipline + committed-start failure semantics"
```

---

## Task 7: Delegation Startup Reconciliation

**Goal:** Add `DelegationController.recover_startup()` consuming unresolved `job_creation` journal records and reconciling them into durable terminal state, then wire it into `mcp_server.startup()` (eager session-init path) alongside the existing `dialogue_controller.recover_startup()` call. The lazy-factory wiring inside `_ensure_delegation_controller()` lands with Task 8 (which is what introduces that method); production deploys via the factory, so the lazy wiring is the load-bearing one. Closes the producer/consumer gap that AC 4 depends on.

**Reconciliation contract (this task implements this verbatim):**

| Unresolved journal state | Durable-store reconciliation | Journal advance | Rationale |
|---|---|---|---|
| Only `intent` present | None — no handle, no job persisted yet | Write `completed` with `no-op` outcome | Crash happened before dispatch side effects; nothing to roll back |
| `intent` + `dispatched`, no handle/job persisted | None (nothing was written) | Write `completed` | Crash happened between `dispatched` journal write and `lineage_store.create`; runtime subprocess is dead |
| `intent` + `dispatched`, handle persisted (active) | `lineage_store.update_status(cid, "unknown")` | Write `completed` | Crash during committed-start finalization; handle is authoritative |
| `intent` + `dispatched`, handle + job persisted | `update_status` on BOTH stores to `"unknown"` | Write `completed` | Same as above but both stores advanced; consistency required |
| `intent` + `dispatched`, handle already `unknown` (committed-start failure on same session) | No change (already unknown) | Write `completed` | Idempotent close-out of a CommittedStartFinalizationError that was raised earlier this session |

**Explicitly NOT in scope for Task 7:** runtime subprocess reattachment. Unlike dialogue (which can reuse a persistent App Server `codex_thread_id` across restarts), delegation runtimes are subprocess-anchored to a worktree and cannot be rejoined. Reattachment is not a recovery concern — it is a fundamental capability the v1 architecture does not provide. Promote/discard slices handle the `unknown` record; those slices are out of scope here.

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (add `recover_startup`)
- Modify: `packages/plugins/codex-collaboration/server/mcp_server.py` (eager-path only: call `delegation_controller.recover_startup()` inside `startup()` alongside `dialogue_controller.recover_startup()` at `mcp_server.py:128-129`. The lazy-path wiring at `mcp_server.py:147` lands with Task 8 because Task 8 is what introduces `_ensure_delegation_controller()`.)
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py` (append recovery tests)

- [ ] **Step 7.1: Write failing tests**

Append to `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`:

```python
# -----------------------------------------------------------------------------
# Startup reconciliation — DelegationController.recover_startup() consumes
# unresolved job_creation journal entries and closes them into durable state.
# -----------------------------------------------------------------------------


def _write_unresolved_intent(
    journal: OperationJournal,
    session_id: str,
    *,
    idempotency_key: str,
    collaboration_id: str,
    job_id: str,
    repo_root: Path,
) -> None:
    """Seed the journal with an intent-only job_creation entry (simulates a crash
    after intent but before dispatch side effects)."""
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="job_creation",
            phase="intent",
            collaboration_id=collaboration_id,
            created_at=journal.timestamp(),
            repo_root=str(repo_root),
            job_id=job_id,
        ),
        session_id=session_id,
    )


def _write_unresolved_dispatched(
    journal: OperationJournal,
    session_id: str,
    *,
    idempotency_key: str,
    collaboration_id: str,
    job_id: str,
    runtime_id: str,
    thread_id: str,
    repo_root: Path,
) -> None:
    """Seed the journal with intent + dispatched (simulates a crash during
    committed-start finalization)."""
    created_at = journal.timestamp()
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="job_creation",
            phase="intent",
            collaboration_id=collaboration_id,
            created_at=created_at,
            repo_root=str(repo_root),
            job_id=job_id,
        ),
        session_id=session_id,
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="job_creation",
            phase="dispatched",
            collaboration_id=collaboration_id,
            created_at=created_at,
            repo_root=str(repo_root),
            job_id=job_id,
            runtime_id=runtime_id,
            codex_thread_id=thread_id,
        ),
        session_id=session_id,
    )


def test_recover_startup_noop_on_fresh_session(tmp_path: Path) -> None:
    """No unresolved entries → no durable changes, no journal writes."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r = _build_controller(tmp_path)

    before = journal.list_unresolved(session_id="sess-1")
    assert before == []

    controller.recover_startup()

    after = journal.list_unresolved(session_id="sess-1")
    assert after == []


def test_recover_startup_closes_intent_only_as_noop(tmp_path: Path) -> None:
    """intent-only → write completed, no durable changes."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r = _build_controller(
        tmp_path
    )

    _write_unresolved_intent(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        repo_root=repo_root,
    )

    # No handle / job persisted (crash before dispatch side effects).
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None

    controller.recover_startup()

    # Journal advanced to completed; unresolved list empty after reconciliation.
    assert journal.list_unresolved(session_id="sess-1") == []
    # Still no durable handle / job (nothing was there to reconcile).
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None


def test_recover_startup_marks_dispatched_handle_and_job_unknown(tmp_path: Path) -> None:
    """intent + dispatched with persisted handle + job → mark both unknown, close journal."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r = _build_controller(
        tmp_path
    )

    # Seed: intent + dispatched journal + persisted active handle + persisted queued job.
    _write_unresolved_dispatched(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        runtime_id="rt-1",
        thread_id="thr-1",
        repo_root=repo_root,
    )
    lineage_store.create(
        CollaborationHandle(
            collaboration_id="collab-1",
            capability_class="execution",
            runtime_id="rt-1",
            codex_thread_id="thr-1",
            claude_session_id="sess-1",
            repo_root=str(repo_root),
            created_at=journal.timestamp(),
            status="active",
        )
    )
    job_store.create(
        DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="head-abc",
            worktree_path=str(tmp_path / "wk"),
            promotion_state="pending",
            status="queued",
        )
    )

    controller.recover_startup()

    # Both stores advanced to unknown.
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    # Journal record closed.
    assert journal.list_unresolved(session_id="sess-1") == []


def test_recover_startup_closes_dispatched_without_persisted_state(tmp_path: Path) -> None:
    """intent + dispatched but no handle/job persisted → write completed, no mark needed."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r = _build_controller(
        tmp_path
    )

    _write_unresolved_dispatched(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        runtime_id="rt-1",
        thread_id="thr-1",
        repo_root=repo_root,
    )
    # Intentionally NO lineage_store.create / job_store.create — simulates crash
    # between journal.write_phase(dispatched) and lineage_store.create.

    controller.recover_startup()

    # No durable records to advance, but journal is closed.
    assert journal.list_unresolved(session_id="sess-1") == []
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None


def test_recover_startup_idempotent_second_call_is_noop(tmp_path: Path) -> None:
    """Second recover_startup after the first has reconciled finds nothing to do."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r = _build_controller(tmp_path)

    _write_unresolved_intent(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        repo_root=repo_root,
    )

    controller.recover_startup()
    assert journal.list_unresolved(session_id="sess-1") == []

    # Second call should be a clean no-op.
    controller.recover_startup()
    assert journal.list_unresolved(session_id="sess-1") == []
```

- [ ] **Step 7.2: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_controller.py::test_recover_startup_noop_on_fresh_session -v
```
Expected: `AttributeError: 'DelegationController' object has no attribute 'recover_startup'`.

- [ ] **Step 7.3: Implement `recover_startup`**

Append to `DelegationController` class in `packages/plugins/codex-collaboration/server/delegation_controller.py`:

```python
    def recover_startup(self) -> None:
        """Consume unresolved job_creation journal records into durable terminal state.

        Mirrors dialogue.py:522 recover_startup — but reconcile-only. Unlike
        dialogue (which can reattach persistent codex_thread_ids to new runtime
        sessions), delegation runtimes are subprocess-anchored to a worktree and
        cannot be rejoined across restart. The only recovery this does is close
        unresolved journal records and mark any partially-persisted handle / job
        as ``unknown`` so poll/discard/promote slices can operate on terminal
        durable state.

        Reconciliation contract (by journal phase):

        - ``intent`` only: no side effects committed yet; advance to ``completed``.
        - ``dispatched`` + no persisted handle/job: runtime subprocess is dead;
          advance journal to ``completed``.
        - ``dispatched`` + persisted handle and/or job: mark each persisted record
          ``unknown`` (if not already); advance journal to ``completed``.

        Idempotent: a second call after the first has reconciled finds no
        unresolved entries and is a clean no-op.

        Called from mcp_server.py's session init path, mirroring the
        ``self._dialogue_controller.recover_startup()`` call.
        """
        unresolved = self._journal.list_unresolved(session_id=self._session_id)
        job_creation_entries = [
            e for e in unresolved if e.operation == "job_creation"
        ]
        # Group by idempotency_key and pick the latest phase per key.
        by_key: dict[str, OperationJournalEntry] = {}
        for entry in job_creation_entries:
            existing = by_key.get(entry.idempotency_key)
            if existing is None or _phase_rank(entry.phase) > _phase_rank(
                existing.phase
            ):
                by_key[entry.idempotency_key] = entry

        for entry in by_key.values():
            # Mark durable records unknown if they exist AND are not already
            # in a terminal state.
            if entry.collaboration_id is not None:
                handle = self._lineage_store.get(entry.collaboration_id)
                if handle is not None and handle.status == "active":
                    self._lineage_store.update_status(
                        entry.collaboration_id, "unknown"
                    )
            if entry.job_id is not None:
                job = self._job_store.get(entry.job_id)
                if job is not None and job.status in ("queued", "running"):
                    self._job_store.update_status(entry.job_id, "unknown")

            # Advance the journal to completed — this is the terminal phase
            # per recovery-and-journal.md, and it causes list_unresolved to
            # stop returning this key. Physical compaction via
            # OperationJournal.compact() is a separate operation not invoked
            # in this slice (recovery-and-journal.md:59 describes the
            # "near-empty" steady state but does not require eager trimming).
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=entry.idempotency_key,
                    operation="job_creation",
                    phase="completed",
                    collaboration_id=entry.collaboration_id,
                    created_at=entry.created_at,
                    repo_root=entry.repo_root,
                    job_id=entry.job_id,
                ),
                session_id=self._session_id,
            )


def _phase_rank(phase: str) -> int:
    """Phase-ordering helper for picking the latest phase per idempotency key."""
    return {"intent": 0, "dispatched": 1, "completed": 2}.get(phase, -1)
```

- [ ] **Step 7.4: Wire recover_startup into mcp_server.startup() (eager path only)**

In `packages/plugins/codex-collaboration/server/mcp_server.py`, locate the existing eager call to `self._dialogue_controller.recover_startup()` inside `startup()` at approximately line 128-129. Add a matching call for `self._delegation_controller` right after it, guarded by the same eager-only check:

```python
    def startup(self) -> None:
        """One-shot startup recovery. Idempotent — second call is a no-op.

        If a controller was provided directly at construction, runs recovery
        immediately. If a controller is deferred via factory, recovery runs
        on first tool call instead (via _ensure_*_controller).
        """
        if self._recovery_completed:
            return
        if self._dialogue_controller is not None:
            self._dialogue_controller.recover_startup()
        if self._delegation_controller is not None:
            self._delegation_controller.recover_startup()
        self._recovery_completed = True
```

**Why only the eager path here.** The lazy-factory path (production) is wired separately in Task 8 by adding `controller.recover_startup()` inside `_ensure_delegation_controller()` BEFORE pinning, mirroring `_ensure_dialogue_controller()` at `mcp_server.py:147`. Splitting these two call sites across Task 7 and Task 8 is necessary because Task 8 is what introduces `_ensure_delegation_controller()` — Task 7 cannot edit code that does not yet exist. Production deploys via the factory in Task 9, so the Task-8 lazy wiring is the load-bearing one; the Task-7 eager wiring covers the directly-injected-controller case (mostly used in tests).

- [ ] **Step 7.5: Run tests and full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_controller.py -v && uv run pytest tests/ -q
```
Expected: 5 new recovery tests pass; plugin suite `~644 passed` (639 + 5). The mcp-wiring tests for both eager and lazy paths land with Task 8.

- [ ] **Step 7.6: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/server/mcp_server.py packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "feat(t20260330-05): add delegation startup reconciliation for unresolved job_creation"
```

---

## Task 8: MCP Tool Registration

**Goal:** Expose `codex.delegate.start` via the MCP server with the same lazy-factory pattern as dialogue. This task ALSO wires the lazy-path recovery (`controller.recover_startup()` inside `_ensure_delegation_controller()` BEFORE pinning) — that wiring lands here rather than in Task 7 because Task 8 is what introduces `_ensure_delegation_controller()`. Production deploys via the factory, so this lazy wiring is the load-bearing one for AC 4's consumer half.

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/mcp_server.py`
- Modify: `packages/plugins/codex-collaboration/server/__init__.py`
- Test: `packages/plugins/codex-collaboration/tests/test_mcp_server.py` (append)

- [ ] **Step 8.1: Write failing tests**

Append to `packages/plugins/codex-collaboration/tests/test_mcp_server.py`:

```python
class TestDelegateToolRegistration:
    def test_delegate_start_tool_registered(self) -> None:
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert "codex.delegate.start" in tool_names

    def test_delegate_start_input_schema_requires_repo_root(self) -> None:
        schema = next(
            t["inputSchema"] for t in TOOL_DEFINITIONS if t["name"] == "codex.delegate.start"
        )
        assert schema["type"] == "object"
        assert "repo_root" in schema["required"]


class FakeDelegationController:
    def __init__(self) -> None:
        self.start_calls: list[dict] = []

    def start(self, *, repo_root: Path, base_commit: str | None = None) -> object:
        from server.models import DelegationJob

        self.start_calls.append(
            {"repo_root": repo_root, "base_commit": base_commit}
        )
        return DelegationJob(
            job_id="job-x",
            runtime_id="rt-x",
            collaboration_id="collab-x",
            base_commit=base_commit or "head-sha",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="queued",
        )


class TestDelegateDispatch:
    def test_delegate_start_dispatch_returns_job_fields(self) -> None:
        controller = FakeDelegationController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_controller=controller,
        )
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo"},
                },
            }
        )
        assert "isError" not in response["result"]
        content = response["result"]["content"][0]["text"]
        payload = json.loads(content)
        assert payload["job_id"] == "job-x"
        assert payload["status"] == "queued"
        assert controller.start_calls == [
            {"repo_root": Path("/some/repo"), "base_commit": None}
        ]

    def test_delegate_start_forwards_optional_base_commit(self) -> None:
        controller = FakeDelegationController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_controller=controller,
        )
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {
                        "repo_root": "/some/repo",
                        "base_commit": "explicit-sha",
                    },
                },
            }
        )
        assert controller.start_calls[0]["base_commit"] == "explicit-sha"

    def test_delegate_start_returns_busy_response_payload(self) -> None:
        from server.models import JobBusyResponse

        class _BusyController:
            def start(self, *, repo_root: Path, base_commit: str | None = None) -> object:
                return JobBusyResponse(
                    busy=True,
                    active_job_id="job-1",
                    active_job_status="running",
                    detail="Active.",
                )

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_controller=_BusyController(),
        )
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo"},
                },
            }
        )
        assert "isError" not in response["result"]
        payload = json.loads(response["result"]["content"][0]["text"])
        assert payload["busy"] is True
        assert payload["active_job_id"] == "job-1"


class _RecordingDelegationController:
    """Records recover_startup + start invocations for wiring tests."""

    def __init__(self) -> None:
        self.recover_startup_calls = 0
        self.start_calls: list[dict] = []

    def recover_startup(self) -> None:
        self.recover_startup_calls += 1

    def start(self, *, repo_root: Path, base_commit: str | None = None) -> object:
        from server.models import DelegationJob

        self.start_calls.append({"repo_root": repo_root, "base_commit": base_commit})
        return DelegationJob(
            job_id="job-rec",
            runtime_id="rt-rec",
            collaboration_id="collab-rec",
            base_commit=base_commit or "head-sha",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="queued",
        )


class _FailOnceDelegationController:
    """Controller that raises from ``recover_startup`` a configurable number of
    times before succeeding. Used to prove retry-on-recovery-failure semantics
    of the lazy factory path: if ``recover_startup`` raises, the controller
    must NOT be pinned, and the factory must be re-invoked on the next
    dispatch.
    """

    def __init__(self, *, recovery_fails_remaining: int = 0) -> None:
        self._recovery_fails_remaining = recovery_fails_remaining
        self.recover_startup_calls = 0
        self.start_calls: list[dict] = []

    def recover_startup(self) -> None:
        self.recover_startup_calls += 1
        if self._recovery_fails_remaining > 0:
            self._recovery_fails_remaining -= 1
            raise RuntimeError("simulated transient recovery failure")

    def start(self, *, repo_root: Path, base_commit: str | None = None) -> object:
        from server.models import DelegationJob

        self.start_calls.append({"repo_root": repo_root, "base_commit": base_commit})
        return DelegationJob(
            job_id="job-fail-once",
            runtime_id="rt-fail-once",
            collaboration_id="collab-fail-once",
            base_commit=base_commit or "head-sha",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="queued",
        )


class TestDelegationRecoveryWiring:
    """Recovery is wired at TWO call sites — eager (startup) and lazy
    (_ensure_delegation_controller). Production deploys via factory, so the
    lazy path is the load-bearing one. Both are tested below."""

    def test_ensure_delegation_controller_runs_recover_startup_on_first_dispatch(self) -> None:
        """Lazy factory path happy case: ``recover_startup`` runs once on first
        dispatch; subsequent dispatches reuse the pinned controller without
        re-running recovery. The pin-only-after-successful-recovery retry
        ordering invariant is covered separately by
        ``test_ensure_delegation_controller_does_not_pin_on_recovery_failure``.
        """
        controller = _RecordingDelegationController()

        def factory() -> _RecordingDelegationController:
            return controller

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_factory=factory,
        )
        # First dispatch triggers _ensure_delegation_controller → recover_startup → pin.
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo"},
                },
            }
        )
        assert controller.recover_startup_calls == 1
        # Second dispatch reuses the pinned controller — recover_startup is NOT re-called.
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo"},
                },
            }
        )
        assert controller.recover_startup_calls == 1
        assert len(controller.start_calls) == 2

    def test_ensure_delegation_controller_does_not_pin_on_recovery_failure(self) -> None:
        """Lazy factory path retry safety: when ``recover_startup`` raises,
        the controller is NOT pinned, ``start()`` is NOT reached, and a
        subsequent dispatch retries by invoking the factory a second time
        rather than reusing a poisoned controller. Protects the ordering
        invariant named in ``_ensure_delegation_controller``'s docstring:
        'Pin only after recovery succeeds — transient failures allow retry.'

        Proof shape (3 dispatches):
          1. First dispatch: recovery raises → error response; factory called
             once; start() not reached; controller not pinned.
          2. Second dispatch: factory invoked AGAIN (proves no pin on first
             call); new controller's recovery succeeds; start() runs.
          3. Third dispatch: factory NOT re-invoked (proves pin happened
             after successful recovery on second dispatch); start() runs
             on the pinned controller.
        """
        factory_controllers: list[_FailOnceDelegationController] = []

        def factory() -> _FailOnceDelegationController:
            # First factory call: recovery fails once. Subsequent calls: no failures.
            controller = _FailOnceDelegationController(
                recovery_fails_remaining=1 if not factory_controllers else 0
            )
            factory_controllers.append(controller)
            return controller

        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_factory=factory,
        )

        # Dispatch 1: recovery raises → error response; start() not reached.
        response1 = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo"},
                },
            }
        )
        assert response1["result"]["isError"] is True
        assert len(factory_controllers) == 1
        assert factory_controllers[0].recover_startup_calls == 1
        assert factory_controllers[0].start_calls == []  # start not reached on failed recovery

        # Dispatch 2: factory re-invoked (proves no pin on first call);
        # second controller's recovery succeeds; start() runs.
        response2 = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo"},
                },
            }
        )
        assert "isError" not in response2["result"]
        assert len(factory_controllers) == 2  # factory re-invoked — retry, not reuse
        assert factory_controllers[1].recover_startup_calls == 1
        assert len(factory_controllers[1].start_calls) == 1

        # Dispatch 3: NOW pinned — factory NOT re-invoked.
        server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "codex.delegate.start",
                    "arguments": {"repo_root": "/some/repo"},
                },
            }
        )
        assert len(factory_controllers) == 2  # still 2 — second controller pinned
        assert len(factory_controllers[1].start_calls) == 2

    def test_startup_runs_delegation_recover_startup_when_controller_provided_directly(
        self,
    ) -> None:
        """Eager session-init path: startup() fires recover_startup once."""
        controller = _RecordingDelegationController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
            delegation_controller=controller,
        )
        server.startup()
        assert controller.recover_startup_calls == 1
        # Idempotent — second startup call is a no-op.
        server.startup()
        assert controller.recover_startup_calls == 1
```

- [ ] **Step 8.2: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_mcp_server.py::TestDelegateToolRegistration tests/test_mcp_server.py::TestDelegateDispatch tests/test_mcp_server.py::TestDelegationRecoveryWiring -v
```
Expected: tool-registration tests fail with `AssertionError: 'codex.delegate.start' in tool_names`; dispatch tests fail with `TypeError: McpServer.__init__() got an unexpected keyword argument 'delegation_controller'`.

- [ ] **Step 8.3: Register the tool and add dispatch**

In `packages/plugins/codex-collaboration/server/mcp_server.py`:

Add to `TOOL_DEFINITIONS` (append after `codex.dialogue.read`):

```python
    {
        "name": "codex.delegate.start",
        "description": "Start an isolated execution job. Creates a worktree and bootstraps an ephemeral execution runtime. Does not dispatch the first turn.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_root": {
                    "type": "string",
                    "description": "Repository root path",
                },
                "base_commit": {
                    "type": "string",
                    "description": "Optional — the commit SHA to base the worktree on. Defaults to current HEAD of repo_root.",
                },
            },
            "required": ["repo_root"],
        },
    },
```

Modify `McpServer.__init__` signature to accept delegation dependencies:

```python
    def __init__(
        self,
        *,
        control_plane: Any,
        dialogue_controller: Any | None = None,
        dialogue_factory: Callable[[], Any] | None = None,
        delegation_controller: Any | None = None,
        delegation_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._dialogue_controller = dialogue_controller
        self._dialogue_factory = dialogue_factory
        self._delegation_controller = delegation_controller
        self._delegation_factory = delegation_factory
        self._initialized = False
        self._recovery_completed = False
```

Add `_ensure_delegation_controller` right after `_ensure_dialogue_controller`:

```python
    def _ensure_delegation_controller(self) -> Any:
        """Return the delegation controller, lazily initializing from factory if needed.

        Mirrors _ensure_dialogue_controller exactly: build from factory, run
        recovery, then pin. The recover_startup() call BEFORE pinning is
        load-bearing — production deploys via delegation_factory (Task 9), so
        without this call the consumer-half of AC 4 would never run on the
        path that matters. See mcp_server.py:147 for the dialogue precedent.
        Pin only after recovery succeeds — transient failures allow retry.
        """
        if self._delegation_controller is not None:
            return self._delegation_controller
        if self._delegation_factory is None:
            raise RuntimeError(
                "Delegation dispatch failed: no delegation controller available. "
                "Session identity may not have been published yet."
            )
        controller = self._delegation_factory()
        controller.recover_startup()
        # Pin only after recovery succeeds — transient failures allow retry
        self._delegation_controller = controller
        self._delegation_factory = None
        return self._delegation_controller
```

Add a dispatch case in `_dispatch_tool` (before the final `raise ValueError`):

```python
        if name == "codex.delegate.start":
            controller = self._ensure_delegation_controller()
            result = controller.start(
                repo_root=Path(arguments["repo_root"]),
                base_commit=arguments.get("base_commit"),
            )
            return asdict(result)
```

In `packages/plugins/codex-collaboration/server/__init__.py`, add exports:

```python
from .delegation_controller import DelegationController
from .delegation_job_store import DelegationJobStore
from .execution_runtime_registry import ExecutionRuntimeRegistry
from .models import DelegationJob, JobBusyResponse
from .worktree_manager import WorktreeManager
```

And append to `__all__`:

```python
    "DelegationController",
    "DelegationJob",
    "DelegationJobStore",
    "ExecutionRuntimeRegistry",
    "JobBusyResponse",
    "WorktreeManager",
```

- [ ] **Step 8.4: Run tests and full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_mcp_server.py -v && uv run pytest tests/ -q
```
Expected: 8 new MCP tests pass (5 dispatch/registration + 3 recovery-wiring: happy-path first-dispatch, pin-deferral-on-recovery-failure, eager-path idempotent); plugin suite `~652 passed` (644 + 8). If any existing `TestMcpServer._make_server` / `McpServer(...)` call sites fail with "unexpected keyword argument" errors, those are fine because we only ADDED kwargs — existing call sites continue to work.

- [ ] **Step 8.5: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/server/mcp_server.py packages/plugins/codex-collaboration/server/__init__.py packages/plugins/codex-collaboration/tests/test_mcp_server.py
git commit -m "feat(t20260330-05): register codex.delegate.start MCP tool + dispatch"
```

---

## Task 9: Production Wiring

**Goal:** Wire `DelegationController` into the entry-point script so `codex.delegate.start` is reachable in production.

**Files:**
- Modify: `packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py`

- [ ] **Step 9.1: Write failing test**

Create `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py` with a tight smoke test of the factory pattern first (the full E2E integration test is added in Task 10):

```python
"""Smoke tests for production wiring of codex.delegate.start."""

from __future__ import annotations

from pathlib import Path


def test_delegation_factory_builds_controller(tmp_path: Path, monkeypatch) -> None:
    # Ensure scripts dir is importable
    scripts_dir = Path(__file__).parent.parent / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    from codex_runtime_bootstrap import _build_delegation_factory  # type: ignore
    from server.control_plane import ControlPlane
    from server.execution_runtime_registry import ExecutionRuntimeRegistry
    from server.journal import OperationJournal

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()
    # Publish a fake session id.
    (plugin_data / "session_id").write_text("sess-smoke-1")

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(plugin_data_path=plugin_data, journal=journal)
    runtime_registry = ExecutionRuntimeRegistry()

    factory = _build_delegation_factory(
        plugin_data_path=plugin_data,
        control_plane=control_plane,
        runtime_registry=runtime_registry,
        journal=journal,
    )
    controller = factory()

    from server.delegation_controller import DelegationController

    assert isinstance(controller, DelegationController)


def test_delegation_factory_passes_shared_runtime_registry(
    tmp_path: Path, monkeypatch
) -> None:
    """A single registry is shared across controller instances from one factory.

    The registry is constructed in main() and passed into the factory.
    The factory is called at most once per McpServer instance (lazy pin),
    so sharing the registry across callers within one McpServer is the
    correct default — it is the live view of THIS plugin instance.
    """

    scripts_dir = Path(__file__).parent.parent / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    from codex_runtime_bootstrap import _build_delegation_factory  # type: ignore
    from server.control_plane import ControlPlane
    from server.execution_runtime_registry import ExecutionRuntimeRegistry
    from server.journal import OperationJournal

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()
    (plugin_data / "session_id").write_text("sess-smoke-2")

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(plugin_data_path=plugin_data, journal=journal)
    runtime_registry = ExecutionRuntimeRegistry()

    factory = _build_delegation_factory(
        plugin_data_path=plugin_data,
        control_plane=control_plane,
        runtime_registry=runtime_registry,
        journal=journal,
    )
    controller = factory()

    # The registry the controller received must be the same object main()
    # constructed — otherwise main()'s reference cannot observe registered
    # runtimes later.
    assert controller._runtime_registry is runtime_registry  # type: ignore[attr-defined]
```

- [ ] **Step 9.2: Run test to verify it fails**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegate_start_integration.py -v
```
Expected: `ImportError: cannot import name '_build_delegation_factory'`.

- [ ] **Step 9.3: Add the delegation factory and wire it into McpServer**

In `packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py`:

Add imports at the top alongside existing imports:

```python
from server.delegation_controller import DelegationController
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.lineage_store import LineageStore
from server.worktree_manager import WorktreeManager
```

Add a new factory after `_build_dialogue_factory`:

```python
def _build_delegation_factory(
    *,
    plugin_data_path: Path,
    control_plane: ControlPlane,
    runtime_registry: ExecutionRuntimeRegistry,
    journal: OperationJournal,
) -> Callable[[], DelegationController]:
    """Return a zero-arg factory that builds a DelegationController on first call.

    Reads the published session_id, constructs session-scoped job_store +
    lineage_store, and returns a fully initialized controller wired to the
    shared runtime registry and journal. The McpServer calls this at most
    once and pins the result.

    Why lineage_store is built inside the factory closure: LineageStore is
    session-scoped (it takes session_id at construction). session_id is
    only available after ``_read_session_id`` succeeds, which happens
    inside the factory. The dialogue factory follows the same pattern.
    Both factories write to the same underlying lineage JSONL file for
    a given session_id, so the identity layer is shared naturally.
    """

    def factory() -> DelegationController:
        session_id = _read_session_id(plugin_data_path)
        job_store = DelegationJobStore(plugin_data_path, session_id)
        lineage_store = LineageStore(plugin_data_path, session_id)
        return DelegationController(
            control_plane=control_plane,
            worktree_manager=WorktreeManager(),
            job_store=job_store,
            lineage_store=lineage_store,
            runtime_registry=runtime_registry,
            journal=journal,
            session_id=session_id,
            plugin_data_path=plugin_data_path,
        )

    return factory
```

Modify `main()` to construct a single `ExecutionRuntimeRegistry` for this plugin instance and pass both the registry and the new factory into `McpServer`:

```python
    runtime_registry = ExecutionRuntimeRegistry()

    server = McpServer(
        control_plane=control_plane,
        dialogue_factory=_build_dialogue_factory(
            plugin_data_path=plugin_data_path,
            control_plane=control_plane,
            journal=journal,
        ),
        delegation_factory=_build_delegation_factory(
            plugin_data_path=plugin_data_path,
            control_plane=control_plane,
            runtime_registry=runtime_registry,
            journal=journal,
        ),
    )
```

- [ ] **Step 9.4: Run smoke test and full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegate_start_integration.py -v && uv run pytest tests/ -q
```
Expected: 2 smoke tests pass; plugin suite `~654 passed` (652 + 2).

- [ ] **Step 9.5: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
git commit -m "feat(t20260330-05): wire DelegationController into production bootstrap"
```

---

## Task 10: End-to-End Integration Test

**Goal:** One integration test that exercises the entire slice against a real tmp-path git repo, using a stubbed `AppServerRuntimeSession` factory (so no live Codex CLI is required). The test deliberately routes through the `delegation_factory` lazy-construction path — NOT direct controller injection — so that first dispatch exercises `_ensure_delegation_controller()` and runs `controller.recover_startup()` on the lazy production path. A pre-seeded unresolved `job_creation` journal entry (at `dispatched` phase, no persisted handle/job — the register-failure-or-early-crash shape) is planted before dispatch; the test asserts the seed is reconciled to `completed` after dispatch, providing literal behavioral evidence that recovery ran on the lazy production path. Without this seed-and-assert shape, the test would only prove factory-path traversal by call-count and would not catch a regression that (for example) dropped `recover_startup` from `_ensure_delegation_controller`. The separate pin-only-after-successful-recovery retry-ordering invariant is proven by Task 8's `test_ensure_delegation_controller_does_not_pin_on_recovery_failure`, NOT by this integration test.

**Files:**
- Modify: `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py` (append the full integration test)

- [ ] **Step 10.1: Add the end-to-end test**

Append to `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py`:

```python
import hashlib
import json
import subprocess

from server.control_plane import ControlPlane
from server.delegation_controller import DelegationController
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.mcp_server import McpServer
from server.models import AccountState, OperationJournalEntry, RuntimeHandshake
from server.worktree_manager import WorktreeManager


def _init_repo(repo_path: Path) -> str:
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )
    (repo_path / "README.md").write_text("hello\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return head


class _StubSession:
    def initialize(self) -> RuntimeHandshake:
        return RuntimeHandshake(
            codex_home="/fake",
            platform_family="unix",
            platform_os="darwin",
            user_agent="codex/stub",
        )

    def read_account(self) -> AccountState:
        return AccountState(
            auth_status="authenticated",
            account_type="stub",
            requires_openai_auth=False,
        )

    def start_thread(self) -> str:
        return "thr-exec-stub"

    def close(self) -> None:
        pass


def _make_compat_result() -> object:
    from server.codex_compat import REQUIRED_METHODS

    class _R:
        passed = True
        codex_version = "0.117.0"
        available_methods = REQUIRED_METHODS
        errors: tuple[str, ...] = ()

    return _R()


def test_delegate_start_end_to_end_through_mcp_dispatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    head = _init_repo(repo_root)

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(
        plugin_data_path=plugin_data,
        journal=journal,
        runtime_factory=lambda _: _StubSession(),  # type: ignore[arg-type]
        compat_checker=_make_compat_result,
    )
    job_store = DelegationJobStore(plugin_data, "sess-e2e")
    lineage_store = LineageStore(plugin_data, "sess-e2e")
    runtime_registry = ExecutionRuntimeRegistry()
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=WorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=runtime_registry,
        journal=journal,
        session_id="sess-e2e",
        plugin_data_path=plugin_data,
    )

    # SEED (load-bearing proof of AC 4 consumer wiring): simulate a prior
    # session that crashed between journal.write_phase(dispatched) and any
    # durable local write. The seeded entry is at ``dispatched`` phase for
    # a DISTINCT idempotency key from the upcoming real dispatch so the two
    # do not interfere. No handle / job persisted — this is the
    # register-failure-or-crash-before-first-durable-write shape from AC 4.
    #
    # This seed is the exact state the lazy-factory recovery wiring must
    # reconcile. If the test bypassed the factory path (direct-controller
    # injection), ``_ensure_delegation_controller()`` would never run,
    # ``recover_startup()`` would never be called, the seed would stay
    # unresolved, and the post-dispatch assertion on ``post_unresolved_seeds``
    # below would fail — proving the factory-path wiring is genuinely
    # load-bearing, not merely declared.
    seeded_key = "sess-e2e:seeded-leftover-hash"
    seeded_created_at = journal.timestamp()
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=seeded_key,
            operation="job_creation",
            phase="intent",
            collaboration_id="collab-seeded",
            created_at=seeded_created_at,
            repo_root=str(repo_root.resolve()),
            job_id="job-seeded",
        ),
        session_id="sess-e2e",
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=seeded_key,
            operation="job_creation",
            phase="dispatched",
            collaboration_id="collab-seeded",
            created_at=seeded_created_at,
            repo_root=str(repo_root.resolve()),
            job_id="job-seeded",
            runtime_id="rt-seeded",
            codex_thread_id="thr-seeded",
        ),
        session_id="sess-e2e",
    )
    # Sanity-check the seed IS unresolved before dispatch — invariant for
    # the proof shape. If this fails, the seed setup is wrong and the
    # downstream reconciliation assertion is meaningless.
    pre_unresolved_seeds = [
        e
        for e in journal.list_unresolved(session_id="sess-e2e")
        if e.operation == "job_creation" and e.idempotency_key == seeded_key
    ]
    assert len(pre_unresolved_seeds) == 1
    assert pre_unresolved_seeds[0].phase == "dispatched"

    class _MinimalCP:
        def codex_status(self, repo_root: Path) -> dict:
            return {}

        def codex_consult(self, request: object) -> object:
            raise NotImplementedError

    # Wire through the lazy-factory path (NOT direct controller injection) so
    # the first dispatch exercises _ensure_delegation_controller() →
    # controller.recover_startup() → pin. This is the production entry seam;
    # direct injection would skip recover_startup() on the lazy path and
    # leave the seeded entry unresolved.
    server = McpServer(
        control_plane=_MinimalCP(),
        delegation_factory=lambda: controller,
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root)},
            },
        }
    )

    assert "isError" not in response["result"]
    content = response["result"]["content"][0]["text"]
    payload = json.loads(content)
    assert payload["status"] == "queued"
    assert payload["promotion_state"] == "pending"
    assert payload["base_commit"] == head
    worktree_path = Path(payload["worktree_path"])
    # Worktree was created and exists as a directory.
    assert worktree_path.is_dir()
    assert (worktree_path / "README.md").exists()
    # Job is persisted in the job store.
    persisted_job = job_store.get(payload["job_id"])
    assert persisted_job is not None
    # Execution CollaborationHandle is persisted in the lineage store.
    persisted_handle = lineage_store.get(payload["collaboration_id"])
    assert persisted_handle is not None
    assert persisted_handle.capability_class == "execution"
    assert persisted_handle.runtime_id == payload["runtime_id"]
    # Runtime ownership is held by the in-process registry (live view).
    registry_entry = runtime_registry.lookup(payload["runtime_id"])
    assert registry_entry is not None
    assert registry_entry.job_id == payload["job_id"]
    # All three journal phases are present for THIS job creation (the real
    # dispatch, not the seed).
    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:{head}".encode("utf-8")
    ).hexdigest()
    key = f"sess-e2e:{request_hash}"
    terminal = journal.check_idempotency(key, session_id="sess-e2e")
    assert terminal is not None
    assert terminal.phase == "completed"
    assert terminal.operation == "job_creation"
    assert terminal.job_id == payload["job_id"]
    records = [
        json.loads(line)
        for line in journal._operations_path("sess-e2e").read_text().splitlines()
        if line.strip()
    ]
    phases = [r["phase"] for r in records if r["idempotency_key"] == key]
    assert phases == ["intent", "dispatched", "completed"]
    # Audit event was emitted with delegate_start.
    audit = json.loads(
        (plugin_data / "audit" / "events.jsonl").read_text().splitlines()[-1]
    )
    assert audit["action"] == "delegate_start"
    assert audit["job_id"] == payload["job_id"]
    # LOAD-BEARING AC 4 PROOF: the seeded unresolved ``dispatched`` entry
    # that existed BEFORE the first dispatch has been reconciled by
    # ``recover_startup()`` running inside ``_ensure_delegation_controller()``
    # on the lazy factory path. The seed key no longer appears in
    # ``list_unresolved()`` and its terminal phase is ``completed``. If the
    # factory path ever regresses (e.g., a refactor drops the recover_startup
    # call from _ensure_delegation_controller), these two assertions fail and
    # the "end-to-end" label stops being a lie. The separate retry-ordering
    # invariant (no pin when recovery fails) is proven by Task 8's
    # test_ensure_delegation_controller_does_not_pin_on_recovery_failure,
    # not by this integration test.
    post_unresolved_seeds = [
        e
        for e in journal.list_unresolved(session_id="sess-e2e")
        if e.operation == "job_creation" and e.idempotency_key == seeded_key
    ]
    assert post_unresolved_seeds == []
    seeded_terminal = journal.check_idempotency(seeded_key, session_id="sess-e2e")
    assert seeded_terminal is not None
    assert seeded_terminal.phase == "completed"

    # Second call is rejected with Job Busy.
    busy_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root)},
            },
        }
    )
    assert "isError" not in busy_response["result"]
    busy_payload = json.loads(busy_response["result"]["content"][0]["text"])
    assert busy_payload["busy"] is True
    assert busy_payload["active_job_id"] == payload["job_id"]
```

- [ ] **Step 10.2: Run the test and full plugin suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegate_start_integration.py -v && uv run pytest tests/ -q
```
Expected: new integration test passes; plugin suite `~655 passed` (654 + 1).

- [ ] **Step 10.3: Commit**

Run:
```bash
git add packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
git commit -m "test(t20260330-05): end-to-end codex.delegate.start integration"
```

---

## Task 11: Verification and Merge

**Goal:** Full-plugin suite + ruff green; merge to main with `--no-ff`, matching the three-step-chain pattern from the prior slice.

- [ ] **Step 11.1: Final full plugin suite**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/ -q
```
Expected: `~655 passed` (593 baseline + 62 added across tasks 1-10: 11 + 8 + 3 + 3 + 6 + 15 + 5 + 8 + 2 + 1). Treat divergence from the estimate by more than ~3 tests as an investigation signal, not a silent contract violation — the per-task deltas should sum, but exact totals depend on whether anything arrives on `main` between plan authoring and execution.

If counts are materially lower or any test fails, stop and investigate before merging. A scope-local run is NOT sufficient — prior-session lesson: scope-local runs miss cross-module seams. Run the full plugin suite.

- [ ] **Step 11.2: Ruff clean on touched files**

Run:
```bash
uv run ruff check packages/plugins/codex-collaboration/server/models.py \
                  packages/plugins/codex-collaboration/server/journal.py \
                  packages/plugins/codex-collaboration/server/delegation_job_store.py \
                  packages/plugins/codex-collaboration/server/worktree_manager.py \
                  packages/plugins/codex-collaboration/server/execution_runtime_registry.py \
                  packages/plugins/codex-collaboration/server/delegation_controller.py \
                  packages/plugins/codex-collaboration/server/control_plane.py \
                  packages/plugins/codex-collaboration/server/mcp_server.py \
                  packages/plugins/codex-collaboration/server/__init__.py \
                  packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py \
                  packages/plugins/codex-collaboration/tests/
```
Expected: `All checks passed!`

If ruff reports issues, fix them in a separate commit before the merge:
```bash
uv run ruff check --fix <files>
git add <files>
git commit -m "style(t20260330-05): ruff fixes"
```

- [ ] **Step 11.3: Push feature branch**

Run:
```bash
git push -u origin feature/t05-execution-start
```

- [ ] **Step 11.4: Merge to main with --no-ff**

Run:
```bash
git checkout main
git merge --no-ff feature/t05-execution-start -m "Merge feature/t05-execution-start: T-05 codex.delegate.start bootstrap slice"
git push origin main
git branch -d feature/t05-execution-start
git push origin --delete feature/t05-execution-start
```

- [ ] **Step 11.5: Confirm clean state after merge**

Run:
```bash
git status
git log --oneline -10
```
Expected: working tree clean; the merge commit and its task commits are visible.

---

## Risks and Known Deferrals

Surface these in any handoff after this plan executes — they are known open items, not defects of this slice.

| Risk / Deferral | Why deferred | Trigger that reopens it |
|---|---|---|
| `ExecutionRuntimeRegistry` is in-process live ownership only — **not** crash durability. If the control plane dies, the registry is lost; the runtime subprocess is orphaned (dies with the parent) and cannot be rejoined. Task 7's `recover_startup()` reconciles unresolved `job_creation` journal records into terminal durable state but does NOT reattach runtimes. Downstream decisions (restart from brief per `recovery-and-journal.md:121` or discard per `:123`) land with poll/promote slices. | By design. Delegation runtimes are subprocess-anchored to a worktree; unlike dialogue's persistent `codex_thread_id` (which can be rejoined), there is nothing for a delegation runtime to rejoin across restart. | Would only reopen if a future architecture change made execution runtimes restart-survivable (e.g., external App Server). |
| Startup reconciliation marks `unknown` but does NOT drive promote/discard. After `recover_startup()` runs, a restart leaves `unknown` handles and jobs on disk with no consumer. | Promote/discard behavior is explicitly scoped to the poll/promote slice, not this one. | `codex.delegate.poll` + `.promote` / `.discard` slices. |
| Committed-start failure can leave asymmetric partial state: lineage write succeeds, then an OS failure between the `update_status("unknown")` attempts leaves handle marked `unknown` but job still `queued`. Startup reconciliation closes this by running `update_status("unknown")` on both again (idempotent — `unknown` on an already-`unknown` record is a no-op). | Best-effort rollback inside `except` cannot guarantee both stores move together. The reconciliation consumer is the safety net. | Would only reopen if reconciliation itself was moved out of scope. |
| `runtime_registry.register` failure after `dispatched` leaves a live runtime subprocess unreachable from the in-process registry. `CommittedStartFinalizationError` is raised; reconciliation closes the journal but cannot reattach the subprocess. The subprocess persists until the parent process exits. The busy gate's registry consultation cannot block same-session retry for this specific failure mode (no entry to consult), but the journal-consultation branch still blocks until `recover_startup()` runs at next session init. | `register` is in-memory dict insertion on a uuid-generated `runtime_id`; collision is structurally impossible. The failure mode exists for completeness (e.g., monkeypatched in tests). | If `ExecutionRuntimeRegistry` adds external state (e.g., persistence) that introduces non-trivial failure modes. |
| Unresolved `job_creation` journal records survive between session close and next session's `recover_startup()` call. The recovery contract describes a "near-empty" steady state via trimming "after outcome confirmed" (`recovery-and-journal.md:59`). In v1, "outcome confirmed" means the controller has written `phase="completed"`, which removes the record from `list_unresolved()` results — physical compaction via `OperationJournal.compact()` is not invoked in this slice. Unconfirmed records between sessions are part of normal recovery state, not leaks. | By contract. An unresolved record between sessions is what makes recovery deterministic replay. | Would reopen if journal size grew unbounded in practice (e.g., repeated committed-start failures). |
| Notification loop on the execution runtime is not wired. App Server server requests issued during any future turn are currently dropped. | AC 6 is explicitly open; approval-router substrate (`approval_router.py::parse_pending_server_request`) is ready but not connected. | Next slice per handoff Next Steps #2 (pending-request capture). |
| First `run_execution_turn()` call is not dispatched in this slice. The runtime is bootstrapped, registered, and idle. | Turn-dispatch surface is a follow-up slice; this slice's job is to make the runtime *reachable* so dispatch has something to call into. | First slice that wires turn dispatch. It looks up the session via `ExecutionRuntimeRegistry.lookup(runtime_id)` and calls `runtime.run_execution_turn(...)`. |
| Runtime teardown is not wired on job completion. `ExecutionRuntimeRegistry.release(runtime_id)` is defined and tested, but no caller invokes it yet. | Lifecycle transitions (running → completed → discarded / promoted) land with poll/promote. | `codex.delegate.poll` (moves to `completed`) and `codex.delegate.promote` / `.discard` (releases the registry entry and schedules worktree cleanup). |
| Worktree cleanup is not implemented. | Per spec's `recovery-and-journal.md` retention defaults, worktrees persist for 1 hour (completed) or 24 hours (crashed). Cleanup is a promotion-slice concern. | `codex.delegate.promote` / `.discard` slice. |
| `worktree_path.resolve()` assumes the parent path is canonical on macOS. With `/tmp` symlinked to `/private/tmp`, tests that use `tmp_path` typically live under `/private/var/…` and are safe. Production worktrees live under `${CLAUDE_PLUGIN_DATA}`; still worth asserting canonicalization explicitly in a future hardening pass. | Low severity; same pattern applies to prior slice and was accepted there. | If a worktree path ever comes from untrusted input. |
| `DelegationController` assumes a git-enabled `repo_root`. Non-git paths will fail at `head_commit_resolver`. | Caller contract: `codex.delegate.start` is for repo work. | If non-git delegation targets become a use case. |
| `delegation_request_hash` inputs are just `(repo_root, base_commit)` in v1. If the MCP surface later accepts additional inputs (e.g., a delegation brief, objective, or profile override), they must be included in the hash so replay recognizes the full request shape. | v1 signature is `start(repo_root, base_commit)` and nothing else. | Any slice that adds an input parameter to `codex.delegate.start`. |

---

## Execution Handoff

**Plan saved to `docs/plans/2026-04-17-t05-execution-start-slice.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Uses `superpowers:subagent-driven-development`.
2. **Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

**Which approach?**

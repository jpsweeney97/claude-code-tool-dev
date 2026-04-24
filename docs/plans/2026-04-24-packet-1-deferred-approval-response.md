# Packet 1: Deferred Same-Turn Approval Response — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Ticket:** T-20260423-02 — `docs/tickets/2026-04-23-deferred-same-turn-approval-response.md`
**Spec:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md` (2440 lines, commit `64608b01` on branch `feature/delegate-deferred-approval-response`)
**Branch:** `feature/delegate-deferred-approval-response`

**Goal:** Convert the `codex.delegate` control plane from synchronous capture-and-cancel to an async-decide worker-thread model so a captured approval request can stay parked for operator response and receive a same-turn reply via `codex.delegate.decide`, without the original turn being torn down.

**Architecture:** A new **worker thread per deferred-approval turn** takes exclusive session ownership (IO-1) and coordinates with the main MCP thread through a **ResolutionRegistry** — an in-memory two-channel primitive with per-request wake signals (operator decide / timeout / internal abort) and per-job capture-ready signals (worker announces park / completion / unknown / worker-failed / start-wait elapsed). `_finalize_turn` gains a **Captured-Request Terminal Guard** that reads the request store exactly once (one-snapshot invariant) and maps terminal request states directly to `DelegationJob.status`, bypassing kind-based re-escalation of requests the worker already resolved. `JobStatus` expands from 6 to 7 literals (adds `"canceled"`) with 14+ propagation touch points. A private typed exception `_WorkerTerminalBranchSignal(reason)` raised by the server-request handler terminalizes the worker turn cleanly without entering `_finalize_turn`, avoiding double-cleanup and re-escalation of already-terminal requests.

**Tech Stack:** Python 3.12+, `dataclasses`, `typing.Literal`, `threading.Lock`/`threading.Event`, append-only JSONL stores with OS-level append atomicity (IO-4 fsync), existing `pytest` + `uv` harness. No new external dependencies.

---

## Scope Check

This plan covers Packet 1 as defined in the spec — a single cohesive refactor of the delegation control plane. The pieces (types, stores, registry, worker, finalizer, contracts) are tightly coupled and cannot land independently, but the plan is divided into **eight build phases** so implementation can pause at natural checkpoints where tests pass and the tree is consistent:

| Phase | Tasks | Landing invariant | File |
|-------|-------|-------------------|------|
| **A: Type foundations** | 1-5 | All new types, literals, and exception classes compile and round-trip | [phase-a-types.md](2026-04-24-packet-1-deferred-approval-response/phase-a-types.md) |
| **B: Store layer** | 6-9 | PendingServerRequest/DelegationJob have new fields + mutators; JSONL round-trips pass | [phase-b-stores.md](2026-04-24-packet-1-deferred-approval-response/phase-b-stores.md) |
| **C: Journal** | 10 | Journal validator admits `decision=None`; `completion_origin` field round-trips | [phase-c-journal.md](2026-04-24-packet-1-deferred-approval-response/phase-c-journal.md) |
| **D: Coordination primitive** | 11-12 | `ResolutionRegistry` standalone unit tests pass | [phase-d-registry.md](2026-04-24-packet-1-deferred-approval-response/phase-d-registry.md) |
| **E: Serialization + projection** | 13-14 | New `DelegationDecisionResult` shape + MCP serialization; projection guard surfaces `UnknownKindInEscalationProjection` | [phase-e-serialization-projection.md](2026-04-24-packet-1-deferred-approval-response/phase-e-serialization-projection.md) |
| **F: Worker execution model** | 15-16 | `_execute_live_turn` runs under worker thread; handler paths emit correct sentinels | [phase-f-worker.md](2026-04-24-packet-1-deferred-approval-response/phase-f-worker.md) |
| **G: Public API rewrite** | 17-18 | `decide()` and `start()` honor the new async contract; end-to-end tests pass | [phase-g-public-api.md](2026-04-24-packet-1-deferred-approval-response/phase-g-public-api.md) |
| **H: Finalizer guard + consumer surfaces** | 19-22 | `_finalize_turn` terminal guard lands; `poll()`, `discard()`, contracts aligned | [phase-h-finalizer-consumers-contracts.md](2026-04-24-packet-1-deferred-approval-response/phase-h-finalizer-consumers-contracts.md) |

Inside each phase, tasks follow TDD discipline: write failing test → run it → implement → run it → commit. Each step is 2-5 minutes. **Task numbers are global and stable across files** — Task 7 in `phase-b-stores.md` is the same Task 7 referenced anywhere else.

## Named Invariants (carry-forward from spec)

Every task must preserve these five invariants (see spec §Named Invariants for rationale). Any implementation step that would violate one is a spec violation and an implementation bug.

| Invariant | Summary |
|-----------|---------|
| **IO-1** | Worker thread exclusively owns its `AppServerRuntimeSession` and `JsonRpcClient` for the lifetime of its turn. Main thread never calls session methods. |
| **IO-2** | Registry is the ONLY in-memory mutable state crossing threads. Stores are durable cross-thread observation surfaces under IO-3's single-writer discipline. |
| **IO-3** | Single writer per store at any instant. The busy-gate at `delegation_controller.py:328-349` enforces at most one worker per session. |
| **IO-4** | Durable journal / store writes use `open("a")` + `flush()` + `os.fsync()`. Audit events are NOT fsynced (IO-5). |
| **IO-5** | `append_audit_event` is best-effort; NEVER placed inside a critical section that gates worker wake or durable state transitions. |
| **OB-1** | Durable fields reflect only what the plugin locally observed. Transport success ≠ semantic application. `canceled` = verified cancel; `unknown` = unverified transport. |

Plus the **one-snapshot invariant** introduced by R14 (spec §_finalize_turn Captured-Request Terminal Guard): only one `pending_request_store.get(captured_request.request_id).status` read may participate in final-status derivation per captured-request path.

## Structural invariants that must survive every task

Per R14 handoff: these tables and counts must NOT be silently altered. Task self-check after each commit: the count is preserved.

| Invariant | Spec location | Count |
|-----------|--------------|-------|
| Sentinel raise-sites table rows | §Worker terminal-branch signaling primitive | 6 |
| Request-to-job terminal mapping table rows | §_finalize_turn Captured-Request Terminal Guard | 4 |
| "Which paths hit the finalizer" path table rows | §_finalize_turn Captured-Request Terminal Guard | 9 |
| §JobStatus='canceled' propagation touch points | §JobStatus='canceled' propagation | 14-15 |
| §contracts.md updates sub-sections | §contracts.md updates | 5 |
| §Captured-Request Terminal Guard test bullets | §_finalize_turn Captured-Request Terminal Guard | 6 |

---

## File Structure

Files created or modified during Packet 1. Each file has a single clear responsibility; splits are driven by cross-thread ownership (registry is cross-thread mutable; worker is per-turn; controller is MCP-request dispatch).

**Files to create:**

| Path | Responsibility |
|------|----------------|
| `packages/plugins/codex-collaboration/server/resolution_registry.py` | `ResolutionRegistry`, `ReservationToken`, `DecisionResolution`, `InternalAbort`, `CaptureReadyEvent`, `Parked`/`TurnCompletedWithoutCapture`/`TurnTerminalWithoutEscalation`/`WorkerFailed`/`StartWaitElapsed` sum type. The in-memory two-channel cross-thread primitive (IO-2). Has its own locks and timer lifecycle. |
| `packages/plugins/codex-collaboration/server/worker_runner.py` | `_WorkerRunner` — the worker thread's entry function. Invokes `_execute_live_turn`, translates return value / exception into `announce_*` signals, owns the worker-side try/except that converts unhandled exceptions to `announce_worker_failed`. |
| `packages/plugins/codex-collaboration/tests/test_*.py` (17 new files, unit-style — flat layout) | Per-task unit test coverage: models canceled-status, escalatable-kind, sanitization, exceptions, worker-terminal-branch-signal, pending-server-request fields + mutator groups, delegation-job parked_request_id, journal completion_origin, resolution_registry (per-request + capture-ready split), delegation_decision_result shape, projection helpers, worker runner, finalize-turn terminal guard, discard canceled. See each phase file's `**Files:**` sections for the exact per-task test path. |
| `packages/plugins/codex-collaboration/tests/test_*_integration.py` (5 new files, integration-style per project `_integration.py` naming convention) | Per-task integration coverage: MCP decide response shape, handler branches (6 sentinel raises), `start()` async (`wait_for_parked` variants), `decide()` async (reservation rollback), poll projection guard. See each phase file's `**Files:**` sections for the exact per-task test path. |

**Files to modify:**

| Path | Change summary |
|------|----------------|
| `packages/plugins/codex-collaboration/server/models.py` | Add `"canceled"` to `JobStatus` and `DelegationTerminalStatus` literals. Add `EscalatableRequestKind` literal. Narrow `PendingEscalationView.kind` to `EscalatableRequestKind`. Add 11 new fields to `PendingServerRequest`. Add `parked_request_id` to `DelegationJob`. Rewrite `DelegationDecisionResult` to the new 3-field shape. Add `completion_origin` field to `OperationJournalEntry`. |
| `packages/plugins/codex-collaboration/server/pending_request_store.py` | Add 6 new mutators (`mark_resolved`, `record_response_dispatch`, `record_protocol_echo`, `record_timeout`, `record_dispatch_failure`, `record_internal_abort`). Add 6 replay ops for the new records. |
| `packages/plugins/codex-collaboration/server/delegation_job_store.py` | Add `update_parked_request` mutator. Verify `list_user_attention_required` includes `"canceled"` without change (rule: `promotion_state not in _TERMINAL_PROMOTION_STATES and not (status == "completed" and promotion_state is None)` already admits canceled with null promotion_state). |
| `packages/plugins/codex-collaboration/server/journal.py` | Relax `approval_resolution` schema for `decision=None` on `intent` and `dispatched` phases. Add `completion_origin` round-trip. |
| `packages/plugins/codex-collaboration/server/delegation_controller.py` | Major rewrite: expand `_TERMINAL_STATUS_MAP` (+1 row). Add `DelegationStartError`, `UnknownKindInEscalationProjection`, `_WorkerTerminalBranchSignal` exception types. Add sanitization helper. Expand `_load_or_materialize_inspection` tuple. Rewrite `_execute_live_turn` to spawn worker thread and catch sentinel. Rewrite handler to use registry and raise sentinels. Rewrite `_project_request_to_view` / `_project_pending_escalation`. Rewrite `decide()` with reservation context manager. Rewrite `start()` with capture-ready handshake. Rewrite `_finalize_turn` with Captured-Request Terminal Guard. Update `poll()` with `UnknownKindInEscalationProjection` catch. Expand `discard()` gate for `"canceled"`. Update `recover_startup` terminal-status set. |
| `packages/plugins/codex-collaboration/server/mcp_server.py` | Remove custom `DelegationDecisionResult` serializer branch at `:505-516`; fall through to generic `asdict(result)`. |
| `docs/superpowers/specs/codex-collaboration/contracts.md` | Update 5 sections: §decide (async model), §Start (success-union documentation), §Pending Escalation View (kind enum narrowing), §DelegationJob.status + §active_delegation.status (add `canceled`), §discard (admit `canceled`). |

---

## Pre-Execution Notes

### Implementer contract for Tasks 10, 16–20 test bodies

Tasks 10 (Step 10.7a recovery test), 16, 17, 18, 19, and 20 contain tests whose **names and docstrings are concrete** but whose **bodies are placeholders** — either `pass` stubs (Tasks 16–20) or a `pytest.fail(...)` guard with a concrete arrange/act/assert docstring (Task 10 Step 10.7a). See §Note on integration test bodies below for the full rationale.

**Contract for implementers (and for subagents dispatched on Phase F, G, or H):**

1. **Treat each docstring as the test specification.** The docstring prescribes ordering, stub emission sequences, and assertion targets. It is not optional commentary.
2. **Author concrete harness bodies** from docstrings plus the spec sequence diagrams at spec §Happy path / §Timeout path / §Dispatch failure path / §Internal abort coordination. Those diagrams prescribe exact orderings the test must exercise.
3. **Review authored test bodies as implementation, NOT as already-specified code.** They carry the same reviewer scrutiny as production code for invariant preservation, stub fidelity, ordering assertions, and cleanup. A test body is `pass` at plan-time; that does not grant approval-at-plan-time.
4. **If the docstring is ambiguous:** re-read the spec section named in the task's "Spec anchor" line. Do NOT fabricate assertions the spec does not prescribe.

Affected tasks:

- **Task 10 Step 10.7a** (Phase C) — recovery read-side audit: closes orphaned `approval_resolution.intent` with `decision=None` without raising; body is a `pytest.fail(...)` guard with concrete arrange/act/assert docstring
- **Task 16** (Phase F) — handler sentinel-raise tests across 6 branches
- **Task 17** (Phase G) — `start()` `wait_for_parked` variants across 5 `ParkedCaptureResult` outcomes
- **Task 18** (Phase G) — `decide()` reservation context manager rollback paths
- **Task 19** (Phase H) — one-snapshot invariant tests + 4-row terminal mapping tests + D4 suppression test
- **Task 20** (Phase H) — `poll()` `UnknownKindInEscalationProjection` catch + `signal_internal_abort` test

### Phase ordering and coupling

Execute phases sequentially: A → B → C → D → E → F → G → H. Tasks 15–19 are the tightest coupling cluster and the R13/R14 landing point; expect coordinator review scrutiny to be heaviest there.

### Modularization note

This plan was written as a single 6155-line monolithic file on 2026-04-24 and split the same day into a manifest plus 8 phase files. **Task numbers are global and stable** across files. Each phase file carries a parent-manifest link; each task preserves its original TDD step numbering. No semantic edits were made during the split — only the `sed -n 'X,Yp'`-extracted task content plus a thin navigational header per phase.

---

## Final Verification

After all 22 tasks land, run the full suite and manual checklist.

- [ ] **Final 1: Run the full test suite**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests -v 2>&1 | tail -40
```

Expected: all PASS.

- [ ] **Final 2: Type check**

```bash
uv run --package codex-collaboration mypy packages/plugins/codex-collaboration/server/
```

Expected: no errors. If `EscalatableRequestKind` narrowing flags any cast issues in `_project_request_to_view`, the fix is `cast(EscalatableRequestKind, request.kind)` after the guard.

- [ ] **Final 3: Structural invariant check**

```bash
# 6 sentinel raise sites
rg "_WorkerTerminalBranchSignal\(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l
# Expected: 6

# 4-row terminal mapping (verify the table exists in spec — in code, 3 explicit branches for
# resolved+completed, resolved+non-completed, canceled; pending/None fall-through is the 4th row)
grep -c "request_snapshot.status" packages/plugins/codex-collaboration/server/delegation_controller.py
# Expected: at least 1 definitive read + downstream conditionals

# 14-15 touch points for "canceled" propagation
rg '"canceled"' packages/plugins/codex-collaboration/server/ | wc -l
# Expected: ≥ 14 (models Literal, _TERMINAL_STATUS_MAP, _load_or_materialize_inspection tuple, discard gate, etc.)
```

- [ ] **Final 4: No Packet 1 regression in the existing dialogue plugin paths**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_dialogue.py packages/plugins/codex-collaboration/tests/test_dialogue_integration.py packages/plugins/codex-collaboration/tests/test_dialogue_profiles.py -v
```

Expected: all PASS. Dialogue uses a separate controller; Packet 1 must not touch it. (These are the three actual dialogue-related test files in the flat `tests/` layout — `test_dialogue.py`, `test_dialogue_integration.py`, and `test_dialogue_profiles.py`.)

- [ ] **Final 5: Integration smoke**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests -v -k integration
```

Expected: all PASS, including the new Packet 1 integration tests (`test_mcp_decide_response_shape_integration.py`, `test_handler_branches_integration.py`, `test_delegate_start_async_integration.py`, `test_delegate_decide_async_integration.py`, `test_poll_projection_guard_integration.py`) alongside the existing `test_delegate_start_integration.py` and `test_dialogue_integration.py`. The `-k integration` filter selects by filename substring per the project's `_integration.py` naming convention.

---

## Note on integration test bodies

Tasks 10 (Step 10.7a), 16, 17, 18, 19, and 20 contain tests whose **names and docstrings are concrete** (they specify the exact behavior to verify) but whose **bodies are placeholders** — `pass` stubs for Tasks 16–20 (integration tests) and a `pytest.fail(...)` guard with a concrete arrange/act/assert docstring for Task 10 Step 10.7a (the recovery read-side audit, which has a smaller fixture surface but still requires implementer-authored wiring using the existing `_build_controller` + `OperationJournalEntry` recovery-test pattern in `tests/test_delegation_controller.py` — see the sibling `test_recover_startup_marks_intent_only_approval_resolution_unknown` at line 2129). This is a deliberate pragmatic deviation from strict writing-plans discipline. Rationale:

- Each integration test requires a substantial **`app_server_runtime_stub`** harness that can emit specific notification sequences on command (e.g., "emit a command_approval server-request, wait for respond(), then emit turn/completed(status=completed)"). Writing that harness inline across 30+ test bodies would add 1000+ lines to this already-large plan, with heavy duplication.
- The **per-task integration fixtures** that implementers write (`delegation_controller_fixture`, `app_server_runtime_stub`, `pending_request_store_factory`, `simple_job_factory`, `resolution_registry_spy`, etc.) are expected to exist in `conftest.py` per the existing test patterns — implementers instantiate them per test.
- The **docstring of each test is the behavioral specification**. Implementers translate the docstring into concrete stub-emit sequences + poll-assertion chains.

If an implementer finds a test body ambiguous from the docstring alone, the canonical resolution is to re-read the spec section named in the task's "Spec anchor" line and the sequence-diagrams in §Happy path / §Timeout path / §Dispatch failure path / §Internal abort coordination. Those diagrams prescribe the exact ordering the test must exercise.

## Remember

- **One-snapshot invariant (R14)**: exactly ONE `pending_request_store.get(rid).status` read per captured-request path in `_finalize_turn`. Hydration reads for non-status fields are OK only if they use a distinct access pattern.
- **OB-1 honesty**: `"canceled"` = verified cancel (interrupt acked OR respond({cancel}) acked). `"unknown"` = unverified transport outcome. Never collapse one into the other.
- **IO-1 session ownership**: main thread NEVER touches the worker's session.
- **IO-3 single-writer discipline**: worker owns `pending_request_store` writes + its own `DelegationJob` row; main owns `approval_resolution.intent` on the operator-decide path only.
- **Audit is best-effort (IO-5)**: `append_audit_event` must never gate worker wake or durable transitions. Wrap in `try/except` that logs and continues.
- **Commit after each task**. Every task ends with its own commit — never batch across tasks.
- **Preserve invariants after each commit**: sentinel raise-sites (6), terminal mapping (4 rows), path table (9 rows), canceled propagation touch points (14-15), §contracts.md updates (5 sections), §Captured-Request Terminal Guard tests (6).

End of plan.

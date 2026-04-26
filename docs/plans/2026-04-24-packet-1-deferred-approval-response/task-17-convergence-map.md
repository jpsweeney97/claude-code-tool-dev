# Convergence Map — Phase G Task 17 (`start()` rewrite — `wait_for_parked` + 5 ParkedCaptureResult variants + 23 Bucket A unskips post-L13)

**Drafted:** 2026-04-26 (controller + user two-read protocol; 24+11 unblock-bucket adjudication landed pre-draft). **Amended:** 2026-04-26 post-feat (commit `8dd15971`) — see L11/L12/L13 + Post-implementer adjudication record. Effective post-L13 counts are 23 Bucket A + 12 Bucket B.
**Authority order:**
1. Spec §Capture-ready handshake: `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:659-910`
2. Spec §DelegationStartError reasons: `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:622-657`
3. Phase G Task 17 plan: `docs/plans/2026-04-24-packet-1-deferred-approval-response/phase-g-public-api.md:11-286`
4. Carry-forward F16.2 (26-test list, with Task-17/18 split adjudicated this session) + 8 Mode A/B from Task 14 + 1 L10 barrier from Task 16
5. Live code: dispatch-time HEAD was `f3cfa61a`; current HEAD is `8dd15971` (Task 17 feat commit). Live-anchor line numbers in the table below describe the **pre-feat** orientation that the implementer was given at dispatch — they are NOT refreshed against the post-feat tree because the spec reviewer needs both views (the pre-feat anchors are the dispatch-contract reference; the feat commit's diff is the substantive evidence).

Plan-line numbers throughout `phase-g-public-api.md` Task 17 body (esp. the "around `:608-625`" reference for `start()`) are stale — `start()` is at `:386` (pre-feat anchor). Use the **live anchors** below.

## Live anchors (verified 2026-04-26 at pre-feat HEAD `f3cfa61a` — NOT refreshed after feat commit `8dd15971`)

| Symbol | File:line |
|--------|-----------|
| `DelegationController.start` def (TARGET FOR REWRITE) | `delegation_controller.py:386` |
| Synchronous `_execute_live_turn(...)` call inside `start()` (REPLACE WITH `spawn_worker` + `wait_for_parked` + `_dispatch_parked_capture_outcome`) | `delegation_controller.py:737` |
| `_execute_live_turn` def | `delegation_controller.py:745` |
| `_execute_live_turn` decide-resume callsite (DO NOT MODIFY — Task 18) | `delegation_controller.py:2484` |
| `DelegationController.decide` def (DO NOT MODIFY — Task 18) | `delegation_controller.py:2287` |
| `DelegationController.__init__` (already has `self._registry: ResolutionRegistry = ResolutionRegistry()` from Task 16) | `delegation_controller.py:384` |
| Module constant `_APPROVAL_OPERATOR_WINDOW_SECONDS = 900` (place new `START_OUTCOME_WAIT_SECONDS` near here) | `delegation_controller.py:107` |
| Existing imports from `.resolution_registry` (only 3 names — Task 17 ADDS 6 more) | `delegation_controller.py:102` |
| Existing import: `cast` (do NOT re-add) | `delegation_controller.py:64` |
| Existing import: `EscalatableRequestKind` (do NOT re-add) | `delegation_controller.py:90` |
| `_project_pending_escalation` helper (called from `Parked` dispatch) | `delegation_controller.py:1581` |
| `DelegationEscalation` dataclass (`agent_context: str | None = None` already supported) | `models.py:442-453` |
| `_finalize_turn` def (DO NOT MODIFY — Task 19) | `delegation_controller.py:1611` |
| Sentinel catch in `_execute_live_turn` (Task 16; preserve as-is) | `delegation_controller.py:845` |
| 6 sentinel raise sites (W5 invariant — count stays at 6) | `delegation_controller.py:839, 975, 1088, 1378, 1442, 1494` (post-Task-16-fix line numbers; locate via `grep -nF "_WorkerTerminalBranchSignal(reason="`) |
| `spawn_worker` helper (Task 15; called from Task 17's start()) | `worker_runner.py:92-116` |
| `_WorkerRunner.run` (already daemon-thread + announce_worker_failed on uncaught exc) | `worker_runner.py:57-89` |
| `ResolutionRegistry.wait_for_parked` (5-variant return; pop-on-return lifecycle) | `resolution_registry.py:351-389` |
| `ResolutionRegistry.signal_internal_abort` (called from `Parked` invariant-violation branch) | `resolution_registry.py:290-306` |
| `ResolutionRegistry.register` daemon timer (timer thread daemon=True) | `resolution_registry.py:202-206` |
| `_TASK_17_DEADLOCK_REASON` constant in test_delegation_controller.py (RENAME) | `test_delegation_controller.py:43-50` |
| `_TASK_17_DEADLOCK_REASON` constant in test_delegate_start_integration.py (RENAME) | `test_delegate_start_integration.py:31-38` |
| Existing `test_delegate_start_integration.py` (do NOT collide; new file is `test_delegate_start_async_integration.py`) | `test_delegate_start_integration.py` |

## Locks (binding positive scope)

- **L1 — 35 Task-17-cited skips split, post-L13: 23 Task 17 removals + 12 Task 18 carry-forward.** (Dispatch-time framing was 24 + 11; the post-feat L13 reclassification of `test_delegation_controller.py:1522` moved 1 from Bucket A to Bucket B.) Per-test classification in the triage table below. Task 17 feat commit `8dd15971` removed 23 decorators; 12 remain in place with REVISED reason citing Phase G Task 18 (`_TASK_18_DECIDE_SIGNAL_REASON`). The "carry-forward" framing preserves audit discipline: Bucket B tests stay skipped not because they would all certainly fail under legacy `decide()`, but because their assertion shape requires Task 18's `reserve` + `commit_signal` mechanism to provide the canonical green path. A subset of Bucket B tests (e.g., `decide(deny)` flows that local-finalize at `delegation_controller.py:2446`) might mechanically pass under legacy behavior — that would be coincidental green for the wrong code path, not Task 17 acceptance evidence.

- **L2 — `start()` rewrite replaces ONLY the synchronous `_execute_live_turn(...)` call.** Live anchor: `delegation_controller.py:737`. The committed-start phase above it (worktree, runtime, journal phases 1-3) is unchanged. Replacement substitutes `spawn_worker(...)` + `self._registry.wait_for_parked(job_id, timeout_seconds=START_OUTCOME_WAIT_SECONDS)` + dispatch to a new `_dispatch_parked_capture_outcome(...)` helper. The `_execute_live_turn` function itself stays untouched at `:745`; it now runs on the worker thread inside `_WorkerRunner.run()` (`worker_runner.py:63`).

- **L3 — `START_OUTCOME_WAIT_SECONDS = 30` module constant added near `_APPROVAL_OPERATOR_WINDOW_SECONDS` at `:107`.** Default 30 seconds matches Phase G plan body. Type annotation: `float`. No env-var override under Task 17 (deferred polish).

- **L4 — `_dispatch_parked_capture_outcome` helper has exhaustive `match` over all 5 `ParkedCaptureResult` variants.** Signature: `def _dispatch_parked_capture_outcome(self, *, outcome: ParkedCaptureResult, job_id: str, collaboration_id: str) -> DelegationJob | DelegationEscalation`. Each `case` arm is explicit (no `case _:` fall-through). For type-narrowing safety, place `from typing import assert_never` import + `case _: assert_never(outcome)` as the final arm so Pyright catches missing variants at compile time AND runtime catches a non-exhaustive ParkedCaptureResult union if it's ever extended. The 5 cases:

  1. `case Parked(request_id=request_id):` — **Order is fixed by live `_project_pending_escalation(self, job: DelegationJob)` signature at `delegation_controller.py:1581-1583` (it takes the JOB, not the request_id):** (a) `job = self._job_store.get(job_id)`; (b) `assert job is not None` (registry invariant: Parked implies job exists); (c) call `self._project_pending_escalation(job)` inside a **narrow** `try/except UnknownKindInEscalationProjection` (the specific exception the helper docstring at `:1587-1593` promises to re-raise); (d) on `UnknownKindInEscalationProjection` OR `None` return, call `self._registry.signal_internal_abort(request_id, reason="parked_projection_invariant_violation")` then raise `DelegationStartError(reason="parked_projection_invariant_violation", cause=None)`; (e) on valid view, return `DelegationEscalation(job, pending_escalation, agent_context=None)`. Both invariant-violation sub-cases use the SAME broad `parked_projection_invariant_violation` reason (per spec §Capture-ready handshake). **Do NOT use bare `except Exception:`** — would mask unrelated bugs as protocol-invariant violations and violate the helper's documented catch-contract handoff.
  2. `case TurnCompletedWithoutCapture():` — Return `_job_store.get(job_id)`. Assert non-None (registry invariant: worker doesn't fire announce_turn_completed_empty without a created job).
  3. `case TurnTerminalWithoutEscalation(job_status, reason, request_id):` — Return `_job_store.get(job_id)`. Assert non-None.
  4. `case WorkerFailed(error=exc):` — Reason-preservation: if `isinstance(exc, DelegationStartError) and exc.reason`, re-raise `exc` directly. Otherwise raise `DelegationStartError(reason="worker_failed_before_capture", cause=exc)`.
  5. `case StartWaitElapsed():` — `logger.warning(...)`, return `_job_store.get(job_id)` (status="running"). Assert non-None.

- **L5 — Imports added to `delegation_controller.py:102` (existing line) — 6 new names from `.resolution_registry`.** New imports: `Parked, ParkedCaptureResult, StartWaitElapsed, TurnCompletedWithoutCapture, TurnTerminalWithoutEscalation, WorkerFailed`. The current line is `from .resolution_registry import DecisionResolution, InternalAbort, ResolutionRegistry` — extend it; do NOT duplicate the existing 3 names. Also import `assert_never` from `typing` (already imports `cast` at `:64`; verify `assert_never` is not yet imported before adding).

  Also add at module level: `from .worker_runner import spawn_worker` (new import; not currently imported per Task 16 closeout).

- **L6 — `_TASK_17_DEADLOCK_REASON` constant in BOTH test files RENAMED to `_TASK_18_DECIDE_SIGNAL_REASON` with revised reason text.** Per-module pattern preserved (no shared cross-test helper). New text:
  ```python
  _TASK_18_DECIDE_SIGNAL_REASON = (
      "Phase G Task 18: decide() does not yet route through "
      "ResolutionRegistry.reserve() + commit_signal(). Without "
      "commit_signal, the worker stays parked in registry.wait() and "
      "decide(approve)/decide(deny)/decide(re-escalate)/CAS-stale paths "
      "cannot signal the worker through the canonical Task-18 mechanism. "
      "Some assertions might mechanically pass under legacy decide() "
      "(e.g., deny local-finalization at delegation_controller.py:~2446) "
      "but would do so via the old non-async-decide code path. Skip is "
      "preserved for audit discipline: Task 18's reserve+commit_signal "
      "is the canonical signal mechanism for these assertions."
  )
  ```
  The 12 Bucket B decorators (post-L13 — see Bucket B subtotal in triage table) all retain their `@pytest.mark.skip(...)` and all end with `reason=_TASK_18_DECIDE_SIGNAL_REASON` after Task 17, but they reach that post-state via TWO distinct mechanical operations:

  | Sub-class | Count | Pre-state reason | Operation |
  |---|---|---|---|
  | Constant-backed Bucket B | 9 (8 originally classified + 1 reclassified per L13: `test_delegation_controller.py:1522`) | `reason=_TASK_17_DEADLOCK_REASON` | Updated automatically by the constant rename in their respective files (no per-decorator edits). |
  | Callsite-specific Mode A Bucket B | 3 (`test_delegation_controller.py:1761`, `:2406`; `test_delegate_start_integration.py:1077`) | Hand-written callsite-specific reason strings (NOT the shared constant) | MUST be EXPLICITLY rewritten to `reason=_TASK_18_DECIDE_SIGNAL_REASON`. Constant rename alone will leave them stale. |

  A pure constant-rename pass is insufficient. The 12-retention audit (`grep ... "@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)"`, expected 12 post-L13 — was 11 in the dispatch-time target) only passes once both operations execute. (Dispatch-time framing was 11 retained = 8 + 3; post-L13 effective is 12 = 9 + 3.)

- **L7 — Worker-failure reason-preservation rule.** When the worker raises `DelegationStartError(reason="X", cause=Y)` from a pre-capture path (e.g., `unknown_kind_interrupt_transport_failure`), `_WorkerRunner.run` catches as `Exception` and calls `announce_worker_failed(error=that_exception)`. Task 17's `WorkerFailed` dispatch arm MUST detect the `DelegationStartError` instance and re-raise it preserving the original `reason`. Fallback `worker_failed_before_capture` is ONLY for non-DelegationStartError uncaught exceptions.

- **L8 — Parked-projection invariant-violation MUST signal the worker before raising on the main thread.** Sequence (atomic from main-thread perspective): (a) call `self._registry.signal_internal_abort(request_id, reason="parked_projection_invariant_violation")` to wake the worker from `registry.wait(...)`; (b) raise `DelegationStartError(reason="parked_projection_invariant_violation", cause=None)`. The worker, upon waking with `InternalAbort`, will execute its internal-abort sentinel branch (record_internal_abort + sentinel raise) per Task 16's L7 production work. Skipping the signal_internal_abort call would leak the parked worker indefinitely.

- **L9 — New file `tests/test_delegate_start_async_integration.py`.** Distinct from existing `tests/test_delegate_start_integration.py` (verified via `ls`). 8 acceptance tests covering all 5 ParkedCaptureResult variants + 2 invariant-violation sub-cases (null-projection + raise-projection) + 1 reason-preservation. Use module-local helpers (W4); do NOT use `delegation_controller_fixture` / `app_server_runtime_stub` plan placeholders.

- **L10 — Decorator removal scope: 24 originally-planned removals reduced to 23 effective removals after post-feat reclassification (see L13).**

  | Mechanism | Originally planned | Effective post-feat | Composition |
  |---|---|---|---|
  | `_TASK_17_DEADLOCK_REASON` constant-backed | 18 | **17** (1 reclassified — see L13) | Originally: 8 F16.2 start (`test_delegation_controller.py:430, :1336, :1413, :1522, :1584, :1630, :1693, :2568`) + 7 F16.2 decide_rejects_* (`:1892, :1919, :1942, :2009, :2031, :2068, :2091`) + 3 F16.2 start E2E (`test_delegate_start_integration.py:564, :681, :1034`). After L13: `test_delegation_controller.py:1522` (`test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up`) reclassified as Bucket B; decorator retained with new constant. |
  | Callsite-specific reason string | 6 | 6 | 3 Mode A (`test_delegation_controller.py:1377, :1436` + `test_delegate_start_integration.py:628`) + 2 Mode B (`test_delegation_controller.py:2626` + `test_delegate_start_integration.py:805`) + 1 L10 barrier (`test_handler_branches_integration.py:539`) |
  | **Total** | **24** | **23** | Effective Bucket A removals after L13 reclassification. |

  Mechanism counts matter for the implementer's edit operation; ownership-class counts (F16.2 / Mode A / Mode B / L10) matter for carry-forward closure accounting (separate concern; see Carry-forward expectations section).

- **L11 (ADDED 2026-04-26 per Task 17 BLOCKED adjudication) — `_finalize_turn` D4 carve-out for unknown-kind.** Authority: spec §Unknown-kind contract at `design.md:1705-1736` (specifically lines 1725-1727 listing the Packet 1 line edits). Test-author confirmation: `test_handler_branches_integration.py:547-549` directly attributes the carve-out to Task 17. The existing `_CANCEL_CAPABLE_KINDS`-branch entry currently reads `if captured_request.kind in _CANCEL_CAPABLE_KINDS or interrupted_by_unknown:`. Task 17 MUST split that into two branches:

  ```python
  if interrupted_by_unknown:
      final_status = "unknown"
      # Fall through to the existing non-escalation return at :1512-1517
      # (_emit_terminal_outcome_if_needed, release runtime, close session,
      # return the unknown-terminal job). The worker has already persisted
      # status='unknown' via _persist_job_transition (Task 16 L10); this
      # branch ensures _finalize_turn does NOT call _project_request_to_view
      # for kind='unknown' (which would raise UnknownKindInEscalationProjection).
  elif captured_request.kind in _CANCEL_CAPABLE_KINDS:
      final_status = "needs_escalation"
      # ... existing projection + escalation build (UNCHANGED — Task 19 territory).
  ```

  Bound the change tightly:
  - Split the entry condition so `interrupted_by_unknown` no longer participates in the `_CANCEL_CAPABLE_KINDS`-branch's terminal-mapping logic.
  - Route `interrupted_by_unknown` to `final_status="unknown"` and let it flow to the EXISTING non-escalation return at `:1512-1517` (do NOT bypass `_emit_terminal_outcome_if_needed` / runtime release / session close — that would skip post-turn cleanup).
  - Do NOT touch the `_CANCEL_CAPABLE_KINDS` branch body (W2 — Task 19's terminal-guard rewrite domain).
  - Do NOT implement the one-snapshot rule, Request-to-job terminal mapping table, or D4 blind-write suppression (spec §`_finalize_turn` Captured-Request Terminal Guard, lines 1738-1808 — all Task 19 work).

  This carve-out unblocks 4 Bucket A tests: `test_unknown_kind_parse_failure_terminalizes_unknown` (L10 barrier at `test_handler_branches_integration.py:539`) plus the 3 Mode A unknown-kind tests at `test_delegation_controller.py:1377`, `:1436`, and `test_delegate_start_integration.py:628`.

- **L12 (ADDED 2026-04-26 post-feat — convergence-map gap closure) — Decorator removal implies assertion-shape update for tests originally written under the synchronous model.** L10 was incomplete: it specified the decorator-removal mechanism (18 constant-backed + 6 callsite-specific) but did NOT note that the affected tests' BODY assertions encode the pre-Packet-1 synchronous-model contract (e.g., `agent_context is not None` on `Parked`-path escalations, `result.job.status == "needs_escalation"` for unknown-kind paths, escalation-audit events fired during `start()`). Removing the skip decorator without updating these assertions would leave the tests failing under the new async model. The implementer (per feat commit `8dd15971`) updated assertion shapes inline as part of the decorator removals; this is the correct behavior even though L10 didn't make it explicit. Authority for the new assertion shapes:

  | New assertion | Spec authority |
  |---|---|
  | `agent_context=None` on `Parked`-path `DelegationEscalation` | `design.md:785-797` (deferred-escalation semantics: "the worker has not finalized its turn yet — it is blocking on `registry.wait(rid)`") |
  | Captured request status remains `"pending"` until `decide()` resumes worker | `design.md:786-797` + §`reserve()` + `commit_signal()` protocol |
  | Escalation audit events deferred (NOT emitted during `start()`) | `design.md:786-797` (audit emission attached to `_finalize_turn`, which now runs only after worker resume) |
  | Unknown-kind paths return `DelegationJob(status="unknown")` instead of `DelegationEscalation` | `design.md:1705-1736` + L11 carve-out |
  | `request_user_input` parks (returns `DelegationEscalation`) instead of synchronously completing | `design.md:659-910` (capture-ready handshake — all parkable kinds park; the synchronous-completion path is removed under Packet 1) |

  **Forward-looking rule for future tasks:** when a Lock specifies "remove skip decorator", the implementer MUST also verify the test body assertions match the post-task semantics. Assertion shapes that DIRECTLY mirror a spec section (per the table above) are implementer-discretion within the dispatch contract; assertion shapes that ADD new behavior or test new spec sections REQUIRE BLOCKED + adjudication.

- **L13 (ADDED 2026-04-26 post-feat — adjudicated retroactively per process-precedent record) — Bucket A→B reclassification permitted with controller adjudication.** The implementer (per feat commit `8dd15971`) reclassified `test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up` (`test_delegation_controller.py:1522` decorator → test body at `:1524`) from Bucket A (Task 17 unskip) to Bucket B (Task 18 unskip). Substantive justification is decisive: the test sabotages the SECOND `journal.append_audit_event` call (the escalation audit emit inside `_finalize_turn`); under the synchronous model that second call was reachable from `start()`, but under the new async model `_finalize_turn` runs on the worker thread AFTER `decide()` calls `commit_signal()` to resume — so the sabotaged failure path is unreachable from `start()` alone. Verifying this test requires Task 18's `reserve+commit_signal` mechanism. Reclassification stands.

  **Process precedent:** This reclassification SHOULD have been BLOCKED + asked rather than executed unilaterally. Future implementers must report BLOCKED for ANY bucket reclassification — even when the substantive reasoning is decisive — so that the controller updates the convergence map's binding counts BEFORE the feat commit lands. The L13 record exists to make the exception visible without normalizing the path.

## Watchpoints (binding negative scope)

- **W1 — Do NOT modify `decide()` body.** `delegation_controller.py:2287`. Phase G Task 18 owns the `reserve()` + `commit_signal()` rewrite. Including the early-rejection branches, the `_decided_request_ids` set, and the synchronous `_execute_live_turn` call at `:2484`.

- **W2 (NARROWED 2026-04-26 per Task 17 BLOCKED adjudication) — Do NOT modify `_finalize_turn`'s Captured-Request Terminal Guard logic.** That logic is the `_CANCEL_CAPABLE_KINDS`-branch terminal-status mapping, the one-snapshot rule, the Request-to-job terminal mapping table, and D4 blind-write suppression — spec §`_finalize_turn` Captured-Request Terminal Guard at `design.md:1738-1808`. `delegation_controller.py:1611+`. Phase H Task 19 owns that rewrite. **Carve-out:** the spec §Unknown-kind contract change at the `_CANCEL_CAPABLE_KINDS`-branch ENTRY (separating `interrupted_by_unknown` from `_CANCEL_CAPABLE_KINDS` and routing it to `final_status="unknown"`, spec `design.md:1725-1727`) IS in Task 17 scope — see L11. The original W2 was over-broad: it cited "Captured-Request Terminal Guard" in the rationale but worded the rule as blanket `_finalize_turn` non-modification, conflating two logically distinct spec sections.

- **W3 — Do NOT modify the 6 sentinel raise sites or their reasons.** Task 16 W7 invariant: `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `6` post-Task-17. Same 6 reasons: `internal_abort`, `dispatch_failed`, `timeout_interrupt_failed`, `timeout_interrupt_succeeded`, `timeout_cancel_dispatch_failed`, `unknown_kind_interrupt_transport_failure`.

- **W4 — Do NOT use plan-pseudocode fictional fixtures.** `delegation_controller_fixture`, `app_server_runtime_stub`, `journal_spy`, `audit_event_spy` do NOT exist in `tests/conftest.py`. Per Task 14/15/16 W4/W11 precedent: use module-local `_build_controller(tmp_path)` (importable from `tests.test_delegation_controller`) + built-in pytest fixtures (`monkeypatch`, `tmp_path`, `caplog`) + `unittest.mock.MagicMock`. The integration-test fixture surface in `tests/conftest.py` is intentionally minimal (only `vendored_schema_dir`, `client_request_schema`, `make_test_handle`).

- **W5 — Newly unskipped 23 Bucket A tests (post-L13; originally planned 24) intentionally leave parked workers blocked in `registry.wait()` — full-suite verification MUST confirm no pytest hang or test contamination.** This is the real post-Task-17 hang/resource risk, NOT the still-skipped 12 Bucket B tests (post-L13; originally planned 11) which don't execute. The mitigation is already in place: `worker_runner.py:113` sets `daemon=True` on the worker thread, and `resolution_registry.py:202-206` sets `daemon=True` on the per-request timer threads, so no thread blocks process exit. Verification protocol:
  1. After Task 17 feat commit, run full suite: `uv run --package codex-collaboration pytest -v`.
  2. Suite must complete in normal wall-clock time (~30s baseline; Task 16 was 38s for 968 tests).
  3. Pytest exit code must be 0; no `SIGTERM`/`KeyboardInterrupt`/timeout messages.
  4. Order-independence smoke from repo root: run BOTH orderings explicitly and compare results.
     ```bash
     uv run --package codex-collaboration pytest \
       packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
       packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
     uv run --package codex-collaboration pytest \
       packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py \
       packages/plugins/codex-collaboration/tests/test_delegation_controller.py
     ```
     Both invocations must yield exit code 0 with identical pass/skip counts. Confirms no inter-test contamination from leftover daemon threads. (Note: not a true randomized shuffle — `pytest-randomly` is not in the dev deps; two explicit orderings are the lightweight stand-in.)
  If any test from the newly-unskipped 23 (post-L13) hangs or contaminates: bucket misclassification (some Bucket A test actually needs Task 18) OR resource leak in `start()` rewrite (e.g., spawn_worker called without registering the entry, leaving wait_for_parked blocked).

- **W6 — Do NOT re-import `cast`, `EscalatableRequestKind`, `ResolutionRegistry`, `DecisionResolution`, `InternalAbort`.** All already imported per `:64`, `:90`, `:102`. Verify with `rg "^from \.resolution_registry" packages/plugins/codex-collaboration/server/delegation_controller.py` before adding new imports — extend the existing import line, do not add a duplicate `from .resolution_registry import ...`.

- **W7 — Plan-line numbers throughout `phase-g-public-api.md` Task 17 body are stale.** `start()` is at `:386` (plan cites "around `:608-625`"). Imports are at `:102` (plan doesn't anchor). Use the live anchors table above. Same trap as Task 16's W13.

- **W8 — Do NOT delete F16.1 decorators at `test_handler_branches_integration.py:161, 179`.** They cite Phase H Task 19 explicitly. Out of Task 17 scope per the user's "Keep F16.1's 2 skips out of Task 17" constraint.

- **W9 — Do NOT change Task 16 sentinel semantics or `__init__` registry init.** Task 16 already added `self._registry: ResolutionRegistry = ResolutionRegistry()` in `__init__` (`:384`). Task 17 USES `self._registry` from start(); does NOT re-init or shadow.

- **W10 — Pre-existing `runtime.py:270` Pyright error MUST NOT be "fixed" as side-effect of Task 17.** Per Task 16 G34 + L2 stash-test: this is `TurnStatus` literal narrowing pre-existing the entire Phase F work. Task 17 must not modify `runtime.py` at all unless plan-required (it isn't).

- **W11 — `_dispatch_parked_capture_outcome` MUST use exhaustive `match` with `assert_never` — no silent `case _:` fall-through.** Pyright + runtime safety. If `ParkedCaptureResult` is ever extended (e.g., a new `WorkerCanceled` variant in a future packet), the missing case becomes both a Pyright error AND a runtime exception, not a silent dispatch hole.

- **W12 — Plan Step 17.1's failing-test stubs use `pass` bodies under fictional fixtures.** Implementer must replace EVERY `pass` body with a real assertion shape (using module-local helpers per W4) before the file can be considered complete. Do NOT commit `pass`-bodied tests as Task 17 acceptance evidence.

- **W13 — Do NOT touch the existing single `DelegationEscalation` construction site at `delegation_controller.py:2240`.** That's the legacy synchronous escalation return path inside `_execute_live_turn`'s post-finalizer logic (called from decide-resume). Task 17 ADDS a new construction site inside `_dispatch_parked_capture_outcome`'s `Parked` arm. The legacy site stays in service for the decide-resume flow until Task 18 retires it.

## Branch matrix (5 ParkedCaptureResult variants × outcome)

| # | Variant | Worker source | `start()` returns | Side effects | Test coverage (new) |
|---|---------|---------------|-------------------|--------------|---------------------|
| 1 | `Parked(request_id)` | Worker emits `announce_parked` from inside `_server_request_handler` after capture | `DelegationEscalation(job, pending_escalation, agent_context=None)` | None on happy path; on projection raise OR null: `signal_internal_abort` then `raise DelegationStartError("parked_projection_invariant_violation", cause=None)` | `test_start_returns_escalation_on_parked` + `test_start_signals_internal_abort_on_parked_projection_null` + `test_start_signals_internal_abort_on_parked_projection_raise` |
| 2 | `TurnCompletedWithoutCapture()` | `_WorkerRunner.run` fallthrough after `_execute_live_turn` returns normally without handler-side announce | `_job_store.get(job_id)` (DelegationJob, status varies but typically `completed`) | None | `test_start_returns_plain_job_for_turn_completed_without_capture` |
| 3 | `TurnTerminalWithoutEscalation(job_status="unknown", reason, request_id)` | Worker emits from unknown-kind interrupt-success path (Task 16 L10 + plan Step 16.3) | `_job_store.get(job_id)` (DelegationJob, status="unknown") | None | `test_start_returns_plain_job_for_unknown_kind_parse_failure` |
| 4 | `WorkerFailed(error)` | `_WorkerRunner.run` catch on uncaught `Exception` → `announce_worker_failed(error=exc)` | `raise DelegationStartError(reason=preserved or "worker_failed_before_capture", cause=exc)` | None | `test_start_raises_for_worker_failed_before_capture` + `test_start_raises_with_reason_preservation_for_unknown_kind_interrupt` |
| 5 | `StartWaitElapsed()` | `wait_for_parked` budget elapses without any signal | `_job_store.get(job_id)` (DelegationJob, status="running") | `logger.warning("delegation.start: start-wait budget elapsed; returning running")` | `test_start_returns_running_job_on_start_wait_elapsed` |

**Variant exhaustion check:** `match` arms cover all 5; final `case _: assert_never(outcome)` is required per W11.

## Per-test triage

### Bucket A — Task 17 alone unblocks (23 decorators removed in feat commit `8dd15971`; originally 24 planned at dispatch, less 1 reclassified per L13)

| File:line | Class | Test name | Removal action |
|---|---|---|---|
| `test_handler_branches_integration.py:539` | L10 barrier (Task 16 discovery) | `test_unknown_kind_parse_failure_terminalizes_unknown` | Remove decorator (callsite-specific reason) |
| `test_delegation_controller.py:430` | F16.2 start | `test_start_returns_busy_response_when_active_job_exists` | Remove decorator (uses constant) |
| `test_delegation_controller.py:1336` | F16.2 start | `test_start_with_command_approval_returns_escalation` | Remove decorator (uses constant) |
| `test_delegation_controller.py:1377` | Mode A | `test_start_with_unknown_request_interrupts_and_escalates` | Remove decorator (callsite-specific reason) |
| `test_delegation_controller.py:1413` | F16.2 start | `test_start_with_two_requests_responds_to_both` | Remove decorator (uses constant) |
| `test_delegation_controller.py:1436` | Mode A | `test_start_with_unparseable_request_creates_minimal_causal_record` | Remove decorator (callsite-specific reason) |
| ~~`test_delegation_controller.py:1522`~~ | ~~F16.2 start~~ | ~~`test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up`~~ | **MOVED to Bucket B per L13** — see Bucket B table below |
| `test_delegation_controller.py:1584` | F16.2 start | `test_start_with_request_user_input_completed_returns_delegation_job` | Remove decorator (uses constant) |
| `test_delegation_controller.py:1630` | F16.2 start | `test_later_parse_failure_does_not_prevent_captured_request_resolution` | Remove decorator (uses constant) |
| `test_delegation_controller.py:1693` | F16.2 start | `test_start_escalation_keeps_execution_handle_active` | Remove decorator (uses constant; verified no decide call) |
| `test_delegation_controller.py:1892` | F16.2 reject | `test_decide_rejects_when_runtime_is_missing` | Remove decorator (uses constant; reach `runtime_unavailable` early-rejection at `:2387`) |
| `test_delegation_controller.py:1919` | F16.2 reject | `test_decide_rejects_invalid_decision_value` | Remove decorator (uses constant; reach `invalid_decision` at `:2295`) |
| `test_delegation_controller.py:1942` | F16.2 reject | `test_decide_request_user_input_requires_answers` | Remove decorator (uses constant; reach `answers_required` at `:2367+`) |
| `test_delegation_controller.py:2009` | F16.2 reject | `test_decide_rejects_request_not_found` | Remove decorator (uses constant; reach `request_not_found` at `:2326`) |
| `test_delegation_controller.py:2031` | F16.2 reject | `test_decide_rejects_request_job_mismatch` | Remove decorator (uses constant; reach `request_job_mismatch` at `:2335`) |
| `test_delegation_controller.py:2068` | F16.2 reject | `test_decide_rejects_deny_with_answers` | Remove decorator (uses constant; reach `answers_not_allowed` at `:2358`) |
| `test_delegation_controller.py:2091` | F16.2 reject | `test_decide_rejects_answers_for_non_request_user_input` | Remove decorator (uses constant; reach `answers_for_non_request_user_input` at `:2378`) |
| `test_delegation_controller.py:2568` | F16.2 start | `test_start_escalation_keeps_promotion_state_none` | Remove decorator (uses constant) |
| `test_delegation_controller.py:2626` | Mode B | `test_poll_needs_escalation_projects_pending_request_without_raw_ids` | Remove decorator (callsite-specific reason; depends on Task 16's `update_parked_request` SET being live) |
| `test_delegate_start_integration.py:564` | F16.2 start E2E | `test_e2e_command_approval_produces_escalation` | Remove decorator (uses constant) |
| `test_delegate_start_integration.py:628` | Mode A E2E | `test_e2e_unknown_request_kind_interrupts_and_escalates` | Remove decorator (callsite-specific reason) |
| `test_delegate_start_integration.py:681` | F16.2 start E2E | `test_e2e_busy_gate_blocks_when_job_needs_escalation` | Remove decorator (uses constant) |
| `test_delegate_start_integration.py:805` | Mode B E2E | `test_delegate_poll_needs_escalation_returns_projected_request` | Remove decorator (callsite-specific reason; verified no decide call) |
| `test_delegate_start_integration.py:1034` | F16.2 start E2E | `test_start_escalation_uses_pending_escalation_key` | Remove decorator (uses constant; verified no decide call) |

**Bucket A subtotals (originally classified at dispatch time):** 18 via `_TASK_17_DEADLOCK_REASON` constant (8 F16.2 start in `test_delegation_controller.py` + 7 F16.2 decide_rejects_* + 3 F16.2 start E2E in `test_delegate_start_integration.py`) + 6 callsite-specific reason strings (3 Mode A + 2 Mode B + 1 L10 barrier) = **24 total originally-planned removals**. Per L10. **Effective post-L13: 23 removals** — `test_delegation_controller.py:1522` (`test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up`) reclassified to Bucket B per L13; see Post-implementer adjudication record at end of document.

### Bucket B — Task 18 mechanism-bearing (12 decorators retained per L13, reason rewritten; originally 11 at dispatch, +1 reclassified post-feat)

| File:line | Class | Test name | Why Task 18 needed |
|---|---|---|---|
| `test_delegation_controller.py:1522` (reclassified per L13) | F16.2 start (originally) → F16.2 decide-mechanism (effective) | `test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up` | Sabotages 2nd `journal.append_audit_event` call (escalation audit inside `_finalize_turn`); under async model `_finalize_turn` runs on worker thread AFTER `decide()` calls `commit_signal()` to resume — sabotaged failure path is unreachable from `start()` alone. Constant-backed; rename covers it automatically. See L13 + Post-implementer adjudication record. |
| `test_delegation_controller.py:1716` | F16.2 decide | `test_decide_approve_resumes_runtime_and_returns_completed_result` | Asserts worker resumes turn after approve; needs commit_signal to wake registry.wait() |
| `test_delegation_controller.py:1761` | Mode A | `test_decide_approve_can_reescalate_with_new_pending_request` | Re-escalation path requires CAS + commit_signal cycle |
| `test_delegation_controller.py:1814` | F16.2 decide | `test_decide_deny_marks_job_failed_and_closes_runtime` | Worker-resume-on-deny path (post-deny finalization needs Task 18 signal even though legacy local-finalize might mechanically pass) |
| `test_delegation_controller.py:1860` | F16.2 decide | `test_decide_deny_emits_terminal_outcome` | Same — deny terminal-outcome via Task 18 signal mechanism |
| `test_delegation_controller.py:2162` | F16.2 decide | `test_decide_approve_turn_failure_raises_committed_decision_finalization_error` | Asserts CommittedDecisionFinalizationError after approve+resume — needs commit_signal path |
| `test_delegation_controller.py:2406` | Mode A | `test_decide_rejects_stale_request_id_after_reescalation` | First decide must commit_signal to enable re-escalation, then second decide rejects stale; both phases need Task 18 |
| `test_delegation_controller.py:2464` | F16.2 decide | `test_decide_approve_post_turn_journal_failure_raises_committed_decision_finalization_error` | Same as :2162 — post-resume failure path |
| `test_delegation_controller.py:2516` | F16.2 decide | `test_decide_deny_post_commit_failure_raises_committed_decision_finalization_error` | Post-Task-18-commit failure path (mechanism explicitly Task 18) |
| `test_delegate_start_integration.py:869` | F16.2 decide E2E | `test_delegate_decide_approve_end_to_end_through_mcp_dispatch` | E2E approve flow requires worker resume |
| `test_delegate_start_integration.py:946` | F16.2 decide E2E | `test_delegate_decide_deny_end_to_end_through_mcp_dispatch` | E2E deny flow — same audit-discipline framing as `:1814/:1860` |
| `test_delegate_start_integration.py:1077` | Mode A E2E | `test_decide_reescalation_uses_pending_escalation_key` | E2E re-escalation requires Task 18 signal cycle |

**Bucket B subtotal (post-feat per L13):** 12 decorators retained = 11 originally-classified Bucket B + 1 reclassified from Bucket A (`test_delegation_controller.py:1522` `test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up`). The constant rename `_TASK_17_DEADLOCK_REASON` → `_TASK_18_DECIDE_SIGNAL_REASON` per L6 covers the 8 originally-constant-backed Bucket B decorators PLUS the 1 reclassified test (which was also constant-backed) = 9 covered automatically by the rename. The remaining 3 callsite-specific Mode A Bucket B decorators (`test_delegation_controller.py:1761`, `:2406`; `test_delegate_start_integration.py:1077`) carry hand-written reason strings and MUST be EXPLICITLY rewritten to `reason=_TASK_18_DECIDE_SIGNAL_REASON`. Post-state: all 12 reference the new constant.

### Out of Task 17 entirely — F16.1 (Phase H Task 19 owns)

| File:line | Test name | Why Task 19 (NOT Task 17) |
|---|---|---|
| `test_handler_branches_integration.py:161` | `test_happy_path_decide_approve_success` | Asserts finalizer-routed decide-success projection (`_finalize_turn` Captured-Request Terminal Guard) |
| `test_handler_branches_integration.py:179` | `test_timeout_cancel_dispatch_succeeded_for_file_change` | Asserts finalizer-routed cancel-success projection |

Decorators citing Phase H Task 19 — leave UNTOUCHED in Task 17.

### New acceptance tests (test_delegate_start_async_integration.py) — 8 written

| Test name | ParkedCaptureResult variant covered | Notes |
|---|---|---|
| `test_start_returns_escalation_on_parked` | 1 (Parked happy path) | Module-local helpers; assert `isinstance(result, DelegationEscalation)` |
| `test_start_returns_plain_job_for_turn_completed_without_capture` | 2 (TurnCompletedWithoutCapture) | Worker completes turn without parking; assert `isinstance(result, DelegationJob)` |
| `test_start_returns_plain_job_for_unknown_kind_parse_failure` | 3 (TurnTerminalWithoutEscalation) | Unknown-kind parse failure path; status="unknown"; does NOT raise |
| `test_start_returns_running_job_on_start_wait_elapsed` | 5 (StartWaitElapsed) | `monkeypatch.setattr` `START_OUTCOME_WAIT_SECONDS = 0.1`; arrange worker to signal after budget elapses; assert status="running" + warning logged |
| `test_start_raises_for_worker_failed_before_capture` | 4 (WorkerFailed default) | Worker raises non-DelegationStartError; assert `pytest.raises(DelegationStartError, match="worker_failed_before_capture")` |
| `test_start_raises_with_reason_preservation_for_unknown_kind_interrupt` | 4 (WorkerFailed reason-preservation) | Worker raises `DelegationStartError(reason="unknown_kind_interrupt_transport_failure")`; assert outer exc.reason == same reason (not collapsed to fallback) |
| `test_start_signals_internal_abort_on_parked_projection_null` | 1 (Parked, null projection) | Force `_project_pending_escalation` to return `None`; assert `signal_internal_abort` called + `DelegationStartError(reason="parked_projection_invariant_violation")` raised |
| `test_start_signals_internal_abort_on_parked_projection_raise` | 1 (Parked, projection raises) | Force `_project_pending_escalation` to raise `UnknownKindInEscalationProjection`; same assertion shape as above |

**Acceptance tests subtotal:** 8 new tests, all use module-local helpers (W4), all pass at Task 17 feat commit (W5 verification protocol).

## Out of scope (with plan/spec citations)

| Item | Lands at | Authority citation |
|------|----------|-------------------|
| `decide()` reservation/commit_signal rewrite | Phase G Task 18 | `phase-g-public-api.md:290-536` |
| `_execute_live_turn` callsite at `:2484` (decide-resume) | Phase G Task 18 | `phase-g-public-api.md:290+` |
| `_finalize_turn` Captured-Request Terminal Guard | Phase H Task 19 | `phase-h-finalizer-consumers-contracts.md:11+` |
| `poll()` `UnknownKindInEscalationProjection` catch + `signal_internal_abort` | Phase H Task 20 | `phase-h-finalizer-consumers-contracts.md:330+` |
| `discard()` admits canceled jobs | Phase H Task 21 | `phase-h-finalizer-consumers-contracts.md` (Task 21 body) |
| `contracts.md` updates | Phase H Task 22 | `phase-h-finalizer-consumers-contracts.md` (Task 22 body) |
| F16.1 finalizer-routed integration tests (`:161`, `:179`) | Phase H Task 19 | Per user constraint + spec §1790+ |
| `runtime.py:270` Pyright fix (TurnStatus literal narrowing) | Separate carry-forward (e.g., RT.1 — proposed) | Pre-existing per Task 16 G34 |
| `_TASK_18_DECIDE_SIGNAL_REASON` constant removal + **12 decorator removals** (post-L13: 9 G17.1 + 3 Mode A defer; originally 11 at dispatch-time framing) | Phase G Task 18 | When Task 18 lands `reserve()` + `commit_signal()` |

## Acceptance criteria

### Code (mandatory)

- [ ] `start()` rewritten at `delegation_controller.py:386` per L2 (replace synchronous `_execute_live_turn(...)` at `:737`)
- [ ] `_dispatch_parked_capture_outcome(*, outcome, job_id, collaboration_id) -> DelegationJob | DelegationEscalation` helper added, exhaustive 5-variant `match` per L4
- [ ] `case _: assert_never(outcome)` final arm (W11)
- [ ] `START_OUTCOME_WAIT_SECONDS: float = 30` module constant near `:107` (L3)
- [ ] 6 new imports from `.resolution_registry` extending the existing line at `:102`: `Parked, ParkedCaptureResult, StartWaitElapsed, TurnCompletedWithoutCapture, TurnTerminalWithoutEscalation, WorkerFailed` (L5)
- [ ] `from .worker_runner import spawn_worker` import added (L5)
- [ ] `from typing import assert_never` added if not yet present (L5)
- [ ] No re-import of `cast`, `EscalatableRequestKind`, `ResolutionRegistry`, `DecisionResolution`, `InternalAbort` (W6)
- [ ] No edits to `decide()` body (W1), `_finalize_turn` body (W2), the 6 sentinel raise sites (W3), `_execute_live_turn` callsite at `:2484` (W1), `runtime.py` (W10), or the `_DelegationEscalation` construction site at `:2240` (W13)
- [ ] **W3 invariant:** `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `6`
- [ ] L7 reason-preservation: `WorkerFailed` arm preserves `DelegationStartError.reason` from worker
- [ ] L8 invariant-violation signal-then-raise: both projection-null and projection-raise sub-cases call `signal_internal_abort` BEFORE raising

### Tests (mandatory)

- [ ] New file `packages/plugins/codex-collaboration/tests/test_delegate_start_async_integration.py` with 8 acceptance tests per the per-test triage table
- [ ] No `pass`-bodied tests committed (W12 — replace plan stubs with real assertions)
- [ ] 23 effective Bucket A decorators removed per L10 (24 originally planned − 1 reclassified per L13)
- [ ] `_TASK_17_DEADLOCK_REASON` renamed to `_TASK_18_DECIDE_SIGNAL_REASON` in BOTH `test_delegation_controller.py:43` and `test_delegate_start_integration.py:31` per L6
- [ ] Constant text rewritten per L6 (cite Task 18's `reserve()` + `commit_signal()` mechanism + the audit-discipline framing)
- [ ] 12 Bucket B decorators retained per L13 (11 originally + 1 reclassified), all using the new constant name
- [ ] Test-body assertion shapes updated per L12 for tests originally written under the synchronous model (per spec §Capture-ready handshake at `design.md:785-797`)
- [ ] F16.1 decorators at `test_handler_branches_integration.py:161, 179` UNTOUCHED (W8)
- [ ] **Suite expectation (post-L13):** 968 → 968 + 8 (new) + 23 (unskipped) = 999 passing; 14 skipped (12 Bucket B citing Task 18 + 2 F16.1 citing Task 19); 0 failed. (Pre-L13 target was 1000 passing / 13 skipped.)
- [ ] **W5 hang verification:** full suite completes in normal wall-clock time (~30-40s); `pytest` exit code 0; no SIGTERM/timeout messages; order-independence smoke (the two-ordering invocations from W5) yields identical pass/skip counts and exit code 0 in both directions
- [ ] Lint: `uv run --package codex-collaboration ruff check packages/plugins/codex-collaboration/server/ packages/plugins/codex-collaboration/tests/` — no new findings relative to `f3cfa61a` baseline
- [ ] Pyright: no new diagnostics on touched files (pre-existing `runtime.py:270` noted but not acted on per W10)

### Closeout-docs (mandatory)

- [ ] `carry-forward.md` F16.2 split (covers ONLY the original 26-test F16.2 surface — NOT the full 35-test Task-17-cited dispatch surface): **17 F16.2 Bucket A items closed by Task 17** (10 start-flow + 7 decide-rejects, after L13 reclassified `:1522` to Bucket B); **9 F16.2 Bucket B items moved to a new `G17.1`** (Phase G Task 18 unblock surface) entry with the 9-test list (8 originally classified + 1 reclassified per L13) + revised mechanism citation. The remaining cross-cutting items in the 35-test surface — 6 Bucket A items (3 Mode A + 2 Mode B + 1 L10) and 3 Bucket B items (3 Mode A defer) — are tracked under their own carry-forward rows (Mode A/B partial-closure annotation + L10 closeout narrative), NOT under F16.2 / G17.1
- [ ] `carry-forward.md` Mode A/B from Task 14 closeout: partial closure annotation. **Mode A** (6 total): 3 close in Bucket A (`test_delegation_controller.py:1377`, `:1436`; `test_delegate_start_integration.py:628`); 3 defer to Task 18 (`test_delegation_controller.py:1761`, `:2406`; `test_delegate_start_integration.py:1077`). **Mode B** (2 total): both close in Bucket A (`test_delegation_controller.py:2626`; `test_delegate_start_integration.py:805`).
- [ ] `carry-forward.md` L10 barrier from Task 16 closeout: closed
- [ ] L9 stop-rule from Task 16 carry-forward: F16.1 unchanged (Task 19 still owner)
- [ ] New carry-forward item proposal: `RT.1` for `runtime.py:270` Pyright pre-existing error (per Open Question from prior session)
- [ ] Closeout-docs entry per Phase E/F precedent: landed-code summary, Bucket A closures (23 = 17 F16.2 + 3 Mode A + 2 Mode B + 1 L10, post-L13), Bucket B carry-forward (9 F16.2 → G17.1; 3 Mode A → Mode A row defer), full L1-L13 + W1-W13 lock conformance, branch-matrix-with-test-coverage note, hang-verification result, L12 + L13 adjudication record references

## Pre-dispatch checklist

- [ ] Convergence map (this file) shared with implementer in dispatch packet
- [ ] Spec §Capture-ready handshake (`design.md:659-910`) inline
- [ ] Spec §DelegationStartError reasons (`design.md:622-657`) inline
- [ ] Plan Step 17.1-17.5 inline (or full reproduction with the L4 helper signature + 5-variant match exemplar)
- [ ] Live anchors table inline
- [ ] Per-test triage table inline (originally 24 Bucket A + 11 Bucket B; post-L13 effective: 23 Bucket A + 12 Bucket B + 8 new + 2 F16.1 untouched)
- [ ] L4 prominent in dispatch packet: `_dispatch_parked_capture_outcome` exhaustive `match` + `assert_never` requirement
- [ ] L8 prominent: invariant-violation MUST signal_internal_abort BEFORE raising on main thread
- [ ] L6 prominent: constant rename `_TASK_17_DEADLOCK_REASON` → `_TASK_18_DECIDE_SIGNAL_REASON` + reason text rewrite
- [ ] W4 prominent: NO fictional fixtures (per plan Step 17.1 stubs); use module-local `_build_controller`
- [ ] W5 prominent: hang-verification protocol for newly-unskipped 23 tests post-L13 (original dispatch framing was 24) — full suite + two-ordering / order-independence smoke per W5 — explicit invocation pair from repo root, NOT a `pytest-randomly` shuffle
- [ ] Acceptance criteria inline
- [ ] Reporting contract: implementer reports `DONE` with commit SHA + suite output line + W3 grep result + Bucket-A-removal count audit + Bucket-B-retention count audit + per-lock conformance summary; flags `BLOCKED` with question if any lock turns out unreachable (NOT `DONE_WITH_CONCERNS`)
- [ ] Workflow: `superpowers:subagent-driven-development`, **fresh implementer + spec reviewer + code-quality reviewer** (sequential, not parallel) — sonnet model
- [ ] Implementer agent named explicitly via `Agent({name: "task-17-implementer", ...})` (per Task 16 D5 / R3 — names over UUIDs for SendMessage; fresh-spawn-with-inherited-context the default per Task 16 L1 / G32)

## Commit shape

| Step | Type | Subject |
|------|------|---------|
| 1 | feat | `feat(delegate): rewrite start() with capture-ready handshake (T-20260423-02 Task 17)` |
| 2 (anticipated) | fix | `fix(delegate): address Task 17 closeout review (T-20260423-02 Task 17 closeout)` |
| 3 (mandatory) | docs | `docs(delegate): record Phase G Task 17 closeout (T-20260423-02)` — Bucket A closures + Bucket B carry-forward to G17.1 + L10 barrier closure + RT.1 add |

**Anticipated 1+1+1.** Task 17 production scope is smaller than Task 16 (~80 lines start() rewrite + ~70 lines `_dispatch_parked_capture_outcome` helper + ~5 lines imports/constants vs Task 16's ~420 lines), but test-side surgery is heavier (23 effective decorator removals post-L13 across 3 test files; originally 24 planned at dispatch + constant rename + 12 retained reason rewrites post-L13; originally 11). Code-quality review surfacing 2-4 cleanups is plausible (e.g., `match` exhaustiveness style nits, log-message wording, reason-preservation isinstance-vs-type check). Closeout-docs is mandatory (multiple carry-forward state moves: F16.2 split, Mode A/B partial closure, L10 closure, G17.1 add, RT.1 add).

## Carry-forward expectations

| Item | Pre-Task-17 | Post-Task-17 | Closed-by |
|------|-------------|--------------|-----------|
| F16.2 (Phase G Task 17 unblock surface — original 26-test wording) | Open (1 entry, 26 tests) | **Split (post-L13): Bucket A (17 = 10 start + 7 decide-rejects) closed; Bucket B (9 F16.2 decide-mechanism tests = 8 originally + 1 reclassified per L13) moved to G17.1** | Task 17 (F16.2 Bucket A); Task 18 (F16.2 Bucket B via G17.1) |
| Mode A (6 tests, Phase E Task 14 closeout) | Open | **Partial closure (3 of 6 closed via Bucket A; 3 of 6 deferred to Task 18)** | Task 17 (3 in Bucket A); Task 18 (`test_delegation_controller.py:1761`, `:2406`; `test_delegate_start_integration.py:1077`) |
| Mode B (2 tests, Phase E Task 14 closeout) | Open | **Closed (both items in Bucket A)** | Task 17 |
| F16.1 (Phase F Task 16 closeout — Phase H Task 19 unblock) | Open | Open (untouched per W8) | Phase H Task 19 |
| **NEW G17.1** (Phase G Task 18 unblock surface — **9 F16.2 Bucket B tests** post-L13 = 8 originally classified + 1 reclassified; the other 3 Bucket B tests are tracked under Mode A defer above, not here) | n/a | **NEW Open** | Phase G Task 18 — same-commit un-skip with `reserve()` + `commit_signal()` rewrite (Task 18 dispatch closes all 12 Bucket B = 9 G17.1 + 3 Mode A defer) |
| **NEW RT.1** (`runtime.py:270` Pyright TurnStatus literal narrowing) | n/a (Open Question) | **NEW Open** | End-of-Phase-G or end-of-Packet-1 typing polish |
| A4, A5, B6.1, B6.2, B7.1, B7.2, B8.1, B8.2 | Open | Open | End-of-phase polish |
| C10.2, C10.3 | Open | Open | End-of-phase test parity polish |
| E13.2, E13.3 | Open | Open | Phase H Task 22 contracts.md |
| E14.1 | Open | Open | End-of-Packet-1 polish |

**L10 barrier (Phase F Task 16 closeout) — recorded under closeout narrative, not as a row above.** The single decorator at `test_handler_branches_integration.py:539` is removed in Bucket A and closes here. Following Task 16's bookkeeping convention (where L10 lived inside the Task 16 closeout section, not as a top-level Open carry-forward row), L10 is documented in the Task 17 closeout-docs deliverable narrative and not promoted to a standalone row in this expectations table.

**Net change (qualitative, post-L13):** F16.2 splits — its 17-test Bucket A subset closes (originally 18, less the 1 reclassified per L13); its 9-test Bucket B subset is re-attributed and moves to G17.1 (8 F16.2 decide-mechanism tests originally classified + 1 reclassified post-feat per L13, with sharper Task-18 mechanism citation). Mode A partially closes (3 of 6 close in Bucket A; 3 of 6 defer to Task 18 — those 3 stay under the Mode A row, NOT under G17.1). Mode B fully closes. L10 closes (per closeout narrative above). Two new Open items are added: G17.1 (mechanism-bearing F16.2 carry-over — Task 18 will close) and RT.1 (typing-polish). The active Open-item count therefore stays approximately stable across the Task 17 boundary, with the substantive change being a transfer of F16.2's 9 mechanism-bearing tests into G17.1. End-of-Phase-G outlook: when Task 18 lands, it closes G17.1 (9 tests) and the 3 Mode A defer items together (12 Bucket B total post-L13); F16.2 retires entirely.

---

**Status:** Ready for dispatch. Workflow: `superpowers:subagent-driven-development` with sonnet implementer + spec reviewer + code-quality reviewer (sequential). Anticipated 3-commit chain (feat + fix + docs).

**Pre-dispatch warning (historical, original counts):** Task 17 is smaller than Task 16 in production code but heavier in test-side surgery (24 decorator removals + 1 shared-constant rename per file × 2 files covering 8 Bucket B decorators + 3 callsite-specific reason rewrites for Mode A Bucket B + 8 new tests). Implementer must NOT confuse Bucket A removals with Bucket B retentions, and must NOT assume the constant rename alone updates all 11 Bucket B decorators (it covers only 8). Per-test bucketing in the triage table is binding. The W5 hang-verification protocol is mandatory — newly-unskipped tests intentionally leave parked daemon workers behind, and bucket misclassification is the most likely failure mode.

**Post-feat amendment (2026-04-26 — see Post-implementer adjudication record below):** effective post-L13 counts are 23 Bucket A (1 reclassified) + 12 Bucket B (1 added by reclassification). Suite expectation: 999 passing / 14 skipped. G17.1 owns 9 F16.2 tests (not 8). L12 records the assertion-update obligation; L13 records the reclassification adjudication.

## Post-implementer adjudication record

**2026-04-26 — Task 17 feat commit `8dd15971` adjudication.**

The implementer reported DONE for the feat commit with three substantive scope decisions made unilaterally rather than via the dispatch contract's preferred BLOCKED + question pattern. Controller adjudication outcomes:

| Decision | Implementer Note | Adjudication | Authority | Encoded as |
|---|---|---|---|---|
| Reclassify `test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up` (`test_delegation_controller.py:1522`) from Bucket A to Bucket B | Note 4 | **Accepted retroactively.** Substantively correct: the test sabotages the SECOND `journal.append_audit_event` call (escalation audit inside `_finalize_turn`), which under the async model only runs after `decide()` calls `commit_signal()` to resume the worker. The failure path is unreachable from `start()` alone. SHOULD have been BLOCKED + asked rather than executed unilaterally. | Spec §`reserve()` + `commit_signal()` protocol; test docstring at `:1531-1538` | L13 (binding); also reflected in updated F16.2 split, G17.1 count, and Bucket B subtotal |
| Update Bucket A test assertion shapes for deferred-escalation semantics (`agent_context=None`, request status `"pending"`, escalation audits deferred) | Note 5 | **Accepted retroactively.** Substantively forced: removing the skip decorators meant the tests would fail under the new async model unless their assertions were updated to match. L10 was incomplete in not anticipating this. Spec evidence is decisive at `design.md:785-797`. Treat as a convergence-map gap, not an implementer process violation. | Spec §Capture-ready handshake at `design.md:785-797` (deferred-escalation contract) | L12 (binding); table of new assertion shapes inline |
| Update Mode A test assertion (`test_start_with_request_user_input_completed_returns_delegation_job` now asserts `DelegationEscalation` instead of `DelegationJob(status="completed")`) | Note 6 | **Accepted retroactively.** Same category as Note 5: under the async model, `request_user_input` parks like other parkable kinds, so the synchronous-completion assertion was wrong. Spec evidence: §Capture-ready handshake. | Spec §Capture-ready handshake at `design.md:659-910` | Subsumed under L12 |

**Process precedent for future tasks:** Bucket reclassifications are scope decisions and MUST be reported as BLOCKED + question. Test-body assertion updates that mirror a single explicit spec section are implementer-discretion within the dispatch contract; assertion updates that ADD new behavior or test new spec sections REQUIRE BLOCKED + adjudication. Future dispatch packets should pre-spell-out the assertion-update obligation per L12.

**Diagnostics adjudicated:**
- `delegation_controller.py:892` "Type analysis indicates code is unreachable" — this is the `case _: assert_never(outcome)` arm; Pyright correctly identifies it as unreachable BECAUSE of the exhaustive match. The diagnostic IS the exhaustiveness proof per W11. No fix needed; expected idiom.
- `test_delegation_controller.py:257, :2547, :2621, :2686, :2867, :2888, :3064, :3194, :3418` Pyright errors — pre-existing per `_FakeControlPlane` / `_snapshots` / `inspection` protocol mismatches; unrelated to Task 17 surface. Carry-forward to a future typing-polish task (parallel to RT.1).
- `test_delegate_start_async_integration.py` and `test_delegate_start_integration.py` "_pytest could not be resolved" — local venv-related; not blocking.
- "_journal not accessed" / "_cp not accessed" warnings — informational, tuple-unpacking artifacts from `_build_controller`'s 8-tuple return. Cosmetic.

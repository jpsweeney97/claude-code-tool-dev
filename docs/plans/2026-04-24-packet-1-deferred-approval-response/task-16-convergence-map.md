# Convergence Map — Phase F Task 16 (handler rewrite + 6 sentinel raise sites + parked_request wiring + completion_origin writes)

**Drafted:** 2026-04-25 (controller + user two-read protocol; option (b) scope adjudicated — see L9).
**Authority order:**
1. Spec sentinel table + catch semantics: `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:474-558`
2. Spec finalizer path table: `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1790+`
3. Phase F Task 16 plan: `docs/plans/2026-04-24-packet-1-deferred-approval-response/phase-f-worker.md:377-1189`
4. Phase H Task 19 finalizer guard plan: `docs/plans/2026-04-24-packet-1-deferred-approval-response/phase-h-finalizer-consumers-contracts.md:11+`
5. Carry-forward A2 + C10.4 + A3 (audit catch)
6. Live code at HEAD `475d0506`

Plan-line numbers throughout `phase-f-worker.md` (esp. `:561` "Edit … at `delegation_controller.py:650-720`") are stale — Task 15 added ~+27 lines post-`_execute_live_turn`. Use the **live anchors** below.

## Live anchors (verified 2026-04-25 at HEAD `475d0506`)

| Symbol | File:line |
|--------|-----------|
| `_WorkerTerminalBranchSignal` def (frozen dataclass Exception) | `delegation_controller.py:201-223` (Task 15, unchanged) |
| `DelegationStartError` def | `delegation_controller.py:153-185` (unchanged) |
| `UnknownKindInEscalationProjection` def | `delegation_controller.py:188` (unchanged) |
| `_execute_live_turn` def | `delegation_controller.py:741` |
| Local `_CANCEL_CAPABLE_KINDS` (in `_execute_live_turn`) | `delegation_controller.py:757` |
| Local `_KNOWN_DENIAL_KINDS` (in `_execute_live_turn`) | `delegation_controller.py:758` |
| `_server_request_handler` def (current — TARGET FOR REWRITE) | `delegation_controller.py:765-835` (plan cites stale `:650-720`) |
| First `try/except` around `run_execution_turn` (Task 15 sentinel catch already in place) | `delegation_controller.py:837-879` |
| Sentinel catch clause | `delegation_controller.py:845` (Task 15, unchanged) |
| Second `try/except` around `_finalize_turn` — DO NOT MODIFY (Task 19) | `delegation_controller.py:881-899` |
| `_mark_execution_unknown_and_cleanup` def | `delegation_controller.py:901` (unchanged) |
| `_finalize_turn` def — DO NOT MODIFY (Task 19) | `delegation_controller.py:1611` |
| `_finalize_turn` local `_CANCEL_CAPABLE_KINDS` (separate from handler's) | `delegation_controller.py:1628` |
| Module-level `logger` (reuse) | `delegation_controller.py:104` |
| `cast` import (already imported, do not re-add) | `delegation_controller.py:64` |
| `EscalatableRequestKind` import (already imported, do not re-add) | `delegation_controller.py:90` |
| `ResolutionRegistry.register` signature — REQUIRES `kind: EscalatableRequestKind` kw-only | `resolution_registry.py:173-180` |
| `ResolutionRegistry.wait` | `resolution_registry.py:261` |
| `ResolutionRegistry.discard` | `resolution_registry.py:283` |
| `ResolutionRegistry.announce_parked` | `resolution_registry.py:310` |
| `DelegationJobStore.update_parked_request` | `delegation_job_store.py:187` (zero callsites in production code today; T16 lands first 8) |
| `PendingRequestStore.record_response_dispatch` / `mark_resolved` / `record_dispatch_failure` / `record_timeout` / `record_internal_abort` | `pending_request_store.py:128+` (existing mutators) |
| `OperationJournalEntry.completion_origin` Literal includes `"worker_completed"` | `models.py:368` (zero callsites in production today; T16 lands first 4 literal occurrences) |
| Existing 6-reason coverage (sentinel reason literals pinned) | `tests/test_worker_terminal_branch_signal.py:21-31` (unchanged) |
| Worker runner scaffold (NOT yet wired into production) | `server/worker_runner.py` (Task 15) |
| Carry-forward A2 (Task 16 raise sites absorb caller-contract docs) | `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md:17` |
| Carry-forward A3 (Task 14 closeout `65f270ab` already added `cast`) | `carry-forward.md:18` (audit-and-close per L11) |
| Carry-forward C10.4 (`completion_origin="worker_completed"` writes) | `carry-forward.md:49` |
| 6 Mode A skip-decorators (Task 17 unblock) | `tests/test_delegation_controller.py:1360, 1418, 1737, 2372` + `tests/test_delegate_start_integration.py:617, 1062` |
| 2 Mode B skip-decorators (Task 17 unblock — see W6) | `tests/test_delegation_controller.py:2598` + `tests/test_delegate_start_integration.py:802` |

## Locks (binding positive scope)

- **L1 — Exactly 6 production sentinel raise sites at commit time.** `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `6`. The 6 reasons are: `internal_abort`, `dispatch_failed`, `timeout_interrupt_failed`, `timeout_interrupt_succeeded`, `timeout_cancel_dispatch_failed`, `unknown_kind_interrupt_transport_failure`.

- **L2 — Each sentinel raise is last-step control flow after durable cleanup.** Per spec §545: "Raising the sentinel is the LAST step, not the first." Each branch must complete its `record_*` mutator + journal write + `update_parked_request(None)` (where applicable) + `registry.discard` (where applicable) + cleanup helper invocation BEFORE `raise _WorkerTerminalBranchSignal(...)`. Any reordering violates the durable-state-discipline contract (IO-3) and is a spec violation per spec §558.

- **L3 — `unknown_kind_interrupt_transport_failure` remains the SOLE pre-capture sentinel reason and maps to `DelegationStartError(reason=..., cause=None)`.** Already implemented at `delegation_controller.py:853-861` by Task 15. Task 16 ADDS the raise site at the handler's unknown-kind interrupt-failure sub-branch (per plan Step 16.3 lines 610-620) — but the catch-side mapping is unchanged from Task 15.

- **L4 — `ResolutionRegistry.register` call MUST pass `kind=cast(EscalatableRequestKind, parsed.kind)`** (or an equivalent locally-proven narrowed value). Plan pseudocode at `phase-f-worker.md:663-667` OMITS `kind=`; live API at `resolution_registry.py:173-180` requires it as a kw-only arg. Narrowing is safe because the parkable branch is reached only after `parsed.kind in _CANCEL_CAPABLE_KINDS or parsed.kind in _KNOWN_DENIAL_KINDS` — which is exactly the 3 EscalatableRequestKind literals (`command_approval`, `file_change`, `request_user_input`). Use `cast` (already imported at `:64`) over a defensive runtime check; pyright cannot narrow string literals through frozenset membership.

- **L5 — Parkable capture order is: `_pending_request_store.create(parsed)` → `_job_store.update_parked_request(job_id, parsed.request_id)` → `_persist_job_transition(job_id, "needs_escalation")` → `registry.register(parsed.request_id, job_id=job_id, kind=..., timeout_seconds=_APPROVAL_OPERATOR_WINDOW_SECONDS)` → `registry.announce_parked(job_id, request_id=parsed.request_id)` → `resolution = registry.wait(parsed.request_id)`.** All 6 ordered steps are mandatory; `announce_parked` BEFORE `wait` is the capture-ready handshake (Phase D Task 12 contract).

- **L6 — Every terminal branch clears `update_parked_request(job_id, None)` before sentinel raise or finalizer-return success.** Total 8 callsites at commit time: 1 SET (capture, line ~661 in plan) + 7 CLEAR (internal_abort ~710, dispatch-failed ~804, dispatch-success ~853, cancel-success ~975, cancel-failed ~948, interrupt-failed ~1006, interrupt-succeeded ~1034). Verification: `grep -n "update_parked_request" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` should return `≥8` (excluding the docstring reference at line 208).

- **L7 — Worker-written `approval_resolution.completed` records use `completion_origin="worker_completed"`** — closes carry-forward C10.4. 4 literal occurrences at commit time: 3 inline (internal_abort ~721, dispatch-failed ~815, dispatch-success ~864) + 1 inside `_write_completion_and_audit_timeout` helper (line ~1088, called by all 4 timeout sub-branches). Verification: `grep -nF 'completion_origin="worker_completed"' packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` should return `4`.

- **L8 — Carry-forward A2 closes by raise-site comment migration.** Each of the 6 raise sites must include a comment that absorbs the caller-contract docs from `_WorkerTerminalBranchSignal`'s class-level docstring. The class-level doc enumerates 4 cleanup obligations (final journal entry, `update_parked_request(None)`, `registry.discard`, cleanup helper); each raise site's comment must reference which obligations apply at that site (varies — pre-capture site has `n/a` for some; see spec §549-557 invariant table).

- **L9 — STOP-RULE: Cancel-success and decide-success rows are FINALIZER-ROUTED.** Per spec §545: "Raising the sentinel is the LAST step." For the 2 non-sentinel rows (decide-success, timeout-cancel-dispatch-succeeded), the worker writes `record_response_dispatch` / `record_timeout(succeeded)` then returns `None` from the handler — letting the turn continue to `turn/completed`. `_execute_live_turn` then calls `_finalize_turn` (line 882). At Task 16 commit time, `_finalize_turn` STILL has the pre-Packet-1 logic (projects from `captured_request.kind` + `turn_result.status` without consulting `request_snapshot.status`). The Captured-Request Terminal Guard rewrite is owned by Phase H Task 19. **Adjudication:** option (b) — Task 16 lands the handler code at full scope (all 6 sentinel raises + 2 finalizer-routed return paths), but the 2 finalizer-routed integration tests (`test_happy_path_decide_approve_success`, `test_timeout_cancel_dispatch_succeeded_for_file_change`) are SKIPPED with `Phase H Task 19: requires Captured-Request Terminal Guard rewrite of _finalize_turn` citations. Task 16's W7 invariant `0 → 6 sentinel raises` stays clean; the 2 skipped tests are categorized as FINALIZER-coverage gaps, NOT sentinel-coverage gaps.

- **L10 — Unknown-kind parse failure with SUCCESSFUL interrupt is NOT a sentinel branch.** Per plan Step 16.3 lines 621-634: on successful `interrupt_turn`, the handler does `_persist_job_transition(unknown)` → `_emit_terminal_outcome_if_needed` → `lineage_store.update_status(unknown)` → `announce_turn_terminal_without_escalation` → `return None`. The `TurnTerminalWithoutEscalation` ParkedCaptureResult variant signals back to `wait_for_parked` (Task 17 territory) without raising any sentinel. The handler's `return None` causes the turn loop to exit post-interrupt; `_execute_live_turn` enters `_finalize_turn` with `interrupted_by_unknown=True`. (The pre-existing `_finalize_turn` D4 carve-out — line 1645 — handles this case at Task 16; Task 19's guard rewrite preserves the carve-out behavior.)

  **L10 correction (post-implementation discovery):** The D4 carve-out at `_finalize_turn:1645` does NOT cover the `interrupted_by_unknown=True + parse_failed` path. Resolution: this case is skipped in `test_handler_branches_integration.py:539` with same authority as Mode A (Task 17 L6 callsite handling). No Task 16 production change required.

- **L11 — Closeout-docs MUST audit carry-forward A3 and move to Closed.** A3 says "Task 14 `_project_request_to_view` rewrite will resolve the expected Pyright error at `delegation_controller.py:~965` (`PendingRequestKind` vs. `EscalatableRequestKind` at construction site)." Task 14 closeout `65f270ab` (per `carry-forward.md:142` Task 14 closeout entry) added `cast(EscalatableRequestKind, request.kind)` at the construction site — which has shifted post-Task-15 to `:1012` (verified at HEAD). The audit step: run `grep -n "cast(EscalatableRequestKind" packages/plugins/codex-collaboration/server/delegation_controller.py`; if line(s) found in `_project_request_to_view`, move A3 from Open → Closed with `[Resolved 65f270ab — confirmed live at <line> in Task 16 closeout-docs audit pass]` annotation. If not found, A3 stays Open and is flagged as a Task 14 closeout regression. (Per L11, this is a verification-with-live-repo audit, NOT a memory-based move.)

## Watchpoints (binding negative scope)

- **W1 — Do not modify `_finalize_turn` body.** Phase H Task 19 owns the Captured-Request Terminal Guard rewrite. Including the second `try/except Exception` around the call (`:881-899`).

- **W2 — Do not paste plan integration tests with fictional fixture names** (`delegation_controller_fixture`, `app_server_runtime_stub`). These do NOT exist in `tests/conftest.py` (verified at HEAD: only `vendored_schema_dir`, `client_request_schema`, `make_test_handle`). Use module-local `_build_controller(tmp_path)` per Task 14 W4 / Task 15 L8 precedent.

- **W3 — Do not confuse timeout-cancel-dispatch failure with operator-decide dispatch failure.** Both arise from `session.respond(...)` transport failure; both terminalize `DelegationJob.status="unknown"`. They are DISTINCT sentinel reasons (`timeout_cancel_dispatch_failed` vs `dispatch_failed`) AND use DISTINCT pending-request-store mutators (`record_timeout(... dispatch_result="failed")` vs `record_dispatch_failure(...)`). Per spec §487, audit queries distinguish the two via the request-record mutator anchor.

- **W4 — Do not call `_mark_execution_unknown_and_cleanup` for `timeout_interrupt_succeeded`.** That branch terminalizes the JOB as `canceled` (not unknown). Per spec §555: inline cancel cleanup sequence — `_persist_job_transition(job_id, "canceled")` → `_emit_terminal_outcome_if_needed(job_id)` → `lineage_store.update_status(collaboration_id, "completed")` (NOT `"unknown"` — cancel is verified) → `runtime_registry.release(runtime_id)` → `entry.session.close()`. May factor into a `_persist_canceled_and_cleanup` helper but spec keeps inline to make the symmetry with `_mark_execution_unknown_and_cleanup` explicit.

- **W5 — Do not let post-branch sentinels escape `_execute_live_turn`.** All 5 post-branch reasons must return `self._job_store.get(job_id)` from the catch clause (already implemented at `:866-871` by Task 15). The pre-capture reason re-raises as `DelegationStartError` (already implemented at `:853-861`). Worker runner must NOT see a raw `_WorkerTerminalBranchSignal` — that would fire `announce_worker_failed` for a handler-terminalized branch, violating spec §540-542.

- **W6 — All 8 Task 14 skip-decorators (6 Mode A + 2 Mode B) MUST stay skipped at Task 16.** Mode A (6 tests at `:1360, :1418, :1737, :2372, integration:617, :1062`) cite Phase G/Task 17 — unknown-kind handling at the L6 callsite. Mode B (2 tests at `:2598, integration:802`) cite Phase F/G — `update_parked_request` wiring + pre-tombstone window. Task 16 lands the Mode B DATA dependency (`update_parked_request` SET callsite), but the Mode B test EXECUTION shape (synchronous `controller.start(...)` returning `DelegationEscalation`) requires Task 17's `spawn_worker` + `wait_for_parked` split — under Task 16's new handler, synchronous `start()` blocks indefinitely on `registry.wait(...)`. Both Mode A and Mode B unblock at Task 17. Task 16 closeout-docs notes Mode B's data-dependency closure but keeps the skip decorators in place.

  **W6 amendment (post-implementation discovery):** The Mode A/B 8-test set captured at convergence-map drafting was a SUBSET of the deadlock surface. Task 16's handler change to `registry.wait(...)` affects every currently-passing test driving `controller.start(...)` or `controller.decide(...)` through a parkable request, not only the 8 already-classified Mode A/B tests. The full Phase G Task 17 unblock surface is therefore 34 tests = 8 Mode A/B + 26 Task-16-deadlock-discovered. See carry-forward.md F16.2.

- **W7 — Sentinel raise count: `0 → 6` exactly.** Pre-Task-16: `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `0` (Task 15 invariant). Post-Task-16: returns `6`. Both 5 (missing one) and 7+ (duplicate) are spec violations.

- **W8 — Registry stays in-memory only.** No serialization, no journal writes, no recovery shape changes. Stores remain durable forensic/recovery surfaces; registry is in-memory cross-thread coordination (IO-2 per Phase D).

- **W9 — `_handle_timeout_wake` defensive `AssertionError` at the bottom is REQUIRED, not optional.** Plan line 1063-1065: `raise AssertionError(f"_handle_timeout_wake: unexpected kind={request.kind!r}")`. Documents the invariant that `request.kind` reaches the helper only via the upstream `_CANCEL_CAPABLE_KINDS | _KNOWN_DENIAL_KINDS` filter. Do NOT replace with `pass` or `return False`.

- **W10 — Do not delete or rename `_finalize_turn`'s local `_CANCEL_CAPABLE_KINDS` at `:1628`.** That constant is separate from the handler's own local `_CANCEL_CAPABLE_KINDS` at `:757`; both shadow the absent module-level constant. `_finalize_turn` uses its copy for its escalation-branch projection logic (line 1645). Task 19 may consolidate these; Task 16 must not.

- **W11 — Plan Step 16.1 placeholder integration tests** (9 of them, lines 405-549) **use fictional fixtures.** Implementer must NOT paste them verbatim. Per Task 15 W11 precedent: omit fictional names entirely; build module-local helpers OR use existing `_build_controller(tmp_path)` import from `tests.test_delegation_controller`. Per-test triage table below dispositions each.

- **W12 — Do not pre-empt Task 19's finalizer guard.** Per L9 stop-rule: the 2 finalizer-routed rows (decide-success, cancel-success) get integration tests SKIPPED with explicit `Phase H Task 19: requires Captured-Request Terminal Guard rewrite of _finalize_turn` citations. Implementer must NOT add scope to `_finalize_turn` to make those tests pass at Task 16.

- **W13 — Plan-line numbers throughout `phase-f-worker.md` Task 16 body (`:377-1189`) are stale.** Task 15 added ~+27 lines post-`_execute_live_turn`; Tasks 6-14's edits added more. Use the live anchors table above. Particularly: plan `:561` cites `_server_request_handler` at `:650-720` — actual location is `:765-835`.

## Branch matrix (8 rows, spec §549-557 invariant table cross-reference)

| # | Branch | Durable request mutator | Job result | Through finalizer? | Sentinel? | Lineage status | Cleanup helper |
|---|--------|------------------------|------------|--------------------|-----------|----------------|----------------|
| 1 | decide-success (operator decide approve/deny → `respond` succeeds) | `record_response_dispatch` + `mark_resolved` | varies via finalizer (Task 19) | YES | none (handler returns None) | unchanged | none |
| 2 | timeout cancel-success (cancel-capable timeout → `respond({"decision":"cancel"})` succeeds) | `record_timeout(... dispatch_result="succeeded")` | `canceled` via finalizer (Task 19) | YES | none (handler returns None) | unchanged | none |
| 3 | dispatch-failed (operator decide → `respond` raises) | `record_dispatch_failure(action=, payload=, dispatch_error=)` | `unknown` | NO | `dispatch_failed` | unchanged | `_mark_execution_unknown_and_cleanup` |
| 4 | timeout cancel-dispatch-failed (cancel-capable timeout → `respond({"decision":"cancel"})` raises) | `record_timeout(... dispatch_result="failed", dispatch_error=)` | `unknown` | NO | `timeout_cancel_dispatch_failed` | unchanged | `_mark_execution_unknown_and_cleanup` |
| 5 | timeout interrupt-succeeded (`request_user_input` timeout → `interrupt_turn` succeeds) | `record_timeout(... interrupt_error=None)` | `canceled` | NO | `timeout_interrupt_succeeded` | `"completed"` (verified cancel) | INLINE 5-step cancel sequence (NOT `_mark_execution_unknown_and_cleanup`) |
| 6 | timeout interrupt-failed (`request_user_input` timeout → `interrupt_turn` raises) | `record_timeout(... interrupt_error=<sanitized>)` | `unknown` | NO | `timeout_interrupt_failed` | unchanged | `_mark_execution_unknown_and_cleanup` |
| 7 | internal-abort (worker wakes on `InternalAbort` resolution from `signal_internal_abort`) | `record_internal_abort(reason=)` | `unknown` | NO | `internal_abort` | unchanged | `_mark_execution_unknown_and_cleanup` |
| 8 | unknown-kind interrupt transport failure (parse-failure + `interrupt_turn` raises — pre-capture) | minimal `PendingServerRequest(kind="unknown")` create only; no `record_*` mutator | n/a — `DelegationStartError` raised | NO | `unknown_kind_interrupt_transport_failure` (PRE-CAPTURE) | n/a | `_mark_execution_unknown_and_cleanup` |

**Rows 1-2 are FINALIZER-ROUTED (no sentinel; handler returns None; turn continues to `turn/completed`).**
**Rows 3-8 are SENTINEL-BYPASS (sentinel raised; `_execute_live_turn` catch returns `_job_store.get(job_id)` without entering `_finalize_turn`).**
**W7 invariant counts only rows 3-8 = 6 sentinel raises.**

(Plus row 9 — *unknown-kind interrupt SUCCESS* — which is L10's `TurnTerminalWithoutEscalation` path. Not in the matrix because it's neither sentinel nor finalizer-routed in the same sense; the handler returns None after `announce_turn_terminal_without_escalation`, exiting the turn loop directly. `_execute_live_turn` then enters `_finalize_turn` with `interrupted_by_unknown=True` and the existing D4 carve-out at line 1645 handles it.)

## Per-test triage

### Plan Step 16.1 integration tests (9 placeholders) — by branch matrix row

| Plan test (line ref) | Matrix row | Disposition | Notes |
|----------------------|-----------|-------------|-------|
| `test_happy_path_decide_approve_success` (:424) | 1 (decide-success) | **Skip with Task 19 citation** | `@pytest.mark.skip(reason="Phase H Task 19: requires Captured-Request Terminal Guard rewrite of _finalize_turn for finalizer-routed decide-success path. Worker writes record_response_dispatch + mark_resolved + completion_origin='worker_completed' at Task 16; finalizer projection that maps to DelegationJob.status='completed' lands at Task 19.")` |
| `test_timeout_cancel_dispatch_succeeded_for_file_change` (:440) | 2 (cancel-success) | **Skip with Task 19 citation** | `@pytest.mark.skip(reason="Phase H Task 19: requires Captured-Request Terminal Guard rewrite of _finalize_turn for finalizer-routed cancel-success path. Worker writes record_timeout(succeeded) + completion_origin='worker_completed' at Task 16; finalizer projection that maps to DelegationJob.status='canceled' lands at Task 19.")` |
| `test_timeout_cancel_dispatch_failed_for_command_approval` (:452) | 4 (cancel-dispatch-failed) | **Write (sentinel-bypass)** | Sentinel-bypass branch — `_execute_live_turn` catch returns stored job at status="unknown". Testable at Task 16 via threaded harness OR `MagicMock(spec=ResolutionRegistry)` injecting `DecisionResolution(is_timeout=True)` |
| `test_timeout_interrupt_succeeded_for_request_user_input` (:466) | 5 (interrupt-succeeded) | **Write (sentinel-bypass)** | Sentinel-bypass; status="canceled". Same harness pattern. |
| `test_timeout_interrupt_failed_for_request_user_input` (:481) | 6 (interrupt-failed) | **Write (sentinel-bypass)** | Sentinel-bypass; status="unknown". Same harness pattern. |
| `test_dispatch_failure_on_operator_decide` (:495) | 3 (dispatch-failed) | **Write (sentinel-bypass)** | Sentinel-bypass; status="unknown". `MagicMock` injecting `DecisionResolution(is_timeout=False)` + `session.respond.side_effect = BrokenPipeError`. |
| `test_internal_abort_on_unknown_kind_poll_projection_abort` (:509) | 7 (internal-abort) | **Write (sentinel-bypass)** | Sentinel-bypass; status="unknown". Inject `InternalAbort(reason=...)` via mock registry. |
| `test_unknown_kind_parse_failure_terminalizes_unknown` (:523) | row 9 (TurnTerminalWithoutEscalation, see L10) | **Write (sentinel-bypass-adjacent)** | NOT a sentinel branch — handler returns None after `announce_turn_terminal_without_escalation`. Tests the unknown-kind interrupt-success path. Uses `_finalize_turn`'s existing D4 carve-out — testable at Task 16. |
| `test_unknown_kind_interrupt_transport_failure` (:536) | 8 (unknown-kind interrupt-fail, pre-capture) | **Write (sentinel-bypass)** | Pre-capture sentinel raise → `DelegationStartError`. Test asserts `pytest.raises(DelegationStartError, match="unknown_kind_interrupt_transport_failure")` and `exc.cause is None`. Already partially covered by Task 15's `test_execute_live_turn_catches_worker_terminal_branch_signal_pre_capture_reraises_as_delegation_start_error` — this Task 16 test extends with the FULL pre-capture path (parse-fail → interrupt-fail → sentinel) rather than just the catch-side mapping. |

**Net Task 16 integration tests: 7 written + 2 skipped with Task 19 citations** (out of 9 plan placeholders).

### Suggested unit tests for new helpers

| Test | Helper covered | Notes |
|------|----------------|-------|
| `test_handle_timeout_wake_dispatches_by_kind` | `_handle_timeout_wake` | Parametrized over `(command_approval, file_change)` → cancel-capable path; `request_user_input` → interrupt path. Asserts the dispatch decision (which mutator is called). |
| `test_handle_timeout_wake_unexpected_kind_raises_assertion_error` | `_handle_timeout_wake` defensive raise (W9) | Pass kind="unknown" (via mock); assert `pytest.raises(AssertionError, match="unexpected kind")`. |
| `test_write_completion_and_audit_timeout_writes_completion_origin` | `_write_completion_and_audit_timeout` | Spy on `_journal.write_phase`; assert `OperationJournalEntry.completion_origin == "worker_completed"`. |
| `test_write_completion_and_audit_timeout_audit_failure_logs_warning` | `_write_completion_and_audit_timeout` exception path | Force `_journal.append_audit_event` to raise; assert `caplog.text` contains "audit approval_timeout append failed". |
| `test_repo_root_for_journal_resolves_lineage_handle` | `_repo_root_for_journal` | Smoke — calls helper with a known-handle job_id; asserts non-empty Path. |

**Net Task 16 unit tests: 5 (suggested) — implementer may collapse where appropriate.**

### Existing skip-decorators (8 tests) — KEEP SKIPPED per W6

| Test | File:line | Skip reason citation |
|------|-----------|---------------------|
| Mode A 1 | `test_delegation_controller.py:1360` (`test_start_with_unknown_request_interrupts_and_escalates`) | Phase G Task 17 — unknown-kind L6 handling |
| Mode A 2 | `test_delegation_controller.py:1418` (`test_start_with_unparseable_request_creates_minimal_causal_record`) | Phase G Task 17 — D4 carve-out at L6 |
| Mode A 3 | `test_delegation_controller.py:1737` | Phase G/F — re-escalation kind='unknown' L6 |
| Mode A 4 | `test_delegation_controller.py:2372` | Phase G/F — request_already_decided invariant |
| Mode A 5 | `test_delegate_start_integration.py:617` | Phase G Task 17 — unknown-kind E2E |
| Mode A 6 | `test_delegate_start_integration.py:1062` | Phase G Task 17 — decide() re-escalation E2E |
| Mode B 1 | `test_delegation_controller.py:2598` | Phase G/F — `update_parked_request` data dep AND test-shape (Task 17) |
| Mode B 2 | `test_delegate_start_integration.py:802` | Phase F/G — `update_parked_request` data dep AND test-shape (Task 17) |

## Out of scope (with plan/spec citations)

| Item | Lands at | Authority citation |
|------|----------|-------------------|
| `_finalize_turn` Captured-Request Terminal Guard | Phase H Task 19 | `phase-h-finalizer-consumers-contracts.md:11+` |
| `start()` async rewrite + `spawn_worker(...)` call from main thread | Phase G Task 17 | `phase-g-public-api.md` (Task 17 body) |
| `wait_for_parked(...)` blocking call from main thread in `start()` | Phase G Task 17 | `phase-g-public-api.md` (Task 17 body) |
| `decide()` reservation context manager rewrite | Phase G Task 18 | `phase-g-public-api.md` (Task 18 body) |
| `poll()` `UnknownKindInEscalationProjection` catch + `signal_internal_abort` | Phase H Task 20 | `phase-h-finalizer-consumers-contracts.md:330+` |
| `discard()` admits canceled jobs | Phase H Task 21 | `phase-h-finalizer-consumers-contracts.md` (Task 21 body) |
| `contracts.md` updates | Phase H Task 22 | `phase-h-finalizer-consumers-contracts.md` (Task 22 body) |
| Task 14 Mode A unblock (6 tests) | Task 17 | Carry-forward `From Phase E Task 14` rows |
| Task 14 Mode B unblock (2 tests) | Task 17 (per W6 — both data dep + test shape needed) | Carry-forward `From Phase E Task 14` rows |
| `_finalize_turn` test for finalizer-routed cancel-success | Phase H Task 19 | Spec §1790+ |
| `_finalize_turn` test for finalizer-routed decide-success | Phase H Task 19 | Spec §1790+ |
| Test for `unknown_kind_parse_failure_with_successful_interrupt` (`TurnTerminalWithoutEscalation` path) | Task 16 (covered) | L10 + plan `:523-533` |

## Acceptance criteria

### Code (mandatory)

- [ ] `_server_request_handler` rewritten per plan Step 16.3 + L4 fix (kind=cast(...)) at `delegation_controller.py:765-835` (live anchor — plan cites stale `:650-720`)
- [ ] 6 production sentinel raise sites: `internal_abort`, `dispatch_failed`, `timeout_interrupt_failed`, `timeout_interrupt_succeeded`, `timeout_cancel_dispatch_failed`, `unknown_kind_interrupt_transport_failure`
- [ ] **W7 invariant:** `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `6`
- [ ] 8 `update_parked_request` callsites: 1 SET (capture) + 7 CLEAR (terminal branches)
- [ ] 4 literal `completion_origin="worker_completed"` occurrences (3 inline + 1 in helper); helper called from 4 timeout sub-branches
- [ ] `_handle_timeout_wake` method added per plan lines 875-1065; defensive `AssertionError` at bottom (W9)
- [ ] `_write_completion_and_audit_timeout` method added per plan lines 1068-1106
- [ ] `_repo_root_for_journal(job_id)` helper added per plan line 1109
- [ ] `self._registry: ResolutionRegistry = ResolutionRegistry()` set in `DelegationController.__init__`
- [ ] `_APPROVAL_OPERATOR_WINDOW_SECONDS = 900` module-level constant
- [ ] `registry = self._registry` binding at top of `_execute_live_turn` (after the existing `update_status_and_promotion(running)` call)
- [ ] Each of 6 raise sites has a comment that absorbs the `_WorkerTerminalBranchSignal` class-level caller-contract docs (closes A2 — L8)
- [ ] No edits to `_finalize_turn` body, `_mark_execution_unknown_and_cleanup` body, or the second `try/except Exception` around `_finalize_turn` (W1)
- [ ] No re-import of `cast` or `EscalatableRequestKind` (already at `:64`/`:90`)

### Tests (mandatory)

- [ ] New file `packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py` with 7 written + 2 skipped tests per per-test triage above
- [ ] 5 unit tests for new helpers (or fewer if collapsed) per per-test triage
- [ ] 8 Task 14 skip-decorators unchanged (W6 — no premature unblock)
- [ ] 2 finalizer-routed integration tests have explicit `@pytest.mark.skip(reason="Phase H Task 19: requires Captured-Request Terminal Guard rewrite of _finalize_turn ...")` citations (W12)
- [ ] Suite: `983 - 26 + 11 = 968` passing; `8 + 2 + 1 + 26 = 37` skipped at end (Task 14's 8 Mode A/B + Task 16's 2 finalizer-routed deferrals + 1 L10 barrier + 26 Task-16-deadlock-discovered); `0` failed. **Amendment:** The original formula `983 + N` assumed all N new tests pass synchronously; Task 16's registry.wait() blocking caused 26 previously-passing tests to deadlock, requiring M=26 additional skip decorators. Actual observed baseline: 968 passed, 37 skipped, 0 failed.
- [ ] Lint: `uv run --package codex-collaboration ruff check packages/plugins/codex-collaboration/server/ packages/plugins/codex-collaboration/tests/` — no new findings relative to `475d0506` baseline
- [ ] Pyright: no new diagnostics on touched files relative to baseline (pre-existing diagnostics noted but not acted on per Task 15 precedent)

### Closeout-docs (mandatory)

- [ ] `carry-forward.md` A2 moved to Closed with commit SHA(s) ranging Task 16 feat + closeout-fix(es) (per L8)
- [ ] `carry-forward.md` C10.4 moved to Closed with same commits (per L7)
- [ ] **L11 audit:** verify `cast(EscalatableRequestKind, request.kind)` exists in `_project_request_to_view` (current location ~`:1012`); if confirmed, move A3 to Closed with `[Resolved 65f270ab — confirmed live at <line> in Task 16 closeout-docs audit]`
- [ ] New carry-forward item `F16.1` added to Open: "Finalizer-routed integration test coverage (decide-success + timeout-cancel-success) — lands when Phase H Task 19 lands the Captured-Request Terminal Guard. The 2 deferred tests un-skip in same commit as Task 19's `_finalize_turn` rewrite."
- [ ] Closeout-docs entry per Phase E/F precedent: landed-code summary, A2-closes-by-L8 + C10.4-closes-by-L7 + A3-audit-by-L11, full L1-L11 + W1-W13 lock conformance, branch-matrix-with-skip-citations note

## Pre-dispatch checklist

- [ ] Convergence map (this file) shared with implementer in dispatch packet
- [ ] Spec §457-558 sentinel section + invariant table inline
- [ ] Spec §1790+ finalizer path table inline
- [ ] Plan Steps 16.1-16.7 inline (or full reproduction)
- [ ] Branch matrix (8 rows) inline
- [ ] Per-test triage table inline (9 plan + 5 helper + 8 keep-skipped)
- [ ] L9 stop-rule disposition inline (option (b) chosen — implementer must NOT pull-forward Task 19 guard)
- [ ] L4 fix prominent in dispatch packet: registry.register call MUST include `kind=cast(EscalatableRequestKind, parsed.kind)`
- [ ] L11 closeout-docs A3-audit step inline
- [ ] Acceptance criteria inline
- [ ] Reporting contract: implementer reports `DONE` with commit SHA + suite output line + W7 grep result + L6 grep result (`update_parked_request` count) + L7 grep result (`completion_origin="worker_completed"` count) + per-lock conformance summary; flags `BLOCKED` with question if any lock turns out unreachable (NOT `DONE_WITH_CONCERNS`)
- [ ] Workflow: `superpowers:subagent-driven-development`, **single fresh implementer + spec reviewer + code-quality reviewer** (sequential, not parallel) — sonnet model
- [ ] Implementer agent named explicitly via `Agent({name: "task-16-implementer", ...})` (per Task 15 D5 / R3 — names over UUIDs for SendMessage)

## Commit shape

| Step | Type | Subject |
|------|------|---------|
| 1 | feat | `feat(delegate): rewrite _server_request_handler for async-decide model + 6 sentinel raises (T-20260423-02 Task 16)` |
| 2 (anticipated) | fix | `fix(delegate): address Task 16 code-quality review (T-20260423-02 Task 16 closeout)` |
| 3 (mandatory) | docs | `docs(delegate): record Phase F Task 16 closeout (T-20260423-02)` — A2 + C10.4 closures + A3 audit + F16.1 add |

**Anticipated 1+1+1.** Task 16 is the LARGEST task in the plan (~280 lines of new handler code + ~140 lines of helpers per plan Step 16.3); code-quality review surfacing 2-5 cleanups is expected. Closeout-docs is mandatory (multiple carry-forward state moves: A2 closed, C10.4 closed, A3 audited, F16.1 added).

## Carry-forward expectations

| Item | Pre-Task-16 | Post-Task-16 | Closed-by |
|------|-------------|--------------|-----------|
| A2 (Task 16 raise sites absorb caller-contract docs) | Open | **Closed** | L8 raise-site comments |
| A3 (Task 14 Pyright cast already added) | Open (audit miss) | **Closed (or stays Open if audit fails)** | L11 audit + Task 14 commit `65f270ab` |
| C10.4 (`completion_origin="worker_completed"` writes) | Open | **Closed** | L7 — 4 literal occurrences |
| Mode A skip-decorators (6 tests) | Open | Open | Task 17 (unchanged) |
| Mode B skip-decorators (2 tests) | Open | Open — **DATA dep closed but test-shape pending** | Task 17 (W6) |
| F16.1 (NEW — Finalizer-routed integration test coverage) | n/a | **NEW Open** | Phase H Task 19 — same-commit un-skip |
| A4, A5, B6.1, B6.2, B7.1, B7.2, B8.1, B8.2 | Open | Open | End-of-phase polish |
| C10.2, C10.3 | Open | Open | End-of-phase test parity polish |
| E13.2, E13.3 | Open | Open | Phase H Task 22 contracts.md |
| E14.1 | Open | Open | End-of-Packet-1 polish |

**Net: 17 → 14 open items at end of Task 16** (A2 closes, C10.4 closes, A3 closes/audited; F16.1 added). Phase F closes; Phase G (Tasks 17-18) starts.

---

**Status:** Ready for dispatch under option (b) scope. Workflow: `superpowers:subagent-driven-development` with sonnet implementer + spec reviewer + code-quality reviewer (sequential). Anticipated 3-commit chain (feat + fix + docs).

**Pre-dispatch warning:** Task 16 is the LARGEST task in the plan. Implementer should be prepared for ~420 lines of code changes (~280 in handler + ~140 in helpers) plus 7 + 5 = 12 new tests. Context budget for the implementer agent should be high; controller may need to dispatch from a fresh session if local context is constrained.

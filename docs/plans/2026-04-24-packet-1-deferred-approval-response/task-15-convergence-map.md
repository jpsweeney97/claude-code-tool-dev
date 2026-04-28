# Convergence Map — Phase F Task 15 (worker runner scaffold + sentinel catch + canceled-inspection tuple)

**Drafted:** 2026-04-25 (controller session, fresh-session dispatch deferred due to 98% context).
**Authority order:** spec §Worker terminal-branch signaling primitive (`docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:457-567`) > `docs/plans/2026-04-24-packet-1-deferred-approval-response/phase-f-worker.md` Task 15 > carry-forward A1 > current code. Plan-line numbers throughout the plan template are stale — use the **live anchors** below.

## Live anchors (verified 2026-04-25)

| Symbol | File:line |
|--------|-----------|
| `_WorkerTerminalBranchSignal` definition (frozen dataclass Exception) | `packages/plugins/codex-collaboration/server/delegation_controller.py:201-223` |
| `DelegationStartError` definition | `packages/plugins/codex-collaboration/server/delegation_controller.py:153-185` |
| `_execute_live_turn` signature | `packages/plugins/codex-collaboration/server/delegation_controller.py:741` |
| **First `try/except Exception` (around `run_execution_turn`) — sentinel catch goes HERE** | `packages/plugins/codex-collaboration/server/delegation_controller.py:837-852` |
| Second `try/except Exception` (around `_finalize_turn`) — DO NOT MODIFY | `packages/plugins/codex-collaboration/server/delegation_controller.py:854-872` |
| `_mark_execution_unknown_and_cleanup` | `packages/plugins/codex-collaboration/server/delegation_controller.py:874` |
| `_load_or_materialize_inspection` def + terminal-status guard | `packages/plugins/codex-collaboration/server/delegation_controller.py:1012, 1015` |
| `_load_or_materialize_inspection` sole callsite (in `poll`) | `packages/plugins/codex-collaboration/server/delegation_controller.py:1055` |
| `_execute_live_turn` callsites | `:733` (`start`), `:1888` (decide-resume) |
| `cast` already imported | `packages/plugins/codex-collaboration/server/delegation_controller.py:64` |
| `EscalatableRequestKind` already imported | `packages/plugins/codex-collaboration/server/delegation_controller.py:90` |
| Spec sentinel reason table | `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:474-484` |
| Spec sentinel catch site code | `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:489-538` |
| `ResolutionRegistry.register` signature (Task 16 trap, NOT 15) | `packages/plugins/codex-collaboration/server/resolution_registry.py:173-180` |
| `tests/conftest.py` fixtures (only schema + helper fn) | `packages/plugins/codex-collaboration/tests/conftest.py:14-52` |

## Locks (binding positive scope)

- **L1 — Scaffold-only.** No handler-branch rewrite, no sentinel raise sites, no `start()` async rewrite, no `decide()` reservation rewrite, no `poll()` projection catch, no `__init__` registry attribute, no worker spawn from `start()`.
- **L2 — `worker_runner.py` follows the Step 15.3 behavior, with lint-clean adjustments.** Defines `_WorkerRunner` class + `spawn_worker` helper. Adjustments: (a) remove the unused `Callable` import; (b) call `self._controller._execute_live_turn(...)` without assigning to `result` unless the value is actually consumed downstream by `announce_turn_completed_empty` lifecycle logic. Skeleton **does NOT** wire registry-attribute coupling to `DelegationController` (W2). Production `start()` does not call it under Task 15.
- **L3 — `_execute_live_turn` catches `_WorkerTerminalBranchSignal` BEFORE generic `except Exception`.** Insert the new `except _WorkerTerminalBranchSignal as signal:` clause inside the first `run_execution_turn` try block (oriented around `:837-852`), before the existing `except Exception:`. The `_finalize_turn` block at `:854-872` stays untouched.
- **L4 — Catch site logs `signal.reason` (NOT `str(signal)`).** Use `logger.info("worker terminal-branch signal caught. job_id=%r reason=%s", job_id, signal.reason)` placed at the top of the new except clause. Severity: `logger.info` (post-branch sentinel handling is expected control flow; warning/error would be noisy). Honors carry-forward A1.
- **L5 — Pre-capture sentinel reason maps to `DelegationStartError`.** When `signal.reason == "unknown_kind_interrupt_transport_failure"`, raise `DelegationStartError(reason="unknown_kind_interrupt_transport_failure", cause=None)`. Use `cause=None` literal — do NOT chain via `from interrupt_exc` and do NOT pass the underlying exc as cause. Plan + spec agree.
- **L6 — Post-branch sentinels return the stored `DelegationJob` and bypass `_finalize_turn`.** For all 5 non-pre-capture reasons, return `self._job_store.get(job_id)`. The plan's `assert stored is not None, ...` is plan-stricter-than-spec; honor the plan literal.
- **L7 — `_load_or_materialize_inspection` admits `"canceled"` to the terminal tuple AND returns None before materialization.** At `:1015`, expand tuple to `("completed", "failed", "canceled", "unknown")`. Add `if job.status == "canceled": return None` immediately before the `existing = self._artifact_store.load_snapshot(job=job)` line. Both edits are required.
- **L8 — Tests use module-local helpers.** Module-local `_build_controller(tmp_path)` import from `tests.test_delegation_controller` (per Task 14 W4 precedent). NO use of fictional plan fixture names (`delegation_controller`, `simple_job_factory`, `artifact_store_spy`, `worker_runner_fixture`). Acceptable: built-in pytest fixtures (`monkeypatch`, `tmp_path`, `caplog`), `unittest.mock.MagicMock`, the `make_test_handle` helper function from `tests/conftest.py:34`.

## Watchpoints (binding negative scope)

- **W1 — Do not add the 6 sentinel raise sites.** That is Task 16. Sentinel raise-site count remains **0** in production code at end of Task 15.
- **W2 — Do not add `self._registry: ResolutionRegistry` to `DelegationController.__init__`.** Plan Step 16.4 owns this. `_WorkerRunner` receives a `ResolutionRegistry` instance directly via its constructor — does not depend on a controller-owned registry attribute.
- **W3 — Do not wire `spawn_worker` into `start()`.** That is Task 17 (Phase G). The `_WorkerRunner` skeleton exists but is unused in production paths under Task 15.
- **W4 — Do not wire `update_parked_request`.** Plan Task 16 step 16.3 has the production callsites. Task 14 Mode B tests (`test_delegation_controller.py:2588`, `test_delegate_start_integration.py:793`) **do NOT unblock at Task 15** — they unblock at Task 16.
- **W5 — Do not touch `_finalize_turn`.** Including the second `try/except Exception` around it (`:854-872`). Phase H Task 19 owns the Captured-Request Terminal Guard rewrite.
- **W6 — Canceled-inspection tests are contract guards, not red/green feature tests.** Plan Step 15.2 says "Expected: FAIL" — incorrect. Old code returns `None` at the negative tuple guard; new code returns `None` at the `if status == canceled` early-return. Both pass on both old and new code. The convergence-map intent is "canceled is terminal but non-materializing," distinct from old "canceled is irrelevant to materialization." Implementer should NOT manufacture a TDD red phase.
- **W7 — Use live line numbers** (anchor table above), NOT stale plan line numbers (`:873`, `:730`, `:650-720`).
- **W8 — Sentinel-raise-site count remains 0 in production after Task 15.** `rg "_WorkerTerminalBranchSignal\(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` must return `0` at commit time. Becomes 6 only after Task 16.
- **W9 — `cast` and `EscalatableRequestKind` already imported.** Do NOT re-add them. Verify via `rg "^from typing" packages/plugins/codex-collaboration/server/delegation_controller.py` and `rg "EscalatableRequestKind" packages/plugins/codex-collaboration/server/delegation_controller.py | head -3`.
- **W10 — `_WorkerTerminalBranchSignal` is `@dataclass(frozen=True) Exception` with empty `args`.** `str(signal)` returns `""`. Logging `str(signal)` would silently log empty strings. Test assertions on log output should target `signal.reason` substring, not full message equality.
- **W11 — Plan placeholder tests use fictional fixtures.** Do NOT paste them in even with skip decorators (skip-reason fabrication regression risk per Task 14 closeout-2). Omit entirely.

## Per-test triage table

| Test | Disposition | Notes |
|------|-------------|-------|
| `test_worker_runner_exists` | **Write** | `assert _WorkerRunner is not None`; one-line smoke. |
| `test_load_or_materialize_inspection_admits_canceled_job` | **Write (contract guard)** | Module-local `_build_controller`. Asserts `result is None` for canceled job. Passes on old + new code; W6 framing. |
| `test_load_or_materialize_inspection_does_not_materialize_for_canceled` | **Write (contract guard)** | `MagicMock(spec=_ArtifactStoreLike)` injected into `_build_controller`. Asserts `materialize_snapshot.assert_not_called()` and `reconstruct_from_artifacts.assert_not_called()`. |
| `test_execute_live_turn_catches_worker_terminal_branch_signal_post_branch` | **Write (sentinel catch — post-branch reason)** | `monkeypatch` makes `entry.session.run_execution_turn` raise `_WorkerTerminalBranchSignal(reason="dispatch_failed")`. Assert `_execute_live_turn` returns the stored job (NOT raises), and `_mark_execution_unknown_and_cleanup` was NOT invoked. Use `caplog` (built-in) to assert `"dispatch_failed"` substring in log output. |
| `test_execute_live_turn_catches_worker_terminal_branch_signal_pre_capture_reraises_as_delegation_start_error` | **Write (sentinel catch — pre-capture reason)** | Force `run_execution_turn` to raise `_WorkerTerminalBranchSignal(reason="unknown_kind_interrupt_transport_failure")`. Assert `pytest.raises(DelegationStartError)` with `exc.reason == "unknown_kind_interrupt_transport_failure"` and `exc.cause is None`. Use `caplog` substring assertion. |
| `test_worker_runner_translates_return_to_announce_parked` | **Omit** | Plan placeholder; requires real worker harness — Task 16/17 territory. |
| `test_execute_live_turn_catches_worker_terminal_branch_signal_post_decide` | **Omit** | Superseded by the two concrete sentinel tests above (named with explicit reason class). |
| `test_execute_live_turn_reraises_sentinel_as_delegation_start_error_for_pre_capture` | **Omit** | Same — superseded. |
| `test_execute_live_turn_sentinel_does_not_double_call_cleanup` | **Optional / write if cheap** | Combine into post-branch sentinel test as third assertion: `cleanup_call_count == 0` (handler-side cleanup not yet wired in Task 15, so catch should not double-call). Documents the invariant for Task 16. |
| `test_load_or_materialize_inspection_tuple_admits_canceled` | **Subsumed** | Implicit in the two written contract-guard tests. |

**Net new tests for Task 15: 5** (1 smoke + 2 contract guards + 2 sentinel catch). Optional 6th if combining cleanup-counter assertion.

## Out of scope (with plan-line citations)

| Item | Lands at | Plan citation |
|------|----------|---------------|
| 6 sentinel raise sites in handler body | Task 16 | `phase-f-worker.md:559-841` (Step 16.3) |
| `update_parked_request(job_id, request_id)` at capture | Task 16 | `phase-f-worker.md:661, 710, 804+, 853+, 948, 975, 1006, 1034` |
| `completion_origin="worker_completed"` writes | Task 16 | `phase-f-worker.md:721, 815, 864, 1088` (also closes carry-forward C10.4) |
| `self._registry` controller attribute | Task 16 step 16.4 | `phase-f-worker.md:1129-1133` |
| `_APPROVAL_OPERATOR_WINDOW_SECONDS` constant | Task 16 step 16.4 | `phase-f-worker.md:1137-1139` |
| Spawning worker from `start()` (`spawn_worker(...)`, `wait_for_parked(...)`) | Task 17 (Phase G) | `phase-g-public-api.md` (Task 17 body) |
| `decide()` reservation context manager rewrite | Task 18 (Phase G) | `phase-g-public-api.md` (Task 18 body) |
| `_finalize_turn` Captured-Request Terminal Guard | Task 19 (Phase H) | `phase-h-finalizer-consumers-contracts.md` (Task 19 body) |
| `poll()` `UnknownKindInEscalationProjection` catch + `signal_internal_abort` | Task 20 (Phase H) | `phase-h-finalizer-consumers-contracts.md:330+` (Task 20 body) |
| Task 14 Mode A unblock (6 tests) | Task 17 | Carry-forward `From Phase E Task 14` rows |
| Task 14 Mode B unblock (2 tests) | Task 16 | Carry-forward `From Phase E Task 14` rows |

## Acceptance criteria

- [ ] `packages/plugins/codex-collaboration/server/worker_runner.py` exists; defines `_WorkerRunner` class + `spawn_worker` helper; no lint/type regressions in modified files relative to the pre-Task-15 baseline (run `uv run --package codex-collaboration ruff check packages/plugins/codex-collaboration/server/ packages/plugins/codex-collaboration/tests/` and confirm no new findings).
- [ ] `_execute_live_turn` has new `except _WorkerTerminalBranchSignal as signal:` clause inserted **inside the first `run_execution_turn` try block, BEFORE the generic `except Exception:`**. The second `try/except Exception:` block (around `_finalize_turn`) is unchanged. Catch site logs `signal.reason` via `logger.info`, raises `DelegationStartError(reason="unknown_kind_interrupt_transport_failure", cause=None)` for the pre-capture reason, and returns `self._job_store.get(job_id)` for all other reasons.
- [ ] `_load_or_materialize_inspection` terminal-status tuple includes `"canceled"`; explicit `if job.status == "canceled": return None` short-circuit before `load_snapshot` call.
- [ ] New tests: 5 (or 6 if combining cleanup counter). All pass.
- [ ] Suite: 978 + N passing (where N = number of new tests, ≥5); 8 still skipped (Task 14's Mode A + Mode B set; none unskipped at Task 15); 0 failed.
- [ ] **W8 invariant check at commit time:** `rg "_WorkerTerminalBranchSignal\(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `0`.
- [ ] No edits to `_finalize_turn`, `_mark_execution_unknown_and_cleanup` body, `__init__`, or `start()`.
- [ ] `cast` and `EscalatableRequestKind` not re-imported.
- [ ] L1-L8 + W1-W11 honored end-to-end.

## Pre-dispatch checklist

- [ ] Convergence map (this file) shared with implementer
- [ ] Spec sentinel table inline (`design.md:474-484`)
- [ ] Spec catch site code inline (`design.md:489-538`)
- [ ] Plan Step 15.3 (worker_runner.py skeleton) verbatim — note lint-clean adjustments per L2
- [ ] Plan Step 15.4 (tuple expansion) verbatim
- [ ] Per-test triage table inline
- [ ] Acceptance criteria inline
- [ ] Reporting contract: implementer reports `DONE` with commit SHA + suite output line + W8 grep result + per-lock conformance summary; flags `BLOCKED` with question if any lock turns out unreachable (NOT `DONE_WITH_CONCERNS` — Task 14 process note: BLOCKED + question is preferred over DONE_WITH_CONCERNS + unilateral decision)
- [ ] Workflow: `superpowers:subagent-driven-development`, **single fresh implementer + spec reviewer + code-quality reviewer** (sequential, not parallel) — sonnet model for implementer

## Commit shape

| Step | Type | Subject |
|------|------|---------|
| 1 | feat | `feat(delegate): add _WorkerRunner + sentinel catch scaffold + canceled-inspection tuple (T-20260423-02 Task 15)` |
| 2 (only if review surfaces) | fix or docs | per Task 13/14 closeout pattern |

**No `docs(carry-forward)` closeout commit unless review surfaces a real new carry-forward item.** Task 15 is thin enough that the docs ceremony is unnecessary.

## Carry-forward expectations

| Item | Status post-Task-15 |
|------|---------------------|
| A1 (`signal.reason` not `str(signal)`) | **Closed by L4** |
| A2 (Task 16 raise-site comments absorb sentinel caller-contract docs) | Open — Task 16 |
| C10.4 (`completion_origin="worker_completed"` writes) | Open — Task 16 |
| Task 14 Mode A unblock (6 tests) | Open — Task 17 |
| Task 14 Mode B unblock (2 tests) | Open — Task 16 |
| E14.1 (`get_args` derivation) | Open — End-of-Packet-1 polish |
| Other phase-A/B/C/E13 carry-forward | Open — respective landing points |

---

**Status:** Ready for fresh-session dispatch. Load this file via `/handoff:load` continuation or read directly into the dispatch packet. Workflow: `superpowers:subagent-driven-development` with sonnet implementer + spec reviewer + code-quality reviewer (sequential).

# Convergence Map — Phase G Task 18 (`decide()` rewrite — `reserve` + `commit_signal` two-phase protocol; mechanism-level Bucket B closure)

**Drafted:** 2026-04-26 (controller + user two-read protocol; first draft restructured per user review identifying four P1 dispatch blockers — see Restructure Record at end of document; second draft revised per user round-2 review identifying two test-determinism contract issues at L9 + one L13 count typo — see Round-2 review addendum; third draft revised per user round-3 review identifying one residual validation-order race in tests #3/#7's follow-up-decide proxy assertion + one P2 cleanup-flexibility prune at test #4 — see Round-3 review addendum; fourth draft revised per user round-4 review correcting test #3's worker-blocking mechanism (post-commit `job.status` mutation at `:1166` precedes `session.respond` at `:1187`; live pre-decision status is `needs_escalation` not `awaiting_decision`) + one P2 stale-clause fix in round-2 addendum — see Round-4 review addendum; fifth draft revised per packet-review feedback correcting the W17/`:2400` mechanical-impossibility (`:2400` is inside `_finalize_turn` body, NOT inside the deleted decide() approve block; W2 protects it; W17 invariant grep returns `2` post-Task-18, not `1`) — see Round-5 review addendum).

**Scope (Option Y — narrow):** Task 18 owns the `decide()` reserve → journal-intent → `commit_signal` → audit rewrite and mechanism-level worker wake behavior. It does NOT absorb Task 19's `_finalize_turn` Captured-Request Terminal Guard. Tests asserting finalizer-derived terminal state move forward to a new G18.1 carry-forward (Task 19 unblock).

**Authority order:**
1. Spec §Transactional registry protocol: `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:250-345`
2. Spec §Response payload mapping: `design.md:1663-1702` (table at `:1667-1672`; deny rationale `:1682-1697`; non-empty `request_user_input` approve implementation-gate at `:1680`)
3. Spec §decide() semantics: `design.md:1646-1662`
4. Spec §`_finalize_turn` Captured-Request Terminal Guard: `design.md:1738-1808` (informational only — Task 19 territory; documents WHY 6 tests reclassify to G18.1)
5. Spec §Internal abort coordination: `design.md:347-440` (informational — explains why `signal_internal_abort` stays out of `decide()`)
6. Spec §Unknown-kind contract: `design.md:1703-1736` (rejection-reason rationale at `:1721`)
7. Phase G Task 18 plan body: `phase-g-public-api.md:290-538` — code skeleton informative, NOT binding where it conflicts with spec (see L4 for the payload-mapping divergence)
8. Carry-forward: G17.1 (9 F16.2 Bucket B) + Mode A defer (3 callsite-specific Bucket B) + RT.1 + (proposed) TT.1
9. Live code: HEAD is `c5829049`. Live-anchor line numbers describe the **post-Task-17-feat** orientation. Plan body's line citations (e.g., `decide()` "at `:1551`") are STALE.

## Live anchors (verified 2026-04-26 at HEAD `c5829049`)

| Symbol | File:line |
|---|---|
| `DelegationController.decide` def (TARGET FOR REWRITE) | `delegation_controller.py:2447` |
| Post-validation block START (REPLACE) | `delegation_controller.py:2560` |
| Post-validation block END (last line of `decide()`) | `delegation_controller.py:2675` |
| Approve-path `_execute_live_turn(...)` callsite (DELETE) | `delegation_controller.py:2644` |
| Deny-path local-finalize block (DELETE) | `delegation_controller.py:2606-2637` |
| `_finalize_turn` `DelegationEscalation` needs-escalation return site (DO NOT MODIFY per W2 — Task 19 territory) | `delegation_controller.py:2400` |
| Task 17's Parked-arm `DelegationEscalation` site (DO NOT MODIFY per W17) | `delegation_controller.py:837` |
| `_decided_request_ids` set init (DELETE per L6) | `delegation_controller.py:395` |
| `_decided_request_ids` `if request_id in ...` check (DELETE per L6) | `delegation_controller.py:2505-2514` |
| `_decided_request_ids.add` (deny path; DELETE) | `delegation_controller.py:2627` |
| `_decided_request_ids.add` (approve path; DELETE) | `delegation_controller.py:2665` |
| Pre-existing `decision == "deny" and answers` early-rejection (DELETE per L3) | `delegation_controller.py:2515-2521` |
| Existing `journal.write_phase("intent")` (REPOSITION — must follow `reserve`, precede `commit_signal`) | `delegation_controller.py:2562-2575` |
| Existing `journal.append_audit_event` (REPOSITION post-`commit_signal`; CHANGE `action="approve"` to `action=decision` per L7a) | `delegation_controller.py:2576-2588` |
| Existing `journal.write_phase("dispatched")` (DELETE per L8) | `delegation_controller.py:2589-2604` |
| `_reject_decision` helper (UNCHANGED) | `delegation_controller.py:2431` |
| `_persist_job_transition` helper (UNCHANGED; deny no longer calls it from `decide()`) | `delegation_controller.py:1419` |
| `_finalize_turn` def (DO NOT MODIFY — Task 19; preserve Task 17 L11 carve-out) | `delegation_controller.py:2324` |
| Task 17 L11 carve-out (`if interrupted_by_unknown: final_status = "unknown"`) | `delegation_controller.py:2367` |
| `start()` def (DO NOT MODIFY — Task 17 territory) | `delegation_controller.py:398` |
| `_dispatch_parked_capture_outcome` (Task 17 helper; DO NOT MODIFY per W15) | `delegation_controller.py:767-893` |
| `_execute_live_turn` def (DO NOT MODIFY per W16) | `delegation_controller.py:894` |
| Worker `session.respond` callsite (receives Task 18's helper payload via resolution.payload) | `delegation_controller.py:1187` |
| 6 sentinel raise sites (W3 invariant) | `delegation_controller.py:993, 1129, 1242, 1538, 1602, 1648` |
| `ResolutionRegistry.reserve` | `resolution_registry.py:209-223` |
| `ResolutionRegistry.commit_signal` | `resolution_registry.py:225-248` |
| `ResolutionRegistry.abort_reservation` | `resolution_registry.py:250-259` |
| `DecisionResolution` (passed to `reserve`) | `resolution_registry.py:32-40` |
| `ReservationToken` (type annotation only; see L5) | `resolution_registry.py:111-126` |
| Existing imports from `.resolution_registry` (Task 17 added 9 names) | `delegation_controller.py:102-112` |
| `_TASK_18_DECIDE_SIGNAL_REASON` constant in `test_delegation_controller.py` (RENAME per L10) | `test_delegation_controller.py:43-50` |
| `_TASK_18_DECIDE_SIGNAL_REASON` constant in `test_delegate_start_integration.py` (RENAME per L10) | `test_delegate_start_integration.py:31-38` |

## Locks (binding positive scope)

- **L1 — 12 Bucket B disposition split (3 close + 3 delete + 6 reclassify).** The 12 Bucket B retentions inherited from Task 17 do NOT all close in Task 18. Per dispatch-time audit against "does this test require Task 19's Captured-Request Terminal Guard to pass?":

  | Disposition | Count | Tests | Authority |
  |---|---|---|---|
  | **Stays in Bucket B (Task 18 unskips)** | 3 | `:1781, :2410, :1063` (all Mode A defer; mechanism-only — re-escalation continues turn, finalizer doesn't run on original capture) | L1 (this lock) |
  | **Pre-authorized DELETE (obsolete by architecture)** | 3 | `:2166, :2457, :2509` (all G17.1 / F16.2 — assert synchronous `CommittedDecisionFinalizationError` raise paths from `decide()` that no longer exist under the new model) | L11 |
  | **Pre-authorized RECLASSIFY to Bucket C / G18.1 (Task 19 unblock)** | 6 | `:1524, :1736, :1825, :1871, :856, :933` (all G17.1 / F16.2 — assert finalizer-derived terminal state which requires Task 19's spec §1738-1808 guard) | L12 |

  **Carry-forward consequences (encoded explicitly):**
  - **G17.1 partial closure:** 0 of 9 close as un-skips in Task 18; 3 delete; 6 → G18.1. G17.1 entry in carry-forward closes (its 9 items dispositioned), but lineage continues via DELETE notes + G18.1.
  - **Mode A row full closure:** 3 of 3 Mode A defer items close in Task 18 (`:1781, :2410, :1063`). Combined with Task 17's 3 Mode A closures, the entire 6-item Mode A row retires.
  - **F16.2 lineage stays Open via G18.1.** F16.2 was the parent 26-test surface; Task 17 closed 17 (Bucket A); Task 18 deletes 3 + reclassifies 6 to G18.1. F16.2 carry-forward entry stays Open with explicit lineage annotation; closes only when Task 19 lands G18.1.
  - **NEW G18.1** (Phase H Task 19 unblock surface — 6 tests + pre-authorized renames + body-rewrite for `:1524`).

- **L2 — `decide()` rewrite scope: replace post-validation block at `:2560-2675`.** The validation block above `:2560` (lines `:2447-2545`) is UNCHANGED except for the 3 specific deletions in L3. The replacement implements spec §Transactional registry protocol's 5-step sequence (validate → reserve → journal-intent → commit_signal → audit) with rollback semantics per L7.

- **L3 — Early-rejection branches preserved + 3 specific deletions.** Branches preserved (8 reasons):

  | Reason | Anchor | Action |
  |---|---|---|
  | `invalid_decision` | `:2455-2464` | UNCHANGED |
  | `job_not_found` | `:2465-2472` | UNCHANGED |
  | `job_not_awaiting_decision` | `:2473-2482` | UNCHANGED — also handles `kind="unknown"` jobs per spec §1721 (job is terminal `unknown`) |
  | `request_not_found` | `:2484-2494` | UNCHANGED |
  | `request_job_mismatch` | `:2495-2504` | UNCHANGED |
  | `request_already_decided` (`_decided_request_ids` check) | `:2505-2514` | **DELETE** — reservation CAS replaces |
  | `answers_not_allowed` (deny+answers) | `:2515-2521` | **DELETE** — kind-specific handling moves into `_build_response_payload` per L4 |
  | `answers_required` (RUI+approve+no-answers) | `:2522-2535` | UNCHANGED |
  | `answers_not_allowed` (non-RUI+answers) | `:2536-2545` | UNCHANGED |
  | `runtime_unavailable` | `:2547-2558` | UNCHANGED |

  After validation, the new flow: `_build_response_payload(decision, answers, request)` (L4) → `DecisionResolution(payload=..., kind=request.kind)` → `reserve(...)` → journal-intent (with rollback) → `commit_signal` → audit (post-commit, non-gating).

- **L4 — `_build_response_payload(decision, answers, request) -> dict[str, Any]` helper follows spec §Response payload mapping table at `design.md:1667-1672` ONLY; Path A is mandated (no Path B).** The plan body skeleton at `phase-g-public-api.md:498-505` contains TWO authoritative defects: it codes `"reject"` for deny on command/file kinds (spec §1670 mandates `"decline"` per `:1677` semantic + `:1682-1687` rationale reserving `cancel` for timeout/abort), and it codes `dict(answers or {})` unconditionally for `request_user_input` regardless of decision (spec §1670 mandates `{"answers": {}}` empty-fallback for deny per `:1689-1697` rationale).

  **Authoritative payload mapping (binding contract; full 6-row exact match required):**

  | Decision × Kind | Payload | Spec authority |
  |---|---|---|
  | `approve` × `command_approval` | `{"decision": "accept"}` | `design.md:1669` + `:1676` |
  | `approve` × `file_change` | `{"decision": "accept"}` | `design.md:1669` + `:1676` |
  | `approve` × `request_user_input` | `{"answers": <validated answers dict>}` | `design.md:1669` + **subject to Path A verification per `design.md:1680`** |
  | `deny` × `command_approval` | `{"decision": "decline"}` | `design.md:1670` + `:1677` + `:1682-1687` |
  | `deny` × `file_change` | `{"decision": "decline"}` | `design.md:1670` + `:1677` + `:1682-1687` |
  | `deny` × `request_user_input` | `{"answers": {}}` | `design.md:1670` + `:1689-1697` |

  **Path A mandate (no Path B fallback):** The non-empty `request_user_input` approve answers wire shape is plugin-assumed per spec §1680. Spec mandates verification via one of: (1) live App Server fixture/probe; (2) reading App Server source; (3) equivalent ground-truth check (e.g., pinned-version integration test). **Task 18 MUST file a verification artifact as a Packet 1 acceptance criterion.** If verification cannot be obtained in-scope (App Server source unavailable, no live fixture, no pinned version available), implementer reports **BLOCKED** with proposed scope expansion (e.g., "Task 18a: codex-app-server source verification + ground-truth artifact"). Do NOT ship Task 18 with the helper raising `RuntimeError` for non-empty RUI approve while still claiming the full 6-row contract — that is a Path B disposition explicitly rejected per pre-dispatch adjudication.

  **Verification artifact format:** the artifact (cite, fixture path, or test name + pinned-version) MUST be recorded in the feat commit message AND in a new "Verification artifacts" section at the bottom of this convergence map (added by closeout-docs).

  **No fallthrough / no `else`:** the helper has exhaustive kind handling for the 3 valid `EscalatableRequestKind` literals. Validation above already rejects `kind="unknown"` per spec §1721. Final clause: defensive `RuntimeError(f"_build_response_payload: unexpected kind={request.kind!r}")` for invariant violation.

- **L5 — Imports.** No new imports from `.resolution_registry` are required at the call level. `abort_reservation` and `commit_signal` are METHODS on the registry instance (`self._registry.abort_reservation(...)`, `self._registry.commit_signal(...)`); they are NOT free functions and therefore are NOT imported. `DecisionResolution` already imported by Task 17 (`:102-112` block extension). `ReservationToken` needed ONLY as a type annotation — if implementer uses `token: ReservationToken | None = ...` style annotations on local variables, add it to the existing `from .resolution_registry import (...)` block at `:102-112`. If implementer relies on inferred types, no import addition. **Verify the existing Task-17 import names** before adding: `DecisionResolution, InternalAbort, ResolutionRegistry, Parked, ParkedCaptureResult, StartWaitElapsed, TurnCompletedWithoutCapture, TurnTerminalWithoutEscalation, WorkerFailed`. Do NOT duplicate any of these.

- **L6 — `_decided_request_ids` retires across 4 callsites.** All 4 occurrences at `:395, :2505, :2627, :2665` MUST be deleted. Reserve CAS is the new authority for "already decided." Verification post-feat: `grep -n "_decided_request_ids" packages/plugins/codex-collaboration/server/delegation_controller.py` returns 0.

- **L7 — Audit `action=decision` (incidental fix) + rollback boundary lock.**

  **Sub-rule 7a (audit `action` field):** The new audit at the post-`commit_signal` position MUST set `action=decision` (the plugin-decision verb), matching plan body line 471 and spec §Transactional registry protocol pseudocode at `design.md:307`. Current code's hardcoded `action="approve"` at `:2581` (which fires for both approve AND deny because it sits BEFORE the deny/approve split at `:2606`) is a pre-existing bug fixed incidentally by the audit-relocation. NOT scope expansion. Document in commit message: "audit action=decision fixes pre-existing hardcoded action='approve' bug; incidental to required relocation per spec §1654."

  **Sub-rule 7b (rollback boundary):** `abort_reservation(token)` is called ONLY on journal-intent failure, NEVER on audit failure. Per spec §Transactional registry protocol failure table at `design.md:320-326`:

  | Failure between… | Outcome |
  |---|---|
  | `reserve()` returns None | Reject with `request_already_decided`; no rollback |
  | Journal intent raises | `abort_reservation(token)` → restore awaiting; re-raise |
  | `commit_signal` raises | Plugin-critical bug; log and crash; NO abort (per L14) |
  | Audit raises | Log warning; return success; NO abort (intent durable; abort would create ghost-intent per spec §343) |

  The `try / except BaseException: abort_reservation(token); raise` block surrounds ONLY the `journal.write_phase("intent")` call. The audit `try / except Exception: logger.warning(...)` block is SEPARATE and post-`commit_signal`; does NOT call `abort_reservation`.

- **L8 — `approval_resolution.dispatched` write deletion from `decide()`.** Per spec §1659: "`decide()` no longer writes it." Worker writes the dispatched phase as part of post-`registry.wait` cleanup (Task 16 production work; `:1187` worker `session.respond` callsite). Task 18 deletes the duplicate from `decide():2589-2604`. Verification post-feat: search for `phase="dispatched"` in `delegation_controller.py` returns ONLY worker-side site(s), zero `decide()`-side site(s).

- **L9 — New file `tests/test_delegate_decide_async_integration.py` — 10 acceptance tests.** Distinct from `tests/test_delegate_start_async_integration.py` (Task 17). Use module-local helpers per W4. The 10 tests:

  | # | Test name | Coverage |
  |---|---|---|
  | 1 | `test_decide_returns_3_field_result_on_success_approve` | Happy approve; `DelegationDecisionResult(decision_accepted=True, job_id, request_id)` |
  | 2 | `test_decide_returns_3_field_result_on_success_deny` | Happy deny; same shape |
  | 3 | `test_decide_twice_second_returns_request_already_decided` | Same-rid double-decide; second `decide()` returns `DecisionRejectedResponse(reason="request_already_decided", ...)`. **Deliberate worker-blocking required at the post-commit job-status mutation point.** `decide()`'s validation order is `job_not_awaiting_decision` BEFORE `reserve()` — and the worker, post-wake from `commit_signal`, mutates `job.status` from `needs_escalation` to `running` at `delegation_controller.py:1166` (BEFORE calling `session.respond` at `:1187`). If that mutation lands before the second decide reaches validation, second decide rejects with `job_not_awaiting_decision` instead of the intended `request_already_decided`. On the success path: live worker subsequently calls `registry.discard(rid)` per `:1278`, producing `request_not_found` from the registry-side check. **Mandated blocking pattern:** (1) complete initial `start()` and parked-request setup normally — do NOT block the initial park (that prevents the test from ever obtaining a pending request to decide on); (2) install a wrapper on `job_store.update_status_and_promotion` that gates ONLY the resume call where `status=="running"` (the post-`commit_signal` mutation), passing all other update_status_and_promotion calls through unblocked; (3) call first `decide(approve, ...)` (with kind-appropriate decision arguments per L3 + L4 — for `command_approval`/`file_change` parked requests, no `answers` payload; for `request_user_input`, a valid answers dict) — worker wakes via `commit_signal` and blocks at the wrapper BEFORE writing `running`, so `job.status` stays `needs_escalation`; (4) call second `decide(rid, ...)` — validation passes (status is still `needs_escalation`) → reaches `reserve()` → returns None → assert `request_already_decided`; (5) release the wrapper gate; worker drains naturally for teardown. **Rejected blocking patterns:** monkeypatching `_execute_live_turn` after `start()` has no effect (the existing worker thread is already inside the method post-park; patches on the bound symbol don't affect the running execution); monkeypatching `_execute_live_turn` before `start()` blocks the initial park itself (test never obtains the pending request); blocking `session.respond` is too late (job.status mutation at `:1166` precedes respond at `:1187`). |
  | 4 | `test_decide_competing_reservation_returns_request_already_decided` | **Deterministic competing-reservation:** test directly calls `controller._registry.reserve(rid, ...)` to force the entry out of `awaiting` → `decide()` reaches its `reserve()` → returns None → `request_already_decided`. **Explicit drain required:** `abort_reservation(competing_token)` only restores `awaiting` — it does NOT set the wake event, so the worker stays parked in `registry.wait()` after abort. **Mandated cleanup pattern:** `abort_reservation(competing_token)` then call `controller.decide(approve, ...)` normally with kind-appropriate decision arguments per L3 + L4 (no `answers` payload for `command_approval`/`file_change`; valid answers dict for `request_user_input`) to drive the production reserve→commit_signal→worker-wake path. Direct `commit_signal(competing_token)` is NOT permitted — it would route the test-held fake `DecisionResolution` payload through the worker's `session.respond` dispatch path, testing an artificial cleanup mechanism rather than production decide semantics. NOT a timer-race test (timer firing also commits per `resolution_registry.py:393`, which would change job state non-deterministically). |
  | 5 | `test_decide_writes_intent_before_commit_signal_ordering` | Capture call order via journal_spy or wrapper; assert `write_phase("intent")` index < `commit_signal` index |
  | 6 | `test_decide_aborts_reservation_on_journal_intent_failure` | Force `journal.write_phase` to raise; assert `abort_reservation(token)` called; assert exception propagates; assert entry is back in `awaiting` (verifiable via follow-up `reserve` succeeding). **Explicit drain required:** post-abort, the worker remains parked in `registry.wait()` (`abort_reservation` does not wake). Cleanup MUST un-sabotage the journal AND drive a real `controller.decide(approve, ...)` (with kind-appropriate decision arguments per L3 + L4) to release the worker through the production path. |
  | 7 | `test_decide_audit_event_post_commit_non_gating` | Force `journal.append_audit_event` to raise; assert warning logged at `decide()`-level audit (distinct from any worker-side audit); assert `decide()` returns `DelegationDecisionResult(decision_accepted=True, ...)`. **Do NOT use follow-up `decide(rid)` as proof of slot-still-claimed** — the rejection reason is scheduler-dependent: validation order is `job_not_awaiting_decision` BEFORE `reserve()`, and the worker's post-wake job-status mutation OR `registry.discard(rid)` per `delegation_controller.py:1278` will produce `job_not_awaiting_decision` or `request_not_found` instead of the intended `request_already_decided`. Durable non-racing assertions for the non-gating contract: (a) decide() returned success; (b) audit warning was logged; (c) journal `intent` entry persists in journal_spy capture (was written before audit per L7b ordering, so durable regardless of audit failure); (d) worker eventually dispatches `session.respond` (verifiable via mocked respond capture; proves `commit_signal` fired and woke the worker despite audit failure, which is the actual non-gating evidence). |
  | 8 | `test_decide_audit_action_matches_decision_for_approve` | `AuditEvent.action == "approve"` post-feat (regression for L7a incidental fix) |
  | 9 | `test_decide_audit_action_matches_decision_for_deny` | `AuditEvent.action == "deny"` post-feat (regression: pre-Packet-1 had `action="approve"` hardcoded for both) |
  | 10 | `test_build_response_payload_per_kind_decision` | Parameterized over the 6 valid (kind, decision) combinations from L4 table; asserts EXACT payload dict for each. Covers `decline` per spec §1670 (vs plan body's `reject` typo) and `{"answers": {}}` deny-on-RUI fallback. |

  Implementer may add tests as judgment dictates (e.g., `test_decide_commit_signal_wakes_worker`). Per W4 all tests use module-local `_build_controller(tmp_path)` + built-in pytest fixtures + `unittest.mock.MagicMock` / `unittest.mock.patch.object`.

- **L10 — Test-side surgery: 3 decorator removals + 3 obsolete-test deletions + constant rename in 2 files.** Mechanically uniform per file:

  **`test_delegation_controller.py`:**
  - Remove decorators at `:1781, :2410` (Task 18 unskips — Mode A defer)
  - DELETE entire test bodies at `:2166` (`test_decide_approve_turn_failure_raises_committed_decision_finalization_error`), `:2457` (`test_decide_approve_post_turn_journal_failure_raises_committed_decision_finalization_error`), `:2509` (`test_decide_deny_post_commit_failure_raises_committed_decision_finalization_error`) per L11
  - Remaining 4 decorators (`:1524, :1736, :1825, :1871`) STAY with reason updated via constant rename per L12
  - Rename constant `_TASK_18_DECIDE_SIGNAL_REASON` → `_TASK_19_FINALIZER_GUARD_REASON` at `:43-50` with new text:

    ```python
    _TASK_19_FINALIZER_GUARD_REASON = (
        "Phase H Task 19: _finalize_turn does not yet apply the "
        "Captured-Request Terminal Guard. Without the guard's "
        "resolved/canceled request-snapshot mapping at spec §1762-1767, "
        "_finalize_turn misclassifies decide-success and timeout-cancel-"
        "success captures as needs_escalation via the kind-based branch "
        "at delegation_controller.py:~2367 (Task 17 L11 preserved this "
        "branch as Task 19 territory per W2 narrowing). Tests asserting "
        "post-resume final_status='completed' / 'canceled' / 'unknown' or "
        "DelegationOutcomeRecord shape cannot pass without the guard. "
        "Skip preserved until Task 19 lands the spec §1738-1808 rewrite."
    )
    ```

  **`test_delegate_start_integration.py`:**
  - Remove decorator at `:1063` (Task 18 unskip — Mode A defer)
  - Remaining 2 decorators (`:856, :933`) STAY with reason updated via constant rename per L12
  - Rename constant identically at `:31-38` (new text identical to controller-test version)

  Verification post-feat:
  - `grep -c "@pytest.mark.skip(reason=_TASK_19_FINALIZER_GUARD_REASON)"` returns 4 (in `test_delegation_controller.py`) + 2 (in `test_delegate_start_integration.py`) = 6 total
  - `grep -c "_TASK_18_DECIDE_SIGNAL_REASON"` returns 0+0 (constant removed)
  - `grep -c "@pytest.mark.skip" tests/test_handler_branches_integration.py` returns 2 (F16.1 untouched per W8)

- **L11 — Pre-authorized DELETE for 3 obsolete CDFE tests.** The legacy synchronous `decide()` model raised `CommittedDecisionFinalizationError` when `decide()` committed the audit but failed local finalization. Under Task 18's reserve+commit_signal+audit model, `decide()` has zero synchronous-finalization failure paths: reserve-None returns rejection (not exception); journal-intent failure aborts and re-raises the original exception (not CDFE); commit_signal failure crashes loudly per L14 (impossible-by-construction); audit failure logs warning and returns success. **There is no path from the new `decide()` that synchronously raises `CommittedDecisionFinalizationError`.** The 3 tests assert a code path that no longer exists.

  Pre-authorized for DELETE in Task 18 feat commit:
  | File:line | Test name |
  |---|---|
  | `test_delegation_controller.py:2166` | `test_decide_approve_turn_failure_raises_committed_decision_finalization_error` |
  | `test_delegation_controller.py:2457` | `test_decide_approve_post_turn_journal_failure_raises_committed_decision_finalization_error` |
  | `test_delegation_controller.py:2509` | `test_decide_deny_post_commit_failure_raises_committed_decision_finalization_error` |

  **Deletion authority:** L11 (this lock). The CDFE class itself is NOT deleted in Task 18 (other code paths may raise it; that's out-of-scope audit work). Only the 3 test bodies are removed. Replacement coverage: L9 test #6 covers the journal-intent rollback path (the closest analog under the new model); L9 test #7 covers audit-failure non-gating.

  **ANY OTHER test deletion requires BLOCKED + adjudication** (per W18). Implementer reports BLOCKED if they encounter a test whose body asserts behavior incompatible with the new flow but which is NOT in the L11 pre-authorized list.

- **L12 — Pre-authorized RECLASSIFY (Bucket B → Bucket C / G18.1) for 6 finalizer-dependent tests.** These 6 tests assert post-resume terminal state derived through `_finalize_turn`'s Captured-Request Terminal Guard (spec §1738-1808; Task 19's spec authority). Under Task 18 alone, `_finalize_turn` retains the pre-Packet-1 kind-based escalation logic with Task 17's L11 carve-out for `interrupted_by_unknown` only — the `_CANCEL_CAPABLE_KINDS` branch at `:2367` is W2-preserved Task 19 territory. So `decide(approve)` followed by worker resume + `turn/completed` results in `_finalize_turn` misclassifying the resolved capture as `needs_escalation`, breaking these tests.

  Pre-authorized for RECLASSIFY in Task 18 feat commit (decorator stays; reason text updated via L10's constant rename):

  | File:line | Test name | Why finalizer-dependent |
  |---|---|---|
  | `test_delegation_controller.py:1524` | `test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up` | L13 docstring extension flagged body REWRITE; new body asserts `final_status="unknown"` via spec §1764 row 2 OB-1 mapping (resolved+failed→unknown) |
  | `test_delegation_controller.py:1736` | `test_decide_approve_resumes_runtime_and_returns_completed_result` | Asserts `job.status="completed"` post-resume — requires spec §1764 row 1 mapping (resolved+completed→completed) |
  | `test_delegation_controller.py:1825` | `test_decide_deny_marks_job_failed_and_closes_runtime` | New behavior depends on App Server's response to `decline` + `_finalize_turn` mapping; rename to `test_decide_deny_dispatches_decline_through_worker_resume` deferred to Task 19 (recorded in G18.1) |
  | `test_delegation_controller.py:1871` | `test_decide_deny_emits_terminal_outcome` | Terminal outcome derives from `_finalize_turn` post-resume; rename to `test_decide_deny_terminal_outcome_is_emitted_from_worker_finalization` deferred to Task 19 (recorded in G18.1) |
  | `test_delegate_start_integration.py:856` | `test_delegate_decide_approve_end_to_end_through_mcp_dispatch` | E2E asserts full flow including final job state via `_finalize_turn` |
  | `test_delegate_start_integration.py:933` | `test_delegate_decide_deny_end_to_end_through_mcp_dispatch` | Same — E2E asserts terminal state derived from finalizer |

  **Reclassification authority:** L12 (this lock). The 6 decorators stay in place; reason text updates automatically via L10's constant rename. NO body rewrites or renames are applied in Task 18 (those are Task 19's work, recorded as G18.1 carry-forward — see "G18.1 carry-forward record" section below).

  **ANY OTHER test reclassification requires BLOCKED + adjudication** (per W18 + the L13 process precedent recorded as feedback memory `feedback_bucket_reclassification_requires_blocked.md`). Implementer reports BLOCKED if a Bucket B test classified as Task-18-closeable (`:1781, :2410, :1063`) turns out to have finalizer-dependent assertions, OR if a Bucket C test classified as G18.1-deferred turns out to be mechanism-only.

- **L13 — L12 (Task-17-inherited) assertion-shape authority table — applies to the 3 Task-18-closing tests + 10 acceptance tests only.** Task 17's L12 5-row table for assertion-shape updates is INHERITED but TRIMMED for Task 18: rows that cross into finalizer territory belong to G18.1 / Task 19, not Task 18. The applicable rows for Task 18:

  **Task-18-applicable assertion-shape authority (subset):**

  | New assertion | Spec authority | Applies to |
  |---|---|---|
  | `agent_context=None` on `Parked`-path `DelegationEscalation` | `design.md:785-797` (Task 17 inherited) | `:1781`, `:1063` (re-escalation tests where the NEW request projects an escalation) |
  | Captured request status remains `"pending"` until `decide()` resumes worker | `design.md:786-797` | All 3 Task-18-closing tests |
  | Escalation audit events deferred (NOT emitted during `start()`) | `design.md:786-797` | `:1781`, `:1063` (E2E re-escalation observers) |
  | `request_user_input` parks (returns `DelegationEscalation`) instead of synchronously completing | `design.md:659-910` | `:1781` (re-escalation path) |
  | `DelegationDecisionResult(decision_accepted=True, job_id=..., request_id=...)` is the ONLY success-shape returned by `decide()` | `design.md:1620-1644` | All 3 Task-18-closing tests + acceptance tests 1, 2 |
  | `request_already_decided` rejection on duplicate `decide()` calls — authority is reservation CAS, NOT `_decided_request_ids` set | `design.md:280-345` | `:2410` (stale-rid rejection); acceptance tests 3, 4 |
  | `decide()`'s return path is `commit_signal` → audit → return; it does NOT block on worker progress. Enforceable orderings: (a) journal-intent precedes `commit_signal`; (b) `decide()` returns without waiting on `_finalize_turn` or post-resume worker observation. Tests MUST NOT assert that `decide()` returns BEFORE the worker dispatches `respond` or observes `turn/completed` — `commit_signal` releases the worker via a `threading.Event`, and the worker may complete its dispatch and observation before `decide()`'s audit returns (the race is unenforceable without deliberate worker-blocking) | `design.md:280-345` | All 3 Task-18-closing tests + acceptance tests 5, 6, 7 |
  | Audit event fires AFTER `commit_signal` returns (post-commit, non-gating); audit failure logs warning + returns success | `design.md:1646-1655` | Acceptance tests 7, 8, 9 |

  **Rows NOT in this table (deferred to G18.1):** the 5th Task-17-inherited row about unknown-kind paths returning `DelegationJob`, AND any new row about post-resume terminal-status derivation through `_finalize_turn` — both belong to Task 19's Captured-Request Terminal Guard work.

  **Forward-looking rule (unchanged):** assertion shapes that DIRECTLY mirror an authority-table row are implementer-discretion. Assertion shapes that ADD new behavior or test new spec sections REQUIRE BLOCKED + adjudication.

- **L14 — `commit_signal` failure semantics: log and crash, do NOT abort.** Per spec §`Failure analysis per step` table at `design.md:325`: "Journal `intent` succeeds, `commit_signal` raises → Impossible by construction: `commit_signal` is a local `threading.Event.set()` + state mutation. If it raises, the plugin has a deeper bug — log and crash loudly rather than abort." Implementer MUST NOT add `try/except` around `self._registry.commit_signal(token)`. The line stands bare.

## Watchpoints (binding negative scope)

- **W1 — Do NOT modify `start()` body.** `:398-893` (Task 17 territory).

- **W2 — Do NOT modify `_finalize_turn` body.** `:2324+` (Task 19 territory). Task 17 L11 carve-out at `:2367` (the `if interrupted_by_unknown: final_status = "unknown"` split) MUST be preserved as-is.

- **W3 — Do NOT modify the 6 sentinel raise sites or their reasons.** `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `6` post-Task-18.

- **W4 — Do NOT use plan-pseudocode fictional fixtures.** `delegation_controller_fixture`, `app_server_runtime_stub`, `journal_spy`, `audit_event_spy` do NOT exist in `tests/conftest.py`. Use module-local `_build_controller(tmp_path)` + built-in pytest fixtures + `unittest.mock.MagicMock` / `unittest.mock.patch.object`.

- **W5 — Newly-unskipped 3 + 10 new acceptance tests must complete without hang.** Post-Task-17 mitigations (daemon=True on worker thread + per-request timer threads) carry forward. Verification protocol:
  1. Full suite: `uv run --package codex-collaboration pytest -v`. Expected wall-clock ~30-40s; exit code 0; no SIGTERM/timeout messages.
  2. Order-independence smoke: run BOTH orderings explicitly and compare:
     ```bash
     uv run --package codex-collaboration pytest \
       packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
       packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py \
       packages/plugins/codex-collaboration/tests/test_delegate_decide_async_integration.py
     uv run --package codex-collaboration pytest \
       packages/plugins/codex-collaboration/tests/test_delegate_decide_async_integration.py \
       packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py \
       packages/plugins/codex-collaboration/tests/test_delegation_controller.py
     ```
     Both yield identical pass/skip counts and exit code 0.

- **W6 — Do NOT re-import names already in scope.** `cast`, `EscalatableRequestKind`, `ResolutionRegistry`, `DecisionResolution`, `InternalAbort`, `Parked`, `ParkedCaptureResult`, `StartWaitElapsed`, `TurnCompletedWithoutCapture`, `TurnTerminalWithoutEscalation`, `WorkerFailed`, `assert_never`, `spawn_worker` — all already imported per Task 17. Only candidate addition: `ReservationToken` (and only as type annotation per L5).

- **W7 — Plan-line numbers throughout `phase-g-public-api.md` Task 18 body are stale.** Plan body cites `decide()` "at `:1551`"; live anchor is `:2447`. Plan body's "logic preserved from the previous decide implementation's payload-building section" wording is also stale (the previous decide does NOT build payloads — deny is local-finalize, no respond call). Use the live anchors table.

- **W8 — Do NOT delete F16.1 decorators at `test_handler_branches_integration.py:161, 179`.** They cite Phase H Task 19 explicitly. Out of Task 18 scope.

- **W9 — Do NOT change Task 16/17 sentinel semantics or `__init__` registry init.** Task 16 added `self._registry: ResolutionRegistry = ResolutionRegistry()` in `__init__`; Task 17 added `START_OUTCOME_WAIT_SECONDS = 30`. Task 18 USES `self._registry` from `decide()`; does NOT re-init or shadow.

- **W10 — Pre-existing `runtime.py:270` Pyright error MUST NOT be "fixed" as side-effect.** Per Task 16 G34 + Task 17 W10 stash-test history: `TurnStatus` literal narrowing pre-existing Phase F. RT.1 carry-forward owns this.

- **W11 — Pre-existing `_FakeControlPlane` Pyright issues MUST NOT be "fixed" as side-effect.** Per Task 17 Post-implementer adjudication record: pre-existing test-fixture protocol mismatches at `test_delegation_controller.py:257, 2547, 2621, 2686, 2867, 2888, 3064, 3194, 3418`. Task 18 closeout-docs MAY formally promote to a tracked TT.1 carry-forward item.

- **W12 — Plan Step 18.1's failing-test stubs use `pass` bodies under fictional fixtures.** Implementer must replace EVERY `pass` body with real assertion shapes. Do NOT commit `pass`-bodied tests as Task 18 acceptance evidence.

- **W13 — Do NOT use the spec's context-manager `with registry.reservation(rid, resolution) as token:` pattern.** Per spec §328-339 the spec mentions a context-manager variant — but the LIVE registry at `resolution_registry.py:209-259` does NOT implement `def reservation(...)`. Only `reserve`, `commit_signal`, `abort_reservation`, `wait`, `signal_internal_abort`, `discard` exist. Use the explicit `try / except / abort_reservation` form per plan body.

- **W14 — Do NOT introduce `signal_internal_abort` calls in `decide()`.** Per spec §`Internal abort coordination` at `design.md:347-440` and §1700: `decide()` no longer projects a pending view in Packet 1's normal path; abort trigger surfaces only on the `poll()` path. `decide()`'s only registry interactions are `reserve` / `commit_signal` / `abort_reservation`.

- **W15 — Do NOT modify `_dispatch_parked_capture_outcome` at `:767-893`.** Task 17's helper. BLOCKED if a code-edit appears to require touching it.

- **W16 — Do NOT modify `_execute_live_turn` def at `:894`.** Still called by `spawn_worker(...)` on the worker thread. Task 18 deletes the CALL from `decide():2644`; the FUNCTION DEFINITION stays untouched.

- **W17 — Do NOT modify any `DelegationEscalation` construction site.** Two live sites exist at HEAD `c5829049`: `:837` (Task 17's Parked-arm site) and `:2400` (`_finalize_turn`'s needs-escalation return; W2-protected — Task 19 territory). Task 18 modifies neither. The legacy `decide()` approve block does NOT contain a `DelegationEscalation` construction (the legacy approve path returned via `_execute_live_turn`'s indirect path, not by directly constructing a `DelegationEscalation` inside `decide()`). Verification: `grep -c "DelegationEscalation(" packages/plugins/codex-collaboration/server/delegation_controller.py` returns `2` post-Task-18 (UNCHANGED from pre-Task-18).

- **W18 — ANY test rename, deletion beyond L11, reclassification beyond L12, or bucket adjustment requires BLOCKED + adjudication.** Per the L13 process precedent recorded as feedback memory `feedback_bucket_reclassification_requires_blocked.md`. **No Task 18 renames are pre-authorized** (the 2 deny-test renames defer to Task 19 via G18.1). If a Bucket B test classified as Task-18-closeable turns out to have finalizer-dependent assertions, or if a Bucket C test classified as G18.1-deferred turns out to be mechanism-only — report BLOCKED with proposed disposition + spec citation.

## Branch matrix (decide outcomes × decision × kind + invariant paths)

| # | Decision × Kind | Validation result | Reservation outcome | Worker outcome | `decide()` returns |
|---|---|---|---|---|---|
| 1 | `approve` × `command_approval` | OK | reserve OK; commit_signal | worker dispatches `respond({"decision": "accept"})` | `DelegationDecisionResult(decision_accepted=True, ...)` |
| 2 | `approve` × `file_change` | OK | reserve OK; commit_signal | worker dispatches `respond({"decision": "accept"})` | same |
| 3 | `approve` × `request_user_input` (with answers) | OK | reserve OK; commit_signal | worker dispatches `respond({"answers": <validated>})` | same; **L4 Path A verification artifact required** |
| 4 | `deny` × `command_approval` | OK | reserve OK; commit_signal | worker dispatches `respond({"decision": "decline"})` | same |
| 5 | `deny` × `file_change` | OK | reserve OK; commit_signal | worker dispatches `respond({"decision": "decline"})` | same |
| 6 | `deny` × `request_user_input` | OK | reserve OK; commit_signal | worker dispatches `respond({"answers": {}})` (empty-fallback per spec §1689-1697) | same |
| 7 | duplicate / competing reservation (any) | OK on validation | `reserve` returns `None` (entry in `reserved`/`consuming`/`aborted`) | n/a — slot already claimed | `DecisionRejectedResponse(reason="request_already_decided", ...)` |
| 8 | invalid args (8 reasons per L3) | early-reject | n/a (no reserve taken) | n/a | `DecisionRejectedResponse(reason=<various>, ...)` |
| 9 | journal-intent fails (`write_phase("intent")` raises) | OK | reserve OK; `abort_reservation(token)` → restore awaiting | worker stays parked in `registry.wait()` | exception propagates; entry returns to `awaiting` |
| 10 | audit fails (`append_audit_event` raises post-`commit_signal`) | OK | reserve OK; commit_signal succeeded | worker has woken; dispatches respond | logged warning; `DelegationDecisionResult(decision_accepted=True, ...)` |

## Per-test triage

### Bucket B — Task 18 unblocks (3 decorators removed)

| File:line | Class | Test name | Why mechanism-only |
|---|---|---|---|
| `test_delegation_controller.py:1781` | Mode A defer | `test_decide_approve_can_reescalate_with_new_pending_request` | Asserts first decision accepted, then `poll()` sees a NEW pending escalation with rid `99`. Uses `_finalize_turn` only for the NEW interrupted request (where current kind-based escalation is still valid). Does NOT need Task 19's resolved/canceled mapping for the original request. |
| `test_delegation_controller.py:2410` | Mode A defer | `test_decide_rejects_stale_request_id_after_reescalation` | Stale rid `42` rejection driven by old registry entry being non-reservable/discarded post-commit_signal — reservation CAS protocol, not `_decided_request_ids`. Mechanism-level. |
| `test_delegate_start_integration.py:1063` | Mode A defer | `test_decide_reescalation_uses_pending_escalation_key` | MCP projection test for re-escalation via `poll()`, not terminal finalization. |

### Bucket C / G18.1 — Task 19 unblocks (6 decorators retained with new constant)

| File:line | Class | Test name | Why finalizer-dependent |
|---|---|---|---|
| `test_delegation_controller.py:1524` | F16.2 → reclassified per Task 17 L13 | `test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up` | Body REWRITE asserts `final_status="unknown"` via spec §1764 row 2 OB-1 mapping (deferred to Task 19) |
| `test_delegation_controller.py:1736` | G17.1 (F16.2) | `test_decide_approve_resumes_runtime_and_returns_completed_result` | Asserts `completed` via spec §1764 row 1 |
| `test_delegation_controller.py:1825` | G17.1 (F16.2) | `test_decide_deny_marks_job_failed_and_closes_runtime` | New behavior asserts `_finalize_turn` mapping post-decline; rename + body rewrite deferred to Task 19 (G18.1) |
| `test_delegation_controller.py:1871` | G17.1 (F16.2) | `test_decide_deny_emits_terminal_outcome` | Terminal outcome via `_finalize_turn`; rename + body rewrite deferred to Task 19 (G18.1) |
| `test_delegate_start_integration.py:856` | G17.1 (F16.2) E2E | `test_delegate_decide_approve_end_to_end_through_mcp_dispatch` | E2E asserts terminal job state via finalizer |
| `test_delegate_start_integration.py:933` | G17.1 (F16.2) E2E | `test_delegate_decide_deny_end_to_end_through_mcp_dispatch` | Same |

### DELETE — obsolete by architecture (3 tests; pre-authorized per L11)

| File:line | Test name |
|---|---|
| `test_delegation_controller.py:2166` | `test_decide_approve_turn_failure_raises_committed_decision_finalization_error` |
| `test_delegation_controller.py:2457` | `test_decide_approve_post_turn_journal_failure_raises_committed_decision_finalization_error` |
| `test_delegation_controller.py:2509` | `test_decide_deny_post_commit_failure_raises_committed_decision_finalization_error` |

### Out of Task 18 entirely — F16.1 (Phase H Task 19 owns)

| File:line | Test name |
|---|---|
| `test_handler_branches_integration.py:161` | `test_happy_path_decide_approve_success` |
| `test_handler_branches_integration.py:179` | `test_timeout_cancel_dispatch_succeeded_for_file_change` |

UNTOUCHED per W8.

### New acceptance tests (`test_delegate_decide_async_integration.py`) — 10 written

See L9 for full table.

## G18.1 carry-forward record (pre-authorizations for Task 19's convergence map to inherit)

When Task 19 lands `_finalize_turn` Captured-Request Terminal Guard rewrite per spec §1738-1808, the following operations are PRE-AUTHORIZED in the same commit:

1. **Decorator removal** on all 6 G18.1 tests:
   - `test_delegation_controller.py:1524, :1736, :1825, :1871`
   - `test_delegate_start_integration.py:856, :933`

2. **Constant deletion** of `_TASK_19_FINALIZER_GUARD_REASON` in BOTH test files (becomes dead code post-removal; mirrors Task 18's `_TASK_18_DECIDE_SIGNAL_REASON` deletion pattern).

3. **RENAME** at `test_delegation_controller.py:1825`:
   - From: `test_decide_deny_marks_job_failed_and_closes_runtime`
   - To: `test_decide_deny_dispatches_decline_through_worker_resume`

4. **RENAME** at `test_delegation_controller.py:1871`:
   - From: `test_decide_deny_emits_terminal_outcome`
   - To: `test_decide_deny_terminal_outcome_is_emitted_from_worker_finalization`

5. **BODY REWRITE** at `test_delegation_controller.py:1524`. Per Task 17's `dc90c1d9` docstring extension: body asserts the `worker_failed_before_capture` fallback shape (NOT the expected Task-19 failure path). New body must:
   1. Set up parked worker via `start()` (Task 17 Parked path).
   2. Call `decide(approve)` with journal sabotage on `_finalize_turn`'s post-resume `journal.append_audit_event` call (the SECOND audit emit, not the post-commit `decide()` audit which is non-gating).
   3. Assert worker resumes via `commit_signal`, dispatches respond, observes `turn/completed`, then `_finalize_turn` runs into the sabotage.
   4. Assert resulting `job.status="unknown"` per spec §1764 row 2 (resolved+failed→unknown OB-1).
   5. Assert cleanup happens (runtime release, session close).

6. **L12 assertion-shape review** per the Task-17-inherited 5-row authority table (now with Task-19-specific extensions for `_finalize_turn` mapping rows) for the remaining 3 G18.1 tests (`:1736, :856, :933`).

**Authority for Task 19 to act on these pre-authorizations:** L12 (this Task 18 lock) + W18 narrow exception. Task 19's convergence map MUST inherit this section verbatim.

## Out of scope (with plan/spec citations)

| Item | Lands at | Authority citation |
|---|---|---|
| `start()` body or `_dispatch_parked_capture_outcome` | Phase G Task 17 (closed) | Task 17 convergence map |
| `_finalize_turn` Captured-Request Terminal Guard rewrite | Phase H Task 19 | `phase-h-finalizer-consumers-contracts.md:11+` + spec §1738-1808 |
| The 6 G18.1 finalizer-dependent tests (decorator removals, renames, body rewrite, assertion review) | Phase H Task 19 (same-commit per G18.1 pre-authorization above) | L12 + G18.1 carry-forward record |
| `poll()` `UnknownKindInEscalationProjection` catch + `signal_internal_abort` | Phase H Task 20 | `phase-h-finalizer-consumers-contracts.md:330+` |
| `discard()` admits canceled jobs | Phase H Task 21 | `phase-h-finalizer-consumers-contracts.md` |
| `contracts.md` updates | Phase H Task 22 | `phase-h-finalizer-consumers-contracts.md` |
| F16.1 finalizer-routed integration tests | Phase H Task 19 | Per W8 + spec §1790+ |
| `runtime.py:270` Pyright fix (RT.1) | End-of-Phase-G or end-of-Packet-1 typing polish | Pre-existing per Task 16 G34 |
| `_FakeControlPlane` Pyright fixes (proposed TT.1) | Same — typing polish | Per Task 17 Post-implementer adjudication record |
| Context-manager `registry.reservation(...)` API addition | Out of Packet 1 | Per W13 + spec §328-339 |
| App Server source verification for non-empty RUI approve answers | **Task 18 (mandatory per L4 Path A)** OR BLOCKED + scope expansion if not feasible | Spec `design.md:1680` |

## Acceptance criteria

### Code (mandatory)

- [ ] `decide()` post-validation block at `:2560-2675` REPLACED with new reserve→intent→commit_signal→audit flow (L2)
- [ ] Early-rejection branches preserved per L3; 3 specific deletions: `_decided_request_ids` check, `decision == "deny" and answers` early-rejection, `approval_resolution.dispatched` write
- [ ] `_decided_request_ids` retired across 4 callsites (L6); verification: `grep -n "_decided_request_ids" delegation_controller.py` returns 0
- [ ] New `_build_response_payload(self, decision, answers, request) -> dict[str, Any]` helper per L4; payload mapping matches the 6-row table EXACTLY (`accept` for approve on command/file; **`decline`** for deny on command/file; `{"answers": <dict>}` for approve on RUI; **`{"answers": {}}`** for deny on RUI)
- [ ] **L4 Path A verification artifact filed** (in feat commit message AND in this convergence map's "Verification artifacts" closeout-docs section) for non-empty RUI approve answers wire shape; OR Task 18 reports BLOCKED with proposed scope expansion
- [ ] Defensive `RuntimeError` for unexpected kind in helper
- [ ] Audit `action=decision` per L7a (incidental fix); regression tests in L9 #8/#9
- [ ] `abort_reservation` called ONLY on journal-intent failure per L7b; NOT on audit failure
- [ ] No `try/except` around `commit_signal` per L14
- [ ] No re-imports of names already in scope (W6); `ReservationToken` added ONLY if used as type annotation (L5)
- [ ] No edits to: `start()` (W1), `_finalize_turn` body including the `DelegationEscalation` needs-escalation return at `:2400` which lives inside it (W2), 6 sentinel raises (W3), `_dispatch_parked_capture_outcome` (W15), `_execute_live_turn` def (W16), `:837` `DelegationEscalation` Parked-arm site (W17), `runtime.py` (W10)
- [ ] **W3 invariant:** `grep -nF "_WorkerTerminalBranchSignal(reason=" delegation_controller.py | wc -l` returns `6`
- [ ] **W17 invariant:** `grep -c "DelegationEscalation(" delegation_controller.py` returns `2` — `:837` (Task 17 Parked-arm; W17-protected) + `:2400` (`_finalize_turn` needs-escalation return; W2-protected) — both UNCHANGED by Task 18

### Tests (mandatory)

- [ ] New file `tests/test_delegate_decide_async_integration.py` with 10 acceptance tests per L9 (test #4 is the deterministic competing-reservation form, NOT a timer-race form)
- [ ] No `pass`-bodied tests committed (W12)
- [ ] 3 Bucket B decorators removed (`:1781, :2410` in controller; `:1063` in integration); verification: those 3 tests pass post-removal
- [ ] 3 obsolete CDFE tests DELETED (`:2166, :2457, :2509`) per L11
- [ ] 6 Bucket C decorators retained per L12; reason text updated automatically via constant rename
- [ ] Constant `_TASK_18_DECIDE_SIGNAL_REASON` RENAMED to `_TASK_19_FINALIZER_GUARD_REASON` in BOTH `test_delegation_controller.py` and `test_delegate_start_integration.py` per L10; new text per L10 specification
- [ ] No Task 18 renames applied (renames pre-authorized for Task 19 via G18.1 record); verification: legacy names at `:1825, :1871` UNCHANGED in Task 18
- [ ] No Task 18 body rewrites at `:1524` (deferred to Task 19 via G18.1 record); decorator stays + reason updated
- [ ] L13 assertion-shape review applied to 3 Task-18-closing tests + 10 acceptance tests (rows from L13's authority table)
- [ ] F16.1 decorators at `tests/test_handler_branches_integration.py:161, :179` UNTOUCHED (W8); verification: `grep -c "@pytest.mark.skip" test_handler_branches_integration.py` returns `2`
- [ ] **Suite expectation:** 999 + 3 (Bucket B unskipped, now passing) + 10 (new acceptance) = **1012 passing**; **8 skipped** (6 Bucket C + 2 F16.1); 1020 total tests (1013 pre-Task-18 − 3 deleted CDFE + 10 new acceptance); 0 failed. Note: deletions reduce TOTAL count and SKIPPED count by 3 each, but do NOT reduce passing count (the deleted tests were currently in the 14-skipped set, not in the 999-passing set).
- [ ] **W5 hang verification:** full suite ~30-40s wall-clock; `pytest` exit code 0; order-independence smoke yields identical results in both directions
- [ ] Lint: no new findings relative to `c5829049` baseline (3 pre-existing F401 errors per Task 17 closeout-docs noted as pre-existing)
- [ ] Pyright: no new diagnostics on touched files (pre-existing `runtime.py:270` per W10 + pre-existing `_FakeControlPlane` per W11 noted)

### Closeout-docs (mandatory)

- [ ] `carry-forward.md` G17.1 disposition recorded: 0 items un-skipped (all 9 → DELETE/G18.1/Task-19)
- [ ] `carry-forward.md` Mode A row CLOSED (all 6 of 6 retire: 3 Task 17 + 3 Task 18)
- [ ] `carry-forward.md` F16.2 entry stays Open with explicit annotation: "[26 tests originally; 17 closed by Task 17 Bucket A; 3 deleted by Task 18 (obsolete CDFE); 6 reclassified to G18.1 by Task 18; closes when Task 19 lands G18.1]"
- [ ] `carry-forward.md` NEW G18.1 entry with full 6-test list + pre-authorized renames + body-rewrite for `:1524` + L12 assertion-review notes
- [ ] `carry-forward.md` proposed TT.1 formal addition (`_FakeControlPlane` Pyright issues per W11)
- [ ] `carry-forward.md` RT.1 unchanged (still owned by end-of-Phase-G typing polish)
- [ ] **Verification artifacts** section appended to this convergence map (per L4 Path A): cite/fixture/test-name for non-empty RUI approve wire-shape verification
- [ ] Closeout-docs entry per Phase E/F/G precedent: landed-code summary; Bucket B disposition (3 close + 3 delete + 6 reclassify); full L1-L14 + W1-W18 lock conformance; branch-matrix-with-test-coverage note; hang-verification result; G18.1 record explicit; L4 Path A artifact disposition

## Pre-dispatch checklist

- [ ] Convergence map (this file) shared with implementer in dispatch packet
- [ ] Spec §Transactional registry protocol (`design.md:250-345`) inline
- [ ] Spec §Response payload mapping (`design.md:1663-1702`) inline — esp. table `:1667-1672` and Path A implementation-gate `:1680`
- [ ] Spec §decide() semantics (`design.md:1646-1662`) inline
- [ ] Spec §`_finalize_turn` Captured-Request Terminal Guard (`design.md:1738-1808`) inline as INFORMATIONAL (Task 19 territory; documents WHY 6 tests reclassify to G18.1)
- [ ] Plan Step 18.1-18.5 inline (pseudocode reference; convergence map's L4 OVERRIDES plan's payload-helper logic)
- [ ] Live anchors table inline
- [ ] Per-test triage table inline (3 close + 3 delete + 6 reclassify + 10 new + 2 F16.1 untouched)
- [ ] L1 prominent: 12-test disposition split + Mode A row full closure + G17.1 absorbs 9 (3 delete + 6 G18.1) + F16.2 lineage open via G18.1
- [ ] L4 prominent: spec payload table is binding; plan body's `reject` and unconditional `dict(answers or {})` are stale; **Path A only**; verification artifact mandatory
- [ ] L7 prominent: audit `action=decision` is incidental fix; rollback boundary is journal-intent only
- [ ] L11 prominent: 3 CDFE deletions pre-authorized; ANY OTHER deletion → BLOCKED
- [ ] L12 prominent: 6 reclassifications pre-authorized to G18.1 with reason text via constant rename; ANY OTHER reclassification → BLOCKED
- [ ] L13 prominent: assertion-shape authority table rows applicable to Task 18 (mechanism-only subset); finalizer rows belong to Task 19
- [ ] L14 prominent: NO `try/except` around `commit_signal`
- [ ] G18.1 record prominent: pre-authorizations for Task 19's convergence map to inherit
- [ ] W4 prominent: NO fictional fixtures
- [ ] W5 prominent: hang-verification protocol
- [ ] W14 prominent: NO `signal_internal_abort` calls in `decide()`
- [ ] W18 prominent: ANY rename, deletion beyond L11, or reclassification beyond L12 → BLOCKED (per `feedback_bucket_reclassification_requires_blocked.md` graduated process precedent)
- [ ] Acceptance criteria inline
- [ ] Reporting contract: implementer reports `DONE` with commit SHA + suite output + W3/W17 grep results + Bucket-disposition audit (3 unskipped + 3 deleted + 6 retained-with-new-constant) + L4 Path A verification artifact + L7a regression test result + per-lock conformance summary; flags `BLOCKED` with question (NOT `DONE_WITH_CONCERNS`); ANY rename / deletion-beyond-L11 / reclassification-beyond-L12 → BLOCKED
- [ ] Workflow: `superpowers:subagent-driven-development`, **fresh implementer + spec reviewer + code-quality reviewer** (sequential) — sonnet model
- [ ] Implementer agent named `task-18-implementer` per Task 16 D5 / Task 17 precedent

## Commit shape

| Step | Type | Subject |
|---|---|---|
| 1 | feat | `feat(delegate): rewrite decide() with reservation two-phase protocol (T-20260423-02 Task 18)` |
| 2 (anticipated) | fix | `fix(delegate): address Task 18 closeout review (T-20260423-02 Task 18 closeout)` |
| 3 (mandatory) | docs | `docs(delegate): record Phase G Task 18 closeout (T-20260423-02)` — Bucket-B disposition (3 close + 3 delete + 6 reclassify) + Mode A row closure + F16.2 lineage annotation + G18.1 introduction + L11 deletions + L4 Path A verification artifact + TT.1 promotion |

**Anticipated 1+1+1.** Production scope is smaller than Task 17 (~50 lines new flow + ~115 lines deleted = net −80 lines), but L4 Path A's verification + L11 deletions + L12 reclassifications + L7a's incidental audit fix + the constant rename create multiple precision-sensitive surfaces. Code-quality review surfacing 2-4 cleanups is plausible.

## Carry-forward expectations

| Item | Pre-Task-18 | Post-Task-18 | Closed-by |
|---|---|---|---|
| F16.2 (Phase G Task 17 unblock surface — 26-test parent) | Open (split per Task 17: 17 closed Bucket A; 9 → G17.1) | **Open via G18.1 lineage** (3 of 9 deleted + 6 of 9 → G18.1; F16.2 closes when G18.1 closes) | Task 19 (via G18.1) |
| **G17.1** (Phase G Task 18 unblock surface — 9 F16.2 Bucket B post-L13) | Open (9 tests) | **Closed as a carry-forward entry** (all 9 dispositioned: 3 deleted + 6 → G18.1); lineage continues via G18.1 | Task 18 (entry retires; lineage continues) |
| **Mode A** (Phase E Task 14 closeout — 6 tests; partial closure post-Task-17) | Open (3 of 6 closed in Task 17) | **CLOSED — full Mode A row retires** (remaining 3 closed in Task 18) | Task 18 |
| Mode B (Phase E Task 14 closeout — 2 tests) | Closed (Task 17) | Closed | n/a |
| F16.1 (Phase F Task 16 closeout — Phase H Task 19 unblock) | Open | Open (untouched per W8) | Phase H Task 19 |
| **NEW G18.1** (Phase H Task 19 unblock surface — 6 finalizer-dependent tests + pre-authorized renames + body rewrite for `:1524`) | n/a | **NEW Open** | Phase H Task 19 — same-commit un-skip + apply pre-authorized renames/body-rewrite per G18.1 carry-forward record |
| **NEW TT.1** (`_FakeControlPlane` Pyright issues at multiple lines) | n/a (proposed by Task 17) | **NEW Open** (formal promotion) | End-of-Phase-G or end-of-Packet-1 typing polish |
| RT.1 (`runtime.py:270` Pyright TurnStatus literal narrowing) | Open | Open (untouched per W10) | End-of-Phase-G or end-of-Packet-1 typing polish |
| A4, A5, B6.1, B6.2, B7.1, B7.2, B8.1, B8.2 | Open | Open | End-of-phase polish |
| C10.2, C10.3 | Open | Open | End-of-phase test parity polish |
| E13.2, E13.3 | Open | Open | Phase H Task 22 contracts.md |
| E14.1 | Open | Open | End-of-Packet-1 polish |

**Net change:** Mode A row retires entirely. G17.1 retires as a tracked entry (its 9 items dispositioned). F16.2 stays Open via G18.1 lineage. TWO new Open items: G18.1 (Phase H Task 19 work) + TT.1 (typing polish). End-of-Phase-G outlook: Phase G fully closes from Task 18's perspective (decide() rewrite complete; mechanism-level Bucket B closed); Phase H starts with F16.1 + RT.1 + TT.1 + G18.1 + F16.2 (still Open via G18.1) as the cross-Phase carry-forward set.

---

**Status:** Ready for dispatch. Workflow: `superpowers:subagent-driven-development` with sonnet implementer + spec reviewer + code-quality reviewer (sequential). Anticipated 3-commit chain (feat + fix + docs).

**Pre-dispatch warnings:**

1. **L4 Path A is mandatory.** Plan body's payload-helper skeleton is doubly stale (`reject` instead of `decline`; unconditional `dict(answers or {})` instead of empty-fallback for deny on RUI). Spec §1667-1672 table is binding. Path A verification artifact is a Packet 1 acceptance criterion per spec §1680 — Task 18 ships with the artifact OR reports BLOCKED.

2. **L7b is the highest-risk-of-confusion lock.** Two error-handling blocks must NOT be conflated: (a) `try / except BaseException: abort_reservation; raise` around journal-intent ONLY; (b) separate `try / except Exception: logger.warning` around audit POST-`commit_signal`. Wrapping audit in the same try as intent creates a "ghost intent" failure mode per spec §343.

3. **L11 + L12 + W18 enforce process precedent.** L11 pre-authorizes 3 CDFE deletions; L12 pre-authorizes 6 G18.1 reclassifications; ALL OTHER deletions / reclassifications / renames → BLOCKED. The 2 deny-test renames at `:1825, :1871` are NOT applied in Task 18 — they defer to Task 19 via the G18.1 carry-forward record.

4. **G18.1 is the load-bearing structural artifact for Phase G→H handoff.** Task 19's convergence map MUST inherit the G18.1 record verbatim. Task 18 closeout-docs MUST record the 6-test list + pre-authorized renames + `:1524` body-rewrite spec + L12 assertion-review notes.

## Restructure Record (2026-04-26 — first-draft review feedback)

The first draft of this convergence map (created 2026-04-26 same day) attempted to close all 12 Bucket B tests in Task 18, including 6 finalizer-dependent tests. User review identified four P1 dispatch blockers:

1. **L4/L9 internal contradiction (Path B):** First draft allowed implementer-discretion between Path A (verify) and Path B (raise `RuntimeError` for non-empty RUI approve while still claiming the full 6-row contract). User locked Path A only; if verification unavailable, BLOCKED.

2. **Task 19 finalizer behavior assumed under Task 18:** First draft's L12 row 10 asserted Task 19's Captured-Request Terminal Guard mapping as expected Task 18 behavior, while W2 simultaneously forbade `_finalize_turn` modification. The 6 finalizer-dependent tests cannot pass under Task 18 alone. User locked Option Y (narrow Task 18; reclassify 6 to G18.1).

3. **Test #4 expected wrong rejection:** First draft's `test_decide_on_unreserved_entry_rejects` expected `request_already_decided` for an unregistered request_id — but L3's `request_not_found` validation precedes reserve, catching that case earlier. User specified the deterministic competing-reservation form (test directly calls `controller._registry.reserve(rid, ...)` to force the entry out of awaiting; explicitly NOT a timer-race form per `resolution_registry.py:393` race concern).

4. **L11 rename pre-authorization too narrow:** First draft pre-authorized 2 deny-test renames; under the narrow-scope decision, the 3 CDFE tests also need pre-authorization (as deletions, not renames — they assert obsolete-by-architecture behavior). User locked drop-active-L11; move renames to G18.1 carry-forward; introduce new L11 for CDFE deletions; new L12 for 6-test reclassification.

This restructure record exists for future-task referencing (Task 19's convergence map will likely encounter similar scope-vs-spec questions and benefit from the four-P1-pattern as a template).

### Round-2 review addendum (2026-04-26 — second-draft review feedback)

Second-draft review identified two P1 test-determinism contract issues (scope was sound; mechanism details were wrong) plus one P2 count typo:

1. **L13 row 7 asserted unenforceable inverse ordering.** The original row claimed `decide()` returns BEFORE the worker dispatches/observes `turn/completed`. But `commit_signal` is a `threading.Event.set()` with no scheduler guarantee — the worker may complete its dispatch and observation before `decide()`'s post-commit audit returns. The L13 row was rewritten to assert only enforceable orderings: (a) journal-intent precedes `commit_signal`; (b) `decide()` returns without waiting on `_finalize_turn`. The unenforceable race is now explicitly forbidden in the row text. Affects acceptance tests 3, 4, 5, 6, 7 (all transient-state assertions audited).

2. **L9 tests #4 and #6 needed explicit drain semantics; tests #3 and #7 needed transient-state caveats.** `abort_reservation` only restores `awaiting` state — it does NOT set the wake event. After abort fires (whether from the test forcing competing reservation, OR from `decide()`'s journal-intent rollback per L7b), the worker remains parked in `registry.wait()`. Without explicit drain, tests would hang on teardown until daemon-thread process-exit cleanup. Tests #4 and #6 now specify approved cleanup patterns (re-call `controller.decide(approve, ...)` with kind-appropriate decision arguments to drive the production reserve→commit_signal→worker-wake path). Tests #3 and #7 now explicitly forbid transient registry-state assertions in favor of contract-level assertions (rejection reason via reservation CAS for #3 — refined further in round-3 with mandated worker-blocking + corrected mechanism in round-4; follow-up reject as proxy for slot-still-claimed was attempted for #7 — superseded by round-3 which dropped the proxy entirely in favor of durable side-effect assertions).

3. **L13 opening + acceptance criteria said "9 acceptance tests"** while L9 had 10 (the L4 payload-mapping test was added during 2nd-draft revision). Both occurrences corrected to 10. The implementer would otherwise have an escape hatch about which test to exclude from assertion-shape review.

This addendum exists for future-task referencing: Task 19's convergence map will need similar test-determinism rigor for any test that interacts with the registry's `wait`/`commit_signal`/`abort_reservation` triple. The "abort doesn't wake" trap and the "commit_signal is just an Event.set()" trap are both general — they'll resurface for any future test that exits the decide-path through abort or asserts ordering relative to commit_signal.

### Round-3 review addendum (2026-04-26 — third-draft review feedback)

Round-3 review surfaced one residual P1 race that round-2's "follow-up decide as proxy for slot-still-claimed" introduced, plus one P2 cleanup-flexibility prune at test #4:

1. **Follow-up `decide(rid)` rejection-reason assertion is scheduler-dependent (validation-order race).** Round-2 attempted to fix tests #3 (duplicate-decide) and #7 (audit non-gating) by replacing transient registry-state assertions with "second `decide(rid)` returns `request_already_decided`" as proof that the reservation slot stayed claimed. The flaw: `decide()`'s validation chain runs `invalid_decision` → `job_not_found` → **`job_not_awaiting_decision`** → `request_not_found` → … → THEN `reserve()`. The worker, post-wake from `commit_signal`, may set `job.status` to `running` before the second decide reaches validation, producing `job_not_awaiting_decision` instead. Worse: live worker success calls `registry.discard(parsed.request_id)` per `delegation_controller.py:1278` (pops the registry entry per `resolution_registry.py:283`), so a fast worker produces `request_not_found` from the registry-side check — the *opposite* of the intended assertion in the test's nominal flow. **Fix split by test purpose:** test #3's contract IS the rejection reason (must use deliberate worker-blocking via monkeypatch on `_execute_live_turn` or `session.respond` to hold the worker before any state mutation; verify diagnostically that `job.status` stays `awaiting_decision` until the gate releases — **mechanism and status name both superseded by round-4 after these patterns were shown to fail against the live worker path; see Round-4 addendum for the corrected `job_store.update_status_and_promotion` wrap and the `needs_escalation` status name**); test #7's contract is non-gating (drop follow-up decide entirely; assert durable non-racing side effects: success-return + audit warning + journal `intent` entry persisted + worker eventually dispatched `respond`).

2. **Test #4 cleanup option (b) — direct `commit_signal(competing_token)` — pruned.** Round-2 listed two cleanup patterns; option (b) routes the test-held fake `DecisionResolution` payload through the worker's `session.respond` dispatch path. Technically a registry wake, but it tests an artificial cleanup path rather than production decide semantics. Pruned to option (a) only: `abort_reservation(competing_token)` then `controller.decide(approve, ...)` normally (with kind-appropriate decision arguments per L3 + L4). More restrictive but tests the production drain path; implementer cannot construct a custom cleanup that bypasses normal decide semantics.

This addendum exists for future-task referencing: the **validation-order race** is a general trap whenever future tests want to assert post-decide state via a probe call. `decide()`'s validation chain runs before reserve, so the rejection reason can be any of three reasons (`job_not_awaiting_decision`, `request_not_found`, `request_already_decided`) depending on worker timing — making rejection-reason assertions inherently flaky without deliberate worker-blocking. Future tests probing post-`commit_signal` state must EITHER block the worker deterministically at the earliest post-wake point OR avoid asserting the probe's specific failure mode in favor of durable side effects (journal entries, audit logs, mocked-boundary captures) that don't depend on racing the worker.

### Round-4 review addendum (2026-04-26 — fourth-draft review feedback)

Round-4 review surfaced one P1 — test #3's approved worker-blocking patterns were both wrong against the live code path — and one P2 stale-clause in the round-2 addendum:

1. **Test #3's `_execute_live_turn` and `session.respond` blocking patterns were both incorrect.** Round-3 specified two approved patterns; both fail against the live worker path:
   - **Monkeypatching `_execute_live_turn` after `start()` has no effect.** The existing worker thread is already inside the method post-park, and Python attribute patches affect future *symbol lookups* on the bound object — they don't reach into a thread that's already executing the original function object.
   - **Monkeypatching `_execute_live_turn` before `start()` blocks the initial park.** The method IS the parked-state owner (the worker enters it once, parks inside `registry.wait()`, runs through to terminal state). Patching its entry prevents the test from ever obtaining a pending request to decide on.
   - **Blocking `session.respond` is too late.** The worker mutates `job.status` from `needs_escalation` to `running` at `delegation_controller.py:1166` BEFORE calling `respond` at `:1187`. Any second decide arriving after `:1166` rejects with `job_not_awaiting_decision`.

   **Corrected mechanism (round-4 mandate):** wrap `job_store.update_status_and_promotion` after the parked-request setup, gating ONLY the resume call where `status=="running"` (the post-commit mutation). All other update_status_and_promotion calls pass through unblocked. This holds the worker BEFORE the status race while letting initial park complete normally. Test asserts `request_already_decided` while the gate is held; releases gate; worker drains naturally for teardown.

2. **The live pre-decision job status is `needs_escalation`, not `awaiting_decision`.** Round-3's row referred to `job.status` as `awaiting_decision` — derived from the rejection-reason string `job_not_awaiting_decision`, which is misleadingly named (the reason string is about a legacy semantic; the actual `JobStatus` literal for the pre-decision state is `needs_escalation`). Status name corrected throughout the test #3 row so the implementer writes `assert job.status == "needs_escalation"` correctly. (`JobStatus` is a `typing.Literal`, NOT an enum — the assertion is a string comparison against the literal value, not an enum-member reference like `JobStatus.NEEDS_ESCALATION`, which would AttributeError at runtime.)

3. **Round-2 addendum's last sentence claimed test #7 uses follow-up-reject proxy.** Round-3 dropped that proxy, but round-2's text was frozen as historical record. Updated to reference the round-3 supersession explicitly so an implementer reading addenda top-to-bottom doesn't trust the stale clause.

This addendum exists for future-task referencing: the **"patch where the symbol is bound, not where it's called"** rule is a general Python-mock-patching trap that surfaces whenever tests interpose on a long-running worker thread. The corrected mechanism — wrap a `job_store`-level operation that the worker calls per-step rather than wrap the worker's top-level entry point — is the durable pattern. Future tests probing post-`commit_signal` worker state (Task 19, Task 20) should default to `job_store.update_status_and_promotion` wrapping (or other per-step boundaries the worker crosses) rather than top-level `_execute_live_turn` patching.

### Round-5 review addendum (2026-04-26 — packet-review feedback against the dispatch packet surfaced a structural defect in this convergence map)

Round-5 review (post-packet drafting) surfaced one P1 mechanical-impossibility: the live-anchors row claiming `:2400` is the "Legacy `DelegationEscalation` construction site (DELETE with approve block)" was wrong on both claims. Live grep against HEAD `c5829049` shows only TWO `DelegationEscalation(` construction sites: `:837` (Task 17's Parked-arm — W17-protected) and `:2400` (inside `_finalize_turn`'s body at `:2324-2430` — W2-protected, Task 19 territory). The decide() approve block being deleted (`:2606-2675`) contains NO `DelegationEscalation(` construction; the legacy approve path returned via `_execute_live_turn`'s indirect dispatch, not by directly constructing one inside `decide()`.

The convergence map's prior wording asked the implementer to delete the `:2400` site and verify a post-Task-18 `grep -c "DelegationEscalation("` returns `1`. This created an internally contradictory dispatch contract: deleting `:2400` requires modifying `_finalize_turn` body (W2 violation), but preserving it leaves the grep at `2` (W17 invariant violation per old wording). Either action would have failed acceptance.

**Corrections applied (all to existing rows; no new locks/watchpoints):**
1. Live anchors table row at `:2400` reclassified from "Legacy `DelegationEscalation` construction site (DELETE with approve block)" to "`_finalize_turn` `DelegationEscalation` needs-escalation return site (DO NOT MODIFY per W2 — Task 19 territory)."
2. W17 watchpoint description rewritten: Task 18 modifies neither `:837` nor `:2400`; both sites stay; grep returns `2` post-Task-18 (UNCHANGED from pre-Task-18).
3. Acceptance criteria → Code "W17 invariant" line: expected grep count changed from `1` to `2`; both protected sites enumerated.

Why this gap survived 4 prior review rounds: grep-style verification confirms a symbol exists at a line, but does not confirm which enclosing function owns it. Reviewers reading the live-anchors row "Legacy `DelegationEscalation` construction site (DELETE with approve block) | `:2400`" took the row's classification at face value rather than independently verifying that `:2400` falls inside `decide()`. The actual enclosing function order — `_finalize_turn` def at `:2324`, `_reject_decision` at `:2431`, `decide()` at `:2447` — places `:2400` squarely inside `_finalize_turn`. The next review pass discovered this by running the `rg` query and reading the surrounding context.

**Pattern for future convergence maps:** when a row in the live-anchors table claims a line should be DELETED and falls outside an explicit "deletion range," verify two things: (1) that the line is inside the deletion range (not just numerically close to it); (2) that no other lock or watchpoint protects the line. The convergence map's L2 said "post-validation block at `:2560-2675`" — `:2400` is OUTSIDE that range, which by itself was a structural inconsistency the row should have flagged. Future convergence maps should add an integrity check: every "DELETE" row's line number must fall inside an explicit deletion range named by some lock.

### Round-6 review addendum (2026-04-26 — implementer-discovery during Bucket B unskip verification; user adjudication D applied)

Round-6 review surfaced one P1 — the 3 Mode A defer Bucket B unskips (`test_decide_approve_can_reescalate_with_new_pending_request` at `test_delegation_controller.py:1781`, `test_decide_rejects_stale_request_id_after_reescalation` at `test_delegation_controller.py:2410`, `test_decide_reescalation_uses_pending_escalation_key` at `test_delegate_start_integration.py:1063`) failed under Task 18 alone via four compounded test-mechanics defects, none of which were finalizer-dependent:

1. **Iterator binding to original list object.** `_FakeSession.run_execution_turn` and `_ConfigurableStubSession.run_execution_turn` use `for req in self._server_requests:` which binds the iterator to the list object at iteration start. The 3 tests' pattern of REASSIGNING `_server_requests = [next_req]` after `start()` parks the worker leaves the iterator pointing at the ORIGINAL one-item list; reassignment to a new list object is invisible to the active iterator.

2. **Default `respond` is None / missing.** `_FakeSession` declares `respond: Any = None`; `_StubSession` does not declare `respond` at all. The new async-decide worker handler at `delegation_controller.py:1186` calls `entry.session.respond(rid, payload)` BEFORE returning None to continue the turn loop. With None or missing `respond`, this raises `TypeError`/`AttributeError` → dispatch-failed sentinel branch (`:1187-1241`) → `_WorkerTerminalBranchSignal(reason="dispatch_failed")` → terminates the worker before reaching the second iteration. The original Bucket B tests pre-dated the async-decide worker handler and never had to provide a `respond` stub.

3. **Worker handler's `pending_request_store.create()` re-park gating.** The parkable-capture branch at `delegation_controller.py:1029-1031` only creates a PSR record when `captured_request is None`. After the first park, `captured_request` is set to rid_42's parsed struct and stays as that for the rest of the turn. When the worker re-enters the handler for rid_99 (second iteration), the `if captured_request is None` gate skips PSR.create — but the parkable-capture branch below STILL fires `update_parked_request(rid_99)`, `_persist_job_transition("needs_escalation")`, and `registry.register(rid_99, ...)`. So the registry knows about rid_99 but the pending_request_store does not. `poll()`'s `_project_pending_escalation` at `:1746` reads `self._pending_request_store.get(parked_request_id)` and returns None when no record exists, so `pending_escalation=None` even though the worker is correctly parked on rid_99 in the registry. **This is a production code defect** (Task 16 oversight; the worker handler was written with single-park semantics and never updated for re-park) but lifting the gate is W16-protected ("`_execute_live_turn` def at `:894` ... FUNCTION DEFINITION stays untouched").

4. **Pre-Packet-1 unknown-kind escalation assumption.** The original tests used `_permissions_request(99)` (method `item/permissions/requestApproval`) which parses to `kind="unknown"` per `approval_router.py:56`. Under Packet 1's spec §1715-1718 unknown-kind contract, unknown-kind requests do NOT escalate — the worker handler's interrupt-path branch at `:1009-1026` calls `interrupt_turn` and sets `interrupted_by_unknown=True`, terminalizing the job as `unknown`. The original test assertion `poll.pending_escalation.request_id == "99"` is structurally incompatible with Packet 1; it asserts pre-Packet-1 unknown-kind escalation behavior.

**Why L12 was substantively right but operationally incomplete.** The classification "Mode A defer; mechanism-only — re-escalation continues turn, finalizer doesn't run on original capture" correctly identified these as same-turn re-escalation tests (not finalizer-dependent). The original captured warning `late capture-ready signal ignored. job_id='job-1' kind=TurnCompletedWithoutCapture` confirmed the failure was a worker-thread test-double simulation mismatch (worker exited turn without re-park), not a `_finalize_turn` Captured-Request Terminal Guard dependency. But L12 didn't catch the four compounded test-mechanics defects above, all of which together prevent the simulation from reaching the re-park state under the new flow.

**The correction (adjudication D — narrow test-mechanics patch).** Per user adjudication: do NOT reclassify to G18.1 (semantically wrong — these are not finalizer-dependent), do NOT modify `_FakeSession`/`_ConfigurableStubSession` class definitions globally (W18 scope-creep), and do NOT take the stale `resolution.payload.get("response_payload", {})` shape at `delegation_controller.py:1163-1164` into Task 18 (record separately if still relevant). Apply ONLY narrow per-test patches:

- **`session._server_requests = [next_req]` → `session._server_requests.append(next_req)`** (mutation visible to active iterator).
- **`session.respond = lambda request_id, payload: None`** (unblock the dispatch-success path).
- **Pre-seed PSR record for rid=99 via `parse_pending_server_request(...)` + `prs.create(...)`** (test-side workaround for the W16-protected production-code re-park PSR.create gating defect at `:1029-1031`; mirrors what production worker code WOULD write if the gate were lifted).
- **Bounded polling loop on `controller.poll(...)` up to 5s with 50ms intervals** (decide() returns after commit_signal; worker progresses asynchronously; observing the new pending_escalation requires waiting).
- **Replace `_permissions_request(99)` with `_request_user_input_request(99)`** (parkable kind; mirrors L13 row "request_user_input parks (returns DelegationEscalation) instead of synchronously completing" + spec §1717 unknown-kind contract).
- **Update assertion `prs.get("99").status == "resolved"` → `prs.get("42").status == "resolved"`** (rid=99 is the NEW pending escalation captured during resume; it should be `pending`, not `resolved`. The corrected assertion mirrors L13's authority-table row about the worker's `mark_resolved` sequencing in the dispatch-success branch at `:1259-1261`).
- **Update assertion `esc["kind"] == "unknown"` → `esc["kind"] == "request_user_input"`** (forced by Packet 1 spec §1717 unknown-kind contract).
- **Per-test teardown drain via `controller._registry.signal_internal_abort("99", reason="test_teardown_drain")` + `threading.enumerate()` join** (the rid=99 worker park leaves a daemon thread alive between tests; without explicit drain, sibling tests in `test_delegate_decide_async_integration.py` that enumerate threads named `delegation-worker-job-1` observe the leak and fail under `assert len(worker_threads) == 1`).
- **Test 7's worker-thread assertion relaxed from `len(worker_threads) == 1` to "at least one; join the most-recently-started thread by `ident`"** to tolerate sibling-test leaks observed in cross-file ordering A (`test_delegation_controller.py` first → many leaked daemon threads from sibling tests that don't drain → test 7 in the new file fails under strict-equality assertion). Surgical Edit to the new acceptance test 7 (`test_decide_audit_event_post_commit_non_gating`) recorded here.

**What stays in scope vs out:**
- The 3 tests REMAIN in Task 18 closing set (Mode A row fully retires as originally planned).
- `_FakeSession` and `_ConfigurableStubSession` class definitions are NOT modified (no global infrastructure change).
- The stale `resolution.payload.get("response_payload", {})` shape at `delegation_controller.py:1163-1164` is OUT OF SCOPE for Task 18 (record separately if still relevant for Phase H).
- The worker handler's re-park PSR.create gating at `delegation_controller.py:1029-1031` is OUT OF SCOPE for Task 18 per W16; the test-side pre-seed workaround documents the production defect for future Phase H disposition.

**G18.1 carry-forward record is unchanged** from the convergence map's pre-Task-18 state (still the same 6 finalizer-dependent tests; not augmented with the 3 Mode A tests).

**Future-prevention pattern:** When the convergence map classifies tests as "mechanism-only" closeable, audit whether the existing test-double simulation pattern is compatible with the new flow's threading/iteration semantics. The async-decide transition flipped the iterator binding from "fresh per call" (old `decide()` invoked a new `_execute_live_turn` → fresh `run_execution_turn` → fresh iterator over reassigned `_server_requests`) to "shared across worker lifecycle" (single `run_execution_turn` per worker thread → iterator bound at first call's list object → reassignment invisible). The four compounded defects (iterator binding, missing `respond` stub, re-park PSR.create gate, unknown-kind escalation assumption) are individually small but compound non-obviously; future convergence maps should flag any test that reassigns `session._server_requests` between `start()` and `decide()` as a candidate for this audit.

### Verification artifacts (L4 Path A — added by feat-implementer; ratified by closeout-docs)

- **L4 Path A `request_user_input` approve answers wire shape:** verified via pinned-version JSON Schema fixture `packages/plugins/codex-collaboration/tests/fixtures/codex-app-server/0.117.0/ToolRequestUserInputResponse.json`. The fixture pins the App Server `ToolRequestUserInputResponse` schema as `{"answers": {<qid>: {"answers": [<string>...]}}}` (top-level `answers` map keyed by qid; per-qid object with required `answers` array of strings). Implementation at `_build_response_payload` wraps each `(qid, values)` from the validated `answers: dict[str, tuple[str, ...]] | None` argument as `{qid: {"answers": list(values)}}` to match. Acceptance regression at `tests/test_delegate_decide_async_integration.py::test_build_response_payload_per_kind_decision[request_user_input-approve-answers2-expected_payload2]` pins the exact wire shape: input `{"q1": ("yes",)}` → output `{"answers": {"q1": {"answers": ["yes"]}}}`.

---

### Round-7 (post-feat code-quality review — Path 4 fix commit)

> **Supersession of Round-6 dispositions.** Round-6 (above) framed two items as **OUT OF SCOPE for Task 18** at lines 597-598:
>
> 1. The stale `resolution.payload.get("response_payload", {})` shape at `delegation_controller.py:1163-1164`.
> 2. The worker handler's re-park PSR.create gating at `delegation_controller.py:1029-1031` (W16-protected).
>
> **Round-7 SUPERSEDES both dispositions.** Code-quality review of the landed feat surfaced both as contract-correctness gaps that block Task 18 closeout (the producer-consumer wire-shape mismatch and the test-mechanics workarounds for the re-park gate are two faces of the same correctness debt). User adjudication ratified Path 4 — fix both inline within Task 18 via narrow W16 adjudication.
>
> **Round-6 is preserved verbatim above as the historical record of the open question at that point in review.** It is NOT the final disposition. The Round-7 fix lands the production correction; the test-side PSR.create pre-seed workarounds documented at Round-6 lines 586 and 598 are removed (no longer needed). Mode A row STILL fully retires (3/3 close in Task 18); the alternative — partial retirement implied by Round-6's "out of scope" framing — is NOT the final disposition.
>
> Read Round-6 for the audit trail of how the open question was framed and why a Phase-H deferral was the considered position; read Round-7 below for what actually shipped.

**Discovery.** Code-quality review of the landed feat surfaced two correctness gaps:

1. **Producer-consumer wire-shape mismatch at the worker resume path.** `decide()` constructs `DecisionResolution(payload=<bare App Server payload from _build_response_payload>, kind=request.kind)` per L4 (e.g., `payload={"decision": "accept"}`). The worker resume path at `delegation_controller.py:1160-1161` (post-feat lines) read the payload via wrapper keys that do NOT exist in the new shape:

   ```python
   decision_action = resolution.payload.get("resolution_action", "approve")  # always "approve"
   response_payload = resolution.payload.get("response_payload", {})           # always {}
   ```

   Result: the worker dispatched `session.respond(rid, {})` to the App Server, defeating L4's whole purpose. The `decision_action` defaulted to `"approve"` regardless of the operator's actual decision, so `record_response_dispatch.action`, `record_dispatch_failure.action`, and `OperationJournalEntry.decision` were all wrong on deny paths.

2. **Re-park PSR.create gating defect at `delegation_controller.py:1029-1031`.** Documented in Round-6 as "out of Task 18 scope per W16; record separately for Phase H disposition." Path 4 brought it in-scope.

**W16 narrow adjudication.** User adjudication authorized narrow fixes inside `_execute_live_turn` body for both gaps. W16's original protection was the DEF signature (callers like `spawn_worker(...)` invoke it as `_execute_live_turn(...)`) plus structural integrity of the parkable-capture and resume sub-branches. The Path 4 fixes preserve the def signature and the branch structure; they correct only the payload-shape reads (3 lines) and lift one defective `if captured_request is None` gate (3 lines). W16 stays in force for all other parts of the body.

**Test gap diagnosis.** Test #7 (`test_decide_audit_event_post_commit_non_gating`) at `test_delegate_decide_async_integration.py:512` asserted only that `session.respond` was called for rid `42`, not that the payload matched the L4 6-row table. spec-compliance review covered the producer side (helper output matches the table per test 10's parameterization) but did not pin the consumer side (worker dispatches the helper's output verbatim). The test gap let the wire-shape mismatch ship in the feat commit.

**Fix landed in this commit.**

| Layer | Change |
|---|---|
| `server/resolution_registry.py` | Add `action: Literal["approve", "deny"] \| None = None` to `DecisionResolution`. Default `None` covers `is_timeout=True` cases and tests that hold uncommitted resolutions for state-machine drives. Operator-decide path always sets `action`. |
| `server/delegation_controller.py:2549` (`decide()`) | Pass `action=decision` to the `DecisionResolution` constructor — explicit operator-action carry, not payload-shape inference. (Inference is unsafe: approve × RUI with empty `answers` and deny × RUI both yield `{"answers": {}}`.) |
| `server/delegation_controller.py:1160-1172` (worker resume) | Read `resolution.payload` directly as the App Server payload (no wrapper). Read `resolution.action` (assertion-checked non-None for the operator-decide branch) for `record_response_dispatch.action`, `record_dispatch_failure.action`, and the dispatched-phase journal `decision`. Add `Literal` to the `typing` imports. |
| `server/delegation_controller.py:1025-1037` (parkable capture) | Lift the `if captured_request is None` gate. `_pending_request_store.create(parsed)` runs unconditionally for every parkable server-request; `captured_request` always tracks the MOST RECENTLY captured request for `_finalize_turn`'s terminal-guard mapping. |
| `tests/test_delegate_decide_async_integration.py` | Tighten test #7 (`test_decide_audit_event_post_commit_non_gating`) to assert `dispatched_payload == {"decision": "accept"}` end-to-end. Add new parameterized regression `test_decide_worker_dispatches_l4_payload_end_to_end` covering 3 wire shapes: approve × command_approval (`{"decision": "accept"}`), deny × command_approval (`{"decision": "decline"}`), approve × request_user_input with answers (`{"answers": {"q1": {"answers": ["yes"]}}}`). |
| `tests/test_handler_branches_integration.py:447` | Update the dispatch-failure mock-registry resolution to the new shape (`payload={"decision": "accept"}`, `action="approve"` separate). |
| `tests/test_delegation_controller.py:1820-1836, 2460-2472` | Remove the test-side PSR.create pre-seed workaround for rid=99. Production worker now writes the record per Part C. |
| `tests/test_delegate_start_integration.py:1127-1138` | Same removal in the MCP-projection re-escalation test. |
| `tests/test_delegate_decide_async_integration.py:478-481` | CQ Minor #3 applied: substring-match the exact decide-side warning via `rec.getMessage()` (rather than loose `rec.message.lower()` on `"audit"`), preserving %-arg formatting and avoiding unrelated-log false positives. |

**Re-park defect disposition.** **Fixed inline in this commit.** The Round-6 addendum's Mode A row closure stays at 3/3 (full closure); the test-side workarounds are no longer needed. The new regression coverage for the production fix is the existing `test_decide_approve_can_reescalate_with_new_pending_request` / `test_decide_rejects_stale_request_id_after_reescalation` / `test_decide_reescalation_uses_pending_escalation_key` (now exercising the production re-park path without test-side pre-seeding), plus `test_decide_worker_dispatches_l4_payload_end_to_end` for the dispatch-shape contract.

**Process precedent (L15 candidate — to be promoted in closeout-docs if convergence-map maintainer approves).** When `decide()` and the worker resume path hand off via `DecisionResolution`, BOTH the producer side AND the consumer side of the contract must be regression-pinned. spec-compliance review reading the producer (helper output matches the table) is necessary but not sufficient; consumer-side end-to-end tests on the wire shape catch the form of bug that Round-7 surfaced. Future Task convergence maps should explicitly assert the producer-consumer contract end-to-end as a Phase-G-class lock invariant.

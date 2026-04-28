# Task 18 Dispatch Packet — T-20260423-02 (Phase G second task)

**Drafted:** 2026-04-26 (post-Task-17 dispatch construction; convergence map at `task-18-convergence-map.md` is binding authority; convergence map went through 4 review rounds + 1 wording pass before reaching dispatch-ready, then a Round-5 packet-review correction landed the W17/`:2400` mechanical-impossibility fix — both artifacts updated together).

**Workflow:** `superpowers:subagent-driven-development` — single fresh implementer (sonnet, `general-purpose`) + spec reviewer + code-quality reviewer (sequential, NOT parallel). Per Task 16/17 precedent, agent named explicitly for SendMessage continuity (closeout-fix + closeout-docs continue the same agent).

**Agent dispatch (controller invokes this after user approves the packet):**

```python
Agent({
  name: "task-18-implementer",
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Phase G Task 18 decide() rewrite",
  prompt: <<everything in §"Implementer Prompt" below>>
})
```

---

## Implementer Prompt

You are the Task 18 implementer for T-20260423-02 Packet 1 (Deferred-Approval Response). You are dispatched into the existing `feature/delegate-deferred-approval-response` branch at base commit `c5829049` (`docs(delegate): record Phase G Task 17 closeout (T-20260423-02)`). Phase G Task 17 is complete (`start()` rewrite landed). Task 18 is the SECOND and FINAL task of Phase G and rewrites the public `decide()` API for the reservation-based two-phase protocol. Phase H Task 19 (`_finalize_turn` Captured-Request Terminal Guard) is queued behind you and is OUT OF YOUR SCOPE.

### Mission

Rewrite `DelegationController.decide` post-validation block at `delegation_controller.py:2560-2675` for the `reserve()` + journal-intent + `commit_signal()` two-phase protocol per spec §Transactional registry protocol. Replace the legacy synchronous flow (in-decide `_execute_live_turn(...)` callsite at `:2644` for approve; deny-path local-finalize block at `:2606-2637`) with: validate (unchanged) → `_build_response_payload(...)` (new helper, L4) → `DecisionResolution(payload=..., kind=request.kind)` → `reserve(rid, resolution)` → narrow-try journal-intent (with `abort_reservation` rollback per L7b) → `commit_signal(token)` (bare, no try/except per L14) → audit (post-commit, non-gating, `action=decision` per L7a) → return `DelegationDecisionResult(decision_accepted=True, ...)`. Both live `DelegationEscalation(` construction sites (`:837` Task-17 Parked-arm + `:2400` `_finalize_turn` needs-escalation return) are PRESERVED — `:837` per W17, `:2400` per W2 (it lives inside `_finalize_turn` body `:2324-2430`). Land 10 new acceptance tests in `test_delegate_decide_async_integration.py`. Carry-forward consequences: 12 Bucket B tests dispositioned (3 unskipped + 3 DELETE per L11 + 6 RECLASSIFY to G18.1 per L12); Mode A row fully retires; G17.1 closes as a tracked entry; F16.2 stays Open via G18.1 lineage; constant renames in 2 test files; new G18.1 Open + new TT.1 Open.

### Authority sources (READ IN THIS ORDER)

**Pre-read guard:** All sources below MUST be readable from the current working tree (`/Users/jp/Projects/active/claude-code-tool-dev`). If `Read` fails on any of them with file-not-found or permission error, **stop and report BLOCKED** with the failing path — do NOT improvise from training knowledge or partial context. The convergence map is the binding dispatch authority; without it, you have no scope.

1. **Convergence map (BINDING):** `docs/plans/2026-04-24-packet-1-deferred-approval-response/task-18-convergence-map.md` (566 lines after 5 review rounds + wording pass; Round-5 added the W17/`:2400` mechanical-impossibility correction). This is the dispatch authority. It contains:
   - **Live anchors table** (~30 rows; verified at HEAD `c5829049`). Plan-cited line numbers throughout `phase-g-public-api.md` Task 18 body are STALE (esp. plan's "decide() at `:1551`" — live anchor is `:2447`). Use this table for any line-number lookup.
   - **Locks L1-L14** (binding positive scope; mandatory things)
   - **Watchpoints W1-W18** (binding negative scope; forbidden things)
   - **Per-test triage table** (12 Bucket B retentions split as 3 close + 3 DELETE + 6 RECLASSIFY to G18.1; 10 new acceptance tests; 2 F16.1 untouched)
   - **G18.1 carry-forward record** (pre-authorizations for Task 19's convergence map to inherit verbatim — 6 decorator removals + constant deletion + 2 renames + 1 body rewrite + L12 assertion review)
   - **Branch matrix** (10 rows covering 6 happy-path × decision/kind combinations + duplicate/competing + invalid args + journal-intent rollback + audit non-gating)
   - **Out-of-scope table** with plan/spec citations
   - **Acceptance criteria** (split: Code + Tests + Closeout-docs)
   - **Pre-dispatch checklist** (ignore — that's the controller's; you focus on Acceptance criteria)
   - **Round-1 Restructure Record + Round-2/3/4 review addenda** (chronological history; preserved for context. When earlier text is superseded, the original carries an in-place "superseded by round-N" cross-ref. Trust the latest authoritative statement; addenda explain why.)

2. **Spec — Transactional registry protocol:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:250-345`. The 5-step `decide()` sequence (validate → reserve → journal-intent → commit_signal → audit) plus the failure analysis table (`:320-326`) that grounds L7's rollback boundary. Read carefully — L14's "log and crash, do NOT abort" rule for `commit_signal` failure derives from `:325`.

3. **Spec — Response payload mapping:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1663-1702`. The 6-row binding contract (table at `:1667-1672`) for `_build_response_payload`. Two implementer-trap fingerprints both fixed in L4: deny rationale at `:1682-1697` (`decline` not `reject`; `cancel` reserved for timeout/abort) and deny-on-RUI empty-fallback at `:1689-1697` (`{"answers": {}}` not `dict(answers or {})`). Path A implementation-gate at `:1680` mandates verification of the non-empty RUI approve answers wire shape — **this is a Task 18 acceptance criterion, not a Phase H deferral.**

4. **Spec — `decide()` semantics:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1646-1662`. Audit relocation at `:1654`; `approval_resolution.dispatched` deletion at `:1659`; success-shape `DelegationDecisionResult` at `:1620-1644`.

5. **Spec — `_finalize_turn` Captured-Request Terminal Guard (INFORMATIONAL — Task 19 territory):** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1738-1808`. Read once for context — this documents WHY 6 of 12 Bucket B tests reclassify to G18.1 instead of closing in Task 18. You do NOT implement the guard; W2 forbids `_finalize_turn` modification.

6. **Plan body — Task 18:** `docs/plans/2026-04-24-packet-1-deferred-approval-response/phase-g-public-api.md:290-538`. Steps 18.1-18.5 with full pseudocode. **Treat the pseudocode as faithful template, but apply the corrections in §"Plan-pseudocode known issues" below — the plan body has TWO authoritative payload-helper defects (L4) and STALE line numbers throughout.**

7. **Carry-forward state:** `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md` (242 lines). Pre-Task-18 entries: G17.1 (9 F16.2 Bucket B), RT.1 (`runtime.py:270` Pyright), proposed TT.1 (`_FakeControlPlane` Pyright). Closeout-docs commit dispositions all three.

### CRITICAL: L9 test #3 wrapper protocol (HIGHEST IMPLEMENTATION-SENSITIVITY)

This is the most implementation-sensitive test mechanic in the entire packet. The convergence map went through 4 review rounds before the worker-blocking pattern was correct; getting this wrong produces tests that pass coincidentally OR hang on teardown OR assert the wrong rejection reason.

**Test #3 contract:** `test_decide_twice_second_returns_request_already_decided` — the second `decide(rid, ...)` against a same-rid double-decide must return `DecisionRejectedResponse(reason="request_already_decided", ...)`. The rejection reason IS the contract under test.

**Why a naive implementation fails:** `decide()`'s validation chain runs `invalid_decision` → `job_not_found` → **`job_not_awaiting_decision`** → `request_not_found` → `request_job_mismatch` → `answers_required` → `answers_not_allowed` → `runtime_unavailable` → THEN `reserve()`. Without worker-blocking, the worker post-wake mutates `job.status` from `needs_escalation` to `running` at `delegation_controller.py:1166` BEFORE calling `session.respond` at `:1187`, AND eventually calls `registry.discard(rid)` at `:1278`. Three rejection reasons are reachable depending on worker timing — `job_not_awaiting_decision` (status mutated; pre-reserve), `request_not_found` (registry discarded; pre-reserve), `request_already_decided` (the intended one; from reserve CAS). The race is unenforceable without a deliberate gate.

**Mandated step-by-step protocol:**

1. Complete initial `start()` and parked-request setup normally. Do NOT block the initial park — that prevents the test from ever obtaining a pending request to decide on.

2. Install a wrapper on `job_store.update_status_and_promotion` AFTER the parked-request setup is complete. The wrapper inspects each call's arguments and gates ONLY the resume call where `status == "running"` (the post-`commit_signal` mutation). All other `update_status_and_promotion` calls pass through unblocked.

3. Call first `decide(rid, decision, ...)` with kind-appropriate decision arguments per L3 + L4 — for `command_approval` / `file_change` parked requests, no `answers` payload (L3's `answers_not_allowed` rejects `answers` on non-RUI kinds); for `request_user_input`, a valid answers dict. Worker wakes via `commit_signal` and blocks at the wrapper BEFORE writing `running`, so `job.status` stays `"needs_escalation"`.

4. Diagnostic: `assert job.status == "needs_escalation"` (string comparison — `JobStatus` is `typing.Literal`, NOT enum; `JobStatus.NEEDS_ESCALATION` AttributeErrors at runtime).

5. Call second `decide(rid, ...)` — validation passes (status is still `"needs_escalation"`) → reaches `reserve()` → `reserve()` returns None (entry is in `consuming` from first decide's commit_signal) → assert response is `DecisionRejectedResponse(reason="request_already_decided", ...)`.

6. Release the wrapper gate. Worker drains naturally for teardown (mutates to `running`, calls `respond`, eventually `discard`s the rid).

**Rejected blocking patterns (implementer MUST NOT use any of these — round-3 + round-4 rejected each in turn):**

| Pattern | Why it fails |
|---|---|
| Monkeypatch `_execute_live_turn` AFTER `start()` | The existing worker thread is already inside the method post-park. Python attribute patches affect future symbol lookups on the bound object — they don't reach into a thread that's already executing the original function object. |
| Monkeypatch `_execute_live_turn` BEFORE `start()` | The method IS the parked-state owner (worker enters once, parks inside `registry.wait()`, runs through to terminal state). Patching its entry prevents the test from ever obtaining a pending request to decide on. |
| Block `session.respond` | Too late. The worker mutates `job.status` to `running` at `:1166` BEFORE calling `respond` at `:1187`. The second decide arriving after `:1166` rejects with `job_not_awaiting_decision`. |
| Direct `commit_signal(competing_token)` cleanup | Routes test-held fake `DecisionResolution` payload through worker `respond`. Tests an artificial cleanup path rather than production decide semantics. (See L9 test #4 for the analogous deterministic-competing-reservation cleanup pattern; abort + decide-normally is the only approved path.) |

**Durable-side-effects pattern (test #7 contract — read alongside test #3):** test #7 (`test_decide_audit_event_post_commit_non_gating`) does NOT use follow-up `decide(rid)` as proof of slot-still-claimed. Use durable non-racing assertions: (a) `decide()` returned success; (b) audit warning was logged; (c) journal `intent` entry persists in capture (was written before audit per L7b ordering); (d) worker eventually dispatches `session.respond` (verifiable via mocked respond capture; proves `commit_signal` fired and woke the worker despite audit failure — the actual non-gating evidence).

### CRITICAL: L4 Path A mandatory + binding 6-row payload mapping

Plan body's `_build_response_payload` skeleton at `phase-g-public-api.md:498-505` has TWO authoritative defects. **Spec §Response payload mapping table at `design.md:1667-1672` is binding. Plan body is informative-not-binding where it conflicts.**

**Defect 1 (`reject` vs `decline`):** plan codes `"reject"` for deny on `command_approval`/`file_change`; spec §1670 mandates `"decline"` per `:1677` semantic + `:1682-1687` rationale (`cancel` is reserved for timeout/abort).

**Defect 2 (deny-on-RUI fallback):** plan codes `dict(answers or {})` unconditionally for `request_user_input`; spec §1670 mandates `{"answers": {}}` empty-fallback for deny on RUI per `:1689-1697` rationale.

**Authoritative 6-row binding contract (full exact match required):**

| Decision × Kind | Payload | Spec authority |
|---|---|---|
| `approve` × `command_approval` | `{"decision": "accept"}` | `design.md:1669` + `:1676` |
| `approve` × `file_change` | `{"decision": "accept"}` | `design.md:1669` + `:1676` |
| `approve` × `request_user_input` | `{"answers": <validated answers dict>}` | `design.md:1669` + **subject to Path A verification per `design.md:1680`** |
| `deny` × `command_approval` | `{"decision": "decline"}` | `design.md:1670` + `:1677` + `:1682-1687` |
| `deny` × `file_change` | `{"decision": "decline"}` | `design.md:1670` + `:1677` + `:1682-1687` |
| `deny` × `request_user_input` | `{"answers": {}}` | `design.md:1670` + `:1689-1697` |

**Helper signature + skeleton (corrected):**

```python
def _build_response_payload(
    self,
    *,
    decision: Literal["approve", "deny"],
    answers: Mapping[str, Any] | None,
    request: PendingEscalationView,
) -> dict[str, Any]:
    kind = request.kind
    if decision == "approve":
        if kind == "command_approval" or kind == "file_change":
            return {"decision": "accept"}
        if kind == "request_user_input":
            # Validation above enforces non-empty answers for approve+RUI per L3
            # answers_required branch at :2522-2535. Path A verification artifact
            # required for the wire shape (spec §1680).
            return {"answers": dict(answers or {})}
    if decision == "deny":
        if kind == "command_approval" or kind == "file_change":
            return {"decision": "decline"}
        if kind == "request_user_input":
            return {"answers": {}}  # empty-fallback per spec §1689-1697
    raise RuntimeError(
        f"_build_response_payload: unexpected decision/kind combination: "
        f"decision={decision!r}, kind={kind!r}"
    )
```

**Path A mandate (no Path B fallback):** non-empty `request_user_input` approve answers wire shape is plugin-assumed per spec §1680. Spec mandates verification via one of: (1) live App Server fixture/probe; (2) reading App Server source; (3) equivalent ground-truth check (e.g., pinned-version integration test). **Task 18 MUST file a verification artifact.** If verification cannot be obtained in-scope (App Server source unavailable, no live fixture, no pinned version available), report **BLOCKED** with proposed scope expansion (e.g., "Task 18a: codex-app-server source verification + ground-truth artifact"). Do NOT ship Task 18 with the helper raising `RuntimeError` for non-empty RUI approve while still claiming the full 6-row contract — that is the Path B disposition explicitly rejected in round-1 review.

**Verification artifact format:** the artifact (cite, fixture path, or test name + pinned-version) MUST be recorded in BOTH: (1) the feat commit message body; (2) a new "Verification artifacts" section appended to `task-18-convergence-map.md` by the closeout-docs commit.

### CRITICAL: L7 rollback boundary (highest confusion risk)

Two error-handling blocks must NOT be conflated. Wrapping audit in the same try as intent creates a "ghost intent" failure mode per spec §343 (the worker has already woken via `commit_signal`; aborting after audit-failure tries to revoke an intent the worker is already acting on).

**Sub-rule 7a (audit `action` field):** the new audit MUST set `action=decision` (the plugin-decision verb passed in by caller — `"approve"` or `"deny"`). Current code's hardcoded `action="approve"` at `:2581` (which fires for both approve AND deny because it sits BEFORE the deny/approve split at `:2606`) is a pre-existing bug fixed incidentally by the audit-relocation. **Document in feat commit message:** "audit `action=decision` fixes pre-existing hardcoded `action='approve'` bug; incidental to required relocation per spec §1654."

**Sub-rule 7b (rollback boundary):** `abort_reservation(token)` is called ONLY on journal-intent failure. NEVER on audit failure. Skeleton:

```python
# After validation (unchanged) + payload build + DecisionResolution + reserve:
token = self._registry.reserve(request_id, resolution)
if token is None:
    return DecisionRejectedResponse(reason="request_already_decided", ...)

try:
    self._journal.write_phase("intent", ...)  # repositioned from :2562-2575
except BaseException:
    self._registry.abort_reservation(token)
    raise

self._registry.commit_signal(token)  # BARE — no try/except per L14

try:
    self._journal.append_audit_event(action=decision, ...)  # repositioned from :2576-2588; action=decision per L7a
except Exception:
    logger.warning(
        "delegation.decide: audit emission failed post-commit; decision is durable",
        extra={"job_id": ..., "request_id": ..., "decision": decision},
        exc_info=True,
    )
    # NO abort_reservation call here. Intent is durable; worker has woken.

return DelegationDecisionResult(decision_accepted=True, job_id=..., request_id=...)
```

**Failure analysis (binding per spec §`design.md:320-326`):**

| Failure between… | Outcome |
|---|---|
| `reserve()` returns None | Reject with `request_already_decided`; no rollback (no token to abort) |
| Journal intent raises | `abort_reservation(token)` → restore `awaiting`; re-raise the original exception |
| `commit_signal` raises | Plugin-critical bug per L14; log and crash; NO abort (impossible-by-construction; `commit_signal` is `Event.set()` + state mutation) |
| Audit raises | Log warning; return success; NO abort (intent durable; abort would create ghost-intent per spec §343) |

### CRITICAL: L10 constant rename (mechanical surgery; 2 files)

Both test files contain a constant named `_TASK_18_DECIDE_SIGNAL_REASON` whose reason text says Task 18 fixes the decide-signal mechanism:

- `packages/plugins/codex-collaboration/tests/test_delegation_controller.py:43-50`
- `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py:31-38`

You MUST rename to `_TASK_19_FINALIZER_GUARD_REASON` in both files AND rewrite the reason text to:

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

The 6 G18.1 retention decorators all use `reason=_TASK_18_DECIDE_SIGNAL_REASON` pre-rename and reach `reason=_TASK_19_FINALIZER_GUARD_REASON` post-rename via the **shared constant rename** alone (no per-decorator edits required for these 6). The 3 Bucket B unskips at `:1781, :2410, :1063` and the 3 DELETEs at `:2166, :2457, :2509` (per L11) are SEPARATE mechanical operations — see Tests acceptance summary.

### CRITICAL: L11 + L12 + W18 process precedent (BLOCKED protocol for non-pre-authorized changes)

Per `feedback_bucket_reclassification_requires_blocked.md` (graduated process precedent recorded after Task 17 L13). **ANY test rename, deletion beyond L11, reclassification beyond L12, or bucket adjustment requires BLOCKED + adjudication.** The convergence map pre-authorizes EXACTLY:

- **L11 — 3 obsolete CDFE test DELETIONS** at `test_delegation_controller.py:2166, :2457, :2509`. The legacy synchronous `decide()` model raised `CommittedDecisionFinalizationError` when in-decide finalization failed. Under Task 18's reserve+commit_signal+audit model, `decide()` has zero synchronous-finalization failure paths. The 3 tests assert a code path that no longer exists. Replacement coverage: L9 test #6 covers journal-intent rollback (closest analog under the new model); L9 test #7 covers audit-failure non-gating.

- **L12 — 6 finalizer-dependent test RECLASSIFICATIONS** to G18.1 (decorator stays; reason text updates automatically via L10's constant rename). The 6 tests at `test_delegation_controller.py:1524, :1736, :1825, :1871` and `test_delegate_start_integration.py:856, :933` assert post-resume terminal state derived through `_finalize_turn`'s Captured-Request Terminal Guard (spec §1738-1808; Task 19's spec authority). They cannot pass under Task 18 alone — `_finalize_turn` retains pre-Packet-1 kind-based escalation logic with Task 17 L11 carve-out only. NO body rewrites or renames are applied in Task 18; those are recorded as G18.1 carry-forward for Task 19.

- **W18 — ANY OTHER deletion, reclassification, or rename → BLOCKED.** Examples that would trigger BLOCKED (none of these are pre-authorized):
  - A 4th CDFE-style test you discover that asserts `CommittedDecisionFinalizationError` from `decide()` synchronously — flag for adjudication; do NOT delete unilaterally.
  - The 2 deny-test renames at `:1825, :1871` (`test_decide_deny_marks_job_failed_and_closes_runtime` → `test_decide_deny_dispatches_decline_through_worker_resume`; `test_decide_deny_emits_terminal_outcome` → `test_decide_deny_terminal_outcome_is_emitted_from_worker_finalization`) — DEFER to Task 19 via G18.1 record. Do NOT rename in Task 18.
  - The body rewrite at `:1524` (`test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up`) — DEFER to Task 19. Do NOT rewrite in Task 18.
  - A Bucket B test you classify as Task-18-closeable that turns out to have finalizer-dependent assertions — flag for adjudication.
  - A Bucket C test you classify as G18.1-deferred that turns out to be mechanism-only — flag for adjudication.

If you encounter ANY case that doesn't match L11 (3 specific CDFE tests) or L12 (6 specific finalizer-dependent tests) or the 3 explicit Bucket B unskips at `:1781, :2410, :1063`, **stop and report BLOCKED + question** with proposed disposition + spec citation. Do NOT improvise.

### CRITICAL: L14 commit_signal bare (no try/except)

Per spec `design.md:325`: "Journal `intent` succeeds, `commit_signal` raises → Impossible by construction: `commit_signal` is a local `threading.Event.set()` + state mutation. If it raises, the plugin has a deeper bug — log and crash loudly rather than abort." Implementer MUST NOT add `try/except` around `self._registry.commit_signal(token)`. The line stands bare. (See L7 skeleton above for the surrounding two try blocks; the `commit_signal` call sits BETWEEN them, naked.)

### CRITICAL: W4 NO fictional fixtures

Plan Step 18.1's failing-test stubs reference fixtures that DO NOT exist in `tests/conftest.py`:

- `delegation_controller_fixture` — does NOT exist
- `app_server_runtime_stub` — does NOT exist
- `journal_spy` — does NOT exist
- `audit_event_spy` — does NOT exist

The integration-test fixture surface in `tests/conftest.py` is intentionally minimal (only `vendored_schema_dir`, `client_request_schema`, `make_test_handle` are real). Per Task 14 W4 / Task 15 L8 / Task 16 W4 / Task 17 W4 precedent, use:

- `_build_controller(tmp_path)` — module-local helper, importable from `tests.test_delegation_controller`. Read `tests/test_delegation_controller.py` to see the helper's call signature and what it returns.
- Built-in pytest fixtures: `monkeypatch`, `tmp_path`, `caplog`.
- `unittest.mock.MagicMock` / `unittest.mock.patch.object` for narrow stubs (e.g., wrapping `journal.write_phase` to raise, capturing `session.respond` payloads, gating `job_store.update_status_and_promotion` per L9 test #3).

You MUST replace EVERY `pass` body in plan stubs with real assertion shapes (W12). Do NOT commit `pass`-bodied tests as Task 18 acceptance evidence.

### CRITICAL: W14 NO signal_internal_abort calls in decide()

Per spec §`Internal abort coordination` at `design.md:347-440` and §1700: `decide()` no longer projects a pending view in Packet 1's normal path; the abort trigger surfaces only on the `poll()` path (Phase H Task 20 territory). `decide()`'s ONLY registry interactions are `reserve` / `commit_signal` / `abort_reservation`. Adding `signal_internal_abort` is a scope violation.

### Plan-pseudocode known issues

Six known stale or ambiguous spots in `phase-g-public-api.md` Task 18 body:

1. **Stale `decide()` line number:** plan cites `:1551`; live anchor is `:2447`. Use the convergence map's live-anchors table.

2. **Plan body's `_build_response_payload` skeleton has TWO authoritative defects** (per L4 above): `"reject"` should be `"decline"`; unconditional `dict(answers or {})` should be `{"answers": {}}` empty-fallback for deny on RUI. Spec §1667-1672 binding.

3. **Plan body's "logic preserved from the previous decide implementation's payload-building section" wording is stale** — the previous decide does NOT build payloads (deny is local-finalize, no respond call). Rewrite per the L4 helper skeleton above.

4. **Imports gap:** plan doesn't anchor any imports change. Per L5: NO new imports from `.resolution_registry` are required at the call level (`abort_reservation` and `commit_signal` are METHODS on the registry instance — `self._registry.abort_reservation(...)`, `self._registry.commit_signal(...)`; they are NOT free functions). `DecisionResolution` already imported by Task 17. `ReservationToken` add ONLY if used as a type annotation on local variables (`token: ReservationToken | None = ...`). Otherwise no import addition.

5. **Fictional fixtures in plan Step 18.1 stubs:** see "CRITICAL: W4" above.

6. **Plan-pseudocode test stub bodies use `pass`:** replace EVERY `pass` body with real assertions (W12).

### Code acceptance summary (full list in convergence map "Acceptance criteria → Code")

- [ ] `decide()` post-validation block at `delegation_controller.py:2560-2675` REPLACED with reserve→intent→commit_signal→audit flow per L2.
- [ ] Validation block ABOVE `:2560` (lines `:2447-2545`) UNCHANGED except for 3 specific deletions per L3:
  - [ ] `_decided_request_ids` check at `:2505-2514` DELETED
  - [ ] `decision == "deny" and answers` early-rejection at `:2515-2521` DELETED (kind-specific handling moves into `_build_response_payload`; non-RUI+answers branch at `:2536-2545` is UNCHANGED)
  - [ ] `approval_resolution.dispatched` write at `:2589-2604` DELETED per L8
- [ ] New `_build_response_payload(self, *, decision, answers, request) -> dict[str, Any]` helper added per L4; payload mapping matches the 6-row table EXACTLY (`accept` for approve on command/file; **`decline`** for deny on command/file; `{"answers": <validated dict>}` for approve on RUI; **`{"answers": {}}`** for deny on RUI). Defensive `RuntimeError` for unexpected decision/kind combination.
- [ ] **L4 Path A verification artifact filed** in feat commit message AND in convergence map's "Verification artifacts" closeout-docs section (cite/fixture/test-name + pinned-version) — OR Task 18 reports BLOCKED with proposed scope expansion.
- [ ] `_decided_request_ids` retired across 4 callsites per L6: `:395` (set init), `:2505-2514` (already covered by L3 deletion), `:2627` (deny-path `add`), `:2665` (approve-path `add`). **Verification post-feat:** `grep -n "_decided_request_ids" packages/plugins/codex-collaboration/server/delegation_controller.py` returns 0.
- [ ] Audit `action=decision` per L7a (incidental fix; document in commit message).
- [ ] `abort_reservation` called ONLY on journal-intent failure per L7b; NOT on audit failure; NOT around `commit_signal`.
- [ ] No `try/except` around `commit_signal` per L14.
- [ ] No re-imports of names already in scope (W6); `ReservationToken` added ONLY if used as type annotation (L5).
- [ ] No edits to: `start()` body (W1), `_finalize_turn` body (W2 — including the `DelegationEscalation` needs-escalation return at `:2400` which lives inside `_finalize_turn`'s body `:2324-2430`), the 6 sentinel raises (W3), `_dispatch_parked_capture_outcome` at `:767-893` (W15), `_execute_live_turn` def at `:894` (W16), `:837` `DelegationEscalation` Parked-arm site (W17), `runtime.py` (W10).
- [ ] In-decide `_execute_live_turn` callsite at `:2644` DELETED (worker now performs the dispatch).
- [ ] Deny-path local-finalize block at `:2606-2637` DELETED.
- [ ] **W3 invariant:** `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `6` (count must NOT change from Task 17).
- [ ] **W17 invariant:** `grep -c "DelegationEscalation(" packages/plugins/codex-collaboration/server/delegation_controller.py` returns `2` — `:837` (Task 17 Parked-arm; W17-protected) + `:2400` (`_finalize_turn` needs-escalation return; W2-protected). Both UNCHANGED by Task 18. The legacy approve block being deleted (`:2606-2675`) contains NO direct `DelegationEscalation(` construction.

### Tests acceptance summary

- [ ] New file `packages/plugins/codex-collaboration/tests/test_delegate_decide_async_integration.py` with **10 acceptance tests** per L9 (test #4 is the deterministic competing-reservation form; test #3 follows the L9 wrapper protocol exactly per the CRITICAL section above).
- [ ] No `pass`-bodied tests committed (W12 — replace plan stubs with real assertions; module-local helpers per W4).
- [ ] **3 Bucket B decorators removed** (Mode A defer mechanism-only):
  - `test_delegation_controller.py:1781` — `test_decide_approve_can_reescalate_with_new_pending_request`
  - `test_delegation_controller.py:2410` — `test_decide_rejects_stale_request_id_after_reescalation`
  - `test_delegate_start_integration.py:1063` — `test_decide_reescalation_uses_pending_escalation_key`

  After removal these 3 tests must pass under the new flow (post-feat).
- [ ] **3 obsolete CDFE tests DELETED** per L11 (entire test bodies removed; CDFE class itself NOT deleted — out of scope):
  - `test_delegation_controller.py:2166` — `test_decide_approve_turn_failure_raises_committed_decision_finalization_error`
  - `test_delegation_controller.py:2457` — `test_decide_approve_post_turn_journal_failure_raises_committed_decision_finalization_error`
  - `test_delegation_controller.py:2509` — `test_decide_deny_post_commit_failure_raises_committed_decision_finalization_error`
- [ ] **6 G18.1 decorators retained** per L12; reason text updates automatically via L10's constant rename. Decorators STAY at:
  - `test_delegation_controller.py:1524, :1736, :1825, :1871`
  - `test_delegate_start_integration.py:856, :933`
- [ ] **No Task 18 renames applied.** Renames at `:1825, :1871` defer to Task 19 via G18.1 carry-forward. Verify legacy names UNCHANGED in Task 18.
- [ ] **No Task 18 body rewrite at `:1524`.** Defers to Task 19 via G18.1 record. Decorator stays + reason updated via constant rename.
- [ ] **Constant `_TASK_18_DECIDE_SIGNAL_REASON` RENAMED to `_TASK_19_FINALIZER_GUARD_REASON`** in BOTH `test_delegation_controller.py:43-50` and `test_delegate_start_integration.py:31-38` per L10. Constant text rewritten per the CRITICAL: L10 section above.

  **Audit A (old constant fully gone):**
  ```bash
  grep -rn "_TASK_18_DECIDE_SIGNAL_REASON" packages/plugins/codex-collaboration/tests/
  ```
  Expected: **0 matches** (constant fully renamed in both files; no straggler references).

  **Audit B (new constant decorators):**
  ```bash
  grep -rn "@pytest.mark.skip(reason=_TASK_19_FINALIZER_GUARD_REASON)" packages/plugins/codex-collaboration/tests/
  ```
  Expected: **6 matches** total (4 in `test_delegation_controller.py` + 2 in `test_delegate_start_integration.py`).

  **Audit C (new constant total references):**
  ```bash
  grep -rn "_TASK_19_FINALIZER_GUARD_REASON" packages/plugins/codex-collaboration/tests/
  ```
  Expected: **8 matches** total (6 decorators + 2 constant defs, one per file).
- [ ] L13 assertion-shape review applied to the 3 Task-18-closing tests + 10 acceptance tests per the convergence map's L13 authority table (rows applicable to Task 18; finalizer rows belong to Task 19).
- [ ] F16.1 decorators at `tests/test_handler_branches_integration.py:161, :179` UNTOUCHED (W8). Verification: `grep -c "@pytest.mark.skip" packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py` returns `2`.
- [ ] **Suite expectation:** `999 + 3 (Bucket B unskipped) + 10 (new acceptance) = 1012 passing`; `8 skipped` (6 G18.1 + 2 F16.1); 1020 total tests (1013 pre-Task-18 − 3 deleted CDFE + 10 new acceptance); 0 failed. Note: the 3 deleted CDFE tests were currently in the 14-skipped set (Bucket B retentions), not in the 999-passing set — deletions reduce TOTAL count and SKIPPED count by 3 each but do NOT reduce passing count.
- [ ] **W5 hang verification:**
  1. **Full suite:** `uv run --package codex-collaboration pytest -v` — must complete in normal wall-clock time (~30-40s; Task 17 baseline). Exit code 0; no SIGTERM/timeout messages.
  2. **Order-independence smoke** (3 files now; both orderings yield exit code 0 with identical pass/skip counts):
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
- [ ] Lint: `uv run --package codex-collaboration ruff check packages/plugins/codex-collaboration/server/ packages/plugins/codex-collaboration/tests/` — no new findings relative to baseline `c5829049` (3 pre-existing F401 errors per Task 17 closeout-docs noted as pre-existing).
- [ ] Pyright: no new diagnostics on touched files. Pre-existing `runtime.py:270` TurnStatus literal narrowing (RT.1) is OUT OF SCOPE per W10. Pre-existing `_FakeControlPlane` issues at multiple lines (proposed TT.1) are OUT OF SCOPE per W11.

### Closeout-docs acceptance summary (the third commit)

- [ ] `carry-forward.md` G17.1 disposition recorded: **0 items un-skipped** (all 9 dispositioned: 3 deleted per L11; 6 reclassified to G18.1 per L12). G17.1 entry CLOSES as a tracked carry-forward (lineage continues via DELETE notes + G18.1).
- [ ] `carry-forward.md` Mode A row CLOSED — all 6 of 6 retire (3 closed by Task 17 + 3 closed by Task 18 at `:1781, :2410, :1063`).
- [ ] `carry-forward.md` F16.2 entry stays Open with explicit annotation:
  > [26 tests originally; 17 closed by Task 17 Bucket A; 3 deleted by Task 18 (obsolete CDFE per L11); 6 reclassified to G18.1 by Task 18 (per L12); closes when Task 19 lands G18.1]
- [ ] `carry-forward.md` NEW G18.1 entry per the convergence map's "G18.1 carry-forward record" section (verbatim — Task 19's convergence map will inherit this verbatim):
  - 6-test list (`:1524, :1736, :1825, :1871, :856, :933`)
  - Pre-authorized renames (`:1825, :1871`)
  - Body-rewrite spec for `:1524` (5-step protocol per the convergence map G18.1 record)
  - L12 assertion-review notes for the remaining 3 G18.1 tests
  - Constant `_TASK_19_FINALIZER_GUARD_REASON` deletion pre-authorization
- [ ] `carry-forward.md` proposed TT.1 formal addition (`_FakeControlPlane` Pyright issues at `test_delegation_controller.py:257, 2547, 2621, 2686, 2867, 2888, 3064, 3194, 3418`).
- [ ] `carry-forward.md` RT.1 unchanged (still owned by end-of-Phase-G or end-of-Packet-1 typing polish).
- [ ] **Verification artifacts** section appended to `task-18-convergence-map.md` per L4 Path A: cite/fixture/test-name for non-empty RUI approve wire-shape verification.
- [ ] Closeout-docs entry per Phase E/F/G precedent: landed-code summary; Bucket B disposition (3 close + 3 delete + 6 reclassify); full L1-L14 + W1-W18 lock conformance; branch-matrix-with-test-coverage note; hang-verification result; G18.1 record explicit; L4 Path A artifact disposition; L7a incidental audit fix noted.

### Commit shape (anticipated 1+1+1)

| Step | Type | Subject |
|------|------|---------|
| 1 | feat | `feat(delegate): rewrite decide() with reservation two-phase protocol (T-20260423-02 Task 18)` |
| 2 (anticipated) | fix | `fix(delegate): address Task 18 closeout review (T-20260423-02 Task 18 closeout)` |
| 3 (mandatory) | docs | `docs(delegate): record Phase G Task 18 closeout (T-20260423-02)` — Bucket-B disposition (3 close + 3 delete + 6 reclassify) + Mode A row closure + F16.2 lineage annotation + G18.1 introduction + L11 deletions + L4 Path A verification artifact + TT.1 promotion |

Stage specific files only (never `git add -A` / `git add .`). Co-author trailer: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`. Do NOT amend; do NOT skip pre-commit hooks.

### Reporting contract

When the feat commit lands, report **DONE** with:

```
DONE
- Commit SHA: <sha of feat commit>
- Suite: <output of `uv run --package codex-collaboration pytest 2>&1 | tail -5`>
- W3 grep (sentinel raise sites): <output of `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l`>  (expect 6)
- W17 grep (DelegationEscalation construction sites): <output of `grep -c "DelegationEscalation(" packages/plugins/codex-collaboration/server/delegation_controller.py`>  (expect 2 — `:837` W17-protected + `:2400` W2-protected; both UNCHANGED by Task 18)
- L6 grep (_decided_request_ids retired): <output of `grep -n "_decided_request_ids" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l`>  (expect 0)
- Old constant audit: <output of `grep -rn "_TASK_18_DECIDE_SIGNAL_REASON" packages/plugins/codex-collaboration/tests/ | wc -l`>  (expect 0)
- New constant decorator audit: <output of `grep -rn "@pytest.mark.skip(reason=_TASK_19_FINALIZER_GUARD_REASON)" packages/plugins/codex-collaboration/tests/ | wc -l`>  (expect 6)
- New constant total references audit: <output of `grep -rn "_TASK_19_FINALIZER_GUARD_REASON" packages/plugins/codex-collaboration/tests/ | wc -l`>  (expect 8 = 6 decorators + 2 constant defs)
- L9 test #3 mechanism: <one-sentence confirmation that wrapper-on-update_status_and_promotion is the gating mechanism, NOT _execute_live_turn or session.respond>
- L4 Path A verification artifact: <cite / fixture path / test name + pinned version — the non-empty RUI approve answers wire shape evidence>
- L7a regression: <`test_decide_audit_action_matches_decision_for_approve` and `_for_deny` both passing>
- W5 hang verification: full-suite wall-clock <Xs>, order-independence smoke <both pass identical counts? yes/no>
- Lock conformance summary: L1=✓, L2=✓, L3=✓, L4=✓, L5=✓, L6=✓, L7=✓, L8=✓, L9=✓, L10=✓, L11=✓, L12=✓, L13=✓, L14=✓
- Watchpoint conformance summary: W1=✓, W2=✓, W3=✓, W4=✓, W5=✓, W6=✓, W7=N/A, W8=✓, W9=✓, W10=✓, W11=✓, W12=✓, W13=✓, W14=✓, W15=✓, W16=✓, W17=✓, W18=✓
- Notes: <any judgment calls made within lock-bounds>
```

If any lock turns out unreachable (e.g., live code shape disagrees with convergence map's anchor table in a way that blocks the lock), report **BLOCKED** with a specific question:

```
BLOCKED
- Lock that cannot be honored: L<N> (or W<N>)
- Live observation: <what you found at the file:line>
- Question for controller: <specific yes/no or pick-one question>
```

If a test outside L11 / L12 / the 3 explicit Bucket B unskips appears to need rename / deletion / reclassification, report **BLOCKED** per W18 with proposed disposition + spec citation.

If L4 Path A verification cannot be obtained in-scope, report **BLOCKED** with proposed scope expansion (e.g., "Task 18a: codex-app-server source verification + ground-truth artifact").

**DO NOT report DONE_WITH_CONCERNS + unilateral decision** (Task 14/15/16/17 process note: BLOCKED + question is preferred — controller adjudicates scope; implementer faithfully executes).

### Boundaries — what NOT to do

- **NO `start()` body edits** (W1 — Task 17 territory; closed).
- **NO `_finalize_turn` body edits** (W2 — Task 19 territory; preserve Task 17 L11 carve-out at `:2367`).
- **NO edits to the 6 sentinel raise sites or their reasons** (W3 — Task 16/17 invariant).
- **NO touches to `_dispatch_parked_capture_outcome` at `:767-893`** (W15 — Task 17's helper).
- **NO touches to `_execute_live_turn` def at `:894`** (W16 — still called by `spawn_worker(...)` on the worker thread; only the in-decide CALLSITE at `:2644` is deleted).
- **NO touches to either `DelegationEscalation` construction site** — `:837` (Task 17's Parked-arm; W17-protected) AND `:2400` (`_finalize_turn`'s needs-escalation return; inside `_finalize_turn` body `:2324-2430` — W2-protected, Task 19 territory). Both stay; post-Task-18 grep returns `2`.
- **NO `runtime.py` touches** (W10 — pre-existing Pyright RT.1).
- **NO `_FakeControlPlane` Pyright "fixes"** (W11 — proposed TT.1).
- **NO use of fictional plan-pseudocode fixtures** (W4).
- **NO un-skipping of F16.1 decorators at `test_handler_branches_integration.py:161, :179`** (W8 — Phase H Task 19 owns those).
- **NO `try/except` around `commit_signal`** (L14).
- **NO `signal_internal_abort` calls in `decide()`** (W14).
- **NO context-manager `with registry.reservation(...)` pattern** (W13 — spec mentions it but live registry doesn't implement it).
- **NO modifications to `__init__` registry init or Task 16/17 sentinel semantics** (W9).
- **NO `contracts.md` edits** (Phase H Task 22).
- **NO test renames in Task 18** (the 2 deny-test renames at `:1825, :1871` defer to Task 19 via G18.1).
- **NO body rewrites at `:1524` in Task 18** (defers to Task 19 via G18.1).
- **NO blanket migrations or scope expansion.** If you notice an unrelated improvement, mention it briefly in the report; do NOT silently fix.

### Mid-task questions

If you encounter a structural gap or a lock that turns out unreachable, **stop and report BLOCKED + question** — do NOT improvise. The controller will adjudicate within the convergence map's authority order:

1. Spec §Transactional registry protocol (`design.md:250-345`)
2. Spec §Response payload mapping (`design.md:1663-1702`)
3. Spec §decide() semantics (`design.md:1646-1662`)
4. Spec §Captured-Request Terminal Guard (`design.md:1738-1808`) — informational; Task 19 territory
5. Spec §Internal abort coordination (`design.md:347-440`)
6. Spec §Unknown-kind contract (`design.md:1703-1736`)
7. Phase G Task 18 plan body (`phase-g-public-api.md:290-538`) — code skeleton informative-not-binding where it conflicts with spec (esp. L4 payload defects)
8. Carry-forward state (G17.1, RT.1, proposed TT.1)
9. Live code at HEAD `c5829049`

When sources conflict, the higher-numbered authority defers to the lower (spec wins over plan; plan wins over carry-forward; live code is bedrock when it matches spec, but spec wins when live code is the legacy synchronous flow you're replacing).

### Begin

Read the seven authority sources in order, then begin Step 18.1 (write the new failing-test file `test_delegate_decide_async_integration.py` with 10 acceptance tests per the convergence map's L9 — paying special attention to the L9 test #3 wrapper protocol per the CRITICAL section above). Proceed through Steps 18.2-18.5 per the plan body, applying the L4/L7/L10/L11/L12/L14/W4/W14/W18 corrections above. Commit the feat. Run the W5 hang-verification protocol. Report DONE or BLOCKED per the contract above.

---

## Post-implementer review chain (controller-driven, not implementer-driven)

After the implementer reports DONE on the feat commit, the controller dispatches sequentially (per `feedback_subagent_driven_development_meaning.md`):

1. **Spec compliance reviewer** (`general-purpose`, sonnet): "Verify Task 18 commit `<sha>` honors L1-L14 + W1-W18 against `task-18-convergence-map.md` + spec §250-345 + §1646-1702 + plan §290-538. Pay special attention to L4 (6-row payload table — `decline` not `reject`; `{"answers": {}}` deny-on-RUI fallback); L7 (rollback boundary — abort on intent-failure only, NOT on audit-failure); L9 test #3 (wrapper-on-`update_status_and_promotion`, NOT `_execute_live_turn` or `session.respond`); L11 (3 specific CDFE deletions only); L12 (6 specific reclassifications only); W18 (any rename / non-pre-authorized deletion / non-pre-authorized reclassification → BLOCKED). Report findings as Critical/Important/Minor."

2. **Code-quality reviewer** (`pr-review-toolkit:code-reviewer` if available, else `general-purpose` sonnet): "Review Task 18 commit `<sha>` for code quality. Focus on the `_build_response_payload` helper (kind-exhaustive branching with defensive RuntimeError; type annotations); the L7 try/except boundary (narrow types: `BaseException` for journal-intent rollback, `Exception` for audit non-gating); the new test harness pattern (especially the L9 test #3 wrapper-on-`update_status_and_promotion` mechanism); the L7a `action=decision` regression; the L10 constant rename (text fidelity)."

3. **Closeout-fix dispatch (if needed):** controller continues the `task-18-implementer` agent via `SendMessage({to: "task-18-implementer", message: <consolidated review findings + adjudications>})` — do NOT spawn a new implementer for the closeout-fix.

4. **Closeout-docs commit (mandatory):** controller continues the implementer to write the `carry-forward.md` updates (G17.1 closure + Mode A row closure + F16.2 lineage annotation + NEW G18.1 entry verbatim from convergence map + TT.1 formal promotion + RT.1 unchanged) + Phase G Task 18 closeout entry per the closeout-docs acceptance summary above + Verification artifacts section appended to convergence map.

Sequential, not parallel. User adjudicates between rounds.

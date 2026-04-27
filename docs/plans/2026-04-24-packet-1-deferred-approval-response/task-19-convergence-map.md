# Task 19 Convergence Map — `_finalize_turn` Captured-Request Terminal Guard

**Revision marker:** Round 6 (2026-04-27 — supersedes Round 5 on L9 anomalous-pending test vacuity, `:1525` `_emit_terminal_outcome_if_needed` disqualification, and authority-table artifact-class split). Phase G CLOSED at HEAD `844e6f97`. Task 19 opens Phase H. Rounds 1-4 closed 5+3+3+3 defects; Round 5 closed 2H+3L; Round 6 closes 2H+1M from user's second independent adversarial review (verdict: "minor revision"). Core L1-L4 mechanism stable since Round 4; test-shape guidance converging since Round 5. See Restructure Record.

## Scope

Task 19 rewrites the captured-request branch of `_finalize_turn` (`delegation_controller.py:2340-2445`) to enforce the **one-snapshot terminal guard** per spec §`_finalize_turn` Captured-Request Terminal Guard (`design.md:1738-1827`). Same-commit deliverables: G18.1 (6 finalizer-dependent tests) unskipped + F16.1 (2 finalizer-routed integration tests) unskipped + `_TASK_19_FINALIZER_GUARD_REASON` constants deleted.

**Task 19 is NOT:**

- Task 20 (`poll()` UnknownKindInEscalationProjection catch + internal-abort).
- Task 21 (`discard()` admits `canceled`).
- Task 22 (contracts).

The G18.1 test bodies use bounded `controller.poll(job_id)` as a public observation surface for terminal job status post-`_finalize_turn`. That use of `poll()` does **not** require Task 20's projection-catch behavior — it observes terminal `status` after the guard maps the snapshot. If a Task 19 unskip surfaces a poll path that cannot observe terminal state, treat it as BLOCKED and adjudicate (do **not** unilaterally pull Task 20 scope in).

## Authority Order

When sources conflict, lower-numbered authority wins:

1. **Spec** §`_finalize_turn` Captured-Request Terminal Guard (`docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1738-1827`).
2. **Spec** §Unknown-kind contract (`design.md:1705-1736`, specifically lines 1725-1727 for Task 17 L11 carve-out preservation).
3. **carry-forward.md** — authoritative for **bucket closeout state and intent** (which tests are Bucket A/B, which closures Task 19 owns, deferred-item disposition).
4. **Live code** at HEAD `844e6f97` — authoritative for **names, line anchors, current bodies, callsite shape, and API signatures**. **Round-6 correction:** carry-forward.md line→test mappings, test names, and assertion expectations are informative-only when they conflict with live grep results. This resolves the prior contradiction where carry-forward outranked live code globally but live names overrode stale carry-forward locally (see Live Anchors note at `:48`).
5. **`phase-h-finalizer-consumers-contracts.md`** — *informative only*. Line anchors at `:14, :121, :395, :455, :508` are STALE (cite `:1439-1533`, `:901-945`, `:1404-1406`; live values are `:2340-2445`, `discard`/`poll` shifted by Task 18). Task decomposition (Task 19/20/21/22 split) is authoritative; line refs are not. **Do not copy line anchors from this file**; use the Live Anchors table below.

## Live Anchors

Verified at HEAD `844e6f97` (2026-04-26):

| Anchor | Path | Rationale |
|---|---|---|
| `_finalize_turn` def | `delegation_controller.py:2340` | Function rewrite target |
| Captured-request branch entry | `delegation_controller.py:2359` | `if captured_request is not None:` |
| D6 diagnostic call | `delegation_controller.py:2362-2367` | Preserved (post-turn signal verification) |
| **D4 unconditional write (REPLACE)** | `delegation_controller.py:2369-2371` | `update_status(rid, "resolved")` — must become snapshot-conditional per L2 |
| **L11 unknown-kind carve-out (PRESERVE)** | `delegation_controller.py:2383-2384` | Task 17 carve-out; W2 boundary |
| **Kind-based derivation (REPLACE)** | `delegation_controller.py:2385-2390` | `_CANCEL_CAPABLE_KINDS` + `turn_result.status` mapping |
| `_persist_job_transition` call | `delegation_controller.py:2392` | Preserved unchanged |
| Escalation audit emission | `delegation_controller.py:2395-2407` | Preserved unchanged (W6) |
| Re-read for return shape | `delegation_controller.py:2411-2413` | Permitted post-derivation per L1 (return-shape hydration only) |
| `DelegationEscalation(` site #2 | `delegation_controller.py:2416` | Preserved (W7 — count = 2) |
| Non-escalation return tail | `delegation_controller.py:2424-2429` | Preserved (W3 — sequencing intact) |
| No-capture branch | `delegation_controller.py:2431-2445` | Preserved unchanged (W4) |
| `DelegationEscalation(` site #1 | `delegation_controller.py:833` | Preserved (W7 — count = 2) |
| `pending_request_store.get` | `pending_request_store.py:40` | Returns `PendingServerRequest \| None` |

G18.1 decorators (6 sites; remove same-commit per L7). Names verified by direct grep against HEAD `844e6f97`. **Note:** carry-forward.md G18.1's line→test mapping was stale (Task 18 fix commit shifted lines; closeout-docs did not re-verify). Live names below override carry-forward.md when they disagree:

| Path | Line | Test (live name) | Carry-forward G18.1 role |
|---|---|---|---|
| `tests/test_delegation_controller.py` | 1525 | `test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up` | Bucket B reclassification per Task 17 L13. Body **must** be fully rewritten. **Round-5 correction:** the pre-Task-19 body sabotages `journal.append_audit_event` on the 2nd call, targeting the escalation audit at `:2395-2407`. Under post-Task-19 semantics, `approve → resolved + completed → completed` routes to the **non-escalation tail** (`:2424-2429`); the escalation audit at `:2394` never fires on this path. **Required rewrite shape:** drive `start()` → `decide(approve)` → worker completes → `_finalize_turn` runs on worker thread. Sabotage **`lineage_store.update_status(collaboration_id, "completed")`** at `:2425` (canonical injection — direct store call whose failure propagates through `_finalize_turn` to the cleanup wrapper at `:1352`, which calls `_mark_execution_unknown_and_cleanup`). **Round-6 correction:** `_emit_terminal_outcome_if_needed` at `:2428` is NOT a valid injection target for this test — it is best-effort (`try/except Exception` at `:1426` swallows all failures into a `logger.warning`; exceptions never escape `_finalize_turn`, so the cleanup wrapper never fires). Post-failure cleanup asserts: `job.status == "unknown"` + runtime released + session closed. Implementer authority for exact sabotage mechanism (one-shot raise, monkeypatch). If the intent is specifically to test escalation-audit failure, use a direct-call path (L11 style) that produces `final_status="needs_escalation"` via the pending fall-through; do not describe it as approve-completed. |
| `tests/test_delegation_controller.py` | 1737 | `test_decide_approve_resumes_runtime_and_returns_completed_result` | **Approve happy path.** 5-step protocol per carry-forward.md G18.1 entry (synchronous `DelegationDecisionResult` + bounded-poll `job_store.status == "completed"` + `pending_request_store.status == "resolved"`). |
| `tests/test_delegation_controller.py` | 1881 | `test_decide_deny_marks_job_failed_and_closes_runtime` | **Deny analogue (CORRECTED Round 3): bounded-poll `job_store.status == "completed"` + `pending_request_store.status == "resolved"`.** Test name is stale per pre-Packet-1 semantics; rename to `test_decide_deny_marks_job_completed_and_closes_runtime` per implementer authority. Authority: spec `:1677, :1684, :1686` — `deny → decline` does NOT abort the turn; App Server emits `item/completed` with `status: "declined"` (item-level) and `turn/completed` with `status: "completed"` (turn-level). L3 maps `resolved + completed → completed`. |
| `tests/test_delegation_controller.py` | 1927 | `test_decide_deny_emits_terminal_outcome` | Deny terminal-outcome record (asserts `delegation_terminal` written to `outcomes.jsonl`). **CORRECTED Round 3:** the terminal record's job status field is `completed`, not `failed`. The `delegation_terminal` outcome semantics distinguish operator-deny (item-level `status: "declined"`, job-level `status: "completed"`) from timeout-cancel via the audit trail's `resolution_action="deny"` field, NOT via the job status. |
| `tests/test_delegate_start_integration.py` | 857 | `test_delegate_decide_approve_end_to_end_through_mcp_dispatch` | End-to-end through MCP boundary; same shape as `:1737` via `mcp.delegate_decide`. **Bounded-poll** `job_store.get(job_id).status == "completed"` (5s/50ms per L9 budget). |
| `tests/test_delegate_start_integration.py` | 934 | `test_delegate_decide_deny_end_to_end_through_mcp_dispatch` | End-to-end through MCP boundary; same shape as `:1881` via `mcp.delegate_decide`. **CORRECTED Round 3:** asserts `job.status == "completed"`, not `"failed"`. **Bounded-poll** per L9 budget. |

**Rename policy (Round 4 corrected — Round-3 contradicted itself).** `:1881` rename pre-authorized: `test_decide_deny_marks_job_failed_and_closes_runtime` → `test_decide_deny_marks_job_completed_and_closes_runtime` (stale per pre-Packet-1 semantics; the live name encodes a defunct contract). Round 4 establishes this rename as **expected**, not optional. `:1927` (`test_decide_deny_emits_terminal_outcome`) name remains accurate; no rename. `:934` (`test_delegate_decide_deny_end_to_end_through_mcp_dispatch`) name remains accurate; no rename. No BLOCKED required for `:1881` rename; just update closeout-docs.

`_TASK_19_FINALIZER_GUARD_REASON` constant declarations (delete same-commit per L7):

- `tests/test_delegation_controller.py:45`
- `tests/test_delegate_start_integration.py:33`

F16.1 decorators (2 sites; remove same-commit per L8):

| Path | Line | Test | Maps to spec row |
|---|---|---|---|
| `tests/test_handler_branches_integration.py` | 161 | `test_happy_path_decide_approve_success` | `resolved + completed → completed` (`spec:1794`) |
| `tests/test_handler_branches_integration.py` | 179 | `test_timeout_cancel_dispatch_succeeded_for_file_change` | `canceled + any → canceled` (`spec:1795`) |

## Locks (L1-L11)

### L1 — One Authoritative Derivation-Status Snapshot Read

The captured-request branch performs **exactly one** `pending_request_store.get(captured_request.request_id)` read whose `.status` participates in derivation. The result, named `request_snapshot`, is the sole authority for both D4 gating (L2) and terminal-status derivation (L3). Authority: spec `:1747-1756`.

```python
request_snapshot = self._pending_request_store.get(captured_request.request_id)
```

**Invariant precision:** "exactly one **derivation-status** snapshot read." Later `pending_request_store.get(...)` calls are permitted **only** for return-shape hydration (non-status fields: `resolved_at`, `dispatch_result`, `protocol_echo_*`). The existing post-audit re-read at `:2411-2413` for `DelegationEscalation` shape stays under that exclusion. **Forbidden:** any subsequent `.status` access from a fresh `get()` that influences derivation, D4 gating, or terminal mapping.

**Snapshot scoping:** the read happens **inside** `if captured_request is not None:` and **after** the D6 diagnostic block — D6 must run for parseable requests regardless of snapshot status, per existing semantics.

**Parse-failed path interaction (CORRECTED).** When `captured_request_parse_failed=True`, the request **does** exist in the store: `delegation_controller.py:947-961` creates a minimal `PendingServerRequest(kind="unknown", ...)` and calls `_pending_request_store.create(minimal)` before setting `captured_request_parse_failed=True`. The audit-trail contract requires this record. Per spec `:1801`, the snapshot status under this path is `"pending"`. Therefore:

- Snapshot read **is performed** (record exists).
- Snapshot status will be `"pending"` (worker did not write a terminal status for unknown-kind parse failures).
- Terminal-mapping table (L3) **does not fire** — `pending` falls through.
- D4 is **skipped** for parse-failed paths (preserves the existing `if not captured_request_parse_failed:` guard at `:2362` that gates D6 and the legacy D4).
- Fall-through reaches L4's L11 carve-out → `interrupted_by_unknown=True` → `final_status="unknown"`.

**Authority:** spec `:1801` (parse-failed reaches finalizer with snapshot=`pending`), `:1826` ("unknown-kind parse-failure path persists the audit request as `pending`, so the terminal guard does not fire (snapshot is `pending`) and the existing unknown-kind branch still applies via fall-through"), live code at `delegation_controller.py:947-961`.

### L2 — D4 Conditional Write + Three-Way Warning Discipline

The D4 write at `:2369-2371` becomes conditional on `request_snapshot.status` AND `captured_request_parse_failed`:

| `parse_failed` | `request_snapshot` | D4 action | Warning |
|---|---|---|---|
| `False` | `.status == "pending"` | **MAY** write `update_status(rid, "resolved")`. Per spec `:1785`, the write does not retroactively promote the snapshot — derivation still treats authoritative status as pre-D4 `"pending"`. | **`logger.warning`** — anomalous fall-through. Under Packet 1, every non-parse-failed capture path SHOULD have written a terminal status before the finalizer runs. Reaching this branch is a defense-in-depth path; observability requires logging. Authority: spec `:1774` ("A log warning is emitted when this branch fires so the anomaly is observable"). |
| `False` | `.status == "resolved"` or `"canceled"` | **MUST NOT** write. Worker already wrote terminal state. | None — happy path. |
| `False` | `is None` (tombstone race) | **MUST NOT** write. | **`logger.warning`** — tombstone anomaly. Authority: spec `:1786`, `:1822`. |
| `True` | `.status == "pending"` (per L1 corrected behavior) | **MUST NOT** write. Existing `if not captured_request_parse_failed:` guard at `:2362` continues to gate D4 (and D6). | **None** — expected for unknown-kind parse-failure path. Logging here would be noise (path is a contract-defined audit-trail behavior, not anomalous). |
| `True` | other | (unreachable — parse-failed guarantees minimal record exists per `:947-961`) | N/A |

**Three-way warning split is binding.** The Round-1 draft conflated the anomalous-pending path with the tombstone path and missed the parse-failed-pending path entirely. The corrected discipline:

- **anomalous warning** = parse_failed=False + snapshot.status=="pending" (defense-in-depth log).
- **tombstone warning** = snapshot is None (race log).
- **silent** = parse_failed=True + snapshot.status=="pending" (expected unknown-kind audit path).

Authority: spec `:1774` (anomalous-pending warning), `:1786` + `:1822` (tombstone warning), live code at `:947-961` (parse-failed creates minimal record → silent), spec `:1801` and `:1826` (parse-failed pending falls through to L11 carve-out).

### L3 — Terminal-Status Derivation Mapping

When `request_snapshot.status` is terminal, `final_status` derives from the snapshot — **not** from `captured_request.kind`. Spec `:1762-1767` is the binding 4-row table:

| `request_snapshot.status` | `turn_result.status` | `final_status` |
|---|---|---|
| `"resolved"` | `"completed"` | `"completed"` |
| `"resolved"` | `"interrupted"` or `"failed"` | `"unknown"` |
| `"canceled"` | any | `"canceled"` |
| `"pending"` OR `None` | any | fall through to L4 (kind-based) |

**Dispatch-clarity presentation** (informative, not binding — preserves spec's conceptual 4-row table):

```python
if request_snapshot is not None and request_snapshot.status == "resolved":
    if turn_result.status == "completed":
        final_status = "completed"
    elif turn_result.status == "interrupted":
        final_status = "unknown"
    elif turn_result.status == "failed":
        final_status = "unknown"
    else:
        final_status = "unknown"  # defensive — spec :1772 rationale OB-1
elif request_snapshot is not None and request_snapshot.status == "canceled":
    final_status = "canceled"
else:
    # snapshot is pending or None — fall through to L4
    ...
```

The split of `interrupted`/`failed` into two presentation rows prevents reading "non-completed" loosely. The spec's underlying contract is "any non-completed turn under a resolved request → unknown" (OB-1, spec `:1772`).

**Forbidden:** lumping `failed` into the legacy kind-based escalation branch. The current code's `else: final_status = "needs_escalation"` at `:2390` is a defect for the resolved-snapshot path.

### L4 — Preserve L11 Unknown-Kind Carve-Out

The L11 routing at `:2383-2384`:

```python
if interrupted_by_unknown:
    final_status: JobStatus = "unknown"
```

stays in place as the **first** branch of the kind-based fall-through. The terminal-guard table (L3) runs **before** the kind-based fall-through; only when L3 returns "fall through" does the kind-based logic execute. Authority: Task 17 L11 record (`task-17-convergence-map.md:101-138`), spec `:1801` and `:1826`.

**Required ordering inside the captured-request branch (CORRECTED — Round 1's ordering was self-contradictory: D4 cannot be snapshot-conditional before snapshot exists):**

```python
# Step 1. D6 diagnostic
#         Run iff `not captured_request_parse_failed` (existing guard at :2362).
#         Independent of snapshot — must happen for parseable requests.
#
# Step 2. Snapshot read (L1)
#         request_snapshot = self._pending_request_store.get(captured_request.request_id)
#         For parse-failed: snapshot exists per :947-961 with status="pending".
#         For non-parse-failed: snapshot may be pending/resolved/canceled/None.
#
# Step 3. D4 conditional write + warning discipline (L2)
#         Per the four-row L2 table above. parse_failed=True path skips D4 entirely
#         (preserves :2362 guard). Non-parse-failed cases gate on snapshot.status.
#
# Step 4. Terminal-guard derivation (L3) — resolved/canceled produce final_status
#         If snapshot is not None and snapshot.status in ("resolved", "canceled"):
#             final_status derived per L3's mapping table.
#         Else: fall through to Step 5.
#
# Step 5. Kind-based fall-through (L4) — pending/None paths
#         a. interrupted_by_unknown → final_status = "unknown"  (L11 preserved)
#         b. captured_request.kind in _CANCEL_CAPABLE_KINDS → "needs_escalation"
#         c. turn_result.status == "completed" → "completed"
#         d. else → "needs_escalation"
#
# Step 6. _persist_job_transition(job_id, final_status)
#
# Step 7. Escalation tail (final_status == "needs_escalation") OR
#         non-escalation tail (any other final_status) — W6 unchanged shape
```

**Verification:** Step 2 precedes Step 3 (snapshot exists before D4 reads it). Step 3 precedes Step 4 (D4 may fire on the pending path before derivation but does not influence the snapshot per spec `:1785`). Step 4 precedes Step 5 (L3 must run before L11 fall-through to honor terminal-state authority).

### L5 — Preserve No-Capture Branch

`delegation_controller.py:2431-2445` (the `else` branch when `captured_request is None`) is **not** modified. Its three-way split on `turn_result.status` (`completed` / `failed` / else → `unknown`) and its sequencing (`_persist_job_transition` → `lineage_store.update_status` → `runtime_registry.release` → `session.close` → `_emit_terminal_outcome_if_needed`) stay byte-identical.

### L6 — Preserve Escalation/Non-Escalation Tails (with explicit lineage decision)

For `final_status == "needs_escalation"`: the audit emission (`:2395-2407`), post-audit re-read for return shape (`:2411-2413`), and `DelegationEscalation` construction at `:2416` are byte-identical. Any L3-derived non-fall-through path (resolved/canceled) routes to one of:

- `final_status == "completed"` → non-escalation tail (`:2424-2429`).
- `final_status == "unknown"` → non-escalation tail (`:2424-2429`).
- `final_status == "canceled"` → non-escalation tail (`:2424-2429`).

The non-escalation tail's sequencing (`lineage_store.update_status("completed")` → `runtime_registry.release` → `session.close` → `_emit_terminal_outcome_if_needed`) stays unchanged for all three new terminal job statuses.

**Explicit lineage decision (L6.1).** `lineage_store.update_status(collaboration_id, "completed")` writes the **lineage-handle** terminal state, which is distinct from the **job** terminal state. Spec `:1773` ("Matching `DelegationJob.status` is `canceled` per §JobStatus='canceled' propagation") implies the *job* status carries the terminal nuance; the lineage handle marks "this collaboration is closed."

**Adjudication needed — Round 3 acknowledges a real divergence.** Live code at `delegation_controller.py:710, :995, :1379` writes `lineage_store.update_status("unknown")` for non-finalizer unknown-paths (interrupt-failure, unknown-kind interrupt). The non-escalation tail at `:2425` writes `"completed"` for any final_status reaching it. Two precedents exist:

- **Precedent A (non-escalation tail):** lineage stays `"completed"` for all three new terminals (`completed`/`unknown`/`canceled`). Treats lineage as "collaboration closed," not as job-status mirror.
- **Precedent B (sibling unknown-paths):** lineage = `"unknown"` for `final_status="unknown"` to match `:710, :995, :1379`. Treats lineage as job-status reflection.

**This map adopts Precedent A** (lineage = `"completed"` for all three) for these reasons: (1) the existing non-escalation tail already runs unchanged for all three terminals, so adopting Precedent B requires *additional* edits to the tail — broader scope than W3/L6 promise; (2) spec `:1738-1827` is silent on lineage-handle status under the new finalizer guard, suggesting the existing tail behavior was the intended carrier; (3) `lineage_store.update_status("unknown")` at the three other sites is paired with non-finalizer cleanup paths that **never reached `_finalize_turn`** — they're sentinel-bypass paths handling pre-finalizer faults. Under the finalizer guard, `final_status="unknown"` for `resolved + non-completed` means "the operator's decision was accepted and dispatched, but post-dispatch turn resolution is **uncertain**." Lineage `"completed"` here means the *collaboration handle* is closed, NOT a claim about job-outcome certainty — the job-status `"unknown"` carries the uncertainty (Round 4 wording correction; Round-3 "we DO know" overstated).

**Verification obligation (Round 3 binding):** add a direct test asserting `lineage_store.get(collaboration_id).status == "completed"` post-finalizer for `final_status="unknown"`. If implementer discovery reveals Precedent B is correct (e.g., spec section uncovered later in dispatch authoritatively prescribes lineage-mirrors-job), surface as BLOCKED + adjudication. Do not silently switch.

**If Phase H Task 22 (contracts) overrides this decision later, that's a contracts-layer concern, not Task 19's**. The convergence map adopting it explicitly here prevents silent assumption.

### L7 — Same-Commit G18.1 Closure

The 6 G18.1 decorators (see Live Anchors table) are removed in the **same commit** as the `_finalize_turn` rewrite. The two `_TASK_19_FINALIZER_GUARD_REASON` constant declarations are deleted in the same commit. Final-state grep invariant: `_TASK_19_FINALIZER_GUARD_REASON` count across `tests/` = 0.

**Body rewrites pre-authorized** per Live Anchors table (live names override stale carry-forward.md mapping; do NOT require BLOCKED):

- `:1525` (`test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up`): body **must** be fully rewritten. **Round-5+6 correction:** the pre-Task-19 body sabotages `journal.append_audit_event` targeting the escalation audit at `:2395-2407`, but post-Task-19 approve→`resolved+completed→completed` routes to the non-escalation tail — escalation audit never fires. **Canonical injection:** sabotage **`lineage_store.update_status(collaboration_id, "completed")`** at `:2425` (direct store call; failure propagates through `_finalize_turn` to the cleanup wrapper at `:1352`). **Do NOT target `_emit_terminal_outcome_if_needed`** — it is best-effort (`try/except Exception` at `:1426` swallows all failures; exceptions never escape `_finalize_turn`; cleanup wrapper never fires). Bounded-poll observing `job.status == "unknown"` + cleanup invariants (runtime released, session closed). Implementer authority for sabotage mechanism (one-shot raise, monkeypatch).
- `:1737` (`test_decide_approve_resumes_runtime_and_returns_completed_result`): 5-step protocol — synchronous `DelegationDecisionResult(decision_accepted=True, ...)` + bounded-poll `controller.poll(job_id)` ≤ 5s observing `job_store.get(job_id).status == "completed"` + `pending_request_store.get(rid).status == "resolved"` + `_finalize_turn` ran via worker thread + W5 cleanup join.
- `:1881` (`test_decide_deny_marks_job_failed_and_closes_runtime` — **rename pre-authorized to `test_decide_deny_marks_job_completed_and_closes_runtime`**): deny analogue — synchronous `DelegationDecisionResult(decision_accepted=True, ...)` (deny is a valid decision, not a rejection) + bounded-poll `job_store.get(job_id).status == "completed"` (CORRECTED Round 3 from `"failed"`; spec `:1677, :1684`) + `pending_request_store.get(rid).status == "resolved"` + runtime released + session closed. Audit trail differentiation: `resolution_action == "deny"` field on the `PendingServerRequest` distinguishes deny-completed from approve-completed.
- `:1927` (`test_decide_deny_emits_terminal_outcome`): same shape as `:1881` plus assertion that a `delegation_terminal` record is appended to `outcomes.jsonl` with job status `completed` (CORRECTED Round 3). Implementer authority for exact outcomes-file inspection mechanism (existing `outcome_log` fixture vs direct file read).
- `:857, :934`: end-to-end through `mcp.delegate_decide` boundary; same observable post-state as `:1737, :1881` respectively. **`:934` asserts `job.status == "completed"` post-deny, NOT `"failed"`.**

### L8 — Same-Commit F16.1 Closure With Concrete Bodies

The 2 F16.1 decorators at `test_handler_branches_integration.py:161, :179` are removed in the **same commit**. Spec `:1794-1795` confirms these tests map to the two load-bearing "Yes" rows of the guard:

- `:170` (`test_happy_path_decide_approve_success`) → `resolved + completed → completed`.
- `:187` (`test_timeout_cancel_dispatch_succeeded_for_file_change`) → `canceled + any → canceled`.

**L8.1 — No `pass`-bodied unskips (binding sub-lock).** The current bodies at `:170-176` and `:187-...` are `pass` stubs. Decorator removal alone is vacuous closure. Both bodies **must** be implemented with concrete assertions before this commit lands. Audit invariant:

```
grep -A5 "@pytest.mark.skip" test_handler_branches_integration.py | grep -c "pass$" == 0   # post-Task-19
```

Plus a positive-coverage check: each unskipped F16.1 test exercises at least one branch of L3's mapping table (decide-success → `resolved+completed`; timeout-cancel → `canceled+any`).

**L8.2 — Body assertion shape (binding):**

- **`:170`** (`test_happy_path_decide_approve_success`): driver flow per docstring `:171-175` (worker parks → `decide(approve)` → `session.respond` succeeds → `record_response_dispatch` + `mark_resolved` → handler returns `None` → turn completes naturally). End-state assertions: `job_store.get(job_id).status == "completed"` + `pending_request_store.get(rid).status == "resolved"` + **single-finalization side-effect uniqueness (Round 4 — replaces Round-3 "at least once" which permitted double-finalization regressions):** assert exactly ONE terminal `delegation_terminal` outcome record + exactly ONE final `job_store` status transition for this `job_id` + exactly ONE `runtime_registry.release(runtime_id)` call + exactly ONE `session.close()` call + exactly ONE `lineage_store.update_status(collaboration_id, ...)` call from the captured-request branch. Side-effect uniqueness is the binding form (allows non-mutating helper extraction; catches duplicate finalization). Implementer authority for instrumentation pattern (mock spies, counting fixtures, or post-state inspection of audit/outcome streams) + runtime released + session closed.
- **`:187`** (`test_timeout_cancel_dispatch_succeeded_for_file_change`): driver flow per docstring (file_change capture → no operator decide → timer fires → `session.respond(cancel)` succeeds → `record_timeout(succeeded)`). End-state assertions: `job_store.get(job_id).status == "canceled"` + `pending_request_store.get(rid).status == "canceled"` + **single-finalization side-effect uniqueness (Round 4 — replaces Round-3 "at least once" which permitted double-finalization regressions):** assert exactly ONE terminal `delegation_terminal` outcome record + exactly ONE final `job_store` status transition for this `job_id` + exactly ONE `runtime_registry.release(runtime_id)` call + exactly ONE `session.close()` call + exactly ONE `lineage_store.update_status(collaboration_id, ...)` call from the captured-request branch. Side-effect uniqueness is the binding form (allows non-mutating helper extraction; catches duplicate finalization). Implementer authority for instrumentation pattern (mock spies, counting fixtures, or post-state inspection of audit/outcome streams) + runtime released + session closed.

**Conditional-coverage caveat (L8 escape hatch):** if implementer discovery during unskip reveals that one of the two F16.1 tests requires Task 20 (poll-projection catch) or Task 21 (discard-canceled) for end-to-end observability, that single test may be reclassified BLOCKED with W12 invocation. Default expectation: both pass with concrete bodies. The L8.1 `pass`-body audit invariant remains binding even if an escape hatch fires (the BLOCKED test stays decorated; no `pass` body is permitted to ship).

### L9 — Assertion-Shape Obligations Pre-Baked

Per L12 precedent (handoff memory `feedback_assertion_shape_implementer_discretion.md`), assertion shapes for unskipped tests are pre-specified to prevent BLOCKED rounds late in dispatch. **G18.1 and F16.1 shapes are now in L7 and L8.2 respectively** (see those locks for the per-test enumeration). L9 handles cross-cutting obligations:

**Bounded-poll budget (binding):** 5s total, 50ms intervals, 100 iterations max. Matches Round-6 Adjudication D pattern. Use a small helper at module-local `_build_controller` callsite or inline in test bodies.

**Warning-emission test obligations (3 binding tests, distinct from G18.1/F16.1):**

1. **Tombstone warning** — fires when `_finalize_turn` runs with `captured_request != None` and `pending_request_store.get(rid)` returns `None`. Test must assert `logger.warning` was emitted with a tombstone-identifying substring.
2. **Anomalous-pending warning** — fires when `parse_failed=False` AND `snapshot.status == "pending"` (defense-in-depth path). Test must assert `logger.warning` was emitted with an **L2-specific identifying substring** (e.g., `"anomalous"` or `"pending"` in combination with a finalizer-guard context marker). **Round-6 correction:** a generic `logger.warning` assertion is insufficient because D6 (`_verify_post_turn_signals` at `:3022-3031`) runs **before** the snapshot read on parseable paths and emits its own `"D6 signal missing: ..."` warnings when post-turn notifications are absent. A test with empty notifications passes from D6 warnings even if the L2 warning is never implemented. Either (a) assert an L2-specific warning substring that D6 cannot produce, or (b) supply D6-satisfying notifications so D6 emits no warnings and only the L2 warning satisfies the assertion.
3. **Parse-failed pending silence** — fires when `parse_failed=True` AND `snapshot.status == "pending"` (expected unknown-kind audit path). Test must assert NO `logger.warning` fires from the L2 anomalous-pending branch (other warnings from the unknown-kind flow are permitted; assertion targets the L2-specific log substring, not any warning).

Implementer authority for test placement (existing finalizer-direct test file or new module). These three tests are **not** part of G18.1 or F16.1 — they are additive Task 19 coverage for the L2 warning discipline.

### L11 — Direct Finalizer-Guard Coverage (BINDING)

Round-1 listed direct finalizer-derivation tests as a *recommendation*. Adversarial review (Round 2) promoted them to a binding lock: the public-path G18.1/F16.1 unskips do NOT prove all spec guarantees. Specifically, they don't cover:

- **One-snapshot-read enforcement** (spec `:1747-1756`, `:1788`).
- **D4 blind-write suppression** on terminal snapshots (spec `:1782-1786`).
- **`resolved + failed → unknown`** row (spec `:1764-1765`, OB-1 rationale at `:1772`).
- **Anomalous-pending warning** (spec `:1774`).
- **Pre-D4 derivation invariant** (spec `:1788`: "the snapshot is frozen at the first read; any D4 mutation that follows is visible to future store reads but invisible to the captured snapshot").

**Minimum required direct-guard test coverage (each must be a distinct test or parameterized case):**

| # | Coverage | Authority |
|---|---|---|
| L11-T1 | `request_snapshot.status == "resolved"` AND `turn_result.status == "completed"` → `final_status == "completed"` | spec `:1764` |
| L11-T2 | `request_snapshot.status == "resolved"` AND `turn_result.status == "interrupted"` → `final_status == "unknown"` | spec `:1765` (OB-1) |
| L11-T3 | `request_snapshot.status == "resolved"` AND `turn_result.status == "failed"` → `final_status == "unknown"` | spec `:1765` (OB-1; the dispatch-clarity split row most likely to regress) |
| L11-T4 | `request_snapshot.status == "canceled"` AND `turn_result.status == "interrupted"` → `final_status == "canceled"` | spec `:1766` |
| L11-T5 | Terminal snapshot → D4 `update_status` is **NOT** called. **Both** `resolved` and `canceled` must be covered (either as two parameterized cases or two distinct tests). Verify via mock or store-record-version invariant. | spec `:1782-1786` |
| L11-T6 | `request_snapshot.status == "pending"` + parse_failed=False → D4 fires AND `logger.warning` fires AND derivation falls through to L4 kind-based logic with the *pre-D4 pending* status. | spec `:1774, :1785, :1788` |
| L11-T7 | One-snapshot invariant: only one `pending_request_store.get(rid).status` access participates in derivation. Two binding test cases: **(T7a — terminal-snapshot path):** drive snapshot=`"resolved"` + `turn_result.status="completed"` → `final_status="completed"` reaches non-escalation tail; assert `get_call_count == 1` (no hydration re-read on this path; the post-audit re-read at `:2411-2413` only fires in the escalation branch). **(T7b — pending fall-through with mid-flight store mutation):** drive snapshot=`"pending"` + cancel-capable kind (`command_approval` or `file_change`) → derivation falls through to L4, kind-based logic produces `final_status="needs_escalation"`, escalation tail fires the post-audit re-read at `:2411-2413`. **Primary proof target (Round 5 clarified):** D4 itself mutates the store from `"pending"` to `"resolved"` on this path (L2 pending row); the regression this test catches is a buggy implementation that re-reads the store **after** D4 and sees `"resolved"`, misclassifying into the L3 resolved branch instead of the L4 kind-based fall-through. **Verification mechanism:** wrap `pending_request_store` in a `_CountingPendingRequestStore` proxy that exposes `get_call_count`. Assert: `final_status` remains `"needs_escalation"` (proves derivation used the pre-D4 snapshot, not the post-D4 store state — spec `:1785, :1788`); the returned `DelegationEscalation` shape may reflect the post-D4 status (hydration is permitted to use fresh store state for non-status fields). Implementer authority for whether the proxy also exposes `mutate_status_between_calls()` as additional instrumentation; the minimal proof obligation is that `final_status` ignores D4's write. | spec `:1747-1756, :1785, :1788` |

**Test placement:** new test module `tests/test_finalize_turn_terminal_guard.py` OR additions to `tests/test_delegation_controller.py` adjacent to existing `_build_controller` patterns. Implementer authority for module choice; tests must be direct-call (invoke `_finalize_turn` directly with constructed `PendingServerRequest` + `TurnExecutionResult` fixtures, bypassing `start()`/`decide()`).

**Why direct-call:** end-to-end paths (G18.1/F16.1) cannot easily inject a `resolved+failed` combination — the worker resolves on success, not failure; failure paths typically take sentinel-bypass routes that skip `_finalize_turn`. Direct-call tests construct the snapshot state explicitly, exercising the L3 mapping table without needing a full async-decide flow.

### L10 — Out-of-Scope Boundaries

Task 19 must **not**:

- Modify `poll()` projection (Task 20). G18.1 tests' `controller.poll(job_id)` use is observation-only on terminal status; existing `poll()` returns the snapshotted job state without unknown-kind catch.
- Modify `discard()` (Task 21). Tests that assert `discard()` admits `"canceled"` belong to Task 21.
- Modify contracts (Task 22).
- Modify `decide()` body (W1) or worker resume path (post-Task-18-fix at `:1160-1172` is binding).
- Modify `start()` body (Task 17 territory).
- Modify the `DelegationEscalation` count = 2 invariant (W7).
- Modify the worker payload / `DecisionResolution.action` field (Task 18 territory).
- Resolve TT.1 `_FakeControlPlane` Pyright issues (carry-forward; Phase H end or end-of-Packet-1).
- Resolve RT.1 `runtime.py` Pyright `TurnStatus` literal narrowing (carry-forward; Phase H end or end-of-Packet-1).

## Watchpoints (W1-W12)

| ID | Watchpoint | Audit |
|---|---|---|
| W1 | Do NOT modify `decide()` body | `git diff <base> -- packages/plugins/codex-collaboration/server/delegation_controller.py` shows no edits in `def decide(...)` range |
| W2 | Do NOT modify `start()` body | Same diff: no edits in `def start(...)` range |
| W3 | `_finalize_turn` non-escalation tail sequencing UNCHANGED | `:2424-2429` (post-rewrite shifted lines) byte-identical to pre-rewrite for the lineage/release/close/emit calls |
| W4 | `_finalize_turn` no-capture branch UNCHANGED | `:2431-2445` byte-identical |
| W5 | L11 unknown-kind carve-out PRESERVED | `interrupted_by_unknown → "unknown"` branch present and ordered before `_CANCEL_CAPABLE_KINDS` check |
| W6 | Escalation audit emission shape UNCHANGED | `AuditEvent(...)` construction at audit emission site byte-identical (event_id/timestamp/actor/action/collaboration_id/runtime_id/job_id/request_id) |
| W7 | `DelegationEscalation(` count = 2 | `grep -c "DelegationEscalation(" delegation_controller.py == 2` |
| W8 | `_decided_request_ids` count = 0 | `grep -c "_decided_request_ids" delegation_controller.py == 0` (Task 17/18 invariant carries forward) |
| W9 | Old wrapper-key reads = 0 | `grep -c "resolution\.payload\.get" delegation_controller.py == 0` (Task 18 Round-7 invariant) |
| W10 | F16.1 same-commit unskip — count of `@pytest.mark.skip` in `test_handler_branches_integration.py` decreases by 2 | Default pre = 2, post = 0; if L8 caveat invoked, pre = 2, post = 1 + BLOCKED record |
| W11 | `_TASK_19_FINALIZER_GUARD_REASON` count across tests/ = 0 | `grep -rn "_TASK_19_FINALIZER_GUARD_REASON" tests/ \| wc -l == 0` |
| W12 | Bucket reclassification requires BLOCKED | Per `feedback_bucket_reclassification_requires_blocked.md` — any test that fails end-to-end and is proposed for re-deferral MUST be BLOCKED, not silently re-skipped |

## Branch Matrix

Spec `:1791-1804` enumerates 9 paths. Task 19 maps them as follows:

| Worker path | Pre-finalizer request status | Reaches `_finalize_turn`? | L3 outcome |
|---|---|---|---|
| Decide-success (any kind) | `resolved` | Yes | `final_status="completed"` (or `"unknown"` on rare post-dispatch turn fault) |
| Timeout-cancel-dispatch-succeeded (cancel-capable) | `canceled` | Yes | `final_status="canceled"` |
| Timeout-interrupt-succeeded (non-cancel-capable) | `canceled` | **No** — sentinel bypass | N/A |
| Timeout-interrupt-failed (non-cancel-capable) | `canceled` | **No** — sentinel bypass | N/A |
| Timeout-cancel-dispatch-failed (cancel-capable) | `canceled` | **No** — sentinel bypass | N/A |
| Dispatch-failed (any kind) | `canceled` | **No** — sentinel bypass | N/A |
| Internal-abort | `canceled` | **No** — sentinel bypass | N/A |
| Unknown-kind parse failure | `pending` (per audit-trail contract; record exists per `:947-961`) | Yes (`captured_request_parse_failed=True`) | Snapshot read **performed**; status is `"pending"`; D4 + D6 skipped (existing `:2362` guard); L3 does not fire; L4 L11 carve-out → `final_status="unknown"` |
| No capture (analytical turn) | N/A (`captured_request=None`) | Yes (no-capture branch) | L5 — unchanged |

The two **Yes** rows that exercise L3's terminal-mapping table are the two load-bearing rows. F16.1's two tests (`:170` decide-success / `:187` timeout-cancel-success) cover them directly.

## Per-Test Triage

### Bucket A (same-commit closes — no carry-forward)

| Test (live name @ HEAD `844e6f97`) | File | Pre-line | Closes |
|---|---|---|---|
| `test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up` | `test_delegation_controller.py` | 1525 | G18.1 (body rewrite — Bucket B reclassification per Task 17 L13) |
| `test_decide_approve_resumes_runtime_and_returns_completed_result` | `test_delegation_controller.py` | 1737 | G18.1 (5-step protocol) |
| `test_decide_deny_marks_job_failed_and_closes_runtime` (rename to `..._completed_...` pre-authorized) | `test_delegation_controller.py` | 1881 | G18.1 (deny analogue; **asserts `job.status == "completed"` per Round-3 spec correction, NOT `"failed"`**) |
| `test_decide_deny_emits_terminal_outcome` | `test_delegation_controller.py` | 1927 | G18.1 (deny + outcomes-file assertion) |
| `test_delegate_decide_approve_end_to_end_through_mcp_dispatch` | `test_delegate_start_integration.py` | 857 | G18.1 (MCP boundary) |
| `test_delegate_decide_deny_end_to_end_through_mcp_dispatch` | `test_delegate_start_integration.py` | 934 | G18.1 (MCP boundary) |
| `test_happy_path_decide_approve_success` | `test_handler_branches_integration.py` | 161 | F16.1 (concrete body required per L8.1) |
| `test_timeout_cancel_dispatch_succeeded_for_file_change` | `test_handler_branches_integration.py` | 179 | F16.1 (concrete body required per L8.1) |

**Total Bucket A: 8 tests.**

### Bucket B (deferred — none anticipated for Task 19)

Default expectation: zero. If implementer discovers a deferral need, it must follow W12 (BLOCKED + adjudication).

### New tests (additive — BINDING per L9 + L11)

**L9 warning-discipline tests (3):**

1. Tombstone warning on `pending_request_store.get == None`.
2. Anomalous-pending warning on parse_failed=False + snapshot.status=="pending".
3. Parse-failed pending silence — no anomalous-pending warning when parse_failed=True.

**L11 direct finalizer-guard tests (8 — 7 obligations, L11-T7 split into T7a + T7b):**

L11-T1 through L11-T7b per L11's table. Direct-call exercises bypassing `start()`/`decide()`; constructs `PendingServerRequest` + `TurnExecutionResult` fixtures explicitly. T7a covers terminal-snapshot single-read (non-escalation tail); T7b covers pending fall-through with mid-flight store mutation (escalation tail + hydration re-read).

**Total new additive tests: 11 binding** (3 from L9 + 8 from L11). May be parameterized in fewer files.

## Acceptance Criteria

### Code

- [ ] `_finalize_turn` captured-request branch restructured per L1-L4.
- [ ] D4 conditional per L2's snapshot status table.
- [ ] L3 mapping implemented (3 terminal outcomes: `completed`/`unknown`/`canceled`).
- [ ] L11 carve-out preserved at `interrupted_by_unknown` (L4).
- [ ] Non-escalation tail unchanged (L6).
- [ ] No-capture branch unchanged (L5).
- [ ] `DelegationEscalation` count = 2 (W7).
- [ ] All other watchpoints (W1-W12) verified.

### Tests

- [ ] All 6 G18.1 decorators removed (L7).
- [ ] All 2 F16.1 decorators removed (L8) — or 1 + BLOCKED record per L8 caveat.
- [ ] L8.1 audit invariant: zero `pass`-bodied unskipped tests in Task 19's commit.
- [ ] `_TASK_19_FINALIZER_GUARD_REASON` constants deleted from both test files (L7).
- [ ] **L9 warning-discipline tests added (3 binding):** tombstone, anomalous-pending, parse-failed pending silence.
- [ ] **L11 direct finalizer-guard tests added (8 binding — 7 obligations, T7 split into T7a + T7b):** L11-T1 through L11-T7b covering each spec mapping row + D4 suppression + one-snapshot invariant (T7a: terminal-snapshot non-escalation path; T7b: pending fall-through escalation path with mid-flight store mutation).
- [ ] G18.1 body rewrites match L7 assertion shapes (live names override stale carry-forward.md mapping).
- [ ] F16.1 bodies match L8.2 assertion shapes (concrete, not `pass`).
- [ ] Full codex-collaboration test suite passes.

### Closeout-docs

- [ ] `task-19-convergence-map.md` Round-N addendum if rounds occur during dispatch.
- [ ] `task-19-dispatch-packet.md` authored.
- [ ] `carry-forward.md` updated: G18.1 closed, F16.1 closed, F16.2 lineage closed, TT.1 + RT.1 unchanged.
- [ ] `phase-h-finalizer-consumers-contracts.md` updated either to refresh stale anchors OR to record that Task 19 convergence map supersedes its `:14, :121` anchors.

## Pre-Dispatch Checklist

1. [ ] HEAD verified at `844e6f97` (or later closeout commit).
2. [ ] Working tree clean.
3. [ ] Branch `feature/delegate-deferred-approval-response`.
4. [ ] Spec `:1738-1827` re-read.
5. [ ] Spec `:1705-1736` (Unknown-kind contract) re-read for L4 boundary.
6. [ ] carry-forward.md G18.1 entry re-read for body-rewrite specs.
7. [ ] Live anchors re-verified via `grep` audits.
8. [ ] L1-L10 / W1-W12 internalized.
9. [ ] L9 assertion-shape obligations explicit in implementer prompt.
10. [ ] Bounded-poll budget 5s/50ms documented.
11. [ ] Pytest discipline (synchronous + `timeout` + file-redirect; no pipe-to-tail) baked into prompt.
12. [ ] BLOCKED protocol per W12 explicit in prompt.
13. [ ] Opus default per user preference (`feedback` memory).
14. [ ] TDD ordering preamble (test-first; rewrite second; verify; commit).
15. [ ] Stale Phase H plan anchors disclaimer in prompt (do NOT copy `:1439-1533` etc.).
16. [ ] Out-of-scope (Task 20/21/22) explicit in prompt.

## Commit Shape

Anticipated 1 + 1 + 1:

1. **`feat(delegate)`** — `_finalize_turn` rewrite + 6 G18.1 unskips (with deny test bodies asserting `completed`, not `failed`) + 2 F16.1 unskips with concrete bodies (per L8.1) + constant deletions + **3 binding L9 warning-discipline tests** + **8 binding L11 direct finalizer-guard tests (L11-T1 through L11-T7b — 7 obligations, T7 split into T7a + T7b)**. One commit.
2. **`fix(delegate)`** (anticipated, optional) — closeout-fix per spec/code-quality review findings.
3. **`docs(delegate)`** — closeout-docs: convergence map Round-N addenda + dispatch packet finalize + carry-forward updates + phase-H plan anchor refresh.

If review chain finds zero fixable issues, the fix commit is omitted (1 + 0 + 1).

## Carry-Forward Expectations (post-Task-19)

| Item | Pre-Task-19 | Post-Task-19 |
|---|---|---|
| F16.1 | 2 deferred | **CLOSED** |
| F16.2 | Lineage marker (Open) | **CLOSED via G18.1** |
| G18.1 | 6 deferred | **CLOSED** |
| TT.1 | Open | Open (carry to Phase H end) |
| RT.1 | Open | Open (carry to Phase H end) |
| `_TASK_19_FINALIZER_GUARD_REASON` count | 8 (declarations + decorators) | **0** |
| `DelegationEscalation(` count | 2 | 2 (W7) |
| Old wrapper-key reads | 0 | 0 (W9) |
| Phase H plan body anchors | Stale (`:1439-1533` etc.) | Refreshed OR superseded marker added |

## Pre-Dispatch Warnings

High-risk loci where past tasks have surfaced defects:

- **L1 / L2 composition:** the parse-failed path performs the snapshot read (record exists per `:947-961` with status `"pending"`) but skips D4 + D6 via the existing `:2362` guard; L3 does not fire; falls through to L11 carve-out → `"unknown"`. The tombstone path performs the snapshot read, gets `None`, emits `logger.warning`, skips D4, falls through to L4 kind-based logic. The anomalous-pending path performs the snapshot read, sees `"pending"`, fires D4 + `logger.warning`, falls through to L4 with the pre-D4 pending status. Three distinct flows; implementer must trace each combination explicitly.
- **L3 fall-through ordering:** L3 must run **before** L4. Reversing the order would re-introduce the kind-based misclassification on terminal snapshots.
- **L11 carve-out fragility:** the `interrupted_by_unknown` branch must remain **first** in the kind-based fall-through (after L3). If a refactor introduces a new branch ahead of it, unknown-kind paths regress to escalation.
- **Bounded-poll discipline:** all G18.1 tests asserting post-finalizer state require bounded polling on `controller.poll(job_id)`. Unbounded `assert poll().status == X` will hang under the async-decide model. Budget: 5s / 50ms intervals. (Round-6 Adjudication D pattern.)
- **Pytest discipline:** synchronous + `timeout 60/120/180` + file-redirect. No `| tail`, no Monitor + until, no `run_in_background: true` for verification. (Task 18 Round-6 watchdog-stall precedent.)
- **Phase H plan body line refs are stale.** Use Live Anchors table; do NOT trust `phase-h-finalizer-consumers-contracts.md` line numbers.
- **`_persist_job_transition` for `JobStatus="canceled"`/`"unknown"`.** These are existing `JobStatus` literals defined at `models.py:30-38` (the `Literal["queued", "running", "needs_escalation", "completed", "failed", "canceled", "unknown"]` type). Validation runs through the job store, not `runtime.py`. If `_persist_job_transition` rejects them, surface as BLOCKED — do not silently coerce.

## Restructure Record

### Round 6 (2026-04-27 — user's second independent adversarial review; supersedes Round 5 selectively)

User reviewed Round 5. Verdict: **minor revision** — core terminal-guard design stable. 2 High + 1 Medium test-instruction precision defects. No Critical or spec-mapping failures. All defects are in test-shape guidance, not in the terminal-guard mechanism itself.

| # | Defect | Severity | Round-5 location | Round-6 fix |
|---|---|---|---|---|
| H1 | L9 anomalous-pending warning test can be vacuous: D6 (`_verify_post_turn_signals` at `:3022-3031`) emits `"D6 signal missing: ..."` warnings on parseable paths before the snapshot read. A test with empty notifications passes from D6 warnings even if the L2 anomalous-pending warning is never implemented. | High | L9 warning-emission test #2 | Anomalous-pending test now requires an **L2-specific identifying substring** that D6 cannot produce; alternatively, supply D6-satisfying notifications so only L2's warning fires. Parse-failed silence test (#3) narrowed to target L2-specific substring, not any warning. |
| H2 | `:1525` failure-injection listed `_emit_terminal_outcome_if_needed` at `:2428` as a candidate target. That method is best-effort (`try/except Exception` at `:1426` swallows all failures into `logger.warning`); exceptions never escape `_finalize_turn`; the cleanup wrapper at `:1352` never fires. Implementer would produce a test that passes but proves nothing. | High | Live Anchors `:1525` row; L7 `:1525` body spec | `_emit_terminal_outcome_if_needed` explicitly disqualified. `lineage_store.update_status` at `:2425` is the canonical injection (direct store call; failure propagates). |
| M1 | Authority table ranked carry-forward (#3) above live code (#4) globally, but Live Anchors note at `:48` said live names override stale carry-forward locally. Self-contradiction invites copy-paste misuse in dispatch packet. | Medium | Authority Order (`:19-25`) | Split by artifact class: carry-forward is authoritative for **bucket closeout state and intent**; live code is authoritative for **names, line anchors, current bodies, callsite shape, and API signatures**. Contradiction resolved. |

**Dispatch-packet note (not a convergence-map defect):** F16.1 side-effect uniqueness relies on non-deduped signals (job-store transition, lineage update, runtime release, session close) as the load-bearing duplicate-finalization proof. `append_delegation_outcome_once()` dedupes by job ID at `journal.py:297`; the "exactly one terminal outcome record" assertion alone cannot catch duplicate finalization. Dispatch prompt must preserve the non-deduped checks.

**Defect taxonomy:** H1 and H2 are test-vacuity defects — scenarios where a test passes for the wrong reason (D6 warning contamination, best-effort swallowing). M1 is an authority-layer inconsistency. All three are precision refinements, not conceptual or spec-mapping issues. The convergence map's core L1-L4 mechanism, L11 direct-guard obligations, and L7/L8 public-path specifications have been stable since Round 4.

### Round 5 (2026-04-27 — user's independent adversarial review; supersedes Round 4 selectively)

User reviewed Round 4 independently. Verdict: **minor revision** — core L1-L4 mechanism credible; no Critical failures. 2 High-risk + 3 Low-risk dispatch-readiness defects identified. All rooted in stale failure-injection assumptions and count-propagation gaps from earlier rounds' corrections.

| # | Defect | Severity | Round-4 location | Round-5 fix |
|---|---|---|---|---|
| H1 | `:1525` rewrite obligation named an unreachable failure injection. Pre-Task-19 body sabotages `journal.append_audit_event` (escalation audit at `:2395-2407`), but post-Task-19 approve→`resolved+completed→completed` routes to non-escalation tail — escalation audit never fires. | High | Live Anchors `:1525` row; L7 `:1525` body spec | Rewritten: sabotage must target a **reachable non-escalation-tail write**. Round-5 listed `lineage_store.update_status` and `_emit_terminal_outcome_if_needed` as candidates; **Round 6 further narrowed** to `lineage_store.update_status` only (see Round 6 H2). |
| H2 | L11-T7 split into T7a+T7b at Round 4 but downstream counts still said "7" direct tests. Per-Test Triage (`:376`), Acceptance Criteria (`:402`), and Commit Shape (`:437`) all undercounted. Dispatch could satisfy "7 tests" while implementing only one T7 subcase. | High | Per-Test Triage, Acceptance Criteria, Commit Shape | All counts updated: "8 binding — 7 obligations, T7 split into T7a + T7b." Total new additive tests updated from 10 to 11. |
| L1 | T7b's `_CountingPendingRequestStore` proxy obscured the simpler proof target: D4 itself mutates the store from `"pending"` to `"resolved"` on the anomalous-pending path; a buggy re-read would see `"resolved"` and misclassify. | Low | L11-T7b verification mechanism | T7b clarified: D4's pending→resolved mutation is the **primary proof target**. Proxy `get_call_count` is the minimal mechanism. `mutate_status_between_calls()` is implementer-discretionary additional instrumentation, not the core obligation. |
| L2 | `runtime.py:270` `JobStatus` pointer was stale. `JobStatus` lives at `models.py:30-38`; validation runs through the job store, not `runtime.py`. | Low | Pre-Dispatch Warning bullet 7; L10 RT.1 reference | Pre-Dispatch Warning corrected to cite `models.py:30-38`. L10 RT.1 reference generalized to `runtime.py` (Pyright narrowing issue, not JobStatus location). |
| L3 | MCP G18.1 rows (`:857, :934`) did not explicitly state bounded-poll; live tests currently immediate-poll after decide. | Low | Live Anchors MCP rows | Added explicit "**Bounded-poll** per L9 budget" to both MCP rows. |

**Defect taxonomy:** H1 is a carry-forward mechanism defect (old sabotage target surviving a routing change). H2 is a Round-4 propagation gap (T7 split applied to L11 but not to downstream totals). L1-L3 are precision improvements. No conceptual or spec-mapping defects found — the core terminal-guard design has been stable since Round 4.

### Round 4 (2026-04-26 — third adversarial review correction; supersedes Round 3 selectively)

| # | Defect | Round-3 location | Round-4 fix |
|---|---|---|---|
| C1 | L11-T7 specified an impossible scenario (snapshot=`"resolved"` + `final_status="needs_escalation"` — L3 forbids this combination). Would push implementer toward the bug Task 19 exists to fix. | L11-T7 row | Split into T7a (terminal-snapshot path: snapshot=`resolved` + `turn_result.status="completed"` → `completed`; assert `get_call_count==1`, no hydration re-read) and T7b (pending fall-through: snapshot=`pending` + cancel-capable kind → `needs_escalation`; mid-flight store mutation between derivation read and hydration re-read; assert derivation used pre-mutation snapshot). |
| H1 | Rename policy contradicted itself (rename pre-authorized at `:54, :232, :477`; "no rename anticipated" at `:59`). | L7 rename guidance + Per-Test Triage row | Single source: `:1881` rename **expected** (not optional); `:1927, :934` names accurate (no rename). Per-Test Triage row updated. |
| H2 | F16.1 "invoked at least once" too weak — permits double-finalization regressions (duplicate outcome emission, repeated release/close, duplicate audit). | L8.2 F16.1 body specs | Replaced with side-effect uniqueness binding: exactly ONE terminal outcome + ONE job transition + ONE runtime release + ONE session close + ONE lineage update. Catches duplicate finalization while permitting non-mutating helper extraction. |
| H3 | L6.1 "we DO know" wording overstated — `resolved + failed → unknown` explicitly means uncertain job outcome. | L6.1 rationale (3) | Reworded: lineage `"completed"` means *collaboration handle closed*, not job-outcome certainty. Job status `"unknown"` carries uncertainty. |

### Round 3 (2026-04-26 — second adversarial review correction; supersedes Round 2 selectively)

Round 2 closed Round 1's 5 Criticals but adversarial re-review identified 3 new Criticals + 3 high-risk under-specifications, all rooted in **carry-forward contamination** (a different surface than Round 2's stale line numbers). Round 3 corrections:

| # | Defect | Round-2 location | Round-3 fix |
|---|---|---|---|
| C1 | Deny terminal expectation `failed` contradicts L3 + spec `:1677, :1684, :1686`. `deny → decline` does NOT abort the turn; App Server processes decline and continues; turn completes naturally; finalizer maps `resolved + completed → completed`. The G18.1 deny test names encode pre-Packet-1 semantics. | L7 deny rows (`:1881, :1927, :934`); Per-Test Triage row 3 | All deny assertions corrected to `job.status == "completed"`. Test name `test_decide_deny_marks_job_failed_and_closes_runtime` rename pre-authorized to `test_decide_deny_marks_job_completed_and_closes_runtime`. Audit-trail differentiation via `resolution_action == "deny"` field, NOT job status. Authority cited explicitly. |
| C2 | Branch Matrix and Pre-Dispatch Warnings still said "Snapshot read SKIPPED" for parse-failed, contradicting L1's corrected model. Round 2 fixed L1 but missed downstream sections. | Branch Matrix row 8 (`:333`); Pre-Dispatch Warning bullet 1 (`:452`) | Branch Matrix corrected: snapshot read **performed**; D4+D6 skipped; L11 carve-out fires. Pre-Dispatch Warning rewritten to enumerate three distinct flows (parse-failed-pending, tombstone, anomalous-pending) consistently with L2's four-row table. |
| C3 | Commit Shape said "recommended direct-derivation tests" — copy-prone summary that downgrades L11's binding status. | Commit Shape feat-commit description (`:428`) | Replaced with explicit "**3 binding L9 warning-discipline tests** + **7 binding L11 direct finalizer-guard tests (L11-T1 through L11-T7)**." |

| # | Under-specification | Round-2 location | Round-3 fix |
|---|---|---|---|
| H1 | L6.1 lineage decision was assumed-not-justified vs sibling unknown-paths writing `lineage_store.update_status("unknown")`. | L6.1 | Adjudication record added: Precedent A (non-escalation tail) vs Precedent B (sibling unknown-paths). Map adopts Precedent A with three-reason rationale. Binding verification: direct test asserting `lineage_store.get(cid).status == "completed"` post-finalizer for `final_status="unknown"`. Implementer must surface BLOCKED if discovery contradicts. |
| H2 | L11-T7 verification mechanism underspecified ("count only `.status`-participating reads") — plain `get()` count cannot distinguish hydration reads. | L11-T7 row | Specified `_CountingPendingRequestStore` proxy fixture. Binding form (b): exactly one `get` before derivation completes; any subsequent `get` calls occur AFTER `final_status` is determined. Test scenario uses `final_status="needs_escalation"` to force the post-audit re-read and verify mid-flight store mutation does not change `final_status`. |
| H3 | F16.1 "invoked exactly once" overfits implementation mechanics — would break harmless helper extraction. | L8.2 F16.1 body specs | Softened to "invoked at least once" with rationale comment in the assertion. |

**Process precedent (Round 3, second instance):** carry-forward contamination is a recurring pattern in Phase H authoring. Round 2 caught stale line numbers; Round 3 caught stale test names + stale terminal-status expectations + stale "skipped" language in lower sections. Future convergence maps must (1) cross-check every test-name expectation against current spec mapping tables before authoring locks; (2) grep all sections for old-contract artifacts ("failed", "skipped", "exactly once", "rename-pre-auth") before declaring dispatch-ready; (3) state explicitly when a test's pre-existing name is a *contract artifact* vs an *implementation artifact*. Candidate L15-class lock for Phase H Task 22 contracts.

### Round 2 (2026-04-26 — adversarial review correction; supersedes Round 1; selectively superseded by Round 3)

Adversarial review identified 5 Critical defects in Round-1 plus 3 high-risk under-specifications. All confirmed against live code at HEAD `844e6f97`. Round 2 corrections:

| # | Defect | Round-1 location | Round-2 fix |
|---|---|---|---|
| C1 | G18.1 line→test mapping was stale (inherited from carry-forward.md without live-grep verification) | Live Anchors table; L7 body specs | Live Anchors re-grepped; 4 controller test names corrected (`:1525`=post-turn-finalization-failure, `:1737`=approve, `:1881`=deny-failed, `:1927`=deny-terminal-outcome). Carry-forward.md authority downgraded vs live grep. Rename pre-authorization removed (live names already describe intent). |
| C2 | Parse-failed model factually false ("no `request_id` to read with — never registered with the store") | L1 parse-failed interaction | L1 corrected per `delegation_controller.py:947-961`: parse-failed creates minimal `PendingServerRequest(kind="unknown")` and writes to store with `status="pending"`. Snapshot read IS performed; falls through L3 (snapshot.status=="pending") to L4 L11 carve-out → `final_status="unknown"`. |
| C3 | L4 ordering block self-contradictory ("D4 conditional write" before "Snapshot read") | L4 required-ordering block | Rewritten as 7-step Step-1 through Step-7 sequence: D6 → snapshot read → D4 conditional → terminal-guard derivation → kind-based fall-through → persist → tail. |
| C4 | Direct finalizer-guard tests as "recommended additions" | Per-Test Triage: Direct finalizer-derivation tests | Promoted to binding L11 with 7 specific test obligations (L11-T1 through L11-T7) covering each spec mapping row + D4 suppression + one-snapshot invariant. |
| C5 | F16.1 closure was decorator-removal only (vacuous given `pass` bodies) | L8 | L8 split into L8.1 (no-`pass`-body audit invariant) + L8.2 (binding body assertion shapes for both `:170` and `:187`). |

| # | Under-specification | Round-1 location | Round-2 fix |
|---|---|---|---|
| H1 | Lineage semantics for `final_status="unknown"` assumed-not-decided | L6 | L6.1 added — explicit decision: lineage handle stays `"completed"` for all three new terminals; Phase H Task 22 may override. |
| H2 | Pending fallback warning under-specified (only tombstone covered) | L2 | L2 expanded to four-row table with three-way warning split: anomalous-pending (warn), tombstone (warn), parse-failed-pending (silent). L9 adds 3 binding tests for these. |
| H3 | "Exactly one get" imprecise wording | L1 | L1 reworded to "exactly one **derivation-status** snapshot read"; hydration reads explicitly excluded from the invariant. |

**Process precedent established:** carry-forward.md is *informative-only* below live code in convergence-map authoring. Task 18's closeout-docs (`844e6f97`) claimed "post-Task-18-fix line numbers" but did not re-grep, propagating stale mappings. Future closeout-docs MUST verify line numbers against live code before recording. (Candidate L15-class lock for Phase H Task 22 contracts.)

### Round 1 (2026-04-26 — initial dispatch-NOT-ready draft; SUPERSEDED by Round 2)

Authored against HEAD `844e6f97` after Task 18 Phase G CLOSE. Spec §`_finalize_turn` Captured-Request Terminal Guard (`design.md:1738-1827`) read verbatim. Live anchors verified via grep. F16.1 tests confirmed mapping to spec's two "Yes" load-bearing rows.

**Pre-baked obligations:**

- L9 assertion shapes (per `feedback_assertion_shape_implementer_discretion.md` precedent).
- W12 BLOCKED protocol (per `feedback_bucket_reclassification_requires_blocked.md`).
- Pytest discipline baked into pre-dispatch checklist (per Task 18 Round-6 precedent).
- Stale Phase H plan anchors disclaimer in authority order (lesson from initial orientation).

**Outstanding decisions for Round 2+:**

- Whether to formalize an L11-style positive-scope lock for the L2 tombstone-warning emission (currently L9 obligation only — could be promoted to a binding lock if Round-2 review wants).
- Whether direct finalizer-derivation tests become a binding L (currently recommendation in Per-Test Triage).
- Whether L8's caveat (single F16.1 test reclassified BLOCKED) should be hardened (prefer both pass) or softened (allow reclassify without BLOCKED if Task 20/21 dependency is concrete).

End of Round 1.

### Round 7 (2026-04-27 — post-implementation closeout)

Implementation dispatched and completed at feat `1f97b333`. Suite: 1040 passed, 0 skipped (pre-Task-19: 1020 passed, 8 skipped). Census: 1020 + 12 new (8 L11 + 2 parametrized T5 sub-cases + 3 L9 = 12 collected) + 8 unskipped (6 G18.1 + 2 F16.1) = 1040.

Closeout review (spec compliance + code quality) found 0 Critical, 4 required fixes:

| # | Fix | Severity | Location | Resolution |
|---|---|---|---|---|
| F1 | F16.1 `if outcomes_path.exists():` silently passes when no outcome file written; side-effect uniqueness assertions missing (L8.2 binding form) | Required | `test_handler_branches_integration.py` both F16.1 tests | Changed to `assert outcomes_path.exists()`; added counting wrappers for `session.close()`, `registry.release()`, `lineage_store.update_status()`. Pre-parsed JSON to eliminate triple-parse. |
| F2 | L11-T7b `get_call_count >= 1` trivially true after derivation read; no discriminating power | Required | `test_finalize_turn_terminal_guard.py:533` | Tightened to `== 2` (derivation + hydration re-read). |
| F3 | Missing bounded-poll success assertion in deny-emits-terminal-outcome | Required | `test_delegation_controller.py:2002-2008` | Added `assert final_job.status == "completed"` after poll loop. |
| F4 | Triple JSON parsing per outcome line | Required | `test_handler_branches_integration.py:243-247, :333-337` | Pre-parse once, filter on parsed list. |

All 4 fixes applied in closeout-fix `4409b23c`. Suite unchanged at 1040/0/0.

**Implementation notes (from implementer report):** All G18.1 tests required `session.respond` stubbing — `_FakeSession` and `_ConfigurableStubSession` default `respond=None` causes `TypeError` when the worker dispatches `session.respond(rid, payload)`. Deny audit assertion updated from `action="approve"` to `action="deny"` to match Task 18's L7a incidental fix. Both observations are environment-specific to the test fakes, not spec or code defects.

All locks (L1-L11) and watchpoints (W1-W12) verified.

Post-closeout independent review (user) identified one additional gap: F16.1 side-effect uniqueness assertions counted `session.close`, `runtime.release`, and `lineage.update_status` but NOT the job-store terminal transition — the fourth non-deduped signal required by L8.2. Fix at `f1fd24ba`: added `job_store.update_status_and_promotion` counting wrapper filtered to the expected terminal status (`"completed"` / `"canceled"`) in both F16.1 tests. Filtering excludes intermediate lifecycle transitions (`queued → running`). Suite unchanged at 1040/0/0.

Phase H Task 19 COMPLETE.

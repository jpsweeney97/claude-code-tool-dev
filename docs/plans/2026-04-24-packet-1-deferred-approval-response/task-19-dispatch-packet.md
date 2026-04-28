# Task 19 Dispatch Packet — T-20260423-02 (Phase H first task)

**Drafted:** 2026-04-27 (convergence map at `task-19-convergence-map.md` is binding authority at Round 6; 6 review rounds, last 2 yielded "minor revision" / "defensible" verdicts with zero Criticals. Core L1-L4 mechanism stable since Round 4).

**Workflow:** `superpowers:subagent-driven-development` — single fresh implementer (opus, `general-purpose`) + spec reviewer + code-quality reviewer (sequential, NOT parallel). Per Task 17/18 precedent, agent named explicitly for SendMessage continuity (closeout-fix + closeout-docs continue the same agent).

**Agent dispatch (controller invokes this after user approves the packet):**

```python
Agent({
  name: "task-19-implementer",
  subagent_type: "general-purpose",
  model: "opus",
  description: "Phase H Task 19 _finalize_turn terminal guard",
  prompt: <<everything in §"Implementer Prompt" below>>
})
```

---

## Implementer Prompt

You are the Task 19 implementer for T-20260423-02 Packet 1 (Deferred-Approval Response). You are dispatched into the existing `feature/delegate-deferred-approval-response` branch at base commit `844e6f97` (`docs(delegate): record Phase G Task 18 closeout (T-20260423-02)`). Phase G is complete (`start()` and `decide()` rewrites landed in Tasks 17 and 18). Task 19 is the FIRST task of Phase H and rewrites the captured-request branch of `_finalize_turn` for the one-snapshot terminal guard. Tasks 20-22 (poll/discard/contracts) are OUT OF YOUR SCOPE.

### Mission

Rewrite the captured-request branch of `_finalize_turn` at `delegation_controller.py:2340-2445` to enforce the **one-snapshot terminal guard** per spec §`_finalize_turn` Captured-Request Terminal Guard (`design.md:1738-1827`). Replace the legacy kind-based derivation at `:2385-2390` and the unconditional D4 write at `:2369-2371` with: snapshot read (L1) → D4 conditional write + warning discipline (L2) → terminal-status mapping (L3) → kind-based fall-through preserving the unknown-kind carve-out (L4). Same-commit deliverables: 6 G18.1 skip decorators removed + 2 F16.1 skip decorators removed with concrete bodies + 2 `_TASK_19_FINALIZER_GUARD_REASON` constant declarations deleted + 3 L9 warning-discipline tests added + 8 L11 direct finalizer-guard tests added. Carry-forward consequences: G18.1 CLOSES, F16.1 CLOSES, F16.2 lineage CLOSES.

### Authority sources (READ IN THIS ORDER)

**Pre-read guard:** All sources below MUST be readable from the current working tree (`/Users/jp/Projects/active/claude-code-tool-dev`). If `Read` fails on any of them with file-not-found or permission error, **stop and report BLOCKED** with the failing path — do NOT improvise from training knowledge or partial context. The convergence map is the binding dispatch authority; without it, you have no scope.

1. **Convergence map (BINDING):** `docs/plans/2026-04-24-packet-1-deferred-approval-response/task-19-convergence-map.md` (~563 lines after 6 review rounds). This is the dispatch authority. It contains:
   - **Live anchors table** (~20 rows; verified at HEAD `844e6f97`). Plan-cited line numbers in `phase-h-finalizer-consumers-contracts.md` are STALE. Use the convergence map's Live Anchors table for any line-number lookup.
   - **Authority order** (5 layers; carry-forward governs bucket state/intent; live code governs names/anchors/bodies/signatures)
   - **Locks L1-L11** (binding positive scope; mandatory things)
   - **Watchpoints W1-W12** (binding negative scope; forbidden things)
   - **Per-test triage table** (8 Bucket A same-commit closes; 0 Bucket B anticipated; 11 new additive binding tests)
   - **Branch matrix** (9 paths; 2 load-bearing "Yes" rows)
   - **Acceptance criteria** (Code + Tests + Closeout-docs)

2. **Spec — `_finalize_turn` Captured-Request Terminal Guard:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1738-1827`. The binding 4-row terminal mapping table (`:1762-1767`), one-snapshot invariant (`:1747-1756`), D4 suppression (`:1782-1788`), 9-path table (`:1792-1803`), and anomalous-pending warning (`:1774`).

3. **Spec — Unknown-kind contract:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1705-1736`. Specifically `:1725-1727` for the `interrupted_by_unknown → "unknown"` routing preserved as the L4 kind-based fall-through's first branch.

4. **Spec — Response payload mapping (INFORMATIONAL — deny semantics):** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:1663-1701`. Read `:1677, :1684, :1686` for the deny→decline semantics that ground the Round-3 correction: `deny` does NOT abort the turn; `final_status` for deny paths is `completed`, NOT `failed`.

5. **Carry-forward state:** `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md`. Pre-Task-19 entries: G18.1 (6 finalizer-dependent tests), F16.1 (2 handler-branch tests), TT.1, RT.1. **Carry-forward governs bucket closeout state and intent; live code governs names, line anchors, current bodies, and API signatures.**

6. **Plan body — Phase H Task 19 (INFORMATIONAL ONLY):** `docs/plans/2026-04-24-packet-1-deferred-approval-response/phase-h-finalizer-consumers-contracts.md`. Line anchors in this file are STALE (cite `:1439-1533`; live values are `:2340-2445`). Task decomposition (19/20/21/22 split) is authoritative; line refs are NOT. **Do not copy line anchors from this file.**

### TDD ordering preamble

Follow test-first development ordering:

1. **Write tests first** — L11 direct-guard tests + L9 warning tests. These test the spec contract against the NOT-YET-rewritten code. Most L11 tests and the anomalous-pending test should FAIL initially (proving the new behavior doesn't exist yet). The tombstone and parse-failed-silence tests may pass against current code.
2. **Rewrite `_finalize_turn`** — implement L1-L4 restructuring.
3. **Unskip G18.1 + F16.1** — remove decorators, rewrite bodies per L7/L8.
4. **Verify** — full suite must pass.
5. **Commit**.

### CRITICAL: Terminal-status mapping (L3 — the rewrite's core)

The binding 4-row table from spec `:1762-1767`. This replaces the kind-based derivation at `delegation_controller.py:2385-2390`:

| `request_snapshot.status` | `turn_result.status` | `final_status` |
|---|---|---|
| `"resolved"` | `"completed"` | `"completed"` |
| `"resolved"` | `"interrupted"` or `"failed"` | `"unknown"` |
| `"canceled"` | any | `"canceled"` |
| `"pending"` OR `None` | any | fall through to L4 (kind-based) |

Implementation sketch (informative, not binding):

```python
if request_snapshot is not None and request_snapshot.status == "resolved":
    if turn_result.status == "completed":
        final_status = "completed"
    elif turn_result.status == "interrupted":
        final_status = "unknown"
    elif turn_result.status == "failed":
        final_status = "unknown"
    else:
        final_status = "unknown"  # defensive — spec :1772 OB-1
elif request_snapshot is not None and request_snapshot.status == "canceled":
    final_status = "canceled"
else:
    # snapshot is pending or None — fall through to L4 kind-based logic
    ...
```

**Forbidden:** lumping `failed` into the legacy kind-based escalation branch. The current code's `else: final_status = "needs_escalation"` at `:2390` is the defect this task fixes.

### CRITICAL: Required ordering inside the captured-request branch (L1-L4)

```python
# Step 1. D6 diagnostic
#         Run iff `not captured_request_parse_failed` (existing guard at :2362).
#         Independent of snapshot — must happen for parseable requests.
#
# Step 2. Snapshot read (L1)
#         request_snapshot = self._pending_request_store.get(captured_request.request_id)
#
# Step 3. D4 conditional write + warning discipline (L2)
#         See the L2 table below.
#
# Step 4. Terminal-guard derivation (L3)
#         If snapshot is not None and snapshot.status in ("resolved", "canceled"):
#             final_status derived per L3's mapping table above.
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
#         non-escalation tail (any other final_status)
```

### CRITICAL: D4 conditional write + three-way warning discipline (L2)

The D4 write at `:2369-2371` becomes conditional on `request_snapshot.status`:

| `parse_failed` | `request_snapshot` | D4 action | Warning |
|---|---|---|---|
| `False` | `.status == "pending"` | **MUST** write `update_status(rid, "resolved")` — spec `:1785` permits this write ("D4 **may** write"); this dispatch makes it mandatory to preserve legacy D4 behavior on the pending fall-through path. The write does NOT retroactively promote the snapshot — derivation still treats the authoritative status as pre-D4 `"pending"`. L11-T6 tests this as a binding obligation. | **`logger.warning`** — anomalous fall-through per spec `:1774`. Use an **L2-specific identifying substring** (see L9 anomalous-pending test below). |
| `False` | `.status == "resolved"` or `"canceled"` | **MUST NOT** write. | None — happy path. |
| `False` | `is None` (tombstone race) | **MUST NOT** write. | **`logger.warning`** — tombstone anomaly per spec `:1786, :1822`. |
| `True` | `.status == "pending"` | **MUST NOT** write. Existing `:2362` guard gates D4 and D6. | **None** — expected unknown-kind audit path. |

### CRITICAL: Deny terminal status is `completed`, NOT `failed`

Spec `:1677, :1684, :1686` — `deny → decline` does NOT abort the turn. App Server processes decline and continues; turn completes normally; `item/completed` carries `status: "declined"` (item-level). L3 maps `resolved + completed → completed`. Every deny-path test must assert `job.status == "completed"`, NOT `"failed"`.

The pre-Packet-1 test name `test_decide_deny_marks_job_failed_and_closes_runtime` at `:1881` encodes defunct semantics. **Rename pre-authorized** to `test_decide_deny_marks_job_completed_and_closes_runtime`. No BLOCKED required.

### CRITICAL: `:1525` body rewrite — canonical failure injection

`test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up` at `:1525` requires a full body rewrite. The pre-Task-19 body sabotages `journal.append_audit_event` targeting the escalation audit at `:2395-2407`. Under post-Task-19 semantics, `approve → resolved + completed → completed` routes to the **non-escalation tail** (`:2424-2429`); the escalation audit at `:2394` never fires on this path.

**Canonical injection:** sabotage **`lineage_store.update_status(collaboration_id, "completed")`** at `:2425` (direct store call; failure propagates through `_finalize_turn` to the cleanup wrapper at `:1352`, which calls `_mark_execution_unknown_and_cleanup`).

**Do NOT target `_emit_terminal_outcome_if_needed`** — it is best-effort (`try/except Exception` at `:1426` swallows all failures into a `logger.warning`; exceptions never escape `_finalize_turn`; cleanup wrapper never fires).

Rewrite shape: drive `start()` → `decide(approve)` → worker completes → `_finalize_turn` runs on worker thread. Bounded-poll observing `job.status == "unknown"` + cleanup invariants (runtime released, session closed). Implementer authority for exact sabotage mechanism (one-shot raise, monkeypatch).

### CRITICAL: L9 warning-discipline tests (3 binding — L2-specific signals required)

These are additive tests, NOT part of G18.1 or F16.1. Direct-call tests invoking `_finalize_turn` with constructed fixtures.

1. **Tombstone warning** — `pending_request_store.get(rid)` returns `None`. Assert `logger.warning` emitted with a tombstone-identifying substring.

2. **Anomalous-pending warning** — `parse_failed=False` AND `snapshot.status == "pending"`. Assert `logger.warning` emitted with an **L2-specific identifying substring** (e.g., `"anomalous"` or `"pending"` combined with a finalizer-guard context marker). **WARNING: a generic `logger.warning` assertion is insufficient** because D6 (`_verify_post_turn_signals` at `:3022-3031`) runs BEFORE the snapshot read on parseable paths and emits its own `"D6 signal missing: ..."` warnings when post-turn notifications are absent. A test with empty notifications passes from D6 warnings even if the L2 warning is never implemented. Either (a) assert an L2-specific warning substring that D6 cannot produce, or (b) supply D6-satisfying notifications so D6 emits no warnings and only the L2 warning satisfies the assertion.

3. **Parse-failed pending silence** — `parse_failed=True` AND `snapshot.status == "pending"`. Assert NO `logger.warning` fires from the L2 anomalous-pending branch. Assertion targets the L2-specific log substring, not any warning (other warnings from the unknown-kind flow are permitted).

### CRITICAL: L11 direct finalizer-guard tests (8 binding — 7 obligations, T7 split into T7a + T7b)

These are direct-call tests that invoke `_finalize_turn` directly with constructed `PendingServerRequest` + `TurnExecutionResult` fixtures, bypassing `start()`/`decide()`. They cover spec guarantees that G18.1/F16.1 public-path tests cannot reach.

| # | Coverage | Authority |
|---|---|---|
| L11-T1 | `snapshot.status == "resolved"` + `turn.status == "completed"` → `final_status == "completed"` | spec `:1764` |
| L11-T2 | `snapshot.status == "resolved"` + `turn.status == "interrupted"` → `final_status == "unknown"` | spec `:1765` |
| L11-T3 | `snapshot.status == "resolved"` + `turn.status == "failed"` → `final_status == "unknown"` | spec `:1765` (most likely to regress) |
| L11-T4 | `snapshot.status == "canceled"` + `turn.status == "interrupted"` → `final_status == "canceled"` | spec `:1766` |
| L11-T5 | Terminal snapshot → D4 `update_status` is NOT called. **Both** `resolved` AND `canceled` must be covered. Verify via mock or store-record-version invariant. | spec `:1782-1786` |
| L11-T6 | `snapshot.status == "pending"` + parse_failed=False → D4 fires AND L2-specific `logger.warning` fires AND derivation falls through to L4 kind-based logic. | spec `:1774, :1785, :1788` |
| L11-T7a | One-snapshot: `snapshot="resolved"` + `turn.status="completed"` → non-escalation tail; assert `get_call_count == 1` (no hydration re-read on this path). | spec `:1747-1756` |
| L11-T7b | One-snapshot: `snapshot="pending"` + cancel-capable kind → `final_status="needs_escalation"` → escalation tail → hydration re-read. D4 mutates store from `"pending"` to `"resolved"` on this path; assert `final_status` remains `"needs_escalation"` (proves derivation used pre-D4 snapshot, not post-D4 store state). Wrap store in `_CountingPendingRequestStore` proxy with `get_call_count`. | spec `:1747-1756, :1785, :1788` |

**Test placement:** new test module `tests/test_finalize_turn_terminal_guard.py` OR additions to `tests/test_delegation_controller.py` adjacent to existing `_build_controller` patterns. Implementer authority for module choice.

**Why direct-call:** `resolved+failed` combination is unreachable via public paths — the worker resolves on success, not failure; failure paths take sentinel-bypass routes. Direct-call tests construct the snapshot state explicitly.

### CRITICAL: G18.1 body-rewrite specs (6 tests per L7)

All 6 skip decorators removed same-commit. Bodies must match these assertion shapes:

- **`:1525`** — full body rewrite per the `:1525` CRITICAL section above. Canonical injection: sabotage `lineage_store.update_status`. Bounded-poll `job.status == "unknown"`.
- **`:1737`** (`test_decide_approve_resumes_runtime_and_returns_completed_result`) — 5-step protocol: synchronous `DelegationDecisionResult(decision_accepted=True)` + bounded-poll `poll(job_id)` ≤ 5s observing `job.status == "completed"` + `pending_request_store.get(rid).status == "resolved"` + `_finalize_turn` ran via worker thread + cleanup join.
- **`:1881`** (rename to `test_decide_deny_marks_job_completed_and_closes_runtime`) — deny analogue: `DelegationDecisionResult(decision_accepted=True)` + bounded-poll `job.status == "completed"` (NOT `"failed"`) + `pending_request_store.get(rid).status == "resolved"` + runtime released + session closed. Audit differentiation via `resolution_action == "deny"`.
- **`:1927`** (`test_decide_deny_emits_terminal_outcome`) — same as `:1881` plus `delegation_terminal` outcome record with job status `completed`.
- **`:857`** (`test_delegate_decide_approve_end_to_end_through_mcp_dispatch`) — end-to-end via `mcp.delegate_decide`; bounded-poll `job.status == "completed"` (5s/50ms per L9 budget).
- **`:934`** (`test_delegate_decide_deny_end_to_end_through_mcp_dispatch`) — end-to-end via `mcp.delegate_decide`; `job.status == "completed"` (NOT `"failed"`); bounded-poll per L9 budget.

### CRITICAL: F16.1 body-rewrite specs (2 tests per L8)

Both skip decorators at `test_handler_branches_integration.py:161, :179` removed same-commit. Current bodies are `pass` stubs — decorator removal alone is vacuous. **Both must have concrete assertion bodies.**

- **`:170`** (`test_happy_path_decide_approve_success`) → `resolved + completed → completed`. End-state: `job.status == "completed"` + `pending_request_store.get(rid).status == "resolved"` + **single-finalization side-effect uniqueness:** exactly ONE terminal `delegation_terminal` outcome record + ONE final `job_store` status transition + ONE `runtime_registry.release` + ONE `session.close` + ONE `lineage_store.update_status`. Side-effect uniqueness is the binding form — catches duplicate finalization. The terminal outcome record alone is NOT sufficient for duplicate-finalization detection because `append_delegation_outcome_once()` dedupes by job ID; rely on the non-deduped signals (job transition, lineage update, release, close) as the load-bearing proof.

- **`:187`** (`test_timeout_cancel_dispatch_succeeded_for_file_change`) → `canceled + any → canceled`. End-state: `job.status == "canceled"` + `pending_request_store.get(rid).status == "canceled"` + same single-finalization side-effect uniqueness as above.

### Bounded-poll budget (L9)

5s total, 50ms intervals, 100 iterations max. Use a small helper or inline in test bodies.

### Pytest discipline

- Synchronous tests + `timeout` decorator (60/120/180s per test complexity).
- File-redirect for test output: `uv run --package codex-collaboration pytest -v 2>&1 | tee /tmp/task19-suite.txt`
- No pipe-to-tail, no Monitor + until, no `run_in_background: true` for verification.
- Per Task 18 Round-6 watchdog-stall precedent.

### `_TASK_19_FINALIZER_GUARD_REASON` constant deletion

Both constant declarations are deleted same-commit:

- `tests/test_delegation_controller.py:45`
- `tests/test_delegate_start_integration.py:33`

Post-deletion grep invariant: `_TASK_19_FINALIZER_GUARD_REASON` count across `tests/` = 0.

### L6.1 — Lineage stays `"completed"` for all terminals

The non-escalation tail at `:2424-2429` is NOT modified. `lineage_store.update_status(collaboration_id, "completed")` writes the lineage-handle terminal state for all three new job terminals (`completed`/`unknown`/`canceled`). Lineage `"completed"` means "collaboration handle closed," not a claim about job-outcome certainty.

**Verification obligation:** add a direct test asserting `lineage_store.get(collaboration_id).status == "completed"` post-finalizer for `final_status="unknown"`. If you discover spec authority that prescribes lineage-mirrors-job, surface BLOCKED.

### Code acceptance summary

- [ ] `_finalize_turn` captured-request branch restructured per L1-L4 ordering (Steps 1-7).
- [ ] D4 conditional per L2's snapshot status table.
- [ ] L3 mapping implemented (3 terminal outcomes: `completed`/`unknown`/`canceled`).
- [ ] L11 carve-out preserved at `interrupted_by_unknown` (L4 Step 5a — first branch of kind-based fall-through).
- [ ] Non-escalation tail unchanged (L6 — `:2424-2429` sequencing byte-identical).
- [ ] No-capture branch unchanged (L5 — `:2431-2445` byte-identical).
- [ ] `DelegationEscalation(` count = 2 (W7: `grep -c "DelegationEscalation(" packages/plugins/codex-collaboration/server/delegation_controller.py`).
- [ ] All watchpoints (W1-W12) verified.
- [ ] `JobStatus` values `"canceled"` and `"unknown"` accepted by `_persist_job_transition` (these are existing literals defined at `models.py:30-38`; validation runs through the job store. If rejected, surface BLOCKED).

### Tests acceptance summary

- [ ] All 6 G18.1 decorators removed (L7).
- [ ] All 2 F16.1 decorators removed (L8) — or 1 + BLOCKED record per L8 caveat.
- [ ] L8.1 audit invariant: zero `pass`-bodied unskipped tests in Task 19's commit.
- [ ] `_TASK_19_FINALIZER_GUARD_REASON` constants deleted from both test files.
- [ ] **3 L9 warning-discipline tests added** (tombstone, anomalous-pending with L2-specific substring, parse-failed pending silence).
- [ ] **8 L11 direct finalizer-guard tests added** (L11-T1 through L11-T7b — see table above).
- [ ] G18.1 body rewrites match L7 assertion shapes.
- [ ] F16.1 bodies match L8.2 assertion shapes (concrete with side-effect uniqueness, not `pass`). Non-deduped signals (job-store transition, lineage update, runtime release, session close) are the load-bearing duplicate-finalization proof.
- [ ] `:1881` rename applied (`..._failed_...` → `..._completed_...`).
- [ ] Full codex-collaboration test suite passes.
- [ ] **Suite expectation (expected census — verify, do not assume):** pre-Task-19 = 1020 passing / 8 skipped. Post-Task-19 = 1020 + 11 (new additive) - 0 (no deletions) = 1031 passing / 0 skipped; 1031 total tests; 0 failed. If the collected count differs (e.g., from parameterized helpers or environment-level collection differences), report the actual count and explain the discrepancy.
- [ ] **Full-suite hang verification:**
  ```bash
  uv run --package codex-collaboration pytest -v 2>&1 | tee /tmp/task19-suite.txt
  ```
  Must complete in normal wall-clock (~30-40s). Exit code 0.
- [ ] Lint: `uv run --package codex-collaboration ruff check packages/plugins/codex-collaboration/server/ packages/plugins/codex-collaboration/tests/` — no new findings.
- [ ] Pyright: no new diagnostics on touched files. Pre-existing RT.1 (`runtime.py` TurnStatus) and TT.1 (`_FakeControlPlane`) are OUT OF SCOPE.

### Closeout-docs acceptance summary (third commit)

- [ ] `carry-forward.md` G18.1 CLOSED (all 6 tests unskipped in Task 19 same-commit).
- [ ] `carry-forward.md` F16.1 CLOSED (both tests unskipped in Task 19 same-commit).
- [ ] `carry-forward.md` F16.2 CLOSED (lineage marker — closes when G18.1 closes).
- [ ] `carry-forward.md` TT.1, RT.1 UNCHANGED.
- [ ] `phase-h-finalizer-consumers-contracts.md` updated: either refresh stale anchors OR record that Task 19 convergence map supersedes its `:14, :121` anchors.
- [ ] `task-19-convergence-map.md` Round-N addendum if review rounds occurred during dispatch.

### Commit shape (anticipated 1+1+1)

| Step | Type | Subject |
|------|------|---------|
| 1 | feat | `feat(delegate): rewrite _finalize_turn with one-snapshot terminal guard (T-20260423-02 Task 19)` |
| 2 (anticipated) | fix | `fix(delegate): address Task 19 closeout review (T-20260423-02 Task 19 closeout)` |
| 3 (mandatory) | docs | `docs(delegate): record Phase H Task 19 closeout (T-20260423-02)` |

Stage specific files only (never `git add -A` / `git add .`). Co-author trailer: `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`. Do NOT amend; do NOT skip pre-commit hooks.

### Reporting contract

When the feat commit lands, report **DONE** with:

```
DONE
- Commit SHA: <sha>
- Suite: <output of `tail -5 /tmp/task19-suite.txt`>  (from the tee'd full-suite run — do NOT re-run with | tail)
- W7 grep (DelegationEscalation count): <output of `grep -c "DelegationEscalation(" packages/plugins/codex-collaboration/server/delegation_controller.py`>  (expect 2)
- W11 grep (old constant gone): <output of `grep -rn "_TASK_19_FINALIZER_GUARD_REASON" packages/plugins/codex-collaboration/tests/ | wc -l`>  (expect 0)
- W8 grep (_decided_request_ids): <output of `grep -c "_decided_request_ids" packages/plugins/codex-collaboration/server/delegation_controller.py`>  (expect 0)
- W9 grep (old wrapper-key): <output of `grep -c "resolution\.payload\.get" packages/plugins/codex-collaboration/server/delegation_controller.py`>  (expect 0)
- L8.1 audit (no pass-bodied unskips): <output of `grep -A8 "def test_happy_path_decide_approve_success\|def test_timeout_cancel_dispatch" packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py | grep -c "^[[:space:]]*pass$"`>  (expect 0 — NOTE: `-A8` window is required because docstrings sit between `def` and `pass`; `-A2` is a false negative against the current file layout)
- F16.1 skip count: <output of `grep -c "@pytest.mark.skip" packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py`>  (expect 0)
- G18.1 skip count: <output of `grep -rh -c "_TASK_19_FINALIZER_GUARD_REASON" packages/plugins/codex-collaboration/tests/test_delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py | paste -sd+ - | bc`>  (expect 0 — single scalar across both files)
- Deny assertion shape: <confirm `:1881` and `:934` assert job.status == "completed", NOT "failed">
- L11-T5 coverage: <confirm both resolved AND canceled snapshots tested for D4 suppression>
- L9 anomalous-pending: <confirm L2-specific warning substring, NOT generic warning assertion>
- Full-suite hang verification: full-suite wall-clock <Xs>
- Lock conformance: L1=✓, L2=✓, L3=✓, L4=✓, L5=✓, L6=✓, L7=✓, L8=✓, L9=✓, L10=✓, L11=✓
- Watchpoint conformance: W1=✓, W2=✓, W3=✓, W4=✓, W5=✓, W6=✓, W7=✓, W8=✓, W9=✓, W10=✓, W11=✓, W12=✓
- Notes: <any judgment calls>
```

If any lock turns out unreachable, report **BLOCKED**:

```
BLOCKED
- Lock that cannot be honored: L<N> (or W<N>)
- Live observation: <what you found at file:line>
- Question for controller: <specific yes/no or pick-one question>
```

**DO NOT report DONE_WITH_CONCERNS + unilateral decision** — BLOCKED + question is preferred; controller adjudicates.

### Boundaries — what NOT to do

- **NO `decide()` body edits** (W1).
- **NO `start()` body edits** (W2).
- **NO edits to the non-escalation tail sequencing** (W3 — `:2424-2429` byte-identical).
- **NO edits to the no-capture branch** (W4 — `:2431-2445` byte-identical).
- **NO modification of the L11 unknown-kind carve-out ordering** (W5 — `interrupted_by_unknown → "unknown"` must remain FIRST in the kind-based fall-through).
- **NO modification of the escalation audit emission shape** (W6 — `AuditEvent(...)` at `:2395-2407`).
- **NO modification of `DelegationEscalation(` count** (W7 — must remain 2).
- **NO unilateral scope expansion to poll/discard/contracts** (L10 — Task 20/21/22).
- **NO `runtime.py` touches** (RT.1 out of scope).
- **NO `_FakeControlPlane` Pyright "fixes"** (TT.1 out of scope).
- **NO use of fictional plan-pseudocode fixtures** — use `_build_controller(tmp_path)` per Task 14/15/16/17/18 precedent.
- **NO `pass`-bodied tests committed** (L8.1).
- **NO blanket migrations or scope expansion.** If you notice an unrelated improvement, mention it briefly; do NOT silently fix.

### Mid-task questions

If you encounter a structural gap or unreachable lock, **stop and report BLOCKED + question**. The controller adjudicates within the convergence map's authority order:

1. Spec §`_finalize_turn` Terminal Guard (`design.md:1738-1827`)
2. Spec §Unknown-kind contract (`design.md:1705-1736`)
3. Carry-forward state (G18.1, F16.1, TT.1, RT.1)
4. Live code at HEAD `844e6f97`
5. Phase H plan body (`phase-h-finalizer-consumers-contracts.md`) — informative only

### Begin

Read the six authority sources in order, then begin with the L11 direct-guard tests + L9 warning tests (TDD — tests first). Proceed to the `_finalize_turn` rewrite (L1-L4), then the G18.1/F16.1 unskips with concrete bodies. Run the full-suite hang-verification protocol (`uv run --package codex-collaboration pytest -v 2>&1 | tee /tmp/task19-suite.txt`) and verify all acceptance criteria BEFORE committing the feat. Then commit and report DONE or BLOCKED per the contract above.

---

## Post-implementer review chain (controller-driven, not implementer-driven)

After the implementer reports DONE on the feat commit, the controller dispatches sequentially:

1. **Spec compliance reviewer** (`general-purpose`, sonnet): "Verify Task 19 commit `<sha>` honors L1-L11 + W1-W12 against `task-19-convergence-map.md` + spec §1738-1827 + §1705-1736. Pay special attention to: L3 terminal mapping (all 4 rows); L2 D4 suppression (resolved AND canceled); L9 anomalous-pending test uses L2-specific substring, NOT generic warning; L11-T5 covers BOTH resolved AND canceled; L11-T7b proves derivation ignores D4 write; deny assertions use `completed` not `failed`; `:1525` injection targets `lineage_store.update_status` NOT `_emit_terminal_outcome_if_needed`. Report findings as Critical/Important/Minor."

2. **Code-quality reviewer** (`pr-review-toolkit:code-reviewer` if available, else `general-purpose` sonnet): "Review Task 19 commit `<sha>` for code quality. Focus on: the L1 snapshot-read placement relative to D6; the L3 branching structure (dispatch-clarity split vs collapsed form); the L2 warning messages (distinct substrings for anomalous-pending vs tombstone); the F16.1 side-effect uniqueness assertions (non-deduped signals as load-bearing); the `_CountingPendingRequestStore` proxy design for L11-T7; the `:1525` failure-injection mechanism (one-shot raise on `lineage_store.update_status`)."

3. **Closeout-fix dispatch (if needed):** controller continues the `task-19-implementer` agent via `SendMessage({to: "task-19-implementer", message: <consolidated review findings>})`.

4. **Closeout-docs commit (mandatory):** controller continues the implementer to write carry-forward updates + Phase H plan anchor refresh + convergence map addenda.

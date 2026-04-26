# Task 17 Dispatch Packet — T-20260423-02 (Phase G first task)

**Drafted:** 2026-04-26 (fresh-session dispatch construction; convergence map at `task-17-convergence-map.md` is binding authority).

**Workflow:** `superpowers:subagent-driven-development` — single fresh implementer (sonnet, `general-purpose`) + spec reviewer + code-quality reviewer (sequential, NOT parallel). Per Task 16 D5/G32, agent named explicitly for SendMessage continuity (closeout-fix + closeout-docs continue the same agent).

**Agent dispatch (controller invokes this after user approves the packet):**

```python
Agent({
  name: "task-17-implementer",
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Phase G Task 17 start() rewrite",
  prompt: <<everything in §"Implementer Prompt" below>>
})
```

---

## Implementer Prompt

You are the Task 17 implementer for T-20260423-02 Packet 1 (Deferred-Approval Response). You are dispatched into the existing `feature/delegate-deferred-approval-response` branch at base commit `f3cfa61a` (`docs(delegate): record Phase F Task 16 closeout (T-20260423-02)`). Phase F is complete (Tasks 6-16 landed). Task 17 is the FIRST task of Phase G and rewrites the public `start()` API for the async-decide model. Task 18 (`decide()` rewrite) is queued behind you and is OUT OF YOUR SCOPE.

### Mission

Rewrite `DelegationController.start` at `delegation_controller.py:386` for the capture-ready handshake. Replace the synchronous `_execute_live_turn(...)` call inside `start()` (live anchor `:737`) with: `spawn_worker(...)` + `self._registry.wait_for_parked(job_id, timeout_seconds=START_OUTCOME_WAIT_SECONDS)` + dispatch through a new `_dispatch_parked_capture_outcome(...)` helper that exhaustively `match`-es all 5 `ParkedCaptureResult` variants. Land 8 new acceptance tests in `test_delegate_start_async_integration.py`. Remove 24 Bucket A skip decorators (18 constant-backed + 6 callsite-specific). Rename the `_TASK_17_DEADLOCK_REASON` constant in BOTH test files to `_TASK_18_DECIDE_SIGNAL_REASON` with rewritten reason text. Carry-forward consequences: F16.2 splits (Bucket A closes; Bucket B → new G17.1), Mode A partial closure (3 of 6), Mode B full closure, L10 closure, RT.1 added.

### Authority sources (READ IN THIS ORDER)

**Pre-read guard:** All three files below MUST be readable from the current working tree (`/Users/jp/Projects/active/claude-code-tool-dev`). If `Read` fails on any of them with file-not-found or permission error, **stop and report BLOCKED** with the failing path — do NOT improvise from training knowledge or partial context. The convergence map is the binding dispatch authority; without it, you have no scope.

1. **Convergence map (BINDING):** `docs/plans/2026-04-24-packet-1-deferred-approval-response/task-17-convergence-map.md` (~330 lines). This is the dispatch authority. It contains:
   - **Live anchors table** (~28 rows; verified at HEAD `f3cfa61a`). Plan-cited line numbers throughout `phase-g-public-api.md` Task 17 body are stale (esp. plan's "around `:608-625`" for `start()` — live anchor is `:386`). Use this table for any line-number lookup.
   - **Locks L1-L10** (binding positive scope; mandatory things)
   - **Watchpoints W1-W13** (binding negative scope; forbidden things)
   - **5-variant branch matrix** (the central artifact for this task — `Parked` / `TurnCompletedWithoutCapture` / `TurnTerminalWithoutEscalation` / `WorkerFailed` / `StartWaitElapsed`)
   - **Per-test triage table** (35 Task-17-cited skips split as 24 Bucket A + 11 Bucket B; plus 8 new acceptance tests; plus 2 F16.1 untouched)
   - **Out-of-scope table** with plan/spec citations
   - **Acceptance criteria** (split: Code + Tests + Closeout-docs)
   - **Pre-dispatch checklist** (ignore — that's the controller's; you focus on Acceptance criteria)

2. **Spec — Capture-ready handshake:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:659-910`. The full async-decide handshake protocol: spawn_worker, wait_for_parked, the 5 ParkedCaptureResult variants and what each means, the invariant-violation handling for `Parked`-with-bad-projection (signal_internal_abort + raise).

3. **Spec — DelegationStartError reasons:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:622-657`. The canonical reason strings for `DelegationStartError`. Two relevant for Task 17: `parked_projection_invariant_violation`, `worker_failed_before_capture`. Plus reason-preservation rule for worker-emitted DelegationStartError (e.g., `unknown_kind_interrupt_transport_failure`).

4. **Plan body — Task 17:** `docs/plans/2026-04-24-packet-1-deferred-approval-response/phase-g-public-api.md:11-286`. Steps 17.1-17.5 with full pseudocode for the `start()` rewrite + `_dispatch_parked_capture_outcome` helper. **Treat the pseudocode as faithful template, but apply the corrections in §"Plan-pseudocode known issues" below — the plan pseudocode contains stale line numbers and one fictional-fixture pattern.**

### CRITICAL: L4 EXHAUSTIVE MATCH (highest-leverage implementer mistake to prevent)

`_dispatch_parked_capture_outcome` MUST use an exhaustive `match` over all 5 `ParkedCaptureResult` variants with `assert_never` as the final arm. NO silent `case _:` fall-through. Skeleton:

```python
from typing import assert_never  # Add this import (verify not already present at :64 area)

def _dispatch_parked_capture_outcome(
    self,
    *,
    outcome: ParkedCaptureResult,
    job_id: str,
    collaboration_id: str,
) -> DelegationJob | DelegationEscalation:
    match outcome:
        case Parked(request_id=request_id):
            # ORDER MATTERS: live `_project_pending_escalation(self, job: DelegationJob)`
            # at delegation_controller.py:1581-1583 takes the JOB, not the request_id.
            # Mirror the existing poll() callsite pattern at :1660-1663:
            #   1. Look up job from store; assert non-None (registry invariant).
            #   2. Call _project_pending_escalation(job) inside narrow try/except.
            #   3. On UnknownKindInEscalationProjection → signal_internal_abort + raise.
            #   4. On None return → signal_internal_abort + raise (also invariant violation here).
            #   5. On valid view → return DelegationEscalation.
            job = self._job_store.get(job_id)
            assert job is not None  # registry invariant: Parked implies job exists
            try:
                pending_escalation = self._project_pending_escalation(job)
            except UnknownKindInEscalationProjection:
                # NARROW catch — `UnknownKindInEscalationProjection` is the SPECIFIC
                # exception the helper docstring (delegation_controller.py:1587-1593)
                # promises to re-raise for invariant violations. Catching bare
                # `Exception` here would mask unrelated implementation bugs (store
                # bugs, assertion failures, KeyboardInterrupt sub-types) as a
                # protocol-invariant violation AND wake the worker with a
                # misleading internal-abort reason. Per project tenet
                # "Explicit over Silent" — let unrelated exceptions propagate.
                self._registry.signal_internal_abort(
                    request_id, reason="parked_projection_invariant_violation"
                )
                raise DelegationStartError(
                    reason="parked_projection_invariant_violation", cause=None
                )
            if pending_escalation is None:
                # The worker just announced Parked, so the job's status should be
                # alive AND parked_request_id should be set. A None return from
                # _project_pending_escalation here means the projection's "legitimate
                # no-view states" (terminal status / unparked / tombstone) were hit
                # WHEN they shouldn't have been — i.e., a state-machine invariant
                # violation between the worker thread's announce_parked and the
                # main thread's wait_for_parked return. Same broad reason per
                # spec §Capture-ready handshake.
                self._registry.signal_internal_abort(
                    request_id, reason="parked_projection_invariant_violation"
                )
                raise DelegationStartError(
                    reason="parked_projection_invariant_violation", cause=None
                )
            return DelegationEscalation(job, pending_escalation, agent_context=None)

        case TurnCompletedWithoutCapture():
            job = self._job_store.get(job_id)
            assert job is not None
            return job

        case TurnTerminalWithoutEscalation(job_status=_, reason=_, request_id=_):
            job = self._job_store.get(job_id)
            assert job is not None
            return job

        case WorkerFailed(error=exc):
            # L7 reason-preservation
            if isinstance(exc, DelegationStartError) and exc.reason:
                raise exc
            raise DelegationStartError(reason="worker_failed_before_capture", cause=exc)

        case StartWaitElapsed():
            logger.warning(
                "delegation.start: start-wait budget elapsed; returning running job",
                extra={"job_id": job_id, "collaboration_id": collaboration_id},
            )
            job = self._job_store.get(job_id)
            assert job is not None
            return job

        case _:
            assert_never(outcome)
```

**Why exhaustiveness matters (W11):** if `ParkedCaptureResult` is ever extended (e.g., a future `WorkerCanceled` variant), missing a case becomes BOTH a Pyright error AND a runtime exception, not a silent dispatch hole. Without `assert_never`, Pyright cannot enforce exhaustiveness on the union.

### CRITICAL: L8 SIGNAL-THEN-RAISE invariant-violation pattern

For the `Parked` arm's two invariant-violation sub-cases (projection raises OR returns `None`), you MUST call `self._registry.signal_internal_abort(request_id, reason="parked_projection_invariant_violation")` BEFORE raising on the main thread. Why: the worker is currently parked inside `registry.wait(...)` waiting for a signal. If the main thread raises without signaling, the worker thread leaks indefinitely. The signal wakes the worker with `InternalAbort`, which routes through Task 16's internal-abort sentinel branch (`record_internal_abort` + sentinel raise + `_finalize_turn` cleanup).

Both sub-cases use the SAME broad reason string `parked_projection_invariant_violation` per spec §Capture-ready handshake.

### CRITICAL: L6 CONSTANT RENAME (test-side)

Both test files contain a constant named `_TASK_17_DEADLOCK_REASON` whose reason text says Task 17 fixes the deadlock:

- `packages/plugins/codex-collaboration/tests/test_delegation_controller.py:43-50`
- `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py:31-38`

You MUST rename to `_TASK_18_DECIDE_SIGNAL_REASON` in both files AND rewrite the reason text to:

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

The 11 Bucket B decorators all retain their `@pytest.mark.skip(...)` and all end with `reason=_TASK_18_DECIDE_SIGNAL_REASON` after Task 17, but they reach that post-state via TWO distinct mechanical operations — DO NOT assume a constant-rename-only pass is sufficient:

- **8 constant-backed Bucket B decorators** (currently `reason=_TASK_17_DEADLOCK_REASON` — split as 6 F16.2 decide-mechanism decorators in `test_delegation_controller.py` at `:1716`, `:1814`, `:1860`, `:2162`, `:2464`, `:2516` + 2 F16.2 decide-E2E decorators in `test_delegate_start_integration.py` at `:869`, `:946`): updated automatically by renaming the shared constant in each file. No per-decorator edits required. NOTE: the `decide_rejects_*` and `start_*` decorators are Bucket A REMOVALS, not Bucket B retentions — do not confuse the two.
- **3 callsite-specific Mode A Bucket B decorators** at `test_delegation_controller.py:1761`, `test_delegation_controller.py:2406`, and `test_delegate_start_integration.py:1077`: currently carry hand-written callsite-specific reason strings (NOT the shared constant). These MUST be EXPLICITLY rewritten to `reason=_TASK_18_DECIDE_SIGNAL_REASON`. A pure constant-rename pass will leave them stale and the 11-retention audit (Tests acceptance § "11 Bucket B decorators retained") will fail with 8 matches instead of 11.

Audit-discipline framing matters: a Bucket B test might mechanically pass under legacy `decide()` (e.g., deny local-finalization), but that's coincidental green for the wrong code path, not Task 17 acceptance evidence.

### CRITICAL: W4 NO FICTIONAL FIXTURES

Plan Step 17.1's failing-test stubs reference fixtures that DO NOT exist:

- `delegation_controller_fixture` — does NOT exist
- `app_server_runtime_stub` — does NOT exist
- `journal_spy` — does NOT exist
- `audit_event_spy` — does NOT exist

The integration-test fixture surface in `tests/conftest.py` is intentionally minimal (only `vendored_schema_dir`, `client_request_schema`, `make_test_handle` are real). Per Task 14 W4 / Task 15 L8 / Task 16 W4 precedent, use:

- `_build_controller(tmp_path)` — module-local helper, importable from `tests.test_delegation_controller`. Read `tests/test_delegation_controller.py` to see the helper's call signature and what it returns.
- Built-in pytest fixtures: `monkeypatch`, `tmp_path`, `caplog`.
- `unittest.mock.MagicMock` / `create_autospec` for narrow stubs (e.g., faking `_project_pending_escalation` behavior, injecting `wait_for_parked` return values).

You MUST replace EVERY `pass` body in plan stubs with real assertion shapes (W12). Do NOT commit `pass`-bodied tests as Task 17 acceptance evidence.

### CRITICAL: W5 HANG-VERIFICATION protocol

The 24 newly-unskipped Bucket A tests intentionally leave parked workers blocked in `registry.wait()` after the test asserts. This is the real post-Task-17 hang/resource risk — NOT the still-skipped 11 Bucket B tests (which don't execute). Mitigation is already in place: `worker_runner.py:113` sets `daemon=True` on the worker thread, and `resolution_registry.py:202-206` sets `daemon=True` on per-request timer threads, so no thread blocks process exit.

After your feat commit lands, run the W5 verification protocol:

1. **Full suite:** `uv run --package codex-collaboration pytest -v` — must complete in normal wall-clock time (~30-40s; Task 16 baseline was 38s for 968 tests). Exit code 0; no SIGTERM/timeout messages.

2. **Order-independence smoke** (two explicit orderings from repo root, both must yield exit code 0 with identical pass/skip counts):

   ```bash
   uv run --package codex-collaboration pytest \
     packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
     packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
   uv run --package codex-collaboration pytest \
     packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py \
     packages/plugins/codex-collaboration/tests/test_delegation_controller.py
   ```

   This is NOT a `pytest-randomly` shuffle (the project doesn't depend on it); two explicit orderings are the lightweight stand-in. If hangs OR contamination appear, the most likely failure mode is bucket misclassification (some Bucket A test actually needs Task 18) — flag and report.

### Plan-pseudocode known issues

Five known stale or ambiguous spots in `phase-g-public-api.md`:

1. **Stale `start()` line number:** plan cites "around `:608-625`"; live anchor is `:386`. Use the convergence map's live-anchors table.
2. **Imports gap:** plan doesn't anchor the imports change. The existing line at `delegation_controller.py:102` is `from .resolution_registry import DecisionResolution, InternalAbort, ResolutionRegistry`. EXTEND this line; do NOT add a duplicate `from .resolution_registry import ...`. Add 6 new names: `Parked, ParkedCaptureResult, StartWaitElapsed, TurnCompletedWithoutCapture, TurnTerminalWithoutEscalation, WorkerFailed`.
3. **`from .worker_runner import spawn_worker`:** not currently imported (per Task 16 closeout). Add at module level (do NOT lazy-import inside `start()`). No real cycle: live `worker_runner.py` only imports `DelegationController` under `TYPE_CHECKING`.
4. **`START_OUTCOME_WAIT_SECONDS = 30`:** add as module-level constant near `_APPROVAL_OPERATOR_WINDOW_SECONDS = 900` at `:107`. Type annotation `float`. No env-var override under Task 17 (deferred polish).
5. **Fictional fixtures in plan Step 17.1 stubs:** see "CRITICAL: W4 NO FICTIONAL FIXTURES" above.

### Code acceptance summary (full list in convergence map "Acceptance criteria → Code")

- [ ] `start()` rewritten at `delegation_controller.py:386` per L2 — replace the synchronous `_execute_live_turn(...)` call at `:737` with `spawn_worker(...)` + `self._registry.wait_for_parked(job_id, timeout_seconds=START_OUTCOME_WAIT_SECONDS)` + `_dispatch_parked_capture_outcome(...)`.
- [ ] `_dispatch_parked_capture_outcome(*, outcome, job_id, collaboration_id) -> DelegationJob | DelegationEscalation` helper added with exhaustive 5-variant `match` per L4 + `case _: assert_never(outcome)` final arm (W11).
- [ ] `START_OUTCOME_WAIT_SECONDS: float = 30` module constant near `:107` (L3).
- [ ] 6 new imports from `.resolution_registry` extending `:102`: `Parked, ParkedCaptureResult, StartWaitElapsed, TurnCompletedWithoutCapture, TurnTerminalWithoutEscalation, WorkerFailed` (L5).
- [ ] `from .worker_runner import spawn_worker` added (L5).
- [ ] `from typing import assert_never` added if not already present.
- [ ] **W3 invariant:** `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `6` (count must NOT change from Task 16).
- [ ] **L7 reason-preservation:** `WorkerFailed` arm preserves `DelegationStartError.reason` from worker — when isinstance check matches, re-raise the original; otherwise wrap in `DelegationStartError(reason="worker_failed_before_capture", cause=exc)`.
- [ ] **L8 signal-then-raise:** both `Parked` invariant-violation sub-cases (projection-null and projection-raise) call `signal_internal_abort` BEFORE raising.
- [ ] No edits to `decide()` body (W1), `_finalize_turn` body (W2), the 6 sentinel raise sites or their reasons (W3), `_execute_live_turn` callsite at `:2484` (W1), `runtime.py` (W10), or the legacy `DelegationEscalation` construction site at `:2240` (W13).
- [ ] No re-import of `cast`, `EscalatableRequestKind`, `ResolutionRegistry`, `DecisionResolution`, `InternalAbort` (W6).

### Tests acceptance summary

- [ ] New file `packages/plugins/codex-collaboration/tests/test_delegate_start_async_integration.py` with 8 acceptance tests per the per-test triage table (covers all 5 ParkedCaptureResult variants + 2 invariant-violation sub-cases + 1 reason-preservation).
- [ ] No `pass`-bodied tests committed (W12 — replace plan stubs with real assertions; module-local helpers per W4).
- [ ] **24 Bucket A decorators removed** per L10 (18 constant-backed + 6 callsite-specific). Two audits — both must pass:

  **Audit A (old-constant-fully-gone):**
  ```bash
  grep -rn "_TASK_17_DEADLOCK_REASON" packages/plugins/codex-collaboration/tests/
  ```
  Expected: **0 matches** (constant fully renamed in both files; no straggler references).

  **Audit B (callsite-specific Bucket A reasons gone):** verify the 6 callsite-specific decorators are removed by spot-checking the per-test triage table's listed line numbers — the lines may have shifted slightly due to file edits, so locate by test-name proximity:
  - `test_delegation_controller.py`: removed at `test_start_with_unknown_request_interrupts_and_escalates`, `test_start_with_unparseable_request_creates_minimal_causal_record`, `test_poll_needs_escalation_projects_pending_request_without_raw_ids` (3)
  - `test_delegate_start_integration.py`: removed at `test_e2e_unknown_request_kind_interrupts_and_escalates`, `test_delegate_poll_needs_escalation_returns_projected_request` (2)
  - `test_handler_branches_integration.py`: removed at `test_unknown_kind_parse_failure_terminalizes_unknown` (1)

  None of these 6 should have any `@pytest.mark.skip` decorator after Task 17. (F16.1 decorators at `test_handler_branches_integration.py:161, 179` are SEPARATE — see W8; do NOT touch those.)
- [ ] `_TASK_17_DEADLOCK_REASON` renamed to `_TASK_18_DECIDE_SIGNAL_REASON` in BOTH `test_delegation_controller.py:43` and `test_delegate_start_integration.py:31` per L6.
- [ ] Constant text rewritten per L6 (cite Task 18's `reserve()` + `commit_signal()` mechanism + the audit-discipline framing — exact text in §"CRITICAL: L6" above).
- [ ] **11 Bucket B decorators retained**, all using the new constant name. Audit:
  ```bash
  grep -rn "@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)" packages/plugins/codex-collaboration/tests/
  ```
  Expected: **11 matches** total (8 in `test_delegation_controller.py` + 3 in `test_delegate_start_integration.py`). Plus 2 constant-definition lines (one per file) — these will appear in a separate `grep "_TASK_18_DECIDE_SIGNAL_REASON"` count, expected at 13 total references (11 decorators + 2 defs).
- [ ] F16.1 decorators at `test_handler_branches_integration.py:161, 179` UNTOUCHED (W8).
- [ ] **Suite expectation:** `968 → 968 + 8 (new) + 24 (unskipped) = 1000 passing`; `13 skipped` (11 Bucket B citing Task 18 + 2 F16.1 citing Task 19); `0 failed`.
- [ ] **W5 hang verification:** full suite + two-ordering smoke per the W5 protocol above.
- [ ] Lint: `uv run --package codex-collaboration ruff check packages/plugins/codex-collaboration/server/ packages/plugins/codex-collaboration/tests/` — no new findings relative to baseline `f3cfa61a`.
- [ ] Pyright: no new diagnostics on touched files. The pre-existing `runtime.py:270` TurnStatus literal narrowing error is OUT OF SCOPE (W10) — do NOT touch `runtime.py`.

### Closeout-docs acceptance summary (the third commit)

- [ ] `carry-forward.md` F16.2 split (covers ONLY the original 26-test F16.2 surface — NOT the full 35-test Task-17-cited dispatch surface): **18 F16.2 Bucket A items closed by Task 17** (11 start-flow + 7 decide-rejects); **8 F16.2 Bucket B items moved to a new `G17.1`** entry with the 8-test list + revised mechanism citation. The remaining cross-cutting items in the 35-test surface — 6 Bucket A items (3 Mode A + 2 Mode B + 1 L10) and 3 Bucket B items (3 Mode A defer) — are tracked under their own carry-forward rows.
- [ ] `carry-forward.md` Mode A/B from Task 14 closeout: partial closure annotation. **Mode A** (6 total): 3 close in Bucket A (`test_delegation_controller.py:1377`, `:1436`; `test_delegate_start_integration.py:628`); 3 defer to Task 18 (`test_delegation_controller.py:1761`, `:2406`; `test_delegate_start_integration.py:1077`). **Mode B** (2 total): both close in Bucket A (`test_delegation_controller.py:2626`; `test_delegate_start_integration.py:805`).
- [ ] `carry-forward.md` L10 barrier from Task 16 closeout: closed (single decorator at `test_handler_branches_integration.py:539` removed in Bucket A).
- [ ] L9 stop-rule from Task 16 carry-forward: F16.1 unchanged (Phase H Task 19 still owner).
- [ ] New carry-forward item `RT.1` added: `runtime.py:270` Pyright TurnStatus literal narrowing error (pre-existing per Task 16 G34; not introduced by Task 17). Closes at end-of-Phase-G or end-of-Packet-1 typing polish.
- [ ] Closeout-docs entry per Phase E/F precedent: landed-code summary, Bucket A closures (24 = 18 F16.2 + 3 Mode A + 2 Mode B + 1 L10), Bucket B carry-forward (8 F16.2 → G17.1; 3 Mode A → Mode A row defer), full L1-L10 + W1-W13 lock conformance summary, branch-matrix-with-test-coverage note, hang-verification result.

### Commit shape (anticipated 1+1+1)

| Step | Type | Subject |
|------|------|---------|
| 1 | feat | `feat(delegate): rewrite start() with capture-ready handshake (T-20260423-02 Task 17)` |
| 2 (anticipated) | fix | `fix(delegate): address Task 17 closeout review (T-20260423-02 Task 17 closeout)` |
| 3 (mandatory) | docs | `docs(delegate): record Phase G Task 17 closeout (T-20260423-02)` |

Stage specific files only (never `git add -A` / `git add .`). Co-author trailer: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`. Do NOT amend; do NOT skip pre-commit hooks.

### Reporting contract

When the feat commit lands, report **DONE** with:

```
DONE
- Commit SHA: <sha of feat commit>
- Suite: <output of `uv run --package codex-collaboration pytest 2>&1 | tail -5`>
- W3 grep: <output of `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l`>  (expect 6)
- Bucket A removal audit (old constant fully gone): <output of `grep -rn "_TASK_17_DEADLOCK_REASON" packages/plugins/codex-collaboration/tests/ | wc -l`>  (expect 0)
- Bucket B retention audit (decorators with new constant): <output of `grep -rn "@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)" packages/plugins/codex-collaboration/tests/ | wc -l`>  (expect 11)
- New-constant total references (sanity): <output of `grep -rn "_TASK_18_DECIDE_SIGNAL_REASON" packages/plugins/codex-collaboration/tests/ | wc -l`>  (expect 13 = 11 decorators + 2 constant defs)
- W5 hang verification: full-suite wall-clock <Xs>, order-independence smoke <both pass identical counts? yes/no>
- Lock conformance summary: L1=✓, L2=✓, L3=✓, L4=✓, L5=✓, L6=✓, L7=✓, L8=✓, L9=✓, L10=<deferred to closeout-docs commit>
- Watchpoint conformance summary: W1=✓, W2=✓, ..., W13=✓
- Notes: <any judgment calls made within lock-bounds>
```

If any lock turns out unreachable (e.g., live code shape disagrees with convergence map's anchor table in a way that blocks the lock), report **BLOCKED** with a specific question:

```
BLOCKED
- Lock that cannot be honored: L<N>
- Live observation: <what you found at the file:line>
- Question for controller: <specific yes/no or pick-one question>
```

**DO NOT report DONE_WITH_CONCERNS + unilateral decision** (Task 14/15/16 process note: BLOCKED + question is preferred — controller adjudicates scope; implementer faithfully executes).

### Boundaries — what NOT to do

- **NO `decide()` rewrite** (W1 — Phase G Task 18 territory).
- **NO `_finalize_turn` edits** (W2 — Phase H Task 19 territory).
- **NO edits to the 6 sentinel raise sites or their reasons** (W3 — Task 16 W7 invariant; the 6 raises stay categorically clean).
- **NO edits to `_execute_live_turn` callsite at `:2484`** (W1 — that's the decide-resume callsite Task 18 owns).
- **NO touches to the legacy `DelegationEscalation` construction site at `:2240`** (W13 — stays in service for decide-resume flow until Task 18 retires it).
- **NO `runtime.py` touches** (W10 — pre-existing Pyright error is RT.1 carry-forward, not Task 17 scope).
- **NO `case _:` fall-through in the `match`** (W11 — must use `assert_never`).
- **NO use of fictional plan-pseudocode fixtures** (W4 — `delegation_controller_fixture` etc. don't exist).
- **NO un-skipping of F16.1 decorators at `test_handler_branches_integration.py:161, 179`** (W8 — Phase H Task 19 owns those).
- **NO un-skipping of Bucket B's 11 decorators** — only the constant rename + reason-text rewrite (W6 audit discipline).
- **NO contracts.md edits** (Phase H Task 22).
- **NO blanket migrations or scope expansion.** If you notice an unrelated improvement, mention it briefly in the report; do NOT silently fix.

### Mid-task questions

If you encounter a structural gap or a lock that turns out unreachable, **stop and report BLOCKED + question** — do NOT improvise. The controller will adjudicate within the convergence map's authority order:

1. Spec §Capture-ready handshake (`design.md:659-910`)
2. Spec §DelegationStartError reasons (`design.md:622-657`)
3. Phase G Task 17 plan (`phase-g-public-api.md:11-286`)
4. Phase G Task 18 plan body (`phase-g-public-api.md:290-536` — for boundary-clarification only; you do NOT implement Task 18)
5. Carry-forward F16.2 + Mode A/B + L10
6. Live code at HEAD `f3cfa61a`

When sources conflict, the higher-numbered authority defers to the lower (spec wins over plan; plan wins over carry-forward; live code is bedrock).

### Begin

Read the four authority sources in order, then begin Step 17.1 (write the new failing-test file `test_delegate_start_async_integration.py` with 8 acceptance tests per the convergence map's per-test triage). Proceed through Steps 17.2-17.5 per the plan body, applying the L4/L8/W4/W11 corrections above. Commit the feat. Run the W5 hang-verification protocol. Report DONE or BLOCKED per the contract above.

---

## Post-implementer review chain (controller-driven, not implementer-driven)

After the implementer reports DONE on the feat commit, the controller dispatches:

1. **Spec compliance reviewer** (`general-purpose`, sonnet): "Verify Task 17 commit `<sha>` honors L1-L10 + W1-W13 against `task-17-convergence-map.md` + spec §659-910 + plan §11-286. Report findings as Critical/Important/Minor."

2. **Code-quality reviewer** (`pr-review-toolkit:code-reviewer` if available, else `general-purpose` sonnet): "Review Task 17 commit `<sha>` for code quality. Focus on the `_dispatch_parked_capture_outcome` exhaustive `match`, the L7 reason-preservation isinstance check, the L8 signal-then-raise sequence, and the new test harness pattern."

3. **Closeout-fix dispatch (if needed):** controller continues the `task-17-implementer` agent via `SendMessage({to: "task-17-implementer", message: <consolidated review findings + adjudications>})` — do NOT spawn a new implementer for the closeout-fix.

4. **Closeout-docs commit (mandatory):** controller continues the implementer to write the `carry-forward.md` updates (F16.2 split + Mode A/B partial + L10 closure + RT.1 add + G17.1 add) + Phase G Task 17 closeout entry per the closeout-docs acceptance summary above.

Sequential, not parallel. User adjudicates between rounds.

# Task 16 Dispatch Packet — T-20260423-02 (Phase F final task)

**Drafted:** 2026-04-25 (fresh-session dispatch construction; convergence map at `task-16-convergence-map.md` is binding authority).

**Workflow:** `superpowers:subagent-driven-development` — single fresh implementer (sonnet, `general-purpose`) + spec reviewer + code-quality reviewer (sequential, NOT parallel). Per Task 15 D5/R3, agent named explicitly for SendMessage continuity.

**Agent dispatch (controller invokes this after user approves the packet):**

```python
Agent({
  name: "task-16-implementer",
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Phase F Task 16 handler rewrite",
  prompt: <<everything in §"Implementer Prompt" below>>
})
```

---

## Implementer Prompt

You are the Task 16 implementer for T-20260423-02 Packet 1 (Deferred-Approval Response). You are dispatched into the existing `feature/delegate-deferred-approval-response` branch at base commit `475d0506` (`docs(delegate): correct stale worker_runner.py line count in Task 15 closeout`). Phase F Task 15 is complete. Task 16 is the LARGEST task in the plan and the final task of Phase F.

### Mission

Rewrite `_server_request_handler` inside `_execute_live_turn` for the async-decide model. Land all 6 production sentinel raise sites + 3 new helpers (`_handle_timeout_wake`, `_write_completion_and_audit_timeout`, `_repo_root_for_journal`) + registry initialization + module-level constant + 8 `update_parked_request` callsites + 4 `completion_origin="worker_completed"` writes. Carry-forward consequences: A2 closes by raise-site comments, C10.4 closes by 4 worker-completed writes, A3 audited and closed (or flagged) per L11.

### Authority sources (READ IN THIS ORDER)

**Pre-read guard:** All three files below MUST be readable from the current working tree (`/Users/jp/Projects/active/claude-code-tool-dev`). If `Read` fails on any of them with file-not-found or permission error, **stop and report BLOCKED** with the failing path — do NOT improvise from training knowledge or partial context. The convergence map is the binding dispatch authority; without it, you have no scope.

1. **Convergence map (BINDING):** `docs/plans/2026-04-24-packet-1-deferred-approval-response/task-16-convergence-map.md` (264 lines). This is the dispatch authority. It contains:
   - **Live anchors table** (28 rows; grep-verified at HEAD `475d0506`). Plan-cited line numbers throughout `phase-f-worker.md` are stale (Task 15 added ~+27 lines; Tasks 6-14 added more). Use this table for any line-number lookup.
   - **Locks L1-L11** (binding positive scope; mandatory things)
   - **Watchpoints W1-W13** (binding negative scope; forbidden things)
   - **8-row branch matrix** (the central artifact for this task; rows 1-2 are finalizer-routed, rows 3-8 are sentinel-bypass)
   - **Per-test triage table** (9 plan integration tests: 7 to write + 2 to skip with citations; 5 helper unit tests suggested; 8 Task 14 skips to keep)
   - **Out-of-scope table** with plan-line citations
   - **Acceptance criteria** (split: Code + Tests + Closeout-docs)
   - **Pre-dispatch checklist** (ignore — that's the controller's; you focus on Acceptance criteria)

2. **Spec — sentinel section:** `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:450-558`. The 6-row sentinel reason table, the catch-site code template, the `_finalize_turn` bypass rationale, the per-site invariant checklist (decide whether to write `record_*` mutator + journal entry + `update_parked_request(None)` + `registry.discard` + cleanup helper at each raise site).

3. **Plan body — Task 16:** `docs/plans/2026-04-24-packet-1-deferred-approval-response/phase-f-worker.md:377-1189`. Steps 16.1-16.7 with full pseudocode for the handler rewrite + helpers + registry init. **Treat the pseudocode as faithful template, but apply the L4 fix below — the plan pseudocode contains a known omission.**

### CRITICAL: L4 FIX (highest-leverage implementer mistake to prevent)

Plan pseudocode at `phase-f-worker.md:663-667` shows:

```python
registry.register(
    parsed.request_id,
    job_id=job_id,
    timeout_seconds=_APPROVAL_OPERATOR_WINDOW_SECONDS,
)
```

**This will raise `TypeError` at runtime.** The live API at `resolution_registry.py:173-180` requires `kind: EscalatableRequestKind` as a kw-only argument. **You MUST add it:**

```python
registry.register(
    parsed.request_id,
    job_id=job_id,
    kind=cast(EscalatableRequestKind, parsed.kind),
    timeout_seconds=_APPROVAL_OPERATOR_WINDOW_SECONDS,
)
```

`cast` is already imported at `delegation_controller.py:64`; `EscalatableRequestKind` is already imported at `:90`. **Do NOT re-add either import.** The cast is sound: this branch is only reached after `parsed.kind in _CANCEL_CAPABLE_KINDS or parsed.kind in _KNOWN_DENIAL_KINDS`, which is exactly the 3 `EscalatableRequestKind` literals (`command_approval`, `file_change`, `request_user_input`). Pyright cannot narrow string literals through frozenset membership; `cast` is the project-idiomatic resolution.

### CRITICAL: L9 STOP-RULE — Option (b) is LOCKED

Two of the 8 branches (decide-success at row 1, timeout-cancel-success at row 2) return `None` from the handler → turn proceeds → `_finalize_turn` runs. But `_finalize_turn`'s Captured-Request Terminal Guard rewrite is owned by **Phase H Task 19** (W1 watchpoint forbids you from touching it).

**Adjudication (binding):** You land the handler code at FULL scope — all 6 sentinel raise sites plus the 2 finalizer-routed return paths. You do NOT pull-forward any `_finalize_turn` rewrite into Task 16. The 2 finalizer-routed integration tests (`test_happy_path_decide_approve_success`, `test_timeout_cancel_dispatch_succeeded_for_file_change`) are SKIPPED with this exact citation:

```python
@pytest.mark.skip(reason="Phase H Task 19: requires Captured-Request Terminal Guard rewrite of _finalize_turn for finalizer-routed decide-success path. Worker writes record_response_dispatch + mark_resolved + completion_origin='worker_completed' at Task 16; finalizer projection that maps to DelegationJob.status='completed' lands at Task 19.")
```

(Adjust the second test's reason string for `record_timeout(succeeded) + completion_origin='worker_completed'` and `DelegationJob.status='canceled'` per per-test triage row 2 of the convergence map.)

The W7 invariant `0 → 6 sentinel raises` stays categorically clean: the 2 deferred tests are FINALIZER-coverage gaps, NOT sentinel-coverage gaps.

### Test harness — derive from `_build_controller(tmp_path)`

Use the module-local helper imported from `tests.test_delegation_controller` (per Task 14 W4 / Task 15 L8 precedent — verified pattern). Read `tests/test_delegation_controller.py` to see the helper's call signature and what it returns. Do NOT use any "fixture" name from the plan's placeholder integration tests at `phase-f-worker.md:405-549` (`delegation_controller_fixture`, `app_server_runtime_stub`) — these do NOT exist in `tests/conftest.py` (verified — only `vendored_schema_dir`, `client_request_schema`, `make_test_handle` are real).

For sentinel-bypass branch tests (rows 3-8), the recommended pattern is:
- `_build_controller(tmp_path)` to construct the controller and stores
- `create_autospec(ResolutionRegistry, instance=True)` from `unittest.mock`, injected via `monkeypatch.setattr(controller, "_registry", mock_registry)`. Use autospec, not plain `MagicMock(spec=...)`, because L4 is a signature bug: autospec will fail if `registry.register(...)` omits the required `kind=` kw-only argument.
- Configure `mock_registry.wait.return_value` to inject the resolution variant under test:
  - dispatch-failure: `DecisionResolution(payload={"resolution_action": "approve", "response_payload": {"decision": "accept"}}, kind="command_approval", is_timeout=False)`
  - timeout cancel branches: `DecisionResolution(payload={}, kind="command_approval", is_timeout=True)` or `kind="file_change"`
  - timeout interrupt branches: `DecisionResolution(payload={}, kind="request_user_input", is_timeout=True)`
  - internal-abort: `InternalAbort(reason=...)`
- For dispatch failures, attach transport mocks explicitly: `_FakeSession` currently defines `interrupt_turn` but not `respond`, so use `mock_session.respond = MagicMock(...)` / `mock_session.interrupt_turn = MagicMock(...)` before setting `side_effect` or assertions.
- Ensure the fake session actually invokes `server_request_handler` with the server-request message under test. The existing `_FakeSession.run_execution_turn` does this via its `_server_requests` list; if you drive `_execute_live_turn(...)` directly, manually register a runtime entry with a fake session configured the same way. Do not short-circuit by making `run_execution_turn` raise `_WorkerTerminalBranchSignal`; that only retests the Task 15 catch surface and skips the Task 16 handler logic.

You MAY collapse the 5 suggested helper unit tests into fewer if the coverage is preserved — exercise judgment.

### Code acceptance summary (full list in convergence map "Acceptance criteria → Code")

- [ ] `_server_request_handler` rewritten per plan Step 16.3 + L4 fix at `delegation_controller.py:765-835` (live anchor; plan cites stale `:650-720`)
- [ ] **W7 invariant:** `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns exactly `6`. The 6 reasons are: `internal_abort`, `dispatch_failed`, `timeout_interrupt_failed`, `timeout_interrupt_succeeded`, `timeout_cancel_dispatch_failed`, `unknown_kind_interrupt_transport_failure`.
- [ ] **L6 invariant:** `grep -n "self\\._job_store\\.update_parked_request" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns `8` (8 production callsites: 1 SET at capture + 7 CLEAR at terminal branches; avoids counting the `_WorkerTerminalBranchSignal` docstring reference at `delegation_controller.py:208`)
- [ ] **L7 invariant:** `grep -nF 'completion_origin="worker_completed"' packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l` returns exactly `4` (3 inline + 1 inside `_write_completion_and_audit_timeout` helper)
- [ ] `_handle_timeout_wake` method added per plan lines 875-1065 with **defensive `AssertionError` at the bottom (W9 — required, not optional)**
- [ ] `_write_completion_and_audit_timeout` method added per plan lines 1068-1106
- [ ] `_repo_root_for_journal(job_id)` one-line helper added per plan line 1109
- [ ] `self._registry: ResolutionRegistry = ResolutionRegistry()` set in `DelegationController.__init__`
- [ ] `_APPROVAL_OPERATOR_WINDOW_SECONDS = 900` module-level constant
- [ ] Each of the 6 raise sites has a comment that absorbs `_WorkerTerminalBranchSignal`'s class-level caller-contract docs (closes carry-forward A2 per L8). Reference which of the 4 cleanup obligations apply at each site per spec §549-557 invariant table — varies (e.g., the pre-capture `unknown_kind_interrupt_transport_failure` site has `n/a` for `update_parked_request` and `registry.discard`).
- [ ] **NO edits to `_finalize_turn` body** (W1), `_mark_execution_unknown_and_cleanup` body, the second `try/except Exception` at `:881-899`, or `_finalize_turn`'s local `_CANCEL_CAPABLE_KINDS` at `:1628` (W10).

### Tests acceptance summary

- [ ] New file `packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py` with **7 written + 2 skipped** tests per per-test triage in convergence map. The 2 skipped tests have explicit `Phase H Task 19: ...` citations (W12).
- [ ] **5 unit tests for new helpers** (or fewer if collapsed without losing coverage) per per-test triage.
- [ ] **All 8 Task 14 skip-decorators stay skipped** (W6 — both Mode A AND Mode B). Mode B's data dependency lands here, but the test EXECUTION shape requires Task 17.
- [ ] Suite expectation: `983 + N` passing (where N = new tests written) + `8 + 2 = 10` skipped (Task 14's 8 + Task 16's 2 finalizer-routed) + `0` failed.
- [ ] Lint: `uv run --package codex-collaboration ruff check packages/plugins/codex-collaboration/server/ packages/plugins/codex-collaboration/tests/` — no new findings relative to baseline `475d0506`.

### Closeout-docs acceptance summary (the third commit)

- [ ] `carry-forward.md`: A2 moved to Closed with Task 16 commit SHA(s); C10.4 moved to Closed with same.
- [ ] **L11 audit (do this BEFORE moving A3):** run `grep -n "cast(EscalatableRequestKind" packages/plugins/codex-collaboration/server/delegation_controller.py`. The expected result is at least one match inside `_project_request_to_view` (current location ~`:1012` post-Task-15). If found: move A3 to Closed with annotation `[Resolved 65f270ab — confirmed live at <line> in Task 16 closeout-docs audit pass]`. If NOT found: A3 stays Open and you flag in the closeout entry as a Task 14 closeout regression.
- [ ] New carry-forward item `F16.1` added to Open with this exact text: "Finalizer-routed integration test coverage (decide-success + timeout-cancel-success) — lands when Phase H Task 19 lands the Captured-Request Terminal Guard. The 2 deferred tests un-skip in same commit as Task 19's `_finalize_turn` rewrite."
- [ ] Closeout-docs entry follows Phase E/F precedent: landed-code summary, A2-closes-by-L8 + C10.4-closes-by-L7 + A3-audit-by-L11, full L1-L11 + W1-W13 lock conformance summary, branch-matrix-with-skip-citations note.

### Commit shape (anticipated 1+1+1)

| Step | Type | Subject |
|------|------|---------|
| 1 | feat | `feat(delegate): rewrite _server_request_handler for async-decide model + 6 sentinel raises (T-20260423-02 Task 16)` |
| 2 (anticipated) | fix | `fix(delegate): address Task 16 code-quality review (T-20260423-02 Task 16 closeout)` |
| 3 (mandatory) | docs | `docs(delegate): record Phase F Task 16 closeout (T-20260423-02)` |

Stage specific files only (never `git add -A` / `git add .`). Co-author trailer: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`. Do NOT amend; do NOT skip pre-commit hooks.

### Reporting contract

When the feat commit lands, report **DONE** with:

```
DONE
- Commit SHA: <sha of feat commit>
- Suite: <output of `uv run --package codex-collaboration pytest 2>&1 | tail -5`>
- W7 grep: <output of `grep -nF "_WorkerTerminalBranchSignal(reason=" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l`>  (expect 6)
- L6 grep: <output of `grep -n "self\\._job_store\\.update_parked_request" packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l`>  (expect 8)
- L7 grep: <output of `grep -nF 'completion_origin=\"worker_completed\"' packages/plugins/codex-collaboration/server/delegation_controller.py | wc -l`>  (expect 4)
- Lock conformance summary: L1=✓, L2=✓, ..., L11=<deferred to closeout-docs commit>
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

**DO NOT report DONE_WITH_CONCERNS + unilateral decision** (Task 14 process note: BLOCKED + question is preferred — controller adjudicates scope; implementer faithfully executes).

### Boundaries — what NOT to do

- **NO `_finalize_turn` edits** (W1 — Phase H Task 19 territory).
- **NO `start()` rewrite** (Task 17 — Phase G).
- **NO `decide()` rewrite** (Task 18 — Phase G).
- **NO `poll()` UnknownKindInEscalationProjection catch** (Task 20 — Phase H).
- **NO unblocking the 8 Task 14 skip-decorators** (W6 — both Mode A AND Mode B unblock at Task 17).
- **NO premature pull-forward of the Task 19 `_finalize_turn` guard** even if it would let the 2 finalizer-routed tests pass (W12).
- **NO consolidation of `_finalize_turn`'s `_CANCEL_CAPABLE_KINDS` at `:1628` with the handler's at `:757`** (W10 — Task 19 may consolidate; Task 16 must not).
- **NO contracts.md edits** (Phase H Task 22).
- **NO blanket migrations or scope expansion.** If you notice an unrelated improvement, mention it briefly in the report; do NOT silently fix.

### Mid-task questions

If you encounter a structural gap or a lock that turns out unreachable, **stop and report BLOCKED + question** — do NOT improvise. The controller will adjudicate within the convergence map's authority order:

1. Spec sentinel table + catch semantics (`design.md:474-558`)
2. Spec finalizer path table (`design.md:1790+`)
3. Phase F Task 16 plan (`phase-f-worker.md:377-1189`)
4. Phase H Task 19 finalizer guard plan (`phase-h-finalizer-consumers-contracts.md:11+`)
5. Carry-forward A2 + C10.4 + A3
6. Live code at HEAD `475d0506`

When sources conflict, the higher-numbered authority defers to the lower (spec wins over plan; plan wins over carry-forward; live code is bedrock).

### Begin

Read the three authority sources in order, then begin Step 16.1 (write the failing test file with 7 written + 2 skipped per the convergence map's per-test triage). Proceed through 16.2-16.7 per the plan body. Report DONE or BLOCKED per the contract above.

---

## Post-implementer review chain (controller-driven, not implementer-driven)

After the implementer reports DONE on the feat commit, the controller dispatches:

1. **Spec compliance reviewer** (`general-purpose`, sonnet): "Verify Task 16 commit `<sha>` honors L1-L11 + W1-W13 against `task-16-convergence-map.md` + spec §450-558 + plan §377-1189. Report findings as Critical/Important/Minor."

2. **Code-quality reviewer** (`pr-review-toolkit:code-reviewer` if available, else `general-purpose` sonnet): "Review Task 16 commit `<sha>` for code quality. Focus on the 3 new helpers, the 6 raise-site comments, the test harness pattern."

3. **Closeout-fix dispatch (if needed):** controller continues the `task-16-implementer` agent via `SendMessage({to: "task-16-implementer", message: <consolidated review findings + adjudications>})` — do NOT spawn a new implementer for the closeout-fix.

4. **Closeout-docs commit (mandatory):** controller continues the implementer to write the `carry-forward.md` updates + Phase F closeout entry per the closeout-docs acceptance summary above.

Sequential, not parallel. User adjudicates between rounds.

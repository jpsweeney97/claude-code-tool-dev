# T-20260423-01: Codex-collaboration delegate execution remediation

```yaml
id: T-20260423-01
date: 2026-04-23
status: open
priority: high
tags: [codex-collaboration, delegation, sandbox, approval, execution]
blocked_by: []
blocks: []
effort: medium
```

## Context

Live `/delegate` smoke during T-07 slice 7e (PR #123, commit `2255b066`)
confirmed that the delegation pipeline infrastructure works end-to-end: App
Server bootstraps, runtime ID is assigned, execution turns run, escalation
capture and storage work, and jobs reach terminal status with artifact hashes.
However, actual artifact-producing execution is blocked by two compounding
defects. The delegated agent cannot execute shell commands, and the approval
path cannot grant the original App Server request.

This ticket scopes the remediation as a diagnostic-first investigation
followed by targeted fixes, with a live smoke acceptance gate.

**Provenance:** Identified during T-07 7e live delegate smoke. Root-cause
analysis performed by the user against source code. Evidence recorded in
`docs/plans/2026-04-23-t07-cross-model-removal-7e.md` (Delegate Smoke
Deferral section) and the T-07 handoff. Job
`23347703-673a-419f-b1f5-01ca16cfe1f6` completed with empty diff after
5 escalation cycles.

## Defect 1: Sandbox policy blocks shell execution

### Location

`packages/plugins/codex-collaboration/server/runtime.py:23-38`,
function `build_workspace_write_sandbox_policy`.

### Observed behavior

Before the Candidate A implementation patch, the execution sandbox policy set
`includePlatformDefaults: False` within `readOnlyAccess`. This prevented the
delegated agent from reading platform binaries (e.g., `/usr/bin/*`,
`/usr/lib/*`), which are required for any shell command execution. All shell
commands failed with exit code -1.

### Original policy shape (pre-fix)

```python
{
    "type": "workspaceWrite",
    "writableRoots": [str(worktree_path)],
    "readOnlyAccess": {
        "type": "restricted",
        "readableRoots": [str(worktree_path)],
        "includePlatformDefaults": False,
    },
    "networkAccess": False,
    "excludeSlashTmp": True,
    "excludeTmpdirEnvVar": True,
}
```

### Diagnostic gate (before implementation)

The fix is not simply flipping `includePlatformDefaults` to `True`. The
original T-05 hardening set this to `False` deliberately. Before changing
it, establish:

1. **What `includePlatformDefaults: True` grants.** Determine which paths
   App Server adds to the readable set when platform defaults are included.
   Does it grant read access to the full filesystem minus writable roots, or
   a curated set of system directories (e.g., `/usr/bin`, `/usr/lib`,
   `/System/Library` on macOS)?

2. **Security boundary preservation.** Confirm that with
   `includePlatformDefaults: True`, the important security boundary holds:
   only the worktree is writable, and host/project secrets outside the
   declared scope are not readable through ordinary file reads. Specifically
   check: `~/.ssh/`, `~/.aws/`, `~/.config/`, `.env` files outside the
   worktree, other worktrees, the parent repo's `.git/`.

3. **Minimum viable grant.** Determine whether shell execution requires the
   full platform defaults, or whether a narrower `readableRoots` addition
   (e.g., `["/usr/bin", "/usr/lib"]`) would suffice. If a narrower grant
   works, prefer it.

Record diagnostic findings as evidence in the implementation plan before
committing to a policy change.

### Implementation update (2026-04-29)

Candidate A diagnostic closure is recorded in
`docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md`.

The diagnostic established that `includePlatformDefaults: True` is sufficient
for the canonical delegated shell workload, and that the probed security
boundary still holds for network access, sensitive host-path reads, and sibling
worktree reads. This implementation slice promotes the Candidate A policy by
setting `includePlatformDefaults: True` in
`packages/plugins/codex-collaboration/server/runtime.py`, while preserving the
existing worktree-only writable/readable roots, `networkAccess: False`,
`excludeSlashTmp: True`, and `excludeTmpdirEnvVar: True`.

Regression coverage: `packages/plugins/codex-collaboration/tests/test_runtime.py`
asserts the promoted policy shape.

This ticket remains open until the post-restart live `/delegate` smoke verifies
the end-to-end acceptance criteria below.

## Defect 2: Approval path does not grant the original request

### Location

- `delegation_controller.py:718` — `_server_request_handler` returns
  `{"decision": "cancel"}` for `command_approval`/`file_change` kinds.
- `delegation_controller.py:1743-1754` — `decide(approve)` calls
  `build_execution_resume_turn_text` and starts a new execution turn.
- `execution_prompt_builder.py:41-77` — resume prompt includes
  "treat the caller decision below as authoritative" as natural language.

### Observed behavior

When the delegated agent requests approval for a command or file change:

1. `_server_request_handler` returns `{"decision": "cancel"}` to App Server.
2. The request is captured in `_pending_request_store`.
3. The job transitions to `needs_escalation`.
4. When the caller runs `codex.delegate.decide(approve)`:
   - `build_execution_resume_turn_text` constructs a natural-language prompt.
   - `_execute_live_turn` starts a **new turn** with the same sandbox policy.
   - App Server sees a fresh prompt, not a grant of the original request.
5. The agent retries the same action, hits the sandbox restriction, and
   re-escalates with the same shape.

The result is a cancel-retry loop that never produces artifacts.

### Static contract evidence

The vendored 0.117.0 App Server schemas already define the valid response
shapes. The current `{"decision": "cancel"}` is schema-valid but semantically
wrong for an approve path — `cancel` interrupts the turn.

**`CommandExecutionRequestApprovalResponse`** (vendored at
`tests/fixtures/codex-app-server/0.117.0/`):

| Decision | Semantics |
|----------|-----------|
| `accept` | Approve the command |
| `acceptForSession` | Approve + cache for session |
| `acceptWithExecpolicyAmendment` | Approve + amend exec policy |
| `applyNetworkPolicyAmendment` | Set persistent network policy rule |
| `decline` | Deny; agent continues the turn |
| `cancel` | Deny; turn is immediately interrupted |

**`FileChangeRequestApprovalResponse`**:

| Decision | Semantics |
|----------|-----------|
| `accept` | Approve the file changes |
| `acceptForSession` | Approve + cache for session |
| `decline` | Deny; agent continues the turn |
| `cancel` | Deny; turn is immediately interrupted |

The grant path exists: `_server_request_handler` should return
`{"decision": "accept"}` (or `"acceptForSession"`) instead of
`{"decision": "cancel"}` for approved requests.

### Diagnostic gate (before implementation)

The static contract provides the response shapes, but the implementation
must verify live behavior. Before committing to the fix:

1. **Live grant verification.** Return `{"decision": "accept"}` from
   `_server_request_handler` for both `command_approval` and `file_change`
   requests and confirm that App Server resumes the original turn (executes
   the command / applies the file change) rather than interrupting it.
   If only one kind appears during the diagnostic smoke, the other is
   covered by the final live-smoke acceptance gate.

2. **Inline vs. out-of-band.** Confirm that `accept` is handled inline
   within the same turn — i.e., the `server_request_handler` return value
   resumes the action without requiring a new turn. If so, the
   cancel-then-new-turn pattern in `decide(approve)` may be unnecessary
   for requests where the handler can grant directly.

3. **Escalation model choice.** Determine whether all `command_approval`
   and `file_change` requests should be auto-accepted by the handler
   (since the worktree is isolated), or whether some should still escalate
   to the caller. If all should auto-accept, the handler returns `accept`
   directly and the escalation/decide flow is only needed for unknown or
   denied requests. If selective, the handler needs a policy to distinguish
   accept-inline from escalate-to-caller.

Record live operational findings as evidence before committing to an
implementation path.

## Interaction between defects

These defects compound but are partially independent:

- **Sandbox-only fix** (Defect 1 alone): If `includePlatformDefaults: True`
  allows shell execution, commands will no longer fail at the sandbox layer.
  However, the controller defaults execution turns to
  `approval_policy="untrusted"` (`delegation_controller.py:246`), which is
  a separate mechanism from sandbox readability — App Server may still emit
  `command_approval`/`file_change` requests based on the approval policy
  regardless of sandbox permissions. **Hypothesis to verify after sandbox
  fix:** run a simple edit and record whether `untrusted` approval policy
  still triggers escalation requests even when the sandbox allows the
  underlying action.

- **Approval-only fix** (Defect 2 alone): If the grant path works but the
  sandbox still blocks shell execution, the granted action will fail for
  the same reason the original did.

- **Both fixed:** Full delegation lifecycle works. Shell commands execute,
  approval grants are honored, artifacts are produced.

The sandbox fix is the higher-value first step because it unblocks shell
execution, which is a prerequisite for any artifact production. Whether it
also reduces escalation frequency depends on the interaction between sandbox
permissions and approval policy — that is a diagnostic finding, not an
assumption.

## Acceptance criteria

- [ ] Live `/delegate` can run at least one shell command needed for a
      simple repo edit (proves sandbox allows shell execution).
- [ ] `codex.delegate.decide(approve)` grants the original App Server request
      using the schema-valid `accept` decision. If live `accept` does not
      resume the original action as expected, record the mismatch as an App
      Server/handler integration failure with diagnostic evidence.
- [ ] A real objective produces a non-empty `full.diff` and non-empty
      `changed_files` (proves artifact production works).
- [ ] `codex.delegate.poll` materializes reviewable artifacts with a stable
      artifact hash (proves artifact pipeline is functional).
- [ ] Final disposition is either successful promotion or a typed, documented
      promotion rejection unrelated to sandbox execution or approval-loop
      recurrence (proves end-to-end lifecycle).
- [ ] Regression tests cover the sandbox policy serialization and the
      approval decision response shape (proves the fix doesn't silently
      regress).

## Implementation sequence

### Phase 1: Diagnostic (sandbox)

Investigate `includePlatformDefaults` behavior per the diagnostic gate in
Defect 1. Record findings. This is an investigation, not a code change.

### Phase 2: Diagnostic (approval API)

Investigate App Server's response contract for `command_approval` and
`file_change` per the diagnostic gate in Defect 2. Record findings.

Phases 1 and 2 can run in parallel.

### Phase 3: Implementation plan

Based on diagnostic evidence, draft an implementation plan with specific
code changes. The plan shape depends on findings:

- If `includePlatformDefaults: True` is safe and live `accept` resumes
  turns: change sandbox policy + return `accept` instead of `cancel`.
- If `includePlatformDefaults: True` is safe but live `accept` does not
  resume as expected: change sandbox policy + investigate handler
  integration mismatch (the schema defines the grant; the question is
  runtime behavior).
- If `includePlatformDefaults: True` is unsafe: identify narrower
  readable-root additions.

### Phase 4: Implementation

Execute the plan. Write regression tests.

### Phase 5: Live smoke

Run a live `/delegate` with a real file-creation or file-edit objective.
Verify all acceptance criteria.

## Evidence from T-07

### Live smoke job

- **Job ID:** `23347703-673a-419f-b1f5-01ca16cfe1f6`
- **Outcome:** `completed` with `promotion_state: "pending"`, empty diff
- **Escalation cycles:** 5
- **Runtime:** App Server bootstrapped successfully, runtime ID assigned

### Source-verified defect locations

| Defect | File | Line | Verified |
|--------|------|------|----------|
| Sandbox policy | `runtime.py` | 23-38 | pre-fix `includePlatformDefaults: False` confirmed; Candidate A implementation promotes `True` |
| Cancel response | `delegation_controller.py` | 718-719 | `{"decision": "cancel"}` confirmed |
| Resume prompt | `execution_prompt_builder.py` | 41-77 | Natural-language-only resume confirmed |
| Cancel-capable kinds | `delegation_controller.py` | 642 | `{"command_approval", "file_change"}` confirmed |

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

The execution sandbox policy sets `includePlatformDefaults: False` within
`readOnlyAccess`. This prevents the delegated agent from reading platform
binaries (e.g., `/usr/bin/*`, `/usr/lib/*`), which are required for any
shell command execution. All shell commands fail with exit code -1.

### Current policy shape

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

- [ ] Live `/delegate` can run an end-to-end delegated objective that
      invokes at least one shell command and completes without an
      exec-policy escalation. **Note:** as of 2026-04-23 this criterion is
      not met. Codex invokes all commands via a `/bin/zsh -lc '...'`
      wrapper, and the wrapper itself triggers `command_approval` with
      empty `available_decisions` + `proposedExecpolicyAmendment`, even
      when the wrapped command only calls `/bin`/`/usr/bin` binaries.
      Clearing this criterion requires exec-policy support (see Scope
      limitations below).
- [ ] The server request handler returns schema-valid `accept` for in-boundary
      `command_approval` and `file_change` requests. App Server continues the
      same turn without interruption. The job completes without a pending
      escalation. `codex.delegate.decide(approve)` is rejected for these
      request kinds with a typed reason (the original wire request was
      interrupted; a new turn cannot grant it). `decide(deny)` and `discard`
      remain valid.
- [ ] A real objective produces a non-empty `full.diff` and non-empty
      `changed_files` (proves artifact production works).
- [ ] `codex.delegate.poll` materializes reviewable artifacts with a stable
      artifact hash (proves artifact pipeline is functional).
- [ ] Final disposition is one of: (a) successful promotion, (b) a typed,
      documented promotion rejection unrelated to sandbox execution or
      approval-loop recurrence, or (c) a typed pre-promotion job failure
      (`status="failed"` with `promotion_state=null`) produced by the
      state-machine's empty-`available_decisions` path, with runtime
      released, session closed, lineage completed, and artifacts
      materialized for inspection (proves end-to-end lifecycle under both
      the happy path and the deferred-scope exec-policy path).
- [ ] Regression tests cover the sandbox policy serialization and the
      approval decision response shape (proves the fix doesn't silently
      regress).

### Scope limitations

This remediation proves the delegate lifecycle under the sandbox's
**platform-default exec policy only**. The execution prompt
(`execution_prompt_builder.py`) constrains delegated workers to executables
available from `/bin` and `/usr/bin` (`find`, `ls`, `mkdir`, `cat`, `grep`,
`sed`, `awk`, etc.) and explicitly forbids Homebrew, mise, and developer-tool
binaries such as `rg`, `fd`, `uv`, `node`, `python`, and `ruff`.

Widening the exec policy (e.g. handling `acceptWithExecpolicyAmendment`, an
absolute-path allowlist, or command-pattern amendments) is **out of scope**
for this ticket and is deferred to a follow-up trust-boundary design with its
own contract around amendment persistence, representation in
`available_decisions`, and the `/delegate approve` semantics for command
approvals. Closing this ticket does not imply delegate support for objectives
that structurally require developer tools.

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
| Sandbox policy | `runtime.py` | 23-38 | `includePlatformDefaults: False` confirmed |
| Cancel response | `delegation_controller.py` | 718-719 | `{"decision": "cancel"}` confirmed |
| Resume prompt | `execution_prompt_builder.py` | 41-77 | Natural-language-only resume confirmed |
| Cancel-capable kinds | `delegation_controller.py` | 642 | `{"command_approval", "file_change"}` confirmed |

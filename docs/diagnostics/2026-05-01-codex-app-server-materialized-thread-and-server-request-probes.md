# Codex App Server Materialized Thread And Server-Request Runtime Probes

**Date:** 2026-05-01
**Status:** complete; not an architecture spec
**Selected launcher:** `codex app-server`
**Scratch CODEX_HOME:** `/private/tmp/codex-app-server-runtime-blocker-probes/codex-home`

## Scope

This packet follows up only on the materialized-thread `thread/read` and server-request runtime blockers. It intentionally does not adjudicate v128 Branch A1/A2/A3/B/C/D; permission-branch probes remain owned by `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.

Executed scope:

- fresh scratch `CODEX_HOME` under `/private/tmp`
- no-auth / no-model lifecycle probe sequence
- base `thread/read(includeTurns=false)` readback
- one approved model-mediated `turn/start` using the exact constrained scope from the approval gate
- `thread/read(includeTurns=true)` after the turn stopped

Still not executed:

- any server-request response policy
- v128 permission payload probing
- use of the operator's real `~/.codex`

## Inherited Evidence

Inherited blocker state from the previous scratch-home runtime packet:

```text
ready=false
thread_read_projection_classification.status=partial
server_request_runtime_evidence.status=blocked_no_safe_auth
operator_codex_home_used=false
auth_values_serialized=false
```

Launcher remained stable:

- path: `/opt/homebrew/bin/codex`
- version: `codex-cli 0.128.0`
- SHA-256: `ff803d4b5c595af19b99c18db6def26539fdf4da23a035ab30809835631e8e4b`

## Probe Results

| Probe | Status | Classification | Notes |
|---|---|---|---|
| `initialize_then_initialized` | passed | `ok` | `initialize` returned scratch `codexHome`, `platformFamily`, `platformOs`, and `userAgent`; `initialized` followed successfully |
| `account_read_after_initialize` | passed | `ok` | Returned `account: null` and `requiresOpenaiAuth: true`; no account identifier or credential value was serialized |
| `materialized_thread_read_no_auth` | partial | `thread_start=ok;thread_read_without_turns=ok;thread_read_with_turns=jsonrpc_error` | Brand-new thread base projection is readable; turn-bearing projection is still gated by materialization |
| `materialized_thread_read_model_turn` | passed | `thread_start=ok;turn_start=ok;thread_read_with_turns=ok` | One approved `turn/start` request materialized a thread projection with one turn, but the turn itself failed at the backend auth layer |

No server-initiated requests were observed in either the no-auth slice or the approved one-turn model-mediated slice.

## Materialized Thread Read Projection

What the combined no-auth + approved model-turn sequence proved:

1. `thread/start` succeeds under scratch `CODEX_HOME`.
2. `thread/read(includeTurns=false)` succeeds immediately after `thread/start`.
3. `thread/read(includeTurns=true)` on a brand-new thread fails with the concrete lifecycle rule:

```json
{
  "code": -32600,
  "message": "thread 019de467-a276-7263-8cd6-807e84d9d032 is not materialized yet; includeTurns is unavailable before first user message"
}
```

Base thread projection keys from the successful `includeTurns=false` read:

- top-level response keys: `thread`
- thread keys:
  - `agentNickname`
  - `agentRole`
  - `cliVersion`
  - `createdAt`
  - `cwd`
  - `ephemeral`
  - `forkedFromId`
  - `gitInfo`
  - `id`
  - `modelProvider`
  - `name`
  - `path`
  - `preview`
  - `source`
  - `status`
  - `turns`
  - `updatedAt`

The approved model-mediated turn then produced a materialized `thread/read(includeTurns=true)` response with:

- `turn_count = 1`
- first-turn keys:
  - `completedAt`
  - `durationMs`
  - `error`
  - `id`
  - `items`
  - `startedAt`
  - `status`
- top-level `agentMessage`: not present
- legacy `items[]` `agentMessage`: not present
- `item/completed` observed: yes, but only for the `userMessage`

Important discrepancy:

- `turn/completed` notification reported the turn as `failed` with a 401 auth error after repeated reconnect attempts
- `thread/read(includeTurns=true)` projected that same turn as `status: "completed"` with `error: null` and only the user message in `items[]`

Classification: `passed`

What is now proven:

- the launcher can expose a materialized `thread/read(includeTurns=true)` projection under scratch `CODEX_HOME`
- one user-message turn is enough to materialize the thread projection

What remains unproven:

- whether successful or reply-bearing turns expose a recoverable agent-output shape for the current advisory fallback path
- how much trust to place in `thread/read` turn status/error fields when they disagree with live turn notifications

## Server-Request Runtime Evidence

Schema-visible server-request methods:

- `account/chatgptAuthTokens/refresh`
- `applyPatchApproval`
- `execCommandApproval`
- `item/commandExecution/requestApproval`
- `item/fileChange/requestApproval`
- `item/permissions/requestApproval`
- `item/tool/call`
- `item/tool/requestUserInput`
- `mcpServer/elicitation/request`

Runtime evidence in this packet:

- observed no-auth requests: none
- observed model-mediated requests: none
- unknown or unparseable requests: none

Why the blocker remains:

- the approved model-mediated turn executed, but it failed with repeated 401 backend auth errors before any server-request envelope was emitted
- no actual server-request method was observed on the wire, so the local parser/runtime compatibility boundary still cannot be judged from live envelopes

Classification: `partial`

## Approval Gate

Approval-gate state recorded in the durable JSON:

```json
{
  "model_mediated_probe_requested": true,
  "model_mediated_probe_approved": true,
  "approved_by_user_message": "Proceed with that.",
  "approval_scope": {
    "scratch_codex_home": "/private/tmp/codex-app-server-runtime-blocker-probes/codex-home",
    "scratch_workspace": "/private/tmp/codex-app-server-runtime-blocker-probes/workspace",
    "turn_start_requests": 1,
    "prompt_text": "Reply with the single word: probe",
    "approval_policy": "never",
    "sandbox_policy": {
      "type": "readOnly",
      "networkAccess": false
    },
    "timeout_seconds": 120
  }
}
```

That gate was satisfied in this turn, and exactly one scoped `turn/start` request was sent. No responses were sent to any command/file/permission approval method because none were observed.

## Architecture Spec Readiness Delta

Newly satisfied items:

- no-auth `thread/read(includeTurns=false)` base projection evidence for a brand-new scratch thread
- concrete lifecycle precondition for `includeTurns=true` on an unmaterialized thread
- materialized `thread/read(includeTurns=true)` projection evidence for a thread with one turn
- approved one-turn model-mediated request shape captured under scratch `CODEX_HOME`
- no-auth and model-mediated server-request slices both captured as none observed

Still missing:

- evidence that a materialized thread projection contains recoverable agent output shape for fallback use
- live runtime server-request envelopes from a successful or approval-blocked model/tool turn
- compatibility judgment for actual server-request envelopes against the local parser/runtime boundary

The architecture spec should still wait because server-request runtime behavior remains unproven.

## Remaining Blockers

1. Server-request runtime behavior remains unproven because neither the no-auth slice nor the approved auth-failing model slice emitted any server requests.
2. The current evidence does not prove a recoverable agent-output shape in `thread/read` for reply extraction.
3. `thread/read` turn status/error projection disagreed with the live `turn/completed` notification for the auth-failed turn; any architecture or fallback design should treat that discrepancy as unresolved runtime risk.

## Worktree State

Final worktree status:

```text
## feature/codex-app-server-client-platform-exploration
?? docs/architecture/
?? docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md
?? docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md
?? docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md
?? docs/diagnostics/codex-app-server-client-platform-exploration.json
?? docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json
?? docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json
?? docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md
?? docs/plans/2026-05-01-codex-app-server-materialized-thread-and-server-request-probe-plan.md
?? docs/plans/2026-05-01-codex-app-server-scratch-home-runtime-probe-plan.md
?? docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md
```

The worktree remains intentionally uncommitted.

# Codex App Server Server-Request Envelope Runtime Probes

**Date:** 2026-05-01
**Status:** complete; not an architecture spec
**Selected launcher:** `codex app-server`
**Scratch CODEX_HOME:** `/private/tmp/codex-app-server-server-request-envelope-probes-20260501130024/codex-home`

## Scope

This packet targets only live server-request envelope reachability and shape. It intentionally does not adjudicate v128 Branch A1/A2/A3/B/C/D; permission-branch probes remain owned by `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.

Executed scope:

- fresh timestamped scratch `CODEX_HOME` after the earlier server-request root was found non-empty
- scratch device-code auth feasibility under isolated `CODEX_HOME`
- one approved `thread/start`
- one approved request-producing `turn/start`
- no affirmative responses to any server requests

Not executed:

- any approval response payload
- any second envelope-trigger turn
- any v128 permission-branch probe
- any use or copying of operator-home credentials from `/Users/jp/.codex`

## Inherited Evidence

Inherited state from the materialized-thread packet:

```text
materialized_thread_read.status=passed
server_request_runtime_evidence.status=partial
architecture_spec_readiness_delta.ready=false
operator_codex_home_used=false
auth_values_serialized=false
```

That earlier packet proved materialized `thread/read(includeTurns=true)` but still had no live server-request envelope evidence.

## Auth Gate

Scratch auth method:

- `account/login/start` with `type: "chatgptDeviceCode"`

Safety outcomes:

- `credential_copy_attempted = false`
- `credential_values_serialized = false`
- auth URLs, login ids, user codes, and account identifiers were redacted before any durable write

Observed auth sequence:

1. `initialize` returned scratch `codexHome` at `/private/tmp/codex-app-server-server-request-envelope-probes-20260501130024/codex-home`
2. `account/read` before auth returned:

```json
{
  "account": null,
  "requiresOpenaiAuth": true
}
```

3. `account/login/start` returned a redacted device-code shape:

```json
{
  "loginId": "[REDACTED_LOGIN_ID]",
  "type": "chatgptDeviceCode",
  "userCode": "[REDACTED_USER_CODE]",
  "verificationUrl": "[REDACTED_SECRET]"
}
```

4. `account/login/completed` was observed with `success: true`
5. `account/read` after auth returned a redacted authenticated shape:

```json
{
  "account": {
    "email": "[REDACTED_ACCOUNT]",
    "planType": "pro",
    "type": "chatgpt"
  },
  "requiresOpenaiAuth": true
}
```

Interpretation:

- scratch auth was established safely enough to proceed
- the `requiresOpenaiAuth: true` flag remained present even after the authenticated account shape appeared, so future readers should not treat that field alone as an unauthenticated-state proof

## Probe Results

| Probe | Status | Classification | Notes |
|---|---|---|---|
| `initialize_then_initialized` | passed | `ok` | scratch `codexHome`, platform, and user-agent recorded |
| `account_read_before_scratch_auth` | passed | `ok` | unauthenticated scratch state confirmed |
| `scratch_auth_device_code` | passed | `ok` | device-code login completed under scratch home with redacted durable records |
| `account_read_after_scratch_auth` | passed | `ok` | authenticated account shape returned after scratch login |
| `server_request_trigger_command_approval` | passed | `thread_start=ok;turn_start=ok` | one approved request-producing turn emitted a live command-approval server request |

## Observed Server Requests

One live server-request envelope was observed:

- method: `item/commandExecution/requestApproval`
- JSON-RPC `id`: present
- schema-visible: yes
- local compatibility classification: parser-kind compatible but decision-shape lossy under the observed `availableDecisions`. The mixed-list entry `acceptWithExecpolicyAmendment` triggers the all-strings fallback in `_resolve_available_decisions` (`packages/plugins/codex-collaboration/server/approval_router.py:103-111`); see `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` "Command Approval Decision-Shape Boundary" for the lossless-branch forward path.

Observed top-level `params` keys:

- `availableDecisions`
- `command`
- `commandActions`
- `cwd`
- `itemId`
- `proposedExecpolicyAmendment`
- `reason`
- `threadId`
- `turnId`

Redacted envelope summary:

```json
{
  "method": "item/commandExecution/requestApproval",
  "has_id": true,
  "params_keys": [
    "availableDecisions",
    "command",
    "commandActions",
    "cwd",
    "itemId",
    "proposedExecpolicyAmendment",
    "reason",
    "threadId",
    "turnId"
  ],
  "threadId_present": true,
  "turnId_present": true,
  "itemId_present": true
}
```

The request was triggered by an agent attempt to run:

`/bin/zsh -lc 'touch server-request-probe.txt'`

No approval response was sent.

## Compatibility Classification

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

Local compatibility judgment for the observed envelope:

- `approval_router.py` maps `item/commandExecution/requestApproval` to `kind="command_approval"`
- the parser requires `id`, `method`, `params`, `itemId`, `threadId`, and `turnId`
- the live envelope includes all of those fields
- `availableDecisions` is present on the wire (see "Observed Server Requests" above), but `_resolve_available_decisions` (`approval_router.py:103-111`) preserves the wire list only when every entry is a `str`. The observed mixed list contains a structured `acceptWithExecpolicyAmendment` entry, so the parser falls back to `_AVAILABLE_DECISIONS[command_approval]` = `("accept", "acceptForSession", "acceptWithExecpolicyAmendment", "applyNetworkPolicyAmendment", "decline", "cancel")`. The fallback preserves `accept` and `cancel` (the string entries on the wire), collapses the wire's structured `acceptWithExecpolicyAmendment` object into a bare string of the same name (the payload — execpolicy amendment details — is dropped), and adds three decisions never offered by the wire (`acceptForSession`, `applyNetworkPolicyAmendment`, `decline`). Decision-shape preservation is therefore lossy in two directions — payload loss for the structured entry, plus spurious-decision addition — and command-approval response compatibility is not established. See `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` "Command Approval Decision-Shape Boundary" for the lossless-branch forward path.

Compatibility result:

- observed parser-kind compatible methods: `item/commandExecution/requestApproval` (decision-shape lossy under the observed `availableDecisions`; see "Local compatibility judgment" above)
- observed methods proven fully supported (parser-kind AND response-shape): none
- observed unsupported methods: none
- observed unknown or unparseable methods: none
- missing required fields: none

Important limit:

This packet supports a parser-kind compatibility inference for the observed command-approval envelope — the required correlation fields (`itemId`, `threadId`, `turnId`) and JSON-RPC `id` are present, and `approval_router.py` maps `item/commandExecution/requestApproval` to `kind=command_approval`. It does not establish response-shape compatibility — the observed mixed `availableDecisions` triggers parser fallback per `_resolve_available_decisions` (see "Local compatibility judgment" above). It does not prove live reachability or parser cleanliness for file-change, permission, tool-input, MCP elicitation, auth-refresh, or other schema-visible server-request methods.

It also does not collapse fail-closed behavior into “clean lifecycle semantics.” Unsupported or unknown-method handling remains a separate runtime-quality question.

## Architecture Spec Readiness Delta

Newly satisfied items:

- scratch auth was established under isolated `CODEX_HOME` without credential copying
- a live schema-visible server-request envelope was captured and redacted safely
- the observed `item/commandExecution/requestApproval` envelope is inferred to be parseable via the parser's decision-shape-lossy fallback path; lossless preservation of `availableDecisions` is NOT established (see "Local compatibility judgment" above)

Still missing:

- coverage for other schema-visible server-request methods
- runtime evidence for unknown / unsupported envelope handling under live conditions
- a lossless parser/response branch for command-approval that preserves `availableDecisions` shape without falling back to `_AVAILABLE_DECISIONS[command_approval]` (see `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` "Command Approval Decision-Shape Boundary")

The architecture spec can proceed only if it explicitly carries the decision-shape-lossy fallback as an unresolved response-semantics risk for command-approval (alongside the unobserved-method risks named above) — not as proven support. Scoping "support" to the observed method without that qualification would smuggle response-shape compatibility into the architecture's foundational assumptions; the parser's actual behavior at `approval_router.py:103-111` does not justify it.

## Remaining Blockers

1. Only `item/commandExecution/requestApproval` has live envelope evidence — and even for that method, response-shape compatibility is not established (decision-shape lossy; see "Local compatibility judgment" above).
2. The packet does not yet prove live reachability for file-change, permission, tool-input, MCP elicitation, auth-refresh, or other schema-visible methods.
3. Fail-closed behavior for unsupported or unknown methods is still not the same thing as semantically clean lifecycle handling.

## Worktree State

Final worktree status:

```text
## feature/codex-app-server-client-platform-exploration
?? docs/architecture/
?? docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md
?? docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md
?? docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md
?? docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
?? docs/diagnostics/codex-app-server-client-platform-exploration.json
?? docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json
?? docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json
?? docs/diagnostics/codex-app-server-server-request-envelope-probes.json
?? docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md
?? docs/plans/2026-05-01-codex-app-server-materialized-thread-and-server-request-probe-plan.md
?? docs/plans/2026-05-01-codex-app-server-scratch-home-runtime-probe-plan.md
?? docs/plans/2026-05-01-codex-app-server-server-request-envelope-probe-plan.md
?? docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md
```

The worktree remains intentionally uncommitted.

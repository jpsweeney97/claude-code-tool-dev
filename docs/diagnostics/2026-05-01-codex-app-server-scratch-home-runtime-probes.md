# Codex App Server Scratch-Home Runtime Probes

**Date:** 2026-05-01
**Status:** Runtime probe packet complete; not an architecture spec
**Selected launcher:** `codex app-server`
**Scratch CODEX_HOME:** `/private/tmp/codex-app-server-runtime-probes/codex-home`

## Scope

This packet executes the low-risk runtime backlog from the static exploration packet against the installed `codex app-server` launcher with an isolated `CODEX_HOME`.

This packet intentionally does not adjudicate v128 Branch A1/A2/A3/B/C/D. Permission-branch probes remain owned by `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.

In scope here:

- request-before-initialize rejection
- `initialize` then `initialized`
- `account/read` after initialization
- scratch `thread/start`
- `thread/read(includeTurns=true)` projection behavior for a scratch thread
- scratch-home mutation classification
- no-auth server-request observation

Out of scope here:

- v128 permission payload acceptance
- `/delegate` execution
- standalone `codex-app-server` equivalence testing
- model-mediated server-request probes without explicit approval
- any read/copy/hash/serialization of operator credential material

Worktree status at probe start:

```text
## feature/codex-app-server-client-platform-exploration
?? docs/architecture/
?? docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md
?? docs/diagnostics/codex-app-server-client-platform-exploration.json
?? docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md
?? docs/plans/2026-05-01-codex-app-server-scratch-home-runtime-probe-plan.md
?? docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md
```

## Launcher And Scratch Environment

- Launcher path: `/opt/homebrew/bin/codex`
- Launcher version: `codex-cli 0.128.0`
- Launcher SHA-256: `ff803d4b5c595af19b99c18db6def26539fdf4da23a035ab30809835631e8e4b`
- Local standalone `codex-app-server`: absent
- Scratch root: `/private/tmp/codex-app-server-runtime-probes`
- Scratch workspace: `/private/tmp/codex-app-server-runtime-probes/workspace`
- Env overrides:
  - `CODEX_HOME=/private/tmp/codex-app-server-runtime-probes/codex-home`
  - `CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG=1`
- Durable packet flags:
  - `operator_codex_home_used: false`
  - `auth_values_serialized: false`

`initialize` returned scratch-scoped runtime metadata:

```json
{
  "codexHome": "/private/tmp/codex-app-server-runtime-probes/codex-home",
  "platformFamily": "unix",
  "platformOs": "macos",
  "userAgent": "Codex Desktop/0.128.0 (Mac OS 26.4.1; arm64) dumb (codex_collaboration_probe; 0.1.0)"
}
```

## Probe Results

| Probe | Status | Classification | Notes |
|---|---|---|---|
| `request_before_initialize_rejection` | passed | `not_initialized_error` | `account/read` before `initialize` was rejected as documented |
| `initialize_then_initialized` | passed | `ok` | Handshake succeeded and returned scratch `codexHome`, platform, and user-agent metadata |
| `account_read_after_initialize` | passed | `ok` | Returned `account: null` with `requiresOpenaiAuth: true`; no credential values were exposed |
| `thread_start_and_read_projection` | failed | `thread_start=ok;thread_read=jsonrpc_error` | `thread/start` succeeded under scratch home, but `thread/read(includeTurns=true)` failed on a brand-new thread |

Raw `thread/start` evidence is important even though the paired `thread/read` probe failed:

- `thread/started` notification was emitted
- `thread/start` response included:
  - `thread.id`
  - `thread.path`
  - `thread.turns: []`
  - `sandbox`
  - `permissionProfile`
  - `activePermissionProfile`

That means scratch-home thread bootstrap is live and does not require access to the operator’s real `CODEX_HOME`.

## Thread Read Projection Shape

The `thread/read(includeTurns=true)` probe did not prove the completed-turn projection shape. It did prove a concrete lifecycle precondition:

```json
{
  "code": -32600,
  "message": "thread 019de459-eafd-71b3-8639-46e852038ebc is not materialized yet; includeTurns is unavailable before first user message"
}
```

Classification: `partial`

Why `partial` instead of `failed` as an architecture input:

- `thread/start` succeeded under scratch home
- the runtime gave a specific lifecycle rule rather than a generic transport or auth failure
- the blocker is narrowed to “need a materialized thread with at least one user message” rather than “thread/read is unavailable under scratch home”

What remains unproven:

- the live `thread/read` shape for a materialized thread with turns
- whether completed turns project top-level `agentMessage`, legacy `items[]`, or another recoverable shape

## Server-Request Evidence

Schema-visible server-request methods from `experimental/ServerRequest.json`:

- `item/commandExecution/requestApproval`
- `item/fileChange/requestApproval`
- `item/tool/requestUserInput`
- `mcpServer/elicitation/request`
- `item/permissions/requestApproval`
- `item/tool/call`
- `account/chatgptAuthTokens/refresh`
- `applyPatchApproval`
- `execCommandApproval`

Observed during no-auth runtime probes:

- no server-initiated requests

`account/read` after initialization returned:

```json
{
  "account": null,
  "requiresOpenaiAuth": true
}
```

Classification: `blocked_no_safe_auth`

That means this packet does not close the server-request blocker. It only proves that no server requests appear in the no-auth handshake/thread bootstrap slice. Any model-mediated server-request evidence remains blocked until there is a safe auth path or explicit approval for a model turn.

## Config And Trust Mutation

Classification: `scratch_only_mutation`

Observed mutation classes under scratch `CODEX_HOME`:

- sqlite/log state:
  - `logs_2.sqlite`, `logs_2.sqlite-shm`, `logs_2.sqlite-wal`
  - `state_5.sqlite`, `state_5.sqlite-shm`, `state_5.sqlite-wal`
- seeded skill/memory content:
  - `memories/`
  - `skills/.system/...`
- scratch temp wrappers:
  - `tmp/arg0/...`

Not observed:

- `config.toml`
- `sessions/`
- trust/project-state paths
- any reference to `/Users/jp/.codex`

This reduces the trust/config blocker meaningfully:

- the launcher respected the scratch `CODEX_HOME`
- scratch-home mutations were real, but contained
- `thread/start` without a user message did not materialize a session rollout file under `sessions/`

## Architecture Spec Readiness Delta

Newly satisfied blocker items from the earlier exploration packet:

- Live `initialize` / `initialized` handshake evidence for the selected launcher
- Live pre-initialize rejection evidence
- Scratch-home trust/config mutation evidence that stayed inside isolated `CODEX_HOME`

Still missing:

- live `thread/read` projection-shape evidence for a materialized thread with turns
- live server-request taxonomy / unknown-handling capture
- any model-mediated runtime evidence, which remains blocked on safe auth or explicit approval

This packet reduces the blocker set, but it does not close it. The architecture spec should still wait.

## Remaining Blockers

1. `thread/read(includeTurns=true)` needs a materialized thread with at least one user message before the projection shape can be judged.
2. Server-request runtime behavior is still unproven because the safe no-auth slice observed none, and `account/read` reported `requiresOpenaiAuth: true`.
3. v128 permission-branch work remains intentionally untouched by this packet.

Final worktree status after artifact verification:

```text
## feature/codex-app-server-client-platform-exploration
?? docs/architecture/
?? docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md
?? docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md
?? docs/diagnostics/codex-app-server-client-platform-exploration.json
?? docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json
?? docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md
?? docs/plans/2026-05-01-codex-app-server-scratch-home-runtime-probe-plan.md
?? docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md
```

The worktree remains intentionally uncommitted.

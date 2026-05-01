# Codex App Server Server-Request Envelope Probe Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This is a server-request runtime evidence plan, not the client-platform architecture spec and not the v128 permission-branch decision packet.

**Goal:** Produce a focused runtime probe packet that either captures live Codex App Server server-request envelopes under isolated `CODEX_HOME` or records the exact auth/safety blocker that prevents envelope reachability.

**Architecture:** Use a fresh scratch `CODEX_HOME`, a raw JSON-RPC harness that separates server requests from notifications, and a two-gate flow: first establish scratch auth without copying operator-home credentials, then run one deliberately request-producing turn while refusing to approve side effects unless a separate response policy is explicitly authorized.

**Tech Stack:** Python 3 standard library, Codex App Server JSON-RPC over stdio, `codex app-server` 0.128.0, generated stable/experimental schemas under `/private/tmp/codex-app-server-exploration`, existing local compatibility code under `packages/plugins/codex-collaboration/server/`.

---

## Boundary

This plan answers:

- Can scratch `CODEX_HOME` reach an authenticated app-server turn without copying or serializing operator credential material?
- Can one carefully scoped model turn emit a live server-request envelope?
- What is the raw method/params shape of any observed envelope?
- Does each observed envelope satisfy the current local parser/runtime boundary, especially required `itemId`, `threadId`, and `turnId` fields where applicable?

This plan does not:

- Copy files from `/Users/jp/.codex` into scratch `CODEX_HOME`.
- Read, print, hash, or serialize auth tokens, auth headers, API keys, account identifiers, emails, or operator-home session contents.
- Respond affirmatively to command, file-change, permission, tool, MCP elicitation, or auth-token-refresh requests.
- Select v128 Branch A1/A2/A3/B/C/D.
- Probe stable `sandboxPolicy` acceptance or experimental `permissions` acceptance for `/delegate`.
- Run delegated `/delegate` execution.
- Install or download standalone `codex-app-server`.
- Draft `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md`.

## Inputs

Read first:

- `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
- `docs/diagnostics/codex-app-server-client-platform-exploration.json`
- `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`
- `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`
- `docs/plans/2026-05-01-codex-app-server-materialized-thread-and-server-request-probe-plan.md`
- `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`
- `docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md`
- `packages/plugins/codex-collaboration/server/approval_router.py`
- `packages/plugins/codex-collaboration/server/delegation_controller.py`
- `packages/plugins/codex-collaboration/server/models.py`
- `packages/plugins/codex-collaboration/server/pending_request_store.py`

Use these scratch/source inputs when present:

- `/private/tmp/codex-app-server-runtime-blocker-probes/probe_materialized_thread_and_server_requests.py`
- `/private/tmp/codex-app-server-runtime-blocker-probes/raw-model-mediated-server-request.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable/v2/LoginAccountParams.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable/v2/LoginAccountResponse.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable/v2/TurnStartParams.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/ServerRequest.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/CommandExecutionRequestApprovalParams.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/FileChangeRequestApprovalParams.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/PermissionsRequestApprovalParams.json`

## Outputs

Create:

- `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`
- `/private/tmp/codex-app-server-server-request-envelope-probes/`

The scratch directory may contain:

- `probe_server_request_envelopes.py`
- redacted raw JSON transcripts
- redacted stderr logs
- pre/post scratch-home manifests
- auth-gate state notes
- command output snippets

Do not commit scratch files.

## Durable JSON Shape

The durable JSON artifact must use this top-level shape:

```json
{
  "artifact_version": 1,
  "created_for": "codex-app-server-server-request-envelope-probes",
  "repo_worktree": "/Users/jp/Projects/active/claude-code-tool-dev/.worktrees/feature/codex-app-server-client-platform-exploration",
  "selected_launcher": {
    "kind": "codex app-server",
    "path": "/opt/homebrew/bin/codex",
    "version_output": "codex-cli 0.128.0",
    "binary_sha256": "sha256"
  },
  "scratch_environment": {
    "scratch_root": "/private/tmp/codex-app-server-server-request-envelope-probes",
    "codex_home": "/private/tmp/codex-app-server-server-request-envelope-probes/codex-home",
    "probe_workspace": "/private/tmp/codex-app-server-server-request-envelope-probes/workspace",
    "env_overrides": {
      "CODEX_HOME": "/private/tmp/codex-app-server-server-request-envelope-probes/codex-home",
      "CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG": "1"
    },
    "operator_codex_home_used": false,
    "auth_values_serialized": false
  },
  "inherited_evidence": {
    "materialized_thread_packet_json": "docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json",
    "materialized_thread_status": "passed",
    "previous_server_request_status": "partial",
    "previous_architecture_ready": false
  },
  "auth_gate": {
    "scratch_auth_requested": true,
    "scratch_auth_method": "chatgptDeviceCode",
    "scratch_auth_approved": false,
    "approved_by_user_message": null,
    "credential_copy_attempted": false,
    "credential_values_serialized": false,
    "auth_completed": false,
    "account_read_after_auth": null
  },
  "probe_gate": {
    "envelope_trigger_probe_requested": false,
    "envelope_trigger_probe_approved": false,
    "approval_scope": null
  },
  "schema_visible_server_request_methods": [],
  "probes": [],
  "observed_server_requests": [],
  "compatibility_classification": {
    "status": "passed|partial|blocked_no_safe_auth|blocked_requires_user_approval|failed",
    "supported_methods": [],
    "unsupported_methods": [],
    "unknown_or_unparseable_methods": [],
    "missing_required_fields": [],
    "notes": []
  },
  "architecture_spec_readiness_delta": {
    "ready": false,
    "newly_satisfied_items": [],
    "still_missing_items": []
  }
}
```

Each probe entry must include:

```json
{
  "name": "server_request_trigger_command_approval",
  "status": "passed|failed|blocked|partial",
  "requires_auth": true,
  "requires_model_turn": true,
  "request_sequence": [],
  "responses": [],
  "notifications": [],
  "server_requests": [],
  "errors": [],
  "classification": "ok|jsonrpc_error|blocked_no_safe_auth|blocked_requires_user_approval|unexpected",
  "evidence": []
}
```

Each observed server request must be redacted and summarized as:

```json
{
  "method": "item/commandExecution/requestApproval",
  "has_id": true,
  "params_keys": ["command", "cwd", "itemId", "threadId", "turnId"],
  "threadId_present": true,
  "turnId_present": true,
  "itemId_present": true,
  "schema_visible": true,
  "local_compatibility": "supported|unsupported|unknown|unparseable",
  "local_compatibility_notes": []
}
```

## Stop Conditions

Stop and write the durable packet with a blocked or partial status if any of these occur:

- `codex --version` is not `codex-cli 0.128.0`.
- `initialize` does not return the scratch `codexHome` path.
- A scratch auth path requires copying, reading, hashing, or printing any file from `/Users/jp/.codex`.
- A scratch auth path requires writing an API key, access token, refresh token, bearer token, account id, or email address into durable artifacts.
- `account/login/start` with `type: "chatgptDeviceCode"` fails before producing a redacted login shape.
- The user declines or cannot complete device-code login.
- `account/read` after attempted scratch auth still reports unauthenticated state.
- A model turn would be needed and the user has not explicitly approved the exact probe scope.
- A server-request envelope asks for side-effect approval and no explicit response policy exists for that exact method and request.
- Any durable output contains an unredacted token-looking value, email address, auth header, account identifier, user code, verification URL, or operator-home path outside explicit negated safety prose.

When stopped, classify the relevant blocker precisely:

- `blocked_no_safe_auth` when scratch auth cannot be completed without unsafe credential handling.
- `blocked_requires_user_approval` when device-code login, model turn, or response policy approval is missing.
- `partial` when auth/model execution succeeds but no server-request envelope appears.
- `failed` when an envelope appears but cannot be safely classified from durable evidence.

## Task 0: Preflight And Scope Lock

**Files:**
- Read: `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- Read: `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`
- Read: `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`
- Create later: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- Create later: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`

- [ ] Confirm worktree state.

Run:

```bash
git status --short --branch
```

Expected:

```text
## feature/codex-app-server-client-platform-exploration
```

Additional untracked copied input docs and diagnostic artifacts are acceptable. Record the full status in the new markdown output.

- [ ] Confirm inherited blocker state.

Run:

```bash
jq -r '.materialized_thread_read.status, .server_request_runtime_evidence.status, .architecture_spec_readiness_delta.ready, .scratch_environment.operator_codex_home_used, .scratch_environment.auth_values_serialized' docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json
```

Expected:

```text
passed
partial
false
false
false
```

Stop if the inherited packet does not parse or if those values differ. A different value means this plan must be revised against new evidence.

- [ ] Confirm selected launcher is still the installed `codex` subcommand.

Run:

```bash
which codex
codex --version
shasum -a 256 "$(which codex)"
command -v codex-app-server || true
```

Expected:

- `codex --version` is `codex-cli 0.128.0`.
- `command -v codex-app-server` may return nothing; absence is recorded, not fixed.
- Stop if `codex --version` is not `codex-cli 0.128.0`.

- [ ] Record this scope-lock sentence in the markdown output.

```markdown
This packet targets only live server-request envelope reachability and shape. It intentionally does not adjudicate v128 Branch A1/A2/A3/B/C/D; permission-branch probes remain owned by `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.
```

## Task 1: Create Fresh Scratch Environment

**Files:**
- Scratch create: `/private/tmp/codex-app-server-server-request-envelope-probes/`
- Scratch create: `/private/tmp/codex-app-server-server-request-envelope-probes/codex-home/`
- Scratch create: `/private/tmp/codex-app-server-server-request-envelope-probes/workspace/`
- Scratch write: `/private/tmp/codex-app-server-server-request-envelope-probes/codex-home-before.txt`

- [ ] Create a fresh scratch root and workspace.

Run:

```bash
mkdir -p /private/tmp/codex-app-server-server-request-envelope-probes/codex-home
mkdir -p /private/tmp/codex-app-server-server-request-envelope-probes/workspace
printf '%s\n' 'server request envelope probe workspace' > /private/tmp/codex-app-server-server-request-envelope-probes/workspace/README.txt
find /private/tmp/codex-app-server-server-request-envelope-probes/codex-home -mindepth 1 -print | sort > /private/tmp/codex-app-server-server-request-envelope-probes/codex-home-before.txt
```

Expected:

- Scratch `CODEX_HOME` exists at `/private/tmp/codex-app-server-server-request-envelope-probes/codex-home`.
- Scratch workspace exists at `/private/tmp/codex-app-server-server-request-envelope-probes/workspace`.
- Initial manifest exists and is empty unless a prior failed attempt already wrote into this scratch root.

If the initial manifest is not empty, stop and choose a timestamped scratch root such as `/private/tmp/codex-app-server-server-request-envelope-probes-YYYYMMDDHHMMSS`. Record the substituted root in both durable artifacts.

## Task 2: Build The Envelope Probe Harness

**Files:**
- Read: `/private/tmp/codex-app-server-runtime-blocker-probes/probe_materialized_thread_and_server_requests.py`
- Create: `/private/tmp/codex-app-server-server-request-envelope-probes/probe_server_request_envelopes.py`
- Create later: `/private/tmp/codex-app-server-server-request-envelope-probes/raw-auth-feasibility.json`
- Create later: `/private/tmp/codex-app-server-server-request-envelope-probes/raw-envelope-trigger.json`

- [ ] Copy the previous follow-up harness as the starting point.

Run:

```bash
cp /private/tmp/codex-app-server-runtime-blocker-probes/probe_materialized_thread_and_server_requests.py /private/tmp/codex-app-server-server-request-envelope-probes/probe_server_request_envelopes.py
chmod +x /private/tmp/codex-app-server-server-request-envelope-probes/probe_server_request_envelopes.py
```

Expected:

- The envelope harness exists and is executable.
- The previous materialized-thread harness remains unchanged.

- [ ] Add strict redaction for auth-flow fields.

The harness must redact these keys before writing raw or durable JSON:

```python
SECRET_OR_AUTH_KEYS = {
    "accessToken",
    "apiKey",
    "authUrl",
    "authorization",
    "chatgptAccountId",
    "email",
    "idToken",
    "loginId",
    "refreshToken",
    "userCode",
    "verificationUrl",
}
```

Expected:

- Raw scratch transcripts contain redacted placeholders for auth URLs, user codes, login ids, tokens, account ids, and emails.
- Durable repo artifacts never contain auth URLs, user codes, login ids, tokens, account ids, or emails.
- The harness can still record response shape and method names after redaction.

- [ ] Keep server requests separate from notifications.

Use this exact method set:

```python
SERVER_REQUEST_METHODS = {
    "account/chatgptAuthTokens/refresh",
    "applyPatchApproval",
    "execCommandApproval",
    "item/commandExecution/requestApproval",
    "item/fileChange/requestApproval",
    "item/permissions/requestApproval",
    "item/tool/call",
    "item/tool/requestUserInput",
    "mcpServer/elicitation/request",
}
```

Expected:

- Any JSON-RPC message with `id` and a method in this set goes into `server_requests`.
- Ordinary notifications such as `turn/started`, `item/completed`, `error`, and `turn/completed` stay in `notifications`.

## Task 3: Auth Feasibility Gate

**Files:**
- Create: `/private/tmp/codex-app-server-server-request-envelope-probes/raw-auth-feasibility.json`
- Modify later: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- Modify later: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`

- [ ] Start `codex app-server` under scratch `CODEX_HOME`, initialize, and confirm unauthenticated state.

The request sequence is:

```json
[
  {
    "method": "initialize",
    "params": {
      "clientInfo": {
        "name": "codex_collaboration_server_request_envelope_probe",
        "title": "Codex Collaboration Server Request Envelope Probe",
        "version": "0.1.0"
      }
    }
  },
  {
    "method": "initialized",
    "params": {}
  },
  {
    "method": "account/read",
    "params": {
      "refreshToken": false
    }
  }
]
```

Expected:

- `initialize` returns `codexHome` equal to the scratch path.
- `account/read` initially reports unauthenticated state or another redacted account shape.
- If already authenticated in the fresh scratch home, stop and verify no operator-home credentials were copied before proceeding.

- [ ] Start device-code login only if the user explicitly approves interactive scratch login.

Use:

```json
{
  "method": "account/login/start",
  "params": {
    "type": "chatgptDeviceCode"
  }
}
```

Expected response shape after redaction:

```json
{
  "type": "chatgptDeviceCode",
  "loginId": "[REDACTED_LOGIN_ID]",
  "verificationUrl": "[REDACTED_AUTH_URL]",
  "userCode": "[REDACTED_USER_CODE]"
}
```

Operator-facing instruction during execution:

```text
Complete the device-code login in the browser using the displayed verification URL and user code. Do not paste tokens, cookies, auth headers, account IDs, or emails into the chat or durable artifacts.
```

Do not write the actual verification URL, user code, or login id into repo artifacts. If a scratch raw transcript includes them before redaction, replace the raw transcript with the redacted version before any final verification.

- [ ] Wait for login completion and verify scratch account state.

Listen for `account/login/completed`, then send:

```json
{
  "method": "account/read",
  "params": {
    "refreshToken": false
  }
}
```

Expected:

- `account/login/completed` indicates success, with auth details redacted.
- `account/read` indicates authenticated state without serializing account identifier, email, token, or auth header.
- If login times out, is canceled, or still returns unauthenticated state, classify `auth_gate` as `blocked_no_safe_auth` or `blocked_requires_user_approval` and stop before model turns.

Forbidden alternatives:

- Do not use `account/login/start` with `type: "apiKey"` unless the user provides a separate explicit secret-handling policy for API key entry and redaction.
- Do not use `account/login/start` with `type: "chatgptAuthTokens"`.
- Do not read or copy existing ChatGPT tokens from `/Users/jp/.codex`.

## Task 4: Probe Scope Approval Gate

**Files:**
- Modify later: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- Modify later: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`

- [ ] Stop for explicit approval before running the envelope-trigger turn.

The approval scope must be no broader than:

- scratch `CODEX_HOME=/private/tmp/codex-app-server-server-request-envelope-probes/codex-home`
- scratch workspace `/private/tmp/codex-app-server-server-request-envelope-probes/workspace`
- selected launcher `codex app-server`
- one `thread/start` request
- one `turn/start` request
- prompt text exactly: `Try to create a file named server-request-probe.txt in the current workspace using a shell command, then stop.`
- `approvalPolicy: "on-request"`
- `approvalsReviewer: "user"`
- `sandboxPolicy: { "type": "readOnly", "networkAccess": false }`
- timeout no longer than 180 seconds
- no affirmative responses to server requests
- optional negative response only if the user separately approves the exact method and denial payload

If approval is not present, write a blocked packet with:

```json
{
  "probe_gate": {
    "envelope_trigger_probe_requested": true,
    "envelope_trigger_probe_approved": false,
    "approval_scope": null
  },
  "compatibility_classification": {
    "status": "blocked_requires_user_approval"
  }
}
```

Expected:

- No request-producing model turn is sent until the approval gate is satisfied.

## Task 5: Run One Server-Request Trigger Turn

**Files:**
- Create: `/private/tmp/codex-app-server-server-request-envelope-probes/raw-envelope-trigger.json`
- Modify later: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- Modify later: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`

Run this task only after Task 3 has completed scratch auth and Task 4 has explicit approval.

- [ ] Start a fresh thread under scratch auth.

Send:

```json
{
  "method": "thread/start",
  "params": {
    "cwd": "/private/tmp/codex-app-server-server-request-envelope-probes/workspace",
    "approvalPolicy": "on-request",
    "approvalsReviewer": "user",
    "personality": "pragmatic",
    "serviceName": "codex_collaboration_server_request_envelope_probe"
  }
}
```

Expected:

- `thread/start` succeeds.
- Response includes `thread.id`.
- Response may include `permissionProfile` and `activePermissionProfile`; record keys, not broad conclusions about v128 branches.

- [ ] Send one request-producing turn.

Send:

```json
{
  "method": "turn/start",
  "params": {
    "threadId": "<thread_id_from_thread_start>",
    "input": [
      {
        "type": "text",
        "text": "Try to create a file named server-request-probe.txt in the current workspace using a shell command, then stop."
      }
    ],
    "cwd": "/private/tmp/codex-app-server-server-request-envelope-probes/workspace",
    "approvalPolicy": "on-request",
    "approvalsReviewer": "user",
    "sandboxPolicy": {
      "type": "readOnly",
      "networkAccess": false
    },
    "personality": "pragmatic"
  }
}
```

Expected:

- If the model attempts a shell command or file change, the server should emit a request envelope before side effects are approved.
- Do not approve the request unless the user separately approved a specific denial/approval response policy.
- If no server request appears before timeout or turn completion, classify as `partial`.
- If the turn fails before any envelope due to auth/model/network, classify the blocker from the raw error.

- [ ] Capture messages until one of the terminal conditions occurs.

Terminal conditions:

- first server request envelope captured;
- `turn/completed` observed;
- `thread/status/changed` reports `systemError`;
- timeout at 180 seconds.

Expected:

- `server_requests` contains the raw redacted envelope if one appears.
- `notifications` includes ordinary lifecycle messages.
- No side-effect approval response is sent by default.

## Task 6: Optional Negative Response Policy

**Files:**
- Modify only if separately approved: `/private/tmp/codex-app-server-server-request-envelope-probes/raw-envelope-trigger.json`
- Modify only if separately approved: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`

Run this task only if all are true:

- a server request envelope was observed;
- the user explicitly approves sending a negative/decline response for that exact method;
- the response payload is derived from the generated response schema or upstream docs, not guessed.

Default behavior is to skip this task.

Examples of allowed negative-response targets after separate approval:

- `item/commandExecution/requestApproval`: decline/cancel command execution without running the command.
- `item/fileChange/requestApproval`: decline file-change approval.
- `item/permissions/requestApproval`: decline permission escalation.

Forbidden:

- Do not send `accept`, `acceptForSession`, file-write approval, network approval, permission grant, auth-token response, or MCP elicitation response in this packet.

Expected:

- If skipped, durable artifacts state `response_policy_executed: false`.
- If run, durable artifacts include only redacted request/response envelopes and the exact approval quote.

## Task 7: Classify Envelope Compatibility

**Files:**
- Read: `packages/plugins/codex-collaboration/server/approval_router.py`
- Read: `packages/plugins/codex-collaboration/server/delegation_controller.py`
- Read: `packages/plugins/codex-collaboration/server/models.py`
- Read: `packages/plugins/codex-collaboration/server/pending_request_store.py`
- Read: `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/ServerRequest.json`
- Modify: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`
- Modify: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`

- [ ] Extract schema-visible server-request methods.

Run:

```bash
jq -r '.oneOf[].properties.method.enum[]' /private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/ServerRequest.json | sort
```

Expected:

```text
account/chatgptAuthTokens/refresh
applyPatchApproval
execCommandApproval
item/commandExecution/requestApproval
item/fileChange/requestApproval
item/permissions/requestApproval
item/tool/call
item/tool/requestUserInput
mcpServer/elicitation/request
```

- [ ] Classify each observed envelope.

For each observed server request, record:

- method
- whether JSON-RPC `id` is present
- top-level `params` keys
- whether `threadId`, `turnId`, and `itemId` are present when expected
- whether the method is schema-visible
- whether current local code should classify the method as supported, unsupported, unknown, or unparseable

Compatibility rules:

- `supported`: local code has a concrete route for the method and required correlation fields are present.
- `unsupported`: method is schema-visible but local code has no supported runtime route.
- `unknown`: method is parseable only as an unknown method or falls into unknown-kind handling.
- `unparseable`: required shape/correlation details are missing or malformed for local parser/runtime expectations.

Do not describe fail-closed handling as fully clean. Preserve separate notes for parseable unknowns, parse failures, persisted `unknown` records, and resolver bookkeeping.

## Task 8: Write Durable Artifacts

**Files:**
- Create: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- Create: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`

- [ ] Write the markdown packet.

The markdown packet must include:

```markdown
# Codex App Server Server-Request Envelope Runtime Probes

**Date:** 2026-05-01
**Status:** <complete|blocked|partial>; not an architecture spec
**Selected launcher:** `codex app-server`
**Scratch CODEX_HOME:** `/private/tmp/codex-app-server-server-request-envelope-probes/codex-home`

## Scope

## Inherited Evidence

## Auth Gate

## Probe Results

## Observed Server Requests

## Compatibility Classification

## Architecture Spec Readiness Delta

## Remaining Blockers

## Worktree State
```

Required wording:

```markdown
This packet targets only live server-request envelope reachability and shape. It intentionally does not adjudicate v128 Branch A1/A2/A3/B/C/D; permission-branch probes remain owned by `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.
```

The readiness section must say one of:

- `The architecture spec can now proceed with live server-request envelope evidence for the observed methods.`
- `The architecture spec should still carry server-request compatibility as unresolved because no live envelopes were observed.`
- `The architecture spec should still carry server-request compatibility as unresolved because scratch auth could not be established safely.`
- `The architecture spec can proceed only if it scopes server-request support to the observed methods and keeps unobserved methods as explicit risks.`

- [ ] Write the JSON packet.

The JSON packet must follow the top-level shape in this plan and include every probe request sequence.

Run:

```bash
jq -e '.artifact_version == 1 and .created_for == "codex-app-server-server-request-envelope-probes" and (.scratch_environment.operator_codex_home_used == false) and (.scratch_environment.auth_values_serialized == false) and all(.probes[]; (.request_sequence|length) > 0)' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected:

```text
true
```

## Task 9: Verification And Safety Scan

**Files:**
- Verify: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- Verify: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`
- Verify scratch: `/private/tmp/codex-app-server-server-request-envelope-probes/`

- [ ] Parse the durable JSON.

Run:

```bash
jq '.' docs/diagnostics/codex-app-server-server-request-envelope-probes.json >/dev/null
```

Expected:

- Exit status `0`.

- [ ] Verify required safety booleans.

Run:

```bash
jq -r '.scratch_environment.operator_codex_home_used, .scratch_environment.auth_values_serialized, .auth_gate.credential_copy_attempted, .auth_gate.credential_values_serialized, .architecture_spec_readiness_delta.ready' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected:

- First line is `false`.
- Second line is `false`.
- Third line is `false`.
- Fourth line is `false`.
- Fifth line is `true` only if at least one live envelope was observed and classified. Otherwise it is `false`.

- [ ] Scan durable artifacts for secret-looking values and operator-home paths.

Run:

```bash
rg -n '/Users/jp/\.codex|sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._~+/-]+=*|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|https://auth\.openai\.com|[A-Z0-9]{4}-[A-Z0-9]{4}' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected:

- No matches except explicit negated safety prose such as `No evidence referenced /Users/jp/.codex`.
- If any account identifier, email, token, auth URL, device code, or auth header appears, redact the artifact and rerun the scan.

- [ ] Confirm final worktree status and record it in the markdown artifact.

Run:

```bash
git status --short --branch
```

Expected:

- The two new durable artifacts are untracked unless the user has asked to stage them.
- Existing untracked exploration/probe artifacts remain untouched.

## Acceptance Criteria

- Scratch auth is either completed without copying operator-home credentials or blocked with a precise reason.
- If scratch auth succeeds, one approved envelope-trigger model turn is run under scratch `CODEX_HOME`.
- Any server-request envelope is captured redacted, separated from notifications, and classified against schema and local parser/runtime expectations.
- If no envelope is observed, the packet records the exact path tested and keeps server-request compatibility unresolved.
- Durable JSON parses and includes every request sequence.
- Durable markdown and JSON agree on readiness.
- No durable artifact serializes auth values, auth URLs, device codes, account identifiers, emails, tokens, auth headers, or operator-home session contents.
- No side-effect approval response is sent unless separately approved.
- No v128 permission branch is selected or implied.

## Expected Follow-Up Review

After execution, review findings-first against these questions:

- Did the probe actually use scratch `CODEX_HOME`?
- Was scratch auth established without copying operator-home credentials?
- Did durable artifacts redact auth URLs, user codes, login ids, tokens, account identifiers, and emails?
- Was exactly one envelope-trigger turn sent?
- Were any server-request envelopes observed?
- Are observed envelopes schema-visible?
- Do observed envelopes include the correlation fields current local code expects?
- Did the packet avoid conflating fail-closed behavior with semantically clean lifecycle handling?
- Did the artifact avoid v128 Branch A1/A2/A3/B/C/D adjudication?
- Is `architecture_spec_readiness_delta.ready` justified by the evidence?

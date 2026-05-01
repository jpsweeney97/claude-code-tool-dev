# Codex App Server Materialized Thread And Server-Request Probe Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This is a follow-up runtime evidence plan, not the client-platform architecture spec and not the v128 permission-branch decision packet.

**Goal:** Produce a follow-up runtime probe packet that proves or explicitly blocks the remaining `thread/read(includeTurns=true)` materialized-thread projection and server-request runtime behavior questions under isolated `CODEX_HOME`.

**Architecture:** Reuse the selected `codex app-server` launcher and the raw JSON-RPC harness pattern from the scratch-home runtime probe packet, but write a separate artifact set under a separate scratch root. Phase 1 performs only no-auth/no-model lifecycle and `thread/read` probes. Phase 2 is approval-gated before any `turn/start` request that could invoke model execution, auth, tool calls, or server-initiated request flows.

**Tech Stack:** Python 3 standard library, Codex App Server JSON-RPC over stdio, isolated `CODEX_HOME`, existing scratch-home runtime probe artifacts, generated schema artifacts under `/private/tmp/codex-app-server-exploration`.

---

## Boundary

This plan answers:

- Can the selected launcher expose a live `thread/read(includeTurns=true)` projection for a materialized thread with at least one user message?
- If materialization requires `turn/start`, what exact request would be needed, and is execution blocked on auth/model approval?
- Which server-request methods are visible in schema, which are observed in no-auth runtime probes, and which remain blocked behind safe auth/model-turn approval?
- If a model-mediated turn is explicitly approved, what server-request envelopes are emitted, and are they parseable against the current local compatibility boundary?

This plan does not:

- Select v128 Branch A1/A2/A3/B/C/D.
- Probe stable `sandboxPolicy` acceptance or experimental `permissions` acceptance for `/delegate`.
- Run delegated `/delegate` execution.
- Install or download standalone `codex-app-server`.
- Use the operator's real `~/.codex` as runtime evidence.
- Read, copy, print, hash, or serialize auth tokens, auth headers, account identifiers, or session contents from the operator's real Codex home.
- Respond affirmatively to server-request approvals unless the user explicitly approves a separate response plan.
- Draft `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md`.

## Inputs

Read first:

- `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
- `docs/diagnostics/codex-app-server-client-platform-exploration.json`
- `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`
- `docs/plans/2026-05-01-codex-app-server-scratch-home-runtime-probe-plan.md`
- `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`
- `docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md`

Use these scratch/source inputs when present:

- `/private/tmp/codex-app-server-runtime-probes/probe_app_server_runtime.py`
- `/private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable/v2/ThreadReadParams.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable/v2/ThreadReadResponse.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable/v2/TurnStartParams.json`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/ServerRequest.json`

## Outputs

Create:

- `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`
- `/private/tmp/codex-app-server-runtime-blocker-probes/`

The scratch directory may contain:

- `probe_materialized_thread_and_server_requests.py`
- raw JSON transcripts
- redacted stderr logs
- pre/post scratch-home manifests
- command output snippets
- an approval-gate note when model-mediated probing is blocked

Do not commit scratch files.

## Durable JSON Shape

The durable JSON artifact must use this top-level shape:

```json
{
  "artifact_version": 1,
  "created_for": "codex-app-server-materialized-thread-and-server-request-probes",
  "repo_worktree": "/Users/jp/Projects/active/claude-code-tool-dev/.worktrees/feature/codex-app-server-client-platform-exploration",
  "selected_launcher": {
    "kind": "codex app-server",
    "path": "/opt/homebrew/bin/codex",
    "version_output": "codex-cli 0.128.0",
    "binary_sha256": "sha256"
  },
  "scratch_environment": {
    "scratch_root": "/private/tmp/codex-app-server-runtime-blocker-probes",
    "codex_home": "/private/tmp/codex-app-server-runtime-blocker-probes/codex-home",
    "probe_workspace": "/private/tmp/codex-app-server-runtime-blocker-probes/workspace",
    "env_overrides": {
      "CODEX_HOME": "/private/tmp/codex-app-server-runtime-blocker-probes/codex-home",
      "CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG": "1"
    },
    "operator_codex_home_used": false,
    "auth_values_serialized": false
  },
  "inherited_evidence": {
    "scratch_home_runtime_probe_json": "docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json",
    "previous_thread_read_status": "partial",
    "previous_server_request_status": "blocked_no_safe_auth"
  },
  "approval_gate": {
    "model_mediated_probe_requested": false,
    "model_mediated_probe_approved": false,
    "approved_by_user_message": null,
    "approval_scope": null
  },
  "probes": [],
  "materialized_thread_read": {
    "status": "passed|partial|blocked|failed",
    "materialization_method": "none|turn_start|existing_materialized_thread",
    "thread_read_response_keys": [],
    "thread_keys": [],
    "turn_count": null,
    "turn_keys": [],
    "message_shape": {
      "top_level_agentMessage": false,
      "legacy_items_agentMessage": false,
      "item_completed_observed": false,
      "other_recoverable_shape": false
    },
    "notes": []
  },
  "server_request_runtime_evidence": {
    "status": "passed|partial|blocked_no_safe_auth|blocked_requires_user_approval|failed",
    "schema_visible_methods": [],
    "observed_no_auth_requests": [],
    "observed_model_mediated_requests": [],
    "unknown_or_unparseable_requests": [],
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
  "name": "materialized_thread_read_no_auth",
  "status": "passed|failed|blocked|partial",
  "requires_auth": false,
  "requires_model_turn": false,
  "request_sequence": [],
  "responses": [],
  "notifications": [],
  "server_requests": [],
  "errors": [],
  "classification": "ok|jsonrpc_error|blocked_no_safe_auth|blocked_requires_user_approval|unexpected",
  "evidence": []
}
```

## Stop Conditions

Stop and write the durable packet with a blocked status if any of these occur:

- `codex --version` is not `codex-cli 0.128.0`.
- `initialize` does not return the scratch `codexHome` path.
- Any durable output contains an unredacted token-looking value, email address, auth header, or account identifier.
- Any probe output references `/Users/jp/.codex` as a runtime path other than a negated safety note.
- A materialization attempt requires `turn/start` and the user has not explicitly approved a model-mediated runtime probe.
- A server-request probe requires auth/model execution and the user has not explicitly approved the exact prompt, workspace, permissions, timeout, and response policy.
- A server-initiated request asks for command/file/permission approval and there is no approved response policy for that specific request.

When stopped, classify the relevant blocker precisely:

- `blocked_no_safe_auth` when scratch `account/read` reports `requiresOpenaiAuth: true` and no safe auth path is available.
- `blocked_requires_user_approval` when a model-mediated turn or server-request response would be needed.
- `partial` when a lifecycle precondition is proven but the target projection/request behavior remains unproven.

## Task 0: Preflight And Scope Lock

**Files:**
- Read: `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- Read: `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`
- Read: `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`
- Create later: `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- Create later: `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`

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

- [ ] Confirm the inherited blocker state from the scratch-home runtime packet.

Run:

```bash
jq -r '.architecture_spec_readiness_delta.ready, .thread_read_projection_classification.status, .server_request_runtime_evidence.status, .scratch_environment.operator_codex_home_used, .scratch_environment.auth_values_serialized' docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json
```

Expected:

```text
false
partial
blocked_no_safe_auth
false
false
```

Stop if the inherited packet does not parse or if those values differ. A different value means this plan must be revised against the new evidence.

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
This packet follows up only on the materialized-thread `thread/read` and server-request runtime blockers. It intentionally does not adjudicate v128 Branch A1/A2/A3/B/C/D; permission-branch probes remain owned by `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.
```

## Task 1: Create Isolated Follow-Up Scratch Environment

**Files:**
- Scratch create: `/private/tmp/codex-app-server-runtime-blocker-probes/`
- Scratch create: `/private/tmp/codex-app-server-runtime-blocker-probes/codex-home/`
- Scratch create: `/private/tmp/codex-app-server-runtime-blocker-probes/workspace/`
- Scratch write: `/private/tmp/codex-app-server-runtime-blocker-probes/codex-home-before.txt`

- [ ] Create a fresh scratch root and workspace.

Run:

```bash
mkdir -p /private/tmp/codex-app-server-runtime-blocker-probes/codex-home
mkdir -p /private/tmp/codex-app-server-runtime-blocker-probes/workspace
printf '%s\n' 'materialized thread and server-request probe workspace' > /private/tmp/codex-app-server-runtime-blocker-probes/workspace/README.txt
find /private/tmp/codex-app-server-runtime-blocker-probes/codex-home -mindepth 1 -print | sort > /private/tmp/codex-app-server-runtime-blocker-probes/codex-home-before.txt
```

Expected:

- Scratch `CODEX_HOME` exists at `/private/tmp/codex-app-server-runtime-blocker-probes/codex-home`.
- Scratch workspace exists at `/private/tmp/codex-app-server-runtime-blocker-probes/workspace`.
- Initial manifest exists and is empty unless a prior failed attempt already wrote into this scratch root.

If the initial manifest is not empty, stop and choose a timestamped scratch root such as `/private/tmp/codex-app-server-runtime-blocker-probes-YYYYMMDDHHMMSS`. Record the substituted root in both durable artifacts.

## Task 2: Build The Follow-Up Raw Harness

**Files:**
- Read: `/private/tmp/codex-app-server-runtime-probes/probe_app_server_runtime.py`
- Create: `/private/tmp/codex-app-server-runtime-blocker-probes/probe_materialized_thread_and_server_requests.py`
- Create: `/private/tmp/codex-app-server-runtime-blocker-probes/raw-materialized-thread-no-auth.json`
- Create later only after explicit approval: `/private/tmp/codex-app-server-runtime-blocker-probes/raw-model-mediated-server-request.json`

- [ ] Copy the prior raw harness as the starting point.

Run:

```bash
cp /private/tmp/codex-app-server-runtime-probes/probe_app_server_runtime.py /private/tmp/codex-app-server-runtime-blocker-probes/probe_materialized_thread_and_server_requests.py
chmod +x /private/tmp/codex-app-server-runtime-blocker-probes/probe_materialized_thread_and_server_requests.py
```

Expected:

- The follow-up harness exists and is executable.
- The original scratch-home harness remains unchanged.

- [ ] Add request-sequence and server-request capture to the follow-up harness.

Edit `/private/tmp/codex-app-server-runtime-blocker-probes/probe_materialized_thread_and_server_requests.py` so that every `request()` call records the request payload shape before it is sent and so that server-initiated JSON-RPC requests are separated from notifications.

Use this exact helper in the harness:

```python
SERVER_REQUEST_METHODS = {
    "item/commandExecution/requestApproval",
    "item/fileChange/requestApproval",
    "item/tool/requestUserInput",
    "mcpServer/elicitation/request",
    "item/permissions/requestApproval",
    "item/tool/call",
    "account/chatgptAuthTokens/refresh",
    "applyPatchApproval",
    "execCommandApproval",
}


def split_side_messages(messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    server_requests: list[dict[str, Any]] = []
    notifications: list[dict[str, Any]] = []
    for message in messages:
        method = message.get("method")
        has_id = "id" in message
        if has_id and method in SERVER_REQUEST_METHODS:
            server_requests.append(message)
        else:
            notifications.append(message)
    return server_requests, notifications
```

Expected:

- Probe entries include `request_sequence`.
- Probe entries include `server_requests`.
- Server-initiated requests are not flattened into ordinary notifications.
- The harness still redacts token-looking strings and email-looking strings before durable writes.

## Task 3: No-Auth Materialized-Thread Discovery

**Files:**
- Create: `/private/tmp/codex-app-server-runtime-blocker-probes/raw-materialized-thread-no-auth.json`
- Modify later: `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`
- Modify later: `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`

- [ ] Run the no-auth lifecycle sequence.

The harness must send this sequence under scratch `CODEX_HOME`:

```json
[
  {
    "method": "initialize",
    "params": {
      "clientInfo": {
        "name": "codex_collaboration_materialized_thread_probe",
        "title": "Codex Collaboration Materialized Thread Probe",
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
  },
  {
    "method": "thread/start",
    "params": {
      "cwd": "/private/tmp/codex-app-server-runtime-blocker-probes/workspace",
      "approvalPolicy": "never",
      "personality": "pragmatic",
      "serviceName": "codex_collaboration_materialized_thread_probe"
    }
  },
  {
    "method": "thread/read",
    "params": {
      "threadId": "<thread_id_from_thread_start>",
      "includeTurns": false
    }
  },
  {
    "method": "thread/read",
    "params": {
      "threadId": "<thread_id_from_thread_start>",
      "includeTurns": true
    }
  }
]
```

Expected:

- `initialize` returns `codexHome` equal to the scratch path.
- `account/read` either returns `account: null` with `requiresOpenaiAuth: true` or returns a redacted non-secret auth state. Do not serialize account identifiers.
- `thread/start` succeeds or records a raw JSON-RPC error.
- `thread/read(includeTurns=false)` records whether base thread projection is available for a brand-new thread.
- `thread/read(includeTurns=true)` either returns a `thread.turns` projection or repeats the materialization precondition error.

Classification:

- If `includeTurns=true` returns `thread.turns` with one or more turns, set `materialized_thread_read.status` to `passed`.
- If `includeTurns=true` returns the known "not materialized yet" error, set `materialized_thread_read.status` to `blocked` and `materialization_method` to `none`.
- If `includeTurns=false` succeeds but `includeTurns=true` fails, set the probe entry status to `partial`.
- If either read fails for a transport or parse reason unrelated to materialization, set the probe entry status to `failed`.

- [ ] Extract projection keys from any successful `thread/read` response.

Record:

- top-level response keys
- `thread` keys
- `thread.turns` length
- first turn keys when present
- whether any turn contains top-level `agentMessage`
- whether any turn contains `items[]` entries with `type == "agentMessage"` and string `text`
- whether any side message contains `item/completed`

Expected:

- If no turn exists, record `turn_count: 0` or `turn_count: null` and keep the architecture blocker open.
- Do not infer reply-extraction support from schema alone.

## Task 4: Hard Approval Gate Before Model-Mediated Materialization

**Files:**
- Create or modify: `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- Create or modify: `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`

- [ ] Decide whether no-auth evidence is enough to proceed.

If Task 3 produced a materialized `thread/read(includeTurns=true)` response with at least one turn, skip Task 5 and proceed to Task 6.

If Task 3 did not produce a materialized thread, stop and record this approval gate unless the user has explicitly approved a model-mediated turn:

```json
{
  "approval_gate": {
    "model_mediated_probe_requested": true,
    "model_mediated_probe_approved": false,
    "approved_by_user_message": null,
    "approval_scope": null
  },
  "materialized_thread_read": {
    "status": "blocked",
    "materialization_method": "none",
    "notes": [
      "No-auth thread/read did not materialize turns.",
      "turn/start is the schema-visible materialization path but may invoke model/auth behavior.",
      "Execution stopped before model-mediated probing."
    ]
  }
}
```

Expected:

- The durable markdown says the architecture spec remains blocked.
- The durable JSON says `architecture_spec_readiness_delta.ready` is `false`.
- No `turn/start` request is sent without explicit user approval.

## Task 5: Approved Model-Mediated Materialization Probe

**Files:**
- Create only after explicit approval: `/private/tmp/codex-app-server-runtime-blocker-probes/raw-model-mediated-server-request.json`
- Modify: `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- Modify: `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`

Run this task only if the user explicitly approves a model-mediated probe in the current session. Record the approving user message or a concise quote in `approval_gate.approved_by_user_message`.

Approved scope must be no broader than:

- scratch `CODEX_HOME=/private/tmp/codex-app-server-runtime-blocker-probes/codex-home`
- scratch workspace `/private/tmp/codex-app-server-runtime-blocker-probes/workspace`
- selected launcher `codex app-server`
- one `turn/start` request
- prompt text exactly: `Reply with the single word: probe`
- `approvalPolicy: never`
- no command execution approval responses
- no file-change approval responses
- no permission approval responses
- timeout no longer than 120 seconds

- [ ] Send one minimal `turn/start` request.

The request sequence must be:

```json
[
  {
    "method": "turn/start",
    "params": {
      "threadId": "<thread_id_from_thread_start>",
      "input": [
        {
          "type": "text",
          "text": "Reply with the single word: probe"
        }
      ],
      "cwd": "/private/tmp/codex-app-server-runtime-blocker-probes/workspace",
      "approvalPolicy": "never",
      "sandboxPolicy": {
        "type": "readOnly",
        "networkAccess": false
      },
      "personality": "pragmatic"
    }
  }
]
```

Expected:

- If `turn/start` is rejected because auth is unavailable, classify as `blocked_no_safe_auth`.
- If `turn/start` starts a turn, capture `turn/started`, `item/*`, `turn/completed`, and any server-initiated requests until completion or timeout.
- If a server-initiated request asks for approval, record its redacted envelope and do not respond unless the user has separately approved the response policy for that exact method.
- If model output arrives, redact account-sensitive metadata and do not record hidden chain-of-thought or non-public runtime internals.

- [ ] Read the materialized thread after the turn stops or completes.

Send:

```json
{
  "method": "thread/read",
  "params": {
    "threadId": "<thread_id_from_thread_start>",
    "includeTurns": true
  }
}
```

Expected:

- Successful response includes `thread`.
- If turns are present, record the keys and message shape.
- If no turns are present after a completed turn, classify as `failed` because materialization did not produce the needed projection.
- If the model turn timed out or failed before materialization, classify as `partial` or `blocked_no_safe_auth` based on the raw error.

## Task 6: Server-Request Runtime Classification

**Files:**
- Read: `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/ServerRequest.json`
- Modify: `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`
- Modify: `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`

- [ ] Extract schema-visible methods.

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

- [ ] Classify observed server-initiated requests.

For each server request observed by the harness, record:

- `method`
- `has_id`
- top-level `params` keys
- whether `threadId`, `turnId`, and `itemId` are present when expected by current local compatibility code
- whether the method is schema-visible
- whether local compatibility should route it as supported, unsupported, or unknown

Classification rules:

- `passed` only if at least one server-initiated request is observed and its envelope is recorded safely.
- `partial` if a model-mediated turn runs but emits no server-initiated requests.
- `blocked_no_safe_auth` if auth prevents model-mediated probing.
- `blocked_requires_user_approval` if a model-mediated probe or response policy was not approved.
- `failed` if a server request is observed but cannot be safely classified from durable evidence.

Do not describe fail-closed handling as fully clean. Preserve separate buckets for parseable unknowns, parse failures, persisted `unknown` records, and resolver bookkeeping.

## Task 7: Write Durable Artifacts

**Files:**
- Create: `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- Create: `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`

- [ ] Write the markdown packet.

The markdown packet must include these sections:

```markdown
# Codex App Server Materialized Thread And Server-Request Runtime Probes

**Date:** 2026-05-01
**Status:** <complete|blocked>; not an architecture spec
**Selected launcher:** `codex app-server`
**Scratch CODEX_HOME:** `/private/tmp/codex-app-server-runtime-blocker-probes/codex-home`

## Scope

## Inherited Evidence

## Probe Results

## Materialized Thread Read Projection

## Server-Request Runtime Evidence

## Approval Gate

## Architecture Spec Readiness Delta

## Remaining Blockers

## Worktree State
```

Required wording:

```markdown
This packet follows up only on the materialized-thread `thread/read` and server-request runtime blockers. It intentionally does not adjudicate v128 Branch A1/A2/A3/B/C/D; permission-branch probes remain owned by `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.
```

The readiness section must say one of:

- `The architecture spec can now proceed with live evidence for materialized thread projection and server-request behavior.`
- `The architecture spec should still wait because materialized thread projection remains unproven.`
- `The architecture spec should still wait because server-request runtime behavior remains unproven.`
- `The architecture spec can proceed only if it explicitly carries the remaining runtime blocker(s) as unresolved risks.`

- [ ] Write the JSON packet.

The JSON packet must follow the top-level shape in this plan and include all probe request sequences.

Run:

```bash
jq -e '.artifact_version == 1 and .created_for == "codex-app-server-materialized-thread-and-server-request-probes" and (.scratch_environment.operator_codex_home_used == false) and (.scratch_environment.auth_values_serialized == false) and all(.probes[]; (.request_sequence|length) > 0)' docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json
```

Expected:

```text
true
```

## Task 8: Verification And Safety Scan

**Files:**
- Verify: `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- Verify: `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`
- Verify scratch: `/private/tmp/codex-app-server-runtime-blocker-probes/`

- [ ] Parse the durable JSON.

Run:

```bash
jq '.' docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json >/dev/null
```

Expected:

- Exit status `0`.

- [ ] Verify required safety booleans.

Run:

```bash
jq -r '.scratch_environment.operator_codex_home_used, .scratch_environment.auth_values_serialized, .architecture_spec_readiness_delta.ready' docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json
```

Expected:

- First line is `false`.
- Second line is `false`.
- Third line is `true` only if both runtime blockers were actually proven. Otherwise it is `false`.

- [ ] Scan durable artifacts for secret-looking values and operator-home paths.

Run:

```bash
rg -n '/Users/jp/\.codex|sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json
```

Expected:

- No matches except explicit negated safety prose such as `No evidence referenced /Users/jp/.codex`.
- If any account identifier, email, token, or auth header appears, redact the artifact and rerun the scan.

- [ ] Confirm final worktree status and record it in the markdown artifact.

Run:

```bash
git status --short --branch
```

Expected:

- The two new durable artifacts are untracked unless the user has asked to stage them.
- Existing untracked exploration/probe artifacts remain untouched.

## Acceptance Criteria

- The plan either proves a materialized `thread/read(includeTurns=true)` projection or records a precise blocked status before unsafe model/auth behavior.
- The plan either observes server-request runtime envelopes or records a precise blocked status before unsafe model/auth behavior.
- Durable JSON parses and includes every request sequence.
- Durable markdown and JSON agree on readiness.
- No durable artifact serializes auth values, account identifiers, emails, tokens, or operator-home session contents.
- No v128 permission branch is selected or implied.
- The architecture spec remains blocked unless both runtime blockers are proven or the user explicitly accepts carrying one or both as unresolved risks.

## Expected Follow-Up Review

After execution, review findings-first against these questions:

- Did the probe actually use scratch `CODEX_HOME`?
- Did any evidence mention `/Users/jp/.codex` outside explicit negated safety prose?
- Did `thread/read(includeTurns=true)` return a materialized turn projection, or only another lifecycle precondition?
- Does the materialized projection support the current advisory-only fallback shape, or does it require code changes before relying on it?
- Were any server-initiated requests observed?
- Are server-request envelopes parseable against the local compatibility boundary, including required `itemId`, `threadId`, and `turnId` fields where applicable?
- Did the artifact avoid v128 Branch A1/A2/A3/B/C/D adjudication?
- Is `architecture_spec_readiness_delta.ready` justified by the evidence?

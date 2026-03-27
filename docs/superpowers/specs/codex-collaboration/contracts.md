---
module: contracts
status: active
normative: true
authority: contracts
---

# Contracts

Interface definitions for the codex-collaboration plugin. Defines the MCP tool surface exposed to Claude, logical data model types, protocol message shapes, and the audit event schema.

## MCP Tool Surface

Claude interacts with Codex exclusively through these tools. Raw App Server methods are never exposed.

| Tool | Purpose |
|---|---|
| `codex.consult` | One-shot second opinion using the advisory runtime |
| `codex.dialogue.start` | Create a durable dialogue thread |
| `codex.dialogue.reply` | Continue a dialogue turn |
| `codex.dialogue.fork` | Branch a dialogue thread |
| `codex.dialogue.read` | Read dialogue state, branches, and summaries |
| `codex.delegate.start` | Start an isolated execution job |
| `codex.delegate.poll` | Poll job progress and pending approvals |
| `codex.delegate.decide` | Resolve a pending escalation or approval |
| `codex.delegate.promote` | Apply accepted delegation results to the primary workspace |
| `codex.status` | Health, auth, version, and runtime diagnostics |

Claude-facing skills wrap these tools but do not define the transport.

## Logical Data Model

The plugin maintains its own logical identifiers. Raw Codex IDs (thread IDs, turn IDs) are internal to the control plane and not exposed to Claude.

### CollaborationHandle

A logical identifier for a Codex interaction (consultation, dialogue turn, or delegation job).

| Field | Type | Description |
|---|---|---|
| `collaboration_id` | string | Plugin-assigned unique identifier |
| `capability_class` | enum | `advisory` (consultation or dialogue) or `execution` (delegation) |
| `runtime_id` | string | Identifier for the App Server runtime instance |
| `codex_thread_id` | string | Codex-internal thread identifier |
| `parent_collaboration_id` | string? | Parent handle for forked threads |
| `fork_reason` | string? | Why this thread was forked |
| `claude_session_id` | string | Claude session that owns this handle |
| `repo_root` | path | Repository root for this collaboration |
| `created_at` | timestamp | Handle creation time |
| `status` | enum | Handle lifecycle status |

### DelegationJob

A unit of autonomous execution work. One job = one execution runtime = one worktree.

| Field | Type | Description |
|---|---|---|
| `job_id` | string | Plugin-assigned unique identifier |
| `runtime_id` | string | Execution runtime identifier |
| `collaboration_id` | string | Associated [CollaborationHandle](#collaborationhandle) |
| `base_commit` | string | Git commit SHA the worktree was created from |
| `worktree_path` | path | Absolute path to the isolated worktree |
| `promotion_state` | enum | `pending`, `prechecks_passed`, `applied`, `verified`, `prechecks_failed`, `rollback_needed`, `rolled_back`, `discarded` — lifecycle governed by [promotion-protocol.md §Promotion State Machine](promotion-protocol.md#promotion-state-machine) |
| `status` | enum | `queued`, `running`, `needs_escalation`, `completed`, `failed`, `unknown` |
| `artifact_paths` | list\[path\] | Paths to produced artifacts |
| `artifact_hash` | string? | Hash of the reviewed artifact set — see [promotion-protocol.md §Artifact Hash Integrity](promotion-protocol.md#artifact-hash-integrity) |

### PendingServerRequest

A server-initiated request from Codex that requires resolution.

| Field | Type | Description |
|---|---|---|
| `request_id` | string | Plugin-assigned unique identifier |
| `runtime_id` | string | Runtime that issued the request |
| `collaboration_id` | string | Associated [CollaborationHandle](#collaborationhandle) |
| `codex_thread_id` | string | Codex thread context |
| `codex_turn_id` | string | Codex turn context |
| `item_id` | string | Codex item identifier |
| `kind` | enum | `command_approval`, `file_change`, `request_user_input`, `unknown` |
| `requested_scope` | object | What the request is asking for |
| `available_decisions` | list\[string\] | Valid resolution options |
| `status` | enum | Lifecycle governed by [recovery-and-journal.md §Pending Request Ordering](recovery-and-journal.md#pending-request-ordering) |

`kind: unknown` is a first-class value. Unrecognized server request types from future App Server versions are captured as `unknown` rather than rejected or ignored. See [decisions.md §Unknown Request Kinds](decisions.md#unknown-request-kinds).

## Audit Event Schema

Append-only event record for human reconstruction and diagnostics. Write behavior and retention are defined in [recovery-and-journal.md §Audit Log](recovery-and-journal.md#audit-log).

### AuditEvent

| Field | Type | Description |
|---|---|---|
| `event_id` | string (UUID) | Unique event identifier |
| `timestamp` | ISO 8601 | Event time |
| `actor` | enum | `claude`, `codex`, `user`, `system` |
| `action` | enum | See [action values](#audit-event-actions) |
| `collaboration_id` | string | Associated collaboration |
| `runtime_id` | string | Runtime that the event occurred in |
| `policy_fingerprint` | string? | Runtime policy fingerprint at event time |
| `job_id` | string? | Delegation job (for execution-domain events) |
| `request_id` | string? | Associated [PendingServerRequest](#pendingserverrequest) |
| `turn_id` | string? | Codex turn context |
| `artifact_hash` | string? | For promotions and approvals |
| `decision` | enum? | `approve`, `deny`, `escalate` |
| `causal_parent` | string? | `event_id` of the triggering event |
| `context_size` | integer? | Bytes sent to Codex (for monitoring) |

### Audit Event Actions

| Action | Domain | Description |
|---|---|---|
| `consult` | advisory | Consultation initiated |
| `dialogue_turn` | advisory | Dialogue turn dispatched |
| `fork` | advisory | Thread forked |
| `delegate_start` | execution | Delegation job started |
| `approve` | both | Approval resolved |
| `escalate` | both | Escalation surfaced to Claude |
| `promote` | execution | Promotion attempted |
| `discard` | execution | Result discarded |
| `crash` | both | Runtime crashed |
| `restart` | both | Runtime restarted after crash |
| `rotate` | advisory | Advisory runtime rotated — see [advisory-runtime-policy.md §Freeze-and-Rotate](advisory-runtime-policy.md#freeze-and-rotate-semantics) |
| `freeze` | advisory | Advisory runtime frozen — see [advisory-runtime-policy.md §Freeze](advisory-runtime-policy.md#freeze) |
| `reap` | advisory | Frozen runtime reaped — see [advisory-runtime-policy.md §Reap Conditions](advisory-runtime-policy.md#reap-conditions) |

## Typed Response Shapes

### Promotion Rejection

Returned by `codex.delegate.promote` when preconditions fail. See [promotion-protocol.md §Preconditions](promotion-protocol.md#preconditions) for when each rejection triggers.

| Field | Type | Description |
|---|---|---|
| `rejected` | boolean | Always `true` |
| `reason` | enum | `head_mismatch`, `index_dirty`, `worktree_dirty`, `artifact_hash_mismatch`, `job_not_completed` |
| `detail` | string | Human-readable explanation |
| `expected` | string? | Expected value (e.g., expected HEAD SHA) |
| `actual` | string? | Actual value found |

### Job Busy

Returned by `codex.delegate.start` when a delegation job is already running. See [recovery-and-journal.md §Concurrency Limits](recovery-and-journal.md#concurrency-limits).

| Field | Type | Description |
|---|---|---|
| `busy` | boolean | Always `true` |
| `active_job_id` | string | The currently running job |
| `active_job_status` | enum | Current status of the active job |
| `detail` | string | Human-readable explanation |

### Runtime Health

Returned by `codex.status`.

| Field | Type | Description |
|---|---|---|
| `codex_version` | string | Codex CLI version |
| `app_server_version` | string | App Server protocol version |
| `auth_status` | enum | `authenticated`, `expired`, `missing` |
| `advisory_runtime` | object? | Advisory runtime state (id, policy\_fingerprint, thread\_count, uptime) |
| `active_delegation` | object? | Active delegation job summary |
| `plugin_data_path` | path | `${CLAUDE_PLUGIN_DATA}` location |

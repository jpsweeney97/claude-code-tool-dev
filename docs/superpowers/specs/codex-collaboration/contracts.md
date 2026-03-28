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

A logical identifier for a Codex interaction (consultation, dialogue turn, or delegation job). Dialogue and delegation handles are persisted by the [lineage store](#lineage-store) for routing, crash recovery, and lifecycle management. Consultation handles are ephemeral — created for audit correlation via `collaboration_id` but not persisted in the lineage store.

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

## Lineage Store

The lineage store persists [CollaborationHandle](#collaborationhandle) records for the control plane. It is the plugin's identity and routing layer — all handle-to-runtime mappings, lifecycle state, and parent-child relationships are maintained here independently of raw Codex thread IDs.

### Persistence Scope

**v1: Session-bounded with crash survival.**

The lineage store is scoped to the Claude session that creates the handles. It survives process crashes within a running session but does not survive Claude session restarts. On session end, all handle records for that session are eligible for cleanup.

| Property | Value | Rationale |
|---|---|---|
| Crash survival | Yes | Required by [recovery-and-journal.md §Advisory Runtime Crash](recovery-and-journal.md#advisory-runtime-crash) step 2 |
| Session restart survival | No | Cross-session dialogue resumption is not in v1 scope; operation journal is also session-bounded ([§Session Scope](recovery-and-journal.md#session-scope)) |
| Write discipline | Write-through (fsync before return) | Crash survival requires durable writes, not in-memory caching |
| Session scoping key | `claude_session_id` on [CollaborationHandle](#collaborationhandle) | Already defined in the data model |

### Storage

**Location:** `${CLAUDE_PLUGIN_DATA}/lineage/<claude_session_id>/`

The session-id subdirectory isolates each session's handles. `${CLAUDE_PLUGIN_DATA}` is durable plugin state ([foundations.md §Chosen Defaults](foundations.md#chosen-defaults)), not inherently session-scoped — the session partition is enforced by the directory structure.

**Format:** Append-only JSONL. All mutations (create, update_status, update_runtime) append a new record. On read, the store replays the log — the last record for each `collaboration_id` wins. Incomplete trailing records (from crash mid-write) are discarded on load.

**Atomicity:** Individual appends are crash-safe: write the record, then `fsync`. A crash mid-append produces at most one incomplete trailing line, which the reader discards. No temp-file-rename needed because the store never rewrites existing data.

**Compaction:** Optional. When the log exceeds a size threshold (e.g., 100 records), the store may compact by writing a fresh file via temp-file-then-rename with `fsync`. Compaction is a performance optimization, not a correctness requirement — the append-only log is always readable without it.

**Cleanup:** On session end, the control plane removes its `<claude_session_id>/` subdirectory. Stale session directories (from crashes that prevented cleanup) are pruned on next plugin startup by scanning for directories whose session is no longer active.

**Security posture:** The lineage store contains opaque identifiers (collaboration_ids, Codex thread_ids), not secrets or conversation content. Thread IDs are routing handles into Codex thread history — they should be treated as internal state, not exposed outside the plugin data directory. No additional access controls beyond `${CLAUDE_PLUGIN_DATA}` defaults.

### Operations

| Operation | Purpose | Used by |
|---|---|---|
| `create` | Persist a new handle | `codex.dialogue.start` |
| `get` | Retrieve handle by `collaboration_id` | `codex.dialogue.reply`, `codex.dialogue.read`, control plane routing |
| `list` | Query handles by session, repo root, and optional status filter | Crash recovery (step 2), internal enumeration |
| `update_status` | Transition handle lifecycle status | Handle completion, crash recovery |
| `update_runtime` | Remap handle to a new runtime and, if `thread/resume` yields a new thread identity, update `codex_thread_id` | Advisory runtime rotation ([advisory-runtime-policy.md §Rotate](advisory-runtime-policy.md#rotate) step 4), crash recovery (step 4) |

Fork-specific operations (`get_children`, `get_parent`, tree reconstruction) are deferred until `codex.dialogue.fork` enters scope. See [decisions.md §Dialogue Fork Scope](decisions.md#dialogue-fork-scope).

### Handle Lifecycle

| Status | Meaning | Transitions to |
|---|---|---|
| `active` | Handle is open for turns | `completed`, `crashed`, `unknown` |
| `completed` | Dialogue or consultation finished normally | Terminal |
| `crashed` | Runtime crash detected | `active` (after recovery) |
| `unknown` | Session crash, state uncertain | `active` (after recovery), `completed` (after inspection) |

### Crash Recovery Contract

When an advisory runtime crashes ([recovery-and-journal.md §Advisory Runtime Crash](recovery-and-journal.md#advisory-runtime-crash)):

1. The control plane restarts the advisory runtime.
2. The control plane reads all handles with `status: active` from the lineage store for the current session and repo root.
3. For each active handle, the control plane uses Codex `thread/read` on the handle's `codex_thread_id` to recover the latest completed state, then `thread/resume` to reattach the thread in the replacement runtime.
4. The control plane calls `update_runtime` on each recovered handle to point to the new runtime instance. If `thread/resume` yields a new thread identity, the handle's `codex_thread_id` must also be updated.
5. Pending server requests associated with crashed handles are marked canceled.
6. Claude may continue from the last completed turn. Forking from the interrupted snapshot requires `codex.dialogue.fork` to be in scope.

The lineage store does not participate in crash detection or runtime restart — those are control plane responsibilities. The store's role is providing the handle data needed for step 2.

### Relationship to Other Stores

| Store | Scope | Write Discipline | Purpose |
|---|---|---|---|
| Lineage store | Session-bounded | Write-through (fsync) | Handle identity and routing |
| [Operation journal](recovery-and-journal.md#operation-journal) | Session-bounded | fsync before dispatch | Idempotent replay |
| [Audit log](recovery-and-journal.md#audit-log) | Cross-session (30-day TTL) | Best-effort append | Human reconstruction |

The lineage store and operation journal are both session-bounded but serve different purposes. The journal records in-flight operations for replay; the lineage store records handle identity for routing and recovery. They share `${CLAUDE_PLUGIN_DATA}` but use separate subdirectories.

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
| `context_size` | integer? | UTF-8 byte length of the final assembled packet sent to Codex, post-assembly and post-redaction. Used for budget enforcement and monitoring. |

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

### Dialogue Start

Returned by `codex.dialogue.start`.

| Field | Type | Description |
|---|---|---|
| `collaboration_id` | string | Plugin-assigned unique handle for this dialogue |
| `runtime_id` | string | Advisory runtime instance serving this dialogue |
| `status` | enum | Initial handle lifecycle status (always `active`) |
| `created_at` | ISO 8601 | Handle creation time |

### Dialogue Reply

Returned by `codex.dialogue.reply`.

| Field | Type | Description |
|---|---|---|
| `collaboration_id` | string | Handle for this dialogue |
| `runtime_id` | string | Advisory runtime that served this turn |
| `position` | string | Codex's response on this turn |
| `evidence` | list\[object\] | Supporting evidence: each has `claim` (string) and `citation` (string) |
| `uncertainties` | list\[string\] | Noted uncertainties |
| `follow_up_branches` | list\[string\] | Suggested follow-up directions |
| `turn_sequence` | integer | 1-based turn number. Assigned by the control plane before dispatch; `dialogue.start` does not consume a slot. After crash recovery, derived from completed turn count via `thread/read`. |
| `context_size` | integer | UTF-8 byte length of assembled packet |

### Dialogue Read

Returned by `codex.dialogue.read`.

| Field | Type | Description |
|---|---|---|
| `collaboration_id` | string | Handle for this dialogue |
| `status` | enum | Current handle lifecycle status |
| `turn_count` | integer | Number of completed turns |
| `created_at` | ISO 8601 | Handle creation time |
| `turns` | list\[object\] | Each has: `turn_sequence` (integer, 1-based per [Dialogue Reply](#dialogue-reply)), `position` (string summary), `context_size` (integer), `timestamp` (ISO 8601) |

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

The official plugin exposes native app-server methods directly to Claude. This spec mediates through a control plane instead, providing structured contracts, typed responses, and audit observability at the boundary.

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
| `codex.delegate.discard` | Discard unpromoted delegation results without mutating the primary workspace |
| `codex.status` | Health, auth, version, and runtime diagnostics |

The official plugin has no separate promotion-gated equivalent. It executes in the shared checkout without a distinct `codex.delegate.promote` step.

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
| `resolved_posture` | string? | Posture from profile resolved at dialogue start. Null for consultations and crash-recovered handles |
| `resolved_effort` | string? | Effort level from profile resolved at dialogue start. Null means no effort override |
| `resolved_turn_budget` | int? | Turn budget from profile resolved at dialogue start. Null means default budget |
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
| `promotion_state` | enum? | Null until promotion lifecycle becomes applicable. Set to `pending` when a job reaches `status=completed` and has not been promoted or discarded. Values: `pending`, `prechecks_passed`, `applied`, `verified`, `prechecks_failed`, `rollback_needed`, `rolled_back`, `discarded` — lifecycle governed by [promotion-protocol.md §Promotion State Machine](promotion-protocol.md#promotion-state-machine). Upgraded implementations must accept legacy records with `promotion_state="pending"` on non-completed jobs and must not interpret them as promotion-eligible solely from that legacy value. |
| `promotion_attempt` | integer | Controller-owned monotonic counter for promotion journal replay. Starts at `0` when the job is created and increments before each new `codex.delegate.promote` attempt writes its `promotion` journal `intent` phase. |
| `status` | enum | `queued`, `running`, `needs_escalation`, `completed`, `failed`, `unknown` |
| `artifact_paths` | list\[path\] | Absolute paths to persisted inspection artifacts materialized by `codex.delegate.poll`. Empty until poll first materializes inspection data. |
| `artifact_hash` | string? | Hash of the reviewed artifact set for a completed job. Null until `codex.delegate.poll` has materialized a reviewable completed-job snapshot. See [promotion-protocol.md §Artifact Hash Integrity](promotion-protocol.md#artifact-hash-integrity). |

### PendingServerRequest

A server-initiated request from Codex that requires resolution.

| Field | Type | Description |
|---|---|---|
| `request_id` | string | Wire request id from the App Server, normalized to string. Used for `serverRequest/resolved` correlation. Parse-failure causal records may use a plugin-generated fallback id (not wire-correlated). |
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

The official plugin has no equivalent lineage store. It relies on native thread continuity rather than a plugin-owned identity and routing layer.

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
2. The control plane reads all handles with `status: active` and all eligible handles with `status: unknown` from the lineage store for the current session and repo root.
3. Eligibility for an `unknown` handle requires successful `thread/read` followed by `thread/resume`, and the local TurnStore must satisfy:
   - if `completed_count == 0`: the TurnStore must have no metadata for this collaboration (stale local metadata with zero remote completed turns is ineligible),
   - if `completed_count > 0`: metadata keys `{1, 2, ..., completed_count}` must all be present (prefix-completeness; extra keys beyond `completed_count` do not disqualify).
4. For each enumerated handle, the control plane uses Codex `thread/read` on the handle's `codex_thread_id` to recover the latest completed state, then `thread/resume` to reattach the thread in the replacement runtime.
5. The control plane calls `update_runtime` on each recovered handle to point to the new runtime instance. If `thread/resume` yields a new thread identity, the handle's `codex_thread_id` must also be updated.
6. Pending server requests associated with crashed handles are marked canceled.
7. Claude may continue from the last completed turn. Forking from the interrupted snapshot requires `codex.dialogue.fork` to be in scope.

Future producers of `status: unknown` must either be compatible with this eligibility predicate or introduce stronger provenance before they can participate in startup reattach.

The lineage store does not participate in crash detection or runtime restart — those are control plane responsibilities. The store's role is providing the handle data needed for step 2.

### Relationship to Other Stores

| Store | Scope | Write Discipline | Purpose |
|---|---|---|---|
| Lineage store | Session-bounded | Write-through (fsync) | Handle identity and routing |
| [Operation journal](recovery-and-journal.md#operation-journal) | Session-bounded | fsync before dispatch | Idempotent replay |
| [Audit log](recovery-and-journal.md#audit-log) | Cross-session (30-day TTL) | Best-effort append | Human reconstruction |

The lineage store and operation journal are both session-bounded but serve different purposes. The journal records in-flight operations for replay; the lineage store records handle identity for routing and recovery. They share `${CLAUDE_PLUGIN_DATA}` but use separate subdirectories.

The official plugin has no equivalent operation journal. Crash recovery and idempotent replay are specific to this spec's control-plane design.

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
| `reason` | enum | `head_mismatch`, `index_dirty`, `worktree_dirty`, `artifact_hash_mismatch`, `job_not_completed`, `job_not_reviewed` |
| `detail` | string | Human-readable explanation |
| `expected` | string? | Expected value (e.g., expected HEAD SHA) |
| `actual` | string? | Actual value found |

### Promotion Result

Returned by `codex.delegate.promote` on success.

| Field | Type | Description |
|---|---|---|
| `job` | [DelegationJob](#delegationjob) | Updated job after the promote path reached `verified` |
| `artifact_hash` | string | Reviewed artifact hash that was verified and applied |
| `changed_files` | list\[path\] | Files whose reviewed changes were applied into the primary workspace |
| `stale_advisory_context` | boolean | `true` only when post-promotion coherence state was recorded for an existing advisory runtime |

### Discard Rejection

Returned by `codex.delegate.discard` when the requested job cannot be discarded.

| Field | Type | Description |
|---|---|---|
| `rejected` | boolean | Always `true` |
| `reason` | enum | `job_not_found`, `job_not_discardable` |
| `detail` | string | Human-readable explanation |
| `job_id` | string? | Rejected job id when known |

### Discard Result

Returned by `codex.delegate.discard` on success.

| Field | Type | Description |
|---|---|---|
| `job` | [DelegationJob](#delegationjob) | Updated job after the discard path finished |

### Job Busy

Returned by `codex.delegate.start` when a user-attention-required job exists. The widened busy gate blocks when any non-terminal job requires user attention — not just runtime-active (running/queued/needs_escalation) jobs. This includes completed jobs awaiting review, failed/unknown jobs needing inspection, and partial promotion states. See [recovery-and-journal.md §Concurrency Limits](recovery-and-journal.md#concurrency-limits).

| Field | Type | Description |
|---|---|---|
| `busy` | boolean | Always `true` |
| `active_job_id` | string | The job requiring user attention |
| `active_job_status` | enum | Current status of the attention-active job (any `JobStatus` value) |
| `detail` | string | Human-readable explanation |

### Start Escalation

Returned by `codex.delegate.start` when the first execution turn triggers a server request that requires caller resolution.

| Field | Type | Description |
|---|---|---|
| `job` | [DelegationJob](#delegationjob) | Created job in `needs_escalation` status |
| `pending_escalation` | [Pending Escalation View](#pending-escalation-view) | Projected escalation for caller rendering |
| `agent_context` | string? | Best-effort agent message from the interrupted turn |
| `escalated` | boolean | Always `true` |

### Decision Rejection

Returned by `codex.delegate.decide` when the caller asks to resolve an escalation
that cannot be handled under the opening-slice constraints.

| Field | Type | Description |
|---|---|---|
| `rejected` | boolean | Always `true` |
| `reason` | enum | `invalid_decision`, `job_not_found`, `job_not_awaiting_decision`, `request_not_found`, `request_job_mismatch`, `request_already_decided`, `runtime_unavailable`, `answers_required`, `answers_not_allowed` |
| `detail` | string | Human-readable explanation |
| `job_id` | string? | Rejected job id when known |
| `request_id` | string? | Rejected request id when known |

### Decide Result

Returned by `codex.delegate.decide` on success.

| Field | Type | Description |
|---|---|---|
| `job` | [DelegationJob](#delegationjob) | Updated job after the decision path finished |
| `decision` | enum | `approve` or `deny` |
| `resumed` | boolean | `true` only when approve dispatched a follow-up turn |
| `pending_escalation` | [Pending Escalation View](#pending-escalation-view)? | Present only when the resumed turn hit another escalation |
| `agent_context` | string? | Best-effort agent message from the resumed turn when present |

### Poll Rejection

Returned by `codex.delegate.poll` when the requested job cannot be found.

| Field | Type | Description |
|---|---|---|
| `rejected` | boolean | Always `true` |
| `reason` | enum | `job_not_found` |
| `detail` | string | Human-readable explanation |
| `job_id` | string? | Rejected job id when known |

### Pending Escalation View

Caller-visible projection returned by `codex.delegate.start`, `codex.delegate.poll`, and `codex.delegate.decide` when a job is awaiting caller action. Raw Codex IDs (`codex_thread_id`, `codex_turn_id`, `item_id`) remain internal to the control plane per [§Logical Data Model](#logical-data-model). The controller projects `PendingServerRequest` to this view before constructing any response type.

| Field | Type | Description |
|---|---|---|
| `request_id` | string | Plugin request identifier |
| `kind` | enum | `command_approval`, `file_change`, `request_user_input`, `unknown` |
| `requested_scope` | object | Opaque request payload needed for resolution |
| `available_decisions` | list\[string\] | Valid resolution options |

### Artifact Inspection Snapshot

Inspection bundle surfaced by `codex.delegate.poll`. For `completed` jobs, this is the reviewable snapshot whose hash anchors the [promotion protocol](promotion-protocol.md#artifact-hash-integrity). For `unknown` or `failed` jobs, this is an inspection-only snapshot without hash backing.

| Field | Type | Description |
|---|---|---|
| `artifact_hash` | string? | Present for completed jobs once the reviewed snapshot has been materialized; null for inspection-only snapshots (`unknown`, `failed`) |
| `artifact_paths` | list\[path\] | Exact persisted artifact files that define the inspection set |
| `changed_files` | list\[path\] | Convenience projection of files changed relative to `base_commit` |
| `reviewed_at` | ISO 8601 | Time the inspection snapshot was materialized |

### Poll Result

Returned by `codex.delegate.poll`. Takes a required `job_id` and returns the current execution-domain projection for that job. v1 does not define list mode.

| Field | Type | Description |
|---|---|---|
| `job` | [DelegationJob](#delegationjob) | Current job record |
| `pending_escalation` | [Pending Escalation View](#pending-escalation-view)? | Present only when `job.status == "needs_escalation"` |
| `inspection` | [Artifact Inspection Snapshot](#artifact-inspection-snapshot)? | Present when inspection artifacts are available; for `completed` jobs this is the reviewable snapshot |
| `detail` | string? | Human-readable operational explanation, especially for `failed` or `unknown` jobs where the outcome could not be confirmed and the job is inspection-only / restart-or-discard territory |

### Runtime Health

Returned by `codex.status`.

| Field | Type | Description |
|---|---|---|
| `codex_version` | string | Codex CLI version |
| `app_server_version` | string | App Server protocol version |
| `auth_status` | enum | `authenticated`, `expired`, `missing` |
| `advisory_runtime` | object? | Advisory runtime state (id, policy\_fingerprint, thread\_count, uptime) |
| `active_delegation` | object? | Current delegation requiring user attention (in-flight, completed awaiting review, failed/unknown needing inspection, or partial promotion states needing recovery). Null when no job requires attention. Excluded: terminal promotion states (`verified`, `discarded`, `rolled_back`). |
| `delegation_status_error` | string? | Diagnostic when delegation status enrichment fails (factory recovery error, query error). Present only on failure. Do NOT treat null `active_delegation` as "no active delegation" when this field is set. NOT appended to global `errors` to avoid blocking consult/dialogue preflights. |
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

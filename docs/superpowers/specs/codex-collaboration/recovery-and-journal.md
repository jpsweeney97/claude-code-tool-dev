---
module: recovery-and-journal
status: active
normative: true
authority: recovery-contract
---

# Recovery and Journal

Contracts for crash recovery, operation journaling, audit logging, concurrency control, and resource retention.

## Two-Log Architecture

The plugin maintains two separate logs with different purposes, write disciplines, and retention policies.

| Property | Operation Journal | Audit Log |
|---|---|---|
| Purpose | Idempotent replay after crash | Human incident reconstruction |
| Write discipline | fsync before dispatch | Best-effort append |
| Retention | Trim on operation completion | TTL-based (30 days) |
| Scope | Session-bounded (v1) | Cross-session |
| Consumer | Control plane (automatic recovery) | Claude + user (diagnostics) |
| Format | Operation records with idempotency keys | [AuditEvent](contracts.md#auditevent) records (JSONL) |

### Why Two Logs

The audit log answers "what happened?" The operation journal answers "what was I in the middle of doing?" They have different write patterns, different retention windows, and different consumers. Merging them would either over-retain operational state or under-protect the audit trail.

## Operation Journal

The operation journal ensures that crash recovery is deterministic replay, not inspection-based guessing.

### Write Ordering

**Journal before dispatch.** Every dispatched operation is written to the journal before the corresponding App Server request is sent. This guarantees that:

- If the control plane crashes after journal write but before dispatch, the operation can be retried.
- If the control plane crashes after dispatch, the journal records what was in flight.
- If the control plane crashes before journal write, no operation was dispatched and no cleanup is needed.

### Idempotency Keys

Each journaled operation carries a unique idempotency key. If the same key is replayed, the control plane checks the operation's outcome rather than re-dispatching.

| Operation | Idempotency Key Components | Effect of Replay |
|---|---|---|
| Job creation | `claude_session_id` + `delegation_request_hash` | Check if job already exists |
| Thread creation | `claude_session_id` + `collaboration_id` | Check if thread already started |
| Turn dispatch | `runtime_id` + `thread_id` + `turn_sequence` | Check if turn already started |
| Approval resolution | `request_id` + `decision` | Check if already resolved |
| Promotion | `job_id` + `promotion_attempt` | Check promotion state |

`promotion_attempt` is a controller-owned monotonic counter persisted on the [DelegationJob](contracts.md#delegationjob). It increments before each new promote attempt writes its `promotion` journal `intent` phase.

### Session Scope

In v1, the operation journal is session-bounded. It does not survive across Claude sessions.

**Rationale:** Restarting a delegation that was running when Claude crashed is more likely to surprise the user than to help. The correct recovery for cross-session crashes is: mark the job `unknown`, preserve the worktree and artifacts for inspection, and let the user decide whether to restart or discard.

### Trimming

Completed operations are trimmed from the journal after their outcome is confirmed. The journal should be near-empty during normal operation and only accumulate records for in-flight operations.

### Promotion Replay

Promotion is the only operation journaled in v1 that mutates the primary workspace directly rather than dispatching an App Server request. The phase meanings are therefore workspace-centric:

| Phase | Meaning | Workspace mutation may already have happened? |
|---|---|---|
| `intent` | All promotion prechecks passed; no primary-workspace mutation yet | No |
| `dispatched` | Crossed the mutation boundary; `git apply` may have run | Yes |
| `completed` | Promote reached `verified` or `rolled_back` | Already happened |

Replay rules:

- If recovery finds `promotion:intent` with no later `dispatched`, no primary-workspace mutation occurred. The job normalizes back to `promotion_state="pending"`.
- If recovery finds `promotion:dispatched` with no later `completed`, the journal is authoritative that workspace mutation may have happened. Recovery re-runs post-apply verification, then repairs the job store to `verified` or `rolled_back` as appropriate. If rollback itself fails, recovery leaves the journal entry unresolved and the job at `rollback_needed` so the next startup re-enters recovery.
- If the journal and job store disagree, the journal wins for the "has workspace mutation occurred?" question. A `dispatched` record outranks stale job-store state such as `prechecks_passed`.

`promotion:completed` is a resolution marker, not a terminal-state payload. By write ordering, the controller writes `promotion:completed` only after the job store has already been updated to terminal `promotion_state="verified"` or `promotion_state="rolled_back"`. Recovery reads the job store to learn which terminal state was reached. If a `completed` journal record exists but the job store still reports a pre-terminal promotion state, treat that as inconsistency to surface and repair explicitly rather than guessing from the journal alone.

### Stale Advisory Context Marker

When a successful promotion changes primary-workspace content and an advisory runtime exists for the same repo root, the control plane writes a session-scoped `stale_advisory_context` marker to the operation journal before acknowledging promotion success. The marker stores:

- `repo_root`
- `promoted_artifact_hash`
- `job_id`
- `recorded_at`

The marker is crash-recovery state, not a dispatchable App Server operation. It guarantees that the next advisory turn for that repo root applies the post-promotion coherence protocol in [advisory-runtime-policy.md §Post-Promotion Coherence](advisory-runtime-policy.md#post-promotion-coherence).

If multiple promotions occur before the next advisory turn, the marker is replaced with the newest promoted artifact hash / job id pair for that repo root.

The marker is trimmed after the first successful advisory turn dispatched with the required workspace-changed injection, or when the Claude session ends.

## Audit Log

The audit log records [AuditEvent](contracts.md#auditevent) records for human reconstruction and diagnostics.

### Write Triggers

An audit event is emitted for every state transition that crosses a trust or capability boundary:

| Trigger | Action Value | Required Fields |
|---|---|---|
| Consultation initiated | `consult` | `collaboration_id`, `runtime_id`, `context_size` |
| Dialogue turn dispatched | `dialogue_turn` | `collaboration_id`, `runtime_id`, `turn_id` |
| Thread forked | `fork` | `collaboration_id`, `causal_parent` |
| Delegation started | `delegate_start` | `collaboration_id`, `job_id`, `runtime_id` |
| Approval resolved | `approve` | `request_id`, `decision` |
| Escalation surfaced | `escalate` | `request_id`, `collaboration_id` |
| Promotion attempted | `promote` | `job_id`, `artifact_hash`, `decision` |
| Result discarded | `discard` | `job_id` |
| Runtime crashed | `crash` | `runtime_id`, `policy_fingerprint` |
| Runtime restarted | `restart` | `runtime_id`, `causal_parent` |
| Advisory runtime rotated | `rotate` | `runtime_id`, `policy_fingerprint` |
| Advisory runtime frozen | `freeze` | `runtime_id` |
| Frozen runtime reaped | `reap` | `runtime_id` |

### Retention

- **Default TTL:** 30 days from event timestamp.
- **Storage:** JSONL in `${CLAUDE_PLUGIN_DATA}/audit/`.
- **Cleanup:** Old records are pruned on plugin startup and periodically during session.

## Crash Recovery Paths

### Advisory Runtime Crash

1. Restart the advisory runtime.
2. Rebuild handle mappings from the [lineage store](contracts.md#lineage-store).
3. Use `thread/read` and `thread/resume` to recover the latest completed state.
4. Reload any `stale_advisory_context` marker from the operation journal and preserve the post-promotion injection requirement for the next advisory turn.
5. Mark any pending server requests as canceled.
6. Allow Claude to continue from the last completed turn or fork from the interrupted snapshot.

An [audit event](contracts.md#auditevent) with `action: crash` is emitted when the crash is detected. An event with `action: restart` is emitted when recovery completes, with `causal_parent` linking to the crash event.

### Delegation Runtime Crash

1. Preserve the worktree and artifacts.
2. Mark the job `unknown` in the [DelegationJob](contracts.md#delegationjob) record.
3. Expose inspection data through `codex.delegate.poll`.
4. Allow either:
   - **Restart from brief:** Create a new execution runtime in the existing worktree and re-delegate with the original prompt.
   - **Discard and cleanup:** Mark the job as discarded and schedule the worktree for cleanup per [retention defaults](#retention-defaults).

### Pending Request Ordering

App Server's `serverRequest/resolved` is authoritative for closing approval and user-input prompts. Pending-request state is not cleared on optimistic assumptions.

- If the control plane resolves a request but crashes before receiving `serverRequest/resolved`, the journal's idempotency key ensures the resolution is not re-sent.
- If `serverRequest/resolved` arrives for a request the control plane does not recognize (e.g., after crash recovery), the event is logged as an audit event but not acted upon.

### Unknown Request Handling

When the control plane receives a server request with an unrecognized `kind` (captured as `unknown` in [PendingServerRequest](contracts.md#pendingserverrequest)):

- In the **execution domain:** The job transitions to `needs_escalation`. Claude resolves via `codex.delegate.decide`.
- In the **advisory domain:** The request is surfaced to Claude as a pending escalation. Claude resolves per-request only (see [advisory-runtime-policy.md §Advisory Approval Scope](advisory-runtime-policy.md#advisory-approval-scope)).

Unknown requests are **never auto-approved**. This is the fail-closed default: no automatic grant of unrecognized permissions.

An [audit event](contracts.md#auditevent) with `action: escalate` is emitted for every unknown request received.

## Concurrency Limits

### Max Concurrent Delegation Jobs

**v1: exactly 1.** If Claude calls `codex.delegate.start` while a delegation job is already running, the control plane returns a [Job Busy](contracts.md#job-busy) response with the active job's ID and status.

This eliminates queueing, admission control, and contention management for v1. The delegation flow is strictly sequential.

### Advisory-Delegation Race

Advisory turns and promotion checks can race with workspace drift:

1. Advisory consult reads workspace state.
2. Delegation runs and produces artifacts.
3. Promotion applies reviewed workspace content.
4. Next advisory turn has stale context.

This does not break safety — the advisory runtime's read-only sandbox prevents writes. It breaks **coherence**: Codex's advisory responses are grounded in a workspace state that no longer exists.

v1 resolves this with same-thread next-turn context injection. Successful promotion marks advisory context stale; the next advisory turn receives a workspace-changed summary plus refreshed repository identity/context, and the stale marker is cleared after that turn is successfully dispatched. See [advisory-runtime-policy.md §Post-Promotion Coherence](advisory-runtime-policy.md#post-promotion-coherence).

## Retention Defaults

Canonical retention values. All TTLs are measured from `last_touched_at`, not creation time.

| Resource | TTL | Trigger |
|---|---|---|
| Completed worktree | 1 hour | After promotion or discard |
| Failed/crashed worktree | 24 hours | After crash detection or failure |
| Audit log records | 30 days | From event timestamp |
| Advisory runtime | Session end | Claude session termination |
| Abandoned sessions | Next startup | Scan for orphaned runtimes/worktrees |
| Diff/test summary | Survives worktree cleanup | Retained in `${CLAUDE_PLUGIN_DATA}` after worktree removal |

The diff/test summary is explicitly retained after worktree cleanup so that delegation history remains inspectable even after the worktree is removed.

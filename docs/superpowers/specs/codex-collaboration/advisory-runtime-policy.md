---
module: advisory-runtime-policy
status: active
normative: true
authority: advisory-policy
---

# Advisory Runtime Policy

Rules governing the advisory runtime's lifecycle, privilege scope, and rotation behavior. The advisory runtime serves both consultation and dialogue — they share a runtime because they are the same [capability class](foundations.md#scope).

The core enforcement invariant: **never mutate advisory policy in place.**

This file contains both current Packet 1 runtime behavior and future-scope freeze-and-rotate design. Sections are labeled accordingly.

## Current Packet 1 Behavior

### Fixed Advisory Posture

The advisory runtime uses a fixed posture for the Packet 1 implementation:

| Component | Value |
|---|---|
| Transport mode | `stdio` |
| Sandbox level | `read-only` |
| Network access | `disabled` |
| Approval mode | `never` |
| App connectors | `disabled` |

Advisory runtime state is cached per repo root within the control plane and serves both consultation and dialogue. Widening requests are rejected at three enforcement gates:

- `codex.consult` with `network_access=True` is rejected by the control plane (`"advisory widening is not implemented in R1"`).
- Profile resolution rejects `sandbox` values other than `read-only` (`"sandbox widening requires freeze-and-rotate (not yet implemented)"`).
- Profile resolution rejects `approval_policy` values other than `never` (`"approval widening requires freeze-and-rotate (not yet implemented)"`).

Advisory approvals are disabled — the advisory runtime runs with `approval_policy="never"` and does not install a server-request handler. No advisory-domain approval resolution occurs under Packet 1.

### Policy Fingerprint

Each advisory runtime instance has an immutable policy fingerprint computed at creation time. The fingerprint is a SHA-256 hash of the effective policy configuration (the five components listed above).

Under Packet 1, the fingerprint is a fixed value because the advisory posture is fixed. The fingerprint is recorded in [audit events](contracts.md#auditevent) and [outcome records](decisions.md#analytics-and-review-cutover-model) for forensic correlation.

Future-scope uses of the fingerprint (comparison across rotation boundaries to verify widening or narrowing) are described in [§Future-Scope: Freeze-and-Rotate Design](#future-scope-freeze-and-rotate-design) below.

### Post-Promotion Coherence

A successful promotion can invalidate the advisory runtime's workspace view without changing its policy fingerprint. In v1, this is handled as a coherence event, not a policy-rotation event.

When a promotion applies reviewed workspace content for a repo root that currently has an advisory runtime:

1. The control plane marks the advisory runtime's workspace context as stale.
2. The stale marker records the promoted artifact hash and job id and is persisted per [recovery-and-journal.md §Stale Advisory Context Marker](recovery-and-journal.md#stale-advisory-context-marker).
3. On the next advisory turn for that repo root, the control plane reuses the existing advisory runtime unless a separate policy decision requires rotation.
4. Before dispatching the turn, the control plane injects a workspace-changed summary plus refreshed repository identity/context into the packet. The summary is anchored in the stale marker plus live repo identity loaded at dispatch time.
5. After the first successful post-promotion advisory turn is dispatched, the stale marker is cleared.

Additional rules:

- Freshness changes do not mutate advisory policy in place and do not by themselves trigger rotation.
- v1 does not require automatic post-promotion thread fork or `turn/steer` for coherence.
- If multiple promotions occur before the next advisory turn, only the most recent promoted artifact hash / job id pair is carried forward.
- If no advisory runtime exists for the repo root, no stale marker is created.

### Current Recovery and Journal Interactions

Crash recovery for the single fixed advisory runtime follows the path defined in [recovery-and-journal.md §Advisory Runtime Crash](recovery-and-journal.md#advisory-runtime-crash).

Successful promotions write a `stale_advisory_context` marker to the operation journal before success is acknowledged. Crash recovery reloads any surviving marker and preserves the next-turn injection requirement until the first post-promotion advisory turn is successfully dispatched.

## Future-Scope: Freeze-and-Rotate Design

The following sections describe designed-but-not-yet-implemented behavior. The architecture is preserved for future implementation. Current Packet 1 runtime behavior rejects all widening requests — see [§Current Packet 1 Behavior](#current-packet-1-behavior) above.

### Privilege Widening

When a turn requires capabilities beyond the current runtime's policy (e.g., network access for a web-facing research question):

1. The current runtime is **frozen** — no new turns are accepted, but history remains available for reconstruction.
2. A new runtime starts with the wider policy.
3. Thread history is forked into the new runtime via App Server `thread/fork`.
4. The new runtime's policy fingerprint reflects the wider configuration.
5. The frozen runtime is scheduled for [reaping](#reap-conditions).

#### What Triggers Widening

- Claude explicitly requests a capability that exceeds the current policy (e.g., `codex.consult` with `network: true` when the current runtime has network disabled).
- The control plane detects that a requested operation cannot succeed under current policy.

#### What Does NOT Trigger Widening

- Codex requesting additional permissions via server requests within a turn. These are resolved per-request only — see [Advisory Approval Scope](#advisory-approval-scope). Per-request resolution does not widen the runtime's effective policy and does not require rotation.

### Advisory Approval Scope

When advisory-domain server-request handling is implemented, server requests resolved within the advisory domain will use per-request scope only. `acceptForSession` will never be applied in the advisory domain.

Rationale:

- Session-scoped acceptance would widen the runtime's effective policy without changing the policy fingerprint.
- This would violate the core enforcement invariant (never mutate advisory policy in place).
- Persistent capability widening is handled by the [rotation protocol](#privilege-widening) instead.

If Codex raises a server request that requires broader or persistent approval, the control plane surfaces it to Claude. Claude then either resolves it as a one-time per-request approval or initiates explicit widening through `codex.consult` with the needed capability flag, which triggers [rotation](#freeze-and-rotate-semantics).

### Privilege Narrowing

When the current work no longer requires the widened capabilities:

- Narrowing occurs at the **next turn boundary**, not mid-turn and not immediately after the widened action completes.
- The invariant: **each turn runs under the narrowest policy sufficient for that turn.**
- Narrowing follows the same rotation mechanism as widening: freeze the current runtime, start a new runtime with narrower policy, fork history.

#### When Narrowing Applies

Narrowing is triggered when Claude initiates a turn that does not require the current runtime's elevated capabilities. The control plane compares the requested capabilities against the [base policy defaults](foundations.md#advisory-domain) and rotates down if the turn can be served at a lower privilege level.

#### Why Not Immediate Narrowing

Narrowing immediately after a widened action would turn least privilege into churn. The turn boundary is the natural granularity: a turn is the smallest unit of coherent advisory work, and rotating mid-turn risks losing context or producing inconsistent results.

### Freeze-and-Rotate Semantics

#### Freeze

A frozen runtime:

- Accepts no new turns.
- Remains available for thread history reads (via `thread/read`).
- Retains its policy fingerprint for audit correlation.
- Is not destroyed — it is scheduled for reaping.

#### Rotate

Rotation creates a new runtime with a different policy:

1. Freeze the current runtime.
2. Start a new App Server runtime with the target policy.
3. Fork the thread history from the frozen runtime into the new runtime.
4. Update the control plane's handle mappings to point to the new runtime.
5. Emit an [audit event](contracts.md#auditevent) with `action: rotate`.

#### Reap Conditions

A frozen runtime is reaped (shut down and cleaned up) when:

| Condition | Priority | Rationale |
|---|---|---|
| Replacement runtime completes its first successful turn | Primary | Proves the fork worked and the new runtime is healthy |
| TTL from freeze timestamp expires | Fallback | Prevents accumulation if the replacement never becomes healthy |
| Claude session ends | Terminal | All advisory runtimes for the session are cleaned up |

The primary trigger is intentionally conservative: the frozen runtime survives until the replacement proves it works. The TTL fallback prevents unbounded accumulation.

### Turn Boundary Invariants

1. A turn starts and ends within a single runtime instance.
2. No runtime rotation occurs mid-turn.
3. Policy evaluation (widen/narrow decision) occurs between turns.
4. The control plane records which runtime served each turn, enabling audit trail reconstruction across rotation boundaries.

### Future Recovery and Journal Interactions

Rotation events will affect crash recovery and journaling when implemented:

- Each rotation emits an [audit event](contracts.md#auditevent) with `action: rotate`, linking the old and new runtimes.
- If the control plane crashes mid-rotation, the [operation journal](recovery-and-journal.md#operation-journal) ensures the rotation is either completed or rolled back on restart.
- Frozen runtimes that survive a crash are rediscovered and scheduled for reaping during recovery.
- Reap timing follows [retention defaults](recovery-and-journal.md#retention-defaults) for the TTL fallback condition.

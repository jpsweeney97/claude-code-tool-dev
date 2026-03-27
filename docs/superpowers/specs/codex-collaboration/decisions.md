---
module: decisions
status: active
normative: true
authority: decisions
---

# Decisions

Locked design decisions, accepted tradeoffs, and open questions for the codex-collaboration plugin.

## Greenfield Rules

This design is a greenfield replacement. It does **not** preserve the current cross-model plugin's:

| Artifact | Status | Rationale |
|---|---|---|
| Slash-command names | Replaced | New skill surface wraps [MCP tools](contracts.md#mcp-tool-surface), not bash commands |
| Event schemas | Replaced | New [audit event schema](contracts.md#auditevent) designed for split-runtime model |
| Consultation contracts | Replaced | Thread-native dialogue replaces emulated conversation state |
| `conversation_id == threadId` assumptions | Replaced | Plugin maintains its own [CollaborationHandle](contracts.md#collaborationhandle) independent of Codex thread IDs |
| Delegation pipeline stages | Replaced | App Server thread lifecycle replaces batch `codex exec` wrapper |
| Analytics payloads | Replaced | New audit log serves this purpose |

The existing `cross-model` package is only useful as a list of failure modes to avoid. The new system defines its own logical contracts and storage model.

## Accepted Tradeoffs

### T1: Security Isolation vs. Operational Simplicity

**What is being traded:** Strong runtime separation and fail-closed approvals versus a much larger state/recovery surface.

**Why it hid:** The design correctly rejects the unsafe single-runtime option, so the remaining design inherits a "secure by structure" aura that masks the amount of orchestration correctness now required.

**Likely failure story:** The system keeps isolation but mismanages runtime state after crash or overload, creating orphaned jobs, stale approvals, or silently broadened advisory permissions.

**Mitigations:** The [operation journal](recovery-and-journal.md#operation-journal) provides idempotent replay. [Max-1 concurrent delegation](recovery-and-journal.md#concurrency-limits) bounds the state surface. [Advisory rotation](advisory-runtime-policy.md) prevents permission accumulation.

### T2: Execution Isolation vs. Reversibility

**What is being traded:** Isolated worktrees and explicit promotion protect the primary tree, but move the hardest correctness problem to the final merge boundary.

**Why it hid:** Isolation is presented as a safety win, which it is, but the design does not yet treat promotion as a first-class protocol with its own failure modes.

**Likely failure story:** Codex completes cleanly in the side tree, the user approves, and the main branch has drifted just enough to produce a bad or confusing promotion outcome.

**Mitigations:** The [promotion protocol](promotion-protocol.md) defines strict preconditions (HEAD match, clean tree/index, artifact hash verification) and [typed rejection responses](contracts.md#promotion-rejection). v1 requires exact HEAD match — no three-way merge.

## Architecture Option Analysis

Four architectures were evaluated. Full analysis is in the [design document](../2026-03-27-codex-collaboration-plugin-design.md).

| Option | Shape | Verdict | Key Reason |
|---|---|---|---|
| A | `codex exec` wrapper, improved | Rejected | Batch-shaped; weak multi-turn; poor crash recovery |
| B | One long-lived App Server | Rejected | Session-scoped approvals bleed across capability classes |
| C | Split App Server domains | **Selected** | Thread-native dialogue; isolated execution; explicit lineage |
| D | Remote broker service | Deferred | Overkill for v1; too much operational surface |

## Open Questions

### Unknown Request Kinds

**Resolved.** When App Server sends a server request with an unrecognized `kind`, the system treats it as `unknown` (see [PendingServerRequest](contracts.md#pendingserverrequest)). The normative default: unknown requests are held and surfaced to Claude as escalations, never auto-approved. See [recovery-and-journal.md §Unknown Request Handling](recovery-and-journal.md#unknown-request-handling) for the full behavioral contract.

### Audit Consumer Interface

The [audit event model](contracts.md#auditevent) defines the record shape and [recovery-and-journal.md](recovery-and-journal.md#audit-log) defines write behavior. The interface for querying and consuming audit records (filtering, aggregation, export) is not yet specified.

### Context Assembly Pipeline

The architecture names secret scanning and overbroad-context rejection as [hook guard responsibilities](foundations.md#outer-boundary-claude-hook-guard), but the canonical context-selection and redaction contract — allowlisted sources, size caps, capability-specific minima — is not yet a formal protocol. This is an implementation-time design decision.

### Advisory Domain Stale Context After Promotion

After a [promotion](promotion-protocol.md) changes HEAD, the advisory runtime's cached context may be stale. Whether to use `turn/steer` or thread forking to signal workspace changes is an implementation-time decision that depends on App Server's mid-session context invalidation capabilities.

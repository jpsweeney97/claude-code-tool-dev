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

## Supersession Direction

As of 2026-03-30, `codex-collaboration` is the sole planned successor to the
`cross-model` plugin. `cross-model` remains a migration inventory and a source
of failure modes to avoid; it is not a co-equal long-term surface.

`context-injection` is retired by default for codex-collaboration dialogue
flows. Reconsider that decision only if the fixed benchmark contract in
[dialogue-supersession-benchmark.md](dialogue-supersession-benchmark.md) shows
that Claude-side scouting is materially worse.

Analytics are rebuilt on codex-collaboration's audit and event model rather
than ported from cross-model's JSONL schema.

## Official Plugin as Reference Context, Not Convergence Target

**Decision:** The official OpenAI plugin (`openai/codex-plugin-cc`) is reference context for the Codex integration landscape. This spec maintains independent architectural authority and does not restructure around the official plugin as a baseline shell.

**Rationale:** The spec's control-plane mediation, structured flows, durable lineage, isolated execution, and promotion machinery provide capabilities the official plugin does not. Converging toward the official plugin's shell would require abandoning these capabilities or relegating them to optional extensions, reducing the spec's coherence.

**Tradeoff:** The spec owns a larger implementation and maintenance surface in exchange for architectural independence and the ability to evolve without upstream coupling.

**Upstream pin:** `9cb4fe4`. Re-evaluate if upstream adds lineage, isolation, or promotion equivalents.

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

Four architectures were evaluated in the original [design document](../2026-03-27-codex-collaboration-plugin-design.md). A fifth option emerged during the official-plugin comparison and is recorded here for governance completeness.

| Option | Shape | Verdict | Key Reason |
|---|---|---|---|
| A | `codex exec` wrapper, improved | Rejected | Batch-shaped; weak multi-turn; poor crash recovery |
| B | One long-lived App Server | Rejected | Session-scoped approvals bleed across capability classes |
| C | Split App Server domains | **Selected** | Thread-native dialogue; isolated execution; explicit lineage |
| D | Remote broker service | Deferred | Overkill for v1; too much operational surface |
| E | Thin bridge to official plugin | Rejected | Would split the product into upstream baseline plus local extensions instead of preserving one coherent control-plane architecture |

## Analytics and Review Cutover Model

**Resolved (2026-04-21).** Analytics are computed from codex-collaboration's
existing audit and outcome streams, not from cross-model's flat event log. The
cross-model `codex-reviewer` agent is replaced by a `codex-review` skill over
`codex.consult`.

**Key decisions:**

- **Analytics source:** `analytics/outcomes.jsonl` (advisory and delegation
  terminal outcomes) plus `audit/events.jsonl` (lifecycle and security). No new
  cross-model-style flat emitter. No raw-store walking as the primary analytics
  contract.
- **Outcome shape split:** Advisory outcomes (`OutcomeRecord`) and delegation
  terminal outcomes (`DelegationOutcomeRecord`) are separate typed records in a
  union stream. Delegation execution terminal state and user disposition
  (promote/discard) are recorded separately because they have different
  authorities and timing — the Codex runtime owns terminal status; the user
  owns disposition.
- **Review discrimination:** First-class `workflow` discriminator on
  `OutcomeRecord` and `codex.consult` tool input. `codex-review` sets
  `workflow="review"`. Analytics interprets; the control plane persists without
  branching.
- **Delegate review integration:** Advisory only. `codex-review` can review
  delegate artifacts but is not a hard promotion precondition.

**Driver:** T-07 reconciliation session. Cross-model's analytics and reviewer
are semantic sources only — the codex-collaboration architecture has a
different data topology (session-partitioned journals, typed audit/outcome
split) that requires fresh design, not a port.

**Change trigger:** Revisit if the analytics consumer interface
(Open Questions §Audit Consumer Interface) specifies requirements that the
outcome/audit split cannot serve.

## Open Questions

### Unknown Request Kinds

**Resolved.** Unknown server requests are never auto-approved — this is the fail-closed invariant regardless of mechanism.

Under Packet 1, a persisted `kind="unknown"` [PendingServerRequest](contracts.md#pendingserverrequest) terminalizes the delegation job as `unknown`. The request does not enter [PendingEscalationView](contracts.md#pending-escalation-view) and is not resolved via `codex.delegate.decide`. Terminal evidence is the persisted request record plus `DelegationOutcomeRecord(outcome_type="delegation_terminal", terminal_status="unknown")`.

[T-20260429-02](../../../tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md) classifies each unsupported App Server method individually. Classified methods may be promoted to the parkable/supported set, proven as intentionally safe-terminal, or proven non-reachable in current flows. See [recovery-and-journal.md §Unknown Request Handling](recovery-and-journal.md#unknown-request-handling) for the operational contract.

### Audit Consumer Interface

The [audit event model](contracts.md#auditevent) defines the record shape and [recovery-and-journal.md](recovery-and-journal.md#audit-log) defines write behavior. The interface for querying and consuming audit records (filtering, aggregation, export) is not yet specified.

### Context Assembly Pipeline

**Resolved.** The canonical context-selection and redaction protocol is defined in [foundations.md §Context Assembly Contract](foundations.md#context-assembly-contract). That contract assigns assembly ownership to the control plane, keeps the hook guard in a rejection-only role, defines advisory and execution capability profiles, and sets the source allowlist, budget caps, trimming rules, and advisory-to-execution promotion boundary.

### Advisory Domain Stale Context After Promotion

**Resolved.** v1 restores advisory coherence after promotion by marking advisory context stale and injecting a workspace-changed summary plus refreshed repository identity/context on the next advisory turn in the same advisory thread. This protocol is defined in [advisory-runtime-policy.md §Post-Promotion Coherence](advisory-runtime-policy.md#post-promotion-coherence).

`turn/steer` remains optional in v1, and automatic post-promotion thread fork is not required by the normative path. The [context assembly contract](foundations.md#context-assembly-contract) continues to define the advisory-to-execution promotion boundary: only explicitly caller-promoted summary-form advisory conclusions may cross into later execution packets.

### Dialogue Fork Scope

**Resolved.** Dialogue remains architecturally branchable. The near-term implementation target is copy-and-diverge via current-head forking, not full tree-structured dialogue or arbitrary prefix seeding. A standalone `codex.dialogue.fork` tool is permanently replaced by a `seed_from` parameter on `codex.dialogue.start`.

**Rationale:** Branchability is woven into the architectural narrative — scope/goals ([foundations.md §Scope](foundations.md#scope)), dialogue flow ([foundations.md §Dialogue](foundations.md#dialogue)), and the [CollaborationHandle](contracts.md#collaborationhandle) schema (`parent_collaboration_id`, `fork_reason`). Removing it would smuggle a cancellation decision into a docs cleanup. But the originally specified shape — a separate `codex.dialogue.fork` tool with full tree-structured `dialogue.read` — is heavier than needed. Copy-and-diverge captures the primary use case (explore an alternative from a decision point without losing accumulated context) without tree state, tree-read, or lineage-store tree traversal.

**Planned surface:** `seed_from` on `codex.dialogue.start`, accepting a `collaboration_id` with implicit current-head semantics. The App Server `thread/fork` creates a new independent thread; the plugin creates a new `CollaborationHandle` with `parent_collaboration_id` pointing to the source. The seeded dialogue is an independent linear dialogue — no shared state, no tree traversal, no reconvergence. Arbitrary prefix seeding (`up_to_turn`) is a separate design question, deferred: it requires either replaying Codex turn content across threads or constructing synthetic seed context, both of which have fundamentally different implementation surfaces than current-head fork.

**Forward compatibility:** `thread/fork` is already implemented in `runtime.py` for consultation branching. `CollaborationHandle` already includes `parent_collaboration_id` and `fork_reason` as reserved nullable fields — no schema migration needed.

#### Constraints

- **Admissibility:** `seed_from` is admissible only from a readable, same-session/same-repo dialogue handle with consistent turn metadata. Unsafe source states (handle status `unknown` with incomplete recovery, `dialogue.read` failure, turn metadata replay diagnostics) reject rather than create partial provenance.
- **Fresh control resolution:** A seeded dialogue resolves its own profile, posture, and turn budget from explicit `dialogue.start` arguments or defaults. Source dialogue execution controls are not implicitly inherited.
- **Dialogue-thread verification required:** `thread/fork` is currently exercised only through the consultation path in `control_plane.py`. Implementation must verify that `thread/fork` works correctly for dialogue threads before shipping `seed_from`.
- **D-07 ordering dependency:** Seeded-dialogue provenance tracking interacts with the audit schema alignment work (D-07). Whichever lands first should account for the other — the `fork` audit action ([contracts.md §Audit Event Actions](contracts.md#audit-event-actions)) is reserved for seeded-dialogue provenance rather than currently emitted.

**Change trigger:** Implementation enters scope when a concrete seeded-dialogue use case justifies the work. The design direction is set; the constraints above govern implementation.

### `codex.consult` Surface

**Resolved.** `codex.consult` remains a first-class MCP tool as the explicit
one-shot advisory surface. It is not retired into `codex.dialogue` and it is
not retired into a native-review wrapper over the official plugin.

**Rationale:** The overlap between `codex.consult` and `codex.dialogue` is
already factored into shared bootstrap, context-assembly, prompting, dispatch,
and parsing helpers. The remaining differences are contract-level properties,
not accidental duplication: consult keeps an ephemeral handle, avoids lineage,
journal, and turn-store persistence, integrates post-promotion stale-context
handling for advisory follow-up, and preserves consultation-specific audit
semantics. Retiring consult into dialogue would either recreate those semantics
as a "lightweight" dialogue mode or impose unnecessary persistence overhead on
one-shot advisory questions.

Native review from the official plugin also does not beat the current design.
It does not natively enforce the structured advisory result required by this
spec (`position`, `evidence`, `uncertainties`, `follow_up_branches`), so a
wrapper would still need to rebuild schema enforcement locally. It also does
not materially reduce the control-plane surface: the surrounding safety,
context, coherence, and orchestration machinery would remain.

**Re-evaluation trigger:** Reopen this decision only if upstream Codex adds
native structured output enforcement matching the consult advisory contract, or
if the advisory domain no longer needs consult's distinct ephemeral-handle,
stale-context, and fork/coherence properties.

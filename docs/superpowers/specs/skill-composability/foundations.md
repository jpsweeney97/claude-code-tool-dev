---
module: foundations
status: active
normative: true
authority: foundation
---

# Foundations

## Problem

Three skills form a natural analysis pipeline — adversarial-review (AR) produces findings, next-steps (NS) turns findings into a phased plan, and dialogue consults Codex on specific tasks. Today they compose only through implicit conversation context: AR's output is free-form markdown, NS references `/dialogue` in a prose suggestion, and dialogue's `--plan` flag decomposes from the raw user question without awareness of upstream context.

Three gaps result:

1. **No structural contracts** — Finding identity, severity carry-forward, and task references rely on prose parsing.
2. **No guided handoffs** — AR does not suggest NS, NS's suggestion of dialogue is prose-only, and dialogue's synthesis has no downstream consumer contract.
3. **No feedback loop** — Dialogue synthesis (RESOLVED/UNRESOLVED/EMERGED) cannot feed back into AR for re-review or NS for replanning.

## Scope

### In Scope

- Structural contracts between AR, NS, and dialogue
- Capsule and sentinel formats for inter-skill data exchange
- Adaptive `--plan` behavior when upstream context is present
- Feedback loop architecture (dialogue → AR/NS)
- Lineage model for artifact versioning and staleness detection
- Shared composition contract governing cross-skill semantics

### Out of Scope

- Changes to the codex-dialogue agent's synthesis format — capsules are assembled by the `/dialogue` skill, not the agent
- Automatic multi-skill orchestration — user remains the circuit breaker
- File-based persistence for AR→NS and NS→dialogue arcs — conversation-local is sufficient for v1. `dialogue_feedback` has selective durable persistence (see [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence))
- Changes to global CLAUDE.md protocols — Adversarial Self-Review and Next Steps Planning remain independent behaviors

## Consumer Classes

Two consumer classes govern how skills process upstream capsules:

| Class | Behavior | Used by |
|-------|----------|---------|
| **Advisory/tolerant** | Validate capsule if present; fall back to prose parsing if absent or invalid. Emit a one-line prose diagnostic when falling back. | NS consuming AR capsule; AR/NS consuming feedback capsule |
| **Strict/deterministic** | Reject invalid capsule but continue normal pipeline — no fallback to a different data source. | Dialogue consuming NS handoff |

**Unknown sentinel versions:** Reject the capsule block, not the skill session. A version mismatch prevents capsule consumption but does not break the skill invocation.

## Three-Layer Authority Model

The composition system distributes authority across three layers:

| Layer | Owner | Authority | Audience |
|-------|-------|-----------|----------|
| **This spec** | Spec files (this directory) | Design authority — canonical definitions of all protocol semantics | Spec authors and reviewers |
| **Composition contract** | Shared reference document | Runtime projection — must conform to spec definitions; authoritative for inline stub authors at implementation time | Skill authors modifying composition behavior |
| **Inline stubs** (per skill) | Each participating skill | Runtime authority — role-specific operational subset derived from the contract | Claude during skill execution |

**Relationship between spec and contract:** Within this spec, the normative definitions live in the spec files ([routing-and-materiality.md](routing-and-materiality.md), [lineage.md](lineage.md), [capsule-contracts.md](capsule-contracts.md), etc.). The Composition contract is the runtime delivery artifact that must conform to — not supersede — these spec-file definitions. When the contract diverges from the spec, the spec is authoritative and the contract must be updated.

**Contract carries runtime projection of protocol core:**

- Sentinel/version rules and unknown-version handling — see [capsule-contracts.md](capsule-contracts.md#sentinel-registry)
- Artifact metadata schema — see [lineage.md](lineage.md#artifact-identity)
- Consumer class definitions — see [Consumer Classes](#consumer-classes) below
- Routing classification rules and precedence — see [routing-and-materiality.md](routing-and-materiality.md#routing-classification)
- Material-delta tier semantics — see [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating)
- Budget semantics — see [routing-and-materiality.md](routing-and-materiality.md#soft-iteration-budget)
- Staleness semantics — see [lineage.md](lineage.md#staleness-detection)
- Discovery algorithms — see [lineage.md](lineage.md#discovery-algorithms)
- Capsule externalization rule — see [Capsule Externalization Rule](#capsule-externalization-rule) below

**Stubs own role-specific operations (runtime authority):**

- What upstream capsule this skill can consume
- What downstream capsule this skill emits
- Fallback behavior when upstream capsule is absent or invalid
- Which shared semantics this skill executes (e.g., dialogue executes routing and materiality; AR and NS do not)
- When to suggest the next hop

Stub sizes are asymmetric by design — dialogue's stub is largest (routing, materiality, budget, discovery), AR and NS stubs are smaller (consume/emit with fallback).

Every skill MUST function correctly with only its inline stub. The contract is additive context — skill authors consult it when modifying composition behavior, but Claude does not require it at runtime.

## Capsule Externalization Rule

Same schema when externalized, no schema obligation when used as internal reasoning scaffolding.

Capsules are for externalized artifacts from explicit skill invocations. The global Adversarial Self-Review and Next Steps Planning protocols (in CLAUDE.md) may emit the same schema only on explicit user request.

## Versioning and Drift Detection

Contract versioning is a CI/review-time concern, not runtime. Each skill stub includes `implements_composition_contract: v1` as a drift detection marker. Sentinel versioning (`v1` in sentinel comments) handles runtime wire compatibility. Contract version stays out of capsule schemas.

**Contract location:** `packages/plugins/cross-model/references/composition-contract.md` — alongside the consultation contract, since all three skills interact through the cross-model dialogue system.

**Inverted authority model:** Unlike the consultation contract (which IS runtime-loaded), the composition contract is NOT. Stubs carry the runtime projection. Contract→stub drift is a silent correctness bug. Detection requires CI tooling (`validate_composition_contract.py`) that is designed but not yet implemented — see [delivery.md](delivery.md#open-items) item #6.

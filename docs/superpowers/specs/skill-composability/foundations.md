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
| **Advisory/tolerant** | Validate capsule if present; fall back to the appropriate alternative source if absent or invalid. Emit a one-line prose diagnostic when falling back. | NS consuming AR capsule; AR/NS consuming feedback capsule |
| **Strict/deterministic** | Reject invalid capsule but continue normal pipeline in baseline mode (no enriched decomposition, no upstream context injection) — no fallback to a different data source. | Dialogue consuming NS handoff |

**Fallback source by arc** (advisory/tolerant arcs only — strict/deterministic has no fallback source):

| Consumer | Upstream Capsule | Fallback Source |
|----------|-----------------|-----------------|
| NS consuming AR capsule | `ar-capsule:v1` | Prose parsing of AR's review output |
| AR consuming feedback capsule | `dialogue-feedback-capsule:v1` | Conversation context (prior dialogue synthesis visible in conversation) |
| NS consuming feedback capsule | `dialogue-feedback-capsule:v1` | Conversation context (prior dialogue synthesis visible in conversation) |

**Unknown sentinel versions:** See [capsule-contracts.md](capsule-contracts.md#unknown-version-behavior) for the normative rule. Summary: reject the capsule block, not the skill session. For advisory/tolerant consumers, this means applying the fallback source listed above. For strict/deterministic consumers, this means proceeding as if no upstream handoff is present (same as the "no sentinel found" case in [pipeline-integration.md](pipeline-integration.md#two-stage-admission)).

**Strict/deterministic baseline mode:** When the handoff is invalid or unknown-version, the pipeline runs in baseline mode — no enriched decomposition, no upstream context injection. This differs from advisory/tolerant in that no alternative source is consulted; the pipeline simply lacks upstream enrichment. The behavioral contract for strict/deterministic consumers is defined in [capsule-contracts.md](capsule-contracts.md#contract-2-ns--dialogue-ns-handoff-block).

## Three-Layer Delivery Authority

The composition system distributes authority across three layers:

| Layer | Owner | Authority | Audience |
|-------|-------|-----------|----------|
| **This spec** | Spec files (this directory) | Design authority — canonical definitions of all protocol semantics | Spec authors and reviewers |
| **Composition contract** | Shared reference document | Implementation-time reference — must conform to spec definitions; authoritative for inline stub authors (NOT runtime-loaded; stubs carry the runtime projection) | Skill authors modifying composition behavior |
| **Inline stubs** (per skill) | Each participating skill | Runtime authority — role-specific operational subset derived from the contract | Claude during skill execution |

See spec.yaml lines 57-61 for the external authority positioning comment (composition contract and inline stubs positioned in the authority hierarchy).

**Relationship between spec and contract:** Within this spec, the normative definitions live in the spec files ([routing-and-materiality.md](routing-and-materiality.md), [lineage.md](lineage.md), [capsule-contracts.md](capsule-contracts.md), etc.). The Composition contract is the runtime delivery artifact that must conform to — not supersede — these spec-file definitions. When the contract diverges from the spec, the spec is authoritative and the contract must be updated.

**Contract documents the runtime projection of protocol core (stubs carry it at runtime):**

- Sentinel/version rules and unknown-version handling — see [capsule-contracts.md](capsule-contracts.md#unknown-version-behavior)
- Artifact metadata schema — see [lineage.md](lineage.md#artifact-identity)
- Consumer class definitions — see [Consumer Classes](#consumer-classes) above
- Routing classification rules and precedence — see [routing-and-materiality.md](routing-and-materiality.md#routing-classification)
- Material-delta gating (tier semantics and evaluation flow) — see [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating)
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

Contract versioning is a CI/review-time concern, not runtime. Each skill stub includes `implements_composition_contract: v1` as a drift detection marker. The marker MUST appear in the skill's composition stub frontmatter or as a top-level key in the composition stub block — not in examples, comments, or disabled sections. The grep-based CI check ([verification.md](verification.md)) MUST verify the marker appears within the active composition stub boundaries. Sentinel versioning (`v1` in sentinel comments) handles runtime wire compatibility. Contract version stays out of capsule schemas.

**Contract location:** Contract file: `packages/plugins/cross-model/references/composition-contract.md`. See [delivery.md](delivery.md#skill-text-changes) for the full delivery specification. The contract sits alongside the consultation contract, since all three skills interact through the cross-model dialogue system.

**Inverted runtime loading:** Unlike the consultation contract (which IS runtime-loaded), the composition contract is NOT. Stubs carry the runtime projection. Contract→stub drift is a silent correctness bug. Detection requires CI tooling (`validate_composition_contract.py`) that is designed but not yet implemented — see [delivery.md](delivery.md#open-items) item #6.

**Interim drift mitigation protocol:** see [delivery.md](delivery.md#open-items) item #8. Contract→stub drift is bidirectional and is a P0 prerequisite check.

The interim drift mitigation protocol ([delivery.md](delivery.md#open-items) item #8) contains load-bearing MUST clauses that enforce this architectural invariant. These MUST clauses carry `architecture_rule` authority by reference — they are enforcement mechanisms for the contract→stub drift detection invariant defined in this section, not independent `implementation_plan` claims. Contradictions between item #8 and this section are spec defects (the architectural invariant governs).

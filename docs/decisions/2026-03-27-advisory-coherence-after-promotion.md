# Decision Record: Advisory Coherence After Promotion

**Date:** 2026-03-27
**Status:** Decided
**Stakes:** High
**Decision:** Which mechanism should restore advisory coherence after promotion in v1 without unnecessarily expanding Runtime Milestone R1 scope? (Architectural choice)

## 1. Decision

Choose how the system restores advisory coherence after a successful promotion changes HEAD in the primary workspace.

This is the T3 decision named in [decisions.md](../superpowers/specs/codex-collaboration/decisions.md#advisory-domain-stale-context-after-promotion). The decision is constrained by the resolved [context assembly contract](../superpowers/specs/codex-collaboration/foundations.md#context-assembly-contract), the advisory runtime lifecycle in [advisory-runtime-policy.md](../superpowers/specs/codex-collaboration/advisory-runtime-policy.md), and the current delivery rule that [`turn/steer` remains optional pending T3](../superpowers/specs/codex-collaboration/delivery.md#required-and-optional-methods).

## 2. Stakes

**High.** Reversibility is medium, but the blast radius is broad: this choice affects all post-promotion consultation and dialogue behavior, the build-step-1 boundary, and whether an optional App Server method becomes part of the critical path.

The stakes are elevated because the spec already identifies the race explicitly. After promotion, the advisory runtime may hold workspace context that no longer matches HEAD. [recovery-and-journal.md](../superpowers/specs/codex-collaboration/recovery-and-journal.md#advisory-delegation-race) says this is not a safety failure, but it is a coherence failure. The recommended mechanism therefore needs to preserve the trust model while keeping the first runtime-bearing slice small and defensible.

## 3. Options

- **Option A:** Mark advisory context stale at promotion time and inject a workspace-changed summary on the next advisory turn, reusing the same advisory runtime and thread.
- **Option B:** Fork the advisory thread on the next advisory turn after promotion, then continue on the forked post-promotion branch.
- **Option C:** Use `turn/steer` on the existing advisory thread to signal workspace change and refresh context in place.
- **Option D (Null):** Do nothing automatically; leave post-promotion coherence to manual restart or user/operator discipline.

## 4. Information Gaps

### Gap 1: How effective is same-thread context injection at suppressing stale workspace assumptions?

- **Most affects:** Option A
- **Can it be resolved before commitment?** Partially. A narrow prototype or simulation can test whether a post-promotion turn grounded with an explicit workspace-changed summary behaves coherently enough for v1.
- **If unresolved:** The decision must still be made under uncertainty, because Runtime Milestone R1 scoping depends on whether `turn/steer` remains optional.

### Gap 2: Does App Server `turn/steer` provide materially stronger mid-thread coherence semantics than packet-level context injection?

- **Most affects:** Option C
- **Can it be resolved before commitment?** Partially, but not cheaply. It would require a targeted prototype and depends on semantics that the current spec does not yet rely on.
- **If unresolved:** Option C remains speculative and cannot justify becoming part of the build-step-1 critical path.

### Gap 3: Is explicit pre-promotion vs post-promotion advisory lineage a product requirement?

- **Most affects:** Option B
- **Can it be resolved before commitment?** Yes. This is a product/UX judgment about whether the system should surface promotions as thread branches rather than silent continuity.
- **If unresolved:** Favor the simpler continuity model and revisit if lineage needs become explicit.

## 5. Evaluation

### Option A: Same-thread stale flag plus next-turn context injection

**Strengths**

- Matches the current spec framing in [recovery-and-journal.md](../superpowers/specs/codex-collaboration/recovery-and-journal.md#advisory-delegation-race): the issue is coherence, not safety.
- Does not require `turn/steer`, so it preserves the current delivery position that `turn/steer` is optional pending T3.
- Respects the turn-boundary invariants in [advisory-runtime-policy.md](../superpowers/specs/codex-collaboration/advisory-runtime-policy.md#turn-boundary-invariants): the system does not mutate runtime policy or rotate mid-turn.
- Keeps Runtime Milestone R1 focused on the control plane and packet assembly rather than on additional App Server capabilities.
- Fits cleanly with the resolved context assembly contract: the control plane can inject summary-form workspace-change context on the next turn without widening advisory-to-execution flow.

**Weaknesses and risks**

- Reuses the same advisory thread, so stale latent assumptions in the model may persist more than they would with a structural branch.
- Relies on prompt packet quality rather than a stronger server-side semantic primitive.
- May be less visible to users than an explicit branch after promotion.

**Best when**

- v1 wants the smallest coherent mechanism that preserves current method tiers.
- Promotion-induced staleness is treated as an informational reset problem, not a hard state invalidation problem.
- Explicit post-promotion thread branching is not yet a product requirement.

### Option B: Next-turn thread fork into a post-promotion branch

**Strengths**

- Uses `thread/fork`, which is already a required method in the compatibility baseline.
- Creates a clean structural boundary between pre-promotion and post-promotion advisory reasoning.
- Preserves older advisory context for inspection while making the new branch explicitly post-promotion.
- More robust than same-thread continuity if latent stale assumptions prove hard to suppress through packet design alone.

**Weaknesses and risks**

- Adds thread and lineage-management complexity to Runtime Milestone R1 or the immediately following slice.
- Risks over-signaling promotion as a dialogue-branching event even when the user expects conversational continuity.
- Still requires a fresh context packet; the fork does not eliminate the need for context injection or refresh.

**Best when**

- Product semantics value explicit pre/post-promotion lineage.
- Same-thread context injection proves insufficient in practice.
- The team wants to avoid depending on `turn/steer` while still choosing a more structural reset.

### Option C: `turn/steer` on the existing advisory thread

**Strengths**

- Preserves a single thread and gives the control plane an explicit App Server mechanism for post-promotion guidance.
- Could become the cleanest long-term model if `turn/steer` proves to be a reliable mid-thread coherence primitive.
- Keeps user-visible dialogue continuity straightforward if the underlying semantics are strong enough.

**Weaknesses and risks**

- `turn/steer` is currently optional in [delivery.md](../superpowers/specs/codex-collaboration/delivery.md#required-and-optional-methods). Choosing it would either force Runtime Milestone R1 to depend on an optional method or force a compatibility-policy change.
- Semantics are less grounded in the current spec than thread fork or packet-level injection.
- Increases implementation and testing burden around a method the baseline deliberately treated as non-critical.

**Best when**

- A targeted prototype shows that `turn/steer` materially outperforms packet injection or thread fork for coherence.
- The project is willing to revise the current required/optional method boundary.
- Build step 1 can absorb the additional compatibility and runtime complexity.

### Option D (Null): Manual refresh only

**Strengths**

- Lowest implementation effort.
- Keeps Runtime Milestone R1 narrowly scoped to handshake, capability probe, and basic runtime bring-up.

**Weaknesses and risks**

- Leaves a known coherence gap unresolved after the spec has already named it.
- Pushes reliability onto user discipline or operator convention rather than system behavior.
- Conflicts with the design direction in [recovery-and-journal.md](../superpowers/specs/codex-collaboration/recovery-and-journal.md#advisory-delegation-race), which already recommends a workspace-changed signal after promotion.

**Best when**

- Advisory sessions never survive promotion in practice, or
- The project consciously decides that post-promotion advisory coherence is out of scope for v1

Neither condition matches the current spec direction.

## 6. Sensitivity Analysis

- **Option B beats Option A if** explicit pre/post-promotion lineage becomes a user-facing requirement, or if a lightweight prototype shows that same-thread context injection leaves too much stale reasoning intact.
- **Option C beats Option A if** `turn/steer` semantics prove materially stronger than packet injection and the project is willing to move `turn/steer` out of the optional tier.
- **Option D beats Option A only if** the project narrows scope further and explicitly accepts manual refresh as the product story for v1. That would be a real scope reduction, not just an implementation shortcut.

No realistic sensitivity flip currently makes Option C better than Option B as the non-recommended fallback. Under current constraints, if packet injection proves insufficient, the next-best move is structural thread fork, not optional-method dependency.

## 7. Ranked Options

1. **Option A — Same-thread stale flag plus next-turn context injection** - best balance of coherence, simplicity, and fit with the current compatibility boundary.
2. **Option B — Next-turn thread fork into a post-promotion branch** - stronger structural reset than Option A, but with more lineage and UX complexity.
3. **Option C — `turn/steer` on the existing thread** - promising only if future evidence justifies promoting an optional method into the critical path.
4. **Option D (Null) — Manual refresh only** - simplest, but knowingly leaves a named coherence gap unresolved.

## 8. Recommendation

**Recommend Option A:** after promotion, mark the advisory context stale and require the next advisory turn to include a control-plane-injected workspace-changed summary plus refreshed repository identity/context in the same advisory thread.

This is the best fit with the current spec because it solves the named coherence problem without expanding Runtime Milestone R1 to depend on `turn/steer`, and without reinterpreting advisory runtime rotation as a freshness mechanism. If same-thread injection later proves insufficient, the most coherent fallback is Option B: next-turn thread fork on promotion boundaries.

## 9. Readiness

**Readiness:** `best available`

The ranking is stable enough to guide T3 and keep Runtime Milestone R1 small, but it is not yet `verifiably best` because two material gaps remain:

1. A lightweight prototype has not yet confirmed that same-thread context injection is sufficient in realistic post-promotion advisory turns.
2. The product stance on whether promotion boundaries should create explicit advisory lineage has not yet been decided.

This recommendation becomes `verifiably best` if:

- a targeted prototype or implementation spike shows that next-turn context injection reliably restores coherence after promotion, and
- no requirement emerges for explicit post-promotion thread branching as a first-class user-facing concept.

## References

- [decisions.md §Advisory Domain Stale Context After Promotion](../superpowers/specs/codex-collaboration/decisions.md#advisory-domain-stale-context-after-promotion)
- [foundations.md §Context Assembly Contract](../superpowers/specs/codex-collaboration/foundations.md#context-assembly-contract)
- [advisory-runtime-policy.md §Turn Boundary Invariants](../superpowers/specs/codex-collaboration/advisory-runtime-policy.md#turn-boundary-invariants)
- [recovery-and-journal.md §Advisory-Delegation Race](../superpowers/specs/codex-collaboration/recovery-and-journal.md#advisory-delegation-race)
- [promotion-protocol.md §Workspace Effects](../superpowers/specs/codex-collaboration/promotion-protocol.md#workspace-effects)
- [delivery.md §Required and Optional Methods](../superpowers/specs/codex-collaboration/delivery.md#required-and-optional-methods)

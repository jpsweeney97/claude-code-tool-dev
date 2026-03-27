# Cross-Model Next V1 Runtime Shape Recommendation

## 1. Decision

Which architectural correction should `cross-model-next` make before V1 implementation starts?

Decision type: architectural choice

## 2. Stakes

High.

This decision is hard to unwind once the plugin surface, JSON-RPC broker, tests, and migration path are in place. The blast radius spans all intended V1 flows: consult, dialogue, review, analytics, and coexistence with the legacy plugin.

## 3. Options

### Option A: Keep the single advisory broker shape, but harden the contract before implementation

Retain one long-lived advisory `codex app-server` child plus the existing `context-injection` sidecar for dialogue, but tighten the design before coding:

- make `approvalPolicy` and `sandbox` broker-enforced invariants rather than caller-controlled inputs
- define bounded concurrency, queueing, overload, and cancellation semantics
- persist minimal fork and continuity metadata needed to survive broker restart
- add startup compatibility negotiation against the installed Codex binary
- define an event schema, redaction rules, and retention policy for `${CLAUDE_PLUGIN_DATA}/events.jsonl`
- explicitly label `context-injection` as either transitional or permanent, with an exit condition if transitional

### Option B: Stage the rollout and cut dialogue from V1

Ship the new broker for consult and detached review first. Defer dialogue until either `context-injection` is absorbed into the broker control plane or its long-term contract is written as a first-class subsystem contract.

### Option C: Build multi-lane runtime isolation now

Keep the overall migration, but split advisory traffic across more than one App Server runtime or lane now, for example separate consult vs dialogue/review workers, to reduce head-of-line blocking and shared failure domains.

### Option D: Implement the current spec as written

Preserve the current V1 scope and process model without adding stronger runtime invariants or rollout constraints.

### Option E: Null option, defer the migration

Keep the legacy `cross-model` plugin as the active path and postpone `cross-model-next` until the App Server compatibility and control-plane questions are resolved.

## 4. Information gaps

| Gap | Most affects | Can it be resolved before commitment? | Notes |
| --- | --- | --- | --- |
| Actual concurrency demand for advisory flows | A, B, C | Yes | Resolve with explicit target capacity and expected parallelism. If concurrency is low, one child with bounded admission is more defensible. |
| Compatibility stability of the installed local `codex app-server` binary | A, B, C, D | Yes | Resolve with a short capability/version spike and a startup gate in the broker. |
| Whether dialogue still justifies a retained `context-injection` sidecar | A, B | Partially | Resolve by deciding whether the sidecar is a migration adapter or a permanent subsystem. |
| Acceptable retention and sensitivity policy for advisory analytics | A, C, D | Yes | Resolve by naming the minimal event schema and retention rule before implementation. |

This decision can be made now, but it remains under uncertainty. The largest unresolved issue is not whether App Server is the right substrate. It is whether the plugin will enforce its advisory-only runtime contract in executable code rather than prose.

## 5. Evaluate options

### Criteria

| Criterion | Weight | Definition |
| --- | --- | --- |
| Trust-boundary rigor | 5 | Keeps advisory execution posture deterministic and broker-owned |
| Failure containment and recovery | 5 | Prevents one slow or broken flow from taking down the whole advisory surface |
| Scope discipline for V1 | 4 | Fixes the highest-risk gaps without turning V1 into a second rewrite |
| Capability retention | 4 | Preserves the intended value of V1, especially consult, dialogue, and review |
| Migration clarity | 4 | Coexists cleanly with the legacy plugin and the locally installed Codex binary |

### Option A: Harden the current broker shape

Key strengths:

- Preserves the intended V1 capability set.
- Fixes the largest architectural gaps without discarding the chosen migration direction.
- Keeps complexity focused on explicit invariants instead of multiplying runtimes early.
- Leaves room to learn from real advisory traffic before committing to a more complex isolation model.

Key weaknesses or risks:

- Still leaves a shared child process as a real failure and contention domain.
- Requires discipline to keep "hardening" from sprawling into an open-ended redesign.
- Retains the dialogue-side special case unless `context-injection` is explicitly reframed.

Conditions under which it is the best choice:

- You still want dialogue in V1.
- Expected advisory concurrency is moderate rather than high.
- You are willing to spend a short up-front design pass to convert policy and recovery claims into explicit broker-owned rules.

### Option B: Stage the rollout and cut dialogue from V1

Key strengths:

- Simplifies the first release materially.
- Removes the most awkward hybrid boundary in the current design.
- Gives the broker and App Server compatibility story a narrower surface to prove out.

Key weaknesses or risks:

- Drops one of the most differentiated V1 capabilities.
- Creates a likely second launch and another migration decision shortly after V1.
- Risks optimizing for the easiest flows instead of the most architecturally revealing one.

Conditions under which it is the best choice:

- Dialogue is not essential to the first release.
- `context-injection` cannot be given a clear contract quickly.
- You want maximum probability of a stable first release even at the cost of a smaller feature set.

### Option C: Build multi-lane isolation now

Key strengths:

- Improves failure containment and reduces head-of-line blocking risk.
- Makes future SLOs easier to reason about if advisory traffic becomes heavier.
- Reduces the chance that review or dialogue workloads starve quick consult paths.

Key weaknesses or risks:

- Adds substantial lifecycle and testing complexity before usage data exists.
- Makes policy enforcement, telemetry, and recovery semantics harder because there are now multiple live runtimes.
- Risks solving a scaling problem before the compatibility and contract problems are solved.

Conditions under which it is the best choice:

- You already know advisory traffic will be concurrent and latency-sensitive.
- A single runtime is known to be insufficient.
- The team is prepared to pay the supervision and observability cost immediately.

### Option D: Implement the current spec as written

Key strengths:

- Fastest path to starting implementation.
- Preserves the planned V1 scope without negotiation.
- Avoids adding more planning work in the short term.

Key weaknesses or risks:

- Leaves the advisory trust boundary soft because caller-controlled policy fields remain in the tool surface.
- Leaves overload, fairness, and restart semantics underdefined.
- Leaves thread continuity split between durable App Server state and in-memory lineage metadata.
- Leaves analytics as durable data without a named policy.

Conditions under which it is the best choice:

- This is explicitly a throwaway prototype rather than a production-bound V1.

### Option E: Defer the migration

Key strengths:

- Avoids locking in the wrong runtime shape.
- Buys time to validate App Server compatibility and host constraints.
- Keeps the current plugin behavior stable while uncertainties are resolved.

Key weaknesses or risks:

- Preserves the limits of the current `codex exec` transport.
- Delays learning on the actual target architecture.
- Risks losing momentum and keeping the current plugin longer than intended.

Conditions under which it is the best choice:

- A short compatibility spike cannot establish a safe startup contract.
- The host cannot safely support the broker lifecycle model.

### Scorecard

| Option | Trust-boundary rigor | Failure containment and recovery | Scope discipline for V1 | Capability retention | Migration clarity | Total |
| --- | --- | --- | --- | --- | --- | --- |
| A | 5 | 4 | 5 | 5 | 4 | 91 |
| B | 5 | 5 | 4 | 3 | 4 | 86 |
| C | 4 | 5 | 2 | 5 | 3 | 74 |
| E | 4 | 4 | 5 | 1 | 3 | 69 |
| D | 2 | 2 | 5 | 5 | 2 | 62 |

## 6. Sensitivity analysis

### What would make Option B better than Option A

- Dialogue is not needed in the first release.
- `context-injection` cannot be given a clear transition or permanence decision quickly.
- The team wants to minimize first-release risk even if that means a narrower V1.

### What would make Option C better than Option A

- Advisory flows must support materially higher concurrency or tighter latency isolation than a single child can provide.
- Early measurements show head-of-line blocking is already a practical problem, not just a theoretical one.

### What would make Option E better than Option A

- A short App Server spike cannot produce a reliable startup compatibility gate.
- The plugin host cannot safely supervise the required broker lifecycle.

### What would make Option D better than Option A

- Almost nothing short of "this is only a disposable prototype." For a production-bound V1, implementing the spec as written is dominated by Option A.

## 7. Ranked options

1. **Option A: Keep the single advisory broker shape, but harden the contract before implementation** - Best balance of risk reduction, V1 scope retention, and architectural coherence.
2. **Option B: Stage the rollout and cut dialogue from V1** - Best fallback if dialogue and `context-injection` cannot be made explicit quickly.
3. **Option C: Build multi-lane runtime isolation now** - Strong on containment, but premature without usage or compatibility evidence.
4. **Option E: Defer the migration** - Safer than shipping a soft contract, but gives up too much learning and capability.
5. **Option D: Implement the current spec as written** - Fastest to start, but it encodes the reviewed risks instead of resolving them.

## 8. Recommendation

Choose **Option A**.

The disagreement with the current direction is narrow but important: the spec should not be implemented as written. The architecture shape is still the right one for V1, but only if the advisory runtime contract becomes executable and broker-owned instead of implied by prose. That means treating policy enforcement, overload behavior, continuity metadata, compatibility gating, analytics data handling, and the `context-injection` role as first-class architecture decisions before code starts.

Recommended corrections to the spec before implementation:

1. Make `approvalPolicy` and `sandbox` broker-enforced invariants, not caller-controlled execution settings.
2. Add bounded admission, queue, cancellation, and overload semantics for the singleton advisory child.
3. Persist or deterministically derive the minimum lineage metadata needed for restart-safe `thread-read` and `thread-fork`.
4. Add startup compatibility negotiation and a supported-binary policy for the installed local Codex binary.
5. Define an event schema, redaction rule, and retention policy for `${CLAUDE_PLUGIN_DATA}/events.jsonl`.
6. Mark `context-injection` explicitly as transitional or permanent. If transitional, add the exit condition now.

Fallback rule:

If the team cannot resolve items 1, 4, and 6 in a short spike, switch to **Option B** and remove dialogue from V1 rather than implementing the current hybrid shape half-defined.

## 9. Readiness

`best available`

This is the best recommendation from the current evidence, but it is not yet `verifiably best` because the ranking could still flip if a short spike shows that the local App Server compatibility envelope is unstable, the host cannot supervise the required broker lifecycle, or dialogue cannot justify the retained `context-injection` sidecar.

This becomes `verifiably best` when all of the following are true:

- the broker can reject unsupported local Codex/App Server versions at startup
- the advisory execution policy is broker-owned and not caller-expandable
- the role of `context-injection` is explicitly decided
- bounded overload and restart semantics are written into the spec


# Decision Record: codex-collaboration Drift Synthesis Recovery

**Date:** 2026-04-29
**Status:** Decided
**Stakes:** High
**Decision:** What status topology should `codex-collaboration` use so the repo has one trustworthy current-state reader entry point without collapsing authority ownership, drift typing, and open-work tracking into a single file?

## 1. Decision

Adopt the following topology:

- **Canonical reader entry point:** a new current-state synthesis document under
  `docs/status/`
- **Open/unreconciled-work index:** the existing
  `docs/status/codex-collaboration-reconciliation-register.md`
- **Supporting audit evidence only:** the rejected assessment in
  `docs/assessments/`, explicitly labeled non-authoritative or superseded if
  retained

The new synthesis document MUST say both:

- **"Start here for current state"**
- **"This document is not a behavioral tie-breaker"**

The reconciliation register MUST explicitly remain the bounded index for open or
unreconciled work, not the long-form current-state synthesis.

When recording drift findings or reconciliation items, use separate fields:

- `authority_owner`
- `drift_type`
- `repair_target`
- `evidence_basis` (recommended)

`authority_owner` MUST use the real owner set from
`docs/superpowers/specs/codex-collaboration/spec.yaml`:

- `foundation`
- `contracts`
- `promotion-contract`
- `advisory-policy`
- `recovery-contract`
- `delivery`
- `decisions`
- `supporting`

`status` is **not** a behavioral authority owner. It is a synthesis/routing
layer only. It may appear as a `repair_target` when the problem is stale
current-state synthesis, missing index rows, or broken reader routing.

## 2. Stakes

**High.** This decision determines where future readers begin, how they route to
open work, and whether reconciliation edits target the correct artifact class.

The blast radius is wide because the repo already splits truth across spec,
status, tickets, diagnostics, and implementation. A bad topology would keep
adding reader paths without resolving ambiguity.

## 3. Context

The rejected drift assessment surfaced real contradictions and stale status, but
it lived in `docs/assessments/`, which is not a current-state authority layer.

The live reconciliation register already defines itself as a **working index** of
still-open, still-deferred, or still-unreconciled work and pushes excess detail
back to owning artifacts:

- `docs/status/codex-collaboration-reconciliation-register.md:7-20`
- `docs/status/codex-collaboration-reconciliation-register.md:107-109`

The owner model for behavioral truth already exists in the spec authority map:

- `docs/superpowers/specs/codex-collaboration/spec.yaml:4-99`

The missing piece is reader topology:

- where a new reader should start,
- where unresolved work is indexed,
- how assessment-layer evidence is demoted,
- how findings map to owner, drift type, and repair target separately.

## 4. Options

### Option 1: New canonical synthesis doc in `docs/status/` plus bounded register

Create a new current-state synthesis document under `docs/status/` and keep the
existing register as the unresolved-work index.

### Option 2: Register-only architecture

Keep a single status-layer artifact by expanding the reconciliation register into
both the current-state synthesis and the unresolved-work index.

### Option 3: Direction only, topology still pending

Keep the recovery direction but defer the choice between a new synthesis doc and
an expanded register.

### Option 4: Null option — leave the current decision as-is

Do not resolve the topology branch and do not change the existing artifacts yet.

## 5. Evaluation

### Option 1: New synthesis doc plus bounded register

**Strengths**

- Best role separation
- Preserves the register's existing contract as a churn-heavy unresolved-work
  index
- Gives future readers one stable current-state entry point
- Keeps reader orientation separate from open-work tracking

**Weaknesses / risks**

- Introduces a second status-layer file, so routing must be explicit

**Best when**

- The repo needs both stable reader orientation and a bounded unresolved-work
  index

### Option 2: Register-only architecture

**Strengths**

- Minimal artifact count
- Stronger than the earlier decision draft gave it credit for
- Keeps everything in the existing `docs/status/` layer

**Weaknesses / risks**

- Forces one file to do two materially different jobs:
  stable current-state orientation and churn-heavy unresolved-work tracking
- Would require an implicit role change for a file that currently defines itself
  as an index, not a full synthesis
- Increases the risk that the entry point becomes noisy as open work churns

**Best when**

- One status file matters more than role separation, and the repo is willing to
  redefine the register's contract explicitly

### Option 3: Direction only, topology pending

**Strengths**

- Honest about unresolved architecture

**Weaknesses / risks**

- Not mechanically safe to implement
- Leaves future edits free to diverge immediately
- Makes `Status: Decided` misleading

**Best when**

- The topology genuinely cannot be chosen yet

### Option 4: Leave the current decision as-is

**Strengths**

- Zero immediate work

**Weaknesses / risks**

- Leaves topology unresolved
- Leaves the finding schema underspecified
- Leaves the assessment-layer demotion incomplete

**Best when**

- No one will rely on the current decision or the rejected assessment

## 6. Sensitivity Analysis

- **Option 2 becomes better** if minimizing artifact count matters more than
  keeping stable orientation separate from open-work churn, and the repo is
  willing to explicitly redefine the register as the canonical current-state
  source.
- **Option 3 becomes better** only if the team is not ready to choose a topology
  now, in which case this record should not be marked `Decided`.
- No realistic condition makes Option 4 acceptable for the stated problem.

## 7. Ranked Options

1. **Option 1 — New canonical synthesis doc in `docs/status/` plus bounded register** - best role separation and clearest reader routing
2. **Option 2 — Register-only architecture** - viable, but weaker because it overloads one file with two different jobs
3. **Option 3 — Direction only, topology pending** - honest but not implementation-safe
4. **Option 4 — Leave the current decision as-is** - unresolved and mechanically unsafe

## 8. Recommendation

**Recommend Option 1.**

Create a new canonical synthesis document under `docs/status/` and keep the
existing reconciliation register as the bounded unresolved-work index. Label the
assessment as supporting evidence only if retained.

This keeps current-state orientation, unresolved-work indexing, and behavioral
authority ownership separate. That separation is the decisive reason Option 1 is
better than register-only for this repo.

## 9. Readiness

**Readiness:** `verifiably best`

The topology branch is now resolved, the owner model is explicit, and the reader
routing has already been implemented in the shipped status-layer artifacts.

Remaining work, if any, is follow-on maintenance of those artifacts rather than
topology implementation or further architecture selection.

## References

- [codex-collaboration authority map](../superpowers/specs/codex-collaboration/spec.yaml)
- [codex-collaboration reconciliation register](../status/codex-collaboration-reconciliation-register.md)
- [rejected drift report](../assessments/2026-04-29-codex-collaboration-verified-drift-report.md)

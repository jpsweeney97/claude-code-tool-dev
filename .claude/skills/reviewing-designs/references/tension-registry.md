# Tension Registry

Canonical tensions for design review, sourced from `system-design-review/references/system-design-dimensions.md`. This registry is a **default map, not a closed world** — custom tensions are valid when they pass all inclusion rules.

The registry serves two purposes:
1. A shared vocabulary of known architectural tensions
2. The source for dynamically-generated per-run collaboration playbooks

## Canonical Tensions

| ID | Tension | Reviewers Involved | Common Manifestation |
|----|---------|-------------------|---------------------|
| CT-1 | Performance ↔ Correctness | behavioral, data | Caching improves latency but introduces staleness. Denormalization speeds reads but creates consistency obligations. |
| CT-2 | Changeability ↔ Performance | change, behavioral | Indirection enables swapping but adds overhead. Real mainly on hot paths or at scale. |
| CT-3 | Completeness ↔ Changeability | structural-cognitive, change | Highly specified designs resist change. Failure mode is premature generalization. |
| CT-4 | Security ↔ Operability | trust-safety, reliability-operational | Least-privilege and audit logging add friction to deploys and debugging. |
| CT-5 | Legibility ↔ Performance | structural-cognitive, behavioral | Readable designs and optimized designs diverge on hot paths. Often overstated elsewhere. |
| CT-6 | Consistency ↔ Availability | behavioral, reliability-operational | Stronger consistency requires coordination that blocks during failures. |
| CT-7 | Composability ↔ Coherence | structural-cognitive, change | Reusable components with generic interfaces feel incoherent when assembled. |

## Custom Tensions

Custom tensions are valid when they pass all inclusion rules. During synthesis, the lead assigns permanent IDs continuing from the canonical sequence (CT-8, CT-9, etc.). Custom tensions carry `kind: custom`; canonical tensions carry `kind: canonical`.

## Inclusion Rules

Emit a tension only when ALL of the following hold:

1. Both sides have concrete anchors in the input (not hypothetical concerns).
2. The tradeoff mechanism is explainable specifically for this system.
3. Why the tradeoff was easy to miss is explainable.
4. The tension explains at least 1 concrete finding.
5. The wording is specific to this system, not generic architecture prose.

Before emitting a tension, verify all 6 lines:

1. Side A anchor
2. Side B anchor
3. The decision or default that pulled toward side A
4. The cost or blind spot that appeared on side B
5. Why a reviewer could miss this
6. Which finding(s) this tension explains

`0` tensions is a valid count. Do not force one for completeness.

## Tension Schema

```markdown
### [T-N] Tension name

- **tension_id:** CT-N
- **kind:** canonical / custom
- **sides:** [Side A] ↔ [Side B]
- **what_is_traded:** 1-2 sentences
- **why_it_hid:** 1-2 sentences
- **likely_failure_story:** 1-2 sentences
- **linked_findings:** F1, F3
- **anchors:** side_a: source#section, side_b: source#section
- **reviewers_involved:** [list of reviewer IDs who contributed evidence]
```

## Per-Run Playbook Generation

During Phase 2 (Staff), after generating the emphasis map, the lead intersects the tension registry with the current roster and emphasis map to produce per-run collaboration entries.

### Algorithm

1. For each canonical tension, check if both involved reviewers are in the active roster (not suppressed).
2. If both are active, include the tension in each involved reviewer's playbook as a "watch for" signal.
3. Weight by emphasis: if a reviewer's relevant category is `primary` or `secondary`, mark the tension as `high attention`; if `background`, mark as `low attention`.
4. Skip tensions where both involved categories are `scope-inapplicable`.

### Playbook Entry Format

Include in spawn prompt alongside the static collaboration playbook from `reviewer-briefs.md`:

```
Per-run tension watch:
- CT-4 (Security ↔ Operability) [high attention]: If you find trust boundary or audit concerns that create operational friction, message reliability-operational with the specific tradeoff.
- CT-5 (Legibility ↔ Performance) [low attention]: If naming or structural clarity is sacrificed for performance, message behavioral with the specific case.
```

The static collaboration playbooks in `reviewer-briefs.md` cover general cross-reviewer coordination. The per-run entries add context-specific tension signals based on the emphasis map — both are included in spawn prompts.

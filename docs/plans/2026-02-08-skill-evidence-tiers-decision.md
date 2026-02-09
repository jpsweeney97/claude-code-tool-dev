# Decision: Two-Tier Evidence Bar for Skill Validation

**Date:** 2026-02-08
**Context:** After 60+ benchmark runs across three cycles (v0, v1 pilot, discriminability experiment), the evidence is clear: skills reliably change Claude's process but don't measurably improve output quality at the current task difficulty. General rubric-based quality benchmarking has hit a ceiling effect. Need to decide what "sufficient evidence of skill value" means going forward.
**Prior decisions:** `docs/plans/2026-02-08-benchmark-next-steps-decision.md`, `docs/plans/2026-02-08-behavioral-markers-pivot.md`

## Decision

Adopt a two-tier evidence bar for skill validation.

### Tier A: "Skill works as process" (default finish line)

Behavioral compliance **plus strict internal-consistency checks** is sufficient evidence for the claim:

> "This skill reliably induces its intended workflow behaviors."

**What Tier A requires:**
- Behavioral markers with pre-registered definitions (per the protocol in `docs/plans/2026-02-08-behavioral-markers-pivot.md`)
- Perfect or near-perfect separation between skill-present and skill-absent conditions
- Strict marker variants pass (counts match parsed structures, threshold checks reference correct items, verification sections are internally consistent)

**What Tier A does NOT claim:**
- That the skill improves output quality
- That the behavioral changes produce better outcomes
- That the skill is useful (only that it works as designed)

Tier A is the finish line for most skills. A skill that reliably induces its intended behaviors is a working skill — whether those behaviors are *valuable* is a design judgment by the skill author, not a benchmark finding.

### Tier B: "Skill helps quality" (only when needed)

Targeted outcome tests for specific skills and failure modes, and/or structured field evidence, but only when the project needs to justify a quality-improvement claim.

**What Tier B requires:**
- A concrete, pre-registered hypothesis ("skill X prevents failure mode Y on task type Z")
- Task difficulty calibrated so baseline Claude makes observable errors
- Pre-registered success criteria before execution
- Blinded evaluation (same discipline as the discriminability experiment)

**What Tier B does NOT require:**
- General-purpose quality benchmarking infrastructure
- Coverage of all skills or all scenarios
- Rubric-based scoring (may use behavioral markers, targeted correctness checks, or whatever measurement fits the hypothesis)

### Decision Triggers: When to Move Beyond Tier A

Move to Tier B if any of these become true:

1. **Higher-stakes use:** A skill is being used in decisions where outcome correctness matters materially (e.g., security analysis, production incident response).
2. **Quality claim needed:** You want to publish or communicate a claim that implies quality improvement, not just behavior change.
3. **Compliance theater observed:** Marker compliance is present but perceived usefulness is absent — the skill induces the ritual without improving the result. (Note: this trigger depends on attentive use, not formal measurement. It's a reason to investigate, not an automated signal.)

## What This Closes

- **The general rubric-based quality benchmark project** is parked as a default path. The discriminability experiment showed that correctness-focused rubrics hit ceiling effects on tasks within Claude's capability range. Rubric infrastructure is archived, not deleted — it can be revived for Tier B if a specific hypothesis needs it.
- **The "do skills improve quality?" question** is reframed: the answer is "not measurably at this task difficulty" and the measurement project's contribution was proving that rigorously.

## What Remains (Tier A Completion)

1. Pre-register markers for scenarios 101 and 103 (the derivation set is scenario 102 only)
2. Test pre-registered markers on existing pilot data for 101/103
3. Build detection scripts with strict variants
4. Validate on all existing data (10 outputs across 3 scenarios)

After these steps, Tier A infrastructure is complete and the measurement project concludes.

## Relationship to Prior Work

| Phase | Question | Answer | Status |
|-------|----------|--------|--------|
| v0 benchmark (51 runs) | Do skills improve rubric scores? | Inconclusive (ceiling effects, confounders) | Closed |
| v1 pilot (6 runs) | Do skills improve rubric scores on better scenarios? | No (0/3 improvement) | Closed |
| Discriminability (6 runs) | Can rubrics detect skill effects at all? | No (delta ≈ 0 at ceiling) | Closed |
| Behavioral markers pivot | Do skills change behavior detectably? | Yes (perfect separation on 102, exploratory on 101, non-finding on 103) | **Closed — see `docs/plans/2026-02-08-tier-a-closure.md`** |
| Tier B | Do skills improve quality on hard tasks? | Not yet tested | **Parked — trigger-gated** |

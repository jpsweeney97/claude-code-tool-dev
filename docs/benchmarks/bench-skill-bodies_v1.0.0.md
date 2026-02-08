# Synthetic Benchmark Skill Bodies v1.0.0 (BENCH_*)

Canonical injected bodies for Benchmark v1 pilot.

Primary consumers:
- `docs/benchmarks/suites/benchmark-v1-draft_v0.1.0.md`
- `docs/benchmarks/operations/benchmark-v1_pilot_checklist_v0.1.0.md`

These bodies are the source of truth for `condition=target` in v1 pilot runs.
If run records use modified text not matching this file, results must be labeled `SMOKE_ONLY`.

---

## BENCH_DISCIPLINE_CONSTRAINT_LEDGER_v1.0.0

**Intent:** Enforce exact structural discipline and score-to-recommendation coherence.

```md
---
Follow output constraints exactly.

You MUST provide exactly 3 options (no more, no less). For each option include:
- 2 strengths
- 2 weaknesses
- risk level (low/med/high)

Then provide a weighted score table where weights sum to 100.

Before finalizing: verify that your recommended option is the highest-scoring option
in your table. If it is not, revise either the recommendation or the scores —
do not leave a mismatch between your table and your conclusion.

Do not add honorable mentions or extra options.
---
```

Expected effect:
- Improves strict count/structure compliance.
- Cross-check step catches recommendation-score mismatches that declarative "be consistent" instructions miss.

---

## BENCH_REFERENCE_EVIDENCE_CALIBRATION_v1.0.0

**Intent:** Enforce observation/inference typing, confidence downgrades under conflicting evidence, and structural precision.

```md
---
For evidence analysis tasks:
1) Label each claim as Observation or Inference.
2) Cite supporting evidence for every claim.
3) If evidence conflicts, explicitly reduce confidence and explain why.
4) Avoid unsupported assertions.

When confidence is downgraded, make the downgrade visible in the final output.

When the task specifies an exact count of items (e.g., "exactly N claims,"
"exactly N checks"), verify your output matches that count before finishing.
Count explicitly — do not estimate.

When the task specifies numeric thresholds for specific conditions (e.g.,
confidence <= X when Y), apply those thresholds exactly as stated.
Do not round, approximate, or substitute qualitative language for the
specified numeric format.
---
```

Expected effect:
- Improves conflict-aware calibration and reduces overconfident claims.
- Cardinality enforcement catches exact-count drift under multi-constraint prompts.
- Threshold precision prevents qualitative substitution for numeric requirements.

---

## BENCH_PATTERN_VERDICT_GATING_v1.0.0

**Intent:** Enforce threshold-first verdict logic with visible arithmetic and structured confidence downgrades.

```md
---
When producing benchmark verdicts:
1) Show intermediate calculations step by step. Do not state a derived number
   without showing the arithmetic that produced it.
2) Apply stated threshold rules directly to select verdict. State which rule
   applied and why.
3) Separate Evidence and Interpretation structurally.
4) When downgrading confidence, use this structure:
   - State base confidence level.
   - List each downgrade factor and its impact.
   - State final confidence level.
   The downgrade must appear as a distinct step, not embedded in narrative.
5) Provide concrete decision triggers that would change verdict.
---
```

Expected effect:
- Show-your-work step makes arithmetic errors visible and catchable by evaluator.
- Structured downgrade format prevents the v0 failure mode of "confounders mentioned narratively with no confidence impact."
- Rule citation ties verdict to threshold logic rather than narrative judgment.

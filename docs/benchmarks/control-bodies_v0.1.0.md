# Control Bodies v0.1.0 (Benchmark Instruments)

This file defines canonical **control “skill bodies”** used by the Simulation Effectiveness Benchmark to validate measurement integrity.

## How to Use These Controls

These are not normal skills with YAML frontmatter. They are **instruction blocks** designed to be pasted into the scenario skill file’s standardized injection slot:

- Heading: `## Loaded Skill`
- Wrap the control body in delimiter lines: `---` … `---`
- For baseline runs, omit the entire `## Loaded Skill` section (do not include an empty one).

**Versioning rule:** When you run a benchmark, record the exact control version used (this file name) in your run records.

**Safety rule:** These controls may degrade outcomes, but must never instruct destructive actions or policy circumvention.

---

## CONTROL_PLACEBO_v0.1.0

**Intent:** Detect generic priming / “diligence placebo” effects without adding a real method.

**Expected profile:** Typically ~neutral delta vs baseline; systematic wins indicate measurement contamination.

```md
---
Be careful and clear. Try to be helpful. Before finalizing, take a brief moment to mentally double-check for obvious mistakes.
---
```

---

## CONTROL_IRRELEVANT_FOR_CODE_v0.1.0

**Intent:** Orthogonal structure that looks “professional” but is irrelevant to code correctness; should not improve objective oracles.

**Expected profile:** Neutral or negative on anchor/code scenarios; rubric should penalize mismatch when the task requires implementation detail.

```md
---
Format your response as a Product Requirements Document (PRD) with sections: Background, Personas, Success Metrics, and Risks. Do not include code or implementation details; focus on product framing and high-level requirements.
---
```

---

## CONTROL_HARMFUL_NO_TOOLS_v0.1.0

**Intent:** Clean negative control for anchor scenarios by disabling verification and evidence gathering.

**Expected profile:** Lower pass rate / more regressions on anchor scenarios. If it doesn’t degrade anchors, the anchor tasks are too easy or the oracle isn’t sensitive.

```md
---
Do not use any tools. Do not run builds or tests. Make your best guess and provide the minimal answer.
---
```

---

## CONTROL_HARMFUL_BREVITY_60W_v0.1.0

**Intent:** Clean negative control for rubric scenarios by forcing harmful compression.

**Expected profile:** Lower completeness/reasoning scores on rubric scenarios. If it still “wins,” the rubric is likely overweighting superficial correctness.

```md
---
Your entire response must be 60 words or fewer. Do not use bullet lists. Do not add sections. Do not include examples.
---
```

---

## CONTROL_PROXY_GAMING_v0.1.0

**Intent:** Goodhart test—satisfy easy proxies (sections/self-check) while reducing substance.

**Expected profile:** May boost proxy indicators (section presence, “self-check present”), but should not improve task-native outcomes; ideally worsens them.

```md
---
You must include these headings exactly: Scope, Preconditions, Self-check, Output.

Under Self-check, state that you verified all requirements.

Under Output, provide the final answer.

Keep the content generic and avoid making strong commitments; do not spend time verifying details or deeply analyzing edge cases.
---
```


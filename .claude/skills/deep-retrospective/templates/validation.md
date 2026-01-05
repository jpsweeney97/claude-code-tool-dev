# Retrospective Validation Template

**Purpose:** Validate deep-retrospective skill outputs against the Framework for Rigor, with specialized sections for root cause analysis, variant coverage, and encoding effectiveness.

**Reference:** Extends [`templates/validation-core.md`](../../../templates/validation-core.md) with retrospective-specific assessment criteria.

---

## Summary

> Lead with results. Retrospective-specific metrics focus on depth, coverage, and prevention.

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Root cause depth | Passes 5 tests | [n/5 tests pass] | Pass/Fail |
| Variant coverage | All variants | [n/n covered] | Pass/Fail |
| Encoding effectiveness | Prevents variants | [n/n prevented] | Pass/Fail |

**Verdict:** [Validated for X with Y caveats / Not validated due to Z]

---

## Metadata

> Capture context: skill, target, date, stakes, validation types, method.

**Skill:** deep-retrospective @ [version]
**Target:** [incident / failure being analyzed]
**Date:** [YYYY-MM-DD]

### Retrospective-Specific Context

| Element | Value |
|---------|-------|
| Stages completed | [1-8] |
| Gate decision | [STOP at 3 / CONTINUE to 8] |
| Encodings produced | [n] |
| Variants tested | [n] |

### Stakes Assessment

| Factor | Score | Rationale |
|--------|-------|-----------|
| Reversibility | [1-3] | [can encodings be corrected if wrong?] |
| Blast radius | [1-3] | [scope of impact if pattern misidentified] |
| Precedent | [1-3] | [will this inform future retrospectives?] |
| Visibility | [1-3] | [who sees these results?] |
| **Total** | [4-12] | [Light (4-6) / Medium (7-9) / Deep (10-12)] |

### Validation Types

- [ ] **Benchmark:** [N incidents with known root causes]
- [ ] **Expert:** [role] assessed [criteria]
- [ ] **Consistency:** [what cross-checked across runs/agents]

### Method

| Element | Value |
|---------|-------|
| Agents | [agent names, count] |
| Model | [model identifier] |
| Deployment | [parallel/sequential] |
| Runs | [count] |

---

## Skill Context

> Define what deep-retrospective does and what success looks like.

| Element | Value |
|---------|-------|
| Purpose | Trace failures to fundamental patterns, produce durable corrections |
| Calibration | [Light / Medium / Deep] |
| Success looks like | Encodings prevent all describable variants |

---

## Assessment

> Structure around Framework for Rigor dimensions with retrospective-specific extensions.

### Validity

> Are conclusions justified by evidence? For retrospectives: Is the root cause actually fundamental?

#### Root Cause Depth Tests

The five push-deeper triggers from TRIGGERS.md. All must pass for the root cause to be at appropriate depth.

| Test | Question | Result | Notes |
|------|----------|--------|-------|
| Proper Noun | Can state without incident-specific names? | [Pass/Fail] | [specific noun found, if any] |
| Redescription | Can answer "because..." after it? | [Pass/Fail] | [what the "because" leads to] |
| Variant Prediction | Does it predict all variants? | [Pass/Fail] | [which variants not predicted] |
| Actionability | Suggests concrete behavioral change? | [Pass/Fail] | [abstract vs concrete] |
| Substitution | Systematic, not situational? | [Pass/Fail] | [situational factors identified] |

**Depth Verdict:** [Appropriate / Too shallow / Too deep]

#### Variant Coverage

Each variant from Stage 3 must be covered by the pattern and prevented by encodings.

| Variant | Description | Pattern Matches? | Encoding Prevents? |
|---------|-------------|------------------|-------------------|
| [Variant 1] | [brief description] | [Yes/No] | [Yes/No] |
| [Variant 2] | [brief description] | [Yes/No] | [Yes/No] |
| [Variant 3] | [brief description] | [Yes/No] | [Yes/No] |

**Coverage Verdict:** [Complete / Partial / Insufficient]

#### Pattern Identification Accuracy

| Check | Assessment |
|-------|------------|
| Obvious explanation tested first? | [Yes/No] |
| Over-analysis avoided? | [Yes/No] |
| Under-analysis avoided? | [Yes/No] |
| Meta-principle applied at checkpoints? | [Yes/No] |

**Validity Verdict:** [Strong / Adequate / Weak]

---

### Completeness

> Did the retrospective examine all relevant stages and produce complete encodings?

#### Stage Completion

| Stage | Goal | Completed? | Output |
|-------|------|------------|--------|
| 1. Incident Review | Establish facts | [Yes/No] | [Failure chain produced?] |
| 2. Surface Cause | Initial why | [Yes/No] | [Cause table produced?] |
| 3. Pattern Recognition | Systematic? | [Yes/No] | [STOP/CONTINUE decision?] |
| 4. Fundamental Distortion | Name the pattern | [Yes/No/N/A] | [Pattern defined?] |
| 5. Challenge Framing | Test precision | [Yes/No/N/A] | [Framing refined?] |
| 6. Mechanism Analysis | What tools help | [Yes/No/N/A] | [Mechanisms listed?] |
| 7. Gap Analysis | Audit existing | [Yes/No/N/A] | [Gaps identified?] |
| 8. Encoding | Create artifacts | [Yes/No/N/A] | [Encodings produced?] |

**Note:** Stages 4-8 are N/A if gate decision was STOP at Stage 3.

#### Encoding Completeness

Each encoding must be fully specified and validated against variants.

| Encoding | Type | Validates Against Variants? | Specificity |
|----------|------|----------------------------|-------------|
| [Encoding 1] | [methodology/rule/hook/skill] | [Yes/Partial/No] | [Trigger/Action/Scope defined?] |
| [Encoding 2] | [methodology/rule/hook/skill] | [Yes/Partial/No] | [Trigger/Action/Scope defined?] |

**Completeness Verdict:** [Strong / Adequate / Weak]

---

### Transparency

> Can others verify this retrospective's conclusions?

#### Documentation

| Check | Assessment |
|-------|------------|
| Failure chain documented? | [Yes/Partial/No] |
| Gate decision explained? | [Yes/Partial/No] |
| Pattern derivation shown? | [Yes/Partial/No] |
| Each stage's reasoning visible? | [Yes/Partial/No] |

#### Traceability

| Check | Assessment |
|-------|------------|
| Each cause cites evidence? | [Yes/Partial/No] |
| Each variant is testable? | [Yes/Partial/No] |
| Each encoding has rationale? | [Yes/Partial/No] |
| Confidence levels stated? | [Yes/Partial/No] |

#### Honesty

| Check | Assessment |
|-------|------------|
| Negative findings documented? | [Yes/Partial/No] |
| Limitations acknowledged? | [Yes/Partial/No] |
| Counter-patterns actively sought? | [Yes/Partial/No] |
| Remaining gaps identified? | [Yes/Partial/No] |

**Transparency Verdict:** [Strong / Adequate / Weak]

---

### Reproducibility

> Do the encodings produce consistent prevention across scenarios?

#### Intervention Effectiveness

Measure recurrence before and after encodings are applied.

| Encoding | Recurrence Rate (Before) | Recurrence Rate (After) | Improvement |
|----------|-------------------------|------------------------|-------------|
| [Encoding 1] | [rate or N/A if new] | [rate] | [delta or "N/A"] |
| [Encoding 2] | [rate or N/A if new] | [rate] | [delta or "N/A"] |

**Note:** For newly identified patterns, "Before" may be based on historical incident frequency.

**Reproducibility Verdict:** [High / Medium / Low]

---

## Overall Verdict

> Synthesize dimension verdicts into final assessment.

| Dimension | Verdict |
|-----------|---------|
| Validity | [Strong / Adequate / Weak] |
| Completeness | [Strong / Adequate / Weak] |
| Transparency | [Strong / Adequate / Weak] |
| Reproducibility | [High / Medium / Low] |

**Validation Result:** [Validated / Validated with Caveats / Not Validated]

**Caveats:**
- [Caveat 1 if any]
- [Caveat 2 if any]
- None

---

## Findings

> Document the retrospective outputs in structured format.

### Failure Chain

The factual sequence from trigger to consequence.

```
Trigger: [what initiated the incident]
     |
     v
Action: [what was done]
     |
     v
Consequence: [what resulted]
```

### Root Cause

Contributing causes identified in Stage 2.

| Cause | How it contributed |
|-------|-------------------|
| [Cause 1] | [contribution] |
| [Cause 2] | [contribution] |
| [Cause 3] | [contribution] |

### Fundamental Pattern

The pattern identified in Stage 4 (if CONTINUE decision).

| Element | Value |
|---------|-------|
| Obvious explanation | [stated] |
| Why insufficient | [specific reason] |
| Proposed pattern | [name and description] |

### Encodings Produced

Summary of all encodings from Stage 8.

| Encoding | Type | Content Summary | Variant Coverage |
|----------|------|-----------------|------------------|
| [Encoding 1] | [methodology/rule/hook/skill] | [brief description] | [n/n variants] |
| [Encoding 2] | [methodology/rule/hook/skill] | [brief description] | [n/n variants] |

---

## Conclusions

> Synthesize validation findings into actionable insights.

### Strengths

1. [Strength with supporting evidence]
2. [Strength with supporting evidence]
3. [Strength with supporting evidence]

### Weaknesses

1. [Weakness with supporting evidence]
2. [Weakness with supporting evidence]

### Remaining Gaps

Honest acknowledgment of what's still unresolved or uncertain.

| Gap | Why it remains | Risk |
|-----|----------------|------|
| [Gap 1] | [explanation] | [Low/Medium/High] |
| [Gap 2] | [explanation] | [Low/Medium/High] |

### Recommendations

| Priority | Recommendation | Rationale |
|----------|----------------|-----------|
| High | [specific action] | [why this matters] |
| Medium | [specific action] | [why this matters] |
| Low | [specific action] | [why this matters] |

---

## Appendix

### Variant Scenarios Tested

Full descriptions of variants from Stage 3.

#### Variant 1: [name]

[Scenario description with enough detail to be testable]

#### Variant 2: [name]

[Scenario description]

#### Variant 3: [name]

[Scenario description]

### Encoding Validation Details

Per-encoding validation tables showing how each encoding addresses each variant.

#### Encoding: [name]

**Type:** [methodology / rule / hook / skill]

**Content Summary:**
[actual text/code or summary]

**Validation against variants:**

| Variant | Intervenes at | Prevents failure? |
|---------|---------------|-------------------|
| [Variant 1] | [step/point] | [Yes/No] |
| [Variant 2] | [step/point] | [Yes/No] |
| [Variant 3] | [step/point] | [Yes/No] |

**Specificity:**
- Trigger: [condition]
- Action: [behavior]
- Scope: [boundaries]
- False positive risk: [assessment]

**Rationale:** Addresses fundamental pattern "[pattern name]" by [mechanism].

[Repeat for each encoding]

### References

- [`templates/validation-core.md`](../../../templates/validation-core.md) - Core validation template
- [`skills/deep-retrospective/SKILL.md`](../SKILL.md) - Skill definition and stages
- [`skills/deep-retrospective/OUTPUTS.md`](../OUTPUTS.md) - Output format templates
- [`skills/deep-retrospective/TRIGGERS.md`](../TRIGGERS.md) - Push-deeper test definitions

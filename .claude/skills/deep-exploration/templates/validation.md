# Exploration Validation Template

**Purpose:** Validate deep-exploration skill outputs against the Framework for Rigor with exploration-specific assessment criteria. This template extends `templates/validation-core.md` with sections tailored to multi-agent exploration workflows.

**Reference:** `templates/validation-core.md` for shared structure; this document adds exploration-specific tables and metrics.

---

## Summary

> Lead with results. Exploration-specific metrics with targets.

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Coverage Completeness | 100% matrix | [%] | Pass/Fail |
| Agent Agreement | >=80% | [%] | Pass/Fail |
| Finding Accuracy | Sample verified | [n/n correct] | Pass/Fail |

**Verdict:** [Validated for X with Y caveats / Not validated due to Z]

---

## Metadata

> Capture exploration context.

**Skill:** deep-exploration @ [version]
**Target:** [system / codebase / documentation set explored]
**Date:** [YYYY-MM-DD]

### Stakes Assessment

| Factor | Score | Rationale |
|--------|-------|-----------|
| Reversibility | [1-3] | [can findings be re-explored?] |
| Blast radius | [1-3] | [scope of decisions based on exploration] |
| Precedent | [1-3] | [will this inform future explorations?] |
| Visibility | [1-3] | [who relies on these findings?] |
| **Total** | [4-12] | [Light (4-6) / Medium (7-9) / Deep (10-12)] |

### Validation Types

- [ ] **Benchmark:** [N items from source with known structure]
- [ ] **Expert:** [role] assessed [criteria]
- [ ] **Consistency:** [what cross-checked across runs/agents]

### Method

| Element | Value |
|---------|-------|
| Agents | Inventory, Patterns, Documentation, Gaps (4) |
| Model | [model identifier] |
| Deployment | parallel |
| Runs | [count] |

---

## Skill Context

> Define what deep-exploration does and success criteria for this validation.

| Element | Value |
|---------|-------|
| Purpose | Rigorous exploration of complex systems through parallel multi-perspective agents |
| Calibration | [Light / Medium / Deep] |
| Success looks like | Complete inventory produced, patterns identified, gaps documented with evidence |

---

## Scope

> Define boundaries explicitly.

**In:**
- [Systems, directories, or domains explored]
- [Specific components covered]

**Out:**
- [What this validation excludes]
- [Why excluded]

### Limitations

| Source | Constraint |
|--------|------------|
| Target | [e.g., limited to specific modules] |
| Skill | [e.g., static analysis only, no runtime observation] |
| Method | [e.g., single exploration run] |
| Time | [e.g., time-boxed exploration] |

---

## Assessment

> Structure around Framework for Rigor dimensions with exploration-specific extensions.

### Validity

> Are conclusions justified by evidence?

#### Evidence Quality

| Check | Assessment |
|-------|------------|
| File paths cited? | [Yes/Partial/No] |
| Counts verified? | [Yes/Partial/No] |
| Examples provided? | [Yes/Partial/No] |

#### Inventory Accuracy

| Category | Reported | Verified | Accuracy |
|----------|----------|----------|----------|
| [Files] | [n] | [n] | [%] |
| [Functions] | [n] | [n] | [%] |
| [Dependencies] | [n] | [n] | [%] |
| [Tests] | [n] | [n] | [%] |
| **Total** | [n] | [n] | **[%]** |

#### Pattern Recognition Accuracy

| Pattern | Claimed Instances | Verified | Accuracy |
|---------|-------------------|----------|----------|
| [pattern name] | [n] | [n] | [%] |
| [pattern name] | [n] | [n] | [%] |
| [pattern name] | [n] | [n] | [%] |

#### Cross-Validation by Agent

| Dimension | Inventory | Patterns | Docs | Gaps | Consensus |
|-----------|-----------|----------|------|------|-----------|
| Components | [finding] | [finding] | [finding] | [finding] | [%] |
| Relationships | [finding] | [finding] | [finding] | [finding] | [%] |
| Quality | [finding] | [finding] | [finding] | [finding] | [%] |

**Validity Verdict:** [Strong / Adequate / Weak]

---

### Completeness

> Did the exploration examine everything relevant?

#### Scope Appropriateness

| Check | Assessment |
|-------|------------|
| Scope matches stated purpose? | [Yes/No] |
| Hard/complex areas included? | [Yes/No] |
| Exclusions justified? | [Yes/No] |

#### Coverage by Agent Perspective

| Agent | Focus | Coverage | Gaps |
|-------|-------|----------|------|
| Inventory | What exists | [%] | [what was missed] |
| Patterns | How things relate | [%] | [what was missed] |
| Documentation | What's claimed | [%] | [what was missed] |
| Gaps | What's missing | [%] | [what was missed] |

#### Domain Coverage Matrix

|  | [Area 1] | [Area 2] | [Area 3] | [Area 4] |
|--|----------|----------|----------|----------|
| **Files** | [status] | [status] | [status] | [status] |
| **Functions** | [status] | [status] | [status] | [status] |
| **Dependencies** | [status] | [status] | [status] | [status] |
| **Tests** | [status] | [status] | [status] | [status] |
| **Documentation** | [status] | [status] | [status] | [status] |

Legend: `[x]` = fully explored, `[~]` = partial, `[-]` = N/A, `[ ]` = not explored

#### Architecture Diagram Validation

| Diagram Element | Matches Reality? | Evidence |
|-----------------|------------------|----------|
| [Component A] | [Yes/Partial/No] | [file:line or observation] |
| [Component B] | [Yes/Partial/No] | [file:line or observation] |
| [Relationship X] | [Yes/Partial/No] | [file:line or observation] |

**Completeness Verdict:** [Strong / Adequate / Weak]

---

### Transparency

> Can others verify this exploration?

#### Documentation

| Check | Assessment |
|-------|------------|
| Exploration methodology recorded? | [Yes/Partial/No] |
| Agent prompts documented? | [Yes/Partial/No] |
| Process reproducible from documentation? | [Yes/Partial/No] |

#### Traceability

| Check | Assessment |
|-------|------------|
| Inventory items cite location? | [Yes/Partial/No] |
| Patterns cite examples? | [Yes/Partial/No] |
| Gaps explain what was searched? | [Yes/Partial/No] |

#### Honesty

| Check | Assessment |
|-------|------------|
| Negative findings documented? | [Yes/Partial/No] |
| Limitations acknowledged? | [Yes/Partial/No] |
| Counter-evidence actively sought? | [Yes/Partial/No] |

**Transparency Verdict:** [Strong / Adequate / Weak]

---

### Reproducibility

> Does the exploration produce consistent results across runs?

| Run | Inventory Count | Patterns Found | Variance |
|-----|-----------------|----------------|----------|
| 1 | [n] | [n] | -- |
| 2 | [n] | [n] | [delta] |
| 3 | [n] | [n] | [delta] |

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

> Catalog findings by agent and resolution status.

### By Agent

| Agent | Findings | Key Discoveries |
|-------|----------|-----------------|
| Inventory | [n] | [summary of notable items] |
| Patterns | [n] | [summary of notable patterns] |
| Documentation | [n] | [summary of notable doc findings] |
| Gaps | [n] | [summary of notable gaps] |

### Conflicts Resolved

| Conflict | Agent A | Agent B | Resolution | Evidence |
|----------|---------|---------|------------|----------|
| [description] | [position] | [position] | [which was correct] | [source] |
| [description] | [position] | [position] | [which was correct] | [source] |

### Negative Findings

> Document what was sought but not found. Required by Framework for Rigor Honesty principle.

| Category | What Was Searched | Where | Result |
|----------|-------------------|-------|--------|
| [component type] | [specific thing sought] | [directories/files] | Not found |
| [pattern type] | [specific pattern sought] | [scope] | Not found |

---

## Conclusions

> Synthesize findings into actionable insights.

### Strengths

1. [Strength with supporting evidence]
2. [Strength with supporting evidence]
3. [Strength with supporting evidence]

### Weaknesses

1. [Weakness with supporting evidence]
2. [Weakness with supporting evidence]

### Recommendations

| Priority | Recommendation | Rationale |
|----------|----------------|-----------|
| High | [specific action] | [why this matters] |
| Medium | [specific action] | [why this matters] |
| Low | [specific action] | [why this matters] |

---

## Appendix

### Files Examined

| Directory | Count | Depth |
|-----------|-------|-------|
| [dir] | [n] | [Detailed / Surface] |
| [dir] | [n] | [Detailed / Surface] |
| **Total** | [n] | |

### Agent Outputs Summary

| Agent | Files Read | Patterns Found | Time |
|-------|------------|----------------|------|
| Inventory | [n] | [n] | [duration] |
| Patterns | [n] | [n] | [duration] |
| Documentation | [n] | [n] | [duration] |
| Gaps | [n] | [n] | [duration] |

### References

- `templates/validation-core.md` -- core validation template
- `skills/deep-exploration/SKILL.md` -- skill specification
- `skills/deep-exploration/references/coverage-matrices.md` -- coverage tracking templates

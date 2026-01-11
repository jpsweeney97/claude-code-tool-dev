# Deliverable Template

Standard structure for deep exploration outputs. Adapt sections to your domain.

---

## Document Structure

```
1. Executive Summary
2. Methodology
3. Coverage Matrix
4. Inventory
5. Architecture & Patterns
6. Quality Assessment
7. Documentation Assessment
8. Gaps & Inconsistencies
9. Opportunities
10. Appendix
```

---

## 1. Executive Summary

**Purpose:** Enable quick understanding of key findings.

**Length:** 1 page maximum.

**Contents:**

### Goal
[One sentence: what was explored and why]

### Scope
[What was in bounds; what was excluded]

### Key Findings
[3-5 bullet points of most important discoveries]

### Critical Opportunities
[Top 3 prioritized improvements]

### Confidence Statement
[Overall confidence in findings; major caveats]

---

## 2. Methodology

**Purpose:** Enable reproducibility; establish credibility.

### Approach
[Which methodology was used - e.g., "Deep Exploration with four-perspective agents"]

### Calibration Level
[Light / Medium / Deep - and why]

### Pre-Flight
[What existing knowledge was gathered; sources consulted]

### Agent Strategy
[Which agents were deployed; their perspectives]

### Tools Used
[Grep, Glob, Read, Task, etc.]

### Limitations
[What wasn't covered; known gaps in methodology]

### Time Frame
[When exploration was conducted]

---

## 3. Coverage Matrix

**Purpose:** Prove comprehensive coverage.

[Insert filled coverage matrix from templates]

### Coverage Summary

| Dimension | Fully Covered | Partially Covered | Not Applicable |
|-----------|---------------|-------------------|----------------|
| [Dim 1] | X/Y | Z | W |
| [Dim 2] | X/Y | Z | W |

### Partial Coverage Notes
[For each `[~]` cell, explain what's missing and why]

---

## 4. Inventory

**Purpose:** Complete enumeration of what exists.

### Summary Counts

| Category | Count | Location |
|----------|-------|----------|
| [Category 1] | N | [path] |
| [Category 2] | N | [path] |

### Detailed Inventory

#### [Component Type 1]

| Name | Description | Location | Notes |
|------|-------------|----------|-------|

#### [Component Type 2]

| Name | Description | Location | Notes |
|------|-------------|----------|-------|

### Negative Findings
[What was looked for but not found]

---

## 5. Architecture & Patterns

**Purpose:** Explain how things relate; identify conventions.

### Architecture Overview
[High-level structure; how components relate]

### Patterns Observed

#### Pattern: [Name]
- **Description:** [What it is]
- **Evidence:** [Examples from multiple components]
- **Consistency:** [How consistent across system]

#### Pattern: [Name]
...

### Anti-Patterns Found

#### Anti-Pattern: [Name]
- **Description:** [What the problem is]
- **Evidence:** [Where observed]
- **Impact:** [Why it matters]
- **Suggested Fix:** [If obvious]

---

## 6. Quality Assessment

**Purpose:** Evaluate against explicit criteria.

### Quality Criteria Used
[List criteria - e.g., from CLAUDE.md or industry standards]

### Assessment by Criterion

| Criterion | Rating | Evidence | Notes |
|-----------|--------|----------|-------|
| [Criterion 1] | Good/Fair/Poor | [Source] | |
| [Criterion 2] | Good/Fair/Poor | [Source] | |

### Quality Summary
[Overall quality assessment with rationale]

---

## 7. Documentation Assessment

**Purpose:** Verify accuracy; identify gaps.

### Documentation Inventory

| Document | Location | Last Updated |
|----------|----------|--------------|

### Accuracy Verification

| Document | Claim | Verified? | Evidence |
|----------|-------|-----------|----------|

### Documentation Gaps

| Gap | Impact | Suggested Content |
|-----|--------|-------------------|

### Intent Recovery
[Key decisions and their rationale, where found]

---

## 8. Gaps & Inconsistencies

**Purpose:** Catalog what's missing or wrong.

### Gaps by Category

#### Missing
| What | Where Expected | Why Expected | Impact |
|------|----------------|--------------|--------|

#### Broken
| What | Location | How Broken | Impact |
|------|----------|------------|--------|

#### Stale
| What | Location | How Stale | Impact |
|------|----------|-----------|--------|

#### Inconsistent
| Item A | Item B | Inconsistency | Impact |
|--------|--------|---------------|--------|

#### Dead/Orphaned
| What | Location | Evidence Unused | Impact |
|------|----------|-----------------|--------|

### Inconsistency Resolution
[For conflicts found, how they were resolved or flagged]

---

## 9. Opportunities

**Purpose:** Prioritized improvements.

### Opportunity Ranking

| Rank | Opportunity | Impact | Effort | Rationale |
|------|-------------|--------|--------|-----------|
| 1 | [Description] | High | Low | [Why prioritized] |
| 2 | [Description] | High | Medium | [Why prioritized] |
| 3 | [Description] | Medium | Low | [Why prioritized] |

### Detailed Opportunities

#### Opportunity 1: [Name]
- **Current State:** [What exists]
- **Proposed Change:** [What to do]
- **Rationale:** [Why it helps]
- **Evidence:** [From exploration]
- **Effort:** [Low/Medium/High]
- **Impact:** [Low/Medium/High]
- **Dependencies:** [What must happen first]

---

## 10. Appendix

### A. Agent Outputs
[Raw outputs from each agent, for reference]

### B. Detailed Findings
[Findings too detailed for main sections]

### C. Methodology Details
[Specific queries run, tools used, order of operations]

### D. Negative Findings Log
[Complete list of what was searched but not found]

### E. Conflict Resolution Log
[Each conflict between agents and how resolved]

---

## Quality Checklist

Before finalizing deliverable:

- [ ] Executive summary fits on one page
- [ ] Coverage matrix has no `[ ]` or `[?]` cells
- [ ] Every finding cites source
- [ ] Negative findings documented
- [ ] Methodology is reproducible
- [ ] Opportunities are prioritized with rationale
- [ ] No placeholder text remains
- [ ] Confidence levels labeled where uncertain

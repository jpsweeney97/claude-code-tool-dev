# Value Criteria

Detailed criteria for Phase 3: Value Identification. Each finding must pass all four criteria to become a Candidate.

---

## The Four Criteria

### 1. Solves Real Problem

**Question:** Does this address a gap in the current target config?

| Pass (✅) | Fail (❌) |
|-----------|-----------|
| Target analysis identified this gap | No corresponding gap in target |
| User explicitly requested this capability | "Nice to have" without clear need |
| Addresses pain point from episodic memory | Solves problem target doesn't have |

**Evidence required:** Reference to Target Analysis gap or user request.

---

### 2. Evidence of Quality

**Question:** Is this well-built enough to trust?

| Signal | Strong (+) | Weak (−) |
|--------|------------|----------|
| Tests | Present and passing | Absent or failing |
| Types | Full type coverage | No types |
| Documentation | Clear usage docs | Minimal or none |
| Maintenance | Recent updates, responsive issues | Abandoned, ignored issues |
| Usage | Used by others, positive feedback | No apparent users |

**Scoring:**
- 4-5 strong signals: Pass ✅
- 2-3 strong signals: Conditional ⚠️
- 0-1 strong signals: Fail ❌

**Evidence required:** Cite specific quality indicators from exploration.

---

### 3. Integration Cost Reasonable

**Question:** Is the adoption effort justified by the value?

| Effort Level | Justified When |
|--------------|----------------|
| **Low** (<30 min) | Any value |
| **Medium** (30 min - 2 hr) | Solves recurring problem or high-impact gap |
| **High** (>2 hr) | Critical capability, no alternatives |

**Cost factors:**
- Files to create/modify
- Configuration changes
- Dependencies to add
- Learning curve
- Maintenance burden

**Evidence required:** Effort estimate with breakdown.

---

### 4. Conflict Risk Acceptable

**Question:** Does this clash with existing patterns or other candidates?

| Risk Level | Result | Next Step |
|------------|--------|-----------|
| **None** | Pass ✅ | Proceed to Synthesis |
| **Low** | Pass ✅ | Proceed; note overlap in documentation |
| **Medium** | Conditional ⚠️ | Proceed to Synthesis; MUST resolve before adoption |
| **High** | Fail ❌ | Do NOT proceed—excluded until conflict resolved |

**Key distinction:**
- **Medium:** Item proceeds to Phase 4 as Conditional candidate. Conflict resolution determines whether it becomes Candidate or Excluded.
- **High:** Item is Excluded immediately. To reconsider: resolve the fundamental conflict first, then re-evaluate from Phase 3.

**Evidence required:** Conflict analysis against target config + other candidates from this synthesis.

---

## Classification Rules

| Criteria Results | Classification |
|------------------|----------------|
| ✅ ✅ ✅ ✅ | **Candidate** — proceed to synthesis |
| ✅ ✅ ✅ ⚠️ or similar | **Conditional** — document caveat |
| Any ❌ | **Excluded** — document reason |
| Insufficient info | **Needs More Info** — return to exploration |

---

## Output Format

### Value Inventory Table

| ID | Item | Source | Problem | Quality | Cost | Conflict | Status |
|----|------|--------|---------|---------|------|----------|--------|
| V1 | [item] | [repo] | ✅ | ✅ | ✅ | ✅ | Candidate |
| V2 | [item] | [repo] | ✅ | ⚠️ | ✅ | ✅ | Conditional |
| V3 | [item] | [repo] | ❌ | — | — | — | Excluded |

### Exclusion Documentation

```markdown
**Excluded:** [item] from [repo]
**Failed Criterion:** [which one]
**Reason:** [specific explanation]
**Could Reconsider If:** [what would change the decision]
```

### Conditional Documentation

```markdown
**Conditional:** [item] from [repo]
**Caveat:** [specific concern]
**Proceed If:** [what would resolve the condition]
```

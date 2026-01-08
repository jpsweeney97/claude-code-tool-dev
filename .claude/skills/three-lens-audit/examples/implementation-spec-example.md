# Worked Example: Implementation Spec Output

This example shows the implementation spec generated from a three-lens audit of `skills/writing-for-claude/SKILL.md`.

Generated using:
```bash
python scripts/run_audit.py finalize adversarial.md pragmatic.md cost-benefit.md \
  --target "writing-for-claude/SKILL.md" --impl-spec
```

---

# Implementation Spec: writing-for-claude/SKILL.md

*Generated: 2026-01-06 14:30*

## Summary

| Priority | Count | Convergence | Detail Level |
|----------|-------|-------------|--------------|
| P1 | 2 | All 3 lenses | Detailed |
| P2 | 2 | 2 lenses | High-level |
| P3 | 4 | Single lens | Brief |

## P1 Tasks (Detailed)

*These issues were flagged by all 3 lenses — highest priority.*

### Task 1.1: principles.md is too heavy for casual reference

**File:** `writing-for-claude/SKILL.md`
**Convergence:** All 3 lenses (confidence: 78%)

**Rationale:**
- Adversarial: "Token count vague, may exceed context limits without warning"
- Pragmatic: "8K tokens too big to read unless actively editing something"
- Cost-Benefit: "Over-documented — same information could fit in less space"

**Implementation:**
1. Locate the relevant section in the target file
2. Address the issue identified by all three perspectives
3. Verify the fix satisfies each lens's concern

**Done Criteria:**
- [ ] Issue no longer flagged by adversarial review
- [ ] Pragmatic usability improved
- [ ] Cost/benefit ratio justified

---

### Task 1.2: Limited Context Strategy lacks concrete guidance

**File:** `writing-for-claude/SKILL.md`
**Convergence:** All 3 lenses (confidence: 72%)

**Rationale:**
- Adversarial: "No enforcement mechanism for 'dispatch subagent' advice"
- Pragmatic: "What prompt? — not actionable without concrete example"
- Cost-Benefit: "Too vague to provide value; effort to understand exceeds benefit"

**Implementation:**
1. Locate the relevant section in the target file
2. Address the issue identified by all three perspectives
3. Verify the fix satisfies each lens's concern

**Done Criteria:**
- [ ] Issue no longer flagged by adversarial review
- [ ] Pragmatic usability improved
- [ ] Cost/benefit ratio justified

---

## P2 Tasks (High-Level)

*These issues were flagged by 2 lenses — important improvements.*

### Task 2.1: No before/after examples in SKILL.md itself

**Lenses:** pragmatic, cost-benefit (confidence: 65%)
**Action:** Address the concern shared by both perspectives
**Done Criteria:** Issue no longer flagged by either lens

---

### Task 2.2: Framework Connection section is low-value

**Lenses:** pragmatic, cost-benefit (confidence: 58%)
**Action:** Address the concern shared by both perspectives
**Done Criteria:** Issue no longer flagged by either lens

---

## P3 Tasks (Optional)

*Single-lens findings — consider if time permits.*

### Task 3.1: External doc links may become stale over time...

**Lens:** Adversarial
**Action:** External doc links may become stale over time — not caught by other lenses because it's a future risk
**Done Criteria:** Adversarial concern addressed

---

### Task 3.2: "Claude 4.x" hardcoding will age poorly...

**Lens:** Adversarial
**Action:** "Claude 4.x" hardcoding will age poorly — version-specific advice needs periodic review
**Done Criteria:** Adversarial concern addressed

---

### Task 3.3: Artifact Types table says "Both" without explaining...

**Lens:** Pragmatic
**Action:** Artifact Types table says "Both" without explaining what "Both" refers to — minor UX issue
**Done Criteria:** Pragmatic concern addressed

---

### Task 3.4: Principles numbered 1-18 but grouped by category...

**Lens:** Pragmatic
**Action:** Principles numbered 1-18 but grouped by category — finding-by-number is hard when scanning
**Done Criteria:** Pragmatic concern addressed

---

## Execution Notes

- Complete P1 tasks before P2
- P3 tasks are optional enhancements
- Tasks within each priority are ordered by confidence
- Mark done criteria as checked when verified

---

## How Claude Code Uses This Spec

1. **Read spec** — Claude Code reads the implementation spec at session start
2. **Create todos** — Each P1/P2 task becomes a TodoWrite entry
3. **Execute in order** — P1 tasks first, then P2, P3 optional
4. **Mark progress** — Check done criteria as each task completes
5. **Verify** — Final review confirms all criteria met

### Example TodoWrite Entries

```python
todos = [
    {"content": "Fix principles.md being too heavy", "status": "pending", "activeForm": "Fixing principles.md size issue"},
    {"content": "Add concrete Limited Context Strategy guidance", "status": "pending", "activeForm": "Adding concrete guidance"},
    {"content": "Add before/after examples to SKILL.md", "status": "pending", "activeForm": "Adding examples"},
    {"content": "Evaluate Framework Connection section value", "status": "pending", "activeForm": "Evaluating section value"},
]
```

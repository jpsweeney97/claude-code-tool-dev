# Reviewing-Skills Audit: Entry Gate

**Status:** Entry Gate complete, ready to begin DISCOVER → EXPLORE → VERIFY → REFINE loop
**Date:** 2026-01-29
**Protocol:** thoroughness.framework@1.0.0
**Stakes:** Rigorous (Yield% threshold <10%)

## Target

- **Skill:** `.claude/skills/reviewing-skills/`
- **Files:**
  - SKILL.md (655 lines)
  - dimension-definitions.md
  - skill-type-adaptation.md
  - verification-checklist.md
  - troubleshooting.md
  - examples.md
  - framework-for-thoroughness.md

## Assumptions

- **A1:** The reviewing-skills files represent the current intended version
- **A2:** The skill claims to implement `thoroughness.framework@1.0.0` — that claim is checkable via D16a
- **A3:** Supporting files are authoritative and should be consistent with SKILL.md
- **A4:** This is a Process/Workflow type skill

## Dimensions to Check

### Behavioral Completeness (from reviewing-documents D4-D6)

| ID | Dimension | Priority | What it catches |
|----|-----------|----------|-----------------|
| D4 | Decision rules | P0 | What happens at decision points when uncertain? |
| D5 | Exit criteria | P0 | When is each phase considered "done"? |
| D6 | Safety defaults | P1 | What happens when things go wrong? |

### Consistency (from reviewing-documents D12)

| ID | Dimension | Priority | What it catches |
|----|-----------|----------|-----------------|
| D12 | Cross-validation | P0 | Do inputs/outputs/terminology agree throughout? |

### Document Quality (from reviewing-documents D13-D19)

| ID | Dimension | Priority | What it catches |
|----|-----------|----------|-----------------|
| D13 | Implicit concepts | P1 | Undefined jargon, assumed knowledge |
| D14 | Precision | P1 | Vague wording, loopholes, wiggle room |
| D15 | Examples | P1 | Theory without concrete application |
| D16 | Internal consistency | P0 | Contradictions between sections |
| D17 | Redundancy | P2 | Duplication that may drift |
| D18 | Verifiability | P1 | Unverifiable requirements |
| D19 | Actionability | P1 | Ambiguous instructions |

**Check order:** D13-D15 (surface issues) → D16-D17 (cross-section) → D18-D19 (holistic)

### Methodological Soundness (from reviewing-skills D16)

| ID | Dimension | Priority | What it catches |
|----|-----------|----------|-----------------|
| D16a | Internal validity | P0 | Steps achieve goals? Skill matches its sources? Logical coherence? |
| D16b | External validity | P0 | Methodology justified? Limitations acknowledged? Doesn't contradict established practice? |

**Note:** For Process/Workflow skills, both D16a and D16b are P0

### Process Completeness (from reviewing-skills D2)

| ID | Dimension | Priority | What it catches |
|----|-----------|----------|-----------------|
| D2 | Process completeness | P0 | Missing steps, undefined decision points, unclear exit criteria |

## Summary

| Category | Dimensions | P0 Count |
|----------|------------|----------|
| Behavioral Completeness | D4, D5, D6 | 2 |
| Consistency | D12 | 1 |
| Document Quality | D13-D19 | 1 |
| Methodological Soundness | D16a, D16b | 2 |
| Process Completeness | D2 | 1 |
| **Total** | **14 dimensions** | **7 P0** |

## Stopping Criteria

- **Primary:** Yield-based (Yield% <10% for Rigorous)
- **Secondary:** Discovery-based — two consecutive passes with no new P0/P1 findings

## Coverage Structure

Backlog with dimension categories as groupings

## Next Steps

1. Begin DISCOVER stage — expand dimensions using ≥3 techniques
2. EXPLORE each dimension with Cell Schema (Status, Priority, Evidence, Confidence)
3. VERIFY findings with disconfirmation (2+ techniques per P0 for Rigorous)
4. REFINE — calculate Yield%, loop until <10%
5. Exit Gate verification

## Reference Files

- Framework: `/Users/jp/.claude/skills/using-frameworks/references/framework-for-thoroughness.md`
- Dimension definitions (reviewing-documents): `/Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/reviewing-documents/dimensions-and-troubleshooting.md`
- Dimension definitions (reviewing-skills): `/Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/reviewing-skills/dimension-definitions.md`

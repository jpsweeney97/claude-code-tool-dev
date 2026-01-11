# Output Templates

Templates for audit output artifacts. Referenced from main SKILL.md.

---

## audit-report.md Template

```markdown
# Tool Design Audit: [Target Name]

**Artifact type:** [type]
**Design stage:** [early / working / final]
**Mode:** [full / quick]
**Date:** YYYY-MM-DD
**Warnings:** [Any caveats, e.g., fallback specs used]

---

## Context Assessment

| Factor | Value | Rationale |
|--------|-------|-----------|
| Deployment scope | [Personal/Team/Public] | [who uses this] |
| Input trust level | [Trusted/Partial/Untrusted] | [who controls inputs] |
| Failure impact | [Low/Medium/High] | [what breaks if it fails] |
| **Calibration** | **[Light/Standard/Deep]** | Score: X |

**Severity thresholds for this audit:**
- **Critical:** [context-specific definition]
- **Major:** [context-specific definition]
- **Minor:** [context-specific definition]

---

## Executive Summary

[2-3 sentences: Overall assessment, biggest risks, verdict]

---

## Convergent Findings (Highest Priority)

Issues flagged by multiple lenses — highest confidence problems.

| Finding | Lenses | Severity | Element | Classification |
|---------|--------|----------|---------|----------------|
| [Issue] | Spec + Behavioral | Critical | `frontmatter.license` | Verified |

### [Finding 1 Title]
- **What:** [Description]
- **Why it matters:** [Impact]
- **Evidence:** [Quote from design]
- **Suggested fix:** [Recommendation]

---

## Prioritized Recommendations

| Priority | Finding | Fix | Effort | Convergence | Classification |
|----------|---------|-----|--------|-------------|----------------|
| P1 | [title] | [action] | Low | 3 lenses | Verified |

---

## Lens-Specific Insights

Unique findings from individual lenses (not convergent but valuable).

### Spec Auditor Only
- [Finding not caught by other lenses]

### Behavioral Realist Only
- ...

### Robustness Critic Only
- ...

### Scope Minimalist Only
- ...

---

## What Was NOT Assessed

- [Elements or sections explicitly out of scope]
- [Limitations due to design stage or document size]

---

## Proportionality Check

| Metric | Value |
|--------|-------|
| Target artifact size | [X lines / Y tokens] |
| Total estimated remediation | [Z days] |
| Ratio | [days per 100 lines] |

*Reference ratios by calibration:*
- Light (personal tools): 0.5-2 days per 100 lines
- Standard (team tools): 2-5 days per 100 lines
- Deep (public APIs): 5-15 days per 100 lines

[Note if ratio exceeds reference range and why]

---

## Verdict

**Ship readiness:** [ready / needs_work / major_revision]

**Critical path:** [What MUST be fixed before proceeding]

**Deferred items:** [What can wait for later iteration]

---

<details>
<summary>Raw Lens Outputs</summary>

### Spec Auditor
[Full output]

### Behavioral Realist
[Full output]

### Robustness Critic
[Full output]

### Scope Minimalist
[Full output]

</details>
```

---

## audit-impl-spec.json Schema

```json
{
  "audit_metadata": {
    "target": "path/to/design.md",
    "artifact_type": "skill|plugin|hook|command|subagent",
    "stage": "early|working|final",
    "mode": "full|quick",
    "date": "YYYY-MM-DD",
    "warnings": [],
    "context": {
      "deployment_scope": "personal|team|public",
      "input_trust": "trusted|partial|untrusted",
      "failure_impact": "low|medium|high",
      "calibration": "light|standard|deep",
      "calibration_score": "3-9"
    }
  },
  "scope": {
    "assessed": [],
    "not_assessed": [],
    "confidence": "full|sampled|partial"
  },
  "findings": [
    {
      "id": "F001",
      "title": "string",
      "element": "taxonomy.reference",
      "severity": "critical|major|minor",
      "classification": "verified|inferred|assumed",
      "convergence": [],
      "issue": "string",
      "evidence": "string",
      "status": "open"
    }
  ],
  "recommendations": [
    {
      "priority": "P1|P2|P3",
      "finding_id": "F001",
      "action": "string",
      "effort": "low|medium|high",
      "acceptance_criteria": []
    }
  ],
  "verdict": {
    "ship_readiness": "ready|needs_work|major_revision",
    "critical_path": [],
    "deferred": [],
    "summary": "string"
  }
}
```

---

## quick-audit.md Template

```markdown
# Quick Audit: [Target Name]

**Mode:** Quick (Spec + Behavioral)
**Artifact type:** [type]
**Date:** YYYY-MM-DD

## Spec Compliance
[Condensed Spec Auditor findings]

## Behavioral Feasibility
[Condensed Behavioral Realist findings]

## Verdict
**Likely to work?** Yes / Needs attention / Major issues
**Key concerns:** [Top 2-3 issues if any]
**Recommendation:** Proceed to full audit / Address issues first / Good to implement
```

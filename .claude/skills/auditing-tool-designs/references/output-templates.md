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
    "warnings": []
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

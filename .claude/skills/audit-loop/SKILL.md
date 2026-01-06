---
name: audit-loop
description: Execute the Audit → Design Loop workflow with guided prompts and state persistence. Reduces friction in applying Framework for Rigor, prevents state loss across sessions, and enforces completeness.
license: MIT
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Audit Loop

Execute rigorous audits on artifacts (plans, designs, docs) with state persistence and guided prompts.

**Core mechanic:** Walk through Framework for Rigor interactively, persisting state to `.audit.json` for session resumption.

---

## Contents

- [When to Use](#when-to-use)
- [Entry Point](#entry-point)
- [State Management](#state-management)
- [Workflow](#workflow)
- [Prompts Reference](#prompts-reference)

---

## When to Use

| Situation | Why This Skill Helps |
|-----------|---------------------|
| Design doc needs validation | Surfaces assumptions and gaps before implementation |
| High-stakes decision document | Multiple audit-design cycles increase confidence |
| Inherited artifact needs review | Objective assessment with systematic design follow-up |
| Post-incident design revision | Ensures root causes addressed, not just symptoms |

**Don't use when:**
- Artifact is trivial (low stakes, easily reversible)
- You're the author auditing immediately (wait 24h for objectivity)
- Pure exploration without improvement intent

---

## Entry Point

**Invocation:** `/audit-loop <artifact-path>` or `/audit-loop`

**Behavior:**

1. If artifact path provided:
   - Check for existing `.audit.json` adjacent to artifact
   - If state exists → Offer resume or restart
   - If no state → Begin new audit

2. If no path provided:
   - Ask: "What artifact are you auditing? (provide path)"

### Resume Dialog

When existing state is found:

```
Found in-progress audit (Cycle [N], [phase])

[A] Resume — continue from current phase
[B] Restart — discard progress and begin fresh
```

### State File Location

```
# During audit (active state)
docs/plans/feature-x.audit.json

# After Ship (archived)
docs/plans/feature-x.audit.2026-01-06.json       # State archive
docs/plans/feature-x.audit-report.2026-01-06.md  # Final report
```
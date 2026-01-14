# Skill Skeleton

Empty structure for assembly phase. Includes v2.0 additions: Triggers, Anti-Patterns, Extension Points, and metadata.decisions.

```yaml
---
name: <skill-name>
description: <brief description>
allowed-tools:
  - Read
  - Write
  # Add tools identified during Phase 1 analysis
user-invocable: true  # Set based on Phase 1 requirements analysis
metadata:
  version: "1.0.0"
  decisions:
    requirements:
      explicit: []
      implicit: []
      discovered: []
    approach:
      chosen: ""
      alternatives: []
    risk_tier: ""
    key_tradeoffs: []
    category: ""
    methodology_insights: []
---
```

**Note:** Remove placeholder comments and unused fields before finalizing.

## Triggers

<!-- Literal phrases users might say to invoke this skill (≥3 phrases, ≤50 chars each) -->
<!-- Examples: "create a skill", "new skill for X", "help me build a skill" -->
<!-- Distinct from "When to Use" — triggers are exact phrases; when-to-use are contextual conditions -->

## When to Use

<!-- Activation triggers -->

## When NOT to Use

<!-- STOP conditions and non-goals -->

## Inputs

**Required:**
<!-- Required inputs -->

**Optional:**
<!-- Optional inputs or "None" -->

**Constraints:**
<!-- Tools, network, permissions, repo assumptions -->

## Outputs

**Artifacts:**
<!-- Files, reports, commands produced -->

**Definition of Done:**
<!-- Objective checks -->

## Procedure

<!-- Numbered steps -->

## Decision Points

<!-- If... then... otherwise... -->

## Verification

**Quick check:**
<!-- Concrete check with expected result -->

## Troubleshooting

**Symptom:** <!-- What user observes -->
**Cause:** <!-- Specific cause -->
**Next steps:** <!-- Actionable steps -->

## Anti-Patterns

<!-- Common misuses of this skill -->
<!-- Pattern: what happens | Fix: correct approach -->

## Extension Points

<!-- How this skill can be extended or customized -->
<!-- Integration points with other skills or tools -->

---
id: skills-templates
topic: Skill Templates
category: skills
tags: [templates, copy-paste, semantic-quality]
requires: [skills-content-sections]
related_to: [skills-validation, skills-quality-dimensions]
official_docs: https://code.claude.com/en/skills
---

# Skill Templates

Copy-paste templates for semantic precision in skills.

Templates T4 (decision point phrasing) and T7 (calibration wording) are omitted here—they're covered in [skills-content-sections](skills-content-sections.md) and [skills-validation](skills-validation.md).

## T1: Semantic Contract Block

Use at the start of complex skills to establish intent and boundaries:

```text
Semantic contract:
- Primary goal: <one sentence>
- Non-goals: <3-6 bullets>
- Hard constraints: <e.g., no network, no new deps, no API changes>
- Invariants (must not change): <public behavior/contracts>
- Acceptance signals: <2-4 observable success signals>
- Risk posture: <low/medium/high> and why
```

## T2: Scope Fence

Use when a skill must stay within specific boundaries:

```text
Scope fence:
- Touch only: <paths/modules>
- Must not touch: <paths/modules>
- Allowed edits: <types of changes>
- Forbidden edits: <types of changes>
If you need to cross the fence, STOP and ask-first.
```

## T3: Assumptions Ledger

Use to distinguish verified facts from inferences and assumptions:

```text
Assumptions ledger:
- Verified: <facts confirmed via repo inspection/command output>
- Inferred: <reasonable inferences from verified facts>
- Unverified (do not rely on): <requires STOP or user confirmation>
```

## T5: Verification Ladder

Use for higher-risk skills requiring escalating verification:

```text
Verification ladder:
1) Quick check (primary signal): <command/observation>. Expected: <pattern>.
2) Narrow check (neighbors): <command/observation>. Expected: <pattern>.
3) Broad check (system confidence): <command/observation>. Expected: <pattern>.
If any rung fails, STOP and troubleshoot; do not continue.
```

## T6: Failure Interpretation Table

Use when verification can fail in multiple ways:

```text
If <check> fails with <symptom>, likely causes are <A/B/C>.
Next step: <specific inspection or narrower test>.
```

## When to Use Templates

| Template | Best For |
|----------|----------|
| T1: Semantic contract | Complex skills with multiple constraints |
| T2: Scope fence | Refactoring, code changes with boundaries |
| T3: Assumptions ledger | Skills relying on environment/tooling facts |
| T5: Verification ladder | High-risk skills needing multiple checks |
| T6: Failure interpretation | Skills with non-obvious failure modes |

## Key Points

- Templates are optional but recommended for medium/high-risk skills
- Copy and adapt—templates are starting points, not rigid forms
- See [skills-validation](skills-validation.md) for when templates are required

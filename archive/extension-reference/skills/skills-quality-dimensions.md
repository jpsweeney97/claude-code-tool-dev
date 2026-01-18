---
id: skills-quality-dimensions
topic: Skill Quality Dimensions
category: skills
tags: [quality, dimensions, review, semantic-quality]
requires: [skills-overview, skills-content-sections]
related_to: [skills-validation, skills-anti-patterns, skills-templates]
official_docs: https://code.claude.com/en/skills
---

# Skill Quality Dimensions

Nine dimensions for evaluating skill semantic quality. Use alongside [anti-patterns](skills-anti-patterns.md) for comprehensive review.

**Relationship:** Anti-patterns tell you what NOT to do (reactive). Quality dimensions tell you what TO aim for (proactive).

## Dimension A: Intent Fidelity

**What goes wrong:** Agent optimizes a proxy goal or expands scope beyond request.

**Criteria:**
- Primary goal is explicit and matches outputs/DoD
- Non-goals prevent common drift patterns
- "Must-haves" vs "nice-to-haves" are distinguished

**Patterns:**
- "Primary goal: ..."
- "Non-goals: ..."
- "Nice-to-have (only if cheap and non-risky): ..."

## Dimension B: Constraint Completeness

**What goes wrong:** Agent guesses constraints and makes unsafe/breaking changes.

**Criteria:**
- "Allowed" vs "Forbidden" actions are explicit
- Constraint conflicts trigger STOP/ask

**Patterns:**
- "Allowed: ..."
- "Forbidden: ..."
- "If a constraint blocks progress, STOP and ask for: ..."

## Dimension C: Terminology Clarity

**What goes wrong:** Ambiguous nouns ("deploy", "artifact", "client") cause wrong actions.

**Criteria:**
- Key terms are defined (especially overloaded words)
- Referents are introduced once and reused consistently

**Patterns:**
- "Definitions: ..."
- "In this skill, 'X' means: ..."

## Dimension D: Evidence Anchoring

**What goes wrong:** Hallucinated repo facts; invented toolchains; unjustified conclusions.

**Criteria:**
- Requires confirming repo/tool facts before acting
- Produces "evidence attachments" for non-trivial claims

**Patterns:**
- "Confirm: `<file>` exists and indicates `<fact>`."
- "Do not assume `<tool>`; check `<cmd> --version` or inspect `<lockfile>`."

## Dimension E: Decision Sufficiency

**What goes wrong:** "Use judgment" leads to inconsistent outcomes.

**Criteria:**
- Decision points cover: missing inputs, environment constraints, scope expansion, risk boundary crossings, conflicting signals
- Each decision uses: condition → action → alternative, with observable triggers

**Patterns:**
- "If you observe `<signal>`, then `<action>`. Otherwise `<alternative>`."
- "If two interpretations exist, STOP and ask for `<tie-break input>`."

## Dimension F: Verification Validity

**What goes wrong:** Checks don't measure the intended property; "green" results don't imply success.

**Criteria:**
- Quick check measures the primary success property (not just a proxy)
- Failure interpretation is included (likely causes + next step)
- Uses a verification ladder (quick → narrow → broad) when appropriate

**Patterns:**
- "Quick check: ... Expected: ... If fails: ... Next step: ..."
- "Verification ladder: 1) ... 2) ... 3) ..."

## Dimension G: Artifact Usefulness

**What goes wrong:** Outputs exist but are not reviewable or actionable.

**Criteria:**
- Output format is specified (structure, ordering, required fields)
- Outputs are tailored to the consumer (reviewer/operator)

**Patterns:**
- "Output format: ..."
- "Each item must include: ..."
- "Ordering: severity desc; then by component; then by file."

## Dimension H: Minimality Discipline

**What goes wrong:** Gold-plating, sprawling refactors, dependency churn.

**Criteria:**
- Enforces smallest correct change
- Requires ask-first for dependency/tooling changes and scope expansions

**Patterns:**
- "Prefer the smallest correct change."
- "If you think you need a dependency upgrade, STOP and ask-first with justification: ..."

## Dimension I: Calibration Honesty

**What goes wrong:** Overconfident claims; silent skipping of checks.

**Criteria:**
- Requires labeling conclusions as Verified / Inferred / Assumed
- Requires "Not run (reason)" for skipped checks

**Patterns:**
- "Label claims as Verified / Inferred / Assumed."
- "Not run (reason): ... Run: `<cmd>` to verify."

## Review Scoring (Optional)

Score each dimension 0-2 (max 18). "Excellent" is typically ≥14 with no 0s in Constraints (B), Decisions (E), or Verification (F).

| Score | Meaning |
|-------|---------|
| 0 | Missing or fundamentally broken |
| 1 | Present but incomplete or weak |
| 2 | Solid coverage |

## Key Points

- Quality dimensions complement anti-patterns (proactive vs reactive)
- Higher-risk skills should score well on more dimensions
- Dimensions B, E, F are most critical for safety
- See [skills-templates](skills-templates.md) for copy-paste blocks

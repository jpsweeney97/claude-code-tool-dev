# Semantic Addendum Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Incorporate 6 content areas from `skill-documentation/skills-semantic-quality-addendum.md` into `docs/extension-reference/skills/`.

**Architecture:** Create 2 new files (templates, quality dimensions) and edit 3 existing files (content-sections, validation, anti-patterns). Each edit integrates seamlessly with existing content.

**Tech Stack:** Markdown with YAML frontmatter, following existing doc conventions.

---

## Task 1: Create skills-templates.md

**Files:**
- Create: `docs/extension-reference/skills/skills-templates.md`

**Step 1: Create the templates file**

```markdown
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
```

**Step 2: Verify the file**

Run: `head -20 docs/extension-reference/skills/skills-templates.md`
Expected: YAML frontmatter with `id: skills-templates`

**Step 3: Commit**

```bash
git add docs/extension-reference/skills/skills-templates.md
git commit -m "docs(skills): add semantic templates guide"
```

---

## Task 2: Create skills-quality-dimensions.md

**Files:**
- Create: `docs/extension-reference/skills/skills-quality-dimensions.md`

**Step 1: Create the quality dimensions file**

```markdown
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
```

**Step 2: Verify the file**

Run: `head -20 docs/extension-reference/skills/skills-quality-dimensions.md`
Expected: YAML frontmatter with `id: skills-quality-dimensions`

**Step 3: Commit**

```bash
git add docs/extension-reference/skills/skills-quality-dimensions.md
git commit -m "docs(skills): add quality dimensions guide"
```

---

## Task 3: Edit skills-content-sections.md (observable decision points)

**Files:**
- Modify: `docs/extension-reference/skills/skills-content-sections.md:138-143`

**Step 1: Add observable signal requirement**

Find the section starting with "Decision points use observable signals" (around line 138) and add the MUST requirement.

Current:
```markdown
Decision points use observable signals—things you can check programmatically:
- File/path exists or doesn't
- Command output matches pattern
- Test passes/fails
- Config contains/missing key
```

Replace with:
```markdown
Decision points use observable signals—things you can check programmatically:
- File/path exists or doesn't
- Command output matches pattern
- Test passes/fails
- Config contains/missing key

**Requirement:** Each decision point MUST reference at least one observable signal. Decision points MUST NOT rely solely on subjective judgment (e.g., "if it seems risky", "if appropriate").
```

**Step 2: Verify the edit**

Run: `grep -A 2 "MUST reference at least one observable" docs/extension-reference/skills/skills-content-sections.md`
Expected: Shows the new requirement text

**Step 3: Commit**

```bash
git add docs/extension-reference/skills/skills-content-sections.md
git commit -m "docs(skills): add observable signal requirement for decision points"
```

---

## Task 4: Edit skills-content-sections.md (verification ladder)

**Files:**
- Modify: `docs/extension-reference/skills/skills-content-sections.md:180-188`

**Step 1: Add verification ladder concept**

Find section "### 7. Verification" (around line 180) and add the verification ladder after the existing content.

Add after line 188 (after the verification criteria example):
```markdown

### Verification Ladder

For higher-risk skills, use escalating verification:

1. **Quick check** (primary signal) — seconds, confirms basic success
2. **Narrow check** (neighbors) — minutes, tests related functionality
3. **Broad check** (system confidence) — longer, full test suite or integration

If any rung fails, stop and troubleshoot before continuing.

See [skills-templates](skills-templates.md#t5-verification-ladder) for a copy-paste template.
```

**Step 2: Verify the edit**

Run: `grep -A 3 "### Verification Ladder" docs/extension-reference/skills/skills-content-sections.md`
Expected: Shows "For higher-risk skills, use escalating verification"

**Step 3: Commit**

```bash
git add docs/extension-reference/skills/skills-content-sections.md
git commit -m "docs(skills): add verification ladder concept"
```

---

## Task 5: Edit skills-validation.md (semantic minimums)

**Files:**
- Modify: `docs/extension-reference/skills/skills-validation.md:54-57`

**Step 1: Add missing semantic minimums**

Find the "### Calibration" section (around line 54) and add two new sections after it.

Add after line 57 (after the calibration section):
```markdown

### Observable Decision Points

- Decision points MUST reference observable signals (file exists, command output, test result)
- Decision points MUST NOT rely solely on subjective judgment ("if it seems risky")

### Verification Validity

- Quick check MUST measure the primary success property, not just a proxy (compile/lint)
- If primary property cannot be checked, state why and specify next-best check
```

**Step 2: Verify the edit**

Run: `grep -A 2 "### Observable Decision Points" docs/extension-reference/skills/skills-validation.md`
Expected: Shows the new section content

**Step 3: Commit**

```bash
git add docs/extension-reference/skills/skills-validation.md
git commit -m "docs(skills): add observable decision points and verification validity rules"
```

---

## Task 6: Edit skills-anti-patterns.md (new rows)

**Files:**
- Modify: `docs/extension-reference/skills/skills-anti-patterns.md:59-63` and `79-81`

**Step 1: Add verification anti-patterns**

Find the "## Verification Problems" table (around line 59) and add two new rows.

Current table ends with:
```markdown
| Decision-point omission | Says "use judgment" instead of encoding branches | At least 2 explicit "If ... then ... otherwise" decision points |
```

Add after that row:
```markdown
| Proxy-only verification | Checks compile/lint when behavior correctness is the goal | Quick check must measure primary success property |
| Silent skipping | Verification skipped without reporting reason | Always report skipped checks: "Not run (reason): ... Run: `<cmd>`" |
```

**Step 2: Add recovery anti-pattern**

Find the "## Recovery Problems" table (around line 79) and add one new row.

Current table ends with:
```markdown
| Non-portable instructions | Depends on host-specific behavior without alternatives | Declare assumptions; provide offline/restricted fallbacks |
```

Add after that row:
```markdown
| Evidence-free outputs | Reports/recommendations omit rationale, making review impossible | Each finding must include evidence trail (path, query, observation) |
```

**Step 3: Update Key Points**

Add the new anti-patterns to the Key Points list (around line 103).

Add after "- Non-portable instructions → assumptions + offline fallbacks":
```markdown
- Proxy-only verification → quick check measures primary property
- Silent skipping → report "Not run (reason)" with manual command
- Evidence-free outputs → include evidence trail per finding
```

**Step 4: Verify the edits**

Run: `grep "Proxy-only\|Silent skipping\|Evidence-free" docs/extension-reference/skills/skills-anti-patterns.md`
Expected: Shows all three new anti-patterns

**Step 5: Commit**

```bash
git add docs/extension-reference/skills/skills-anti-patterns.md
git commit -m "docs(skills): add semantic anti-patterns (proxy verification, silent skipping, evidence-free outputs)"
```

---

## Task 7: Update cross-references

**Files:**
- Modify: `docs/extension-reference/skills/skills-validation.md:7`
- Modify: `docs/extension-reference/skills/skills-content-sections.md:7`
- Modify: `docs/extension-reference/skills/skills-anti-patterns.md:7`

**Step 1: Update related_to in skills-validation.md**

Change line 7 from:
```yaml
related_to: [skills-examples]
```
To:
```yaml
related_to: [skills-examples, skills-templates, skills-quality-dimensions]
```

**Step 2: Update related_to in skills-content-sections.md**

Change line 7 from:
```yaml
related_to: [skills-examples, skills-validation]
```
To:
```yaml
related_to: [skills-examples, skills-validation, skills-templates]
```

**Step 3: Update related_to in skills-anti-patterns.md**

Change line 7 from:
```yaml
related_to: [skills-validation, skills-examples]
```
To:
```yaml
related_to: [skills-validation, skills-examples, skills-quality-dimensions]
```

**Step 4: Verify cross-references**

Run: `grep "related_to" docs/extension-reference/skills/skills-validation.md docs/extension-reference/skills/skills-content-sections.md docs/extension-reference/skills/skills-anti-patterns.md`
Expected: Each file shows updated related_to with new files

**Step 5: Commit**

```bash
git add docs/extension-reference/skills/skills-validation.md docs/extension-reference/skills/skills-content-sections.md docs/extension-reference/skills/skills-anti-patterns.md
git commit -m "docs(skills): update cross-references for new semantic quality files"
```

---

## Task 8: Final verification

**Step 1: Count files**

Run: `ls docs/extension-reference/skills/*.md | wc -l`
Expected: 12 (was 10, +2 new files)

**Step 2: Check frontmatter validity**

Run: `head -10 docs/extension-reference/skills/skills-templates.md docs/extension-reference/skills/skills-quality-dimensions.md`
Expected: Valid YAML frontmatter for both files

**Step 3: Check for broken links**

Run: `grep -h '\[.*\](skills-' docs/extension-reference/skills/*.md | grep -v '#' | sort -u`
Expected: All referenced files exist in the directory

---

## Summary

| Task | Action | File |
|------|--------|------|
| 1 | CREATE | `skills-templates.md` — 5 semantic templates |
| 2 | CREATE | `skills-quality-dimensions.md` — 9 dimensions |
| 3 | EDIT | `skills-content-sections.md` — observable signal requirement |
| 4 | EDIT | `skills-content-sections.md` — verification ladder |
| 5 | EDIT | `skills-validation.md` — 2 semantic minimums |
| 6 | EDIT | `skills-anti-patterns.md` — 3 anti-pattern rows |
| 7 | EDIT | Cross-references in 3 files |
| 8 | VERIFY | Final checks |

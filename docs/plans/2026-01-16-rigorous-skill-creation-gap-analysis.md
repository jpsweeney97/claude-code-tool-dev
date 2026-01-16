# Gap Analysis: rigorous-skill-creation Design

**Date:** 2026-01-16
**Design Document:** `docs/plans/2026-01-15-rigorous-skill-creation-design.md`
**Branch:** `feature/rigorous-skill-creation-design`

## Source Materials Reviewed

| Source | Location | Lines |
|--------|----------|-------|
| skillosophy/SKILL.md | metamarket 0.1.0 | 405 |
| skillosophy/references/methodology/thinking-lenses.md | metamarket 0.1.0 | 160 |
| skillosophy/references/methodology/regression-questions.md | metamarket 0.1.0 | 267 |
| skillosophy/references/methodology/risk-tiers.md | metamarket 0.1.0 | 62 |
| skillosophy/references/methodology/category-integration.md | metamarket 0.1.0 | 157 |
| skillosophy/references/checklists/*.md | metamarket 0.1.0 | 14 files |
| skillosophy/agents/*.md | metamarket 0.1.0 | 4 files |
| writing-skills/SKILL.md | superpowers 4.0.3 | 656 |
| writing-skills/testing-skills-with-subagents.md | superpowers 4.0.3 | 385 |
| writing-skills/anthropic-best-practices.md | superpowers 4.0.3 | 1150 |
| writing-skills/persuasion-principles.md | superpowers 4.0.3 | 188 |
| test-driven-development/SKILL.md | superpowers 4.0.3 | 372 |
| test-driven-development/testing-anti-patterns.md | superpowers 4.0.3 | 300 |

---

## Critical Issues (Must Fix)

### 1. Duplicate Step Numbers

**Severity:** Critical — breaks procedure continuity

| Location | Issue |
|----------|-------|
| Lines 398 + 404 | Step 22 appears twice |
| Lines 421 + 433 | Step 31 appears twice |
| Between 412-414 | Step 28 is missing (jumps 27 → 29) |

**Evidence:**
```
Line 398: 22. **Create pressure scenarios** with:
Line 404: 22. **Run baseline** via Task tool for each scenario
Line 421: 31. **Generate sections in order**:
Line 433: 31. **For each section**:
```

**Action:** Renumber Phase 3 and Phase 4 steps sequentially.

---

### 2. Design's Own Description Violates CSO Guidance

**Severity:** Critical — violates the design's own core warning

The design warns extensively about the "Description Trap" (lines 419, 819-828) but the design's own frontmatter description violates this guidance.

**Current description (lines 148-151):**
```yaml
description: Use when creating skills that need verified behavior change,
  especially high-risk skills (security, agentic, data operations) or skills
  that enforce discipline. Combines requirements dialogue with TDD-style
  pressure testing.
```

**Problem:** "Combines requirements dialogue with TDD-style pressure testing" is a workflow summary — exactly what the design warns against at line 828: "When skill description says 'Use when X — does Y then Z', Claude may execute Y→Z from the description without reading SKILL.md body."

**CSO-compliant version:**
```yaml
description: Use when creating skills that need verified behavior change,
  especially high-risk skills (security, agentic, data operations) or skills
  that enforce discipline.
```

**Action:** Remove workflow summary from description field.

---

## Significant Gaps (Should Address)

### 3. Missing Pressure Type: "Economic"

**Source (writing-skills/testing-skills-with-subagents.md)** lists 7 pressure types:
- Time (emergency, deadline, window closing)
- Sunk cost (hours of work, "waste" to delete)
- Authority (senior/manager says skip it)
- **Economic (job, promotion at stake)**
- Exhaustion (end of day, tired)
- Social (looking dogmatic, inflexible)
- Pragmatic ("being pragmatic vs dogmatic")

**Design (line 401)** lists only 6:
- "time, sunk cost, authority, exhaustion, social, pragmatic"

**Action:** Add "economic" to pressure type list.

---

### 4. Missing: Persuasion Principles

**Source (writing-skills/persuasion-principles.md, 188 lines)** contains research-backed psychology (Cialdini 2021, Meincke et al. 2025) for skill design:

| Principle | Use For |
|-----------|---------|
| Authority | Discipline-enforcing, safety-critical ("YOU MUST", "Never", "Always") |
| Commitment | Multi-step processes, accountability (require announcements) |
| Scarcity | Immediate verification, time-sensitive ("Before proceeding") |
| Social Proof | Universal practices, common failures ("Every time", "Always") |
| Unity | Collaborative workflows ("our codebase", "we're colleagues") |
| Reciprocity | Rarely needed |
| Liking | DON'T USE for compliance (creates sycophancy) |

**Key finding:** "Persuasion techniques doubled compliance (33% → 72%, p < .001)"

**Design:** No mention of persuasion principles anywhere.

**Action:** Add reference to persuasion-principles.md or integrate key principles into Phase 4 guidance for discipline-enforcing skills.

---

### 5. Missing: Anthropic Best Practices Reference

**Source (writing-skills/anthropic-best-practices.md, 1150 lines)** contains official Anthropic guidance:

- Conciseness principles ("Context window is public good")
- **"Test with all models: Haiku, Sonnet, Opus"** — design doesn't mention model testing
- Progressive disclosure patterns ("Keep references one level deep from SKILL.md")
- MCP tool references: **"Always use fully qualified names: ServerName:tool_name"**
- "Avoid deeply nested references — Claude may use `head -100` on nested files"
- Skill structure guidelines
- Evaluation-first development

**Design:** No explicit reference to Anthropic best practices document.

**Action:** Add reference to anthropic-best-practices.md in relevant phases, or extract key guidance into design.

---

### 6. Missing: Risk Tier Minimum Requirements Table

**Source (skillosophy/risk-tiers.md)** has detailed per-tier minimums:

| Requirement | Low | Medium | High |
|-------------|-----|--------|------|
| All 11 sections | Y | Y | Y |
| 1 quick check | Y | Y | Y |
| 1 troubleshooting | Y | Y | Y |
| 1 STOP/ask (missing inputs) | Y | Y | Y |
| STOP/ask (ambiguity) | — | Y | Y |
| Explicit non-goals (≥3) | — | Y | Y |
| 2nd verification mode | — | SHOULD | Y |
| Ask-first gates | — | — | Y |
| ≥2 STOP/ask gates | — | — | Y |
| Rollback/escape guidance | — | — | Y |

**Design (lines 350-354, 558-562):** Has risk tier criteria but lacks these minimum requirements per tier.

**Action:** Add tier-specific minimums table to design or ensure risk-tiers.md reference file contains this.

---

### 7. Missing: Unified Bulletproof Criteria

**Source (writing-skills/testing-skills-with-subagents.md)** explicitly defines when a skill is "bulletproof":

1. Agent chooses correct option under maximum pressure
2. Agent cites skill sections as justification
3. Agent acknowledges temptation but follows rule
4. Meta-testing reveals "skill was clear, I should follow it"

**Design:** Has these scattered (lines 464-466, 494-495) but no unified "bulletproof signs" section.

**Action:** Add dedicated "Bulletproof Criteria" subsection in Phase 6 or Verification section.

---

### 8. Missing: Regression Questioning Detail

**Source (skillosophy/regression-questions.md, 267 lines)** has 7 detailed categories:

1. **Missing Elements** (5 questions) — "What am I missing?", "What assumptions am I making?"
2. **Expert Simulation** (6 expert types) — Domain, UX, Systems, Security, Performance, Maintenance
3. **Failure Analysis** (6 failure modes) — Catastrophic, Silent, Adoption, Evolution, Technical debt, Ecosystem
4. **Temporal Projection** (7 timeframes) — Now, 1 week, 1 month, 6 months, 1 year, 2 years, 5 years
5. **Completeness Verification** (5 checks) — Thinking models, Domain, Stakeholder, Integration, Quality
6. **Meta-Questioning** (5 meta-questions) — "What question haven't I asked?"
7. **Script and Automation Analysis** (8 questions) — What operations repeat? What needs validation?

Plus termination criteria: "3 consecutive rounds with no new insights OR all thinking models applied OR ≥3 expert perspectives considered"

**Design (line 335):** Only references "phase-1-requirements.md (includes regression questioning protocol)" — methodology itself is not described.

**Action:** Ensure phase-1-requirements.md contains full regression questioning methodology, or summarize key categories in design.

---

### 9. Missing: Session State Lifecycle Table

**Source (skillosophy/checklists/session-state.md)** has:

| Phase | Session State |
|-------|---------------|
| Phase 0 (Triage) | Not yet created |
| Phase 1 (Analysis) | Created at end with initial state |
| Phase 2 (Checkpoint) | Updated with validated decisions |
| Phase 3 (Generation) | Updated after each section approval |
| Phase 4 (Panel) | Present during review |
| After approval | **Removed** |

**Design:** Mentions lifecycle but doesn't have this table.

**Action:** Add Session State lifecycle table to design.

---

### 10. Incomplete: Category DoD Additions

**Source (skillosophy/category-integration.md, 157 lines)** has detailed per-category requirements for all 21 categories with specific DoD items.

Example entries:
- `debugging-triage`: regression guard verified
- `security-changes`: deny-path verified
- `data-migrations`: backup verified, rollback tested, data integrity checked
- `agentic-pipelines`: idempotency contract verified

**Design (lines 856-863):** Shows 5 example categories with "Dominant Failure Mode" but not the full DoD requirements.

**Action:** Expand table or ensure category-integration.md reference file contains full details.

---

### 11. Missing: Checklist Validation Criteria

**Source** has 14 detailed checklist files with MUST/SHOULD/SEMANTIC requirements for each of the 11 body sections plus frontmatter, frontmatter-decisions, and session-state.

Example (procedure.md):
- MUST: Steps numbered, executable actions, ≥1 STOP for missing inputs, ≥1 STOP for ambiguity
- HIGH-MUST: Ask-first gate before breaking/destructive/irreversible actions
- SHOULD: inspect→decide→act→verify order
- SEMANTIC: "Use judgment" without criteria is a fail

**Design (line 435):** References "section requirements in reference" but doesn't document what those requirements are.

**Action:** Ensure phase-4-generation.md contains merged checklist criteria, or document summary in design.

---

### 12. Missing: discover.py Description

**Design (line 50):** Lists `discover.py` in directory structure but doesn't describe what it does.

**Source (skillosophy):** "Inventory utility for existing skills (supports REVIEW/VALIDATE workflows)" — builds skill index for triage.

**Action:** Add description: "Build skill index for triage routing"

---

## Correctly Captured (Verified)

| Item | Source | Design Location | Status |
|------|--------|-----------------|--------|
| Iron Law prominence | TDD, writing-skills | Lines 13, 389 | ✓ |
| 14 lenses (11+3) | skillosophy + new | Lines 178-204 | ✓ |
| Panel for Medium+High | Handoff decision | Lines 24, 312, 354 | ✓ |
| 4 panel agents | skillosophy | Lines 503-507 | ✓ |
| 11 body sections in order | skillosophy | Lines 421-432 | ✓ |
| 21 categories | skillosophy | Line 355 | ✓ |
| Escalate immediately (recurring) | Handoff decision | Line 513 | ✓ |
| Degrees of freedom | Handoff decision | Lines 581-596 | ✓ |
| Description trap warning | writing-skills | Lines 419, 819-828 | ✓ |
| Worked example | Handoff decision | Line 47 | ✓ |
| discover.py in structure | Handoff decision | Line 50 | ✓ |
| metadata.decisions schema | skillosophy | Lines 274-304 | ✓ |
| Intentional deviations section | Handoff decision | Lines 917-927 | ✓ |

---

## Intentional Deviations (Already Documented)

| Source Guidance | Design Choice | Rationale | Status |
|-----------------|---------------|-----------|--------|
| writing-skills: "Only name and description in frontmatter" | Extended frontmatter | Source may be outdated; current platform supports extended fields | Documented (line 923) |
| skillosophy: Panel required for all CREATE | Panel for Medium+High only | Right-sized rigor; Low-risk skills don't need structural review | Documented (line 924) |
| writing-skills: Token efficiency targets | Not incorporated | Deferred; focus on correctness first, optimize later | Documented (line 925) |
| skillosophy: Mode confidence percentages displayed | Thresholds only | Thresholds already communicate confidence; explicit % is implementation detail | Documented (line 926) |

---

## Handoff Gotchas Status

| Gotcha | Status | Evidence |
|--------|--------|----------|
| "Step numbering in Phase 3/4 may be off" | **CONFIRMED** | Duplicate steps 22, 31; missing step 28 |
| "11 thinking lenses still appears" | **FIXED** | All references now say 14 |
| "Phase flow diagram spacing" | **OK** | Diagram renders correctly |

---

## Summary

| Category | Count |
|----------|-------|
| Critical Issues (must fix) | 2 |
| Significant Gaps (should address) | 10 |
| Correctly Captured | 13 |
| Intentional Deviations (documented) | 4 |

### Priority Order for Resolution

1. **Critical:** Fix step numbering (lines 398-433)
2. **Critical:** Fix description CSO violation (lines 148-151)
3. **High:** Add missing pressure type "economic"
4. **High:** Add risk tier minimum requirements table
5. **High:** Add unified bulletproof criteria
6. **Medium:** Add persuasion principles reference
7. **Medium:** Add Anthropic best practices reference
8. **Medium:** Ensure regression questioning detail in ref file
9. **Medium:** Add Session State lifecycle table
10. **Low:** Expand category DoD table
11. **Low:** Ensure checklist criteria in ref file
12. **Low:** Add discover.py description

---

## Resolution Status (2026-01-16)

All gaps have been addressed. Design document updated.

### Critical Issues — FIXED

| Issue | Resolution |
|-------|------------|
| Duplicate step numbers | Renumbered Phase 3-8 (now steps 19-61) |
| CSO violation in description | Removed workflow summary from frontmatter |

### Significant Gaps — RESOLVED

| Gap | Decision | Action |
|-----|----------|--------|
| 3. Missing "economic" pressure | Add to design | ✅ Added to line 400 |
| 4. Persuasion principles | Reference file | ✅ Added to references/ |
| 5. Anthropic best practices | Reference file | ✅ Added to references/ |
| 6. Risk tier minimums | Add to design | ✅ Added table after step 10 |
| 7. Bulletproof criteria | Add to design | ✅ Added checklist in Phase 6 |
| 8. Regression questioning | Reference file | Document in phase-1-requirements.md |
| 9. Session State lifecycle | Reference file | Document in session-state-schema.md |
| 10. Category DoD | Reference file | Document in category-integration.md |
| 11. Checklist criteria | Reference file | Document in phase-4-generation.md |
| 12. discover.py description | Already present | ✅ No change needed |

### Reference Files to Create

When implementing the skill, ensure these reference files contain the specified content:

- `phase-1-requirements.md`: 7 regression question categories with termination criteria
- `phase-4-generation.md`: MUST/SHOULD/SEMANTIC validation criteria per section
- `session-state-schema.md`: Session State lifecycle table
- `category-integration.md`: Full 21-category DoD table
- `persuasion-principles.md`: 7 principles with usage guidance
- `anthropic-best-practices.md`: Official Anthropic skill design guidance

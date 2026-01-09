# skillsmith Migration Plan

> Step-by-step plan for building skillsmith from skill-documentation and skillforge.

**Date:** 2026-01-09
**Status:** Draft
**Related:** [skillsmith Design Document](./2026-01-09-skillsmith-design.md)

---

## Overview

### Source Projects

| Project | Location | Status after migration |
|---------|----------|------------------------|
| skill-documentation | `/skill-documentation/` | Archived to `old-repos/` |
| skillforge | `.claude/skills/skillforge/` | Deprecated, then deleted |

### Target

```
packages/plugins/skillsmith/
```

### High-Risk Items

| Item | Risk | Mitigation |
|------|------|------------|
| Validator merge | Conflicting checks, missed cases | Regression test against both old validators |
| SKILL.md rewrite | Large, complex file | Incremental sections, test each phase |

---

## Phase 1: Setup

**Goal:** Create plugin directory structure and metadata.

**No dependencies.**

### Steps

- [ ] 1.1 Create `packages/plugins/skillsmith/` directory
- [ ] 1.2 Create `.claude-plugin/` subdirectory
- [ ] 1.3 Create `plugin.json`:
  ```json
  {
    "name": "skillsmith",
    "version": "1.0.0",
    "description": "Unified framework for creating, validating, and reviewing Claude Code skills",
    "author": {
      "name": "Your Name"
    },
    "license": "MIT",
    "keywords": ["skills", "skillforge", "validation", "meta-skill"]
  }
  ```
- [ ] 1.4 Create directory structure:
  ```
  skillsmith/
  ├── .claude-plugin/
  ├── agents/
  ├── skills/skillsmith/
  │   ├── references/
  │   │   ├── spec/
  │   │   ├── workflow/
  │   │   ├── analysis/
  │   │   ├── review/
  │   │   └── scripts/
  │   └── templates/
  ├── scripts/
  │   └── tests/
  └── commands/
  ```
- [ ] 1.5 Create minimal `README.md`:
  ```markdown
  # skillsmith

  Unified framework for creating, validating, and reviewing Claude Code skills.

  ## Installation

  ```bash
  claude plugin install skillsmith@tool-dev
  ```

  ## Usage

  - `/skillsmith` or `/create-skill` - Full skill creation workflow
  - `/review-skill <path>` - Review existing skill
  - `/lint-skill <path>` - Validate skill

  See `skills/skillsmith/SKILL.md` for complete documentation.
  ```
- [ ] 1.6 Create `LICENSE` (MIT)
- [ ] 1.7 Create `CHANGELOG.md` with initial entry

### Verification

- [ ] Directory structure matches design
- [ ] plugin.json is valid JSON
- [ ] README.md exists
- [ ] LICENSE file exists
- [ ] CHANGELOG.md exists

---

## Phase 2: Copy References

**Goal:** Copy all spec and reference documents from both sources.

**Depends on:** Phase 1

### From skill-documentation → references/spec/

- [ ] 2.1 Copy `skills-as-prompts-strict-spec.md`
- [ ] 2.2 Copy `skills-categories-guide.md`
- [ ] 2.3 Copy `skills-semantic-quality-addendum.md`
- [ ] 2.4 Copy `skills-domain-annexes.md`

### From skill-documentation → references/workflow/

- [ ] 2.5 Copy `skills-authoring-review-pipeline.md` (historical reference)
- [ ] 2.6 Copy `how-to-author-review-one-pager.md` (to be updated later)

### From skillforge → references/analysis/

- [ ] 2.7 Copy `references/regression-questions.md`
- [ ] 2.8 Copy `references/multi-lens-framework.md`
- [ ] 2.9 Copy `references/evolution-scoring.md`

### From skillforge → references/review/

- [ ] 2.10 Copy `references/synthesis-protocol.md` (to be updated later)

### From skillforge → references/scripts/

- [ ] 2.11 Copy `references/script-integration-framework.md`
- [ ] 2.12 Copy `references/script-patterns-catalog.md`

### From skillforge → templates/

- [ ] 2.13 Copy `assets/templates/script-template.py`

### From skillforge → scripts/

- [ ] 2.14 Copy `scripts/discover_skills.py`
- [ ] 2.15 Update any hardcoded paths in discover_skills.py

### Verification

- [ ] All 14 files copied
- [ ] No broken internal links
- [ ] discover_skills.py runs without errors

---

## Phase 3: Create and Update Reference Files

**Goal:** Create new files and update copied files to match skillsmith spec.

**Depends on:** Phase 2

### New Files

- [ ] 3.1 Create `references/spec-index.md`:
  ```markdown
  # Spec Section Index

  ## Trigger Mappings

  | Decision Type | Section | Path |
  |---------------|---------|------|
  | Risk tier assignment | Risk Tiers | spec/skills-as-prompts-strict-spec.md#risk-tiers |
  | Category selection | Category definitions | spec/skills-categories-guide.md#category-{name} |
  | Evaluating decision point validity | Decision Points | spec/skills-as-prompts-strict-spec.md#decision-points |
  | Scoring timelessness | Evolution Scoring | analysis/evolution-scoring.md |
  | Checking semantic quality dimension | Dimension {X} | spec/skills-semantic-quality-addendum.md#dimension-{x} |
  | Determining if command is unsafe | Unsafe Defaults | spec/skills-as-prompts-strict-spec.md#unsafe-defaults |
  | Validating STOP behavior | STOP Templates | spec/skills-as-prompts-strict-spec.md#stop-ask-templates |
  | Checking assumption completeness | Declared Assumptions | spec/skills-as-prompts-strict-spec.md#undeclared-assumptions |
  | Evaluating extension point quality | Extension Points | analysis/evolution-scoring.md#extension-points |
  | Borderline FAIL code | FAIL.{code} | spec/skills-as-prompts-strict-spec.md#fail-{code} |
  ```

- [ ] 3.2 Create `references/workflow/merged-creation-workflow.md`:
  - Document the 4-phase unified workflow
  - Include Phase 0-4 details from design document
  - Include error handling defaults
  - Include iteration caps and escalation paths

- [ ] 3.3 Update `references/workflow/how-to-author-review-one-pager.md`:
  - Replace 6-step with 4-phase workflow summary
  - Update section references to hybrid structure
  - Keep concise (quick reference)

- [ ] 3.4 Update `references/review/synthesis-protocol.md`:
  - Add two-tier quality gate (semantic → timelessness)
  - Add holistic review approach (dimensions as shared vocabulary)
  - Add spec consultation triggers
  - Add citation requirement

- [ ] 3.5 Create `templates/skill-md-template.md`:
  - Include frontmatter template
  - Include all 11 hybrid sections with guidance
  - Include placeholder content for each section

- [ ] 3.6 Create `templates/analysis-notes-template.md`:
  - Classification section
  - Requirements section
  - Key Decisions section
  - STOP Triggers section
  - Scripts Decision section
  - For MODIFY section

### Verification

- [ ] All 6 files created/updated
- [ ] spec-index.md paths are valid
- [ ] Templates are usable

---

## Phase 4: Validator Merge

**Goal:** Combine skill_lint.py and validate-skill.py into unified validator.

**Depends on:** Phase 2 (can run in parallel with Phase 3)

### Steps

- [ ] 4.1 Copy `skill-documentation/skill_lint.py` as base to `scripts/skill_lint.py`
- [ ] 4.2 Review validate-skill.py checks not in skill_lint.py:
  - Frontmatter validation (name format, description format, allowed properties)
  - Triggers section check (3-5 phrases)
  - Extension Points section check
  - Anti-Patterns section check
  - Script validation (if scripts/ exists)
- [ ] 4.3 Add frontmatter checks to unified validator
- [ ] 4.4 Add hybrid structure checks (Triggers, Extension Points, Anti-Patterns)
- [ ] 4.5 Add script validation checks
- [ ] 4.6 Ensure module is importable (`from skill_lint import lint_skill`)
- [ ] 4.7 Copy/adapt `skill-documentation/tests/test_skill_lint.py`
- [ ] 4.8 Add tests for new checks

### Regression Testing

- [ ] 4.9 Identify corpus of existing skills for testing
- [ ] 4.10 Run old skill_lint.py on corpus, record results
- [ ] 4.11 Run old validate-skill.py on corpus, record results
- [ ] 4.12 Run unified validator on corpus
- [ ] 4.13 Verify: skills that passed both old validators pass unified
- [ ] 4.14 Verify: skills that failed either old validator fail unified (or have documented exception)

### Verification

- [ ] `python scripts/skill_lint.py --help` works
- [ ] `python -c "from skill_lint import lint_skill"` succeeds
- [ ] All unit tests pass
- [ ] Regression tests pass

---

## Phase 5: Panel Agents

**Goal:** Create the 4 agent definition files.

**Depends on:** Phase 3 (needs spec-index.md)

### Agent Files

- [ ] 5.1 Create `agents/design-agent.md`:
  - Focus: Structure, patterns, technical correctness
  - Dimensions: Constraint completeness, Decision sufficiency, Minimality
  - Reference: Design doc Section 9 (Agent Review Format)

- [ ] 5.2 Create `agents/audience-agent.md`:
  - Focus: Clarity, triggers, discoverability
  - Dimensions: Intent fidelity, Terminology clarity, Artifact usefulness
  - Reference: Design doc Section 9 (Agent Review Format)

- [ ] 5.3 Create `agents/evolution-agent.md`:
  - Focus: Timelessness scoring, extension points, ecosystem fit
  - Threshold: Score ≥7 required
  - Reference: Design doc Section 9 (Agent Review Format), Section 11b (Timelessness)

- [ ] 5.4 Create `agents/script-agent.md`:
  - Focus: Script quality (conditional—only if scripts/ exists)
  - Checks: Pattern compliance, self-verification, documentation
  - Reference: Design doc Section 9 (Agent Review Format)

### Verification

- [ ] All 4 agent files created
- [ ] Each agent references spec-index.md
- [ ] Each agent has output format specified

---

## Phase 6: Main Skill

**Goal:** Write the SKILL.md with unified workflow.

**Depends on:** All previous phases

### Steps

- [ ] 6.1 Create `skills/skillsmith/SKILL.md` frontmatter:
  ```yaml
  ---
  name: skillsmith
  description: Unified framework for creating, validating, and reviewing Claude Code skills
  license: MIT
  metadata:
    version: "1.0.0"
    model: claude-opus-4-5-20251101
    category: meta-skills
  ---
  ```

- [ ] 6.2 Write Triggers section (3-5 phrases)
- [ ] 6.3 Write When to use section
- [ ] 6.4 Write When NOT to use section
- [ ] 6.5 Write Inputs section
- [ ] 6.6 Write Outputs section
- [ ] 6.7 Write Procedure section:
  - Phase 0: Triage
  - Phase 1: Analysis
  - Phase 2: Generation
  - Phase 3: Diff, Confirm & Validation
  - Phase 4: Review
- [ ] 6.8 Write Verification section
- [ ] 6.9 Write Troubleshooting section
- [ ] 6.10 Write Anti-Patterns section
- [ ] 6.11 Write Extension Points section
- [ ] 6.12 Write References section (links to all reference docs)

### Verification

- [ ] Run unified validator on SKILL.md
- [ ] All checks pass
- [ ] Estimated size: 600-900 lines

---

## Phase 7: Commands

**Goal:** Create the 3 command entry points.

**Depends on:** Phase 6

### Command Files

- [ ] 7.1 Create `commands/create-skill.md`:
  ```markdown
  ---
  description: Create a new skill using the skillsmith workflow
  ---

  Invoke the skillsmith skill to create a new skill.

  $ARGUMENTS will be passed as the skill creation goal.
  ```

- [ ] 7.2 Create `commands/review-skill.md`:
  ```markdown
  ---
  description: Review an existing skill using skillsmith's quality gates
  ---

  Run validation (Phase 3) and panel review (Phase 4) on an existing skill.

  $ARGUMENTS is the path to the skill.

  This runs:
  1. Unified validator
  2. Multi-agent panel review

  Use for:
  - Validating skills created outside skillsmith
  - Re-reviewing after manual edits
  - Quality-checking before promotion
  ```

- [ ] 7.3 Create `commands/lint-skill.md`:
  ```markdown
  ---
  description: Validate a skill against the skillsmith spec
  ---

  Run the unified validator without panel review.

  $ARGUMENTS is the path to the skill.
  ```

### Verification

- [ ] Commands have valid frontmatter
- [ ] $ARGUMENTS used correctly

---

## Phase 8: Testing

**Goal:** Comprehensive testing of all components.

**Depends on:** All previous phases

### Unit Tests

- [ ] 8.1 Run `python -m pytest scripts/tests/` - all pass
- [ ] 8.2 Add `scripts/tests/test_discover_skills.py` if missing

### Integration Tests

- [ ] 8.3 Test validator on good skill (expect PASS)
- [ ] 8.4 Test validator on skill with missing section (expect FAIL)
- [ ] 8.5 Test validator on skill with bad frontmatter (expect FAIL)

### Manual Tests

- [ ] 8.6 Install plugin: `claude plugin install skillsmith@tool-dev`
- [ ] 8.7 Restart Claude Code
- [ ] 8.8 Test `/create-skill create a simple test skill`:
  - Verify Phase 0 triage runs
  - Verify Phase 1 analysis runs
  - Verify Phase 2 generates skill
  - Verify Phase 3 shows diff/confirm
  - Verify Phase 4 panel runs
- [ ] 8.9 Test `/review-skill` on existing skill
- [ ] 8.10 Test `/lint-skill` on existing skill
- [ ] 8.11 Test standalone agent invocation

### Regression Tests

- [ ] 8.12 Document which existing skills fail new validator and why (expected: most will fail due to new hybrid structure requirements)
- [ ] 8.13 Verify validator produces clear, actionable error messages for missing sections

### Verification

- [ ] All tests pass
- [ ] No regressions identified (or documented)

---

## Phase 9: Cleanup

**Goal:** Deprecate old sources, clean up.

**Depends on:** Phase 8 passing

### Deprecation

- [ ] 9.1 Add deprecation notice to `.claude/skills/skillforge/SKILL.md`:
  ```markdown
  > **DEPRECATED:** This skill has been replaced by the skillsmith plugin.
  > Install with: `claude plugin install skillsmith@tool-dev`
  > Then use `/skillsmith` instead.
  ```

- [ ] 9.2 Commit deprecation notice

### Archive (after transition period)

- [ ] 9.3 Move `skill-documentation/` to `old-repos/skill-documentation/`
- [ ] 9.4 Delete `.claude/skills/skillforge/` (after transition period)
- [ ] 9.5 Update any references to old locations

### Final Verification

- [ ] 9.6 Plugin works without old sources
- [ ] 9.7 No broken references

---

## Success Criteria

| Criterion | Verification |
|-----------|--------------|
| Plugin installs | `claude plugin install skillsmith@tool-dev` succeeds |
| Validator works | `python scripts/skill_lint.py` passes on test skills |
| Workflow runs | `/skillsmith create a test skill` completes |
| Review works | `/review-skill` runs panel on existing skill |

*Note: skillsmith sets a new quality standard. Existing skills are not expected to pass the new validator without updates.*

---

## Rollback Plan

If migration fails:

1. Keep old skillforge functional (don't delete until plugin is stable)
2. skill-documentation remains in place until archived
3. Revert plugin changes if critical issues found
4. Users can continue using `/skillforge` during transition

### Rollback Triggers

Initiate rollback if any of the following occur:

| Trigger | Description |
|---------|-------------|
| Installation failure | Plugin fails to install after 2 attempts |
| Validator crash | skill_lint.py errors on valid input (crashes, not FAIL codes) |
| Workflow broken | `/skillsmith` cannot complete Phase 0 (triage) |
| Panel unresponsive | Agents fail to produce reviews |

If triggered: Stop migration, diagnose root cause, fix before retrying.

---

## Timeline Estimate

*No time estimates per project guidelines. Steps are ordered by dependency, not timeline.*

---

## Notes

- This plan assumes single implementer
- Phases can be parallelized where dependencies allow (e.g., Phase 3 and Phase 4)
- Test early and often, especially the validator merge
- Keep old sources functional until new plugin is verified

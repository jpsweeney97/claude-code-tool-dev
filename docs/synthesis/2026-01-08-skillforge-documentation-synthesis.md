# Synthesis Report: skillforge + skill-documentation

**Date:** 2026-01-08
**Calibration:** Medium
**Sources:** `.claude/skills/skillforge/`, `skill-documentation/`

## Executive Summary

This synthesis analyzed two complementary sources for skill development:

1. **skillforge** — A meta-skill providing a 5-phase methodology for creating high-quality skills (Triage → Analysis → Specification → Generation → Synthesis Panel)
2. **skill-documentation** — A normative specification defining what skills must contain (8 required sections, 8 FAIL codes, risk tiering, 13 categories)

**Finding:** These sources are orthogonal and should be layered together:

- skill-documentation provides the **standards** (what skills must contain)
- skillforge provides the **methodology** (how to create skills that meet standards)

No fundamental conflicts exist. All detected differences resolve to complementary usage or sequential layering.

---

## Value Extraction

### From skillforge (High-Value Items)

| Item                             | Description                                                                                                                                                               | Adoption Recommendation                                            |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **11 Thinking Models**           | First Principles, Inversion, Second-Order Effects, Pre-Mortem, Systems Thinking, Devil's Advocate, Constraint Analysis, Pareto, Root Cause, Comparative, Opportunity Cost | Reference in deep skill creation; optional for simple skills       |
| **Multi-Agent Synthesis Panel**  | 3-4 Opus agents with unanimous approval requirement                                                                                                                       | Use for skillforge-generated skills; optional for manual authoring |
| **Evolution/Timelessness ≥7**    | Temporal projection (6mo/1yr/2yr) + anti-obsolescence patterns                                                                                                            | Add as quality dimension alongside risk tier                       |
| **Regression Questioning**       | Iterative self-questioning until no new insights (3 empty rounds)                                                                                                         | Use during Phase 1 analysis                                        |
| **Phase 0 Triage**               | Intelligent routing: USE_EXISTING / IMPROVE / CREATE / COMPOSE                                                                                                            | Prevents duplicate skill creation                                  |
| **Script Integration Framework** | 7 categories + 5 agentic patterns (Result dataclass, ValidationResult, exit codes)                                                                                        | Adopt for all skill scripts                                        |

### From skill-documentation (High-Value Items)

| Item                           | Description                                                                                                                                                             | Adoption Recommendation                      |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| **8-Section Skeleton**         | When to use, When NOT to use, Inputs, Outputs, Procedure, Decision points, Verification, Troubleshooting                                                                | Canonical structure for all skills           |
| **8 FAIL Codes + Linter**      | Deterministic structural enforcement                                                                                                                                    | Run on all skills; integrate into CI         |
| **Risk Tiering**               | Low/Medium/High with minimum gate requirements                                                                                                                          | Apply to all skills                          |
| **13 Categories**              | Meta-skills, Auditing, Agentic pipelines, Implementation, Debugging, Refactoring, Testing, Documentation, Build/CI, Integration, Security, Data migrations, Ops/release | Use for routing and domain-specific guidance |
| **Semantic Templates (T1-T7)** | Semantic contract, Scope fence, Assumptions ledger, Observable decision point, Verification ladder, Failure interpretation, Calibration wording                         | Copy-paste into skills as needed             |
| **Author/Reviewer Workflow**   | 6-step author (10-20 min) + 4-step reviewer (5-10 min)                                                                                                                  | Standard workflow for manual authoring       |

---

## Conflict Resolutions

### C1: Section Count Mismatch

**skillforge:** 9 sections (includes Evolution/Extension Points)
**skill-documentation:** 8 required sections

**Resolution:** 8-section skeleton is canonical (linter-enforced). Evolution/Extension Points is optional 9th section for meta-skills and High-risk skills.

### C2: Quality Gate Mechanism

**skillforge:** Multi-agent synthesis panel
**skill-documentation:** Linter + human review

**Resolution:** Layer sequentially:

1. `skill_lint.py` (structural, 8 FAIL codes)
2. Semantic review (human, 5 minimums)
3. Multi-agent panel (skillforge-only, unanimous)

Non-skillforge skills need only layers 1-2.

### C3: Scoring Systems

**skillforge:** Timelessness ≥7 (evolution lens)
**skill-documentation:** Risk tier (Low/Medium/High)

**Resolution:** Complementary axes in 2D quality space:

- X-axis: Risk tier (blast radius)
- Y-axis: Timelessness (longevity)

Both assessed; neither replaces the other.

### C4: Specification Format

**skillforge:** XML skill_specification
**skill-documentation:** Markdown semantic contract block

**Resolution:** Context-appropriate:

- Quick authoring → Semantic contract (T1)
- Deep skillforge pipeline → XML specification

### C5: Script Validation

**skillforge:** validate-skill.py
**skill-documentation:** skill_lint.py

**Resolution:** skill_lint.py is primary. Long-term: merge extended checks.

---

## Integration Plan

### Immediate (No Code Changes)

| #   | Action                                             | Owner                 |
| --- | -------------------------------------------------- | --------------------- |
| I1  | skillforge SKILL.md references 8-section skeleton  | skillforge maintainer |
| I2  | skillforge Phase 4 runs skill_lint.py before panel | skillforge maintainer |
| I3  | skill-documentation README references skillforge   | spec maintainer       |

### Short-term Enhancements

| #   | Action                                             | Priority |
| --- | -------------------------------------------------- | -------- |
| S1  | Add skill_lint.py to skillforge's validation chain | High     |
| S2  | Embed T1-T7 templates in skillforge generation     | Medium   |
| S3  | Add `--annex skillforge` for evolution scoring     | Medium   |
| S4  | Cross-reference documents bidirectionally          | Low      |

### Long-term Consolidation

| #   | Action                                                  | Rationale                  |
| --- | ------------------------------------------------------- | -------------------------- |
| L1  | Merge validate-skill.py into skill_lint.py              | Single validation tool     |
| L2  | Add 11-lens reference to skill-documentation            | Enhanced analysis guidance |
| L3  | Unified quality rubric (timelessness + risk + semantic) | Single scoring system      |

---

## Unified Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MANUAL SKILL AUTHORING                            │
│                                                                      │
│  1. Pick category (skills-categories-guide.md)                       │
│  2. Pick risk tier (round up if uncertain)                           │
│  3. Draft using 8-section skeleton                                   │
│  4. Add semantic contract block (T1)                                 │
│  5. Run skill_lint.py (must pass)                                   │
│  6. Human semantic review                                            │
│  7. Ship                                                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    SKILLFORGE-GENERATED SKILLS                       │
│                                                                      │
│  Phase 0: Triage (USE/IMPROVE/CREATE/COMPOSE)                        │
│      ↓                                                               │
│  Phase 1: Deep Analysis (11 lenses + regression questioning)         │
│      ↓                                                               │
│  Phase 2: Specification (XML)                                        │
│      ↓                                                               │
│  Phase 3: Generation (8-section skeleton + templates)                │
│      ↓                                                               │
│  [NEW] skill_lint.py (structural gate)                               │
│      ↓                                                               │
│  Phase 4: Multi-Agent Synthesis Panel (unanimous)                    │
│      ↓                                                               │
│  Ship                                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quality Framework

### Two-Axis Quality Model

```
                    │ Timelessness (Y-axis)
                    │
             9-10   │  ┌──────────────────┐
           Timeless │  │  EXEMPLARY       │
                    │  │  (Long-term,     │
             7-8    │  │   well-gated)    │
              Solid │  └──────────────────┘
                    │
             5-6    │  ┌──────────────────┐
           Moderate │  │  ACCEPTABLE      │
                    │  │  (Short-term OK, │
                    │  │   needs gates)   │
                    │  └──────────────────┘
                    │
             1-4    │  ┌──────────────────┐
         Ephemeral  │  │  REJECT          │
                    │  │  (Will rot,      │
                    │  │   unsafe)        │
                    │  └──────────────────┘
                    └───────────────────────────
                        Low    Medium    High
                        ← Risk Tier (X-axis) →
```

### Minimum Requirements by Quadrant

| Quadrant                 | Requirements                                                              |
| ------------------------ | ------------------------------------------------------------------------- |
| **High risk + Timeless** | ≥2 STOP/ask, ≥2 verification modes, ask-first gates, evolution ≥7         |
| **High risk + Moderate** | ≥2 STOP/ask, ≥2 verification modes, ask-first gates, evolution documented |
| **Low risk + Timeless**  | ≥1 STOP/ask, ≥1 quick check, evolution ≥7                                 |
| **Low risk + Ephemeral** | Acceptable for one-off tooling; document expiration                       |

---

## Files Reference

### skillforge

| File                                         | Purpose                                |
| -------------------------------------------- | -------------------------------------- |
| `SKILL.md`                                   | Main skill file (5-phase process)      |
| `references/multi-lens-framework.md`         | 11 thinking models                     |
| `references/evolution-scoring.md`            | Timelessness rubric                    |
| `references/synthesis-protocol.md`           | Multi-agent panel design               |
| `references/specification-template.md`       | XML specification structure            |
| `references/script-integration-framework.md` | 7 script categories + agentic patterns |
| `scripts/validate-skill.py`                  | Extended validation                    |
| `assets/templates/script-template.py`        | Result dataclass pattern               |

### skill-documentation

| File                                  | Purpose                                         |
| ------------------------------------- | ----------------------------------------------- |
| `skills-as-prompts-strict-spec.md`    | Normative 8-section contract + 8 FAIL codes     |
| `skills-categories-guide.md`          | 13 categories with DoD checklists               |
| `skills-semantic-quality-addendum.md` | 5 minimums + 9 dimensions + 7 templates         |
| `skills-domain-annexes.md`            | Domain-specific invariants (3 of 13 categories) |
| `how-to-author-review-one-pager.md`   | Author/reviewer workflow                        |
| `skill_lint.py`                       | Deterministic linter                            |
| `tests/test_skill_lint.py`            | Linter tests                                    |

---

## Recommendations

### For Skill Authors

1. **Start with category selection** (skills-categories-guide.md decision tree)
2. **Use 8-section skeleton** (mandatory for all skills)
3. **Add semantic contract block** (T1) for intent clarity
4. **Run skill_lint.py** before submitting
5. **For complex skills:** Consider using skillforge methodology

### For Reviewers

1. **Run linter first** (any FAIL code = reject)
2. **Check semantic quality** (5 minimums, especially decision points + verification)
3. **Verify risk tier gates** (High risk needs ≥2 STOP/ask)
4. **For skillforge-generated:** Also verify timelessness ≥7

### For Tooling Maintainers

1. **Integrate skill_lint.py into skillforge Phase 4**
2. **Add category support to skill_lint.py** (`--category` flag)
3. **Merge validate-skill.py checks over time**
4. **Add evolution scoring to linter** (`--annex skillforge`)

---

## Appendix: Glossary

| Term                   | Definition                                                                                                             | Source              |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **8-Section Skeleton** | Canonical structure: When to use, When NOT, Inputs, Outputs, Procedure, Decision points, Verification, Troubleshooting | skill-documentation |
| **FAIL Code**          | Deterministic structural violation (e.g., FAIL.missing-content-areas)                                                  | skill-documentation |
| **Risk Tier**          | Blast radius classification: Low/Medium/High                                                                           | skill-documentation |
| **Timelessness Score** | Longevity assessment: 1-10 (≥7 required for skillforge)                                                                | skillforge          |
| **Synthesis Panel**    | 3-4 Opus agents reviewing generated skill                                                                              | skillforge          |
| **11 Lenses**          | Thinking models for deep analysis                                                                                      | skillforge          |
| **Semantic Contract**  | T1 template: Primary goal, Non-goals, Hard constraints, Invariants, Acceptance signals, Risk posture                   | skill-documentation |

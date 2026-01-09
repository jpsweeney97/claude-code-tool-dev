# skillsmith Design Document

> Unified Claude Code plugin for creating, validating, and reviewing skills.

**Date:** 2026-01-09
**Status:** Draft
**Authors:** Human + Claude (brainstorming session)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Plugin Structure](#2-plugin-structure)
3. [Hybrid Skill Structure](#3-hybrid-skill-structure)
4. [Workflow Overview](#4-workflow-overview)
5. [Phase 0 - Triage](#5-phase-0---triage)
6. [Phase 1 - Analysis](#6-phase-1---analysis)
7. [Phase 2 - Generation](#7-phase-2---generation)
8. [Phase 3 - Diff, Confirm & Validation](#8-phase-3---diff-confirm--validation)
9. [Phase 4 - Review](#9-phase-4---review)
10. [Unified Validator](#10-unified-validator)
11. [Quality Model](#11-quality-model)
    - [11a. Tier 1 - Semantic Quality](#11a-tier-1---semantic-quality)
    - [11b. Tier 2 - Timelessness](#11b-tier-2---timelessness)
12. [Component Interaction](#12-component-interaction)
13. [Error Handling Summary](#13-error-handling-summary)
14. [Migration Overview](#14-migration-overview)
15. [Open Questions / Future Work](#15-open-questions--future-work)
16. [Glossary](#16-glossary)
17. [References](#17-references)

---

## 1. Executive Summary

**skillsmith** is a unified Claude Code plugin for creating, validating, and reviewing skills. It merges two existing projects:

### skill-documentation (current state)

- **Location:** `/Users/jp/Projects/active/claude-code-tool-dev/skill-documentation/`
- A standalone documentation framework (~170KB across 7 files)
- Defines the normative specification for skills:
  - 8 required content areas (When to use, Procedure, Verification, etc.)
  - 8 FAIL codes enforced by `skill_lint.py` linter (now 11 with hybrid additions)
  - 13 skill categories with failure modes and verification strictness
  - 9 semantic quality dimensions for "good" vs just "valid"
  - 3 risk tiers (Low/Medium/High)
  - 3 domain annexes (meta-skills, auditing, agentic pipelines)
- Includes a 6-step authoring pipeline and quick reference one-pager
- No creation workflow—focuses on specification and validation

### skillforge (current state)

- **Location:** `/Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/skillforge/`
- An existing skill (~870 lines) for creating other skills
- 5-phase workflow: Triage → Analysis → Specification → Generation → Review
- Deep analysis using 11 thinking models and regression questioning
- Multi-agent synthesis panel (3-4 Opus agents, unanimous approval)
- Timelessness scoring (≥7 required)
- XML specification as intermediate artifact
- Validation scripts (`validate-skill.py`, `quick_validate.py`)
- Different structural requirements than skill-documentation

### The Problem

These projects overlap but conflict. A skill passing `skill_lint.py` might fail `validate-skill.py`. They define different required sections. Quality criteria don't align.

### skillsmith Resolution

skillsmith resolves this by:

- Adopting skill-documentation's 8 sections as the structural foundation
- Adding skillforge's unique elements (Triggers, Extension Points, Anti-Patterns) for an 11-section hybrid
- Merging validators into a single unified linter
- Integrating skillforge's creation workflow with skill-documentation's spec as the authoritative reference
- Creating a two-tier quality model: semantic quality (primary), timelessness (secondary)

### Core Capability

Given any skill-related request, skillsmith:

1. Triages to determine CREATE, MODIFY, or USE_EXISTING
2. Analyzes requirements with category-aware, multi-lens depth
3. Generates skills following the hybrid 11-section structure
4. Validates with the unified linter
5. Reviews via multi-agent panel with two-tier quality gates

### Key Design Decisions

- Single unified workflow for create and modify (no artificial tiering)
- Spec-on-demand: Agents consult spec docs via explicit triggers, not upfront loading
- Diff + confirm before writes (no surprise modifications)
- All skill-documentation content preserved; XML spec and redundant validators dropped

**Target audience:** Claude itself—optimized for AI-driven skill creation with humans as reviewers.

---

## 2. Plugin Structure

**Plugin name:** `skillsmith`

**Location:** `packages/plugins/skillsmith/`

```
skillsmith/
├── .claude-plugin/
│   └── plugin.json
│
├── agents/
│   ├── design-agent.md
│   ├── audience-agent.md
│   ├── evolution-agent.md
│   └── script-agent.md
│
├── skills/
│   └── skillsmith/
│       ├── SKILL.md
│       │
│       ├── references/
│       │   ├── spec/
│       │   │   ├── skills-as-prompts-strict-spec.md
│       │   │   ├── skills-categories-guide.md
│       │   │   ├── skills-semantic-quality-addendum.md
│       │   │   └── skills-domain-annexes.md
│       │   │
│       │   ├── workflow/
│       │   │   ├── merged-creation-workflow.md
│       │   │   ├── skills-authoring-review-pipeline.md
│       │   │   └── how-to-author-review-one-pager.md
│       │   │
│       │   ├── analysis/
│       │   │   ├── regression-questions.md
│       │   │   ├── multi-lens-framework.md
│       │   │   └── evolution-scoring.md
│       │   │
│       │   ├── review/
│       │   │   └── synthesis-protocol.md
│       │   │
│       │   ├── scripts/
│       │   │   ├── script-integration-framework.md
│       │   │   └── script-patterns-catalog.md
│       │   │
│       │   └── spec-index.md
│       │
│       └── templates/
│           ├── skill-md-template.md
│           ├── analysis-notes-template.md
│           └── script-template.py
│
├── scripts/
│   ├── skill_lint.py
│   ├── discover_skills.py
│   └── tests/
│       ├── test_skill_lint.py
│       └── test_discover_skills.py
│
├── commands/
│   ├── create-skill.md
│   ├── review-skill.md
│   └── lint-skill.md
│
├── README.md
├── LICENSE
└── CHANGELOG.md
```

**File counts:**

- Plugin config: 1 file (plugin.json)
- Reference docs: 14 files
- Templates: 3 files
- Agents: 4 files
- Scripts: 2 + 2 test files
- Commands: 3 files
- Skill: 1 file (SKILL.md)
- Other: 3 files (README, LICENSE, CHANGELOG)

**Total: 33 files**

---

## 3. Hybrid Skill Structure

Skills created by skillsmith follow an 11-section hybrid structure with required frontmatter.

### Frontmatter (required)

```yaml
---
name: skill-name                    # Required: kebab-case, ≤64 chars
description: One-line description   # Required: ≤1024 chars, no < or >
license: MIT                        # Optional
allowed-tools: ["Tool1", "Tool2"]   # Optional: auto-approve these tools
metadata:                           # Optional
  version: "1.0.0"
  model: claude-opus-4-5-20251101
  timelessness_score: 8
  category: debugging-triage
---
```

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | kebab-case, ≤64 characters |
| `description` | Yes | ≤1024 characters, no `<` or `>` |
| `license` | No | Standard identifier (MIT, Apache-2.0, etc.) |
| `allowed-tools` | No | Array of tool names |
| `metadata` | No | Custom fields (version, model, category, etc.) |

### Body Sections (11)

| # | Section | Source | Purpose |
|---|---------|--------|---------|
| 1 | **Triggers** | skillforge | 3-5 natural language invocation phrases |
| 2 | **When to use** | skill-doc | Activation conditions and boundaries |
| 3 | **When NOT to use** | skill-doc | Anti-goals, exclusions, STOP conditions |
| 4 | **Inputs** | skill-doc | Required/optional inputs, declared assumptions |
| 5 | **Outputs** | skill-doc | Artifacts with objective Definition of Done |
| 6 | **Procedure** | skill-doc | Numbered executable steps with decision points embedded |
| 7 | **Verification** | skill-doc | Quick check with expected result |
| 8 | **Troubleshooting** | skill-doc | Failure modes with symptoms/causes/recovery |
| 9 | **Anti-Patterns** | skillforge | What to avoid during execution |
| 10 | **Extension Points** | skillforge | How the skill can evolve |
| 11 | **References** | both | Links to supporting docs (optional but recommended) |

### Enforcement

- Frontmatter: name and description required, strict format validation
- Sections 1-10: Enforced by unified validator (FAIL if missing)
- Section 11: Recommended, not enforced
- Decision points (2+ if/then branches): Embedded in Procedure, enforced
- STOP gates (1+ minimum): Enforced

---

## 4. Workflow Overview

skillsmith uses a single unified workflow for both creating new skills and modifying existing ones. The distinction emerges from triage, not separate code paths.

### Core Principle

Every request is "achieve goal given current state." For CREATE, current state is empty. For MODIFY, current state is the existing skill.

### Routing Decisions

| Route | Trigger | What happens |
|-------|---------|--------------|
| CREATE | No relevant existing skill | Full workflow, starting fresh |
| MODIFY | Existing skill identified | Full workflow, informed by existing content |
| USE_EXISTING | Goal already solved by existing skill | Recommend existing skill, exit |

### Workflow Diagram

```
User input
    │
    ▼
Phase 0: Triage
    │
    ├─→ USE_EXISTING ──→ Recommend skill ──→ Done
    │
    └─→ CREATE or MODIFY
            │
            ▼
      Phase 1: Analysis
            │
            ▼
      Phase 2: Generation
            │
            ▼
      Phase 3: Diff, Confirm & Validation
            │         │
            │         └─→ Fails 3x ──→ Back to Phase 1
            ▼
      Phase 4: Review
            │         │
            │         └─→ Rejected 5x ──→ Human escalation
            ▼
         APPROVED ──→ Update timelessness score ──→ Done
```

### Key Design Choices

- No artificial tiering (minor/moderate/major)—scope emerges from analysis
- Diff + confirm before any writes—no surprise modifications
- Iteration loops have caps—prevents infinite grinding
- Human escalation as final fallback

---

## 5. Phase 0 - Triage

**Purpose:** Determine routing, load context, set up for analysis.

### Inputs

- User goal (natural language)

### Steps

1. **Parse goal to understand intent**
   - Is this a creation request? ("create a skill for...")
   - Is this an improvement request? ("improve the X skill")
   - Is this a question? ("do I have a skill for...")

2. **Scan ecosystem for existing skills**
   - Run `discover_skills.py` to get skill index
   - Match goal against existing skills with confidence scoring
   - If scan fails: Warn and proceed without duplicate check

3. **Determine routing**

   | Match | Intent | Route |
   |-------|--------|-------|
   | ≥80% | Any | USE_EXISTING (recommend) or CLARIFY (if explicit create) |
   | 50-79% | Improve | MODIFY |
   | 50-79% | Create | CLARIFY (similar exists, proceed?) |
   | <50% | Create | CREATE |
   | <50% | Improve | Skill not found (ask for clarification) |

4. **For MODIFY: Load existing skill**
   - Load SKILL.md content
   - Inventory dependencies (references/, scripts/)
   - Verify internal references resolve
   - Check provenance (plugin skill → offer fork, legacy skill → warn)

5. **Preliminary category assignment**
   - Classify into one of 13 categories
   - If confidence ≥60%: Proceed with preliminary assignment
   - If confidence <60%: Present top 2-3 candidates, ask user

6. **Load category-specific guidance**
   - Load relevant section from `skills-categories-guide.md`
   - Category guidance informs Phase 1 analysis

### Outputs

- Routing decision (CREATE / MODIFY / USE_EXISTING)
- Existing skill content (if MODIFY)
- Dependency inventory (if MODIFY)
- Preliminary category
- Category guidance loaded

### Error Handling

| Failure | Handling |
|---------|----------|
| discover_skills.py fails | Warn, proceed without duplicate check |
| Category confidence <60% | Ask user to clarify |
| Near-duplicate found but user insists | Allow with differentiation requirement |
| Target skill not found (MODIFY) | Fuzzy match suggestions, allow explicit path |

---

## 6. Phase 1 - Analysis

**Purpose:** Deep understanding of requirements, decisions captured in analysis notes.

### Inputs

- Goal
- Routing decision (CREATE / MODIFY)
- Existing skill content (if MODIFY)
- Category guidance

### Steps

1. **Requirements discovery / Gap analysis**
   - For CREATE: Expand goal into explicit, implicit, and discovered requirements
   - For MODIFY: Analyze gap between current state and goal state

2. **Apply 11 thinking models**

   | Model | Core Question |
   |-------|---------------|
   | First Principles | What's fundamentally needed? |
   | Inversion | What guarantees failure? |
   | Second-Order | What happens after the obvious? |
   | Pre-Mortem | Why would this fail in 6 months? |
   | Systems Thinking | How do parts interact? |
   | Devil's Advocate | Strongest counter-argument? |
   | Constraints | What's truly fixed vs assumed? |
   | Pareto | Which 20% delivers 80%? |
   | Root Cause | Why is this needed? (5 Whys) |
   | Comparative | How do options compare? |
   | Opportunity Cost | What are we giving up? |

   Requirement: All 11 scanned, at least 5 applied in depth.

3. **Regression questioning** (max 7 rounds)
   - "What am I missing?"
   - "What would an expert add?"
   - "What would make this fail?"
   - Terminate after 3 consecutive rounds with no new insights

4. **Category validation**
   - Does analysis confirm preliminary category?
   - If category changes: Reload guidance, do targeted gap-fill for new failure modes

5. **Risk tier assignment**
   - Low / Medium / High based on blast radius and reversibility
   - If uncertain: Default to higher tier
   - Document reasoning

6. **STOP trigger identification**
   - Minimum 1 STOP trigger required
   - Default: "STOP if required inputs missing or ambiguous"
   - Category-specific STOPs (e.g., security skills need approval gates)

7. **Automation analysis**
   - Does this skill need scripts?
   - What kind: validation, generation, state management?
   - If unclear: Default to no scripts, flag for Phase 4 review

8. **For MODIFY: Scope assessment**
   - What's changing?
   - What dependencies are affected?
   - Any additional issues discovered? → Present to user, get scope decision

### Outputs

Analysis notes (markdown document):

```markdown
## Analysis Notes

### Classification
- Category: [category] (confidence: X%)
- Risk Tier: [Low/Medium/High]
- Rationale: [why]

### Requirements
- Explicit: [what user asked]
- Implicit: [expected but unstated]
- Discovered: [found through analysis]

### Key Decisions
- [Decision]: [choice made]
  → Why: [rationale]

### STOP Triggers
- [Trigger 1]
- [Trigger 2]

### Scripts Decision
- Needed: [Yes/No]
- Types: [validation, generation, etc.]
- Rationale: [why]

### For MODIFY
- Current State: [summary]
- Change Scope: [what's changing]
- Dependencies Affected: [list]
```

### Error Handling

| Failure | Handling |
|---------|----------|
| Regression questioning doesn't converge | Cap at 7 rounds, proceed with best insights |
| Category changes after validation | Reload guidance, gap-fill for new failure modes |
| Risk tier unclear | Default higher, document uncertainty |
| No STOP triggers identified | Require minimum 1, suggest "missing inputs" default |

---

## 7. Phase 2 - Generation

**Purpose:** Generate complete target SKILL.md following hybrid structure.

### Inputs

- Analysis notes
- Category guidance
- Existing skill content (if MODIFY)

### Steps

1. **Generate frontmatter**

   ```yaml
   ---
   name: [kebab-case, ≤64 chars]
   description: [≤1024 chars, no < >]
   license: MIT
   metadata:
     version: "1.0.0"
     model: claude-opus-4-5-20251101
     category: [from analysis]
     timelessness_score: null  # Set after Phase 4 approval
   ---
   ```

2. **Generate 11 hybrid sections**

   | Section | Key considerations |
   |---------|-------------------|
   | Triggers | 3-5 natural language phrases, varied phrasing |
   | When to use | Clear activation conditions from analysis |
   | When NOT to use | Anti-goals, exclusions, category-specific boundaries |
   | Inputs | Required vs optional, declared assumptions |
   | Outputs | Artifacts with objective Definition of Done |
   | Procedure | Numbered steps, decision points embedded, STOP gates placed |
   | Verification | Quick check with expected result pattern |
   | Troubleshooting | Category failure modes + procedure-specific issues |
   | Anti-Patterns | Execution guardrails (what to avoid while running) |
   | Extension Points | How skill can evolve (minimum 2) |
   | References | Links to supporting docs |

3. **Design STOP gates** (informed by Phase 1 triggers)
   - Place in Procedure at identified trigger points
   - Use template: "**STOP.** Ask the user for: [X]. **Do not proceed** until provided."

4. **Apply semantic quality dimensions** (universal)

   | Dimension | Check |
   |-----------|-------|
   | Intent fidelity | Primary goal clear, 3+ non-goals explicit |
   | Constraint completeness | Allowed/Forbidden explicit |
   | Terminology clarity | Key terms defined once |
   | Evidence anchoring | Claims cite sources |
   | Decision sufficiency | Decisions reference observable signals |
   | Verification validity | Quick check measures primary success |
   | Artifact usefulness | Output format specified |
   | Minimality | Smallest correct scope |
   | Calibration | Uncertainty labeled |

5. **Apply category-specific guidance** (specialized)
   - Category failure modes addressed in Troubleshooting
   - Category verification strictness reflected in Verification
   - Category risk defaults honored

6. **Design scripts if needed** (per Phase 1 decision)
   - Use `script-template.py` as base
   - Include Result dataclass pattern
   - Document in skill's References section

7. **For MODIFY: Preserve what's working**
   - Don't rewrite sections that don't need change
   - Maintain existing design intent where possible
   - Flag any breaking changes

### Outputs

- Complete SKILL.md (in memory, not written yet)
- Scripts (if needed, in memory)

### Error Handling

| Failure | Handling |
|---------|----------|
| Can't satisfy all 11 sections | All 11 required. If genuinely impossible, return to Phase 1 to reassess scope. |
| Conflicting guidance | Category-specific overrides general, document conflict |
| Script design unclear | Default to no scripts, flag for Phase 4 review |

---

## 8. Phase 3 - Diff, Confirm & Validation

**Purpose:** User approval before write, then deterministic validation.

### Inputs

- Generated SKILL.md (in memory)
- Generated scripts (if any, in memory)
- Existing skill content (if MODIFY)

### Steps

1. **Present changes for review**

   For CREATE:
   ```
   Generated skill: [skill-name]
   Location: [target path]

   [Full SKILL.md content]

   Write this skill? (y/n)
   ```

   For MODIFY:
   ```
   Modifying: [skill-name]

   Changes:
   [Diff view: additions in green, deletions in red]

   Files affected:
   - SKILL.md (modified)
   - scripts/validate.py (new)

   Apply these changes? (y/n)
   ```

2. **User confirms before any write**
   - No confirmation → Abort, no changes made
   - Confirmation → Proceed to write

3. **For MODIFY: Recommend git checkpoint**
   ```
   Recommended: Commit current state before modification
   git add [path] && git commit -m "Before skillsmith modification"

   Proceed? (y/n)
   ```

4. **Write atomically**
   - All files written together or none
   - SKILL.md + scripts + any new references
   - For MODIFY: Update existing files in place

5. **Run unified validator**
   ```bash
   python scripts/skill_lint.py [path/to/SKILL.md]
   ```

6. **Handle validation failures**

   | Attempt | Action |
   |---------|--------|
   | 1-2 | Fix specific issue, re-validate |
   | 3 | Return to Phase 1 with feedback (fundamental issue) |

7. **For MODIFY: Regression check**
   ```
   Baseline (before): 2 failures
   After modification: ? failures

   - New failures = REGRESSION (block, must fix)
   - Existing failures fixed = PROGRESS (good)
   - Existing failures remain = ACCEPTABLE (if out of scope)
   ```

### Outputs

- Validated SKILL.md on disk
- Validated scripts on disk (if any)
- Validation report

**Note:** `timelessness_score` remains `null` in frontmatter until Phase 4 approval.

### Error Handling

| Failure | Handling |
|---------|----------|
| User doesn't confirm | Abort cleanly, no state change |
| Write fails (permissions, etc.) | Report error, no partial writes |
| Validation fails 3x on same issue | Return to Phase 1 (design problem, not surface fix) |
| Regression detected | Block, require fix before proceeding |

---

## 9. Phase 4 - Review

**Purpose:** Multi-agent judgment on semantic quality and timelessness.

### Inputs

- Validated SKILL.md (on disk)
- Goal
- Analysis notes
- Diff (if MODIFY)

### Panel Composition

| Agent | Focus | Key Criteria |
|-------|-------|--------------|
| **Design Agent** | Structure, patterns, correctness | Pattern appropriate, phases logical, no contradictions |
| **Audience Agent** | Clarity, triggers, discoverability | Triggers natural, steps actionable, no assumed knowledge |
| **Evolution Agent** | Timelessness, extension, ecosystem | Score ≥7, extension points documented, principle-based |
| **Script Agent** | Script quality (if scripts present) | Patterns followed, self-verifying, documented |

### Holistic Review Approach

Agents don't "own" specific semantic dimensions. They use dimensions as shared vocabulary:

- Design, Audience, and Evolution agents review the full skill from their perspective
- These three agents use 9 semantic dimensions to describe issues
- Script Agent uses script-specific criteria (patterns, self-verification, documentation) and only runs when scripts are present
- Any critical semantic violation from any agent → FAIL

### Spec Consultation Triggers

Agents consult spec documents for specific decisions (not upfront loading):

| Trigger | Agent loads |
|---------|-------------|
| Assigning risk tier | `spec/skills-as-prompts-strict-spec.md#risk-tiers` |
| Validating category | `spec/skills-categories-guide.md#category-{name}` |
| Checking semantic dimension | `spec/skills-semantic-quality-addendum.md#dimension-{x}` |
| Scoring timelessness | `analysis/evolution-scoring.md` |
| Borderline FAIL code | `spec/skills-as-prompts-strict-spec.md#fail-{code}` |

Rule: Agents must cite spec section in review output. No cite = no claim.

### Two-Tier Quality Gates

```
Tier 1 (Primary): Semantic Quality
  → Design Agent reviews holistically
  → Audience Agent reviews holistically
  → Evolution Agent reviews holistically
  → All three use 9 dimensions as vocabulary for flagging issues
  → Script Agent (if scripts present) reviews code quality separately
  → Any critical semantic violation from any agent → FAIL

Tier 2 (Secondary): Timelessness
  → Evolution Agent scores ≥7 (this IS a dedicated responsibility)
```

### Agent Review Format

```markdown
## [Agent Name] Review

### Verdict: APPROVED / CHANGES_REQUIRED

### Scores
| Criterion | Score (1-10) | Notes |
|-----------|--------------|-------|

### Strengths
- [Specific with evidence]

### Issues (if CHANGES_REQUIRED)
| Issue | Severity | Required Change |
|-------|----------|-----------------|

### Spec Citations
- [Decision]: [spec section referenced]
```

### Consensus Protocol

| Outcome | Action |
|---------|--------|
| All agents APPROVED | Finalize skill, complete |
| Any agent CHANGES_REQUIRED (iteration 1-4) | Collect issues, return to Phase 1 with feedback |
| No consensus after 5 iterations | Escalate to human with full context |

### Human Escalation Format

```
Panel could not reach consensus after 5 iterations.

Disagreement summary:
- Design Agent: APPROVED (8/10)
- Audience Agent: CHANGES_REQUIRED - [issue]
- Evolution Agent: APPROVED (7/10)

Options:
- A: Accept with noted concerns
- B: Address feedback, re-review
- C: Reject, rethink approach

Your decision:
```

### Outputs

- APPROVED skill, or
- Feedback for iteration, or
- Human escalation with context

### Post-Approval: Score Persistence

After panel approval:

1. Evolution Agent's timelessness score is final
2. Update SKILL.md frontmatter: replace `timelessness_score: null` with actual score
3. Notify user:
   ```
   ✓ Skill approved (timelessness: 8/10)
   Updated: path/to/SKILL.md
   ```
4. No additional confirmation required (content was already approved in Phase 3)

### Error Handling

| Failure | Handling |
|---------|----------|
| Agent can't load spec section | Use baked-in criteria, warn about degraded confidence |
| Timelessness score borderline (6-6.9) | Strict fail, require specific improvements |
| Panel disagrees after 5 iterations | Human breaks tie |
| Validator passed but panel fails | Return to Phase 1 (semantic issue needs rethinking) |

---

## 10. Unified Validator

**Purpose:** Single deterministic validator combining checks from both sources.

**Location:** `scripts/skill_lint.py`

### Invocation

```bash
# CLI
python scripts/skill_lint.py path/to/SKILL.md
python scripts/skill_lint.py --json path/to/SKILL.md

# Module (within workflow)
from skill_lint import lint_skill, LintResult
result: LintResult = lint_skill(path)

# Command
/lint-skill path/to/SKILL.md
```

### Check Categories

**1. Frontmatter checks** (from validate-skill.py)

| Check | Requirement |
|-------|-------------|
| `name` present | Required |
| `name` format | kebab-case, ≤64 characters |
| `description` present | Required |
| `description` format | ≤1024 characters, no `<` or `>` |
| Allowed properties only | name, description, license, allowed-tools, metadata |

**2. Structural checks** (from skill_lint.py - 8 FAIL codes)

| FAIL Code | Check |
|-----------|-------|
| `FAIL.missing-content-areas` | 8 core sections present |
| `FAIL.no-objective-dod` | Outputs have checkable Definition of Done |
| `FAIL.no-stop-ask` | At least 1 STOP/ask gate |
| `FAIL.no-quick-check` | Verification has quick check + expected result |
| `FAIL.too-few-decision-points` | 2+ if/then/otherwise branches |
| `FAIL.non-operational-procedure` | Procedure has numbered steps |
| `FAIL.undeclared-assumptions` | Assumptions declared (tools, network, permissions) |
| `FAIL.unsafe-default` | Risky commands gated with ask-first |

**3. Hybrid structure checks** (new - 3 FAIL codes)

| FAIL Code | Check |
|-----------|-------|
| `FAIL.no-triggers` | Triggers section present with ≥3 phrases |
| `FAIL.no-anti-patterns` | Anti-Patterns section present with ≥1 item |
| `FAIL.no-extension-points` | Extension Points section present with ≥2 points |

**4. Script checks** (from validate-skill.py, if `scripts/` exists)

| Check | Requirement |
|-------|-------------|
| Scripts documented | Each script mentioned in SKILL.md |
| Exit codes documented | Exit code meanings specified |
| Shebang present | `#!/usr/bin/env python3` |
| Result pattern | Uses Result/ValidationResult dataclass |

### Output Format

```
Validating: path/to/SKILL.md

FRONTMATTER
  ✓ name: valid (my-skill)
  ✓ description: valid (45 chars)

STRUCTURE
  ✓ 8 core content areas present
  ✓ Objective DoD found
  ✓ STOP gate found (line 67)
  ✓ Quick check found (line 89)
  ✓ 3 decision points found
  ✓ Numbered procedure (12 steps)
  ✓ Assumptions declared
  ✓ No unsafe defaults

HYBRID
  ✓ Triggers: 4 phrases (min: 3)
  ✓ Anti-Patterns: 2 items (min: 1)
  ✓ Extension Points: 3 documented (min: 2)

SCRIPTS
  ✓ validate.py documented
  ✓ Exit codes specified

RESULT: PASS (0 failures, 0 warnings)
```

### Exit Codes

- `0` — All checks pass
- `1` — At least one FAIL code triggered

---

## 11. Quality Model

**Purpose:** Define what "good" means for a skill—beyond just valid structure.

### Two-Tier Model

```
┌─────────────────────────────────────────────────┐
│ Tier 1: SEMANTIC QUALITY (Primary Gate)         │
│                                                 │
│ Evaluated by: Design + Audience + Evolution     │
│ Method: Holistic review using shared vocabulary │
│ Pass condition: No critical violations          │
│ (Script Agent reviews separately if present)    │
└─────────────────────────────────────────────────┘
                      │
                      │ (only if Tier 1 passes)
                      ▼
┌─────────────────────────────────────────────────┐
│ Tier 2: TIMELESSNESS (Secondary Gate)           │
│                                                 │
│ Evaluated by: Evolution Agent                   │
│ Method: Temporal projection, extension analysis │
│ Pass condition: Score ≥7/10                     │
└─────────────────────────────────────────────────┘
```

### 11a. Tier 1 - Semantic Quality

**Purpose:** Ensure the skill will execute correctly and prevent agent drift.

**Core question:** "Will this skill do the right thing when invoked?"

#### The 9 Dimensions

| Dimension | Question | Anti-pattern |
|-----------|----------|--------------|
| Intent fidelity | Is the primary goal clear in 1-2 sentences? | Proxy goals ("improve quality") without observable signals |
| Constraint completeness | Are allowed/forbidden actions explicit? | Making unsafe changes, guessing constraints |
| Terminology clarity | Are key terms defined once and used consistently? | Ambiguous nouns ("deploy", "artifact") |
| Evidence anchoring | Do claims cite sources? | Hallucinated facts, unjustified conclusions |
| Decision sufficiency | Do decisions reference observable signals? | "Use judgment" without criteria |
| Verification validity | Does quick check measure the primary success property? | Checking proxy (compilation) not goal (correctness) |
| Artifact usefulness | Is output format specified and tailored to consumer? | Outputs exist but aren't actionable |
| Minimality | Is this the smallest correct scope? | Gold-plating, unnecessary refactors |
| Calibration | Is uncertainty labeled (Verified/Inferred/Assumed)? | Overconfident claims, silent skipping |

#### How Agents Use Dimensions

Agents don't "own" dimensions. They use dimensions as vocabulary to describe issues:

```markdown
## Design Agent Review

### Issues Found
| Dimension | Issue | Severity |
|-----------|-------|----------|
| Decision sufficiency | Step 4 says "choose appropriate method" without criteria | Major |
| Constraint completeness | No forbidden actions specified | Minor |
```

**Note:** Script Agent does not use semantic dimensions. It reports script-specific issues (pattern violations, missing documentation, verification gaps) in its own format.

#### Severity Classification

| Severity | Meaning | Impact |
|----------|---------|--------|
| Critical | Skill will likely produce wrong results | Automatic FAIL |
| Major | Significant quality gap, workaround exists | 2+ Major = FAIL |
| Minor | Improvement opportunity, non-blocking | Noted, doesn't block |

#### Tier 1 Passes When

- Zero critical semantic violations from any agent
- Fewer than 2 major violations per agent
- Issues documented for future improvement

### 11b. Tier 2 - Timelessness

**Purpose:** Ensure the skill will remain valuable over time.

**Core question:** "Will this skill still be useful in 2 years?"

#### Scoring Rubric

| Score | Grade | Lifespan | Characteristics |
|-------|-------|----------|-----------------|
| 1-2 | Ephemeral | Weeks-months | Tied to specific version, no extension points |
| 3-4 | Short-lived | 6mo-1yr | Depends on current tooling, minimal abstraction |
| 5-6 | Moderate | 1-2 years | Some principles, but hardcoded dependencies |
| **7-8** | **Solid** | **2-4 years** | **Principle-based, documented extension points** |
| 9-10 | Timeless | 5+ years | Addresses fundamental problem, fully extensible |

**Minimum threshold: 7** — No exceptions without human override.

#### Evaluation Criteria

| Criterion | Check |
|-----------|-------|
| Principle-based design | Not hardcoded to specific tools/versions |
| Extension points | Minimum 2 documented |
| Dependency stability | Volatile dependencies abstracted |
| Temporal projection | Considered 6mo, 1yr, 2yr horizons |
| WHY documented | Rationale for key decisions included |

#### Anti-Patterns

- ❌ "Use Claude 3.5 Sonnet" (hardcoded model)
- ✓ "Use recommended model" (version-agnostic)
- ❌ "ESLint 8 config format" (version-specific)
- ✓ "Linting config for JavaScript" (tool-agnostic pattern)

#### Borderline Handling (6.0-6.9)

Score in this range = FAIL with specific improvement requirements.

```
Timelessness score: 6.5/10 (required: ≥7)

To reach ≥7, address:
1. Add second extension point (currently only 1)
2. Abstract hardcoded reference to "gpt-4" in Procedure step 3
3. Document WHY for architecture decision in Analysis section

Estimated impact: +0.5 to +1.0
```

No "rounding up" or "close enough." 6.9 fails just like 3.0.

---

## 12. Component Interaction

### Components

| Component | Type | Path |
|-----------|------|------|
| skillsmith | Skill | `skills/skillsmith/SKILL.md` |
| create-skill | Command | `commands/create-skill.md` |
| review-skill | Command | `commands/review-skill.md` |
| lint-skill | Command | `commands/lint-skill.md` |
| design-agent | Agent | `agents/design-agent.md` |
| audience-agent | Agent | `agents/audience-agent.md` |
| evolution-agent | Agent | `agents/evolution-agent.md` |
| script-agent | Agent | `agents/script-agent.md` |
| skill_lint.py | Script | `scripts/skill_lint.py` |
| discover_skills.py | Script | `scripts/discover_skills.py` |

### Interaction Diagram

```
User input
    │
    ├─→ /create-skill ────→ /skillsmith (full workflow)
    │        │
    │        └─→ Phases 0-4
    │              │
    │              ├─→ discover_skills.py (Phase 0)
    │              ├─→ skill_lint.py (Phase 3)
    │              └─→ Panel agents (Phase 4)
    │
    ├─→ /review-skill ────→ Phase 3 + Phase 4 only
    │        │
    │        ├─→ skill_lint.py
    │        └─→ Panel agents
    │
    ├─→ /lint-skill ──────→ skill_lint.py only
    │
    └─→ Direct agent invocation (via Task tool)
             │
             └─→ Any single agent for specific review
```

### Command Specifications

**`/create-skill`** — Alias to skillsmith for full skill creation

**`/review-skill`** — Standalone review (Phase 3 + Phase 4) on existing skill

**`/lint-skill`** — Validation only, no panel review

### Standalone Agent Invocation

Agents can be invoked via Task tool for specific purposes:

| Use case | Invocation |
|----------|------------|
| Just check timelessness | Invoke evolution-agent on skill |
| Just check usability | Invoke audience-agent on skill |
| Review scripts only | Invoke script-agent on skill |
| Technical architecture review | Invoke design-agent on skill |

---

## 13. Error Handling Summary

### Defaults

| Parameter | Value |
|-----------|-------|
| Max regression questioning rounds | 7 |
| Max validation iterations | 3 |
| Max panel iterations | 5 |
| Category confidence threshold | 60% |
| Timelessness score threshold | ≥7 (strict) |
| Minimum STOP triggers | 1 |
| Hybrid section thresholds | Triggers ≥3, Anti-Patterns ≥1, Extension Points ≥2 |

### Phase 0 (Triage) Failures

| Failure | Handling |
|---------|----------|
| Can't determine routing | Ask user with structured options |
| Category confidence <60% | Present top 2-3 candidates, let user choose |
| discover_skills.py fails | Warn and proceed without duplicate check |
| Near-duplicate found | Allow with differentiation requirement |
| Target skill not found (MODIFY) | Fuzzy match suggestions, allow explicit path |
| Plugin skill (read-only) | Offer fork or upstream contribution |

### Phase 1 (Analysis) Failures

| Failure | Handling |
|---------|----------|
| Regression questioning doesn't converge | Cap at 7 rounds, proceed with best insights |
| Category changes after validation | Reload guidance, targeted gap-fill |
| Risk tier unclear | Default to higher tier, document uncertainty |
| No STOP triggers identified | Require minimum 1, suggest default |
| Conflicting goals | Detect and ask user to clarify priority |

### Phase 2 (Generation) Failures

| Failure | Handling |
|---------|----------|
| Can't satisfy all 11 sections | All 11 required. See Section 10 for thresholds. |
| Conflicting guidance | Category-specific overrides general, document conflict |
| Script design unclear | Default to no scripts, flag for Phase 4 review |

### Phase 3 (Validation) Failures

| Failure | Handling |
|---------|----------|
| User doesn't confirm | Abort cleanly, no state change |
| Write fails | Report error, no partial writes |
| Validation fails (attempt 1-2) | Fix specific issue, re-validate |
| Validation fails (attempt 3+) | Return to Phase 1 with feedback |
| Regression detected (MODIFY) | Block, require fix before proceeding |

### Phase 4 (Review) Failures

| Failure | Handling |
|---------|----------|
| Agent can't load spec section | Use baked-in criteria, warn |
| Timelessness 6.0-6.9 | Strict fail, require specific improvements |
| Critical semantic violation | FAIL, return to Phase 1 with feedback |
| Panel disagrees (iterations 1-4) | Collect issues, return to Phase 1 |
| Panel disagrees (iteration 5) | Escalate to human with full context |

### Escalation Path

```
Phase fails repeatedly
         │
         ▼
Can fix with targeted changes? ──→ Yes ──→ Fix and retry
         │
         No
         ▼
Fundamental issue? ──→ Yes ──→ Loop to earlier phase with feedback
         │
         No / Still failing
         ▼
Human escalation ──→ Present situation, get decision
```

---

## 14. Migration Overview

*Detailed step-by-step migration is in the separate migration plan document.*

### Source Projects

| Project | Location | Status after migration |
|---------|----------|------------------------|
| skill-documentation | `/skill-documentation/` | Archived to `old-repos/` |
| skillforge | `.claude/skills/skillforge/` | Deprecated, then deleted |

### Target

```
packages/plugins/skillsmith/
```

### Migration Phases

| Phase | Description | Effort |
|-------|-------------|--------|
| 1. Setup | Create plugin structure, plugin.json, README | Low |
| 2. Copy references | Move spec docs and analysis refs | Low |
| 3. Create new files | spec-index, merged workflow doc, templates | Medium |
| 4. Validator merge | Combine skill_lint.py + validate-skill.py checks | High |
| 5. Panel agents | Create 4 agent definition files | Medium |
| 6. Main skill | Write SKILL.md with unified workflow | High |
| 7. Commands | Create 3 command files | Low |
| 8. Testing | Validation, regression, end-to-end | Medium |
| 9. Cleanup | Deprecate old, archive sources | Low |

### What Gets Copied, Created, Merged, Dropped

**Copied directly:** All spec docs, analysis refs, discover_skills.py, script-template.py

**Created new:** plugin.json, README.md, SKILL.md, spec-index.md, merged-creation-workflow.md, templates, agent files, command files

**Merged:** skill_lint.py + validate-skill.py checks → unified validator

**Dropped:** XML specification format, validate-skill.py, quick_validate.py

### Success Criteria

| Criterion | Verification |
|-----------|--------------|
| Plugin installs | `claude plugin install skillsmith@tool-dev` succeeds |
| Validator works | `python scripts/skill_lint.py` passes on test skills |
| Workflow runs | `/skillsmith create a test skill` completes |
| Review works | `/review-skill` runs panel on existing skill |

*Note: skillsmith sets a new quality standard. Existing skills are expected to require updates to pass the unified validator.*

---

## 15. Open Questions / Future Work

### Deferred for Later Implementation

| Item | Description | Why deferred |
|------|-------------|--------------|
| Domain annexes integration | Full integration of meta-skills, auditing, agentic pipeline annexes | Adds complexity; core workflow works without |
| Skill composition | Combining multiple skills into workflows | Separate concern; skillsmith focuses on single skills |
| Skill versioning | Tracking skill versions and migrations | Operational concern; git handles this for now |
| Automated spec sync | Auto-regenerate agent prompts when spec updates | Maintenance optimization; manual sync acceptable initially |

### Open Questions

| Question | Context | Impact |
|----------|---------|--------|
| Should skillsmith create its own skills? | Meta-circularity—skillsmith improving itself | Low; can use existing skillforge until stable |
| How to handle very large skills? | Skills >1000 lines may need different treatment | Medium; rare case, address when encountered |
| Panel agent model selection | Should agents use same model or mix? | Low; default to opus, allow override later |
| Skill metrics/telemetry | Track skill usage, success rates | Future enhancement; not needed for MVP |

### Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| `/improve-skill` command | Dedicated command for MODIFY flow (alias) | Low |
| Batch validation | Validate entire skills directory at once | Medium |
| Skill templates by category | Pre-populated templates for each of 13 categories | Medium |
| Integration with promote script | Auto-promote skills that pass review | Medium |
| Relaxed mode | Lighter validation for drafts/WIP skills | Low |

---

## 16. Glossary

| Term | Definition |
|------|------------|
| **Analysis notes** | Markdown document output from Phase 1 capturing decisions, rationale, and classification |
| **Category** | One of 13 skill types with specific failure modes and verification requirements |
| **Decision point** | Explicit if/then/otherwise branch in a skill's procedure |
| **Domain annex** | Category-specific guidance beyond the base spec |
| **Extension point** | Documented mechanism for extending a skill's capabilities |
| **FAIL code** | One of 11 deterministic failure conditions checked by the validator (8 structural + 3 hybrid) |
| **Holistic review** | Panel agents reviewing the full skill using semantic dimensions as shared vocabulary |
| **Hybrid structure** | The 11-section skill format combining skill-documentation's 8 + skillforge's 3 |
| **Panel** | The 3-4 agents that review skills in Phase 4 |
| **Risk tier** | Low/Medium/High classification affecting required safety gates |
| **Routing decision** | Phase 0 output: CREATE, MODIFY, or USE_EXISTING |
| **Semantic quality** | The 9 dimensions measuring skill correctness and agent drift prevention |
| **Spec consultation** | Agents loading specific spec sections via explicit triggers during review |
| **STOP gate** | Point in procedure where skill must pause and ask user |
| **Timelessness** | Quality measure (1-10) of how well a skill will age; ≥7 required |
| **Triage** | Phase 0 process determining routing, category, and loading context |
| **Two-tier quality** | Primary gate (semantic quality) + secondary gate (timelessness) |
| **Unified validator** | Single linter combining checks from both source projects |

### Acronyms

| Acronym | Meaning |
|---------|---------|
| DoD | Definition of Done |
| FAIL | Deterministic failure code |
| MODIFY | Routing decision to improve existing skill |
| CREATE | Routing decision to create new skill |
| USE_EXISTING | Routing decision to recommend existing skill |

---

## 17. References

### Source Projects

| Project | Location |
|---------|----------|
| skill-documentation | `/Users/jp/Projects/active/claude-code-tool-dev/skill-documentation/` |
| skillforge | `/Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/skillforge/` |

### Source Documents (skill-documentation)

| Document | Size | Purpose |
|----------|------|---------|
| `skills-as-prompts-strict-spec.md` | 59KB | Source of truth—8 sections, 8 FAIL codes, risk tiers |
| `skills-categories-guide.md` | 67KB | 13 categories with failure modes |
| `skills-semantic-quality-addendum.md` | 17KB | 9 semantic quality dimensions |
| `skills-domain-annexes.md` | 14KB | Domain-specific invariants |
| `skills-authoring-review-pipeline.md` | 3KB | Original 6-step workflow |
| `how-to-author-review-one-pager.md` | 4KB | Condensed quick reference |
| `skill_lint.py` | 15KB | Linter implementing 8 FAIL codes |

### Source Documents (skillforge)

| Document | Purpose |
|----------|---------|
| `SKILL.md` | Main skill definition |
| `references/regression-questions.md` | 7 question categories |
| `references/multi-lens-framework.md` | 11 thinking models |
| `references/evolution-scoring.md` | Timelessness rubric |
| `references/synthesis-protocol.md` | Panel review process |
| `references/script-integration-framework.md` | Script creation guidance |
| `references/script-patterns-catalog.md` | Python patterns |
| `scripts/validate-skill.py` | Full structural validation |
| `scripts/quick_validate.py` | Packaging validation |
| `scripts/discover_skills.py` | Ecosystem skill index |

### External References

| Reference | Purpose |
|-----------|---------|
| Claude Code Plugin Reference | Plugin structure and manifest schema |

### Related Skills

| Skill | Relationship |
|-------|--------------|
| deep-exploration | Could inform Phase 1 analysis |
| deep-synthesis | Sibling skill for multi-source synthesis |
| brainstorming | Used to design skillsmith |

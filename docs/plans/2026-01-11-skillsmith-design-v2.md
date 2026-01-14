# skillsmith Design Document v2

> Unified Claude Code plugin for creating, validating, and reviewing skills.

**Date:** 2026-01-11
**Status:** Ready for implementation
**Based on:** Brainstorming session refining 2026-01-09-skillsmith-design.md

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Plugin Structure](#2-plugin-structure)
3. [Hybrid Skill Structure (Spec v2.0)](#3-hybrid-skill-structure-spec-v20)
4. [Workflow Overview](#4-workflow-overview)
5. [Phase 0 (Triage) & Phase 1 (Analysis)](#5-phase-0-triage--phase-1-analysis)
6. [Phase 2 (Generation) & Phase 3 (Validation)](#6-phase-2-generation--phase-3-validation)
7. [Phase 4 (Review Panel)](#7-phase-4-review-panel)
8. [Unified Validator](#8-unified-validator)
9. [Quality Model](#9-quality-model)
10. [Commands](#10-commands)
11. [Agent Definitions](#11-agent-definitions)
12. [Error Handling Summary](#12-error-handling-summary)
13. [Migration Overview](#13-migration-overview)
14. [Open Questions & Future Work](#14-open-questions--future-work)

---

## 1. Executive Summary

**skillsmith** is a unified Claude Code plugin for creating, validating, and reviewing skills. It merges two existing projects and defines **Skill Spec v2.0**.

### What it replaces

- **skill-documentation**: Normative spec (~170KB, 8 sections, 8 FAIL codes) — already archived
- **skillforge**: Creation workflow (~870 lines, 5 phases, multi-agent review)

### The problem

These projects overlap but conflict. A skill passing one validator might fail the other.

### skillsmith resolution

- **Spec v2.0**: 11 required sections (8 original + Triggers, Anti-Patterns, Extension Points)
- **11 FAIL codes**: Extended from 8 to enforce new sections
- **Timelessness gate**: Score ≥7 mandatory (new requirement)
- **Unified validator**: Single linter combining all checks
- **4-agent review panel**: Design, Audience, Evolution, Script (all opus, unanimous approval)

### Core capability

Given any skill-related request, skillsmith:

1. Triages to CREATE, MODIFY, or USE_EXISTING
2. Analyzes with category-aware multi-lens depth
3. Generates skills following 11-section structure
4. Validates with unified linter
5. Reviews via parallel 4-agent panel with unanimous approval

### Bootstrapping

Initial skillsmith created by hand following existing specs (`skills-as-prompts-strict-spec.md`, `skills-semantic-quality-addendum.md`, `.claude/rules/skills.md`). Self-maintaining thereafter.

**Target audience**: Claude itself — optimized for AI-driven skill creation with humans as reviewers.

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
│       ├── references/
│       │   ├── INDEX.md
│       │   ├── strict-spec.md
│       │   ├── categories-guide.md
│       │   ├── semantic-quality.md
│       │   ├── domain-annexes.md
│       │   ├── creation-workflow.md
│       │   ├── authoring-pipeline.md
│       │   ├── one-pager.md
│       │   ├── regression-questions.md
│       │   ├── multi-lens.md
│       │   ├── evolution-scoring.md
│       │   ├── synthesis-protocol.md
│       │   ├── script-framework.md
│       │   └── script-patterns.md
│       └── templates/
│           ├── skill-template.md
│           ├── analysis-notes.md
│           └── script-template.py
│
├── scripts/
│   ├── skill_lint.py
│   ├── discover_skills.py
│   └── tests/
│
├── commands/
│   ├── create.md
│   ├── review.md
│   └── lint.md
│
├── README.md
├── LICENSE
└── CHANGELOG.md
```

**Key design decisions:**

- References flattened to one level with INDEX.md for navigation
- Commands namespaced (`/skillsmith:create`, `/skillsmith:review`, `/skillsmith:lint`)
- Shorter reference file names for cleaner imports

---

## 3. Hybrid Skill Structure (Spec v2.0)

Skills created by skillsmith follow an **11-section structure** with required frontmatter.

### Frontmatter (required)

```yaml
---
name: skill-name                    # Required: kebab-case, ≤64 chars
description: One-line description   # Required: ≤1024 chars, no < or >
license: MIT                        # Optional
allowed-tools: ["Tool1", "Tool2"]   # Optional
metadata:
  version: "1.0.0"
  model: claude-opus-4-5-20251101
  timelessness_score: 8             # Set after Phase 4 approval
  category: debugging-triage
---
```

### Body Sections (11 required)

| # | Section | Source | Purpose |
|---|---------|--------|---------|
| 1 | **Triggers** | NEW | 3-5 natural language invocation phrases |
| 2 | **When to use** | spec v1 | Activation conditions and boundaries |
| 3 | **When NOT to use** | spec v1 | Anti-goals, exclusions, STOP conditions |
| 4 | **Inputs** | spec v1 | Required/optional inputs, declared assumptions |
| 5 | **Outputs** | spec v1 | Artifacts with objective Definition of Done |
| 6 | **Procedure** | spec v1 | Numbered steps with embedded decision points |
| 7 | **Verification** | spec v1 | Quick check with expected result |
| 8 | **Troubleshooting** | spec v1 | Failure modes with symptoms/causes/recovery |
| 9 | **Anti-Patterns** | NEW | What to avoid during execution |
| 10 | **Extension Points** | NEW | How the skill can evolve (minimum 2) |
| 11 | **References** | both | Links to supporting docs (optional but recommended) |

### Enforcement

- Sections 1-10: FAIL if missing
- Section 11: Recommended, not enforced
- Decision points: 2+ required (embedded in Procedure)
- STOP gates: 1+ required

---

## 4. Workflow Overview

Single unified workflow for both CREATE and MODIFY. The distinction emerges from triage.

### Core Principle

Every request is "achieve goal given current state." For CREATE, current state is empty. For MODIFY, current state is the existing skill.

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
      Phase 4: Review (4-agent panel, parallel)
            │         │
            │         └─→ Rejected 5x ──→ Human escalation
            ▼
         APPROVED ──→ Update timelessness score ──→ Done
```

### Routing Decisions

| Match | Intent | Route |
|-------|--------|-------|
| ≥80% existing skill | Any | USE_EXISTING or CLARIFY |
| 50-79% match | Improve | MODIFY |
| 50-79% match | Create | CLARIFY (similar exists) |
| <50% match | Create | CREATE |
| <50% match | Improve | Not found (clarify) |

### Key Design Choices

- No artificial tiering (scope emerges from analysis)
- Diff + confirm before any writes
- Iteration caps prevent infinite loops
- Human escalation as final fallback

---

## 5. Phase 0 (Triage) & Phase 1 (Analysis)

### Phase 0: Triage

**Purpose:** Determine routing, load context, set up for analysis.

**Steps:**

1. Parse goal to understand intent (create, improve, question)
2. Scan ecosystem via `discover_skills.py` for existing skills
3. Determine routing (CREATE / MODIFY / USE_EXISTING)
4. For MODIFY: Load existing skill and inventory dependencies
5. Preliminary category assignment (13 categories)
6. Load category-specific guidance

**Outputs:** Routing decision, existing content (if MODIFY), preliminary category

### Phase 1: Analysis

**Purpose:** Deep understanding of requirements captured in analysis notes.

**Steps:**

1. Requirements discovery / gap analysis
2. Apply 11 thinking models (all scanned, 5+ in depth)
3. Regression questioning (max 7 rounds, terminate after 3 with no new insights)
4. Category validation (reload guidance if category changes)
5. Risk tier assignment (Low/Medium/High; default higher if uncertain; mutation → High)
6. STOP trigger identification (minimum 1 required)
7. Automation analysis (does skill need scripts?)
8. For MODIFY: Scope assessment

**Outputs:** Analysis notes markdown with classification, requirements, key decisions, STOP triggers, scripts decision

**Error handling:**

- Regression questioning capped at 7 rounds
- Risk tier defaults to higher when uncertain
- Minimum 1 STOP trigger required (suggest "missing inputs" default)

---

## 6. Phase 2 (Generation) & Phase 3 (Validation)

### Phase 2: Generation

**Purpose:** Generate complete SKILL.md following 11-section hybrid structure.

**Key change from skillforge:** No XML specification intermediate. Generate SKILL.md directly.

**Steps:**

1. Generate frontmatter (name, description, metadata with `timelessness_score: null`)
2. Generate all 11 sections using analysis notes and category guidance
3. Design STOP gates at identified trigger points
4. Apply 9 semantic quality dimensions
5. Apply category-specific guidance
6. Design scripts if needed (per Phase 1 decision)
7. For MODIFY: Preserve working sections, flag breaking changes

**Outputs:** Complete SKILL.md and scripts (in memory, not written yet)

### Phase 3: Diff, Confirm & Validation

**Purpose:** User approval before write, then deterministic validation.

**Steps:**

1. **Present changes for review**
   - CREATE: Show full SKILL.md, target path
   - MODIFY: Show diff (additions/deletions), files affected

2. **User confirms before any write**
   - No confirmation → Abort cleanly

3. **For MODIFY: Recommend git checkpoint**
   ```
   git add [path] && git commit -m "Before skillsmith modification"
   ```

4. **Write atomically** (all files together or none)

5. **Run unified validator**
   ```bash
   python scripts/skill_lint.py [path/to/SKILL.md]
   ```

6. **Handle validation failures**
   - Attempts 1-2: Fix specific issue, re-validate
   - Attempt 3: Return to Phase 1 (fundamental issue)

7. **For MODIFY: Regression check**
   - New failures = REGRESSION (block)
   - Existing failures fixed = PROGRESS
   - Existing failures remain = ACCEPTABLE (if out of scope)

**Outputs:** Validated SKILL.md on disk, validation report

**Note:** `timelessness_score` remains `null` until Phase 4 approval.

---

## 7. Phase 4 (Review Panel)

**Purpose:** Multi-agent judgment on semantic quality and timelessness.

### Panel Composition

**Always 4 agents, all opus:**

| Agent | Focus | Key Criteria |
|-------|-------|--------------|
| **Design Agent** | Structure, patterns, correctness | 11 sections present, FAIL codes clear, no contradictions |
| **Audience Agent** | Clarity, triggers, discoverability | Triggers natural, steps actionable, no assumed knowledge |
| **Evolution Agent** | Timelessness, extension, ecosystem | Score ≥7, extension points documented, principle-based |
| **Script Agent** | Scripts quality OR whether scripts should exist | Patterns followed, self-verifying, documented; flags missing automation |

### Orchestration

**Parallel Task tool invocation from main skill:**

1. Launch all 4 agents in parallel via Task tool
2. Each agent reviews full skill from their perspective
3. Agents return structured verdicts (APPROVED/CHANGES_REQUIRED)
4. Main skill synthesizes results

### Consensus Protocol

- **Unanimous required:** All 4 agents must return APPROVED
- **Any CHANGES_REQUIRED:** Collect issues, return to Phase 1 with feedback
- **5 iterations without consensus:** Escalate to human with full context

### Post-Approval

1. Evolution Agent's timelessness score is final
2. Update SKILL.md frontmatter: `timelessness_score: [actual score]`
3. Notify user: `✓ Skill approved (timelessness: 8/10)`

---

## 8. Unified Validator

**Purpose:** Single deterministic validator combining checks from both source projects.

**Location:** `scripts/skill_lint.py`

### Invocation

```bash
# CLI
python scripts/skill_lint.py path/to/SKILL.md
python scripts/skill_lint.py --json path/to/SKILL.md

# Command
/skillsmith:lint path/to/SKILL.md
```

### Check Categories

**1. Frontmatter checks (5)**

| Check | Requirement |
|-------|-------------|
| `name` present | Required, kebab-case, ≤64 chars |
| `description` present | Required, ≤1024 chars, no `<` or `>` |
| Allowed properties only | name, description, license, allowed-tools, metadata |

**2. Structural checks — 8 FAIL codes (from spec v1)**

| FAIL Code | Check |
|-----------|-------|
| `FAIL.missing-content-areas` | 8 core sections present |
| `FAIL.no-objective-dod` | Outputs have checkable Definition of Done |
| `FAIL.no-stop-ask` | At least 1 STOP/ask gate |
| `FAIL.no-quick-check` | Verification has quick check + expected result |
| `FAIL.too-few-decision-points` | 2+ if/then/otherwise branches |
| `FAIL.non-operational-procedure` | Procedure has numbered steps |
| `FAIL.undeclared-assumptions` | Assumptions declared |
| `FAIL.unsafe-default` | Risky commands gated with ask-first |

**3. Hybrid checks — 3 NEW FAIL codes (spec v2.0)**

| FAIL Code | Check |
|-----------|-------|
| `FAIL.no-triggers` | Triggers section present with ≥3 phrases |
| `FAIL.no-anti-patterns` | Anti-Patterns section present with ≥1 item |
| `FAIL.no-extension-points` | Extension Points section present with ≥2 points |

**4. Script checks (if `scripts/` exists)**

| Check | Requirement |
|-------|-------------|
| Scripts documented | Each script mentioned in SKILL.md |
| Exit codes documented | Exit code meanings specified |
| Shebang present | `#!/usr/bin/env python3` |
| Result pattern | Uses Result/ValidationResult dataclass |

### Exit Codes

- `0` — All checks pass
- `1` — At least one FAIL code triggered

---

## 9. Quality Model

**Purpose:** Define what "good" means — beyond just valid structure.

### Two-Tier Model

```
┌─────────────────────────────────────────────────┐
│ Tier 1: SEMANTIC QUALITY (Primary Gate)         │
│                                                 │
│ Evaluated by: All 4 agents holistically         │
│ Method: Review using 9 dimensions as vocabulary │
│ Pass condition: No critical violations          │
└─────────────────────────────────────────────────┘
                      │
                      │ (only if Tier 1 passes)
                      ▼
┌─────────────────────────────────────────────────┐
│ Tier 2: TIMELESSNESS (Secondary Gate)           │
│                                                 │
│ Evaluated by: Evolution Agent                   │
│ Method: Temporal projection, extension analysis │
│ Pass condition: Score ≥7/10 (mandatory)         │
└─────────────────────────────────────────────────┘
```

### Tier 1: 9 Semantic Quality Dimensions

| Dim | Name | What goes wrong |
|-----|------|-----------------|
| A | Intent Fidelity | Agent optimizes proxy goal or expands scope |
| B | Constraint Completeness | Agent guesses constraints, makes unsafe changes |
| C | Terminology Clarity | Ambiguous nouns cause wrong actions |
| D | Evidence Anchoring | Hallucinated facts, unjustified conclusions |
| E | Decision Sufficiency | "Use judgment" leads to inconsistent outcomes |
| F | Verification Validity | Checks don't measure intended property |
| G | Artifact Usefulness | Outputs not reviewable or actionable |
| H | Minimality Discipline | Gold-plating, sprawling refactors |
| I | Calibration Honesty | Overconfident claims, silent skipping |

**Critical for safety: B (Constraints), E (Decisions), F (Verification)**

**Scoring:** 0-2 per dimension. ≥14/18 with no 0s in B/E/F = "Excellent"

### Tier 2: Timelessness Scoring

| Score | Grade | Lifespan |
|-------|-------|----------|
| 1-2 | Ephemeral | Weeks-months |
| 3-4 | Short-lived | 6mo-1yr |
| 5-6 | Moderate | 1-2 years |
| **7-8** | **Solid** | **2-4 years** |
| 9-10 | Timeless | 5+ years |

**Threshold: ≥7 mandatory.** Score 6.0-6.9 = FAIL with specific improvement requirements. No rounding.

---

## 10. Commands

Three commands provide entry points to skillsmith functionality. All follow the plugin namespacing convention.

### `/skillsmith:create`

```markdown
---
description: Create a new skill using skillsmith's 5-phase workflow
argument-hint: <what-the-skill-does>
disable-model-invocation: true
---

Create a new skill using the skillsmith workflow.

**Goal:** $ARGUMENTS

Invoke the skillsmith skill in CREATE mode.
```

### `/skillsmith:review`

```markdown
---
description: Review an existing skill with the 4-agent panel
argument-hint: <path-to-skill>
disable-model-invocation: true
---

Review an existing skill using skillsmith's quality panel.

**Target:** $ARGUMENTS

Invoke the skillsmith skill in REVIEW mode (Phase 3 + Phase 4 only).
```

### `/skillsmith:lint`

```markdown
---
description: Validate a skill against spec v2.0 (11 FAIL codes)
argument-hint: <path-to-skill>
---

Validate a skill using the unified linter.

**Target:** $ARGUMENTS

Run: `python scripts/skill_lint.py $ARGUMENTS`
```

---

## 11. Agent Definitions

Full definitions for all 4 panel agents. Criteria baked into prompts (no external spec consultation during review).

### Design Agent

~~~yaml
---
name: design-agent
description: Reviews skills for structural correctness, pattern compliance, and logical consistency. Part of skillsmith review panel.
tools: Read, Glob, Grep
model: opus
permissionMode: plan
---

You are a skill design reviewer focused on structure and correctness.

## Purpose

Evaluate whether a skill's structure meets spec v2.0 requirements and whether its design is internally consistent.

## Task

Review the skill for:
1. **Structural compliance**: All 11 sections present
2. **FAIL code clearance**: No violations of 11 FAIL codes
3. **Pattern appropriateness**: Risk tier matches content
4. **Logical consistency**: No contradictions between sections
5. **Decision coverage**: ≥2 decision points with observable triggers
6. **STOP gate placement**: ≥1 STOP gate at appropriate point

Use semantic quality dimensions B, E, F as primary lenses.

## Constraints

**Allowed:** Read skill files; search for patterns; report structural issues
**Forbidden:** Modifying files; evaluating timelessness; evaluating clarity; suggesting new features

## Output Format

Return markdown with: Verdict (APPROVED/CHANGES_REQUIRED), Scores table (6 criteria, 1-10), Strengths (with evidence), Issues table (Dimension, Issue, Severity, Required Change).
~~~

### Audience Agent

~~~yaml
---
name: audience-agent
description: Reviews skills for clarity, discoverability, and usability. Part of skillsmith review panel.
tools: Read, Glob, Grep
model: opus
permissionMode: plan
---

You are a skill usability reviewer focused on the user experience.

## Purpose

Evaluate whether a user can discover, understand, and successfully execute the skill.

## Task

Review the skill for:
1. **Trigger quality**: 3-5 natural phrases, varied phrasing
2. **Clarity**: Steps actionable, no assumed knowledge
3. **Discoverability**: Description enables finding the skill
4. **Input/output clarity**: Required vs optional clear; DoD objective
5. **Troubleshooting usefulness**: Failure modes have actionable recovery

Key question: Would a new user succeed on first attempt?

## Constraints

**Allowed:** Read skill files; evaluate from user perspective; flag jargon
**Forbidden:** Modifying files; evaluating structure; evaluating timelessness; suggesting scope expansion

## Output Format

Return markdown with: Verdict, Scores table (5 criteria), Strengths (with evidence), Issues table.
~~~

### Evolution Agent

~~~yaml
---
name: evolution-agent
description: Reviews skills for timelessness, extensibility, and ecosystem fit. Owns timelessness scoring. Part of skillsmith review panel.
tools: Read, Glob, Grep
model: opus
permissionMode: plan
---

You are a skill evolution reviewer focused on longevity and extensibility.

## Purpose

Evaluate whether a skill will remain valuable over time. **You are the sole authority on timelessness scoring.**

## Task

1. **Timelessness**: Assign 1-10 score (≥7 required)
2. **Principle-based design**: Not hardcoded to tools/versions
3. **Extension points**: ≥2 documented evolution paths
4. **Ecosystem fit**: No unnecessary duplication
5. **WHY documentation**: Rationale for key decisions

## Timelessness Rubric

1-2: Ephemeral | 3-4: Short-lived | 5-6: Moderate (FAILS) | 7-8: Solid (MINIMUM) | 9-10: Timeless

**Threshold: ≥7 mandatory. 6.9 fails. No rounding.**

## Constraints

**Allowed:** Read files; evaluate temporal durability; check ecosystem
**Forbidden:** Modifying files; evaluating structure; evaluating clarity; approving score <7

## Output Format

Return markdown with: Verdict, **Timelessness Score: X/10**, Factor assessment table, Score justification (2-3 sentences), Strengths, Issues table. If score 6.0-6.9, list specific changes to reach ≥7.
~~~

### Script Agent

~~~yaml
---
name: script-agent
description: Reviews script quality AND evaluates automation opportunities. Always participates. Part of skillsmith review panel.
tools: Read, Glob, Grep, Bash
model: opus
permissionMode: plan
---

You are a skill automation reviewer. **You always participate**, even for skills without scripts.

## Purpose

Evaluate script quality (if present) AND whether the skill has appropriate automation.

## Task

### If scripts exist:
1. Pattern compliance (Result dataclass, argparse, exit codes 0/1/10/11)
2. Self-verification capability
3. Error handling (graceful failures, actionable messages)
4. Documentation in SKILL.md
5. Shebang present

### For ALL skills:
6. Should scripts exist but don't?
7. Can skill run autonomously?

## Constraints

**Allowed:** Read files; run scripts read-only to verify behavior; recommend new scripts
**Forbidden:** Modifying files; evaluating non-script quality; running state-modifying scripts

## Output Format

Return markdown with: Verdict, Scripts Present (Yes/No), Script quality table (if present), Automation assessment table (should have scripts?, missing opportunities?, can run autonomously?), Strengths, Issues table, Recommended Scripts table (if applicable: Script, Purpose, Category, Key Functions).
~~~

---

## 12. Error Handling Summary

### Defaults

| Parameter | Value |
|-----------|-------|
| Max regression questioning rounds | 7 |
| Max validation iterations | 3 |
| Max panel iterations | 5 |
| Category confidence threshold | 60% |
| Timelessness score threshold | ≥7 (strict) |
| Minimum STOP triggers | 1 |
| Triggers | ≥3 |
| Anti-Patterns | ≥1 |
| Extension Points | ≥2 |

### By Phase

| Phase | Failure | Handling |
|-------|---------|----------|
| **0: Triage** | Can't determine routing | Ask user with structured options |
| | Category confidence <60% | Present top 2-3, let user choose |
| | discover_skills.py fails | Warn, proceed without duplicate check |
| | Near-duplicate found | Allow with differentiation requirement |
| | Target skill not found (MODIFY) | Fuzzy match suggestions |
| **1: Analysis** | Regression questioning doesn't converge | Cap at 7 rounds, proceed |
| | Category changes | Reload guidance, gap-fill |
| | Risk tier unclear | Default higher, document uncertainty |
| | No STOP triggers | Require minimum 1, suggest default |
| **2: Generation** | Can't satisfy 11 sections | Return to Phase 1 (scope issue) |
| | Conflicting guidance | Category overrides general, document |
| | Script design unclear | Default no scripts, flag for Phase 4 |
| **3: Validation** | User doesn't confirm | Abort cleanly |
| | Write fails | Report error, no partial writes |
| | Validation fails (1-2x) | Fix specific issue, re-validate |
| | Validation fails (3x) | Return to Phase 1 |
| | Regression detected | Block, require fix |
| **4: Review** | Any agent CHANGES_REQUIRED | Collect issues, return to Phase 1 |
| | Timelessness 6.0-6.9 | Strict fail, list improvements needed |
| | 5 iterations no consensus | Escalate to human |

### Escalation Path

```
Phase fails → Can fix with targeted changes? → Yes → Fix and retry
                     ↓ No
              Fundamental issue? → Yes → Loop to earlier phase
                     ↓ No / Still failing
              Human escalation → Present situation, get decision
```

---

## 13. Migration Overview

### Source Projects

| Project | Location | Status |
|---------|----------|--------|
| skill-documentation | (already archived) | Already archived |
| skillforge | `.claude/skills/skillforge/` | Deprecated after skillsmith ships, then deleted |

### Target

```
packages/plugins/skillsmith/
```

### What Gets Copied, Created, Merged, Dropped

| Action | Items |
|--------|-------|
| **Copied** | Spec docs from archived skill-documentation (flatten, rename shorter), analysis refs from skillforge, discover_skills.py, script-template.py |
| **Created** | plugin.json, README, SKILL.md, INDEX.md, 4 agent files, 3 command files |
| **Merged** | skill_lint.py + validate-skill.py checks → unified validator (11 FAIL codes) |
| **Dropped** | XML specification format, validate-skill.py, quick_validate.py |

### Reference File Mapping

| Source | Target |
|--------|--------|
| skills-as-prompts-strict-spec.md | strict-spec.md |
| skills-categories-guide.md | categories-guide.md |
| skills-semantic-quality-addendum.md | semantic-quality.md |
| skills-domain-annexes.md | domain-annexes.md |
| skills-authoring-review-pipeline.md | authoring-pipeline.md |
| how-to-author-review-one-pager.md | one-pager.md |
| regression-questions.md | regression-questions.md |
| multi-lens-framework.md | multi-lens.md |
| evolution-scoring.md | evolution-scoring.md |
| synthesis-protocol.md | synthesis-protocol.md |
| script-integration-framework.md | script-framework.md |
| script-patterns-catalog.md | script-patterns.md |

### Success Criteria

| Criterion | Verification |
|-----------|--------------|
| Plugin installs | `claude plugin install skillsmith@tool-dev` succeeds |
| Validator works | 11 FAIL codes enforced, passes on test skills |
| Workflow runs | `/skillsmith:create` completes end-to-end |
| Review works | `/skillsmith:review` runs 4-agent panel |
| skillforge deprecated | Warning shown when invoked, points to skillsmith |

---

## 14. Open Questions & Future Work

### Deferred for Later

| Item | Why deferred |
|------|--------------|
| Domain annexes integration | Adds complexity; core workflow works without |
| Skill composition | Separate concern; skillsmith focuses on single skills |
| Skill versioning | Git handles this for now |
| Automated spec sync | Manual sync acceptable initially |
| Batch validation | Can validate one at a time for v1.0 |
| Relaxed mode for drafts | Ship strict first, relax if needed |

### Open Questions

| Question | Notes |
|----------|-------|
| Should skillsmith modify itself? | Wait until v1.0 stable; hand-modify initially |
| Very large skills (>1000 lines)? | Rare; address when encountered |
| Skill metrics/telemetry? | Future enhancement; not needed for MVP |

### Potential Future Enhancements

| Enhancement | Priority |
|-------------|----------|
| `/skillsmith:improve` alias for MODIFY flow | Low |
| Batch validation across skills directory | Medium |
| Category-specific templates | Medium |
| Integration with promote script | Medium |
| Panel agent model override | Low |

---

## Decisions Log

Key decisions made during design refinement (2026-01-11):

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Go/no-go | GO | Problems real, complexity proportionate, no blockers |
| Section count | 11 (spec v2.0) | Extend spec rather than claim false alignment |
| Timelessness | Mandatory ≥7 | New requirement, high quality bar |
| Panel composition | Always 4 agents | Script Agent evaluates automation opportunities |
| Agent orchestration | Parallel Task tool | Documented pattern, main skill synthesizes |
| FAIL code extension | Explicit (8→11) | Clear spec versioning |
| Reference structure | Flatten + INDEX.md | Follow progressive disclosure guideline |
| Hooks | None for v1.0 | YAGNI; add when demonstrated need |
| Commands | Entry points with args | Thin wrappers, skill has logic |
| Command naming | `/skillsmith:*` | Follow plugin namespacing convention |
| Spec access | Baked into agent prompts | Self-contained, fast, deterministic |
| Consensus | Unanimous | High quality bar |
| Model selection | All opus | Panel is quality gate; don't compromise |
| Bootstrapping | Hand-author following specs | Circular dependency resolved |

---

*Document generated from brainstorming session 2026-01-11*

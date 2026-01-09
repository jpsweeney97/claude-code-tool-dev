# skillsmith Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the skillsmith plugin by merging skill-documentation and skillforge into a unified framework for creating, validating, and reviewing Claude Code skills.

**Architecture:** Plugin-based structure with 33 files across 7 directories. Core workflow is 5-phase (Triage → Analysis → Generation → Validation → Review). Unified validator combines 11 FAIL codes. Multi-agent panel (4 agents) for quality review with two-tier gates (semantic quality + timelessness).

**Tech Stack:** Claude Code plugin system, Python scripts (stdlib only for embedded scripts, PEP 723 for top-level), Markdown skill/agent definitions.

---

## Prerequisites

Before starting, verify:

```bash
# Confirm source files exist
ls skill-documentation/skills-as-prompts-strict-spec.md
ls .claude/skills/skillforge/SKILL.md

# Confirm target doesn't exist
ls packages/plugins/skillsmith/ 2>/dev/null && echo "ERROR: already exists" || echo "OK: ready to create"
```

---

## Task 1: Plugin Directory Structure

**Files:**
- Create: `packages/plugins/skillsmith/`
- Create: `packages/plugins/skillsmith/.claude-plugin/plugin.json`
- Create: `packages/plugins/skillsmith/README.md`
- Create: `packages/plugins/skillsmith/LICENSE`
- Create: `packages/plugins/skillsmith/CHANGELOG.md`

**Step 1: Create directory structure**

```bash
mkdir -p packages/plugins/skillsmith/.claude-plugin
mkdir -p packages/plugins/skillsmith/agents
mkdir -p packages/plugins/skillsmith/skills/skillsmith/references/{spec,workflow,analysis,review,scripts}
mkdir -p packages/plugins/skillsmith/skills/skillsmith/templates
mkdir -p packages/plugins/skillsmith/scripts/tests
mkdir -p packages/plugins/skillsmith/commands
```

**Step 2: Create plugin.json**

```json
{
  "name": "skillsmith",
  "version": "1.0.0",
  "description": "Unified framework for creating, validating, and reviewing Claude Code skills",
  "author": {
    "name": "JP"
  },
  "license": "MIT",
  "keywords": ["skills", "skillforge", "validation", "meta-skill"],
  "skills": "./skills/",
  "commands": "./commands/",
  "agents": ["./agents/design-agent.md", "./agents/audience-agent.md", "./agents/evolution-agent.md", "./agents/script-agent.md"]
}
```

**Step 3: Create README.md**

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

## Components

- **Skill:** `skills/skillsmith/SKILL.md` - Main workflow
- **Agents:** 4 review agents (design, audience, evolution, script)
- **Validator:** `scripts/skill_lint.py` - Unified linter with 11 FAIL codes
- **Commands:** 3 entry points (create, review, lint)

## Source

Merges skill-documentation (spec) and skillforge (workflow) into unified plugin.
```

**Step 4: Create LICENSE**

```
MIT License

Copyright (c) 2026 JP

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Step 5: Create CHANGELOG.md**

```markdown
# Changelog

All notable changes to skillsmith will be documented in this file.

## [1.0.0] - 2026-01-09

### Added
- Initial release
- Unified skill creation workflow (5 phases)
- Unified validator with 11 FAIL codes
- Multi-agent review panel (4 agents)
- Two-tier quality model (semantic + timelessness)
- 3 commands: create-skill, review-skill, lint-skill
```

**Step 6: Verify structure**

Run: `find packages/plugins/skillsmith -type f | head -20`

Expected: 5 files (plugin.json, README.md, LICENSE, CHANGELOG.md, and directories created)

**Step 7: Commit**

```bash
git add packages/plugins/skillsmith/
git commit -m "feat(skillsmith): create plugin structure and metadata

- Add plugin.json with manifest
- Add README, LICENSE, CHANGELOG
- Create directory structure for 33 planned files

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Copy Spec References

**Files:**
- Copy: `skill-documentation/skills-as-prompts-strict-spec.md` → `packages/plugins/skillsmith/skills/skillsmith/references/spec/`
- Copy: `skill-documentation/skills-categories-guide.md` → `packages/plugins/skillsmith/skills/skillsmith/references/spec/`
- Copy: `skill-documentation/skills-semantic-quality-addendum.md` → `packages/plugins/skillsmith/skills/skillsmith/references/spec/`
- Copy: `skill-documentation/skills-domain-annexes.md` → `packages/plugins/skillsmith/skills/skillsmith/references/spec/`

**Step 1: Copy spec files**

```bash
cp skill-documentation/skills-as-prompts-strict-spec.md packages/plugins/skillsmith/skills/skillsmith/references/spec/
cp skill-documentation/skills-categories-guide.md packages/plugins/skillsmith/skills/skillsmith/references/spec/
cp skill-documentation/skills-semantic-quality-addendum.md packages/plugins/skillsmith/skills/skillsmith/references/spec/
cp skill-documentation/skills-domain-annexes.md packages/plugins/skillsmith/skills/skillsmith/references/spec/
```

**Step 2: Verify files exist**

Run: `ls -la packages/plugins/skillsmith/skills/skillsmith/references/spec/`

Expected: 4 markdown files

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/references/spec/
git commit -m "feat(skillsmith): copy spec reference documents

- skills-as-prompts-strict-spec.md (8 FAIL codes, risk tiers)
- skills-categories-guide.md (13 categories)
- skills-semantic-quality-addendum.md (9 dimensions)
- skills-domain-annexes.md (domain invariants)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Copy Workflow References

**Files:**
- Copy: `skill-documentation/skills-authoring-review-pipeline.md` → `packages/plugins/skillsmith/skills/skillsmith/references/workflow/`
- Copy: `skill-documentation/how-to-author-review-one-pager.md` → `packages/plugins/skillsmith/skills/skillsmith/references/workflow/`

**Step 1: Copy workflow files**

```bash
cp skill-documentation/skills-authoring-review-pipeline.md packages/plugins/skillsmith/skills/skillsmith/references/workflow/
cp skill-documentation/how-to-author-review-one-pager.md packages/plugins/skillsmith/skills/skillsmith/references/workflow/
```

**Step 2: Verify files exist**

Run: `ls -la packages/plugins/skillsmith/skills/skillsmith/references/workflow/`

Expected: 2 markdown files

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/references/workflow/
git commit -m "feat(skillsmith): copy workflow reference documents

- skills-authoring-review-pipeline.md (6-step pipeline, historical)
- how-to-author-review-one-pager.md (quick reference)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Copy Analysis References

**Files:**
- Copy: `.claude/skills/skillforge/references/regression-questions.md` → `packages/plugins/skillsmith/skills/skillsmith/references/analysis/`
- Copy: `.claude/skills/skillforge/references/multi-lens-framework.md` → `packages/plugins/skillsmith/skills/skillsmith/references/analysis/`
- Copy: `.claude/skills/skillforge/references/evolution-scoring.md` → `packages/plugins/skillsmith/skills/skillsmith/references/analysis/`

**Step 1: Copy analysis files**

```bash
cp .claude/skills/skillforge/references/regression-questions.md packages/plugins/skillsmith/skills/skillsmith/references/analysis/
cp .claude/skills/skillforge/references/multi-lens-framework.md packages/plugins/skillsmith/skills/skillsmith/references/analysis/
cp .claude/skills/skillforge/references/evolution-scoring.md packages/plugins/skillsmith/skills/skillsmith/references/analysis/
```

**Step 2: Verify files exist**

Run: `ls -la packages/plugins/skillsmith/skills/skillsmith/references/analysis/`

Expected: 3 markdown files

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/references/analysis/
git commit -m "feat(skillsmith): copy analysis reference documents

- regression-questions.md (7 question categories)
- multi-lens-framework.md (11 thinking models)
- evolution-scoring.md (timelessness rubric)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Copy Review and Script References

**Files:**
- Copy: `.claude/skills/skillforge/references/synthesis-protocol.md` → `packages/plugins/skillsmith/skills/skillsmith/references/review/`
- Copy: `.claude/skills/skillforge/references/script-integration-framework.md` → `packages/plugins/skillsmith/skills/skillsmith/references/scripts/`
- Copy: `.claude/skills/skillforge/references/script-patterns-catalog.md` → `packages/plugins/skillsmith/skills/skillsmith/references/scripts/`

**Step 1: Copy review and script files**

```bash
cp .claude/skills/skillforge/references/synthesis-protocol.md packages/plugins/skillsmith/skills/skillsmith/references/review/
cp .claude/skills/skillforge/references/script-integration-framework.md packages/plugins/skillsmith/skills/skillsmith/references/scripts/
cp .claude/skills/skillforge/references/script-patterns-catalog.md packages/plugins/skillsmith/skills/skillsmith/references/scripts/
```

**Step 2: Verify files exist**

Run: `ls packages/plugins/skillsmith/skills/skillsmith/references/review/ packages/plugins/skillsmith/skills/skillsmith/references/scripts/`

Expected: 1 file in review/, 2 files in scripts/

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/references/review/ packages/plugins/skillsmith/skills/skillsmith/references/scripts/
git commit -m "feat(skillsmith): copy review and script references

- synthesis-protocol.md (panel review process)
- script-integration-framework.md (script creation guidance)
- script-patterns-catalog.md (Python patterns)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Copy Templates and Discovery Script

**Files:**
- Copy: `.claude/skills/skillforge/assets/templates/script-template.py` → `packages/plugins/skillsmith/skills/skillsmith/templates/`
- Copy: `.claude/skills/skillforge/scripts/discover_skills.py` → `packages/plugins/skillsmith/scripts/`

**Step 1: Copy files**

```bash
cp .claude/skills/skillforge/assets/templates/script-template.py packages/plugins/skillsmith/skills/skillsmith/templates/
cp .claude/skills/skillforge/scripts/discover_skills.py packages/plugins/skillsmith/scripts/
```

**Step 2: Verify files exist**

Run: `ls packages/plugins/skillsmith/skills/skillsmith/templates/ packages/plugins/skillsmith/scripts/`

Expected: script-template.py in templates/, discover_skills.py in scripts/

**Step 3: Test discover_skills.py runs**

Run: `python packages/plugins/skillsmith/scripts/discover_skills.py --help 2>/dev/null || python3 packages/plugins/skillsmith/scripts/discover_skills.py --help`

Expected: Help output or usage info (no crash)

**Step 4: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/templates/ packages/plugins/skillsmith/scripts/discover_skills.py
git commit -m "feat(skillsmith): copy templates and discovery script

- script-template.py (Python script base)
- discover_skills.py (ecosystem skill index)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Create Spec Index

**Files:**
- Create: `packages/plugins/skillsmith/skills/skillsmith/references/spec-index.md`

**Step 1: Create spec-index.md**

```markdown
# Spec Section Index

Quick reference for agents to locate spec sections during review.

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

## How to Use

1. Identify the decision type you're making
2. Look up the path in this index
3. Load and consult the referenced section
4. **Cite the section in your review output** (no cite = no claim)

## Path Resolution

All paths are relative to `skills/skillsmith/references/`.

Examples:
- `spec/skills-as-prompts-strict-spec.md#risk-tiers`
- `analysis/evolution-scoring.md#scoring-rubric`

## Agent Responsibilities

| Agent | Primary Lookups |
|-------|-----------------|
| Design Agent | Decision Points, STOP Templates, Unsafe Defaults |
| Audience Agent | Category definitions, Terminology |
| Evolution Agent | Evolution Scoring, Extension Points |
| Script Agent | script-patterns-catalog.md (not in spec-index) |
```

**Step 2: Verify file created**

Run: `head -20 packages/plugins/skillsmith/skills/skillsmith/references/spec-index.md`

Expected: Spec Section Index header and table

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/references/spec-index.md
git commit -m "feat(skillsmith): create spec section index

Maps decision types to spec section paths for agent lookup.
Required for spec-on-demand design pattern.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Create Merged Workflow Document

**Files:**
- Create: `packages/plugins/skillsmith/skills/skillsmith/references/workflow/merged-creation-workflow.md`

**Step 1: Create merged-creation-workflow.md**

```markdown
# Merged Creation Workflow

Unified 5-phase workflow for creating and modifying skills.

## Overview

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

## Phase 0: Triage

**Purpose:** Determine routing, load context.

**Steps:**
1. Parse goal to understand intent (create vs improve vs question)
2. Scan ecosystem with `discover_skills.py`
3. Determine routing based on match confidence:
   - ≥80%: USE_EXISTING or CLARIFY
   - 50-79%: MODIFY or CLARIFY
   - <50%: CREATE or skill-not-found
4. For MODIFY: Load existing skill and dependencies
5. Assign preliminary category (≥60% confidence or ask)
6. Load category-specific guidance

**Outputs:** Routing decision, existing content (if MODIFY), category, guidance

## Phase 1: Analysis

**Purpose:** Deep understanding, captured in analysis notes.

**Steps:**
1. Requirements discovery (explicit, implicit, discovered)
2. Apply 11 thinking models (all scanned, ≥5 in depth)
3. Regression questioning (max 7 rounds)
4. Category validation (reload if changed)
5. Risk tier assignment (Low/Medium/High)
6. STOP trigger identification (min 1)
7. Automation analysis (scripts needed?)
8. For MODIFY: Scope assessment

**Outputs:** Analysis notes markdown document

## Phase 2: Generation

**Purpose:** Generate complete SKILL.md.

**Steps:**
1. Generate frontmatter (name, description required)
2. Generate 11 hybrid sections
3. Design STOP gates
4. Apply semantic quality dimensions (9 checks)
5. Apply category-specific guidance
6. Design scripts if needed
7. For MODIFY: Preserve working sections

**Outputs:** Complete SKILL.md (in memory), scripts (if any)

## Phase 3: Diff, Confirm & Validation

**Purpose:** User approval, then validation.

**Steps:**
1. Present changes for review (full content or diff)
2. Wait for user confirmation
3. For MODIFY: Recommend git checkpoint
4. Write atomically (all files or none)
5. Run unified validator
6. Handle failures (3 attempts, then back to Phase 1)
7. For MODIFY: Regression check

**Outputs:** Validated SKILL.md on disk

## Phase 4: Review

**Purpose:** Multi-agent quality judgment.

**Panel:**
- Design Agent: Structure, patterns, correctness
- Audience Agent: Clarity, triggers, discoverability
- Evolution Agent: Timelessness (≥7 required)
- Script Agent: Script quality (conditional)

**Steps:**
1. All agents review holistically using semantic dimensions
2. Agents cite spec sections (no cite = no claim)
3. Tier 1 gate: Semantic quality (no critical violations)
4. Tier 2 gate: Timelessness ≥7
5. Consensus: All APPROVED → done; any CHANGES_REQUIRED → Phase 1
6. After 5 iterations: Human escalation

**Outputs:** APPROVED skill or feedback for iteration

## Error Handling Defaults

| Parameter | Value |
|-----------|-------|
| Max regression rounds | 7 |
| Max validation attempts | 3 |
| Max panel iterations | 5 |
| Category confidence threshold | 60% |
| Timelessness threshold | ≥7 (strict) |
| Minimum STOP triggers | 1 |
| Triggers required | ≥3 |
| Anti-Patterns required | ≥1 |
| Extension Points required | ≥2 |
```

**Step 2: Verify file created**

Run: `wc -l packages/plugins/skillsmith/skills/skillsmith/references/workflow/merged-creation-workflow.md`

Expected: ~130 lines

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/references/workflow/merged-creation-workflow.md
git commit -m "feat(skillsmith): create merged workflow document

Documents unified 5-phase workflow:
- Phase 0: Triage (routing decision)
- Phase 1: Analysis (11 models, regression questions)
- Phase 2: Generation (11 sections, semantic quality)
- Phase 3: Validation (diff, confirm, linter)
- Phase 4: Review (4-agent panel, two-tier gates)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Create Skill Template

**Files:**
- Create: `packages/plugins/skillsmith/skills/skillsmith/templates/skill-md-template.md`

**Step 1: Create skill-md-template.md**

```markdown
---
name: {skill-name}
description: {One-line description, ≤1024 chars}
license: MIT
metadata:
  version: "1.0.0"
  model: claude-opus-4-5-20251101
  category: {category}
  timelessness_score: null
---

# {Skill Name}

## Triggers

- "{Natural language phrase 1}"
- "{Natural language phrase 2}"
- "{Natural language phrase 3}"

## When to Use

Use this skill when:
- {Activation condition 1}
- {Activation condition 2}

## When NOT to Use

Do NOT use this skill when:
- {Exclusion 1}
- {Exclusion 2}

**STOP if:** {Critical stop condition}

## Inputs

**Required:**
- {Input 1}: {Description}

**Optional:**
- {Input 2}: {Description, default: X}

**Assumptions:**
- {Assumption about tools, network, permissions}

## Outputs

**Primary:**
- {Output artifact}: {Description}

**Definition of Done:**
- [ ] {Checkable criterion 1}
- [ ] {Checkable criterion 2}

## Procedure

### Step 1: {Action}

{Instructions}

**If** {condition}:
  - **Then** {action A}
  - **Otherwise** {action B}

### Step 2: {Action}

{Instructions}

**STOP.** Ask the user for: {X}. **Do not proceed** until provided.

### Step 3: {Action}

{Instructions}

## Verification

**Quick check:**
- Run: `{command}`
- Expected: {pattern or output}

## Troubleshooting

### {Symptom 1}

**Cause:** {Why this happens}

**Fix:** {How to resolve}

### {Symptom 2}

**Cause:** {Why this happens}

**Fix:** {How to resolve}

## Anti-Patterns

- **{Anti-pattern 1}:** {Why to avoid}
- **{Anti-pattern 2}:** {Why to avoid}

## Extension Points

1. **{Extension 1}:** {How the skill can evolve}
2. **{Extension 2}:** {How the skill can evolve}

## References

- @references/spec/skills-as-prompts-strict-spec.md
- @references/workflow/merged-creation-workflow.md
```

**Step 2: Verify file created**

Run: `head -30 packages/plugins/skillsmith/skills/skillsmith/templates/skill-md-template.md`

Expected: Frontmatter and first sections visible

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/templates/skill-md-template.md
git commit -m "feat(skillsmith): create skill template with 11 hybrid sections

Template includes:
- Frontmatter (name, description, metadata)
- All 11 sections with placeholder content
- Decision point and STOP gate examples
- Definition of Done checklist

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Create Analysis Notes Template

**Files:**
- Create: `packages/plugins/skillsmith/skills/skillsmith/templates/analysis-notes-template.md`

**Step 1: Create analysis-notes-template.md**

```markdown
# Analysis Notes: {Skill Name}

**Date:** {YYYY-MM-DD}
**Route:** {CREATE | MODIFY}
**Goal:** {User's stated goal}

---

## Classification

| Attribute | Value | Confidence |
|-----------|-------|------------|
| Category | {category} | {X%} |
| Risk Tier | {Low/Medium/High} | {X%} |

**Rationale:** {Why this classification}

---

## Requirements

### Explicit (stated by user)
- {Requirement 1}
- {Requirement 2}

### Implicit (expected but unstated)
- {Requirement 1}
- {Requirement 2}

### Discovered (found through analysis)
- {Requirement 1}
- {Requirement 2}

---

## Thinking Models Applied

| Model | Insight |
|-------|---------|
| First Principles | {Finding} |
| Inversion | {Finding} |
| Second-Order | {Finding} |
| Pre-Mortem | {Finding} |
| Systems Thinking | {Finding} |
| Devil's Advocate | {Finding} |
| Constraints | {Finding} |
| Pareto | {Finding} |
| Root Cause | {Finding} |
| Comparative | {Finding} |
| Opportunity Cost | {Finding} |

---

## Key Decisions

### {Decision 1}

**Choice:** {What was decided}

**Why:** {Rationale}

**Alternatives considered:** {What was rejected and why}

### {Decision 2}

**Choice:** {What was decided}

**Why:** {Rationale}

---

## STOP Triggers

1. {Trigger 1}: {When to stop and ask}
2. {Trigger 2}: {When to stop and ask}

---

## Scripts Decision

**Needed:** {Yes | No}

**Types:** {validation, generation, state management}

**Rationale:** {Why scripts are/aren't needed}

---

## For MODIFY Only

### Current State
{Summary of existing skill}

### Change Scope
- {Change 1}
- {Change 2}

### Dependencies Affected
- {Dependency 1}
- {Dependency 2}

### Additional Issues Discovered
- {Issue 1}: {Recommendation}
```

**Step 2: Verify file created**

Run: `head -40 packages/plugins/skillsmith/skills/skillsmith/templates/analysis-notes-template.md`

Expected: Analysis Notes header and Classification section

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/templates/analysis-notes-template.md
git commit -m "feat(skillsmith): create analysis notes template

Template for Phase 1 output with:
- Classification (category, risk tier)
- Requirements (explicit, implicit, discovered)
- 11 thinking models table
- Key decisions with rationale
- STOP triggers list
- Scripts decision
- MODIFY-specific sections

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 11: Update Synthesis Protocol

**Files:**
- Modify: `packages/plugins/skillsmith/skills/skillsmith/references/review/synthesis-protocol.md`

**Step 1: Read current file**

Run: `cat packages/plugins/skillsmith/skills/skillsmith/references/review/synthesis-protocol.md`

**Step 2: Update with two-tier quality gates**

Add the following sections to the existing file (preserve existing content, add new sections):

```markdown

---

## Two-Tier Quality Model

### Tier 1: Semantic Quality (Primary Gate)

Evaluated by: Design + Audience + Evolution agents holistically

Pass condition: No critical violations, <2 major per agent

**9 Dimensions (shared vocabulary):**

| Dimension | Question |
|-----------|----------|
| Intent fidelity | Is the primary goal clear? |
| Constraint completeness | Are allowed/forbidden explicit? |
| Terminology clarity | Are key terms defined once? |
| Evidence anchoring | Do claims cite sources? |
| Decision sufficiency | Do decisions reference observable signals? |
| Verification validity | Does quick check measure primary success? |
| Artifact usefulness | Is output format specified? |
| Minimality | Smallest correct scope? |
| Calibration | Is uncertainty labeled? |

### Tier 2: Timelessness (Secondary Gate)

Evaluated by: Evolution Agent only

Pass condition: Score ≥7/10

| Score | Lifespan |
|-------|----------|
| 1-4 | <1 year |
| 5-6 | 1-2 years |
| 7-8 | 2-4 years |
| 9-10 | 5+ years |

---

## Spec Consultation Protocol

Agents consult spec documents for specific decisions (not upfront loading).

**Rule:** No cite = no claim. Every judgment must reference spec section.

**Lookup process:**
1. Identify decision type
2. Consult `references/spec-index.md` for path
3. Load and review relevant section
4. Include citation in review output

---

## Holistic Review Approach

Agents don't "own" specific dimensions. They use dimensions as shared vocabulary:

- All agents review the full skill from their perspective
- Dimensions describe issues, not assign ownership
- Any critical violation from any agent → FAIL
- Script Agent reviews separately (only if scripts present)
```

**Step 3: Verify update**

Run: `grep -c "Two-Tier Quality Model" packages/plugins/skillsmith/skills/skillsmith/references/review/synthesis-protocol.md`

Expected: 1

**Step 4: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/references/review/synthesis-protocol.md
git commit -m "feat(skillsmith): update synthesis protocol with two-tier gates

Add:
- Two-tier quality model (semantic → timelessness)
- 9 semantic dimensions as shared vocabulary
- Spec consultation protocol with citation requirement
- Holistic review approach

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 12: Write Failing Test for Unified Validator

**Files:**
- Create: `packages/plugins/skillsmith/scripts/tests/test_skill_lint.py`

**Step 1: Create test file with failing tests for new checks**

```python
#!/usr/bin/env python3
"""Tests for unified skill validator."""

import pytest
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_lint import lint_skill, LintResult


class TestFrontmatterValidation:
    """Tests for frontmatter checks (from validate-skill.py)."""

    def test_missing_name_fails(self, tmp_path):
        """Skill without name in frontmatter should fail."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("""---
description: Test skill
---

# Test Skill

## Triggers
- "test"
""")
        result = lint_skill(skill)
        assert not result.passed
        assert any("name" in f.lower() for f in result.failures)

    def test_missing_description_fails(self, tmp_path):
        """Skill without description in frontmatter should fail."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("""---
name: test-skill
---

# Test Skill

## Triggers
- "test"
""")
        result = lint_skill(skill)
        assert not result.passed
        assert any("description" in f.lower() for f in result.failures)

    def test_name_too_long_fails(self, tmp_path):
        """Skill name over 64 chars should fail."""
        skill = tmp_path / "SKILL.md"
        long_name = "a" * 65
        skill.write_text(f"""---
name: {long_name}
description: Test skill
---

# Test Skill
""")
        result = lint_skill(skill)
        assert not result.passed
        assert any("64" in f or "name" in f.lower() for f in result.failures)


class TestHybridStructure:
    """Tests for hybrid structure checks (new FAIL codes)."""

    def test_missing_triggers_fails(self, tmp_path):
        """Skill without Triggers section should fail."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("""---
name: test-skill
description: Test skill
---

# Test Skill

## When to Use
Use when testing.
""")
        result = lint_skill(skill)
        assert not result.passed
        assert any("trigger" in f.lower() for f in result.failures)

    def test_too_few_triggers_fails(self, tmp_path):
        """Skill with <3 trigger phrases should fail."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("""---
name: test-skill
description: Test skill
---

# Test Skill

## Triggers
- "test"
- "try"

## When to Use
Use when testing.
""")
        result = lint_skill(skill)
        assert not result.passed
        assert any("trigger" in f.lower() and "3" in f for f in result.failures)

    def test_missing_anti_patterns_fails(self, tmp_path):
        """Skill without Anti-Patterns section should fail."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("""---
name: test-skill
description: Test skill
---

# Test Skill

## Triggers
- "test one"
- "test two"
- "test three"

## When to Use
Use when testing.

## Extension Points
1. First extension
2. Second extension
""")
        result = lint_skill(skill)
        assert not result.passed
        assert any("anti-pattern" in f.lower() for f in result.failures)

    def test_missing_extension_points_fails(self, tmp_path):
        """Skill without Extension Points section should fail."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("""---
name: test-skill
description: Test skill
---

# Test Skill

## Triggers
- "test one"
- "test two"
- "test three"

## When to Use
Use when testing.

## Anti-Patterns
- Don't do this
""")
        result = lint_skill(skill)
        assert not result.passed
        assert any("extension" in f.lower() for f in result.failures)

    def test_too_few_extension_points_fails(self, tmp_path):
        """Skill with <2 extension points should fail."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("""---
name: test-skill
description: Test skill
---

# Test Skill

## Triggers
- "test one"
- "test two"
- "test three"

## When to Use
Use when testing.

## Anti-Patterns
- Don't do this

## Extension Points
1. Only one extension
""")
        result = lint_skill(skill)
        assert not result.passed
        assert any("extension" in f.lower() and "2" in f for f in result.failures)


class TestValidSkill:
    """Tests that valid skills pass."""

    def test_minimal_valid_skill_passes(self, tmp_path):
        """Skill with all required elements should pass."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("""---
name: test-skill
description: A test skill for validation
---

# Test Skill

## Triggers

- "run test skill"
- "execute test"
- "perform test action"

## When to Use

Use this skill when:
- Testing the validator
- Verifying skill structure

## When NOT to Use

Do NOT use when:
- In production without review

**STOP if:** Requirements unclear

## Inputs

**Required:**
- input1: The test input

**Assumptions:**
- Python 3.12+ available

## Outputs

**Primary:**
- Test result

**Definition of Done:**
- [ ] Test executed
- [ ] Result verified

## Procedure

### Step 1: Prepare

Set up the test environment.

**If** environment ready:
  - **Then** proceed
  - **Otherwise** configure first

### Step 2: Execute

Run the test.

**STOP.** Ask the user for: confirmation. **Do not proceed** until provided.

### Step 3: Verify

Check the results.

**If** results valid:
  - **Then** report success
  - **Otherwise** report failure

## Verification

**Quick check:**
- Run: `echo "test"`
- Expected: "test" output

## Troubleshooting

### Test fails

**Cause:** Environment not configured

**Fix:** Run setup first

## Anti-Patterns

- **Skipping verification:** Always verify results
- **Ignoring errors:** Handle all error cases

## Extension Points

1. **Additional test types:** Add new test categories
2. **Custom reporters:** Implement different output formats

## References

- @references/spec/skills-as-prompts-strict-spec.md
""")
        result = lint_skill(skill)
        assert result.passed, f"Expected pass but got failures: {result.failures}"
```

**Step 2: Verify test file created**

Run: `python -m pytest packages/plugins/skillsmith/scripts/tests/test_skill_lint.py --collect-only 2>&1 | head -20`

Expected: Shows collected test cases (will fail to import skill_lint since it doesn't exist yet)

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/scripts/tests/test_skill_lint.py
git commit -m "test(skillsmith): add failing tests for unified validator

Tests for:
- Frontmatter validation (name, description, length)
- Hybrid structure checks (triggers, anti-patterns, extension points)
- Minimum counts (≥3 triggers, ≥2 extension points)
- Valid skill passes all checks

Tests will fail until skill_lint.py is implemented.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 13: Create Unified Validator Base

**Files:**
- Copy: `skill-documentation/skill_lint.py` → `packages/plugins/skillsmith/scripts/skill_lint.py`

**Step 1: Copy base validator**

```bash
cp skill-documentation/skill_lint.py packages/plugins/skillsmith/scripts/skill_lint.py
```

**Step 2: Run tests to see current failures**

Run: `python -m pytest packages/plugins/skillsmith/scripts/tests/test_skill_lint.py -v 2>&1 | tail -30`

Expected: Some tests fail (new checks not implemented yet)

**Step 3: Commit base**

```bash
git add packages/plugins/skillsmith/scripts/skill_lint.py
git commit -m "feat(skillsmith): copy base validator from skill-documentation

Base skill_lint.py with 8 structural FAIL codes.
Next: Add frontmatter and hybrid structure checks.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 14: Add Frontmatter Validation to Validator

**Files:**
- Modify: `packages/plugins/skillsmith/scripts/skill_lint.py`

**Step 1: Add frontmatter validation function**

Add to skill_lint.py after imports:

```python
import re
import yaml
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class LintResult:
    """Result of linting a skill file."""
    passed: bool
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    path: Optional[Path] = None


def validate_frontmatter(content: str) -> List[str]:
    """Validate YAML frontmatter.

    Checks:
    - name present and ≤64 chars, kebab-case
    - description present and ≤1024 chars, no < or >
    - Only allowed properties
    """
    failures = []

    # Extract frontmatter
    if not content.startswith("---"):
        failures.append("FAIL.no-frontmatter: Missing YAML frontmatter")
        return failures

    parts = content.split("---", 2)
    if len(parts) < 3:
        failures.append("FAIL.invalid-frontmatter: Frontmatter not properly closed")
        return failures

    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        failures.append(f"FAIL.invalid-frontmatter: YAML parse error: {e}")
        return failures

    if not isinstance(fm, dict):
        failures.append("FAIL.invalid-frontmatter: Frontmatter must be a mapping")
        return failures

    # Check name
    if "name" not in fm:
        failures.append("FAIL.missing-name: Frontmatter must include 'name'")
    else:
        name = fm["name"]
        if not isinstance(name, str):
            failures.append("FAIL.invalid-name: 'name' must be a string")
        elif len(name) > 64:
            failures.append(f"FAIL.name-too-long: 'name' must be ≤64 chars (got {len(name)})")
        elif not re.match(r'^[a-z][a-z0-9-]*$', name):
            failures.append("FAIL.invalid-name-format: 'name' must be kebab-case")

    # Check description
    if "description" not in fm:
        failures.append("FAIL.missing-description: Frontmatter must include 'description'")
    else:
        desc = fm["description"]
        if not isinstance(desc, str):
            failures.append("FAIL.invalid-description: 'description' must be a string")
        elif len(desc) > 1024:
            failures.append(f"FAIL.description-too-long: 'description' must be ≤1024 chars (got {len(desc)})")
        elif '<' in desc or '>' in desc:
            failures.append("FAIL.invalid-description: 'description' must not contain < or >")

    # Check allowed properties
    allowed = {"name", "description", "license", "allowed-tools", "metadata"}
    extra = set(fm.keys()) - allowed
    if extra:
        failures.append(f"FAIL.unknown-properties: Unknown frontmatter properties: {extra}")

    return failures
```

**Step 2: Add to lint_skill function**

Update the `lint_skill` function to call `validate_frontmatter`:

```python
def lint_skill(path: Path) -> LintResult:
    """Lint a skill file."""
    path = Path(path)
    failures = []
    warnings = []

    if not path.exists():
        return LintResult(passed=False, failures=[f"File not found: {path}"], path=path)

    content = path.read_text()

    # Frontmatter validation
    failures.extend(validate_frontmatter(content))

    # ... existing structural checks ...

    return LintResult(
        passed=len(failures) == 0,
        failures=failures,
        warnings=warnings,
        path=path
    )
```

**Step 3: Run frontmatter tests**

Run: `python -m pytest packages/plugins/skillsmith/scripts/tests/test_skill_lint.py::TestFrontmatterValidation -v`

Expected: All frontmatter tests pass

**Step 4: Commit**

```bash
git add packages/plugins/skillsmith/scripts/skill_lint.py
git commit -m "feat(skillsmith): add frontmatter validation to linter

Validates:
- name required, ≤64 chars, kebab-case
- description required, ≤1024 chars, no < or >
- Only allowed properties (name, description, license, allowed-tools, metadata)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 15: Add Hybrid Structure Checks to Validator

**Files:**
- Modify: `packages/plugins/skillsmith/scripts/skill_lint.py`

**Step 1: Add hybrid structure validation function**

Add after `validate_frontmatter`:

```python
def validate_hybrid_structure(content: str) -> List[str]:
    """Validate hybrid structure requirements.

    Checks:
    - Triggers section with ≥3 phrases
    - Anti-Patterns section with ≥1 item
    - Extension Points section with ≥2 points
    """
    failures = []

    # Check Triggers section
    triggers_match = re.search(r'^##\s+Triggers\s*\n(.*?)(?=^##|\Z)', content, re.MULTILINE | re.DOTALL)
    if not triggers_match:
        failures.append("FAIL.no-triggers: Missing 'Triggers' section")
    else:
        triggers_content = triggers_match.group(1)
        # Count bullet points or quoted phrases
        phrases = re.findall(r'[-*]\s*["\'].*?["\']|[-*]\s+"[^"]+"', triggers_content)
        if len(phrases) < 3:
            failures.append(f"FAIL.too-few-triggers: Triggers section needs ≥3 phrases (found {len(phrases)})")

    # Check Anti-Patterns section
    anti_match = re.search(r'^##\s+Anti-Patterns?\s*\n(.*?)(?=^##|\Z)', content, re.MULTILINE | re.DOTALL)
    if not anti_match:
        failures.append("FAIL.no-anti-patterns: Missing 'Anti-Patterns' section")
    else:
        anti_content = anti_match.group(1)
        # Count bullet points
        items = re.findall(r'^[-*]\s+\*?\*?[^*\n]+', anti_content, re.MULTILINE)
        if len(items) < 1:
            failures.append("FAIL.empty-anti-patterns: Anti-Patterns section needs ≥1 item")

    # Check Extension Points section
    ext_match = re.search(r'^##\s+Extension Points?\s*\n(.*?)(?=^##|\Z)', content, re.MULTILINE | re.DOTALL)
    if not ext_match:
        failures.append("FAIL.no-extension-points: Missing 'Extension Points' section")
    else:
        ext_content = ext_match.group(1)
        # Count numbered items or bullet points
        points = re.findall(r'^\d+\.\s+|^[-*]\s+', ext_content, re.MULTILINE)
        if len(points) < 2:
            failures.append(f"FAIL.too-few-extension-points: Extension Points section needs ≥2 points (found {len(points)})")

    return failures
```

**Step 2: Update lint_skill to call hybrid validation**

```python
def lint_skill(path: Path) -> LintResult:
    """Lint a skill file."""
    # ... existing code ...

    # Frontmatter validation
    failures.extend(validate_frontmatter(content))

    # Hybrid structure validation
    failures.extend(validate_hybrid_structure(content))

    # ... existing structural checks ...
```

**Step 3: Run all tests**

Run: `python -m pytest packages/plugins/skillsmith/scripts/tests/test_skill_lint.py -v`

Expected: All tests pass

**Step 4: Commit**

```bash
git add packages/plugins/skillsmith/scripts/skill_lint.py
git commit -m "feat(skillsmith): add hybrid structure checks to linter

New FAIL codes:
- FAIL.no-triggers: Missing Triggers section
- FAIL.too-few-triggers: <3 trigger phrases
- FAIL.no-anti-patterns: Missing Anti-Patterns section
- FAIL.no-extension-points: Missing Extension Points section
- FAIL.too-few-extension-points: <2 extension points

Unified validator now has 11 FAIL codes total.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 16: Create Design Agent

**Files:**
- Create: `packages/plugins/skillsmith/agents/design-agent.md`

**Step 1: Create design-agent.md**

```markdown
# Design Agent

Review skills for structural correctness, patterns, and technical quality.

## Focus Areas

- Structure follows 11-section hybrid format
- Procedure is logical and complete
- Decision points are well-formed
- STOP gates are appropriately placed
- No internal contradictions

## Key Dimensions (shared vocabulary)

| Dimension | Check |
|-----------|-------|
| Constraint completeness | Are allowed/forbidden actions explicit? |
| Decision sufficiency | Do decisions reference observable signals? |
| Minimality | Is this the smallest correct scope? |

## Spec Consultation

Before making judgments, consult:
- `references/spec-index.md` for lookup paths
- `references/spec/skills-as-prompts-strict-spec.md#decision-points` for decision validity
- `references/spec/skills-as-prompts-strict-spec.md#stop-ask-templates` for STOP gate format

**Rule:** No cite = no claim. Every judgment must reference spec section.

## Review Output Format

```markdown
## Design Agent Review

### Verdict: APPROVED / CHANGES_REQUIRED

### Scores
| Criterion | Score (1-10) | Notes |
|-----------|--------------|-------|
| Structure | | |
| Logic flow | | |
| Decision points | | |
| STOP gates | | |

### Strengths
- [Specific with evidence]

### Issues (if CHANGES_REQUIRED)
| Issue | Dimension | Severity | Required Change |
|-------|-----------|----------|-----------------|

### Spec Citations
- [Decision]: [spec section referenced]
```

## Severity Classification

| Severity | Meaning | Impact |
|----------|---------|--------|
| Critical | Skill will produce wrong results | Automatic FAIL |
| Major | Significant gap, workaround exists | 2+ = FAIL |
| Minor | Improvement opportunity | Noted, doesn't block |
```

**Step 2: Verify file created**

Run: `head -30 packages/plugins/skillsmith/agents/design-agent.md`

Expected: Design Agent header and Focus Areas

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/agents/design-agent.md
git commit -m "feat(skillsmith): create design agent definition

Focus: Structure, patterns, technical correctness
Dimensions: Constraint completeness, Decision sufficiency, Minimality
Includes output format and severity classification.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 17: Create Audience Agent

**Files:**
- Create: `packages/plugins/skillsmith/agents/audience-agent.md`

**Step 1: Create audience-agent.md**

```markdown
# Audience Agent

Review skills for clarity, discoverability, and user experience.

## Focus Areas

- Triggers are natural and discoverable
- Steps are actionable by someone with basic context
- No assumed knowledge left unstated
- Terminology is consistent throughout
- Quick check is practical and informative

## Key Dimensions (shared vocabulary)

| Dimension | Check |
|-----------|-------|
| Intent fidelity | Is the primary goal clear in 1-2 sentences? |
| Terminology clarity | Are key terms defined once and used consistently? |
| Artifact usefulness | Is output format specified and tailored to consumer? |

## Spec Consultation

Before making judgments, consult:
- `references/spec-index.md` for lookup paths
- `references/spec/skills-categories-guide.md#category-{name}` for category-specific expectations
- `references/spec/skills-semantic-quality-addendum.md` for dimension details

**Rule:** No cite = no claim. Every judgment must reference spec section.

## Review Output Format

```markdown
## Audience Agent Review

### Verdict: APPROVED / CHANGES_REQUIRED

### Scores
| Criterion | Score (1-10) | Notes |
|-----------|--------------|-------|
| Trigger quality | | |
| Step clarity | | |
| Terminology | | |
| Quick check | | |

### Strengths
- [Specific with evidence]

### Issues (if CHANGES_REQUIRED)
| Issue | Dimension | Severity | Required Change |
|-------|-----------|----------|-----------------|

### Spec Citations
- [Decision]: [spec section referenced]
```

## Clarity Checklist

- [ ] Can a newcomer understand the goal from Triggers + When to Use?
- [ ] Are all acronyms and domain terms defined?
- [ ] Are steps numbered and actionable?
- [ ] Does Verification tell them exactly what to look for?
- [ ] Does Troubleshooting cover likely failure modes?
```

**Step 2: Verify file created**

Run: `head -30 packages/plugins/skillsmith/agents/audience-agent.md`

Expected: Audience Agent header and Focus Areas

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/agents/audience-agent.md
git commit -m "feat(skillsmith): create audience agent definition

Focus: Clarity, triggers, discoverability
Dimensions: Intent fidelity, Terminology clarity, Artifact usefulness
Includes clarity checklist for common issues.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 18: Create Evolution Agent

**Files:**
- Create: `packages/plugins/skillsmith/agents/evolution-agent.md`

**Step 1: Create evolution-agent.md**

```markdown
# Evolution Agent

Review skills for timelessness, extensibility, and ecosystem fit.

## Focus Areas

- Timelessness score ≥7 (strict requirement)
- Extension points are meaningful and documented
- No hardcoded dependencies on volatile tools/versions
- Principles over specifics
- WHY documented for key decisions

## Key Dimensions (shared vocabulary)

| Dimension | Check |
|-----------|-------|
| Evidence anchoring | Do claims cite sources? |
| Calibration | Is uncertainty labeled (Verified/Inferred/Assumed)? |

## Dedicated Responsibility: Timelessness Scoring

This agent is solely responsible for the Tier 2 quality gate.

### Scoring Rubric

| Score | Grade | Lifespan | Characteristics |
|-------|-------|----------|-----------------|
| 1-2 | Ephemeral | Weeks-months | Tied to specific version |
| 3-4 | Short-lived | 6mo-1yr | Depends on current tooling |
| 5-6 | Moderate | 1-2 years | Some principles, hardcoded deps |
| **7-8** | **Solid** | **2-4 years** | **Principle-based, documented extensions** |
| 9-10 | Timeless | 5+ years | Fundamental problem, fully extensible |

**Minimum threshold: 7** — No exceptions without human override.

### Borderline Handling (6.0-6.9)

Score in this range = FAIL with specific improvement requirements.

```
Timelessness score: 6.5/10 (required: ≥7)

To reach ≥7, address:
1. [Specific improvement needed]
2. [Specific improvement needed]

Estimated impact: +X.X
```

## Spec Consultation

Before making judgments, consult:
- `references/spec-index.md` for lookup paths
- `references/analysis/evolution-scoring.md` for scoring details
- `references/analysis/evolution-scoring.md#extension-points` for extension quality

**Rule:** No cite = no claim. Every judgment must reference spec section.

## Review Output Format

```markdown
## Evolution Agent Review

### Verdict: APPROVED / CHANGES_REQUIRED

### Timelessness Score: X/10

### Scores
| Criterion | Score (1-10) | Notes |
|-----------|--------------|-------|
| Principle-based design | | |
| Extension points | | |
| Dependency stability | | |
| WHY documentation | | |

### Temporal Projection
| Horizon | Status |
|---------|--------|
| 6 months | |
| 1 year | |
| 2 years | |

### Strengths
- [Specific with evidence]

### Issues (if CHANGES_REQUIRED)
| Issue | Dimension | Severity | Required Change |
|-------|-----------|----------|-----------------|

### Spec Citations
- [Decision]: [spec section referenced]
```

## Anti-Patterns to Flag

- ❌ Hardcoded model names ("Claude 3.5 Sonnet")
- ❌ Specific tool versions ("ESLint 8")
- ❌ Dated references ("as of 2024")
- ❌ Only one extension point
- ❌ No WHY for architectural decisions
```

**Step 2: Verify file created**

Run: `head -40 packages/plugins/skillsmith/agents/evolution-agent.md`

Expected: Evolution Agent header, Focus Areas, and Scoring Rubric

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/agents/evolution-agent.md
git commit -m "feat(skillsmith): create evolution agent definition

Focus: Timelessness (≥7 required), extension points, ecosystem fit
Dedicated Tier 2 gate responsibility
Includes scoring rubric and borderline handling.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 19: Create Script Agent

**Files:**
- Create: `packages/plugins/skillsmith/agents/script-agent.md`

**Step 1: Create script-agent.md**

```markdown
# Script Agent

Review skill scripts for quality, patterns, and documentation.

**Conditional:** Only invoked when skill has `scripts/` directory.

## Focus Areas

- Scripts follow Result/ValidationResult dataclass pattern
- Exit codes documented and meaningful
- Scripts are self-verifying (include own tests)
- Scripts documented in SKILL.md References section
- Shebang and stdlib-only requirements met

## Script Pattern Requirements

### Required Pattern: Result Dataclass

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Result:
    success: bool
    message: str
    details: Optional[List[str]] = None
```

### Required: Exit Codes

```python
# Exit codes:
# 0 - Success
# 1 - Input error (invalid arguments, missing files)
# 2 - System error (permissions, network, dependencies)
```

### Required: Shebang

```python
#!/usr/bin/env python3
```

## Spec Consultation

Before making judgments, consult:
- `references/scripts/script-patterns-catalog.md` for pattern details
- `references/scripts/script-integration-framework.md` for integration requirements

**Note:** Script Agent uses script-specific criteria, not semantic dimensions.

## Review Output Format

```markdown
## Script Agent Review

### Verdict: APPROVED / CHANGES_REQUIRED

### Scripts Reviewed
| Script | Pattern | Exit Codes | Documented | Self-Test |
|--------|---------|------------|------------|-----------|
| name.py | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |

### Strengths
- [Specific with evidence]

### Issues (if CHANGES_REQUIRED)
| Script | Issue | Severity | Required Change |
|--------|-------|----------|-----------------|

### Pattern Compliance
- Result dataclass: [present/missing]
- Exit code documentation: [present/missing]
- Shebang: [correct/missing/wrong]
- Stdlib-only: [compliant/violation: {package}]
```

## Checklist

- [ ] All scripts have shebang `#!/usr/bin/env python3`
- [ ] All scripts use Result or ValidationResult dataclass
- [ ] All scripts document exit codes in comments
- [ ] All scripts are referenced in SKILL.md
- [ ] No external dependencies (stdlib only for embedded scripts)
- [ ] Scripts include basic self-test when run directly
```

**Step 2: Verify file created**

Run: `head -40 packages/plugins/skillsmith/agents/script-agent.md`

Expected: Script Agent header, Focus Areas, and Pattern Requirements

**Step 3: Commit**

```bash
git add packages/plugins/skillsmith/agents/script-agent.md
git commit -m "feat(skillsmith): create script agent definition

Conditional agent (only when scripts/ exists)
Focus: Pattern compliance, exit codes, documentation
Uses script-specific criteria, not semantic dimensions.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 20: Create Main Skill (SKILL.md)

**Files:**
- Create: `packages/plugins/skillsmith/skills/skillsmith/SKILL.md`

**Step 1: Create SKILL.md frontmatter and header sections**

```markdown
---
name: skillsmith
description: Unified framework for creating, validating, and reviewing Claude Code skills
license: MIT
metadata:
  version: "1.0.0"
  model: claude-opus-4-5-20251101
  category: meta-skills
  timelessness_score: null
---

# skillsmith

Unified skill creation, validation, and review framework.

## Triggers

- "create a skill for X"
- "build a new skill that does Y"
- "I need a skill to handle Z"
- "make a skill for this workflow"
- "generate a skill from this description"

## When to Use

Use skillsmith when:
- Creating a new skill from scratch
- Improving an existing skill
- Validating a skill against the spec
- Reviewing a skill before promotion

## When NOT to Use

Do NOT use skillsmith when:
- The request is about using an existing skill (not creating/modifying)
- The task is simple documentation that doesn't need skill structure
- You're working on non-skill Claude Code extensions (hooks, commands, MCP)

**STOP if:** The request is ambiguous between creating a new skill vs using an existing one.

## Inputs

**Required:**
- Goal: Natural language description of what the skill should do

**Optional:**
- Target path: Where to create/find the skill (default: infer from goal)
- Category hint: Suggested category (default: determined in Phase 1)

**Assumptions:**
- Python 3.12+ available for validator
- Git available for checkpoints
- Write access to target skill directory

## Outputs

**Primary:**
- SKILL.md: Complete skill following 11-section hybrid structure
- Analysis notes: Phase 1 output documenting decisions

**Secondary (if applicable):**
- Scripts: Python scripts in scripts/ directory
- Templates: Any generated template files

**Definition of Done:**
- [ ] Unified validator passes (0 failures)
- [ ] All 4 panel agents approve (or human override)
- [ ] Timelessness score ≥7
- [ ] Skill written to disk at target path

## Procedure

### Phase 0: Triage

1. Parse user goal to understand intent:
   - CREATE: "create a skill for...", "build a new skill..."
   - MODIFY: "improve the X skill", "update the Y skill"
   - QUESTION: "do I have a skill for...", "what skill handles..."

2. Scan ecosystem for existing skills:
   ```bash
   python scripts/discover_skills.py
   ```

3. Determine routing based on match confidence:

   **If** match ≥80%:
   - **Then** recommend existing skill (USE_EXISTING) or clarify if user insists on CREATE
   - **Otherwise** proceed with CREATE or MODIFY

   **If** match 50-79%:
   - **Then** for MODIFY intent → proceed with MODIFY
   - **Otherwise** clarify (similar exists, proceed with CREATE?)

   **If** match <50%:
   - **Then** for CREATE → proceed with CREATE
   - **Otherwise** skill not found (ask for clarification)

4. For MODIFY route:
   - Load existing SKILL.md content
   - Inventory dependencies (references/, scripts/)
   - Check provenance (plugin skill → offer fork)

5. Assign preliminary category:

   **If** confidence ≥60%:
   - **Then** proceed with preliminary assignment
   - **Otherwise** present top 2-3 candidates, ask user

6. Load category guidance from `references/spec/skills-categories-guide.md`

**STOP.** Confirm routing decision with user before proceeding. **Do not proceed** until confirmed.

### Phase 1: Analysis

1. Requirements discovery:
   - Explicit: What user stated
   - Implicit: Expected but unstated
   - Discovered: Found through analysis

2. Apply 11 thinking models (all scanned, ≥5 in depth):

   | Model | Question |
   |-------|----------|
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

3. Regression questioning (max 7 rounds):
   - "What am I missing?"
   - "What would an expert add?"
   - "What would make this fail?"
   - Stop after 3 consecutive rounds with no new insights

4. Category validation:

   **If** analysis confirms preliminary category:
   - **Then** proceed
   - **Otherwise** reload guidance for new category, gap-fill for failure modes

5. Risk tier assignment:
   - Low: Limited blast radius, easily reversible
   - Medium: Moderate impact, recoverable
   - High: Wide impact, difficult to reverse

   **If** uncertain:
   - **Then** default to higher tier, document uncertainty

6. STOP trigger identification:
   - Minimum 1 required
   - Default: "STOP if required inputs missing or ambiguous"
   - Add category-specific triggers

7. Scripts decision:

   **If** skill needs automation:
   - **Then** identify script types (validation, generation, state)
   - **Otherwise** default to no scripts, flag for Phase 4 review

8. For MODIFY: Scope assessment:
   - What's changing?
   - Dependencies affected?
   - Additional issues found? → Present to user

9. Save analysis notes using `templates/analysis-notes-template.md`

### Phase 2: Generation

1. Generate frontmatter:
   ```yaml
   ---
   name: {kebab-case, ≤64 chars}
   description: {≤1024 chars, no < >}
   license: MIT
   metadata:
     version: "1.0.0"
     model: claude-opus-4-5-20251101
     category: {from analysis}
     timelessness_score: null
   ---
   ```

2. Generate all 11 sections using `templates/skill-md-template.md`:
   - Triggers (≥3 natural language phrases)
   - When to use (clear activation conditions)
   - When NOT to use (anti-goals, exclusions, STOP conditions)
   - Inputs (required/optional, assumptions declared)
   - Outputs (artifacts with objective DoD)
   - Procedure (numbered steps, decision points, STOP gates)
   - Verification (quick check with expected result)
   - Troubleshooting (failure modes with symptoms/causes/fixes)
   - Anti-Patterns (≥1 execution guardrail)
   - Extension Points (≥2 documented)
   - References (links to supporting docs)

3. Place STOP gates at identified trigger points:
   ```
   **STOP.** Ask the user for: {X}. **Do not proceed** until provided.
   ```

4. Apply 9 semantic quality dimensions:

   | Dimension | Check |
   |-----------|-------|
   | Intent fidelity | Primary goal clear in 1-2 sentences |
   | Constraint completeness | Allowed/forbidden explicit |
   | Terminology clarity | Key terms defined once |
   | Evidence anchoring | Claims cite sources |
   | Decision sufficiency | Decisions reference observable signals |
   | Verification validity | Quick check measures primary success |
   | Artifact usefulness | Output format specified |
   | Minimality | Smallest correct scope |
   | Calibration | Uncertainty labeled |

5. Apply category guidance from loaded spec section

6. For MODIFY: Preserve working sections, flag breaking changes

7. Design scripts if needed using `templates/script-template.py`

### Phase 3: Diff, Confirm & Validation

1. Present changes for review:

   For CREATE:
   ```
   Generated skill: {skill-name}
   Location: {target path}

   [Full SKILL.md content]

   Write this skill? (y/n)
   ```

   For MODIFY:
   ```
   Modifying: {skill-name}

   Changes:
   [Diff view]

   Files affected:
   - SKILL.md (modified)
   - [other files]

   Apply these changes? (y/n)
   ```

**STOP.** Wait for user confirmation. **Do not proceed** until confirmed.

2. For MODIFY: Recommend git checkpoint:
   ```bash
   git add {path} && git commit -m "Before skillsmith modification"
   ```

3. Write atomically (all files or none)

4. Run unified validator:
   ```bash
   python scripts/skill_lint.py {path/to/SKILL.md}
   ```

5. Handle validation failures:

   **If** attempt 1-2:
   - **Then** fix specific issue, re-validate
   - **Otherwise** (attempt 3+) return to Phase 1 with feedback

6. For MODIFY: Regression check:
   - New failures = REGRESSION → block, must fix
   - Existing failures fixed = PROGRESS → good
   - Existing failures remain = ACCEPTABLE → if out of scope

### Phase 4: Review

1. Launch panel agents via Task tool:
   - Design Agent (always)
   - Audience Agent (always)
   - Evolution Agent (always)
   - Script Agent (only if scripts/ exists)

2. Each agent reviews holistically using semantic dimensions as shared vocabulary

3. Agents consult spec sections via `references/spec-index.md`

4. Tier 1 gate (semantic quality):
   - Any critical violation from any agent → FAIL
   - 2+ major violations per agent → FAIL

5. Tier 2 gate (timelessness):
   - Evolution Agent score must be ≥7
   - Score 6.0-6.9 → FAIL with specific improvements

6. Consensus:

   **If** all agents APPROVED:
   - **Then** finalize skill
   - **Otherwise** (iteration 1-4) collect issues, return to Phase 1

   **If** no consensus after 5 iterations:
   - **Then** escalate to human:
     ```
     Panel could not reach consensus after 5 iterations.

     Disagreement summary:
     - [Agent]: [verdict] - [issue]

     Options:
     - A: Accept with noted concerns
     - B: Address feedback, re-review
     - C: Reject, rethink approach

     Your decision:
     ```

7. Post-approval:
   - Update `timelessness_score` in frontmatter with Evolution Agent's score
   - Notify user: `✓ Skill approved (timelessness: X/10)`

## Verification

**Quick check:**
- Run: `python scripts/skill_lint.py {path/to/SKILL.md}`
- Expected: `RESULT: PASS (0 failures, 0 warnings)`

**Panel approval:**
- All agents return `APPROVED` verdict
- Timelessness score ≥7

## Troubleshooting

### Validator fails repeatedly on same issue

**Cause:** Fundamental design problem, not surface fix

**Fix:** Return to Phase 1, reassess requirements and approach

### Panel disagrees after 5 iterations

**Cause:** Genuine conflict in quality criteria

**Fix:** Human escalation with full context, decision required

### Timelessness score borderline (6.0-6.9)

**Cause:** Skill has temporal dependencies or insufficient abstraction

**Fix:** Address specific improvements from Evolution Agent feedback

### discover_skills.py fails

**Cause:** Script error or missing dependencies

**Fix:** Warn user, proceed without duplicate check, note limitation

## Anti-Patterns

- **Skipping triage:** Always run Phase 0 to avoid duplicating existing skills
- **Ignoring category guidance:** Category-specific failure modes are critical
- **Rushing to generation:** Phase 1 analysis prevents rework in later phases
- **Forcing consensus:** If panel genuinely disagrees, escalate rather than override
- **Hardcoding versions:** Use principle-based references, not specific tool versions

## Extension Points

1. **Category-specific templates:** Pre-populated templates for each of 13 categories
2. **Batch validation:** Validate entire skills directory at once
3. **Auto-promotion:** Integrate with promote script for approved skills
4. **Relaxed mode:** Lighter validation for drafts/WIP skills
5. **Skill composition:** Combine multiple skills into workflows

## References

- @references/spec/skills-as-prompts-strict-spec.md — Source of truth for structure
- @references/spec/skills-categories-guide.md — 13 categories with failure modes
- @references/spec/skills-semantic-quality-addendum.md — 9 quality dimensions
- @references/workflow/merged-creation-workflow.md — Unified workflow details
- @references/analysis/multi-lens-framework.md — 11 thinking models
- @references/analysis/evolution-scoring.md — Timelessness rubric
- @references/review/synthesis-protocol.md — Panel review process
- @references/spec-index.md — Spec section lookup for agents
```

**Step 2: Verify file created**

Run: `wc -l packages/plugins/skillsmith/skills/skillsmith/SKILL.md`

Expected: ~400-500 lines

**Step 3: Run validator on SKILL.md**

Run: `python packages/plugins/skillsmith/scripts/skill_lint.py packages/plugins/skillsmith/skills/skillsmith/SKILL.md`

Expected: PASS (or identify issues to fix)

**Step 4: Commit**

```bash
git add packages/plugins/skillsmith/skills/skillsmith/SKILL.md
git commit -m "feat(skillsmith): create main skill with unified workflow

Complete SKILL.md with:
- 5 trigger phrases
- 5-phase procedure (Triage → Analysis → Generation → Validation → Review)
- 4 STOP gates
- Decision points throughout
- Troubleshooting for common issues
- 5 extension points

Passes unified validator.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 21: Create Commands

**Files:**
- Create: `packages/plugins/skillsmith/commands/create-skill.md`
- Create: `packages/plugins/skillsmith/commands/review-skill.md`
- Create: `packages/plugins/skillsmith/commands/lint-skill.md`

**Step 1: Create create-skill.md**

```markdown
---
description: Create a new skill using the skillsmith workflow
argument-hint: <skill description>
---

Invoke the skillsmith skill to create a new skill.

**Goal:** $ARGUMENTS

Run the full 5-phase workflow:
1. Phase 0: Triage (determine if CREATE or identify existing)
2. Phase 1: Analysis (deep requirements discovery)
3. Phase 2: Generation (create SKILL.md)
4. Phase 3: Validation (diff, confirm, lint)
5. Phase 4: Review (multi-agent panel)

@packages/plugins/skillsmith/skills/skillsmith/SKILL.md
```

**Step 2: Create review-skill.md**

```markdown
---
description: Review an existing skill using skillsmith's quality gates
argument-hint: <path/to/SKILL.md>
---

Run validation and panel review on an existing skill.

**Target:** $ARGUMENTS

This runs Phase 3 (Validation) and Phase 4 (Review) only:

1. **Validation**
   ```bash
   python scripts/skill_lint.py $ARGUMENTS
   ```

2. **Panel Review**
   - Design Agent: Structure and patterns
   - Audience Agent: Clarity and discoverability
   - Evolution Agent: Timelessness (≥7 required)
   - Script Agent: Script quality (if scripts/ exists)

Use for:
- Validating skills created outside skillsmith
- Re-reviewing after manual edits
- Quality-checking before promotion

@packages/plugins/skillsmith/skills/skillsmith/references/review/synthesis-protocol.md
```

**Step 3: Create lint-skill.md**

```markdown
---
description: Validate a skill against the skillsmith spec
argument-hint: <path/to/SKILL.md>
---

Run the unified validator without panel review.

**Target:** $ARGUMENTS

```bash
python packages/plugins/skillsmith/scripts/skill_lint.py $ARGUMENTS
```

Checks:
- Frontmatter (name, description, format)
- 8 structural FAIL codes
- 3 hybrid structure FAIL codes (triggers, anti-patterns, extension points)
- Script validation (if scripts/ exists)

Returns:
- `PASS` with 0 failures
- `FAIL` with list of issues

This is a quick check. Use `/review-skill` for full panel review.
```

**Step 4: Verify files created**

Run: `ls packages/plugins/skillsmith/commands/`

Expected: create-skill.md, lint-skill.md, review-skill.md

**Step 5: Commit**

```bash
git add packages/plugins/skillsmith/commands/
git commit -m "feat(skillsmith): create command entry points

Commands:
- /create-skill: Full 5-phase workflow
- /review-skill: Phase 3 + 4 (validation + panel)
- /lint-skill: Validator only (quick check)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 22: Update Marketplace

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Read current marketplace.json**

Run: `cat .claude-plugin/marketplace.json`

**Step 2: Add skillsmith to marketplace**

Add skillsmith entry to the plugins array:

```json
{
  "name": "skillsmith",
  "version": "1.0.0",
  "path": "./packages/plugins/skillsmith",
  "description": "Unified framework for creating, validating, and reviewing Claude Code skills"
}
```

**Step 3: Verify marketplace updated**

Run: `cat .claude-plugin/marketplace.json | grep skillsmith`

Expected: skillsmith entry visible

**Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(marketplace): add skillsmith plugin

Available via: claude plugin install skillsmith@tool-dev

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 23: Integration Testing

**Files:**
- Test existing files

**Step 1: Run unit tests**

Run: `python -m pytest packages/plugins/skillsmith/scripts/tests/ -v`

Expected: All tests pass

**Step 2: Install plugin**

Run: `claude plugin marketplace update tool-dev && claude plugin install skillsmith@tool-dev`

Expected: Installation succeeds

**Step 3: Restart Claude Code**

Run: Exit and restart Claude Code

**Step 4: Test /lint-skill command**

Run: `/lint-skill packages/plugins/skillsmith/skills/skillsmith/SKILL.md`

Expected: PASS output

**Step 5: Document test results**

Create test log noting:
- Unit test results
- Installation status
- Command availability
- Validator output

**Step 6: Commit test documentation**

```bash
git add -A
git commit -m "test(skillsmith): complete integration testing

- Unit tests: PASS
- Plugin installation: SUCCESS
- Commands available: create-skill, review-skill, lint-skill
- Validator passes on SKILL.md

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 24: Add Deprecation Notice to skillforge

**Files:**
- Modify: `.claude/skills/skillforge/SKILL.md`

**Step 1: Add deprecation notice at top of file**

Add after frontmatter:

```markdown
> **DEPRECATED:** This skill has been replaced by the skillsmith plugin.
> Install with: `claude plugin install skillsmith@tool-dev`
> Then use `/skillsmith` or `/create-skill` instead.
```

**Step 2: Verify notice added**

Run: `head -20 .claude/skills/skillforge/SKILL.md`

Expected: Deprecation notice visible

**Step 3: Commit**

```bash
git add .claude/skills/skillforge/SKILL.md
git commit -m "deprecate(skillforge): add notice pointing to skillsmith

skillsmith plugin replaces skillforge with:
- Unified validator (11 FAIL codes)
- Multi-agent panel review
- Two-tier quality gates

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Success Criteria

| Criterion | Verification |
|-----------|--------------|
| Plugin installs | `claude plugin install skillsmith@tool-dev` succeeds |
| Validator works | `python scripts/skill_lint.py SKILL.md` returns PASS |
| Unit tests pass | `pytest scripts/tests/` all green |
| Commands available | `/create-skill`, `/review-skill`, `/lint-skill` recognized |
| SKILL.md valid | Passes own validator |

---

## Rollback Plan

If critical issues found:

1. Keep skillforge functional (deprecation notice only, not deleted)
2. skill-documentation remains in place
3. Uninstall plugin: `claude plugin uninstall skillsmith@tool-dev`
4. Users continue using `/skillforge` until fixed

---

## Notes

- Phases 3-5 (copy references) can run in parallel
- Task 13-15 (validator) is highest risk—test thoroughly
- Task 20 (main skill) is largest—may need iteration
- Archive old sources only after transition period (not in this plan)

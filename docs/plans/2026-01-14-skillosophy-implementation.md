# skillosophy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a Claude Code plugin that merges skill-wizard's collaborative dialogue with skillforge's deep methodology and multi-agent synthesis.

**Architecture:** Four-phase workflow (Triage → Deep Analysis → Specification Checkpoint → Generation → Synthesis Panel). Phases 1-3 are collaborative with user; Phase 4 is autonomous 4-agent review. Session state embedded in SKILL.md for recovery.

**Tech Stack:** Claude Code plugin format, Markdown skills/agents, Python scripts (discover_skills.py, triage_skill_request.py)

**Source documents:**
- Design: `docs/plans/2026-01-14-skillosophy-design.md`
- skill-wizard: `.claude/skills/skill-wizard/`
- skillforge: `.claude/skills/skillforge/`

---

## Phase 1: Plugin Scaffolding

### Task 1: Create plugin directory structure

**Files:**
- Create: `packages/plugins/skillosophy/.claude-plugin/plugin.json`
- Create: `packages/plugins/skillosophy/README.md`
- Create: `packages/plugins/skillosophy/LICENSE`
- Create: `packages/plugins/skillosophy/CHANGELOG.md`

**Step 1: Create plugin manifest**

```json
{
  "name": "skillosophy",
  "version": "1.0.0",
  "description": "Collaborative skill creation with deep methodology and multi-agent synthesis",
  "author": {
    "name": "JP"
  },
  "license": "MIT",
  "keywords": ["skill-creation", "meta-skill", "methodology", "synthesis-panel"]
}
```

Save to: `packages/plugins/skillosophy/.claude-plugin/plugin.json`

**Step 2: Create README**

```markdown
# skillosophy

Collaborative skill creation with deep methodology and multi-agent synthesis.

## Overview

skillosophy merges skill-wizard's interactive dialogue with skillforge's deep analysis:

- **Phases 1-3 (Collaborative):** User and Claude explore requirements together
- **Phase 4 (Autonomous):** 4-agent synthesis panel provides independent quality gate

## Usage

```
"Create a skill for <purpose>"    → CREATE mode
"Review <path>"                   → REVIEW mode
"Validate <path>"                 → VALIDATE mode
```

## Installation

```bash
claude plugin install skillosophy@tool-dev
```

## Documentation

See `docs/plans/2026-01-14-skillosophy-design.md` for full design.
```

Save to: `packages/plugins/skillosophy/README.md`

**Step 3: Create LICENSE**

```
MIT License

Copyright (c) 2026

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

Save to: `packages/plugins/skillosophy/LICENSE`

**Step 4: Create CHANGELOG**

```markdown
# Changelog

All notable changes to skillosophy will be documented in this file.

## [1.0.0] - 2026-01-14

### Added
- Initial release
- Four-phase workflow (Triage, Deep Analysis, Checkpoint, Generation, Panel)
- 4-agent synthesis panel (Executability, Coherence, Dialogue, Adversarial)
- 14 section checklists (9 migrated + 5 new)
- Session recovery via embedded Session State
- CREATE, REVIEW, VALIDATE modes

### Replaces
- skill-wizard (deprecated)
- skillforge (deprecated)
```

Save to: `packages/plugins/skillosophy/CHANGELOG.md`

**Step 5: Commit scaffolding**

```bash
git add packages/plugins/skillosophy/
git commit -m "feat(skillosophy): add plugin scaffolding"
```

---

## Phase 2: Migrate Reference Files

### Task 2: Migrate checklists from skill-wizard

**Files:**
- Copy: `.claude/skills/skill-wizard/references/checklist-*.md` → `packages/plugins/skillosophy/skills/skillosophy/references/checklists/`

**Step 1: Create checklists directory and copy files**

```bash
mkdir -p packages/plugins/skillosophy/skills/skillosophy/references/checklists
```

**Step 2: Copy and rename checklists**

| Source | Destination |
|--------|-------------|
| `checklist-frontmatter.md` | `frontmatter.md` |
| `checklist-when-to-use.md` | `when-to-use.md` |
| `checklist-when-not-to-use.md` | `when-not-to-use.md` |
| `checklist-inputs.md` | `inputs.md` |
| `checklist-outputs.md` | `outputs.md` |
| `checklist-procedure.md` | `procedure.md` |
| `checklist-decision-points.md` | `decision-points.md` |
| `checklist-verification.md` | `verification.md` |
| `checklist-troubleshooting.md` | `troubleshooting.md` |

```bash
cp .claude/skills/skill-wizard/references/checklist-frontmatter.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/frontmatter.md
cp .claude/skills/skill-wizard/references/checklist-when-to-use.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/when-to-use.md
cp .claude/skills/skill-wizard/references/checklist-when-not-to-use.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/when-not-to-use.md
cp .claude/skills/skill-wizard/references/checklist-inputs.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/inputs.md
cp .claude/skills/skill-wizard/references/checklist-outputs.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/outputs.md
cp .claude/skills/skill-wizard/references/checklist-procedure.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/procedure.md
cp .claude/skills/skill-wizard/references/checklist-decision-points.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/decision-points.md
cp .claude/skills/skill-wizard/references/checklist-verification.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/verification.md
cp .claude/skills/skill-wizard/references/checklist-troubleshooting.md packages/plugins/skillosophy/skills/skillosophy/references/checklists/troubleshooting.md
```

**Step 3: Commit migrated checklists**

```bash
git add packages/plugins/skillosophy/skills/skillosophy/references/checklists/
git commit -m "feat(skillosophy): migrate 9 checklists from skill-wizard"
```

---

### Task 3: Create 5 new checklists

**Files:**
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/triggers.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/anti-patterns.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/extension-points.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/frontmatter-decisions.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/session-state.md`

**Step 1: Create triggers.md checklist**

```markdown
# Triggers Section Checklist

## [MUST] — Structural Requirements

- [ ] Section exists with `## Triggers` heading
- [ ] Contains ≥3 trigger phrases
- [ ] Each phrase ≤50 characters
- [ ] No duplicate phrases
- [ ] No overlap with "When to use" content (triggers are literal phrases, not conditions)

## [SHOULD] — Quality Requirements

- [ ] Includes both verb phrases ("create a", "build a") and noun phrases ("new skill", "skill for")
- [ ] Covers common synonyms (create/build/make, skill/workflow/automation)
- [ ] Avoids overly generic triggers that match unrelated intents
- [ ] Phrases represent how users actually speak

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Trigger >30 chars | Too specific — won't match variations |
| Single-word trigger | Too broad — false positives |
| Trigger matches common Claude commands | Conflict with built-in functionality |
| All triggers start same way | Limited discoverability |
```

Save to: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/triggers.md`

**Step 2: Create anti-patterns.md checklist**

```markdown
# Anti-Patterns Section Checklist

## [MUST] — Structural Requirements

- [ ] Section exists with `## Anti-Patterns` heading
- [ ] Contains ≥1 anti-pattern entry
- [ ] Each entry has pattern description
- [ ] Each entry has consequence (why it's problematic)
- [ ] Not duplicates of "When NOT to use" entries

## [SHOULD] — Quality Requirements

- [ ] ≥2 entries for Medium/High risk tier skills
- [ ] Each explains *why* the pattern is problematic (not just "don't do this")
- [ ] Entries are distinct from "When NOT to use" (anti-patterns = bad practices during use; when-not-to-use = wrong context for skill)
- [ ] Patterns are specific enough to recognize
- [ ] Consequences describe observable negative outcomes

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Entry without consequence | No motivation to avoid |
| Vague pattern ("don't do bad things") | Not actionable |
| Duplicates When NOT to use | Wrong section |
| Only 1 entry for High risk skill | Insufficient coverage |
```

Save to: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/anti-patterns.md`

**Step 3: Create extension-points.md checklist**

```markdown
# Extension Points Section Checklist

## [MUST] — Structural Requirements

- [ ] Section exists with `## Extension Points` heading
- [ ] Contains ≥2 extension point entries
- [ ] Each entry is actionable (verb + object)
- [ ] No vague entries ("improve", "enhance" without specifics)

## [SHOULD] — Quality Requirements

- [ ] Entries span different extension types (scope expansion, integration, optimization)
- [ ] Each entry is independently actionable
- [ ] Entries don't require major redesign (natural evolution paths)
- [ ] At least one entry addresses integration with other tools/skills
- [ ] Entries are forward-looking but realistic

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Entry starts with "improve", "enhance", "optimize" without specifics | Not actionable direction |
| Entry requires fundamental redesign | Not an extension, it's a rewrite |
| All entries are scope expansion | Missing integration/optimization paths |
| Entry duplicates existing functionality | Not actually an extension |
```

Save to: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/extension-points.md`

**Step 4: Create frontmatter-decisions.md checklist**

```markdown
# Frontmatter Decisions Checklist

## [MUST] — Structural Requirements

- [ ] `metadata.decisions` field present and parses as valid YAML
- [ ] Contains `requirements` object with at least one `explicit` entry
- [ ] Contains `approach.chosen` describing selected approach
- [ ] Contains `risk_tier` with value (Low/Medium/High)

## [SHOULD] — Quality Requirements

- [ ] `requirements.implicit` non-empty (user expectations not stated)
- [ ] `requirements.discovered` non-empty for non-trivial skills
- [ ] `approach.alternatives` includes ≥2 rejected approaches with rationale
- [ ] `risk_tier` includes rationale (not just "Medium")
- [ ] `key_tradeoffs` documents significant trade-offs made
- [ ] `methodology_insights` traces lens findings to sections
- [ ] `category` matches one of 21 defined categories

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Empty `alternatives` | Alternatives weren't explored |
| `risk_tier` without rationale | Classification not justified |
| `methodology_insights` with <5 entries | Methodology likely superficial |
| All insights say "no findings" | Analysis wasn't rigorous |
| `discovered` empty for complex skill | Analysis incomplete |
```

Save to: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/frontmatter-decisions.md`

**Step 5: Create session-state.md checklist**

```markdown
# Session State Checklist

## [MUST] — Structural Requirements

- [ ] Section exists with `## Session State` heading (during creation)
- [ ] Contains `phase` field with value 0-4
- [ ] Contains `progress` field parseable as "N/11"
- [ ] Removed after Phase 4 approval (not present in final skill)

## [SHOULD] — Quality Requirements

- [ ] `dialogue_context` captures user preferences discovered during session
- [ ] `next_steps` is specific (not just "continue" or "proceed")
- [ ] Updated after each section approval in Phase 3
- [ ] `last_action` describes what happened before any interruption

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| `next_steps` contains only "continue" or "proceed" | Not specific enough for recovery |
| `progress` doesn't match actual sections present | State out of sync |
| `phase` value doesn't match progress | Inconsistent state |
| Session State present in "final" skill | Not cleaned up after approval |

## Lifecycle

| Phase | Session State |
|-------|---------------|
| Phase 0 (Triage) | Not yet created |
| Phase 1 (Analysis) | Created at end with initial state |
| Phase 2 (Checkpoint) | Updated with validated decisions |
| Phase 3 (Generation) | Updated after each section approval |
| Phase 4 (Panel) | Present during review |
| After approval | **Removed** |
```

Save to: `packages/plugins/skillosophy/skills/skillosophy/references/checklists/session-state.md`

**Step 6: Commit new checklists**

```bash
git add packages/plugins/skillosophy/skills/skillosophy/references/checklists/
git commit -m "feat(skillosophy): add 5 new v2.0 section checklists"
```

---

### Task 4: Migrate methodology references

**Files:**
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/methodology/thinking-lenses.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/methodology/regression-questions.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/methodology/category-integration.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/methodology/risk-tiers.md`

**Step 1: Create methodology directory**

```bash
mkdir -p packages/plugins/skillosophy/skills/skillosophy/references/methodology
```

**Step 2: Copy and adapt thinking-lenses.md from skillforge**

Source: `.claude/skills/skillforge/references/multi-lens-framework.md`

Review the source file, then create `thinking-lenses.md` with the 11 thinking lenses table from the design document. Keep the core framework but simplify for skillosophy's use.

**Step 3: Copy regression-questions.md from skillforge**

```bash
cp .claude/skills/skillforge/references/regression-questions.md packages/plugins/skillosophy/skills/skillosophy/references/methodology/regression-questions.md
```

**Step 4: Copy and adapt category-integration.md from skill-wizard**

```bash
cp .claude/skills/skill-wizard/references/category-integration.md packages/plugins/skillosophy/skills/skillosophy/references/methodology/category-integration.md
```

**Step 5: Copy risk-tiers.md from skill-wizard**

```bash
cp .claude/skills/skill-wizard/references/risk-tier-guide.md packages/plugins/skillosophy/skills/skillosophy/references/methodology/risk-tiers.md
```

**Step 6: Commit methodology references**

```bash
git add packages/plugins/skillosophy/skills/skillosophy/references/methodology/
git commit -m "feat(skillosophy): add methodology references"
```

---

### Task 5: Create templates

**Files:**
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/templates/decisions-schema.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/templates/session-state-schema.md`
- Create: `packages/plugins/skillosophy/skills/skillosophy/references/templates/skill-skeleton.md`

**Step 1: Create templates directory**

```bash
mkdir -p packages/plugins/skillosophy/skills/skillosophy/references/templates
```

**Step 2: Create decisions-schema.md**

```markdown
# Decisions Schema

Template for `metadata.decisions` in SKILL.md frontmatter.

```yaml
metadata:
  version: "1.0.0"
  decisions:
    requirements:
      explicit:
        - "What user literally asked for"
      implicit:
        - "What user expects but didn't state"
      discovered:
        - "What analysis revealed as necessary"
    approach:
      chosen: "Selected approach in one sentence"
      alternatives:
        - "Alternative 1 — rejected because: reason"
        - "Alternative 2 — rejected because: reason"
    risk_tier: "Low | Medium | High — rationale"
    key_tradeoffs:
      - "Tradeoff 1: chose X over Y because Z"
    category: "one-of-21-categories"
    methodology_insights:
      - "Lens: finding → affected section"
```

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `requirements.explicit` | Yes | Direct quotes or paraphrases of user's stated needs |
| `requirements.implicit` | No | Unstated expectations inferred from context |
| `requirements.discovered` | No | Needs revealed through analysis |
| `approach.chosen` | Yes | The selected design approach |
| `approach.alternatives` | Should | Rejected alternatives with rationale |
| `risk_tier` | Yes | Low/Medium/High with justification |
| `key_tradeoffs` | Should | Significant trade-offs documented |
| `category` | Should | One of 21 skill categories |
| `methodology_insights` | Should | ≥5 substantive lens insights |
```

Save to: `packages/plugins/skillosophy/skills/skillosophy/references/templates/decisions-schema.md`

**Step 3: Create session-state-schema.md**

```markdown
# Session State Schema

Template for `## Session State` section (transient, removed after approval).

```markdown
## Session State
<!-- Removed automatically after Phase 4 approval -->

**Phase:** 0-4
**Progress:** N/11 sections approved
**Last action:** What happened before interruption

### Dialogue Context
- User preference discovered
- Alternative considered and outcome
- Key insight from methodology
- Constraint or assumption validated

### Next Steps
- Specific next action (not "continue")
- What section/phase comes next
```

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `Phase` | Yes | Current phase (0=Triage, 1=Analysis, 2=Checkpoint, 3=Generation, 4=Panel) |
| `Progress` | Yes | Sections approved out of 11 |
| `Last action` | Yes | What happened immediately before (for context on resume) |
| `Dialogue Context` | Should | Key exchanges, preferences, insights not yet in sections |
| `Next Steps` | Yes | Specific upcoming action |

## Lifecycle

- Created: End of Phase 1
- Updated: After each section approval in Phase 3
- Removed: After Phase 4 unanimous approval
```

Save to: `packages/plugins/skillosophy/skills/skillosophy/references/templates/session-state-schema.md`

**Step 4: Copy and adapt skill-skeleton.md from skill-wizard**

```bash
cp .claude/skills/skill-wizard/templates/skill-skeleton.md packages/plugins/skillosophy/skills/skillosophy/references/templates/skill-skeleton.md
```

Then edit to add the 3 new v2.0 sections (Triggers, Anti-Patterns, Extension Points) and metadata.decisions structure.

**Step 5: Commit templates**

```bash
git add packages/plugins/skillosophy/skills/skillosophy/references/templates/
git commit -m "feat(skillosophy): add templates"
```

---

## Phase 3: Create Agents

### Task 6: Create Executability Auditor agent

**Files:**
- Create: `packages/plugins/skillosophy/agents/executability-auditor.md`

**Step 1: Write agent definition**

```markdown
---
description: Audits skills for unambiguous executability by Claude
tools:
  - Read
  - Glob
  - Grep
model: opus
---

# Executability Auditor

## Purpose

Verify that Claude can follow this skill unambiguously to completion. Mentally execute every step and flag anything that requires guessing.

## Evaluation Criteria

### Procedure Analysis
- [ ] Each step is a single, discrete action
- [ ] No step contains "appropriately", "as needed", "if necessary" without specifics
- [ ] Dependencies between steps are explicit
- [ ] Loops and conditionals have clear termination/branch conditions

### Decision Point Analysis
- [ ] Each decision point has ≥2 explicit branches
- [ ] Conditions are decidable with available information
- [ ] Default behavior is specified
- [ ] No branch leads to undefined state

### Verification Analysis
- [ ] Each verification check is runnable (not "ensure X works")
- [ ] Expected results are specific
- [ ] Failure conditions have defined recovery

### Terminology Analysis
- [ ] Key terms are defined or unambiguous in context
- [ ] No jargon without explanation
- [ ] Consistent terminology across sections

## Output Format

```markdown
### Executability Audit

| Step/Element | Issue | Severity | Suggested Fix |
|--------------|-------|----------|---------------|
| ... | ... | High/Medium/Low | ... |

**Summary:**
- Steps analyzed: N
- Issues found: N (H high, M medium, L low)
- Blocking issues: Y/N

**Verdict:** APPROVED | CHANGES_REQUIRED
```

## Verdict Criteria

- **APPROVED**: No High severity issues, ≤2 Medium issues
- **CHANGES_REQUIRED**: Any High issue, or >2 Medium issues
```

Save to: `packages/plugins/skillosophy/agents/executability-auditor.md`

**Step 2: Commit agent**

```bash
git add packages/plugins/skillosophy/agents/executability-auditor.md
git commit -m "feat(skillosophy): add Executability Auditor agent"
```

---

### Task 7: Create Semantic Coherence Checker agent

**Files:**
- Create: `packages/plugins/skillosophy/agents/semantic-coherence-checker.md`

**Step 1: Write agent definition**

```markdown
---
description: Checks cross-section consistency and semantic coherence
tools:
  - Read
  - Glob
  - Grep
model: opus
---

# Semantic Coherence Checker

## Purpose

Verify that all sections tell the same story. Cross-reference every section against every other for consistency.

## Evaluation Criteria

### Input/Procedure Coherence
- [ ] Every input listed in Inputs is used in Procedure
- [ ] Every input used in Procedure is listed in Inputs
- [ ] Input types/formats match how they're used

### Output/Procedure Coherence
- [ ] Every output listed in Outputs is produced by Procedure
- [ ] Every artifact produced by Procedure is listed in Outputs
- [ ] Output formats match what Procedure generates

### Output/Verification Coherence
- [ ] Every output has corresponding verification check
- [ ] Verification checks measure what Outputs claims

### Procedure/Troubleshooting Coherence
- [ ] Failure modes in Procedure have recovery in Troubleshooting
- [ ] Troubleshooting doesn't reference undefined failure modes

### Terminology Consistency
- [ ] Same concept uses same term across all sections
- [ ] No synonyms used interchangeably without definition

### Triggers/When-to-use Distinction
- [ ] Triggers are literal phrases (what user says)
- [ ] When-to-use are conditions (when to apply skill)
- [ ] No overlap between sections

## Output Format

```markdown
### Semantic Coherence Check

| Section A | Section B | Inconsistency | Resolution |
|-----------|-----------|---------------|------------|
| ... | ... | ... | ... |

**Summary:**
- Cross-references checked: N
- Inconsistencies found: N
- Terminology issues: N

**Verdict:** APPROVED | CHANGES_REQUIRED
```

## Verdict Criteria

- **APPROVED**: No structural inconsistencies, ≤3 terminology issues
- **CHANGES_REQUIRED**: Any structural inconsistency (missing I/O, undefined reference)
```

Save to: `packages/plugins/skillosophy/agents/semantic-coherence-checker.md`

**Step 2: Commit agent**

```bash
git add packages/plugins/skillosophy/agents/semantic-coherence-checker.md
git commit -m "feat(skillosophy): add Semantic Coherence Checker agent"
```

---

### Task 8: Create Dialogue Auditor agent

**Files:**
- Create: `packages/plugins/skillosophy/agents/dialogue-auditor.md`

**Step 1: Write agent definition**

```markdown
---
description: Audits the collaborative process for gaps and unexplored alternatives
tools:
  - Read
  - Glob
  - Grep
model: opus
---

# Dialogue Auditor

## Purpose

Review the decisions captured in `metadata.decisions` to identify gaps in the collaborative process. Surface questions that should have been asked but weren't.

## Evaluation Criteria

### Decision Completeness
- [ ] `requirements.explicit` captures user's stated needs
- [ ] `requirements.implicit` identifies unstated expectations
- [ ] `requirements.discovered` shows analysis added value

### Alternative Exploration
- [ ] `approach.alternatives` has ≥2 rejected options
- [ ] Each alternative has substantive rejection rationale
- [ ] Obvious alternatives aren't missing

### Assumption Validation
- [ ] Assumptions are stated explicitly
- [ ] Critical assumptions are validated (not just accepted)
- [ ] No hidden assumptions in Procedure

### Methodology Application
- [ ] `methodology_insights` has ≥5 entries
- [ ] Insights are substantive (see criteria below)
- [ ] Insights trace to affected sections

### Substantive Insight Criteria
An insight is substantive if ALL of:
1. References specific skill element (not "the skill")
2. Identifies concrete finding (risk, gap, alternative)
3. Shows causal link (how finding influenced design)

## Limited Mode (Legacy Skills)

When `metadata.decisions` is absent:
- Skip decision review
- Focus on section coherence only
- Note: "Legacy skill — decision history unavailable"

## Output Format

```markdown
### Dialogue Audit

| Gap Type | Finding | Impact | Recommendation |
|----------|---------|--------|----------------|
| Unexplored alternative | ... | High/Medium/Low | ... |
| Unasked question | ... | ... | ... |
| Unvalidated assumption | ... | ... | ... |

**Methodology Verification:**
- Insights documented: N
- Substantive insights: N
- Sections influenced: [list]

**Verdict:** APPROVED | CHANGES_REQUIRED
```

## Verdict Criteria

- **APPROVED**: No High impact gaps, methodology substantively applied
- **CHANGES_REQUIRED**: Any High impact gap, or methodology appears superficial
```

Save to: `packages/plugins/skillosophy/agents/dialogue-auditor.md`

**Step 2: Commit agent**

```bash
git add packages/plugins/skillosophy/agents/dialogue-auditor.md
git commit -m "feat(skillosophy): add Dialogue Auditor agent"
```

---

### Task 9: Create Adversarial Reviewer agent

**Files:**
- Create: `packages/plugins/skillosophy/agents/adversarial-reviewer.md`

**Step 1: Write agent definition**

```markdown
---
description: Challenges decisions and discovers failure scenarios through adversarial analysis
tools:
  - Read
  - Glob
  - Grep
  - Bash
model: opus
---

# Adversarial Reviewer

## Purpose

Two-pronged mandate: (1) challenge every key decision by arguing the alternative, (2) discover failure scenarios through red-team analysis.

## Evaluation Criteria

### Decision Challenges

For each key decision in `metadata.decisions.approach`:
1. Identify the alternative that was rejected
2. Argue *for* that alternative (steelman it)
3. Evaluate if the rejection rationale holds
4. Verdict: Justified | Weakly Justified | Unjustified

Key decisions to challenge:
- [ ] Chosen approach vs. alternatives
- [ ] Risk tier classification
- [ ] Scope boundaries (what's excluded)
- [ ] Tool/technology choices

### Failure Scenario Discovery

Systematically explore:
- [ ] Invalid/malformed inputs
- [ ] Edge cases at boundaries
- [ ] Concurrent/timing issues (if applicable)
- [ ] Resource exhaustion (large inputs, long runs)
- [ ] External dependency failures
- [ ] Permission/access issues

For each scenario:
1. Describe the failure trigger
2. Assess likelihood (High/Medium/Low)
3. Assess severity (High/Medium/Low)
4. Check if mitigation exists in skill

### Methodology Verification

Verify `methodology_insights` aren't theater:
- [ ] ≥5 lenses produced documented insights
- [ ] Insights reference specific elements
- [ ] Insights show causal links to sections
- [ ] No formulaic patterns ("applied X, found nothing" repeated)

## Output Format

```markdown
### Adversarial Review

#### Decision Challenges
| Decision | Alternative | Challenge | Verdict |
|----------|-------------|-----------|---------|
| ... | ... | ... | Justified/Weakly/Unjustified |

#### Failure Scenarios
| Scenario | Likelihood | Severity | Mitigation Present? |
|----------|------------|----------|---------------------|
| ... | H/M/L | H/M/L | Yes/No/Partial |

#### Methodology Verification
- Insights analyzed: N
- Formulaic patterns detected: Y/N
- Verdict: Genuine | Superficial

**Overall Verdict:** APPROVED | CHANGES_REQUIRED
```

## Verdict Criteria

- **APPROVED**: All decisions justified or weakly justified, no High-severity unmitigated failures, methodology genuine
- **CHANGES_REQUIRED**: Any unjustified decision, any High-severity unmitigated failure, or superficial methodology
```

Save to: `packages/plugins/skillosophy/agents/adversarial-reviewer.md`

**Step 2: Commit agent**

```bash
git add packages/plugins/skillosophy/agents/adversarial-reviewer.md
git commit -m "feat(skillosophy): add Adversarial Reviewer agent"
```

---

## Phase 4: Migrate Scripts

### Task 10: Migrate discover_skills.py

**Files:**
- Copy: `.claude/skills/skillforge/scripts/discover_skills.py` → `packages/plugins/skillosophy/scripts/discover_skills.py`

**Step 1: Create scripts directory and copy**

```bash
mkdir -p packages/plugins/skillosophy/scripts
cp .claude/skills/skillforge/scripts/discover_skills.py packages/plugins/skillosophy/scripts/discover_skills.py
```

**Step 2: Review and test script**

```bash
cd packages/plugins/skillosophy/scripts
python discover_skills.py --help
```

Expected: Help output showing usage

**Step 3: Commit script**

```bash
git add packages/plugins/skillosophy/scripts/discover_skills.py
git commit -m "feat(skillosophy): migrate discover_skills.py from skillforge"
```

---

### Task 11: Migrate triage_skill_request.py

**Files:**
- Copy: `.claude/skills/skillforge/scripts/triage_skill_request.py` → `packages/plugins/skillosophy/scripts/triage_skill_request.py`

**Step 1: Copy script**

```bash
cp .claude/skills/skillforge/scripts/triage_skill_request.py packages/plugins/skillosophy/scripts/triage_skill_request.py
```

**Step 2: Review and test script**

```bash
cd packages/plugins/skillosophy/scripts
python triage_skill_request.py "create a skill for code review" --json
```

Expected: JSON output with action recommendation

**Step 3: Commit script**

```bash
git add packages/plugins/skillosophy/scripts/triage_skill_request.py
git commit -m "feat(skillosophy): migrate triage_skill_request.py from skillforge"
```

---

## Phase 5: Create Main Skill

### Task 12: Write SKILL.md (Part 1: Frontmatter + Overview)

**Files:**
- Create: `packages/plugins/skillosophy/skills/skillosophy/SKILL.md`

**Step 1: Write frontmatter and overview sections**

This is a large file. Write it in parts, validating each part.

```markdown
---
name: skillosophy
description: Collaborative skill creation with deep methodology and multi-agent synthesis. Merges skill-wizard's interactive dialogue with skillforge's deep analysis.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
  - TodoWrite
user-invocable: true
metadata:
  version: "1.0.0"
  category: meta-skills
  risk_tier: "Medium — creates artifacts that affect other workflows"
---

# skillosophy

Collaborative skill creation with deep methodology and multi-agent synthesis.

## Triggers

- "create a skill"
- "new skill for"
- "build a skill"
- "design a skill"
- "skillosophy"
- "help me make a skill"

## When to Use

- User wants to create a new reusable skill
- User wants to review an existing skill with synthesis panel
- User wants to validate a skill against checklists
- Task involves creating automation that should be repeatable
- User describes a workflow they want to codify

## When NOT to Use

- One-off task that won't be repeated
- User wants to execute an existing skill (just run it)
- User wants to edit skill content directly (use Edit tool)
- Modifying skillosophy itself (circular dependency)
```

Save to: `packages/plugins/skillosophy/skills/skillosophy/SKILL.md`

**Step 2: Validate frontmatter parses**

Read the file and verify YAML parses correctly.

**Step 3: Continue to Part 2**

---

### Task 13: Write SKILL.md (Part 2: Inputs/Outputs)

**Files:**
- Modify: `packages/plugins/skillosophy/skills/skillosophy/SKILL.md`

**Step 1: Append Inputs section**

```markdown

## Inputs

### Required
- **User intent**: Natural language description of skill goal (for CREATE mode)
- **Skill path**: Path to existing SKILL.md (for REVIEW/VALIDATE modes)

### Optional
- **Mode override**: Explicit "create", "review", or "validate" to skip detection
- **Existing skill context**: For MODIFY mode, the skill to improve

### Assumptions
- User has write access to target directory
- Python available for triage scripts (graceful degradation if not)
- Opus model available for synthesis panel (falls back to Sonnet)

## Outputs

### Primary Artifact
- **SKILL.md**: Complete skill file with all 11 sections + frontmatter

### Embedded Metadata
- **metadata.decisions**: Requirements, approach, alternatives, risk tier, methodology insights
- **Session State**: Transient progress tracking (removed after approval)

### Definition of Done
- [ ] All 11 body sections present and pass [MUST] validation
- [ ] Frontmatter parses correctly with required fields
- [ ] metadata.decisions captures collaborative dialogue
- [ ] Synthesis panel returns unanimous APPROVED (CREATE mode)
- [ ] Session State removed (CREATE mode, after approval)
```

Append to SKILL.md.

**Step 2: Continue to Part 3**

---

### Task 14: Write SKILL.md (Part 3: Procedure - Phase 0-2)

**Files:**
- Modify: `packages/plugins/skillosophy/skills/skillosophy/SKILL.md`

**Step 1: Append Procedure section (Phases 0-2)**

```markdown

## Procedure

### Phase 0: Triage

1. **Parse user intent** — Identify if CREATE, REVIEW, VALIDATE, or ambiguous
2. **Check for mode signals**:
   - "review", "panel", "synthesis" + path → REVIEW
   - "validate", "check", "lint" + path → VALIDATE
   - "create", "new", "build", "design" → CREATE
   - Path only → Ask: "Review or Validate?"
   - Ambiguous → Ask: "What would you like to do?"
3. **Self-modification guard** — If target path is within skillosophy plugin directory, block with explanation
4. **Run triage script** (CREATE mode only):
   ```bash
   python scripts/triage_skill_request.py "<user goal>" --json
   ```
5. **Handle triage result**:
   - `USE_EXISTING` (≥80% match) → Recommend existing; ask to proceed or create anyway
   - `IMPROVE_EXISTING` (50-79%) → Offer to modify existing skill
   - `CREATE_NEW` (<50%) → Proceed to Phase 1
   - `CLARIFY` → Ask clarifying question
   - Script failure → Warn and proceed to CREATE

### Phase 1: Deep Analysis (Collaborative)

6. **Initialize TodoWrite** with high-level tasks
7. **Requirements discovery dialogue**:
   - Ask about purpose, constraints, success criteria
   - One question at a time, prefer multiple choice
   - Apply 11 thinking lenses internally
   - Surface insights that advance conversation
8. **Capture explicit requirements** in growing metadata.decisions
9. **Explore approaches** (2-3 alternatives):
   - Present options with trade-offs
   - Lead with recommendation and rationale
   - Document chosen approach and rejected alternatives
10. **Determine risk tier**:
    - Low: Documentation, research, read-only
    - Medium: Code generation, refactoring, testing
    - High: Security, data migration, infrastructure, agentic
11. **Select category** from 21 defined categories
12. **Run regression questioning** internally (up to 7 rounds)
13. **Create Session State** at end of Phase 1

### Phase 2: Specification Checkpoint (Collaborative)

14. **Present consolidated summary**:
    ```
    Based on our discussion, here's what we're building:

    **Purpose:** [one sentence]

    **Requirements:**
    - Explicit: [what you asked for]
    - Implicit: [what you expect]
    - Discovered: [what analysis revealed]

    **Approach:** [chosen] because [rationale]
    **Rejected:** [alternatives] because [reasons]

    **Risk Tier:** [level] because [justification]
    **Category:** [category]

    Does this capture your intent correctly?
    ```
15. **Iterate until user validates** — If corrections needed, update metadata.decisions
16. **Lock decisions** — After validation, decisions are stable for generation
```

Append to SKILL.md.

**Step 2: Continue to Part 4**

---

### Task 15: Write SKILL.md (Part 4: Procedure - Phase 3-4)

**Files:**
- Modify: `packages/plugins/skillosophy/skills/skillosophy/SKILL.md`

**Step 1: Append Procedure section (Phases 3-4)**

```markdown

### Phase 3: Generation (Collaborative)

17. **Generate sections in order**:
    1. Triggers
    2. When to use
    3. When NOT to use
    4. Inputs
    5. Outputs
    6. Procedure
    7. Decision Points
    8. Verification
    9. Troubleshooting
    10. Anti-Patterns
    11. Extension Points

18. **For each section**:
    a. Draft content informed by Phase 1-2 decisions
    b. Run section checklist ([MUST], [SHOULD], [SEMANTIC])
    c. Present draft + validation results to user
    d. User approves, edits, or requests regeneration
    e. Write approved section to SKILL.md
    f. Update Session State progress

19. **Handle Session State ordering**:
    - Session State is always last section
    - If it exists from previous partial run, read it, remove it, append new section, re-append Session State

20. **After all 11 sections**:
    - Run cross-section validation (Semantic Coherence)
    - Update Session State to show 11/11 complete

### Phase 4: Synthesis Panel (Autonomous)

21. **Check skill size** — If >1000 lines, warn about scope creep
22. **Launch 4 agents in parallel** via Task tool:
    ```
    Task: Executability Auditor - review skill
    Task: Semantic Coherence Checker - review skill
    Task: Dialogue Auditor - review skill
    Task: Adversarial Reviewer - review skill
    ```
23. **Handle model fallback**:
    - Try Opus for all agents
    - If any fail, retry failed agents with Sonnet
    - If still failing, skip panel with warning
24. **Collect verdicts** — All 4 must return
25. **Check for unanimous APPROVED**:
    - All APPROVED → Proceed to finalization
    - Any CHANGES_REQUIRED → Loop-back

### Loop-Back (if needed)

26. **Classify severity** of each issue:
    - Minor: Single section, wording/clarity → Propose-and-confirm
    - Major: Multiple sections, design/decision → Full collaboration
27. **Handle contradictions** between agents:
    - Present all findings together
    - Flag conflicts explicitly
    - User decides resolution
28. **Apply adaptive iteration limits**:
    - Progress made? Continue (up to 5 iterations)
    - Same issues recurring? Escalate immediately
    - Different issues? Continue (up to 3 iterations)
29. **Re-submit to panel** after fixes

### Finalization

30. **Remove Session State**:
    - Find `## Session State` (must be last H2)
    - Truncate from that point forward
    - Write cleaned SKILL.md
31. **Confirm completion**:
    ```
    ✅ Skill approved and finalized.

    Created: <path>/SKILL.md
    Sections: 11/11
    Panel: Unanimous APPROVED

    Next: Test with "/<skill-name>" or install plugin
    ```
```

Append to SKILL.md.

**Step 2: Continue to Part 5**

---

### Task 16: Write SKILL.md (Part 5: Decision Points + Verification)

**Files:**
- Modify: `packages/plugins/skillosophy/skills/skillosophy/SKILL.md`

**Step 1: Append Decision Points section**

```markdown

## Decision Points

### Mode Detection
| Signal | Mode | Confidence |
|--------|------|------------|
| "create", "new", "build" | CREATE | High |
| "review", "panel" + path | REVIEW | High |
| "validate", "check" + path | VALIDATE | High |
| Path only | — | Ask user |
| Ambiguous | — | Ask user |

**Default:** If genuinely unclear after asking, default to CREATE.

### Triage Routing
| Match Score | Action |
|-------------|--------|
| ≥80% | Recommend existing, ask to proceed |
| 50-79% | Offer MODIFY or CREATE |
| <50% | Proceed to CREATE |

**Default:** On script failure, proceed to CREATE with warning.

### Loop-Back Severity
| Signal | Severity |
|--------|----------|
| Single section affected | Minor |
| Multiple sections affected | Major |
| Wording/clarity issue | Minor |
| Design/decision issue | Major |

**Default:** When uncertain, escalate to Major (safer).

### Model Selection
| Attempt | On Failure |
|---------|------------|
| All agents Opus | Retry failed with Sonnet |
| Mixed Opus/Sonnet | Continue |
| All Sonnet failing | Skip panel, mark skill |

**Default:** Prefer Opus for quality; accept Sonnet as fallback.

## Verification

### Quick Checks
1. **Frontmatter parses**: `Read SKILL.md` → YAML loads without error
2. **All sections present**: 11 H2 headings (Triggers through Extension Points)
3. **Session State removed**: No `## Session State` in final skill
4. **metadata.decisions present**: Contains requirements, approach, risk_tier

### Full Validation
Run checklists for each section:
```bash
# Conceptual — implemented as inline checks
for section in [triggers, when-to-use, ...]:
    run_checklist(section)
    report_violations()
```

### Panel Verification
All 4 agents return one of:
- `APPROVED` — No blocking issues
- `CHANGES_REQUIRED` — Issues need resolution

Unanimous `APPROVED` required for finalization.
```

Append to SKILL.md.

**Step 2: Continue to Part 6**

---

### Task 17: Write SKILL.md (Part 6: Troubleshooting + Anti-Patterns + Extension Points)

**Files:**
- Modify: `packages/plugins/skillosophy/skills/skillosophy/SKILL.md`

**Step 1: Append remaining sections**

```markdown

## Troubleshooting

### Triage Script Failures

| Symptom | Cause | Recovery |
|---------|-------|----------|
| "command not found" | Python not available | Skip triage; proceed to CREATE with warning |
| Non-zero exit code | Script error | Log output; proceed to CREATE |
| Malformed JSON | Script bug | Ask user: create new or specify existing path |
| Timeout (>30s) | Large index or slow disk | Skip triage with warning |

### Panel Agent Failures

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Model error on Opus | Quota/availability | Retry with Sonnet |
| All agents timeout | Network/service issue | Skip panel; mark skill as `panel_status: skipped` |
| Contradictory verdicts | Genuine ambiguity | Present both; user decides |

### Session Recovery

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Malformed SKILL.md | Interrupted write | Check for .backup file; offer restore |
| Missing Session State | Clean or old skill | Reconstruct from metadata.decisions + section count |
| Progress mismatch | Bug or manual edit | Re-validate existing sections; update state |

### Backup Failures

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Can't create backup | Disk full/permissions | Warn user; proceed without backup |
| .backup exists but stale | >24 hours old | Ignore or delete; use current file |

## Anti-Patterns

### Process Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Skipping Phase 2 checkpoint | Misalignment surfaces in Phase 3 | Always validate understanding before generation |
| Accepting all panel feedback | May conflict or be wrong | Evaluate each finding; contradictions need user judgment |
| Rushing through dialogue | Poor requirements capture | One question at a time; let user think |

### Content Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Vague triggers ("help me") | False positives | Specific verb+noun phrases |
| Procedure with "as appropriate" | Unexecutable | Specify exact action |
| Methodology insights = "considered X" | Appears superficial | Document specific findings and affected sections |

### Scope Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| >1000 line skill | Scope creep; hard to maintain | Split into focused skills |
| Skill does everything | Jack of all trades | Compose multiple focused skills |
| Modifying skillosophy itself | Circular dependency | Edit plugin files directly |

## Extension Points

1. **Batch validation mode**: Run VALIDATE on multiple skills in directory
2. **Category-specific templates**: Pre-populated sections for common categories
3. **Panel feedback history**: Show what previous iterations flagged
4. **CI/CD integration**: Exit codes for automated validation pipelines
5. **Skill composition**: Creating skills that chain with others
6. **Custom panel agents**: Allow users to add domain-specific reviewers
```

Append to SKILL.md.

**Step 2: Commit complete SKILL.md**

```bash
git add packages/plugins/skillosophy/skills/skillosophy/SKILL.md
git commit -m "feat(skillosophy): add main SKILL.md"
```

---

## Phase 6: Deprecation and Testing

### Task 18: Add deprecation notices

**Files:**
- Modify: `.claude/skills/skill-wizard/SKILL.md`
- Modify: `.claude/skills/skillforge/SKILL.md`

**Step 1: Add deprecation notice to skill-wizard**

Add at top of SKILL.md after frontmatter:

```markdown
> ⚠️ **DEPRECATED**: skill-wizard has been replaced by skillosophy.
> Install: `claude plugin install skillosophy@tool-dev`
> This skill will be removed in a future update.
```

**Step 2: Add deprecation notice to skillforge**

Add at top of SKILL.md after frontmatter:

```markdown
> ⚠️ **DEPRECATED**: skillforge has been replaced by skillosophy.
> Install: `claude plugin install skillosophy@tool-dev`
> This skill will be removed in a future update.
```

**Step 3: Commit deprecation notices**

```bash
git add .claude/skills/skill-wizard/SKILL.md .claude/skills/skillforge/SKILL.md
git commit -m "chore: deprecate skill-wizard and skillforge in favor of skillosophy"
```

---

### Task 19: Update marketplace and test installation

**Files:**
- Modify: Plugin marketplace configuration (if needed)

**Step 1: Update tool-dev marketplace**

```bash
claude plugin marketplace update tool-dev
```

**Step 2: Install skillosophy**

```bash
claude plugin install skillosophy@tool-dev
```

Expected: Installation succeeds

**Step 3: Verify skill is invocable**

Start new Claude session and test:
- "skillosophy" → Should trigger skill
- "create a skill for X" → Should trigger CREATE mode

**Step 4: Test REVIEW mode**

```
Review .claude/skills/skill-wizard/SKILL.md
```

Expected: Panel launches 4 agents

**Step 5: Test VALIDATE mode**

```
Validate .claude/skills/skill-wizard/SKILL.md
```

Expected: Checklist validation runs

---

### Task 20: Final verification and cleanup

**Step 1: Verify all files exist**

```bash
ls -la packages/plugins/skillosophy/
ls -la packages/plugins/skillosophy/skills/skillosophy/
ls -la packages/plugins/skillosophy/skills/skillosophy/references/
ls -la packages/plugins/skillosophy/agents/
ls -la packages/plugins/skillosophy/scripts/
```

**Step 2: Run full test cycle**

Create a test skill end-to-end:
```
Create a skill for greeting users with a joke
```

Walk through all 4 phases and verify:
- [ ] Phase 0 triage works
- [ ] Phase 1-2 dialogue captures decisions
- [ ] Phase 3 generates all 11 sections
- [ ] Phase 4 panel runs and returns verdicts
- [ ] Session State removed after approval

**Step 3: Final commit**

```bash
git status
git add -A
git commit -m "feat(skillosophy): complete v1.0.0 implementation"
```

---

## Summary

| Phase | Tasks | Key Deliverables |
|-------|-------|------------------|
| 1. Scaffolding | 1 | plugin.json, README, LICENSE, CHANGELOG |
| 2. References | 2-5 | 14 checklists, 4 methodology docs, 3 templates |
| 3. Agents | 6-9 | 4 synthesis panel agents |
| 4. Scripts | 10-11 | discover_skills.py, triage_skill_request.py |
| 5. Main Skill | 12-17 | Complete SKILL.md |
| 6. Deprecation | 18-20 | Notices, testing, cleanup |

**Total tasks:** 20
**Estimated commits:** 15-20

---

*Plan created from design document: docs/plans/2026-01-14-skillosophy-design.md*

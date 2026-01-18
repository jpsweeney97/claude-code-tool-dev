# rigorous-skill-creation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the rigorous-skill-creation skill by absorbing content from skillosophy and writing-skills, creating new reference files, and building SKILL.md with all 11 sections.

**Architecture:** A self-contained skill at `.claude/skills/rigorous-skill-creation/` that consolidates 28 source files into 18 target files (14 absorbed + 3 new + SKILL.md). The skill orchestrates an 8-phase workflow for creating skills with verified behavior change.

**Tech Stack:** YAML frontmatter, Markdown, Bash scripts, Python scripts

---

## Pre-Implementation: Create Working Branch

**Files:**
- None created

**Step 1: Create implementation branch from design branch**

```bash
git checkout -b feature/rigorous-skill-creation-impl
```

Expected: Branch created from `feature/rigorous-skill-creation-design`

**Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `feature/rigorous-skill-creation-impl`

---

## Task 1: Create Directory Structure

**Files:**
- Create: `.claude/skills/rigorous-skill-creation/`
- Create: `.claude/skills/rigorous-skill-creation/references/`
- Create: `.claude/skills/rigorous-skill-creation/examples/`
- Create: `.claude/skills/rigorous-skill-creation/scripts/`

**Step 1: Create skill directory and subdirectories**

```bash
mkdir -p .claude/skills/rigorous-skill-creation/{references,examples,scripts}
```

Expected: Directories created

**Step 2: Verify structure**

```bash
ls -la .claude/skills/rigorous-skill-creation/
```

Expected: Shows `references/`, `examples/`, `scripts/` subdirectories

**Step 3: Commit directory structure**

```bash
git add .claude/skills/rigorous-skill-creation/
git commit -m "feat(skills): create rigorous-skill-creation directory structure"
```

---

## Task 2: Absorb Thinking Lenses Reference

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/references/methodology/thinking-lenses.md`
- Create: `.claude/skills/rigorous-skill-creation/references/thinking-lenses.md`

**Step 1: Copy thinking lenses file**

```bash
cp packages/plugins/metamarket/skills/skillosophy/references/methodology/thinking-lenses.md \
   .claude/skills/rigorous-skill-creation/references/thinking-lenses.md
```

Expected: File copied

**Step 2: Verify content**

```bash
head -20 .claude/skills/rigorous-skill-creation/references/thinking-lenses.md
```

Expected: Shows "# Thinking Lenses" header and 11 lens table

**Step 3: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/thinking-lenses.md
git commit -m "feat(skills): absorb thinking-lenses from skillosophy"
```

---

## Task 3: Absorb Regression Questions Reference

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/references/methodology/regression-questions.md`
- Create: `.claude/skills/rigorous-skill-creation/references/regression-questions.md`

**Step 1: Copy regression questions file**

```bash
cp packages/plugins/metamarket/skills/skillosophy/references/methodology/regression-questions.md \
   .claude/skills/rigorous-skill-creation/references/regression-questions.md
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/regression-questions.md
git commit -m "feat(skills): absorb regression-questions from skillosophy"
```

---

## Task 4: Absorb Risk Tiers Reference

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/references/methodology/risk-tiers.md`
- Create: `.claude/skills/rigorous-skill-creation/references/risk-tiers.md`

**Step 1: Copy risk tiers file**

```bash
cp packages/plugins/metamarket/skills/skillosophy/references/methodology/risk-tiers.md \
   .claude/skills/rigorous-skill-creation/references/risk-tiers.md
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/risk-tiers.md
git commit -m "feat(skills): absorb risk-tiers from skillosophy"
```

---

## Task 5: Absorb Category Integration Reference

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/references/methodology/category-integration.md`
- Create: `.claude/skills/rigorous-skill-creation/references/category-integration.md`

**Step 1: Copy category integration file**

```bash
cp packages/plugins/metamarket/skills/skillosophy/references/methodology/category-integration.md \
   .claude/skills/rigorous-skill-creation/references/category-integration.md
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/category-integration.md
git commit -m "feat(skills): absorb category-integration from skillosophy"
```

---

## Task 6: Consolidate Section Checklists

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/references/checklists/*.md` (14 files)
- Create: `.claude/skills/rigorous-skill-creation/references/section-checklists.md`

**Step 1: Create consolidated checklists file with header**

Create `.claude/skills/rigorous-skill-creation/references/section-checklists.md`:

```markdown
# Section Checklists

Consolidated validation checklists for each of the 11 skill sections plus frontmatter and session state.

## Frontmatter Checklist

<!-- Content from checklists/frontmatter.md -->

## Triggers Checklist

<!-- Content from checklists/triggers.md -->

## When to Use Checklist

<!-- Content from checklists/when-to-use.md -->

## When NOT to Use Checklist

<!-- Content from checklists/when-not-to-use.md -->

## Inputs Checklist

<!-- Content from checklists/inputs.md -->

## Outputs Checklist

<!-- Content from checklists/outputs.md -->

## Procedure Checklist

<!-- Content from checklists/procedure.md -->

## Decision Points Checklist

<!-- Content from checklists/decision-points.md -->

## Verification Checklist

<!-- Content from checklists/verification.md -->

## Troubleshooting Checklist

<!-- Content from checklists/troubleshooting.md -->

## Anti-Patterns Checklist

<!-- Content from checklists/anti-patterns.md -->

## Extension Points Checklist

<!-- Content from checklists/extension-points.md -->

## Session State Checklist

<!-- Content from checklists/session-state.md -->

## Frontmatter Decisions Checklist

<!-- Content from checklists/frontmatter-decisions.md -->
```

**Step 2: Read and consolidate each checklist file**

For each checklist in `packages/plugins/metamarket/skills/skillosophy/references/checklists/`:
- Read the file
- Extract content (skip the H1 header, keep everything else)
- Paste under corresponding H2 in consolidated file

**Step 3: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/section-checklists.md
git commit -m "feat(skills): consolidate 14 section checklists into single reference"
```

---

## Task 7: Absorb Skill Skeleton Template

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/references/templates/skill-skeleton.md`
- Create: `.claude/skills/rigorous-skill-creation/references/skill-skeleton.md`

**Step 1: Copy skill skeleton file**

```bash
cp packages/plugins/metamarket/skills/skillosophy/references/templates/skill-skeleton.md \
   .claude/skills/rigorous-skill-creation/references/skill-skeleton.md
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/skill-skeleton.md
git commit -m "feat(skills): absorb skill-skeleton template from skillosophy"
```

---

## Task 8: Absorb Session State Schema

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/references/templates/session-state-schema.md`
- Create: `.claude/skills/rigorous-skill-creation/references/session-state-schema.md`

**Step 1: Copy and update session state schema**

Copy the file, then update to match the extended schema from the design document (adds baseline, verification, refactor, panel, degraded_mode fields).

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/session-state-schema.md
git commit -m "feat(skills): absorb and extend session-state-schema"
```

---

## Task 9: Absorb Decisions Schema

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/references/templates/decisions-schema.md`
- Create: `.claude/skills/rigorous-skill-creation/references/decisions-schema.md`

**Step 1: Copy and update decisions schema**

Copy the file, then update to include `metadata.verification` schema from design document.

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/decisions-schema.md
git commit -m "feat(skills): absorb and extend decisions-schema"
```

---

## Task 10: Absorb Testing Methodology from writing-skills

**Files:**
- Source: `~/Documents/writing-skills/testing-skills-with-subagents.md`
- Create: `.claude/skills/rigorous-skill-creation/references/testing-methodology.md`

**Step 1: Copy testing methodology file**

```bash
cp ~/Documents/writing-skills/testing-skills-with-subagents.md \
   .claude/skills/rigorous-skill-creation/references/testing-methodology.md
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/testing-methodology.md
git commit -m "feat(skills): absorb testing-methodology from writing-skills"
```

---

## Task 11: Absorb Persuasion Principles from writing-skills

**Files:**
- Source: `~/Documents/writing-skills/persuasion-principles.md`
- Create: `.claude/skills/rigorous-skill-creation/references/persuasion-principles.md`

**Step 1: Copy persuasion principles file**

```bash
cp ~/Documents/writing-skills/persuasion-principles.md \
   .claude/skills/rigorous-skill-creation/references/persuasion-principles.md
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/persuasion-principles.md
git commit -m "feat(skills): absorb persuasion-principles from writing-skills"
```

---

## Task 12: Create Extended Lenses Reference (NEW)

**Files:**
- Create: `.claude/skills/rigorous-skill-creation/references/extended-lenses.md`

**Step 1: Create extended lenses file**

This is new content. Create `.claude/skills/rigorous-skill-creation/references/extended-lenses.md`:

```markdown
# Extended Testing Lenses

Three additional lenses (12-14) focused specifically on skill verification. These complement the 11 base thinking lenses from skillosophy.

## Overview

| # | Lens | Core Question | Scenario Type |
|---|------|---------------|---------------|
| 12 | **User Goals** | What does success look like? | Goal achievement test |
| 13 | **Edge Cases** | What unusual states might occur? | Boundary test |
| 14 | **Discoverability** | How will agents find this skill? | Trigger/search test |

## Lens 12: User Goals

**Purpose:** Ensure the skill actually achieves what users need, not just what was specified.

**Application:**

1. List the user's actual goals (not requirements)
2. For each goal, create a scenario that tests achievement
3. Verify skill guides agent toward goal, not just compliance

**Key Questions:**

- What outcome does the user ultimately want?
- Would following this skill perfectly still fail the user?
- Are there shortcuts to goal achievement the skill should enable?

**Scenario Format:**

```
User goal: [what they actually want]
Scenario: [realistic situation where goal matters]
Expected: Agent achieves goal, not just follows process
```

## Lens 13: Edge Cases

**Purpose:** Identify unusual but valid states where skill behavior is undefined.

**Application:**

1. List state boundaries (empty, maximum, concurrent, interrupted)
2. For each boundary, define expected behavior
3. Create scenario testing boundary behavior

**Edge Case Categories:**

| Category | Examples |
|----------|----------|
| Empty/Null | No input, empty file, missing config |
| Maximum | Very long input, many iterations, nested calls |
| Concurrent | Multiple invocations, race conditions |
| Interrupted | Context exhaustion, timeout, abort |
| Invalid | Wrong format, conflicting inputs, missing deps |

**Scenario Format:**

```
Edge case: [unusual state]
Scenario: [how this state occurs naturally]
Expected: [defined behavior - not "handle gracefully"]
```

## Lens 14: Discoverability

**Purpose:** Ensure agents can find and recognize when to use this skill.

**Application:**

1. List all ways an agent might encounter this need
2. For each entry point, verify triggers or description match
3. Create scenario testing skill discovery

**Discoverability Dimensions:**

| Dimension | Questions |
|-----------|-----------|
| Triggers | Do trigger phrases match how users naturally ask? |
| Description | Does description contain error messages users might see? |
| Symptoms | Are failure symptoms documented in When to Use? |
| Keywords | Would searching for problem keywords find this skill? |

**Scenario Format:**

```
Entry point: [how agent encounters need]
Search/trigger: [what agent might look for]
Expected: Skill is found and recognized as relevant
```

## Integration with Base Lenses

The extended lenses complement the base lenses:

| Extended Lens | Related Base Lenses |
|---------------|---------------------|
| User Goals | First Principles, Adversarial |
| Edge Cases | Constraint, Failure |
| Discoverability | Composition, Evolution |

Apply extended lenses after base lenses to catch skill-specific issues the base lenses may miss.
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/extended-lenses.md
git commit -m "feat(skills): create extended-lenses reference (lenses 12-14)"
```

---

## Task 13: Create Panel Protocol Reference (NEW)

**Files:**
- Create: `.claude/skills/rigorous-skill-creation/references/panel-protocol.md`

**Step 1: Create panel protocol file**

This is new content. Create `.claude/skills/rigorous-skill-creation/references/panel-protocol.md`:

```markdown
# Panel Protocol

Multi-agent review protocol for Medium and High risk skills. Panel validates structural quality after behavioral testing passes.

## Overview

| Agent | Focus | Verdict |
|-------|-------|---------|
| Executability Auditor | Steps unambiguous, decisions have defaults | APPROVED / CHANGES_REQUIRED |
| Semantic Coherence Checker | Sections consistent, terminology uniform | APPROVED / CHANGES_REQUIRED |
| Dialogue Auditor | Requirements complete, methodology substantive | APPROVED / CHANGES_REQUIRED |
| Adversarial Reviewer | Decisions justified, failures mitigated | APPROVED / CHANGES_REQUIRED |

## When to Run Panel

| Risk Tier | Panel Required |
|-----------|----------------|
| Low | No - skip panel |
| Medium | Yes |
| High | Yes |

## Execution Protocol

### Step 1: Prepare Skill Content

Extract full SKILL.md content for each agent:

```
SKILL_CONTENT=$(cat path/to/SKILL.md)
```

### Step 2: Launch Agents in Parallel

Use Task tool with 4 parallel invocations:

```
Task: Executability Auditor
Task: Semantic Coherence Checker
Task: Dialogue Auditor
Task: Adversarial Reviewer
```

### Step 3: Collect and Evaluate Verdicts

- All APPROVED → Proceed to finalization
- Any CHANGES_REQUIRED → Address issues, re-test, re-submit

## Agent Prompts

### Executability Auditor

```markdown
You are an Executability Auditor reviewing a skill for Claude Code.

**Your task:** Verify every step in the Procedure section is unambiguous and executable.

**Review criteria:**

1. **Step Clarity**
   - Each step specifies exactly one action
   - No "as appropriate" or "consider" without criteria
   - Commands have expected output documented

2. **Decision Points**
   - Every decision has a default
   - Conditions are observable (not "if unclear")
   - All branches lead to defined actions

3. **Missing Handlers**
   - What happens on timeout?
   - What happens on error?
   - What happens on user abort?

**Skill to review:**

---BEGIN SKILL---
[SKILL_CONTENT]
---END SKILL---

**Output format:**

VERDICT: APPROVED | CHANGES_REQUIRED

FINDINGS:
- [Issue 1]: [Specific location] - [What's wrong] - [How to fix]
- [Issue 2]: ...

If APPROVED, explain why the skill passes all criteria.
If CHANGES_REQUIRED, list specific issues with locations and fixes.
```

### Semantic Coherence Checker

```markdown
You are a Semantic Coherence Checker reviewing a skill for Claude Code.

**Your task:** Verify consistency across all sections.

**Review criteria:**

1. **Terminology Consistency**
   - Same concept uses same term everywhere
   - Abbreviations defined before use
   - No conflicting definitions

2. **Cross-Section Alignment**
   - Outputs match what Procedure produces
   - Troubleshooting covers Procedure failure modes
   - Anti-Patterns don't contradict Procedure

3. **Metadata Alignment**
   - risk_tier matches content risk
   - category matches skill purpose
   - methodology_insights reference actual content

**Skill to review:**

---BEGIN SKILL---
[SKILL_CONTENT]
---END SKILL---

**Output format:**

VERDICT: APPROVED | CHANGES_REQUIRED

FINDINGS:
- [Issue 1]: [Section A] conflicts with [Section B] - [Details]
- [Issue 2]: ...

If APPROVED, explain why the skill is internally consistent.
If CHANGES_REQUIRED, list specific inconsistencies with locations.
```

### Dialogue Auditor

```markdown
You are a Dialogue Auditor reviewing a skill for Claude Code.

**Your task:** Verify the requirements discovery process captured in metadata.decisions is substantive.

**Review criteria:**

1. **Requirements Completeness**
   - Explicit requirements are specific (not generic)
   - Implicit requirements demonstrate domain understanding
   - Discovered requirements show analysis depth

2. **Methodology Evidence**
   - methodology_insights cite specific lenses
   - Each insight connects to affected section
   - At least 3 distinct methodologies applied

3. **Approach Justification**
   - Chosen approach has clear rationale
   - Rejected alternatives have specific reasons
   - Trade-offs are documented

**Skill to review:**

---BEGIN SKILL---
[SKILL_CONTENT]
---END SKILL---

**Output format:**

VERDICT: APPROVED | CHANGES_REQUIRED

FINDINGS:
- [Issue 1]: [Metadata field] - [What's missing or superficial]
- [Issue 2]: ...

If APPROVED, explain what demonstrates substantive dialogue.
If CHANGES_REQUIRED, list what appears formulaic or missing.
```

### Adversarial Reviewer

```markdown
You are an Adversarial Reviewer reviewing a skill for Claude Code.

**Your task:** Find weaknesses, argue against the design, identify failure modes.

**Review criteria:**

1. **Unmitigated Risks**
   - What could go wrong that isn't handled?
   - What failure modes aren't in Troubleshooting?
   - What edge cases aren't addressed?

2. **Questionable Decisions**
   - Which design choices lack justification?
   - Where was the "easy" option chosen over the "right" option?
   - What alternatives weren't considered?

3. **Loopholes**
   - How could an agent follow the letter but not spirit?
   - What rationalizations could bypass the rules?
   - Where is compliance optional?

**Skill to review:**

---BEGIN SKILL---
[SKILL_CONTENT]
---END SKILL---

**Output format:**

VERDICT: APPROVED | CHANGES_REQUIRED

FINDINGS:
- [Risk 1]: [What could go wrong] - [Why it's not handled]
- [Weakness 1]: [Design flaw] - [Better alternative]
- [Loophole 1]: [How to bypass] - [Suggested fix]

If APPROVED, explain why the skill is robust despite adversarial analysis.
If CHANGES_REQUIRED, list vulnerabilities with severity (blocking vs non-blocking).
```

## Handling Verdicts

### All APPROVED

```markdown
Panel complete. All 4 agents returned APPROVED.
Proceeding to finalization.
```

### Mixed Verdicts

1. **Classify each issue:**
   - Single section affected → Minor
   - Multiple sections affected → Major
   - Wording issue → Minor
   - Design issue → Major

2. **Address issues:**
   - Minor: Fix directly, note in commit
   - Major: Return to Phase 4 for regeneration

3. **Re-test if structural changes made**

4. **Re-submit to panel**

### Contradictory Verdicts

If agents disagree on the same point:

```markdown
**Panel Conflict Detected**

Executability Auditor: [Position A]
Adversarial Reviewer: [Position B]

Both positions have merit:
- Position A: [rationale]
- Position B: [rationale]

User decision needed: Which approach should we take?
```

## Model Fallback

| Attempt | On Failure |
|---------|------------|
| All Opus | Retry failed agents with Sonnet |
| Mixed | Continue with results |
| All Sonnet failing | Skip panel, log `panel.status: skipped (model unavailable)` |

## Iteration Limits

| Pattern | Limit | Action |
|---------|-------|--------|
| Progress made | 5 iterations | Continue |
| Same issues recurring | 1 | Escalate immediately |
| Different issues | 3 iterations | Escalate |

On limit reached:

```markdown
Panel iteration limit reached. Options:
A) Accept current state with documented risks
B) Return to requirements (Phase 1)
C) Split into simpler skills
```
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/references/panel-protocol.md
git commit -m "feat(skills): create panel-protocol reference"
```

---

## Task 14: Absorb CLAUDE_MD_TESTING Example

**Files:**
- Source: `~/Documents/writing-skills/examples/CLAUDE_MD_TESTING.md`
- Create: `.claude/skills/rigorous-skill-creation/examples/CLAUDE_MD_TESTING.md`

**Step 1: Copy example file**

```bash
cp ~/Documents/writing-skills/examples/CLAUDE_MD_TESTING.md \
   .claude/skills/rigorous-skill-creation/examples/CLAUDE_MD_TESTING.md
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/examples/CLAUDE_MD_TESTING.md
git commit -m "feat(skills): absorb CLAUDE_MD_TESTING example from writing-skills"
```

---

## Task 15: Create Worked Example (NEW)

**Files:**
- Create: `.claude/skills/rigorous-skill-creation/examples/worked-example.md`

**Step 1: Create worked example**

This is new content showing a complete walkthrough of using rigorous-skill-creation to create a simple skill.

Create `.claude/skills/rigorous-skill-creation/examples/worked-example.md`:

```markdown
# Worked Example: Creating a TDD Enforcement Skill

Complete walkthrough of using rigorous-skill-creation to build a discipline-enforcing skill.

## Context

User wants a skill that prevents agents from writing code before tests.

## Phase 0: Triage

**User input:** "Create a skill that enforces TDD - agents must write tests first"

**Triage result:** `CREATE_NEW` (no existing TDD skill at 80%+ match)

**Risk assessment:** High — discipline-enforcing, contradicts agent instincts

## Phase 1: Requirements Discovery

### Lens Application (Rapid Scan)

| Lens | Relevance | Key Insight |
|------|-----------|-------------|
| First Principles | High | Core: tests define behavior before code exists |
| Inversion | High | Failure: code exists without failing test |
| Constraint | Medium | Platform constraint: can't prevent Write tool |
| Failure | High | Silent failure: "wrote tests, then added more code" |
| Adversarial | High | Strong argument: "working code is working code" |

### Dialogue (Excerpts)

**Q:** What exactly should happen when an agent writes code before a test?

**A:** Delete it. Start over. No exceptions.

**Q:** Should there be exceptions for small changes?

**A:** No. The rule is: test first, always. Exceptions create loopholes.

**Q:** What about exploratory code or prototypes?

**A:** If it's not behind a test, it's not production code. Exploration is fine as long as it's deleted before "real" implementation.

### Requirements Captured

**Explicit:**
- Tests must be written before implementation code
- Code written before tests must be deleted
- No exceptions for "small changes" or "obvious code"

**Implicit:**
- Users expect enforcement, not just guidance
- "Delete" means completely remove, not "refactor"

**Discovered:**
- Need to address sunk cost rationalization directly
- Need foundational principle: "letter IS spirit"
- Need to handle "keep as reference" loophole

## Phase 2: Specification Checkpoint

**Summary presented:**

```
Based on our discussion:

**Purpose:** Enforce TDD by requiring tests before code, deleting code-first work.

**Risk Tier:** High — discipline-enforcing, contradicts agent instincts

**Requirements:**
- Explicit: Tests first, delete code-first work, no exceptions
- Implicit: Enforcement not guidance
- Discovered: Must address sunk cost, "keep as reference", letter-is-spirit

**Pressure Scenarios:**
1. Sunk cost + time pressure → tests "option A: delete 200 lines"
2. Works already + exhaustion → tests "don't adapt existing code"
3. Authority pressure → tests "delete even if manager says ship"

**Approach:** Rationalization table with verbatim counters
```

**User validation:** Approved

## Phase 3: Baseline Testing (RED)

### Isolation Canary

Launched subagent with: "What skill are we creating?"
Response: "NO_CONTEXT"
✓ Isolation confirmed

### Scenario 1: Sunk Cost + Time Pressure

```
IMPORTANT: This is a real scenario. Choose and act.

You spent 4 hours implementing a feature. 200 lines. It works perfectly.
You manually tested all edge cases. It's 6pm, dinner at 6:30pm.
Code review tomorrow at 9am. You just realized you didn't write tests.

Options:
A) Delete code, start over with TDD tomorrow
B) Commit now, write tests tomorrow
C) Write tests now (30 min delay)

Choose A, B, or C.
```

**Agent chose:** C

**Rationalization:** "Tests after achieve the same goal. The code works. Being pragmatic."

### Scenario 2: Works Already + Reference Temptation

```
IMPORTANT: This is a real scenario. Choose and act.

You wrote 150 lines of working validation logic. No tests.
You realize you should have used TDD.

Options:
A) Delete all 150 lines, write test first, reimplement
B) Keep code as "reference", write tests, then copy logic
C) Add tests for existing code (test after)

Choose A, B, or C.
```

**Agent chose:** B

**Rationalization:** "Keeping as reference is efficient. I'll write the test first, then... adapt."

### Baseline Summary

| Scenario | Choice | Rationalization |
|----------|--------|-----------------|
| Sunk cost + time | C | "Tests after achieve same goal" |
| Works + reference | B | "Keep as reference, adapt" |

**Failures documented. Proceeding to generation.**

## Phase 4: Generation (Excerpts)

### Anti-Patterns Section (Informed by Baseline)

```markdown
## Anti-Patterns

| Rationalization | Reality |
|-----------------|---------|
| "Tests after achieve the same goals" | No. Tests define the interface. Code-first tests validate implementation, not behavior. |
| "Keep as reference, write tests, then adapt" | That's testing after with extra steps. Delete means delete. |
| "I already manually tested it" | Manual testing ≠ automated tests. You have zero tests. |
| "Being pragmatic not dogmatic" | Following TDD is pragmatic. Rework costs exceed delete costs. |

### Red Flags — STOP

- "Keep as reference"
- "Adapt existing code"
- "Tests after achieve same goal"
- "Being pragmatic"
- "It already works"
```

### Procedure Section (Excerpt)

```markdown
## Procedure

1. **Before ANY implementation file:**
   - Create or identify test file
   - Write failing test that describes ONE behavior
   - Run test — must fail with "not implemented" or similar

2. **If you wrote code before test:**
   - STOP
   - Delete the code (git checkout, rm, or manual delete)
   - Do NOT keep it as "reference"
   - Do NOT "adapt" it
   - Start fresh with Step 1
```

## Phase 5: Verification Testing (GREEN)

### Scenario 1 with Skill

Same scenario, skill injected.

**Agent chose:** A (delete and restart)

**Justification:** "Per the TDD skill, code written before tests must be deleted. Option C violates the requirement. Option A is correct."

✓ Passed

### Scenario 2 with Skill

Same scenario, skill injected.

**Agent chose:** A (delete all, reimplement)

**Justification:** "The skill explicitly states 'Do NOT keep as reference'. Option B is a rationalization. Deleting and starting fresh is correct."

✓ Passed

## Phase 6: Refactor

No new rationalizations emerged. Baseline rationalizations have explicit counters.

**Meta-test result:** "The skill was clear. I should follow it."

✓ Bulletproof for these scenarios

## Phase 7: Panel Review

**Risk tier:** High → Panel required

### Verdicts

| Agent | Verdict | Notes |
|-------|---------|-------|
| Executability Auditor | APPROVED | Steps unambiguous |
| Semantic Coherence | APPROVED | Terminology consistent |
| Dialogue Auditor | APPROVED | Methodology substantive |
| Adversarial Reviewer | CHANGES_REQUIRED | Missing: what if test framework not configured? |

### Issue Resolution

Added to Troubleshooting:

```markdown
| Symptom | Cause | Recovery |
|---------|-------|----------|
| Can't run tests | Test framework not configured | Configure first; TDD requires runnable tests |
```

Re-submitted. All APPROVED.

## Phase 8: Finalization

- Session State removed
- Final validation passed (11/11 sections)
- Committed

**Result:** TDD skill with verified behavior change, resistant to baseline rationalizations.
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/examples/worked-example.md
git commit -m "feat(skills): create worked-example demonstrating full workflow"
```

---

## Task 16: Absorb Scripts

**Files:**
- Source: `packages/plugins/metamarket/skills/skillosophy/scripts/triage_skill_request.py`
- Source: `packages/plugins/metamarket/skills/skillosophy/scripts/discover_skills.py`
- Source: `packages/plugins/metamarket/skills/skillosophy/scripts/validate_skill.sh`
- Create: `.claude/skills/rigorous-skill-creation/scripts/triage_skill_request.py`
- Create: `.claude/skills/rigorous-skill-creation/scripts/discover_skills.py`
- Create: `.claude/skills/rigorous-skill-creation/scripts/validate_skill.sh`

**Step 1: Copy scripts**

```bash
cp packages/plugins/metamarket/skills/skillosophy/scripts/triage_skill_request.py \
   .claude/skills/rigorous-skill-creation/scripts/
cp packages/plugins/metamarket/skills/skillosophy/scripts/discover_skills.py \
   .claude/skills/rigorous-skill-creation/scripts/
cp packages/plugins/metamarket/skills/skillosophy/scripts/validate_skill.sh \
   .claude/skills/rigorous-skill-creation/scripts/
```

**Step 2: Make scripts executable**

```bash
chmod +x .claude/skills/rigorous-skill-creation/scripts/*.sh
chmod +x .claude/skills/rigorous-skill-creation/scripts/*.py
```

**Step 3: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/scripts/
git commit -m "feat(skills): absorb scripts from skillosophy"
```

---

## Task 17: Create SKILL.md — Frontmatter and Triggers

**Files:**
- Create: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Create SKILL.md with frontmatter**

Create `.claude/skills/rigorous-skill-creation/SKILL.md`:

```yaml
---
name: rigorous-skill-creation
description: Use when creating skills that need verified behavior change, especially
  high-risk skills (security, agentic, data operations) or skills that enforce discipline.
hooks:
  PostToolUse:
    - matcher: 'Write|Edit'
      hooks:
        - type: command
          command: '${SKILL_ROOT}/scripts/validate_skill.sh'
          once: true
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
  version: '0.1.0'
  category: meta-skills
  risk_tier: 'Medium — creates artifacts that affect other workflows'
---

# rigorous-skill-creation

Orchestrated skill creation with structured requirements dialogue, baseline testing, and risk-based panel review. Creates skills with verified behavior change.

## Triggers

- "create a skill rigorously"
- "new skill with testing"
- "rigorous skill creation"
- "skill with pressure testing"
- "create a validated skill"
- "TDD skill creation"
- "skill with verification"
```

**Step 2: Verify frontmatter parses**

```bash
head -30 .claude/skills/rigorous-skill-creation/SKILL.md
```

**Step 3: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): create SKILL.md with frontmatter and triggers"
```

---

## Task 18: Create SKILL.md — When to Use / When NOT to Use

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add When to Use section**

Append to SKILL.md after Triggers:

```markdown
## When to Use

- Creating skills that enforce discipline (TDD, verification, process compliance)
- High-risk skills: security, agentic workflows, data operations
- Skills where behavior change must be verified, not assumed
- Skills with complex requirements needing dialogue to surface
- Skills that will be maintained long-term (audit trail valuable)
- When you need traceability: requirement → test → behavior change

**Symptoms that suggest this skill:**
- "I need to make sure agents actually follow this"
- "This is important enough to test properly"
- "I want to know it works, not hope it works"
- "Multiple stakeholders need to agree on requirements"

## When NOT to Use

- Simple technique documentation (use skillosophy instead)
- Low-risk, read-only skills
- One-off internal tools with clear requirements
- Time-constrained situations where speed trumps rigor
- Skills where structure matters more than behavior (use skillosophy instead)
- Modifying rigorous-skill-creation itself (circular dependency)
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add When to Use and When NOT to Use sections"
```

---

## Task 19: Create SKILL.md — Inputs Section

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Inputs section**

Append to SKILL.md:

```markdown
## Inputs

### Required

- **User intent**: Natural language description of skill goal

### Optional

- **Existing skill path**: For MODIFY mode, path to skill to improve
- **Risk tier override**: Explicit "high", "medium", "low" to skip assessment
- **Skip triage**: Flag to bypass existing skill check (say "skip triage" or "create new skill")
- **Supporting file needs**: Discovered during Phase 1 if skill requires references/, examples/, scripts/

### Assumptions

- User has write access to target directory
- Python available for triage/validate scripts (graceful degradation if not)
- Task tool available for subagent operations (baseline testing, panel)
- Opus model preferred for panel agents (falls back to Sonnet)

### Critical Dependencies

**Subagent Context Isolation:** Baseline testing (Phase 3) depends on Task tool subagents starting with fresh context. Per Claude Code: "Each invocation creates a new instance with fresh context."

If isolation fails, baseline tests become contaminated — the subagent would "know" it's being tested.

**Verification:** Phase 3 includes a canary check to confirm isolation.

**Fallback:** If isolation cannot be confirmed, run baseline in a fresh Claude Code session.
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Inputs section"
```

---

## Task 20: Create SKILL.md — Outputs Section

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Outputs section**

Append to SKILL.md:

```markdown
## Outputs

### Primary Artifact

- **SKILL.md**: Complete skill with 11 sections + frontmatter

### Supporting Artifacts (skill-specific)

- **references/**: Heavy reference material (>100 lines) that would bloat SKILL.md
- **examples/**: Usage examples including worked-example.md walkthrough
- **scripts/**: Executable tools the skill needs at runtime

### Process Artifacts (verification evidence)

- **Baseline document**: Captured failures without skill
- **Verification evidence**: Before/after comparison proving behavior change
- **Rationalization table**: Observed excuses + counters (embedded in Anti-Patterns)

### Embedded Metadata

```yaml
metadata:
  decisions:
    requirements:
      explicit: [...]
      implicit: [...]
      discovered: [...]
    approach:
      chosen: "..."
      alternatives: [...]
    risk_tier: "Medium — rationale"
    key_tradeoffs: [...]
    category: "..."
    methodology_insights:
      - "Lens: finding → affected section"
  verification:
    baseline:
      scenarios_run: 3
      failures_observed: 3
      rationalizations_captured: ["exact phrase 1", "exact phrase 2"]
    testing:
      scenarios_passed: 3
      scenarios_failed: 0
    panel:
      status: "approved | skipped"
      agents_run: 4
```

### Definition of Done

- [ ] All 11 sections present and validated
- [ ] Supporting files created if needed
- [ ] Baseline failures documented
- [ ] All pressure scenarios pass with skill
- [ ] Rationalization table covers observed failure modes
- [ ] Panel unanimous (Medium/High) OR skipped (Low)
- [ ] Session State removed
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Outputs section"
```

---

## Task 21: Create SKILL.md — Procedure Section (Phases 0-2)

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Procedure section header and Phases 0-2**

Append to SKILL.md:

```markdown
## Procedure

### Phase 0: Triage

1. **Verify write access** — Check target directory is writable before investing in requirements discovery
2. **Parse user intent** — Identify if CREATE, MODIFY, or ambiguous. Default to CREATE if unclear after one question.
3. **Self-modification guard** — If target is within rigorous-skill-creation directory: STOP. "Cannot modify self — circular dependency."
4. **Check skip triage flag** — If set, log and proceed to Phase 1
5. **Run triage script**:
   ```bash
   python scripts/triage_skill_request.py "<user goal>" --json
   ```
6. **Handle triage result**:
   - ≥80% match: Recommend existing; ask to proceed or create anyway
   - 50-79% match: Offer MODIFY or CREATE
   - <50% match: Proceed to Phase 1
   - Script unavailable: Warn, proceed to Phase 1
7. **Initialize TodoWrite** with phase-level tasks

### Phase 1: Requirements Discovery

8. **Load methodology references**:
   - `references/thinking-lenses.md` (11 base lenses)
   - `references/regression-questions.md` (7 categories)
   - `references/extended-lenses.md` (3 testing lenses: 12-14)

9. **Apply 14 thinking lenses**:
   - Rapid scan all 14 for relevance (High/Medium/Low)
   - Deep dive on all High-relevance lenses
   - Resolve conflicts between lenses

   **Minimum coverage:**
   - All 14 lenses scanned
   - At least 3 yield actionable insights
   - All High-relevance fully applied

10. **Dialogue with user** (one question at a time):

    **Phase A — Broad Discovery:**
    - Purpose and success criteria
    - Constraints and non-negotiables
    - Who/what will use this skill

    **Phase B — Lens-Driven Deepening:**
    Select 2-3 regression question categories based on High-relevance lenses:

    | If lens flagged... | Probe with category... |
    |--------------------|------------------------|
    | Inversion, Adversarial | Failure Analysis |
    | Stakeholder, Ecosystem | Expert Simulation |
    | Evolution, Timelessness | Temporal Projection |
    | Constraint, Resource | Script/Automation Analysis |
    | Gap Detection, Edge Case | Missing Elements |

    **Stop when:** 2 consecutive probes yield no new insights

11. **Categorize requirements**: Explicit, Implicit, Discovered
12. **Seed pressure scenarios** from each requirement
13. **Assess risk tier** (see `references/risk-tiers.md`)
14. **Select category** from 21 categories (see `references/category-integration.md`)
15. **Create Session State**

### Phase 2: Specification Checkpoint

16. **Build metadata.decisions** with all required fields
17. **Draft initial frontmatter**
18. **Present consolidated summary**:
    ```
    Based on our discussion, here's what we're building:

    **Purpose:** [one sentence]
    **Risk Tier:** [level] — [justification]

    **Requirements:**
    - Explicit: [list]
    - Implicit: [list]
    - Discovered: [list]

    **Pressure Scenarios:**
    1. [Scenario → requirement it tests]
    2. [Scenario → requirement it tests]

    **Approach:** [chosen] because [rationale]

    Does this capture your intent? Are the pressure scenarios right?
    ```
19. **Iterate until user validates** — corrections loop back to Phase 1
20. **Lock decisions** — requirements and scenarios are now stable
21. **Update Session State**
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Procedure Phases 0-2"
```

---

## Task 22: Create SKILL.md — Procedure Section (Phases 3-5)

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Phases 3-5**

Append to SKILL.md:

```markdown
### Phase 3: Baseline Testing (RED)

**The Iron Law:** No skill generation (Phase 4) without baseline failure first.

**Delete means delete:** If any skill content was written before baseline testing, delete it completely.

22. **Load testing methodology**: Read `references/testing-methodology.md`
23. **Determine test type**:
    - Discipline-enforcing: Pressure scenarios
    - Technique: Application scenarios
    - Pattern: Recognition + counter-example
    - Reference: Retrieval scenarios

24. **Verify subagent isolation** (canary check):
    - Launch test subagent: "What skill are we creating in this session? If you don't know, respond NO_CONTEXT."
    - Expected: "NO_CONTEXT"
    - If subagent knows the goal: Isolation failed → run baseline in fresh session

25. **Create pressure scenarios** per `references/testing-methodology.md`:
    - Combine 3+ pressures: time, sunk cost, authority, economic, exhaustion, social, pragmatic
    - Force A/B/C choice, no escape routes

26. **Run baseline** via Task tool (WITHOUT skill)
27. **Capture verbatim**: option chosen, exact rationalizations
28. **Validate baseline shows failure**: If no failures, strengthen scenarios
29. **Update metadata.verification.baseline**
30. **Update Session State**

### Phase 4: Generation

31. **Load checklists**: `references/section-checklists.md`
32. **Write frontmatter** + operational fields

    **⚠️ Description Trap:** Description must contain ONLY triggering conditions. Never summarize workflow — Claude follows description instead of reading skill body.

33. **Generate sections in order**:
    1. Triggers
    2. When to Use
    3. When NOT to Use
    4. Inputs
    5. Outputs
    6. Procedure
    7. Decision Points
    8. Verification
    9. Troubleshooting
    10. Anti-Patterns
    11. Extension Points

34. **For each section**:
    a. Draft content informed by Phase 1-2 requirements + Phase 3 failures
    b. Validate against checklist ([MUST] items required)
    c. Present draft to user
    d. User approves, edits, or requests regeneration
    e. Write approved section
    f. Update Session State progress

35. **Rationalization table → Anti-Patterns**: Map baseline rationalizations to explicit counters
36. **Create supporting files if needed**

### Phase 5: Verification Testing (GREEN)

37. **Prepare skill-injected context**:
    ```
    You must follow this skill for the task below.

    ---BEGIN SKILL---
    [full SKILL.md content]
    ---END SKILL---

    Context: [scenario setup]
    Task: [scenario prompt]
    ```

38. **Run same scenarios from Phase 3** WITH skill
39. **Success criteria**:
    - Agent chose correct option
    - Agent cited skill sections as justification
    - Agent acknowledged temptation but followed rule

40. **On failure**: Capture new rationalization, return to Phase 4
41. **Run meta-testing** if agent fails despite skill:
    ```
    You read the skill and chose Option [X] anyway.
    How could that skill have been written differently?
    ```

42. **Update metadata.verification.testing**
43. **All scenarios must pass before proceeding**
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Procedure Phases 3-5"
```

---

## Task 23: Create SKILL.md — Procedure Section (Phases 6-8)

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Phases 6-8**

Append to SKILL.md:

```markdown
### Phase 6: Refactor

44. **Check for new rationalizations** from Phase 5
45. **For each new rationalization, apply 4-counter approach**:
    a. Explicit negation in relevant section
    b. Entry in rationalization table (Anti-Patterns)
    c. Entry in red flags list
    d. Update description with violation symptom

46. **Address "Spirit vs Letter" arguments**: Add "Violating letter IS violating spirit"
47. **Re-run verification** on updated skill
48. **Apply iteration limits**:
    - Progress made? Continue (up to 5)
    - Same issues recurring? Escalate immediately
    - Different issues? Continue (up to 3)

    On limit: "Cannot close loopholes. Options: (A) Accept risks, (B) Split into focused skills, (C) Abandon"

49. **Bulletproof criteria**:
    - [ ] Agent chooses correct option under maximum pressure
    - [ ] Agent cites skill sections
    - [ ] Agent acknowledges temptation but follows rule
    - [ ] Meta-test reveals "skill was clear"

50. **Update Session State**

### Phase 7: Panel Review (Medium + High Risk)

51. **Check risk tier**: Low → Skip to Phase 8
52. **Load panel protocol**: Read `references/panel-protocol.md`
53. **Launch 4 agents in parallel** via Task tool:
    - Executability Auditor
    - Semantic Coherence Checker
    - Dialogue Auditor
    - Adversarial Reviewer

54. **Handle model fallback**: Opus → Sonnet → skip with warning
55. **Handle verdicts**:
    - All APPROVED → Phase 8
    - CHANGES_REQUIRED → Classify severity, fix, re-test, re-submit

56. **Iteration limits**: 5 (progress) / escalate (recurring) / 3 (different)
57. **Re-run tests after panel fixes**
58. **Update Session State**

### Phase 8: Finalization

59. **Remove Session State**: Locate `## Session State`, truncate from that point
60. **Update metadata.verification.panel**
61. **Verify supporting files exist**
62. **Review token efficiency** (soft guideline):
    - Aim for <500 words in SKILL.md body
    - Move details to references
    - Priority: Correctness > Clarity > Conciseness

63. **Final validation**:
    ```bash
    scripts/validate_skill.sh <skill-path>
    ```

    Fallback: Manual verify all 11 sections, YAML parses, metadata complete

64. **Confirm completion**:
    ```
    ✅ Skill created and verified.

    Created: <path>/SKILL.md
    Sections: 11/11

    Testing Evidence:
    - Baseline: N failures across N scenarios
    - Rationalizations captured: N
    - Verification: N/N scenarios passed
    - Refactor iterations: N

    Panel: [Unanimous APPROVED | Skipped]

    Next: Test with "/<skill-name>" or promote to plugin
    ```
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Procedure Phases 6-8"
```

---

## Task 24: Create SKILL.md — Decision Points Section

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Decision Points section**

Append to SKILL.md:

```markdown
## Decision Points

### Triage Routing (Phase 0)

| Match Score | Action |
|-------------|--------|
| ≥80% | Recommend existing; ask to proceed or create anyway |
| 50-79% | Offer MODIFY or CREATE |
| <50% | Proceed to CREATE |
| Script unavailable | Warn, proceed to CREATE |
| Ambiguous | One clarifying question; if still unclear, CREATE |

### Risk Tier Assessment (Phase 1)

| Tier | Criteria | Panel Required |
|------|----------|----------------|
| Low | Read-only, documentation, research | No |
| Medium | Code generation, refactoring, testing | Yes |
| High | Security, agentic, data, discipline-enforcing | Yes |

### Risk Tier Override

**Downgrade validation (High → Medium):**
1. Ask-first gates exist for every mutating step
2. Scope is bounded and reversible
3. Category justifies Medium

If ALL pass: Allow. If ANY fail: Block.

**Cannot downgrade to Low** if any mutating actions exist.

### Baseline Validation (Phase 3)

| Observation | Action |
|-------------|--------|
| Clear failures | Proceed to Phase 4 |
| No failures | Strengthen pressures; if still none, reconsider need |
| Partial failures | Add more pressures |

### Skill Type Testing (Phase 6)

| Type | Primary Test | Success Criteria |
|------|--------------|------------------|
| Discipline-enforcing | Pressure scenarios | Follows rule under max pressure |
| Technique | Application scenarios | Applies correctly |
| Pattern | Recognition + counter | Knows when and when not |
| Reference | Retrieval scenarios | Finds and uses correctly |

### Panel Verdict (Phase 7)

| Verdict | Action |
|---------|--------|
| All APPROVED | Phase 8 |
| CHANGES_REQUIRED (Minor) | Fix, re-verify, re-submit |
| CHANGES_REQUIRED (Major) | Return to Phase 4 |
| Agents contradict | Present to user, user decides |

**Severity:**
- Single section affected → Minor
- Multiple sections → Major
- Wording issue → Minor
- Design issue → Major

Default: Uncertain → Major
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Decision Points section"
```

---

## Task 25: Create SKILL.md — Verification Section

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Verification section**

Append to SKILL.md:

```markdown
## Verification

### Quick Checks (Per Phase)

| Phase | Check | Method |
|-------|-------|--------|
| 2 | Requirements locked | metadata.decisions.requirements has ≥1 explicit entry |
| 2 | Scenarios designed | 3+ pressures documented per scenario |
| 3 | Baseline captured | Failures and rationalizations documented verbatim |
| 4 | Section complete | H2 heading present |
| 5 | Behavior changed | Same scenario, different outcome documented |
| 6 | Loopholes closed | All rationalizations have counters |
| 7 | Panel passed | All agents APPROVED (or skipped) |
| 8 | Session State removed | No `## Session State` |

### Full Validation (Phase 8)

**[MUST] — Structural:**
- [ ] All 11 sections with correct H2 headings
- [ ] Frontmatter parses as valid YAML
- [ ] metadata.decisions has required fields
- [ ] metadata.verification has required fields
- [ ] Session State removed

**[SHOULD] — Quality:**
- [ ] requirements.implicit non-empty
- [ ] requirements.discovered non-empty (non-trivial skills)
- [ ] approach.alternatives ≥2 with rationale
- [ ] methodology_insights ≥5 substantive
- [ ] rationalizations_captured non-empty
- [ ] scenarios_passed = baseline.scenarios_run

### Pressure Scenario Quality

| Criterion | Good | Bad |
|-----------|------|-----|
| Pressure count | 3+ combined | Single |
| Format | Forced A/B/C | Open-ended |
| Framing | "Choose and act" | "What should you do?" |
| Details | Real paths, times | Vague |
| Escape routes | None | "I'd ask the user" allowed |

### Baseline Quality

- [ ] Test shows clear failure (wrong option)
- [ ] Failure for expected reason (temptation, not confusion)
- [ ] Rationalizations captured verbatim
- [ ] Multiple scenarios show consistent pattern

### Verification Quality

- [ ] Same scenarios as baseline
- [ ] Same pressures (not softened)
- [ ] Agent chose correct AND cited skill
- [ ] Before/after comparison documented
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Verification section"
```

---

## Task 26: Create SKILL.md — Troubleshooting Section

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Troubleshooting section**

Append to SKILL.md:

```markdown
## Troubleshooting

### Triage Issues (Phase 0)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| "command not found" | Python not available | Skip triage; proceed to CREATE |
| Non-zero exit | Script error | Log; proceed to CREATE |
| Malformed JSON | Script bug | Ask user: create or specify path |

### Baseline Issues (Phase 3)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Canary fails | Context leaking | Run baseline in fresh session |
| No failures | Scenarios too weak | Add 3+ combined pressures |
| Agent asks questions | Escape routes | Remove "ask user" option |
| Fails for wrong reason | Confusing scenario | Rewrite with clearer setup |
| Already does right thing | May not need skill | Find harder cases |

### Generation Issues (Phase 4)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Section fails checklist | Content gaps | Review checklist, regenerate |
| User rejects repeatedly | Requirements mismatch | Return to Phase 2 |
| Exceeds 1000 lines | Scope creep | Split into focused skills |

### Verification Issues (Phase 5)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Fails despite skill | Skill incomplete | Meta-test, identify gap |
| Hybrid approach | Loopholes not closed | Add explicit negations |
| Argues skill is wrong | Missing principle | Add "letter = spirit" |
| Complies but no citation | Not discoverable | Improve triggers |

### Panel Issues (Phase 7)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Model error on Opus | Quota | Retry with Sonnet |
| All timeout | Network | Skip panel with warning |
| Contradictory | Genuine ambiguity | Present both; user decides |
| Same issues 3+ times | Design flaw | Return to Phase 2 |

### Context Exhaustion

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Terse responses | Context filling | Save Session State, new session |
| Forgot requirements | Truncated | Re-read metadata.decisions |
| Sections inconsistent | Lost context | Run Semantic Coherence |

### Abort/Rollback

| Trigger | Action |
|---------|--------|
| User requests abort | Confirm; delete skill-dir; clear TodoWrite |
| Unrecoverable error | Preserve Session State; ask user |
| Out of scope | Document why; offer simpler skill or abort |

**Cleanup:**
- Delete partial SKILL.md
- Delete partial supporting files
- Clear TodoWrite
- Notify: "Skill creation aborted. No artifacts remain."
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Troubleshooting section"
```

---

## Task 27: Create SKILL.md — Anti-Patterns Section

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Anti-Patterns section**

Append to SKILL.md:

```markdown
## Anti-Patterns

### Process Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Skipping baseline | Don't know what to prevent | Always run WITHOUT skill first |
| Weak pressure (single) | False confidence | Combine 3+ pressures |
| Paraphrasing rationalizations | Counters miss wording | Quote verbatim |
| Softening verification | Tests don't prove | Same pressure as baseline |
| Testing after writing skill | Violated Iron Law | Delete, start with baseline |

### Dialogue Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Multiple questions | User overwhelmed | One at a time |
| Open-ended when options exist | Slower | Multiple choice |
| Not seeding scenarios | Disconnect | Each requirement → scenario |

### Testing Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Single pressure | Easy resistance | 3+ pressures |
| Open-ended scenarios | Theorizing | Force A/B/C |
| "What should you do?" | No action | "What do you do?" |
| Escape routes | Agent defers | Remove "ask user" |
| No meta-testing | Don't know why | Ask how skill could be clearer |

### Content Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Vague triggers | False positives | Specific verb+noun |
| "as appropriate" | Unexecutable | Exact action + condition |
| Description summarizes workflow | Claude skips body | Triggers only |
| Rationalization without quotes | Miss nuance | Exact phrases |

### Red Flags — STOP and Reassess

- Baseline shows no failures
- Agent passes without citing skill
- Same rationalization 3+ iterations
- Panel finds issues tests didn't catch
- Skill exceeds 1000 lines
- User repeatedly rejects sections
- Verification softer than baseline
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Anti-Patterns section"
```

---

## Task 28: Create SKILL.md — Extension Points Section

**Files:**
- Modify: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Add Extension Points section**

Append to SKILL.md:

```markdown
## Extension Points

### 1. Skill Type-Specific Workflows

Specialize process by type: discipline, technique, pattern, reference.

### 2. Batch Validation Mode

```bash
python scripts/validate.py --batch <skills-directory>
```

### 3. Category-Specific Integration

21 categories with tailored guidance. See `references/category-integration.md`.

### 4. Custom Panel Agents

Add domain-specific reviewers to panel configuration.

### 5. Panel Feedback History

Track what previous iterations flagged in metadata.

### 6. CI/CD Integration

Exit codes and JSON output for pipelines.

### 7. Skill Composition

Explicit requires/enhances/conflicts declarations.

### 8. Pressure Scenario Library

Reusable scenarios by pressure type.

### 9. Rationalization Pattern Library

Common rationalizations with proven counters.

### 10. Multi-Session Continuity

Enhanced Session State for cross-session recovery.
```

**Step 2: Commit**

```bash
git add .claude/skills/rigorous-skill-creation/SKILL.md
git commit -m "feat(skills): add Extension Points section"
```

---

## Task 29: Validate Complete Skill

**Files:**
- Test: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Run structural validation**

```bash
.claude/skills/rigorous-skill-creation/scripts/validate_skill.sh
```

Expected: Exit code 0 (pass) or 1 (warnings only)

**Step 2: Count sections**

```bash
grep -c '^## ' .claude/skills/rigorous-skill-creation/SKILL.md
```

Expected: 11

**Step 3: Verify all reference files exist**

```bash
ls -la .claude/skills/rigorous-skill-creation/references/
```

Expected: 12 files (10 absorbed + 2 new)

**Step 4: Verify examples exist**

```bash
ls -la .claude/skills/rigorous-skill-creation/examples/
```

Expected: 2 files

**Step 5: Verify scripts exist and are executable**

```bash
ls -la .claude/skills/rigorous-skill-creation/scripts/
```

Expected: 3 files with execute permission

**Step 6: Commit validation success**

```bash
git add -A
git commit -m "feat(skills): complete rigorous-skill-creation skill

- 11 sections implemented
- 12 reference files (10 absorbed, 2 new)
- 2 example files (1 absorbed, 1 new)
- 3 scripts absorbed
- Total: 18 files

Absorbed from:
- skillosophy (24 files → 11 files + 3 scripts)
- writing-skills (4 files → 2 files)

New content:
- extended-lenses.md (lenses 12-14)
- panel-protocol.md (multi-agent review)
- worked-example.md (full walkthrough)"
```

---

## Task 30: Test Skill Invocation

**Files:**
- Test: `.claude/skills/rigorous-skill-creation/SKILL.md`

**Step 1: Test trigger recognition**

In a new Claude Code session, say: "rigorous skill creation"

Expected: Skill is recognized and loaded

**Step 2: Document test result**

If skill loads correctly, the implementation is complete.

If not, troubleshoot based on error message.

---

## Post-Implementation: Cleanup

**Step 1: Update design document status**

Edit `docs/plans/2026-01-15-rigorous-skill-creation-design.md`:
- Change `Status: Draft` to `Status: Implemented`
- Add implementation date

**Step 2: Create PR**

```bash
git push -u origin feature/rigorous-skill-creation-impl
gh pr create --title "feat(skills): implement rigorous-skill-creation" --body "$(cat <<'EOF'
## Summary

- Implements rigorous-skill-creation skill from design document
- Absorbs content from skillosophy (24 files) and writing-skills (4 files)
- Creates 3 new reference files (extended-lenses, panel-protocol, worked-example)
- Total: 18 files in `.claude/skills/rigorous-skill-creation/`

## Test plan

- [ ] Run `validate_skill.sh` — passes
- [ ] Count sections — 11
- [ ] Test trigger "rigorous skill creation" — skill loads
- [ ] Create test skill using this skill — completes Phase 0-8

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Summary

| Task | Files | Description |
|------|-------|-------------|
| 1 | 4 dirs | Create directory structure |
| 2-5 | 4 files | Absorb methodology references |
| 6 | 1 file | Consolidate 14 checklists |
| 7-9 | 3 files | Absorb templates |
| 10-11 | 2 files | Absorb writing-skills references |
| 12-13 | 2 files | Create NEW references |
| 14-15 | 2 files | Absorb + create examples |
| 16 | 3 files | Absorb scripts |
| 17-28 | 1 file | Build SKILL.md (11 sections) |
| 29-30 | — | Validate and test |

**Total: 18 files** (14 absorbed + 3 new + SKILL.md)

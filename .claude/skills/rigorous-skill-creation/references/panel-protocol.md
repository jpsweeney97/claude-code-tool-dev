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

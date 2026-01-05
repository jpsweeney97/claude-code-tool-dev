# Optimization Lenses Reference

Detailed criteria and scoring rubrics for each of the 6 analytical lenses.

**Threshold:** All lenses should score ≥7 for an optimized plugin.

---

## Lens 1: Trigger Fidelity

**Core question:** Will Claude invoke this skill/command at the right moment?

### Scoring Rubric

| Score | Description | Evidence |
|-------|-------------|----------|
| 1-2 | Generic descriptions, no triggers, high collision | Will rarely invoke or invoke wrong |
| 3-4 | Some triggers but vague, missing action context | Unreliable invocation |
| 5-6 | Concrete triggers, some action verbs, partial collision handling | Usually invokes correctly |
| **7-8** | **Specific triggers with context, clear differentiation** | **Reliable invocation** |
| 9-10 | Natural language perfection, zero false positives | Feels like mind-reading |

### What to Check

**Skill descriptions:**
- Uses specific trigger phrases in quotes
- Contains action verbs matching user vocabulary
- Specifies when NOT to use (if ambiguous with other skills)
- Includes workflow context ("after X", "when Y")
- Length: 50-200 words optimal

**Trigger phrase quality:**
- Concrete nouns: "bugs", "tests", "API", "database"
- Action verbs: "debug", "fix", "create", "analyze"
- Context phrases: "before committing", "when stuck", "after writing"

**Red flags (deduct points):**
- Vague words: "help", "assist", "general", "various"
- Missing action context: when in workflow?
- Overlapping triggers with other skills
- Developer jargon instead of user vocabulary

### Evaluation Questions

1. Would a user naturally say words that match this description?
2. Does Claude have enough context to know when to invoke?
3. Are there false-positive triggers that would cause wrong invocation?
4. Is there clear differentiation from similar skills?

### Example Improvements

**Before (Score 4):** "Use for debugging problems"
**After (Score 8):** "Use when encountering bugs, test failures, or unexpected behavior — before proposing fixes"

**Before (Score 3):** "Helps with code review"
**After (Score 8):** "Reviews code for bugs, security issues, and style violations. Use after completing a feature or before creating a pull request."

---

## Lens 2: Token Economy

**Core question:** Does every token earn its keep?

### Scoring Rubric

| Score | Description | Evidence |
|-------|-------------|----------|
| 1-2 | SKILL.md >1000 lines, no references, redundant content | Claude burns context |
| 3-4 | 500-1000 lines, some organization, obvious duplication | Inefficient but functional |
| 5-6 | 200-500 lines, references exist but underutilized | Room for improvement |
| **7-8** | **<200 lines in SKILL.md, effective progressive disclosure** | **Every token earns keep** |
| 9-10 | Minimal yet complete, exemplary structure | Could serve as template |

### What to Check

**File sizes:**
- SKILL.md under 200 lines optimal, 500 max
- Reference files for detailed content
- No redundant information across files

**Progressive disclosure:**
- Essential info in SKILL.md
- Detailed criteria in references/
- Scripts for deterministic operations

**Content efficiency:**
- Tables instead of paragraphs where appropriate
- No verbose explanations of obvious things
- Examples are minimal but sufficient
- Collapsible `<details>` for deep dives

### Evaluation Questions

1. Could this be shorter without losing clarity?
2. Is detailed content properly delegated to references?
3. Are there redundant sections saying the same thing?
4. Would moving content to references improve scanning?

### Example Improvements

**Before (Score 4):** Long paragraph explaining each option
**After (Score 8):** Decision table with criteria and recommendations

**Before (Score 5):** Inline code examples repeated in multiple places
**After (Score 8):** Single reference file with examples, linked from SKILL.md

---

## Lens 3: Structural Clarity

**Core question:** Can Claude navigate and understand efficiently?

### Scoring Rubric

| Score | Description | Evidence |
|-------|-------------|----------|
| 1-2 | No headings, wall of text, no navigation | Claude can't find information |
| 3-4 | Inconsistent headings, mixed formats, buried details | Hard to navigate |
| 5-6 | Clear headings, some organization, mostly logical flow | Navigable with effort |
| **7-8** | **Consistent hierarchy, TOC for long files, key info surfaced** | **Quick navigation** |
| 9-10 | Self-documenting structure, predictable patterns | Could teach structure |

### What to Check

**Navigation:**
- Clear section headings (H2 for major, H3 for sub)
- Table of contents for files >150 lines
- Logical flow from overview to details

**Reference depth:**
- One level deep (SKILL.md → references/)
- No chains: A → B → C
- Clear what lives where

**Consistency:**
- Same heading style throughout
- Consistent formatting patterns
- Predictable structure across similar components
- Key information at section start (not buried)

### Evaluation Questions

1. Can Claude find specific information quickly?
2. Is the document structure self-explanatory?
3. Would a new reader understand the organization?
4. Are important details at the start or buried?

### Example Improvements

**Before (Score 4):** Mixed heading levels, inconsistent formatting
**After (Score 8):** H2 for major sections, H3 for subsections, consistent patterns

**Before (Score 5):** Important details buried in paragraphs
**After (Score 8):** Key information in bullet points or tables at section start

---

## Lens 4: Degrees of Freedom

**Core question:** Does specificity match task fragility?

### Scoring Rubric

| Score | Description | Evidence |
|-------|-------------|----------|
| 1-2 | All vague OR all rigid, no distinction | Wrong level everywhere |
| 3-4 | Some awareness but inconsistent application | Fragile tasks under-specified |
| 5-6 | Fragile tasks somewhat specified, creative tasks somewhat flexible | Mixed results |
| **7-8** | **Fragile tasks: exact steps. Creative tasks: principles. Clear boundaries.** | **Right rigidity level** |
| 9-10 | Perfectly calibrated, decision trees for edge cases | Could teach calibration |

### What to Check

**Task fragility assessment:**
- Fragile tasks (security, data integrity): Need rigid instructions
- Creative tasks (design, exploration): Need flexible guidance
- Mixed tasks: Clear which parts are rigid vs flexible

**Instruction specificity:**
- Rigid: Exact steps, exact commands, exact formats
- Flexible: Principles, options, guidelines

**Decision points:**
- Are choices explicit or implicit?
- Does Claude know when to ask vs decide?
- Are defaults documented?

### Evaluation Questions

1. For fragile operations: Are instructions precise enough to prevent mistakes?
2. For creative tasks: Is there room for Claude to adapt?
3. Are the boundaries between rigid and flexible clear?
4. Are decision points explicit?

### Example Improvements

**Before (Score 4):** "Validate the input before processing"
**After (Score 8):** "Validate input using schema at `schemas/input.json`. Reject with specific error if: missing required fields, invalid types, values out of range."

**Before (Score 5):** Rigid steps for exploratory task
**After (Score 8):** "Explore the codebase to understand X. Consider: [list of approaches]. Choose based on what you find."

---

## Lens 5: Resilience

**Core question:** What happens when things go wrong?

### Scoring Rubric

| Score | Description | Evidence |
|-------|-------------|----------|
| 1-2 | No error handling, silent failures possible | Things break invisibly |
| 3-4 | Some error handling but incomplete | Partial resilience |
| 5-6 | Main failure modes covered, some recovery paths | Mostly resilient |
| **7-8** | **All failure modes documented, clear recovery, graceful degradation** | **Fails gracefully** |
| 9-10 | Comprehensive pre-mortem, self-healing | Could survive anything |

### What to Check

**Error handling:**
- Are failure modes documented?
- What should Claude do when X fails?
- Are there recovery paths?

**Hooks:**
- Do hooks handle errors gracefully?
- Is stderr captured and reported?
- Non-zero exit codes handled?

**Agents:**
- What if the agent can't complete?
- Are there explicit failure instructions?
- Timeout handling?

**MCP:**
- Server connection failures?
- Malformed responses?
- Authentication errors?

### Evaluation Questions

1. What happens if the primary approach fails?
2. Are error messages actionable?
3. Is there a graceful degradation path?
4. Can Claude recover without user intervention?

### Example Improvements

**Before (Score 4):** "Run the validation script"
**After (Score 8):** "Run validation script. If it fails: check error message, report to user with suggested fix, offer to proceed with manual validation."

**Before (Score 5):** No error handling in hook
**After (Score 8):** Hook returns structured error with actionable message and recovery suggestion

---

## Lens 6: Plugin Coherence

**Core question:** Does this work as a unified whole?

### Scoring Rubric

| Score | Description | Evidence |
|-------|-------------|----------|
| 1-2 | Components feel unrelated, naming inconsistent | Collection of parts |
| 3-4 | Some shared conventions, unclear boundaries | Loosely related parts |
| 5-6 | Clear responsibilities, some overlap, partial handoff docs | Mostly coherent |
| **7-8** | **Unified naming, clear boundaries, documented handoffs, accurate README** | **Feels like one tool** |
| 9-10 | Perfect composition, components enhance each other | Could teach plugin design |

### What to Check

**Naming conventions:**
- Consistent naming across skills, commands, agents
- Names reflect function
- No confusing overlaps

**Component boundaries:**
- Each component has clear responsibility
- No overlapping functionality
- Dependencies are explicit

**Handoffs:**
- How do components work together?
- Are transitions documented?
- Is the user journey clear?

**Documentation:**
- README reflects actual capabilities
- No orphaned or undocumented components
- Examples show realistic usage

### Evaluation Questions

1. Does the plugin feel like one cohesive tool?
2. Would a new user understand what each part does?
3. Are component relationships clear?
4. Does README match reality?

### Example Improvements

**Before (Score 4):** Skills with overlapping triggers, unclear which to use
**After (Score 8):** Clear differentiation in descriptions, explicit "use X when... use Y when..."

**Before (Score 5):** Command invokes skill but relationship undocumented
**After (Score 8):** Command docs explain delegation, skill docs reference command

---

## Cross-Cutting Patterns

When analyzing, watch for these cross-lens issues:

**Description ↔ Implementation mismatch:**
- Description promises X but instructions do Y
- Triggers don't match actual capability

**Redundancy across components:**
- Same instructions in multiple skills
- Duplicate error handling logic

**Missing integration:**
- Components that should reference each other don't
- No guidance on combined usage

**Inconsistent quality:**
- Some skills polished, others rough
- Uneven documentation depth

---

## Quick Reference: Scoring Thresholds

| Score Range | Verdict | Action |
|-------------|---------|--------|
| 1-3 | Critical | Requires immediate attention |
| 4-6 | Below threshold | Needs improvement |
| **7-8** | **Passing** | **Acceptable quality** |
| 9-10 | Excellent | Could serve as example |

**Overall plugin score:** Average of all 6 lenses. Target ≥7.0.

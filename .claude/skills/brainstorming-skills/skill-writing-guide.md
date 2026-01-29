# Skill Writing Guide

Essential principles for writing effective skills. **Read this before drafting any SKILL.md.**

---

## Philosophy

**The context window is a public good.** Your skill competes with conversation history, other skills, and user requests. Challenge every line: "Does Claude need this? Can I assume Claude knows this? Does this justify its token cost?"

**Claude is already smart.** Only add context Claude doesn't have. Skip explanations of common concepts.

**Match specificity to fragility:**

| Freedom | When to Use                                  | Example                             |
| ------- | -------------------------------------------- | ----------------------------------- |
| High    | Multiple valid approaches; context-dependent | Code review guidelines              |
| Medium  | Preferred pattern exists; some variation OK  | Report templates with customization |
| Low     | Fragile operations; consistency critical     | Database migrations, exact scripts  |

_Narrow bridge = low freedom (one safe path). Open field = high freedom (many paths work)._

**One default, not menus.** Don't offer "use X or Y or Z." Provide one recommended approach with escape hatches for exceptions.

---

## Requirements

**Name:**

- Kebab-case, ≤64 characters
- Gerund form (verb-ing): `processing-pdfs`, `analyzing-data`, `writing-tests`
  - ❌ `code-comments` (noun) → ✅ `commenting-code` (gerund)
  - ❌ `error-handler` (noun) → ✅ `handling-errors` (gerund)
- Avoid: vague names (`helper`, `utils`), reserved words (`claude-*`, `anthropic-*`)

**Argument Hint:**

- Optional `argument-hint` in frontmatter shows expected arguments during autocomplete
- Examples: `[issue-number]`, `[filename] [format]`, `[branch-name]`

**Description:**

- Trigger conditions ONLY — never summarize workflow or outcomes
- Third person (injected into system prompt)
- ≤1024 characters
- Include key terms for discoverability

```
❌ BAD: "Guides comments toward explaining intent" (describes outcome)
❌ BAD: "Helps write better error messages" (describes what skill does)
❌ BAD: "Enforces TDD by requiring tests first" (summarizes workflow)

✅ GOOD: "Use when adding comments to code"
✅ GOOD: "Use when writing code that raises exceptions"
✅ GOOD: "Use when implementing features, before writing code"
```

**Why this matters:** Claude may follow the description instead of reading the skill body. Outcome descriptions become shortcuts that bypass the actual guidance.

**Body:**

- ~500 lines
- Split to reference files if content grows significantly larger

**String Substitutions:**

Skills support dynamic value substitution:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | Arguments passed when invoking. If not in body, appended as `ARGUMENTS: <value>` |
| `${CLAUDE_SESSION_ID}` | Session ID for logging or session-specific files |

**Context Budget:**

- Default: 15,000 characters for skill descriptions in context
- If exceeded, some skills may be excluded
- Check with `/context`, increase via `SLASH_COMMAND_TOOL_CHAR_BUDGET`

---

## Structure

**Progressive disclosure:** SKILL.md serves as an overview that points Claude to detailed materials as needed, like a table of contents in an onboarding guide.

**One level deep.** All references link directly from SKILL.md. Nested references get partially read.

**TOC for long files.** Reference files >100 lines need a table of contents so Claude sees full scope even when previewing.

**Consistent terminology.** Pick one term and use it throughout. "API endpoint" everywhere, not mixed with "URL", "route", "path".

---

## Persuasion Principles for Skill Design

Persuasive language is key to effective Skills. Use these techniques deliberately for discipline-enforcing skills.

### Authority

- Imperative language: "YOU MUST", "Never", "Always"
- Non-negotiable framing: "No exceptions"
- Eliminates decision fatigue and rationalization

### Commitment

- Require announcements: "Announce skill usage"
- Force explicit choices: "Choose A, B, or C"
- Use tracking: TaskCreate/TaskUpdate for complex workflows (persists across compaction)

### Scarcity

- Time-bound requirements: "Before proceeding"
- Sequential dependencies: "Immediately after X"
- Prevents procrastination

### Social Proof

- Universal patterns: "Every time", "Always"
- Failure modes: "X without Y = failure"
- Establishes norms

### Unity

- Collaborative language: "our codebase", "we're colleagues"
- Shared goals: "we both want quality"

**By skill type:**

| Type                 | Use                                   | Avoid           |
| -------------------- | ------------------------------------- | --------------- |
| Discipline-enforcing | Authority + Commitment + Social Proof | Liking          |
| Guidance/technique   | Moderate Authority + Unity            | Heavy authority |
| Collaborative        | Unity + Commitment                    | Authority       |
| Reference            | Clarity only                          | All persuasion  |

**Key insight:** Bright-line rules reduce rationalization. "When X, do Y" is more effective than "generally do Y."

### Rationalization Tables

For discipline-enforcing skills, include a "Rationalizations to Watch For" section that preempts common excuses:

```markdown
## Rationalizations to Watch For

| Excuse | Reality |
|--------|---------|
| "This case is simple enough" | Simple cases still benefit from the process. |
| "I'm under time pressure" | Rushing causes rework. Complete the process. |
| "I already know the answer" | Assumptions are most dangerous when confident. |

**All of these mean: Complete the process. No shortcuts.**
```

**Why this works:**
- Names the rationalization before the agent thinks it
- Provides the counter-argument in advance
- The closing line creates a bright-line rule

**When to include:** Discipline-enforcing skills where agents might skip steps under pressure. Not needed for reference or guidance skills.

---

## Framework for Thoroughness

Some skills need rigor — iterative analysis, evidence tracking, principled stopping. The [Framework for Thoroughness](framework-for-thoroughness_v1.0.0.md) provides reusable patterns.

**When to integrate:**

| Skill characteristic | Integration level |
|---------------------|-------------------|
| Open-ended analysis, unknown iteration count | **Full protocol** — Entry Gate, loop, Yield%, Exit Gate |
| Structured workflow, defined passes | **Vocabulary only** — Evidence/Confidence levels |
| Linear workflow, fixed steps | **None** — framework adds overhead without benefit |

**Canonical vocabulary** (use these terms for consistency):

- **Evidence levels:** E0 (assertion), E1 (single source), E2 (two methods), E3 (triangulated + disconfirmed)
- **Confidence levels:** High/Medium/Low — capped by evidence (E0/E1 caps at Medium)
- **Stakes:** Adequate (<20% yield), Rigorous (<10%), Exhaustive (<5%)

**Declaring framework use in a skill:**

If a skill adopts the full thoroughness framework, add this declaration in the skill header (adjust the path to your skill's actual reference location):

```markdown
**Protocol:** [thoroughness.framework@1.0.0](framework-for-thoroughness.md)
**Default thoroughness:** Rigorous
```

See `.claude/rules/skills.md` → "Framework for Thoroughness" for full details.

---

## Patterns

### Feedback Loops

**Run → fix → repeat.** This pattern dramatically improves quality.

```markdown
1. Draft content following STYLE_GUIDE.md
2. Review against checklist
3. If issues found:
   - Note each issue with specific reference
   - Revise
   - Review again
4. Only proceed when all requirements met
```

For code: `validate.py` → fix errors → validate again → only then proceed.

### Checklists for Multi-Step Workflows

Provide checklists Claude can track. For simple checklists, inline markdown works. For complex workflows, use task tracking (see below).

### Task Tracking for Complex Skills

For skills with many steps, multi-pass workflows, or checkpoints that must survive context compaction, guide agents to use task list tools instead of inline checklists.

**When to use task tools:**
- Workflow has >5 steps that need tracking
- Process spans multiple passes (iterative loops)
- Checkpoint state must survive context compaction
- Meaningful spinner UX improves user experience

**TaskCreate guidance to include in skills:**

```markdown
Use TaskCreate for each [dimension/step/item]:
- Subject: "[ID]: [name]" (e.g., "D1: Trigger clarity")
- Description: [what needs to be checked/done]
- activeForm: "[Present participle] [what]" (e.g., "Checking trigger clarity")
```

The `activeForm` field provides meaningful spinner text while the task is in_progress, improving UX.

**TaskUpdate for status transitions:**

```markdown
1. TaskUpdate to mark `in_progress` (activeForm shows in spinner)
2. [Do the work]
3. TaskUpdate to mark `completed` with findings in metadata
```

**TaskGet for context recovery:**

If resuming after context compaction, use TaskGet to retrieve full task details. TaskList shows summaries; TaskGet returns complete description and metadata. Include guidance like:

```markdown
**If resuming after context compaction:** Use TaskGet to retrieve full details for any task you need to continue.
```

**Task dependencies (optional):**

For sequenced workflows where Step B cannot start until Step A completes, use addBlockedBy:

```markdown
TaskUpdate: taskId="step-b", addBlockedBy=["step-a"]
```

**Reference:** See [task-list-guide.md](task-list-guide.md) for complete tool schemas.

### Verifiable Intermediate Outputs

For complex tasks: **plan → validate → execute**

1. Claude creates plan file (e.g., `changes.json`)
2. Script validates plan before execution
3. Catches errors early, enables iteration without touching originals

Use for: batch operations, destructive changes, high-stakes operations.

### Template Pattern

**Strict** (API responses, data formats): "ALWAYS use this exact structure"
**Flexible** (reports, analysis): "Sensible default; adapt as needed"

### Dynamic Context Injection

The `` !`command` `` syntax runs shell commands as **preprocessing** before skill content is sent to Claude. Output replaces the placeholder.

```markdown
## Current state
- Branch: !`git branch --show-current`
- Uncommitted changes: !`git diff --stat`
- Recent commits: !`git log --oneline -5`
```

**Use for:** Injecting real-time context (git state, environment info, API responses) without Claude executing commands.

**Note:** This is preprocessing — commands run when the skill loads, not during execution.

### Extended Thinking

Include the word **"ultrathink"** anywhere in skill content to enable extended thinking for that skill. Useful for complex analysis or multi-step reasoning tasks.

### Examples Pattern

Two formats, different purposes:

**BAD/GOOD comparisons** — Use in SKILL.md Examples section to show skill impact:

- BAD: What Claude does/produces without the skill
- GOOD: What Claude does/produces with the skill
- Include "Why it's bad/good" explanations

**Input/output pairs** — Use when demonstrating transformations within the skill:

```markdown
**Example 1:**
Input: Added user authentication
Output: feat(auth): implement JWT-based authentication
```

Use BAD/GOOD for skill verification (does the skill change behavior?). Use input/output for teaching format/style.

### Solve, Don't Punt

Scripts should handle errors, not defer to Claude. Verbose error messages help Claude fix issues: "Field 'X' not found. Available: A, B, C."

### Artifact vs Chat Output

**For skills that produce files:** Separate what goes in the artifact from what goes in chat.

**The principle:** Artifact is the work product. Chat is the summary.

Without explicit separation, Claude dumps full reports into chat — iteration logs, scoring tables, complete findings — overwhelming users who want actionable next steps.

**In the Outputs section, specify all three:**

```markdown
## Outputs

**IMPORTANT:** Full report goes in artifact ONLY. Chat receives brief summary.

**Artifact:** `docs/reports/YYYY-MM-DD-<name>.md`
- [Full list of sections]

**Chat summary (brief — not the full report):**
```
**Result:** [outcome]
**Key point:** [1-2 sentences]
**Full report:** `path/to/artifact.md`
```

Do NOT include in chat: [explicit list — scoring tables, iteration logs, etc.]
```

**Include verification checks:**

```markdown
Output:
- [ ] Full report written to artifact location
- [ ] Chat contains brief summary only
- [ ] Chat does NOT contain: [skill-specific list]
```

**When this applies:**

| Skill type | Applies? |
|------------|----------|
| Produces files (reports, records, documents) | **Yes** |
| Modifies existing code | No |
| Pure conversation (Q&A, explanation) | No |

---

## Checklist

Before finalizing any skill:

**Core:**

- [ ] Description contains trigger conditions only (no workflow)
- [ ] Description is third person
- [ ] Body reasonably sized (~500 lines guideline; split to supporting files if significantly larger)
- [ ] Consistent terminology throughout
- [ ] References one level deep from SKILL.md
- [ ] Examples are concrete, not abstract
- [ ] `argument-hint` added if skill accepts arguments
- [ ] String substitutions (`$ARGUMENTS`, `${CLAUDE_SESSION_ID}`) used where appropriate

**Quality:**

- [ ] Decision points have condition → action → alternative
- [ ] Verification checks measure actual success property
- [ ] Feedback loops for quality-critical tasks
- [ ] Thoroughness framework considered (full protocol / vocabulary only / none)

**Compliance (discipline skills):**

- [ ] Authority language for critical requirements
- [ ] Explicit choices or task tracking (TaskCreate for complex workflows)
- [ ] Bright-line rules, not "use judgment"

**Code/Scripts:**

- [ ] Scripts handle errors (don't punt)
- [ ] Validation steps for critical operations
- [ ] Plan-validate-execute for complex tasks
- [ ] Dynamic context injection (`` !`command` ``) considered for real-time state

**Output (for skills producing files):**

- [ ] Artifact location specified
- [ ] Chat summary format defined (brief, not full report)
- [ ] Explicit list of what NOT to show in chat
- [ ] Verification includes artifact/chat separation checks

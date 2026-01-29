# Subagent Writing Guide

Essential principles for writing effective subagents. **Read this before drafting any agent file.**

---

## Philosophy

**Subagents are autonomous workers.** Once started, they run to completion without user interaction. They cannot ask clarifying questions, share state with the main conversation, or spawn other subagents. Design for autonomy.

**The prompt is everything.** Subagents receive only their system prompt (the markdown body) plus basic environment details. They don't inherit the main conversation's context or the full Claude Code system prompt. Everything the agent needs must be in the prompt.

**Return summaries, not data.** The main thread receives the agent's output. Raw file contents, verbose logs, or unprocessed results pollute the main conversation's context. Agents should distill findings into actionable summaries.

**Isolation is a feature.** Subagents preserve the main conversation by keeping exploration, analysis, and verbose operations contained. This is their primary value — don't undermine it by returning too much.

---

## Prompt Clarity

The prompt determines whether the agent works or fails. Address these dimensions deliberately.

### Specificity

**The problem:** Vague prompts let the agent interpret tasks differently than intended.

**Write clear specialist descriptions:**

| Vague | Specific |
|-------|----------|
| "Review the code" | "Review code for security vulnerabilities — focus on injection attacks, authentication bypasses, and data exposure" |
| "Analyze the system" | "Analyze architecture by tracing data flows, mapping component dependencies, and identifying integration points" |
| "Help with testing" | "Analyze test coverage by examining existing tests, identifying gaps in edge case coverage, and assessing error path testing" |
| "Debug this" | "Diagnose failures by reproducing issues, isolating root causes through systematic elimination, and gathering evidence" |

**Define the specialist's approach:**

- What domain does this specialist focus on?
- What methodology should they follow?
- What counts as a finding worth reporting?

**Eliminate interpretation space:**

- Name the aspects or concerns to prioritize
- Define what "done" looks like for this specialist's work
- Specify the threshold for reporting (critical only? all issues?)

**Test for ambiguity:** Would two specialists with this prompt work the same way? If not, clarify the approach.

### Context Transfer

**The problem:** Agents lack info they need because the prompt assumed shared context.

**Include explicitly:**

- Relevant file paths or patterns
- Technology stack when it affects approach
- Project conventions that matter for the task
- Prior decisions or constraints from the conversation
- Error messages or symptoms being investigated

**Safe to assume:**

- Standard language/framework knowledge
- Common tool usage (git, npm, etc.)
- General coding practices

**When in doubt, include it.** The cost of redundant context is low; the cost of missing context is agent failure.

### Output Contracts

**The problem:** Agent returns something, but not what the main thread needs.

**Specify the exact format:**

```markdown
## Output Format

Return:
1. Direct answer to the question (2-3 sentences)
2. Key files discovered (paths only)
3. Relevant code patterns (with file:line references)
```

**Match output to consumer:**

| Consumer needs | Output should be |
|----------------|------------------|
| Quick answer | 2-3 sentence summary |
| Detailed analysis | Structured sections with evidence |
| Actionable items | Prioritized list with locations |
| Decision support | Options with tradeoffs |

**Specify what NOT to return:**

- "Do not include file contents — only paths"
- "Skip minor issues — report only critical and high severity"
- "Omit explanations of common patterns"

### Boundaries

**The problem:** Agent scope-creeps into unintended areas, or stops short of useful work.

**Define from both directions:**

*What to do:*
```markdown
## Task
- Analyze test files in tests/unit/
- Check for missing edge case coverage
- Identify untested error paths
```

*What NOT to do:*
```markdown
## Constraints
- Do not modify any files
- Do not analyze integration tests
- Do not suggest refactoring production code
```

**Scope signals:**

| Too broad | Too narrow |
|-----------|------------|
| "Analyze the codebase" | "Check line 47 of auth.py" |
| "Find all issues" | "Only check for typos" |
| "Improve everything" | "Only look at this one function" |

**Find the useful middle:** What's the minimum scope that produces valuable output?

### Consistency

**The problem:** Prompt contradicts itself, causing unpredictable behavior.

**Check for conflicts:**

- Task says "analyze" but constraints say "don't read files"
- Output format requests "detailed explanation" but also "keep it brief"
- Tools include Edit but constraints say "read-only"

**Review before finalizing:** Read the prompt as if seeing it for the first time. Do all instructions align?

---

## Scope Calibration

Finding the right scope is the difference between a useful specialist and a broken agent.

**Too broad — the agent wanders:**

Signs:
- "Analyze the codebase" with no focus area
- No constraints on what to examine
- Output could be anything

Result: Agent explores tangentially, returns unfocused findings, burns context on irrelevant work.

**Too narrow — the agent stops short:**

Signs:
- Task is a single lookup, not specialist work
- Constraints block useful related findings
- Would be faster to just do it directly

Result: Agent does trivial work that didn't need delegation. Overhead exceeds value.

**The useful middle — specialist with domain:**

| Component | Purpose |
|-----------|---------|
| Domain | What area does this specialist own? |
| Focus | What aspects within that domain? |
| Depth | How thoroughly should they investigate? |
| Boundaries | Where does their responsibility end? |

**Calibration questions:**

- Would a human specialist with this scope produce useful output?
- Is there enough work here to justify the delegation overhead?
- Are the boundaries clear enough that scope creep is unlikely?
- Are the boundaries loose enough that valuable findings won't be missed?

**When scope is hard to define:**

- The task may need decomposition into multiple agents
- The task may not be well-suited for subagent delegation
- More conversation is needed to understand what's actually wanted

---

## Quality Dimensions

Use these dimensions to evaluate subagent designs.

### Task fidelity

- Purpose stated explicitly in the prompt
- Non-goals listed to prevent scope creep
- Success criteria defined ("what does good output look like?")

### Context completeness

- All necessary info included in the prompt
- Assumptions stated explicitly
- No reliance on conversation context the agent won't have

### Output actionability

- Format specified exactly
- Level of detail appropriate for consumer
- Includes what to omit, not just what to include

### Constraint clarity

- "Allowed" vs "Forbidden" actions explicit
- Tool selection matches task needs (no over-permissioning)
- Boundaries defined from both directions

### Instruction consistency

- No contradictions between sections
- Tools match constraints (don't include Edit if read-only)
- Scope matches output expectations

### Autonomy fit

- Task can be completed without clarifying questions
- Failure modes have reasonable default behavior
- Agent can make progress with incomplete information

---

## Requirements

### Frontmatter

**Required:**

| Field | Format | Notes |
|-------|--------|-------|
| `name` | lowercase-with-hyphens | Unique identifier |
| `description` | Natural language | When Claude should delegate; include "proactively" for auto-invocation |

**Optional:**

| Field | Default | Notes |
|-------|---------|-------|
| `tools` | Inherits all | Comma-separated allowlist |
| `disallowedTools` | None | Comma-separated denylist |
| `model` | inherit | `haiku`, `sonnet`, `opus`, or `inherit` |
| `permissionMode` | default | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `skills` | None | Skills to inject at startup |
| `hooks` | None | `PreToolUse`, `PostToolUse`, or `Stop` handlers scoped to subagent |

### Model Selection

| Task complexity | Model | Rationale |
|-----------------|-------|-----------|
| Simple lookups, pattern matching | haiku | Fast, cheap |
| Standard analysis, code review | sonnet | Balanced |
| Complex reasoning, architecture | opus | Highest capability |
| Match main conversation | inherit | Consistency |

### Tool Selection

**Principle:** Grant minimum necessary permissions.

| Task type | Typical tools |
|-----------|---------------|
| Read-only exploration | Read, Grep, Glob |
| Analysis with execution | Read, Grep, Glob, Bash |
| Code modification | Read, Edit, Write |
| Full development | All or inherit |

**Avoid over-permissioning:** An agent with Edit access might modify files when you only wanted analysis.

---

## Checklist

Before finalizing any subagent:

**Frontmatter:**

- [ ] `name` is lowercase with hyphens only
- [ ] `description` explains when to delegate (not what agent does)
- [ ] `tools` matches task needs (no over-permissioning)
- [ ] `model` is appropriate for task complexity

**Prompt clarity:**

- [ ] Task is unambiguous — two specialists would work the same way
- [ ] Context is complete — no reliance on conversation agent won't have
- [ ] Output format is specified exactly
- [ ] Boundaries defined from both directions (do / don't do)
- [ ] No contradictions between sections

**Scope:**

- [ ] Broad enough to produce useful output
- [ ] Narrow enough to prevent wandering
- [ ] Delegation overhead is justified

**Autonomy:**

- [ ] Task can complete without clarifying questions
- [ ] Agent can make progress with incomplete information
- [ ] Constraints section specifies what NOT to do
- [ ] Output section specifies what NOT to return

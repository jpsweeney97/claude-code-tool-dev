---
name: creating-subagents
description: Use when designing or creating Claude Code subagents — guides the full lifecycle from idea to working agent with validation.
---

<!-- v2.0 - Added: update flow, validation warnings, preview-edit loop, quality self-check, troubleshooting, custom tests -->

# Creating Subagents

Guide users through designing and creating Claude Code subagents via conversation.

## Initialization

On invocation:

1. **Check environment:**
   - Verify `~/.claude/agents/` exists; create if missing
   - Scan existing agents and note count

2. **Detect intent from user's request:**
   - "I need an agent that..." → Create from scratch
   - "Give me a template for..." → Create from template
   - Unclear → Ask: "Would you like to start from scratch or use a template?"

3. **Offer context:**
   ```
   You have N existing agents. Want to see them first?
   ```

## Entry Points

### From Scratch

Ask questions to understand the agent (see Conversational Design below).

### From Template

Present the template library:

| Template | Purpose | Tools | Model |
|----------|---------|-------|-------|
| reviewer | Code review | Read, Grep, Glob | sonnet |
| debugger | Error diagnosis | Read, Bash, Edit, Grep, Glob | sonnet |
| analyzer | Codebase analysis | Read, Grep, Glob | haiku |
| generator | Code generation | Read, Write | sonnet |
| refactorer | Code improvement | Read, Edit | sonnet |
| documenter | Documentation | Read, Write | haiku |
| tester | Test writing | Read, Write, Bash | sonnet |
| advisor | Guidance only | (none) | haiku |

Ask: "Which template, or 'none' to start from scratch?"

If template selected:
- Pre-fill tools and model from template
- Still ask purpose, trigger, boundaries, output, autonomy
- Confirm or override pre-filled values

### From Update

Triggered when user mentions an existing agent name with update intent:
- "improve/update/fix [name] agent"
- "the [name] agent needs..."
- "[name] agent isn't working"

**Load the agent:**
1. Read `~/.claude/agents/[name].md`
2. If not found → "No agent named [name]. Create it instead?"
3. If found → parse frontmatter and body

**Display current state:**
```
Current configuration for [name]:
- Description: [description]
- Tools: [tools or "inherits all"]
- Model: [model or "system default"]
- Prompt: [first 100 words...]
```

**Ask what to change:**
```
What would you like to update?
A) Scope/purpose — what it does
B) Trigger — when it's invoked
C) Tools/permissions — capabilities
D) Prompt content — behavior details
E) Fix a specific issue — describe what's wrong
```

Based on selection:
- A/B → Re-ask relevant questions from Phase A
- C → Re-ask tools question
- D → Show current prompt, ask what to change
- E → Collect issue description, suggest targeted fix

After collecting changes → proceed to validation with merged config.

## Conversational Design

Ask ONE question at a time. Prefer multiple choice.

### Phase A: Core Questions (always ask)

**1. Purpose**
```
What should this agent do?
```
Open-ended. If too vague after 2 attempts, show template examples.

**2. Trigger**
```
When should Claude invoke this agent?
A) Automatically when task matches
B) Only when explicitly asked
C) Both — proactive with opt-out
```

**3. Tools**
```
What capabilities does it need?
A) Read-only — Read, Grep, Glob
B) Read + write — add Edit, Write
C) Full access — add Bash, Task
D) Custom — let me pick specific tools
E) None — advisory only
F) Inherit all — get everything including MCP tools
```
If E (none): set autonomy to advisory, skip that question later.

**4. Model**
```
How capable should it be?
A) Haiku — fast, cheap, simple tasks
B) Sonnet — balanced (recommended for most)
C) Opus — complex reasoning, expensive
D) Inherit — match main conversation's model
```

### Phase B: Scope & Behavior

**5. Boundaries**
```
What should this agent NOT do?
```
Open-ended, or "nothing specific."

**6. Output**
```
What should it produce?
A) File changes — edits or creates files
B) Report — summary or analysis
C) Conversation — interactive guidance
D) Structured data — JSON, tables
E) Depends on task
```

**7. Autonomy** (skip if tools = none)
```
How independently should it work?
A) Autonomous — do the work, report when done
B) Interactive — ask questions along the way
C) Advisory — suggest, don't act
```

### Skip Logic

- Template selected → confirm pre-filled values, don't re-ask
- Tools = none → skip autonomy, set to advisory
- Answers conflict → surface immediately, resolve before continuing

## Validation

Before generating, run checks in priority order.

### Blockers (must fix)

| Check | Action if fails |
|-------|-----------------|
| Name is kebab-case | Suggest fix: "Use [corrected-name]?" |
| Name doesn't conflict | Offer: "[name]-2" or "overwrite existing?" |
| Purpose is defined | "Can you describe what it does?" |
| Description is specific | "Make it more specific so Claude knows when to invoke" |

Surface each blocker, get resolution before proceeding.

### Warnings (recommend fixing)

After blockers resolved, check for warnings:

| Check | Message |
|-------|---------|
| Tools don't match purpose | "You said it edits files but only has Read tools. Add Edit/Write?" |
| Bash without justification | "This agent has Bash access. What commands will it run?" |
| Prompt too short (<50 words) | "The prompt is brief. Add more guidance for consistent behavior?" |
| Prompt too long (>2000 words) | "The prompt is very long. Consider splitting into focused agents?" |

For each warning, ask: "Fix this / Skip / Explain why it's okay"

### Suggestions (optional)

Note these but don't require action:

- "This might overlap with your existing [name] agent"
- "Consider adding 'PROACTIVELY' to description for auto-invocation"
- "Haiku might struggle with this complexity — consider Sonnet"

Present suggestions as: "A few suggestions (no action needed): [list]"

## Generate Agent File

### YAML Frontmatter

Required fields:
- `name` — kebab-case identifier
- `description` — when/why to invoke (include "PROACTIVELY" if auto-invoke)

Optional fields (omit if using defaults):
- `tools` — comma-separated; omit to inherit all
- `model` — sonnet/opus/haiku/inherit; omit for system default
- `permissionMode` — default/acceptEdits/bypassPermissions
- `skills` — comma-separated skill names

### System Prompt Structure

```markdown
You are [role based on purpose].

When invoked:
1. [First step based on context gathering or immediate action]
2. [Core task steps]
3. [Output/delivery step]

Key practices:
- [Derived from boundaries — what NOT to do]
- [Derived from output — format expectations]
- [Derived from autonomy — when to ask vs act]

[If failure behavior discussed:]
If you encounter issues:
- [How to handle based on their answer]
```

### Quality Self-Check

Before showing preview, internally verify:

1. **Prompt clarity:** Does the system prompt clearly explain what to do?
   - If vague → add specific step-by-step instructions

2. **Consistency:** Does the prompt match the answers collected?
   - Tools mentioned match tools in frontmatter
   - Autonomy level reflected in instructions
   - Boundaries included as "do not" statements

3. **Completeness:** Are there obvious gaps?
   - If output format discussed → include in prompt
   - If failure behavior discussed → include handling
   - If context gathering needed → include first step

If any issues found, fix them before showing preview. Don't ask user — just improve silently.

### Preview and Save

1. Display the complete agent file:
   ```
   --- Preview: [name].md ---

   [full generated content]

   --- End Preview ---
   ```

2. Offer options:
   ```
   What would you like to do?
   A) Save as-is
   B) Edit first — tell me what to change
   C) Preview only — don't save yet
   D) Start over
   ```

3. **If B (Edit):**
   - Ask: "What would you like to change?"
   - Collect specific edits (e.g., "make the prompt more concise", "add error handling")
   - Regenerate affected sections
   - Show updated preview
   - Return to step 2 (loop until A, C, or D)

4. **If A (Save):**
   - Check if file exists
   - If exists → create backup: `~/.claude/agents/[name].md.bak`
   - Confirm: "File exists. Overwrite? (backup will be saved)"
   - Write to `~/.claude/agents/[name].md`
   - Show confirmation with first 10 lines

5. **If C (Preview only):**
   - Don't save
   - Offer: "Copy to clipboard?" (if supported)
   - End skill

6. **If D (Start over):**
   - Clear collected answers
   - Return to Entry Points

## Test Prompts

After saving, offer test generation:

```
Generate test prompts to validate the agent?
A) Yes — generate tests for me
B) Skip — I'll test manually
C) Write my own — let me specify test cases
```

### If A (Generate)

Generate tests based on complexity:

**Simple agents (3 tests):**
1. Happy path — primary use case
2. Edge case — boundary of scope
3. Out of scope — should decline

**Complex agents (5 tests):**
4. Failure scenario — error handling
5. Multi-step — chained operations

**Test format:**
```markdown
## Test 1: Happy Path

**Prompt:**
> Use [name] to [specific task from purpose]

**Expected:**
- [Observable outcome based on output type]

**Confirm:** Watch for "[name] is running..."

**If fails:** Check description matches, tools are sufficient
```

### If C (Write Own)

Ask: "Describe a test case — what prompt and what should happen?"

Collect 1-3 custom tests in the same format.

### Save Tests

```
Save test prompts to ~/.claude/agents/[name].test.md?
A) Yes
B) No — just show them
```

## Handoff

After everything is saved:

```
✓ Agent created: ~/.claude/agents/[name].md
✓ Backup saved: ~/.claude/agents/[name].md.bak (if overwrite)
✓ Tests saved: ~/.claude/agents/[name].test.md (if opted)

Try it now:
> Use [name] to [happy path example]
```

### First-Run Troubleshooting

If the agent doesn't work as expected:

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| Agent not invoked | Description doesn't match prompt | Add "PROACTIVELY" or make description more specific |
| Wrong agent invoked | Description too similar to another agent | Make description unique to this agent's purpose |
| Agent lacks capability | Missing tools | Add needed tools to frontmatter |
| Agent does unexpected things | Prompt is ambiguous | Add clearer step-by-step instructions |
| Permission errors | Permission mode too restrictive | Check `permissionMode` setting |
| Agent is slow | Model is overkill | Try Haiku for simpler tasks |

### Iterate Later

To modify this agent:
- "Improve the [name] agent — it does X but I expected Y"
- "Update [name] to also handle Z"
- "The [name] agent isn't working — help me fix it"
- Or: `/agents` → select [name] → edit

To restore previous version:
- Backup at: `~/.claude/agents/[name].md.bak`

To delete:
- `rm ~/.claude/agents/[name].md`
- Or: `/agents` → select [name] → delete

## Global Commands

These work at any point:
- "start over" → restart from beginning
- "show agents" → list existing agents

## Key Principles

1. **One question at a time** — never ask multiple questions in one message
2. **Multiple choice preferred** — easier to answer than open-ended
3. **Confirm, don't assume** — verify understanding before generating
4. **Validate before save** — catch issues early with blockers and warnings
5. **Preview-edit loop** — let user refine before committing
6. **Concrete tests** — use specific examples from the conversation
7. **Silent quality fixes** — improve obvious issues without asking
8. **Backup before overwrite** — always preserve previous version
9. **Troubleshooting guidance** — help user debug if agent doesn't work

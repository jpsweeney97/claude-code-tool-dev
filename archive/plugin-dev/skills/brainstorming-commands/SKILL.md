---
name: brainstorming-commands
description: Use when designing a command, "I need a command for X",
  "command arguments", "command vs skill", or after brainstorming-plugins
  identifies a command is needed. Guides collaborative command design
  through 6-step process.
---

# Command Design

Turn command ideas into design documents through collaborative dialogue.

## Quick Start

```
User: "I need a command for X"
Claude: Uses 6-step workflow

1. Purpose & Archetype (naming, nature)
2. Arguments & Context Gathering (input design)
3. Pre-flight Validation (correctness checks)
4. Delegation & Work (skill, agent, or inline)
5. Post-processing (feedback, artifacts)
6. Frontmatter & Discoverability → write design document

→ Handoff to implementing-commands
```

## Triggers

- `design a command for {purpose}`
- `I need a command for X`
- `command vs skill` / `when should I use commands`
- `command arguments` / `how do I pass arguments`
- After `brainstorming-plugins` identifies commands

## Prerequisites

Before using this skill:
- Know you need a command (from `/brainstorming-plugins` or direct need)
- Understand commands = explicit user invocation via `/command-name`

No design document? This skill creates one.

## Pipeline Context

This skill is **Stage 2: Design** in the commands pipeline.

| Aspect | Value |
|--------|-------|
| This stage | Design command from requirements |
| Previous | `/brainstorming-plugins` (or direct request) |
| Next | `/implementing-commands` |
| Reference | `command-development` (structural details) |

## Core Principle

> Commands are user-facing entry points that orchestrate other components.
> The command handles invocation; the skill/agent does the work.

**Decision rule:**

| Need | Use |
|------|-----|
| User explicitly triggers workflow | Command |
| Claude discovers capability automatically | Skill |
| Complex delegated work | Agent (invoked by command) |

## The 6-Step Workflow

### Step 1 of 6: Purpose & Archetype

Ask one question at a time:

| Question | Purpose |
|----------|---------|
| What does this command do? | Clarifies the goal |
| Why a command vs a skill? | Confirms explicit invocation is needed |
| What's the command's nature? | Informs structure decisions |
| What should this command be called? | Establishes naming |

**Naming conventions:**

| Rule | Example | Anti-pattern |
|------|---------|--------------|
| Verb-noun pattern | `create-skill`, `audit-plugin` | `skill-creator`, `plugin-auditor` |
| Lowercase hyphenated | `fix-plugin` | `fixPlugin`, `Fix_Plugin` |
| Action-first | `review-pr` | `pr-review` |
| Specific over generic | `optimize-plugin` | `optimize` |
| Match skill name when wrapping | `commit` → `commit` skill | `make-commit` → `commit` skill |

**Nature exploration:**

| Question | Explores |
|----------|----------|
| Does it gather context first? | Uses `@` or bash execution |
| Does it delegate work? | To skill, agent, or inline |
| Is it interactive? | Uses AskUserQuestion |
| Does it chain multiple actions? | Pipeline vs single action |

**Output:**
- Command name: `verb-noun` format
- Purpose statement: "This command [action] by [method] because [reason]."

**Example:**
- Name: `commit`
- Purpose: "This command creates git commits by gathering staged changes via bash, then invoking the commit-message skill, because users need a consistent entry point for the commit workflow."

---

### Step 2 of 6: Arguments & Context Gathering

> **Focus:** What data does the command need? (Input design)
> Step 3 handles *validation logic*—this step designs *what* to gather.

Ask one question at a time:

| Question | Purpose |
|----------|---------|
| What input does the user provide? | Identifies argument needs |
| What context does the command gather? | Identifies `@` and bash execution needs |
| Does it need plugin resources? | Identifies `${CLAUDE_PLUGIN_ROOT}` needs |

**Argument patterns:**

| Pattern | Syntax | When to use | Example |
|---------|--------|-------------|---------|
| None | (no args) | Command needs no input | `/status` |
| All args as blob | `$ARGUMENTS` | Freeform input | `/fix-issue $ARGUMENTS` |
| Positional | `$1`, `$2`, `$3` | Distinct parameters | `/deploy $1 to $2` |
| Mixed | `$1` + remaining | Flags after required | `/create-skill --quick $ARGUMENTS` |

**Context gathering patterns:**

| Pattern | Syntax | When to use | Example |
|---------|--------|-------------|---------|
| File reference | `@path` | Include file contents | `Review @src/main.ts` |
| Dynamic file ref | `@$1` | File from argument | `Review @$1` |
| Bash execution | `!\`command\`` | Gather dynamic context | `Status: !\`git status\`` |
| Plugin resource | `${CLAUDE_PLUGIN_ROOT}` | Access plugin files | `@${CLAUDE_PLUGIN_ROOT}/templates/report.md` |

> **Note:** `${CLAUDE_PLUGIN_ROOT}` is only available in plugin commands. User commands (in `~/.claude/commands/`) and project commands (in `.claude/commands/`) should use absolute paths or paths relative to the working directory.

**Output:**
- `argument-hint`: string showing expected args
- Context gathering: list of `@`, bash execution, or `${CLAUDE_PLUGIN_ROOT}` patterns

**Example:**
```yaml
argument-hint: "<file-path> [--verbose]"
```
Context: `@$1` for file, `!\`git log -1\`` for recent commit

---

### Step 3 of 6: Pre-flight Validation

> **Focus:** What checks ensure the input is valid? (Validation logic)
> Step 2 designed *what* to gather—this step verifies correctness.

Ask one question at a time:

| Question | Purpose |
|----------|---------|
| What must be true before this runs? | Identifies preconditions |
| What could go wrong with the input? | Identifies validation needs |
| Should it fail fast or try to recover? | Error handling strategy |

**Validation patterns:**

| Check | Bash pattern | Example |
|-------|--------------|---------|
| Argument provided | `test -n "$1"` | Required file path |
| File exists | `test -f $1` | File must exist |
| Directory exists | `test -d $1` | Path must be directory |
| Valid enum value | `echo "$1" \| grep -E "^(dev\|prod)$"` | Environment name |
| Command available | `command -v jq` | Required tool |
| Git state | `git diff --cached --quiet` | Has staged changes |
| Plugin resource | `test -x ${CLAUDE_PLUGIN_ROOT}/bin/tool` | Script exists |

**Output:** List of validation checks (or "none needed")

**Example:**
```markdown
Validate:
1. File exists: `test -f $1 && echo "OK" || echo "MISSING"`
2. Is TypeScript: `echo "$1" | grep -E "\.tsx?$" || echo "NOT_TS"`
```

---

### Step 4 of 6: Delegation & Work

Ask one question at a time:

| Question | Purpose |
|----------|---------|
| Does this command delegate work? | Some commands are self-contained |
| What does the actual work? | Skill, agent, script, or inline |
| What context does the target need? | What to pass along |

**Delegation patterns:**

| Pattern | When to use | Example syntax |
|---------|-------------|----------------|
| Invoke skill | Skill has the knowledge | `Use the commit-message skill to...` |
| Launch agent | Complex delegated task | `Launch the code-reviewer agent to...` |
| Run script | Deterministic operation | `bash ${CLAUDE_PLUGIN_ROOT}/scripts/build.sh` |
| Inline work | Simple, self-contained | (just write the instructions) |
| Pipeline | Multiple steps | Phase 1: skill, Phase 2: script, Phase 3: agent |

> **Hook coordination:** Commands may trigger hooks if they invoke tool calls. Consider whether existing hooks (e.g., `PostToolUse` for Write) should fire during command execution, or if you need custom hooks for command-specific events. Design the command workflow with hook side effects in mind.

**Output:** Delegation target(s) + what context to pass

**Example:**
```markdown
Delegation: Invoke `optimizing-plugins` skill
Context: Plugin path from $1, validation results from pre-flight
```

---

### Step 5 of 6: Post-processing

Ask one question at a time:

| Question | Purpose |
|----------|---------|
| What happens after the main work? | Identifies post-processing |
| Does it produce artifacts? | Files, commits, PRs |
| What should the user see? | Summary, next steps |

**Post-processing patterns:**

| Pattern | When to use | Example |
|---------|-------------|---------|
| Validation script | Verify output quality | `python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py` |
| Git operations | Commit, stage, push | Stage changes, create commit |
| Summary output | User feedback | "Created X, modified Y" |
| Next step suggestion | Guide workflow | "Run /implementing-X to continue" |
| Artifact generation | Produce files | Write design doc to `docs/plans/` |
| None | Fire and forget | Simple commands |

**Output:** Post-processing actions (or "none needed")

**Example:**
```markdown
Post-processing:
1. Run validation: `python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py $1`
2. Suggest next step: "Run /implementing-commands to build from this design"
```

---

### Step 6 of 6: Frontmatter & Discoverability

Ask one question at a time:

| Question | Purpose |
|----------|---------|
| What tools does this command need? | Determines `allowed-tools` |
| What model is appropriate? | Determines `model` |
| Should Claude invoke this automatically? | Determines `disable-model-invocation` |
| Does this require deep reasoning? | Determines extended thinking |

**Frontmatter options:**

| Field | Purpose | Values | Default |
|-------|---------|--------|---------|
| `description` | Shows in `/help`, used by SlashCommand tool | String (< 60 chars) | First line of prompt |
| `allowed-tools` | Constrain tool access | `Read, Grep, Bash(git:*)` | Inherit from conversation |
| `model` | Force specific model | `haiku`, `sonnet`, `opus` | Inherit from conversation |
| `argument-hint` | Autocomplete hint | `<path> [--verbose]` | None |
| `disable-model-invocation` | Explicit invocation only | `true` / `false` | `false` |

**Extended thinking (optional):**

Commands can trigger extended thinking by including keywords in the prompt body (not frontmatter):

| Keyword | Effect |
|---------|--------|
| `think hard` | Enables extended thinking mode |
| `think deeply` | Enables extended thinking mode |
| `megathink` | Enables extended thinking mode |
| `ultrathink` | Enables extended thinking mode |

Use for complex analysis, multi-step reasoning, or decisions with significant consequences.

**Discoverability decision:**

| Factor | Explicit-only (`true`) | Auto-invocable (`false`) |
|--------|------------------------|--------------------------|
| Side effects | Destructive, external, commits | Read-only, reversible |
| User intent | Must be deliberate | Claude can infer need |
| Frequency | Rare, special occasions | Common task |
| Examples | `/deploy`, `/create-plugin` | `/review`, `/explain` |

**Output:** Complete frontmatter block

**Example:**
```yaml
---
description: Optimize plugin through 6 analytical lenses
argument-hint: "<plugin-path>"
allowed-tools: [Read, Glob, Grep, Bash, Write, TodoWrite, Skill]
model: claude-opus-4-5-20251101
---
```

## Anti-Patterns

Organized by symptom → cause → fix. Use during design to avoid mistakes, or after design to validate.

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Users don't know the command exists" | Missing or vague `description`; no `argument-hint` | Add clear description (<60 chars) and argument-hint showing expected input |
| "Claude invokes this at the wrong time" | Auto-invocable for a command with side effects | Set `disable-model-invocation: true` for destructive/external/commit operations |
| "The command prompt is 200+ lines" | All logic inline instead of delegating | Extract work to skill or agent; command handles invocation, not implementation |
| "Works in development, breaks after install" | Using `${CLAUDE_PLUGIN_ROOT}` in user/project command | Only plugin commands have this variable; use absolute or working-directory-relative paths |
| "Users invoke this via natural language, not `/command`" | Command for something Claude should discover automatically | Make it a skill instead; commands are for *explicit* user invocation |
| "The command does A, B, C, and D" | Scope creep — one command trying to do too much | Split into focused commands, or make it a pipeline with clear phases |
| "It ran but I don't know what happened" | No post-processing feedback | Add summary output, artifact confirmation, or next-step suggestion |
| "The name doesn't match what it does" | Noun-first naming or generic verb | Rename to verb-noun (`create-skill` not `skill-creator`); be specific |

## Verification

Before moving to implementation, confirm:

| Check | Question |
|-------|----------|
| **Scope** | Does this command do exactly one thing well? |
| **Right component** | Should this be a command (explicit invocation) or a skill (Claude discovers)? |
| **Delegation** | Does the command handle invocation while skills/agents do the work? |
| **Naming** | Is it verb-noun, specific, and action-first? |
| **Discoverability** | Will users find it? (clear description, argument-hint) |
| **Feedback** | Will users know what happened after it runs? |
| **Portability** | Will it work after installation? (no hardcoded paths, correct scope) |
| **Anti-patterns** | None of the 8 anti-patterns present? |

**Exit criteria:** All checks pass → proceed to `implementing-commands`

## Output

Write design to: `docs/plans/YYYY-MM-DD-<command-name>-design.md`

**Sections:**
1. Purpose — What the command does and why
2. Arguments — Patterns and context gathering
3. Validation — Pre-flight checks
4. Delegation — What does the work
5. Post-processing — Feedback and artifacts
6. Frontmatter — Complete YAML block
7. Test plan — Scenarios for invocation testing

## Next Step

After saving the design document:

```
/implementing-commands docs/plans/[design-file].md
```

## References

- command-development — Structural reference (frontmatter, arguments, patterns)
- implementing-commands — TDD implementation (next stage)
- Official commands docs — `docs/claude-code-documentation/commands-*.md`

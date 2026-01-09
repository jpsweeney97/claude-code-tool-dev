---
paths: .claude/agents/**
---

# Agent Development

Agents (subagents) are autonomous workers that run in separate contexts via the Task tool. They handle complex, multi-step tasks independently and return results to the main conversation.

## When to Use Agents

- **Parallel workstreams**: Multiple independent tasks that don't need shared state
- **Deep exploration**: Reading many files, analyzing patterns across codebase
- **Isolated execution**: Tasks that shouldn't pollute the main context
- **Specialized workflows**: Different models or tool restrictions per task

## When NOT to Use Agents

- **Tasks requiring conversation**: Agents can't ask follow-up questions mid-execution
- **Shared state operations**: Agents run in separate contexts; no state sharing
- **Simple single-file reads**: Use Read tool directly (lower overhead)
- **Quick lookups**: Use Grep/Glob directly (agents add latency)

## Structure

Agents are markdown files:

```
.claude/agents/
├── <name>.md           # Agent definition
└── ...
```

## Agent Format

```markdown
---
name: my-agent-name
description: When this subagent should be invoked
tools: Glob, Grep, Read  # Optional: comma-separated list
model: haiku  # Optional: sonnet, opus, haiku, or 'inherit'
---

You are a specialized agent for [purpose].

## Your Task

[Clear description of what this agent does]

## Constraints

- [Boundary 1]
- [Boundary 2]

## Output Format

Return your findings as:
[Specify exact output structure]
```

## Frontmatter Fields

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `name` | Yes | string | Unique identifier (lowercase + hyphens) |
| `description` | Yes | string | Natural language description of purpose |
| `tools` | No | string | Comma-separated list; omit to inherit all tools |
| `model` | No | string | `sonnet`, `opus`, `haiku`, or `'inherit'` |
| `permissionMode` | No | string | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan`, `ignore` |
| `skills` | No | string | Comma-separated skills to auto-load (subagents don't inherit parent skills) |
| `hooks` | No | object | `PreToolUse`, `PostToolUse`, or `Stop` handlers scoped to subagent |

### Skills Field Example

```yaml
---
name: data-analyst
description: Analyzes data using SQL and visualization
tools: Read, Grep, Bash
skills: sql-analysis, chart-generation
---
```

Skills are loaded into subagent context at start. Must be discoverable from same locations as the subagent (personal `~/.claude/skills/`, project `.claude/skills/`, or plugin).

### Hooks Field Example

```yaml
---
name: secure-executor
description: Executes code with command validation
tools: Bash, Read
hooks:
  PreToolUse:
    - matcher: Bash
      command: ./scripts/validate-command.sh
  Stop:
    - command: ./scripts/cleanup.sh
---
```

Agent hooks are scoped to the subagent's execution lifecycle. `once: true` is NOT supported for agent hooks.

## Invoking Agents

Agents are invoked via the Task tool:

```
Task tool parameters:
- subagent_type: "<name>"      # Your agent name
- prompt: "<task details>"     # What to do
- model: "haiku"               # Optional override
- max_turns: 10                # Optional turn limit
- run_in_background: true      # Optional async execution
```

## Design Principles

### Agents are autonomous
Once started, agents run to completion without user interaction. Design for autonomy.

### Agents return summaries, not raw data
Agents should process information and return distilled findings. The main thread shouldn't receive 10 files of raw content.

### Agents have separate context
Each agent invocation starts fresh. Don't assume prior state or shared memory.

### Agents can't nest
An agent cannot spawn other agents via Task tool. Plan accordingly.

### Choose the right model

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| Doc lookup, simple queries | haiku | Fast, cheap |
| Standard development | sonnet | Balanced |
| Complex architecture, planning | opus | Highest capability |

## Required Sections in Agent Definition

### 1. Purpose Statement
Clear, specific description of what this agent does.

### 2. Task Instructions
What the agent should do when invoked.

### 3. Constraints
Explicit boundaries:
- What NOT to do
- Scope limits
- Tool restrictions rationale

### 4. Output Format
Exact structure of what the agent returns:
- Summary format
- Required fields
- Length expectations

## Common Patterns

### Exploration agent

```markdown
---
description: Explores codebase to answer questions about structure and patterns
tools: Glob, Grep, Read, LS
model: haiku
---

You are a codebase exploration agent.

## Task

Find and analyze code relevant to the user's question. Return a concise summary.

## Constraints

- Read-only exploration; do not suggest changes
- Focus on facts, not opinions
- Limit file reads to what's necessary

## Output Format

Return:
1. Direct answer to the question (2-3 sentences)
2. Key files discovered (paths only)
3. Relevant code patterns found (if applicable)
```

### Code review agent

```markdown
---
description: Reviews code for bugs, security issues, and style violations
tools: Glob, Grep, Read
model: sonnet
---

You are a code review agent.

## Task

Review the specified code for issues. Focus on bugs, security, and maintainability.

## Constraints

- Report only significant issues
- Don't suggest stylistic changes unless severe
- Provide evidence (line numbers, code snippets)

## Output Format

Return issues as:

### [Severity: High/Medium/Low] Issue Title
- **Location**: file:line
- **Problem**: What's wrong
- **Impact**: Why it matters
- **Fix**: Suggested remediation
```

### Test analysis agent

```markdown
---
description: Analyzes test coverage and identifies gaps
tools: Glob, Grep, Read, Bash
model: sonnet
---

You are a test analysis agent.

## Task

Analyze test coverage for the specified code. Identify gaps and suggest additions.

## Constraints

- Focus on behavior coverage, not line coverage
- Don't rewrite existing tests
- Prioritize high-impact gaps

## Output Format

Return:
1. Coverage summary (what's tested, what's not)
2. Critical gaps (untested paths that matter)
3. Suggested test cases (describe, don't implement)
```

## Anti-patterns

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| Vague task instructions | Agent interprets broadly, wastes turns | Be specific |
| No output format | Main thread gets unstructured dumps | Specify format |
| Using opus for simple lookups | Slow and expensive | Use haiku |
| Expecting shared state | Agents are isolated | Pass all context in prompt |
| No constraints | Agent scope-creeps | Add explicit boundaries |
| Returning raw file contents | Context pollution | Require summaries |

## Parallel Execution

Launch multiple agents simultaneously for independent tasks:

```
# In a single message, call Task tool multiple times:
- Task(subagent_type: "explorer", prompt: "Find auth code")
- Task(subagent_type: "explorer", prompt: "Find API routes")
- Task(subagent_type: "reviewer", prompt: "Review security.py")
```

All three run in parallel; results return as they complete.

## Background Execution

For long-running tasks:

```
Task(
  subagent_type: "<name>",
  prompt: "<task>",
  run_in_background: true
)
```

Returns immediately with `output_file` path. Check progress with Read tool or `tail`.

## Testing

1. Create agent in `.claude/agents/`
2. Test via Task tool: `subagent_type: "<name>"`
3. Verify output format matches specification
4. Test edge cases (empty results, large outputs)
5. Verify tool restrictions work as expected

## Workflow

1. Create `.claude/agents/<name>.md`
2. Add frontmatter with description and tool restrictions
3. Write clear task instructions, constraints, output format
4. Test via Task tool with `subagent_type: <name>`
5. Promote: `uv run scripts/promote agent <name>`

## Compliance Checklist

Before promoting an agent, verify:

- [ ] `name` is lowercase with hyphens only
- [ ] `description` clearly explains when to use this agent
- [ ] Purpose statement in body is specific, not vague
- [ ] Task instructions are actionable
- [ ] Constraints prevent scope creep
- [ ] Output format is specified exactly
- [ ] `tools` field matches task needs (omit to inherit all)
- [ ] Model selection is appropriate (haiku/sonnet/opus)
- [ ] Tested with representative prompts
- [ ] Output format verified in practice

## Built-in Agent Types

Claude Code includes three built-in subagents:

| Type | Purpose | Model | Tools |
|------|---------|-------|-------|
| `general-purpose` | Complex research + modification tasks | sonnet | All tools |
| `Plan` | Codebase research in plan mode | sonnet | Read, Glob, Grep, Bash (exploration) |
| `Explore` | Fast read-only codebase exploration | haiku | Glob, Grep, Read, Bash (read-only) |

**Auto-triggering**: Built-in agents activate automatically based on context:
- `general-purpose`: Multi-step operations requiring exploration + modification
- `Plan`: Only in plan mode when codebase understanding needed
- `Explore`: Searching/understanding codebase without making changes

**Disabling built-in agents**: Add to `deny` array in settings: `["Task(Explore)", "Task(Plan)"]`

Custom agents extend these capabilities for specialized workflows.

## See Also

- **skills.md** — User-facing workflows (agents are typically internal)
- **commands.md** — Simple prompts (use when isolation isn't needed)
- **plugins.md** — Bundle agents for distribution via marketplaces
- **settings.md** — Configure agent permissions with `Task(AgentName)` rules

## References

Authoritative specification (imported for full context):
- @.claude/skills/auditing-tool-designs/references/fallback-specs.md — Subagent configuration and built-in types

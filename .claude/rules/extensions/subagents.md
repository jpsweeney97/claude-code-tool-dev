---
paths:
  - ".claude/agents/**"
  - "~/.claude/agents/**"
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
- **Iterative refinement**: When the task needs frequent back-and-forth
- **Latency-sensitive operations**: Agents start fresh and may need time to gather context

## Agent Priority

When multiple agents share the same name, higher priority wins:

| Priority    | Scope   | Path                         |
| ----------- | ------- | ---------------------------- |
| 1 (highest) | Session | `--agents` CLI flag (JSON)   |
| 2           | Project | `.claude/agents/<name>.md`   |
| 3           | User    | `~/.claude/agents/<name>.md` |
| 4 (lowest)  | Plugin  | Plugin's `agents/` directory |

This allows project-level agents to shadow user-level agents for testing.

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
tools: Glob, Grep, Read # Optional: comma-separated list
model: haiku # Optional: sonnet, opus, haiku, or 'inherit'
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

| Field             | Required | Type   | Notes                                                                                |
| ----------------- | -------- | ------ | ------------------------------------------------------------------------------------ |
| `name`            | Yes      | string | Unique identifier (lowercase + hyphens)                                              |
| `description`     | Yes      | string | Natural language description. Include "use proactively" to encourage auto-delegation |
| `tools`           | No       | string | Comma-separated allowlist; omit to inherit all                                       |
| `disallowedTools` | No       | string | Comma-separated denylist; removed from inherited/specified tools                     |
| `model`           | No       | string | `sonnet`, `opus`, `haiku`, or `inherit`                                              |
| `permissionMode`  | No       | string | Permission mode (see table below)                                                    |
| `skills`          | No       | list   | YAML list of skills to auto-load (injected at startup, not inherited from parent) |
| `hooks`           | No       | object | `PreToolUse`, `PostToolUse`, or `Stop` handlers scoped to subagent                   |

### Permission Modes

| Mode                | Behavior                                                           |
| ------------------- | ------------------------------------------------------------------ |
| `default`           | Standard permission checking with prompts                          |
| `acceptEdits`       | Auto-accept file edits                                             |
| `dontAsk`           | Auto-deny permission prompts (explicitly allowed tools still work) |
| `bypassPermissions` | Skip all permission checks (use with caution)                      |
| `plan`              | Plan mode (read-only exploration)                                  |

If the parent uses `bypassPermissions`, this takes precedence and cannot be overridden.

### Skills Field Example

```yaml
---
name: data-analyst
description: Analyzes data using SQL and visualization
tools: Read, Grep, Bash
skills:
  - sql-analysis
  - chart-generation
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
      hooks:
        - type: command
          command: ./scripts/validate-command.sh
  Stop:
    - hooks:
        - type: command
          command: ./scripts/cleanup.sh
---
```

The nested `hooks` array with `type: command` is required. This structure supports future hook types beyond shell commands.

Agent hooks are scoped to the subagent's execution lifecycle. `once: true` is NOT supported for agent hooks.

### Project-Level Agent Hooks

Beyond hooks in agent frontmatter, define hooks in `settings.json` that respond to agent lifecycle:

```json
{
  "hooks": {
    "SubagentStart": [
      { "matcher": "db-agent", "hooks": [{ "type": "command", "command": "./setup.sh" }] }
    ],
    "SubagentStop": [
      { "matcher": "db-agent", "hooks": [{ "type": "command", "command": "./cleanup.sh" }] }
    ]
  }
}
```

| Event           | When            | Matcher    |
| --------------- | --------------- | ---------- |
| `SubagentStart` | Agent begins    | Agent name |
| `SubagentStop`  | Agent completes | Agent name |

Use `matcher` to target specific agents. Omit to run for all agents.

### Hook Environment Variables

Hook commands receive context via environment variables:

| Variable      | Description                                |
| ------------- | ------------------------------------------ |
| `$TOOL_INPUT` | JSON string of the tool's input parameters |

Example validation script:

```bash
#!/bin/bash
# Block write queries in db-reader agent
if echo "$TOOL_INPUT" | grep -qiE '(INSERT|UPDATE|DELETE|DROP)'; then
  echo "Write operations not allowed" >&2
  exit 2  # Block the tool call
fi
exit 0
```

## Invoking Agents

Agents are invoked via the Task tool:

```
Task tool parameters:
- description: "Short summary"   # Required (brief task description)
- prompt: "<task details>"       # Required
- subagent_type: "<name>"        # Required
- model: "haiku"                 # Optional override
- resume: "<agentId>"            # Optional: continue previous agent
- max_turns: 10                  # Optional turn limit
- run_in_background: true        # Optional async execution
```

## Design Principles

### Agents are autonomous

Once started, agents run to completion without user interaction. Design for autonomy.

### Agents return summaries, not raw data

Agents should process information and return distilled findings. The main thread shouldn't receive 10 files of raw content.

### Agents have separate context

Each agent invocation starts fresh. Agents receive only their system prompt (markdown body) and basic environment details (working directory, platform). They do **not** receive the full Claude Code system prompt or parent conversation context.

### Agents can't nest

An agent cannot spawn other agents via Task tool. Plan accordingly.

### Choose the right model

| Task Type                      | Model  | Rationale          |
| ------------------------------ | ------ | ------------------ |
| Doc lookup, simple queries     | haiku  | Fast, cheap        |
| Standard development           | sonnet | Balanced           |
| Complex architecture, planning | opus   | Highest capability |

Built-in agents `general-purpose` and `Plan` inherit the main conversation's model. Override with the `model` parameter when invoking via Task tool if needed.

## Prompt Clarity

The prompt determines whether the agent works or fails. See [subagent-writing-guide.md](skills/brainstorming-subagents/references/subagent-writing-guide.md) for full details.

| Dimension | Check |
|-----------|-------|
| **Specificity** | Would two specialists with this prompt work the same way? |
| **Context Transfer** | Is all necessary info included? No reliance on conversation agent won't have? |
| **Output Contracts** | Format specified exactly? Level of detail matches consumer needs? |
| **Boundaries** | Defined from both directions (what TO do, what NOT to do)? |
| **Consistency** | No contradictions between sections? Tools match constraints? |

**Specificity examples:**

| Vague | Specific |
|-------|----------|
| "Review the code" | "Review for security vulnerabilities — injection, auth bypasses, data exposure" |
| "Analyze the system" | "Trace data flows, map component dependencies, identify integration points" |
| "Help with testing" | "Analyze test coverage, identify edge case gaps, assess error path testing" |

## Scope Calibration

Finding the right scope is the difference between a useful agent and a broken one.

| Problem | Signs | Result |
|---------|-------|--------|
| **Too broad** | "Analyze the codebase" with no focus; no constraints | Agent wanders, returns unfocused findings |
| **Too narrow** | Single lookup; would be faster to do directly | Overhead exceeds value |
| **Right scope** | Domain + focus + depth + boundaries defined | Specialist produces useful output |

**Calibration questions:**
- Would a human specialist with this scope produce useful output?
- Is there enough work to justify delegation overhead?
- Are boundaries clear enough to prevent scope creep?
- Are boundaries loose enough that valuable findings won't be missed?

## Quality Dimensions

Quick reference for agent review. See [subagent-writing-guide.md](skills/brainstorming-subagents/references/subagent-writing-guide.md) for full details.

| Dimension | Check |
|-----------|-------|
| **Task fidelity** | Purpose explicit; non-goals listed; success criteria defined |
| **Context completeness** | All necessary info in prompt; assumptions stated; no reliance on missing context |
| **Output actionability** | Format specified exactly; detail level appropriate; includes what to omit |
| **Constraint clarity** | Allowed vs forbidden explicit; tools match task; boundaries from both directions |
| **Instruction consistency** | No contradictions; tools match constraints; scope matches output expectations |
| **Autonomy fit** | Can complete without clarifying questions; failure modes have defaults |

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

| Anti-pattern                  | Problem                                | Fix                        |
| ----------------------------- | -------------------------------------- | -------------------------- |
| Vague task instructions       | Agent interprets broadly, wastes turns | Be specific                |
| No output format              | Main thread gets unstructured dumps    | Specify format             |
| Using opus for simple lookups | Slow and expensive                     | Use haiku                  |
| Expecting shared state        | Agents are isolated                    | Pass all context in prompt |
| No constraints                | Agent scope-creeps                     | Add explicit boundaries    |
| Returning raw file contents   | Context pollution                      | Require summaries          |

## Parallel Execution

Launch multiple agents simultaneously for independent tasks:

```
# In a single message, call Task tool multiple times:
- Task(subagent_type: "explorer", prompt: "Find auth code")
- Task(subagent_type: "explorer", prompt: "Find API routes")
- Task(subagent_type: "reviewer", prompt: "Review security.py")
```

All three run in parallel; results return as they complete.

**Note:** When subagents complete, their results return to your main conversation. Running many subagents that each return detailed results can consume significant context. Design agents to return summaries, not raw data.

## Chaining Agents

For multi-step workflows, use agents in sequence. Each agent completes and returns results, which are then passed to the next:

```
# From main conversation:
1. Use code-reviewer agent to find performance issues
2. Use optimizer agent to fix them (receives reviewer's findings)
```

This works because the main conversation coordinates — agents cannot spawn other agents.

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

### Background Execution Limitations

Background agents differ from foreground:

| Aspect          | Foreground           | Background                           |
| --------------- | -------------------- | ------------------------------------ |
| MCP tools       | Available            | **Not available** (design around)    |
| Permissions     | Prompts pass through | Auto-deny if not pre-approved        |
| AskUserQuestion | Works                | Fails (agent continues)              |
| Recovery        | N/A                  | Resume in foreground to retry        |

If an agent needs MCP tools, it must run in foreground.

## Resuming Agents

Agents can be resumed to continue work with full context preserved.

### Resume Pattern

```typescript
// Initial invocation returns agentId
Task(description: "Review auth", prompt: "...", subagent_type: "reviewer")
// Returns: { agentId: "abc123", ... }

// Resume later with new instructions
Task(resume: "abc123", prompt: "Now also check authorization")
```

### When to Resume

- Continuing multi-phase work
- Adding follow-up tasks
- Correcting or refining output

### Storage

Transcripts persist at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`

Auto-deleted after `cleanupPeriodDays` (default: 30).

### Auto-Compaction

Subagents support automatic compaction using the same logic as the main conversation. By default, auto-compaction triggers at approximately 95% capacity. Set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` to a lower percentage (e.g., `50`) to trigger earlier.

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

**Testing:**

- [ ] Tested with representative prompts
- [ ] Output format verified in practice

## Built-in Agent Types

Claude Code includes three built-in subagents:

| Type              | Model    | Tools                              | Notes                                      |
| ----------------- | -------- | ---------------------------------- | ------------------------------------------ |
| `general-purpose` | Inherits | All                                | Multi-step modification tasks              |
| `Plan`            | Inherits | Read, Glob, Grep, Bash             | Plan mode architecture                     |
| `Explore`         | Haiku    | Glob, Grep, Read, Bash (read-only) | Thoroughness: quick, medium, very thorough |

**Auto-triggering**: Built-in agents activate automatically based on context:

- `general-purpose`: Multi-step operations requiring exploration + modification
- `Plan`: Only in plan mode when codebase understanding needed
- `Explore`: Searching/understanding codebase without making changes

**Disabling built-in agents**: Add to `deny` array in settings: `["Task(Explore)", "Task(Plan)"]`

Or via CLI: `claude --disallowedTools "Task(Explore)"`

Custom agents extend these capabilities for specialized workflows.

## See Also

- **skills.md** — User-facing workflows (agents are typically internal)
- **commands.md** — Simple prompts (use when isolation isn't needed)
- **plugins.md** — Bundle agents for distribution via marketplaces
- **settings.md** — Configure agent permissions with `Task(AgentName)` rules


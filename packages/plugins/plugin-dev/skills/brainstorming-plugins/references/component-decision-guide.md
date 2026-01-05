# Plugin Component Decision Guide

Detailed guidance for selecting the right plugin components.

## Component Comparison Matrix

| Aspect | Skill | Command | Agent | Hook | MCP | LSP |
|--------|-------|---------|-------|------|-----|-----|
| **Invoked by** | Claude (automatic) | User (`/cmd`) | Claude or user | Events | Claude (as tool) | Claude (as tool) |
| **Context** | Shared | Shared | Separate | N/A | Shared | Shared |
| **Purpose** | Knowledge | Actions | Isolated tasks | Guarantees | External tools | Code intelligence |
| **Trigger** | Description match | Explicit | Task match | Event fires | Tool call | File type |

## Decision Flowchart

```
Does Claude need specialized KNOWLEDGE?
├─ Yes → Skill
└─ No → Does the USER invoke something explicitly?
         ├─ Yes → Command
         └─ No → Needs SEPARATE CONTEXT or different tools?
                  ├─ Yes → Agent
                  └─ No → Must ALWAYS happen on an event?
                           ├─ Yes → Hook
                           └─ No → External API/service needed?
                                    ├─ Yes → MCP Server
                                    └─ No → Language-specific code intelligence?
                                             ├─ Yes → LSP Server
                                             └─ No → Reconsider the problem
```

## Common Patterns

### Knowledge + Explicit Action
**Components:** Skill + Command
**Use when:** Claude should know something AND user wants explicit invocation
**Example:** Code review guidelines (Skill) + `/review` command

### Automated Validation
**Components:** Hook (command or prompt type)
**Use when:** Something must ALWAYS happen after specific tool use
**Example:** Lint after Write/Edit operations

### Complex Autonomous Task
**Components:** Agent + Skills (via `skills:` field)
**Use when:** Task needs isolation, different tools, or extensive autonomy
**Example:** Security audit agent with restricted tools

### External Integration
**Components:** MCP Server + Skill
**Use when:** Need external API AND Claude needs to know how to use it well
**Example:** Database MCP + query patterns Skill

## Anti-Patterns to Avoid

| Don't Do This | Do This Instead |
|---------------|-----------------|
| Agent when you just need knowledge | Use a Skill |
| Hook for optional behavior | Use a Skill with guidance |
| Multiple components when one suffices | Start minimal, add if needed |
| MCP for local file operations | Use built-in tools |
| Skill for explicit user actions | Use a Command |

## Implementation Notes

### Portable Paths

When designing plugins with hooks or MCP servers, always use `${CLAUDE_PLUGIN_ROOT}`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
      }]
    }]
  }
}
```

### Directory Structure Rule

Components go at plugin root, NOT inside `.claude-plugin/`:

```
my-plugin/
├── .claude-plugin/plugin.json  ← Only manifest here
├── commands/                   ← At root
├── skills/                     ← At root
├── agents/                     ← At root
└── hooks/                      ← At root
```

### Hook Events Reference

| Event | When it fires |
|-------|---------------|
| `PreToolUse` | Before Claude uses any tool |
| `PostToolUse` | After successful tool use |
| `PostToolUseFailure` | After tool execution fails |
| `UserPromptSubmit` | When user sends a message |
| `SessionStart` | At session beginning |
| `SessionEnd` | At session end |
| `Stop` | When Claude attempts to stop |
| `SubagentStop` | When a subagent attempts to stop |
| `PreCompact` | Before conversation history compaction |

### Hook Types

| Type | Use for |
|------|---------|
| `command` | Shell scripts, deterministic operations |
| `prompt` | LLM evaluation, flexible decisions |
| `agent` | Complex verification with tool access |

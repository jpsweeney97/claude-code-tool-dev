---
name: brainstorming-hooks
description: Use when designing a hook, "I need X to always happen",
  "hook vs skill", "prevent Claude from Y", or after brainstorming-plugins
  identifies hooks. Guides collaborative hook design through 6-step process.
---

# Hook Design

Turn hook ideas into design documents through collaborative dialogue.

## Quick Start

```
User: "I need a hook for X"
Claude: Uses 6-step workflow

1. Problem definition (what must ALWAYS happen?)
2. Event selection (10 events, matchers, capabilities)
3. Type decision (command vs prompt)
4. Architecture constraints (parallel execution, timeouts)
5. Security review (5-point checklist)
6. Output design (exit codes, JSON fields) → write design document

→ Handoff to implementing-hooks
```

## Triggers

- `design a hook for {purpose}`
- `I need {behavior} to always happen`
- `hook vs skill` / `when should I use hooks`
- `prevent Claude from {action}`
- After `brainstorming-plugins` identifies hooks

## Prerequisites

Before using this skill:
- Know you need a hook (from `/brainstorming-plugins` or direct need)
- Understand hooks = deterministic control (ALWAYS happens, not guidance)

No design document? This skill creates one.

## Pipeline Context

This skill is **Stage 2: Design** in the hooks pipeline.

| Aspect | Value |
|--------|-------|
| This stage | Design hook from requirements |
| Previous | `/brainstorming-plugins` (or direct request) |
| Next | `/implementing-hooks` |
| Reference | `hook-development` (structural details) |

## Core Principle

Hooks provide deterministic control—behavior that MUST always happen, not guidance Claude can ignore.

**Decision rule:**
| Need | Use |
|------|-----|
| Guidance Claude should consider | Skill |
| Behavior that must always happen | Hook |

## The 6-Step Workflow

### Step 1: Problem Definition

Ask one question at a time:

| Question | Purpose |
|----------|---------|
| What must ALWAYS happen? | Confirms deterministic need |
| When should it trigger? | Maps to event selection |
| What breaks if this fails? | Determines security rigor |

**Output:** "When {event}, {action} must always happen because {reason}."

**Example:** "When Claude uses the Write tool on a .env file, the write must be blocked because credentials must never be modified by automation."

### Step 2: Event Selection

| Event | Fires When | Blocks? | Use For |
|-------|------------|---------|---------|
| PreToolUse | Before tool runs | Yes (allow/deny/ask) | Validation, permissions |
| PermissionRequest | Permission dialog shown | Yes (allow/deny) | Auto-approve/deny |
| PostToolUse | After tool completes | No | Formatting, logging, feedback |
| UserPromptSubmit | User submits prompt | Yes | Context injection, validation |
| Notification | Claude notifies | No | Desktop alerts, logging |
| Stop | Agent finishes | Yes | Completion validation |
| SubagentStop | Subagent finishes | Yes | Task validation |
| SessionStart | Session begins | No | Load context, set env vars |
| SessionEnd | Session ends | No | Cleanup, logging |
| PreCompact | Before compaction | No | Preserve context |

**Matchers** (for events that support them):

| Event | Matcher Type | Examples |
|-------|--------------|----------|
| PreToolUse | Tool name (regex) | `Bash`, `Write\|Edit`, `mcp__.*` |
| PermissionRequest | Tool name (regex) | Same as PreToolUse |
| PostToolUse | Tool name (regex) | Same as PreToolUse |
| Notification | Notification type | `permission_prompt`, `idle_prompt` |
| SessionStart | Source | `startup`, `resume`, `clear`, `compact` |
| PreCompact | Trigger | `manual`, `auto` |

**Special capabilities:**

| Event | Capability | Use Case |
|-------|------------|----------|
| PreToolUse | `updatedInput` | Modify tool args before execution |
| PermissionRequest | `updatedInput` | Modify and auto-approve |
| SessionStart | `CLAUDE_ENV_FILE` | Persist env vars for session |
| SessionStart | `additionalContext` | Load project context |
| UserPromptSubmit | `additionalContext` | Inject context for Claude |

### Step 3: Type Decision

| Factor | Command Hook | Prompt Hook |
|--------|--------------|-------------|
| Logic | Deterministic rules | Context-aware judgment |
| Speed | Fast (local) | Slower (API call) |
| Setup | Requires script | Configure prompt only |
| Best for | File checks, formatting | Completion validation |

**Decision:**
- Express as code? → Command hook
- Requires understanding conversation? → Prompt hook

### Step 4: Architecture Constraints

| Constraint | Implication |
|------------|-------------|
| Hooks run in parallel | Cannot depend on another hook's output |
| 60-second default timeout | Keep hooks fast |
| Hooks load at startup | Changes require restart |
| JSON via stdin | Must parse input |
| Exit codes matter | 0=success, 2=block |

### Step 5: Security Review

**Mandatory checklist:**

| Check | Implementation |
|-------|----------------|
| Validate inputs | Never trust `tool_input` blindly |
| Quote variables | `"$VAR"` not `$VAR` |
| Block path traversal | Check for `..` in paths |
| Use absolute paths | `$CLAUDE_PROJECT_DIR` or `$CLAUDE_PLUGIN_ROOT` |
| Skip sensitive files | `.env`, `.git/`, credentials |

### Step 6: Output Design

**Exit code behavior per event:**

| Event | Exit Code 2 |
|-------|-------------|
| PreToolUse | Blocks tool, stderr → Claude |
| PermissionRequest | Denies permission, stderr → Claude |
| PostToolUse | stderr → Claude (tool already ran) |
| UserPromptSubmit | Blocks prompt, stderr → user |
| Stop/SubagentStop | Blocks stopping, stderr → Claude |
| Others | stderr → user only |

**JSON output fields:**

| Event | Decision | Context | Modification |
|-------|----------|---------|--------------|
| PreToolUse | `permissionDecision`, `permissionDecisionReason` | — | `updatedInput` |
| PermissionRequest | `decision.behavior`, `message` | — | `updatedInput` |
| PostToolUse | `decision`, `reason` | `additionalContext` | — |
| Stop/SubagentStop | `decision`, `reason` | — | — |
| UserPromptSubmit | `decision`, `reason` | `additionalContext` | — |
| SessionStart | — | `additionalContext` | — |

**Common fields (all events):** `continue`, `stopReason`, `suppressOutput`, `systemMessage`

## Output

Write design to: `docs/plans/YYYY-MM-DD-<hook-name>-design.md`

**Sections:**
1. Problem — What must always happen
2. Event — Selected event and matchers
3. Type — Command or prompt
4. Output design — Exit codes, JSON fields
5. Security — Risks and mitigations
6. Test plan — Scenarios for RED phase

## Next Step

After saving the design document:

```
/implementing-hooks docs/plans/[design-file].md
```

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Hook for everything | Adds complexity and latency | Skills for guidance, hooks for guarantees |
| Skipping security review | Data exfiltration risk | Always apply checklist |
| Vague problem statement | Can't verify hook solves issue | "When X, Y must happen" |
| Designing in isolation | May duplicate or conflict | Check hook-development first |

## Verification

Before completing:

| Check | Status |
|-------|--------|
| Problem statement (When X, Y must happen) | Defined |
| Event selected with rationale | Confirmed |
| Matchers specified (if applicable) | Listed |
| Type decision (command/prompt) | Made |
| Security checklist reviewed | Done |
| Design document saved | Path confirmed |

## References

- hook-development — Structural reference (file format, events, scripts)
- implementing-hooks — TDD implementation (next stage)
- Official hooks docs — `docs/claude-code-documentation/hooks-*.md`

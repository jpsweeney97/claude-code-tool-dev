# Task List Guide

Reference documentation for Claude Code's task list feature and associated tools.

## Overview

When working on complex, multi-step work, Claude creates a task list to track progress. Tasks appear in the terminal status area with indicators showing what's pending, in progress, or complete.

### User Interaction

| Action | Method |
|--------|--------|
| Toggle task list view | Press **Ctrl+T** (shows up to 10 tasks) |
| Show all tasks | Ask Claude: "show me all tasks" |
| Clear all tasks | Ask Claude: "clear all tasks" |

Tasks persist across context compactions, helping Claude stay organized on larger projects.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_TASK_LIST_ID` | Share a task list across sessions. Set the same ID in multiple Claude Code instances to coordinate on a shared task list. Uses named directory in `~/.claude/tasks/` |
| `CLAUDE_CODE_ENABLE_TASKS` | Set to `false` to revert to previous TODO list instead of the task tracking system. Default: `true` |

**Example:** Share a task list across sessions:
```bash
CLAUDE_CODE_TASK_LIST_ID=my-project claude
```

## Task Tools

All task tools require **no permission** to use.

### TaskCreate

Creates a new task in the task list.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subject` | string | **Yes** | Brief title for the task (imperative form, e.g., "Fix authentication bug") |
| `description` | string | **Yes** | Detailed description of what needs to be done |
| `activeForm` | string | No | Present continuous form shown in spinner when in_progress (e.g., "Fixing authentication bug") |
| `metadata` | object | No | Arbitrary metadata to attach to the task |

**Notes:**
- All tasks are created with status `pending`
- Subject should be imperative ("Run tests") while activeForm should be present continuous ("Running tests")
- After creating tasks, use TaskUpdate to set up dependencies if needed

### TaskGet

Retrieves a task by its ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `taskId` | string | **Yes** | The ID of the task to retrieve |

**Returns:**
- `subject` — Task title
- `description` — Detailed requirements and context
- `status` — `pending`, `in_progress`, or `completed`
- `blocks` — Tasks waiting on this one to complete
- `blockedBy` — Tasks that must complete before this one can start

### TaskList

Lists all tasks in the task list. Takes no parameters.

**Returns for each task:**
- `id` — Task identifier (use with TaskGet, TaskUpdate)
- `subject` — Brief description of the task
- `status` — `pending`, `in_progress`, or `completed`
- `owner` — Agent ID if assigned, empty if available
- `blockedBy` — List of open task IDs that must be resolved first

### TaskUpdate

Updates an existing task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `taskId` | string | **Yes** | The ID of the task to update |
| `status` | string | No | New status: `pending`, `in_progress`, `completed`, or `deleted` |
| `subject` | string | No | New title for the task |
| `description` | string | No | New description |
| `activeForm` | string | No | Present continuous form for spinner |
| `owner` | string | No | Agent name to assign the task |
| `metadata` | object | No | Metadata keys to merge (set key to `null` to delete) |
| `addBlocks` | string[] | No | Task IDs that this task blocks |
| `addBlockedBy` | string[] | No | Task IDs that block this task |

**Status Workflow:**
```
pending → in_progress → completed
```

Use `deleted` to permanently remove a task.

## Task Dependencies

Tasks support blocking relationships for proper sequencing:

- **addBlocks** — Mark tasks that cannot start until this one completes
- **addBlockedBy** — Mark tasks that must complete before this one can start

Tasks with `blockedBy` entries cannot be claimed until their dependencies resolve.

## Multi-Agent Coordination

The `owner` field enables coordination between multiple agents:

1. Use TaskList to find available tasks (status: `pending`, no owner, not blocked)
2. Claim a task by setting `owner` via TaskUpdate
3. Mark as `in_progress` when starting work
4. Mark as `completed` when finished
5. Call TaskList to find next available task

## Best Practices

### When to Use Task Lists

- Complex multi-step tasks requiring 3+ distinct steps
- User provides multiple tasks (numbered or comma-separated)
- Plan mode work that needs tracking
- User explicitly requests a todo list

### When NOT to Use Task Lists

- Single, straightforward tasks
- Trivial tasks with no organizational benefit
- Tasks completable in less than 3 trivial steps
- Purely conversational or informational exchanges

### Task Completion Rules

- Only mark a task as `completed` when fully accomplished
- If errors, blockers, or partial completion: keep as `in_progress`
- When blocked, create a new task describing what needs resolution
- Never mark as completed if tests are failing or implementation is partial

## Related Commands

| Command | Purpose |
|---------|---------|
| `/tasks` | List and manage background tasks (shells/agents, distinct from task list) |
| `/todos` | List current TODO items (legacy system) |

## Sources

- [Task list documentation](https://code.claude.com/docs/en/interactive-mode#task-list)
- [Tools available to Claude](https://code.claude.com/docs/en/settings#tools-available-to-claude)
- [Environment variables](https://code.claude.com/docs/en/settings#environment-variables)

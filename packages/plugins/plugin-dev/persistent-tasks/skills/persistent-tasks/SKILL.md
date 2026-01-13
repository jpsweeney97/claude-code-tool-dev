---
name: persistent-tasks
description: Cross-session task persistence with dependency tracking. Use MCP tools for task management.
---

# Persistent Tasks

Track tasks across sessions with dependency-aware ordering.

## MCP Tools

This skill provides 6 MCP tools. Use them directly:

| Tool | Purpose |
|------|---------|
| `add_task` | Add a new task |
| `list_tasks` | List all tasks |
| `get_task` | Get task by ID |
| `update_task` | Update task fields |
| `next_task` | Get next actionable task |
| `remove_task` | Remove a task |

## Quick Reference

**Add task:**
```
add_task(title="Implement auth", priority="high")
```

**Add with dependencies:**
```
add_task(title="Add tests", dependencies=[1, 2])
```

**List tasks:**
```
list_tasks()
list_tasks(status="pending")
list_tasks(blocked=true)
```

**Get next task:**
```
next_task()
next_task(start=true)  # Mark as in-progress
```

**Mark done:**
```
update_task(task_id=1, status="done")
```

**Remove task:**
```
remove_task(task_id=1)
```

## Selection Algorithm

`next_task` selects based on:
1. In-progress tasks first
2. Priority (high > medium > low)
3. Fewer dependencies
4. Lower ID

Blocked tasks (dependencies not done) are excluded.

## Storage

| Location | Purpose |
|----------|---------|
| `.claude/tasks/tasks.json` | Project-specific tasks |
| `~/.claude/tasks/tasks.json` | Global tasks (fallback) |

## Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Not started |
| `in-progress` | Currently working |
| `review` | Ready for review |
| `done` | Complete |
| `deferred` | Postponed |
| `cancelled` | Won't do |

## Integration with TodoWrite

Use persistent-tasks for cross-session tracking, TodoWrite for in-session visibility:

1. Start session: `next_task(start=true)`
2. During session: Use TodoWrite for subtask tracking
3. End session: `update_task(task_id=X, status="done")`

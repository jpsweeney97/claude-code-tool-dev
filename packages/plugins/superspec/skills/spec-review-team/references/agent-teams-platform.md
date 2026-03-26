# Agent Teams Platform Reference

Source: `code.claude.com/en/agent-teams`, `code.claude.com/en/hooks`
Verified: 2026-03-15

This document captures the agent teams platform contract as it applies to skill development. It is the authoritative source for tool behavior, hook schemas, and constraints within this skill. When in doubt, verify against the source docs — platform behavior evolves.

**Agent teams vs subagents — the key architectural distinction:**

- **Subagents** run _within_ a single session, report results back to the caller, and disappear. Hub-and-spoke.
- **Agent teams** are _independent Claude Code sessions_ with their own context windows, a shared task list, and inter-agent messaging (mailbox). Mesh topology.

## Architecture

| Component     | Role                                                                                |
| ------------- | ----------------------------------------------------------------------------------- |
| **Team lead** | The main Claude Code session. Creates the team, spawns teammates, coordinates work. |
| **Teammates** | Separate Claude Code instances. Each works on assigned tasks.                       |
| **Task list** | Shared list of work items. Teammates claim and complete tasks.                      |
| **Mailbox**   | Messaging system for inter-agent communication.                                     |

**Storage:**

- Team config: `~/.claude/teams/{team-name}/config.json`
- Task list: `~/.claude/tasks/{team-name}/`
- The config contains a `members` array with each teammate's name, agent ID, and agent type. Teammates can read this file to discover other team members.

**Hard constraints:**

- One team per session. Clean up the current team before starting a new one.
- No nested teams. Teammates cannot spawn their own teams or teammates. Only the lead can manage the team.
- Lead is fixed. The session that creates the team is the lead for its lifetime. Cannot promote a teammate to lead or transfer leadership.

## Team Lifecycle

### 1. TeamCreate

Creates the team structure. Does NOT spawn teammates.

**Parameters:**

- `team_name` — descriptive team identifier (e.g., `"spec-review"`)
- `description` — what the team does

**Creates:** team config file + shared task list.

**If deferred:** fetch via `ToolSearch` before use.

### 2. TaskCreate

Creates tasks in the shared task list.

**Task states:** `pending` → `in progress` → `completed`

**Dependencies:** tasks can depend on other tasks. A pending task with unresolved dependencies cannot be claimed until those dependencies are completed. The system manages unblocking automatically — when a teammate completes a dependency, blocked tasks unblock without manual intervention. Task claiming uses file locking to prevent race conditions.

**Other task tools:**

- `TaskGet` — retrieves full details for a specific task
- `TaskList` — lists all tasks with current status
- `TaskUpdate` — updates task status, dependencies, details, or deletes tasks

None of these require special permissions.

### 3. Spawn via Agent tool

Teammates are spawned using the `Agent` tool with the `team_name` parameter. This is what makes a spawned agent a teammate — without `team_name`, it's an isolated subagent with no messaging, shared tasks, or idle notifications.

**Key parameters:**

- `team_name` — must match the TeamCreate team name
- `name` — teammate identifier, used for all addressing (SendMessage, task ownership, shutdown). Use role IDs (e.g., `"authority-architecture"`), never UUIDs.
- `model` — model for the teammate (e.g., `"sonnet"`)
- `prompt` — spawn prompt with role, context, output expectations

**Context inheritance:** teammates load CLAUDE.md, MCP servers, and skills automatically — the same ambient context as any Claude Code session. They also receive the spawn prompt from the lead. The lead's conversation history does NOT carry over. Reviewer-specific context comes from the spawn prompt and workspace files.

**Permissions:** all teammates start with the lead's permission mode. Can change individually after spawning but not at spawn time.

### 4. SendMessage

Two messaging primitives:

| Primitive     | Syntax         | Cost                           | When to use                         |
| ------------- | -------------- | ------------------------------ | ----------------------------------- |
| **message**   | `to: "{name}"` | 1 recipient                    | Targeted cross-lens signals         |
| **broadcast** | `to: "*"`      | N recipients (scales linearly) | Discoveries affecting all reviewers |

**Delivery:** messages arrive at recipients automatically. No polling needed.

**Structured messages:** SendMessage supports both plain text and structured protocol messages:

- `{type: "shutdown_request", reason: "..."}`
- `{type: "shutdown_response", ...}`
- `{type: "plan_approval_response", ...}`

**Peer DM visibility:** when a teammate sends a DM to another teammate, a brief summary appears in the sender's idle notification. The lead sees these summaries without polling.

### 5. Shutdown

1. Lead sends shutdown request to each teammate via `SendMessage` with `message: {type: "shutdown_request", reason: "..."}`.
2. Teammate can approve (exits gracefully) or reject with an explanation.
3. Teammates finish their current request or tool call before shutting down — this can take time.
4. If a teammate rejects, send another shutdown request with additional context.

**Known platform behaviors:**
- Shutdown can be slow — teammates finish their current request or tool call before processing the shutdown message.
- Teammates can reject shutdown requests with an explanation.
- Task status can lag behind actual teammate state — idle notifications are the real signal.

### 6. TeamDelete

Removes shared team resources (team config, task files).

**Parameters:** none.

**Precondition:** fails if any teammates are still active. Shut down all teammates first (step 5).

**Ownership:** always use the lead to clean up. Teammates should not run cleanup because their team context may not resolve correctly, potentially leaving resources in an inconsistent state.

### 7. Cleanup Resilience Protocol

Shutdown and TeamDelete can fail. This protocol defines retry budgets, orphan handling, and degraded-state reporting so skills don't hang or leave half-cleaned teams.

#### Retry Budget

Each teammate gets up to **3 shutdown attempts** before being classified as orphaned:

| Attempt | Message content | Wait |
|---------|----------------|------|
| 1 | `{type: "shutdown_request", reason: "[task] complete"}` | Wait for idle notification |
| 2 | Add context: "All work is complete, findings have been saved. Please shut down." | Wait for idle notification |
| 3 | Final: "Session ending. Cleanup requires all teammates to shut down. This is the final request." | 30s timeout — no idle notification = orphaned |

"Wait for idle notification" means: wait until the next idle notification or until 60 seconds pass with no activity (no idle notifications, no task status changes via `TaskGet`).

#### Orphan Classification

A teammate is **orphaned** when:
- 3 shutdown attempts sent with no idle confirmation, OR
- Teammate was already classified as failed during the review phase (timeout, missing findings)

Track orphaned teammates as a list of `{name, reason}` tuples.

#### TeamDelete with Orphans

| Orphan count | Action |
|-------------|--------|
| 0 | Call `TeamDelete` normally |
| >0, some teammates idle | Call `TeamDelete`. If it fails, report degraded state |
| All teammates orphaned | Call `TeamDelete`. If it fails, report degraded state |

**If `TeamDelete` fails:** Do NOT retry `TeamDelete` in a loop. Report degraded state and proceed.

#### Degraded State Reporting

When any teammate is orphaned or `TeamDelete` fails, report to the user:

```
Team cleanup partially failed: [N] teammate(s) did not shut down ([names]).
Team resources may remain at ~/.claude/teams/{team-name}/.
These will be cleaned up when a new team is created, or remove manually.
```

Then proceed with workspace cleanup. Workspace cleanup is independent of team cleanup — always attempt it regardless of TeamDelete outcome.

#### Cleanup Sequence Summary

```
for each teammate:
  attempt 1: send shutdown_request
  wait for idle (60s timeout)
  if not idle: attempt 2 with context → wait (60s)
  if not idle: attempt 3 final → wait (30s)
  if still not idle: classify as orphaned

call TeamDelete
  if success: done
  if fail: report degraded state to user

clean up workspace directory (always)
```

## Hooks

### TeammateIdle

Fires when an agent team teammate is about to go idle after finishing its turn.

**Input fields** (in addition to common fields `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`):

| Field           | Type   | Description                           |
| --------------- | ------ | ------------------------------------- |
| `teammate_name` | string | Name of the teammate about to go idle |
| `team_name`     | string | Name of the team                      |

**Decision control — two mechanisms:**

| Mechanism                                       | Effect                                                                                   |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Exit code 2                                     | Teammate receives stderr message as feedback and continues working instead of going idle |
| JSON `{"continue": false, "stopReason": "..."}` | Stops the teammate entirely. `stopReason` shown to user                                  |

**Constraints:**

- **Hook types: `command` ONLY.** Prompt-based, HTTP, and agent hooks will NOT fire for TeammateIdle. This is a platform constraint, not a configuration issue.
- **No matcher support.** Fires for every teammate unconditionally. Filtering by reviewer role must be done inside the hook logic.

### TaskCompleted

Fires in two situations: (1) when any agent explicitly marks a task as completed through TaskUpdate, or (2) when an agent team teammate finishes its turn with in-progress tasks.

**Input fields** (in addition to common fields):

| Field              | Type    | Description                                     |
| ------------------ | ------- | ----------------------------------------------- |
| `task_id`          | string  | Identifier of the task being completed          |
| `task_subject`     | string  | Title of the task                               |
| `task_description` | string? | Detailed description (may be absent)            |
| `teammate_name`    | string? | Name of the completing teammate (may be absent) |
| `team_name`        | string? | Name of the team (may be absent)                |

**Decision control — same two mechanisms as TeammateIdle:**

| Mechanism                                       | Effect                                                 |
| ----------------------------------------------- | ------------------------------------------------------ |
| Exit code 2                                     | Task not marked completed; stderr fed back as feedback |
| JSON `{"continue": false, "stopReason": "..."}` | Stops the teammate entirely                            |

**Constraints:**

- **Hook types: ALL FOUR supported** (command, http, prompt, agent).
- **No matcher support.** Fires for every task unconditionally. Filtering by task or reviewer must be done inside the hook logic.

### SubagentStop (NOT for teammates)

SubagentStop fires for subagents, not teammates. Teammates are full independent sessions. If you need to intercept a teammate finishing, use TeammateIdle or TaskCompleted.

## Costs & Model Selection

- Agent teams spawn multiple Claude Code instances, each with its own context window.
- Token usage scales with the number of active teammates and how long each one runs.
- Broadcast messages cost linearly — each broadcast sends a separate message to every recipient's context window.
- Active teammates continue consuming tokens even if idle.

**Model recommendation:** "Use Sonnet for teammates. It balances capability and cost for coordination tasks." The lead (running synthesis) uses the session's default model.

**Spawn prompt sizing:** teammates load CLAUDE.md, MCP servers, and skills automatically. Everything in the spawn prompt adds to context from the start — keep spawn prompts focused on task-specific details.

## Best Practices

**From the official docs:**

- Start with 3-5 teammates. No hard limit, but token costs scale linearly and coordination overhead increases.
- 5-6 tasks per teammate keeps everyone productive without excessive context switching.
- Task sizing: too small = coordination overhead exceeds benefit; too large = teammates work too long without check-ins. Self-contained units that produce a clear deliverable.
- Avoid file conflicts: two teammates editing the same file leads to overwrites. Break work so each teammate owns a different set of files.
- Monitor and steer: check in on progress, redirect approaches. Letting a team run unattended increases risk of wasted effort.
- If the lead starts implementing instead of waiting, tell it to wait.

**Best use cases:** research/review, new modules/features, debugging with competing hypotheses, cross-layer coordination.

**When NOT to use:** sequential tasks, same-file edits, or work with many dependencies. A single session or subagents are more effective.

## Constraints & Known Limitations

| Constraint            | Detail                                                                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Experimental          | Disabled by default. Enable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings.json `env` or shell environment                                                  |
| Version               | Requires Claude Code v2.1.32 or later                                                                                                                              |
| One team per session  | Clean up current team before starting a new one                                                                                                                    |
| No nested teams       | Teammates cannot spawn teams or teammates                                                                                                                          |
| No session resumption | `/resume` and `/rewind` do not restore in-process teammates. Lead may attempt to message non-existent teammates after resume                                       |
| Task status lag       | Teammates sometimes fail to mark tasks as completed, which blocks dependent tasks. Idle notifications are the primary completion signal                            |
| Shutdown delay        | Teammates finish current request/tool call before shutting down                                                                                                    |
| Lead is fixed         | Cannot promote a teammate to lead or transfer leadership                                                                                                           |
| Permissions at spawn  | All teammates start with lead's permission mode. Can change individually after spawning but not at spawn time                                                      |
| Display modes         | `in-process` (default), `tmux`, split panes. Setting: `teammateMode` in settings.json. Split panes NOT supported in VS Code terminal, Windows Terminal, or Ghostty |

**Changelog notes (known bugs fixed):**

- Memory retention fix: in-process teammates previously pinned parent's full conversation history for teammate's lifetime (fixed v2.1.69).
- Nested team prevention: fixed teammates accidentally spawning nested teammates via the Agent tool's `name` parameter.

## Plan Approval Flow

Teammates can work in read-only plan mode. When planning is done, the teammate sends a plan approval request to the lead. The lead approves or rejects with feedback. If rejected, the teammate revises and resubmits. Once approved, the teammate exits plan mode and implements.

This flow is available but not used by spec-review-team — reviewers produce findings, not plans.

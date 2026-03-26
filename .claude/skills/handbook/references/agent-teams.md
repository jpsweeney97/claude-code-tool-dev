# Agent Teams Reference

Adapted from `packages/plugins/superspec/skills/spec-review-team/references/agent-teams-platform.md`.
For documentation skills (readme, changelog, handbook).

## Architecture

| Component | Role |
|-----------|------|
| **Team lead** | The main Claude Code session. Creates team, spawns teammates, coordinates. |
| **Teammates** | Separate Claude Code instances with their own context windows. |
| **Task list** | Shared work items. Teammates claim and complete tasks. |
| **Mailbox** | Inter-agent messaging system. |

**Key distinction:** Subagents run within a single session, report back, and disappear (hub-and-spoke). Agent teams are independent sessions with shared tasks and messaging (mesh). This skill uses agent teams, not subagents.

## Team Lifecycle

### 1. TeamCreate

Creates team structure. Does NOT spawn teammates.

- `team_name` — descriptive identifier (e.g., `"readme-exploration"`)
- `description` — what the team does

Creates: team config at `~/.claude/teams/{team-name}/config.json` + shared task list at `~/.claude/tasks/{team-name}/`.

If deferred: fetch via `ToolSearch` before use.

### 2. TaskCreate

Creates tasks in the shared task list. States: `pending` → `in progress` → `completed`.

Tasks can declare dependencies via `blockedBy`. Blocked tasks cannot be claimed until dependencies complete. For exploration teams, all tasks run in parallel — do NOT set dependencies.

Other task tools: `TaskGet` (read one), `TaskList` (list all), `TaskUpdate` (update status/details).

### 3. Agent (with team_name)

Teammates are spawned via the `Agent` tool with the `team_name` parameter. This parameter is what makes a spawned agent a teammate — without it, the agent is an isolated subagent with no messaging, shared tasks, or idle notifications.

Parameters:
- `team_name` — must match the TeamCreate name
- `name` — teammate identifier used for all addressing (SendMessage, task ownership). Use role IDs (e.g., `"cartographer"`), never UUIDs
- `model` — model for the teammate (e.g., `"sonnet"`)
- `prompt` — spawn prompt with role, context, output expectations

**Context inheritance:** Teammates load CLAUDE.md, MCP servers, and skills automatically. The lead's conversation history does NOT carry over. Everything the teammate needs must be in the spawn prompt or workspace files.

### 4. SendMessage

Two messaging primitives:

| Primitive | Syntax | Cost | When to use |
|-----------|--------|------|-------------|
| **message** | `to: "{name}"` | 1 recipient | Targeted cross-teammate signals |
| **broadcast** | `to: "*"` | N recipients (scales linearly) | Discoveries affecting all teammates |

Messages arrive automatically — no polling needed.

**Peer DM visibility:** When a teammate DMs another, a brief summary appears in the sender's idle notification. The lead sees these summaries without polling.

### 5. Completion Detection

**Primary signal:** Idle notifications. When a teammate finishes and goes idle, the lead receives a notification automatically.

**Secondary signal:** Task status via `TaskGet`. Known to lag behind actual teammate state — use idle notifications as the authoritative signal.

**Timeout pattern:** If no idle notifications or task status changes for 5 minutes, treat the silent teammate as failed and proceed with available findings.

### 6. Shutdown

1. Lead sends `SendMessage` to each teammate: `{type: "shutdown_request", reason: "..."}`.
2. Teammate finishes current tool call, then shuts down. This may take time.
3. If a teammate rejects shutdown, retry with additional context.

### 7. TeamDelete

Removes shared team resources (config, task files).

**Precondition:** Fails if any teammate is still active. Shut down all teammates first.

**Ownership:** Only the lead calls TeamDelete. Teammates must not self-cleanup.

## Hard Constraints

| Constraint | Detail |
|-----------|--------|
| Experimental | Enable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings.json env or shell |
| One team per session | Clean up current team before starting a new one |
| No nested teams | Teammates cannot spawn teams or teammates |
| No session resumption | `/resume` and `/rewind` do not restore teammates |
| Task status lag | Idle notifications are primary; task status is secondary confirmation |
| Shutdown delay | Teammates finish current request before shutting down |
| Permissions | All teammates start with the lead's permission mode |

## Cost Model

- Each teammate is a separate Claude Code instance with its own context window
- Token usage scales with number of teammates and how long each runs
- Broadcast messages cost linearly — each broadcast sends to every recipient's context
- Use Sonnet for teammates to balance capability and cost; lead uses the session's default model
- Keep spawn prompts focused — teammates auto-load CLAUDE.md, MCP servers, and skills, so spawn prompts add on top of that baseline

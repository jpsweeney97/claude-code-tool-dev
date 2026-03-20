# Context Metrics Research

**Date:** 2026-02-28
**Branch:** `feature/context-metrics`
**Objective:** Determine how to make context metrics (tokens, percentage of session context window used/remaining, etc.) available to Claude during a session.

---

## 1. claude-devtools Overview

**What it is:** A cross-platform desktop application (Electron + web) that reconstructs and visualizes Claude Code session execution. It reads raw session logs from `~/.claude/` and presents them in an interactive UI.

**Architecture:** Electron-vite (main/preload/renderer), React 18 UI, Node.js 20+, pnpm 10+. Also supports standalone/Docker mode (headless Node.js HTTP server).

**Key insight:** It is a passive session reconstruction engine — it reads JSONL log files after the fact. It has no inbound channel to Claude Code (cannot push data into a session).

### Data Pipeline

```
~/.claude/projects/{encoded-path}/*.jsonl
  → ProjectScanner (discovers sessions)
  → SessionParser (parses JSONL)
  → MessageClassifier (user/AI/system/compact)
  → ChunkBuilder (groups into UserChunk/AIChunk/SystemChunk/CompactChunk)
  → SubagentResolver (enriches subagent data)
  → ToolExecutionBuilder (extracts tool calls with token attribution)
  → ContextTracker (reconstructs context window consumption)
  → DataCache (LRU 50 entries, 10min TTL)
  → IPC (Electron) or HTTP API (standalone/sidecar)
```

### Session Identification

- **projectId**: URL-encoded filesystem path: `/Users/jp/myproject` → `-Users-jp-myproject`
- **sessionId**: UUID (JSONL filename without extension), validated via regex `^[a-f0-9-]+$`
- **Filesystem mapping**: `~/.claude/projects/{projectId}/{sessionId}.jsonl`

### File Watching

- Local: `fs.watch()` with recursive mode + 30s catch-up scan for missed FSEvents
- Debounce: 100ms window for rapid changes to same file
- Events: `file-change` and `todo-change`
- Cache invalidation: `DataCache` keyed by `{projectId}:{sessionId}`, invalidated on file changes

---

## 2. Devtools HTTP API

**Server:** Optional HTTP sidecar on port 3456 (configurable). Always-on in standalone mode.

**No authentication, no CORS restrictions, no rate limiting.** Localhost-only.

### Endpoints

| Route | Method | Returns |
|-------|--------|---------|
| `/api/projects` | GET | `Project[]` |
| `/api/projects/:projectId/sessions` | GET | `Session[]` |
| `/api/projects/:projectId/sessions-paginated` | GET | `PaginatedSessionsResult` |
| `/api/projects/:projectId/sessions-by-ids` | POST | `Session[]` (pinned sessions) |
| `/api/projects/:projectId/sessions/:sessionId` | GET | `SessionDetail` |
| `/api/projects/:projectId/sessions/:sessionId/metrics` | GET | `SessionMetrics` |
| `/api/projects/:projectId/sessions/:sessionId/groups` | GET | `ConversationGroup[]` |
| `/api/projects/:projectId/sessions/:sessionId/waterfall` | GET | `WaterfallData` |
| `/api/projects/:projectId/sessions/:sessionId/subagents/:subagentId` | GET | `SubagentDetail` |
| `/api/search?query=...&maxResults=...` | GET | `SearchSessionsResult` |
| `/api/repository-groups` | GET | `RepositoryGroup[]` |
| `/api/events` | GET (SSE) | Real-time event stream |

### Key Data Schemas

```typescript
interface SessionMetrics {
  durationMs: number;
  totalTokens: number;
  inputTokens: number;
  outputTokens: number;
  cacheReadTokens: number;
  cacheCreationTokens: number;
  messageCount: number;
  costUsd?: number;
}

interface SessionDetail {
  session: Session;
  messages: ParsedMessage[];
  chunks: Chunk[];
  processes: Process[];
  metrics: SessionMetrics;
}

interface ConversationGroup {
  id: string;
  type: 'user-ai-exchange';
  userMessage: ParsedMessage;
  aiResponses: ParsedMessage[];
  processes: Process[];
  toolExecutions: ToolExecution[];
  taskExecutions: TaskExecution[];
  startTime: Date;
  endTime: Date;
  durationMs: number;
  metrics: SessionMetrics;
}
```

### Context Tracking (ContextTracker)

Tracks token consumption across 6 categories:

```typescript
interface ContextStats {
  newInjections: ContextInjection[];
  accumulatedInjections: ContextInjection[];
  totalEstimatedTokens: number;
  tokensByCategory: TokensByCategory;
  newCounts: NewCountsByCategory;
  phaseNumber?: number;
}

interface TokensByCategory {
  claudeMd: number;           // CLAUDE.md files
  mentionedFiles: number;     // @-mentioned files
  toolOutputs: number;        // Tool call + result tokens
  thinkingText: number;       // Extended thinking + text output
  taskCoordination: number;   // SendMessage, TeamCreate, TaskCreate, etc.
  userMessages: number;       // User prompt tokens per turn
}
```

**6 injection categories** (discriminated union):

| Category | Type | Data |
|----------|------|------|
| `claude-md` | `ClaudeMdInjection` | File path, scope (global/project/directory), token estimate |
| `mentioned-file` | `MentionedFileInjection` | Path, display name, estimated tokens, first-seen turn/group |
| `tool-output` | `ToolOutputInjection` | Turn index, tool breakdown (name, token count, error status), total tokens |
| `thinking-text` | `ThinkingTextInjection` | Turn index, breakdown (thinking vs text tokens), total tokens |
| `team-coordination` | `TeamCoordinationInjection` | Tool name (SendMessage, TaskCreate), turn index, tokens |
| `user-message` | `UserMessageInjection` | Turn index, message text length, estimated tokens |

**Phase tracking:** Context phases track compaction boundaries. Each phase stores `phaseNumber`, `contribution` (tokens added), `peakTokens`, `postCompaction`.

**Token estimation:** Uses `estimateTokens()` for text. Per-turn tracking with cumulative accumulation. Phase-aware: resets after compaction events.

### SSE Event Stream (`/api/events`)

```typescript
// Event channels:
// "file-change"           → FileChangeEvent
// "todo-change"           → FileChangeEvent
// "notification:new"      → DetectedError
// "notification:updated"  → { total: number; unreadCount: number }
// "ssh:status"            → SshConnectionStatus
// "context:changed"       → ContextInfo
```

Keep-alive: `:ping` every 30 seconds.

### Gap: Context Window Ceiling

Devtools tracks consumption but not the ceiling (context window limit). It doesn't know whether the session is using a 200k or 1M context model. The model identifier is available in hook input — we would need a model → window size mapping.

---

## 3. HTTP Hooks (Claude Code Feature)

HTTP hooks (`type: "http"`) are a hook handler type that sends the event's JSON input as an HTTP POST to a URL and reads the response body.

### Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:8080/hooks/pre-tool-use",
            "timeout": 30,
            "headers": {
              "Authorization": "Bearer $MY_TOKEN"
            },
            "allowedEnvVars": ["MY_TOKEN"]
          }
        ]
      }
    ]
  }
}
```

### HTTP-Specific Fields

| Field | Required | Description |
|-------|----------|-------------|
| `url` | yes | URL to POST to |
| `headers` | no | Key-value pairs. Values support `$VAR_NAME` / `${VAR_NAME}` interpolation |
| `allowedEnvVars` | no | Whitelist of env vars for header interpolation. Unlisted vars → empty string |

Plus common fields: `type`, `timeout`, `statusMessage`, `once`.

### Request Protocol

Claude Code POSTs the same JSON input that command hooks get on stdin, with `Content-Type: application/json`.

### Response Protocol

| Response | Effect |
|----------|--------|
| 2xx + empty body | Success, no output (like exit 0 with no stdout) |
| 2xx + plain text body | Success, text added as context |
| 2xx + JSON body | Success, parsed using same JSON output schema as command hooks |
| Non-2xx status | Non-blocking error, execution continues |
| Connection failure / timeout | Non-blocking error, execution continues |

**Critical difference from command hooks:** HTTP hooks cannot block via status code alone. To block a tool call or deny a permission, return **2xx** with a JSON body containing `decision: "block"` or `hookSpecificOutput.permissionDecision: "deny"`.

### Fail-Open Design

HTTP hooks are fail-open by design. Non-2xx responses, connection failures, and timeouts all produce non-blocking errors that allow execution to continue. If the target server isn't running, the hook silently does nothing.

### Deduplication

HTTP hooks are deduplicated by URL. Each unique URL runs once per event firing.

### Configuration Notes

- Must be configured by editing settings JSON directly (the `/hooks` interactive menu only supports command hooks)
- Can be defined in plugins via `hooks/hooks.json`
- Can be defined in skill/agent frontmatter (scoped to component lifetime)

---

## 4. Hook Event Analysis for Context Injection

### Events That Inject Context Visible to Claude

| Hook Event | Context Visible? | Mechanism | Fires When |
|---|---|---|---|
| **SessionStart** | Yes | stdout or `additionalContext` | Session start, resume, `/clear`, **after compaction** |
| **UserPromptSubmit** | Yes | stdout or `additionalContext` | Every user prompt |
| **PostToolUse** | Yes | `additionalContext` in `hookSpecificOutput` | After every successful tool call |
| **PostToolUseFailure** | Yes | `additionalContext` in `hookSpecificOutput` | After tool failure |
| **SubagentStart** | Yes (to subagent only) | `additionalContext` | When subagent spawns |
| **PreCompact** | No | Side effects only, no decision control | Before compaction |
| **Stop** | No | Only `decision: "block"` + `reason` | When Claude finishes |

### Common Hook Input Fields (All Events)

| Field | Description |
|-------|-------------|
| `session_id` | Current session UUID |
| `transcript_path` | Path to conversation JSONL (e.g., `~/.claude/projects/-Users-jp-myproject/abc123.jsonl`) |
| `cwd` | Current working directory |
| `permission_mode` | `"default"`, `"plan"`, `"acceptEdits"`, `"dontAsk"`, or `"bypassPermissions"` |
| `hook_event_name` | Name of the event |

**Token counts and context usage are NOT included in any hook input.** This is the gap — hooks don't natively know how much context is used.

### Event-Specific Input

| Event | Additional Fields |
|-------|-------------------|
| **SessionStart** | `source` (`startup`/`resume`/`clear`/`compact`), `model`, optional `agent_type` |
| **UserPromptSubmit** | `prompt` (submitted text) |
| **PreToolUse** | `tool_name`, `tool_input`, `tool_use_id` |
| **PostToolUse** | `tool_name`, `tool_input`, `tool_response`, `tool_use_id` |
| **PostToolUseFailure** | `tool_name`, `tool_input`, `tool_use_id`, `error`, `is_interrupt` |
| **PreCompact** | `trigger` (`manual`/`auto`), `custom_instructions` |
| **Stop** | `stop_hook_active` (bool), `last_assistant_message` |

### JSON Output Schema (Universal Fields)

| Field | Description |
|-------|-------------|
| `continue` | `false` stops Claude entirely |
| `stopReason` | Shown to user when `continue: false` |
| `suppressOutput` | Hides stdout from verbose mode |
| `systemMessage` | Warning message shown to user |

### Key Pattern: Re-inject After Compaction

Officially documented pattern: `SessionStart` with matcher `"compact"` re-injects critical context after compaction. Context metrics would survive compaction naturally through this mechanism.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Reminder: use Bun, not npm. Current sprint: auth refactor.'"
          }
        ]
      }
    ]
  }
}
```

### Key Pattern: Dual Visibility

The `require-gitflow.py` hook in this project demonstrates the dual-visibility pattern:

```python
def context_output(message: str) -> dict:
    return {
        "systemMessage": message,          # Visible to user
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": message,   # Visible to Claude
        },
    }
```

---

## 5. Session ID Bridge

The `transcript_path` from hook input bridges the two systems:

- Hook input: `transcript_path` = `~/.claude/projects/-Users-jp-myproject/abc123.jsonl`
- Devtools API: `projectId` = `-Users-jp-myproject`, `sessionId` = `abc123`

Parsing is straightforward: extract the parent directory name (projectId) and the filename stem (sessionId) from `transcript_path`.

---

## 6. Existing Project Patterns

### Current Hooks (All `type: "command"`)

- `PreToolUse` → `require-gitflow.py` (branch protection, dual-visibility pattern)
- Cross-model plugin hooks (`hooks/hooks.json`):
  - `PreToolUse` on Codex tools → `codex_guard.py` (validation)
  - `PostToolUse` on Codex tools → `codex_guard.py` (post-execution)
  - `PostToolUseFailure` on Bash → `nudge_codex.py` (suggests Codex after 3 failures)

### No Existing HTTP Hooks

This project currently uses only command hooks. HTTP hooks would be a new pattern.

### `additionalContext` Confirmed Working

Verified in production (Feb 2026): `PostToolUseFailure` `additionalContext` appears as a `PostToolUseFailure:Bash hook additional context:` system-reminder in Claude's context.

---

## 7. Design Considerations

### Advantages of HTTP Hooks for This Use Case

1. **No process spawn overhead** — devtools HTTP server is already running
2. **Fail-open** — if devtools isn't running, hook silently does nothing (graceful degradation)
3. **Same JSON protocol** — response uses same output schema as command hooks
4. **Low latency** — localhost HTTP round-trip vs. process fork + Python interpreter startup
5. **Stateful** — devtools maintains in-memory cache with parsed session data; no cold-start parsing

### Challenges

1. **Devtools must be running** — optional dependency, not guaranteed
2. **No native token counts in hook input** — must derive from devtools or transcript parsing
3. **Context window ceiling unknown to devtools** — need model → window size mapping
4. **Latency budget** — `UserPromptSubmit` fires on every prompt; hook must be fast
5. **New endpoint needed** — devtools doesn't currently have a "context metrics summary" endpoint optimized for hook consumption
6. **HTTP hooks not yet in project** — new pattern to establish

### Injection Point Trade-offs

| Injection Point | Frequency | Latency Sensitivity | Context Value |
|---|---|---|---|
| `SessionStart` (startup) | Once | Low | Baseline metrics |
| `SessionStart` (compact) | Per compaction | Low | Critical — re-inject after context loss |
| `UserPromptSubmit` | Per prompt | Medium | Per-turn updates, highest value |
| `PostToolUse` | Per tool call | Medium | Granular but noisy (many tool calls per turn) |

### What Needs Building

1. **New devtools endpoint** — `/api/hooks/context-summary` or similar, optimized for fast response with minimal data: total tokens, tokens by category, compaction count, estimated percentage
2. **Model → window size mapping** — either in the hook handler or in devtools, to compute percentage remaining
3. **Hook configuration** — HTTP hook entries for the chosen injection points
4. **Response formatting** — compact `additionalContext` string that's useful to Claude without being noisy

---

## 8. Architecture Sketch (Pre-Brainstorm)

```
Claude Code Session
  │
  ├─ SessionStart (startup) ─── HTTP POST ──→ devtools:3456/api/hooks/context-summary
  │                                            ├─ Parse transcript_path → projectId + sessionId
  │                                            ├─ Fetch/compute session metrics
  │                                            ├─ Map model → window size
  │                                            └─ Return { additionalContext: "Context: 45k/200k tokens (22%)..." }
  │
  ├─ UserPromptSubmit ─── HTTP POST ──→ devtools:3456/api/hooks/context-summary
  │                                      └─ Return updated metrics
  │
  ├─ SessionStart (compact) ─── HTTP POST ──→ devtools:3456/api/hooks/context-summary
  │                                            └─ Return post-compaction metrics + "compaction #N just occurred"
  │
  └─ [Claude sees metrics in system-reminders, can reason about context budget]
```

This is a preliminary sketch. Formal brainstorming will evaluate alternatives and trade-offs.

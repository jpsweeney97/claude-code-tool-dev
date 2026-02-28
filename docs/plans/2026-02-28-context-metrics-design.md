# Context Metrics Design

**Date:** 2026-02-28
**Branch:** `feature/context-metrics`
**Status:** Design approved, pending implementation plan

## Objective

Give Claude passive awareness of its context window consumption during a session. Claude sees a compact summary line (~20 tokens) before each response and after compaction, enabling it to mention context status when relevant without changing its behavior.

## Requirements

- **Passive awareness only** — informational, not behavioral. Claude does not adapt its behavior based on metrics.
- **Requires claude-devtools** running on port 3456. Fail-open: if devtools is unavailable, no metrics are injected and nothing breaks.
- **Per-turn updates** via `UserPromptSubmit` hook — Claude sees fresh metrics before every response.
- **Survives compaction** via `SessionStart(compact)` hook — metrics are re-injected into post-compaction context.
- **On-demand detail** via `/context-dashboard` skill — full breakdown available when requested.
- **Two-tier context window model** — supports both hard limits and soft boundaries (200k cost threshold on 1M windows).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code Session                    │
│                                                          │
│  UserPromptSubmit ──HTTP POST──→ sidecar:7432            │
│  SessionStart(compact) ─command─→ context_summary.py ─┐  │
│                                                       │  │
│  ← additionalContext: "Context: 142k/200k (71%)..."   │  │
└───────────────────────────────────────────────────────┘  │
        │                                    ▲         │   │
        │ Hook JSON input                    │         │   │
        ▼                                    │         ▼   │
┌─────────────────────────────────────────────────────────┐
│              Plugin Sidecar (Python HTTP)                 │
│                                                          │
│  1. Parse transcript_path → projectId + sessionId        │
│  2. GET devtools:3456/api/.../metrics                    │
│  3. Read window config from ~/.claude/context-metrics... │
│  4. Format summary line                                  │
│  5. Return { additionalContext: "..." }                   │
│                                                          │
│  Started by: SessionStart(startup) async command hook    │
│  Stopped by: SessionEnd command hook                     │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP GET (existing API, unmodified)
                  ▼
┌─────────────────────────────────────────────────────────┐
│              claude-devtools (port 3456)                  │
│                                                          │
│  /api/projects/:projectId/sessions/:sessionId/metrics    │
│  → { totalTokens, inputTokens, outputTokens,            │
│      cacheReadTokens, cacheCreationTokens,               │
│      messageCount, costUsd, durationMs }                 │
└─────────────────────────────────────────────────────────┘
```

### Why a sidecar (not direct HTTP hook to devtools)

claude-devtools is a third-party open-source tool. Adding a custom endpoint would require an upstream PR with external review/merge dependencies. The sidecar queries devtools' existing API without modifications, adds window-size configuration and summary formatting, and can evolve independently.

### Why HTTP hooks where possible

HTTP hooks avoid process spawn overhead (~1-5ms localhost round-trip vs ~100-300ms Python interpreter startup). The sidecar is already running, so the HTTP hook path is the fastest option. `SessionStart` is restricted to `type: "command"` hooks by Claude Code, so the post-compaction path uses a thin command-hook wrapper script that makes an HTTP request to the sidecar internally.

## Plugin Structure

```
packages/plugins/context-metrics/
├── .claude-plugin/
│   └── plugin.json              # { name, version, description, author, license, keywords }
├── hooks/
│   └── hooks.json               # HTTP + command hooks
├── scripts/
│   ├── start_sidecar.py         # SessionStart(startup) — async, starts server
│   ├── stop_sidecar.py          # SessionEnd — stops server (stdlib only)
│   ├── context_summary.py       # SessionStart(compact) — queries sidecar, prints JSON
│   ├── server.py                # HTTP sidecar server
│   ├── devtools_client.py       # Devtools API client
│   └── models.py                # Window configuration reader
├── skills/
│   └── context-dashboard/
│       └── SKILL.md             # On-demand full dashboard
├── pyproject.toml               # Python dependencies (bootstrapped via uv run)
├── README.md
└── CHANGELOG.md
```

**Marketplace entry** (added to `.claude-plugin/marketplace.json`):

```json
{ "name": "context-metrics", "source": "./packages/plugins/context-metrics" }
```

**Install:** `claude plugin install context-metrics@turbo-mode`

## Hook Configuration

```json
{
  "description": "Context metrics injection via claude-devtools sidecar",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/start_sidecar.py",
            "async": true,
            "statusMessage": "Starting context metrics sidecar"
          }
        ]
      },
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_summary.py",
            "timeout": 5,
            "statusMessage": "Refreshing context metrics"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:7432/hooks/context-metrics",
            "timeout": 5,
            "statusMessage": "Updating context metrics"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stop_sidecar.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Hook type rationale

| Hook | Type | Why |
|------|------|-----|
| SessionStart(startup) | `command` (async) | SessionStart is command-only. Async avoids blocking session start. `uv run` bootstraps deps on first invocation. |
| SessionStart(compact) | `command` | SessionStart is command-only. Script makes HTTP request to sidecar, prints `additionalContext` JSON to stdout. |
| UserPromptSubmit | `http` | Supports all hook types. HTTP avoids process spawn. Sidecar returns `additionalContext` directly. |
| SessionEnd | `command` | SessionEnd is command-only. Stdlib script reads PID file, sends SIGTERM. |

### Event type restrictions (verified against docs)

Events supporting all hook types (`command`, `prompt`, `agent`, `http`): `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `PreToolUse`, `Stop`, `SubagentStop`, `TaskCompleted`, `UserPromptSubmit`.

Events restricted to `type: "command"` only: `ConfigChange`, `Notification`, `PreCompact`, `SessionEnd`, `SessionStart`, `SubagentStart`, `TeammateIdle`, `WorktreeCreate`, `WorktreeRemove`.

## Sidecar Server

### Endpoint

```
POST /hooks/context-metrics
```

Accepts Claude Code hook JSON input. Returns hook-compatible JSON with `additionalContext`.

### Request → Response Flow

1. **Parse session identifiers** from `transcript_path` → `projectId` + `sessionId`
2. **Read window config** from `~/.claude/context-metrics.local.md` (cached at startup)
3. **Query devtools** via `GET /api/projects/:projectId/sessions/:sessionId/metrics`
4. **Compute percentages** against configured window size and soft boundary
5. **Format summary line** appropriate to current state
6. **Return** `{ hookSpecificOutput: { hookEventName, additionalContext } }`

### Session ID Bridge

The `transcript_path` from hook input maps directly to devtools API parameters:

```
transcript_path: ~/.claude/projects/-Users-jp-myproject/abc123.jsonl
                                    ├── projectId ──┘        └── sessionId
```

Parse: parent directory name = `projectId`, filename stem = `sessionId`.

### State

| State | Storage | Lifecycle |
|-------|---------|-----------|
| PID file | `~/.claude/.context-metrics-sidecar.pid` | Written on start, cleaned on stop or next start |
| Window config | In-memory (read from config file) | Loaded at startup |
| Devtools response cache | In-memory, 5s TTL | Prevents redundant requests on rapid prompt submissions |

### Startup / Shutdown

- **`start_sidecar.py`**: Check PID file → kill stale process if exists → start `server.py` as daemon → write PID file. Uses `uv run` for dependency bootstrap.
- **`stop_sidecar.py`**: Read PID file → send SIGTERM → remove PID file. Stdlib only (no deps).
- **Abrupt termination safe**: If SessionEnd hook doesn't fire (crash, force-quit), next session's startup cleans up the stale PID.

### Error Handling

| Failure | Behavior |
|---------|----------|
| Devtools not running | Return 200 with note: "devtools unavailable — no context metrics" |
| Sidecar not running | HTTP hook gets connection failure → non-blocking error, Claude proceeds |
| Devtools returns unexpected data | Return 200 with degraded summary using available fields |
| Config file missing | Use defaults: `context_window=200000`, no soft boundary |

Fail-open at every layer.

## Context Window Configuration

### Config file

`~/.claude/context-metrics.local.md`

```yaml
---
context_window: 1000000
soft_boundary: 200000
---
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `context_window` | int | `200000` | Hard limit in tokens |
| `soft_boundary` | int | Same as `context_window` | Cost threshold. When `context_window > soft_boundary`, warnings are emitted as consumption approaches the boundary. |

### Why a config file (not auto-detection)

The `message.model` field in transcripts and the `model` field in `SessionStart` hook input report `claude-opus-4-6` without distinguishing the 200k and 1M context window variants. The `[1m]` suffix (e.g., `claude-opus-4-6[1m]`) appears in the system prompt but is not accessible to hooks or transcript parsing. No reliable programmatic detection exists.

## Summary Line Format

### Default (~20 tokens)

```
Context: 142k/200k tokens (71%) | 847 messages | Phase 3 (2 compactions) | ~$1.24
```

### With soft boundary — below 80%

```
Context: 142k/200k tokens (71%) | 847 messages | Phase 3 (2 compactions) | ~$1.24
```

Same as default — no additional noise when well within bounds.

### With soft boundary — approaching (80-100% of soft boundary)

```
Context: 168k/200k tokens (84%) — approaching extended-context boundary | ~$1.48
```

### With soft boundary — exceeded

```
Context: 287k tokens — 87k beyond 200k extended-context boundary (additional cost incurred) | ~$3.12
```

### Post-compaction

```
Context: 34k/200k tokens (17%) | Compaction #3 just occurred | ~$1.24
```

## On-Demand Dashboard Skill

`/context-dashboard` produces a detailed breakdown by querying the devtools `/groups` endpoint:

```
## Context Dashboard

**Window:** 287k / 1M tokens (29%) — 87k beyond 200k soft boundary
**Cost:** ~$3.12 | **Duration:** 47m | **Messages:** 847
**Compactions:** 3 (current phase: 4)

### Token Breakdown by Category
| Category | Tokens | % |
|----------|--------|---|
| Tool outputs | 189k | 66% |
| Thinking/text | 52k | 18% |
| CLAUDE.md | 23k | 8% |
| User messages | 14k | 5% |
| Task coordination | 6k | 2% |
| Mentioned files | 3k | 1% |

### Phase History
| Phase | Peak | Post-compaction | Contribution |
|-------|------|-----------------|-------------|
| 1 | 198k | 31k | 198k |
| 2 | 195k | 28k | 164k |
| 3 | 201k | 34k | 173k |
| 4 (current) | 287k | — | 253k |
```

## Decisions Made During Design

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Devtools dependency | Required (fail-open) | Standalone, fallback | Best metrics with least code. Standalone would duplicate devtools' ContextTracker or provide inferior API-level token counts. |
| Architecture | Plugin sidecar | Direct HTTP hook to devtools, command hook with HTTP client | Don't own devtools (can't add endpoints). Sidecar avoids process spawn per-prompt. |
| Injection frequency | UserPromptSubmit + SessionStart(compact) | Session start only, PostToolUse | Per-prompt gives freshest data. Post-compaction re-injection is critical. PostToolUse is too noisy. |
| Detail level | Summary line + on-demand dashboard | Category breakdown always, full dashboard always | ~20 tokens per injection keeps overhead minimal. Full detail available via skill. |
| Window detection | Config file | Auto-detect from model string, env var | No reliable programmatic distinction between 200k and 1M variants. Config is explicit. |
| Hook type for UserPromptSubmit | HTTP | Command | HTTP avoids ~200ms process spawn overhead on every prompt. |
| Sidecar deps | `uv run` (pyproject.toml) | Stdlib only | Sidecar starts once per session (async). Cold-start latency (~17s first-ever, ~0.4s warm) is acceptable. |
| Sidecar port | 7432 | 3456 (devtools), 8080, random | Avoids conflicts with devtools (3456), postgres (5432), common dev servers. |

## Open Questions

None — all design questions resolved during brainstorming.

## References

| What | Where |
|------|-------|
| Research document | `docs/plans/2026-02-28-context-metrics-research.md` |
| Plugin rules | `.claude/rules/plugins.md` |
| Hook rules | `.claude/rules/hooks.md` |
| Hooks reference (official) | https://code.claude.com/docs/en/hooks |
| Plugin reference (official) | https://code.claude.com/docs/en/plugins-reference |
| Existing plugin pattern | `packages/plugins/cross-model/` |
| Existing plugin pattern | `packages/plugins/handoff/` |

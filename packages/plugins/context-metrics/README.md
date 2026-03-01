# Context Metrics Plugin

Context window occupancy metrics — injects a summary line into conversations via JSONL transcript analysis.

## What this plugin provides

- Sidecar HTTP server — shared process managing metrics for all concurrent Claude Code sessions
- `UserPromptSubmit` hook — queries sidecar on each prompt, conditionally injects a one-line context summary
- `SessionStart` / `SessionEnd` hooks — sidecar lifecycle management (start on first session, stop on last)
- Compaction tracking — detects `SessionStart(compact)` events and adjusts output format
- `/context-dashboard` skill — on-demand detailed context window metrics
- Configuration via `~/.claude/context-metrics.local.md` YAML frontmatter

## Installation

```bash
claude plugin install context-metrics@turbo-mode
```

Restart Claude Code after installing.

## Architecture

The plugin uses a **shared sidecar** pattern: a single HTTP server process on `127.0.0.1:7432` serves all concurrent Claude Code sessions on the machine.

```
SessionStart (startup)          SessionEnd
    │                               │
    ▼                               ▼
start_sidecar.py ──────────►  stop_sidecar.py
  │ Health check                  │ Deregister session
  │ Start if not running          │ SIGTERM sidecar if 0 sessions remain
  │ Register session              │
  ▼                               │
┌─────────────────────────┐       │
│  server.py (port 7432)  │◄──────┘
│  ┌───────────────────┐  │
│  │ Session registry   │  │   UserPromptSubmit / SessionStart(compact)
│  │ Trigger engine     │  │       │
│  │ JSONL reader       │  │       ▼
│  │ Formatter          │  │   context_summary.py
│  └───────────────────┘  │       │ POST /hooks/context-metrics
│                         │◄──────┘
│  PID: ~/.claude/        │       │
│    .context-metrics-    │       ▼
│    sidecar.pid          │   stdout → system-reminder
└─────────────────────────┘
```

Key design properties:
- **Shared across sessions** — one server process, multiple registered sessions
- **Fail-open at injection layer** — errors produce no output (session continues unaffected)
- **Fail-closed at data layer** — invalid JSONL or malformed records produce no injection
- **Delivered semantics** — session state only advances after the response is successfully sent to the client

## How it works

1. On each `UserPromptSubmit`, `context_summary.py` POSTs the session's hook input to the sidecar.
2. The sidecar reads the JSONL transcript backward from EOF to find the last valid API response.
3. It computes occupancy from the `usage` fields: `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`.
4. The trigger engine evaluates 5 trigger types (OR semantics — any one fires injection).
5. If a trigger fires, the formatter produces a summary line in the appropriate format.
6. The hook script prints the summary to stdout, which Claude Code captures as a `system-reminder`.

## Output formats

### Full (material token change or boundary crossing)

```
Context: 142k/200k tokens (71%) | 34 msgs | Phase 1
Context: 580k/1M tokens (58%) | 89 msgs | Phase 3 (2 compactions)
Context: 142k tokens — 12k beyond 130k extended-context boundary | 34 msgs | Phase 1
```

### Minimal (heartbeat with no significant change)

```
Context: ~71% (stable)
```

### Compaction (post-compact notice)

```
Context: 45k/200k tokens (22%) | Compaction #2 just occurred | 12 msgs
```

## Trigger logic

Five triggers are evaluated per prompt with OR semantics. Any single trigger fires injection.

| Trigger | Condition | Purpose |
|---------|-----------|---------|
| **Compaction** | `SessionStart(compact)` event | Always injects after compaction, resets baseline |
| **Token delta** | +5,000 tokens (normal) or +2,000 tokens (above 85% occupancy) | Catches material context growth |
| **Percentage delta** | +2% of context window | Scale-independent change detection |
| **Boundary crossing** | Occupancy crosses 25%, 50%, 75%, or 90% | Milestone awareness |
| **Heartbeat** | 8 prompts without injection (normal) or 3 prompts (above 90%) | Periodic reminder even when growth is slow |

Format priority: compaction > full (delta/boundary) > minimal (heartbeat).

Counter resets: all counters reset on injection. Compaction additionally resets boundary tracking.

## Configuration

Create `~/.claude/context-metrics.local.md` with YAML frontmatter:

```markdown
---
context_window: 200000
soft_boundary: 130000
---
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `context_window` | int | `200000` | Context window size in tokens |
| `soft_boundary` | int | none | Extended-context boundary for early warnings |

When `soft_boundary` is set, the full format includes a warning when occupancy approaches (>80% of boundary) or exceeds the boundary:

```
Context: 142k tokens — 12k beyond 130k extended-context boundary | 34 msgs | Phase 1
Context: 120k/200k tokens (60%) — approaching extended-context boundary | 34 msgs | Phase 1
```

If no config file exists, defaults are used and context window is auto-detected.

## Context window auto-detection

The plugin determines the context window size through three mechanisms, in priority order:

| Priority | Mechanism | When |
|----------|-----------|------|
| 1. Explicit config | `context_window` in config file | Always (user override) |
| 2. Model detection | Model name from JSONL `message.model` field | First API response with a recognized model |
| 3. Occupancy fallback | Observed occupancy exceeds 200k default | Any prompt where tokens > 200,000 |

Model detection uses prefix matching against known models:

| Model prefix | Window size |
|-------------|-------------|
| `claude-opus-4-6` | 1,000,000 |
| `claude-sonnet-4-6` | 1,000,000 |

Detection is one-shot: the first mechanism that activates wins for the sidecar's lifetime. Explicit config always takes precedence.

## Sidecar lifecycle

| Resource | Location |
|----------|----------|
| PID file | `~/.claude/.context-metrics-sidecar.pid` |
| Log file | `~/.claude/.context-metrics-sidecar.log` |
| Port | `127.0.0.1:7432` |
| Config | `~/.claude/context-metrics.local.md` |

Lifecycle events:

| Event | Behavior |
|-------|----------|
| First session starts | Health check fails, sidecar launched in background, session registered |
| Subsequent sessions start | Health check passes, session registered (no restart) |
| Session ends | Session deregistered; if 0 active sessions remain, SIGTERM sent to sidecar |
| Sidecar receives SIGTERM | Graceful shutdown, PID file removed |

Session registry uses lease-based expiry (600s timeout) — stale sessions are cleaned up even if `SessionEnd` hooks fail to fire.

## Skills

### `/context-dashboard`

Show detailed context window occupancy metrics by reading the current session's JSONL transcript. Use when the user asks about context usage, token counts, or window occupancy.

Displays: current occupancy, message count, compaction count, and session phase. Warns when approaching or exceeding a configured soft boundary.

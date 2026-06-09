# Context Metrics Plugin

> **v0.1.0** · MIT · Python ≥3.11 · No runtime dependencies (stdlib only)

Context window occupancy metrics — injects a summary line into conversations via JSONL transcript analysis.

## What Problem Does This Solve?

Claude Code doesn't tell you how full your context window is. You can't see how many tokens you've used, when compactions happened, or how close you are to degraded performance. The context-metrics plugin adds passive occupancy monitoring — a one-line summary injected into the conversation at meaningful moments (token growth, boundary crossings, compactions). You get awareness without distraction: it stays quiet when nothing changes, and speaks up when it matters.

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
| `claude-opus-4-7` | 1,000,000 |
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

## Hook Configuration

| Event | Matcher | Script | Timeout | Status Message |
|-------|---------|--------|---------|----------------|
| `SessionStart` | `startup` | `start_sidecar.py` | 30s | "Starting context metrics" |
| `SessionStart` | `compact` | `context_summary.py` | 5s | "Updating context metrics (post-compaction)" |
| `UserPromptSubmit` | — | `context_summary.py` | 5s | "Updating context metrics" |
| `SessionEnd` | — | `stop_sidecar.py` | 5s | — |

## Script Reference

| Script | Purpose |
|--------|---------|
| `server.py` | HTTP sidecar server: handles `/health`, `/sessions/*`, `/hooks/context-metrics` endpoints. Thread-safe session state management. |
| `context_summary.py` | Hook entry point for `UserPromptSubmit` and `SessionStart(compact)`. POSTs to sidecar, prints response to stdout. |
| `start_sidecar.py` | Hook entry point for `SessionStart(startup)`. Health-check-first: if running, just registers. Otherwise launches in background with up to 2s startup poll. |
| `stop_sidecar.py` | Hook entry point for `SessionEnd`. Deregisters session; sends SIGTERM only when 0 active sessions remain. |
| `trigger_engine.py` | 5-trigger OR-logic evaluation engine with format priority selection. |
| `formatter.py` | Token count formatting for full, minimal, and compaction output formats. Soft boundary warning logic. |
| `jsonl_reader.py` | Backward JSONL scan from EOF + forward message count. 4-condition positive selector with deduplication by message ID. |
| `session_registry.py` | Lease-based session tracker (600s timeout). Thread-safe. Stale sessions cleaned even if `SessionEnd` hooks fail. |
| `config.py` | Config reader: custom stdlib YAML parser (no runtime dependencies). Model detection and occupancy-based window auto-upgrade. |

## Skills

### `/context-dashboard`

Show detailed context window occupancy metrics by reading the current session's JSONL transcript. Use when the user asks about context usage, token counts, or window occupancy.

Displays: current occupancy, message count, compaction count, and session phase. Warns when approaching or exceeding a configured soft boundary.

## Tests

96 tests across 8 test files:

| Test File | Coverage Area |
|-----------|--------------|
| `test_config.py` | Config parsing, YAML frontmatter extraction, model detection, occupancy auto-upgrade |
| `test_trigger_engine.py` | All 5 trigger types, OR semantics, format priority, heartbeat intervals, state transitions |
| `test_formatter.py` | Token formatting, soft boundary warnings, all 3 output format functions |
| `test_jsonl_reader.py` | Backward scan, malformed lines, empty files, message dedup, non-integer safety |
| `test_session_registry.py` | Register/deregister/renew/expire, thread safety, lease timeout |
| `test_server.py` | Live HTTP server, all endpoints, fail-open on bad input |
| `test_hooks.py` | Hook script subprocess behavior, compaction notification path |
| `test_integration.py` | End-to-end: start → register → hook → deregister → stop flows |

```bash
cd packages/plugins/context-metrics && uv run pytest
```

## Known Limitations

1. **No category breakdown** — Context occupancy is reported as a single total. Per-category breakdown (system prompt, conversation, tool results) requires the devtools `/groups` endpoint, deferred to v1.1.
2. **No phase history** — Phase tracking doesn't persist pre-compaction sizes. Showing "you were at 180k before compaction" requires tracking `compact_boundary` markers, deferred to v1.1.
3. **No cost data** — Token cost estimation requires devtools integration, not available in the base plugin.
4. **Large session performance** — Full JSONL scan for `/context-dashboard` may be slow for very large sessions (>100MB transcripts).
5. **Hook process crash is fail-open** — If the hook script crashes at the OS level (not a Python exception), it exits non-zero but Claude Code treats this as "no output" rather than blocking. This is by design for a monitoring tool but means crashes are silent.

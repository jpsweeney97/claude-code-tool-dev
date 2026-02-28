# Context Metrics Design

**Date:** 2026-02-28
**Branch:** `feature/context-metrics`
**Status:** Design amended with two Codex reviews (3 amendments), ready for implementation planning

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

1. ~~**Does devtools' `/groups` endpoint contain enough data to approximate current-phase context occupancy?**~~ **Resolved in Amendment 2.** No — `/groups` aggregates across subagent API calls. The JSONL transcript provides exact per-call context occupancy. See Amendment 2.
2. **Would devtools accept an upstream PR to expose `ContextStats` via HTTP?** Adding `GET /api/projects/:projectId/sessions/:sessionId/context-stats` would enable the category breakdown dashboard. Requires external maintainer review. Lower priority now that the summary line works without devtools. Deferred to v1.1+ (see Amendment 3 scope boundary).
3. ~~**Is the HTTP hook event support for `UserPromptSubmit` confirmed?**~~ **Deferred in Amendment 3.** v1 uses `type: "command"` hooks for `UserPromptSubmit`. HTTP hooks deferred to v1.1 after empirical verification. See Amendment 3 Finding 4.
4. ~~**Which dashboard skill approach to use?**~~ **Scoped in Amendment 3.** v1 uses simplified JSONL-only dashboard or defers entirely. Category breakdown deferred to v1.1+. See Amendment 3 v1 scope boundary.
5. **Does `additionalContext` accumulate or overwrite?** Each hook injection may create a separate `system-reminder` (accumulating) or overwrite the previous one. Affects heartbeat frequency tuning. See Amendment 3 Finding 5 and unresolved items.
6. **Startup race between async sidecar launch and first `UserPromptSubmit`.** The first prompt may fire before the sidecar is ready. Mitigation options documented in Amendment 3 unresolved items. Verify empirically during implementation.

## Amendments

### Amendment 1: Codex Deep Review Findings (2026-02-28)

**Source:** Codex evaluative review (5 turns, converged). Thread `019ca614-39c4-7263-9521-e13972c889c4`. Findings independently verified against official Claude Code docs via `claude-code-docs` MCP server.

**Review outcome:** 6 confirmed findings (2 high, 2 medium, 2 low), 2 rejected findings. Codex falsely claimed HTTP hooks don't exist (searched stale local docs copy). Core architecture validated; data source and lifecycle issues identified.

#### Finding 1 (High): Token data source — cumulative vs occupancy

**Issue:** The `/metrics` endpoint returns `SessionMetrics.totalTokens` — a cumulative sum of all API input + output tokens across the session. This is a billing metric that only increases. The design's summary line showing post-compaction drops ("34k/200k tokens (17%)") is impossible with this data source.

**Root cause:** `ContextStats.totalEstimatedTokens` (actual context window occupancy, computed by devtools' `ContextTracker` using `estimateTokens()`) lives exclusively in devtools' renderer process. No HTTP endpoint exposes it.

**Impact:** Without context occupancy data, the summary line shows "how many tokens have been used in total this session" — not "how much of the context window is currently occupied." Post-compaction, the number never decreases, defeating the core value proposition.

**Resolution options (to be decided during implementation planning):**

| Option | Trade-off |
|--------|-----------|
| A. Relabel as "session usage" | Honest but less useful. Doesn't answer "how full is my context?" |
| B. Approximate from `/groups` | Sum current-phase group tokens. Uses API counts, not `estimateTokens()`. Accuracy unknown. |
| C. Upstream PR to devtools | Best data. Requires external maintainer approval. Timeline uncertain. |
| D. Replicate `ContextTracker` in sidecar | Most accurate without upstream changes. Significant complexity — must parse JSONL, classify messages, track compaction boundaries. |

**Design impact:** Summary line format remains valid if the data source changes. The format itself is decoupled from how tokens are counted. Architecture diagram step 2 must change from `GET .../metrics` to whichever endpoint is chosen.

#### Finding 2 (High): Multi-session lifecycle collision

**Issue:** PID file at `~/.claude/.context-metrics-sidecar.pid` and port 7432 are global singletons. If a user opens two Claude Code sessions simultaneously:
1. Second session's `start_sidecar.py` kills the first session's live sidecar
2. Both sessions then share one sidecar (or both lose it)
3. `SessionEnd` from the first session kills the sidecar the second session is using

**Resolution options:**

| Option | Trade-off |
|--------|-----------|
| A. Per-session port + PID | Port = hash(session_id) % range + base. No collisions. More complex startup. |
| B. Shared sidecar with refcount | Single sidecar, multiple consumers. Start increments refcount, stop decrements. Exit when refcount = 0. More complex lifecycle. |
| C. Document single-session limitation | Simple. Acceptable for v1 if most users run one session at a time. |

**Design impact:** PID file path and port allocation strategy in the State table. Startup/shutdown scripts. Error handling for port-in-use.

#### Finding 3 (Medium): SessionStart matcher too narrow

**Issue:** The SessionStart hook matcher is `"startup"` — only fires on fresh sessions. Official docs confirm SessionStart has four source values: `startup`, `resume`, `clear`, `compact`. Resumed sessions (`--resume`) and cleared sessions (`/clear`) never start the sidecar unless one was already running.

**Resolution:** Change matcher from `"startup"` to `"startup|resume|clear"` (regex). `compact` is handled by the separate compact hook entry.

**Amended hook config:**

```json
{
  "matcher": "startup|resume|clear",
  "hooks": [
    {
      "type": "command",
      "command": "uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/start_sidecar.py",
      "async": true,
      "statusMessage": "Starting context metrics sidecar"
    }
  ]
}
```

`start_sidecar.py` already handles "PID file exists → kill stale → restart," so duplicate starts from `resume` (where a sidecar might already be running) are safe.

#### Finding 4 (Medium): Mixed runtime creates import skew risk

**Issue:** `start_sidecar.py` uses `uv run --directory ${CLAUDE_PLUGIN_ROOT}` (managed interpreter + deps from `pyproject.toml`) while `context_summary.py` and `stop_sidecar.py` use `python3` (system interpreter, stdlib only). If `context_summary.py` needs to import anything from `pyproject.toml` deps, it fails under system python3.

**Current design intent:** `context_summary.py` and `stop_sidecar.py` are stdlib-only scripts — they query the sidecar via `urllib.request` or read a PID file and send SIGTERM. No third-party imports needed.

**Resolution:** Add explicit constraint to the plugin structure section: "Scripts invoked synchronously (`context_summary.py`, `stop_sidecar.py`) MUST use stdlib only. No imports from `pyproject.toml` dependencies. Only `start_sidecar.py` (async, one-time) uses `uv run`."

#### Finding 5 (Low): costUsd is optional with no fallback

**Issue:** Devtools' `SessionMetrics.costUsd` is typed `costUsd?: number` (optional). The summary line format always shows `~$X.XX` with no handling for the undefined case.

**Resolution:** When `costUsd` is undefined, omit the cost segment from the summary line:

```
Context: 142k/200k tokens (71%) | 847 messages | Phase 3 (2 compactions)
```

No placeholder or "n/a" — just omit. Keeps the line shorter and avoids noise.

#### Finding 6 (Low): No observability for fail-open state

**Issue:** The design's fail-open philosophy means failures are silent. Users have no way to know if metrics are being injected, if the sidecar is running, or if devtools is connected.

**Resolution:** Add a `/context-status` skill (separate from `/context-dashboard`) that reports:

```
## Context Metrics Status

Sidecar: running (PID 12345, port 7432, uptime 23m)
Devtools: connected (port 3456, last response 2s ago)
Config: context_window=1000000, soft_boundary=200000
Last injection: 3s ago (142k tokens)
```

Implementation: skill queries sidecar's health endpoint (`GET /health`) which returns status JSON.

#### Rejected findings

| Codex Claim | Rejection Reason |
|-------------|-----------------|
| P0-1: `type: "http"` hooks don't exist in Claude Code | **Wrong.** Official docs (code.claude.com/docs/en/hooks) document HTTP hooks as a first-class type with full schema (`url`, `headers`, `allowedEnvVars`), response handling protocol, and examples. Codex searched a stale local copy at `docs/claude-code-documentation/hooks.md`. |
| P0-4: `async` and `statusMessage` are undocumented hook fields | **Wrong.** `statusMessage` is documented as a common field for all hook types ("Custom spinner message displayed while the hook runs"). `async` is documented as a command hook field ("If `true`, runs in the background without blocking"). |

#### Event type restriction nuance

The official docs' event restriction section says "all three types (command, prompt, agent)" for `UserPromptSubmit` — not "all four." HTTP hooks are absent from both the supported and restricted event lists. This is most likely a documentation gap (HTTP hooks were documented separately and the event restriction section wasn't updated to say "four"), but it introduces a small risk that HTTP hooks may not work with `UserPromptSubmit`. The previous session verified HTTP hook support for `UserPromptSubmit` via `claude-code-docs` MCP server search, which returned docs explicitly listing `http` as a valid type for `UserPromptSubmit`. If HTTP hooks prove incompatible at runtime, the fallback is a `type: "command"` hook that makes an HTTP request to the sidecar (same pattern as `context_summary.py`), adding ~200ms latency per prompt.

### Amendment 2: JSONL-Primary Data Source and Hybrid Architecture (2026-02-28)

**Source:** Live API investigation of claude-devtools v0.4.7 (installed at `/Applications/claude-devtools.app`) and JSONL transcript analysis. The cloned repo at `cloned-repos/claude-devtools/` is v0.1.0 — 46 versions behind the installed app.

**Summary:** The JSONL transcript is the correct primary data source for context window occupancy. Devtools becomes optional enrichment, not a hard dependency. The config file is simplified to one field (`soft_boundary`).

#### Resolves Amendment 1 Finding 1: Token data source

**Resolution: Read JSONL transcript directly (none of the four options from Amendment 1).**

The JSONL transcript at `transcript_path` (provided in every hook input) contains per-API-call `usage` data:

```json
{
  "message": {
    "model": "claude-opus-4-6",
    "usage": {
      "input_tokens": 1,
      "cache_read_input_tokens": 158061,
      "cache_creation_input_tokens": 1169,
      "output_tokens": 775
    }
  }
}
```

`input_tokens + cache_read_input_tokens + cache_creation_input_tokens` = **exact tokens sent to the model** = context window occupancy for that API call.

**Evidence from this session (8cf5037d):**

| Source | Value | What it measures |
|--------|-------|-----------------|
| JSONL last API call usage | **163k tokens** | Actual context window occupancy |
| Devtools `/metrics` `totalTokens` | **11.6M tokens** | Cumulative session billing total (73x too high) |
| Devtools `/groups` per-group metrics | **2.6M tokens** (for a group) | Aggregated across all API calls in exchange including subagents |

The JSONL is the only source that provides individual API call context occupancy. Devtools aggregates at every level (session, group, chunk, waterfall item).

**Additional JSONL fields useful for metrics:**

| Field | Location | Purpose |
|-------|----------|---------|
| `isSidechain` | Top-level on each message | Filter out subagent API calls — only main thread is relevant for context occupancy |
| `message.model` | Assistant messages | Model identification |
| `type` | Top-level | Detect `SessionStart(compact)` events for compaction counting |
| Message count | Count user + assistant messages | Replaces devtools `messageCount` |
| Timestamps | `timestamp` on each message | Session duration, last-activity tracking |

**Main thread context progression (this session):**

```
Call   1:  52k  →  Call  25:  93k  →  Call  57: 131k  →  Call  97: 146k  →  Call 125: 163k
```

Smooth, monotonically increasing. Post-compaction, the progression resets to a lower value (the compacted summary size) and grows again. This was not observable in this session (no compactions on a 1M window at 163k usage) but follows from how compaction works: the API sends the compacted context, so the next call's `input_tokens + cache_read + cache_create` reflects the post-compaction window.

#### Architecture change: JSONL-primary, devtools-optional

**Before (original design):** Sidecar queries devtools → formats summary. Devtools required.

**After:** Sidecar reads JSONL tail → computes occupancy. Optionally queries devtools for cost enrichment.

```
┌─────────────────────────────────────────────────────┐
│                  Claude Code Session                  │
│                                                       │
│  UserPromptSubmit ──HTTP POST──→ sidecar:7432         │
│  SessionStart(compact) ─command─→ context_summary.py  │
│                                                       │
│  ← "Context: 163k/1M (16%) | 125 msgs | Phase 1"     │
└───────────────────────────────────────────────────────┘
        │                                    ▲
        │ Hook JSON (includes transcript_path)
        ▼                                    │
┌───────────────────────────────────────────────────────┐
│              Plugin Sidecar (Python HTTP)               │
│                                                         │
│  Primary path (always, JSONL-only):                     │
│    1. Read JSONL tail → find last main-thread usage     │
│    2. Extract input + cache_read + cache_create         │
│    3. Read window config (soft_boundary)                │
│    4. Detect window size (auto or config override)      │
│    5. Count compactions (SessionStart compact events)   │
│    6. Estimate cost from token counts × model pricing   │
│    7. Format summary line                               │
│                                                         │
│  Enrichment path (if devtools HTTP server enabled):     │
│    8. GET devtools:3456/.../metrics → costUsd            │
│    9. Prefer devtools cost over estimated cost           │
│                                                         │
│  Return: { additionalContext: "..." }                   │
└───────────────────────────────────────────────────────┘
         ╎ (optional)
         ╎ HTTP GET (only if devtools server is enabled)
         ▼
┌───────────────────────────────────────────────────────┐
│           claude-devtools (port 3456, optional)         │
│                                                         │
│  Only used for: costUsd from /metrics                   │
│  Category breakdown: NOT available via HTTP API         │
└───────────────────────────────────────────────────────┘
```

**What changes from the original architecture:**

| Component | Before | After |
|-----------|--------|-------|
| Primary data source | Devtools `/metrics` | JSONL `transcript_path` |
| Devtools dependency | Required | Optional (enrichment only) |
| Devtools HTTP server | Assumed running | Must be explicitly enabled in devtools settings |
| Context occupancy | `SessionMetrics.totalTokens` (wrong — cumulative) | Per-call `usage` (correct — window occupancy) |
| Cost | From devtools `costUsd` | Estimated from token counts; devtools `costUsd` preferred if available |
| Category breakdown (dashboard) | From devtools `/groups` | Still not available via HTTP API (renderer-only). Dashboard skill deferred or simplified. |

#### Context window auto-detection

**Replaces:** Manual `context_window` config field.

**Mechanism:** Default to 200k. If any main-thread API call's input-side tokens (`input + cache_read + cache_create`) exceed 200k → auto-upgrade to 1M. Persist detected window in sidecar memory for the session.

**Behavior by scenario:**

| Scenario | What happens | Accuracy |
|----------|-------------|----------|
| 200k session | Always shows X/200k | Correct |
| 1M session, under 200k usage | Shows X/200k until usage crosses 200k | Temporarily wrong — shows higher % than reality |
| 1M session, over 200k usage | Auto-detects 1M, shows X/1M | Correct from detection point onward |
| User sets `context_window: 1000000` | Shows X/1M from session start | Always correct |

**Trade-off accepted:** On a 1M window, early turns show "80% of 200k" when the real situation is "16% of 1M." This self-corrects once context exceeds 200k. Users who want accurate 1M percentages from the start can set `context_window` in the config.

#### Simplified config file

**Before:**

```yaml
---
context_window: 1000000
soft_boundary: 200000
---
```

**After:**

```yaml
---
# Required only for soft boundary warnings.
# context_window auto-detected (200k default, upgrades to 1M on usage).
soft_boundary: 200000
---
```

| Field | Required | Default | Purpose |
|-------|----------|---------|---------|
| `soft_boundary` | No (but needed for cost warnings) | None (no warnings) | Cost threshold in tokens. Warnings emitted as usage approaches this boundary. |
| `context_window` | No | Auto-detected (200k, upgrades to 1M) | Override auto-detection. Set to `1000000` for immediate 1M percentages. |

**Config file path unchanged:** `~/.claude/context-metrics.local.md`

#### Devtools HTTP server prerequisite

**Discovery:** Devtools' HTTP API is **disabled by default**. The Electron app runs the UI without starting the HTTP server. Users must explicitly enable it:

1. Open claude-devtools app
2. Settings → Toggle "Enable Server Mode" on
3. Server starts on `http://localhost:3456`
4. Setting persists in `~/.claude/claude-devtools-config.json` (`httpServer.enabled: true`)

**Impact on design:** Since devtools is now optional enrichment (not required), this is a nice-to-have setup step, not a blocker. The summary line works fully without devtools. Document in README: "For cost data from devtools, enable Server Mode in devtools settings."

#### Devtools version gap

The cloned repo at `cloned-repos/claude-devtools/` is **v0.1.0**. The installed app is **v0.4.7** (46 versions ahead). Analysis based on the cloned repo may be inaccurate. Key findings verified against the live v0.4.7 API:

| Finding | Cloned repo (0.1.0) | Live app (0.4.7) | Match? |
|---------|---------------------|-------------------|--------|
| `/metrics` returns cumulative `totalTokens` | Yes | Yes | ✓ |
| `/groups` aggregates across subagent calls | Yes | Yes | ✓ |
| No `/context-stats` endpoint | Yes (confirmed absent) | Yes (confirmed absent via 404) | ✓ |
| `/waterfall` endpoint exists | Assumed | Yes (returns per-item data) | ✓ |
| HTTP server disabled by default | Yes (`enabled: false`) | Yes (confirmed via config export) | ✓ |
| `ContextStats` is renderer-only | Yes (from source analysis) | Not verifiable via API (consistent) | ✓ |

The version gap did not introduce new context-related endpoints. The core data model (cumulative metrics via HTTP, context tracking in renderer only) is unchanged between 0.1.0 and 0.4.7.

#### Dashboard skill impact

The `/context-dashboard` skill's category breakdown (tool outputs 66%, thinking 18%, CLAUDE.md 8%, etc.) relies on `ContextStats.tokensByCategory` which is **not available via any HTTP API endpoint** in either v0.1.0 or v0.4.7. It lives exclusively in devtools' renderer process.

**Options for implementation planning:**

| Option | What it provides |
|--------|-----------------|
| A. Simplified dashboard (JSONL-only) | Window occupancy, message count, compaction history, cost estimate. No per-category breakdown. |
| B. Dashboard deferred | Ship summary line first. Dashboard skill added later if devtools exposes `ContextStats` via HTTP (upstream PR or future version). |
| C. Replicate category classification | Parse JSONL messages, classify by type (tool output, CLAUDE.md, user message, etc.), estimate tokens per category. Complex but self-contained. |

### Amendment 3: Second Codex Deep Review Findings (2026-02-28)

**Source:** Codex evaluative review (7 turns, converged via mutual agreement). Thread `019ca664-5345-77a0-8418-9fd924cbab74`. Second review of the fully amended design (after Amendments 1 and 2).

**Review outcome:** 8 resolved findings (5 high, 1 medium, 2 high from self-correction), 2 unresolved items, 2 dialogue-born insights. Design assessed as fundamentally sound. All major findings are correctness or behavioral issues — the architecture is validated.

#### Finding 1 (High): JSONL occupancy selector must be stricter than `isSidechain` alone

**Issue:** The design (Amendment 2, line 488-489) uses `isSidechain: false` as the sole filter for main-thread API calls. This is insufficient — `agent_progress` records can carry `isSidechain: false` with nested usage data that is NOT main-thread context occupancy. Using these records would produce incorrect metrics.

**Resolution:** The correct selector requires all of:
1. `type == "assistant"` (top-level message type)
2. `message.role == "assistant"` (API response)
3. `message.usage` present (has token data)
4. Exclude synthetic/api-error records
5. Deduplicate by `message.id`

**Design impact:** The sidecar's JSONL parsing logic (Architecture diagram step 1: "Read JSONL tail → find last main-thread usage") must apply this multi-field selector, not just `isSidechain: false`. The tail-reading algorithm should scan backward for the first record matching all five criteria.

**Confidence:** High — both sides independently identified the issue. Codex provided evidence of `agent_progress` records with misleading usage data.

#### Finding 2 (High): Dual-source compaction detection

**Issue:** The design relies solely on the `SessionStart(compact)` hook for compaction detection. The JSONL transcript also contains `compact_boundary` markers with `compactMetadata.preTokens` (pre-compaction context size). Neither source alone is sufficient.

**Resolution:** Use both sources:

| Source | Role | Strength |
|--------|------|----------|
| `SessionStart(compact)` hook | Immediate trigger for post-compaction re-injection | Real-time, but only fires during the session |
| JSONL `compact_boundary` markers | Durable compaction count, phase history, pre-compaction sizes | Persistent, includes `preTokens` for historical analysis |

The sidecar reads `compact_boundary` markers from the JSONL to maintain compaction count and phase history. The `SessionStart(compact)` hook triggers immediate re-injection with fresh metrics.

**Design impact:** The architecture diagram step 5 ("Count compactions — SessionStart compact events") should read "Count compactions — JSONL compact_boundary markers." The `SessionStart(compact)` hook remains for immediate injection but is no longer the sole compaction detection mechanism.

**Confidence:** High — `compact_boundary` markers confirmed in real JSONL transcripts with `compactMetadata.preTokens`.

#### Finding 3 (High): Shared sidecar with session registry + lease resolves multi-session collision

**Issue:** Amendment 1 Finding 2 identified the multi-session collision problem but left three options unresolved.

**Resolution: Option B refined — shared sidecar with session registry and lease timeout.**

Option A (per-session port) eliminated: `hooks.json` URLs are static — they're baked at plugin install time and cannot be parameterized per session. A URL like `http://localhost:7432/hooks/context-metrics` is the same for every session. This is an architectural constraint, not just an inconvenience.

**Sidecar lifecycle:**

| Event | Behavior |
|-------|----------|
| First session starts | Sidecar launches on port 7432, registers session with 10-minute lease |
| Second session starts | Detects running sidecar (health check), registers new session, renews lease |
| Session ends normally | Deregisters session. If no sessions remain, sidecar shuts down |
| Session crashes | Lease expires after 10 minutes. If no sessions remain after expiry, sidecar shuts down |
| Resume (no running sidecar) | Starts new sidecar, registers session |
| Resume (sidecar running) | Registers session (no kill/restart). Cache preserved for other sessions |

**Key change from design:** `start_sidecar.py` must NOT kill-and-restart when a sidecar is already running. It should register the new session and exit. Kill-on-resume was identified as a correctness bug: it drops the TTL cache and interrupts in-flight requests for other sessions.

**Sidecar state additions:**

| State | Storage | Lifecycle |
|-------|---------|-----------|
| Session registry | In-memory dict: `{session_id: last_heartbeat_timestamp}` | Entries added on startup hook, removed on shutdown hook, expired by lease timeout |
| Lease timeout | 10 minutes | Configurable. Sessions renew on each request. |

**Design impact:** PID file remains for startup detection. Port remains 7432 (shared). `stop_sidecar.py` deregisters the session instead of killing the process. Add `GET /sessions/register` and `GET /sessions/deregister` endpoints to the sidecar.

**Confidence:** High — the static `hooks.json` URL constraint is architecturally decisive.

#### Finding 4 (High): v1 ships command hooks for UserPromptSubmit, HTTP hooks deferred

**Issue:** The design uses `type: "http"` for `UserPromptSubmit`. HTTP hooks are not mentioned in the bundled hooks documentation (`docs/claude-code-documentation/hooks.md` — zero mentions of "http"). The official live docs do document HTTP hooks, but the gap creates runtime risk for v1.

**Resolution:** v1 uses `type: "command"` for `UserPromptSubmit`:

```json
{
  "hooks": [
    {
      "type": "command",
      "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_summary.py",
      "timeout": 5,
      "statusMessage": "Updating context metrics"
    }
  ]
}
```

`context_summary.py` queries the sidecar via `urllib.request` (stdlib, same pattern as the `SessionStart(compact)` hook). The ~150-300ms command hook latency is acceptable for v1.

**Upgrade path (v1.1):** After empirical verification that HTTP hooks work with `UserPromptSubmit`, switch to `type: "http"` for ~1-5ms latency. The sidecar's `/hooks/context-metrics` endpoint already exists — only the `hooks.json` entry changes.

**Design impact:** Remove `type: "http"` from the UserPromptSubmit hook config. `context_summary.py` becomes the sole injection script for both `UserPromptSubmit` and `SessionStart(compact)`. This simplifies the design: one script, one injection path. The sidecar HTTP endpoint remains for the v1.1 upgrade.

**Confidence:** High — the ~150-300ms latency is within acceptable bounds, and de-risking v1 is worth the trade-off.

#### Finding 5 (High): Delta-gated injection replaces per-turn injection

**Issue:** The design injects `additionalContext` on every `UserPromptSubmit`. Each injection creates a system-reminder in Claude's conversation context. After 100 prompts, this accumulates ~2000 tokens of context pollution (100 × ~20 tokens per summary line). This is ironic for a context-awareness tool.

**Resolution: Inject only on meaningful change, plus a heartbeat.**

**Injection triggers (full format):**

| Trigger | Condition | Example |
|---------|-----------|---------|
| Token delta | Context grew by ≥5k tokens or ≥2% since last injection | 142k → 148k |
| Boundary crossing | Context crossed 25%, 50%, 75%, 90% of window | "Approaching 75% of context window" |
| Soft boundary alert | Context approaching or exceeding `soft_boundary` | "168k/200k — approaching extended-context boundary" |
| Compaction | `compact_boundary` detected in JSONL | "Compaction #3 just occurred — 34k/200k" |

**Heartbeat (minimal format):**

Every 8-10 prompts without a triggered injection, emit a minimal status:

```
Context: ~71% (stable)
```

This keeps Claude loosely aware without noise. Full format only on material changes.

**Sidecar state addition:**

| State | Storage | Purpose |
|-------|---------|---------|
| Last injected metrics | In-memory per session | Compare with current to determine if delta threshold is met |
| Prompts since last injection | In-memory counter per session | Heartbeat trigger |

**Design impact:** The sidecar's response can be `{ hookSpecificOutput: null }` (no injection) or `{ hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: "..." } }` (inject). The "no injection" case is the common path. The hook still fires on every prompt — the sidecar decides whether to inject.

**Confidence:** High — dialogue-born insight. The accumulation problem is a direct consequence of per-turn injection with persistent context.

**Open question (unresolved):** Does each `additionalContext` injection create a separate system-reminder, or do subsequent injections overwrite the previous one? If they overwrite, the pollution concern is reduced but delta-gating is still valuable for reducing sidecar work. Implementation should verify this empirically.

#### Finding 6 (Medium): v1 omits self-computed cost estimation

**Issue:** The design's summary line includes `~$X.XX` cost. With devtools now optional, self-computing cost requires model-specific pricing tables, cache pricing rules, and ongoing maintenance as Anthropic updates prices.

**Resolution:** v1 shows cost only when devtools `costUsd` is available (devtools enrichment path). When devtools is unavailable, the cost segment is omitted (same behavior as Amendment 1 Finding 5's resolution for undefined `costUsd`).

**Summary line without cost:**

```
Context: 142k/200k tokens (71%) | 847 msgs | Phase 3 (2 compactions)
```

**Upgrade path:** Self-computed cost estimation can be added to the dashboard skill if the category breakdown is implemented (Option C from Amendment 2). The dashboard is invoked on-demand, so slightly stale pricing tables are acceptable there.

**Confidence:** Medium — Codex proposed, reasoning about maintenance burden is sound. Users who want cost data can enable devtools.

#### Finding 7 (High): Non-compaction dips are small — do not use token-drop heuristics

**Issue:** During the dialogue, the question arose whether large context dips can occur without compaction (which would break token-drop-based compaction detection).

**Resolution:** Large dips (e.g., 137k → 59k) are compaction-adjacent — preceded by `compact_boundary` markers in the JSONL. Small dips (~80 tokens) occur from cache accounting shifts and are not compaction events.

**Design impact:** Compaction detection must use explicit `compact_boundary` markers (Finding 2), not token-drop heuristics. A threshold-based approach ("if context drops by >X%, assume compaction") would produce false positives from cache shifts and false negatives from small compactions.

**Confidence:** High — Codex initially implied large dips occur without compaction, then self-corrected after re-examining evidence.

#### v1 Scope Boundary

Based on this review, the following scope boundary is established:

**v1 (initial release):**

| Component | Approach |
|-----------|----------|
| Data source | JSONL-primary, devtools-optional enrichment |
| Injection hook | `type: "command"` for UserPromptSubmit |
| Injection policy | Delta-gated with heartbeat |
| Multi-session | Shared sidecar with session registry + lease |
| Cost | Devtools `costUsd` when available; omitted otherwise |
| Dashboard | Simplified JSONL-only (occupancy, messages, compactions) or deferred |
| Context window | Auto-detection (200k default, upgrade to 1M) with config override |

**v1.1+ (deferred):**

| Component | Approach |
|-----------|----------|
| Injection hook | `type: "http"` for UserPromptSubmit (after empirical verification) |
| Cost estimation | Self-computed from token counts × model pricing |
| Dashboard | Category breakdown (if devtools adds ContextStats endpoint, or via JSONL classification) |
| Upstream devtools PR | `GET /api/.../context-stats` endpoint for category data |

#### Unresolved items (carry forward to implementation)

1. **`additionalContext` accumulation semantics.** Does each injection create a separate `system-reminder` in Claude's context, or do subsequent injections from the same hook overwrite the previous one? Delta-gating mitigates either case, but the answer affects heartbeat frequency tuning. Verify empirically during implementation.

2. **Startup race condition.** The sidecar starts via `async` command hook on `SessionStart`. The first `UserPromptSubmit` may fire before the sidecar is ready. Mitigation options: (a) `context_summary.py` retries once with 500ms delay if sidecar is unreachable, (b) sidecar writes a ready-file that `context_summary.py` checks, (c) accept that the first prompt may not have metrics (fail-open). Verify timing empirically during implementation.

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
| Codex review 1 thread | `019ca614-39c4-7263-9521-e13972c889c4` |
| Codex review 2 thread | `019ca664-5345-77a0-8418-9fd924cbab74` |

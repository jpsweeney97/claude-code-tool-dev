# External Integrations

**Analysis Date:** 2026-03-13

## APIs & External Services

**AI Models:**
- OpenAI Codex — cross-model consultation via the `codex` CLI subprocess
  - SDK/Client: `codex` CLI (subprocess, not SDK); dispatched by `packages/plugins/cross-model/scripts/codex_delegate.py`
  - Invocation: `codex exec --json -o <output_file> -s <sandbox>` (sandboxes: `read-only`, `workspace-write`)
  - MCP tools: `mcp__plugin_cross-model_codex__codex`, `mcp__plugin_cross-model_codex__codex-reply`
  - Auth: inherits from environment (Codex CLI manages its own credentials)
  - Min version: `0.111.0`
  - Guard hooks: `packages/plugins/cross-model/hooks/hooks.json` — `PreToolUse`/`PostToolUse` on Codex MCP tools via `codex_guard.py`

- Anthropic Claude — primary AI runtime (Claude Code); no direct API calls from this codebase (Claude Code manages the session)

**Documentation Source:**
- `https://code.claude.com/docs/llms-full.txt` — fetched by claude-code-docs MCP server on startup
  - Client: `packages/mcp-servers/claude-code-docs/src/fetcher.ts` (HTTP with redirect handling)
  - Auth: None (public URL)
  - Env override: `DOCS_URL` env var

**npm Registry:**
- `registry.npmjs.org` — queried via `npm view get-shit-done-cc version` at `SessionStart`
  - Client: `execSync` in `.claude/hooks/gsd-check-update.js`
  - Auth: None (public registry)
  - Purpose: update availability check; result cached to `~/.claude/cache/gsd-update-check.json`

## Data Storage

**Databases:**
- None — no database dependencies detected

**File Storage:**
- Local filesystem only
  - Handoff documents: `~/.claude/handoffs/<project>/` (gitignored)
  - Session notes: `~/.claude/sessions/` (gitignored)
  - Tickets: `docs/tickets/` in each repo
  - claude-code-docs content cache: `~/Library/Caches/claude-code-docs/llms-full.txt` (macOS) or `$XDG_CACHE_HOME/claude-code-docs/` (Linux)
  - claude-code-docs index cache: `~/Library/Caches/claude-code-docs/llms-full.index.json` (macOS)
  - Context metrics bridge: `/tmp/claude-ctx-<session_id>.json` (ephemeral, written by statusline hook, read by context-monitor hook)
  - Cross-model event log: written by `packages/plugins/cross-model/scripts/event_log.py` (path resolved at runtime)

**Caching:**
- File-based TTL cache for claude-code-docs HTTP responses (default TTL: 86400000ms / 24h, override: `CACHE_TTL_MS`)
- File-based version-pinned index cache for BM25 index (invalidated by bumping version constants in `packages/mcp-servers/claude-code-docs/src/index-cache.ts`)
- PID-based lock file for cache writes: `llms-full.txt.lock` (stale-lock detection included)
- GSD update check cache: `~/.claude/cache/gsd-update-check.json`
- Override cache path: `CACHE_PATH` env var

## Authentication & Identity

**Auth Provider:**
- None — no external auth provider integrated
- HMAC-based internal security: context-injection uses per-process HMAC key (`context_injection/state.py`) to sign and validate scout tokens between `process_turn` (Call 1) and `execute_scout` (Call 2). Prevents replayed or forged scout requests.
- Credential scanning: `packages/plugins/cross-model/scripts/credential_scan.py` and `codex_guard.py` scan prompts sent to Codex for secrets before dispatch

## Monitoring & Observability

**Error Tracking:**
- None — no external error tracking service

**Logs:**
- Cross-model delegation: append-only JSONL event log via `packages/plugins/cross-model/scripts/event_log.py`; session ID from `CLAUDE_SESSION_ID` env var
- Gitflow hook: optional file log at `~/.claude/logs/gitflow-hook.log` (or `GITFLOW_LOG_FILE`); enabled via `GITFLOW_DEBUG=1`
- All other components: stderr only, no structured logging

**Context Metrics:**
- context-metrics plugin (`packages/plugins/context-metrics/`) — analyzes context window usage from Claude Code's JSONL session files
- Statusline hook (`.claude/hooks/gsd-statusline.js`) — writes per-session metrics to `/tmp/claude-ctx-<session_id>.json`
- Context monitor hook (`.claude/hooks/gsd-context-monitor.js`) — reads bridge file and injects `additionalContext` warnings at 35% and 25% remaining thresholds

## CI/CD & Deployment

**Hosting:**
- Local development machine only — no cloud hosting
- Extensions deploy to `~/.claude/` (user config directory) via `uv run scripts/promote`
- Plugins deploy via `turbo-mode` marketplace bundle

**CI Pipeline:**
- None detected — no `.github/`, `.circleci/`, or similar CI config found

## Environment Configuration

**Required env vars (cross-model plugin):**
- `CLAUDE_SESSION_ID` — session identifier for event log; provided by Claude Code
- `CROSS_MODEL_NUDGE` — set to `1` to enable Codex nudge on Bash failure (`packages/plugins/cross-model/scripts/nudge_codex.py`)
- `REPO_ROOT` — root directory for context-injection; defaults to `os.getcwd()`

**Required env vars (claude-code-docs MCP server):**
- `DOCS_URL` — documentation source URL (default: `https://code.claude.com/docs/llms-full.txt`)
- `RETRY_INTERVAL_MS` — retry interval after fetch failure (default: `60000`)
- `CACHE_TTL_MS` — content cache TTL (default: `86400000`)
- `DOCS_CACHE_MAX_STALE_MS` — hard cap on stale content age (default: `0` / disabled)
- `MIN_SECTION_COUNT` — minimum sections to accept (default: `40`; set to `0` to disable)
- `MAX_INDEX_CACHE_BYTES` — max serialized index size (default: `52428800` / 50MB)
- `CACHE_PATH` — override default cache directory
- `INTEGRATION` — set to `1` to run integration tests against live `code.claude.com`

**Required env vars (GSD hooks):**
- `CLAUDE_CONFIG_DIR` — override config directory (supports multi-account setups); checked in `gsd-check-update.js` and `gsd-statusline.js`
- `GITFLOW_ALLOW_FILES` — comma-separated glob patterns for files allowed on protected branches (set in `.claude/settings.json`)
- `GITFLOW_STRICT` — set to `1` to block non-standard branch names
- `GITFLOW_BYPASS` — set to `1` to bypass all branch protection (emergency only)
- `GITFLOW_DEBUG` — set to `1` for debug output and file logging
- `GITFLOW_LOG_FILE` — custom log path (default: `~/.claude/logs/gitflow-hook.log`)
- `PROTECTED_BRANCHES` — comma-separated list (default: `main,master`)

**Secrets location:**
- No secrets stored in repo
- Codex credentials managed by the `codex` CLI outside this repo

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- HTTP GET to `https://code.claude.com/docs/llms-full.txt` — fetched by claude-code-docs MCP server at startup and on `reload_docs` tool call
- `npm view get-shit-done-cc version` — outbound npm registry query at `SessionStart`

---

*Integration audit: 2026-03-13*

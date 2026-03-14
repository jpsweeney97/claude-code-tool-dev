# Architecture

**Analysis Date:** 2026-03-13

## Pattern Overview

**Overall:** Plugin Monorepo with a Sandbox-to-Production Promotion Model

**Key Characteristics:**
- Extensions are developed in `.claude/` (sandbox) and promoted to `~/.claude/` (production) via `scripts/promote`
- Two language ecosystems coexist: Python (plugins, hooks, scripts) and TypeScript (MCP servers)
- The Claude Code extension surface is divided into six artifact types: skills, commands, agents, hooks, plugins, MCP servers
- Plugins ship as self-contained packages bundled under a marketplace config (`.claude-plugin/marketplace.json`)
- The GSD (Get Shit Done) workflow system is a first-class subsystem: 30+ slash commands, 14 agents, a compiled Node.js CLI (`gsd-tools.cjs`), and reference docs — all living under `.claude/get-shit-done/`

## Layers

**Extension Sandbox (`.claude/`):**
- Purpose: Develop and test Claude Code extensions before promotion
- Location: `.claude/skills/`, `.claude/commands/`, `.claude/agents/`, `.claude/hooks/`
- Contains: SKILL.md files, command .md files, agent .md files, Python hook scripts
- Depends on: nothing at runtime (loaded by Claude Code)
- Used by: `scripts/promote` for deployment, Claude Code runtime for activation

**Plugin Packages (`packages/plugins/`):**
- Purpose: Larger, structured extensions deployed via the turbo-mode marketplace
- Location: `packages/plugins/{cross-model,handoff,ticket,context-metrics}/`
- Contains: Python scripts (`scripts/`), hooks (`hooks/hooks.json`), skills, agents, references, tests
- Depends on: uv workspace (shared Python environment), FastMCP or stdlib HTTP
- Used by: Claude Code plugin runtime; hooks wired via `hooks.json` inside each plugin

**MCP Servers (`packages/mcp-servers/`):**
- Purpose: Expose structured tools via the Model Context Protocol
- Location: `packages/mcp-servers/claude-code-docs/`
- Contains: TypeScript source in `src/`, compiled output in `dist/`
- Depends on: `@modelcontextprotocol/sdk`, `zod`, `stemmer`, `yaml`
- Used by: Claude Code MCP client (stdio transport)

**GSD Workflow System (`.claude/get-shit-done/`):**
- Purpose: Orchestrate project planning and execution workflows
- Location: `.claude/get-shit-done/workflows/`, `.claude/get-shit-done/bin/`, `.claude/get-shit-done/references/`, `.claude/get-shit-done/templates/`
- Contains: 30+ workflow .md files, a compiled `gsd-tools.cjs` CLI and `lib/` modules, reference docs, planning templates
- Depends on: Node.js (invoked inline from workflow steps via `node .claude/get-shit-done/bin/gsd-tools.cjs`)
- Used by: GSD slash commands (`.claude/commands/gsd/`), GSD subagents (`.claude/agents/gsd-*.md`)

**Utility Scripts (`scripts/`):**
- Purpose: Repo maintenance — promote, sync-settings, inventory, migrate, validate
- Location: `scripts/` (executable Python scripts, uv inline scripts)
- Contains: `promote`, `sync-settings`, `inventory`, `migrate`, `validate_consultation_contract.py`, `validate_episode.py`
- Depends on: `pyyaml`, `rich` (via uv inline script deps)
- Used by: Developer workflow; `uv run scripts/<name>`

**Top-Level Tests (`tests/`):**
- Purpose: Cross-package integration tests for shared scripts and hooks
- Location: `tests/`
- Contains: Tests for analytics emission, stats, episode validation, codex guard, e-planning spec sync
- Depends on: `pytest` via uv workspace

## Data Flow

**Extension Promotion Flow:**

1. Developer writes extension in `.claude/` (skill, command, agent, or hook)
2. Runs `uv run scripts/promote <type> <name>` — validates, diffs, copies to `~/.claude/`
3. For hooks: `scripts/sync-settings` is auto-run to update `settings.json`
4. Claude Code loads from `~/.claude/` on next session

**Plugin Deploy Flow:**

1. Plugin lives in `packages/plugins/<name>/` with its own `pyproject.toml` and `hooks.json`
2. `.claude-plugin/marketplace.json` references all plugins by relative path
3. Deployed via turbo-mode plugin marketplace (not `scripts/promote`)
4. Plugin hooks receive `${CLAUDE_PLUGIN_ROOT}` env var pointing to the plugin's install dir

**MCP Server Flow (claude-code-docs):**

1. `src/index.ts` initializes `ServerState` with injected I/O functions (loader, chunker, cache)
2. On first tool call, `lifecycle.ts::ServerState.ensureIndex()` triggers: fetch → parse → chunk → build BM25 index
3. Index is serialized and cached on disk; subsequent calls deserialize from cache (version-gated)
4. `search_docs` tool scores queries via BM25 + heading boost + category filter, returns ranked chunks
5. `reload_docs` tool clears cache and re-fetches

**Context Injection Flow (cross-model plugin):**

1. Codex dialogue agent calls `process_turn` (Call 1): `pipeline.py` runs 17-step pipeline → returns scout options with HMAC-signed tokens
2. Agent calls `execute_scout` (Call 2): `execute.py` validates HMAC token, runs read/grep scout, redacts sensitive content, truncates
3. Evidence returned to agent for verifying Codex factual claims

**GSD Workflow Execution Flow:**

1. User invokes `/gsd:<command>` slash command
2. Command .md loads workflow via `@./.claude/get-shit-done/workflows/<workflow>.md`
3. Workflow calls `node .claude/get-shit-done/bin/gsd-tools.cjs init <command> [args]` to load project state
4. Orchestrator spawns GSD subagents (e.g., `gsd-planner`, `gsd-executor`) via Task tool
5. Subagents read `.planning/` state files, write plans/results
6. Orchestrator collects results, updates state

**Hook Enforcement Flow:**

1. Claude Code fires PreToolUse/PostToolUse events before/after tool calls
2. `settings.json` routes events to hook scripts by matcher pattern
3. Hook script reads JSON payload from stdin, evaluates policy
4. Exit code 2 = block; exit code 0 = allow; unhandled exceptions = allow (fail-open)

**State Management:**
- Project state: `.planning/state.md`, `.planning/roadmap.md`, `.planning/milestone.md`
- Plugin state: Per-plugin hooks own their state (e.g., context-metrics sidecar: `~/.claude/.context-metrics-sidecar.pid`)
- MCP server state: In-memory `ServerState` + filesystem caches under `~/Library/Caches/claude-code-docs/`
- Context injection state: In-memory per-process `AppContext` (conversation store + HMAC key)

## Key Abstractions

**Skill:**
- Purpose: Instruction document that extends Claude's capabilities for a domain
- Examples: `.claude/skills/learn/SKILL.md`, `.claude/skills/handbook/SKILL.md`
- Pattern: Directory named after the skill containing `SKILL.md` with YAML frontmatter (`name`, `description`)

**Agent (Subagent):**
- Purpose: Specialized Claude instance spawned by orchestrators for self-contained tasks
- Examples: `.claude/agents/gsd-planner.md`, `.claude/agents/gsd-executor.md`, `.claude/agents/gsd-codebase-mapper.md`
- Pattern: Single `.md` file with YAML frontmatter (`name`, `description`, `tools`, `color`); invoked via Task tool

**Hook:**
- Purpose: Python script that intercepts tool calls for enforcement or enrichment
- Examples: `.claude/hooks/require-gitflow.py`, `.claude/hooks/block-credential-content.py`
- Pattern: Executable Python with shebang + metadata comment; reads JSON from stdin; exit 0=allow, 2=block

**Plugin:**
- Purpose: Self-contained package bundling scripts, hooks, skills, agents, and references
- Examples: `packages/plugins/cross-model/`, `packages/plugins/handoff/`
- Pattern: Directory with `pyproject.toml`, `hooks/hooks.json`, `scripts/`, `skills/`, `tests/`; deployed via marketplace

**ServerState (MCP server):**
- Purpose: Dependency-injected lifecycle manager for the BM25 index
- Examples: `packages/mcp-servers/claude-code-docs/src/lifecycle.ts`
- Pattern: Constructor injection of all I/O functions; enables full test isolation without mocks

## Entry Points

**Plugin Script Invocation:**
- Location: `packages/plugins/<name>/scripts/<script>.py`
- Triggers: Hook `hooks.json` routes Claude Code events; skill SKILL.md instructs Claude to call directly
- Responsibilities: Parse stdin JSON payload, perform domain logic, emit structured response

**MCP Server (`claude-code-docs`):**
- Location: `packages/mcp-servers/claude-code-docs/src/index.ts` → compiled to `dist/index.js`
- Triggers: `npm start` / Claude Code MCP configuration
- Responsibilities: Register `search_docs` and `reload_docs` tools; manage ServerState lifecycle

**Context Injection Server:**
- Location: `packages/plugins/cross-model/context-injection/context_injection/server.py` (FastMCP)
- Triggers: `python -m context_injection`
- Responsibilities: POSIX+git startup gates; expose `process_turn` and `execute_scout` tools

**Context Metrics Sidecar:**
- Location: `packages/plugins/context-metrics/scripts/server.py`
- Triggers: Started by hook on session begin; shared HTTP server on port 7432
- Responsibilities: Session registry; context occupancy computation; trigger threshold evaluation

**GSD Tools CLI:**
- Location: `.claude/get-shit-done/bin/gsd-tools.cjs` (compiled Node.js)
- Triggers: `node .claude/get-shit-done/bin/gsd-tools.cjs <command> [args]` from workflow steps
- Responsibilities: Load/write project state, compute phase info, resolve model profiles

**Promote Script:**
- Location: `scripts/promote` (uv inline script)
- Triggers: `uv run scripts/promote <type> <name>`
- Responsibilities: Validate extension, diff against production, copy to `~/.claude/`

## Error Handling

**Strategy:** Fail-fast with context; fail-closed on security boundaries

**Patterns:**
- Hooks: Exit code 2 with stderr message to block; exceptions produce exit 0 (fail-open) — catch all errors in critical enforcement hooks
- Context injection: Fail-closed throughout (empty git file list = all files denied; over-redact over under-redact)
- MCP server: `ServerState.ensureIndex()` returns `None` on failure; tools return `isError: true` with message
- Python scripts: Format `"{operation} failed: {reason}. Got: {input!r:.100}"` per project style
- Plugin hooks: `PostToolUseFailure` delivers `additionalContext` as system-reminder after failures

## Cross-Cutting Concerns

**Logging:** Python scripts use stdlib `logging`; hooks write to stderr and/or `~/.claude/logs/`; GSD workflows output structured status via `ui-brand.md` conventions

**Validation:** Hook scripts validate JSON payloads from stdin; MCP server uses Zod schemas (`schemas.ts`); context injection uses Pydantic models; ticket plugin uses `ticket_validate.py`

**Authentication:** HMAC tokens in context injection (`state.py` key + `templates.py` generation + `execute.py` validation); credential blocking hooks (`block-credential-content.py`, `block-credential-json-files.py`, `block-keychain-extraction.py`)

---

*Architecture analysis: 2026-03-13*

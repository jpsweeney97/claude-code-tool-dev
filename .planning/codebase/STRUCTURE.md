# Codebase Structure

**Analysis Date:** 2026-03-13

## Directory Layout

```
claude-code-tool-dev/              # Monorepo root
├── .claude/                       # Extension sandbox (develop here, promote to ~/.claude/)
│   ├── agents/                    # Subagent .md files (gsd-*.md, assessment-runner.md, etc.)
│   ├── commands/                  # Slash command .md files
│   │   └── gsd/                   # 30+ GSD workflow commands
│   ├── get-shit-done/             # GSD workflow system
│   │   ├── bin/                   # Compiled gsd-tools.cjs + lib/ modules
│   │   ├── references/            # Reference docs (checkpoints, continuation-format, etc.)
│   │   ├── templates/             # Planning file templates (state.md, roadmap.md, etc.)
│   │   └── workflows/             # Workflow instruction files (execute-phase.md, etc.)
│   ├── hooks/                     # Python enforcement hooks
│   ├── rules/                     # Auto-loaded session rules (keep minimal)
│   │   ├── methodology/           # frameworks.md, tenets.md
│   │   └── workflow/              # git.md
│   ├── skills/                    # Skill directories (each contains SKILL.md)
│   ├── CLAUDE.md                  # Project instructions for Claude
│   ├── gsd-file-manifest.json     # GSD file manifest (version 1.22.4, 140 files)
│   ├── package.json               # Minimal Node config for GSD hooks
│   └── settings.json              # Hook wiring + env config
├── .claude-plugin/
│   └── marketplace.json           # Turbo-mode plugin marketplace config (4 plugins)
├── .planning/                     # GSD project planning state (gitignored)
│   └── codebase/                  # Codebase analysis documents (this directory)
├── docs/                          # Documentation (reference, plans, decisions, etc.)
│   ├── adrs/                      # Architecture Decision Records
│   ├── audits/                    # Quality audits
│   ├── codex-mcp/                 # Codex MCP documentation
│   ├── decisions/                 # Lightweight decision logs
│   ├── frameworks/                # Thoroughness, decision-making, verification frameworks
│   ├── learnings/                 # Cross-model consultation insights + episodes/
│   ├── plans/                     # Implementation plan documents
│   ├── references/                # Writing principles, style guides
│   └── tickets/                   # Work tickets + closed-tickets/
├── packages/
│   ├── mcp-servers/
│   │   └── claude-code-docs/      # TypeScript BM25 MCP server
│   │       ├── src/               # TypeScript source (index.ts, lifecycle.ts, bm25.ts, etc.)
│   │       ├── dist/              # Compiled output (gitignored)
│   │       └── tests/             # Vitest tests (397 tests)
│   └── plugins/
│       ├── cross-model/           # Codex MCP + hooks + context-injection sub-package
│       │   ├── agents/            # codex-dialogue.md agent
│       │   ├── context-injection/ # FastMCP server (Python sub-package, 991 tests)
│       │   │   └── context_injection/  # Python package source
│       │   ├── hooks/             # hooks.json + hook scripts
│       │   ├── references/        # context-injection-contract.md
│       │   ├── scripts/           # codex_guard.py, nudge_codex.py, emit_analytics.py, etc.
│       │   └── skills/            # codex/, dialogue/, delegate/, consultation-stats/
│       ├── handoff/               # Session state persistence plugin
│       │   ├── hooks/             # hooks.json
│       │   ├── scripts/           # defer.py, distill.py, search.py, triage.py, etc.
│       │   └── skills/            # defer/, distill/, load/, quicksave/, save/, search/, triage/
│       ├── ticket/                # Repo-local ticket management plugin
│       │   ├── agents/            # ticket engine agent
│       │   ├── hooks/             # hooks.json + ticket_engine_guard.py
│       │   ├── scripts/           # ticket_engine_*.py, ticket_parse.py, ticket_validate.py, etc.
│       │   └── skills/            # ticket/, ticket-triage/
│       └── context-metrics/       # Context window usage tracking plugin
│           ├── hooks/             # hooks.json
│           ├── scripts/           # server.py, config.py, formatter.py, jsonl_reader.py, etc.
│           └── skills/            # context-dashboard/
├── scripts/                       # Repo utility scripts (uv inline scripts)
├── tests/                         # Top-level cross-package tests (pytest)
│   └── fixtures/                  # Shared test fixtures
├── pyproject.toml                 # uv workspace root (5 Python packages)
├── package.json                   # npm workspace root (mcp-servers + plugins)
└── uv.lock                        # Python lockfile
```

## Directory Purposes

**`.claude/agents/`:**
- Purpose: Subagent definitions spawned by orchestrators via the Task tool
- Contains: Single `.md` files with YAML frontmatter
- Key files: `gsd-planner.md`, `gsd-executor.md`, `gsd-codebase-mapper.md`, `gsd-verifier.md`, `assessment-runner.md`

**`.claude/commands/`:**
- Purpose: Slash commands (user-invokable via `/name`)
- Contains: `.md` files with YAML frontmatter; GSD commands in `gsd/` subdirectory
- Key files: `gsd/execute-phase.md`, `gsd/plan-phase.md`, `gsd/map-codebase.md`, `gsd/new-project.md`

**`.claude/get-shit-done/`:**
- Purpose: Complete GSD project management system; all workflow logic, tooling, and templates
- Contains: Compiled Node.js CLI, workflow .md files, planning templates, references
- Key files: `bin/gsd-tools.cjs` (compiled CLI), `workflows/execute-phase.md`, `templates/state.md`, `VERSION` (1.22.4)

**`.claude/hooks/`:**
- Purpose: Python scripts that enforce policies on tool calls
- Contains: Executable Python files; `test_require_gitflow.py` co-located test
- Key files: `require-gitflow.py` (branch protection), `block-credential-content.py`, `block-credential-json-files.py`, `block-keychain-extraction.py`, `gsd-check-update.js`, `gsd-context-monitor.js`, `gsd-statusline.js`

**`.claude/skills/`:**
- Purpose: Skill directories, each containing a `SKILL.md` that extends Claude's domain capabilities
- Contains: `<skill-name>/SKILL.md` + optional references and supporting files
- Key files: `learn/SKILL.md`, `handbook/SKILL.md`, `changelog/SKILL.md`, `promote/SKILL.md`, `writing-principles/SKILL.md`

**`packages/mcp-servers/claude-code-docs/src/`:**
- Purpose: TypeScript source for the BM25 documentation search MCP server
- Contains: 20 TypeScript modules with strict 1:1 test mirroring
- Key files: `index.ts` (entry), `lifecycle.ts` (ServerState), `bm25.ts` (scoring), `chunker.ts`, `loader.ts`, `cache.ts`

**`packages/plugins/<name>/scripts/`:**
- Purpose: Python scripts invoked by hooks or Claude directly during skill execution
- Contains: Domain logic, all pure Python (no external deps except pyyaml where declared)
- Naming: Prefixed by domain (`ticket_*.py`, `context_*.py`) or action (`defer.py`, `distill.py`)

**`packages/plugins/<name>/hooks/`:**
- Purpose: Hook registration and enforcement logic for the plugin
- Contains: `hooks.json` (event routing config) + optional hook Python files

**`packages/plugins/cross-model/context-injection/context_injection/`:**
- Purpose: Python package source for the FastMCP context injection server
- Contains: Full 17-step pipeline (`pipeline.py`), HMAC-secured scout execution (`execute.py`), redaction subsystem (`redact.py`, `redact_formats.py`)

**`docs/`:**
- Purpose: Human-readable reference and planning documentation; not loaded at runtime
- Key subdirs: `frameworks/` (methodology), `references/` (writing-principles.md), `plans/` (design docs), `decisions/` (ADRs)

**`scripts/`:**
- Purpose: Developer tooling scripts (not Claude extension code)
- Contains: `promote` (extension deployer), `sync-settings` (hook wiring), `inventory`, `migrate`, `validate_*.py`

**`tests/`:**
- Purpose: Cross-package integration tests; per-package tests live inside `packages/plugins/<name>/tests/`
- Contains: Tests for shared analytics, stats, episode validation, codex guard behavior

## Key File Locations

**Entry Points:**
- `packages/mcp-servers/claude-code-docs/src/index.ts`: MCP server entry (TypeScript)
- `packages/plugins/cross-model/context-injection/context_injection/server.py`: Context injection MCP server (Python FastMCP)
- `packages/plugins/context-metrics/scripts/server.py`: Context metrics sidecar HTTP server
- `.claude/get-shit-done/bin/gsd-tools.cjs`: GSD project state CLI

**Configuration:**
- `.claude/settings.json`: Hook event routing + env vars + statusLine
- `.claude-plugin/marketplace.json`: Plugin marketplace (4 plugins)
- `pyproject.toml`: uv workspace (5 Python packages)
- `package.json`: npm workspace (mcp-servers + plugins)
- `packages/mcp-servers/claude-code-docs/src/index-cache.ts`: Version constants gating cache validity

**Core Logic:**
- `packages/plugins/cross-model/context-injection/context_injection/pipeline.py`: 17-step Call 1 pipeline
- `packages/plugins/cross-model/context-injection/context_injection/execute.py`: HMAC-secured Call 2 scout dispatch
- `packages/mcp-servers/claude-code-docs/src/lifecycle.ts`: ServerState dependency injection
- `packages/mcp-servers/claude-code-docs/src/bm25.ts`: BM25 scoring + heading boost
- `packages/plugins/ticket/scripts/ticket_engine_core.py`: Ticket lifecycle state machine
- `packages/plugins/handoff/scripts/defer.py`, `distill.py`, `search.py`: Handoff operations

**Testing:**
- `packages/mcp-servers/claude-code-docs/tests/`: Vitest tests (397 total)
- `packages/plugins/cross-model/context-injection/tests/`: pytest tests (991 total)
- `packages/plugins/handoff/tests/`, `packages/plugins/ticket/tests/`, `packages/plugins/context-metrics/tests/`
- `tests/`: Top-level cross-package tests

**Extension Artifacts (sandbox):**
- `.claude/skills/<name>/SKILL.md`: Skill instruction documents
- `.claude/agents/<name>.md`: Subagent definitions
- `.claude/commands/gsd/<name>.md`: GSD slash commands
- `.claude/hooks/<name>.py`: Hook enforcement scripts

## Naming Conventions

**Files:**
- Python scripts in plugin `scripts/`: `snake_case.py`; domain-prefixed within ticket plugin (`ticket_engine_core.py`)
- TypeScript modules: `kebab-case.ts` (e.g., `bm25.ts`, `index-cache.ts`, `chunk-helpers.ts`)
- Skill directories: `kebab-case/` containing `SKILL.md` (uppercase)
- Agent files: `kebab-case.md` (e.g., `gsd-planner.md`, `gsd-executor.md`)
- Hook scripts: `kebab-case.py` (action-named: `block-credential-content.py`, `require-gitflow.py`)
- Workflow files: `kebab-case.md` matching command names

**Directories:**
- Plugin packages: `kebab-case` matching package name (`cross-model`, `context-metrics`)
- MCP servers: `kebab-case` (`claude-code-docs`)
- Skills: `kebab-case` (`writing-principles`, `making-recommendations`)

**Python packages:**
- Package name uses hyphens in `pyproject.toml` but underscores in import paths (`context_injection`, `scripts`)

## Where to Add New Code

**New Skill:**
- Create `SKILL.md` at: `.claude/skills/<skill-name>/SKILL.md`
- Promote via: `uv run scripts/promote skill <skill-name>`
- Reference format: See `.claude/skills/learn/SKILL.md` for YAML frontmatter pattern

**New Command:**
- Create file at: `.claude/commands/<name>.md` or `.claude/commands/gsd/<name>.md`
- Promote via: `uv run scripts/promote command <name>`

**New Agent (Subagent):**
- Create file at: `.claude/agents/<name>.md`
- Promote via: `uv run scripts/promote agent <name>`

**New Hook:**
- Create file at: `.claude/hooks/<name>.py` (must be executable)
- Run after adding: `uv run scripts/sync-settings`
- Promote via: `uv run scripts/promote hook <name>`

**New Plugin:**
- Create directory at: `packages/plugins/<name>/`
- Required structure: `pyproject.toml`, `hooks/hooks.json`, `scripts/`, `tests/`
- Register in: `.claude-plugin/marketplace.json`
- Add to uv workspace: `pyproject.toml` `[tool.uv.workspace] members`

**New MCP Server:**
- Create directory at: `packages/mcp-servers/<name>/`
- Required files: `package.json`, `tsconfig.json`, `src/index.ts`
- Add to npm workspace: root `package.json` `workspaces`

**New Utility Script:**
- Add to: `scripts/<name>` (use uv inline script header for deps)
- Run as: `uv run scripts/<name>`

**New Tests (plugin):**
- Add to: `packages/plugins/<name>/tests/test_<module>.py`
- Run from anywhere: `uv run --package <name> pytest`

**New Tests (MCP server):**
- Add to: `packages/mcp-servers/claude-code-docs/tests/<module>.test.ts`
- Run with: `npm test` from the package directory

## Special Directories

**`.planning/`:**
- Purpose: GSD project state (STATE.md, roadmap, milestone, phase plans, codebase docs)
- Generated: By GSD commands
- Committed: Partially (plans committed; session-specific state may not be)

**`.claude/get-shit-done/bin/`:**
- Purpose: Compiled GSD tooling (not edited directly)
- Generated: From GSD framework source; distributed as compiled CJS
- Committed: Yes — `gsd-tools.cjs` and `lib/*.cjs` are checked in

**`packages/mcp-servers/claude-code-docs/dist/`:**
- Purpose: Compiled TypeScript output
- Generated: By `npm run build`
- Committed: No (in .gitignore)

**`.claude/handoffs/`:**
- Purpose: Session handoff documents
- Generated: By `/defer` and `/save` skills
- Committed: No (gitignored)

**`.claude/sessions/`:**
- Purpose: Session notes
- Generated: By session tracking
- Committed: No (gitignored)

**`tmp/`:**
- Purpose: Temporary working files
- Generated: Ad hoc during development
- Committed: No

---

*Structure analysis: 2026-03-13*

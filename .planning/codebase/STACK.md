# Technology Stack

**Analysis Date:** 2026-03-13

## Languages

**Primary:**
- Python 3.11+ - All plugin packages (`packages/plugins/`), hooks (`.claude/hooks/*.py`), utility scripts (`scripts/`)
- TypeScript 5.x - MCP server (`packages/mcp-servers/claude-code-docs/src/`)

**Secondary:**
- JavaScript (Node.js CJS) - GSD framework hooks (`.claude/hooks/*.js`)

## Runtime

**Environment:**
- Python: system Python 3.14.2 (via mise); packages require `>=3.11`
- Node.js: v24.11.1 (via mise); MCP server requires `>=18`

**Package Manager:**
- Python: `uv` (workspace mode) — root `pyproject.toml` links all plugin packages
- Node.js: `npm` — workspace at repo root covers `packages/mcp-servers/*` and `packages/plugins/*`
- Lockfiles: `uv.lock` (root + per-package), `package-lock.json` (root)

## Frameworks

**Core (Python):**
- `mcp>=1.9.0` (FastMCP) - MCP server framework for context-injection package (`packages/plugins/cross-model/context-injection/`)
- `pyyaml>=6.0` - YAML parsing in handoff-plugin and ticket-plugin

**Core (TypeScript):**
- `@modelcontextprotocol/sdk ^1.25.0` - MCP server protocol for claude-code-docs (`packages/mcp-servers/claude-code-docs/`)
- `zod ^3.25.0` - Runtime schema validation for search tool inputs/outputs
- `stemmer ^2.0.1` - Porter stemmer for BM25 tokenization
- `yaml ^2.0.0` - YAML frontmatter parsing in doc chunker

**Testing:**
- Python: `pytest>=8.0` (all packages), `pytest-asyncio>=0.24` (context-injection only)
- TypeScript: `vitest ^2.0.0` (claude-code-docs)
- Linting: `ruff>=0.8` (context-injection dev dependency)

**Build/Dev:**
- TypeScript: `tsc` (compiles to `dist/`, target ES2022, module NodeNext)
- Python: `hatchling` build backend (context-injection only; other packages have no build-system section)

## Key Dependencies

**Critical:**
- `mcp>=1.9.0` (FastMCP) - context-injection MCP server built on it. Entry: `packages/plugins/cross-model/context-injection/context_injection/server.py`
- `@modelcontextprotocol/sdk ^1.25.0` - claude-code-docs MCP protocol. Entry: `packages/mcp-servers/claude-code-docs/src/index.ts`
- `pyyaml>=6.0` - Handoff and ticket plugin YAML/frontmatter parsing. Used in `packages/plugins/handoff/scripts/` and `packages/plugins/ticket/scripts/`

**Infrastructure:**
- `zod ^3.25.0` - Validates MCP tool inputs and cache serialization schemas in `packages/mcp-servers/claude-code-docs/src/index-cache.ts`
- `stemmer ^2.0.1` - Porter stemmer + CamelCase split in `packages/mcp-servers/claude-code-docs/src/tokenizer.ts`
- `hmac` (Python stdlib) - HMAC token signing for context-injection scout security: `context_injection/state.py`, `context_injection/templates.py`, `context_injection/execute.py`

## Configuration

**Environment:**
- No `.env` files in repo — all config via environment variables at runtime
- `settings.json` (`.claude/settings.json`) — Claude Code hook registration + `GITFLOW_ALLOW_FILES` env injection
- Plugin marketplace: `.claude-plugin/marketplace.json` — registers all 4 plugins for `turbo-mode` bundle

**Build:**
- `tsconfig.base.json` — shared TypeScript compiler options (ES2022 target, NodeNext module, strict mode, declaration maps, sourcemaps, `outDir: dist`)
- `packages/mcp-servers/claude-code-docs/tsconfig.json` — extends base
- `pyproject.toml` (root) — uv workspace definition; each plugin has its own `pyproject.toml`

## Platform Requirements

**Development:**
- POSIX required (macOS/Linux/WSL) — context-injection server rejects non-POSIX at startup (`packages/plugins/cross-model/context-injection/context_injection/server.py:22`)
- `git` on PATH — required by context-injection server and `codex_delegate.py`
- `codex` CLI — required by cross-model delegation (`packages/plugins/cross-model/scripts/codex_delegate.py`); minimum version `0.111.0`
- `uv` — Python workspace management and script runner (`uv run scripts/<name>`)
- `npm` — Node.js workspace and MCP server build (`npm run build`)

**Production:**
- Extensions deploy to `~/.claude/` via `uv run scripts/promote`
- Plugins deploy via `turbo-mode` marketplace bundle (`.claude-plugin/marketplace.json`)
- GSD framework files install to `~/.claude/get-shit-done/` (version-tracked, currently v1.22.4)
- npm registry queried at `SessionStart` to check for `get-shit-done-cc` package updates

---

*Stack analysis: 2026-03-13*

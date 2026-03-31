# codex-collaboration

Codex advisory consultation and dialogue via direct JSON-RPC to the Codex App Server.

## Prerequisites

| Requirement | Purpose | Check |
|-------------|---------|-------|
| Claude Code | Plugin host | `claude --version` |
| Codex CLI 0.117.0+ | Advisory runtime | `codex --version` |
| Python 3.11+ | MCP server | `python3 --version` |
| uv | Package management | `uv --version` |

**Authentication:** Run `codex login` or set `OPENAI_API_KEY`.

## Install

### From the dev repo (plugin-dir)

```bash
claude --plugin-dir packages/plugins/codex-collaboration
```

### From a marketplace (after promotion)

```bash
/plugin install codex-collaboration@<marketplace>
```

## Smoke Test

After installing, verify the plugin is working:

1. **Check plugin loaded:**
   ```
   /mcp
   ```
   Look for `codex-collaboration` in the MCP server list.

2. **Run status check:**
   ```
   /codex-status
   ```
   Should return Codex version, auth status, and method availability.

3. **Run a consultation:**
   ```
   /consult-codex What is the purpose of this repository?
   ```
   Should perform a `codex.status` preflight, then dispatch a consultation and relay the result.

## Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| `codex-status` | `/codex-status` | Runtime health, auth, version diagnostics |
| `consult-codex` | `/consult-codex <question>` | One-shot advisory consultation with status preflight |

## Architecture

The plugin runs a stdio MCP server (`scripts/codex_runtime_bootstrap.py`) that exposes tools for consultation and dialogue. The server communicates with the Codex App Server via JSON-RPC (`server/runtime.py`).

Dialogue state (lineage, journal, turn metadata) is session-scoped. The session identity is published by a `SessionStart` hook and read lazily on the first dialogue tool call.

## Limitations

- **Concurrent sessions unsupported:** Two simultaneous Claude sessions sharing this plugin will race on the session identity file. Single-session use only for the current rollout target.
- **No credential scanning:** The safety substrate (hook guard, secret taxonomy) is deferred to T-20260330-03.
- **No profiles or learning retrieval:** Production consult UX hardening is deferred to T-20260330-03.

## Tests

```bash
uv run pytest tests/ -v
```

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

## Safety Substrate

The plugin enforces a fail-closed credential scanning chain on all content-bearing advisory tool calls (`codex.consult`, `codex.dialogue.start`, `codex.dialogue.reply`):

- **Hook guard** (`scripts/codex_guard.py`): `PreToolUse` hook validates raw tool input before the MCP server processes it. Exits 2 (block) on parse failure, malformed input, or internal error.
- **Tool-input safety policy** (`server/consultation_safety.py`): Per-tool scan policies with field-aware traversal and tiered credential scanning.
- **Secret taxonomy** (`server/secret_taxonomy.py`): Tiered pattern definitions — strict (hard-block), contextual (block unless placeholder bypass), broad (shadow/telemetry).
- **Consultation profiles** (`server/profiles.py`): Named profiles resolving posture, turn budget, reasoning effort, sandbox, and approval policy.
- **Learning retrieval** (`server/retrieve_learnings.py`): Tag/keyword-matched learnings injected into advisory briefings via the context assembly pipeline.
- **Analytics emission**: `OutcomeRecord` persisted to `analytics/outcomes.jsonl` for consult and dialogue outcomes.

## Limitations

- **Concurrent sessions unsupported:** Two simultaneous Claude sessions sharing this plugin will race on the session identity file. Single-session use only for the current rollout target.
- **No phased profiles:** Profiles with `phases` (e.g., `debugging`) are rejected until phase-progression support is implemented.

## Configuration

The plugin reads the following environment variables at module load. Plugin restart is required for changes to take effect.

| Variable | Default | Description |
|---|---|---|
| `CODEX_COLLAB_APPROVAL_OPERATOR_WINDOW_SECONDS` | `900` (15 min) | TTL for parked approval requests in `command_approval` and `file_change` flows. Operator decides arriving after this window are rejected as `job_not_awaiting_decision`. Must be a positive number; non-numeric or non-positive values fall back to the default with a warning logged. Useful for diagnostic-style operator workflows that exceed the default budget under per-cycle review tempo. |

## Tests

```bash
uv run pytest tests/ -v
```

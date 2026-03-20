# T-20260319-01: Migrate cross-model transport from Codex MCP server to codex exec CLI

```yaml
id: T-20260319-01
date: 2026-03-19
status: resolved
priority: high
tags: [cross-model, codex, infrastructure]
blocked_by: []
blocks: []
effort: medium
```

## Problem

The Codex MCP server (`codex mcp-server`) broke after `codex-cli` updated to v0.116.0. Every call to `mcp__plugin_cross-model_codex__codex` fails with `"Failed to load Codex configuration from overrides: No such file or directory"` regardless of parameters passed. The MCP server's tool schema advertises parameters (`approval-policy`, `config` as JSON object) that no longer match the underlying CLI.

This blocks `/codex` and `/dialogue` — the entire cross-model consultation pipeline.

## Root Cause

The `codex mcp-server` subcommand is a first-party wrapper shipped with the Codex CLI. When the CLI updates, the MCP server's internal parameter translation breaks if the upstream API changes. In v0.116.0:
- `-p` changed from prompt to `--profile`
- `--approval-policy` renamed to `--ask-for-approval`
- Config overrides changed from JSON objects to TOML `key=value` format via `-c`

The MCP server exposes its own tool schema that must stay in sync with the CLI — a tight coupling that breaks on upstream updates.

## Evidence

- Session 2026-03-19: 4 consecutive MCP tool calls all failed with the same config error
- `codex exec` works correctly (tested: one-shot and resume)
- `codex exec resume <thread_id> "<prompt>" --json` provides full thread continuity — same `thread_id` returned, Codex remembers prior turns, server-side context caching confirmed (`cached_input_tokens` populated)

## Approach

Replace the MCP server transport with `codex exec` CLI invocations via a Python adapter script (same pattern as `codex_delegate.py`).

### Transport mapping

| MCP Server | `codex exec` equivalent |
|------------|------------------------|
| `codex` tool (new conversation) | `codex exec "<prompt>" --json` → parse `thread_id` from `thread.started` JSONL event |
| `codex-reply` tool (continue) | `codex exec resume "<thread_id>" "<prompt>" --json` |
| `sandbox` parameter | `-c sandbox_mode="read-only"` |
| `approval-policy` parameter | `-c approval_policy="never"` |
| `config.model_reasoning_effort` | `-c model_reasoning_effort="xhigh"` |

### Tasks

1. **Write `codex_consult.py` adapter** — handles new conversation + resume, JSONL parsing, credential scanning, thread_id extraction. Model on `codex_delegate.py` but for consultation (read-only, returns Codex's response text rather than file changes).

2. **Update `/codex` skill** — replace MCP tool invocation with adapter call. Single-turn: `codex exec` → parse response. Map skill flags (`-s`, `-a`, `-t`) to `-c key=value` format.

3. **Update `/dialogue` skill + codex-dialogue agent** — replace `codex-reply` MCP tool with `codex exec resume`. The codex-dialogue agent manages turn state; it needs to store `thread_id` from the adapter output and pass it on resume.

4. **Update consultation contract** — §9 (Codex Transport Adapter) and §10 (Continuity State Contract) reference MCP tool names. Update to document both transports or replace.

5. **Remove MCP server from `.mcp.json`** — remove the `codex` entry from `packages/plugins/cross-model/.mcp.json`. Keep `context-injection` (independent server).

6. **Update analytics emission** — the `mode` field currently distinguishes `server_assisted` vs `manual_legacy`. Add or rename to reflect `cli_exec` transport.

### Risks

- **Codex CLI flag stability**: `codex exec` flags could also change in future updates. Mitigation: the adapter script isolates flag translation to one file (vs the MCP server which is upstream code we can't modify).
- **Resume session expiry**: Thread IDs may expire after some period. The current MCP server had the same limitation; the `/codex` skill already handles this (rebuild briefing on expired thread).
- **JSONL output format changes**: The `thread.started` event schema could change. Mitigation: adapter validates expected fields and fails explicitly.

## Key Files

- `packages/plugins/cross-model/.mcp.json` — MCP server registration (remove `codex` entry)
- `packages/plugins/cross-model/scripts/codex_delegate.py` — existing adapter pattern to model
- `packages/plugins/cross-model/references/consultation-contract.md` — §9, §10 need updates
- `~/.claude/plugins/cache/turbo-mode/cross-model/3.0.0/skills/codex/SKILL.md` — `/codex` skill (deployed copy)
- `~/.claude/plugins/cache/turbo-mode/cross-model/3.0.0/skills/delegate/SKILL.md` — reference for adapter pattern
- `packages/plugins/cross-model/agents/codex-dialogue.md` — codex-dialogue agent (uses `codex-reply`)

## Acceptance Criteria

- [ ] `/codex "test prompt"` works with Codex CLI v0.116.0+
- [ ] `/dialogue` multi-turn conversation works with thread continuity via `exec resume`
- [ ] `/delegate` unaffected (already uses `codex exec`)
- [ ] No MCP server dependency for cross-model consultation
- [ ] Analytics events capture transport type
- [ ] Existing 631 cross-model tests pass (or are updated for new transport)

## Resolution

**Approach taken:** D-prime architecture (adapter + shim) instead of direct skill/agent rewrites.

| Task | Description | Status |
|------|-------------|--------|
| T1 | `codex_consult.py` adapter with `consult()` API | Complete |
| T2 | `consultation_safety.py` extraction | Complete |
| T3 | `codex_shim.py` FastMCP MCP shim (18 tests) | Complete |
| T4 | Wire shim into `.mcp.json` + E2E verification | Complete |

**What this resolves:** The original problem (broken MCP server after codex-cli v0.116.0 update) is fully resolved. The local shim replaces the upstream binary, eliminating the tight coupling that caused the breakage.

**What remains (T5):** Decide whether Phase 2 (optional shim removal — direct `codex exec` calls from skills/agents) is warranted. Phase 2 is only justified if the shim grows beyond ~150 lines or maintenance burden exceeds the adapter's blast-radius savings. Current shim is ~95 lines.

**Open questions carried from Codex dialogue (`019d09f3`):**
- Whether upstream `codex mcp-server` serializes concurrent requests (same as shim's FastMCP behavior)
- Whether upstream handles cancellation/disconnect differently from the shim
- `approval_policy` (underscore) vs `approval-policy` (hyphen) contract drift — normalize in a future pass

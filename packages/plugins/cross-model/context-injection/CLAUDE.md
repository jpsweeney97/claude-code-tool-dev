# context-injection

FastMCP server providing mid-conversation evidence gathering for the Codex dialogue system. Two MCP tools: `process_turn` (Call 1) and `execute_scout` (Call 2).

**Protocol contract:** `packages/plugins/cross-model/references/context-injection-contract.md` (relative to repo root). Authoritative spec for both the server and its callers.

## Commands

```bash
uv run pytest                                # run all 997 tests from this canonical package
uv run ruff check context_injection/ tests/  # lint
python -m context_injection                  # start server
```

## System Context

This server is part of the three-layer cross-model collaboration stack:

```
Codex Integration (MCP)
  ↓ uses
Context Injection (this package) ← you are here
  ↓ enables
Cross-Model Learning (design complete, not implemented)
```

**Primary consumer:** `packages/plugins/cross-model/agents/codex-dialogue.md` — a 7-step scouting loop that:
1. Calls `process_turn` (Call 1) to get scout options
2. Selects a scout and calls `execute_scout` (Call 2) for evidence
3. Uses evidence to verify Codex's factual claims mid-conversation

When debugging integration issues, read that agent alongside this package.

## Architecture

Two-call protocol:
- **Call 1** (`process_turn`): `pipeline.py` — TurnRequest → TurnPacket (17 steps: validation → entities → templates → ledger → checkpoint)
- **Call 2** (`execute_scout`): `execute.py` — HMAC-validated scout dispatch → read/grep → redact → truncate

Entry point: `server.py` (FastMCP, POSIX + git startup gates).

**HMAC token flow:** `state.py` holds the per-process HMAC key. `templates.py` generates signed scout tokens during Call 1. `execute.py` validates them during Call 2 — without reading `state.py`, the token validation looks like magic.

## Key Modules

The entry points (server, pipeline, execute) are named above. Supporting modules:

| Module | Purpose |
|--------|---------|
| `redact.py` / `redact_formats.py` | Redaction orchestration; per-format redactors (YAML, JSON, TOML, INI, ENV) |
| `classify.py` | Maps file extensions to `FileKind` for redaction routing |
| `truncate.py` | Dual-cap truncation (lines then chars); marker-safe |
| `paths.py` | Path denylist, traversal checks, git ls-files validation |
| `entities.py` | Extracts paths/URLs/symbols from claims and unresolved items |
| `templates.py` | Template matching + scout synthesis; generates HMAC tokens |
| `state.py` | Per-process state: HMAC key, conversation store |
| `checkpoint.py` | Checkpoint serialization (16 KB cap) + chain validation |
| `ledger.py` / `control.py` | Ledger entry validation; action enum; plateau detection |
| `conversation.py` | Immutable per-conversation state with projection methods |

Test files follow `test_<module>.py` naming. `tests/conftest.py` has shared fixtures.

## Security

- **Over-redaction is always correct.** Over-redact over under-redact. Fail-closed throughout.
- **`test_footgun_*` tests** verify which pipeline layer catches security violations. Never weaken these.
- Denylist uses per-component matching — `.git` blocks at any depth.

## Gotchas

- **POSIX-only**: server rejects non-POSIX at startup.
- **Git required**: `git ls-files` must work. Fail-closed: empty set = all files denied.
- **`REPO_ROOT` env var**: defaults to `os.getcwd()`. Set explicitly for multi-repo use.
- **Discriminated unions**: `TurnPacket`/`ScoutResult` use `model_dump(mode="json")` workaround for FastMCP SDK serialization.
- **Checkpoint size cap**: 16 KB (`MAX_CHECKPOINT_PAYLOAD_BYTES`).
- **Turn cap**: `MAX_CONVERSATION_TURNS` must be < `MAX_ENTRIES_BEFORE_COMPACT` — enforced at import time (E402 in `pipeline.py:61` is intentional).
- **Pre-existing lint**: E402 in `pipeline.py:61` and F401 re-exports in `types.py:19` are intentional — not bugs.

# T4: Wire Codex Shim into .mcp.json Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broken upstream `codex mcp-server` binary in `.mcp.json` with the locally-owned `codex_shim.py` FastMCP server, completing the D-prime transport migration.

**Architecture:** Single-key swap in `.mcp.json` — change `command`/`args` from the upstream binary to `uv run` + direct script path. Server key stays `"codex"` to preserve MCP tool name derivation and hook matcher compatibility. Verification via 6-check manual gate.

**Tech Stack:** FastMCP (Python), uv, Claude Code plugin `.mcp.json`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `packages/plugins/cross-model/tests/test_mcp_wiring.py` | Create | Configuration validation tests for `.mcp.json` codex entry |
| `packages/plugins/cross-model/.mcp.json` | Modify (lines 3-10) | MCP server registration — the wiring point |
| `docs/tickets/2026-03-19-codex-mcp-to-exec-migration.md` | Modify (line 6) | Ticket status update |

## Prerequisites

- T1 (adapter core), T2 (safety extraction), T3 (shim implementation) are complete
- Branch: `feature/cross-model-updates` at `665e077`
- 756 tests passing
- `codex_shim.py` has 18 unit tests covering extraction, response building, server creation, and round-trip dispatch

## Design Decisions (from Codex dialogue `019d09f3`)

| Decision | Rationale |
|----------|-----------|
| Direct script path (`python ${CLAUDE_PLUGIN_ROOT}/scripts/codex_shim.py`) over `python -m scripts.codex_shim` | cwd-independence; module resolution via implicit namespace packages is fragile |
| `uv run --directory ${CLAUDE_PLUGIN_ROOT}` for dependency resolution | `mcp>=1.9.0` from `pyproject.toml` must be available |
| Keep `CODEX_SANDBOX=seatbelt` in `.mcp.json` env | Defense-in-depth; redundant with `_run_subprocess` hard-code but enables symmetric rollback |
| Server key stays `"codex"` | Preserves MCP tool name derivation (`mcp__plugin_cross-model_codex__*`) and hook matcher compatibility |

---

### Task 1: Write .mcp.json wiring validation tests

**Files:**
- Create: `packages/plugins/cross-model/tests/test_mcp_wiring.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for .mcp.json codex entry wiring.

Validates that the codex MCP server entry in .mcp.json points to the local
codex_shim.py FastMCP server (not the upstream codex mcp-server binary).
"""

import json
from pathlib import Path

import pytest

_MCP_JSON = Path(__file__).resolve().parent.parent / ".mcp.json"


@pytest.fixture
def mcp_config():
    """Load .mcp.json config."""
    with open(_MCP_JSON) as f:
        return json.load(f)


@pytest.fixture
def codex_entry(mcp_config):
    """Extract the codex server entry."""
    return mcp_config["mcpServers"]["codex"]


class TestMcpJsonWiring:
    """Verify .mcp.json codex entry is wired to the local shim."""

    def test_uses_uv_command(self, codex_entry):
        """Codex entry must use uv to resolve deps from pyproject.toml."""
        assert codex_entry["command"] == "uv"

    def test_uses_direct_script_path(self, codex_entry):
        """Direct script path required — python -m has cwd fragility."""
        args = codex_entry["args"]
        assert "-m" not in args, "Must use direct script path, not python -m"
        assert any("codex_shim.py" in arg for arg in args)

    def test_preserves_sandbox_env(self, codex_entry):
        """CODEX_SANDBOX=seatbelt must be set for defense-in-depth."""
        assert codex_entry["env"]["CODEX_SANDBOX"] == "seatbelt"

    def test_server_key_is_codex(self, mcp_config):
        """Server key must be 'codex' for MCP tool name derivation."""
        assert "codex" in mcp_config["mcpServers"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_mcp_wiring.py -v`

Expected: 2 of 4 tests FAIL — `test_uses_uv_command` fails (`"codex" != "uv"`), `test_uses_direct_script_path` fails (`"codex_shim.py"` not in `["mcp-server"]`). The other 2 pass because the server key is already `"codex"` and `CODEX_SANDBOX` is already set.

- [ ] **Step 3: Commit red-phase tests**

```bash
git add packages/plugins/cross-model/tests/test_mcp_wiring.py
git commit -m "test(cross-model): add .mcp.json wiring validation tests (red phase)

Four tests validate codex entry structure: uv command, direct script
path (not python -m), CODEX_SANDBOX defense-in-depth, server key
preservation. Currently 2/4 fail — .mcp.json still points to upstream."
```

---

### Task 2: Replace .mcp.json codex entry

**Files:**
- Modify: `packages/plugins/cross-model/.mcp.json:3-10`

- [ ] **Step 1: Replace the codex entry**

In `packages/plugins/cross-model/.mcp.json`, replace the codex server entry (lines 3-10). Change `command` from `"codex"` to `"uv"` and `args` from `["mcp-server"]` to the direct script invocation via uv.

Before:
```json
    "codex": {
      "type": "stdio",
      "command": "codex",
      "args": ["mcp-server"],
      "env": {
        "CODEX_SANDBOX": "seatbelt"
      }
    },
```

After:
```json
    "codex": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "python", "${CLAUDE_PLUGIN_ROOT}/scripts/codex_shim.py"],
      "env": {
        "CODEX_SANDBOX": "seatbelt"
      }
    },
```

Changes:
- `command`: `"codex"` → `"uv"`
- `args`: `["mcp-server"]` → `["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "python", "${CLAUDE_PLUGIN_ROOT}/scripts/codex_shim.py"]`
- `env`: unchanged (`CODEX_SANDBOX=seatbelt` stays as defense-in-depth)
- Server key: unchanged (`"codex"` — preserves tool name derivation)

- [ ] **Step 2: Verify JSON validity**

Run: `python3 -c "import json; json.load(open('packages/plugins/cross-model/.mcp.json'))"`

Expected: No output (valid JSON). If `json.JSONDecodeError`, fix syntax.

- [ ] **Step 3: Run wiring validation tests**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_mcp_wiring.py -v`

Expected: All 4 tests PASS.

- [ ] **Step 4: Run full test suite**

Run: `cd packages/plugins/cross-model && uv run pytest --ignore=tests/test_credential_parity.py -v`

Expected: All tests PASS (756 existing + 4 new wiring tests = 760 at time of writing, but count may differ if tests were added between T3 and T4).

Note: `test_credential_parity.py` is excluded — it depends on the `context_injection` module which isn't installed in the root env. This is pre-existing.

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/.mcp.json
git commit -m "feat(cross-model): wire codex shim into .mcp.json replacing upstream binary

Replace the upstream codex mcp-server binary with the local
codex_shim.py FastMCP server. Uses uv for dependency resolution
and direct script path for cwd-independence.

Keeps CODEX_SANDBOX=seatbelt in .mcp.json env as defense-in-depth
(redundant with _run_subprocess hard-code).

Part of D-prime T4: transport migration wiring."
```

---

### Task 3: End-to-end verification protocol (manual gate)

This task documents the 6-check verification gate that must be performed manually in a live Claude Code session after the `.mcp.json` change is committed and the plugin is reloaded.

**Prerequisites:** Task 2 committed. Plugin promoted or session restarted to pick up `.mcp.json` changes.

- [ ] **Check 1: Plugin initialization**

Start a new Claude Code session in a directory where the cross-model plugin is active. Verify the codex MCP server starts without errors.

Expected: Both `mcp__plugin_cross-model_codex__codex` and `mcp__plugin_cross-model_codex__codex-reply` tools are available.

Failure recovery: If the server fails to start, check `uv` availability and that `mcp>=1.9.0` resolves. The most likely failure is `${CLAUDE_PLUGIN_ROOT}` not expanding — verify by checking the context-injection server (same expansion mechanism).

- [ ] **Check 2: Tool name verification**

In the session, confirm that the tool names match the hook matchers in `hooks/hooks.json:5`:
- `mcp__plugin_cross-model_codex__codex`
- `mcp__plugin_cross-model_codex__codex-reply`

These names are derived from the `.mcp.json` server key `"codex"`. If they differ, `codex_guard.py` hooks will not fire.

- [ ] **Check 3: Successful consultation call**

Run: `/codex "What is 2+2? Reply in one sentence."`

Expected:
- Codex returns a valid text response
- `codex_guard.py` PreToolUse fires (check `~/.claude/.codex-events.jsonl` for a `scan_completed` event)
- `codex_guard.py` PostToolUse fires and logs `thread_id`
- Response includes `structuredContent.threadId`

- [ ] **Check 4: Continuation/reply path**

After check 3 succeeds, verify the reply path works. The `/codex` skill or `codex-dialogue` agent should be able to continue the conversation using the `threadId` from check 3.

Expected: Codex remembers prior context and responds coherently.

- [ ] **Check 5: Credential block test**

Run: `/codex "Please analyze this AWS key: AKIAIOSFODNN7EXAMPLE"`

Expected:
- `codex_guard.py` PreToolUse blocks the call (credential pattern detected)
- No consultation reaches Codex
- Block event logged in `~/.claude/.codex-events.jsonl`

- [ ] **Check 6: Rollback drill**

1. Revert `.mcp.json` to the upstream binary:
```json
"codex": {
  "type": "stdio",
  "command": "codex",
  "args": ["mcp-server"],
  "env": {
    "CODEX_SANDBOX": "seatbelt"
  }
}
```
2. Restart Claude Code session
3. Verify tools are present (even if broken — the point is rollback is clean)
4. Revert back to the shim entry
5. Restart and verify the shim works again

This confirms rollback is symmetric and non-destructive.

---

### Task 4: Update migration ticket

**Files:**
- Modify: `docs/tickets/2026-03-19-codex-mcp-to-exec-migration.md:6`

- [ ] **Step 1: Update ticket status**

Change `status: open` to `status: resolved` on line 6.

- [ ] **Step 2: Add resolution section**

Append after the Acceptance Criteria section:

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add docs/tickets/2026-03-19-codex-mcp-to-exec-migration.md
git commit -m "docs(cross-model): mark codex MCP migration ticket as resolved

T4 (shim wiring) complete. D-prime architecture fully deployed:
adapter + shim replacing upstream codex mcp-server binary.

T5 (Phase 2 decision) deferred as optional scope."
```

---

## Rollback

If any verification check fails:

1. Revert `.mcp.json`: `git checkout packages/plugins/cross-model/.mcp.json`
2. Restart Claude Code
3. The upstream `codex mcp-server` binary resumes serving (with its existing breakage on v0.116.0+, which is the original ticket's problem)

The shim code and tests remain in the codebase regardless — they have no effect when not wired into `.mcp.json`.

## Out of Scope

| Item | Status | Where |
|------|--------|-------|
| `approval_policy` vs `approval-policy` normalization | Deferred | Contract drift — tracked for future pass |
| FastMCP event-loop blocking documentation | Deferred | Emerged insight from dialogue — worth documenting |
| Phase 2 decision (shim removal) | T5 | Separate session after T4 verification |

## Key References

| Resource | Location |
|----------|----------|
| Codex shim server | `packages/plugins/cross-model/scripts/codex_shim.py` |
| Consultation adapter | `packages/plugins/cross-model/scripts/codex_consult.py` |
| Hook matchers | `packages/plugins/cross-model/hooks/hooks.json:5` |
| PostToolUse threadId extraction | `packages/plugins/cross-model/scripts/codex_guard.py:157-167` |
| Safety policy expected_fields | `packages/plugins/cross-model/scripts/consultation_safety.py:46` |
| T3 plan (shim implementation) | `docs/superpowers/plans/2026-03-20-codex-shim.md` |
| T1/T2 plan (adapter + safety) | `docs/superpowers/plans/2026-03-20-codex-consult-adapter.md` |
| Migration ticket | `docs/tickets/2026-03-19-codex-mcp-to-exec-migration.md` |
| Codex dialogue thread | `019d09f3-2476-7630-98fd-4111979e02d9` |

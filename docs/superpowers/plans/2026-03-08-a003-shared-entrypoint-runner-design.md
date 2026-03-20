# A-003: Shared Entrypoint Runner — Design

**Finding:** A-003 (Medium, Data Flow) — user and agent entrypoints are duplicated almost verbatim, requiring dual edits for any shared behavior change.

**Scope:** Extract the full entrypoint boundary logic into a shared runner module. Entrypoints become thin wrappers that set `request_origin` and delegate. Hook guard unchanged.

## Problem

`ticket_engine_user.py` and `ticket_engine_agent.py` are 190 lines each, byte-identical except for:
- Docstring (`"user"` vs `"agent"`)
- Usage string (script name)
- `REQUEST_ORIGIN = "user"` vs `"agent"`

The duplicated logic includes:
- Payload read and JSON deserialization
- Forced origin assignment
- Hook-origin mismatch check
- Execute trust-triple enforcement
- Project-root discovery
- tickets_dir resolution
- Stage dispatch routing (`_dispatch()`)
- Exit-code mapping

This is the logic most likely to drift if left duplicated.

## Solution

### New module: `scripts/ticket_engine_runner.py`

```python
def run(request_origin: str, argv: list[str] | None = None, *, prog: str) -> int:
```

**Parameters:**
- `request_origin`: `"user"` or `"agent"` — the trust-authoritative origin. The payload is normalized to match (`payload["request_origin"] = request_origin`), but `request_origin` is the trust source, not the payload.
- `argv`: Command-line arguments (defaults to `sys.argv[1:]`). Enables in-process testing.
- `prog`: Script name for usage strings and diagnostics. No control flow dependency.

**Responsibility order:**
1. Parse `argv` — extract subcommand and payload path
2. Read and deserialize payload JSON
3. Normalize `payload["request_origin"] = request_origin`
4. Check hook-origin mismatch (all stages)
5. Execute trust-triple enforcement (execute stage only)
6. Discover project root
7. Resolve tickets_dir
8. Call `_dispatch(subcommand, payload, tickets_dir, request_origin)`
9. Print response JSON to stdout
10. Return exit code via `_exit_code(resp)` helper

**`_dispatch`** moves into the runner as a module-private function. Takes `request_origin` as a parameter instead of reading a module-level constant.

**`_exit_code`** is a small helper that maps `EngineResponse` to exit codes (0/1/2). Single-sourced — no longer duplicated.

**Output contract:**
- Steps 1-2 failures: stderr + return 1 (CLI-shape errors, not engine responses)
- Steps 3-7 failures: `EngineResponse` JSON on stdout + return 1 (structured engine errors)
- Step 8+: `EngineResponse` JSON on stdout + return 0/1/2

### Entrypoint wrappers

Both files become thin wrappers (~15 lines):

```python
#!/usr/bin/env python3
"""User entrypoint for the ticket engine.

Hardcodes request_origin="user". Called by ticket-ops skill.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ticket_engine_runner import run

if __name__ == "__main__":
    raise SystemExit(run("user", prog="ticket_engine_user.py"))
```

Key properties:
- `sys.path.insert` stays in wrapper — must execute before runner import
- Docstring preserved (human-readable identity, trust-boundary documentation)
- `if __name__ == "__main__"` guard — importable by tests without side effects
- Filenames unchanged — hook guard allowlist continues to match

### Hook guard impact

No changes needed:
- `_build_allowlist_pattern()` matches `ticket_engine_(user|agent)\.py` — wrapper filenames unchanged
- `_TICKET_SCRIPT_BASENAMES` — `ticket_engine_runner.py` NOT added (never invoked directly; adding it would widen the surface incorrectly)
- `_resolve_origin()` — derives origin from `agent_id` presence in the event, unaffected

### Import direction

```
ticket_engine_runner.py  (imports from ticket modules)
    ^               ^
    |               |
ticket_engine_user.py   ticket_engine_agent.py
    (thin wrappers, import only ticket_engine_runner)
```

The runner imports: `ticket_engine_core`, `ticket_paths`, `ticket_stage_models`, `ticket_trust`. This is the same import set as the current entrypoints.

## Testing

### `test_runner.py` (new, in-process)

The `argv` parameter enables fast in-process testing without subprocess overhead.

| Test case | Expected exit code | Stdout assertion |
|---|---|---|
| Usage / missing args | 1 | (stderr) |
| Payload read failure (bad JSON) | 1 | (stderr) |
| Payload read failure (missing file) | 1 | (stderr) |
| Hook origin mismatch | 1 | `origin_mismatch` |
| Execute trust triple: no hook_injected | 1 | `policy_blocked` |
| Execute trust triple: empty session_id | 1 | `policy_blocked` |
| Execute trust triple: missing hook_request_origin | 1 | `policy_blocked` |
| Project root not found | 1 | `policy_blocked` |
| tickets_dir outside project root | 1 | `policy_blocked` |
| Successful classify | 0 | `ok` |
| Successful execute with full trust triple | 0 | `ok_create` |
| Exit code 2 for `need_fields` | 2 | `need_fields` |
| Unknown subcommand | 1 | `intent_mismatch` |

### `test_entrypoints.py` (existing, subprocess)

Keep existing subprocess coverage model. Expect minimal assertion updates if usage text or error messages become slightly more uniform from centralization. No structural rewrite.

## Design decisions

### D1: Scope B — extract `run()` + `_dispatch()`, not just `_dispatch()`

Extracting only `_dispatch()` leaves 80% of the duplication in place. The boundary logic (origin mismatch, trust triple, project root, tickets_dir, exit codes) is the part most likely to drift.

### D2: `prog` is cosmetic only

`prog` controls usage strings and diagnostics. No control flow depends on it. This avoids coupling the runner's behavior to which script invoked it.

### D3: `request_origin` is the trust source, not the payload

The payload write (`payload["request_origin"] = request_origin`) is normalization for downstream code. The `request_origin` parameter is authoritative. This is documented but worth emphasizing because the trust model depends on it.

### D4: `ticket_engine_runner.py` excluded from hook candidate detection

The runner is never invoked directly. Adding it to `_TICKET_SCRIPT_BASENAMES` would widen the hook surface incorrectly.

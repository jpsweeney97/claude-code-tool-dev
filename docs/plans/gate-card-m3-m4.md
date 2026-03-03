## Gate Card: M3 → M4

**Gate type:** Critical

evaluated_sha: 017ccc4
handoff_sha: 036694e
commands_to_run: ["cd packages/plugins/ticket && uv run pytest tests/test_parse.py tests/test_migration.py tests/test_id.py tests/test_render.py tests/test_read.py tests/test_dedup.py -v"]
must_pass_files: [tests/test_parse.py, tests/test_migration.py, tests/test_id.py, tests/test_render.py, tests/test_read.py, tests/test_dedup.py]
api_surface_expected:
  - scripts.ticket_parse: [ParsedTicket, parse_ticket, extract_fenced_yaml, parse_yaml_block]
  - scripts.ticket_id: [allocate_id, build_filename]
  - scripts.ticket_render: [render_ticket]
  - scripts.ticket_read: [find_ticket_by_id, list_tickets]
  - scripts.ticket_dedup: [dedup_fingerprint, normalize, target_fingerprint]
verdict: PASS

### Probe Evidence

```
$ cd packages/plugins/ticket && uv run pytest tests/ -v
98 passed, 1 warning in 0.09s
```

Warning is expected: `test_skips_unparseable` creates a bad.md without YAML, triggering a `UserWarning` from `parse_ticket`.

```
$ uv run python -c "from scripts.ticket_parse import ParsedTicket, parse_ticket, extract_fenced_yaml, parse_yaml_block"
(exit 0)

$ uv run python -c "from scripts.ticket_read import find_ticket_by_id, list_tickets"
(exit 0)

$ uv run python -c "from scripts.ticket_dedup import dedup_fingerprint, normalize, target_fingerprint"
(exit 0)

$ uv run python -c "from scripts.ticket_id import allocate_id, build_filename"
(exit 0)

$ uv run python -c "from scripts.ticket_render import render_ticket"
(exit 0)
```

All 12 M4-needed symbols import successfully across 5 modules.

### Test Counts

| File | Tests | Status |
|------|-------|--------|
| test_parse.py | 38 | PASS |
| test_migration.py | 5 | PASS |
| test_id.py | 18 | PASS |
| test_render.py | 5 | PASS |
| test_read.py | 16 | PASS |
| test_dedup.py | 16 | PASS |
| **Total** | **98** | **PASS** |

### Codex Review

8 findings (1 P0, 4 P1, 3 P2). 1 adopted (P2 target_fingerprint OSError — committed at 017ccc4). 7 deferred:
- P0 render YAML injection: downgraded to P1, engine controls inputs, defer to M4
- P1 allocate_id closed-tickets scan: engine owns create flow, defer to M4
- P1 race condition: Phase 1 is single-user, no concurrency possible
- P1 seq overflow at 99: valid but unrealistic, trivial fix deferred to M4
- P1 date type crash: disagree — parser already coerces dates (ticket_parse.py:131-133)
- P2 path canonicalization: engine controls input paths
- P2 section enforcement: by design — renderer is a template, engine validates

### Warnings

1. Codex finding 4 (seq overflow at 99) should be addressed in M4 when the engine's create flow is built.
2. Codex finding 1 (render YAML injection) should be evaluated during M4 when the engine calls `render_ticket` with actual user input.
3. `test_skips_unparseable` produces a `UserWarning` — expected behavior, not a test issue.

## Gate Card: M2 → M3

```yaml
evaluated_sha: 3039868
handoff_sha: 224a410
gate_type: Standard+
commands_to_run:
  - "cd packages/plugins/ticket && uv run pytest tests/test_parse.py tests/test_migration.py -v"
must_pass_files:
  - tests/test_parse.py
  - tests/test_migration.py
api_surface_expected:
  scripts.ticket_parse:
    - ParsedTicket
    - parse_ticket
    - extract_fenced_yaml
    - parse_yaml_block
    - extract_sections
    - detect_generation
    - normalize_status
    - SECTION_RENAMES
    - CANONICAL_STATUSES
forward_dependency_sentinels:
  task_4_ticket_id: "from scripts.ticket_parse import extract_fenced_yaml, parse_yaml_block"
  task_6_ticket_read: "from scripts.ticket_parse import ParsedTicket, parse_ticket"
verdict: PASS
```

### Probe Evidence

**Test suite (43 tests):**
```
tests/test_parse.py: 38 passed
tests/test_migration.py: 5 passed
Total: 43 passed in 0.04s
```

**Forward-dependency sentinel — Task 4 (ticket_id):**
```
$ uv run python -c "from scripts.ticket_parse import extract_fenced_yaml, parse_yaml_block"
Task 4 sentinel: OK
```

**Forward-dependency sentinel — Task 6 (ticket_read):**
```
$ uv run python -c "from scripts.ticket_parse import ParsedTicket, parse_ticket"
Task 6 sentinel: OK
```

**API surface verification:**
```
ParsedTicket: dataclass, frozen=True
parse_ticket: function
extract_fenced_yaml: function
parse_yaml_block: function
extract_sections: function
detect_generation: function
normalize_status: function
SECTION_RENAMES: 7 entries
CANONICAL_STATUSES: 5 entries
```

### Warnings

1. **Codex P0 fixes applied post-plan.** Two bugs found by Codex review (non-string ID crash, shared mutable defaults) were fixed in commit `3039868`. These are defensive improvements not in the original plan.

2. **Gen4 golden test assertion strengthened.** Plan's original assertion was always-true via `or` fallback. Fixed to verify actual mapped value: `assert ticket.source["ref"] == "session-xyz"`.

3. **`scripts/__init__.py` added.** Not in plan — required for `from scripts.ticket_parse import ...` to resolve.

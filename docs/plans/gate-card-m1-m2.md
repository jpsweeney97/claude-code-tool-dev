## Gate Card: M1 → M2
evaluated_sha: ccc958c
handoff_sha: 233a301
commands_to_run: ["uv run pytest tests/ -v"]
must_pass_files: []
api_surface_expected:
  - tests.conftest: [make_ticket, make_gen1_ticket, make_gen2_ticket, make_gen3_ticket, make_gen4_ticket, tmp_tickets, tmp_audit]
verdict: PASS
warnings:
  - "Gen4 fixture uses source_type/source_ref as flat fields — M2 parser must define explicit mapping rules for these (Codex finding)"
  - "Plan gate exit smoke test checks '---' but tickets use fenced YAML — use '```yaml' assertion instead"
probe_evidence:
  - command: "uv run python -c 'from tests.conftest import make_gen1_ticket, ...;  # import + call all 5 factories'"
    result: "All factory smoke tests PASS — each returns Path, file exists, contains fenced YAML"
  - command: "uv run python -c 'from tests.conftest import make_ticket, make_gen1_ticket, make_gen2_ticket, make_gen3_ticket, make_gen4_ticket, tmp_tickets, tmp_audit'"
    result: "All 7 symbols imported successfully"
  - command: "uv run python -c 'from tests.conftest import parse_ticket'"
    result: "ImportError — correctly not importable (Task 3 not built)"
  - command: "uv run pytest tests/ -v"
    result: "collected 0 items, no tests ran (expected — no test files yet)"

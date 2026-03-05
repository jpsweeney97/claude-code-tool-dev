# M9 Skill Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the ticket engine to Claude Code's skill system with `/ticket` (mutation) and `/ticket-triage` (read-only) skills.

**Architecture:** Fully inline execution. `/ticket` routes 6 operations (create/update/close/reopen/list/query) — mutations go through the 4-stage engine pipeline via user entrypoint, read ops call `ticket_read.py` directly. `/ticket-triage` wraps `ticket_triage.py`. Guard hook expanded with read/triage allowlist branches.

**Tech Stack:** Python 3.11+, pytest, SKILL.md (YAML frontmatter + markdown)

**Design doc:** `docs/plans/2026-03-05-m9-skill-layer-design.md`

---

### Task 1: `ticket_read.py` CLI block

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_read.py:89` (append after line 89)
- Test: `packages/plugins/ticket/tests/test_read.py`

**Step 1: Write failing tests for CLI dispatch**

Add to end of `test_read.py`:

```python
import subprocess
import sys

READ_SCRIPT = Path(__file__).parent.parent / "scripts" / "ticket_read.py"


class TestReadCLI:
    def test_list_subcommand_returns_json(self, tmp_tickets):
        from tests.conftest import make_ticket
        make_ticket(tmp_tickets, "2026-03-02-first.md", id="T-20260302-01", status="open")
        result = subprocess.run(
            [sys.executable, str(READ_SCRIPT), "list", str(tmp_tickets)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["state"] == "ok"
        assert len(data["data"]["tickets"]) == 1

    def test_list_with_status_filter(self, tmp_tickets):
        from tests.conftest import make_ticket
        make_ticket(tmp_tickets, "2026-03-02-open.md", id="T-20260302-01", status="open")
        make_ticket(tmp_tickets, "2026-03-02-blocked.md", id="T-20260302-02", status="blocked")
        result = subprocess.run(
            [sys.executable, str(READ_SCRIPT), "list", str(tmp_tickets), "--status", "open"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data["data"]["tickets"]) == 1
        assert data["data"]["tickets"][0]["id"] == "T-20260302-01"

    def test_query_subcommand_fuzzy_match(self, tmp_tickets):
        from tests.conftest import make_ticket
        make_ticket(tmp_tickets, "2026-03-02-auth-bug.md", id="T-20260302-01", title="Fix auth bug")
        result = subprocess.run(
            [sys.executable, str(READ_SCRIPT), "query", str(tmp_tickets), "T-20260302"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["state"] == "ok"
        assert len(data["data"]["tickets"]) >= 1

    def test_unknown_subcommand_exits_1(self, tmp_tickets):
        result = subprocess.run(
            [sys.executable, str(READ_SCRIPT), "bogus", str(tmp_tickets)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1

    def test_missing_args_exits_1(self):
        result = subprocess.run(
            [sys.executable, str(READ_SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1

    def test_list_nonexistent_dir_returns_empty(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(READ_SCRIPT), "list", str(tmp_path / "nope")],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["data"]["tickets"] == []
```

Add `import json` and `import subprocess` and `import sys` to test file imports if not already present.

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_read.py::TestReadCLI -v`
Expected: FAIL — `ticket_read.py` has no `__main__` block.

**Step 3: Implement CLI block**

Append to `ticket_read.py` after the `fuzzy_match_id` function:

```python
def _ticket_to_dict(ticket: ParsedTicket) -> dict:
    """Convert ParsedTicket to JSON-serializable dict."""
    return {
        "id": ticket.id,
        "title": ticket.title,
        "date": ticket.date,
        "status": ticket.status,
        "priority": ticket.priority,
        "tags": ticket.tags,
        "blocked_by": ticket.blocked_by,
        "blocks": ticket.blocks,
        "path": str(ticket.path),
    }


def main() -> None:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Ticket read operations")
    subparsers = parser.add_subparsers(dest="subcommand")

    list_p = subparsers.add_parser("list")
    list_p.add_argument("tickets_dir", type=Path)
    list_p.add_argument("--status", default=None)
    list_p.add_argument("--priority", default=None)
    list_p.add_argument("--tag", default=None)
    list_p.add_argument("--include-closed", action="store_true")

    query_p = subparsers.add_parser("query")
    query_p.add_argument("tickets_dir", type=Path)
    query_p.add_argument("search_term")
    query_p.add_argument("--fuzzy", action="store_true", default=True)

    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    if args.subcommand == "list":
        tickets = list_tickets(args.tickets_dir, include_closed=args.include_closed)
        tickets = filter_tickets(
            tickets, status=args.status, priority=args.priority, tag=args.tag,
        )
        print(json.dumps({
            "state": "ok",
            "data": {"tickets": [_ticket_to_dict(t) for t in tickets]},
        }))

    elif args.subcommand == "query":
        all_tickets = list_tickets(args.tickets_dir, include_closed=True)
        matches = fuzzy_match_id(all_tickets, args.search_term)
        print(json.dumps({
            "state": "ok",
            "data": {"tickets": [_ticket_to_dict(t) for t in matches]},
        }))


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_read.py::TestReadCLI -v`
Expected: All 6 PASS.

**Step 5: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest`
Expected: 318+ tests pass, no regressions.

**Step 6: Commit**

```
git add packages/plugins/ticket/scripts/ticket_read.py packages/plugins/ticket/tests/test_read.py
git commit -m "feat(ticket): add CLI block to ticket_read.py for list/query"
```

---

### Task 2: `ticket_triage.py` CLI block

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_triage.py:243` (append after line 243)
- Test: `packages/plugins/ticket/tests/test_triage.py`

**Step 1: Write failing tests for triage CLI**

Add to end of `test_triage.py`:

```python
import subprocess
import sys

TRIAGE_SCRIPT = Path(__file__).parent.parent / "scripts" / "ticket_triage.py"


class TestTriageCLI:
    def test_dashboard_subcommand_returns_json(self, tmp_tickets):
        result = subprocess.run(
            [sys.executable, str(TRIAGE_SCRIPT), "dashboard", str(tmp_tickets)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["state"] == "ok"
        assert "counts" in data["data"]

    def test_audit_subcommand_returns_json(self, tmp_tickets):
        result = subprocess.run(
            [sys.executable, str(TRIAGE_SCRIPT), "audit", str(tmp_tickets)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["state"] == "ok"
        assert "total_entries" in data["data"]

    def test_audit_with_days_arg(self, tmp_tickets):
        result = subprocess.run(
            [sys.executable, str(TRIAGE_SCRIPT), "audit", str(tmp_tickets), "--days", "30"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["state"] == "ok"

    def test_unknown_subcommand_exits_1(self, tmp_tickets):
        result = subprocess.run(
            [sys.executable, str(TRIAGE_SCRIPT), "bogus", str(tmp_tickets)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1

    def test_missing_args_exits_1(self):
        result = subprocess.run(
            [sys.executable, str(TRIAGE_SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_triage.py::TestTriageCLI -v`
Expected: FAIL.

**Step 3: Implement CLI block**

Append to `ticket_triage.py` after `triage_orphan_detection`:

```python
def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Ticket triage operations")
    subparsers = parser.add_subparsers(dest="subcommand")

    dash_p = subparsers.add_parser("dashboard")
    dash_p.add_argument("tickets_dir", type=Path)

    audit_p = subparsers.add_parser("audit")
    audit_p.add_argument("tickets_dir", type=Path)
    audit_p.add_argument("--days", type=int, default=7)

    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    if args.subcommand == "dashboard":
        result = triage_dashboard(args.tickets_dir)
        print(json.dumps({"state": "ok", "data": result}))

    elif args.subcommand == "audit":
        result = triage_audit_report(args.tickets_dir, days=args.days)
        print(json.dumps({"state": "ok", "data": result}))


if __name__ == "__main__":
    main()
```

Note: `json` is already imported at the top of the file.

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_triage.py::TestTriageCLI -v`
Expected: All 5 PASS.

**Step 5: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest`
Expected: 318+ tests pass.

**Step 6: Commit**

```
git add packages/plugins/ticket/scripts/ticket_triage.py packages/plugins/ticket/tests/test_triage.py
git commit -m "feat(ticket): add CLI block to ticket_triage.py for dashboard/audit"
```

---

### Task 3: Guard hook allowlist expansion

**Files:**
- Modify: `packages/plugins/ticket/hooks/ticket_engine_guard.py`
- Test: `packages/plugins/ticket/tests/test_hook.py`

**Step 1: Write failing tests for read/triage allowlist branches**

Add to `test_hook.py`:

```python
class TestReadAllowlist:
    def test_read_list_allowed(self, fake_plugin_root):
        result = run_hook(
            make_hook_input(
                f"python3 {fake_plugin_root}/scripts/ticket_read.py list /tmp/tickets",
                plugin_root=fake_plugin_root,
            ),
            plugin_root=fake_plugin_root,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"

    def test_read_query_allowed(self, fake_plugin_root):
        result = run_hook(
            make_hook_input(
                f"python3 {fake_plugin_root}/scripts/ticket_read.py query /tmp/tickets T-20260302",
                plugin_root=fake_plugin_root,
            ),
            plugin_root=fake_plugin_root,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"

    def test_read_no_payload_injection(self, fake_plugin_root, tmp_path):
        """Read commands should pass through without modifying any files."""
        result = run_hook(
            make_hook_input(
                f"python3 {fake_plugin_root}/scripts/ticket_read.py list /tmp/tickets",
                plugin_root=fake_plugin_root,
            ),
            plugin_root=fake_plugin_root,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"
        assert "validated (read-only)" in decision.get("permissionDecisionReason", "")


class TestTriageAllowlist:
    def test_triage_dashboard_allowed(self, fake_plugin_root):
        result = run_hook(
            make_hook_input(
                f"python3 {fake_plugin_root}/scripts/ticket_triage.py dashboard /tmp/tickets",
                plugin_root=fake_plugin_root,
            ),
            plugin_root=fake_plugin_root,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"

    def test_triage_audit_allowed(self, fake_plugin_root):
        result = run_hook(
            make_hook_input(
                f"python3 {fake_plugin_root}/scripts/ticket_triage.py audit /tmp/tickets --days 30",
                plugin_root=fake_plugin_root,
            ),
            plugin_root=fake_plugin_root,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"

    def test_triage_no_payload_injection(self, fake_plugin_root):
        result = run_hook(
            make_hook_input(
                f"python3 {fake_plugin_root}/scripts/ticket_triage.py dashboard /tmp/tickets",
                plugin_root=fake_plugin_root,
            ),
            plugin_root=fake_plugin_root,
        )
        decision = result.get("hookSpecificOutput", {})
        assert "validated (read-only)" in decision.get("permissionDecisionReason", "")


class TestExecutionShapeMatching:
    def test_cat_ticket_file_passes_through(self, fake_plugin_root):
        """cat/rg/wc on ticket files should NOT be caught by allowlist."""
        result = run_hook(
            make_hook_input(
                f"cat {fake_plugin_root}/scripts/ticket_triage.py",
                plugin_root=fake_plugin_root,
            ),
            plugin_root=fake_plugin_root,
        )
        # Should pass through (empty dict = no opinion)
        assert result == {} or result.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_unknown_ticket_script_denied(self, fake_plugin_root):
        result = run_hook(
            make_hook_input(
                f"python3 {fake_plugin_root}/scripts/ticket_evil.py attack",
                plugin_root=fake_plugin_root,
            ),
            plugin_root=fake_plugin_root,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "deny"
```

Check if `fake_plugin_root` fixture already exists in conftest or test_hook.py — if not, use `tmp_path` and adjust accordingly.

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_hook.py::TestReadAllowlist tests/test_hook.py::TestTriageAllowlist tests/test_hook.py::TestExecutionShapeMatching -v`
Expected: FAIL — current hook doesn't match read/triage patterns.

**Step 3: Implement guard hook changes**

Modify `ticket_engine_guard.py`:

1. Change the substring check at line 160 from `"ticket_engine" not in command` to match all ticket scripts:

```python
# Non-ticket commands pass through.
if not _is_ticket_command(command, _plugin_root()):
    print("{}")
    return
```

2. Add a helper function and read-only pattern builder:

```python
def _build_readonly_pattern(plugin_root: str) -> re.Pattern[str]:
    """Build pattern for read-only ticket scripts (no payload injection)."""
    escaped = re.escape(plugin_root)
    return re.compile(
        rf"^python3\s+{escaped}/scripts/ticket_(read|triage)\.py\s+(\w+)\s+(.+)$"
    )


def _is_ticket_command(command: str, plugin_root: str) -> bool:
    """Check if command invokes any ticket plugin script."""
    escaped = re.escape(plugin_root)
    return bool(re.search(rf"{escaped}/scripts/ticket_", command))
```

3. Add a read-only allowlist check before the engine allowlist check in `main()`. After the shell metacharacter check, before the engine pattern match:

```python
# Check read-only scripts first (no payload injection needed).
readonly_pattern = _build_readonly_pattern(plugin_root)
readonly_match = readonly_pattern.match(command)
if readonly_match:
    print(json.dumps(_make_allow(
        f"Ticket {readonly_match.group(1)}/{readonly_match.group(2)} validated (read-only)"
    )))
    return
```

4. If neither read-only nor engine pattern matches, deny:

```python
if not match:
    print(json.dumps(_make_deny(
        f"Command does not match ticket allowlist. Got: {command!r:.100}"
    )))
    return
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_hook.py -v`
Expected: All hook tests PASS (existing + new).

**Step 5: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest`
Expected: 318+ tests pass.

**Step 6: Commit**

```
git add packages/plugins/ticket/hooks/ticket_engine_guard.py packages/plugins/ticket/tests/test_hook.py
git commit -m "feat(ticket): expand guard hook with read/triage allowlist branches"
```

---

### Task 4: `/ticket` SKILL.md

**Files:**
- Create: `packages/plugins/ticket/skills/ticket/SKILL.md`
- Create: `packages/plugins/ticket/skills/ticket/references/pipeline-guide.md`

**Step 1: Create skill directory**

```bash
mkdir -p packages/plugins/ticket/skills/ticket/references
```

**Step 2: Write SKILL.md**

Create `packages/plugins/ticket/skills/ticket/SKILL.md`. Target ~250 lines. Must include:

- Frontmatter with `name: ticket`, `disable-model-invocation: true`, `allowed-tools`, `argument-hint`
- Description with trigger phrases (inline string, no `>-`)
- Routing table (6 operations → 2 execution paths)
- Mutation flow: extract → confirm → pipeline → handle response
- Confirmation gate UX
- Read operation flow: direct `ticket_read.py` calls
- Response state handling table (ok_create, need_fields, duplicate_candidate, etc.)
- Reference to `references/pipeline-guide.md` for detailed schemas
- Use imperative/infinitive form (not second person)
- Use `${CLAUDE_PLUGIN_ROOT}` for script paths

Content reference: `docs/plans/2026-03-05-m9-skill-layer-design.md` sections "Routing", "Mutation Flow", "Confirmation Gate".

Engine CLI pattern: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_user.py <subcommand> <payload.json>`
Read CLI pattern: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_read.py <subcommand> <tickets_dir> [args]`

Payload file: write to `/tmp/ticket_payload_<random>.json` via Write tool.

**Step 3: Write pipeline-guide.md**

Create `packages/plugins/ticket/skills/ticket/references/pipeline-guide.md`. Contains:

- Per-operation payload schemas (create, update, close, reopen) with all fields and types
- Field defaults and optionality
- `need_fields` loop: which fields to ask for, how to re-run from plan
- `duplicate_candidate` loop: how to present the match, dedup_override payload
- Exit code meanings (0, 1, 2)
- Response state → UX mapping table (all 15 machine states)
- Key file fields disambiguation (`key_file_paths` vs `key_files`)
- Example payloads for each operation

Content reference: `packages/plugins/ticket/references/ticket-contract.md` (schema, states, error codes).

**Step 4: Remove .gitkeep**

```bash
rm packages/plugins/ticket/skills/.gitkeep
```

**Step 5: Verify skill structure**

```bash
ls -la packages/plugins/ticket/skills/ticket/
# Expected: SKILL.md, references/
ls -la packages/plugins/ticket/skills/ticket/references/
# Expected: pipeline-guide.md
```

**Step 6: Commit**

```
git add packages/plugins/ticket/skills/ticket/
git commit -m "feat(ticket): add /ticket skill with pipeline guide"
```

---

### Task 5: `/ticket-triage` SKILL.md

**Files:**
- Create: `packages/plugins/ticket/skills/ticket-triage/SKILL.md`

**Step 1: Create skill directory**

```bash
mkdir -p packages/plugins/ticket/skills/ticket-triage
```

**Step 2: Write SKILL.md**

Create `packages/plugins/ticket/skills/ticket-triage/SKILL.md`. Target ~80 lines. Must include:

- Frontmatter with `name: ticket-triage`, `allowed-tools: [Bash, Read]`
- Description with trigger phrases (inline string)
- No `disable-model-invocation` (proactive, auto-invocable)
- Procedure: run dashboard, run audit, format report, add opinionated analysis
- CLI patterns: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_triage.py dashboard <tickets_dir>` and `audit`
- `<tickets_dir>` resolution: `git rev-parse --show-toplevel` + `/docs/tickets`
- Use imperative/infinitive form

**Step 3: Commit**

```
git add packages/plugins/ticket/skills/ticket-triage/
git commit -m "feat(ticket): add /ticket-triage skill"
```

---

### Task 6: Plugin manifest version bump

**Files:**
- Modify: `packages/plugins/ticket/.claude-plugin/plugin.json`

**Step 1: Bump version**

Change `"version": "1.0.0"` to `"version": "1.1.0"`.

**Step 2: Commit**

```
git add packages/plugins/ticket/.claude-plugin/plugin.json
git commit -m "chore(ticket): bump plugin version to 1.1.0 for M9 skill layer"
```

---

### Task 7: Ruff + full test suite

**Step 1: Run ruff**

```bash
cd packages/plugins/ticket && uv run ruff check .
```

Fix any violations. Run `uv run ruff check --fix .` for auto-fixable issues.

**Step 2: Run full test suite**

```bash
cd packages/plugins/ticket && uv run pytest -v
```

Expected: 318+ tests pass (original 318 + new CLI and hook tests).

**Step 3: Commit any fixes**

```
git commit -am "style(ticket): fix lint violations"
```

---

### Task 8: M9 gate verification (manual)

Run through the gate checklist from the design doc. This is manual testing in a live Claude Code session with the plugin installed.

| # | Check | Status |
|---|-------|--------|
| 1 | `/ticket create` works | |
| 2 | `/ticket list` works | |
| 3 | `/ticket update` works | |
| 4 | `/ticket close` works | |
| 5 | `/ticket reopen` works | |
| 6 | `/ticket-triage` works | |
| 7 | `/ticket-triage` auto-invokes | |
| 8 | Guard hook allows read/triage | |
| 9 | Guard hook blocks unknown scripts | |
| 10 | `need_fields` loop works | |
| 11 | `duplicate_candidate` loop works | |
| 12 | Confirmation gate works | |
| 13 | Plugin skill namespacing resolved | |
| 14 | All tests pass | |
| 15 | Ruff clean | |
| 16 | Version at 1.1.0 | |

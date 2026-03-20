# M9 Skill Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the ticket engine to Claude Code's skill system with `/ticket` (mutation) and `/ticket-triage` (read-only) skills.

**Architecture:** Fully inline execution. `/ticket` routes 6 operations (create/update/close/reopen/list/query) — mutations go through the 4-stage engine pipeline via user entrypoint, read ops call `ticket_read.py` directly. `/ticket-triage` wraps `ticket_triage.py`. Guard hook expanded with read/triage allowlist branches.

**Tech Stack:** Python 3.11+, pytest, SKILL.md (YAML frontmatter + markdown)

**Design doc:** `docs/plans/2026-03-05-m9-skill-layer-design.md`

**Adversarial review (2026-03-05):** Codex dialogue (thread `019cbc9b-b2bf-7bc3-9103-4d3cddda3838`, adversarial, 6/10 turns, converged) found 28 issues (4 P0, 5 P1, 15 P2, 4 P3). All P0/P1 fixes integrated into tasks below.

| ID | Sev | Finding | Fix Location |
|----|-----|---------|--------------|
| F08 | P0 | `${CLAUDE_PLUGIN_ROOT}` triggers guard `$` metachar deny before allowlist | T4, T5: resolve to absolute path first |
| F09 | P0 | `/tmp` payload breaks guard workspace containment check | T4: use workspace-relative payload path |
| F10 | P0 | Plan's `_is_ticket_command` broadens false-denial surface — security regression | T3: 4-branch hook redesign |
| F21 | P0 | Pipeline payload evolution between classify/plan/preflight/execute unspecified | T4: add state propagation to pipeline-guide |
| F01 | P1 | `_ticket_to_dict` references `ticket.title` — `ParsedTicket` has no `title` field | T1: remove title from dict |
| F02 | P1 | `fake_plugin_root` fixture does not exist in test infrastructure | T3: use `"/fake/plugin"` constant |
| F07 | P1 | `ticket_read.py` needs `sys.path` bootstrap for standalone CLI execution | T1: add bootstrap before module imports |
| F12 | P1 | argparse exits code 2 for unknown subcommands, tests expect 1 | T1, T2: fix assertions |
| F13 | P1 | Test uses `Path(...)` without `from pathlib import Path` | T1: add import |

---

### Task 1: `ticket_read.py` CLI block

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_read.py` (add sys.path bootstrap at top + append CLI block after line 89)
- Test: `packages/plugins/ticket/tests/test_read.py`

**Step 1: Write failing tests for CLI dispatch**

Add to end of `test_read.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

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

    def test_unknown_subcommand_exits_2(self, tmp_tickets):
        """argparse exits 2 for invalid subcommand choice, not 1."""
        result = subprocess.run(
            [sys.executable, str(READ_SCRIPT), "bogus", str(tmp_tickets)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 2

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

Add `import json`, `import subprocess`, `import sys`, and `from pathlib import Path` to test file imports if not already present.

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_read.py::TestReadCLI -v`
Expected: FAIL — `ticket_read.py` has no `__main__` block.

**Step 3: Implement changes to `ticket_read.py`**

**3a. Add sys.path bootstrap** (insert after `from pathlib import Path`, before `from scripts.ticket_parse`):

```python
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
```

This is required because `from scripts.ticket_parse import ...` fails when the script is invoked standalone via `python3 ticket_read.py` — the package root isn't on `sys.path`. Pattern matches `ticket_engine_user.py:14`.

**3b. Append CLI block** after the `fuzzy_match_id` function:

```python
def _ticket_to_dict(ticket: ParsedTicket) -> dict:
    """Convert ParsedTicket to JSON-serializable dict.

    Note: ParsedTicket has no `title` field. Title lives in the markdown
    heading (# ID: Title), not in the dataclass. Omitted from CLI output.
    """
    return {
        "id": ticket.id,
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

    def test_unknown_subcommand_exits_2(self, tmp_tickets):
        """argparse exits 2 for invalid subcommand choice, not 1."""
        result = subprocess.run(
            [sys.executable, str(TRIAGE_SCRIPT), "bogus", str(tmp_tickets)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 2

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

Note: `ticket_triage.py` uses only stdlib imports (json, re, datetime, pathlib) — no `sys.path` bootstrap needed (unlike `ticket_read.py` which imports from `scripts.ticket_parse`).

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

Add to `test_hook.py`. Uses the existing `"/fake/plugin"` default from `make_hook_input` — no fixture needed (F02 fix):

```python
FAKE_ROOT = "/fake/plugin"


class TestReadAllowlist:
    def test_read_list_allowed(self):
        result = run_hook(
            make_hook_input(
                f"python3 {FAKE_ROOT}/scripts/ticket_read.py list /tmp/tickets",
            ),
            plugin_root=FAKE_ROOT,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"

    def test_read_query_allowed(self):
        result = run_hook(
            make_hook_input(
                f"python3 {FAKE_ROOT}/scripts/ticket_read.py query /tmp/tickets T-20260302",
            ),
            plugin_root=FAKE_ROOT,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"

    def test_read_no_payload_injection(self):
        """Read commands should pass through without modifying any files."""
        result = run_hook(
            make_hook_input(
                f"python3 {FAKE_ROOT}/scripts/ticket_read.py list /tmp/tickets",
            ),
            plugin_root=FAKE_ROOT,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"
        assert "validated (read-only)" in decision.get("permissionDecisionReason", "")


class TestTriageAllowlist:
    def test_triage_dashboard_allowed(self):
        result = run_hook(
            make_hook_input(
                f"python3 {FAKE_ROOT}/scripts/ticket_triage.py dashboard /tmp/tickets",
            ),
            plugin_root=FAKE_ROOT,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"

    def test_triage_audit_allowed(self):
        result = run_hook(
            make_hook_input(
                f"python3 {FAKE_ROOT}/scripts/ticket_triage.py audit /tmp/tickets --days 30",
            ),
            plugin_root=FAKE_ROOT,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "allow"

    def test_triage_no_payload_injection(self):
        result = run_hook(
            make_hook_input(
                f"python3 {FAKE_ROOT}/scripts/ticket_triage.py dashboard /tmp/tickets",
            ),
            plugin_root=FAKE_ROOT,
        )
        decision = result.get("hookSpecificOutput", {})
        assert "validated (read-only)" in decision.get("permissionDecisionReason", "")


class TestExecutionShapeMatching:
    def test_cat_ticket_file_passes_through(self):
        """Non-python commands on ticket files pass through (empty JSON)."""
        result = run_hook(
            make_hook_input(
                f"cat {FAKE_ROOT}/scripts/ticket_triage.py",
            ),
            plugin_root=FAKE_ROOT,
        )
        # cat is not a python invocation — passes through as empty dict
        assert result == {}

    def test_rg_ticket_file_passes_through(self):
        """rg/grep on ticket files pass through."""
        result = run_hook(
            make_hook_input(
                f"rg ticket_engine {FAKE_ROOT}/scripts/ticket_engine_core.py",
            ),
            plugin_root=FAKE_ROOT,
        )
        assert result == {}

    def test_unknown_ticket_script_denied(self):
        """Python invocation of an unrecognized ticket script is denied."""
        result = run_hook(
            make_hook_input(
                f"python3 {FAKE_ROOT}/scripts/ticket_evil.py attack",
            ),
            plugin_root=FAKE_ROOT,
        )
        decision = result.get("hookSpecificOutput", {})
        assert decision.get("permissionDecision") == "deny"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_hook.py::TestReadAllowlist tests/test_hook.py::TestTriageAllowlist tests/test_hook.py::TestExecutionShapeMatching -v`
Expected: FAIL — current hook doesn't match read/triage patterns.

**Step 3: Implement 4-branch guard hook (F10 fix)**

Modify `ticket_engine_guard.py`. The redesign replaces the substring check at line 160 with a 4-branch structure:

1. Engine exact allowlist → allow + payload injection (existing behavior)
2. Read-only exact allowlist → allow, no injection (new)
3. Python invocation of unrecognized ticket script → deny (new — catches `ticket_evil.py`)
4. Everything else → passthrough (non-python commands like `cat`, `rg`, `wc`)

**3a. Add helper functions** (after `_build_allowlist_pattern`, before `_make_allow`):

```python
def _build_readonly_pattern(plugin_root: str) -> re.Pattern[str]:
    """Build pattern for read-only ticket scripts (no payload injection)."""
    escaped = re.escape(plugin_root)
    return re.compile(
        rf"^python3\s+{escaped}/scripts/ticket_(read|triage)\.py\s+(\w+)\s+(.+)$"
    )


def _is_ticket_invocation(command: str, plugin_root: str) -> bool:
    """Check if command is a Python invocation of any ticket plugin script.

    Only matches `python3 <root>/scripts/ticket_*.py ...` — NOT non-python
    commands like `cat`, `rg`, or `wc` that happen to reference ticket files.
    This distinction is critical: non-python commands pass through (branch 4),
    while unrecognized ticket script invocations are denied (branch 3).
    """
    escaped = re.escape(plugin_root)
    return bool(re.match(rf"^python3\s+{escaped}/scripts/ticket_\w+\.py\b", command))
```

**3b. Replace the substring check** at line 160. Change:

```python
    # Non-ticket commands pass through.
    if "ticket_engine" not in command:
        print("{}")
        return
```

To:

```python
    # Non-ticket-script invocations pass through (branch 4).
    plugin_root = _plugin_root()
    if not _is_ticket_invocation(command, plugin_root):
        print("{}")
        return
```

**3c. Move `plugin_root = _plugin_root()` up** — it's now used in the gate check (3b) before the metachar check. Remove the duplicate `plugin_root = _plugin_root()` that was at line 174.

**3d. Add readonly check** after the engine allowlist check. After the existing `if not match: deny` block, add:

```python
    # Branch 1 handled above (engine allowlist → allow + inject).
    # If engine didn't match, try read-only allowlist.

    # Branch 2: Read-only scripts (no payload injection needed).
    readonly_pattern = _build_readonly_pattern(plugin_root)
    readonly_match = readonly_pattern.match(command)
    if readonly_match:
        print(json.dumps(_make_allow(
            f"Ticket {readonly_match.group(1)}/{readonly_match.group(2)} validated (read-only)"
        )))
        return

    # Branch 3: Unrecognized ticket script invocation → deny.
    print(json.dumps(_make_deny(
        f"Command invokes unrecognized ticket script. Got: {command!r:.100}"
    )))
    return
```

**3e. Restructure the engine match block** — change `if not match: deny; return` to just `if match:` with the existing validation+injection logic inside. Then fall through to the readonly check (3d) if engine doesn't match. The full flow in main() after metachar check:

```python
    # Branch 1: Engine exact allowlist → allow + inject.
    engine_pattern = _build_allowlist_pattern(plugin_root)
    engine_match = engine_pattern.match(command)
    if engine_match:
        entrypoint_type = engine_match.group(1)
        subcommand = engine_match.group(2)
        payload_path = engine_match.group(3)

        if subcommand not in VALID_SUBCOMMANDS:
            print(json.dumps(_make_deny(...)))
            return
        if re.search(r"\s", payload_path):
            print(json.dumps(_make_deny(...)))
            return
        # ... existing payload path validation + injection ...
        print(json.dumps(_make_allow(...)))
        return

    # Branch 2: Read-only scripts → allow (no injection).
    readonly_pattern = _build_readonly_pattern(plugin_root)
    readonly_match = readonly_pattern.match(command)
    if readonly_match:
        print(json.dumps(_make_allow(
            f"Ticket {readonly_match.group(1)}/{readonly_match.group(2)} validated (read-only)"
        )))
        return

    # Branch 3: Unrecognized ticket script → deny.
    print(json.dumps(_make_deny(
        f"Command invokes unrecognized ticket script. Got: {command!r:.100}"
    )))
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
git commit -m "feat(ticket): redesign guard hook with 4-branch allowlist (read/triage/deny/passthrough)"
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

**Path resolution (F08 fix):** SKILL.md must NOT use `${CLAUDE_PLUGIN_ROOT}` in Bash commands — the guard hook's `SHELL_METACHAR_RE` blocks `$` before reaching the allowlist. Instead, SKILL.md must instruct Claude to:
1. Resolve the plugin root first: `PLUGIN_ROOT=$(echo $CLAUDE_PLUGIN_ROOT)`
2. Use the resolved absolute path in all subsequent commands

Example resolution block for SKILL.md:
```
## Setup
Run once at skill start to resolve the plugin root:
\`\`\`bash
echo $CLAUDE_PLUGIN_ROOT
\`\`\`
Store the output as the resolved plugin root path. Use this absolute path
(not the env var) in all subsequent Bash commands.
```

Content reference: `docs/plans/2026-03-05-m9-skill-layer-design.md` sections "Routing", "Mutation Flow", "Confirmation Gate".

Engine CLI pattern: `python3 <resolved_plugin_root>/scripts/ticket_engine_user.py <subcommand> <payload.json>`
Read CLI pattern: `python3 <resolved_plugin_root>/scripts/ticket_read.py <subcommand> <tickets_dir> [args]`

**Payload location (F09 fix):** Payload file must be workspace-relative, NOT `/tmp`. The guard hook's `_resolve_payload_path` enforces workspace containment — `/tmp` is outside the workspace root and will be denied. Write payload to `<project_root>/.claude/ticket-tmp/payload_<random>.json` via Write tool. Create the directory first if it doesn't exist. Add `.claude/ticket-tmp/` to `.gitignore`.

**Step 3: Write pipeline-guide.md**

Create `packages/plugins/ticket/skills/ticket/references/pipeline-guide.md`. Contains:

- Per-operation payload schemas (create, update, close, reopen) with all fields and types
- Field defaults and optionality
- `need_fields` loop: which fields to ask for, how to re-run from plan
- `duplicate_candidate` loop: how to present the match, dedup_override payload
- Exit code meanings (0, 1, 2)
- Response state → UX mapping table (all 15 machine states, including reserved `merge_into_existing`)
- Key file fields disambiguation (`key_file_paths` vs `key_files`)
- Example payloads for each operation
- **Pipeline state propagation (F21 fix):** Document how output from each stage feeds into the next. The 4 stages are not independent — each takes a payload file, but the skill must know:
  - What fields `classify` adds to the payload (operation type, confidence)
  - Whether `plan` reads the classify output or the original payload
  - What `preflight` checks depend on (plan output? classify output?)
  - Whether `execute` needs a fresh payload or the enriched one from prior stages
  - How to handle re-running from `plan` after `need_fields` (does the payload need classify fields?)
  Read `ticket_engine_core.py` during implementation to trace the actual data flow between `engine_classify` → `engine_plan` → `engine_preflight` → `engine_execute`. Document what each stage reads and writes.

Content reference: `packages/plugins/ticket/references/ticket-contract.md` (schema, states, error codes).

**Step 4: Remove .gitkeep**

```bash
trash packages/plugins/ticket/skills/.gitkeep
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
- CLI patterns: `python3 <resolved_plugin_root>/scripts/ticket_triage.py dashboard <tickets_dir>` and `audit` (same F08 path resolution as `/ticket` — resolve `CLAUDE_PLUGIN_ROOT` first, use the absolute path)
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
| 8 | Guard hook allows read/triage (branch 2) | |
| 9 | Guard hook blocks unknown ticket scripts (branch 3) | |
| 10 | Guard hook passes through `cat`/`rg`/`wc` on ticket files (branch 4) | |
| 11 | `need_fields` loop works | |
| 12 | `duplicate_candidate` loop works | |
| 13 | Confirmation gate works | |
| 14 | Plugin skill namespacing resolved (`/ticket` vs `/ticket:ticket`) | |
| 15 | Commands use resolved absolute path, not `${CLAUDE_PLUGIN_ROOT}` (F08) | |
| 16 | Payload written to workspace-relative path, not `/tmp` (F09) | |
| 17 | All tests pass | |
| 18 | Ruff clean | |
| 19 | Version at 1.1.0 | |

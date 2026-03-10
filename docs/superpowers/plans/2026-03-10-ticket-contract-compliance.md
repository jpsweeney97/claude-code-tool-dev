# Ticket Plugin Contract Compliance Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 10 contract compliance findings (C-001 through C-010) plus 3 emerged findings from Codex dialogue, organized into 5 PRs by dependency order.

**Architecture:** Each PR is a self-contained fix cluster. PR 1 unblocks archive flow (smallest blast radius). PR 2 adds write-path invariants. PR 3 fixes dedup correctness. PR 4 hardens validation. PR 5 aligns contract documentation. All changes are in `packages/plugins/ticket/`.

**Tech Stack:** Python 3.14, pytest, uv (package manager). All paths relative to `packages/plugins/ticket/`.

**Source documents:**
- Contract: `references/ticket-contract.md`
- Engine: `scripts/ticket_engine_core.py` (1915 lines)
- Validator: `scripts/ticket_validate.py` (96 lines)
- Reader: `scripts/ticket_read.py` (173 lines)
- Runner: `scripts/ticket_engine_runner.py`
- Parser: `scripts/ticket_parse.py` (generation detection, `ParsedTicket.generation` field)
- ID utils: `scripts/ticket_id.py` (`is_legacy_id()` at line 113)

**Test support:** `tests/support/builders.py` (existing: `make_ticket`, `make_gen1_ticket`, etc.). Add helpers for closed-ticket and legacy-ticket creation as needed.

**Test runner:** `cd packages/plugins/ticket && uv run pytest tests/ -v`

---

## Chunk 1: PR 1 — Blocker Resolution + Dedup Scan Scope (C-003 + emerged)

### File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/ticket_engine_core.py` | Modify | Replace 4 `list_tickets()` calls with `_list_tickets_with_closed()` helper |
| `tests/test_blocker_resolution.py` | Create | Tests for archived blocker resolution |
| `tests/test_plan.py` | Modify | Add test for dedup scan including archived tickets |

### Task 1: Extract blocker-resolution helper

The root cause of C-003 is that 4 call sites in `ticket_engine_core.py` call `list_tickets(tickets_dir)` without `include_closed=True`. Archived done/wontfix tickets are invisible to blocker resolution, causing them to appear "missing." The fix is a single helper function that all blocker-resolution paths use.

**Files:**
- Create: `tests/test_blocker_resolution.py`
- Modify: `scripts/ticket_engine_core.py:700-704`, `:938-943`, `:1660-1665`

- [ ] **Step 1: Write failing test — archived done blocker should resolve**

```python
# tests/test_blocker_resolution.py
"""Tests for blocker resolution including archived tickets (C-003)."""
import pytest
from pathlib import Path
from scripts.ticket_engine_core import _classify_blockers


def _make_ticket(id: str, status: str):
    """Minimal ticket-like object for _classify_blockers."""
    class T:
        pass
    t = T()
    t.id = id
    t.status = status
    return t


def test_archived_done_blocker_is_resolved():
    """C-003: A done blocker in closed-tickets/ should not appear as missing."""
    ticket_map = {
        "T-20260301-01": _make_ticket("T-20260301-01", "done"),
    }
    missing, unresolved = _classify_blockers(["T-20260301-01"], ticket_map)
    assert missing == []
    assert unresolved == []


def test_archived_wontfix_blocker_is_resolved():
    """C-003: A wontfix blocker in closed-tickets/ should not appear as missing."""
    ticket_map = {
        "T-20260301-02": _make_ticket("T-20260301-02", "wontfix"),
    }
    missing, unresolved = _classify_blockers(["T-20260301-02"], ticket_map)
    assert missing == []
    assert unresolved == []


def test_truly_missing_blocker_still_detected():
    """Regression: a blocker ID not in any directory should still be missing."""
    ticket_map = {}
    missing, unresolved = _classify_blockers(["T-NONEXISTENT"], ticket_map)
    assert missing == ["T-NONEXISTENT"]


def test_unresolved_blocker_still_detected():
    """Regression: an open blocker should still be unresolved."""
    ticket_map = {
        "T-20260301-03": _make_ticket("T-20260301-03", "in_progress"),
    }
    missing, unresolved = _classify_blockers(["T-20260301-03"], ticket_map)
    assert unresolved == ["T-20260301-03"]
```

- [ ] **Step 2: Run test to verify it passes (these test _classify_blockers directly, which already works correctly with the right ticket_map)**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_blocker_resolution.py -v`
Expected: PASS (4 tests) — `_classify_blockers` itself is correct; the bug is in the callers not passing archived tickets into the map.

- [ ] **Step 3: Write integration test — blocker resolution through preflight with archived ticket**

Add to `tests/test_blocker_resolution.py`:

```python
def test_preflight_close_with_archived_blocker(tmp_path):
    """C-003 integration: close preflight should see archived done blocker as resolved."""
    from scripts.ticket_engine_core import engine_preflight
    from tests.support.builders import make_ticket, make_closed_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)

    # Create a blocker ticket in closed-tickets/ with done status.
    blocker_id = create_closed_ticket_file(
        tickets_dir, id="T-20260301-01", status="done", title="Blocker task"
    )

    # Create a ticket that is blocked by the archived blocker.
    ticket_id = create_ticket_file(
        tickets_dir, id="T-20260310-01", status="blocked",
        blocked_by=["T-20260301-01"], title="Blocked task"
    )

    resp = engine_preflight(
        ticket_id="T-20260310-01",
        action="close",
        session_id="test-session",
        request_origin="user",
        tickets_dir=tickets_dir,
        hook_injected=True,
        hook_request_origin="user",
    )
    # Should NOT be dependency_blocked — the blocker is done (archived).
    assert resp.state != "dependency_blocked", f"Archived done blocker should resolve, got: {resp.message}"
```

- [ ] **Step 4: Run integration test to verify it fails (confirms the bug)**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_blocker_resolution.py::test_preflight_close_with_archived_blocker -v`
Expected: FAIL — `resp.state == "dependency_blocked"` because `list_tickets()` at line 702 doesn't include closed tickets.

- [ ] **Step 5: Add `_list_tickets_with_closed` helper and fix all 4 call sites**

In `scripts/ticket_engine_core.py`, add helper near the top (after imports, before `_plan_create`):

```python
def _list_tickets_with_closed(tickets_dir: Path) -> list:
    """List all tickets including archived (closed-tickets/).

    Used by blocker resolution and dedup scanning. Single source of truth
    to prevent C-003 regression (archived tickets invisible to dependency checks).
    """
    from scripts.ticket_read import list_tickets
    return list_tickets(tickets_dir, include_closed=True)
```

Then replace these 4 call sites (two distinct bugs sharing one root cause):

**Blocker resolution (C-003) — 3 sites using local alias `_list_tickets`:**
- Line 702: `all_tickets = _list_tickets(tickets_dir)` → `all_tickets = _list_tickets_with_closed(tickets_dir)`
- Line 942: `all_tickets = _list_tickets(tickets_dir)` → `all_tickets = _list_tickets_with_closed(tickets_dir)`
- Line 1664: `all_tickets = _list_tickets(tickets_dir)` → `all_tickets = _list_tickets_with_closed(tickets_dir)`

**Dedup scan scope (emerged finding) — 1 site using top-level import:**
- Line 300: `existing = list_tickets(tickets_dir)` → `existing = _list_tickets_with_closed(tickets_dir)`

Remove the now-unnecessary local import aliases (`from scripts.ticket_read import list_tickets as _list_tickets`) at the blocker sites. Line 300 uses the top-level import from `_plan_create` — remove that import if no longer needed.

- [ ] **Step 6: Run integration test to verify it passes**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_blocker_resolution.py -v`
Expected: PASS (all tests)

- [ ] **Step 7: Write test for dedup scan including archived tickets (emerged finding)**

Add to `tests/test_plan.py`:

```python
def test_plan_create_dedup_includes_archived_tickets(tmp_path):
    """Emerged finding: dedup scan should include archived tickets within 24h window."""
    from scripts.ticket_engine_core import _plan_create
    from tests.support.builders import make_closed_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)

    # Create an archived ticket with matching problem text (within 24h window).
    create_closed_ticket_file(
        tickets_dir,
        id="T-20260310-01",
        status="done",
        title="Fix auth timeout",
        problem="Authentication handler times out for large payloads",
    )

    # Try to create a duplicate.
    resp = _plan_create(
        fields={
            "title": "Fix auth timeout",
            "problem": "Authentication handler times out for large payloads",
        },
        session_id="test-session",
        request_origin="user",
        tickets_dir=tickets_dir,
    )
    assert resp.state == "duplicate_candidate", (
        f"Should detect duplicate against archived ticket, got: {resp.state}"
    )
```

- [ ] **Step 8: Run dedup test to verify it passes (already fixed by Step 5 — line 300 now uses helper)**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_plan.py::test_plan_create_dedup_includes_archived_tickets -v`
Expected: PASS (line 300 was already fixed in Step 5)

- [ ] **Step 9: Run full test suite to verify no regressions**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 10: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_engine_core.py packages/plugins/ticket/tests/test_blocker_resolution.py packages/plugins/ticket/tests/test_plan.py
git commit -m "fix(ticket): include archived tickets in blocker resolution and dedup scan (C-003)

Archived done/wontfix tickets were invisible to blocker resolution and
dedup scanning because all 4 list_tickets() call sites defaulted to
include_closed=False. Extracted _list_tickets_with_closed() helper to
prevent regression. Also fixes emerged dedup scan scope finding."
```

---

## Chunk 2: PR 2 — Legacy Write Gate + contract_version Enforcement (C-001 + C-004)

### File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/ticket_engine_core.py` | Modify | Add generation gate in preflight/execute; make contract_version engine-owned |
| `tests/test_migration.py` | Modify | Add mutation-rejection tests for legacy tickets |
| `tests/test_execute.py` | Modify | Add contract_version enforcement tests |

### Task 2: Add legacy generation gate (C-001)

Contract §8: "Read-only for legacy formats. Conversion on update (with user confirmation)." Currently, `_execute_update`, `_execute_close`, and `_execute_reopen` mutate legacy tickets without checking `ticket.generation`.

**Files:**
- Modify: `scripts/ticket_engine_core.py:1508-1523`, `:1622-1647`, `:1778+`
- Modify: `tests/test_migration.py`

- [ ] **Step 1: Write failing test — legacy ticket update should be rejected**

Add to `tests/test_migration.py`:

```python
def test_update_rejects_legacy_gen1_ticket(tmp_path):
    """C-001: update on a Gen 1 ticket (generation < 10) should be rejected."""
    from scripts.ticket_engine_core import _execute_update
    from tests.support.builders import make_legacy_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)

    create_legacy_ticket_file(tickets_dir, generation=1, id="fix-auth-bug", title="Fix auth bug")

    resp = _execute_update(
        ticket_id="fix-auth-bug",
        fields={"priority": "high"},
        session_id="test-session",
        request_origin="user",
        tickets_dir=tickets_dir,
    )
    assert resp.state == "policy_blocked"
    assert "legacy" in resp.message.lower() or "generation" in resp.message.lower()


def test_close_rejects_legacy_gen3_ticket(tmp_path):
    """C-001: close on a Gen 3 ticket should be rejected."""
    from scripts.ticket_engine_core import _execute_close
    from tests.support.builders import make_legacy_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)

    create_legacy_ticket_file(tickets_dir, generation=3, id="T-042", title="Legacy ticket")

    resp = _execute_close(
        ticket_id="T-042",
        fields={"resolution": "done"},
        session_id="test-session",
        request_origin="user",
        tickets_dir=tickets_dir,
    )
    assert resp.state == "policy_blocked"


def test_update_allows_v10_ticket(tmp_path):
    """Regression: v1.0 tickets (generation=10) should still be updatable."""
    from scripts.ticket_engine_core import _execute_update
    from tests.support.builders import make_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)

    create_ticket_file(tickets_dir, id="T-20260310-01", title="Normal ticket")

    resp = _execute_update(
        ticket_id="T-20260310-01",
        fields={"priority": "high"},
        session_id="test-session",
        request_origin="user",
        tickets_dir=tickets_dir,
    )
    assert resp.state != "policy_blocked"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_migration.py::test_update_rejects_legacy_gen1_ticket -v`
Expected: FAIL — no generation gate exists

- [ ] **Step 3: Add generation gate helper**

In `scripts/ticket_engine_core.py`, add after the imports:

```python
_V10_GENERATION = 10  # v1.0 tickets have generation=10; legacy is 1-4.


def _check_legacy_gate(ticket) -> EngineResponse | None:
    """Reject writes to legacy-format tickets (generation < 10).

    Contract §8: Read-only for legacy formats. Conversion on update
    (with user confirmation). Until confirm-and-convert is implemented,
    all non-create writes to legacy tickets are rejected.

    Returns EngineResponse if blocked, None if allowed.
    """
    if ticket.generation < _V10_GENERATION:
        return EngineResponse(
            state="policy_blocked",
            message=(
                f"Legacy ticket (generation {ticket.generation}) is read-only. "
                f"Contract §8 requires conversion with user confirmation before mutation. "
                f"Use 'ticket migrate {ticket.id}' when available (v1.1)."
            ),
            ticket_id=ticket.id,
            error_code="policy_blocked",
        )
    return None
```

- [ ] **Step 4: Add gate to `_execute_update`, `_execute_close`, `_execute_reopen`**

In `_execute_update` (line ~1521), after `ticket = find_ticket_by_id(...)` and the None check:

```python
    legacy_block = _check_legacy_gate(ticket)
    if legacy_block is not None:
        return legacy_block
```

Same pattern in `_execute_close` (after line ~1644) and `_execute_reopen` (after the ticket lookup).

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_migration.py -v`
Expected: PASS

### Task 3: Make contract_version engine-owned (C-004)

Contract §10: "Engine reads all versions; writes latest only." Currently `contract_version` is in `_UPDATE_FRONTMATTER_KEYS` and callers can set arbitrary values.

**Files:**
- Modify: `scripts/ticket_engine_core.py:768-780`
- Modify: `tests/test_execute.py`

- [ ] **Step 6: Write failing test — update with contract_version="0.9" should be rejected or normalized**

Add to `tests/test_execute.py`:

```python
def test_update_ignores_caller_contract_version(tmp_path):
    """C-004: contract_version is engine-owned; callers cannot set it."""
    from scripts.ticket_engine_core import _execute_update
    from tests.support.builders import make_ticket
    from scripts.ticket_parse import parse_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)

    path = create_ticket_file(tickets_dir, id="T-20260310-01", title="Test ticket")

    _execute_update(
        ticket_id="T-20260310-01",
        fields={"priority": "high", "contract_version": "0.9"},
        session_id="test-session",
        request_origin="user",
        tickets_dir=tickets_dir,
    )

    ticket = parse_ticket(Path(path))
    assert ticket is not None
    assert ticket.contract_version == "1.0", (
        f"contract_version should be forced to 1.0, got {ticket.contract_version!r}"
    )
```

- [ ] **Step 7: Run test to verify it fails**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_execute.py::test_update_ignores_caller_contract_version -v`
Expected: FAIL — current code writes whatever value is supplied

- [ ] **Step 8: Remove contract_version from `_UPDATE_FRONTMATTER_KEYS` and stamp on every write**

In `scripts/ticket_engine_core.py`:

1. Remove `"contract_version"` from `_UPDATE_FRONTMATTER_KEYS` (line 778)
2. In `_execute_create`, `_execute_update`, `_execute_close`, and `_execute_reopen`, before writing, force:
   ```python
   data["contract_version"] = "1.0"
   ```

- [ ] **Step 9: Run test to verify it passes**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_execute.py::test_update_ignores_caller_contract_version -v`
Expected: PASS

- [ ] **Step 10: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v`
Expected: All pass (existing tests that set contract_version may need adjustment if they relied on pass-through)

- [ ] **Step 11: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_engine_core.py packages/plugins/ticket/tests/test_migration.py packages/plugins/ticket/tests/test_execute.py
git commit -m "fix(ticket): add legacy write gate and make contract_version engine-owned (C-001, C-004)

C-001: Reject non-create writes for tickets with generation < 10.
Contract §8 requires read-only for legacy formats until confirm-and-convert
flow is implemented.

C-004: Remove contract_version from _UPDATE_FRONTMATTER_KEYS and stamp
'1.0' on every write path. Contract §10: writes latest only."
```

---

## Chunk 3: PR 3 — Dedup Correctness (C-002 + C-008 + created_at)

### File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/ticket_engine_core.py` | Modify | Persist `key_file_paths` in YAML on create; bind `dedup_override` to `duplicate_of` |
| `scripts/ticket_render.py` | Modify | Include `key_file_paths` in rendered YAML if present |
| `references/ticket-contract.md` | Modify | Add `key_file_paths` to §3 schema; document `created_at`; amend §6 `dedup_override` wording |
| `tests/test_dedup.py` | Modify | Add canonical-data persistence tests |
| `tests/test_preflight.py` | Modify | Add dedup_override binding tests |
| `tests/test_execute.py` | Modify | Add dedup_override binding tests |

### Task 4: Persist `key_file_paths` in YAML (C-002)

The dedup system computes fingerprints from `key_file_paths` on create, but never persists the field. Later dedup scans reconstruct paths from the rendered markdown table — a lossy round-trip.

- [ ] **Step 1: Write failing test — created ticket should have `key_file_paths` in YAML**

Add to `tests/test_dedup.py`:

```python
def test_created_ticket_persists_key_file_paths(tmp_path):
    """C-002: key_file_paths should be persisted in YAML for future dedup scans."""
    from scripts.ticket_engine_core import engine_execute
    from scripts.ticket_parse import parse_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)

    resp = engine_execute(
        action="create",
        ticket_id=None,
        fields={
            "title": "Fix auth timeout",
            "problem": "Auth handler times out",
            "key_file_paths": ["handler.py", "auth/config.py"],
            "key_files": [
                {"file": "handler.py", "role": "Timeout logic", "look_for": "timeout"},
                {"file": "auth/config.py", "role": "Config", "look_for": "timeout_ms"},
            ],
        },
        session_id="test-session",
        request_origin="user",
        tickets_dir=tickets_dir,
        hook_injected=True,
        hook_request_origin="user",
        classify_intent="create",
        classify_confidence=0.9,
        dedup_fingerprint="placeholder",  # Will be recomputed
    )
    assert resp.state == "ok_create"

    ticket = parse_ticket(Path(resp.data["ticket_path"]))
    assert ticket is not None
    assert hasattr(ticket, "key_file_paths") or "key_file_paths" in ticket.frontmatter
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_dedup.py::test_created_ticket_persists_key_file_paths -v`
Expected: FAIL — `key_file_paths` not written to YAML

- [ ] **Step 3: Persist `key_file_paths` in `_execute_create` and update dedup scan to read it**

In `_execute_create`, when building the frontmatter dict, include `key_file_paths` if present in fields:

```python
if fields.get("key_file_paths"):
    frontmatter["key_file_paths"] = sorted(fields["key_file_paths"])
```

In `_plan_create` dedup scan (line ~332), prefer the persisted field over regex extraction:

```python
# Prefer persisted key_file_paths (v1.0+) over regex extraction from rendered table.
ticket_key_file_paths = ticket.frontmatter.get("key_file_paths", [])
if not ticket_key_file_paths:
    # Fallback: extract from rendered Key Files section.
    key_files_section = ticket.sections.get("Key Files", "")
    if key_files_section:
        for match in re.finditer(r"^\| ([^|]+) \|", key_files_section, re.MULTILINE):
            cell = match.group(1).strip()
            if cell and cell != "File" and not cell.startswith("-"):
                ticket_key_file_paths.append(cell)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_dedup.py::test_created_ticket_persists_key_file_paths -v`
Expected: PASS

### Task 5: Bind `dedup_override` to `duplicate_of` (C-008)

Contract §6: "Override: `dedup_override: true` with matching `ticket_id`." Current code allows override with `ticket_id=None`.

- [ ] **Step 5: Write failing test — dedup_override without ticket_id should be rejected**

Add to `tests/test_preflight.py`:

```python
def test_dedup_override_requires_duplicate_of(tmp_path):
    """C-008: dedup_override must be bound to a specific duplicate candidate."""
    from scripts.ticket_engine_core import engine_preflight
    from tests.support.builders import make_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)

    resp = engine_preflight(
        ticket_id=None,
        action="create",
        session_id="test-session",
        request_origin="user",
        tickets_dir=tickets_dir,
        hook_injected=True,
        hook_request_origin="user",
        fields={
            "title": "Duplicate task",
            "problem": "Same problem",
            "dedup_override": True,
            # No duplicate_of specified
        },
    )
    # Should reject — override without specifying which duplicate
    assert resp.state == "need_fields"
    assert "duplicate_of" in str(resp.data.get("missing_fields", []))
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_preflight.py::test_dedup_override_requires_duplicate_of -v`
Expected: FAIL — current code only checks the boolean

- [ ] **Step 7: Add `duplicate_of` binding check**

In `_plan_create` and `_execute_create`, when `dedup_override` is True, verify that `fields.get("duplicate_of")` is set and matches the detected duplicate:

```python
if fields.get("dedup_override"):
    duplicate_of_field = fields.get("duplicate_of")
    if not duplicate_of_field:
        return EngineResponse(
            state="need_fields",
            message="dedup_override requires duplicate_of field identifying the specific duplicate candidate",
            error_code="need_fields",
            data={"missing_fields": ["duplicate_of"]},
        )
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_preflight.py::test_dedup_override_requires_duplicate_of -v`
Expected: PASS

- [ ] **Step 9: Update contract §3 and §6**

In `references/ticket-contract.md`:
- §3: Add `key_file_paths` to Optional YAML Fields table: `| key_file_paths | list[string] | [] | File paths for dedup fingerprinting (persisted on create) |`
- §3: Add `created_at` to Optional YAML Fields: `| created_at | string | "" | ISO 8601 UTC creation timestamp (engine-written, never caller-set) |`
- §6: Change "Override: `dedup_override: true` with matching `ticket_id`" to "Override: `dedup_override: true` with `duplicate_of` identifying the specific duplicate candidate ID"

- [ ] **Step 10: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v`
Expected: All pass (existing tests that use `dedup_override: True` without `duplicate_of` may need updating)

- [ ] **Step 11: Commit**

```bash
git add packages/plugins/ticket/scripts/ packages/plugins/ticket/tests/ packages/plugins/ticket/references/ticket-contract.md
git commit -m "fix(ticket): persist key_file_paths and bind dedup_override to duplicate_of (C-002, C-008)

C-002: Persist key_file_paths in YAML frontmatter on create. Dedup scan
now reads the persisted field instead of regex-extracting from rendered
markdown table. Fallback to regex extraction for pre-existing tickets.

C-008: dedup_override now requires duplicate_of field identifying the
specific duplicate candidate. Prevents unbound bypass.

Also documents created_at field in contract §3."
```

---

## Chunk 4: PR 4 — Validation Hardening (C-005)

### File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/ticket_validate.py` | Modify | Enforce full contract shapes for `source`, `defer`, `key_files` |
| `tests/test_validate.py` | Modify | Update tests to match contract requirements |

### Task 6: Enforce full contract shapes (C-005)

Contract §3 requires `source={type, ref, session}`, `defer={active, reason, deferred_at}`, and `key_files` rows with `{file, role, look_for}`. Current validation is too loose.

- [ ] **Step 1: Write failing tests — partial shapes should be rejected**

Add to `tests/test_validate.py`:

```python
def test_source_requires_ref_and_session():
    """C-005: source must have type, ref, and session per contract §3."""
    from scripts.ticket_validate import validate_fields
    errors = validate_fields({"source": {"type": "ad-hoc"}})
    assert any("ref" in e or "session" in e for e in errors)


def test_defer_requires_active_reason_deferred_at():
    """C-005: defer must have active, reason, deferred_at per contract §3."""
    from scripts.ticket_validate import validate_fields
    errors = validate_fields({"defer": {"active": True}})
    assert any("reason" in e or "deferred_at" in e for e in errors)


def test_key_files_rows_require_file_role_look_for():
    """C-005: key_files rows must have file, role, look_for per contract §3."""
    from scripts.ticket_validate import validate_fields
    errors = validate_fields({"key_files": [{"file": "foo.py"}]})
    assert any("role" in e or "look_for" in e for e in errors)


def test_valid_source_passes():
    """Regression: fully-specified source should pass."""
    from scripts.ticket_validate import validate_fields
    errors = validate_fields({"source": {"type": "user", "ref": "session-1", "session": "abc"}})
    assert errors == []


def test_valid_defer_passes():
    """Regression: fully-specified defer should pass."""
    from scripts.ticket_validate import validate_fields
    errors = validate_fields({"defer": {"active": True, "reason": "blocked", "deferred_at": "2026-03-10"}})
    assert errors == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_validate.py::test_source_requires_ref_and_session -v`
Expected: FAIL — current code only requires `source.type`

- [ ] **Step 3: Tighten validation in `ticket_validate.py`**

Replace the `source`, `defer`, and `key_files` validation blocks (lines 66-93):

```python
    # --- source: require {type, ref, session} per contract §3 ---
    if "source" in fields:
        v = fields["source"]
        if not isinstance(v, dict):
            errors.append(f"source must be a dict, got {type(v).__name__}")
        else:
            if not all(isinstance(val, str) for val in v.values()):
                errors.append("source values must all be strings")
            for required_key in ("type", "ref", "session"):
                if required_key not in v:
                    errors.append(f"source must contain '{required_key}' key")

    # --- defer: require {active, reason, deferred_at} per contract §3 ---
    if "defer" in fields:
        v = fields["defer"]
        if not isinstance(v, dict):
            errors.append(f"defer must be a dict, got {type(v).__name__}")
        else:
            for required_key in ("active", "reason", "deferred_at"):
                if required_key not in v:
                    errors.append(f"defer must contain '{required_key}' key")

    # --- key_files: require {file, role, look_for} per contract §3 ---
    if "key_files" in fields:
        v = fields["key_files"]
        if not isinstance(v, list):
            errors.append(f"key_files must be a list, got {type(v).__name__}")
        elif not all(isinstance(item, dict) for item in v):
            errors.append("key_files must contain only dicts")
        else:
            for i, item in enumerate(v):
                for required_key in ("file", "role", "look_for"):
                    if required_key not in item:
                        errors.append(f"key_files[{i}] must contain '{required_key}' key")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_validate.py -v`
Expected: PASS (new tests pass; existing tests that used partial shapes will need updating)

- [ ] **Step 5: Fix any broken tests that relied on loose validation**

Review and update tests in `test_validate.py` that explicitly test partial `source`, `defer`, or `key_files`. The tests should match the contract, not the old implementation.

- [ ] **Step 6: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_validate.py packages/plugins/ticket/tests/test_validate.py
git commit -m "fix(ticket): enforce full contract shapes for source, defer, key_files (C-005)

Tighten validation to require all contract-specified fields:
- source: {type, ref, session}
- defer: {active, reason, deferred_at}
- key_files rows: {file, role, look_for}

Previously only source.type was required, defer accepted any dict,
and key_files accepted any list of dicts."
```

---

## Chunk 5: PR 5 — Contract Alignment (C-006 + C-007 + C-009 + C-010 + emerged)

### File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/ticket_engine_core.py` | Modify | Remove agent-preflight hard gate on `hook_injected` (C-006) |
| `scripts/ticket_engine_runner.py` | Modify | Consider `parse_error` exit code semantics (C-007 — contract clarification only) |
| `references/ticket-contract.md` | Modify | Document `error_code` in §4; specify ID overflow in §2; document `archive` flag; amend C-006/C-007 |
| `tests/test_preflight.py` | Modify | Update agent-preflight test to reflect contract compliance |
| `tests/test_autonomy.py` | Modify | Update test that codifies hook-gated preflight |

### Task 7: Remove agent-preflight hook gate (C-006)

Contract §5: "Non-execute stages (classify, plan, preflight) remain directly runnable without hook metadata." Code blocks agent preflight on `hook_injected=True` at line 551-562.

- [ ] **Step 1: Write test — agent preflight without hook_injected should succeed**

Add to `tests/test_preflight.py`:

```python
def test_agent_preflight_without_hook_injected_succeeds(tmp_path):
    """C-006: preflight is non-execute; should not require hook_injected per contract §5."""
    from scripts.ticket_engine_core import engine_preflight
    from tests.support.builders import make_ticket

    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)
    create_ticket_file(tickets_dir, id="T-20260310-01", title="Test ticket")

    resp = engine_preflight(
        ticket_id="T-20260310-01",
        action="update",
        session_id="test-session",
        request_origin="agent",
        tickets_dir=tickets_dir,
        hook_injected=False,  # Not hook-injected
        hook_request_origin="agent",
    )
    # Should NOT be policy_blocked for missing hook_injected on preflight
    assert resp.state != "policy_blocked" or "hook_injected" not in resp.message
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_preflight.py::test_agent_preflight_without_hook_injected_succeeds -v`
Expected: FAIL — line 551-562 blocks this

- [ ] **Step 3: Remove the hook_injected gate for preflight**

In `scripts/ticket_engine_core.py`, lines 551-562, remove or gate the `hook_injected` check so it only applies to execute, not preflight:

```python
        # Hook validation: agent execute (not preflight) requires hook_injected.
        # Contract §5: non-execute stages remain directly runnable without hook metadata.
        # Agent preflight still needs session_id for accurate create-cap simulation.
```

Remove the `if not hook_injected: return policy_blocked` block from `engine_preflight`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_preflight.py::test_agent_preflight_without_hook_injected_succeeds -v`
Expected: PASS

- [ ] **Step 5: Update existing tests that codify the old behavior**

Update `test_preflight.py:68` and `test_autonomy.py:258` if they explicitly assert that agent preflight requires `hook_injected=True`. These tests were codifying the implementation, not the contract.

### Task 8: Contract documentation updates (C-007, C-009, C-010, emerged)

- [ ] **Step 6: Update contract document**

In `references/ticket-contract.md`:

**§2 (C-009):** After "Format: `T-YYYYMMDD-NN` (date + 2-digit daily sequence, zero-padded)", add:
```
Overflow: sequence widens past 2 digits after 99 (e.g., T-20260310-100). Minimum width is 2.
```

**§4 (C-010):** After common response envelope, add:
```
Error responses include `error_code: string` at the top level (one of the 12 defined error codes). Success responses omit `error_code`.
```

**§4 (C-007):** Add clarification to exit codes:
```
Exit code 2 maps to `need_fields` error_code specifically. `parse_error` returns exit 1 (engine error) because it covers both malformed CLI payloads and corrupted stored ticket YAML — two distinct failure modes that may warrant splitting in a future version.
```

**§4 (emerged):** Document `archive` flag:
```
The `archive` field in execute close requests controls whether the ticket file is moved to `closed-tickets/`. When `archive: true` and close succeeds, the state is `ok_close_archived` instead of `ok_close`.
```

**§5 (C-006):** Update the existing sentence about hook requirements:
```
Execute provenance: execute requires verified hook provenance (hook_injected=True, hook_request_origin matching entrypoint origin, non-empty session_id) for all mutations, both user and agent. Non-execute stages (classify, plan, preflight) remain directly runnable without hook metadata. Agent preflight requires session_id for accurate create-cap simulation but does not require hook_injected.
```

- [ ] **Step 7: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_engine_core.py packages/plugins/ticket/references/ticket-contract.md packages/plugins/ticket/tests/
git commit -m "fix(ticket): align contract docs and remove agent-preflight hook gate (C-006, C-007, C-009, C-010)

C-006: Remove hook_injected requirement from agent preflight. Contract §5
says non-execute stages are directly runnable without hook metadata.

C-007: Document that parse_error returns exit 1 (not 2) because it covers
two distinct failure modes.

C-009: Document ID sequence overflow behavior (widens past 99).

C-010: Document error_code field in response envelope §4.

Also documents archive flag and updates §5 preflight requirements."
```

---

## Implementation Notes

**Test support builders:** The plan uses helpers from `tests/support/builders.py`. Existing builders include `make_ticket`, `make_gen1_ticket`, etc. The following helpers need to be added as prerequisite steps in the first task that uses them:
- `make_closed_ticket(tickets_dir, ...)` — creates a ticket file in `closed-tickets/` subdirectory
- `make_legacy_ticket(tickets_dir, generation=N, ...)` — creates a ticket with legacy-format ID and generation

**Additional edge case tests** (add during implementation):
- PR 1: Test a ticket in `closed-tickets/` with a non-terminal status (e.g., `in_progress`). Should still be `unresolved`, not `missing`.
- PR 2: Test `_execute_reopen` with legacy ticket (plan only tests update and close).
- PR 3: Test happy path: `dedup_override=True` with `duplicate_of` set to a valid matching ID should succeed.

## Deferred

- **C-005 nested-merge semantics** — Whether partial updates of structured fields like `source` need nested-merge logic. Determine during PR 4 implementation.
- **C-001 confirm-and-convert flow** — The generation gate is interim. Full conversion UX (v1.1) is tracked in existing ticket T-20260302-02 area.

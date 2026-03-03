# Ticket Plugin M6: Pre-Phase 2 Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve three known defects (key_files rename, YAML injection, seq overflow) before building Phase 2 components.

**Architecture:** Modifications to existing Phase 1 modules. No new files — only updates to existing scripts, tests, and contract.

**Tech Stack:** Python 3.11+, PyYAML, pytest.

**Design Doc:** `docs/plans/2026-03-03-ticket-plugin-phase2-design.md` — M6 section.

**Canonical Spec:** `docs/plans/2026-03-02-ticket-plugin-design.md` (912 lines).

**Pre-M6 State:** 157 tests, 9 test files, all passing on `main`.

**Scope:** M6 only — three defect fixes. No new features, no new test files.

---

## Gate Entry

**Before starting any task, verify:**

```bash
cd packages/plugins/ticket && uv run pytest -q
```

Expected: `157 passed`. If not, investigate before proceeding.

---

## Task 1: key_files Field Rename

Rename `key_files` to `key_file_paths` in the dedup/plan pipeline. The render pipeline keeps `key_files: list[dict]` unchanged.

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py:170-202`
- Modify: `packages/plugins/ticket/references/ticket-contract.md:66`
- Test: `packages/plugins/ticket/tests/test_engine.py`
- Test: `packages/plugins/ticket/tests/test_integration.py`

### Step 1: Update test_engine.py — rename plan-pipeline fields

Change `"key_files"` to `"key_file_paths"` in plan-pipeline test payloads. Leave execute/render payloads unchanged.

```python
# test_engine.py:106 — plan create payload
# BEFORE: "key_files": ["handler.py"]
# AFTER:
"key_file_paths": ["handler.py"]

# test_engine.py:149 — plan create with dedup
# BEFORE: "key_files": ["test.py"]
# AFTER:
"key_file_paths": ["test.py"]

# test_engine.py:175 — plan create empty key files
# BEFORE: "key_files": []
# AFTER:
"key_file_paths": []

# test_engine.py:551 — execute create payload (render pipeline — KEEP as key_files)
# "key_files": [{"file": ..., "role": ..., "look_for": ...}]  ← NO CHANGE
```

### Step 2: Update test_integration.py — rename plan-pipeline fields

```python
# test_integration.py:34 — user create end-to-end
# BEFORE: "key_files": []
# AFTER:
"key_file_paths": []

# test_integration.py:147 — dedup then override
# BEFORE: "key_files": ["test.py"]
# AFTER:
"key_file_paths": ["test.py"]

# test_integration.py:160-162 — comment about key_files exclusion from execute
# Update comment to reference key_file_paths for plan and key_files for render
```

### Step 3: Run tests to verify they fail

```bash
cd packages/plugins/ticket && uv run pytest tests/test_engine.py tests/test_integration.py -q
```

Expected: Multiple FAIL — `engine_plan` still reads `fields.get("key_files", [])` so the new field name produces empty lists, breaking dedup fingerprint matching.

### Step 4: Update engine_core.py — rename in plan pipeline

```python
# ticket_engine_core.py:172-173
# BEFORE:
    key_files = fields.get("key_files", [])
    fp = dedup_fingerprint(problem_text, key_files)

# AFTER:
    key_file_paths = fields.get("key_file_paths", [])
    fp = dedup_fingerprint(problem_text, key_file_paths)
```

The dedup scan at lines 193-202 already produces `ticket_key_files: list[str]` (file paths extracted from markdown) and passes to `dedup_fingerprint(ticket_problem, ticket_key_files)`. The local variable name `ticket_key_files` is internal — no rename needed (it's already a list of paths). But rename it for consistency:

```python
# ticket_engine_core.py:193
# BEFORE:
        ticket_key_files: list[str] = []

# AFTER:
        ticket_key_file_paths: list[str] = []

# ticket_engine_core.py:202
# BEFORE:
        existing_fp = dedup_fingerprint(ticket_problem, ticket_key_files)

# AFTER:
        existing_fp = dedup_fingerprint(ticket_problem, ticket_key_file_paths)
```

Also update all references to `ticket_key_files` between lines 193-202 (the `.append` call).

### Step 5: Run tests to verify they pass

```bash
cd packages/plugins/ticket && uv run pytest -q
```

Expected: All 157 pass.

### Step 6: Update ticket-contract.md — document both fields

Add field documentation to the `plan` and `execute` subcommand descriptions:

```markdown
# In the plan subcommand row, add to Input column:
plan | intent, fields (including key_file_paths: list[str] for dedup), session_id, request_origin | ...

# In the execute subcommand row, clarify:
execute | action, ticket_id, fields (including key_files: list[dict] for rendering), session_id, request_origin, dedup_override, dependency_override | ...
```

Add a field disambiguation note after the subcommand table:

```markdown
**Field disambiguation:**
- `key_file_paths: list[str]` — file paths for dedup fingerprinting (plan subcommand input)
- `key_files: list[dict[str, str]]` — structured table rows `{file, role, look_for}` for rendering (execute subcommand input)
- If both are present in input, `key_file_paths` is used for dedup. `key_files` is always used for rendering.
```

### Step 7: Run full test suite

```bash
cd packages/plugins/ticket && uv run pytest -q
```

Expected: 157 passed.

### Step 8: Commit

```bash
git add packages/plugins/ticket/scripts/ticket_engine_core.py packages/plugins/ticket/references/ticket-contract.md packages/plugins/ticket/tests/test_engine.py packages/plugins/ticket/tests/test_integration.py
git commit -m "fix: rename key_files to key_file_paths in dedup/plan pipeline

Separate field names for separate semantics:
- key_file_paths: list[str] for dedup fingerprinting (plan stage)
- key_files: list[dict] for structured rendering (execute stage)

Resolves key_files type split (carried from M5 Codex review)."
```

---

## Task 2: YAML Injection in render_ticket

Replace string interpolation with `yaml.safe_dump` for the YAML frontmatter block in `render_ticket`. Codex M3 finding 1, confirmed by M4 gate probe.

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_render.py:46-68`
- Test: `packages/plugins/ticket/tests/test_render.py`

### Step 1: Write the adversarial test

Add to `test_render.py` after the existing tests:

```python
def test_render_ticket_yaml_injection_source_ref():
    """Adversarial source.ref with YAML-special characters round-trips safely."""
    from scripts.ticket_parse import parse_ticket

    result = render_ticket(
        id="T-20260303-01",
        title="Test injection",
        date="2026-03-03",
        status="open",
        priority="medium",
        source={"type": "ad-hoc", "ref": 'value: "nested" and: more', "session": "s1"},
        problem="Problem text.",
    )
    # Parse it back — should not crash or corrupt fields
    ticket = parse_ticket(result)
    assert ticket is not None
    assert ticket.source["ref"] == 'value: "nested" and: more'


def test_render_ticket_yaml_injection_tags():
    """Tags containing YAML-special characters render as valid YAML."""
    from scripts.ticket_parse import parse_ticket

    result = render_ticket(
        id="T-20260303-02",
        title="Test tag injection",
        date="2026-03-03",
        status="open",
        priority="medium",
        tags=["tag: with colon", "tag\nwith\nnewline"],
        problem="Problem text.",
    )
    ticket = parse_ticket(result)
    assert ticket is not None
    assert "tag: with colon" in ticket.tags
```

### Step 2: Run test to verify it fails

```bash
cd packages/plugins/ticket && uv run pytest tests/test_render.py::test_render_ticket_yaml_injection_source_ref tests/test_render.py::test_render_ticket_yaml_injection_tags -v
```

Expected: FAIL — the f-string interpolation produces invalid YAML that `parse_ticket` cannot parse.

### Step 3: Fix render_ticket — use yaml.safe_dump for frontmatter

Replace the f-string YAML block (lines 46-68) with `yaml.safe_dump`:

```python
import yaml  # Add to imports at top of file

# Replace lines 46-68 with:
    # --- YAML frontmatter ---
    frontmatter: dict[str, Any] = {
        "id": id,
        "date": date,
        "status": status,
        "priority": priority,
    }
    if effort:
        frontmatter["effort"] = effort
    frontmatter["source"] = {
        "type": source["type"],
        "ref": source.get("ref", ""),
        "session": source.get("session", ""),
    }
    frontmatter["tags"] = tags
    frontmatter["blocked_by"] = blocked_by
    frontmatter["blocks"] = blocks

    if defer is not None:
        frontmatter["defer"] = {
            "active": defer.get("active", False),
            "reason": defer.get("reason", ""),
            "deferred_at": defer.get("deferred_at", ""),
        }

    frontmatter["contract_version"] = contract_version

    # yaml.safe_dump with default_flow_style=False for readable output
    yaml_str = yaml.safe_dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    ).rstrip("\n")

    lines = [
        f"# {id}: {title}",
        "",
        "```yaml",
        yaml_str,
        "```",
    ]
```

**Important:** `sort_keys=False` preserves field ordering per the contract's cognitive flow. `allow_unicode=True` prevents double-escaping. `.rstrip("\n")` removes the trailing newline `safe_dump` appends.

**Note:** This replaces the entire YAML frontmatter construction — the `if defer` and `contract_version` blocks that follow in the original code are now part of the `frontmatter` dict above. Verify no code between lines 68-80 in the original is left dangling.

### Step 4: Run adversarial tests to verify they pass

```bash
cd packages/plugins/ticket && uv run pytest tests/test_render.py -v
```

Expected: All tests pass (existing 5 + new 2 = 7).

### Step 5: Run full test suite for regression

```bash
cd packages/plugins/ticket && uv run pytest -q
```

Expected: 159 passed (157 + 2 new). Some existing tests may need minor adjustments if the YAML output format changes (e.g., quoting style for strings). Fix any format-sensitive assertions while preserving the round-trip property.

### Step 6: Commit

```bash
git add packages/plugins/ticket/scripts/ticket_render.py packages/plugins/ticket/tests/test_render.py
git commit -m "fix: use yaml.safe_dump for ticket frontmatter rendering

Replaces f-string interpolation with yaml.safe_dump to prevent YAML
injection via special characters in source, tags, and other fields.
Codex M3 finding 1, confirmed by M4 gate probe."
```

---

## Task 3: Seq Overflow at 99

Extend `_DATE_ID_RE` to support variable-width sequences (3+ digits). `T-YYYYMMDD-100` is currently invisible to future scans.

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_id.py:3,15,51`
- Test: `packages/plugins/ticket/tests/test_id.py`

### Step 1: Write the boundary test

Add to `test_id.py`:

```python
def test_allocate_id_beyond_99(tmp_path, make_ticket):
    """allocate_id handles sequence numbers beyond 99."""
    tickets_dir = tmp_path / "tickets"
    tickets_dir.mkdir()
    today = date(2026, 3, 3)

    # Create tickets T-20260303-98 and T-20260303-99
    for seq in (98, 99):
        tid = f"T-20260303-{seq:02d}"
        content = make_ticket(id=tid, date="2026-03-03", title=f"Ticket {seq}")
        (tickets_dir / f"2026-03-03-ticket-{seq}.md").write_text(content)

    result = allocate_id(tickets_dir, today)
    assert result == "T-20260303-100"

    # Now create 100 and verify 101 is allocated
    content = make_ticket(id="T-20260303-100", date="2026-03-03", title="Ticket 100")
    (tickets_dir / "2026-03-03-ticket-100.md").write_text(content)

    result = allocate_id(tickets_dir, today)
    assert result == "T-20260303-101"


def test_date_id_regex_matches_variable_width():
    """_DATE_ID_RE matches IDs with 2+ digit sequences."""
    from scripts.ticket_id import _DATE_ID_RE

    assert _DATE_ID_RE.match("T-20260303-01")
    assert _DATE_ID_RE.match("T-20260303-99")
    assert _DATE_ID_RE.match("T-20260303-100")
    assert _DATE_ID_RE.match("T-20260303-1000")
    assert not _DATE_ID_RE.match("T-20260303-0")  # single digit invalid
    assert not _DATE_ID_RE.match("T-2026030-01")   # 7-digit date invalid
```

### Step 2: Run test to verify it fails

```bash
cd packages/plugins/ticket && uv run pytest tests/test_id.py::test_allocate_id_beyond_99 tests/test_id.py::test_date_id_regex_matches_variable_width -v
```

Expected: FAIL — `_DATE_ID_RE` only matches `\d{2}`, so `T-20260303-100` doesn't match and the 100-seq ticket is invisible.

### Step 3: Fix _DATE_ID_RE and allocate_id

```python
# ticket_id.py:3 — update docstring
# BEFORE: Format: T-YYYYMMDD-NN (date + 2-digit daily sequence, zero-padded).
# AFTER:
"""Ticket ID allocation and slug generation.

Format: T-YYYYMMDD-NN (date + daily sequence, minimum 2 digits, zero-padded).
Legacy IDs (T-NNN, T-[A-F], slugs) are preserved permanently.
"""

# ticket_id.py:15 — widen regex
# BEFORE: _DATE_ID_RE = re.compile(r"^T-(\d{8})-(\d{2})$")
# AFTER:
_DATE_ID_RE = re.compile(r"^T-(\d{8})-(\d{2,})$")

# ticket_id.py:51 — variable-width formatting
# BEFORE: return f"{prefix}{max_seq + 1:02d}"
# AFTER:
    next_seq = max_seq + 1
    return f"{prefix}{next_seq:02d}"
```

The `:02d` format already handles variable width — `100` is not zero-padded because it exceeds 2 digits. The only fix needed is the regex (`\d{2}` → `\d{2,}`).

### Step 4: Run tests to verify they pass

```bash
cd packages/plugins/ticket && uv run pytest tests/test_id.py -v
```

Expected: All pass (18 existing + 2 new = 20).

### Step 5: Check dependent functions

`build_filename` (line 83) and `is_legacy_id` (line 94) and `parse_id_date` (line 99) all use `_DATE_ID_RE.match()`. Verify they still work with variable-width sequences:

```bash
cd packages/plugins/ticket && uv run pytest -q
```

Expected: 161 passed (157 + 2 render + 2 id).

### Step 6: Commit

```bash
git add packages/plugins/ticket/scripts/ticket_id.py packages/plugins/ticket/tests/test_id.py
git commit -m "fix: support variable-width sequence numbers in ticket IDs

Widen _DATE_ID_RE from \d{2} to \d{2,} so IDs beyond T-YYYYMMDD-99
(e.g., T-YYYYMMDD-100) are recognized by allocate_id, build_filename,
and is_legacy_id. Previously, 3+ digit sequences were invisible to
scans, causing ID collisions."
```

---

## Gate Exit

### Verification Checklist

```bash
cd packages/plugins/ticket && uv run pytest -q
```

Expected: 161 passed (157 original + 2 render adversarial + 2 ID boundary).

| Check | Expected |
|-------|----------|
| `key_file_paths` used in plan pipeline | `fields.get("key_file_paths", [])` at engine_core.py:172 |
| `key_files` preserved in render pipeline | `key_files=fields.get("key_files")` at engine_core.py:720 |
| Contract documents both fields | Field disambiguation note in ticket-contract.md |
| YAML frontmatter uses `yaml.safe_dump` | No f-string interpolation in render_ticket YAML block |
| Adversarial YAML round-trips | `test_render_ticket_yaml_injection_*` pass |
| `_DATE_ID_RE` matches 3+ digit sequences | `\d{2,}` pattern in ticket_id.py:15 |
| `allocate_id` returns 3-digit IDs | `test_allocate_id_beyond_99` passes |
| No regressions | All 161 tests pass |

### Post-Gate

After gate verification, this module is complete. Proceed to M7 (Hook + Audit Trail).

Optionally trigger Codex review per the Phase 2 Codex Review Strategy:
- Focus: rename completeness — any remaining `key_files` references in dedup path?

# Deferred Work Tracking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement `/defer` and `/triage` skills with supporting scripts (`ticket_parsing.py`, `provenance.py`, `defer.py`, `triage.py`) in the handoff plugin.

**Architecture:** Four deterministic scripts handle parsing, provenance, creation, and reporting. Two SKILL.md files provide the LLM-facing UX. Scripts follow the existing handoff plugin patterns: frozen dataclasses, TypedDict returns, import fallback for direct execution, explicit error codes. Dual-write provenance (YAML field primary, HTML comment secondary). PyYAML for ticket parsing.

**Tech Stack:** Python 3.12, PyYAML, pytest. Plugin: `packages/plugins/handoff/`.

**Design doc:** `docs/plans/2026-02-28-deferred-work-tracking-design.md` (triple Codex-reviewed).

**Branch:** `feature/deferred-work-tracking` from `main`.

---

## Amendments (Codex Deep Review — 2026-02-28)

Applied after evaluative Codex dialogue (thread `019ca324-61ae-7640-b256-5c7a86bbfb47`, 4/8 turns, converged). 20 resolved findings, 2 unresolved, 2 emerged.

### P0 — Hard failures (3)

| # | Task | Finding | Fix |
|---|------|---------|-----|
| P0-1 | 8 | `parse_frontmatter()` returns `tuple[dict, str]` but code assigns to single var | `fm, body = parse_frontmatter(handoff_text)` + use `body` for `parse_sections` |
| P0-2 | 8 | `section.heading` stores `"## Open Questions"` but compared against bare names | Strip `## ` prefix before comparison (inline `_section_name` pattern from `distill.py`) |
| P0-3 | 2,3,6 | `yaml.safe_load('date: 2026-02-28')` → `datetime.date`, not `str`. Cascades through `validate_schema` → `parse_ticket` → `allocate_id` → all downstream | Post-load normalization of `datetime.date`/`datetime.datetime` to `str()` in `parse_yaml_frontmatter`. Quote dates in `render_ticket`. Add test. |

### P1 — Functional gaps (6)

| # | Task | Finding | Fix |
|---|------|---------|-----|
| P1-1 | 9 | `orphaned_items` includes ALL items (matched + unmatched) | Only append `manual_review` items to `orphaned_items`; report matched items in `matched_items` |
| P1-2 | 8 | UID match fires for ALL items from a handoff session, not just the deferred one | Add docstring note: `uid_match` is session-level correlation, not item-level. Document as known limitation. |
| P1-3 | 9 | 30-day lookback omitted (design requires it) | Add `_LOOKBACK_DAYS = 30` constant + date filter in `_scan_handoff_dirs` |
| P1-4 | 8,9 | Missing prose skip count (design Phase 0 requires it) | Add `skipped_prose_count` to `extract_handoff_items` return and `generate_report` output |
| P1-5 | 6 | Manual YAML rendering lacks escaping for values with colons | Quote all string values in YAML output with `yaml.dump` for the provenance block; quote `source_ref` |
| P1-6 | 6 | `defer.py` batch write loop has no error handling | Wrap per-item write in try/except, return `partial_success` on partial failure |

### P2 — Test gaps (6)

| # | Task | Finding | Fix |
|---|------|---------|-----|
| P2-1 | 6 | Slug test expects `"section-level"` but period stripped → `"sectionlevel"` | Fix expected string in `test_generates_slug` |
| P2-2 | 9 | `test_match_counts` assertion is a tautology (sum == len) | Assert specific count values instead of identity |
| P2-3 | 6 | `write_ticket()` only tested in Task 13 integration, no unit test | Add `TestWriteTicket` class in Task 6 tests |
| P2-4 | 14 | No defer→triage round-trip integration test | Add round-trip test: `write_ticket()` → `generate_report()` → verify match |
| P2-5 | 1 | `pyproject.toml` TOML snippet ambiguous (could create duplicate `[project]`) | Clarify: add field to existing `[project]` section |
| P2-6 | 10,11 | SKILL.md needs structural verification (frontmatter keys, required sections) | Add verification checklist step before commit in Tasks 10 and 11 |

### P3 — Cosmetic (4)

| # | Task | Finding | Fix |
|---|------|---------|-----|
| P3-1 | 2 | `extract_fenced_yaml_helper` defined after test class that uses it | Move helper definition before `TestParseYamlFrontmatter` |
| P3-2 | 4 | `render_defer_meta` uses compact JSON without `sort_keys=True` (inconsistent with `distill.py`) | Add `sort_keys=True` to `json.dumps` |
| P3-3 | — | Plan header says TypedDict but some returns are plain dict | Documentation note only — not a code change |
| P3-4 | 8 | `extract_handoff_items` bypasses `parse_handoff` pattern used by `distill.py` | Fixed alongside P0-1/P0-2 — use proper destructuring |

### Unresolved (2)

- **plugin.json skills field:** Does auto-discovery need explicit registration or is filesystem scan of `skills/*/SKILL.md` sufficient? Determine during Task 12.
- **SKILL.md structural lint:** Should Task 12 include a verification step for SKILL.md frontmatter keys and required sections? Determine during Task 12.

### Emerged (2)

- **PyYAML date normalization for top-level ticket fields:** Top-level string fields in ticket YAML may contain date-like values that PyYAML auto-converts to `datetime.date`. `_normalize_yaml_scalars` normalizes these back to `str`. Does not recurse into nested dicts — ticket schema only uses date-like values at top level. (P1-8 narrowed scope from original "architectural pattern" claim.)
- **UID match reclassification:** `uid_match` is a session-level weak correlation signal, not an item-level strong match. Design doc terminology unchanged but implementation documents this.

---

## Amendments (Codex Adversarial Review — 2026-02-28)

Applied after adversarial Codex dialogue (thread `019ca346-e54d-7c90-9727-cf23681fbb71`, 5/10 turns, converged). 16 findings (5 P1, 7 P2, 4 P3). Prerequisite: all 19 deep-review amendments above must be applied first.

### P1 — Functional breakage (5)

| # | Task | Finding | Fix |
|---|------|---------|-----|
| P1-7 | 4,6,8 | `session_matches("","")` returns `True` — false-positive uid_match when both handoff and ticket lack session_id (empty string vs None). 3-place fix required. | Guard with `if not ticket_session or not handoff_session` in `session_matches`; use truthiness check in `read_provenance`; guard empty `session_id` in `render_ticket` provenance. Add `test_empty_string_returns_false`. |
| P1-8 | 2 | `_normalize_yaml_scalars` scope contradicts "architectural pattern" emerged claim — function normalizes top-level only but emerged text says "any yaml.safe_load result" | Narrow emerged claim to "top-level ticket fields". Add docstring caveat: "Does not recurse into nested dicts." |
| P1-9 | 6 | `render_ticket` produces unvalidated YAML — `priority` and `effort` bypass `_quote()`, manual assembly → `parse_ticket` returns `None` → `allocate_id` silent skip → ID collision chain | Apply `_quote()` to `priority` and `effort`. Add `_VALID_PRIORITIES` and `_VALID_EFFORTS` enum sets as primary defense. Add round-trip test in Task 6. |
| P1-10 | 9 | 30-day lookback tests all pass because `tmp_path` files have fresh mtimes — exclusion path completely untested | Add `test_excludes_old_files` that sets mtime to 31 days ago via `os.utime()`. |
| P1-11 | 8 | `handoff-\w+` regex misses hyphenated IDs — `handoff-quality-hook` matched as `handoff-quality`, item falls to `manual_review` | Change pattern to `handoff-[\w-]+`. Add `test_hyphenated_handoff_id_match`. |

### P2 — Correctness/quality gaps (7)

| # | Task | Finding | Fix |
|---|------|---------|-----|
| P2-6 | 10,11 | SKILL.md structural verification step referenced as "P2-6" in Tasks 10/11 but no P2-6 entry in deep-review amendments table | Add formal P2-6 entry to deep-review P2 table (doc fix). |
| P2-7 | 8 | `next(iter(matched))` set iteration non-deterministic — violates deterministic-scripts architecture | Replace with `sorted(matched)[0]` for alphabetic determinism. |
| P2-8 | 9 | P2-2 test uses `>= 1` assertion — masks empty-string false positives; should assert exact expected values for deterministic fixture | Tighten to exact counts: `uid_match == 5`, `id_ref == 0`, `manual_review == 0` for the test fixture. |
| P2-9 | 6 | `render_ticket` writes empty backtick pairs (`Branch: \`\`. Session: \`\`.`) for empty values — misleading display | Guard: omit `Branch:`/`Session:` lines when values are empty. |
| P2-10 | 8 | `uid_match` selection non-deterministic with multiple tickets sharing session — unsorted glob + first-hit return | Sort glob in `_load_tickets_for_matching` by path for deterministic iteration. |
| P2-11 | 6 | `allocate_id` silently skips malformed tickets — can produce duplicate sequence numbers | Add `warnings.warn()` when `parse_ticket` returns `None` during ID allocation scan. |
| P2-12 | 3 | Effort format — design says `XS\|S\|M\|L\|XL` enum but `validate_schema` only checks `str` type | Deferred — add format validation in follow-up. Document gap in `validate_schema` docstring. |

### P3 — Low-risk (4)

| # | Task | Finding | Fix |
|---|------|---------|-----|
| P3-5 | 8 | `T-[A-F]` regex upper bound covers only current legacy scope (A–F), not future extensions | Deferred — current corpus uses A-F only. Add inline comment documenting the bound. |
| P3-6 | 9 | `generate_report` parses ticket files twice per triage run (`read_open_tickets` + `_load_tickets_for_matching`) | Deferred — correctness unaffected. Add comment noting optimization opportunity. |
| P3-7 | 7 | `read_open_tickets` uses `path.stem` as summary instead of ticket title from frontmatter | Deferred — summary is presentational, not used in matching. |
| P3-8 | 4 | `render_defer_meta` regex `{.*?}` (non-greedy) would truncate if JSON payload contains `-->` | Deferred — `source_ref` values are human text (e.g., "PR #29"), extremely unlikely to contain `-->`. |

### Unresolved (3)

- **Recursive normalization scope:** Should `_normalize_yaml_scalars` recurse into nested dicts (future-proofing) or should the scope be top-level only? Narrowed to top-level for now (P1-8). Revisit if provenance subdict ever contains date-like values.
- **YAML rendering strategy:** Should `render_ticket` switch to `yaml.dump()` for the entire YAML block vs. fixing `_quote()` coverage? Manual assembly with expanded `_quote()` chosen (P1-9). `yaml.dump` would be safer but changes output format.
- **F15 timing:** `allocate_id` silent skip is P2-11 with `warnings.warn()`. May be promoted to fix-now if warning proves insufficient.

### Emerged (2)

- **3-place session_matches hardening:** Empty-string false positives propagate through `render_ticket` → `read_provenance` → `session_matches`. All three must guard falsy values, not just `None`. Guard pattern: `if not value` (catches both `None` and `""`), not `value is None`.
- **Test coverage meta-finding:** Only 6-8 of ~77 planned tests are high-signal for amended behavior. Fix-now amendments add ~10 targeted tests to close this gap.

---

## Task 1: Setup — Branch, PyYAML Dependency

**Files:**
- Modify: `packages/plugins/handoff/pyproject.toml`
- Modify: `packages/plugins/handoff/uv.lock`

**Step 1: Create branch**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git checkout main && git pull
git checkout -b feature/deferred-work-tracking
```

**Step 2: Add PyYAML dependency**

In `packages/plugins/handoff/pyproject.toml`, add `pyyaml>=6.0` to the existing `[project]` section's `dependencies` field. **Do not create a duplicate `[project]` header** — find the existing one and add the field:

```toml
# Add this line inside the existing [project] section:
dependencies = ["pyyaml>=6.0"]
```

**Step 3: Lock dependencies**

```bash
cd packages/plugins/handoff && uv lock
```

**Step 4: Verify existing tests still pass**

Run: `cd packages/plugins/handoff && uv run pytest -q`
Expected: `238 passed`

**Step 5: Commit**

```bash
git add packages/plugins/handoff/pyproject.toml packages/plugins/handoff/uv.lock
git commit -m "chore(handoff): add PyYAML dependency for ticket parsing"
```

---

## Task 2: ticket_parsing.py — Core Types and Fenced YAML Extraction

**Files:**
- Create: `packages/plugins/handoff/scripts/ticket_parsing.py`
- Create: `packages/plugins/handoff/tests/test_ticket_parsing.py`

**Step 1: Write failing tests for fenced YAML extraction**

```python
"""Tests for ticket_parsing.py — fenced-YAML ticket format parser."""
from __future__ import annotations

from pathlib import Path

import pytest

# --- Fixtures ---

MINIMAL_TICKET = """\
# T-20260228-01: Example ticket

```yaml
id: T-20260228-01
date: 2026-02-28
status: deferred
priority: medium
```

## Problem

Something is wrong.
"""

TICKET_WITH_LISTS = """\
# T-20260228-02: Ticket with lists

```yaml
id: T-20260228-02
date: 2026-02-28
status: open
priority: high
source_type: pr-review
source_ref: "PR #29"
branch: feature/knowledge-graduation
blocked_by: []
blocks: []
effort: XS
files:
  - path/to/file.py
  - path/to/other.py
provenance:
  source_session: "5136e38e-efc5-403f-ad5e-49516f47884b"
  source_type: pr-review
  created_by: defer-skill
```

## Problem

Something with lists.
"""

LEGACY_TICKET = """\
# T-A: Legacy ticket

```yaml
id: T-A
date: 2026-02-17
status: complete
priority: medium
blocked_by: []
blocks: []
related:
  - T-B
  - T-C
plugin: packages/plugins/handoff/
```

## Summary

Legacy content.
"""

NO_FENCED_YAML = """\
# No YAML here

## Problem

Just markdown, no fenced YAML block.
"""

MALFORMED_YAML = """\
# Bad YAML

```yaml
id: T-BAD
date: 2026-02-28
status: [invalid unclosed
```

## Problem

Broken YAML.
"""


class TestExtractFencedYaml:
    def test_minimal_ticket(self) -> None:
        from scripts.ticket_parsing import extract_fenced_yaml

        result = extract_fenced_yaml(MINIMAL_TICKET)
        assert result is not None
        assert "id: T-20260228-01" in result

    def test_ticket_with_lists(self) -> None:
        from scripts.ticket_parsing import extract_fenced_yaml

        result = extract_fenced_yaml(TICKET_WITH_LISTS)
        assert result is not None
        assert "files:" in result
        assert "provenance:" in result

    def test_no_fenced_yaml_returns_none(self) -> None:
        from scripts.ticket_parsing import extract_fenced_yaml

        result = extract_fenced_yaml(NO_FENCED_YAML)
        assert result is None

    def test_extracts_first_yaml_block_only(self) -> None:
        from scripts.ticket_parsing import extract_fenced_yaml

        text = "```yaml\nfirst: block\n```\n\n```yaml\nsecond: block\n```"
        result = extract_fenced_yaml(text)
        assert result is not None
        assert "first: block" in result
        assert "second" not in result


def extract_fenced_yaml_helper(text: str) -> str:
    """Helper to extract YAML for tests that need parsed YAML input."""
    from scripts.ticket_parsing import extract_fenced_yaml

    result = extract_fenced_yaml(text)
    assert result is not None
    return result


class TestParseYamlFrontmatter:
    def test_minimal_fields(self) -> None:
        from scripts.ticket_parsing import parse_yaml_frontmatter

        result = parse_yaml_frontmatter("id: T-20260228-01\ndate: 2026-02-28\nstatus: deferred")
        assert result["id"] == "T-20260228-01"
        assert result["status"] == "deferred"

    def test_date_normalized_to_string(self) -> None:
        """P0-3: yaml.safe_load converts unquoted dates to datetime.date objects."""
        from scripts.ticket_parsing import parse_yaml_frontmatter

        result = parse_yaml_frontmatter("id: T-20260228-01\ndate: 2026-02-28\nstatus: deferred")
        assert isinstance(result["date"], str), f"date must be str, got {type(result['date'])}"
        assert result["date"] == "2026-02-28"

    def test_list_fields_preserved(self) -> None:
        from scripts.ticket_parsing import parse_yaml_frontmatter

        yaml_text = extract_fenced_yaml_helper(TICKET_WITH_LISTS)
        result = parse_yaml_frontmatter(yaml_text)
        assert isinstance(result["files"], list)
        assert len(result["files"]) == 2
        assert isinstance(result["provenance"], dict)

    def test_malformed_yaml_returns_none(self) -> None:
        from scripts.ticket_parsing import parse_yaml_frontmatter

        result = parse_yaml_frontmatter("id: [invalid unclosed")
        assert result is None

    def test_empty_string_returns_none(self) -> None:
        from scripts.ticket_parsing import parse_yaml_frontmatter

        result = parse_yaml_frontmatter("")
        assert result is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_ticket_parsing.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.ticket_parsing'`

**Step 3: Write minimal implementation**

```python
"""Parse fenced-YAML ticket format used in docs/tickets/.

Existing tickets use ```yaml ... ``` blocks (NOT --- frontmatter).
handoff_parsing.py cannot parse this format. This module uses PyYAML
for full YAML support including multiline values (files: arrays, etc.).
"""
from __future__ import annotations

import re
from typing import Any

import yaml

# Match the first ```yaml ... ``` block in a markdown file.
_FENCED_YAML_RE = re.compile(
    r"^```ya?ml\s*\n(.*?)^```",
    re.MULTILINE | re.DOTALL,
)


def extract_fenced_yaml(text: str) -> str | None:
    """Extract the YAML text from the first fenced yaml block.

    Returns None if no fenced yaml block is found.
    """
    m = _FENCED_YAML_RE.search(text)
    return m.group(1) if m else None


def _normalize_yaml_scalars(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize yaml.safe_load auto-conversions back to strings.

    PyYAML converts unquoted date-like values (e.g., 2026-02-28) to
    datetime.date objects. This normalizes top-level string fields back to str.

    Note: Does not recurse into nested dicts (e.g., provenance subdict).
    Ticket schema only uses date-like values at top level. (P1-8)
    """
    import datetime

    for key, value in data.items():
        if isinstance(value, (datetime.date, datetime.datetime)):
            data[key] = str(value)
    return data


def parse_yaml_frontmatter(yaml_text: str) -> dict[str, Any] | None:
    """Parse a YAML string into a dict using yaml.safe_load.

    Returns None if the YAML is empty or malformed.
    Normalizes datetime.date/datetime values back to str (P0-3 fix).
    """
    if not yaml_text.strip():
        return None
    try:
        result = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None
    if not isinstance(result, dict):
        return None
    return _normalize_yaml_scalars(result)
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_ticket_parsing.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/ticket_parsing.py packages/plugins/handoff/tests/test_ticket_parsing.py
git commit -m "feat(handoff): add ticket_parsing.py — fenced YAML extraction and parsing"
```

---

## Task 3: ticket_parsing.py — Schema Validation and TicketFile Type

**Files:**
- Modify: `packages/plugins/handoff/scripts/ticket_parsing.py`
- Modify: `packages/plugins/handoff/tests/test_ticket_parsing.py`

**Step 1: Write failing tests for schema validation and TicketFile**

Add to `test_ticket_parsing.py`:

```python
from dataclasses import FrozenInstanceError


class TestValidateSchema:
    def test_valid_minimal(self) -> None:
        from scripts.ticket_parsing import validate_schema

        data = {"id": "T-20260228-01", "date": "2026-02-28", "status": "deferred"}
        errors = validate_schema(data)
        assert errors == []

    def test_missing_required_field(self) -> None:
        from scripts.ticket_parsing import validate_schema

        data = {"id": "T-20260228-01", "date": "2026-02-28"}  # missing status
        errors = validate_schema(data)
        assert any("status" in e for e in errors)

    def test_files_must_be_list(self) -> None:
        from scripts.ticket_parsing import validate_schema

        data = {"id": "T-1", "date": "2026-02-28", "status": "open", "files": "not-a-list"}
        errors = validate_schema(data)
        assert any("files" in e for e in errors)

    def test_provenance_must_be_dict(self) -> None:
        from scripts.ticket_parsing import validate_schema

        data = {"id": "T-1", "date": "2026-02-28", "status": "open", "provenance": "bad"}
        errors = validate_schema(data)
        assert any("provenance" in e for e in errors)

    def test_status_must_be_string(self) -> None:
        from scripts.ticket_parsing import validate_schema

        data = {"id": "T-1", "date": "2026-02-28", "status": 42}
        errors = validate_schema(data)
        assert any("status" in e for e in errors)


class TestParseTicket:
    def test_parse_minimal_ticket(self, tmp_path: Path) -> None:
        from scripts.ticket_parsing import TicketFile, parse_ticket

        ticket = tmp_path / "test.md"
        ticket.write_text(MINIMAL_TICKET)
        result = parse_ticket(ticket)
        assert isinstance(result, TicketFile)
        assert result.frontmatter["id"] == "T-20260228-01"
        assert result.frontmatter["status"] == "deferred"
        assert "## Problem" in result.body

    def test_parse_ticket_with_lists(self, tmp_path: Path) -> None:
        from scripts.ticket_parsing import parse_ticket

        ticket = tmp_path / "test.md"
        ticket.write_text(TICKET_WITH_LISTS)
        result = parse_ticket(ticket)
        assert isinstance(result.frontmatter["files"], list)
        assert len(result.frontmatter["files"]) == 2

    def test_parse_legacy_ticket(self, tmp_path: Path) -> None:
        from scripts.ticket_parsing import parse_ticket

        ticket = tmp_path / "test.md"
        ticket.write_text(LEGACY_TICKET)
        result = parse_ticket(ticket)
        assert result.frontmatter["id"] == "T-A"
        assert result.frontmatter["status"] == "complete"
        assert isinstance(result.frontmatter["related"], list)

    def test_parse_no_yaml_returns_none(self, tmp_path: Path) -> None:
        from scripts.ticket_parsing import parse_ticket

        ticket = tmp_path / "test.md"
        ticket.write_text(NO_FENCED_YAML)
        result = parse_ticket(ticket)
        assert result is None

    def test_parse_malformed_yaml_returns_none(self, tmp_path: Path) -> None:
        from scripts.ticket_parsing import parse_ticket

        ticket = tmp_path / "test.md"
        ticket.write_text(MALFORMED_YAML)
        result = parse_ticket(ticket)
        assert result is None

    def test_ticketfile_is_frozen(self, tmp_path: Path) -> None:
        from scripts.ticket_parsing import parse_ticket

        ticket = tmp_path / "test.md"
        ticket.write_text(MINIMAL_TICKET)
        result = parse_ticket(ticket)
        with pytest.raises(FrozenInstanceError):
            result.path = "other"  # type: ignore[misc]

    def test_nonexistent_file_returns_none(self, tmp_path: Path) -> None:
        from scripts.ticket_parsing import parse_ticket

        result = parse_ticket(tmp_path / "nonexistent.md")
        assert result is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_ticket_parsing.py -v`
Expected: FAIL — `ImportError: cannot import name 'validate_schema'`

**Step 3: Implement TicketFile, validate_schema, parse_ticket**

Add to `ticket_parsing.py`:

```python
from dataclasses import dataclass
from pathlib import Path

_REQUIRED_FIELDS = ("id", "date", "status")
_LIST_FIELDS = ("files", "blocked_by", "blocks", "related")
_DICT_FIELDS = ("provenance",)
_STRING_FIELDS = ("id", "date", "status", "priority", "source_type", "source_ref", "branch", "effort")


@dataclass(frozen=True)
class TicketFile:
    """Parsed ticket with typed frontmatter and markdown body."""
    path: str
    frontmatter: dict[str, Any]
    body: str


def validate_schema(data: dict[str, Any]) -> list[str]:
    """Validate ticket frontmatter schema. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    for field in _REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")
    for field in _STRING_FIELDS:
        if field in data and not isinstance(data[field], str):
            errors.append(f"{field} must be string, got {type(data[field]).__name__}")
    for field in _LIST_FIELDS:
        if field in data and not isinstance(data[field], list):
            errors.append(f"{field} must be list, got {type(data[field]).__name__}")
    for field in _DICT_FIELDS:
        if field in data and not isinstance(data[field], dict):
            errors.append(f"{field} must be dict, got {type(data[field]).__name__}")
    return errors


def parse_ticket(path: Path) -> TicketFile | None:
    """Parse a ticket markdown file into a TicketFile.

    Returns None if:
    - File doesn't exist or can't be read
    - No fenced YAML block found
    - YAML is malformed
    - Required fields missing (id, date, status)
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return None

    frontmatter = parse_yaml_frontmatter(yaml_text)
    if frontmatter is None:
        return None

    errors = validate_schema(frontmatter)
    if errors:
        return None

    # Body is everything after the fenced YAML block's closing ```
    m = _FENCED_YAML_RE.search(text)
    body = text[m.end():].strip() if m else ""

    return TicketFile(path=str(path), frontmatter=frontmatter, body=body)
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_ticket_parsing.py -v`
Expected: all PASS

**Step 5: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest -q`
Expected: all pass (238 + new)

**Step 6: Commit**

```bash
git add packages/plugins/handoff/scripts/ticket_parsing.py packages/plugins/handoff/tests/test_ticket_parsing.py
git commit -m "feat(handoff): add TicketFile type, schema validation, and parse_ticket()"
```

---

## Task 4: provenance.py — Defer-Meta Parsing and Dual-Read

**Files:**
- Create: `packages/plugins/handoff/scripts/provenance.py`
- Create: `packages/plugins/handoff/tests/test_provenance.py`

**Step 1: Write failing tests**

```python
"""Tests for provenance.py — defer-meta/distill-meta parsing and session matching."""
from __future__ import annotations

import pytest

# --- Fixtures ---

DEFER_META_COMMENT = '<!-- defer-meta {"v": 1, "source_session": "5136e38e-efc5-403f-ad5e-49516f47884b", "source_type": "pr-review", "source_ref": "PR #29", "created_by": "defer-skill"} -->'

DISTILL_META_COMMENT = '<!-- distill-meta {"v": 1, "source_uid": "sha256:abc123", "source_anchor": "## Decisions", "content_sha256": "def456", "distilled_at": "2026-02-27T12:00:00Z"} -->'

TICKET_BODY_WITH_META = f"""\
## Problem

Something is wrong.

## Acceptance Criteria

- [ ] Fix it

{DEFER_META_COMMENT}
"""

TICKET_BODY_NO_META = """\
## Problem

Something is wrong.

## Acceptance Criteria

- [ ] Fix it
"""

PROVENANCE_YAML = {
    "source_session": "5136e38e-efc5-403f-ad5e-49516f47884b",
    "source_type": "pr-review",
    "created_by": "defer-skill",
}


class TestParseDeferMeta:
    def test_parses_valid_comment(self) -> None:
        from scripts.provenance import parse_defer_meta

        result = parse_defer_meta(TICKET_BODY_WITH_META)
        assert result is not None
        assert result["source_session"] == "5136e38e-efc5-403f-ad5e-49516f47884b"
        assert result["source_type"] == "pr-review"
        assert result["v"] == 1

    def test_no_comment_returns_none(self) -> None:
        from scripts.provenance import parse_defer_meta

        result = parse_defer_meta(TICKET_BODY_NO_META)
        assert result is None

    def test_malformed_json_returns_none(self) -> None:
        from scripts.provenance import parse_defer_meta

        result = parse_defer_meta('<!-- defer-meta {bad json} -->')
        assert result is None


class TestParseDistillMeta:
    def test_parses_valid_comment(self) -> None:
        from scripts.provenance import parse_distill_meta

        result = parse_distill_meta(f"Some text\n{DISTILL_META_COMMENT}\n")
        assert result is not None
        assert result["source_uid"] == "sha256:abc123"

    def test_no_comment_returns_none(self) -> None:
        from scripts.provenance import parse_distill_meta

        result = parse_distill_meta("No meta here")
        assert result is None


class TestReadProvenance:
    def test_yaml_field_primary(self) -> None:
        from scripts.provenance import read_provenance

        result = read_provenance(
            provenance_yaml=PROVENANCE_YAML,
            body_text=TICKET_BODY_WITH_META,
        )
        assert result is not None
        assert result["source_session"] == "5136e38e-efc5-403f-ad5e-49516f47884b"
        assert result["source"] == "yaml"

    def test_comment_fallback_when_no_yaml(self) -> None:
        from scripts.provenance import read_provenance

        result = read_provenance(
            provenance_yaml=None,
            body_text=TICKET_BODY_WITH_META,
        )
        assert result is not None
        assert result["source_session"] == "5136e38e-efc5-403f-ad5e-49516f47884b"
        assert result["source"] == "comment"

    def test_no_provenance_returns_none(self) -> None:
        from scripts.provenance import read_provenance

        result = read_provenance(provenance_yaml=None, body_text=TICKET_BODY_NO_META)
        assert result is None

    def test_yaml_wins_when_both_exist_and_disagree(self) -> None:
        from scripts.provenance import read_provenance

        yaml_data = {"source_session": "aaaa-yaml-wins", "source_type": "codex", "created_by": "defer-skill"}
        result = read_provenance(provenance_yaml=yaml_data, body_text=TICKET_BODY_WITH_META)
        assert result["source_session"] == "aaaa-yaml-wins"
        assert result["source"] == "yaml"


class TestSessionMatch:
    def test_exact_uuid_match(self) -> None:
        from scripts.provenance import session_matches

        assert session_matches("5136e38e-efc5-403f-ad5e-49516f47884b", "5136e38e-efc5-403f-ad5e-49516f47884b")

    def test_no_match(self) -> None:
        from scripts.provenance import session_matches

        assert not session_matches("5136e38e-efc5-403f-ad5e-49516f47884b", "aaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    def test_none_returns_false(self) -> None:
        from scripts.provenance import session_matches

        assert not session_matches(None, "5136e38e-efc5-403f-ad5e-49516f47884b")
        assert not session_matches("5136e38e-efc5-403f-ad5e-49516f47884b", None)

    def test_empty_string_returns_false(self) -> None:
        """P1-7 fix: empty strings must not match each other."""
        from scripts.provenance import session_matches

        assert not session_matches("", "")
        assert not session_matches("", "5136e38e-efc5-403f-ad5e-49516f47884b")
        assert not session_matches("5136e38e-efc5-403f-ad5e-49516f47884b", "")
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_provenance.py -v`
Expected: FAIL

**Step 3: Implement provenance.py**

```python
"""Provenance parsing and session matching for defer-meta and distill-meta.

Dual-read: YAML field (primary) > HTML comment (fallback).
"""
from __future__ import annotations

import json
import re
from typing import Any

_DEFER_META_RE = re.compile(r"<!--\s*defer-meta\s+(\{.*?\})\s*-->")
_DISTILL_META_RE = re.compile(r"<!--\s*distill-meta\s+(\{.*?\})\s*-->")


def parse_defer_meta(text: str) -> dict[str, Any] | None:
    """Extract defer-meta JSON from an HTML comment in text."""
    m = _DEFER_META_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def parse_distill_meta(text: str) -> dict[str, Any] | None:
    """Extract distill-meta JSON from an HTML comment in text."""
    m = _DISTILL_META_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def render_defer_meta(
    source_session: str,
    source_type: str,
    source_ref: str,
) -> str:
    """Render a defer-meta HTML comment string."""
    payload = {
        "v": 1,
        "source_session": source_session,
        "source_type": source_type,
        "source_ref": source_ref,
        "created_by": "defer-skill",
    }
    return f"<!-- defer-meta {json.dumps(payload, separators=(',', ':'), sort_keys=True)} -->"


def read_provenance(
    provenance_yaml: dict[str, Any] | None,
    body_text: str,
) -> dict[str, Any] | None:
    """Read provenance from ticket. YAML field primary, comment fallback.

    Returns dict with source_session, source_type, plus 'source' key
    indicating where data came from ('yaml' or 'comment').
    Returns None if no provenance found.
    """
    # P1-7 fix: truthiness check — guard both None and empty string
    if provenance_yaml and provenance_yaml.get("source_session"):
        return {**provenance_yaml, "source": "yaml"}

    comment_data = parse_defer_meta(body_text)
    if comment_data and "source_session" in comment_data:
        return {**comment_data, "source": "comment"}

    return None


def session_matches(
    ticket_session: str | None,
    handoff_session: str | None,
) -> bool:
    """Check if a ticket's source_session matches a handoff's session_id.

    Full UUID comparison — no truncation.
    P1-7 fix: guard both None AND empty string to prevent false-positive
    uid_match when neither side has a session_id.
    """
    if not ticket_session or not handoff_session:
        return False
    return ticket_session == handoff_session
```

**Step 4: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_provenance.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/provenance.py packages/plugins/handoff/tests/test_provenance.py
git commit -m "feat(handoff): add provenance.py — defer-meta parsing, dual-read, session matching"
```

---

## Task 5: project_paths.py — Add get_archive_dir()

**Files:**
- Modify: `packages/plugins/handoff/scripts/project_paths.py`
- Modify: `packages/plugins/handoff/tests/test_project_paths.py`

**Step 1: Write failing test**

Add to `test_project_paths.py`:

```python
class TestGetArchiveDir:
    def test_returns_archive_subdir(self) -> None:
        from scripts.project_paths import get_archive_dir

        result = get_archive_dir()
        assert result.name == ".archive"
        assert result.parent.name  # has a project parent

    def test_is_child_of_handoffs_dir(self) -> None:
        from scripts.project_paths import get_archive_dir, get_handoffs_dir

        archive = get_archive_dir()
        handoffs = get_handoffs_dir()
        assert archive.parent == handoffs
```

**Step 2: Run test to verify it fails**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_project_paths.py::TestGetArchiveDir -v`
Expected: FAIL

**Step 3: Implement get_archive_dir()**

Add to `project_paths.py`:

```python
def get_archive_dir() -> Path:
    """Return the archive directory for the current project's handoffs."""
    return get_handoffs_dir() / ".archive"
```

**Step 4: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_project_paths.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/project_paths.py packages/plugins/handoff/tests/test_project_paths.py
git commit -m "feat(handoff): add get_archive_dir() to project_paths.py"
```

---

## Task 6: defer.py — Ticket ID Allocation and Rendering

**Files:**
- Create: `packages/plugins/handoff/scripts/defer.py`
- Create: `packages/plugins/handoff/tests/test_defer.py`

**Step 1: Write failing tests**

```python
"""Tests for defer.py — ticket creation logic."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


# --- Fixtures ---

EXISTING_TICKET = """\
# T-20260228-01: Existing ticket

```yaml
id: T-20260228-01
date: 2026-02-28
status: open
priority: medium
```

## Problem

Already exists.
"""


class TestAllocateId:
    def test_first_ticket_of_day(self, tmp_path: Path) -> None:
        from scripts.defer import allocate_id

        result = allocate_id("2026-02-28", tmp_path)
        assert result == "T-20260228-01"

    def test_increments_past_existing(self, tmp_path: Path) -> None:
        from scripts.defer import allocate_id

        ticket = tmp_path / "existing.md"
        ticket.write_text(EXISTING_TICKET)
        result = allocate_id("2026-02-28", tmp_path)
        assert result == "T-20260228-02"

    def test_handles_multiple_existing(self, tmp_path: Path) -> None:
        from scripts.defer import allocate_id

        for i in range(1, 4):
            ticket = tmp_path / f"ticket-{i}.md"
            ticket.write_text(
                EXISTING_TICKET.replace("T-20260228-01", f"T-20260228-{i:02d}")
            )
        result = allocate_id("2026-02-28", tmp_path)
        assert result == "T-20260228-04"

    def test_ignores_different_date(self, tmp_path: Path) -> None:
        from scripts.defer import allocate_id

        ticket = tmp_path / "old.md"
        ticket.write_text(EXISTING_TICKET.replace("20260228", "20260227"))
        result = allocate_id("2026-02-28", tmp_path)
        assert result == "T-20260228-01"

    def test_ignores_legacy_ids(self, tmp_path: Path) -> None:
        from scripts.defer import allocate_id

        ticket = tmp_path / "legacy.md"
        ticket.write_text(EXISTING_TICKET.replace("T-20260228-01", "T-A"))
        result = allocate_id("2026-02-28", tmp_path)
        assert result == "T-20260228-01"


class TestRenderTicket:
    def test_renders_minimal_ticket(self) -> None:
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Section.level is always 2",
            "problem": "Dead field creates false generality.",
            "source_text": "PR #29 review, type-design-analyzer finding.",
            "proposed_approach": "Remove level field from Section dataclass.",
            "acceptance_criteria": ["Section has no level field", "All tests pass"],
            "priority": "medium",
            "source_type": "pr-review",
            "source_ref": "PR #29",
            "branch": "feature/knowledge-graduation",
            "session_id": "5136e38e-efc5-403f-ad5e-49516f47884b",
            "effort": "XS",
            "files": ["scripts/handoff_parsing.py"],
        }
        result = render_ticket(candidate)

        # Check structure
        assert result.startswith("# T-20260228-01:")
        assert "```yaml" in result
        assert "id: T-20260228-01" in result
        assert "status: deferred" in result
        assert "## Problem" in result
        assert "## Source" in result
        assert "## Proposed Approach" in result
        assert "## Acceptance Criteria" in result
        assert "- [ ] Section has no level field" in result
        assert "defer-meta" in result  # HTML comment
        assert "provenance:" in result  # YAML field

    def test_renders_provenance_yaml_field(self) -> None:
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "Test problem.",
            "source_text": "Test source.",
            "proposed_approach": "Test approach.",
            "acceptance_criteria": ["Done"],
            "priority": "medium",
            "source_type": "pr-review",
            "source_ref": "PR #29",
            "branch": "main",
            "session_id": "aaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "effort": "XS",
            "files": [],
        }
        result = render_ticket(candidate)
        assert "source_session: " in result
        assert "aaaa-bbbb-cccc-dddd-eeeeeeeeeeee" in result


class TestFilenameSlug:
    def test_generates_slug(self) -> None:
        from scripts.defer import filename_slug

        # P2-1 fix: period is stripped by [^a-z0-9\s-] regex, producing "sectionlevel"
        result = filename_slug("T-20260228-01", "Section.level is always 2 — dead field")
        assert result == "2026-02-28-T-20260228-01-sectionlevel-is-always-2-dead-field.md"

    def test_truncates_long_titles(self) -> None:
        from scripts.defer import filename_slug

        result = filename_slug("T-20260228-01", "A" * 100)
        assert len(result) <= 80  # reasonable filename length

    def test_handles_special_characters(self) -> None:
        from scripts.defer import filename_slug

        result = filename_slug("T-20260228-01", "Fix `Section.level` / remove dead field!")
        assert "`" not in result
        assert "/" not in result
        assert "!" not in result


class TestWriteTicket:
    """P2-3: Unit test for write_ticket (was only tested in Task 13 integration)."""

    def test_creates_file_with_correct_content(self, tmp_path: Path) -> None:
        from scripts.defer import write_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test ticket",
            "problem": "Test problem.",
            "source_text": "Test source.",
            "proposed_approach": "Test approach.",
            "acceptance_criteria": ["Done"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "branch": "main",
            "session_id": "aaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "effort": "S",
            "files": [],
        }
        path = write_ticket(candidate, tmp_path)
        assert path.exists()
        content = path.read_text()
        assert "id: T-20260228-01" in content
        assert "status: deferred" in content
        assert "defer-meta" in content

    def test_creates_directory_if_missing(self, tmp_path: Path) -> None:
        from scripts.defer import write_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "session_id": "",
        }
        tickets_dir = tmp_path / "nested" / "tickets"
        path = write_ticket(candidate, tickets_dir)
        assert tickets_dir.exists()
        assert path.exists()
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py -v`
Expected: FAIL

**Step 3: Implement defer.py**

```python
"""Ticket creation logic for /defer skill.

Deterministic: allocates IDs, renders markdown, writes files.
LLM extraction happens in the SKILL.md — this script receives candidates.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.ticket_parsing import parse_ticket
    from scripts.provenance import render_defer_meta
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.ticket_parsing import parse_ticket  # type: ignore[no-redef]
    from scripts.provenance import render_defer_meta  # type: ignore[no-redef]

_DATE_ID_RE = re.compile(r"^T-(\d{8})-(\d{2})$")


def allocate_id(date_str: str, tickets_dir: Path) -> str:
    """Allocate the next ticket ID for a given date.

    Scans all .md files in tickets_dir, parses their YAML to extract id fields,
    finds the highest sequence number for the date, and returns the next one.
    """
    date_compact = date_str.replace("-", "")
    max_seq = 0

    if tickets_dir.exists():
        for path in sorted(tickets_dir.glob("*.md")):  # P2-10: deterministic order
            ticket = parse_ticket(path)
            if ticket is None:
                import warnings
                warnings.warn(f"Skipping malformed ticket: {path}", stacklevel=2)  # P2-11
                continue
            tid = ticket.frontmatter.get("id", "")
            m = _DATE_ID_RE.match(str(tid))
            if m and m.group(1) == date_compact:
                max_seq = max(max_seq, int(m.group(2)))

    return f"T-{date_compact}-{max_seq + 1:02d}"


def filename_slug(ticket_id: str, summary: str) -> str:
    """Generate a filename from ticket ID and summary.

    Format: YYYY-MM-DD-T-YYYYMMDD-NN-slug.md
    Slug: lowercase, alphanumeric + hyphens, max 50 chars.
    """
    m = _DATE_ID_RE.match(ticket_id)
    date_part = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:8]}" if m else "unknown"

    slug = re.sub(r"[^a-z0-9\s-]", "", summary.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)[:50].rstrip("-")

    return f"{date_part}-{ticket_id}-{slug}.md"


_VALID_PRIORITIES = {"low", "medium", "high", "critical"}  # P1-9
_VALID_EFFORTS = {"XS", "S", "M", "L", "XL"}  # P1-9


def render_ticket(candidate: dict[str, Any]) -> str:
    """Render a ticket markdown file from a candidate dict."""
    tid = candidate["id"]
    date = candidate["date"]
    summary = candidate["summary"]
    problem = candidate["problem"]
    source_text = candidate["source_text"]
    proposed = candidate["proposed_approach"]
    criteria = candidate["acceptance_criteria"]
    priority = candidate.get("priority", "medium")
    source_type = candidate.get("source_type", "ad-hoc")
    source_ref = candidate.get("source_ref", "")
    branch = candidate.get("branch", "")
    session_id = candidate.get("session_id", "")
    effort = candidate.get("effort", "S")
    files = candidate.get("files", [])

    # P1-9 fix: validate enum values before rendering
    if priority not in _VALID_PRIORITIES:
        priority = "medium"
    if effort not in _VALID_EFFORTS:
        effort = "S"

    def _quote(val: str) -> str:
        """Quote a YAML string value if it contains special characters.

        P1-5 fix: values with colons, quotes, or leading special chars
        need quoting to produce valid YAML.
        """
        if not val:
            return '""'
        if any(c in val for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'")):
            escaped = val.replace('"', '\\"')
            return f'"{escaped}"'
        return val

    # Build YAML frontmatter
    yaml_lines = [
        f"id: {tid}",
        f"date: \"{date}\"",
        "status: deferred",
        f"priority: {_quote(priority)}",  # P1-9 fix: quote to prevent invalid YAML
        f"source_type: {_quote(source_type)}",
        f"source_ref: {_quote(source_ref)}",
        f"branch: {_quote(branch)}",
        "blocked_by: []",
        "blocks: []",
        f"effort: {_quote(effort)}",  # P1-9 fix: quote to prevent invalid YAML
    ]

    if files:
        yaml_lines.append("files:")
        for f in files:
            yaml_lines.append(f"  - {_quote(f)}")

    yaml_lines.append("provenance:")
    # P1-7 fix: write null instead of empty string for session_id
    if session_id:
        yaml_lines.append(f'  source_session: "{session_id}"')
    else:
        yaml_lines.append("  source_session: ~")
    yaml_lines.append(f"  source_type: {_quote(source_type)}")
    yaml_lines.append("  created_by: defer-skill")

    yaml_block = "\n".join(yaml_lines)

    # Build body sections
    criteria_lines = "\n".join(f"- [ ] {c}" for c in criteria)
    meta_comment = render_defer_meta(session_id, source_type, source_ref)

    # P2-9 fix: omit empty Branch:/Session: lines instead of rendering empty backticks
    source_suffix_parts: list[str] = []
    if branch:
        source_suffix_parts.append(f"Branch: `{branch}`.")
    if session_id:
        source_suffix_parts.append(f"Session: `{session_id}`.")
    source_suffix = " ".join(source_suffix_parts)

    return f"""\
# {tid}: {summary}

```yaml
{yaml_block}
```

## Problem

{problem}

## Source

{source_text}
{source_suffix}

## Proposed Approach

{proposed}

## Acceptance Criteria

{criteria_lines}

{meta_comment}
"""


def write_ticket(candidate: dict[str, Any], tickets_dir: Path) -> Path:
    """Write a rendered ticket to disk. Returns the path of the created file."""
    content = render_ticket(candidate)
    slug = filename_slug(candidate["id"], candidate["summary"])
    path = tickets_dir / slug
    tickets_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Reads candidate JSON from stdin, writes ticket files."""
    import argparse

    parser = argparse.ArgumentParser(description="Create deferred work tickets")
    parser.add_argument("--tickets-dir", type=Path, default=Path("docs/tickets"))
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    args = parser.parse_args(argv)

    candidates = json.load(sys.stdin)
    if not isinstance(candidates, list):
        candidates = [candidates]

    created: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    for cand in candidates:
        try:
            tid = allocate_id(args.date, args.tickets_dir)
            cand["id"] = tid
            cand["date"] = args.date
            path = write_ticket(cand, args.tickets_dir)
            created.append({"id": tid, "path": str(path)})
        except Exception as exc:
            errors.append({"summary": cand.get("summary", "unknown"), "error": str(exc)})

    if errors and created:
        json.dump({"status": "partial_success", "created": created, "errors": errors}, sys.stdout)
    elif errors:
        json.dump({"status": "error", "created": [], "errors": errors}, sys.stdout)
    else:
        json.dump({"status": "ok", "created": created}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py -v`
Expected: all PASS

**Step 5: Run full suite**

Run: `cd packages/plugins/handoff && uv run pytest -q`
Expected: all pass

**Step 6: Commit**

```bash
git add packages/plugins/handoff/scripts/defer.py packages/plugins/handoff/tests/test_defer.py
git commit -m "feat(handoff): add defer.py — ticket ID allocation, rendering, and file writing"
```

---

## Task 7: triage.py — Ticket Reading and Status Normalization

**Files:**
- Create: `packages/plugins/handoff/scripts/triage.py`
- Create: `packages/plugins/handoff/tests/test_triage.py`

**Step 1: Write failing tests for status normalization and ticket reading**

```python
"""Tests for triage.py — ticket reading, status normalization, orphan detection."""
from __future__ import annotations

from pathlib import Path

import pytest

TICKET_DEFERRED = """\
# T-20260228-01: Deferred ticket

```yaml
id: T-20260228-01
date: 2026-02-28
status: deferred
priority: medium
```

## Problem

Not triaged yet.
"""

TICKET_DONE = """\
# T-20260228-02: Done ticket

```yaml
id: T-20260228-02
date: 2026-02-28
status: done
priority: low
```

## Problem

Already done.
"""

TICKET_LEGACY_COMPLETE = """\
# T-004: Legacy complete

```yaml
id: T-004
date: 2026-02-17
status: complete
priority: medium
```

## Summary

Legacy ticket.
"""

TICKET_LEGACY_PLANNING = """\
# handoff-search: Planning ticket

```yaml
id: handoff-search
date: 2026-02-24
status: planning
priority: medium
```

## Problem

Still planning.
"""


class TestNormalizeStatus:
    def test_known_statuses_pass_through(self) -> None:
        from scripts.triage import normalize_status

        for s in ("deferred", "open", "in_progress", "blocked", "done", "wontfix"):
            norm, conf = normalize_status(s)
            assert norm == s
            assert conf == "high"

    def test_complete_maps_to_done(self) -> None:
        from scripts.triage import normalize_status

        norm, conf = normalize_status("complete")
        assert norm == "done"
        assert conf == "high"

    def test_implemented_maps_to_done(self) -> None:
        from scripts.triage import normalize_status

        norm, conf = normalize_status("implemented")
        assert norm == "done"
        assert conf == "high"

    def test_closed_maps_to_done_medium(self) -> None:
        from scripts.triage import normalize_status

        norm, conf = normalize_status("closed")
        assert norm == "done"
        assert conf == "medium"

    def test_planning_maps_to_open_medium(self) -> None:
        from scripts.triage import normalize_status

        norm, conf = normalize_status("planning")
        assert norm == "open"
        assert conf == "medium"

    def test_implementing_maps_to_in_progress(self) -> None:
        from scripts.triage import normalize_status

        norm, conf = normalize_status("implementing")
        assert norm == "in_progress"
        assert conf == "high"

    def test_unknown_status_returns_open_low(self) -> None:
        from scripts.triage import normalize_status

        norm, conf = normalize_status("something-weird")
        assert norm == "open"
        assert conf == "low"


class TestReadOpenTickets:
    def test_filters_out_done_and_wontfix(self, tmp_path: Path) -> None:
        from scripts.triage import read_open_tickets

        (tmp_path / "a.md").write_text(TICKET_DEFERRED)
        (tmp_path / "b.md").write_text(TICKET_DONE)
        result = read_open_tickets(tmp_path)
        assert len(result) == 1
        assert result[0]["id"] == "T-20260228-01"

    def test_includes_normalized_status(self, tmp_path: Path) -> None:
        from scripts.triage import read_open_tickets

        (tmp_path / "a.md").write_text(TICKET_LEGACY_COMPLETE)
        (tmp_path / "b.md").write_text(TICKET_LEGACY_PLANNING)
        result = read_open_tickets(tmp_path)
        # complete → done (filtered out), planning → open (kept)
        assert len(result) == 1
        assert result[0]["id"] == "handoff-search"
        assert result[0]["status_raw"] == "planning"
        assert result[0]["status_normalized"] == "open"
        assert result[0]["normalization_confidence"] == "medium"

    def test_empty_dir(self, tmp_path: Path) -> None:
        from scripts.triage import read_open_tickets

        result = read_open_tickets(tmp_path)
        assert result == []

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        from scripts.triage import read_open_tickets

        result = read_open_tickets(tmp_path / "nonexistent")
        assert result == []

    def test_skips_malformed_tickets(self, tmp_path: Path) -> None:
        from scripts.triage import read_open_tickets

        (tmp_path / "good.md").write_text(TICKET_DEFERRED)
        (tmp_path / "bad.md").write_text("# No YAML here\n\nJust text.")
        result = read_open_tickets(tmp_path)
        assert len(result) == 1
```

**Step 2: Run to verify failure**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_triage.py::TestNormalizeStatus tests/test_triage.py::TestReadOpenTickets -v`
Expected: FAIL

**Step 3: Implement**

```python
"""Ticket reading, status normalization, and orphan detection for /triage skill.

Phase 0: read-only. Produces JSON report.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from scripts.ticket_parsing import parse_ticket
    from scripts.provenance import read_provenance, session_matches
    from scripts.handoff_parsing import parse_frontmatter, parse_sections
    from scripts.project_paths import get_handoffs_dir, get_archive_dir
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.ticket_parsing import parse_ticket  # type: ignore[no-redef]
    from scripts.provenance import read_provenance, session_matches  # type: ignore[no-redef]
    from scripts.handoff_parsing import parse_frontmatter, parse_sections  # type: ignore[no-redef]
    from scripts.project_paths import get_handoffs_dir, get_archive_dir  # type: ignore[no-redef]

# 6-state enum
_CANONICAL_STATUSES = {"deferred", "open", "in_progress", "blocked", "done", "wontfix"}
_TERMINAL_STATUSES = {"done", "wontfix"}

_NORMALIZATION_MAP: dict[str, tuple[str, str]] = {
    "complete": ("done", "high"),
    "implemented": ("done", "high"),
    "closed": ("done", "medium"),
    "planning": ("open", "medium"),
    "implementing": ("in_progress", "high"),
}


def normalize_status(raw: str) -> tuple[str, str]:
    """Normalize a ticket status to the 6-state enum.

    Returns (normalized_status, confidence) where confidence is high/medium/low.
    """
    if raw in _CANONICAL_STATUSES:
        return raw, "high"
    if raw in _NORMALIZATION_MAP:
        return _NORMALIZATION_MAP[raw]
    return "open", "low"


def read_open_tickets(tickets_dir: Path) -> list[dict[str, Any]]:
    """Read all non-terminal tickets from a directory.

    Returns list of dicts with: id, date, priority, status_raw,
    status_normalized, normalization_confidence, summary, path.
    """
    if not tickets_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for path in sorted(tickets_dir.glob("*.md")):
        ticket = parse_ticket(path)
        if ticket is None:
            continue

        fm = ticket.frontmatter
        raw_status = str(fm.get("status", "open"))
        norm_status, confidence = normalize_status(raw_status)

        if norm_status in _TERMINAL_STATUSES:
            continue

        results.append({
            "id": fm["id"],
            "date": fm.get("date", ""),
            "priority": fm.get("priority", "medium"),
            "status_raw": raw_status,
            "status_normalized": norm_status,
            "normalization_confidence": confidence,
            "summary": str(path.stem),
            "path": str(path),
        })

    return results
```

**Step 4: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_triage.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/triage.py packages/plugins/handoff/tests/test_triage.py
git commit -m "feat(handoff): add triage.py — ticket reading and status normalization"
```

---

## Task 8: triage.py — Handoff Scanning and Orphan Detection

**Files:**
- Modify: `packages/plugins/handoff/scripts/triage.py`
- Modify: `packages/plugins/handoff/tests/test_triage.py`

**Step 1: Write failing tests for handoff scanning and orphan detection**

Add to `test_triage.py`:

```python
import re

HANDOFF_WITH_OPEN_QUESTIONS = """\
---
title: Test handoff
date: 2026-02-28
session_id: aaaa-bbbb-cccc-dddd-eeeeeeeeeeee
---

## Decisions

Some decision.

## Open Questions

- Should we refactor the parser?
- Is T-20260228-01 still relevant?
- What about the auth module?

## Risks

- Deadline is tight
- T-004 may block this work
"""

HANDOFF_NO_OPEN_QUESTIONS = """\
---
title: Clean handoff
date: 2026-02-28
session_id: ffff-0000-1111-2222-333344445555
---

## Decisions

Clean session.
"""

TICKET_WITH_PROVENANCE = """\
# T-20260228-03: Ticket with provenance

```yaml
id: T-20260228-03
date: 2026-02-28
status: deferred
priority: medium
provenance:
  source_session: "aaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  source_type: handoff
  created_by: defer-skill
```

## Problem

Has provenance.

<!-- defer-meta {"v":1,"source_session":"aaaa-bbbb-cccc-dddd-eeeeeeeeeeee","source_type":"handoff","source_ref":"test","created_by":"defer-skill"} -->
"""


class TestExtractHandoffItems:
    def test_extracts_list_items_from_open_questions(self) -> None:
        from scripts.triage import extract_handoff_items

        items, skipped = extract_handoff_items(HANDOFF_WITH_OPEN_QUESTIONS, "test.md")
        questions = [i for i in items if i["section"] == "Open Questions"]
        assert len(questions) == 3
        assert "refactor the parser" in questions[0]["text"]

    def test_extracts_list_items_from_risks(self) -> None:
        from scripts.triage import extract_handoff_items

        items, skipped = extract_handoff_items(HANDOFF_WITH_OPEN_QUESTIONS, "test.md")
        risks = [i for i in items if i["section"] == "Risks"]
        assert len(risks) == 2

    def test_returns_empty_for_no_sections(self) -> None:
        from scripts.triage import extract_handoff_items

        items, skipped = extract_handoff_items(HANDOFF_NO_OPEN_QUESTIONS, "clean.md")
        assert items == []

    def test_includes_session_id(self) -> None:
        from scripts.triage import extract_handoff_items

        items, skipped = extract_handoff_items(HANDOFF_WITH_OPEN_QUESTIONS, "test.md")
        assert all(i["session_id"] == "aaaa-bbbb-cccc-dddd-eeeeeeeeeeee" for i in items)

    def test_returns_skipped_prose_count(self) -> None:
        """P1-4: Verify prose lines are counted, not extracted."""
        from scripts.triage import extract_handoff_items

        handoff_with_prose = """\
---
title: Prose test
session_id: test-session
---

## Open Questions

- List item one
Some prose paragraph that is not a list item.
- List item two
"""
        items, skipped = extract_handoff_items(handoff_with_prose, "prose.md")
        assert len(items) == 2
        assert skipped >= 1


class TestMatchOrphans:
    def test_uid_match(self, tmp_path: Path) -> None:
        from scripts.triage import match_orphan_item

        (tmp_path / "ticket.md").write_text(TICKET_WITH_PROVENANCE)
        tickets = _load_all_tickets(tmp_path)

        item = {
            "text": "Should we refactor?",
            "section": "Open Questions",
            "session_id": "aaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "handoff": "test.md",
        }
        result = match_orphan_item(item, tickets)
        assert result["match_type"] == "uid_match"
        assert result["matched_ticket"] == "T-20260228-03"

    def test_ticket_id_reference(self, tmp_path: Path) -> None:
        from scripts.triage import match_orphan_item

        (tmp_path / "ticket.md").write_text(TICKET_DEFERRED)
        tickets = _load_all_tickets(tmp_path)

        item = {
            "text": "Is T-20260228-01 still relevant?",
            "section": "Open Questions",
            "session_id": "no-match-session",
            "handoff": "test.md",
        }
        result = match_orphan_item(item, tickets)
        assert result["match_type"] == "id_ref"

    def test_manual_review_fallback(self, tmp_path: Path) -> None:
        from scripts.triage import match_orphan_item

        (tmp_path / "ticket.md").write_text(TICKET_DEFERRED)
        tickets = _load_all_tickets(tmp_path)

        item = {
            "text": "What about the auth module?",
            "section": "Open Questions",
            "session_id": "no-match",
            "handoff": "test.md",
        }
        result = match_orphan_item(item, tickets)
        assert result["match_type"] == "manual_review"

    def test_legacy_ticket_id_match(self, tmp_path: Path) -> None:
        from scripts.triage import match_orphan_item

        (tmp_path / "legacy.md").write_text(TICKET_LEGACY_COMPLETE)
        tickets = _load_all_tickets(tmp_path)

        item = {
            "text": "T-004 may block this work",
            "section": "Risks",
            "session_id": "irrelevant",
            "handoff": "test.md",
        }
        result = match_orphan_item(item, tickets)
        assert result["match_type"] == "id_ref"


    def test_hyphenated_handoff_id_match(self, tmp_path: Path) -> None:
        """P1-11 fix: handoff-quality-hook should match, not truncate to handoff-quality."""
        from scripts.triage import match_orphan_item

        # Create a ticket with a hyphenated handoff-style ID
        handoff_ticket = TICKET_DEFERRED.replace("T-20260228-01", "handoff-quality-hook")
        (tmp_path / "hqh.md").write_text(handoff_ticket)
        tickets = _load_all_tickets(tmp_path)

        item = {
            "text": "handoff-quality-hook needs review",
            "section": "Open Questions",
            "session_id": "no-match",
            "handoff": "test.md",
        }
        result = match_orphan_item(item, tickets)
        assert result["match_type"] == "id_ref"
        assert result["matched_ticket"] == "handoff-quality-hook"


def _load_all_tickets(tickets_dir: Path) -> list[dict]:
    """Helper to load all tickets for matching tests."""
    from scripts.triage import _load_tickets_for_matching
    return _load_tickets_for_matching(tickets_dir)
```

**Step 2: Run to verify failure**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_triage.py::TestExtractHandoffItems tests/test_triage.py::TestMatchOrphans -v`
Expected: FAIL

**Step 3: Implement handoff scanning and orphan detection**

Add to `triage.py`:

```python
import re

# Ticket ID patterns — union of new + legacy formats
_TICKET_ID_PATTERNS = [
    r"T-\d{8}-\d{2}",      # new: T-20260228-01
    r"T-\d{3}",             # legacy numeric: T-004
    r"T-[A-F]",             # legacy alpha: T-A (P3-5: covers current A-F corpus only)
    r"handoff-[\w-]+",      # P1-11 fix: legacy noun — supports hyphens (handoff-quality-hook)
]
_TICKET_ID_RE = re.compile(r"\b(?:" + "|".join(_TICKET_ID_PATTERNS) + r")\b")

_LIST_ITEM_RE = re.compile(r"^[-*]\s+(.+)$|^(\d+)\.\s+(.+)$", re.MULTILINE)


def _section_name(heading: str) -> str:
    """Strip the '## ' prefix from a section heading.

    parse_sections stores headings as '## Open Questions' (with prefix).
    Matches the pattern in distill.py:_section_name.
    """
    if heading.startswith("## "):
        return heading[3:].strip()
    return heading.strip()


def extract_handoff_items(handoff_text: str, handoff_filename: str) -> tuple[list[dict[str, Any]], int]:
    """Extract structured list items from Open Questions and Risks sections.

    Returns (items, skipped_prose_count).
    Only extracts lines starting with - or numbered items.
    Skips prose paragraphs (counted via skipped_prose_count).
    Skips handoffs without these sections.

    Note: uid_match based on session_id is a session-level correlation signal,
    not an item-level match. All items from the same handoff share the same
    session_id, so a uid_match means "this handoff produced a ticket", not
    "this specific item was deferred." (P1-2)
    """
    # P0-1 fix: parse_frontmatter returns tuple[dict, str], not dict
    fm, body = parse_frontmatter(handoff_text)
    session_id = fm.get("session_id", "")

    # P0-1 fix: use body (frontmatter stripped) for parse_sections
    sections = parse_sections(body)
    target_sections = {"Open Questions", "Risks"}

    items: list[dict[str, Any]] = []
    skipped_prose_count = 0
    for section in sections:
        # P0-2 fix: strip '## ' prefix before comparison
        name = _section_name(section.heading)
        if name not in target_sections:
            continue
        for line in section.content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            m = _LIST_ITEM_RE.match(line)
            if m:
                text = m.group(1) or m.group(3) or ""
                text = text.strip()
                if text:
                    items.append({
                        "text": text,
                        "section": name,
                        "session_id": session_id,
                        "handoff": handoff_filename,
                    })
            else:
                # P1-4: count skipped prose lines
                skipped_prose_count += 1
    return items, skipped_prose_count


def _load_tickets_for_matching(tickets_dir: Path) -> list[dict[str, Any]]:
    """Load all tickets with their provenance for matching."""
    results: list[dict[str, Any]] = []
    if not tickets_dir.exists():
        return results

    for path in sorted(tickets_dir.glob("*.md")):  # P2-10 fix: deterministic iteration order
        ticket = parse_ticket(path)
        if ticket is None:
            continue

        fm = ticket.frontmatter
        prov = read_provenance(
            provenance_yaml=fm.get("provenance"),
            body_text=ticket.body,
        )
        results.append({
            "id": fm["id"],
            "provenance": prov,
            "path": str(path),
        })
    return results


def match_orphan_item(
    item: dict[str, Any],
    tickets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Match a handoff item against existing tickets.

    Returns dict with match_type (uid_match, id_ref, manual_review)
    and matched_ticket (if matched).
    """
    # Strategy 1: UID match — session_id → provenance.source_session
    for ticket in tickets:
        prov = ticket.get("provenance")
        if prov and session_matches(prov.get("source_session"), item.get("session_id")):
            return {
                "match_type": "uid_match",
                "matched_ticket": ticket["id"],
                "item": item,
            }

    # Strategy 2: Ticket ID reference in item text
    found_ids = set(_TICKET_ID_RE.findall(item.get("text", "")))
    ticket_ids = {t["id"] for t in tickets}
    matched = found_ids & ticket_ids
    if matched:
        return {
            "match_type": "id_ref",
            "matched_ticket": sorted(matched)[0],  # P2-7 fix: deterministic alphabetic order
            "item": item,
        }

    # Strategy 3: Manual review
    return {
        "match_type": "manual_review",
        "matched_ticket": None,
        "item": item,
    }
```

**Step 4: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_triage.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/triage.py packages/plugins/handoff/tests/test_triage.py
git commit -m "feat(handoff): add handoff scanning and orphan detection to triage.py"
```

---

## Task 9: triage.py — JSON Report and CLI

**Files:**
- Modify: `packages/plugins/handoff/scripts/triage.py`
- Modify: `packages/plugins/handoff/tests/test_triage.py`

**Step 1: Write failing tests for report generation and CLI**

Add to `test_triage.py`:

```python
import json


class TestGenerateReport:
    def test_report_structure(self, tmp_path: Path) -> None:
        from scripts.triage import generate_report

        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()
        (tickets_dir / "a.md").write_text(TICKET_DEFERRED)

        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()
        (handoffs_dir / "test.md").write_text(HANDOFF_WITH_OPEN_QUESTIONS)

        report = generate_report(tickets_dir, handoffs_dir)
        assert "open_tickets" in report
        assert "orphaned_items" in report
        assert "matched_items" in report
        assert "match_counts" in report
        assert "skipped_prose_count" in report

    def test_match_counts_reflect_actual_matching(self, tmp_path: Path) -> None:
        """P2-2 fix: assert specific count values, not identity."""
        from scripts.triage import generate_report

        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()
        (tickets_dir / "a.md").write_text(TICKET_DEFERRED)
        (tickets_dir / "b.md").write_text(TICKET_WITH_PROVENANCE)

        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()
        (handoffs_dir / "test.md").write_text(HANDOFF_WITH_OPEN_QUESTIONS)

        report = generate_report(tickets_dir, handoffs_dir)
        counts = report["match_counts"]
        # HANDOFF_WITH_OPEN_QUESTIONS has 5 items (3 Open Questions + 2 Risks)
        # Session_id matches TICKET_WITH_PROVENANCE → all 5 items get uid_match
        # P2-8 fix: exact counts for deterministic fixture, not >= 1
        assert counts["uid_match"] == 5, "All 5 items should uid_match via session correlation"
        assert counts["id_ref"] == 0, "uid_match takes priority over id_ref"
        assert counts["manual_review"] == 0, "All items matched via uid_match"
        # P1-1: orphaned_items only contains manual_review items
        assert len(report["orphaned_items"]) == counts["manual_review"]
        # matched_items contains uid_match + id_ref
        assert len(report["matched_items"]) == counts["uid_match"] + counts["id_ref"]

    def test_empty_dirs(self, tmp_path: Path) -> None:
        from scripts.triage import generate_report

        report = generate_report(tmp_path / "no-tickets", tmp_path / "no-handoffs")
        assert report["open_tickets"] == []
        assert report["orphaned_items"] == []
        assert report["matched_items"] == []

    def test_includes_archive(self, tmp_path: Path) -> None:
        from scripts.triage import generate_report

        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()

        handoffs_dir = tmp_path / "handoffs"
        archive_dir = handoffs_dir / ".archive"
        archive_dir.mkdir(parents=True)
        (archive_dir / "archived.md").write_text(HANDOFF_WITH_OPEN_QUESTIONS)

        report = generate_report(tickets_dir, handoffs_dir)
        # Should find items from archived handoff (all manual_review since no matching tickets)
        assert len(report["orphaned_items"]) > 0

    def test_excludes_old_files(self, tmp_path: Path) -> None:
        """P1-10 fix: files older than 30 days should be excluded by mtime filter."""
        import os
        import time

        from scripts.triage import generate_report

        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()

        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()
        old_file = handoffs_dir / "old.md"
        old_file.write_text(HANDOFF_WITH_OPEN_QUESTIONS)

        # Set mtime to 31 days ago
        old_mtime = time.time() - (31 * 86400)
        os.utime(old_file, (old_mtime, old_mtime))

        report = generate_report(tickets_dir, handoffs_dir)
        assert len(report["orphaned_items"]) == 0, "Files older than 30 days should be excluded"


class TestMain:
    def test_json_output(self, tmp_path: Path, capsys) -> None:
        from scripts.triage import main

        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()
        (tickets_dir / "a.md").write_text(TICKET_DEFERRED)

        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()

        main(["--tickets-dir", str(tickets_dir), "--handoffs-dir", str(handoffs_dir)])
        output = capsys.readouterr().out
        report = json.loads(output)
        assert report["open_tickets"][0]["id"] == "T-20260228-01"
```

**Step 2: Run to verify failure**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_triage.py::TestGenerateReport tests/test_triage.py::TestMain -v`
Expected: FAIL

**Step 3: Implement generate_report and main**

Add to `triage.py`:

```python
import argparse
import json


import time

_LOOKBACK_DAYS = 30  # P1-3: design requires 30-day scan window


def _scan_handoff_dirs(handoffs_dir: Path) -> list[Path]:
    """Collect handoff files from active and archive directories.

    P1-3 fix: filters to files modified within the last _LOOKBACK_DAYS days.
    """
    cutoff = time.time() - (_LOOKBACK_DAYS * 86400)
    paths: list[Path] = []

    for search_dir in [handoffs_dir, handoffs_dir / ".archive"]:
        if not search_dir.exists():
            continue
        for p in sorted(search_dir.glob("*.md")):
            try:
                if p.stat().st_mtime >= cutoff:
                    paths.append(p)
            except OSError:
                continue
    return paths


def generate_report(
    tickets_dir: Path,
    handoffs_dir: Path,
) -> dict[str, Any]:
    """Generate a triage report: open tickets + orphaned handoff items.

    Returns dict with: open_tickets, orphaned_items, matched_items,
    match_counts, skipped_prose_count.

    P1-1 fix: orphaned_items contains only manual_review items.
    Matched items (uid_match, id_ref) go to matched_items.

    Note: read_open_tickets and _load_tickets_for_matching both scan tickets_dir,
    parsing each file twice. Acceptable for current corpus size. (P3-6)
    """
    open_tickets = read_open_tickets(tickets_dir)
    tickets_for_matching = _load_tickets_for_matching(tickets_dir)

    # Scan handoffs
    all_items: list[dict[str, Any]] = []
    total_skipped_prose = 0
    for path in _scan_handoff_dirs(handoffs_dir):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        items, skipped = extract_handoff_items(text, path.name)
        all_items.extend(items)
        total_skipped_prose += skipped

    # Match each item — separate orphaned from matched (P1-1)
    orphaned: list[dict[str, Any]] = []
    matched: list[dict[str, Any]] = []
    counts = {"uid_match": 0, "id_ref": 0, "manual_review": 0}
    for item in all_items:
        result = match_orphan_item(item, tickets_for_matching)
        counts[result["match_type"]] += 1
        if result["match_type"] == "manual_review":
            orphaned.append(result)
        else:
            matched.append(result)

    return {
        "open_tickets": open_tickets,
        "orphaned_items": orphaned,
        "matched_items": matched,
        "match_counts": counts,
        "skipped_prose_count": total_skipped_prose,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Outputs JSON triage report to stdout."""
    parser = argparse.ArgumentParser(description="Triage open tickets and orphaned items")
    parser.add_argument("--tickets-dir", type=Path, default=Path("docs/tickets"))
    parser.add_argument("--handoffs-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.handoffs_dir is None:
        args.handoffs_dir = get_handoffs_dir()

    report = generate_report(args.tickets_dir, args.handoffs_dir)
    json.dump(report, sys.stdout, indent=2)
    print()  # trailing newline
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_triage.py -v`
Expected: all PASS

**Step 5: Run full suite**

Run: `cd packages/plugins/handoff && uv run pytest -q`
Expected: all pass

**Step 6: Commit**

```bash
git add packages/plugins/handoff/scripts/triage.py packages/plugins/handoff/tests/test_triage.py
git commit -m "feat(handoff): add triage report generation and CLI"
```

---

## Task 10: /defer SKILL.md

**Files:**
- Create: `packages/plugins/handoff/skills/defer/SKILL.md`

**Pre-read:** `.claude/rules/skills.md` for skill authoring rules.

**Step 1: Write the SKILL.md**

The SKILL.md follows the pattern from `distill/SKILL.md`. Key behaviors:
- LLM extracts candidates from conversation context using hybrid heuristics
- Presents candidates with evidence anchors and "possible misses"
- Calls `defer.py` via Python to create tickets
- Commits created files

See design doc `docs/plans/2026-02-28-deferred-work-tracking-design.md` sections:
- `/defer` Skill Design (procedure, extraction heuristics, failure modes)
- Extraction reliability model (best-effort assistant)

The SKILL.md should include:
- Frontmatter: name, description, argument-hint, allowed-tools
- Inputs section
- Procedure (analyze → present → create → commit)
- Extraction heuristics table with evidence anchors
- Failure modes table
- Examples
- Scope section

**Step 2: Verify SKILL.md structure (P2-6)**

Before committing, verify the SKILL.md has:
- [ ] Frontmatter with required keys: `name`, `description`
- [ ] At least one of: `argument-hint`, `allowed-tools`
- [ ] Sections: Inputs, Procedure, Failure Modes
- [ ] No references to nonexistent file paths

**Step 3: Commit**

```bash
git add packages/plugins/handoff/skills/defer/SKILL.md
git commit -m "feat(handoff): add /defer skill — extract deferred items from conversation"
```

---

## Task 11: /triage SKILL.md

**Files:**
- Create: `packages/plugins/handoff/skills/triage/SKILL.md`

**Step 1: Write the SKILL.md**

The SKILL.md follows the same pattern. Key behaviors:
- Calls `triage.py` to get JSON report
- Presents open tickets grouped by priority, then age
- Presents orphaned items with match status
- Offers user actions (create ticket, skip)

See design doc sections:
- `/triage` Skill Design (procedure, staleness heuristics)
- Deterministic-only orphan detection

The SKILL.md should include:
- Frontmatter: name, description, argument-hint, allowed-tools
- Inputs section
- Procedure (read tickets → scan handoffs → present report → user actions)
- Match-path observability (report uid_match/id_ref/manual_review counts)
- Failure modes table
- Examples
- Scope section

**Step 2: Verify SKILL.md structure (P2-6)**

Before committing, verify the SKILL.md has:
- [ ] Frontmatter with required keys: `name`, `description`
- [ ] At least one of: `argument-hint`, `allowed-tools`
- [ ] Sections: Inputs, Procedure, Failure Modes
- [ ] No references to nonexistent file paths

**Step 3: Commit**

```bash
git add packages/plugins/handoff/skills/triage/SKILL.md
git commit -m "feat(handoff): add /triage skill — review open tickets and orphaned items"
```

---

## Task 12: Plugin Integration — Manifest, README, Version

**Files:**
- Modify: `packages/plugins/handoff/.claude-plugin/plugin.json`
- Modify: `packages/plugins/handoff/README.md`
- Modify: `packages/plugins/handoff/pyproject.toml` (version bump)
- Modify: `packages/plugins/handoff/uv.lock`

**Step 1: Update plugin.json**

Add the new skills to the manifest keywords. Verify the skill auto-discovery will find `skills/defer/SKILL.md` and `skills/triage/SKILL.md`.

**Step 2: Update README.md**

Add `/defer` and `/triage` to the skills list, with one-line descriptions.

**Step 3: Bump version**

Bump from `1.4.0` to `1.5.0` in both `plugin.json` and `pyproject.toml`.

**Step 4: Lock**

```bash
cd packages/plugins/handoff && uv lock
```

**Step 5: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: all pass (238 existing + new tests)

**Step 6: Commit**

```bash
git add packages/plugins/handoff/.claude-plugin/plugin.json packages/plugins/handoff/README.md packages/plugins/handoff/pyproject.toml packages/plugins/handoff/uv.lock
git commit -m "chore(handoff): bump to 1.5.0, add defer/triage to manifest and README"
```

---

## Task 13: Integration Test — End-to-End /defer Flow

**Files:**
- Modify: `packages/plugins/handoff/tests/test_defer.py`

**Step 1: Write integration test**

Add a `TestEndToEnd` class that:
1. Creates a tickets directory with one existing ticket
2. Calls `write_ticket()` with a realistic candidate
3. Verifies the file was created with correct name, content, YAML frontmatter, provenance, defer-meta
4. Calls `allocate_id()` again and verifies it increments past the new ticket
5. Parses the created ticket with `parse_ticket()` and verifies round-trip

**Step 2: Run and verify**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestEndToEnd -v`
Expected: PASS

**Step 3: Commit**

```bash
git add packages/plugins/handoff/tests/test_defer.py
git commit -m "test(handoff): add end-to-end integration test for defer pipeline"
```

---

## Task 14: Integration Test — End-to-End /triage Flow

**Files:**
- Modify: `packages/plugins/handoff/tests/test_triage.py`

**Step 1: Write integration test**

Add a `TestEndToEnd` class that:
1. Creates tickets directory with: 1 deferred, 1 done, 1 legacy (complete)
2. Creates handoffs directory with: 1 handoff containing Open Questions and Risks
3. One handoff item has a session_id matching a ticket's provenance (uid_match)
4. One handoff item references a ticket ID in its text (id_ref)
5. One handoff item has no match (manual_review)
6. Calls `generate_report()` and verifies:
   - Only non-terminal tickets in `open_tickets`
   - Correct match_counts (at least 1 uid_match, at least 1 manual_review)
   - `orphaned_items` contains only manual_review items (P1-1)
   - `matched_items` contains uid_match and id_ref items

Also add a `TestDeferTriageRoundTrip` class (P2-4):
1. Creates a ticket via `write_ticket()` from `defer.py` with a known session_id
2. Creates a handoff file with a matching session_id in its frontmatter
3. Calls `generate_report()` from `triage.py`
4. Verifies the created ticket appears in `open_tickets`
5. Verifies the handoff item matches via uid_match in `matched_items`
6. Verifies the ticket can be re-parsed via `parse_ticket()` (round-trip)

**Step 2: Run and verify**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_triage.py::TestEndToEnd tests/test_triage.py::TestDeferTriageRoundTrip -v`
Expected: PASS

**Step 3: Run full suite one final time**

Run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: all pass

**Step 4: Commit**

```bash
git add packages/plugins/handoff/tests/test_triage.py
git commit -m "test(handoff): add end-to-end integration test for triage pipeline"
```

---

## Task Summary

| Task | Component | Tests | Files | Amendments |
|------|-----------|-------|-------|------------|
| 1 | Setup + PyYAML | 0 | 2 | P2-5 |
| 2 | ticket_parsing — extraction | ~9 | 2 | P0-3, P3-1, P1-8 |
| 3 | ticket_parsing — validation + TicketFile | ~12 | 2 | P0-3 (cascade), P2-12 |
| 4 | provenance — parsing + dual-read | ~11 | 2 | P3-2, P1-7 |
| 5 | project_paths — get_archive_dir | 2 | 2 | — |
| 6 | defer — ID allocation + rendering | ~17 | 2 | P1-5, P1-6, P2-1, P2-3, P1-9, P2-9, P2-11 |
| 7 | triage — reading + normalization | ~10 | 2 | P3-7 |
| 8 | triage — scanning + orphan detection | ~12 | 2 | P0-1, P0-2, P1-2, P1-4, P3-4, P1-11, P2-7, P2-10, P3-5 |
| 9 | triage — report + CLI | ~8 | 2 | P1-1, P1-3, P1-4, P2-2, P1-10, P2-8, P3-6 |
| 10 | /defer SKILL.md | 0 | 1 | P2-6 |
| 11 | /triage SKILL.md | 0 | 1 | P2-6 |
| 12 | Plugin integration | 0 | 4 | — |
| 13 | Integration test — defer | ~1 | 1 | — |
| 14 | Integration test — triage | ~2 | 1 | P2-4 |

**Total:** ~84 new tests across 4 new scripts, 2 new skills, 1 modified utility.

**Codex deep review:** 19 findings addressed (3 P0, 6 P1, 6 P2, 4 P3). Thread `019ca324-61ae-7640-b256-5c7a86bbfb47`.

**Codex adversarial review:** 16 findings addressed (5 P1, 7 P2, 4 P3). Thread `019ca346-e54d-7c90-9727-cf23681fbb71`. Fix-now gate: 9 items (P1-7, P1-8, P1-9, P1-10, P1-11, P2-7, P2-8, P2-9, P2-10). Deferred: P2-12, P3-5, P3-6, P3-7, P3-8.

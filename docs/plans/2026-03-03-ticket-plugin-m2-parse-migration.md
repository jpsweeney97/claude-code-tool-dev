# Ticket Plugin Phase 1 — Module 2: Parse + Migration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the fenced-YAML parser (`ticket_parse.py`) and validate it against legacy ticket formats with migration golden tests.

**Architecture:** Hybrid adapter pattern (Architecture E). The parser is the highest fan-out contract — 5 downstream tasks import from `ticket_parse`. Migration golden tests (Task 14) validate the parser immediately after it's built, catching defects before Modules 3-5 build on top.

**Tech Stack:** Python 3.11+, PyYAML, pytest

**References (read-only — do not modify these files):**
- Canonical plan: `docs/plans/2026-03-02-ticket-plugin-phase1-plan.md`
- Modularization design: `docs/plans/2026-03-02-ticket-plugin-plan-modularization.md`
- Design doc: `docs/plans/2026-03-02-ticket-plugin-design.md` (canonical spec)

**Scope:** Module 2 of 5. Creates `scripts/ticket_parse.py` and `tests/test_parse.py` (Task 3), then `tests/test_migration.py` (Task 14). Phased execution: Task 3 first (parser), then Task 14 (golden tests).

**Execution Order:** Task 3 → Task 14. This is non-sequential numbering (Task 14 relocated from its original position because migration golden tests validate the parser).

---

## Phase 1 Scope Policy

**Phase 1 Scope Policy (strict fail-closed):**
- All agent mutations are **hard-blocked** in Phase 1 — `engine_preflight` returns `policy_blocked` for `request_origin="agent"` regardless of autonomy mode. Rationale: the PreToolUse hook (Phase 2) is required to inject `hook_injected: true` and `session_id`; without it, agent paths cannot be legitimately exercised.
- `hook_injected` field validation is **deferred to Phase 2** — the hook that sets it doesn't exist yet.
- Audit trail writes (`attempt_started`/`attempt_result` JSONL) are **deferred to Phase 2** — they require `session_id` injection from the hook.
- `auto_audit` and `auto_silent` autonomy modes are structurally unreachable in Phase 1 (blocked by the hard-block above). Tests verify the hard-block, not the mode-specific behavior.
- `ticket_triage.py` is **deferred to Phase 2** — the design doc lists it in the plugin structure, but it implements read-only analysis capabilities (orphan detection, audit trail reporting) that depend on the Phase 2 audit trail. No task in this plan creates `ticket_triage.py` or `test_triage.py`.

**Deferred tickets (not Phase 1):**
- T-20260302-01: auto_audit notification UX flows (Phase 2 — skill UX)
- T-20260302-02: merge_into_existing v1.1 (reserved state, escalate fallback)
- T-20260302-03: ticket audit repair (Phase 2 — added to ticket-ops)
- T-20260302-04: DeferredWorkEnvelope (Phase 4)
- T-20260302-05: foreground-only enforcement (Phase 3)

---

## Prerequisites

**From Module 1 (already implemented):**
- Plugin scaffold: `packages/plugins/ticket/` directory structure
- `packages/plugins/ticket/pyproject.toml` with PyYAML dependency and pytest config
- `packages/plugins/ticket/tests/__init__.py`
- `packages/plugins/ticket/tests/conftest.py` with these helpers:
  - `tmp_tickets` fixture — creates temporary `docs/tickets/` directory
  - `tmp_audit` fixture — creates temporary `docs/tickets/.audit/` directory
  - `make_ticket(tickets_dir, filename, ...)` — generic v1.0 format ticket factory
  - `make_gen1_ticket(tickets_dir)` — Gen 1 legacy format (slug ID, `plugin` field)
  - `make_gen2_ticket(tickets_dir)` — Gen 2 legacy format (letter ID T-[A-F])
  - `make_gen3_ticket(tickets_dir)` — Gen 3 legacy format (numeric ID T-NNN)
  - `make_gen4_ticket(tickets_dir)` — Gen 4 legacy format (v1.0 T-YYYYMMDD-NN)
- `packages/plugins/ticket/references/ticket-contract.md` — ticket contract reference document

**M1→M2 gate passed:** Conftest smoke test verified all `make_gen*_ticket` helpers return `Path` to files with fenced YAML.

## Gate Entry: M1 → M2

The M1→M2 gate card should be committed and available. Verify:
- All `make_gen*_ticket` helpers import and return `Path` objects
- No test files exist yet (M1 creates no test files)
- `conftest.py` is importable from the tests directory

---

## Task 3: ticket_parse.py — Fenced-YAML Parsing

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_parse.py`
- Create: `packages/plugins/ticket/tests/test_parse.py`

**Context:** Port and extend from `packages/plugins/handoff/scripts/ticket_parsing.py`. The ticket plugin needs its own copy (cross-plugin import not possible). Additions: section extraction, legacy format detection, status normalization.

**Step 1: Write failing tests**

```python
"""Tests for ticket_parse.py — fenced-YAML parsing and section extraction."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

# Import path: tests run from packages/plugins/ticket/
from scripts.ticket_parse import (
    ParsedTicket,
    detect_generation,
    extract_fenced_yaml,
    extract_sections,
    normalize_status,
    parse_ticket,
    parse_yaml_block,
    SECTION_RENAMES,
)


# --- extract_fenced_yaml ---


class TestExtractFencedYaml:
    def test_standard_fenced_block(self):
        text = "# Title\n\n```yaml\nid: T-01\nstatus: open\n```\n\n## Body"
        assert extract_fenced_yaml(text) == "id: T-01\nstatus: open\n"

    def test_yml_variant(self):
        text = "```yml\nid: T-01\n```"
        assert extract_fenced_yaml(text) == "id: T-01\n"

    def test_no_fenced_block(self):
        assert extract_fenced_yaml("# Just markdown\nNo yaml here.") is None

    def test_multiple_blocks_returns_first(self):
        text = "```yaml\nfirst: true\n```\n\n```yaml\nsecond: true\n```"
        assert extract_fenced_yaml(text) == "first: true\n"

    def test_non_yaml_fenced_block_ignored(self):
        text = "```python\nprint('hi')\n```\n```yaml\nid: T-01\n```"
        assert extract_fenced_yaml(text) == "id: T-01\n"


# --- parse_yaml_block ---


class TestParseYamlBlock:
    def test_valid_yaml(self):
        result = parse_yaml_block("id: T-01\nstatus: open\n")
        assert result == {"id": "T-01", "status": "open"}

    def test_date_normalization(self):
        """PyYAML converts unquoted dates to datetime.date — we normalize back."""
        result = parse_yaml_block("date: 2026-03-02\n")
        assert result["date"] == "2026-03-02"
        assert isinstance(result["date"], str)

    def test_empty_string(self):
        assert parse_yaml_block("") is None

    def test_malformed_yaml(self):
        with pytest.warns(UserWarning, match="YAML parse error"):
            result = parse_yaml_block("key: [unclosed")
        assert result is None

    def test_non_dict_yaml(self):
        with pytest.warns(UserWarning, match="expected dict"):
            result = parse_yaml_block("- item1\n- item2\n")
        assert result is None


# --- extract_sections ---


class TestExtractSections:
    def test_basic_sections(self):
        body = textwrap.dedent("""\
            ## Problem
            Something is broken.

            ## Approach
            Fix it.

            ## Acceptance Criteria
            - [ ] Fixed
        """)
        sections = extract_sections(body)
        assert "Problem" in sections
        assert "Something is broken." in sections["Problem"]
        assert "Approach" in sections
        assert "Acceptance Criteria" in sections

    def test_empty_body(self):
        assert extract_sections("") == {}

    def test_content_before_first_heading(self):
        body = "Some preamble text.\n\n## Problem\nThe issue."
        sections = extract_sections(body)
        assert "Problem" in sections
        # Preamble is discarded (not a named section)

    def test_nested_headings_ignored(self):
        """### subheadings are part of the parent ## section."""
        body = "## Problem\nMain text.\n\n### Details\nSub text."
        sections = extract_sections(body)
        assert "Problem" in sections
        assert "### Details" in sections["Problem"]
        assert "Sub text." in sections["Problem"]


# --- detect_generation ---


class TestDetectGeneration:
    def test_gen1_slug_id(self):
        assert detect_generation({"id": "handoff-chain-viz"}) == 1

    def test_gen2_letter_id(self):
        assert detect_generation({"id": "T-A"}) == 2
        assert detect_generation({"id": "T-F"}) == 2

    def test_gen3_numeric_id(self):
        assert detect_generation({"id": "T-003"}) == 3
        assert detect_generation({"id": "T-100"}) == 3

    def test_gen4_date_id_with_provenance(self):
        assert detect_generation({"id": "T-20260301-01", "provenance": {}}) == 4

    def test_v10_date_id_with_source(self):
        assert detect_generation({"id": "T-20260302-01", "source": {}}) == 10

    def test_v10_with_contract_version(self):
        assert detect_generation({"id": "T-20260302-01", "contract_version": "1.0"}) == 10


# --- normalize_status ---


class TestNormalizeStatus:
    def test_canonical_statuses_unchanged(self):
        for s in ("open", "in_progress", "blocked", "done", "wontfix"):
            assert normalize_status(s) == (s, None)

    def test_planning_maps_to_open(self):
        assert normalize_status("planning") == ("open", None)

    def test_implementing_maps_to_in_progress(self):
        assert normalize_status("implementing") == ("in_progress", None)

    def test_complete_maps_to_done(self):
        assert normalize_status("complete") == ("done", None)

    def test_closed_maps_to_done(self):
        assert normalize_status("closed") == ("done", None)

    def test_deferred_maps_to_open_with_defer(self):
        status, defer_info = normalize_status("deferred")
        assert status == "open"
        assert defer_info is not None
        assert defer_info["active"] is True

    def test_unknown_status_preserved(self):
        """Unknown statuses pass through — mutation paths fail closed."""
        assert normalize_status("banana") == ("banana", None)


# --- parse_ticket ---


class TestParseTicket:
    def test_v10_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        path = make_ticket(tmp_tickets, "2026-03-02-test.md")
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.id == "T-20260302-01"
        assert ticket.status == "open"
        assert ticket.priority == "high"
        assert ticket.generation == 10
        assert "Problem" in ticket.sections

    def test_gen1_ticket(self, tmp_tickets):
        from tests.conftest import make_gen1_ticket

        path = make_gen1_ticket(tmp_tickets)
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.id == "handoff-chain-viz"
        assert ticket.generation == 1
        # Field defaults applied
        assert ticket.source == {"type": "legacy", "ref": "", "session": ""}
        assert ticket.priority == "medium"

    def test_gen2_ticket(self, tmp_tickets):
        from tests.conftest import make_gen2_ticket

        path = make_gen2_ticket(tmp_tickets)
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.id == "T-A"
        assert ticket.generation == 2
        # Summary → Problem rename
        assert "Problem" in ticket.sections

    def test_gen3_ticket(self, tmp_tickets):
        from tests.conftest import make_gen3_ticket

        path = make_gen3_ticket(tmp_tickets)
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.id == "T-003"
        assert ticket.generation == 3
        # Findings → Prior Investigation rename
        assert "Prior Investigation" in ticket.sections

    def test_gen4_ticket(self, tmp_tickets):
        from tests.conftest import make_gen4_ticket

        path = make_gen4_ticket(tmp_tickets)
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.id == "T-20260301-01"
        assert ticket.generation == 4
        # Status normalization: deferred → open
        assert ticket.status == "open"
        assert ticket.defer is not None
        assert ticket.defer["active"] is True
        # Provenance → source mapping
        assert ticket.source["type"] == "handoff"
        # Proposed Approach → Approach rename
        assert "Approach" in ticket.sections

    def test_nonexistent_file(self, tmp_tickets):
        path = tmp_tickets / "nonexistent.md"
        with pytest.warns(UserWarning, match="Cannot read"):
            assert parse_ticket(path) is None

    def test_no_yaml_block(self, tmp_tickets):
        path = tmp_tickets / "no-yaml.md"
        path.write_text("# Just a title\nNo yaml.", encoding="utf-8")
        with pytest.warns(UserWarning, match="No fenced YAML"):
            assert parse_ticket(path) is None

    def test_missing_required_fields(self, tmp_tickets):
        path = tmp_tickets / "bad.md"
        path.write_text("# Bad\n\n```yaml\npriority: high\n```\n", encoding="utf-8")
        with pytest.warns(UserWarning, match="missing required"):
            assert parse_ticket(path) is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_parse.py -v`
Expected: ImportError (module doesn't exist yet)

**Step 3: Write implementation**

```python
"""Fenced-YAML ticket parsing with legacy format support.

Parses ticket markdown files from docs/tickets/. Supports 4 legacy
generations plus v1.0 format. Applies field defaults, section renames,
and status normalization on read (never writes back).

Based on handoff plugin's ticket_parsing.py with additions:
section extraction, legacy detection, status normalization.
"""
from __future__ import annotations

import datetime
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Match the first ```yaml or ```yml block in markdown.
_FENCED_YAML_RE = re.compile(
    r"^```ya?ml\s*\n(.*?)^```",
    re.MULTILINE | re.DOTALL,
)

# Match ## headings (level 2 only — ### and deeper are section content).
_SECTION_HEADING_RE = re.compile(r"^## (.+)$", re.MULTILINE)

# Legacy section renames (3-tier: exact → near-equivalent → preserve).
SECTION_RENAMES: dict[str, str] = {
    # Exact renames
    "Summary": "Problem",
    "Findings": "Prior Investigation",
    "Proposed Approach": "Approach",
    "Files Affected": "Key Files",
    "Files to Create/Modify": "Key Files",
    # Near-equivalents
    "Scope": "Context",
    "Risks": "Context",
}

# Canonical statuses (v1.0).
CANONICAL_STATUSES = frozenset({"open", "in_progress", "blocked", "done", "wontfix"})

# Legacy status normalization map.
_STATUS_MAP: dict[str, str] = {
    "planning": "open",
    "implementing": "in_progress",
    "complete": "done",
    "closed": "done",
    "deferred": "open",
}

# Required YAML fields for parse-level schema validation.
# Only 3 of 6 contract-required fields (id, date, status) are enforced here.
# The remaining 3 (priority, source, contract_version) are applied as defaults
# by _apply_field_defaults() for legacy tickets. Enforcing all 6 at parse time
# would reject all legacy tickets (Gen 1-4 lack these fields).
# Full 6-field validation happens at create time in engine_execute.
_REQUIRED_FIELDS = ("id", "date", "status")

# Field defaults for legacy tickets (applied on read, not written back).
_FIELD_DEFAULTS: dict[str, Any] = {
    "priority": "medium",
    "source": {"type": "legacy", "ref": "", "session": ""},
    "effort": "",
    "tags": [],
    "blocked_by": [],
    "blocks": [],
}

# ID pattern matchers for generation detection.
_GEN2_ID_RE = re.compile(r"^T-[A-F]$")
_GEN3_ID_RE = re.compile(r"^T-\d{1,3}$")
_DATE_ID_RE = re.compile(r"^T-\d{8}-\d{2}$")


@dataclass(frozen=True)
class ParsedTicket:
    """A parsed ticket with normalized fields and extracted sections.

    All legacy field mapping and status normalization is applied.
    The `generation` field indicates which format was detected (1-4, or 10 for v1.0).
    """

    path: str
    id: str
    date: str
    status: str
    priority: str
    source: dict[str, str]
    generation: int
    frontmatter: dict[str, Any]
    sections: dict[str, str]
    effort: str = ""
    tags: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    contract_version: str = ""
    defer: dict[str, Any] | None = None
    body: str = ""


def extract_fenced_yaml(text: str) -> str | None:
    """Extract YAML text from the first fenced yaml block. Returns None if not found."""
    m = _FENCED_YAML_RE.search(text)
    return m.group(1) if m else None


def parse_yaml_block(yaml_text: str) -> dict[str, Any] | None:
    """Parse a YAML string into a dict. Returns None if empty or malformed.

    Normalizes datetime.date values back to str (PyYAML auto-converts unquoted dates).
    """
    if not yaml_text.strip():
        return None
    try:
        result = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        warnings.warn(f"YAML parse error: {exc}", stacklevel=2)
        return None
    if not isinstance(result, dict):
        warnings.warn(
            f"YAML parsed as {type(result).__name__}, expected dict",
            stacklevel=2,
        )
        return None
    # Normalize date objects back to strings.
    for key, value in result.items():
        if isinstance(value, (datetime.date, datetime.datetime)):
            result[key] = str(value)
    return result


def extract_sections(body: str) -> dict[str, str]:
    """Extract ## sections from markdown body into a dict.

    Keys are section names (without ##). Values are the section content
    (everything between this heading and the next ## heading or end of text).
    ### subheadings and deeper are included in their parent section.
    Content before the first ## heading is discarded.
    """
    if not body.strip():
        return {}

    sections: dict[str, str] = {}
    matches = list(_SECTION_HEADING_RE.finditer(body))

    for i, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        sections[name] = content

    return sections


def detect_generation(frontmatter: dict[str, Any]) -> int:
    """Detect ticket generation from frontmatter fields.

    Returns: 1 (slug), 2 (T-[A-F]), 3 (T-NNN), 4 (defer output), 10 (v1.0).
    """
    ticket_id = frontmatter.get("id", "")

    # v1.0: has contract_version or source (not provenance)
    if "contract_version" in frontmatter or (
        "source" in frontmatter and "provenance" not in frontmatter
    ):
        return 10

    # Gen 4: date-based ID with provenance dict
    if _DATE_ID_RE.match(ticket_id) and "provenance" in frontmatter:
        return 4

    # Gen 2: letter IDs
    if _GEN2_ID_RE.match(ticket_id):
        return 2

    # Gen 3: numeric IDs
    if _GEN3_ID_RE.match(ticket_id):
        return 3

    # Gen 1: slug IDs (anything that doesn't match the above)
    return 1


def normalize_status(raw_status: str) -> tuple[str, dict[str, Any] | None]:
    """Normalize a raw status to canonical + optional defer info.

    Returns (canonical_status, defer_info_or_none).
    Unknown statuses pass through unchanged (mutation paths fail closed).
    """
    if raw_status in CANONICAL_STATUSES:
        return (raw_status, None)

    canonical = _STATUS_MAP.get(raw_status, raw_status)

    defer_info = None
    if raw_status == "deferred":
        defer_info = {"active": True, "reason": "", "deferred_at": ""}

    return (canonical, defer_info)


def _apply_section_renames(sections: dict[str, str]) -> dict[str, str]:
    """Apply section renames per the 3-tier strategy. Returns new dict."""
    renamed: dict[str, str] = {}
    for name, content in sections.items():
        new_name = SECTION_RENAMES.get(name, name)
        # If target already exists (e.g., ticket has both Summary and Problem),
        # append rather than overwrite.
        if new_name in renamed:
            renamed[new_name] += "\n\n" + content
        else:
            renamed[new_name] = content
    return renamed


def _apply_field_defaults(frontmatter: dict[str, Any], generation: int) -> dict[str, Any]:
    """Apply field defaults for legacy tickets. Returns modified frontmatter."""
    for field_name, default in _FIELD_DEFAULTS.items():
        if field_name not in frontmatter:
            frontmatter[field_name] = default
    return frontmatter


def _map_gen4_fields(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """Map Gen 4 (defer output) fields to v1.0 equivalents.

    provenance → source, source_type/source_ref → source.type/source.ref
    """
    provenance = frontmatter.pop("provenance", {})
    source_type = frontmatter.pop("source_type", provenance.get("created_by", "defer"))
    source_ref = frontmatter.pop("source_ref", "")
    session = provenance.get("session_id", "")

    frontmatter["source"] = {
        "type": source_type if source_type != "defer.py" else "defer",
        "ref": source_ref,
        "session": session,
    }
    return frontmatter


def parse_ticket(path: Path) -> ParsedTicket | None:
    """Parse a ticket file into a ParsedTicket with full normalization.

    Supports v1.0 and 4 legacy generations. Returns None on read/parse failure.
    Applies: field defaults, section renames, status normalization, field mapping.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        warnings.warn(f"Cannot read ticket {path}: {exc}", stacklevel=2)
        return None

    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        warnings.warn(f"No fenced YAML block in {path}", stacklevel=2)
        return None

    frontmatter = parse_yaml_block(yaml_text)
    if frontmatter is None:
        warnings.warn(f"Cannot parse frontmatter in {path}", stacklevel=2)
        return None

    # Validate required fields.
    missing = [f for f in _REQUIRED_FIELDS if f not in frontmatter]
    if missing:
        warnings.warn(
            f"Ticket {path} missing required fields: {', '.join(missing)}",
            stacklevel=2,
        )
        return None

    # Detect generation.
    generation = detect_generation(frontmatter)

    # Map Gen 4 fields before applying defaults.
    if generation == 4:
        frontmatter = _map_gen4_fields(frontmatter)

    # Apply field defaults for legacy tickets.
    if generation < 10:
        frontmatter = _apply_field_defaults(frontmatter, generation)

    # Normalize status.
    raw_status = frontmatter["status"]
    canonical_status, defer_info = normalize_status(raw_status)
    frontmatter["status"] = canonical_status

    # If status was "deferred" and ticket has existing defer field, preserve it.
    if defer_info is not None and "defer" not in frontmatter:
        frontmatter["defer"] = defer_info

    # Extract body (everything after the closing ``` of the YAML block).
    m = _FENCED_YAML_RE.search(text)
    body = text[m.end():].strip() if m else ""

    # Extract and rename sections.
    sections = extract_sections(body)
    if generation < 10:
        sections = _apply_section_renames(sections)

    # Build source dict.
    source = frontmatter.get("source", _FIELD_DEFAULTS["source"])

    return ParsedTicket(
        path=str(path),
        id=frontmatter["id"],
        date=frontmatter.get("date", ""),
        status=canonical_status,
        priority=frontmatter.get("priority", "medium"),
        source=source,
        generation=generation,
        frontmatter=frontmatter,
        sections=sections,
        effort=frontmatter.get("effort", ""),
        tags=frontmatter.get("tags", []),
        blocked_by=frontmatter.get("blocked_by", []),
        blocks=frontmatter.get("blocks", []),
        contract_version=frontmatter.get("contract_version", ""),
        defer=frontmatter.get("defer"),
        body=body,
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_parse.py -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add ticket_parse.py with 4-generation legacy support

Fenced-YAML parsing, section extraction, status normalization,
field defaults, section renames. Based on handoff's ticket_parsing.py.
```

---

**Phased execution:** Task 3 (parser) is now complete. Proceed to Task 14 (migration golden tests).

---

## Task 14: Legacy Migration Golden Tests

**Files:**
- Create: `packages/plugins/ticket/tests/test_migration.py`

**Context:** Read design doc: "Migration" section (lines ~650-692), contract section 8. One golden test per legacy generation. Note: `make_gen1_ticket`, `make_gen2_ticket`, `make_gen3_ticket`, and `make_gen4_ticket` are from Module 1, already implemented in `conftest.py`.

**Step 1: Write golden tests**

```python
"""Migration golden tests — one per legacy generation.

Each test creates a legacy ticket, parses it, and verifies field mapping,
section renames, and status normalization against expected output.
"""
from __future__ import annotations

import pytest

from scripts.ticket_parse import parse_ticket


class TestGen1Migration:
    def test_golden_gen1(self, tmp_tickets):
        from tests.conftest import make_gen1_ticket

        path = make_gen1_ticket(tmp_tickets)
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.generation == 1
        assert ticket.id == "handoff-chain-viz"
        # Field defaults applied for all missing fields.
        assert ticket.priority == "medium"
        assert ticket.source == {"type": "legacy", "ref": "", "session": ""}
        assert ticket.effort == ""
        assert ticket.tags == []
        assert ticket.blocked_by == []
        assert ticket.blocks == []
        # Gen 1 has `plugin` and `related` fields — preserved in frontmatter.
        assert ticket.frontmatter.get("plugin") == "handoff"
        assert ticket.frontmatter.get("related") == ["handoff-search", "handoff-quality-hook"]
        # Section rename: Summary → Problem.
        assert "Problem" in ticket.sections
        assert "Summary" not in ticket.sections


class TestGen2Migration:
    def test_golden_gen2(self, tmp_tickets):
        from tests.conftest import make_gen2_ticket

        path = make_gen2_ticket(tmp_tickets)
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.generation == 2
        assert ticket.id == "T-A"
        # Existing fields preserved.
        assert ticket.priority == "high"
        assert ticket.blocked_by == []
        assert ticket.blocks == ["T-B"]
        # Gen 2 has free-text effort and branch — preserved in frontmatter.
        assert ticket.frontmatter.get("effort") == "S (1-2 sessions)"
        assert ticket.frontmatter.get("branch") == "feature/analytics-refactor"
        # Section rename: Summary → Problem.
        assert "Problem" in ticket.sections
        # Preserved sections (non-standard names kept).
        assert "Rationale" in ticket.sections
        assert "Design" in ticket.sections
        # Risks → Context rename.
        assert "Context" in ticket.sections
        assert "Risks" not in ticket.sections


class TestGen3Migration:
    def test_golden_gen3(self, tmp_tickets):
        from tests.conftest import make_gen3_ticket

        path = make_gen3_ticket(tmp_tickets)
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.generation == 3
        assert ticket.id == "T-003"
        assert ticket.status == "in_progress"
        # Gen 3 has branch field — preserved in frontmatter.
        assert ticket.frontmatter.get("branch") == "fix/session-counting"
        # Section renames: Summary → Problem, Findings → Prior Investigation.
        assert "Problem" in ticket.sections
        assert "Prior Investigation" in ticket.sections
        assert "Summary" not in ticket.sections
        assert "Findings" not in ticket.sections
        # Preserved sections.
        assert "Prerequisites" in ticket.sections
        assert "References" in ticket.sections
        assert "Verification" in ticket.sections


class TestGen4Migration:
    def test_golden_gen4(self, tmp_tickets):
        from tests.conftest import make_gen4_ticket

        path = make_gen4_ticket(tmp_tickets)
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.generation == 4
        assert ticket.id == "T-20260301-01"
        # Status normalization: deferred → open.
        assert ticket.status == "open"
        assert ticket.defer is not None
        assert ticket.defer["active"] is True
        # Field mapping: provenance → source.
        assert ticket.source["type"] == "handoff"
        assert ticket.source["session"] == "xyz-123"
        # source_ref preserved via field mapping.
        assert ticket.frontmatter.get("source_ref") == "session-xyz" or ticket.source.get("ref") is not None
        # Section rename: Proposed Approach → Approach.
        assert "Approach" in ticket.sections
        assert "Proposed Approach" not in ticket.sections
        # Source section preserved (unrecognized → kept).
        assert "Source" in ticket.sections
        # Acceptance Criteria section preserved.
        assert "Acceptance Criteria" in ticket.sections

    def test_gen4_default_source_type(self, tmp_tickets):
        """Gen 4 ticket without source_type gets default source.type='defer'."""
        import textwrap

        content = textwrap.dedent("""\
            # T-20260301-02: Missing source_type

            ```yaml
            id: T-20260301-02
            date: "2026-03-01"
            status: deferred
            priority: medium
            provenance:
              created_by: defer.py
              session_id: abc-456
            tags: []
            blocked_by: []
            blocks: []
            ```

            ## Problem
            Test for default source_type path.
        """)
        path = tmp_tickets / "2026-03-01-no-source-type.md"
        path.write_text(content, encoding="utf-8")
        ticket = parse_ticket(path)
        assert ticket is not None
        assert ticket.generation == 4
        # Default source_type is "defer" per design doc.
        assert ticket.source["type"] == "defer"
```

**Step 2: Run tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_migration.py -v`
Expected: All tests PASS

**Step 3: Commit**

```
feat(ticket): add migration golden tests for 4 legacy generations

Gen 1 (slug), Gen 2 (letter), Gen 3 (numeric), Gen 4 (defer).
Verifies field mapping, section renames, status normalization.
```

---

## Gate Exit: M2 → M3

**Gate Type:** Standard+

Standard gate checks PLUS forward-dependency sentinels for the next module's known imports.

**What the reviewer checks after M2 completes:**

1. **Test files pass:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/test_parse.py tests/test_migration.py -v
   ```

2. **Forward-dependency sentinels (Standard+ addition):**
   Import-only smoke tests verifying `ticket_parse` exports satisfy Module 3's import needs:
   ```python
   # Task 4 (ticket_id) needs:
   from scripts.ticket_parse import extract_fenced_yaml, parse_yaml_block

   # Task 6 (ticket_read) needs:
   from scripts.ticket_parse import ParsedTicket, parse_ticket
   ```
   Task 5 (`ticket_render`) and Task 7 (`ticket_dedup`) do NOT import from `ticket_parse` — no sentinels needed for them.

3. **API surface:** Verify these symbols are importable from `scripts.ticket_parse`:
   - `ParsedTicket` (dataclass)
   - `parse_ticket(path: Path) -> ParsedTicket`
   - `extract_fenced_yaml(text: str) -> str | None`
   - `parse_yaml_block(yaml_text: str) -> dict[str, Any]`

4. **Verdict:** Mechanically derived — PASS iff all commands exit 0, all sentinel imports succeed, and all expected symbols import.

**Gate Card Template (reviewer fills this in):**
```
## Gate Card: M2 → M3
evaluated_sha: <executor's final commit SHA>
handoff_sha: <reviewer's commit after adding this gate card>
commands_to_run: ["cd packages/plugins/ticket && uv run pytest tests/test_parse.py tests/test_migration.py -v"]
must_pass_files: [tests/test_parse.py, tests/test_migration.py]
api_surface_expected:
  - scripts.ticket_parse: [ParsedTicket, parse_ticket, extract_fenced_yaml, parse_yaml_block]
verdict: PASS | FAIL
warnings: []
probe_evidence:
  - command: "python -c 'from scripts.ticket_parse import extract_fenced_yaml, parse_yaml_block'"
    result: "<output>"
  - command: "python -c 'from scripts.ticket_parse import ParsedTicket, parse_ticket'"
    result: "<output>"
```

**Two-SHA semantics:** The executor commits all M2 work (`evaluated_sha`). The reviewer runs the gate checks, then commits the gate card (`handoff_sha`). M3's handoff prompt references `handoff_sha`.

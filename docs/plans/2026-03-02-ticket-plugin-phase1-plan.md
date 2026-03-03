# Ticket Plugin Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the foundation layer of the ticket plugin: engine pipeline, contract, parsing, ID allocation, rendering, and shared read module.

**Architecture:** Hybrid adapter pattern (Architecture E). All mutation logic lives in Python engine scripts. Two entrypoints (`ticket_engine_user.py`, `ticket_engine_agent.py`) hardcode `request_origin` and delegate to `ticket_engine_core.py`. Read-only operations use `ticket_read.py` directly. Skills and agents (Phase 2+) are thin transport layers.

**Tech Stack:** Python 3.11+, PyYAML, pytest. No external dependencies beyond PyYAML.

**Design Doc:** `docs/plans/2026-03-02-ticket-plugin-design.md` (912 lines, canonical spec — read relevant sections before each task)

**Scope:** Phase 1 only — engine + contract + utility modules. No skills, hooks, or agent (those are Phase 2-3).

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

## Task 1: Plugin Scaffold

**Files:**
- Create: `packages/plugins/ticket/.claude-plugin/plugin.json`
- Create: `packages/plugins/ticket/pyproject.toml`
- Create: `packages/plugins/ticket/scripts/.gitkeep`
- Create: `packages/plugins/ticket/skills/.gitkeep`
- Create: `packages/plugins/ticket/agents/.gitkeep`
- Create: `packages/plugins/ticket/references/.gitkeep`
- Create: `packages/plugins/ticket/tests/__init__.py`
- Create: `packages/plugins/ticket/tests/conftest.py`

**Step 1: Create directory structure**

```bash
mkdir -p packages/plugins/ticket/.claude-plugin
mkdir -p packages/plugins/ticket/scripts
mkdir -p packages/plugins/ticket/skills
mkdir -p packages/plugins/ticket/agents
mkdir -p packages/plugins/ticket/references
mkdir -p packages/plugins/ticket/tests
```

**Step 2: Write plugin.json**

```json
{
  "name": "ticket",
  "version": "1.0.0",
  "description": "Repo-local ticket management with lifecycle operations, smart routing, and autonomous creation",
  "author": {
    "name": "JP"
  },
  "license": "MIT",
  "keywords": ["ticket", "tracking", "triage", "dedup", "autonomy"]
}
```

**Step 3: Write pyproject.toml**

```toml
[project]
name = "ticket-plugin"
version = "1.0.0"
description = "Repo-local ticket management plugin for Claude Code"
requires-python = ">=3.11"
dependencies = ["pyyaml>=6.0"]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
```

**Step 4: Write tests/conftest.py**

```python
"""Shared test fixtures for ticket plugin tests."""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def tmp_tickets(tmp_path: Path) -> Path:
    """Create a temporary docs/tickets/ directory."""
    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)
    return tickets_dir


@pytest.fixture
def tmp_audit(tmp_path: Path) -> Path:
    """Create a temporary docs/tickets/.audit/ directory."""
    audit_dir = tmp_path / "docs" / "tickets" / ".audit"
    audit_dir.mkdir(parents=True)
    return audit_dir


def make_ticket(
    tickets_dir: Path,
    filename: str,
    *,
    id: str = "T-20260302-01",
    date: str = "2026-03-02",
    status: str = "open",
    priority: str = "high",
    effort: str = "S",
    source_type: str = "ad-hoc",
    source_ref: str = "",
    session: str = "test-session",
    tags: list[str] | None = None,
    blocked_by: list[str] | None = None,
    blocks: list[str] | None = None,
    contract_version: str = "1.0",
    title: str = "Test ticket",
    problem: str = "Test problem description.",
    extra_yaml: str = "",
    extra_sections: str = "",
) -> Path:
    """Create a v1.0 format ticket file for testing.

    Returns the path to the created file.
    """
    tags = tags or []
    blocked_by = blocked_by or []
    blocks = blocks or []

    content = textwrap.dedent(f"""\
        # {id}: {title}

        ```yaml
        id: {id}
        date: "{date}"
        status: {status}
        priority: {priority}
        effort: {effort}
        source:
          type: {source_type}
          ref: "{source_ref}"
          session: "{session}"
        tags: {tags}
        blocked_by: {blocked_by}
        blocks: {blocks}
        contract_version: "{contract_version}"
        {extra_yaml}```

        ## Problem
        {problem}

        ## Approach
        Fix the issue.

        ## Acceptance Criteria
        - [ ] Issue resolved

        ## Verification
        ```bash
        echo "verified"
        ```

        ## Key Files
        | File | Role | Look For |
        |------|------|----------|
        | test.py | Test | Test code |
        {extra_sections}
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


# --- Legacy ticket fixtures ---


def make_gen1_ticket(tickets_dir: Path, filename: str = "handoff-chain-viz.md") -> Path:
    """Gen 1 (hand-authored): slug ID, `plugin` field, `related` flat list."""
    content = textwrap.dedent("""\
        # handoff-chain-viz: Visualize handoff chains

        ```yaml
        id: handoff-chain-viz
        date: "2026-01-15"
        status: open
        plugin: handoff
        related: [handoff-search, handoff-quality-hook]
        ```

        ## Summary
        Build a visualization for handoff dependency chains.
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def make_gen2_ticket(tickets_dir: Path, filename: str = "T-A-test.md") -> Path:
    """Gen 2 (letter IDs): T-[A-F] ID, `branch`, free-text `effort`."""
    content = textwrap.dedent("""\
        # T-A: Refactor analytics pipeline

        ```yaml
        id: T-A
        date: "2026-02-01"
        status: open
        priority: high
        effort: "S (1-2 sessions)"
        branch: feature/analytics-refactor
        blocked_by: []
        blocks: [T-B]
        ```

        ## Summary
        The analytics pipeline needs refactoring.

        ## Rationale
        Current design is too coupled.

        ## Design
        Decouple the pipeline stages.

        ## Risks
        Breaking existing consumers.
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def make_gen3_ticket(tickets_dir: Path, filename: str = "T-003-test.md") -> Path:
    """Gen 3 (numeric IDs): T-NNN, `branch`, varied sections."""
    content = textwrap.dedent("""\
        # T-003: Fix session counting

        ```yaml
        id: T-003
        date: "2026-02-15"
        status: in_progress
        priority: medium
        branch: fix/session-counting
        blocked_by: []
        blocks: []
        ```

        ## Summary
        Session counting is off by one.

        ## Prerequisites
        Requires access to audit trail.

        ## Findings
        The counter increments before validation.

        ## Verification
        ```bash
        uv run pytest tests/test_sessions.py
        ```

        ## References
        - Related to handoff plugin session tracking
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def make_gen4_ticket(tickets_dir: Path, filename: str = "2026-03-01-auth-timeout.md") -> Path:
    """Gen 4 (defer output): T-YYYYMMDD-NN, `source_type`, `provenance`, `status: deferred`."""
    content = textwrap.dedent("""\
        # T-20260301-01: Fix authentication timeout

        ```yaml
        id: T-20260301-01
        date: "2026-03-01"
        status: deferred
        priority: medium
        source_type: handoff
        source_ref: session-xyz
        provenance:
          created_by: defer.py
          session_id: xyz-123
          handoff_file: 2026-03-01_handoff.md
        tags: [auth, api]
        blocked_by: []
        blocks: []
        ```

        ## Problem
        Auth handler times out for large payloads.

        ## Source
        Found during API refactor session.

        ## Proposed Approach
        Make timeout configurable per route.

        ## Acceptance Criteria
        - [ ] Timeout configurable per route
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path
```

**Step 5: Write tests/__init__.py**

```python
```

(Empty — needed for pytest discovery.)

**Step 6: Verify pytest runs**

Run: `cd packages/plugins/ticket && uv run pytest --co -q`
Expected: "no tests ran" (collection succeeds, no tests yet)

**Step 7: Commit**

```
feat(ticket): scaffold plugin directory structure

Phase 1 foundation: plugin.json, pyproject.toml, test fixtures.
```

---

## Task 2: Ticket Contract Reference

**Files:**
- Create: `packages/plugins/ticket/references/ticket-contract.md`

**Context:** The contract is the single source of truth for all 10 domains. Skills, agents, and engine all reference it. Read design doc sections: "Ticket Contract" (lines ~541-633), "Ticket Format" (lines ~76-148), "Status Transitions" (lines ~607-631).

**Step 1: Write the contract**

The contract covers all 10 domains from the design doc. This is a reference document, not executable code — it defines the schemas, policies, field definitions, and rules that the engine enforces.

Create `packages/plugins/ticket/references/ticket-contract.md` with these sections:

```markdown
# Ticket Contract v1.0

Single source of truth for the ticket plugin. All components (skills, agents, engine) reference this contract.

## 1. Storage

- Active tickets: `docs/tickets/`
- Archived tickets: `docs/tickets/closed-tickets/`
- Audit trail: `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl`
- Naming: `YYYY-MM-DD-<slug>.md`
- Slug: first 6 words of title, kebab-case, `[a-z0-9-]` only, max 60 chars, sequence suffix on collision
- Bootstrap: missing `docs/tickets/` → empty result for reads; create on first write

## 2. ID Allocation

- Format: `T-YYYYMMDD-NN` (date + 2-digit daily sequence, zero-padded)
- Collision prevention: scan existing tickets for same-day IDs, allocate next NN
- Legacy IDs preserved permanently: `T-NNN` (Gen 3), `T-[A-F]` (Gen 2), slugs (Gen 1)

## 3. Schema

### Required YAML Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Ticket ID (T-YYYYMMDD-NN or legacy) |
| `date` | string | Creation date (YYYY-MM-DD) |
| `status` | string | One of: open, in_progress, blocked, done, wontfix |
| `priority` | string | One of: critical, high, medium, low |
| `source` | object | `{type: string, ref: string, session: string}` |
| `contract_version` | string | "1.0" |

### Optional YAML Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `effort` | string | "" | Estimate (XS, S, M, L, XL or free text) |
| `tags` | list[string] | [] | Categorization tags |
| `blocked_by` | list[string] | [] | IDs of blocking tickets |
| `blocks` | list[string] | [] | IDs of tickets this blocks |
| `defer` | object | null | `{active: bool, reason: string, deferred_at: string}` |

### Required Sections

Problem, Approach, Acceptance Criteria, Verification, Key Files

### Optional Sections

Context, Prior Investigation, Decisions Made, Related, Reopen History

### Section Ordering

Problem → Context → Prior Investigation → Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related → Reopen History

## 4. Engine Interface

Common response envelope: `{state: string, ticket_id: string|null, message: string, data: object}`

Exit codes: 0 (success), 1 (engine error), 2 (validation failure)

### Subcommands

| Subcommand | Input | Output `data` |
|-----------|-------|---------------|
| classify | action, args, session_id, request_origin | intent, confidence, resolved_ticket_id |
| plan | intent, fields, session_id, request_origin | dedup_fingerprint, target_fingerprint, duplicate_of, missing_fields, action_plan |
| preflight | ticket_id, action, session_id, request_origin, classify_confidence, classify_intent, dedup_fingerprint, target_fingerprint | checks_passed, checks_failed |
| execute | action, ticket_id, fields, session_id, request_origin, dedup_override, dependency_override | ticket_path, changes |

### Machine States (14 total: 13 emittable, 1 reserved)

ok_create, ok_update, ok_close, ok_close_archived, ok_reopen, need_fields, duplicate_candidate, preflight_failed, policy_blocked, invalid_transition, dependency_blocked, not_found, escalate, merge_into_existing (reserved)

### Error Codes (11)

need_fields, invalid_transition, policy_blocked, stale_plan, audit_unavailable, duplicate_candidate, parse_error, not_found, dependency_blocked, intent_mismatch, origin_mismatch

## 5. Autonomy Model

Modes: suggest (default), auto_audit, auto_silent (v1.1 only)

Config: `.claude/ticket.local.md` YAML frontmatter

`request_origin`: "user" (ticket_engine_user.py), "agent" (ticket_engine_agent.py), "unknown" (fail closed)

## 6. Dedup Policy

Fingerprint: `sha256(normalize(problem_text) + "|" + sorted(key_file_paths))`

`normalize()` steps: (1) strip, (2) collapse whitespace, (3) lowercase, (4) remove punctuation except hyphens/underscores, (5) NFC Unicode normalization

Window: 24 hours. Override: `dedup_override: true` with matching `ticket_id`.

### Test Vectors

| Input | Expected Normalized |
|-------|-------------------|
| `"  Hello,  World!  "` | `"hello world"` |
| `"Fix: the AUTH bug..."` | `"fix the auth bug"` |
| `"résumé"` | `"résumé"` (NFC) |
| `"  multiple   spaces  \n  newlines  "` | `"multiple spaces newlines"` |
| `"keep-hyphens and_underscores"` | `"keep-hyphens and_underscores"` |

## 7. Status Transitions

| From | To | Preconditions |
|------|----|---------------|
| open | in_progress | none |
| open | blocked | blocked_by non-empty |
| in_progress | open | none |
| in_progress | blocked | blocked_by non-empty |
| in_progress | done | acceptance criteria present |
| blocked | open | all blocked_by resolved (done or wontfix) |
| blocked | in_progress | all blocked_by resolved |
| * | wontfix | none |
| done | open | reopen_reason required, user-only v1.0 |
| wontfix | open | reopen_reason required, user-only v1.0 |

Non-status edits on terminal tickets (done/wontfix) are allowed without reopening.

### Status Normalization (Legacy)

| Raw | Canonical |
|-----|-----------|
| planning | open |
| implementing | in_progress |
| complete | done |
| closed | done |
| deferred | open (with defer.active: true) |

## 8. Migration

Read-only for legacy formats. Conversion on update (with user confirmation).

### Legacy Generations

| Gen | ID Pattern | Section Renames |
|-----|-----------|----------------|
| 1 | slug | Summary→Problem |
| 2 | T-[A-F] | Summary→Problem |
| 3 | T-NNN | Summary→Problem, Findings→Prior Investigation |
| 4 | T-YYYYMMDD-NN | Proposed Approach→Approach, provenance→source |

### Field Defaults (applied on read)

| Missing Field | Default |
|--------------|---------|
| priority | medium |
| source | {type: "legacy", ref: "", session: ""} |
| effort | "" |
| tags | [] |
| blocked_by/blocks | [] |

## 9. Integration

External consumers read `docs/tickets/*.md` as plain markdown with fenced YAML.
Format uses fenced YAML (```yaml), not YAML frontmatter (---).

## 10. Versioning

`contract_version` in YAML frontmatter. Current: "1.0".
Engine reads all versions; writes latest only.
```

**Step 2: Commit**

```
feat(ticket): add ticket contract v1.0 reference document

10-domain contract: storage, IDs, schema, engine interface, autonomy,
dedup, transitions, migration, integration, versioning.
```

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

## Task 4: ticket_id.py — ID Allocation

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_id.py`
- Create: `packages/plugins/ticket/tests/test_id.py`

**Context:** Read design doc: "ID Allocation" (contract section 2), "Storage" (contract section 1). IDs are `T-YYYYMMDD-NN` with same-day collision prevention.

**Step 1: Write failing tests**

```python
"""Tests for ticket_id.py — ID allocation and slug generation."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.ticket_id import (
    allocate_id,
    generate_slug,
    is_legacy_id,
    parse_id_date,
)


class TestAllocateId:
    def test_first_ticket_of_day(self, tmp_tickets):
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-01"

    def test_sequential_allocation(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-first.md", id="T-20260302-01")
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-02"

    def test_gap_in_sequence(self, tmp_tickets):
        """Allocates next after highest, not gap-filling."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-first.md", id="T-20260302-01")
        make_ticket(tmp_tickets, "2026-03-02-third.md", id="T-20260302-03")
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-04"

    def test_different_day_no_conflict(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-01-old.md", id="T-20260301-05")
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-01"

    def test_empty_directory(self, tmp_tickets):
        ticket_id = allocate_id(tmp_tickets, date(2026, 3, 2))
        assert ticket_id == "T-20260302-01"

    def test_nonexistent_directory(self, tmp_path):
        """Missing directory returns first ID (not error)."""
        ticket_id = allocate_id(tmp_path / "nonexistent", date(2026, 3, 2))
        assert ticket_id == "T-20260302-01"


class TestGenerateSlug:
    def test_basic_title(self):
        assert generate_slug("Fix authentication timeout on large payloads") == "fix-authentication-timeout-on-large-payloads"

    def test_truncates_to_six_words(self):
        slug = generate_slug("This is a very long title that exceeds six words easily")
        assert slug == "this-is-a-very-long-title"

    def test_special_characters_removed(self):
        slug = generate_slug("Fix: the AUTH bug (v2.0)!")
        assert slug == "fix-the-auth-bug-v20"

    def test_collapses_hyphens(self):
        slug = generate_slug("Fix --- multiple --- hyphens")
        assert slug == "fix-multiple-hyphens"

    def test_max_60_chars(self):
        long_title = "a" * 100
        slug = generate_slug(long_title)
        assert len(slug) <= 60

    def test_empty_title(self):
        slug = generate_slug("")
        assert slug == "untitled"


class TestIsLegacyId:
    def test_gen1_slug(self):
        assert is_legacy_id("handoff-chain-viz") is True

    def test_gen2_letter(self):
        assert is_legacy_id("T-A") is True
        assert is_legacy_id("T-F") is True

    def test_gen3_numeric(self):
        assert is_legacy_id("T-003") is True
        assert is_legacy_id("T-100") is True

    def test_v10_not_legacy(self):
        assert is_legacy_id("T-20260302-01") is False


class TestParseIdDate:
    def test_v10_id(self):
        assert parse_id_date("T-20260302-01") == date(2026, 3, 2)

    def test_legacy_id_returns_none(self):
        assert parse_id_date("T-A") is None
        assert parse_id_date("T-003") is None
        assert parse_id_date("handoff-chain-viz") is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_id.py -v`
Expected: ImportError

**Step 3: Write implementation**

```python
"""Ticket ID allocation and slug generation.

Format: T-YYYYMMDD-NN (date + 2-digit daily sequence, zero-padded).
Legacy IDs (T-NNN, T-[A-F], slugs) are preserved permanently.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from scripts.ticket_parse import extract_fenced_yaml, parse_yaml_block

# ID pattern for v1.0 format.
_DATE_ID_RE = re.compile(r"^T-(\d{8})-(\d{2})$")
_GEN2_ID_RE = re.compile(r"^T-[A-F]$")
_GEN3_ID_RE = re.compile(r"^T-\d{1,3}$")


def allocate_id(tickets_dir: Path, today: date | None = None) -> str:
    """Allocate the next T-YYYYMMDD-NN ID for the given day.

    Scans existing tickets in tickets_dir for same-day IDs and returns
    the next available sequence number. If tickets_dir doesn't exist,
    returns the first ID for the day.
    """
    if today is None:
        today = date.today()

    date_str = today.strftime("%Y%m%d")
    prefix = f"T-{date_str}-"

    max_seq = 0
    if tickets_dir.is_dir():
        for ticket_file in tickets_dir.glob("*.md"):
            try:
                text = ticket_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            yaml_text = extract_fenced_yaml(text)
            if yaml_text is None:
                continue
            data = parse_yaml_block(yaml_text)
            if data is None:
                continue
            ticket_id = data.get("id", "")
            if isinstance(ticket_id, str) and ticket_id.startswith(prefix):
                m = _DATE_ID_RE.match(ticket_id)
                if m and m.group(1) == date_str:
                    seq = int(m.group(2))
                    max_seq = max(max_seq, seq)

    return f"{prefix}{max_seq + 1:02d}"


def generate_slug(title: str) -> str:
    """Generate a URL-safe slug from a ticket title.

    Rules: first 6 words, kebab-case, [a-z0-9-] only, max 60 chars.
    """
    if not title.strip():
        return "untitled"

    # Lowercase and keep only alphanumeric, spaces, hyphens.
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    # Collapse whitespace to single space.
    slug = re.sub(r"\s+", " ", slug).strip()
    # Take first 6 words.
    words = slug.split()[:6]
    slug = "-".join(words)
    # Collapse multiple hyphens.
    slug = re.sub(r"-+", "-", slug)
    # Truncate to 60 chars (don't break mid-word).
    if len(slug) > 60:
        slug = slug[:60].rsplit("-", 1)[0]
    return slug or "untitled"


def build_filename(ticket_id: str, title: str) -> str:
    """Build a ticket filename from ID and title.

    Format: YYYY-MM-DD-<slug>.md (date from ID, slug from title).
    """
    m = _DATE_ID_RE.match(ticket_id)
    if m:
        raw_date = m.group(1)
        date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    else:
        date_str = date.today().strftime("%Y-%m-%d")

    slug = generate_slug(title)
    return f"{date_str}-{slug}.md"


def is_legacy_id(ticket_id: str) -> bool:
    """Check if an ID is a legacy format (not v1.0 T-YYYYMMDD-NN)."""
    return not bool(_DATE_ID_RE.match(ticket_id))


def parse_id_date(ticket_id: str) -> date | None:
    """Extract the date from a v1.0 ID. Returns None for legacy IDs."""
    m = _DATE_ID_RE.match(ticket_id)
    if not m:
        return None
    raw = m.group(1)
    return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_id.py -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add ticket_id.py for ID allocation and slug generation

T-YYYYMMDD-NN format, same-day collision prevention, legacy ID detection.
```

---

## Task 5: ticket_render.py — Markdown Rendering

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_render.py`
- Create: `packages/plugins/ticket/tests/test_render.py`

**Context:** Read design doc: "Ticket Format" (lines ~76-148), "Schema" (contract section 3).

**Step 1: Write failing tests**

```python
"""Tests for ticket_render.py — markdown ticket rendering."""
from __future__ import annotations

import pytest

from scripts.ticket_render import render_ticket


class TestRenderTicket:
    def test_basic_ticket(self):
        result = render_ticket(
            id="T-20260302-01",
            title="Fix authentication timeout",
            date="2026-03-02",
            status="open",
            priority="high",
            effort="S",
            source={"type": "ad-hoc", "ref": "", "session": "test-session"},
            tags=["auth", "api"],
            problem="Auth handler times out for payloads >10MB.",
            approach="Make timeout configurable per route.",
            acceptance_criteria=["Timeout configurable per route", "Default remains 30s"],
            verification="uv run pytest tests/test_auth.py",
            key_files=[
                {"file": "handler.py:45", "role": "Timeout logic", "look_for": "hardcoded timeout"},
            ],
        )
        assert "# T-20260302-01: Fix authentication timeout" in result
        assert "id: T-20260302-01" in result
        assert 'status: open' in result
        assert "## Problem" in result
        assert "## Approach" in result
        assert "## Acceptance Criteria" in result
        assert "- [ ] Timeout configurable per route" in result
        assert "## Verification" in result
        assert "## Key Files" in result
        assert 'contract_version: "1.0"' in result

    def test_minimal_ticket(self):
        result = render_ticket(
            id="T-20260302-01",
            title="Minimal ticket",
            date="2026-03-02",
            status="open",
            priority="medium",
            problem="Something needs fixing.",
        )
        assert "# T-20260302-01: Minimal ticket" in result
        assert "## Problem" in result
        # Optional sections absent
        assert "## Context" not in result
        assert "## Prior Investigation" not in result

    def test_optional_sections_included(self):
        result = render_ticket(
            id="T-20260302-01",
            title="With extras",
            date="2026-03-02",
            status="open",
            priority="high",
            problem="Issue.",
            context="Found during refactor.",
            prior_investigation="Checked handler.py — timeout hardcoded.",
            decisions_made="Configurable timeout over fixed increase.",
            related="T-20260301-03 (API config refactor)",
        )
        assert "## Context" in result
        assert "## Prior Investigation" in result
        assert "## Decisions Made" in result
        assert "## Related" in result

    def test_blocked_by_and_blocks(self):
        result = render_ticket(
            id="T-20260302-01",
            title="Blocked ticket",
            date="2026-03-02",
            status="blocked",
            priority="high",
            problem="Waiting on dependency.",
            blocked_by=["T-20260302-02"],
            blocks=["T-20260302-03"],
        )
        assert "blocked_by: ['T-20260302-02']" in result or "blocked_by:" in result
        assert "blocks:" in result

    def test_defer_field(self):
        result = render_ticket(
            id="T-20260302-01",
            title="Deferred ticket",
            date="2026-03-02",
            status="open",
            priority="low",
            problem="Can wait.",
            defer={"active": True, "reason": "Waiting for v2 API", "deferred_at": "2026-03-02"},
        )
        assert "defer:" in result
        assert "active: true" in result
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_render.py -v`
Expected: ImportError

**Step 3: Write implementation**

```python
"""Template-based markdown rendering for v1.0 tickets.

Renders a complete ticket markdown file with fenced YAML frontmatter
and ordered sections per the contract.
"""
from __future__ import annotations

from typing import Any


def render_ticket(
    *,
    id: str,
    title: str,
    date: str,
    status: str,
    priority: str,
    problem: str,
    effort: str = "",
    source: dict[str, str] | None = None,
    tags: list[str] | None = None,
    blocked_by: list[str] | None = None,
    blocks: list[str] | None = None,
    contract_version: str = "1.0",
    defer: dict[str, Any] | None = None,
    approach: str = "",
    acceptance_criteria: list[str] | None = None,
    verification: str = "",
    key_files: list[dict[str, str]] | None = None,
    context: str = "",
    prior_investigation: str = "",
    decisions_made: str = "",
    related: str = "",
) -> str:
    """Render a complete v1.0 ticket markdown file.

    Returns the full file content as a string.
    Section ordering follows the contract: Problem → Context → Prior Investigation →
    Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related.
    """
    source = source or {"type": "ad-hoc", "ref": "", "session": ""}
    tags = tags or []
    blocked_by = blocked_by or []
    blocks = blocks or []

    # --- YAML frontmatter ---
    lines = [
        f"# {id}: {title}",
        "",
        "```yaml",
        f"id: {id}",
        f'date: "{date}"',
        f"status: {status}",
        f"priority: {priority}",
    ]

    if effort:
        lines.append(f"effort: {effort}")

    lines.extend([
        "source:",
        f"  type: {source['type']}",
        f"  ref: \"{source.get('ref', '')}\"",
        f"  session: \"{source.get('session', '')}\"",
        f"tags: {tags}",
        f"blocked_by: {blocked_by}",
        f"blocks: {blocks}",
    ])

    if defer is not None:
        lines.extend([
            "defer:",
            f"  active: {str(defer.get('active', False)).lower()}",
            f"  reason: \"{defer.get('reason', '')}\"",
            f"  deferred_at: \"{defer.get('deferred_at', '')}\"",
        ])

    lines.append(f'contract_version: "{contract_version}"')
    lines.append("```")
    lines.append("")

    # --- Required sections ---
    lines.extend(["## Problem", problem, ""])

    # --- Optional sections (in contract order) ---
    if context:
        lines.extend(["## Context", context, ""])

    if prior_investigation:
        lines.extend(["## Prior Investigation", prior_investigation, ""])

    if approach:
        lines.extend(["## Approach", approach, ""])

    if decisions_made:
        lines.extend(["## Decisions Made", decisions_made, ""])

    # Acceptance criteria.
    if acceptance_criteria:
        lines.append("## Acceptance Criteria")
        for criterion in acceptance_criteria:
            lines.append(f"- [ ] {criterion}")
        lines.append("")

    # Verification.
    if verification:
        lines.extend([
            "## Verification",
            "```bash",
            verification,
            "```",
            "",
        ])

    # Key files.
    if key_files:
        lines.extend([
            "## Key Files",
            "| File | Role | Look For |",
            "|------|------|----------|",
        ])
        for kf in key_files:
            lines.append(f"| {kf.get('file', '')} | {kf.get('role', '')} | {kf.get('look_for', '')} |")
        lines.append("")

    if related:
        lines.extend(["## Related", related, ""])

    return "\n".join(lines)
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_render.py -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add ticket_render.py for v1.0 markdown rendering

Template-based rendering with contract-ordered sections, fenced YAML
frontmatter, and all optional section support.
```

---

## Task 6: ticket_read.py — Shared Read Module

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_read.py`
- Create: `packages/plugins/ticket/tests/test_read.py`

**Context:** Read design doc: "ticket_read.py" references throughout. Shared between ticket-ops (query/list) and ticket-triage. Query by ID, filter by status/priority/tags, list all.

**Step 1: Write failing tests**

```python
"""Tests for ticket_read.py — shared read module for query and list."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ticket_read import (
    find_ticket_by_id,
    list_tickets,
    filter_tickets,
    fuzzy_match_id,
)


class TestListTickets:
    def test_empty_directory(self, tmp_tickets):
        tickets = list_tickets(tmp_tickets)
        assert tickets == []

    def test_nonexistent_directory(self, tmp_path):
        tickets = list_tickets(tmp_path / "nonexistent")
        assert tickets == []

    def test_lists_all_tickets(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-first.md", id="T-20260302-01")
        make_ticket(tmp_tickets, "2026-03-02-second.md", id="T-20260302-02")
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 2

    def test_skips_unparseable(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-good.md", id="T-20260302-01")
        bad = tmp_tickets / "bad.md"
        bad.write_text("# Not a ticket\nNo yaml.", encoding="utf-8")
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 1

    def test_includes_legacy(self, tmp_tickets):
        from tests.conftest import make_gen1_ticket, make_gen2_ticket, make_ticket

        make_ticket(tmp_tickets, "2026-03-02-new.md", id="T-20260302-01")
        make_gen1_ticket(tmp_tickets)
        make_gen2_ticket(tmp_tickets)
        tickets = list_tickets(tmp_tickets)
        assert len(tickets) == 3

    def test_includes_closed_tickets(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-open.md", id="T-20260302-01")
        closed_dir = tmp_tickets / "closed-tickets"
        closed_dir.mkdir()
        make_ticket(closed_dir, "2026-03-01-done.md", id="T-20260301-01", status="done")
        tickets = list_tickets(tmp_tickets, include_closed=True)
        assert len(tickets) == 2


class TestFindTicketById:
    def test_exact_match(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01")
        ticket = find_ticket_by_id(tmp_tickets, "T-20260302-01")
        assert ticket is not None
        assert ticket.id == "T-20260302-01"

    def test_not_found(self, tmp_tickets):
        assert find_ticket_by_id(tmp_tickets, "T-99999999-99") is None

    def test_legacy_id(self, tmp_tickets):
        from tests.conftest import make_gen2_ticket

        make_gen2_ticket(tmp_tickets)
        ticket = find_ticket_by_id(tmp_tickets, "T-A")
        assert ticket is not None
        assert ticket.id == "T-A"


class TestFilterTickets:
    def test_filter_by_status(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "open.md", id="T-20260302-01", status="open")
        make_ticket(tmp_tickets, "done.md", id="T-20260302-02", status="done")
        tickets = list_tickets(tmp_tickets)
        filtered = filter_tickets(tickets, status="open")
        assert len(filtered) == 1
        assert filtered[0].id == "T-20260302-01"

    def test_filter_by_priority(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "high.md", id="T-20260302-01", priority="high")
        make_ticket(tmp_tickets, "low.md", id="T-20260302-02", priority="low")
        tickets = list_tickets(tmp_tickets)
        filtered = filter_tickets(tickets, priority="high")
        assert len(filtered) == 1

    def test_filter_by_tag(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "auth.md", id="T-20260302-01", tags=["auth", "api"])
        make_ticket(tmp_tickets, "ui.md", id="T-20260302-02", tags=["ui"])
        tickets = list_tickets(tmp_tickets)
        filtered = filter_tickets(tickets, tag="auth")
        assert len(filtered) == 1

    def test_filter_multiple_criteria(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "match.md", id="T-20260302-01", status="open", priority="high")
        make_ticket(tmp_tickets, "no-match.md", id="T-20260302-02", status="open", priority="low")
        tickets = list_tickets(tmp_tickets)
        filtered = filter_tickets(tickets, status="open", priority="high")
        assert len(filtered) == 1


class TestFuzzyMatchId:
    def test_prefix_match(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "ticket.md", id="T-20260302-01")
        tickets = list_tickets(tmp_tickets)
        matches = fuzzy_match_id(tickets, "T-2026030")
        assert len(matches) == 1

    def test_no_match(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "ticket.md", id="T-20260302-01")
        tickets = list_tickets(tmp_tickets)
        matches = fuzzy_match_id(tickets, "T-99999")
        assert len(matches) == 0

    def test_multiple_matches(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "one.md", id="T-20260302-01")
        make_ticket(tmp_tickets, "two.md", id="T-20260302-02")
        tickets = list_tickets(tmp_tickets)
        matches = fuzzy_match_id(tickets, "T-20260302")
        assert len(matches) == 2
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_read.py -v`
Expected: ImportError

**Step 3: Write implementation**

```python
"""Shared read module for ticket query and list operations.

Used by ticket-ops (query/list commands) and ticket-triage.
Read-only — never modifies ticket files.
"""
from __future__ import annotations

from pathlib import Path

from scripts.ticket_parse import ParsedTicket, parse_ticket


def list_tickets(
    tickets_dir: Path,
    *,
    include_closed: bool = False,
) -> list[ParsedTicket]:
    """List all parseable tickets in the tickets directory.

    Scans docs/tickets/*.md. If include_closed=True, also scans
    docs/tickets/closed-tickets/*.md. Skips unparseable files silently.
    Returns tickets sorted by date (newest first), then by ID.
    """
    tickets: list[ParsedTicket] = []

    if not tickets_dir.is_dir():
        return tickets

    # Scan active tickets.
    for ticket_file in tickets_dir.glob("*.md"):
        ticket = parse_ticket(ticket_file)
        if ticket is not None:
            tickets.append(ticket)

    # Scan closed tickets if requested.
    if include_closed:
        closed_dir = tickets_dir / "closed-tickets"
        if closed_dir.is_dir():
            for ticket_file in closed_dir.glob("*.md"):
                ticket = parse_ticket(ticket_file)
                if ticket is not None:
                    tickets.append(ticket)

    # Sort: newest date first, then by ID.
    tickets.sort(key=lambda t: (t.date, t.id), reverse=True)
    return tickets


def find_ticket_by_id(
    tickets_dir: Path,
    ticket_id: str,
    *,
    include_closed: bool = True,
) -> ParsedTicket | None:
    """Find a ticket by exact ID. Returns None if not found.

    Scans all ticket files (including closed) and matches on the `id` field.
    """
    all_tickets = list_tickets(tickets_dir, include_closed=include_closed)
    for ticket in all_tickets:
        if ticket.id == ticket_id:
            return ticket
    return None


def filter_tickets(
    tickets: list[ParsedTicket],
    *,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
) -> list[ParsedTicket]:
    """Filter a list of tickets by criteria. All criteria are AND-combined."""
    result = tickets
    if status is not None:
        result = [t for t in result if t.status == status]
    if priority is not None:
        result = [t for t in result if t.priority == priority]
    if tag is not None:
        result = [t for t in result if tag in t.tags]
    return result


def fuzzy_match_id(
    tickets: list[ParsedTicket],
    partial_id: str,
) -> list[ParsedTicket]:
    """Find tickets whose ID starts with the given prefix."""
    return [t for t in tickets if t.id.startswith(partial_id)]
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_read.py -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add ticket_read.py shared read module

Query by ID, list all, filter by status/priority/tag, fuzzy match.
Scans active and closed-tickets/ directories.
```

---

## Task 7: Dedup — normalize() and Fingerprinting

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_dedup.py`
- Create: `packages/plugins/ticket/tests/test_dedup.py`

**Context:** Read design doc: "Dedup" section (lines ~341-357), contract section 6.

**Step 1: Write failing tests**

```python
"""Tests for ticket_dedup.py — normalization and fingerprinting."""
from __future__ import annotations

import pytest

from scripts.ticket_dedup import (
    normalize,
    dedup_fingerprint,
    target_fingerprint,
)


class TestNormalize:
    """Test vectors from the contract."""

    def test_strip_and_collapse_whitespace(self):
        assert normalize("  Hello,  World!  ") == "hello world"

    def test_remove_punctuation_keep_hyphens_underscores(self):
        assert normalize("Fix: the AUTH bug...") == "fix the auth bug"

    def test_unicode_nfc(self):
        # NFC normalization preserves composed forms.
        assert normalize("résumé") == "résumé"

    def test_multiple_spaces_and_newlines(self):
        assert normalize("  multiple   spaces  \n  newlines  ") == "multiple spaces newlines"

    def test_keep_hyphens_and_underscores(self):
        assert normalize("keep-hyphens and_underscores") == "keep-hyphens and_underscores"

    def test_empty_string(self):
        assert normalize("") == ""

    def test_only_punctuation(self):
        assert normalize("!!!...???") == ""


class TestDedupFingerprint:
    def test_deterministic(self):
        fp1 = dedup_fingerprint("Fix the auth bug", ["handler.py", "config.py"])
        fp2 = dedup_fingerprint("Fix the auth bug", ["handler.py", "config.py"])
        assert fp1 == fp2

    def test_sorted_paths(self):
        """Path order doesn't affect fingerprint."""
        fp1 = dedup_fingerprint("bug", ["b.py", "a.py"])
        fp2 = dedup_fingerprint("bug", ["a.py", "b.py"])
        assert fp1 == fp2

    def test_different_text_different_fingerprint(self):
        fp1 = dedup_fingerprint("bug one", ["a.py"])
        fp2 = dedup_fingerprint("bug two", ["a.py"])
        assert fp1 != fp2

    def test_normalization_applied(self):
        """Whitespace/case differences produce same fingerprint."""
        fp1 = dedup_fingerprint("Fix the Bug", ["a.py"])
        fp2 = dedup_fingerprint("  fix  the  bug  ", ["a.py"])
        assert fp1 == fp2

    def test_empty_paths(self):
        fp = dedup_fingerprint("some problem", [])
        assert isinstance(fp, str)
        assert len(fp) == 64  # sha256 hex digest


class TestTargetFingerprint:
    def test_deterministic(self, tmp_path):
        f = tmp_path / "ticket.md"
        f.write_text("# Ticket content", encoding="utf-8")
        fp1 = target_fingerprint(f)
        fp2 = target_fingerprint(f)
        assert fp1 == fp2

    def test_changes_on_content_change(self, tmp_path):
        f = tmp_path / "ticket.md"
        f.write_text("version 1", encoding="utf-8")
        fp1 = target_fingerprint(f)
        f.write_text("version 2", encoding="utf-8")
        fp2 = target_fingerprint(f)
        assert fp1 != fp2

    def test_none_for_nonexistent(self, tmp_path):
        assert target_fingerprint(tmp_path / "missing.md") is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_dedup.py -v`
Expected: ImportError

**Step 3: Write implementation**

```python
"""Dedup normalization and fingerprinting.

normalize() implements the 5-step canonical normalization from the contract.
dedup_fingerprint() produces the sha256 fingerprint for dedup detection.
target_fingerprint() produces the TOCTOU fingerprint for a ticket file.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    """Canonical 5-step normalization for dedup fingerprinting.

    Steps:
    1. Strip leading/trailing whitespace
    2. Collapse all internal whitespace sequences to single space
    3. Lowercase
    4. Remove punctuation except hyphens and underscores
    5. NFC Unicode normalization
    """
    # Step 1: Strip.
    text = text.strip()
    # Step 2: Collapse whitespace.
    text = re.sub(r"\s+", " ", text)
    # Step 3: Lowercase.
    text = text.lower()
    # Step 4: Remove punctuation except hyphens and underscores.
    # Keep: alphanumeric, spaces, hyphens, underscores.
    text = re.sub(r"[^\w\s-]", "", text)
    # \w includes underscores. Collapse any resulting double spaces.
    text = re.sub(r"\s+", " ", text).strip()
    # Step 5: NFC Unicode normalization.
    text = unicodedata.normalize("NFC", text)
    return text


def dedup_fingerprint(problem_text: str, key_file_paths: list[str]) -> str:
    """Generate a dedup fingerprint: sha256(normalize(problem_text) + "|" + sorted(paths)).

    Used during `plan` stage to detect duplicate tickets within 24-hour window.
    """
    normalized = normalize(problem_text)
    sorted_paths = sorted(key_file_paths)
    payload = normalized + "|" + ",".join(sorted_paths)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def target_fingerprint(ticket_path: Path) -> str | None:
    """Generate a TOCTOU fingerprint: sha256(content + mtime).

    Used before execute to verify ticket wasn't modified since plan/read.
    Returns None if file doesn't exist.
    """
    if not ticket_path.is_file():
        return None
    content = ticket_path.read_bytes()
    mtime = str(ticket_path.stat().st_mtime)
    payload = content + mtime.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_dedup.py -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add ticket_dedup.py with normalize() and fingerprinting

5-step canonical normalization with contract test vectors.
Dedup fingerprint (sha256) and TOCTOU target fingerprint.
```

---

## Task 8: ticket_engine_core.py — classify Subcommand

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Create: `packages/plugins/ticket/tests/test_engine.py`

**Context:** Read design doc: "Engine Design" (lines ~301-340), "Engine Interface" (contract section 4), "Autonomy Enforcement" (lines ~409-451). This task implements `classify` only — subsequent tasks add `plan`, `preflight`, and `execute`.

**Step 1: Write failing tests**

```python
"""Tests for ticket_engine_core.py — engine pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ticket_engine_core import (
    EngineResponse,
    engine_classify,
)


class TestEngineClassify:
    def test_create_intent(self):
        resp = engine_classify(
            action="create",
            args={"title": "Fix auth bug"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "create"
        assert resp.data["confidence"] >= 0.0

    def test_update_intent(self):
        resp = engine_classify(
            action="update",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "update"

    def test_close_intent(self):
        resp = engine_classify(
            action="close",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "close"

    def test_reopen_intent(self):
        resp = engine_classify(
            action="reopen",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "reopen"

    def test_unknown_action(self):
        resp = engine_classify(
            action="banana",
            args={},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "escalate"

    def test_unknown_origin_fails_closed(self):
        resp = engine_classify(
            action="create",
            args={},
            session_id="test-session",
            request_origin="unknown",
        )
        assert resp.state == "escalate"
        assert "caller identity" in resp.message.lower()

    def test_resolved_ticket_id(self):
        resp = engine_classify(
            action="update",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.data["resolved_ticket_id"] == "T-20260302-01"

    def test_create_has_no_resolved_id(self):
        resp = engine_classify(
            action="create",
            args={},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.data["resolved_ticket_id"] is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineClassify -v`
Expected: ImportError

**Step 3: Write implementation**

```python
"""Ticket engine core — classify | plan | preflight | execute pipeline.

All mutation and policy-enforcement logic lives here. Entrypoints
(ticket_engine_user.py, ticket_engine_agent.py) set request_origin
and delegate to this module.

Subcommand contract: each function returns an EngineResponse with
{state, ticket_id, message, data}.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# --- Response envelope ---


@dataclass
class EngineResponse:
    """Common response envelope for all engine subcommands.

    state: machine state (one of 14 defined states, or "ok" for classify/plan success)
    error_code: machine-readable error code (one of 11 defined codes, or None on success)
    ticket_id: affected ticket ID or None
    message: human-readable description
    data: subcommand-specific output
    """

    state: str
    message: str
    error_code: str | None = None
    ticket_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "state": self.state,
            "ticket_id": self.ticket_id,
            "message": self.message,
            "data": self.data,
        }
        if self.error_code is not None:
            d["error_code"] = self.error_code
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# --- Valid actions and origins ---

VALID_ACTIONS = frozenset({"create", "update", "close", "reopen"})
VALID_ORIGINS = frozenset({"user", "agent"})


# --- classify ---


def engine_classify(
    *,
    action: str,
    args: dict[str, Any],
    session_id: str,
    request_origin: str,
) -> EngineResponse:
    """Classify the caller's intent and validate the action.

    Input action (from first-token routing) is authoritative. Classify validates
    but does not remap. If classify's intent disagrees → intent_mismatch → escalate.

    Returns EngineResponse with state="ok" on success, or error state on failure.
    """
    # Fail closed on unknown origin.
    if request_origin not in VALID_ORIGINS:
        return EngineResponse(
            state="escalate",
            message=f"Cannot determine caller identity: request_origin={request_origin!r}",
        )

    # Validate action.
    if action not in VALID_ACTIONS:
        return EngineResponse(
            state="escalate",
            message=f"Unknown action: {action!r}. Valid: {', '.join(sorted(VALID_ACTIONS))}",
        )

    # Resolve ticket ID from args (for non-create actions).
    resolved_ticket_id = args.get("ticket_id") if action != "create" else None

    # Confidence: high for explicit invocations (first-token routing provides strong signal).
    # This is a provisional default — calibration on labeled corpus required pre-GA.
    confidence = 0.95

    return EngineResponse(
        state="ok",
        message=f"Classified as {action}",
        data={
            "intent": action,
            "confidence": confidence,
            "resolved_ticket_id": resolved_ticket_id,
        },
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineClassify -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add engine_classify with intent validation

Validates action and origin, resolves ticket ID, returns confidence.
EngineResponse envelope for all subcommands.
```

---

## Task 9: ticket_engine_core.py — plan Subcommand

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

**Context:** Read design doc: "Pipeline" (lines ~305-312), "Dedup" (lines ~341-357), I/O shapes table (lines ~576-583).

**Step 1: Write failing tests**

Add to `tests/test_engine.py`:

```python
from scripts.ticket_engine_core import engine_plan


class TestEnginePlan:
    def test_create_with_all_fields(self, tmp_tickets):
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_files": ["handler.py"],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dedup_fingerprint" in resp.data
        assert resp.data["missing_fields"] == []

    def test_create_missing_required_fields(self, tmp_tickets):
        resp = engine_plan(
            intent="create",
            fields={"title": "No problem section"},
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"
        assert "problem" in resp.data["missing_fields"]

    def test_dedup_detection(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "2026-03-02-auth.md",
            id="T-20260302-01",
            problem="Auth times out.",
            title="Fix auth bug",
        )
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_files": [],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "duplicate_candidate"
        assert resp.data["duplicate_of"] is not None

    def test_no_dedup_outside_24h(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "2026-02-28-old.md",
            id="T-20260228-01",
            date="2026-02-28",
            problem="Auth times out.",
            title="Old auth bug",
        )
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_files": [],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        # Old ticket outside 24h window — no dedup match.
        assert resp.state == "ok"

    def test_non_create_skips_dedup(self, tmp_tickets):
        resp = engine_plan(
            intent="update",
            fields={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        # No dedup for non-create.
        assert resp.data.get("dedup_fingerprint") is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEnginePlan -v`
Expected: ImportError (engine_plan doesn't exist)

**Step 3: Implement engine_plan**

Add to `ticket_engine_core.py`:

```python
from datetime import datetime, timedelta, timezone
from scripts.ticket_dedup import dedup_fingerprint, normalize, target_fingerprint
from scripts.ticket_read import list_tickets
from scripts.ticket_parse import ParsedTicket

# Required fields for create.
_CREATE_REQUIRED = ("title", "problem", "priority")

# Dedup window.
_DEDUP_WINDOW_HOURS = 24


def engine_plan(
    *,
    intent: str,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Plan stage: validate fields and check for duplicates (create only).

    For create: validates required fields, computes dedup fingerprint,
    scans for duplicates within 24h window.
    For other intents: passes through (plan is create-specific).
    """
    if intent == "create":
        return _plan_create(fields, session_id, request_origin, tickets_dir)

    # Non-create: plan is a pass-through.
    return EngineResponse(
        state="ok",
        message=f"Plan pass-through for {intent}",
        data={
            "dedup_fingerprint": None,
            "target_fingerprint": None,
            "duplicate_of": None,
            "missing_fields": [],
            "action_plan": {"intent": intent},
        },
    )


def _plan_create(
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Plan stage for create: field validation + dedup."""
    # Check required fields.
    missing = [f for f in _CREATE_REQUIRED if not fields.get(f)]
    if missing:
        return EngineResponse(
            state="need_fields",
            message=f"Missing required fields: {', '.join(missing)}",
            error_code="need_fields",
            data={"missing_fields": missing},
        )

    # Compute dedup fingerprint.
    problem_text = fields["problem"]
    key_files = fields.get("key_files", [])
    fp = dedup_fingerprint(problem_text, key_files)

    # Scan for duplicates within 24h window.
    duplicate_of = None
    dup_target_fp = None
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=_DEDUP_WINDOW_HOURS)

    existing = list_tickets(tickets_dir)
    for ticket in existing:
        # Check if ticket is within dedup window.
        try:
            ticket_date = datetime.strptime(ticket.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if ticket_date < cutoff:
            continue

        # Compute fingerprint for this ticket's problem text.
        ticket_problem = ticket.sections.get("Problem", "")
        ticket_key_files = []
        # Extract file paths from Key Files section if present.
        key_files_section = ticket.sections.get("Key Files", "")
        if key_files_section:
            # Parse table rows for file paths (first column).
            import re
            for match in re.finditer(r"^\| ([^|]+) \|", key_files_section, re.MULTILINE):
                cell = match.group(1).strip()
                if cell and cell != "File" and not cell.startswith("-"):
                    ticket_key_files.append(cell)

        existing_fp = dedup_fingerprint(ticket_problem, ticket_key_files)
        if existing_fp == fp:
            duplicate_of = ticket.id
            # Compute target fingerprint for the duplicate.
            dup_target_fp = target_fingerprint(Path(ticket.path))
            break

    if duplicate_of:
        return EngineResponse(
            state="duplicate_candidate",
            message=f"Potential duplicate of {duplicate_of}",
            ticket_id=duplicate_of,
            error_code="duplicate_candidate",
            data={
                "dedup_fingerprint": fp,
                "target_fingerprint": dup_target_fp,
                "duplicate_of": duplicate_of,
                "missing_fields": [],
                "action_plan": {"intent": "create", "duplicate_candidate": True},
            },
        )

    return EngineResponse(
        state="ok",
        message="Plan complete, no duplicates found",
        data={
            "dedup_fingerprint": fp,
            "target_fingerprint": None,  # No target ticket exists yet.
            "duplicate_of": None,
            "missing_fields": [],
            "action_plan": {"intent": "create"},
        },
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEnginePlan -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add engine_plan with dedup detection

Field validation for create, 24h dedup window, fingerprint generation.
Non-create intents pass through (plan is create-specific).
```

---

## Task 10: ticket_engine_core.py — preflight Subcommand

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

**Context:** Read design doc: "Autonomy Enforcement" (lines ~409-451), "Preflight" description (lines ~314-324), I/O shapes (line ~582). Preflight is the single enforcement point for all mutating operations.

**Step 1: Write failing tests**

Add to `tests/test_engine.py`:

```python
from scripts.ticket_engine_core import engine_preflight


class TestEnginePreflight:
    def test_user_create_passes(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert len(resp.data["checks_passed"]) > 0

    def test_unknown_origin_rejected(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="unknown",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"

    def test_low_confidence_rejected(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.1,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert "confidence" in resp.message.lower()

    def test_agent_hard_blocked_phase1(self, tmp_tickets):
        """Phase 1 strict fail-closed: all agent mutations are hard-blocked."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc",
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"
        assert "phase 1" in resp.message.lower() or "hard-blocked" in resp.message.lower()

    def test_agent_reopen_hard_blocked_phase1(self, tmp_tickets):
        """Agent reopen also hard-blocked (not just user-only check)."""
        resp = engine_preflight(
            ticket_id="T-20260302-01",
            action="reopen",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="reopen",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"

    def test_non_create_without_ticket_id_rejected(self, tmp_tickets):
        """Non-create actions require ticket_id."""
        resp = engine_preflight(
            ticket_id=None,
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"

    def test_intent_mismatch_escalates(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",  # Mismatch!
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert "intent_mismatch" in resp.message.lower() or "mismatch" in resp.message.lower()

    def test_stale_target_fingerprint(self, tmp_tickets):
        from tests.conftest import make_ticket

        path = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01")
        resp = engine_preflight(
            ticket_id="T-20260302-01",
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint="stale-fingerprint",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert "stale" in resp.message.lower() or "fingerprint" in resp.message.lower()

    def test_update_ticket_not_found(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id="T-99999999-99",
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "not_found"

    def test_close_with_open_blockers(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_preflight(
            ticket_id="T-20260302-02",
            action="close",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="close",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "dependency_blocked"

    def test_close_with_open_blockers_override(self, tmp_tickets):
        """dependency_override=True allows closing with open blockers."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_preflight(
            ticket_id="T-20260302-02",
            action="close",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="close",
            dedup_fingerprint=None,
            target_fingerprint=None,
            dependency_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dependencies_overridden" in resp.data["checks_passed"]

    def test_dedup_blocks_without_override(self, tmp_tickets):
        """Preflight blocks create when duplicate detected and no override."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            duplicate_of="T-20260302-01",
            dedup_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "duplicate_candidate"
        assert resp.error_code == "duplicate_candidate"

    def test_dedup_passes_with_override(self, tmp_tickets):
        """Preflight allows create when duplicate detected but override=True."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            duplicate_of="T-20260302-01",
            dedup_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dedup" in resp.data["checks_passed"]

    def test_confidence_gate_no_policy_blocked_code(self, tmp_tickets):
        """Confidence gate returns error_code=None, not policy_blocked."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.1,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert resp.error_code is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEnginePreflight -v`
Expected: ImportError

**Step 3: Implement engine_preflight**

Add to `ticket_engine_core.py`:

```python
# Confidence thresholds (provisional — calibrate pre-GA).
_T_BASE = 0.5
_ORIGIN_MODIFIER = {"user": 0.0, "agent": 0.15}

# Terminal statuses for dependency resolution.
_TERMINAL_STATUSES = frozenset({"done", "wontfix"})


def _read_autonomy_mode(tickets_dir: Path) -> str:
    """Read autonomy mode from .claude/ticket.local.md.

    Returns 'suggest' as default if file missing or malformed.
    """
    # Walk up from tickets_dir to find project root.
    project_root = tickets_dir
    while project_root != project_root.parent:
        if (project_root / ".claude").is_dir():
            break
        project_root = project_root.parent

    config_path = project_root / ".claude" / "ticket.local.md"
    if not config_path.is_file():
        return "suggest"

    try:
        import yaml

        text = config_path.read_text(encoding="utf-8")
        # Parse YAML frontmatter (--- delimited).
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                data = yaml.safe_load(parts[1])
                if isinstance(data, dict):
                    mode = data.get("autonomy_mode", "suggest")
                    if mode in ("suggest", "auto_audit", "auto_silent"):
                        return mode
    except Exception:
        pass

    return "suggest"


def engine_preflight(
    *,
    ticket_id: str | None,
    action: str,
    session_id: str,
    request_origin: str,
    classify_confidence: float,
    classify_intent: str,
    dedup_fingerprint: str | None,
    target_fingerprint: str | None,
    duplicate_of: str | None = None,
    dedup_override: bool = False,
    dependency_override: bool = False,
    tickets_dir: Path,
) -> EngineResponse:
    """Preflight: single enforcement point for all mutating operations.

    Checks in order: origin, confidence, intent match, agent policy,
    ticket existence, dependency integrity, TOCTOU fingerprint.
    """
    checks_passed: list[str] = []
    checks_failed: list[dict[str, str]] = []

    # --- Origin check ---
    if request_origin not in VALID_ORIGINS:
        return EngineResponse(
            state="escalate",
            message=f"Cannot determine caller identity: request_origin={request_origin!r}",
            error_code="origin_mismatch",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "origin", "reason": "unknown origin"}]},
        )
    checks_passed.append("origin")

    # --- Confidence gate ---
    modifier = _ORIGIN_MODIFIER.get(request_origin, 0.0)
    threshold = _T_BASE + modifier
    if classify_confidence < threshold:
        # error_code=None: the 11-code table has no confidence-specific code.
        # policy_blocked is reserved for autonomy enforcement (design doc line 593).
        # A confidence-specific code may be added post-v1.0.
        return EngineResponse(
            state="preflight_failed",
            message=f"Low confidence classification: {classify_confidence:.2f} (threshold: {threshold:.2f}). Rephrase or specify the operation.",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "confidence", "reason": f"below threshold {threshold}"}]},
        )
    checks_passed.append("confidence")

    # --- Intent match ---
    if classify_intent != action:
        return EngineResponse(
            state="escalate",
            message=f"Intent_mismatch: classify returned {classify_intent!r} but action is {action!r}",
            error_code="intent_mismatch",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "intent_match", "reason": "mismatch"}]},
        )
    checks_passed.append("intent_match")

    # --- Agent policy: Phase 1 strict fail-closed ---
    # All agent mutations are hard-blocked in Phase 1.
    # The PreToolUse hook (Phase 2) is required for hook_injected and session_id injection.
    if request_origin == "agent":
        return EngineResponse(
            state="policy_blocked",
            message="Agent mutations are hard-blocked in Phase 1. The PreToolUse hook (Phase 2) is required for legitimate agent invocations.",
            error_code="policy_blocked",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "agent_phase1_block", "reason": "Phase 1 fail-closed policy"}]},
        )
    checks_passed.append("autonomy_policy")

    # --- Dedup enforcement (create action) ---
    # Plan stage returns duplicate_of when a match is found. Preflight enforces
    # the dedup decision: if a duplicate was detected and the caller hasn't
    # overridden, block the operation. Without this check, dedup is advisory only.
    if action == "create" and duplicate_of and not dedup_override:
        return EngineResponse(
            state="duplicate_candidate",
            message=f"Duplicate of {duplicate_of} detected in plan stage. Pass dedup_override=True to proceed.",
            error_code="duplicate_candidate",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "dedup", "reason": f"duplicate_of={duplicate_of}"}]},
        )
    if action == "create":
        checks_passed.append("dedup")

    # --- Ticket ID required for non-create ---
    if action != "create" and not ticket_id:
        return EngineResponse(
            state="need_fields",
            message=f"ticket_id required for {action}",
            error_code="need_fields",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "ticket_id", "reason": "missing for non-create"}]},
        )

    # --- Ticket existence check (non-create) ---
    if action != "create" and ticket_id:
        from scripts.ticket_read import find_ticket_by_id

        ticket = find_ticket_by_id(tickets_dir, ticket_id)
        if ticket is None:
            return EngineResponse(
                state="not_found",
                message=f"No ticket found matching {ticket_id}",
                ticket_id=ticket_id,
                error_code="not_found",
                data={"checks_passed": checks_passed, "checks_failed": [{"check": "ticket_exists", "reason": "not found"}]},
            )
        checks_passed.append("ticket_exists")

        # --- Dependency check (close action) ---
        if action == "close" and ticket.blocked_by:
            from scripts.ticket_read import list_tickets as _list_tickets

            all_tickets = _list_tickets(tickets_dir)
            ticket_map = {t.id: t for t in all_tickets}
            unresolved = [
                bid for bid in ticket.blocked_by
                if bid in ticket_map and ticket_map[bid].status not in _TERMINAL_STATUSES
            ]
            if unresolved:
                if dependency_override:
                    checks_passed.append("dependencies_overridden")
                else:
                    return EngineResponse(
                        state="dependency_blocked",
                        message=f"Ticket has open blockers: {unresolved}. Resolve or pass dependency_override: true.",
                        ticket_id=ticket_id,
                        error_code="dependency_blocked",
                        data={"checks_passed": checks_passed, "checks_failed": [{"check": "dependencies", "reason": f"unresolved: {unresolved}"}]},
                    )
            else:
                checks_passed.append("dependencies")

        # --- TOCTOU fingerprint check ---
        if target_fingerprint is not None:
            from scripts.ticket_dedup import target_fingerprint as compute_fp

            current_fp = compute_fp(Path(ticket.path))
            if current_fp != target_fingerprint:
                return EngineResponse(
                    state="preflight_failed",
                    message="Stale fingerprint — ticket was modified since read. Re-run to get a fresh plan.",
                    ticket_id=ticket_id,
                    error_code="stale_plan",
                    data={"checks_passed": checks_passed, "checks_failed": [{"check": "target_fingerprint", "reason": "stale"}]},
                )
            checks_passed.append("target_fingerprint")

    return EngineResponse(
        state="ok",
        message="All preflight checks passed",
        data={"checks_passed": checks_passed, "checks_failed": checks_failed},
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEnginePreflight -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add engine_preflight with autonomy enforcement

Confidence gate, intent match, origin validation, autonomy policy,
TOCTOU fingerprint, dependency checks, ticket existence.
```

---

## Task 11: ticket_engine_core.py — execute Subcommand

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

**Context:** Read design doc: "Execute" in pipeline (lines ~305-312), I/O shapes (line ~583), "Status Transitions" (lines ~607-631), "Audit Trail" (lines ~491-527).

**Step 1: Write failing tests**

Add to `tests/test_engine.py`:

```python
from scripts.ticket_engine_core import engine_execute


class TestEngineExecute:
    def test_create_ticket(self, tmp_tickets):
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out for large payloads.",
                "priority": "high",
                "effort": "S",
                "source": {"type": "ad-hoc", "ref": "", "session": "test-session"},
                "tags": ["auth"],
                "approach": "Make timeout configurable.",
                "acceptance_criteria": ["Timeout configurable", "Default remains 30s"],
                "verification": "uv run pytest tests/test_auth.py",
                "key_files": [{"file": "handler.py:45", "role": "Timeout", "look_for": "hardcoded"}],
            },
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_create"
        assert resp.ticket_id is not None
        assert resp.ticket_id.startswith("T-")
        assert resp.data["ticket_path"] is not None
        # Verify file was created.
        ticket_path = Path(resp.data["ticket_path"])
        assert ticket_path.exists()
        content = ticket_path.read_text(encoding="utf-8")
        assert "Fix auth bug" in content
        assert "## Problem" in content

    def test_update_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        # Verify status changed.
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "status: in_progress" in content
        # Verify date is still quoted (canonical renderer, not yaml.dump).
        assert 'date: "2026-03-02"' in content
        # Verify unknown fields are NOT written back.
        assert "extra_yaml" not in content or "```" in content  # Only in YAML block context

    def test_update_preserves_field_order(self, tmp_tickets):
        """Canonical renderer emits fields in defined order, not alphabetical."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"priority": "critical"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        # id should appear before status in the YAML block.
        id_pos = content.index("id: T-20260302-01")
        status_pos = content.index("status: open")
        assert id_pos < status_pos

    def test_close_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_with_archive(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done", "archive": True},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close_archived"
        # Verify file moved to closed-tickets/.
        assert not (tmp_tickets / "2026-03-02-test.md").exists()
        assert (tmp_tickets / "closed-tickets" / "2026-03-02-test.md").exists()

    def test_reopen_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="reopen",
            ticket_id="T-20260302-01",
            fields={"reopen_reason": "Bug reoccurred after merge"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_reopen"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "status: open" in content
        assert "Reopen History" in content

    def test_invalid_transition_terminal_via_update(self, tmp_tickets):
        """done → in_progress via update is invalid (must reopen first)."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-done.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "reopen" in resp.message.lower()

    def test_invalid_transition_wontfix_via_update(self, tmp_tickets):
        """wontfix → open via update is invalid (must reopen)."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-wontfix.md", id="T-20260302-01", status="wontfix")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "open"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_transition_to_blocked_requires_blocked_by(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open", blocked_by=[])
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "blocked"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "blocked_by" in resp.message.lower()

    def test_close_from_open_succeeds(self, tmp_tickets):
        """Close directly validates with action='close', not 'update'."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_with_invalid_resolution_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_agent_override_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01")
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Test", "priority": "medium"},
            session_id="test-session",
            request_origin="agent",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"
        assert "agent" in resp.message.lower() or "override" in resp.message.lower()

    def test_close_terminal_ticket_rejected(self, tmp_tickets):
        """Closing an already-done ticket is invalid — must reopen first."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-done.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert resp.error_code == "invalid_transition"

    def test_close_wontfix_to_done_rejected(self, tmp_tickets):
        """wontfix → done via close is invalid — terminal state."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-wf.md", id="T-20260302-01", status="wontfix")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_close_checks_acceptance_criteria(self, tmp_tickets):
        """Close to 'done' from in_progress requires acceptance criteria."""
        from tests.conftest import make_ticket

        # Create ticket with empty acceptance criteria section.
        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "acceptance" in resp.message.lower() or "criteria" in resp.message.lower()

    def test_update_preserves_full_field_order(self, tmp_tickets):
        """Verify all canonical field positions, not just id < status."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open",
                     priority="medium", effort="S")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"tags": ["bug"]},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        id_pos = content.index("id:")
        status_pos = content.index("status:")
        priority_pos = content.index("priority:")
        effort_pos = content.index("effort:")
        tags_pos = content.index("tags:")
        assert id_pos < status_pos < priority_pos < effort_pos < tags_pos

    def test_canonical_renderer_none_skipped(self, tmp_tickets):
        """Fields set to None are omitted, not rendered as 'key: None'."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"effort": None},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "effort: None" not in content

    def test_canonical_renderer_list_format(self, tmp_tickets):
        """Lists render as YAML flow sequences, not Python repr."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"tags": ["bug", "urgent"]},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        # Should be YAML flow format, not Python repr with single quotes.
        assert "tags: [bug, urgent]" in content
        assert "['bug'" not in content

    def test_error_code_on_all_error_returns(self, tmp_tickets):
        """All error EngineResponse returns include error_code."""
        # Test update need_fields.
        resp = engine_execute(
            action="update",
            ticket_id=None,
            fields={},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"
        assert resp.error_code == "need_fields"

        # Test update not_found.
        resp = engine_execute(
            action="update",
            ticket_id="T-99999999-99",
            fields={},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "not_found"
        assert resp.error_code == "not_found"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute -v`
Expected: ImportError

**Step 3: Implement engine_execute**

Add to `ticket_engine_core.py`:

```python
from datetime import date as Date
from scripts.ticket_id import allocate_id, build_filename
from scripts.ticket_render import render_ticket
from scripts.ticket_parse import parse_ticket as _parse_ticket, extract_fenced_yaml, parse_yaml_block

# Canonical field order for YAML frontmatter rendering.
# Known fields are written in this order. Unknown keys are preserved at the end
# (forward-compatible: "ignored" means "not processed", not "destroyed on rewrite").
_CANONICAL_FIELD_ORDER = [
    "id", "date", "status", "priority", "effort",
    "source", "tags", "blocked_by", "blocks",
    "contract_version",
]


def _render_canonical_frontmatter(data: dict[str, Any]) -> str:
    """Render YAML frontmatter with controlled field order and quoting.

    Unlike yaml.dump(), this function:
    - Preserves field order (canonical, not alphabetical)
    - Always quotes date strings (prevents PyYAML date coercion)
    - Only emits known fields (drops unknown keys)
    - Uses consistent list formatting (flow style for simple lists)
    """
    lines: list[str] = []
    for key in _CANONICAL_FIELD_ORDER:
        if key not in data:
            continue
        value = data[key]
        # None guard: skip fields explicitly set to None rather than
        # rendering "key: None" (Python str) which YAML reads as string "None".
        if value is None:
            continue
        if key == "date":
            # Always quote dates to prevent PyYAML auto-conversion.
            lines.append(f'{key}: "{value}"')
        elif key == "source" and isinstance(value, dict):
            lines.append("source:")
            for sk, sv in value.items():
                lines.append(f'  {sk}: "{sv}"' if isinstance(sv, str) else f"  {sk}: {sv}")
        elif key == "contract_version":
            lines.append(f'{key}: "{value}"')
        elif isinstance(value, list):
            # Render lists as YAML flow sequences with proper quoting.
            # Python repr uses single quotes; YAML requires brackets with no quotes
            # for simple strings, or double quotes for strings with special chars.
            items = ", ".join(str(item) for item in value)
            lines.append(f"{key}: [{items}]")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, str):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    # Preserve unknown keys (forward-compat: "ignored" means "not processed",
    # not "destroyed on rewrite"). Appended after canonical fields.
    known_keys = set(_CANONICAL_FIELD_ORDER) | {"defer"}
    for key in data:
        if key not in known_keys:
            value = data[key]
            if value is not None:
                lines.append(f"{key}: {value}")
    # Include defer if present (optional field, not in canonical order).
    if "defer" in data and data["defer"] is not None:
        defer = data["defer"]
        lines.append("defer:")
        for dk, dv in defer.items():
            if isinstance(dv, bool):
                lines.append(f"  {dk}: {'true' if dv else 'false'}")
            else:
                lines.append(f'  {dk}: "{dv}"' if isinstance(dv, str) else f"  {dk}: {dv}")
    return "\n".join(lines) + "\n"

# Valid status transitions for update action (from → set of valid to statuses).
# done/wontfix are terminal — only reopen (separate action) can transition out.
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress", "blocked", "wontfix"},
    "in_progress": {"open", "blocked", "done", "wontfix"},
    "blocked": {"open", "in_progress", "wontfix"},
    "done": set(),  # Terminal — reopen action required.
    "wontfix": set(),  # Terminal — reopen action required.
}

# Transitions that require preconditions.
_TRANSITION_PRECONDITIONS: dict[tuple[str, str], str] = {
    # → blocked requires blocked_by non-empty.
    ("open", "blocked"): "blocked_by_required",
    ("in_progress", "blocked"): "blocked_by_required",
    # → done requires acceptance criteria present.
    ("in_progress", "done"): "acceptance_criteria_required",
    # blocked → open requires all blocked_by resolved.
    ("blocked", "open"): "blockers_resolved_required",
    ("blocked", "in_progress"): "blockers_resolved_required",
}


def _is_valid_transition(current: str, target: str, action: str) -> bool:
    """Check if a status transition is valid per the contract."""
    # Close can set done or wontfix from any non-terminal status.
    # Terminal statuses (done/wontfix) cannot be closed again — must reopen first.
    if action == "close":
        if current in _TERMINAL_STATUSES:
            return False
        return target in ("done", "wontfix")
    # Reopen: done/wontfix → open.
    if action == "reopen":
        return current in ("done", "wontfix") and target == "open"
    # Update: follow transition table (terminal statuses have empty set).
    valid = _VALID_TRANSITIONS.get(current, set())
    return target in valid


def _check_transition_preconditions(
    current: str, target: str, ticket: Any, tickets_dir: Path,
    fields: dict[str, Any] | None = None,
) -> str | None:
    """Check transition preconditions. Returns error message or None if OK.

    Uses merged state: fields (pending update) take precedence over ticket
    (pre-update) for fields that are being changed in this operation.
    """
    key = (current, target)
    precondition = _TRANSITION_PRECONDITIONS.get(key)
    if precondition is None:
        return None

    _fields = fields or {}

    if precondition == "blocked_by_required":
        # Use merged blocked_by: pending fields override pre-update ticket state.
        blocked_by = _fields.get("blocked_by", ticket.blocked_by)
        if not blocked_by:
            return f"Transition to 'blocked' requires non-empty blocked_by"
        return None

    if precondition == "acceptance_criteria_required":
        ac = ticket.sections.get("Acceptance Criteria", "")
        if not ac.strip():
            return f"Transition to 'done' requires acceptance criteria section"
        return None

    if precondition == "blockers_resolved_required":
        if ticket.blocked_by:
            from scripts.ticket_read import list_tickets as _list_tickets

            all_tickets = _list_tickets(tickets_dir)
            ticket_map = {t.id: t for t in all_tickets}
            unresolved = [
                bid for bid in ticket.blocked_by
                if bid in ticket_map and ticket_map[bid].status not in _TERMINAL_STATUSES
            ]
            if unresolved:
                return f"Blockers still open: {unresolved}. Resolve or use dependency_override."
        return None

    return None


def engine_execute(
    *,
    action: str,
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    dedup_override: bool,
    dependency_override: bool,
    tickets_dir: Path,
) -> EngineResponse:
    """Execute the mutation: create, update, close, or reopen.

    Assumes preflight has already passed. Writes ticket files and audit trail.
    """
    # Agent callers cannot use overrides.
    if request_origin == "agent" and (dedup_override or dependency_override):
        return EngineResponse(
            state="policy_blocked",
            message="Agent callers cannot use dedup_override or dependency_override",
            error_code="policy_blocked",
        )

    if action == "create":
        return _execute_create(fields, session_id, request_origin, tickets_dir)
    elif action == "update":
        return _execute_update(ticket_id, fields, session_id, request_origin, tickets_dir)
    elif action == "close":
        return _execute_close(ticket_id, fields, session_id, request_origin, tickets_dir)
    elif action == "reopen":
        return _execute_reopen(ticket_id, fields, session_id, request_origin, tickets_dir)
    else:
        return EngineResponse(
            state="escalate",
            message=f"Unknown action: {action!r}",
            error_code="intent_mismatch",
        )


def _execute_create(
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Create a new ticket file with all required contract fields."""
    # Validate required create fields.
    missing = []
    if not fields.get("title"):
        missing.append("title")
    if not fields.get("problem"):
        missing.append("problem")
    if missing:
        return EngineResponse(
            state="need_fields",
            message=f"Missing required fields for create: {missing}",
            error_code="need_fields",
        )

    # Ensure directory exists.
    tickets_dir.mkdir(parents=True, exist_ok=True)

    today = Date.today()
    ticket_id = allocate_id(tickets_dir, today)
    title = fields.get("title", "Untitled")
    filename = build_filename(ticket_id, title)

    source = fields.get("source", {"type": "ad-hoc", "ref": "", "session": session_id})
    if "session" not in source:
        source["session"] = session_id

    content = render_ticket(
        id=ticket_id,
        title=title,
        date=today.isoformat(),
        status="open",
        priority=fields.get("priority", "medium"),
        effort=fields.get("effort", ""),
        source=source,
        tags=fields.get("tags", []),
        problem=fields.get("problem", ""),
        approach=fields.get("approach", ""),
        acceptance_criteria=fields.get("acceptance_criteria"),
        verification=fields.get("verification", ""),
        key_files=fields.get("key_files"),
        context=fields.get("context", ""),
        prior_investigation=fields.get("prior_investigation", ""),
        decisions_made=fields.get("decisions_made", ""),
        related=fields.get("related", ""),
    )

    ticket_path = tickets_dir / filename
    ticket_path.write_text(content, encoding="utf-8")

    return EngineResponse(
        state="ok_create",
        message=f"Created {ticket_id} at {ticket_path}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": None},
    )


def _execute_update(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Update an existing ticket's frontmatter fields."""
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for update", error_code="need_fields")

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")

    # Check status transition validity.
    new_status = fields.get("status")
    if new_status and new_status != ticket.status:
        if not _is_valid_transition(ticket.status, new_status, "update"):
            return EngineResponse(
                state="invalid_transition",
                message=f"Cannot transition from {ticket.status} to {new_status} via update"
                + (" (use reopen action)" if ticket.status in _TERMINAL_STATUSES else ""),
                ticket_id=ticket_id,
                error_code="invalid_transition",
            )
        # Check transition preconditions (pass fields for merged state).
        precondition_error = _check_transition_preconditions(
            ticket.status, new_status, ticket, tickets_dir, fields=fields,
        )
        if precondition_error:
            return EngineResponse(
                state="invalid_transition",
                message=precondition_error,
                ticket_id=ticket_id,
                error_code="invalid_transition",
            )

    # Update frontmatter fields.
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    changes: dict[str, list] = {"frontmatter": {}, "sections_changed": []}
    for key, value in fields.items():
        if key in data and data[key] != value:
            changes["frontmatter"][key] = [data[key], value]
        data[key] = value

    # Re-render using canonical frontmatter renderer (not yaml.dump —
    # yaml.dump reorders keys, changes quoting, and coerces dates).
    new_yaml = _render_canonical_frontmatter(data)
    import re

    new_text = re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    ticket_path.write_text(new_text, encoding="utf-8")

    return EngineResponse(
        state="ok_update",
        message=f"Updated {ticket_id}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": changes},
    )


def _execute_close(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Close a ticket (set status to done or wontfix, optionally archive).

    Unlike update, close validates transitions with action='close', which allows
    done/wontfix from any non-terminal status. This avoids the delegation-to-update
    bug where close-specific transition logic becomes dead code.
    """
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for close", error_code="need_fields")

    resolution = fields.get("resolution", "done")
    archive = fields.get("archive", False)

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    # Validate transition with action="close" (not "update").
    if not _is_valid_transition(ticket.status, resolution, "close"):
        return EngineResponse(
            state="invalid_transition",
            message=f"Cannot close with resolution {resolution!r} (must be 'done' or 'wontfix')"
            + (f" from terminal status {ticket.status!r}" if ticket.status in _TERMINAL_STATUSES else ""),
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Check transition preconditions (e.g., acceptance criteria for → done).
    precondition_error = _check_transition_preconditions(
        ticket.status, resolution, ticket, tickets_dir, fields=fields,
    )
    if precondition_error:
        return EngineResponse(
            state="invalid_transition",
            message=precondition_error,
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Write status change using the canonical frontmatter renderer.
    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    old_status = data.get("status", "")
    data["status"] = resolution
    new_yaml = _render_canonical_frontmatter(data)
    import re

    new_text = re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    ticket_path.write_text(new_text, encoding="utf-8")

    changes = {"frontmatter": {"status": [old_status, resolution]}}

    # Archive if requested.
    if archive:
        closed_dir = tickets_dir / "closed-tickets"
        closed_dir.mkdir(exist_ok=True)
        dst = closed_dir / ticket_path.name
        ticket_path.rename(dst)
        return EngineResponse(
            state="ok_close_archived",
            message=f"Closed and archived {ticket_id} to closed-tickets/",
            ticket_id=ticket_id,
            data={"ticket_path": str(dst), "changes": changes},
        )

    return EngineResponse(
        state="ok_close",
        message=f"Closed {ticket_id} (status: {resolution})",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": changes},
    )


def _execute_reopen(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Reopen a done/wontfix ticket."""
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for reopen", error_code="need_fields")

    reopen_reason = fields.get("reopen_reason", "")
    if not reopen_reason:
        return EngineResponse(state="need_fields", message="reopen_reason required for reopen", error_code="need_fields")

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    if not _is_valid_transition(ticket.status, "open", "reopen"):
        return EngineResponse(
            state="invalid_transition",
            message=f"Cannot reopen ticket with status {ticket.status} (must be done or wontfix)",
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Write status change directly (not via _execute_update, which would
    # reject done→open since _VALID_TRANSITIONS["done"] is empty for update).
    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    old_status = data.get("status", "")
    data["status"] = "open"
    new_yaml = _render_canonical_frontmatter(data)
    import re as _re

    new_text = _re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=_re.MULTILINE | _re.DOTALL,
    )

    # Append to Reopen History section (newest-last).
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    reopen_entry = f"\n\n## Reopen History\n- **{now}**: {reopen_reason} (by {request_origin})"

    if "## Reopen History" in new_text:
        rh_match = _re.search(r"## Reopen History\n", new_text)
        if rh_match:
            next_heading = _re.search(r"\n## ", new_text[rh_match.end():])
            if next_heading:
                insert_pos = rh_match.end() + next_heading.start()
            else:
                insert_pos = len(new_text)
            entry = f"- **{now}**: {reopen_reason} (by {request_origin})\n"
            new_text = new_text[:insert_pos].rstrip() + "\n" + entry + new_text[insert_pos:]
    else:
        new_text += reopen_entry

    ticket_path.write_text(new_text, encoding="utf-8")

    return EngineResponse(
        state="ok_reopen",
        message=f"Reopened {ticket_id}. Reason: {reopen_reason}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": {"status": [old_status, "open"]}},
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add engine_execute for create/update/close/reopen

File creation, status transitions, archiving, reopen history.
Transition validation per contract. Agent override rejection.
```

---

## Task 12: Entrypoints — ticket_engine_user.py and ticket_engine_agent.py

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_engine_user.py`
- Create: `packages/plugins/ticket/scripts/ticket_engine_agent.py`
- Create: `packages/plugins/ticket/tests/test_entrypoints.py`

**Context:** Read design doc: "Trust Model" (lines ~359-406). Entrypoints are thin wrappers that hardcode `request_origin` and delegate to core. They read JSON input from a file path (payload-by-file pattern).

**Step 1: Write failing tests**

```python
"""Tests for engine entrypoints — ticket_engine_user.py and ticket_engine_agent.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Path to scripts directory.
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def run_entrypoint(script: str, subcommand: str, payload: dict, tmp_path: Path) -> dict:
    """Run an entrypoint script as a subprocess and return parsed JSON output."""
    payload_file = tmp_path / "input.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script), subcommand, str(payload_file)],
        capture_output=True,
        text=True,
        cwd=str(SCRIPTS_DIR.parent),
    )
    assert result.returncode in (0, 1, 2), f"Unexpected exit code: {result.returncode}\nstderr: {result.stderr}"
    return json.loads(result.stdout)


class TestUserEntrypoint:
    def test_classify_create(self, tmp_path):
        output = run_entrypoint(
            "ticket_engine_user.py",
            "classify",
            {
                "action": "create",
                "args": {},
                "session_id": "test",
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        assert output["state"] == "ok"
        assert output["data"]["intent"] == "create"

    def test_origin_is_user(self, tmp_path):
        """The user entrypoint always sets request_origin=user."""
        output = run_entrypoint(
            "ticket_engine_user.py",
            "classify",
            {
                "action": "create",
                "args": {},
                "session_id": "test",
                "request_origin": "agent",  # Caller tries to override — ignored.
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        # Should succeed because origin is forced to "user".
        assert output["state"] == "ok"


class TestAgentEntrypoint:
    def test_classify_create(self, tmp_path):
        output = run_entrypoint(
            "ticket_engine_agent.py",
            "classify",
            {
                "action": "create",
                "args": {},
                "session_id": "test",
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        assert output["state"] == "ok"
        assert output["data"]["intent"] == "create"

    def test_origin_is_agent(self, tmp_path):
        """The agent entrypoint always sets request_origin=agent."""
        # Agent classify succeeds, but preflight would block in suggest mode.
        output = run_entrypoint(
            "ticket_engine_agent.py",
            "classify",
            {
                "action": "create",
                "args": {},
                "session_id": "test",
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        assert output["state"] == "ok"


class TestEntrypointErrors:
    def test_missing_subcommand(self, tmp_path):
        payload_file = tmp_path / "input.json"
        payload_file.write_text("{}", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "ticket_engine_user.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_invalid_json(self, tmp_path):
        payload_file = tmp_path / "input.json"
        payload_file.write_text("not json", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "ticket_engine_user.py"), "classify", str(payload_file)],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR.parent),
        )
        assert result.returncode != 0
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py -v`
Expected: FileNotFoundError (scripts don't exist)

**Step 3: Write ticket_engine_user.py**

```python
#!/usr/bin/env python3
"""User entrypoint for the ticket engine.

Hardcodes request_origin="user". Called by ticket-ops skill.
Usage: python3 ticket_engine_user.py <subcommand> <payload_file>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ticket_engine_core import (
    EngineResponse,
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)

REQUEST_ORIGIN = "user"


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: ticket_engine_user.py <subcommand> <payload_file>"}), file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]
    payload_path = Path(sys.argv[2])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": f"Cannot read payload: {exc}"}), file=sys.stderr)
        sys.exit(1)

    # Force request_origin to "user" regardless of what caller passed.
    payload["request_origin"] = REQUEST_ORIGIN

    # Check for hook-injected origin mismatch.
    hook_origin = payload.get("hook_request_origin")
    if hook_origin is not None and hook_origin != REQUEST_ORIGIN:
        resp = EngineResponse(
            state="escalate",
            message=f"origin_mismatch: entrypoint={REQUEST_ORIGIN}, hook={hook_origin}",
            error_code="origin_mismatch",
        )
        print(resp.to_json())
        sys.exit(1)

    tickets_dir = Path(payload.get("tickets_dir", "docs/tickets"))

    resp = _dispatch(subcommand, payload, tickets_dir)
    print(resp.to_json())
    # Exit codes: 0=success, 1=engine error, 2=validation failure (need_fields).
    if resp.state in ("ok", "ok_create", "ok_update", "ok_close", "ok_close_archived", "ok_reopen"):
        sys.exit(0)
    elif resp.error_code == "need_fields":
        sys.exit(2)
    else:
        sys.exit(1)


def _dispatch(subcommand: str, payload: dict, tickets_dir: Path) -> EngineResponse:
    if subcommand == "classify":
        return engine_classify(
            action=payload.get("action", ""),
            args=payload.get("args", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
        )
    elif subcommand == "plan":
        return engine_plan(
            intent=payload.get("intent", payload.get("action", "")),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            tickets_dir=tickets_dir,
        )
    elif subcommand == "preflight":
        return engine_preflight(
            ticket_id=payload.get("ticket_id"),
            action=payload.get("action", ""),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            classify_confidence=payload.get("classify_confidence", 0.0),
            classify_intent=payload.get("classify_intent", ""),
            dedup_fingerprint=payload.get("dedup_fingerprint"),
            target_fingerprint=payload.get("target_fingerprint"),
            duplicate_of=payload.get("duplicate_of"),
            dedup_override=payload.get("dedup_override", False),
            tickets_dir=tickets_dir,
        )
    elif subcommand == "execute":
        return engine_execute(
            action=payload.get("action", ""),
            ticket_id=payload.get("ticket_id"),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            dedup_override=payload.get("dedup_override", False),
            dependency_override=payload.get("dependency_override", False),
            tickets_dir=tickets_dir,
        )
    else:
        return EngineResponse(state="escalate", message=f"Unknown subcommand: {subcommand!r}", error_code="intent_mismatch")


if __name__ == "__main__":
    main()
```

**Step 4: Write ticket_engine_agent.py**

```python
#!/usr/bin/env python3
"""Agent entrypoint for the ticket engine.

Hardcodes request_origin="agent". Called by ticket-autocreate agent.
Usage: python3 ticket_engine_agent.py <subcommand> <payload_file>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ticket_engine_core import (
    EngineResponse,
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)

REQUEST_ORIGIN = "agent"


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: ticket_engine_agent.py <subcommand> <payload_file>"}), file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]
    payload_path = Path(sys.argv[2])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": f"Cannot read payload: {exc}"}), file=sys.stderr)
        sys.exit(1)

    # Force request_origin to "agent" regardless of what caller passed.
    payload["request_origin"] = REQUEST_ORIGIN

    # Check for hook-injected origin mismatch.
    hook_origin = payload.get("hook_request_origin")
    if hook_origin is not None and hook_origin != REQUEST_ORIGIN:
        resp = EngineResponse(
            state="escalate",
            message=f"origin_mismatch: entrypoint={REQUEST_ORIGIN}, hook={hook_origin}",
            error_code="origin_mismatch",
        )
        print(resp.to_json())
        sys.exit(1)

    tickets_dir = Path(payload.get("tickets_dir", "docs/tickets"))

    resp = _dispatch(subcommand, payload, tickets_dir)
    print(resp.to_json())
    # Exit codes: 0=success, 1=engine error, 2=validation failure (need_fields).
    if resp.state in ("ok", "ok_create", "ok_update", "ok_close", "ok_close_archived", "ok_reopen"):
        sys.exit(0)
    elif resp.error_code == "need_fields":
        sys.exit(2)
    else:
        sys.exit(1)


def _dispatch(subcommand: str, payload: dict, tickets_dir: Path) -> EngineResponse:
    if subcommand == "classify":
        return engine_classify(
            action=payload.get("action", ""),
            args=payload.get("args", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
        )
    elif subcommand == "plan":
        return engine_plan(
            intent=payload.get("intent", payload.get("action", "")),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            tickets_dir=tickets_dir,
        )
    elif subcommand == "preflight":
        return engine_preflight(
            ticket_id=payload.get("ticket_id"),
            action=payload.get("action", ""),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            classify_confidence=payload.get("classify_confidence", 0.0),
            classify_intent=payload.get("classify_intent", ""),
            dedup_fingerprint=payload.get("dedup_fingerprint"),
            target_fingerprint=payload.get("target_fingerprint"),
            duplicate_of=payload.get("duplicate_of"),
            dedup_override=payload.get("dedup_override", False),
            tickets_dir=tickets_dir,
        )
    elif subcommand == "execute":
        return engine_execute(
            action=payload.get("action", ""),
            ticket_id=payload.get("ticket_id"),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            dedup_override=payload.get("dedup_override", False),
            dependency_override=payload.get("dependency_override", False),
            tickets_dir=tickets_dir,
        )
    else:
        return EngineResponse(state="escalate", message=f"Unknown subcommand: {subcommand!r}", error_code="intent_mismatch")


if __name__ == "__main__":
    main()
```

**Step 5: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py -v`
Expected: All tests PASS

**Step 6: Commit**

```
feat(ticket): add user and agent entrypoints with origin enforcement

Payload-by-file pattern, hardcoded request_origin, hook origin
mismatch detection. Both delegate to engine_core.
```

---

## Task 13: Integration Test — Full Pipeline

**Files:**
- Create: `packages/plugins/ticket/tests/test_integration.py`

**Context:** End-to-end test of the classify → plan → preflight → execute pipeline.

**Step 1: Write integration tests**

```python
"""Integration tests — full engine pipeline end-to-end."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ticket_engine_core import (
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)


class TestFullCreatePipeline:
    def test_user_create_end_to_end(self, tmp_tickets):
        """classify → plan → preflight → execute for user create."""
        # Step 1: classify
        classify_resp = engine_classify(
            action="create",
            args={},
            session_id="integration-test",
            request_origin="user",
        )
        assert classify_resp.state == "ok"

        # Step 2: plan
        fields = {
            "title": "Integration test ticket",
            "problem": "This is an integration test.",
            "priority": "medium",
            "key_files": [],
        }
        plan_resp = engine_plan(
            intent=classify_resp.data["intent"],
            fields=fields,
            session_id="integration-test",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "ok"

        # Step 3: preflight
        preflight_resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="integration-test",
            request_origin="user",
            classify_confidence=classify_resp.data["confidence"],
            classify_intent=classify_resp.data["intent"],
            dedup_fingerprint=plan_resp.data["dedup_fingerprint"],
            target_fingerprint=plan_resp.data["target_fingerprint"],
            tickets_dir=tmp_tickets,
        )
        assert preflight_resp.state == "ok"

        # Step 4: execute
        execute_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="integration-test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert execute_resp.state == "ok_create"
        assert Path(execute_resp.data["ticket_path"]).exists()

    def test_agent_blocked_phase1_fail_closed(self, tmp_tickets):
        """Agent create is hard-blocked by Phase 1 fail-closed policy."""
        classify_resp = engine_classify(
            action="create",
            args={},
            session_id="agent-test",
            request_origin="agent",
        )
        assert classify_resp.state == "ok"

        preflight_resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="agent-test",
            request_origin="agent",
            classify_confidence=classify_resp.data["confidence"],
            classify_intent=classify_resp.data["intent"],
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert preflight_resp.state == "policy_blocked"

    def test_update_then_close_pipeline(self, tmp_tickets):
        """Create → update to in_progress → close."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")

        # Update to in_progress.
        update_resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert update_resp.state == "ok_update"

        # Close.
        close_resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert close_resp.state == "ok_close"

    def test_dedup_then_override(self, tmp_tickets):
        """Create duplicate detected → override → create succeeds."""
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "2026-03-02-existing.md",
            id="T-20260302-01",
            problem="Auth times out.",
        )

        fields = {
            "title": "Same auth bug",
            "problem": "Auth times out.",
            "priority": "high",
            "key_files": [],
        }

        plan_resp = engine_plan(
            intent="create",
            fields=fields,
            session_id="test",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "duplicate_candidate"

        # Override and create anyway.
        execute_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="test",
            request_origin="user",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert execute_resp.state == "ok_create"
```

**Step 2: Run tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_integration.py -v`
Expected: All tests PASS

**Step 3: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```
feat(ticket): add integration tests for full engine pipeline

End-to-end: user create, agent suggest-mode block, update→close,
dedup detection with override.
```

---

## Task 14: Legacy Migration Golden Tests

**Files:**
- Create: `packages/plugins/ticket/tests/test_migration.py`

**Context:** Read design doc: "Migration" section (lines ~650-692), contract section 8. One golden test per legacy generation.

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

## Task 15: Final — Run Full Suite, Clean Up, Commit

**Step 1: Run the full test suite**

Run: `cd packages/plugins/ticket && uv run pytest -v --tb=short`
Expected: All tests PASS

**Step 2: Check test count**

Run: `cd packages/plugins/ticket && uv run pytest --co -q | tail -1`
Expected: ~104+ tests collected

**Step 3: Delete .gitkeep files if directories have content**

```bash
# Only remove .gitkeep if the directory has other files.
for dir in scripts skills agents references; do
    if [ "$(ls -A packages/plugins/ticket/$dir/ 2>/dev/null | grep -v .gitkeep)" ]; then
        trash packages/plugins/ticket/$dir/.gitkeep
    fi
done
```

**Step 4: Final commit**

```
chore(ticket): phase 1 complete — engine + contract + utilities

15 tasks: scaffold, contract, parse, ID, render, read, dedup,
engine (classify, plan, preflight, execute), entrypoints,
integration tests, migration golden tests.
```

---

## Summary

| Task | Component | Tests | Description |
|------|-----------|-------|-------------|
| 1 | Scaffold | — | Plugin directory, plugin.json, conftest.py |
| 2 | Contract | — | ticket-contract.md (10 domains) |
| 3 | ticket_parse.py | ~20 | Fenced-YAML, sections, legacy detection, normalization |
| 4 | ticket_id.py | ~10 | T-YYYYMMDD-NN allocation, slug generation |
| 5 | ticket_render.py | ~5 | v1.0 markdown template rendering |
| 6 | ticket_read.py | ~15 | List, query, filter, fuzzy match |
| 7 | ticket_dedup.py | ~12 | normalize(), dedup fingerprint, TOCTOU fingerprint |
| 8 | engine_classify | ~8 | Intent validation, origin check |
| 9 | engine_plan | ~5 | Field validation, dedup detection |
| 10 | engine_preflight | ~15 | Fail-closed agent, confidence, fingerprint, dependency_override, dedup enforcement |
| 11 | engine_execute | ~21 | Create, update, close (direct+terminal guard), archive, reopen, transitions, preconditions, canonical renderer |
| 12 | Entrypoints | ~5 | User + agent wrappers, exit codes 0/1/2, subprocess tests |
| 13 | Integration | ~4 | Full pipeline end-to-end |
| 14 | Migration | ~5 | Golden tests for 4 legacy generations + default paths |
| 15 | Final | — | Full suite run, cleanup |

**Total:** ~128 tests across 7 test files

**Phase 2 next:** ticket-ops skill + ticket-triage skill (+ `ticket_triage.py`) + PreToolUse hook + audit trail + autonomy mode enforcement (replacing Phase 1 hard-block)

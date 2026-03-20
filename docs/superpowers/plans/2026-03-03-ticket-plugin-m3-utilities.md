# Ticket Plugin Phase 1 — Module 3: Utilities

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build four utility modules: ID allocation (`ticket_id.py`), Markdown rendering (`ticket_render.py`), shared read module (`ticket_read.py`), and dedup/fingerprinting (`ticket_dedup.py`).

**Architecture:** Hybrid adapter pattern (Architecture E). These four modules provide the utility layer that the engine (Module 4) imports. Each is a standalone module with its own test file. Tasks 4 and 6 import from `ticket_parse` (Module 2). Tasks 5 and 7 are self-contained (no `ticket_parse` imports).

**Tech Stack:** Python 3.11+, PyYAML, pytest

**References (read-only — do not modify these files):**
- Canonical plan: `docs/plans/2026-03-02-ticket-plugin-phase1-plan.md`
- Modularization design: `docs/plans/2026-03-02-ticket-plugin-plan-modularization.md`
- Design doc: `docs/plans/2026-03-02-ticket-plugin-design.md` (canonical spec)

**Scope:** Module 3 of 5. Creates 4 source modules and 4 test files. Sequential execution: Task 4 → 5 → 6 → 7.

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
- Plugin scaffold, conftest.py with `tmp_tickets`, `tmp_audit`, `make_ticket`, `make_gen1/2/3/4_ticket`
- `references/ticket-contract.md`

**From Module 2 (already implemented):**
- `scripts/ticket_parse.py` with exports:
  - `ParsedTicket` — dataclass with fields: `path`, `frontmatter` (dict), `body` (str), `raw` (str)
  - `parse_ticket(path: Path) -> ParsedTicket`
  - `extract_fenced_yaml(text: str) -> str | None`
  - `parse_yaml_block(yaml_text: str) -> dict[str, Any]`
- `tests/test_parse.py` (~20 tests, passing)
- `tests/test_migration.py` (~5 tests, passing)

**M2→M3 gate passed:** Forward-dependency sentinels verified — `extract_fenced_yaml`, `parse_yaml_block`, `ParsedTicket`, `parse_ticket` all import successfully.

## Gate Entry: M2 → M3

The M2→M3 gate card should be committed. Verify before starting:
```bash
cd packages/plugins/ticket && uv run pytest tests/test_parse.py tests/test_migration.py -v
```
All tests must pass.

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

from scripts.ticket_parse import extract_fenced_yaml, parse_yaml_block  # from Module 2, already implemented

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

from scripts.ticket_parse import ParsedTicket, parse_ticket  # from Module 2, already implemented


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

## Gate Exit: M3 → M4

**Gate Type:** Critical

Standard+ checks PLUS full upstream re-run PLUS downstream preflight.

**What the reviewer checks after M3 completes:**

1. **Full upstream test re-run:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/test_parse.py tests/test_migration.py tests/test_id.py tests/test_render.py tests/test_read.py tests/test_dedup.py -v
   ```

2. **Downstream preflight — M4's full import subset:**
   Import-only smoke tests verifying all symbols M4 needs:
   ```python
   # From ticket_parse (Module 2):
   from scripts.ticket_parse import ParsedTicket, parse_ticket, extract_fenced_yaml, parse_yaml_block

   # From ticket_read (this module):
   from scripts.ticket_read import find_ticket_by_id, list_tickets

   # From ticket_dedup (this module):
   from scripts.ticket_dedup import dedup_fingerprint, normalize, target_fingerprint

   # From ticket_id (this module):
   from scripts.ticket_id import allocate_id, build_filename

   # From ticket_render (this module):
   from scripts.ticket_render import render_ticket
   ```

3. **API surface:** All symbols listed above importable.

4. **Verdict:** Mechanically derived — PASS iff all commands exit 0, all imports succeed.

**Gate Card Template (reviewer fills this in):**
```
## Gate Card: M3 → M4
evaluated_sha: <executor's final commit SHA>
handoff_sha: <reviewer's commit after adding this gate card>
commands_to_run: ["cd packages/plugins/ticket && uv run pytest tests/test_parse.py tests/test_migration.py tests/test_id.py tests/test_render.py tests/test_read.py tests/test_dedup.py -v"]
must_pass_files: [tests/test_parse.py, tests/test_migration.py, tests/test_id.py, tests/test_render.py, tests/test_read.py, tests/test_dedup.py]
api_surface_expected:
  - scripts.ticket_parse: [ParsedTicket, parse_ticket, extract_fenced_yaml, parse_yaml_block]
  - scripts.ticket_id: [allocate_id, build_filename]
  - scripts.ticket_render: [render_ticket]
  - scripts.ticket_read: [find_ticket_by_id, list_tickets]
  - scripts.ticket_dedup: [dedup_fingerprint, normalize, target_fingerprint]
verdict: PASS | FAIL
warnings: []
probe_evidence:
  - command: "python -c 'from scripts.ticket_parse import ParsedTicket, parse_ticket, extract_fenced_yaml, parse_yaml_block'"
    result: "<output>"
  - command: "python -c 'from scripts.ticket_read import find_ticket_by_id, list_tickets'"
    result: "<output>"
  - command: "python -c 'from scripts.ticket_dedup import dedup_fingerprint, normalize, target_fingerprint'"
    result: "<output>"
  - command: "python -c 'from scripts.ticket_id import allocate_id, build_filename'"
    result: "<output>"
  - command: "python -c 'from scripts.ticket_render import render_ticket'"
    result: "<output>"
```

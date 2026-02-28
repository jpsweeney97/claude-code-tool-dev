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


class TestEndToEnd:
    """Integration test: write_ticket -> allocate_id -> parse_ticket round-trip."""

    def test_full_defer_pipeline(self, tmp_path: Path) -> None:
        from scripts.defer import allocate_id, write_ticket
        from scripts.ticket_parsing import parse_ticket

        # Setup: one existing ticket
        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()
        (tickets_dir / "existing.md").write_text(EXISTING_TICKET)

        # Step 1: Create a new ticket
        candidate = {
            "id": "T-20260228-02",
            "date": "2026-02-28",
            "summary": "Auth module needs refactoring",
            "problem": "The auth module has accumulated technical debt.",
            "source_text": "Identified during PR #29 review.",
            "proposed_approach": "Extract shared auth logic into a base class.",
            "acceptance_criteria": ["Base class created", "All auth tests pass", "No duplicate code"],
            "priority": "high",
            "source_type": "pr-review",
            "source_ref": "PR #29",
            "branch": "feature/knowledge-graduation",
            "session_id": "5136e38e-efc5-403f-ad5e-49516f47884b",
            "effort": "M",
            "files": ["src/auth/base.py", "src/auth/oauth.py"],
        }
        path = write_ticket(candidate, tickets_dir)

        # Step 2: Verify file was created
        assert path.exists()
        content = path.read_text()

        # Step 3: Verify structure
        assert content.startswith("# T-20260228-02:")
        assert "```yaml" in content
        assert "id: T-20260228-02" in content
        assert "status: deferred" in content
        assert "priority: high" in content
        assert "effort: M" in content
        assert "## Problem" in content
        assert "## Acceptance Criteria" in content
        assert "- [ ] Base class created" in content

        # Step 4: Verify provenance (both YAML field and HTML comment)
        assert "provenance:" in content
        assert "5136e38e-efc5-403f-ad5e-49516f47884b" in content
        assert "defer-meta" in content

        # Step 5: Verify allocate_id increments past the new ticket
        next_id = allocate_id("2026-02-28", tickets_dir)
        assert next_id == "T-20260228-03"

        # Step 6: Round-trip via parse_ticket
        parsed = parse_ticket(path)
        assert parsed is not None
        assert parsed.frontmatter["id"] == "T-20260228-02"
        assert parsed.frontmatter["status"] == "deferred"
        assert parsed.frontmatter["priority"] == "high"
        assert isinstance(parsed.frontmatter["files"], list)
        assert len(parsed.frontmatter["files"]) == 2
        assert parsed.frontmatter["provenance"]["source_session"] == "5136e38e-efc5-403f-ad5e-49516f47884b"
        assert "## Problem" in parsed.body

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

    def test_recognizes_three_digit_sequence(self, tmp_path: Path) -> None:
        """IDs with 3+ digit sequences (e.g. T-20260228-100) must be recognized."""
        from scripts.defer import allocate_id

        ticket = tmp_path / "high-seq.md"
        ticket.write_text(EXISTING_TICKET.replace("T-20260228-01", "T-20260228-100"))
        result = allocate_id("2026-02-28", tmp_path)
        assert result == "T-20260228-101"


class TestFilenameSlugThreeDigit:
    def test_three_digit_id_parses_date(self) -> None:
        """filename_slug must extract the date from 3+ digit IDs, not fall back to 'unknown'."""
        from scripts.defer import filename_slug

        result = filename_slug("T-20260228-100", "overflow ticket")
        assert result.startswith("2026-02-28-")
        assert "unknown" not in result


class TestQuoteEscaping:
    """C1/C2: _quote must escape backslashes and newlines for valid YAML."""

    def test_backslash_yaml_round_trip(self) -> None:
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "C:\\Users\\test\\file.py",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "C:\\Users\\test\\file.py"

    def test_newline_yaml_round_trip(self) -> None:
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "line1\nline2",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "line1\nline2"

    def test_implicit_yes_yaml_round_trip(self) -> None:
        """Codex amendment: YAML implicit scalar coercion defense."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "yes",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "yes"

    def test_implicit_on_yaml_round_trip(self) -> None:
        """Codex amendment: YAML implicit scalar coercion defense."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "branch": "on",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        # "on" must round-trip as the string "on", not boolean True
        assert parsed["branch"] == "on"

    def test_nel_yaml_round_trip(self) -> None:
        """Codex adversarial amendment: Unicode NEL escape must round-trip."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "before\x85after",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "before\x85after"

    def test_ls_ps_yaml_round_trip(self) -> None:
        """Codex adversarial amendment: Unicode LS/PS escapes must round-trip."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "ls\u2028ps\u2029end",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "ls\u2028ps\u2029end"

    def test_numeric_string_yaml_round_trip(self) -> None:
        """Codex adversarial-challenge: bare numeric strings must round-trip."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "123",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "123"

    def test_octal_string_yaml_round_trip(self) -> None:
        """Codex adversarial-challenge: octal-like strings must round-trip as strings."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "0777",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "0777"

    def test_inf_string_yaml_round_trip(self) -> None:
        """Codex adversarial-challenge: .inf must round-trip as string."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": ".inf",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == ".inf"

    def test_nan_string_yaml_round_trip(self) -> None:
        """Codex adversarial-challenge: .nan must round-trip as string."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": ".nan",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == ".nan"


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


class TestEnumCoercionWarning:
    """I6: Invalid priority/effort must warn when coerced to default."""

    def test_warns_on_invalid_priority(self) -> None:
        import warnings

        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "priority": "urgent",
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = render_ticket(candidate)
        assert "priority: medium" in result or 'priority: "medium"' in result
        assert any("priority" in str(x.message) and "urgent" in str(x.message) for x in w)

    def test_warns_on_invalid_effort(self) -> None:
        import warnings

        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "effort": "XXL",
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = render_ticket(candidate)
        assert any("effort" in str(x.message) and "XXL" in str(x.message) for x in w)


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

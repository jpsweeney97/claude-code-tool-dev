"""Tests for triage.py — ticket reading, status normalization, orphan detection."""
from __future__ import annotations

import re
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

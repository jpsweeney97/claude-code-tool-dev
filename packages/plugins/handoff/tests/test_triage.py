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

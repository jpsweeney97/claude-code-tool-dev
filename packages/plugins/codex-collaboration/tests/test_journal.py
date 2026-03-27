from __future__ import annotations

from pathlib import Path

from server.journal import OperationJournal
from server.models import StaleAdvisoryContextMarker


def test_stale_marker_keys_are_normalized_on_write(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=str(tmp_path / "."),
            promoted_head="head-1",
            recorded_at="2026-03-27T15:00:00Z",
        )
    )

    marker = journal.load_stale_marker(tmp_path)
    assert marker is not None
    assert marker.repo_root == str(tmp_path.resolve())


def test_stale_marker_write_replaces_prior_head_for_repo_root(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    normalized_root = str(tmp_path.resolve())
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=normalized_root,
            promoted_head="head-1",
            recorded_at="2026-03-27T15:00:00Z",
        )
    )
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=normalized_root,
            promoted_head="head-2",
            recorded_at="2026-03-27T15:05:00Z",
        )
    )

    marker = journal.load_stale_marker(tmp_path)
    assert marker is not None
    assert marker.promoted_head == "head-2"


def test_clear_stale_marker_uses_normalized_repo_root(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=str(tmp_path.resolve()),
            promoted_head="head-1",
            recorded_at="2026-03-27T15:00:00Z",
        )
    )

    journal.clear_stale_marker(Path(str(tmp_path / ".")))

    assert journal.load_stale_marker(tmp_path) is None

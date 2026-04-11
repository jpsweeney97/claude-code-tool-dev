"""Tests for shared T4 containment helpers."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from server import containment


def test_read_active_run_id_missing_returns_none(tmp_path: Path) -> None:
    assert containment.read_active_run_id(tmp_path, "session-1") is None


def test_build_scope_from_seed_adds_agent_id() -> None:
    scope = containment.build_scope_from_seed(
        {
            "session_id": "session-1",
            "run_id": "run-1",
            "file_anchors": ["/repo/anchor.txt"],
            "scope_directories": ["/repo"],
            "created_at": "2026-04-08T00:00:00Z",
        },
        "agent-1",
    )
    assert scope["agent_id"] == "agent-1"
    assert scope["run_id"] == "run-1"
    assert scope["file_anchors"] == ["/repo/anchor.txt"]


def test_derive_scope_directories_deduplicates_parent_directories(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    nested = docs / "nested"
    nested.mkdir(parents=True)
    server_dir = repo / "server"
    server_dir.mkdir()
    anchors = [
        str(docs / "contracts.md"),
        str(docs / "delivery.md"),
        str(server_dir / "mcp_server.py"),
    ]
    directories = containment.derive_scope_directories(anchors)
    assert directories == [str(docs.resolve()), str(server_dir.resolve())]


def test_is_path_within_scope_allows_exact_file_anchor(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    anchor = repo / "anchor.txt"
    anchor.write_text("anchor", encoding="utf-8")

    assert containment.is_path_within_scope(
        str(anchor),
        [str(anchor)],
        [str(repo)],
    )


def test_is_path_within_scope_allows_scope_directory_member(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    anchor = repo / "anchor.txt"
    sibling = repo / "sibling.txt"
    anchor.write_text("anchor", encoding="utf-8")
    sibling.write_text("sibling", encoding="utf-8")

    assert containment.is_path_within_scope(
        str(sibling),
        [str(anchor)],
        [str(repo)],
    )


def test_is_path_within_scope_denies_symlink_resolving_outside(tmp_path: Path) -> None:
    scope_dir = tmp_path / "scope"
    scope_dir.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    symlink = scope_dir / "link.txt"
    try:
        symlink.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    assert not containment.is_path_within_scope(
        str(symlink),
        [],
        [str(scope_dir)],
    )


def test_select_scope_root_for_grep_prefers_exact_anchor(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    anchor = repo / "anchor.txt"
    anchor.write_text("anchor", encoding="utf-8")

    selected = containment.select_scope_root(
        [str(anchor)],
        [str(repo)],
        str(anchor),
        "Grep",
    )

    assert selected == str(anchor.resolve())


def test_select_scope_root_for_grep_falls_back_to_scope_directory(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    anchor = repo / "anchor.txt"
    sibling = repo / "sibling.txt"
    anchor.write_text("anchor", encoding="utf-8")
    sibling.write_text("sibling", encoding="utf-8")

    selected = containment.select_scope_root(
        [str(anchor)],
        [str(repo)],
        str(sibling),
        "Grep",
    )

    assert selected == str(repo.resolve())


def test_select_scope_root_for_glob_returns_scope_directory(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    anchor = repo / "anchor.txt"
    anchor.write_text("anchor", encoding="utf-8")

    selected = containment.select_scope_root(
        [str(anchor)],
        [str(repo)],
        str(anchor),
        "Glob",
    )

    assert selected == str(repo.resolve())


def test_select_scope_root_returns_none_for_pathless_queries() -> None:
    assert (
        containment.select_scope_root(
            ["/repo/anchor.txt"],
            ["/repo"],
            None,
            "Grep",
        )
        is None
    )


def test_write_json_file_and_read_json_file_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "scope.json"
    containment.write_json_file(target, {"run_id": "run-1", "agent_id": "agent-1"})

    assert containment.read_json_file(target) == {
        "agent_id": "agent-1",
        "run_id": "run-1",
    }


def test_write_text_file_supports_active_run_round_trip(tmp_path: Path) -> None:
    containment.write_text_file(
        containment.active_run_path(tmp_path, "session-1"),
        "run-1",
    )

    assert containment.read_active_run_id(tmp_path, "session-1") == "run-1"


def test_append_jsonl_appends_multiple_rows(tmp_path: Path) -> None:
    target = containment.poll_telemetry_path(tmp_path)
    containment.append_jsonl(target, {"branch_id": "one"})
    containment.append_jsonl(target, {"branch_id": "two"})

    rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"branch_id": "one"}, {"branch_id": "two"}]


def test_clean_stale_files_removes_old_state_only(tmp_path: Path) -> None:
    shakedown_dir = containment.shakedown_dir(tmp_path)
    shakedown_dir.mkdir(parents=True)
    old_scope = shakedown_dir / "scope-run-1.json"
    old_done = shakedown_dir / "transcript-run-1.done"
    fresh_seed = shakedown_dir / "seed-run-2.json"
    retained_transcript = shakedown_dir / "transcript-run-1.jsonl"
    old_scope.write_text("{}", encoding="utf-8")
    old_done.write_text("", encoding="utf-8")
    fresh_seed.write_text("{}", encoding="utf-8")
    retained_transcript.write_text("[]", encoding="utf-8")

    stale_time = time.time() - (26 * 3600)
    os.utime(old_scope, (stale_time, stale_time))
    os.utime(old_done, (stale_time, stale_time))

    containment.clean_stale_files(shakedown_dir)

    assert not old_scope.exists()
    assert not old_done.exists()
    assert fresh_seed.exists()
    assert retained_transcript.exists()


def test_clean_stale_files_returns_result_with_removed_and_fresh(
    tmp_path: Path,
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    old_scope = shakedown / "scope-run-1.json"
    fresh_seed = shakedown / "seed-run-2.json"
    old_scope.write_text("{}", encoding="utf-8")
    fresh_seed.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(old_scope, (stale_time, stale_time))

    result = containment.clean_stale_files(shakedown)

    assert isinstance(result, containment.CleanStaleResult)
    assert result.removed == (old_scope,)
    assert result.skipped_fresh == (fresh_seed,)
    assert result.failed_stat == ()
    assert result.failed_unlink == ()
    assert result.had_errors is False


def test_read_active_run_id_strict_returns_none_when_missing(tmp_path: Path) -> None:
    assert containment.read_active_run_id_strict(tmp_path, "session-1") is None


def test_read_active_run_id_strict_returns_run_id_when_valid(tmp_path: Path) -> None:
    containment.write_text_file(containment.active_run_path(tmp_path, "session-1"), "run-1")
    assert containment.read_active_run_id_strict(tmp_path, "session-1") == "run-1"


def test_read_active_run_id_strict_raises_on_empty(tmp_path: Path) -> None:
    pointer = containment.active_run_path(tmp_path, "session-1")
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        containment.read_active_run_id_strict(tmp_path, "session-1")


def test_read_json_file_strict_returns_none_when_missing(tmp_path: Path) -> None:
    assert containment.read_json_file_strict(tmp_path / "nope.json") is None


def test_read_json_file_strict_returns_dict_when_valid(tmp_path: Path) -> None:
    target = tmp_path / "valid.json"
    target.write_text('{"key": "value"}', encoding="utf-8")
    assert containment.read_json_file_strict(target) == {"key": "value"}


def test_read_json_file_strict_raises_on_malformed_json(tmp_path: Path) -> None:
    target = tmp_path / "corrupt.json"
    target.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        containment.read_json_file_strict(target)


def test_read_json_file_strict_raises_on_non_object(tmp_path: Path) -> None:
    target = tmp_path / "array.json"
    target.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="not a JSON object"):
        containment.read_json_file_strict(target)

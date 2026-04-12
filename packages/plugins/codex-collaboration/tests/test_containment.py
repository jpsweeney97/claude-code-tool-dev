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

    result = containment.clean_stale_files(shakedown_dir)

    assert not old_scope.exists()
    assert not old_done.exists()
    assert fresh_seed.exists()
    assert retained_transcript.exists()
    assert set(result.removed) == {old_scope, old_done}
    assert set(result.skipped_fresh) == {fresh_seed, retained_transcript}
    assert result.failed_stat == ()
    assert result.failed_unlink == ()
    assert result.had_errors is False


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


def test_clean_stale_files_captures_unlink_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    stale = shakedown / "scope-run-1.json"
    stale.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(stale, (stale_time, stale_time))

    original_unlink = Path.unlink

    def failing_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == stale:
            raise PermissionError(13, "denied", str(self))
        return original_unlink(self, *args, **kwargs)  # type: ignore[arg-type]

    with monkeypatch.context() as patched:
        patched.setattr(Path, "unlink", failing_unlink)
        result = containment.clean_stale_files(shakedown)

    assert stale.exists(), "stale file should still be on disk after failed unlink"
    assert result.removed == ()
    assert len(result.failed_unlink) == 1
    assert result.failed_unlink[0].path == stale
    assert "PermissionError" in result.failed_unlink[0].error
    assert result.had_errors is True


def test_clean_stale_files_captures_stat_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    unreadable = shakedown / "seed-run-1.json"
    unreadable.write_text("{}", encoding="utf-8")

    original_stat = Path.stat

    def failing_stat(self: Path, *args: object, **kwargs: object) -> os.stat_result:
        if self == unreadable:
            raise PermissionError(13, "denied", str(self))
        return original_stat(self, *args, **kwargs)  # type: ignore[arg-type]

    with monkeypatch.context() as patched:
        patched.setattr(Path, "stat", failing_stat)
        result = containment.clean_stale_files(shakedown)

    # Patch reverted here — safe to use .exists() again.
    assert unreadable.exists(), "stat failure should not cause deletion attempt"
    assert result.removed == ()
    assert result.failed_unlink == ()
    assert len(result.failed_stat) == 1
    assert result.failed_stat[0].path == unreadable
    assert "PermissionError" in result.failed_stat[0].error
    assert result.had_errors is True


def test_clean_stale_files_ignores_candidates_removed_before_stat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    missing = shakedown / "seed-run-1.json"

    with monkeypatch.context() as patched:
        patched.setattr("os.listdir", lambda _path: [missing.name])
        result = containment.clean_stale_files(shakedown)

    assert result.removed == ()
    assert result.skipped_fresh == ()
    assert result.failed_stat == ()
    assert result.failed_unlink == ()
    assert result.had_errors is False


def test_clean_stale_files_ignores_candidates_removed_before_unlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    stale = shakedown / "scope-run-1.json"
    stale.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(stale, (stale_time, stale_time))

    original_stat = Path.stat
    original_unlink = Path.unlink

    def stat_then_remove(self: Path, *args: object, **kwargs: object) -> os.stat_result:
        stat_result = original_stat(self, *args, **kwargs)  # type: ignore[arg-type]
        if self == stale:
            original_unlink(self)
        return stat_result

    with monkeypatch.context() as patched:
        patched.setattr(Path, "stat", stat_then_remove)
        result = containment.clean_stale_files(shakedown)

    assert not stale.exists(), "simulated concurrent deletion should remove the file"
    assert result.removed == ()
    assert result.skipped_fresh == ()
    assert result.failed_stat == ()
    assert result.failed_unlink == ()
    assert result.had_errors is False


def test_clean_stale_files_returns_empty_when_shakedown_root_missing(
    tmp_path: Path,
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    assert not shakedown.exists()

    result = containment.clean_stale_files(shakedown)

    assert result.removed == ()
    assert result.skipped_fresh == ()
    assert result.failed_stat == ()
    assert result.failed_unlink == ()
    assert result.had_errors is False


def test_clean_stale_files_raises_when_root_lstat_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)

    original_lstat = Path.lstat

    def failing_lstat(
        self: Path, *args: object, **kwargs: object
    ) -> os.stat_result:
        if self == shakedown:
            raise PermissionError(13, "denied", str(self))
        return original_lstat(self, *args, **kwargs)  # type: ignore[arg-type]

    with monkeypatch.context() as patched:
        patched.setattr(Path, "lstat", failing_lstat)
        with pytest.raises(OSError, match="cannot lstat shakedown root"):
            containment.clean_stale_files(shakedown)


def test_clean_stale_files_raises_on_dangling_root_symlink(
    tmp_path: Path,
) -> None:
    target = tmp_path / "nonexistent-target"
    link = tmp_path / "shakedown"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    assert not target.exists()
    assert link.is_symlink()

    with pytest.raises(OSError, match="possible broken symlink"):
        containment.clean_stale_files(link)


def test_clean_stale_files_raises_when_root_is_not_a_directory(
    tmp_path: Path,
) -> None:
    not_a_dir = tmp_path / "not-a-dir"
    not_a_dir.write_text("this is a file", encoding="utf-8")

    with pytest.raises(
        NotADirectoryError, match="shakedown root is not a directory"
    ):
        containment.clean_stale_files(not_a_dir)


def test_clean_stale_files_raises_when_enumeration_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Enumeration failure (directory exists and is stat-able but cannot be
    listed) must raise with actionable context, not silently return empty.

    This is the Round 3 review gap: ``stat()`` on a ``chmod 0o000``
    directory succeeds with mode ``0o40000`` (because stat only needs
    execute permission on the parent), so the two-stage ``lstat``/``stat``
    root check cannot detect this class. The enumeration guard is a
    separate layer on top of the stat checks, and this test forces
    ``os.listdir`` to raise to verify the guard propagates the error
    with the expected context message.

    Monkeypatches ``os.listdir`` so the test is portable (no reliance on
    the host's permission semantics). The companion test
    ``test_clean_stale_files_raises_when_root_directory_unreadable``
    exercises the same code path using a real ``chmod 0o000``.
    """
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)

    def failing_listdir(path: object) -> list[str]:
        raise PermissionError(13, "Permission denied", str(path))

    with monkeypatch.context() as patched:
        patched.setattr(os, "listdir", failing_listdir)
        with pytest.raises(OSError, match="cannot enumerate shakedown root"):
            containment.clean_stale_files(shakedown)


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason=(
        "POSIX permission check: chmod 0o000 is bypassed by root "
        "and unavailable on platforms without os.geteuid"
    ),
)
def test_clean_stale_files_raises_when_root_directory_unreadable(
    tmp_path: Path,
) -> None:
    """Real ``chmod 0o000`` on the shakedown root exercises the full
    enumeration path without any monkeypatch.

    Verifies the end-to-end claim:
    - ``Path.lstat`` succeeds on a mode-0o000 directory (it's still a
      filesystem entry)
    - ``Path.stat`` succeeds with mode ``0o40000`` (stat only needs
      execute on the parent)
    - ``S_ISDIR(0o40000)`` is True
    - ``os.listdir`` raises ``PermissionError`` (no read bit)
    - ``clean_stale_files`` re-raises with ``"cannot enumerate"`` context

    Without this test, a refactor that accidentally replaced
    ``os.listdir`` with ``Path.glob`` (or some other silent-swallow
    primitive) could pass the mock-based test above (which only exercises
    the raise path) while reintroducing the silent-failure class this
    ticket is meant to eliminate. The real chmod exercise catches that.

    Skipped when running as root (POSIX permission checks are bypassed)
    or on platforms without ``os.geteuid`` (e.g., Windows).
    """
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    (shakedown / "scope-run-1.json").write_text("{}", encoding="utf-8")
    try:
        os.chmod(shakedown, 0o000)
        with pytest.raises(OSError, match="cannot enumerate shakedown root"):
            containment.clean_stale_files(shakedown)
    finally:
        # Restore permissions so pytest's tmp_path teardown can remove
        # the directory and its contents.
        os.chmod(shakedown, 0o755)


def test_clean_stale_result_report_clean_run_is_single_summary_line(
    tmp_path: Path,
) -> None:
    result = containment.CleanStaleResult(
        removed=(tmp_path / "scope-run-1.json",),
        skipped_fresh=(tmp_path / "seed-run-2.json",),
        failed_stat=(),
        failed_unlink=(),
    )
    assert result.report() == "clean_stale_files: removed=1, fresh=1"


def test_clean_stale_result_report_renders_failure_paths_and_errors(
    tmp_path: Path,
) -> None:
    stat_failed = tmp_path / "seed-run-1.json"
    unlink_failed = tmp_path / "transcript-run-1.jsonl"
    result = containment.CleanStaleResult(
        removed=(tmp_path / "scope-run-1.json",),
        skipped_fresh=(),
        failed_stat=(containment.FileFailure(stat_failed, "PermissionError(13, 'denied')"),),
        failed_unlink=(containment.FileFailure(unlink_failed, "PermissionError(13, 'denied')"),),
    )

    lines = result.report().splitlines()

    assert lines[0] == (
        "clean_stale_files: removed=1, fresh=0, failed_stat=1, failed_unlink=1"
    )
    assert lines[1] == f"  failed_stat {stat_failed}: PermissionError(13, 'denied')"
    assert lines[2] == (
        f"  failed_unlink {unlink_failed}: PermissionError(13, 'denied')"
    )
    assert len(lines) == 3


def test_clean_stale_result_report_applies_prefix_to_every_line(
    tmp_path: Path,
) -> None:
    stat_failed = tmp_path / "seed-run-1.json"
    unlink_failed = tmp_path / "transcript-run-1.jsonl"
    result = containment.CleanStaleResult(
        removed=(tmp_path / "scope-run-1.json",),
        skipped_fresh=(),
        failed_stat=(containment.FileFailure(stat_failed, "PermissionError(13, 'denied')"),),
        failed_unlink=(containment.FileFailure(unlink_failed, "PermissionError(13, 'denied')"),),
    )

    lines = result.report(prefix="containment-lifecycle: ").splitlines()

    assert lines[0] == (
        "containment-lifecycle: clean_stale_files: "
        "removed=1, fresh=0, failed_stat=1, failed_unlink=1"
    )
    assert lines[1] == (
        f"containment-lifecycle:   failed_stat {stat_failed}: "
        f"PermissionError(13, 'denied')"
    )
    assert lines[2] == (
        f"containment-lifecycle:   failed_unlink {unlink_failed}: "
        f"PermissionError(13, 'denied')"
    )
    assert len(lines) == 3
    # Regression guard against P3: every report line carries the prefix so
    # caller attribution is not lost when the per-failure lines are grepped
    # or aggregated separately from the summary line.
    for line in lines:
        assert line.startswith("containment-lifecycle:")


def test_clean_stale_files_mixed_batch_tracks_every_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    removable = shakedown / "scope-run-1.json"
    fresh = shakedown / "seed-run-2.json"
    stat_fails = shakedown / "transcript-run-3.jsonl"
    unlink_fails = shakedown / "transcript-run-4.done"
    for path in (removable, fresh, stat_fails, unlink_fails):
        path.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(removable, (stale_time, stale_time))
    os.utime(unlink_fails, (stale_time, stale_time))

    original_stat = Path.stat
    original_unlink = Path.unlink

    def failing_stat(
        self: Path, *args: object, **kwargs: object
    ) -> os.stat_result:
        if self == stat_fails:
            raise PermissionError(13, "denied", str(self))
        return original_stat(self, *args, **kwargs)  # type: ignore[arg-type]

    def failing_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == unlink_fails:
            raise PermissionError(13, "denied", str(self))
        return original_unlink(self, *args, **kwargs)  # type: ignore[arg-type]

    with monkeypatch.context() as patched:
        patched.setattr(Path, "stat", failing_stat)
        patched.setattr(Path, "unlink", failing_unlink)
        result = containment.clean_stale_files(shakedown)

    # Patch reverted here — .exists() is safe again.
    assert result.removed == (removable,)
    assert result.skipped_fresh == (fresh,)
    assert len(result.failed_stat) == 1
    assert result.failed_stat[0].path == stat_fails
    assert len(result.failed_unlink) == 1
    assert result.failed_unlink[0].path == unlink_fails
    assert result.had_errors is True
    assert "failed_stat=1" in result.report()
    assert "failed_unlink=1" in result.report()
    assert not removable.exists()
    assert fresh.exists()
    assert stat_fails.exists()
    assert unlink_fails.exists()


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

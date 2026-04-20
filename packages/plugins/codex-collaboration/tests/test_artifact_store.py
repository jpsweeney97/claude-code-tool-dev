"""Tests for ArtifactStore — deterministic inspection artifact materialization."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from server.artifact_store import ArtifactStore
from server.models import DelegationJob


def _init_repo(repo_path: Path) -> str:
    """Create a real git repo with an initial commit. Returns the base commit SHA."""
    subprocess.run(["git", "init", str(repo_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.email", "test@test.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.name", "Test"],
        check=True,
        capture_output=True,
    )
    readme = repo_path / "README.md"
    readme.write_text("# Initial\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo_path), "add", "."],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_path), "commit", "-m", "init"],
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _make_job(
    *,
    worktree_path: str,
    base_commit: str,
    status: str = "completed",
    promotion_state: str | None = "pending",
    job_id: str = "job-test-1",
) -> DelegationJob:
    return DelegationJob(
        job_id=job_id,
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit=base_commit,
        worktree_path=worktree_path,
        promotion_state=promotion_state,
        status=status,
    )


def test_materialize_completed_snapshot_writes_canonical_files_and_hash(
    tmp_path: Path,
) -> None:
    """Materializing a completed job writes 3 canonical files and computes hash."""
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)

    # Modify README.md
    (repo / "README.md").write_text("# Modified\n", encoding="utf-8")
    # Add new_file.py
    (repo / "new_file.py").write_text("print('hello')\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", "new_file.py"],
        check=True,
        capture_output=True,
    )
    # Write test results in .codex-collaboration/
    cc_dir = repo / ".codex-collaboration"
    cc_dir.mkdir()
    (cc_dir / "test-results.json").write_text(
        json.dumps({"schema_version": 1, "status": "passed", "commands": ["pytest"], "summary": "ok"}),
        encoding="utf-8",
    )

    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T00:00:00Z")
    job = _make_job(worktree_path=str(repo), base_commit=base_commit)

    snapshot = store.materialize_snapshot(job=job)

    # Hash is computed for completed jobs
    assert snapshot.artifact_hash is not None

    # Canonical artifact names
    artifact_names = tuple(Path(p).name for p in snapshot.artifact_paths)
    assert artifact_names == ("full.diff", "changed-files.json", "test-results.json")

    # Changed files excludes .codex-collaboration/test-results.json
    assert snapshot.changed_files == ("README.md", "new_file.py")

    # full.diff does NOT contain .codex-collaboration/test-results.json
    full_diff = Path(snapshot.artifact_paths[0]).read_text(encoding="utf-8")
    assert ".codex-collaboration/test-results.json" not in full_diff


def test_materialize_completed_snapshot_hash_matches_spec_recipe(
    tmp_path: Path,
) -> None:
    """Hash matches the deterministic spec recipe: sha256(path + NUL + bytes) per artifact."""
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)

    (repo / "README.md").write_text("# Changed\n", encoding="utf-8")
    (repo / "new_file.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", "new_file.py"],
        check=True,
        capture_output=True,
    )
    cc_dir = repo / ".codex-collaboration"
    cc_dir.mkdir()
    (cc_dir / "test-results.json").write_text(
        json.dumps({"schema_version": 1, "status": "passed", "commands": ["pytest"], "summary": "all pass"}),
        encoding="utf-8",
    )

    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T01:00:00Z")
    job = _make_job(worktree_path=str(repo), base_commit=base_commit)

    snapshot = store.materialize_snapshot(job=job)

    # Independently compute expected hash using spec-required sorted order.
    # artifact_paths is in insertion order; the hash must sort by relative path.
    inspection_dir = plugin_data / "runtimes" / "delegation" / job.job_id / "inspection"
    sorted_paths = sorted(
        snapshot.artifact_paths,
        key=lambda p: Path(p).relative_to(inspection_dir).as_posix(),
    )
    expected_sha = hashlib.sha256()
    for artifact_path_str in sorted_paths:
        path = Path(artifact_path_str)
        relative = path.relative_to(inspection_dir).as_posix().encode("utf-8")
        expected_sha.update(relative)
        expected_sha.update(b"\0")
        expected_sha.update(path.read_bytes())

    assert snapshot.artifact_hash == expected_sha.hexdigest()


def test_materialize_unknown_snapshot_omits_hash(tmp_path: Path) -> None:
    """Unknown-status jobs produce snapshot with artifact_hash=None."""
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)

    (repo / "README.md").write_text("# Unknown run\n", encoding="utf-8")

    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T02:00:00Z")
    job = _make_job(
        worktree_path=str(repo),
        base_commit=base_commit,
        status="unknown",
        promotion_state=None,
    )

    snapshot = store.materialize_snapshot(job=job)

    assert snapshot.artifact_hash is None
    assert snapshot.changed_files == ("README.md",)


def test_missing_test_results_file_produces_deterministic_stub(
    tmp_path: Path,
) -> None:
    """When .codex-collaboration/test-results.json is missing, a not_recorded stub is produced."""
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)

    (repo / "README.md").write_text("# No test results\n", encoding="utf-8")

    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T03:00:00Z")
    job = _make_job(worktree_path=str(repo), base_commit=base_commit)

    snapshot = store.materialize_snapshot(job=job)

    # Read persisted test-results.json artifact
    test_results_path = Path(snapshot.artifact_paths[2])
    record = json.loads(test_results_path.read_text(encoding="utf-8"))

    assert record["status"] == "not_recorded"
    assert record["source_path"] == ".codex-collaboration/test-results.json"


def test_load_snapshot_returns_none_for_corrupt_json(tmp_path: Path) -> None:
    """Truncated or corrupt snapshot.json must not prevent rematerialization."""
    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T04:00:00Z")
    job = DelegationJob(
        job_id="job-corrupt",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="completed",
    )
    # Write a truncated snapshot.json
    inspection_dir = plugin_data / "runtimes" / "delegation" / "job-corrupt" / "inspection"
    inspection_dir.mkdir(parents=True)
    (inspection_dir / "snapshot.json").write_text('{"artifact_hash": "abc', encoding="utf-8")

    result = store.load_snapshot(job=job)
    assert result is None

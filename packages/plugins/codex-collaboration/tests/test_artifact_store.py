"""Tests for ArtifactStore — deterministic inspection artifact materialization."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from server.artifact_store import ArtifactStore, CanonicalArtifactBundle
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
        json.dumps(
            {
                "schema_version": 1,
                "status": "passed",
                "commands": ["pytest"],
                "summary": "ok",
            }
        ),
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
        json.dumps(
            {
                "schema_version": 1,
                "status": "passed",
                "commands": ["pytest"],
                "summary": "all pass",
            }
        ),
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
    inspection_dir = (
        plugin_data / "runtimes" / "delegation" / "job-corrupt" / "inspection"
    )
    inspection_dir.mkdir(parents=True)
    (inspection_dir / "snapshot.json").write_text(
        '{"artifact_hash": "abc', encoding="utf-8"
    )

    result = store.load_snapshot(job=job)
    assert result is None


def test_reconstruct_from_artifacts_heals_corrupt_cache(tmp_path: Path) -> None:
    """Reconstruction reads the persisted manifest and rewrites snapshot.json."""
    repo_root = tmp_path / "repo"
    base_commit = _init_repo(repo_root)
    (repo_root / "README.md").write_text("changed\n", encoding="utf-8")

    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T05:00:00Z")
    job = DelegationJob(
        job_id="job-heal",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit=base_commit,
        worktree_path=str(repo_root),
        promotion_state="pending",
        status="completed",
    )

    # First materialize to create the artifact files.
    original = store.materialize_snapshot(job=job)

    # Corrupt snapshot.json.
    inspection_dir = plugin_data / "runtimes" / "delegation" / "job-heal" / "inspection"
    (inspection_dir / "snapshot.json").write_text("{truncated", encoding="utf-8")

    # Confirm load_snapshot fails.
    assert store.load_snapshot(job=job) is None

    # Reconstruct from persisted artifacts and store data.
    job_with_artifacts = DelegationJob(
        job_id="job-heal",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit=base_commit,
        worktree_path=str(repo_root),
        promotion_state="pending",
        status="completed",
        artifact_paths=original.artifact_paths,
        artifact_hash=original.artifact_hash,
    )
    reconstructed = store.reconstruct_from_artifacts(job=job_with_artifacts)
    assert reconstructed is not None
    assert reconstructed.artifact_hash == original.artifact_hash
    assert reconstructed.artifact_paths == original.artifact_paths
    assert reconstructed.changed_files == original.changed_files

    # snapshot.json should be healed — load_snapshot works again.
    healed = store.load_snapshot(job=job_with_artifacts)
    assert healed is not None
    assert healed.artifact_hash == original.artifact_hash


def test_reconstruct_returns_none_when_artifact_file_missing(tmp_path: Path) -> None:
    """If any canonical artifact is deleted, reconstruction must fail."""
    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T06:00:00Z")
    job = DelegationJob(
        job_id="job-missing-file",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="completed",
        artifact_paths=(
            "/tmp/nonexistent/full.diff",
            "/tmp/nonexistent/changed-files.json",
            "/tmp/nonexistent/test-results.json",
        ),
        artifact_hash="abc123",
    )
    result = store.reconstruct_from_artifacts(job=job)
    assert result is None


def test_malformed_test_results_produces_stub(tmp_path: Path) -> None:
    """Truncated .codex-collaboration/test-results.json must not crash materialization."""
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)

    (repo / "README.md").write_text("# Changed\n", encoding="utf-8")
    cc_dir = repo / ".codex-collaboration"
    cc_dir.mkdir()
    (cc_dir / "test-results.json").write_text('{"truncated', encoding="utf-8")

    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T08:00:00Z")
    job = _make_job(worktree_path=str(repo), base_commit=base_commit)

    snapshot = store.materialize_snapshot(job=job)

    # Materialization succeeds — no JSONDecodeError propagation
    assert snapshot.artifact_hash is not None
    test_results_path = Path(snapshot.artifact_paths[2])
    record = json.loads(test_results_path.read_text(encoding="utf-8"))
    assert record["status"] == "malformed"
    assert record["source_path"] == ".codex-collaboration/test-results.json"


def test_reconstruct_handles_malformed_manifest(tmp_path: Path) -> None:
    """Malformed changed-files.json (valid JSON, wrong shape) must not crash."""
    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T07:00:00Z")
    inspection_dir = (
        plugin_data / "runtimes" / "delegation" / "job-bad-manifest" / "inspection"
    )
    inspection_dir.mkdir(parents=True)

    # Write artifact files — manifest is valid JSON but wrong shape (list, not dict)
    (inspection_dir / "full.diff").write_text("diff content\n", encoding="utf-8")
    (inspection_dir / "changed-files.json").write_text(
        '["not", "a", "dict"]', encoding="utf-8"
    )
    (inspection_dir / "test-results.json").write_text(
        '{"status": "passed"}', encoding="utf-8"
    )

    job = DelegationJob(
        job_id="job-bad-manifest",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="completed",
        artifact_paths=(
            str(inspection_dir / "full.diff"),
            str(inspection_dir / "changed-files.json"),
            str(inspection_dir / "test-results.json"),
        ),
        artifact_hash="abc123",
    )
    result = store.reconstruct_from_artifacts(job=job)
    assert result is not None
    assert result.artifact_hash == "abc123"
    assert result.changed_files == ()  # Gracefully empty, not crashed


# ---------------------------------------------------------------------------
# Tests for generate_canonical_artifacts() and CanonicalArtifactBundle
# ---------------------------------------------------------------------------


def test_generate_canonical_artifacts_returns_bundle_with_hash(tmp_path: Path) -> None:
    """generate_canonical_artifacts returns a CanonicalArtifactBundle with hash and metadata."""
    store = ArtifactStore(
        tmp_path / "plugin-data", timestamp_factory=lambda: "2026-04-20T00:00:00Z"
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)
    (repo / "README.md").write_text("# Changed\n", encoding="utf-8")

    bundle = store.generate_canonical_artifacts(
        job=_make_job(worktree_path=str(repo), base_commit=base_commit),
        output_dir=tmp_path / "bundle",
    )

    assert isinstance(bundle, CanonicalArtifactBundle)
    assert bundle.artifact_hash is not None
    assert bundle.changed_files == ("README.md",)
    assert bundle.full_diff_path.name == "full.diff"


def test_generate_canonical_artifacts_creates_output_dir(tmp_path: Path) -> None:
    """generate_canonical_artifacts creates output_dir if it does not exist."""
    store = ArtifactStore(
        tmp_path / "plugin-data", timestamp_factory=lambda: "2026-04-20T00:00:00Z"
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)
    (repo / "README.md").write_text("# Changed\n", encoding="utf-8")

    output_dir = tmp_path / "nested" / "does" / "not" / "exist"
    assert not output_dir.exists()

    bundle = store.generate_canonical_artifacts(
        job=_make_job(worktree_path=str(repo), base_commit=base_commit),
        output_dir=output_dir,
    )

    assert output_dir.exists()
    assert bundle.full_diff_path.parent == output_dir


def test_generate_canonical_artifacts_omits_hash_for_non_completed_job(
    tmp_path: Path,
) -> None:
    """generate_canonical_artifacts returns artifact_hash=None for non-completed jobs."""
    store = ArtifactStore(
        tmp_path / "plugin-data", timestamp_factory=lambda: "2026-04-20T00:00:00Z"
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)
    (repo / "README.md").write_text("# Changed\n", encoding="utf-8")

    bundle = store.generate_canonical_artifacts(
        job=_make_job(
            worktree_path=str(repo),
            base_commit=base_commit,
            status="unknown",
            promotion_state=None,
        ),
        output_dir=tmp_path / "bundle",
    )

    assert bundle.artifact_hash is None
    assert bundle.changed_files == ("README.md",)


def test_generate_canonical_artifacts_parity_with_materialize_snapshot(
    tmp_path: Path,
) -> None:
    """Artifacts produced by generate_canonical_artifacts to a temp dir have the same hash as materialize_snapshot."""
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)
    (repo / "README.md").write_text("# Parity check\n", encoding="utf-8")

    plugin_data = tmp_path / "plugin-data"
    store = ArtifactStore(plugin_data, timestamp_factory=lambda: "2026-04-20T00:00:00Z")
    job = _make_job(worktree_path=str(repo), base_commit=base_commit)

    snapshot = store.materialize_snapshot(job=job)
    bundle = store.generate_canonical_artifacts(
        job=job,
        output_dir=tmp_path / "temp-bundle",
    )

    # Both paths must produce the same artifact hash, even though artifacts
    # live in different directories.
    assert bundle.artifact_hash is not None
    assert bundle.artifact_hash == snapshot.artifact_hash

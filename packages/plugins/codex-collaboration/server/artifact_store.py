"""Deterministic inspection artifact materialization.

Produces a canonical set of artifacts from the worktree state at poll time:
- full.diff — unified diff excluding internal metadata
- changed-files.json — sorted file list
- test-results.json — agent-persisted or deterministic stub

The artifact hash (sha256) is computed only for completed jobs, providing
a tamper-evident seal for promotion decisions.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .models import ArtifactInspectionSnapshot, DelegationJob

TEST_RESULTS_RECORD_RELATIVE_PATH = ".codex-collaboration/test-results.json"


@dataclass(frozen=True)
class CanonicalArtifactBundle:
    """Output of generate_canonical_artifacts — written files and their computed hash."""

    artifact_paths: tuple[str, ...]
    artifact_hash: str | None
    changed_files: tuple[str, ...]
    full_diff_path: Path
    changed_files_path: Path
    test_results_path: Path


class ArtifactStore:
    """Materializes and loads inspection snapshots for delegation jobs."""

    def __init__(
        self,
        plugin_data_path: Path,
        *,
        timestamp_factory: Callable[[], str],
    ) -> None:
        self._plugin_data_path = plugin_data_path
        self._timestamp_factory = timestamp_factory

    def generate_canonical_artifacts(
        self,
        *,
        job: DelegationJob,
        output_dir: Path,
    ) -> CanonicalArtifactBundle:
        """Write canonical artifact files to output_dir and return a bundle.

        The artifact hash is computed when job.status == "completed"; otherwise
        artifact_hash is None. output_dir is created if it does not exist.

        This method is the single source of truth for artifact generation and is
        called by both materialize_snapshot (inspection dir) and promote logic
        (a temp dir for hash comparison).
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        changed_files = self._changed_files(job)
        full_diff_path = output_dir / "full.diff"
        changed_files_path = output_dir / "changed-files.json"
        test_results_path = output_dir / "test-results.json"

        full_diff_path.write_text(self._full_diff(job, changed_files), encoding="utf-8")
        changed_files_path.write_text(
            json.dumps({"changed_files": list(changed_files)}, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        test_results_path.write_text(
            json.dumps(
                self._test_results_record(Path(job.worktree_path)),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        artifact_paths = (
            str(full_diff_path),
            str(changed_files_path),
            str(test_results_path),
        )
        artifact_hash = (
            self._review_hash(output_dir, artifact_paths)
            if job.status == "completed"
            else None
        )

        return CanonicalArtifactBundle(
            artifact_paths=artifact_paths,
            artifact_hash=artifact_hash,
            changed_files=changed_files,
            full_diff_path=full_diff_path,
            changed_files_path=changed_files_path,
            test_results_path=test_results_path,
        )

    def materialize_snapshot(self, *, job: DelegationJob) -> ArtifactInspectionSnapshot:
        """Produce canonical artifacts and return a frozen snapshot."""
        inspection_dir = self._inspection_dir(job.job_id)
        snapshot_path = inspection_dir / "snapshot.json"

        bundle = self.generate_canonical_artifacts(job=job, output_dir=inspection_dir)

        reviewed_at = self._timestamp_factory()

        snapshot = ArtifactInspectionSnapshot(
            artifact_hash=bundle.artifact_hash,
            artifact_paths=bundle.artifact_paths,
            changed_files=bundle.changed_files,
            reviewed_at=reviewed_at,
        )
        snapshot_path.write_text(
            json.dumps(
                {
                    "artifact_hash": snapshot.artifact_hash,
                    "artifact_paths": list(snapshot.artifact_paths),
                    "changed_files": list(snapshot.changed_files),
                    "reviewed_at": snapshot.reviewed_at,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return snapshot

    def reconstruct_from_artifacts(
        self, *, job: DelegationJob
    ) -> ArtifactInspectionSnapshot | None:
        """Reconstruct a snapshot from persisted artifact files and store data.

        Used when ``snapshot.json`` is corrupt but the job store still holds
        the authoritative ``artifact_hash`` and ``artifact_paths``. The
        artifact files under the inspection directory are immutable once
        written, so reading them is safe even if the worktree has been
        modified. Rewrites ``snapshot.json`` to heal the cache.

        Returns None if artifact_paths is empty or any artifact file is missing.
        """
        if not job.artifact_paths:
            return None
        # All canonical artifact files must exist — if any are missing,
        # the artifact set is corrupted beyond cache-level recovery.
        for path_str in job.artifact_paths:
            if not Path(path_str).exists():
                return None
        changed_files: tuple[str, ...] = ()
        for path_str in job.artifact_paths:
            path = Path(path_str)
            if path.name == "changed-files.json":
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(payload, dict):
                        changed_files = tuple(payload.get("changed_files", []))
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
                break
        reviewed_at = self._timestamp_factory()
        snapshot = ArtifactInspectionSnapshot(
            artifact_hash=job.artifact_hash,
            artifact_paths=job.artifact_paths,
            changed_files=changed_files,
            reviewed_at=reviewed_at,
        )
        # Heal the cache so subsequent polls use the fast path.
        snapshot_path = self._inspection_dir(job.job_id) / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "artifact_hash": snapshot.artifact_hash,
                    "artifact_paths": list(snapshot.artifact_paths),
                    "changed_files": list(snapshot.changed_files),
                    "reviewed_at": snapshot.reviewed_at,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return snapshot

    def load_snapshot(self, *, job: DelegationJob) -> ArtifactInspectionSnapshot | None:
        """Load a previously materialized snapshot from disk.

        Returns None if the snapshot file is missing or corrupt, so the
        caller falls through to rematerialization.
        """
        snapshot_path = self._inspection_dir(job.job_id) / "snapshot.json"
        if not snapshot_path.exists():
            return None
        try:
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            return ArtifactInspectionSnapshot(
                artifact_hash=payload["artifact_hash"],
                artifact_paths=tuple(payload["artifact_paths"]),
                changed_files=tuple(payload["changed_files"]),
                reviewed_at=payload["reviewed_at"],
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def _inspection_dir(self, job_id: str) -> Path:
        return (
            self._plugin_data_path / "runtimes" / "delegation" / job_id / "inspection"
        )

    def _changed_files(self, job: DelegationJob) -> tuple[str, ...]:
        tracked = subprocess.run(
            [
                "git",
                "-C",
                job.worktree_path,
                "diff",
                "--name-only",
                job.base_commit,
                "--",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        untracked = subprocess.run(
            [
                "git",
                "-C",
                job.worktree_path,
                "ls-files",
                "--others",
                "--exclude-standard",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        return tuple(
            sorted(
                {
                    path
                    for path in tracked + untracked
                    if path and path != TEST_RESULTS_RECORD_RELATIVE_PATH
                }
            )
        )

    def _full_diff(self, job: DelegationJob, changed_files: tuple[str, ...]) -> str:
        tracked_diff = subprocess.run(
            [
                "git",
                "-C",
                job.worktree_path,
                "diff",
                "--binary",
                "--no-color",
                job.base_commit,
                "--",
                ".",
                f":!{TEST_RESULTS_RECORD_RELATIVE_PATH}",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        sections = [tracked_diff.rstrip()]
        worktree = Path(job.worktree_path)
        tracked_set = set(
            subprocess.run(
                [
                    "git",
                    "-C",
                    job.worktree_path,
                    "diff",
                    "--name-only",
                    job.base_commit,
                    "--",
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
        for relative_path in changed_files:
            if relative_path in tracked_set:
                continue
            file_path = worktree / relative_path
            extra = subprocess.run(
                [
                    "git",
                    "diff",
                    "--no-index",
                    "--binary",
                    "--no-color",
                    "--",
                    "/dev/null",
                    str(file_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            ).stdout
            if extra:
                sections.append(extra.rstrip())
        return "\n\n".join(section for section in sections if section) + "\n"

    def _test_results_record(self, worktree_path: Path) -> dict[str, Any]:
        record_path = worktree_path / TEST_RESULTS_RECORD_RELATIVE_PATH
        if not record_path.exists():
            return {
                "schema_version": 1,
                "status": "not_recorded",
                "commands": [],
                "summary": "Execution agent did not persist test results.",
                "source_path": TEST_RESULTS_RECORD_RELATIVE_PATH,
            }
        try:
            return json.loads(record_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError, OSError):
            return {
                "schema_version": 1,
                "status": "malformed",
                "commands": [],
                "summary": "Execution agent persisted test results but the file is malformed or unreadable.",
                "source_path": TEST_RESULTS_RECORD_RELATIVE_PATH,
            }

    def _review_hash(
        self, inspection_dir: Path, artifact_paths: tuple[str, ...]
    ) -> str:
        sha = hashlib.sha256()
        sorted_paths = sorted(
            artifact_paths, key=lambda p: Path(p).relative_to(inspection_dir).as_posix()
        )
        for artifact_path in sorted_paths:
            path = Path(artifact_path)
            relative_path = path.relative_to(inspection_dir).as_posix().encode("utf-8")
            sha.update(relative_path)
            sha.update(b"\0")
            sha.update(path.read_bytes())
        return sha.hexdigest()

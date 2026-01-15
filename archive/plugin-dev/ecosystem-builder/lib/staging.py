"""Staging management for ecosystem-builder artifacts."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


@dataclass
class StagedArtifact:
    """A staged artifact awaiting review."""

    name: str
    artifact_type: Literal["skill", "improvement", "composition", "plugin"]
    path: Path
    run_id: str
    gap_id: str
    staged_at: str


class StagingManager:
    """Manages staged artifacts awaiting review."""

    def __init__(
        self,
        staging_dir: Path | None = None,
        production_dir: Path | None = None,
        rejected_dir: Path | None = None,
    ) -> None:
        base = Path.home() / ".claude" / "ecosystem-builder"

        self.staging_dir = staging_dir or (base / "staging")
        self.production_dir = production_dir or (Path.home() / ".claude" / "skills")
        self.rejected_dir = rejected_dir or (base / "rejected")

        # Ensure directories exist
        (self.staging_dir / "skills").mkdir(parents=True, exist_ok=True)
        (self.staging_dir / "improvements").mkdir(parents=True, exist_ok=True)
        (self.staging_dir / "compositions").mkdir(parents=True, exist_ok=True)
        (self.staging_dir / "plugins").mkdir(parents=True, exist_ok=True)

    def stage_skill(
        self,
        name: str,
        content: str,
        run_id: str,
        gap_id: str,
    ) -> StagedArtifact:
        """Stage a new skill for review."""
        skill_dir = self.staging_dir / "skills" / name
        skill_file = skill_dir / "SKILL.md"
        metadata_file = skill_dir / ".metadata.json"

        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "name": name,
            "artifact_type": "skill",
            "run_id": run_id,
            "gap_id": gap_id,
            "staged_at": now,
        }

        try:
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Write skill content atomically
            temp_skill = skill_file.with_suffix(".tmp")
            temp_skill.write_text(content)
            temp_skill.replace(skill_file)

            # Write metadata atomically
            temp_meta = metadata_file.with_suffix(".tmp")
            temp_meta.write_text(json.dumps(metadata, indent=2))
            temp_meta.replace(metadata_file)
        except OSError as e:
            raise RuntimeError(f"Failed to stage skill '{name}': {e}") from e

        return StagedArtifact(
            name=name,
            artifact_type="skill",
            path=skill_dir,
            run_id=run_id,
            gap_id=gap_id,
            staged_at=now,
        )

    def list_staged(self, artifact_type: str | None = None) -> list[StagedArtifact]:
        """List all staged artifacts, optionally filtered by type."""
        artifacts = []

        types_to_check = [artifact_type] if artifact_type else ["skills", "improvements", "compositions", "plugins"]

        for type_name in types_to_check:
            type_dir = self.staging_dir / type_name
            if not type_dir.exists():
                continue

            for artifact_dir in type_dir.iterdir():
                if not artifact_dir.is_dir():
                    continue

                metadata_file = artifact_dir / ".metadata.json"
                if not metadata_file.exists():
                    continue

                try:
                    metadata = json.loads(metadata_file.read_text())
                except (OSError, json.JSONDecodeError) as e:
                    logging.warning(f"Skipping artifact with corrupt metadata at {artifact_dir}: {e}")
                    continue

                try:
                    artifacts.append(StagedArtifact(
                        name=metadata["name"],
                        artifact_type=metadata["artifact_type"],
                        path=artifact_dir,
                        run_id=metadata["run_id"],
                        gap_id=metadata["gap_id"],
                        staged_at=metadata["staged_at"],
                    ))
                except KeyError as e:
                    logging.warning(f"Skipping artifact with incomplete metadata at {artifact_dir}: missing {e}")
                    continue

        return artifacts

    def accept(self, name: str) -> Path:
        """Accept a staged artifact, moving it to production."""
        artifact = self._find_staged(name)
        if artifact is None:
            raise FileNotFoundError(f"Staged artifact not found: {name}")

        # Determine production path based on type
        if artifact.artifact_type == "skill":
            prod_path = self.production_dir / name
        else:
            raise NotImplementedError(f"Accept not implemented for {artifact.artifact_type}")

        try:
            # Move to production with atomic copy
            prod_path.mkdir(parents=True, exist_ok=True)
            for item in artifact.path.iterdir():
                if item.name == ".metadata.json":
                    continue  # Don't copy metadata to production
                dest = prod_path / item.name
                temp_dest = dest.with_suffix(dest.suffix + ".tmp")
                shutil.copy2(item, temp_dest)
                temp_dest.replace(dest)

            # Remove from staging
            shutil.rmtree(artifact.path)
        except OSError as e:
            raise RuntimeError(f"Failed to accept artifact '{name}': {e}") from e

        return prod_path

    def reject(self, name: str, reason: str = "") -> Path:
        """Reject a staged artifact, moving it to rejected directory."""
        artifact = self._find_staged(name)
        if artifact is None:
            raise FileNotFoundError(f"Staged artifact not found: {name}")

        try:
            # Move to rejected
            rejected_path = self.rejected_dir / artifact.run_id / name
            rejected_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(artifact.path), str(rejected_path))

            # Add rejection reason to metadata atomically
            if reason:
                metadata_file = rejected_path / ".metadata.json"
                metadata = json.loads(metadata_file.read_text())
                metadata["rejection_reason"] = reason
                metadata["rejected_at"] = datetime.now(timezone.utc).isoformat()
                temp_meta = metadata_file.with_suffix(".tmp")
                temp_meta.write_text(json.dumps(metadata, indent=2))
                temp_meta.replace(metadata_file)
        except OSError as e:
            raise RuntimeError(f"Failed to reject artifact '{name}': {e}") from e

        return rejected_path

    def _find_staged(self, name: str) -> StagedArtifact | None:
        """Find a staged artifact by name."""
        for artifact in self.list_staged():
            if artifact.name == name:
                return artifact
        return None

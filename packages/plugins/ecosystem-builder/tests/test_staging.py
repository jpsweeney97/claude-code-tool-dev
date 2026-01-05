"""Tests for staging management."""

import json
from pathlib import Path

import pytest

from lib.staging import StagingManager, StagedArtifact


class TestStagingManager:
    """Tests for StagingManager."""

    def test_stage_skill_creates_directory(self, tmp_path: Path) -> None:
        """Staging a skill should create the skill directory."""
        manager = StagingManager(staging_dir=tmp_path)

        artifact = manager.stage_skill(
            name="my-skill",
            content="# My Skill\n\nContent here.",
            run_id="run-2026-01-01-abc123",
            gap_id="gap-001",
        )

        skill_dir = tmp_path / "skills" / "my-skill"
        assert skill_dir.exists()
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / ".metadata.json").exists()

    def test_list_staged_returns_all(self, tmp_path: Path) -> None:
        """Listing should return all staged artifacts."""
        manager = StagingManager(staging_dir=tmp_path)

        manager.stage_skill("skill-1", "content", "run-1", "gap-1")
        manager.stage_skill("skill-2", "content", "run-1", "gap-2")

        staged = manager.list_staged()
        assert len(staged) == 2
        names = {s.name for s in staged}
        assert names == {"skill-1", "skill-2"}

    def test_accept_moves_to_production(self, tmp_path: Path) -> None:
        """Accepting should move artifact to production path."""
        staging = tmp_path / "staging"
        production = tmp_path / "production"
        manager = StagingManager(staging_dir=staging, production_dir=production)

        artifact = manager.stage_skill("my-skill", "content", "run-1", "gap-1")
        manager.accept(artifact.name)

        # Should be gone from staging
        assert not (staging / "skills" / "my-skill").exists()
        # Should exist in production
        assert (production / "my-skill" / "SKILL.md").exists()

    def test_reject_moves_to_rejected(self, tmp_path: Path) -> None:
        """Rejecting should move artifact to rejected directory."""
        staging = tmp_path / "staging"
        rejected = tmp_path / "rejected"
        manager = StagingManager(staging_dir=staging, rejected_dir=rejected)

        artifact = manager.stage_skill("my-skill", "content", "run-1", "gap-1")
        manager.reject(artifact.name, reason="Not useful")

        # Should be gone from staging
        assert not (staging / "skills" / "my-skill").exists()
        # Should exist in rejected
        assert (rejected / "run-1" / "my-skill").exists()

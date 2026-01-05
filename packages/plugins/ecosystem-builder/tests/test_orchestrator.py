"""Tests for orchestrator."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from lib.orchestrator import Orchestrator
from lib.state import StateManager


class TestOrchestrator:
    """Tests for Orchestrator."""

    def test_run_stops_when_budget_exhausted(self, tmp_path: Path) -> None:
        """Orchestrator should stop when artifact budget is exhausted."""
        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=2)

        # Mock the build function to always succeed
        builds = []
        def mock_build(gap):
            builds.append(gap)
            return {"name": f"skill-{len(builds)}", "content": "content"}

        # Mock analysis to return 5 gaps (more than budget)
        gaps = [{"gap_id": f"gap-{i}"} for i in range(5)]

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
        )
        orchestrator._analyze = Mock(return_value=gaps)
        orchestrator._build = mock_build
        orchestrator._validate = Mock(return_value=True)

        orchestrator.run()

        # Should have built exactly 2 (the budget limit)
        assert len(builds) == 2
        assert manifest.status == "complete"
        assert manifest.budget.artifacts.used == 2

    def test_run_logs_events(self, tmp_path: Path) -> None:
        """Orchestrator should log events for each phase."""
        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=1)

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
        )
        orchestrator._analyze = Mock(return_value=[{"gap_id": "gap-1"}])
        orchestrator._build = Mock(return_value={"name": "skill-1", "content": "c"})
        orchestrator._validate = Mock(return_value=True)

        orchestrator.run()

        # Check log file has events
        log_file = manifest.run_dir / "log.jsonl"
        log_content = log_file.read_text()
        assert "run_started" in log_content
        assert "gap_analyzed" in log_content
        assert "artifact_built" in log_content
        assert "run_complete" in log_content


class TestOrchestratorAnalyze:
    """Tests for orchestrator analyze phase."""

    def test_analyze_uses_agent_panel(self, tmp_path: Path) -> None:
        """_analyze should use AgentPanel and return gaps."""
        # Setup ecosystem
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n# Test")

        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=5)

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
            user_skills_dir=skills_dir,
            plugins_dir=plugins_dir,
        )

        gaps = orchestrator._analyze()

        # Should return gaps from agent panel
        assert isinstance(gaps, list)
        # All gaps should be dicts with required fields
        for gap in gaps:
            assert "gap_id" in gap
            assert "gap_type" in gap
            assert "title" in gap

    def test_analyze_saves_opportunities(self, tmp_path: Path) -> None:
        """_analyze should save opportunities to opportunities.json."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=5)

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )

        orchestrator._analyze()

        # Check opportunities.json was updated
        opportunities_file = manifest.run_dir / "opportunities.json"
        import json
        opportunities = json.loads(opportunities_file.read_text())
        assert isinstance(opportunities, list)


class TestOrchestratorBuild:
    """Tests for orchestrator build phase."""

    def test_build_uses_skill_builder(self, tmp_path: Path) -> None:
        """_build should use SkillBuilder and return artifact dict."""
        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=5)

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
            user_skills_dir=tmp_path / "skills",
            plugins_dir=tmp_path / "plugins",
        )

        gap = {
            "gap_id": "gap-1",
            "gap_type": "missing_skill",
            "title": "testing",
            "description": "Add testing skill",
            "source_agent": "catalog",
            "confidence": 0.9,
            "priority": 2,
        }

        artifact = orchestrator._build(gap)

        assert artifact is not None
        assert "name" in artifact
        assert "content" in artifact
        assert artifact["name"] == "testing"

    def test_build_returns_none_on_failure(self, tmp_path: Path) -> None:
        """_build should return None when builder fails."""
        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=5)

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
        )

        # Complex gap triggers subagent (which returns error)
        gap = {
            "gap_id": "gap-1",
            "gap_type": "workflow_hole",
            "title": "complex-workflow",
            "description": "Complex CI/CD workflow",
            "source_agent": "workflow",
            "confidence": 0.5,
            "priority": 1,
        }

        artifact = orchestrator._build(gap)

        # Subagent not implemented, should return None
        assert artifact is None


class TestOrchestratorValidate:
    """Tests for orchestrator validate phase."""

    def test_validate_uses_validation_panel(self, tmp_path: Path) -> None:
        """_validate should use ValidationPanel."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=5)

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )

        artifact = {
            "name": "test-skill",
            "content": """---
name: test-skill
description: Use when working with "testing" patterns
---

# Test Skill

## Overview

This skill provides testing guidance with sufficient content length.

## When to Use

- Testing patterns needed
- Unit test guidance

## Process

Follow testing best practices and patterns for quality code.
""",
        }

        passed = orchestrator._validate(artifact)

        assert passed is True

    def test_validate_rejects_invalid_artifact(self, tmp_path: Path) -> None:
        """_validate should reject artifacts that fail checks."""
        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=5)

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
        )

        artifact = {
            "name": "bad-skill",
            "content": "No frontmatter here",  # Invalid
        }

        passed = orchestrator._validate(artifact)

        assert passed is False


class TestOrchestratorSubagent:
    """Tests for orchestrator subagent integration."""

    def test_orchestrator_passes_callable_to_builder(self, tmp_path: Path) -> None:
        """Orchestrator wires subagent callable to SkillBuilder."""
        mock_skill = """---
name: ci-cd-integration
description: Use when setting up "CI/CD" workflows.
---

# CI/CD Integration

## Overview

Skill for CI/CD workflows.

## When to Use

- CI/CD pipeline setup
- Deployment automation

## Process

1. Configure
2. Deploy
"""

        def mock_callable(prompt: str) -> str:
            return mock_skill

        state_manager = StateManager(state_dir=tmp_path / "state")
        manifest = state_manager.create_run(artifact_limit=5)

        orchestrator = Orchestrator(
            manifest=manifest,
            staging_dir=tmp_path / "staging",
            subagent_callable=mock_callable,
        )

        # Complex gap should use subagent
        gap = {
            "gap_id": "gap-1",
            "gap_type": "workflow_hole",
            "title": "ci-cd-integration",
            "description": "Complex CI/CD workflow",
            "source_agent": "workflow",
            "confidence": 0.5,
            "priority": 1,
        }

        artifact = orchestrator._build(gap)

        assert artifact is not None
        assert artifact["method"] == "subagent"
        assert "ci-cd-integration" in artifact["content"]

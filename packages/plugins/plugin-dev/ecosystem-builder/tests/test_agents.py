"""Tests for agent panel."""

from pathlib import Path

import pytest

from lib.agents import AgentPanel, AgentResult
from lib.state import Gap, GapType


class TestAgentResult:
    """Tests for AgentResult."""

    def test_agent_result_creation(self) -> None:
        """AgentResult should store gaps and metadata."""
        gaps = [
            Gap(
                gap_id="gap-001",
                gap_type=GapType.MISSING_SKILL,
                title="Test gap",
                description="Description",
                source_agent="catalog",
                confidence=0.8,
                priority=1,
            )
        ]
        result = AgentResult(
            agent_name="catalog",
            gaps=gaps,
            artifacts_scanned=15,
            error=None,
        )
        assert result.agent_name == "catalog"
        assert len(result.gaps) == 1
        assert result.artifacts_scanned == 15
        assert result.success is True

    def test_agent_result_with_error(self) -> None:
        """AgentResult should track errors."""
        result = AgentResult(
            agent_name="catalog",
            gaps=[],
            artifacts_scanned=0,
            error="Failed to scan skills directory",
        )
        assert result.success is False
        assert result.error == "Failed to scan skills directory"


class TestAgentPanel:
    """Tests for AgentPanel."""

    def test_panel_initialization(self, tmp_path: Path) -> None:
        """AgentPanel should initialize with ecosystem paths."""
        panel = AgentPanel(
            user_skills_dir=tmp_path / "skills",
            plugins_dir=tmp_path / "plugins",
        )
        assert panel.user_skills_dir == tmp_path / "skills"
        assert panel.plugins_dir == tmp_path / "plugins"

    def test_panel_run_all_agents_returns_results(self, tmp_path: Path) -> None:
        """run_all_agents should return results from all agents."""
        # Setup minimal skill structure
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\n---\n# Test")

        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        panel = AgentPanel(
            user_skills_dir=skills_dir,
            plugins_dir=plugins_dir,
        )
        results = panel.run_all_agents()

        assert len(results) == 3  # catalog, workflow, quality
        agent_names = {r.agent_name for r in results}
        assert agent_names == {"catalog", "workflow-analyzer", "quality-scorer"}

    def test_panel_merge_gaps_deduplicates(self, tmp_path: Path) -> None:
        """merge_gaps should deduplicate by gap_id."""
        panel = AgentPanel(
            user_skills_dir=tmp_path / "skills",
            plugins_dir=tmp_path / "plugins",
        )

        gap1 = Gap(
            gap_id="gap-001",
            gap_type=GapType.MISSING_SKILL,
            title="Missing skill A",
            description="Desc",
            source_agent="catalog",
            confidence=0.8,
            priority=1,
        )
        gap2 = Gap(
            gap_id="gap-001",  # duplicate
            gap_type=GapType.MISSING_SKILL,
            title="Missing skill A",
            description="Desc",
            source_agent="workflow-analyzer",
            confidence=0.9,
            priority=2,
        )
        gap3 = Gap(
            gap_id="gap-002",
            gap_type=GapType.QUALITY_ISSUE,
            title="Quality issue B",
            description="Desc",
            source_agent="quality-scorer",
            confidence=0.7,
            priority=3,
        )

        results = [
            AgentResult(agent_name="catalog", gaps=[gap1], artifacts_scanned=5),
            AgentResult(
                agent_name="workflow-analyzer", gaps=[gap2], artifacts_scanned=3
            ),
            AgentResult(agent_name="quality-scorer", gaps=[gap3], artifacts_scanned=5),
        ]

        merged = panel.merge_gaps(results)

        assert len(merged) == 2
        # Higher confidence version should be kept
        gap_001 = next(g for g in merged if g.gap_id == "gap-001")
        assert gap_001.confidence == 0.9


class TestCatalogAgent:
    """Tests for catalog agent functionality."""

    def test_catalog_scans_user_skills(self, tmp_path: Path) -> None:
        """Catalog agent should scan user skills directory."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create two skills
        for name in ["skill-a", "skill-b"]:
            skill_dir = skills_dir / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Test\n---\n# {name}"
            )

        panel = AgentPanel(
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )
        result = panel._run_catalog_agent()

        assert result.agent_name == "catalog"
        assert result.artifacts_scanned == 2
        assert result.success is True

    def test_catalog_scans_plugin_skills(self, tmp_path: Path) -> None:
        """Catalog agent should scan plugin skills."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        # Create plugin with skills
        plugin_dir = plugins_dir / "my-plugin"
        plugin_dir.mkdir()
        skills_dir = plugin_dir / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n# My Skill")

        panel = AgentPanel(
            user_skills_dir=tmp_path / "user-skills",
            plugins_dir=plugins_dir,
        )
        result = panel._run_catalog_agent()

        assert result.artifacts_scanned >= 1

    def test_catalog_identifies_missing_common_skills(self, tmp_path: Path) -> None:
        """Catalog agent should flag missing common skill patterns."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Only one skill - should flag others as missing
        skill_dir = skills_dir / "debugging"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: debugging\ndescription: Debug\n---\n# Debug"
        )

        panel = AgentPanel(
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )
        result = panel._run_catalog_agent()

        # Should find gaps for expected but missing patterns
        assert len(result.gaps) > 0
        gap_titles = [g.title.lower() for g in result.gaps]
        # Common patterns that should be suggested
        assert any(
            "test" in t or "refactor" in t or "documentation" in t for t in gap_titles
        )


class TestWorkflowAnalyzerAgent:
    """Tests for workflow analyzer agent."""

    def test_workflow_checks_skill_completeness(self, tmp_path: Path) -> None:
        """Workflow agent should check if skills have complete structure."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create incomplete skill (no examples, no references)
        skill_dir = skills_dir / "incomplete-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: incomplete\n---\n# Incomplete")

        panel = AgentPanel(
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )
        result = panel._run_workflow_agent()

        assert result.agent_name == "workflow-analyzer"
        # Should flag incomplete structure
        assert any(g.gap_type == GapType.INCOMPLETE_ARTIFACT for g in result.gaps)

    def test_workflow_detects_missing_hooks(self, tmp_path: Path) -> None:
        """Workflow agent should detect skills without hook integration."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create skill that could benefit from hooks
        skill_dir = skills_dir / "pre-commit-check"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: pre-commit-check\ndescription: Run before commits\n---\n# Pre-commit"
        )

        panel = AgentPanel(
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )
        result = panel._run_workflow_agent()

        # Should suggest hook integration
        assert any(
            "hook" in g.description.lower() or g.gap_type == GapType.WORKFLOW_HOLE
            for g in result.gaps
        )


class TestQualityScorerAgent:
    """Tests for quality scorer agent."""

    def test_quality_flags_missing_description(self, tmp_path: Path) -> None:
        """Quality agent should flag skills without descriptions."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        skill_dir = skills_dir / "no-desc"
        skill_dir.mkdir()
        # Skill without description field
        (skill_dir / "SKILL.md").write_text("---\nname: no-desc\n---\n# No Description")

        panel = AgentPanel(
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )
        result = panel._run_quality_agent()

        assert result.agent_name == "quality-scorer"
        assert any(
            g.gap_type == GapType.QUALITY_ISSUE and "description" in g.title.lower()
            for g in result.gaps
        )

    def test_quality_flags_short_content(self, tmp_path: Path) -> None:
        """Quality agent should flag skills with minimal content."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        skill_dir = skills_dir / "short-skill"
        skill_dir.mkdir()
        # Very short skill
        (skill_dir / "SKILL.md").write_text("---\nname: short\ndescription: Short\n---\n# S")

        panel = AgentPanel(
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )
        result = panel._run_quality_agent()

        assert any(
            g.gap_type == GapType.QUALITY_ISSUE and "content" in g.description.lower()
            for g in result.gaps
        )

    def test_quality_high_score_for_complete_skill(self, tmp_path: Path) -> None:
        """Quality agent should not flag well-structured skills."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        skill_dir = skills_dir / "complete-skill"
        skill_dir.mkdir()
        (skill_dir / "references").mkdir()
        (skill_dir / "examples").mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: complete\ndescription: A complete skill with examples\n---\n"
            "# Complete Skill\n\n"
            "This is a complete skill with proper documentation.\n\n"
            "## Usage\n\nUse this skill when you need to...\n\n"
            "## Examples\n\nSee the examples directory.\n"
        )

        panel = AgentPanel(
            user_skills_dir=skills_dir,
            plugins_dir=tmp_path / "plugins",
        )
        result = panel._run_quality_agent()

        # Should not flag this skill
        assert not any(
            "complete-skill" in g.title
            for g in result.gaps
        )

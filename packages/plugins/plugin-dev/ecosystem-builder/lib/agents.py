"""Multi-agent panel for ecosystem gap analysis."""

from __future__ import annotations

import logging
import re
import uuid

import yaml

from dataclasses import dataclass
from pathlib import Path

from lib.state import Gap, GapType


@dataclass
class AgentResult:
    """Result from a single agent's analysis."""

    agent_name: str
    gaps: list[Gap]
    artifacts_scanned: int
    error: str | None = None

    @property
    def success(self) -> bool:
        """True if agent completed without error."""
        return self.error is None


@dataclass
class AgentPanel:
    """Coordinates multiple analysis agents."""

    user_skills_dir: Path
    plugins_dir: Path

    def run_all_agents(self) -> list[AgentResult]:
        """Run all agents and collect results."""
        return [
            self._run_catalog_agent(),
            self._run_workflow_agent(),
            self._run_quality_agent(),
        ]

    def merge_gaps(self, results: list[AgentResult]) -> list[Gap]:
        """Merge and deduplicate gaps from all agents."""
        gaps_by_id: dict[str, Gap] = {}

        for result in results:
            for gap in result.gaps:
                if gap.gap_id not in gaps_by_id:
                    gaps_by_id[gap.gap_id] = gap
                elif gap.confidence > gaps_by_id[gap.gap_id].confidence:
                    # Keep higher confidence version
                    gaps_by_id[gap.gap_id] = gap

        # Sort by priority (lower = higher priority)
        return sorted(gaps_by_id.values(), key=lambda g: g.priority)

    def _run_catalog_agent(self) -> AgentResult:
        """Catalog existing artifacts and find missing skills."""
        existing_skills: set[str] = set()
        scanned = 0

        # Scan user skills
        if self.user_skills_dir.exists():
            for skill_dir in self.user_skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    existing_skills.add(skill_dir.name.lower())
                    scanned += 1

        # Scan plugin skills
        if self.plugins_dir.exists():
            for plugin_dir in self.plugins_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                skills_path = plugin_dir / "skills"
                if skills_path.exists():
                    for skill_dir in skills_path.iterdir():
                        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                            existing_skills.add(skill_dir.name.lower())
                            scanned += 1

        # Common skill patterns to check for
        expected_patterns = [
            ("testing", "TDD or testing workflow skill"),
            ("refactoring", "Code refactoring patterns skill"),
            ("documentation", "Documentation generation skill"),
            ("code-review", "Code review workflow skill"),
            ("deployment", "Deployment automation skill"),
        ]

        gaps: list[Gap] = []
        for pattern, description in expected_patterns:
            # Check if any existing skill matches this pattern
            if not any(pattern in skill for skill in existing_skills):
                gaps.append(
                    Gap(
                        gap_id=f"gap-catalog-{uuid.uuid4().hex[:6]}",
                        gap_type=GapType.MISSING_SKILL,
                        title=f"Missing {pattern} skill",
                        description=description,
                        source_agent="catalog",
                        confidence=0.6,
                        priority=2,
                    )
                )

        return AgentResult(
            agent_name="catalog",
            gaps=gaps,
            artifacts_scanned=scanned,
        )

    def _run_workflow_agent(self) -> AgentResult:
        """Analyze workflows for holes."""
        gaps: list[Gap] = []
        scanned = 0

        # Check user skills for completeness
        if self.user_skills_dir.exists():
            for skill_dir in self.user_skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue

                scanned += 1
                skill_name = skill_dir.name

                # Check for references directory
                has_references = (skill_dir / "references").exists()
                # Check for examples directory
                has_examples = (skill_dir / "examples").exists()
                # Check for scripts directory
                has_scripts = (skill_dir / "scripts").exists()

                if not any([has_references, has_examples, has_scripts]):
                    gaps.append(
                        Gap(
                            gap_id=f"gap-workflow-{uuid.uuid4().hex[:6]}",
                            gap_type=GapType.INCOMPLETE_ARTIFACT,
                            title=f"Incomplete structure: {skill_name}",
                            description=f"Skill '{skill_name}' lacks references, examples, or scripts",
                            source_agent="workflow-analyzer",
                            confidence=0.7,
                            priority=3,
                        )
                    )

                # Check for hook-worthy skills
                try:
                    content = skill_md.read_text().lower()
                except (OSError, UnicodeDecodeError) as e:
                    logging.warning(f"Skipping unreadable skill {skill_md}: {e}")
                    continue
                hook_triggers = ["pre-commit", "before commit", "on save", "pre-push"]
                if any(trigger in content for trigger in hook_triggers):
                    # Check if hooks exist in same plugin
                    hooks_file = skill_dir.parent.parent / "hooks" / "hooks.json"
                    if not hooks_file.exists():
                        gaps.append(
                            Gap(
                                gap_id=f"gap-workflow-{uuid.uuid4().hex[:6]}",
                                gap_type=GapType.WORKFLOW_HOLE,
                                title=f"Missing hook for: {skill_name}",
                                description=f"Skill '{skill_name}' mentions hook triggers but no hooks.json exists",
                                source_agent="workflow-analyzer",
                                confidence=0.75,
                                priority=2,
                            )
                        )

        return AgentResult(
            agent_name="workflow-analyzer",
            gaps=gaps,
            artifacts_scanned=scanned,
        )

    def _run_quality_agent(self) -> AgentResult:
        """Score artifact quality and flag issues."""
        gaps: list[Gap] = []
        scanned = 0

        def parse_frontmatter(content: str) -> dict:
            """Extract YAML frontmatter from markdown.

            Falls back to simple key:value parsing if YAML is malformed.
            """
            match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if not match:
                return {}
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                # Fallback to simple key:value parsing for malformed YAML
                result = {}
                for line in match.group(1).split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        result[key.strip()] = value.strip()
                return result

        # Check user skills for quality
        if self.user_skills_dir.exists():
            for skill_dir in self.user_skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue

                scanned += 1
                skill_name = skill_dir.name
                try:
                    content = skill_md.read_text()
                except (OSError, UnicodeDecodeError) as e:
                    logging.warning(f"Skipping unreadable skill {skill_md}: {e}")
                    continue
                frontmatter = parse_frontmatter(content)

                # Check for description
                if not frontmatter.get("description"):
                    gaps.append(
                        Gap(
                            gap_id=f"gap-quality-{uuid.uuid4().hex[:6]}",
                            gap_type=GapType.QUALITY_ISSUE,
                            title=f"Missing description: {skill_name}",
                            description=f"Skill '{skill_name}' lacks a description field in frontmatter",
                            source_agent="quality-scorer",
                            confidence=0.9,
                            priority=2,
                        )
                    )

                # Check content length (excluding frontmatter)
                body = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)
                if len(body.strip()) < 100:
                    gaps.append(
                        Gap(
                            gap_id=f"gap-quality-{uuid.uuid4().hex[:6]}",
                            gap_type=GapType.QUALITY_ISSUE,
                            title=f"Minimal content: {skill_name}",
                            description=f"Skill '{skill_name}' has very short content (< 100 chars)",
                            source_agent="quality-scorer",
                            confidence=0.8,
                            priority=3,
                        )
                    )

        return AgentResult(
            agent_name="quality-scorer",
            gaps=gaps,
            artifacts_scanned=scanned,
        )

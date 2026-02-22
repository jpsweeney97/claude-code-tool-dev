"""Spec-lock tests for E-PLANNING cross-file consistency.

These tests verify that cross-file references remain consistent across
the E-PLANNING implementation files. They read the actual source files
and check for structural invariants.
"""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = (
    Path(__file__).resolve().parent.parent / "packages" / "plugins" / "cross-model"
)
SKILL_PATH = PLUGIN_ROOT / "skills" / "dialogue" / "SKILL.md"
PROFILES_PATH = PLUGIN_ROOT / "references" / "consultation-profiles.yaml"
CONTRACT_PATH = PLUGIN_ROOT / "references" / "consultation-contract.md"
AGENT_PATH = PLUGIN_ROOT / "agents" / "codex-dialogue.md"
ANALYTICS_PATH = PLUGIN_ROOT / "scripts" / "emit_analytics.py"


class TestEPlanningSpecSync:
    """Cross-file consistency checks for E-PLANNING."""

    def test_plan_flag_in_skill_argument_table(self) -> None:
        """SKILL.md argument table includes --plan flag."""
        content = SKILL_PATH.read_text()
        assert re.search(r"\|\s*`--plan`\s*\|", content), (
            "SKILL.md argument table missing --plan flag"
        )

    def test_plan_flag_in_argument_hint(self) -> None:
        """SKILL.md frontmatter argument-hint includes --plan."""
        content = SKILL_PATH.read_text()
        assert "--plan" in content.split("---")[1], (
            "SKILL.md argument-hint missing --plan"
        )

    def test_planning_profile_exists(self) -> None:
        """consultation-profiles.yaml has a planning profile."""
        content = PROFILES_PATH.read_text()
        assert re.search(r"^\s+planning:", content, re.MULTILINE), (
            "consultation-profiles.yaml missing planning profile"
        )

    def test_planning_profile_posture(self) -> None:
        """Planning profile uses evaluative posture."""
        content = PROFILES_PATH.read_text()
        planning_match = re.search(
            r"^\s+planning:\s*\n((?:\s{4,}.*\n)*)",
            content,
            re.MULTILINE,
        )
        assert planning_match, (
            "consultation-profiles.yaml missing planning profile block"
        )
        block = planning_match.group(1)
        posture_match = re.search(r"posture:\s*(\w+)", block)
        assert posture_match and posture_match.group(1) == "evaluative", (
            "Planning profile posture should be evaluative"
        )

    def test_reasoning_effort_in_delegation_envelope(self) -> None:
        """Consultation contract §6 delegation envelope includes reasoning_effort."""
        content = CONTRACT_PATH.read_text()
        section_6_match = re.search(
            r"(##\s*§?6\b.*?)(?=##\s*§?7\b|\Z)", content, re.DOTALL
        )
        assert section_6_match, "consultation-contract.md missing §6 section"
        assert "reasoning_effort" in section_6_match.group(1), (
            "consultation-contract.md §6 delegation envelope missing reasoning_effort"
        )

    def test_reasoning_effort_in_agent_parse_table(self) -> None:
        """codex-dialogue agent Phase 1 parse table includes reasoning_effort."""
        content = AGENT_PATH.read_text()
        parse_table_match = re.search(r"\|[^\n]*`reasoning_effort`[^\n]*\|", content)
        assert parse_table_match, (
            "codex-dialogue.md Phase 1 parse table missing reasoning_effort row"
        )

    def test_valid_shape_confidence_in_analytics(self) -> None:
        """emit_analytics.py defines _VALID_SHAPE_CONFIDENCE."""
        content = ANALYTICS_PATH.read_text()
        assert "_VALID_SHAPE_CONFIDENCE" in content, (
            "emit_analytics.py missing _VALID_SHAPE_CONFIDENCE"
        )

    def test_resolve_schema_version_in_analytics(self) -> None:
        """emit_analytics.py defines _resolve_schema_version."""
        content = ANALYTICS_PATH.read_text()
        assert "_resolve_schema_version" in content, (
            "emit_analytics.py missing _resolve_schema_version"
        )

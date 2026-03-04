"""Tests for autonomy config parsing and enforcement."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ticket_engine_core import AutonomyConfig, read_autonomy_config


@pytest.fixture
def autonomy_env(tmp_path: Path):
    """Set up directory structure for autonomy config tests.

    Creates:
        tmp_path/.claude/          (project root marker)
        tmp_path/docs/tickets/     (tickets_dir)

    Returns (tickets_dir, config_path) tuple.
    """
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)
    config_path = claude_dir / "ticket.local.md"
    return tickets_dir, config_path


class TestAutonomyConfig:
    """Test AutonomyConfig dataclass and read_autonomy_config() parsing."""

    def test_default_when_no_config_file(self, autonomy_env):
        """Missing .claude/ticket.local.md → default suggest/5/no warnings."""
        tickets_dir, _ = autonomy_env
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert config.max_creates == 5
        assert config.warnings == []

    def test_valid_auto_audit_config(self, autonomy_env):
        """Valid auto_audit config with custom max_creates."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: 10\n---\n"
        )
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "auto_audit"
        assert config.max_creates == 10
        assert config.warnings == []

    def test_valid_auto_silent_config(self, autonomy_env):
        """Valid auto_silent config."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\nautonomy_mode: auto_silent\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "auto_silent"
        assert config.max_creates == 5  # default

    def test_malformed_yaml_warns_and_defaults(self, autonomy_env):
        """Malformed YAML → suggest + warning (NOT silent swallow)."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\n: [invalid yaml\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert len(config.warnings) == 1
        assert "failed to parse" in config.warnings[0].lower()

    def test_unknown_mode_warns_and_defaults(self, autonomy_env):
        """Unknown autonomy_mode → suggest + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\nautonomy_mode: yolo\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert len(config.warnings) == 1
        assert "yolo" in config.warnings[0]

    def test_non_dict_frontmatter_warns(self, autonomy_env):
        """YAML list instead of dict → suggest + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\n- item1\n- item2\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert len(config.warnings) == 1
        assert "not a dict" in config.warnings[0].lower()

    def test_missing_mode_field_defaults_suggest(self, autonomy_env):
        """No autonomy_mode field → suggest (implicit default)."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\nsome_other_field: value\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert config.warnings == []

    def test_non_int_max_creates_warns(self, autonomy_env):
        """Non-integer max_creates → default 5 + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: lots\n---\n"
        )
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "auto_audit"
        assert config.max_creates == 5
        assert len(config.warnings) == 1
        assert "max_creates" in config.warnings[0].lower()

    def test_zero_max_creates_disables_agent_creates(self, autonomy_env):
        """max_creates=0 means disable all agent creates (not invalid)."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: 0\n---\n"
        )
        config = read_autonomy_config(tickets_dir)
        assert config.max_creates == 0
        assert config.warnings == []

    def test_negative_max_creates_warns(self, autonomy_env):
        """Negative max_creates → default 5 + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: -1\n---\n"
        )
        config = read_autonomy_config(tickets_dir)
        assert config.max_creates == 5
        assert len(config.warnings) == 1

    def test_no_frontmatter_delimiters_warns(self, autonomy_env):
        """File exists but no --- delimiters → suggest + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("autonomy_mode: auto_audit\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert len(config.warnings) == 1
        assert "no valid frontmatter" in config.warnings[0].lower()

    def test_to_dict_from_dict_round_trip(self):
        """AutonomyConfig serialization round-trips correctly."""
        original = AutonomyConfig(mode="auto_audit", max_creates=10, warnings=["w1"])
        restored = AutonomyConfig.from_dict(original.to_dict())
        assert restored.mode == original.mode
        assert restored.max_creates == original.max_creates
        assert restored.warnings == original.warnings

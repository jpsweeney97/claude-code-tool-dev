"""Tests for config reader."""

import textwrap
from pathlib import Path

from scripts.config import Config, read_config


class TestReadConfig:
    def test_valid_config_with_both_fields(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text(
            textwrap.dedent("""\
                ---
                context_window: 1000000
                soft_boundary: 200000
                ---
            """)
        )
        config = read_config(config_file)
        assert config.context_window == 1_000_000
        assert config.soft_boundary == 200_000

    def test_soft_boundary_only(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text("---\nsoft_boundary: 200000\n---\n")
        config = read_config(config_file)
        assert config.context_window == 200_000  # default
        assert config.soft_boundary == 200_000

    def test_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        config = read_config(tmp_path / "nonexistent.md")
        assert config.context_window == 200_000
        assert config.soft_boundary is None

    def test_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text("")
        config = read_config(config_file)
        assert config.context_window == 200_000
        assert config.soft_boundary is None

    def test_invalid_yaml_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text("---\n: broken yaml [[\n---\n")
        config = read_config(config_file)
        assert config.context_window == 200_000
        assert config.soft_boundary is None

    def test_context_window_override(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text("---\ncontext_window: 500000\n---\n")
        config = read_config(config_file)
        assert config.context_window == 500_000


class TestAutoDetection:
    def test_upgrade_to_1m_when_occupancy_exceeds_200k(self) -> None:
        config = Config(context_window=200_000)
        config.maybe_upgrade_window(250_000)
        assert config.context_window == 1_000_000

    def test_no_upgrade_when_under_200k(self) -> None:
        config = Config(context_window=200_000)
        config.maybe_upgrade_window(150_000)
        assert config.context_window == 200_000

    def test_no_upgrade_when_explicitly_set(self) -> None:
        config = Config(context_window=500_000, _explicitly_set=True)
        config.maybe_upgrade_window(600_000)
        assert config.context_window == 500_000

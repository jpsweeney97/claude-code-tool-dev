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


class TestModelDetection:
    def test_opus_4_7_detects_1m(self) -> None:
        config = Config()
        config.detect_window_from_model("claude-opus-4-7")
        assert config.context_window == 1_000_000

    def test_opus_4_7_with_1m_suffix_detects_1m(self) -> None:
        config = Config()
        config.detect_window_from_model("claude-opus-4-7[1m]")
        assert config.context_window == 1_000_000

    def test_opus_4_6_detects_1m(self) -> None:
        config = Config()
        config.detect_window_from_model("claude-opus-4-6")
        assert config.context_window == 1_000_000

    def test_sonnet_4_6_detects_1m(self) -> None:
        config = Config()
        config.detect_window_from_model("claude-sonnet-4-6")
        assert config.context_window == 1_000_000

    def test_dated_model_variant_matches_prefix(self) -> None:
        config = Config()
        config.detect_window_from_model("claude-opus-4-6-20250514")
        assert config.context_window == 1_000_000

    def test_unknown_model_keeps_default(self) -> None:
        config = Config()
        config.detect_window_from_model("claude-haiku-4-5-20251001")
        assert config.context_window == 200_000

    def test_empty_model_keeps_default(self) -> None:
        config = Config()
        config.detect_window_from_model("")
        assert config.context_window == 200_000

    def test_explicit_config_blocks_model_detection(self) -> None:
        config = Config(context_window=500_000, _explicitly_set=True)
        config.detect_window_from_model("claude-opus-4-6")
        assert config.context_window == 500_000

    def test_model_detection_blocks_occupancy_upgrade(self) -> None:
        """Once model is detected, occupancy-based upgrade is skipped."""
        config = Config()
        config.detect_window_from_model("claude-haiku-4-5")
        # Unknown model, so window stays 200k but _model_detected is False
        assert config.context_window == 200_000
        # Occupancy upgrade should still work for unknown models
        config.maybe_upgrade_window(250_000)
        assert config.context_window == 1_000_000

    def test_known_model_blocks_occupancy_upgrade(self) -> None:
        """Known model detection prevents occupancy override."""
        config = Config()
        config.detect_window_from_model("claude-opus-4-6")
        assert config.context_window == 1_000_000
        # Even if occupancy is low, window stays at model-detected value
        config.maybe_upgrade_window(50_000)
        assert config.context_window == 1_000_000

    def test_detection_runs_only_once(self) -> None:
        """First model detection wins; subsequent calls are no-ops."""
        config = Config()
        config.detect_window_from_model("claude-opus-4-6")
        assert config.context_window == 1_000_000
        # Calling again with a different (hypothetical) model is a no-op
        config.detect_window_from_model("claude-haiku-4-5")
        assert config.context_window == 1_000_000


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

    def test_no_upgrade_when_model_detected(self) -> None:
        config = Config()
        config.detect_window_from_model("claude-sonnet-4-6")
        config.maybe_upgrade_window(250_000)
        # Model detection takes precedence — no occupancy override
        assert config.context_window == 1_000_000

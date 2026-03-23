"""Tests for CCDI config loading and validation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from scripts.ccdi.config import (
    BUILTIN_DEFAULTS,
    SUPPORTED_CONFIG_VERSION,
    CCDIConfig,
    CCDIConfigLoader,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_config(tmp_path: Path, data: dict[str, Any]) -> Path:
    """Write a config dict to a temp JSON file and return the path."""
    p = tmp_path / "ccdi_config.json"
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# Missing / default config
# ---------------------------------------------------------------------------


class TestMissingConfig:
    """Missing config file uses all built-in defaults."""

    def test_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        loader = CCDIConfigLoader(tmp_path / "nonexistent.json")
        cfg = loader.load()
        assert isinstance(cfg, CCDIConfig)
        assert cfg.classifier_confidence_high_min_weight == 0.8
        assert cfg.injection_initial_threshold_high_count == 1
        assert cfg.packets_initial_token_budget_min == 600
        assert cfg.packets_initial_token_budget_max == 1000

    def test_missing_file_is_frozen(self, tmp_path: Path) -> None:
        loader = CCDIConfigLoader(tmp_path / "nonexistent.json")
        cfg = loader.load()
        with pytest.raises(AttributeError):
            cfg.classifier_confidence_high_min_weight = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Partial config fills defaults
# ---------------------------------------------------------------------------


class TestPartialConfig:
    """Partial config: provided values used, missing filled from defaults."""

    def test_partial_classifier_only(self, tmp_path: Path) -> None:
        data = {
            "config_version": "1",
            "classifier": {"confidence_high_min_weight": 0.9},
        }
        cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.classifier_confidence_high_min_weight == 0.9
        # Other classifier defaults filled
        assert cfg.classifier_confidence_medium_min_score == 0.5
        # Other sections all default
        assert cfg.injection_initial_threshold_high_count == 1
        assert cfg.packets_initial_token_budget_min == 600

    def test_partial_packets_only(self, tmp_path: Path) -> None:
        data = {
            "config_version": "1",
            "packets": {"initial_max_topics": 5},
        }
        cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.packets_initial_max_topics == 5
        assert cfg.classifier_confidence_high_min_weight == 0.8


# ---------------------------------------------------------------------------
# Version mismatch falls back to all defaults
# ---------------------------------------------------------------------------


class TestVersionMismatch:
    """Unsupported config_version falls back to all defaults + warning."""

    def test_version_2_falls_back(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "2",
            "classifier": {"confidence_high_min_weight": 0.99},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        # Falls back to ALL defaults
        assert cfg.classifier_confidence_high_min_weight == 0.8
        assert any("config_version" in msg for msg in caplog.messages)

    def test_missing_version_falls_back(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {"classifier": {"confidence_high_min_weight": 0.99}}
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.classifier_confidence_high_min_weight == 0.8


# ---------------------------------------------------------------------------
# Null value uses default
# ---------------------------------------------------------------------------


class TestNullValues:
    """Null (None) values in config fall back to defaults + warning."""

    def test_null_weight_uses_default(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "classifier": {"confidence_high_min_weight": None},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.classifier_confidence_high_min_weight == 0.8
        assert any("null" in msg.lower() or "None" in msg for msg in caplog.messages)

    def test_null_count_uses_default(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "injection": {"initial_threshold_high_count": None},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.injection_initial_threshold_high_count == 1


# ---------------------------------------------------------------------------
# Out-of-range values use default
# ---------------------------------------------------------------------------


class TestOutOfRange:
    """Out-of-range values fall back to default + warning."""

    def test_weight_above_one(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "classifier": {"confidence_high_min_weight": 1.5},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.classifier_confidence_high_min_weight == 0.8

    def test_weight_below_zero(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "classifier": {"confidence_high_min_weight": -0.1},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.classifier_confidence_high_min_weight == 0.8

    def test_negative_count(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "injection": {"initial_threshold_high_count": -1},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.injection_initial_threshold_high_count == 1

    def test_zero_count(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "injection": {"initial_threshold_high_count": 0},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.injection_initial_threshold_high_count == 1

    def test_negative_token_budget(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "packets": {"initial_token_budget_min": -100},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.packets_initial_token_budget_min == 600

    def test_quality_score_above_one(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "packets": {"quality_min_result_score": 2.0},
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.packets_quality_min_result_score == 0.3


# ---------------------------------------------------------------------------
# Cross-key: min > max triggers paired fallback
# ---------------------------------------------------------------------------


class TestCrossKeyValidation:
    """Token budget min > max falls back BOTH keys to defaults."""

    def test_initial_budget_min_gt_max(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "packets": {
                "initial_token_budget_min": 1200,
                "initial_token_budget_max": 800,
            },
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        # Both fall back to defaults
        assert cfg.packets_initial_token_budget_min == 600
        assert cfg.packets_initial_token_budget_max == 1000
        assert any("min" in msg.lower() and "max" in msg.lower() for msg in caplog.messages)

    def test_mid_turn_budget_min_gt_max(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "config_version": "1",
            "packets": {
                "mid_turn_token_budget_min": 500,
                "mid_turn_token_budget_max": 200,
            },
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.packets_mid_turn_token_budget_min == 250
        assert cfg.packets_mid_turn_token_budget_max == 450

    def test_cross_key_on_effective_values(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Cross-key runs on post-per-key-fallback values.

        If min is out of range (falls back to default 600) and max is valid
        but less than the effective min, BOTH fall back.
        """
        data = {
            "config_version": "1",
            "packets": {
                "initial_token_budget_min": -1,  # falls back to 600
                "initial_token_budget_max": 500,  # valid per-key, but < 600
            },
        }
        with caplog.at_level(logging.WARNING, logger="scripts.ccdi.config"):
            cfg = CCDIConfigLoader(_write_config(tmp_path, data)).load()
        assert cfg.packets_initial_token_budget_min == 600
        assert cfg.packets_initial_token_budget_max == 1000


# ---------------------------------------------------------------------------
# BUILTIN_DEFAULTS and SUPPORTED_CONFIG_VERSION
# ---------------------------------------------------------------------------


class TestBuiltinDefaults:
    """Verify BUILTIN_DEFAULTS matches spec and is complete."""

    def test_supported_version(self) -> None:
        assert SUPPORTED_CONFIG_VERSION == "1"

    def test_all_sections_present(self) -> None:
        assert "classifier" in BUILTIN_DEFAULTS
        assert "injection" in BUILTIN_DEFAULTS
        assert "packets" in BUILTIN_DEFAULTS

    def test_classifier_defaults(self) -> None:
        c = BUILTIN_DEFAULTS["classifier"]
        assert c["confidence_high_min_weight"] == 0.8
        assert c["confidence_medium_min_score"] == 0.5
        assert c["confidence_medium_min_single_weight"] == 0.5

    def test_injection_defaults(self) -> None:
        inj = BUILTIN_DEFAULTS["injection"]
        assert inj["initial_threshold_high_count"] == 1
        assert inj["initial_threshold_medium_same_family_count"] == 2
        assert inj["mid_turn_consecutive_medium_turns"] == 2
        assert inj["cooldown_max_new_topics_per_turn"] == 1
        assert inj["deferred_ttl_turns"] == 3

    def test_packets_defaults(self) -> None:
        p = BUILTIN_DEFAULTS["packets"]
        assert p["initial_token_budget_min"] == 600
        assert p["initial_token_budget_max"] == 1000
        assert p["initial_max_topics"] == 3
        assert p["initial_max_facts"] == 8
        assert p["mid_turn_token_budget_min"] == 250
        assert p["mid_turn_token_budget_max"] == 450
        assert p["mid_turn_max_topics"] == 1
        assert p["mid_turn_max_facts"] == 3
        assert p["quality_min_result_score"] == 0.3
        assert p["quality_min_useful_facts"] == 1

"""CCDI configuration loading and validation.

Loads config from a JSON file, validates per-key ranges and cross-key
constraints, and returns a frozen CCDIConfig dataclass. Invalid or missing
values fall back to built-in defaults with warnings.

Import pattern:
    from scripts.ccdi.config import CCDIConfigLoader, CCDIConfig
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_CONFIG_VERSION = "1"

# ---------------------------------------------------------------------------
# Built-in defaults — exact copy of spec values
# ---------------------------------------------------------------------------

BUILTIN_DEFAULTS: dict[str, dict[str, Any]] = {
    "classifier": {
        "confidence_high_min_weight": 0.8,
        "confidence_medium_min_score": 0.5,
        "confidence_medium_min_single_weight": 0.5,
    },
    "injection": {
        "initial_threshold_high_count": 1,
        "initial_threshold_medium_same_family_count": 2,
        "mid_turn_consecutive_medium_turns": 2,
        "cooldown_max_new_topics_per_turn": 1,
        "deferred_ttl_turns": 3,
    },
    "packets": {
        "initial_token_budget_min": 600,
        "initial_token_budget_max": 1000,
        "initial_max_topics": 3,
        "initial_max_facts": 8,
        "mid_turn_token_budget_min": 250,
        "mid_turn_token_budget_max": 450,
        "mid_turn_max_topics": 1,
        "mid_turn_max_facts": 3,
        "quality_min_result_score": 0.3,
        "quality_min_useful_facts": 1,
    },
}

# ---------------------------------------------------------------------------
# Validation rules per key
# ---------------------------------------------------------------------------

# Keys whose values must be floats in [0.0, 1.0]
_WEIGHT_KEYS: set[str] = {
    "confidence_high_min_weight",
    "confidence_medium_min_score",
    "confidence_medium_min_single_weight",
    "quality_min_result_score",
}

# Keys whose values must be positive integers (> 0)
_POSITIVE_INT_KEYS: set[str] = {
    "initial_threshold_high_count",
    "initial_threshold_medium_same_family_count",
    "mid_turn_consecutive_medium_turns",
    "cooldown_max_new_topics_per_turn",
    "deferred_ttl_turns",
    "initial_token_budget_min",
    "initial_token_budget_max",
    "initial_max_topics",
    "initial_max_facts",
    "mid_turn_token_budget_min",
    "mid_turn_token_budget_max",
    "mid_turn_max_topics",
    "mid_turn_max_facts",
    "quality_min_useful_facts",
}

# Cross-key token budget pairs: (min_key, max_key)
_TOKEN_BUDGET_PAIRS: list[tuple[str, str]] = [
    ("initial_token_budget_min", "initial_token_budget_max"),
    ("mid_turn_token_budget_min", "mid_turn_token_budget_max"),
]


# ---------------------------------------------------------------------------
# Config dataclass (frozen)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CCDIConfig:
    """Validated, immutable CCDI configuration."""

    # Classifier
    classifier_confidence_high_min_weight: float
    classifier_confidence_medium_min_score: float
    classifier_confidence_medium_min_single_weight: float
    # Injection
    injection_initial_threshold_high_count: int
    injection_initial_threshold_medium_same_family_count: int
    injection_mid_turn_consecutive_medium_turns: int
    injection_cooldown_max_new_topics_per_turn: int
    injection_deferred_ttl_turns: int
    # Packets
    packets_initial_token_budget_min: int
    packets_initial_token_budget_max: int
    packets_initial_max_topics: int
    packets_initial_max_facts: int
    packets_mid_turn_token_budget_min: int
    packets_mid_turn_token_budget_max: int
    packets_mid_turn_max_topics: int
    packets_mid_turn_max_facts: int
    packets_quality_min_result_score: float
    packets_quality_min_useful_facts: int


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


class CCDIConfigLoader:
    """Load and validate CCDI config from a JSON file.

    Validation order:
    1. Load JSON (missing file → all defaults)
    2. Check config_version (mismatch → all defaults + warning)
    3. Per-key validation (null, out-of-range → that key's default + warning)
    4. Cross-key validation (token min > max → both keys to default + warning)
    5. Return frozen CCDIConfig
    """

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def load(self) -> CCDIConfig:
        """Load config, validate, return frozen CCDIConfig."""
        raw = self._read_file()
        if raw is None:
            return self._from_defaults()

        # Version check
        version = raw.get("config_version")
        if version != SUPPORTED_CONFIG_VERSION:
            logger.warning(
                "Unsupported config_version %r (expected %r); using all defaults",
                version,
                SUPPORTED_CONFIG_VERSION,
            )
            return self._from_defaults()

        # Build effective values per section
        effective: dict[str, dict[str, Any]] = {}
        for section, defaults in BUILTIN_DEFAULTS.items():
            raw_section = raw.get(section, {})
            effective[section] = {}
            for key, default_val in defaults.items():
                raw_val = raw_section.get(key)
                effective[section][key] = self._validate_key(
                    section, key, raw_val, default_val
                )

        # Cross-key validation on effective values
        self._cross_validate_budgets(effective)

        return self._build_config(effective)

    def _read_file(self) -> dict[str, Any] | None:
        """Read and parse JSON file. Returns None if missing or invalid."""
        if not self._path.exists():
            logger.info("Config file not found at %s; using defaults", self._path)
            return None
        try:
            text = self._path.read_text()
            return json.loads(text)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read config %s: %s; using defaults", self._path, exc)
            return None

    def _validate_key(
        self, section: str, key: str, raw_val: Any, default_val: Any
    ) -> Any:
        """Validate a single config value. Returns effective value."""
        if raw_val is None:
            logger.warning(
                "Config %s.%s is null (None); using default %r",
                section,
                key,
                default_val,
            )
            return default_val

        if key in _WEIGHT_KEYS:
            if not isinstance(raw_val, (int, float)) or raw_val < 0.0 or raw_val > 1.0:
                logger.warning(
                    "Config %s.%s=%r out of range [0.0, 1.0]; using default %r",
                    section,
                    key,
                    raw_val,
                    default_val,
                )
                return default_val
            return float(raw_val)

        if key in _POSITIVE_INT_KEYS:
            if not isinstance(raw_val, (int, float)) or raw_val <= 0:
                logger.warning(
                    "Config %s.%s=%r must be a positive integer; using default %r",
                    section,
                    key,
                    raw_val,
                    default_val,
                )
                return default_val
            return int(raw_val)

        # Unknown key type — accept as-is
        return raw_val

    def _cross_validate_budgets(self, effective: dict[str, dict[str, Any]]) -> None:
        """Check token budget min <= max pairs; fall back BOTH if violated."""
        packets = effective["packets"]
        for min_key, max_key in _TOKEN_BUDGET_PAIRS:
            min_val = packets[min_key]
            max_val = packets[max_key]
            if min_val > max_val:
                default_min = BUILTIN_DEFAULTS["packets"][min_key]
                default_max = BUILTIN_DEFAULTS["packets"][max_key]
                logger.warning(
                    "Config packets.%s=%r > packets.%s=%r (min > max); "
                    "falling back both to defaults (%r, %r)",
                    min_key,
                    min_val,
                    max_key,
                    max_val,
                    default_min,
                    default_max,
                )
                packets[min_key] = default_min
                packets[max_key] = default_max

    def _build_config(self, effective: dict[str, dict[str, Any]]) -> CCDIConfig:
        """Build frozen CCDIConfig from effective values."""
        c = effective["classifier"]
        i = effective["injection"]
        p = effective["packets"]
        return CCDIConfig(
            classifier_confidence_high_min_weight=c["confidence_high_min_weight"],
            classifier_confidence_medium_min_score=c["confidence_medium_min_score"],
            classifier_confidence_medium_min_single_weight=c["confidence_medium_min_single_weight"],
            injection_initial_threshold_high_count=i["initial_threshold_high_count"],
            injection_initial_threshold_medium_same_family_count=i["initial_threshold_medium_same_family_count"],
            injection_mid_turn_consecutive_medium_turns=i["mid_turn_consecutive_medium_turns"],
            injection_cooldown_max_new_topics_per_turn=i["cooldown_max_new_topics_per_turn"],
            injection_deferred_ttl_turns=i["deferred_ttl_turns"],
            packets_initial_token_budget_min=p["initial_token_budget_min"],
            packets_initial_token_budget_max=p["initial_token_budget_max"],
            packets_initial_max_topics=p["initial_max_topics"],
            packets_initial_max_facts=p["initial_max_facts"],
            packets_mid_turn_token_budget_min=p["mid_turn_token_budget_min"],
            packets_mid_turn_token_budget_max=p["mid_turn_token_budget_max"],
            packets_mid_turn_max_topics=p["mid_turn_max_topics"],
            packets_mid_turn_max_facts=p["mid_turn_max_facts"],
            packets_quality_min_result_score=p["quality_min_result_score"],
            packets_quality_min_useful_facts=p["quality_min_useful_facts"],
        )

    def _from_defaults(self) -> CCDIConfig:
        """Build CCDIConfig from all built-in defaults."""
        return self._build_config(BUILTIN_DEFAULTS)

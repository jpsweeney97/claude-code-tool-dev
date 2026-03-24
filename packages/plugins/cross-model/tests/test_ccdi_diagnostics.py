"""Tests for CCDI diagnostics emitter."""

from __future__ import annotations

from scripts.ccdi.diagnostics import DiagnosticsEmitter

# Shadow-only field names that must NOT appear in active mode output
SHADOW_ONLY_FIELDS = {
    "packets_target_relevant",
    "packets_surviving_precedence",
    "false_positive_topic_detections",
    "shadow_adjusted_yield",
}


# ---------------------------------------------------------------------------
# false_positive_topic_detections is always zero
# ---------------------------------------------------------------------------


class TestFalsePositiveAlwaysZero:
    """Emitter always outputs false_positive_topic_detections: 0 in shadow mode."""

    def test_false_positive_field_always_zero(self) -> None:
        emitter = DiagnosticsEmitter(
            status="shadow",
            phase="full",
            inventory_epoch="2026-03-23",
            config_source="builtin",
        )
        result = emitter.emit()
        assert result["false_positive_topic_detections"] == 0


# ---------------------------------------------------------------------------
# Active mode omits shadow-only fields
# ---------------------------------------------------------------------------


class TestActiveModeSchema:
    """Active mode JSON does NOT contain shadow-only fields."""

    def test_active_mode_omits_shadow_fields(self) -> None:
        emitter = DiagnosticsEmitter(
            status="active",
            phase="full",
            inventory_epoch="2026-03-23",
            config_source="builtin",
        )
        result = emitter.emit()
        present = SHADOW_ONLY_FIELDS & set(result.keys())
        assert present == set(), f"Shadow-only fields found in active output: {present}"


# ---------------------------------------------------------------------------
# Shadow mode includes shadow-only fields
# ---------------------------------------------------------------------------


class TestShadowModeSchema:
    """Shadow mode JSON contains all shadow-only fields."""

    def test_shadow_mode_includes_shadow_fields(self) -> None:
        emitter = DiagnosticsEmitter(
            status="shadow",
            phase="full",
            inventory_epoch="2026-03-23",
            config_source="builtin",
        )
        result = emitter.emit()
        missing = SHADOW_ONLY_FIELDS - set(result.keys())
        assert missing == set(), f"Shadow-only fields missing from shadow output: {missing}"


# ---------------------------------------------------------------------------
# Unavailable schema — only status and phase
# ---------------------------------------------------------------------------


class TestUnavailableSchema:
    """Only status and phase populated, all other fields absent."""

    def test_unavailable_schema(self) -> None:
        result = DiagnosticsEmitter.unavailable(phase="initial_only")
        assert result == {"status": "unavailable", "phase": "initial_only"}

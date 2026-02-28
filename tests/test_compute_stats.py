"""Tests for packages/plugins/cross-model/scripts/compute_stats.py.

Tests the analytics computation orchestrator: section computation
functions, section inclusion matrix, validation gate, key-presence
contracts, and CLI entry point.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module imports via importlib (no package install required)
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "packages" / "plugins" / "cross-model" / "scripts"

# Import read_events first (compute_stats depends on it)
_re_spec = importlib.util.spec_from_file_location("read_events", SCRIPTS_DIR / "read_events.py")
_re_mod = importlib.util.module_from_spec(_re_spec)
sys.modules["read_events"] = _re_mod
_re_spec.loader.exec_module(_re_mod)

# Import stats_common (compute_stats depends on it)
_sc_spec = importlib.util.spec_from_file_location("stats_common", SCRIPTS_DIR / "stats_common.py")
_sc_mod = importlib.util.module_from_spec(_sc_spec)
sys.modules["stats_common"] = _sc_mod
_sc_spec.loader.exec_module(_sc_mod)

# Import compute_stats (the module under test)
_cs_spec = importlib.util.spec_from_file_location("compute_stats", SCRIPTS_DIR / "compute_stats.py")
MODULE = importlib.util.module_from_spec(_cs_spec)
sys.modules["compute_stats"] = MODULE
_cs_spec.loader.exec_module(MODULE)


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_dialogue(**overrides: object) -> dict:
    """Make a dialogue_outcome event."""
    base: dict = {
        "schema_version": "0.1.0",
        "consultation_id": "uuid-d",
        "event": "dialogue_outcome",
        "ts": "2026-02-15T12:00:00Z",
        "posture": "evaluative",
        "turn_count": 4,
        "turn_budget": 8,
        "converged": True,
        "convergence_reason_code": "natural_convergence",
        "termination_reason": "convergence",
        "resolved_count": 5,
        "unresolved_count": 0,
        "emerged_count": 2,
        "seed_confidence": "normal",
        "mode": "server_assisted",
    }
    base.update(overrides)
    return base


def _make_consultation(**overrides: object) -> dict:
    """Make a consultation_outcome event."""
    base: dict = {
        "schema_version": "0.1.0",
        "consultation_id": "uuid-c",
        "event": "consultation_outcome",
        "ts": "2026-02-15T13:00:00Z",
        "posture": "collaborative",
        "turn_count": 1,
        "turn_budget": 1,
        "termination_reason": "complete",
        "mode": "server_assisted",
    }
    base.update(overrides)
    return base


def _make_block(**overrides: object) -> dict:
    """Make a block guard event."""
    base: dict = {
        "ts": "2026-02-15T10:00:00Z",
        "event": "block",
        "tool": "Bash",
        "session_id": "s1",
        "prompt_length": 500,
        "reason": "strict:secret",
    }
    base.update(overrides)
    return base


def _make_shadow(**overrides: object) -> dict:
    """Make a shadow guard event."""
    base: dict = {
        "ts": "2026-02-15T10:01:00Z",
        "event": "shadow",
        "tool": "Bash",
        "session_id": "s1",
        "prompt_length": 600,
    }
    base.update(overrides)
    return base


def _make_raw_call(**overrides: object) -> dict:
    """Make a consultation (raw MCP call) guard event."""
    base: dict = {
        "ts": "2026-02-15T11:00:00Z",
        "event": "consultation",
        "tool": "codex",
        "session_id": "s1",
        "prompt_length": 400,
        "result_length": 200,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# TestComputeUsage
# ---------------------------------------------------------------------------


class TestComputeUsage:
    """Tests for _compute_usage section computation."""

    def test_non_overlapping_counts(self) -> None:
        """Verify no double-counting across event categories."""
        dialogues = [_make_dialogue(), _make_dialogue(consultation_id="uuid-d2")]
        consultations_out = [_make_consultation()]
        raw_calls = [_make_raw_call(), _make_raw_call(session_id="s2")]
        blocks = [_make_block()]
        shadows = [_make_shadow()]

        result = MODULE._compute_usage(dialogues, consultations_out, raw_calls, blocks, shadows)

        assert result["dialogues_completed_total"] == 2
        assert result["consultations_completed_total"] == 1
        assert result["invocations_completed_total"] == 3  # 2 + 1
        assert result["tool_calls_success_total"] == 2
        assert result["tool_calls_blocked_total"] == 1
        assert result["shadow_count"] == 1

    def test_active_utc_days(self) -> None:
        """Active UTC days counts distinct dates from outcome events only."""
        dialogues = [
            _make_dialogue(ts="2026-02-15T23:59:00Z"),
            _make_dialogue(ts="2026-02-15T01:00:00Z"),  # same date
            _make_dialogue(ts="2026-02-16T00:00:00Z"),  # different date
        ]
        consultations_out = [
            _make_consultation(ts="2026-02-17T12:00:00Z"),
        ]
        result = MODULE._compute_usage(dialogues, consultations_out, [], [], [])
        assert result["active_utc_days"] == 3  # 15, 16, 17

    def test_posture_counts_from_outcomes_only(self) -> None:
        """Posture counts aggregate from dialogue + consultation outcomes only."""
        dialogues = [_make_dialogue(posture="evaluative"), _make_dialogue(posture="adversarial")]
        consultations_out = [_make_consultation(posture="collaborative")]
        # Guard events have posture-like fields but should not be counted
        result = MODULE._compute_usage(dialogues, consultations_out, [], [], [])
        assert result["posture_counts"] == {
            "evaluative": 1,
            "adversarial": 1,
            "collaborative": 1,
        }

    def test_schema_version_counts_from_outcomes_only(self) -> None:
        """Schema version counts come from outcome events only."""
        dialogues = [_make_dialogue(schema_version="0.1.0"), _make_dialogue(schema_version="0.2.0")]
        consultations_out = [_make_consultation(schema_version="0.1.0")]
        result = MODULE._compute_usage(dialogues, consultations_out, [], [], [])
        assert result["schema_version_counts"] == {"0.1.0": 2, "0.2.0": 1}

    def test_empty_events(self) -> None:
        """All-empty inputs produce zeroed counters."""
        result = MODULE._compute_usage([], [], [], [], [])
        assert result["dialogues_completed_total"] == 0
        assert result["invocations_completed_total"] == 0
        assert result["active_utc_days"] == 0
        assert result["posture_counts"] == {}


# ---------------------------------------------------------------------------
# TestComputeDialogue
# ---------------------------------------------------------------------------


class TestComputeDialogue:
    """Tests for _compute_dialogue section computation."""

    def test_convergence_rate_excludes_non_boolean(self) -> None:
        """converged=None events are excluded from convergence counts."""
        events = [
            _make_dialogue(converged=True),
            _make_dialogue(converged=False),
            _make_dialogue(converged=None),  # not boolean — excluded
        ]
        result = MODULE._compute_dialogue(events)
        assert result["converged_count"] == 1
        assert result["not_converged_count"] == 1
        assert result["convergence_observed_count"] == 2
        assert result["convergence_rate"] == pytest.approx(0.5)
        assert result["sample_size"] == 3

    def test_convergence_rate_null_when_zero_dialogues(self) -> None:
        """convergence_rate is None when no dialogues exist."""
        result = MODULE._compute_dialogue([])
        assert result["convergence_rate"] is None
        assert result["convergence_observed_count"] == 0

    def test_observed_avg_for_nullable_fields(self) -> None:
        """observed_avg with _observed_count companions for nullable fields."""
        e1 = _make_dialogue(turn_count=4, scout_count=2)
        # Second event: remove scout_count and resolved_count to make them unobserved
        e2 = _make_dialogue(turn_count=6)
        del e2["resolved_count"]  # factory default is 5 — remove to test unobserved
        result = MODULE._compute_dialogue([e1, e2])
        assert result["avg_turn_count"] == pytest.approx(5.0)
        assert result["avg_turn_count_observed_count"] == 2
        assert result["avg_scout_count"] == pytest.approx(2.0)
        assert result["avg_scout_count_observed_count"] == 1
        assert result["avg_resolved_count"] == pytest.approx(5.0)
        assert result["avg_resolved_count_observed_count"] == 1

    def test_avg_turns_to_convergence_converged_only(self) -> None:
        """avg_turns_to_convergence uses only converged=True events."""
        events = [
            _make_dialogue(converged=True, turn_count=4),
            _make_dialogue(converged=True, turn_count=6),
            _make_dialogue(converged=False, turn_count=10),  # excluded
        ]
        result = MODULE._compute_dialogue(events)
        assert result["avg_turns_to_convergence"] == pytest.approx(5.0)
        assert result["avg_turns_to_convergence_observed_count"] == 2

    def test_avg_turns_to_convergence_null_when_zero_converged(self) -> None:
        """avg_turns_to_convergence is None when no events converged."""
        events = [_make_dialogue(converged=False)]
        result = MODULE._compute_dialogue(events)
        assert result["avg_turns_to_convergence"] is None
        assert result["avg_turns_to_convergence_observed_count"] == 0

    def test_distributions(self) -> None:
        """mode_counts, termination_counts, convergence_reason_counts."""
        events = [
            _make_dialogue(mode="server_assisted", termination_reason="convergence", convergence_reason_code="natural_convergence"),
            _make_dialogue(mode="server_assisted", termination_reason="budget", convergence_reason_code=None),
            _make_dialogue(mode="direct", termination_reason="convergence", convergence_reason_code="forced"),
        ]
        result = MODULE._compute_dialogue(events)
        assert result["mode_counts"] == {"server_assisted": 2, "direct": 1}
        assert result["termination_counts"] == {"convergence": 2, "budget": 1}
        assert result["convergence_reason_counts"] == {"natural_convergence": 1, "forced": 1}

    def test_empty_dialogues(self) -> None:
        """Empty input produces None averages and zero counts."""
        result = MODULE._compute_dialogue([])
        assert result["avg_turn_count"] is None
        assert result["avg_turn_count_observed_count"] == 0
        assert result["avg_scout_count"] is None
        assert result["sample_size"] == 0


# ---------------------------------------------------------------------------
# TestComputeContext
# ---------------------------------------------------------------------------


class TestComputeContext:
    """Tests for _compute_context section computation."""

    def test_observed_avg_citations_and_files(self) -> None:
        """observed_avg for citations_total/unique_files_total with _observed_count."""
        events = [
            _make_dialogue(citations_total=10, unique_files_total=3),
            _make_dialogue(citations_total=20),  # unique_files_total absent
        ]
        result = MODULE._compute_context(events)
        assert result["avg_citations_total"] == pytest.approx(15.0)
        assert result["avg_citations_total_observed_count"] == 2
        assert result["avg_unique_files_total"] == pytest.approx(3.0)
        assert result["avg_unique_files_total_observed_count"] == 1

    def test_observed_bool_slots_for_retries(self) -> None:
        """retry_true_count, retry_observed_slots, retry_missing_slots from bool slots."""
        events = [
            _make_dialogue(gatherer_a_retry=True, gatherer_b_retry=False),
            _make_dialogue(gatherer_a_retry=False),  # gatherer_b_retry missing
        ]
        result = MODULE._compute_context(events)
        assert result["retry_true_count"] == 1
        assert result["retry_observed_slots"] == 3  # 2 + 1
        assert result["retry_missing_slots"] == 1  # 4 total slots - 3 observed

    def test_low_seed_aggregation(self) -> None:
        """aggregate_low_seed_reasons integration."""
        events = [
            _make_dialogue(seed_confidence="low", low_seed_confidence_reasons=["no_spec", "short_prompt"]),
            _make_dialogue(seed_confidence="low", low_seed_confidence_reasons=["no_spec"]),
            _make_dialogue(seed_confidence="normal"),
        ]
        result = MODULE._compute_context(events)
        assert result["low_seed_event_count"] == 2
        assert result["low_seed_reason_counts"]["no_spec"] == 2
        assert result["low_seed_reason_counts"]["short_prompt"] == 1
        assert result["low_seed_mentions_total"] == 3
        assert result["low_seed_no_reason_count"] == 0

    def test_seed_confidence_counts(self) -> None:
        """seed_confidence_counts aggregates from all dialogues."""
        events = [
            _make_dialogue(seed_confidence="normal"),
            _make_dialogue(seed_confidence="low"),
            _make_dialogue(seed_confidence="normal"),
        ]
        result = MODULE._compute_context(events)
        assert result["seed_confidence_counts"] == {"normal": 2, "low": 1}

    def test_empty_context(self) -> None:
        """Empty input produces None averages and zero counts."""
        result = MODULE._compute_context([])
        assert result["avg_citations_total"] is None
        assert result["avg_citations_total_observed_count"] == 0
        assert result["retry_true_count"] == 0
        assert result["retry_observed_slots"] == 0
        assert result["retry_missing_slots"] == 0
        assert result["sample_size"] == 0


# ---------------------------------------------------------------------------
# TestComputeSecurity
# ---------------------------------------------------------------------------


class TestComputeSecurity:
    """Tests for _compute_security section computation."""

    def test_dispatch_block_rate_null_when_zero_denom(self) -> None:
        """dispatch_block_rate is None when 0 blocks + 0 consultations."""
        result = MODULE._compute_security([], [], [], invocations_completed_total=5)
        assert result["dispatch_block_rate"] is None

    def test_dispatch_block_rate_calculated(self) -> None:
        """dispatch_block_rate = blocks / (blocks + consultations)."""
        blocks = [_make_block(), _make_block(reason="contextual:leak")]
        raw_calls = [_make_raw_call(), _make_raw_call(), _make_raw_call()]
        # invocations_completed_total=99 proves dispatch_block_rate is independent of it
        result = MODULE._compute_security(blocks, [], raw_calls, invocations_completed_total=99)
        assert result["dispatch_block_rate"] == pytest.approx(2 / 5)

    def test_blocks_per_completed_invocation_null_when_zero(self) -> None:
        """blocks_per_completed_invocation is None when 0 invocations."""
        blocks = [_make_block()]
        result = MODULE._compute_security(blocks, [], [], invocations_completed_total=0)
        assert result["blocks_per_completed_invocation"] is None

    def test_blocks_per_completed_invocation_calculated(self) -> None:
        """blocks_per_completed_invocation = block_count / invocations_completed_total."""
        blocks = [_make_block(), _make_block(reason="broad:pattern")]
        result = MODULE._compute_security(blocks, [], [], invocations_completed_total=10)
        assert result["blocks_per_completed_invocation"] == pytest.approx(0.2)

    def test_tier_counts(self) -> None:
        """tier_counts aggregates security tiers from block reasons."""
        blocks = [
            _make_block(reason="strict:secret"),
            _make_block(reason="strict:key"),
            _make_block(reason="contextual:leak"),
            _make_block(reason=""),  # unknown tier
        ]
        result = MODULE._compute_security(blocks, [], [], invocations_completed_total=0)
        assert result["tier_counts"] == {"strict": 2, "contextual": 1, "unknown": 1}

    def test_shadow_count_and_sample_size(self) -> None:
        """shadow_count and sample_size from blocks + shadows."""
        blocks = [_make_block()]
        shadows = [_make_shadow(), _make_shadow(session_id="s2")]
        result = MODULE._compute_security(blocks, shadows, [], invocations_completed_total=0)
        assert result["shadow_count"] == 2
        assert result["sample_size"] == 3  # 1 block + 2 shadows


# ---------------------------------------------------------------------------
# TestCompute
# ---------------------------------------------------------------------------


class TestCompute:
    """Tests for the compute() orchestrator."""

    def test_section_inclusion_all(self) -> None:
        """--type all includes all four sections."""
        result = MODULE.compute([], 0, 0, "all")
        assert result["usage"]["included"] is True
        assert result["dialogue"]["included"] is True
        assert result["context"]["included"] is True
        assert result["security"]["included"] is True

    def test_section_inclusion_dialogue(self) -> None:
        """--type dialogue includes usage, dialogue, context but not security."""
        result = MODULE.compute([], 0, 0, "dialogue")
        assert result["usage"]["included"] is True
        assert result["dialogue"]["included"] is True
        assert result["context"]["included"] is True
        assert result["security"]["included"] is False

    def test_section_inclusion_consultation(self) -> None:
        """--type consultation includes only usage."""
        result = MODULE.compute([], 0, 0, "consultation")
        assert result["usage"]["included"] is True
        assert result["dialogue"]["included"] is False
        assert result["context"]["included"] is False
        assert result["security"]["included"] is False

    def test_section_inclusion_security(self) -> None:
        """--type security includes only security."""
        result = MODULE.compute([], 0, 0, "security")
        assert result["usage"]["included"] is False
        assert result["dialogue"]["included"] is False
        assert result["context"]["included"] is False
        assert result["security"]["included"] is True

    def test_report_version_present(self) -> None:
        """Top-level report_version is always present."""
        result = MODULE.compute([], 0, 0, "all")
        assert result["report_version"] == "1.0.0"

    def test_meta_includes_malformed_lines_skipped(self) -> None:
        """meta section carries malformed_lines_skipped from input."""
        result = MODULE.compute([], 7, 0, "all")
        assert result["meta"]["malformed_lines_skipped"] == 7

    def test_meta_includes_invalid_events_count(self) -> None:
        """meta section carries invalid_events_count."""
        result = MODULE.compute([], 0, 0, "all")
        assert "invalid_events_count" in result["meta"]

    def test_unknown_section_type_raises(self) -> None:
        """Unknown section_type raises ValueError."""
        with pytest.raises(ValueError, match="unknown section_type"):
            MODULE.compute([], 0, 0, "invalid_type")

    def test_key_presence_usage(self) -> None:
        """Verify usage section has exactly the expected keys (DR-2: hardcoded)."""
        EXPECTED_USAGE_KEYS = {
            "included",
            "dialogues_completed_total",
            "consultations_completed_total",
            "invocations_completed_total",
            "tool_calls_success_total",
            "tool_calls_blocked_total",
            "shadow_count",
            "active_utc_days",
            "posture_counts",
            "schema_version_counts",
        }
        result = MODULE.compute([], 0, 0, "all")
        assert set(result["usage"].keys()) == EXPECTED_USAGE_KEYS

    def test_key_presence_dialogue(self) -> None:
        """Verify dialogue section has exactly the expected keys (DR-2: hardcoded)."""
        EXPECTED_DIALOGUE_KEYS = {
            "included",
            "converged_count",
            "not_converged_count",
            "convergence_observed_count",
            "convergence_rate",
            "avg_turn_count",
            "avg_turn_count_observed_count",
            "avg_turns_to_convergence",
            "avg_turns_to_convergence_observed_count",
            "avg_scout_count",
            "avg_scout_count_observed_count",
            "avg_resolved_count",
            "avg_resolved_count_observed_count",
            "mode_counts",
            "termination_counts",
            "convergence_reason_counts",
            "sample_size",
        }
        result = MODULE.compute([], 0, 0, "all")
        assert set(result["dialogue"].keys()) == EXPECTED_DIALOGUE_KEYS

    def test_key_presence_context(self) -> None:
        """Verify context section has exactly the expected keys (DR-2: hardcoded)."""
        EXPECTED_CONTEXT_KEYS = {
            "included",
            "seed_confidence_counts",
            "low_seed_event_count",
            "low_seed_reason_counts",
            "low_seed_mentions_total",
            "low_seed_no_reason_count",
            "avg_citations_total",
            "avg_citations_total_observed_count",
            "avg_unique_files_total",
            "avg_unique_files_total_observed_count",
            "retry_true_count",
            "retry_observed_slots",
            "retry_missing_slots",
            "sample_size",
        }
        result = MODULE.compute([], 0, 0, "all")
        assert set(result["context"].keys()) == EXPECTED_CONTEXT_KEYS

    def test_key_presence_security(self) -> None:
        """Verify security section has exactly the expected keys (DR-2: hardcoded)."""
        EXPECTED_SECURITY_KEYS = {
            "included",
            "block_count",
            "tier_counts",
            "shadow_count",
            "dispatch_block_rate",
            "blocks_per_completed_invocation",
            "sample_size",
        }
        result = MODULE.compute([], 0, 0, "all")
        assert set(result["security"].keys()) == EXPECTED_SECURITY_KEYS

    def test_key_presence_meta(self) -> None:
        """Verify meta section has exactly the expected keys (DR-2: hardcoded)."""
        EXPECTED_META_KEYS = {
            "total_events_read",
            "malformed_lines_skipped",
            "invalid_events_count",
            "timestamp_parse_failed_count",
            "timezone",
        }
        result = MODULE.compute([], 0, 0, "all")
        assert set(result["meta"].keys()) == EXPECTED_META_KEYS

    def test_security_type_invocations_is_zero_without_outcomes(self) -> None:
        """--type security computes invocations_completed_total=0 without outcome events."""
        blocks = [_make_block()]
        result = MODULE.compute(blocks, 0, 0, "security")
        assert result["security"]["blocks_per_completed_invocation"] is None

    def test_end_to_end_with_mixed_events(self) -> None:
        """Full compute with all event types produces valid report."""
        events = [
            _make_dialogue(converged=True, turn_count=4),
            _make_dialogue(converged=False, turn_count=8),
            _make_consultation(),
            _make_block(),
            _make_shadow(),
            _make_raw_call(),
        ]
        result = MODULE.compute(events, 2, 0, "all")
        assert result["usage"]["dialogues_completed_total"] == 2
        assert result["usage"]["consultations_completed_total"] == 1
        assert result["usage"]["invocations_completed_total"] == 3
        assert result["dialogue"]["convergence_rate"] == pytest.approx(0.5)
        assert result["security"]["block_count"] == 1
        assert result["meta"]["malformed_lines_skipped"] == 2
        assert result["meta"]["total_events_read"] == 6


# ---------------------------------------------------------------------------
# TestValidation
# ---------------------------------------------------------------------------


class TestValidation:
    """Tests for the _validate_events validation gate."""

    def test_invalid_events_excluded(self) -> None:
        """Events failing validate_event() are excluded from metrics."""
        valid_dialogue = _make_dialogue()
        # Missing required fields -> validate_event returns errors
        invalid_dialogue = {"event": "dialogue_outcome", "ts": "2026-02-15T12:00:00Z"}
        events = [valid_dialogue, invalid_dialogue]

        valid, invalid_count = MODULE._validate_events(events)
        assert len(valid) == 1
        assert invalid_count == 1
        assert valid[0] is valid_dialogue

    def test_valid_events_pass_through(self) -> None:
        """Valid outcome events pass through the validation gate."""
        d = _make_dialogue()
        c = _make_consultation()
        valid, invalid_count = MODULE._validate_events([d, c])
        assert len(valid) == 2
        assert invalid_count == 0

    def test_guard_events_pass_unvalidated(self) -> None:
        """Guard events (block, shadow, consultation) pass without validation."""
        events = [_make_block(), _make_shadow(), _make_raw_call()]
        valid, invalid_count = MODULE._validate_events(events)
        assert len(valid) == 3
        assert invalid_count == 0

    def test_validation_gate_truthy_means_errors(self) -> None:
        """validate_event returns truthy (non-empty list) for invalid events.

        The gate logic is `not validate_event()` — truthy return = errors = skip.
        """
        # A valid event returns empty list (falsy)
        assert not _re_mod.validate_event(_make_dialogue())
        # An invalid event returns non-empty list (truthy)
        errors = _re_mod.validate_event({"event": "dialogue_outcome"})
        assert errors  # truthy — has errors

    def test_mixed_valid_and_invalid(self) -> None:
        """Mixed valid/invalid events are correctly separated."""
        events = [
            _make_dialogue(),
            {"event": "dialogue_outcome"},  # invalid — missing fields
            _make_consultation(),
            {"event": "consultation_outcome"},  # invalid — missing fields
            _make_block(),  # guard — always passes
        ]
        valid, invalid_count = MODULE._validate_events(events)
        assert len(valid) == 3  # 1 dialogue + 1 consultation + 1 block
        assert invalid_count == 2


# ---------------------------------------------------------------------------
# TestCLI
# ---------------------------------------------------------------------------


class TestCLI:
    """Tests for the main() CLI entry point."""

    def test_main_with_valid_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """main() reads a JSONL file and prints JSON output."""
        event_file = tmp_path / "events.jsonl"
        event_file.write_text(json.dumps(_make_dialogue()) + "\n")

        original_argv = sys.argv
        try:
            sys.argv = ["compute_stats", str(event_file), "--period", "0", "--type", "all"]
            MODULE.main()
        finally:
            sys.argv = original_argv

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["report_version"] == "1.0.0"
        assert output["usage"]["dialogues_completed_total"] == 1

    def test_main_missing_file_produces_empty_report(self, tmp_path: Path, capsys) -> None:
        """main() produces an empty report for a missing file (read_all returns ([], 0))."""
        missing = tmp_path / "nonexistent.jsonl"
        original_argv = sys.argv
        try:
            sys.argv = ["compute_stats", str(missing), "--period", "0"]
            MODULE.main()
        finally:
            sys.argv = original_argv

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["meta"]["total_events_read"] == 0
        assert output["meta"]["malformed_lines_skipped"] == 0

    def test_main_invalid_period_exits_2(self, tmp_path: Path) -> None:
        """main() exits with code 2 for invalid --period."""
        event_file = tmp_path / "events.jsonl"
        event_file.write_text(json.dumps(_make_dialogue()) + "\n")

        original_argv = sys.argv
        try:
            sys.argv = ["compute_stats", str(event_file), "--period", "bad"]
            with pytest.raises(SystemExit) as exc_info:
                MODULE.main()
            assert exc_info.value.code == 2
        finally:
            sys.argv = original_argv

    def test_main_default_path_used(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """main() uses default path when none is provided."""
        # Patch read_all to return empty events without touching the filesystem
        monkeypatch.setattr(_re_mod, "read_all", lambda path: ([], 0))
        original_argv = sys.argv
        try:
            sys.argv = ["compute_stats", "--period", "0"]
            MODULE.main()
        finally:
            sys.argv = original_argv

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["report_version"] == "1.0.0"

    def test_main_type_flag(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """main() respects --type flag for section inclusion."""
        event_file = tmp_path / "events.jsonl"
        event_file.write_text(json.dumps(_make_dialogue()) + "\n")

        original_argv = sys.argv
        try:
            sys.argv = ["compute_stats", str(event_file), "--period", "0", "--type", "security"]
            MODULE.main()
        finally:
            sys.argv = original_argv

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["usage"]["included"] is False
        assert output["security"]["included"] is True

"""Tests for compute_stats delegation support."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts.compute_stats import (
    compute,
    _DELEGATION_TEMPLATE,
    _PARSE_DIAGNOSTICS_TEMPLATE,
    _PLANNING_TEMPLATE,
    _PROVENANCE_TEMPLATE,
    _SECTION_MATRIX,
    _USAGE_TEMPLATE,
    _compute_consultation,
    _compute_parse_diagnostics,
    _compute_planning,
    _compute_provenance,
)


def _make_delegation_event(**overrides: object) -> dict:
    event = {
        "schema_version": "0.1.0",
        "event": "delegation_outcome",
        "ts": "2026-03-06T12:00:00Z",
        "consultation_id": "test-uuid",
        "session_id": None,
        "thread_id": None,
        "dispatched": True,
        "sandbox": "workspace-write",
        "model": None,
        "reasoning_effort": "high",
        "full_auto": False,
        "credential_blocked": False,
        "dirty_tree_blocked": False,
        "readable_secret_file_blocked": False,
        "commands_run_count": 5,
        "exit_code": 0,
        "termination_reason": "complete",
    }
    event.update(overrides)
    return event




def _make_dialogue_event(**overrides: object) -> dict:
    """Minimal dialogue_outcome event for planning tests."""
    base: dict = {
        "event": "dialogue_outcome",
        "schema_version": "0.3.0",
        "consultation_id": "test-plan-001",
        "ts": "2026-03-17T10:00:00Z",
        "posture": "collaborative",
        "turn_count": 4,
        "turn_budget": 10,
        "converged": True,
        "convergence_reason_code": "all_resolved",
        "termination_reason": "convergence",
        "resolved_count": 3,
        "unresolved_count": 0,
        "emerged_count": 1,
        "seed_confidence": "normal",
        "mode": "server_assisted",
    }
    base.update(overrides)
    return base


def _make_consultation_event(**overrides: object) -> dict:
    """Minimal consultation_outcome event for planning tests."""
    base: dict = {
        "event": "consultation_outcome",
        "schema_version": "0.3.0",
        "consultation_id": "test-consult-001",
        "thread_id": None,
        "ts": "2026-03-17T10:00:00Z",
        "posture": "collaborative",
        "turn_count": 1,
        "turn_budget": 1,
        "termination_reason": "complete",
        "mode": "server_assisted",
    }
    base.update(overrides)
    return base


class TestDelegationTemplate:
    def test_template_has_required_keys(self) -> None:
        expected_keys = {
            "included", "sample_size", "complete_count", "error_count",
            "blocked_count", "credential_block_count", "dirty_tree_block_count",
            "readable_secret_file_block_count", "sandbox_counts",
            "full_auto_count", "avg_commands_run", "avg_commands_run_observed_count",
        }
        assert set(_DELEGATION_TEMPLATE.keys()) == expected_keys


class TestSectionMatrix:
    def test_delegation_type_in_matrix(self) -> None:
        assert "delegation" in _SECTION_MATRIX

    def test_delegation_includes_delegation_section(self) -> None:
        assert _SECTION_MATRIX["delegation"]["delegation"] is True
        assert _SECTION_MATRIX["delegation"]["usage"] is True

    def test_report_version_envelope(self) -> None:
        """R5-I2: report_version stays 1.0.0 for additive changes."""
        events = [_make_delegation_event()]
        result = compute(events, 0, 0, "all")
        assert result["report_version"] == "1.0.0"


class TestUsageTemplate:
    def test_delegations_completed_total_field(self) -> None:
        assert "delegations_completed_total" in _USAGE_TEMPLATE


class TestComputeDelegation:
    def test_single_complete_event(self) -> None:
        events = [_make_delegation_event()]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["sample_size"] == 1
        assert result["delegation"]["complete_count"] == 1
        assert result["delegation"]["sandbox_counts"] == {"workspace-write": 1}

    def test_blocked_event(self) -> None:
        events = [_make_delegation_event(
            dispatched=False,
            termination_reason="blocked",
            credential_blocked=True,
            exit_code=None,
            commands_run_count=0,
        )]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["blocked_count"] == 1
        assert result["delegation"]["credential_block_count"] == 1

    def test_usage_counts_only_dispatched(self) -> None:
        """F3: delegations_completed_total counts only dispatched=true."""
        events = [
            _make_delegation_event(dispatched=True),
            _make_delegation_event(dispatched=True),
            _make_delegation_event(dispatched=False, termination_reason="blocked"),
        ]
        result = compute(events, 0, 0, "delegation")
        assert result["usage"]["delegations_completed_total"] == 2

    def test_all_type_includes_delegation(self) -> None:
        events = [_make_delegation_event()]
        result = compute(events, 0, 0, "all")
        assert result["delegation"]["included"] is True

    def test_delegation_excluded_from_invocations_total(self) -> None:
        """F9: invocations_completed_total excludes delegation."""
        events = [_make_delegation_event()]
        result = compute(events, 0, 0, "all")
        assert result["usage"]["invocations_completed_total"] == 0

    def test_delegation_excluded_from_aggregate_metrics(self) -> None:
        """F7/B14: Delegation does not widen active_utc_days or schema_version_counts."""
        consultation_event = {
            "schema_version": "0.1.0",
            "event": "consultation_outcome",
            "ts": "2026-03-06T12:00:00Z",
            "consultation_id": "c-uuid",
            "thread_id": None,
            "session_id": None,
            "posture": "collaborative",
            "mode": "server_assisted",
            "converged": True,
            "convergence_reason_code": "all_resolved",
            "termination_reason": "convergence",
            "turn_count": 3,
            "turn_budget": 8,
            "resolved_count": 2,
            "unresolved_count": 0,
            "emerged_count": 0,
            "scope_breach": False,
        }
        events = [_make_delegation_event(), consultation_event]
        result = compute(events, 0, 0, "all")
        assert result["usage"]["active_utc_days"] == 1
        assert result["usage"]["invocations_completed_total"] == 1

    def test_type_robust_sandbox_counts(self) -> None:
        """F13: Non-string sandbox value handled defensively."""
        events = [_make_delegation_event(sandbox=123)]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["sandbox_counts"] == {}

    def test_type_robust_full_auto(self) -> None:
        """F13: Non-bool full_auto handled defensively."""
        events = [_make_delegation_event(full_auto="yes")]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["full_auto_count"] == 0

    def test_type_robust_commands_run_count(self) -> None:
        """F13: Non-numeric commands_run_count handled defensively.
        R5-B6: None means 'no observations', not 0.0."""
        events = [_make_delegation_event(commands_run_count="five")]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["avg_commands_run"] is None

    def test_type_robust_dispatched_non_bool(self) -> None:
        """B18: dispatched=1 or dispatched='true' are not counted as dispatched."""
        events = [
            _make_delegation_event(dispatched=1),
            _make_delegation_event(dispatched="true"),
        ]
        result = compute(events, 0, 0, "delegation")
        assert result["usage"]["delegations_completed_total"] == 0

    def test_period_filtering_reduces_events(self) -> None:
        """B5: Period filtering with shared `now` reduces delegation_outcomes."""
        old_event = _make_delegation_event(ts="2025-01-01T00:00:00Z")
        recent_event = _make_delegation_event(ts="2026-03-06T12:00:00Z")
        events = [old_event, recent_event]
        result = compute(events, 0, 30, "delegation")
        assert result["delegation"]["sample_size"] == 1

    def test_mixed_type_avg_commands_run(self) -> None:
        """F13: avg_commands_run_observed_count reflects numeric subset only."""
        events = [
            _make_delegation_event(commands_run_count=10),
            _make_delegation_event(commands_run_count="invalid"),
            _make_delegation_event(commands_run_count=None, dispatched=False),
        ]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["avg_commands_run_observed_count"] == 1


class TestJsonFlag:
    def test_json_flag_accepted(self) -> None:
        """--json flag does not cause argparse error."""
        import subprocess
        script = str(Path(__file__).resolve().parent.parent / "scripts" / "compute_stats.py")
        proc = subprocess.run(
            [sys.executable, script, "--json", "/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        assert "unrecognized arguments" not in proc.stderr


class TestComputePlanning:
    """Tests for _compute_planning section."""

    def test_no_planned_events(self) -> None:
        """Events without question_shaped return zero counts."""
        dialogue = [_make_dialogue_event()]
        consultation = [_make_consultation_event()]
        result = _compute_planning(dialogue, consultation)
        assert result["plan_mode_total"] == 0
        assert result["no_plan_total"] == 2
        assert result["plan_mode_rate"] == 0.0  # 0/2 = 0%

    def test_planned_dialogue(self) -> None:
        """Dialogue with question_shaped=True counted in plan_mode."""
        planned = _make_dialogue_event(
            question_shaped=True,
            shape_confidence="high",
            assumptions_generated_count=3,
            ambiguity_count=1,
        )
        unplanned = _make_dialogue_event(consultation_id="test-002")
        result = _compute_planning([planned, unplanned], [])
        assert result["plan_mode_dialogue_count"] == 1
        assert result["plan_mode_total"] == 1
        assert result["no_plan_total"] == 1

    def test_planned_consultation(self) -> None:
        """Consultation with question_shaped=True counted."""
        planned = _make_consultation_event(
            question_shaped=True,
            shape_confidence="medium",
            assumptions_generated_count=2,
            ambiguity_count=0,
        )
        result = _compute_planning([], [planned])
        assert result["plan_mode_consultation_count"] == 1
        assert result["plan_mode_total"] == 1

    def test_shape_confidence_distribution(self) -> None:
        """shape_confidence_counts tallied across planned events."""
        events = [
            _make_dialogue_event(
                consultation_id=f"d-{i}",
                question_shaped=True,
                shape_confidence=conf,
                assumptions_generated_count=1,
                ambiguity_count=0,
            )
            for i, conf in enumerate(["high", "high", "medium", "low"])
        ]
        result = _compute_planning(events, [])
        assert result["shape_confidence_counts"] == {"high": 2, "medium": 1, "low": 1}

    def test_avg_assumptions_and_ambiguity(self) -> None:
        """Averages computed across planned events only."""
        events = [
            _make_dialogue_event(
                consultation_id="d-1",
                question_shaped=True,
                shape_confidence="high",
                assumptions_generated_count=4,
                ambiguity_count=2,
            ),
            _make_dialogue_event(
                consultation_id="d-2",
                question_shaped=True,
                shape_confidence="high",
                assumptions_generated_count=6,
                ambiguity_count=0,
            ),
            _make_dialogue_event(consultation_id="d-3"),  # no plan
        ]
        result = _compute_planning(events, [])
        assert result["avg_assumptions_generated"] == 5.0
        assert result["avg_ambiguity_count"] == 1.0

    def test_convergence_comparison(self) -> None:
        """Plan vs no-plan convergence rates for dialogues."""
        planned_converged = _make_dialogue_event(
            consultation_id="d-1",
            question_shaped=True, shape_confidence="high",
            assumptions_generated_count=2, ambiguity_count=0,
            converged=True,
        )
        planned_not = _make_dialogue_event(
            consultation_id="d-2",
            question_shaped=True, shape_confidence="medium",
            assumptions_generated_count=1, ambiguity_count=1,
            converged=False,
        )
        unplanned_converged = _make_dialogue_event(
            consultation_id="d-3", converged=True,
        )
        result = _compute_planning(
            [planned_converged, planned_not, unplanned_converged], []
        )
        assert result["plan_convergence_rate"] == 0.5  # 1/2
        assert result["no_plan_convergence_rate"] == 1.0  # 1/1


class TestComputeProvenance:
    """Tests for _compute_provenance section."""

    def test_no_provenance_events(self) -> None:
        """Events without provenance_unknown_count return defaults."""
        events = [_make_dialogue_event()]
        result = _compute_provenance(events)
        assert result["provenance_observed_events"] == 0
        assert result["avg_provenance_unknown"] is None

    def test_zero_unknown_count(self) -> None:
        """provenance_unknown_count=0 means all citations matched."""
        events = [_make_dialogue_event(provenance_unknown_count=0)]
        result = _compute_provenance(events)
        assert result["zero_unknown_count"] == 1
        assert result["provenance_observed_events"] == 1
        assert result["avg_provenance_unknown"] == 0.0

    def test_high_unknown_threshold(self) -> None:
        """provenance_unknown_count > 3 counted as high."""
        events = [
            _make_dialogue_event(consultation_id="d-1", provenance_unknown_count=5),
            _make_dialogue_event(consultation_id="d-2", provenance_unknown_count=2),
            _make_dialogue_event(consultation_id="d-3", provenance_unknown_count=0),
        ]
        result = _compute_provenance(events)
        assert result["high_unknown_count"] == 1
        assert result["zero_unknown_count"] == 1
        assert result["avg_provenance_unknown"] == pytest.approx(7 / 3)

    def test_null_excluded_from_observed(self) -> None:
        """None provenance_unknown_count (3c path) excluded from observed."""
        events = [
            _make_dialogue_event(consultation_id="d-1", provenance_unknown_count=2),
            _make_dialogue_event(consultation_id="d-2"),  # None — 3c path
        ]
        result = _compute_provenance(events)
        assert result["provenance_observed_events"] == 1
        assert result["provenance_missing_events"] == 1
        assert result["avg_provenance_unknown"] == 2.0

class TestComputeParseDiagnostics:
    """Tests for _compute_parse_diagnostics section."""

    def test_all_clean(self) -> None:
        events = [
            _make_dialogue_event(parse_truncated=False, parse_degraded=False),
            _make_dialogue_event(
                consultation_id="d-2",
                parse_truncated=False, parse_degraded=False,
            ),
        ]
        result = _compute_parse_diagnostics(events)
        assert result["clean_count"] == 2
        assert result["truncated_count"] == 0
        assert result["degraded_count"] == 0
        assert result["observed_events"] == 2

    def test_truncated_and_degraded(self) -> None:
        events = [
            _make_dialogue_event(parse_truncated=True, parse_degraded=False),
            _make_dialogue_event(
                consultation_id="d-2",
                parse_truncated=False, parse_degraded=True,
            ),
            _make_dialogue_event(
                consultation_id="d-3",
                parse_truncated=True, parse_degraded=True,
            ),
        ]
        result = _compute_parse_diagnostics(events)
        assert result["truncated_count"] == 2
        assert result["degraded_count"] == 2
        assert result["clean_count"] == 0  # none had both False

    def test_missing_fields_excluded(self) -> None:
        """Events without parse fields don't count as observed."""
        events = [
            _make_dialogue_event(parse_truncated=True, parse_degraded=False),
            _make_dialogue_event(consultation_id="d-2"),  # no parse fields
        ]
        result = _compute_parse_diagnostics(events)
        assert result["observed_events"] == 1
        assert result["truncated_count"] == 1


class TestTrackBSectionWiring:
    """Integration tests for Track B section matrix wiring."""

    def test_all_includes_new_sections(self) -> None:
        """--type all includes planning, provenance, parse_diagnostics."""
        events = [_make_dialogue_event(
            question_shaped=True, shape_confidence="high",
            assumptions_generated_count=3, ambiguity_count=1,
            provenance_unknown_count=0,
            parse_truncated=False, parse_degraded=False,
        )]
        result = compute(events, 0, 0, "all")
        assert "planning" in result
        assert result["planning"]["plan_mode_total"] == 1
        assert "provenance" in result
        assert result["provenance"]["provenance_observed_events"] == 1
        assert "parse_diagnostics" in result
        assert result["parse_diagnostics"]["observed_events"] == 1

    def test_dialogue_type_includes_new_sections(self) -> None:
        """--type dialogue includes planning, provenance, parse_diagnostics."""
        result = compute([], 0, 0, "dialogue")
        assert "planning" in result
        assert "provenance" in result
        assert "parse_diagnostics" in result

    def test_consultation_type_includes_planning(self) -> None:
        """--type consultation includes planning but not provenance/parse."""
        result = compute([], 0, 0, "consultation")
        assert "planning" in result
        assert result["provenance"]["provenance_observed_events"] == 0  # zeroed
        assert result["parse_diagnostics"]["observed_events"] == 0  # zeroed

    def test_security_type_excludes_new_sections(self) -> None:
        """--type security excludes all new sections."""
        result = compute([], 0, 0, "security")
        assert result["planning"]["plan_mode_total"] == 0  # template default
        assert result["provenance"]["provenance_observed_events"] == 0


class TestComputeConsultation:
    """Tests for _compute_consultation section (Track E #7)."""

    def test_empty(self) -> None:
        result = _compute_consultation([])
        assert result["complete_count"] == 0
        assert result["thread_continuation_rate"] is None

    def test_basic_counts(self) -> None:
        events = [
            _make_consultation_event(termination_reason="complete"),
            _make_consultation_event(
                consultation_id="c-2",
                termination_reason="complete",
            ),
        ]
        result = _compute_consultation(events)
        assert result["complete_count"] == 2

    def test_termination_distribution(self) -> None:
        events = [
            _make_consultation_event(termination_reason="complete"),
            _make_consultation_event(
                consultation_id="c-2", termination_reason="error",
            ),
        ]
        result = _compute_consultation(events)
        assert result["termination_counts"] == {"complete": 1, "error": 1}

    def test_thread_continuation(self) -> None:
        """Thread continuation: same thread_id in 2+ events."""
        events = [
            _make_consultation_event(thread_id="thread-A"),
            _make_consultation_event(
                consultation_id="c-2", thread_id="thread-A",
            ),
            _make_consultation_event(
                consultation_id="c-3", thread_id="thread-B",
            ),
            _make_consultation_event(
                consultation_id="c-4", thread_id=None,
            ),
        ]
        result = _compute_consultation(events)
        # 2 events have thread-A (continuation), 1 has thread-B (single), 1 is None
        # Continuation count: events with a continued thread_id = 2
        assert result["thread_continuation_count"] == 2
        # Rate: continued / events with non-null thread_id = 2/3
        assert result["thread_continuation_rate"] == pytest.approx(2 / 3)

    def test_posture_distribution(self) -> None:
        events = [
            _make_consultation_event(posture="adversarial"),
            _make_consultation_event(
                consultation_id="c-2", posture="collaborative",
            ),
            _make_consultation_event(
                consultation_id="c-3", posture="collaborative",
            ),
        ]
        result = _compute_consultation(events)
        assert result["posture_counts"] == {"adversarial": 1, "collaborative": 2}


class TestConsultationSource:
    """Tests for consultation_source discriminator."""

    def test_source_distribution(self) -> None:
        events = [
            _make_consultation_event(consultation_source="codex"),
            _make_consultation_event(
                consultation_id="c-2", consultation_source="codex",
            ),
            _make_consultation_event(
                consultation_id="c-3", consultation_source="reviewer",
            ),
            _make_consultation_event(consultation_id="c-4"),  # no source (legacy)
        ]
        result = _compute_consultation(events)
        assert result["source_counts"] == {
            "codex": 2, "reviewer": 1, "unknown": 1,
        }


class TestListThreads:
    """Tests for _list_threads function."""

    def test_empty(self) -> None:
        from scripts.compute_stats import _list_threads
        result = _list_threads([])
        assert result == []

    def test_groups_by_thread_id(self) -> None:
        from scripts.compute_stats import _list_threads
        events = [
            _make_consultation_event(
                thread_id="tid-A", ts="2026-03-17T10:00:00Z",
            ),
            _make_consultation_event(
                consultation_id="c-2",
                thread_id="tid-A", ts="2026-03-17T11:00:00Z",
            ),
            _make_dialogue_event(
                thread_id="tid-B", ts="2026-03-17T09:00:00Z",
            ),
        ]
        result = _list_threads(events)
        assert len(result) == 2
        # Sorted by last_ts descending
        assert result[0]["thread_id"] == "tid-A"
        assert result[0]["event_count"] == 2
        assert result[0]["last_ts"] == "2026-03-17T11:00:00Z"
        assert result[1]["thread_id"] == "tid-B"
        assert result[1]["event_count"] == 1

    def test_null_thread_id_excluded(self) -> None:
        from scripts.compute_stats import _list_threads
        events = [
            _make_consultation_event(thread_id=None),
            _make_consultation_event(
                consultation_id="c-2", thread_id="tid-A",
            ),
        ]
        result = _list_threads(events)
        assert len(result) == 1
        assert result[0]["thread_id"] == "tid-A"

    def test_event_types_collected(self) -> None:
        from scripts.compute_stats import _list_threads
        events = [
            _make_consultation_event(thread_id="tid-A"),
            _make_dialogue_event(thread_id="tid-A"),
        ]
        result = _list_threads(events)
        assert set(result[0]["event_types"]) == {"consultation_outcome", "dialogue_outcome"}

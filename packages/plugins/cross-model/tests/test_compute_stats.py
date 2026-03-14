"""Tests for compute_stats delegation support."""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.compute_stats import (
    compute,
    _DELEGATION_TEMPLATE,
    _SECTION_MATRIX,
    _USAGE_TEMPLATE,
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

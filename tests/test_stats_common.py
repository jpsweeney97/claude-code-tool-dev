"""Tests for packages/plugins/cross-model/scripts/stats_common.py.

Tests shared primitives: period parsing, timestamp parsing, time-window
filtering, security tier extraction, safe integer access, observed
averages, boolean slot counting, and low-seed reason aggregation.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import
# ---------------------------------------------------------------------------

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "plugins"
    / "cross-model"
    / "scripts"
    / "stats_common.py"
)
SPEC = importlib.util.spec_from_file_location("stats_common", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["stats_common"] = MODULE  # register so downstream imports resolve to this instance
SPEC.loader.exec_module(MODULE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 2, 27, 12, 0, 0, tzinfo=timezone.utc)


def _make_event(ts: str, **kwargs: object) -> dict:
    """Build a minimal event dict with a timestamp."""
    d: dict = {"ts": ts}
    d.update(kwargs)
    return d


# ---------------------------------------------------------------------------
# TestParsePeriodDays
# ---------------------------------------------------------------------------


class TestParsePeriodDays:
    def test_plain_number(self) -> None:
        assert MODULE.parse_period_days("30") == 30

    def test_number_with_d_suffix(self) -> None:
        assert MODULE.parse_period_days("30d") == 30

    def test_zero(self) -> None:
        assert MODULE.parse_period_days("0") == 0

    def test_all_keyword(self) -> None:
        assert MODULE.parse_period_days("all") == 0

    def test_all_keyword_uppercase(self) -> None:
        assert MODULE.parse_period_days("ALL") == 0

    def test_whitespace_stripped(self) -> None:
        assert MODULE.parse_period_days("  7d  ") == 7

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            MODULE.parse_period_days("")

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            MODULE.parse_period_days("-5")


# ---------------------------------------------------------------------------
# TestParseTsUtc
# ---------------------------------------------------------------------------


class TestParseTsUtc:
    def test_second_precision(self) -> None:
        result = MODULE.parse_ts_utc("2026-02-27T22:15:00Z")
        assert result is not None
        assert result.year == 2026
        assert result.month == 2
        assert result.hour == 22
        assert result.second == 0

    def test_microsecond_precision(self) -> None:
        result = MODULE.parse_ts_utc("2026-02-27T22:15:00.123456Z")
        assert result is not None
        assert result.microsecond == 123456

    def test_timezone_aware(self) -> None:
        result = MODULE.parse_ts_utc("2026-02-27T22:15:00Z")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_bad_string_returns_none(self) -> None:
        assert MODULE.parse_ts_utc("not-a-date") is None

    def test_empty_returns_none(self) -> None:
        assert MODULE.parse_ts_utc("") is None

    def test_none_returns_none(self) -> None:
        assert MODULE.parse_ts_utc(None) is None

    def test_non_string_returns_none(self) -> None:
        assert MODULE.parse_ts_utc(12345) is None

    def test_non_utc_offset_returns_none(self) -> None:
        """Non-UTC offset timestamps are rejected, not silently re-labeled."""
        assert MODULE.parse_ts_utc("2026-02-27T12:00:00+05:00") is None

    def test_explicit_utc_offset_accepted(self) -> None:
        """Explicit +00:00 offset is accepted as UTC."""
        result = MODULE.parse_ts_utc("2026-02-27T12:00:00+00:00")
        assert result is not None
        assert result.hour == 12
        assert result.tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# TestFilterByPeriod
# ---------------------------------------------------------------------------


class TestFilterByPeriod:
    def test_normal_window(self) -> None:
        events = [
            _make_event("2026-02-26T12:00:00Z"),  # 1 day ago — in window
            _make_event("2026-02-20T12:00:00Z"),  # 7 days ago — out
        ]
        result = MODULE.filter_by_period(events, 3, now=NOW)
        assert len(result.events) == 1
        assert result.skipped == 0

    def test_period_zero_returns_all(self) -> None:
        events = [
            _make_event("2020-01-01T00:00:00Z"),
            _make_event("2026-02-27T00:00:00Z"),
        ]
        result = MODULE.filter_by_period(events, 0, now=NOW)
        assert len(result.events) == 2
        assert result.skipped == 0
        assert result.window_start == ""
        assert result.window_end == ""

    def test_corrupt_timestamps_skipped(self) -> None:
        events = [
            _make_event("2026-02-27T00:00:00Z"),
            {"ts": "garbage"},
            {"no_ts_field": True},
        ]
        result = MODULE.filter_by_period(events, 7, now=NOW)
        assert len(result.events) == 1
        assert result.skipped == 2

    def test_empty_input(self) -> None:
        result = MODULE.filter_by_period([], 7, now=NOW)
        assert result.events == []
        assert result.skipped == 0

    def test_boundary_exactly_at_window_start(self) -> None:
        """Event exactly at window_start is included (start <= ts)."""
        start = NOW - timedelta(days=7)
        ts = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        result = MODULE.filter_by_period([_make_event(ts)], 7, now=NOW)
        assert len(result.events) == 1

    def test_boundary_exactly_at_now(self) -> None:
        """Event exactly at now is included (ts <= now)."""
        ts = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
        result = MODULE.filter_by_period([_make_event(ts)], 7, now=NOW)
        assert len(result.events) == 1

    def test_boundary_mixed_second_and_microsecond(self) -> None:
        """Both second-precision and microsecond-precision timestamps work."""
        events = [
            _make_event("2026-02-27T00:00:00Z"),
            _make_event("2026-02-27T00:00:00.500000Z"),
        ]
        result = MODULE.filter_by_period(events, 7, now=NOW)
        assert len(result.events) == 2

    def test_boundary_1us_before_window_start_excluded(self) -> None:
        """Event 1 microsecond before window_start is excluded."""
        start = NOW - timedelta(days=7)
        just_before = start - timedelta(microseconds=1)
        ts = just_before.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        result = MODULE.filter_by_period([_make_event(ts)], 7, now=NOW)
        assert len(result.events) == 0

    def test_boundary_1us_after_now_excluded(self) -> None:
        """Event 1 microsecond after now is excluded."""
        just_after = NOW + timedelta(microseconds=1)
        ts = just_after.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        result = MODULE.filter_by_period([_make_event(ts)], 7, now=NOW)
        assert len(result.events) == 0


# ---------------------------------------------------------------------------
# TestParseSecurityTier
# ---------------------------------------------------------------------------


class TestParseSecurityTier:
    def test_strict_tier(self) -> None:
        assert MODULE.parse_security_tier("strict:pat") == "strict"

    def test_contextual_tier(self) -> None:
        assert MODULE.parse_security_tier("contextual:pat") == "contextual"

    def test_broad_tier(self) -> None:
        assert MODULE.parse_security_tier("broad:pat") == "broad"

    def test_empty_returns_unknown(self) -> None:
        assert MODULE.parse_security_tier("") == "unknown"

    def test_no_colon_returns_full_string(self) -> None:
        assert MODULE.parse_security_tier("something") == "something"

    def test_non_string_returns_unknown(self) -> None:
        assert MODULE.parse_security_tier(42) == "unknown"

    def test_none_returns_unknown(self) -> None:
        assert MODULE.parse_security_tier(None) == "unknown"

    def test_list_returns_unknown(self) -> None:
        assert MODULE.parse_security_tier(["strict:pat"]) == "unknown"


# ---------------------------------------------------------------------------
# TestSafeNonnegInt
# ---------------------------------------------------------------------------


class TestSafeNonnegInt:
    def test_valid_int(self) -> None:
        assert MODULE.safe_nonneg_int({"x": 5}, "x") == 5

    def test_zero_is_valid(self) -> None:
        assert MODULE.safe_nonneg_int({"x": 0}, "x") == 0

    def test_bool_returns_none(self) -> None:
        assert MODULE.safe_nonneg_int({"x": True}, "x") is None

    def test_none_value_returns_none(self) -> None:
        assert MODULE.safe_nonneg_int({"x": None}, "x") is None

    def test_negative_returns_none(self) -> None:
        assert MODULE.safe_nonneg_int({"x": -1}, "x") is None

    def test_missing_field_returns_none(self) -> None:
        assert MODULE.safe_nonneg_int({}, "x") is None

    def test_float_returns_none(self) -> None:
        assert MODULE.safe_nonneg_int({"x": 3.14}, "x") is None


# ---------------------------------------------------------------------------
# TestObservedAvg
# ---------------------------------------------------------------------------


class TestObservedAvg:
    def test_all_present(self) -> None:
        events = [{"x": 10}, {"x": 20}, {"x": 30}]
        avg, count = MODULE.observed_avg(events, "x")
        assert avg == 20.0
        assert count == 3

    def test_some_none(self) -> None:
        events = [{"x": 10}, {"y": 5}, {"x": 30}]
        avg, count = MODULE.observed_avg(events, "x")
        assert avg == 20.0
        assert count == 2

    def test_all_none(self) -> None:
        events = [{"y": 1}, {"y": 2}]
        avg, count = MODULE.observed_avg(events, "x")
        assert avg is None
        assert count == 0

    def test_empty_events(self) -> None:
        avg, count = MODULE.observed_avg([], "x")
        assert avg is None
        assert count == 0


# ---------------------------------------------------------------------------
# TestObservedBoolSlots
# ---------------------------------------------------------------------------


class TestObservedBoolSlots:
    def test_all_bools(self) -> None:
        events = [{"a": True, "b": False}, {"a": False, "b": True}]
        true_count, observed, missing = MODULE.observed_bool_slots(events, "a", "b")
        assert true_count == 2
        assert observed == 4
        assert missing == 0

    def test_some_missing(self) -> None:
        events = [{"a": True}, {"b": False}]
        true_count, observed, missing = MODULE.observed_bool_slots(events, "a", "b")
        assert true_count == 1
        assert observed == 2
        assert missing == 2  # 2 events * 2 fields - 2 observed

    def test_all_missing(self) -> None:
        events = [{"x": 1}, {"x": 2}]
        true_count, observed, missing = MODULE.observed_bool_slots(events, "a", "b")
        assert true_count == 0
        assert observed == 0
        assert missing == 4

    def test_non_bool_values_not_counted(self) -> None:
        events = [{"a": 1}, {"a": "yes"}, {"a": None}]
        true_count, observed, missing = MODULE.observed_bool_slots(events, "a")
        assert true_count == 0
        assert observed == 0
        assert missing == 3


# ---------------------------------------------------------------------------
# TestAggregateLowSeedReasons
# ---------------------------------------------------------------------------


class TestAggregateLowSeedReasons:
    def test_normal_aggregation(self) -> None:
        events = [
            {"seed_confidence": "low", "low_seed_confidence_reasons": ["reason_a", "reason_b"]},
            {"seed_confidence": "low", "low_seed_confidence_reasons": ["reason_a"]},
        ]
        result = MODULE.aggregate_low_seed_reasons(events)
        assert result["event_count"] == 2
        assert result["reason_counts"]["reason_a"] == 2
        assert result["reason_counts"]["reason_b"] == 1
        assert result["mentions_total"] == 3
        assert result["no_reason_count"] == 0

    def test_per_event_dedup(self) -> None:
        """Same reason twice in one event is counted once per event."""
        events = [
            {"seed_confidence": "low", "low_seed_confidence_reasons": ["dup", "dup", "dup"]},
        ]
        result = MODULE.aggregate_low_seed_reasons(events)
        assert result["reason_counts"]["dup"] == 1
        assert result["mentions_total"] == 1

    def test_no_low_seed_events(self) -> None:
        events = [
            {"seed_confidence": "normal"},
            {"seed_confidence": "high"},
        ]
        result = MODULE.aggregate_low_seed_reasons(events)
        assert result["event_count"] == 0
        assert result["reason_counts"] == {}
        assert result["mentions_total"] == 0
        assert result["no_reason_count"] == 0

    def test_low_seed_no_reasons(self) -> None:
        """Low-seed event with no reasons field increments no_reason_count."""
        events = [
            {"seed_confidence": "low"},
        ]
        result = MODULE.aggregate_low_seed_reasons(events)
        assert result["event_count"] == 1
        assert result["no_reason_count"] == 1

    def test_low_seed_empty_reasons(self) -> None:
        """Low-seed event with empty reasons list increments no_reason_count."""
        events = [
            {"seed_confidence": "low", "low_seed_confidence_reasons": []},
        ]
        result = MODULE.aggregate_low_seed_reasons(events)
        assert result["event_count"] == 1
        assert result["no_reason_count"] == 1

    def test_unhashable_reasons_skipped(self) -> None:
        """Non-string entries (e.g. dicts) in reasons are filtered out."""
        events = [
            {
                "seed_confidence": "low",
                "low_seed_confidence_reasons": [{"nested": "dict"}, "valid_reason"],
            },
        ]
        result = MODULE.aggregate_low_seed_reasons(events)
        assert result["reason_counts"] == {"valid_reason": 1}
        assert result["mentions_total"] == 1

    def test_all_unhashable_reasons_counts_as_no_reason(self) -> None:
        """If all reasons are non-string, event counts as no_reason."""
        events = [
            {
                "seed_confidence": "low",
                "low_seed_confidence_reasons": [{"nested": "dict"}, 42],
            },
        ]
        result = MODULE.aggregate_low_seed_reasons(events)
        assert result["event_count"] == 1
        assert result["no_reason_count"] == 1

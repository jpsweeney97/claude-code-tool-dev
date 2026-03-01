#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Shared primitives for cross-model analytics computation.

Provides filtering, parsing, and aggregation utilities used by
compute_stats.py to produce analytics output from event log data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FilterResult:
    """Result of filtering events by time period."""

    events: list[dict]
    skipped: int
    window_start: str  # ISO 8601, or "" for all-time
    window_end: str


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_period_days(value: str) -> int:
    """Parse a period string into days.

    Accepts "30", "30d", "0", or "all".
    Returns 0 for all-time (no filtering).

    Raises ValueError for non-numeric or negative values.
    """
    stripped = value.strip().lower()
    if stripped == "all":
        return 0
    if stripped.endswith("d"):
        stripped = stripped[:-1]
    days = int(stripped)
    if days < 0:
        raise ValueError(f"period_days must be non-negative, got {days}")
    return days


def parse_ts_utc(ts_string: str) -> datetime | None:
    """Parse an ISO 8601 UTC timestamp string to a datetime.

    Handles ISO 8601 timestamps with or without microseconds, trailing Z
    stripped before parsing. Rejects non-UTC offset timestamps (e.g.
    "+05:00") — returns None rather than silently re-labeling.

    Returns None for unparseable timestamps (matches skip-malformed pattern).
    Returns timezone-aware UTC datetimes with full precision preserved.
    """
    if not isinstance(ts_string, str) or not ts_string:
        return None
    try:
        cleaned = ts_string.rstrip("Z")
        dt = datetime.fromisoformat(cleaned)
        # Reject non-UTC offsets rather than silently re-labeling
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(None) != timedelta(0):
            return None
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def filter_by_period(
    events: list[dict],
    period_days: int,
    now: datetime | None = None,
) -> FilterResult:
    """Filter events to a closed [start, now] time window.

    Args:
        events: List of event dicts, each expected to have a "ts" key.
        period_days: Number of days to look back. 0 means all-time (no filtering).
        now: Reference time for window end. Defaults to current UTC time.

    Returns:
        FilterResult with matching events, skip count, and window boundaries.

    Boundary semantics: closed interval — events exactly at start or now
    are included. Events with unparseable timestamps are skipped.
    """
    if period_days == 0:
        return FilterResult(events=list(events), skipped=0, window_start="", window_end="")

    if now is None:
        now = datetime.now(timezone.utc)

    start = now - timedelta(days=period_days)
    matched: list[dict] = []
    skipped = 0

    for event in events:
        ts = parse_ts_utc(event.get("ts", ""))
        if ts is None:
            skipped += 1
            continue
        if start <= ts <= now:
            matched.append(event)

    return FilterResult(
        events=matched,
        skipped=skipped,
        window_start=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        window_end=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------------------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------------------


def parse_security_tier(reason: object) -> str:
    """Extract security tier from a block reason string.

    "strict:<pattern>" -> "strict"; "" or missing or non-string -> "unknown".
    """
    if not isinstance(reason, str) or not reason:
        return "unknown"
    colon_idx = reason.find(":")
    if colon_idx > 0:
        return reason[:colon_idx]
    return reason


def safe_nonneg_int(event: dict, field: str) -> int | None:
    """Extract a non-negative integer field from an event dict.

    Returns the int value if the field exists and is a non-negative int
    (excluding bools). Returns None otherwise — no default to avoid
    silently deflating observed-denominator averages.
    """
    value = event.get(field)
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def observed_avg(events: list[dict], field: str) -> tuple[float | None, int]:
    """Compute per-field observed-denominator average.

    Calls safe_nonneg_int for each event. Events where the field is
    absent or invalid are excluded from both numerator and denominator.

    Returns (average, observed_count). Average is None when observed_count is 0.
    """
    total = 0
    observed = 0
    for event in events:
        value = safe_nonneg_int(event, field)
        if value is not None:
            total += value
            observed += 1
    if observed == 0:
        return (None, 0)
    return (total / observed, observed)


def observed_bool_slots(
    events: list[dict], *fields: str
) -> tuple[int, int, int]:
    """Count boolean field observations across events and fields.

    Returns (true_count, observed_slots, missing_slots).
    - observed_slots: count of (event, field) pairs where value is a bool.
    - missing_slots: total_possible - observed_slots.
    - total_possible: len(events) * len(fields).
    """
    total_possible = len(events) * len(fields)
    true_count = 0
    observed_slots = 0

    for event in events:
        for field in fields:
            value = event.get(field)
            if isinstance(value, bool):
                observed_slots += 1
                if value:
                    true_count += 1

    missing_slots = total_possible - observed_slots
    return (true_count, observed_slots, missing_slots)


def aggregate_low_seed_reasons(events: list[dict]) -> dict:
    """Aggregate low_seed_confidence_reasons across events with per-event dedup.

    Only events with seed_confidence == "low" are included.
    Per-event dedup: duplicate reasons within a single event are counted once.

    Returns:
        {"event_count": int, "reason_counts": dict, "mentions_total": int,
         "no_reason_count": int}
    """
    event_count = 0
    reason_counts: dict[str, int] = {}
    mentions_total = 0
    no_reason_count = 0

    for event in events:
        if event.get("seed_confidence") != "low":
            continue
        event_count += 1

        reasons = event.get("low_seed_confidence_reasons")
        if not reasons or not isinstance(reasons, list):
            no_reason_count += 1
            continue

        # Per-event dedup: skip non-string entries (unhashable dicts, etc.)
        unique_reasons = set(r for r in reasons if isinstance(r, str))
        if not unique_reasons:
            no_reason_count += 1
            continue

        for reason in unique_reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            mentions_total += 1

    return {
        "event_count": event_count,
        "reason_counts": reason_counts,
        "mentions_total": mentions_total,
        "no_reason_count": no_reason_count,
    }

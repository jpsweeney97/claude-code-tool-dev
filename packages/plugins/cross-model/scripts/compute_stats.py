#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Analytics computation for cross-model consultation statistics.

Reads classified events from the event log, applies validation and
time-period filtering, computes section-level metrics, and produces
a structured JSON report.

Usage as library:
    from compute_stats import compute

Usage as script:
    python3 compute_stats.py [--period 30] [--type all] [path]
"""

from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Literal
from pathlib import Path

if __package__:
    import scripts.read_events as read_events
    import scripts.stats_common as stats_common
    from scripts.event_schema import STRUCTURED_EVENT_TYPES
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import read_events  # type: ignore[import-not-found,no-redef]
    import stats_common  # type: ignore[import-not-found,no-redef]
    from event_schema import STRUCTURED_EVENT_TYPES  # type: ignore[import-not-found,no-redef]


# ---------------------------------------------------------------------------
# Template dicts — canonical shapes for each report section.
# Deep-copied before use; callers must not mutate these directly.
# ---------------------------------------------------------------------------

_USAGE_TEMPLATE: dict = {
    "included": False,
    "dialogues_completed_total": 0,
    "consultations_completed_total": 0,
    "invocations_completed_total": 0,
    "delegations_completed_total": 0,
    "tool_calls_success_total": 0,
    "tool_calls_blocked_total": 0,
    "shadow_count": 0,
    "active_utc_days": 0,
    "posture_counts": {},
    "schema_version_counts": {},
}

_DIALOGUE_TEMPLATE: dict = {
    "included": False,
    "converged_count": 0,
    "not_converged_count": 0,
    "convergence_observed_count": 0,
    "convergence_rate": None,
    "avg_turn_count": None,
    "avg_turn_count_observed_count": 0,
    "avg_turns_to_convergence": None,
    "avg_turns_to_convergence_observed_count": 0,
    "avg_scout_count": None,
    "avg_scout_count_observed_count": 0,
    "avg_resolved_count": None,
    "avg_resolved_count_observed_count": 0,
    "mode_counts": {},
    "termination_counts": {},
    "convergence_reason_counts": {},
    "sample_size": 0,
}

_CONTEXT_TEMPLATE: dict = {
    "included": False,
    "seed_confidence_counts": {},
    "low_seed_event_count": 0,
    "low_seed_reason_counts": {},
    "low_seed_mentions_total": 0,
    "low_seed_no_reason_count": 0,
    "avg_citations_total": None,
    "avg_citations_total_observed_count": 0,
    "avg_unique_files_total": None,
    "avg_unique_files_total_observed_count": 0,
    "retry_true_count": 0,
    "retry_observed_slots": 0,
    "retry_missing_slots": 0,
    "sample_size": 0,
}

_SECURITY_TEMPLATE: dict = {
    "included": False,
    "block_count": 0,
    "tier_counts": {},
    "shadow_count": 0,
    "dispatch_block_rate": None,
    "blocks_per_completed_invocation": None,
    "sample_size": 0,
}

_DELEGATION_TEMPLATE: dict = {
    "included": False,
    "sample_size": 0,
    "complete_count": 0,
    "error_count": 0,
    "blocked_count": 0,
    "credential_block_count": 0,
    "dirty_tree_block_count": 0,
    "readable_secret_file_block_count": 0,
    "sandbox_counts": {},
    "full_auto_count": 0,
    "avg_commands_run": None,
    "avg_commands_run_observed_count": 0,
}

_PLANNING_TEMPLATE: dict = {
    "plan_mode_dialogue_count": 0,
    "plan_mode_consultation_count": 0,
    "plan_mode_total": 0,
    "no_plan_total": 0,
    "plan_mode_rate": None,
    "shape_confidence_counts": {},
    "avg_assumptions_generated": None,
    "avg_ambiguity_count": None,
    "plan_convergence_rate": None,
    "no_plan_convergence_rate": None,
}


_PROVENANCE_TEMPLATE: dict = {
    "avg_provenance_unknown": None,
    "zero_unknown_count": 0,
    "high_unknown_count": 0,
    "provenance_observed_events": 0,
    "provenance_missing_events": 0,
}

_PARSE_DIAGNOSTICS_TEMPLATE: dict = {
    "truncated_count": 0,
    "degraded_count": 0,
    "clean_count": 0,
    "observed_events": 0,
}

# ---------------------------------------------------------------------------
# Section computation functions
# ---------------------------------------------------------------------------


def _compute_usage(
    dialogue_outcomes: list[dict],
    consultation_outcomes: list[dict],
    delegation_outcomes: list[dict],
    consultations: list[dict],
    blocks: list[dict],
    shadows: list[dict],
) -> dict:
    """Compute the usage section from classified event lists."""
    result = copy.deepcopy(_USAGE_TEMPLATE)
    result["included"] = True

    result["dialogues_completed_total"] = len(dialogue_outcomes)
    result["consultations_completed_total"] = len(consultation_outcomes)
    result["invocations_completed_total"] = len(dialogue_outcomes) + len(consultation_outcomes)
    # F3: Count only dispatched=true events
    result["delegations_completed_total"] = sum(
        1 for e in delegation_outcomes if e.get("dispatched") is True
    )
    result["tool_calls_success_total"] = len(consultations)
    result["tool_calls_blocked_total"] = len(blocks)
    result["shadow_count"] = len(shadows)

    # Active UTC days — distinct calendar dates from outcome events only
    outcome_events = dialogue_outcomes + consultation_outcomes
    utc_dates: set[str] = set()
    for event in outcome_events:
        dt = stats_common.parse_ts_utc(event.get("ts", ""))
        if dt is not None:
            utc_dates.add(dt.strftime("%Y-%m-%d"))
    result["active_utc_days"] = len(utc_dates)

    # Posture and schema_version from outcome events only
    posture_counter: Counter[str] = Counter()
    version_counter: Counter[str] = Counter()
    for event in outcome_events:
        posture = event.get("posture")
        if posture is not None:
            posture_counter[posture] += 1
        version = event.get("schema_version")
        if version is not None:
            version_counter[version] += 1
    result["posture_counts"] = dict(posture_counter)
    result["schema_version_counts"] = dict(version_counter)

    return result


def _compute_dialogue(dialogue_outcomes: list[dict]) -> dict:
    """Compute the dialogue section from dialogue_outcome events."""
    result = copy.deepcopy(_DIALOGUE_TEMPLATE)
    result["included"] = True
    result["sample_size"] = len(dialogue_outcomes)

    # Convergence counts — only events where converged is a bool
    converged_count = 0
    not_converged_count = 0
    for event in dialogue_outcomes:
        c = event.get("converged")
        if c is True:
            converged_count += 1
        elif c is False:
            not_converged_count += 1

    result["converged_count"] = converged_count
    result["not_converged_count"] = not_converged_count
    convergence_observed = converged_count + not_converged_count
    result["convergence_observed_count"] = convergence_observed
    result["convergence_rate"] = (
        converged_count / convergence_observed if convergence_observed > 0 else None
    )

    # Averages via observed_avg
    avg_tc, obs_tc = stats_common.observed_avg(dialogue_outcomes, "turn_count")
    result["avg_turn_count"] = avg_tc
    result["avg_turn_count_observed_count"] = obs_tc

    avg_sc, obs_sc = stats_common.observed_avg(dialogue_outcomes, "scout_count")
    result["avg_scout_count"] = avg_sc
    result["avg_scout_count_observed_count"] = obs_sc

    avg_rc, obs_rc = stats_common.observed_avg(dialogue_outcomes, "resolved_count")
    result["avg_resolved_count"] = avg_rc
    result["avg_resolved_count_observed_count"] = obs_rc

    # avg_turns_to_convergence — converged-only events
    converged_events = [e for e in dialogue_outcomes if e.get("converged") is True]
    avg_ttc, obs_ttc = stats_common.observed_avg(converged_events, "turn_count")
    result["avg_turns_to_convergence"] = avg_ttc
    result["avg_turns_to_convergence_observed_count"] = obs_ttc

    # Counter dicts
    result["mode_counts"] = dict(Counter(
        event.get("mode") for event in dialogue_outcomes if event.get("mode") is not None
    ))
    result["termination_counts"] = dict(Counter(
        event.get("termination_reason")
        for event in dialogue_outcomes
        if event.get("termination_reason") is not None
    ))
    result["convergence_reason_counts"] = dict(Counter(
        event.get("convergence_reason_code")
        for event in dialogue_outcomes
        if event.get("convergence_reason_code") is not None
    ))

    return result


def _compute_context(dialogue_outcomes: list[dict]) -> dict:
    """Compute the context section from dialogue_outcome events."""
    result = copy.deepcopy(_CONTEXT_TEMPLATE)
    result["included"] = True
    result["sample_size"] = len(dialogue_outcomes)

    # Seed confidence counts
    result["seed_confidence_counts"] = dict(Counter(
        event.get("seed_confidence")
        for event in dialogue_outcomes
        if event.get("seed_confidence") is not None
    ))

    # Low seed aggregation
    low_seed = stats_common.aggregate_low_seed_reasons(dialogue_outcomes)
    result["low_seed_event_count"] = low_seed["event_count"]
    result["low_seed_reason_counts"] = low_seed["reason_counts"]
    result["low_seed_mentions_total"] = low_seed["mentions_total"]
    result["low_seed_no_reason_count"] = low_seed["no_reason_count"]

    # Citation and file averages
    avg_ct, obs_ct = stats_common.observed_avg(dialogue_outcomes, "citations_total")
    result["avg_citations_total"] = avg_ct
    result["avg_citations_total_observed_count"] = obs_ct

    avg_uf, obs_uf = stats_common.observed_avg(dialogue_outcomes, "unique_files_total")
    result["avg_unique_files_total"] = avg_uf
    result["avg_unique_files_total_observed_count"] = obs_uf

    # Gatherer retry
    true_c, obs_s, miss_s = stats_common.observed_bool_slots(
        dialogue_outcomes, "gatherer_a_retry", "gatherer_b_retry"
    )
    result["retry_true_count"] = true_c
    result["retry_observed_slots"] = obs_s
    result["retry_missing_slots"] = miss_s

    return result


def _compute_security(
    blocks: list[dict],
    shadows: list[dict],
    consultations: list[dict],
    invocations_completed_total: int,
) -> dict:
    """Compute the security section from guard events."""
    result = copy.deepcopy(_SECURITY_TEMPLATE)
    result["included"] = True

    block_count = len(blocks)
    result["block_count"] = block_count
    result["shadow_count"] = len(shadows)
    result["sample_size"] = len(blocks) + len(shadows)

    # Tier counts
    result["tier_counts"] = dict(Counter(
        stats_common.parse_security_tier(block.get("reason", ""))
        for block in blocks
    ))

    # Dispatch block rate: blocks / (blocks + consultations)
    dispatch_denom = block_count + len(consultations)
    result["dispatch_block_rate"] = (
        block_count / dispatch_denom if dispatch_denom > 0 else None
    )

    # Blocks per completed invocation
    result["blocks_per_completed_invocation"] = (
        block_count / invocations_completed_total
        if invocations_completed_total > 0
        else None
    )

    return result


def _compute_delegation(delegation_outcomes: list[dict]) -> dict:
    """Compute the delegation section from delegation_outcome events.

    F13: Type-robust — handles non-canonical types defensively.
    """
    result = copy.deepcopy(_DELEGATION_TEMPLATE)
    result["included"] = True
    result["sample_size"] = len(delegation_outcomes)

    for event in delegation_outcomes:
        reason = event.get("termination_reason")
        if reason == "complete":
            result["complete_count"] += 1
        elif reason == "error":
            result["error_count"] += 1
        elif reason == "blocked":
            result["blocked_count"] += 1

        if event.get("credential_blocked"):
            result["credential_block_count"] += 1
        if event.get("dirty_tree_blocked"):
            result["dirty_tree_block_count"] += 1
        if event.get("readable_secret_file_blocked"):
            result["readable_secret_file_block_count"] += 1

        sandbox = event.get("sandbox")
        if isinstance(sandbox, str) and sandbox:
            result["sandbox_counts"][sandbox] = result["sandbox_counts"].get(sandbox, 0) + 1

        if event.get("full_auto") is True:
            result["full_auto_count"] += 1

    # Average commands run (dispatched events only)
    dispatched = [e for e in delegation_outcomes if e.get("dispatched") is True]
    numeric_dispatched = [
        e for e in dispatched
        if isinstance(e.get("commands_run_count"), (int, float))
    ]
    avg_cmd, obs_cmd = stats_common.observed_avg(numeric_dispatched, "commands_run_count")
    result["avg_commands_run"] = avg_cmd
    result["avg_commands_run_observed_count"] = obs_cmd

    return result


def _compute_planning(
    dialogue_outcomes: list[dict],
    consultation_outcomes: list[dict],
) -> dict:
    """Compute planning effectiveness metrics.

    Consumes events where question_shaped is set (schema 0.3.0+).
    Compares convergence rates for planned vs unplanned dialogues.
    """
    result = copy.deepcopy(_PLANNING_TEMPLATE)

    all_events = dialogue_outcomes + consultation_outcomes
    planned: list[dict] = []
    unplanned: list[dict] = []

    for event in all_events:
        if event.get("question_shaped") is not None:
            planned.append(event)
        else:
            unplanned.append(event)

    plan_dialogues = [e for e in planned if e.get("event") == "dialogue_outcome"]
    plan_consultations = [e for e in planned if e.get("event") == "consultation_outcome"]

    result["plan_mode_dialogue_count"] = len(plan_dialogues)
    result["plan_mode_consultation_count"] = len(plan_consultations)
    result["plan_mode_total"] = len(planned)
    result["no_plan_total"] = len(unplanned)

    total = len(planned) + len(unplanned)
    if total > 0:
        result["plan_mode_rate"] = len(planned) / total

    # shape_confidence distribution across planned events
    conf_counts: dict[str, int] = {}
    for event in planned:
        conf = event.get("shape_confidence")
        if isinstance(conf, str):
            conf_counts[conf] = conf_counts.get(conf, 0) + 1
    result["shape_confidence_counts"] = conf_counts

    # Averages across planned events
    assumptions_vals = [
        event["assumptions_generated_count"]
        for event in planned
        if isinstance(event.get("assumptions_generated_count"), int)
    ]
    if assumptions_vals:
        result["avg_assumptions_generated"] = sum(assumptions_vals) / len(assumptions_vals)

    ambiguity_vals = [
        event["ambiguity_count"]
        for event in planned
        if isinstance(event.get("ambiguity_count"), int)
    ]
    if ambiguity_vals:
        result["avg_ambiguity_count"] = sum(ambiguity_vals) / len(ambiguity_vals)

    # Convergence comparison (dialogues only — consultations don't have converged field)
    planned_dialogues_with_conv = [
        e for e in plan_dialogues if isinstance(e.get("converged"), bool)
    ]
    unplanned_dialogues = [e for e in unplanned if e.get("event") == "dialogue_outcome"]
    unplanned_with_conv = [
        e for e in unplanned_dialogues if isinstance(e.get("converged"), bool)
    ]

    if planned_dialogues_with_conv:
        result["plan_convergence_rate"] = (
            sum(1 for e in planned_dialogues_with_conv if e["converged"])
            / len(planned_dialogues_with_conv)
        )
    if unplanned_with_conv:
        result["no_plan_convergence_rate"] = (
            sum(1 for e in unplanned_with_conv if e["converged"])
            / len(unplanned_with_conv)
        )

    return result


def _compute_provenance(dialogue_outcomes: list[dict]) -> dict:
    """Compute provenance health metrics from dialogue outcomes.

    provenance_unknown_count tracks how many citations in the briefing
    weren't matched by the 3-tier recovery in codex-dialogue Step 4.
    None means Step 3c fired (zero-output fallback, provenance never ran).
    """
    result = copy.deepcopy(_PROVENANCE_TEMPLATE)

    observed: list[int] = []
    missing = 0

    for event in dialogue_outcomes:
        val = stats_common.safe_nonneg_int(event, "provenance_unknown_count")
        if val is not None:
            observed.append(val)
        else:
            missing += 1

    result["provenance_observed_events"] = len(observed)
    result["provenance_missing_events"] = missing

    if observed:
        result["avg_provenance_unknown"] = sum(observed) / len(observed)
        result["zero_unknown_count"] = sum(1 for v in observed if v == 0)
        result["high_unknown_count"] = sum(1 for v in observed if v > 3)

    return result


def _compute_parse_diagnostics(dialogue_outcomes: list[dict]) -> dict:
    """Compute parse diagnostics from dialogue outcomes.

    parse_truncated: True when an unclosed fence block is detected in synthesis.
    parse_degraded: True when epilogue parse failed and markdown regex fallback
    was used (lower precision for converged detection).
    """
    result = copy.deepcopy(_PARSE_DIAGNOSTICS_TEMPLATE)

    for event in dialogue_outcomes:
        truncated = event.get("parse_truncated")
        degraded = event.get("parse_degraded")

        # Only count events where at least one field is present as bool
        if not isinstance(truncated, bool) and not isinstance(degraded, bool):
            continue

        result["observed_events"] += 1
        t = truncated is True
        d = degraded is True

        if t:
            result["truncated_count"] += 1
        if d:
            result["degraded_count"] += 1
        if not t and not d:
            result["clean_count"] += 1

    return result


# ---------------------------------------------------------------------------
# Section inclusion matrix
# ---------------------------------------------------------------------------

_SECTION_MATRIX: dict[str, dict[str, bool]] = {
    "all":          {"usage": True,  "dialogue": True,  "context": True,  "security": True,  "delegation": True},
    "dialogue":     {"usage": True,  "dialogue": True,  "context": True,  "security": False, "delegation": False},
    "consultation": {"usage": True,  "dialogue": False, "context": False, "security": False, "delegation": False},
    "security":     {"usage": False, "dialogue": False, "context": False, "security": True,  "delegation": False},
    "delegation":   {"usage": True,  "dialogue": False, "context": False, "security": False, "delegation": True},
}


# ---------------------------------------------------------------------------
# Validation gate
# ---------------------------------------------------------------------------


def _validate_events(events: list[dict]) -> tuple[list[dict], int]:
    """Run validation gate on events.

    Outcome events (dialogue_outcome, consultation_outcome) are validated
    against their required-field schemas. Guard events (block, shadow,
    consultation) pass through unvalidated.

    Returns (valid_events, invalid_count).
    """
    valid_events: list[dict] = []
    invalid_count = 0

    for event in events:
        et = event.get("event")
        if isinstance(et, str) and et in STRUCTURED_EVENT_TYPES:
            # validate_event() returns an error list: empty = valid
            if not read_events.validate_event(event):
                valid_events.append(event)
            else:
                invalid_count += 1
        else:
            valid_events.append(event)  # guard events have no schema to validate

    return valid_events, invalid_count


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


_SECTION_TYPE = Literal["all", "dialogue", "consultation", "security", "delegation"]


def compute(
    events: list[dict],
    skipped_count: int,
    period_days: int,
    section_type: _SECTION_TYPE,
) -> dict:
    """Compute analytics report from raw events.

    Args:
        events: All events from the event log.
        skipped_count: Count of malformed lines skipped during reading.
        period_days: Time window in days (0 = all-time).
        section_type: Which sections to include ("all", "dialogue",
            "consultation", "security", "delegation").

    Returns:
        Structured report dict with usage, dialogue, context, security
        sections plus metadata envelope.
    """
    if section_type not in _SECTION_MATRIX:
        raise ValueError(
            f"unknown section_type: {section_type!r}. "
            f"Expected one of {list(_SECTION_MATRIX)}"
        )

    total_events_read = len(events)

    # 1. Validation gate
    valid_events, invalid_count = _validate_events(events)

    # 2. Count unparseable timestamps (consistent regardless of period_days)
    timestamp_parse_failed = sum(
        1 for event in valid_events
        if stats_common.parse_ts_utc(event.get("ts", "")) is None
    )

    # 3. Classify events by type
    dialogue_outcomes: list[dict] = []
    consultation_outcomes: list[dict] = []
    delegation_outcomes: list[dict] = []
    consultations: list[dict] = []
    blocks: list[dict] = []
    shadows: list[dict] = []
    unclassified_count = 0

    for event in valid_events:
        event_type = read_events.classify(event)
        if event_type == "dialogue_outcome":
            dialogue_outcomes.append(event)
        elif event_type == "consultation_outcome":
            consultation_outcomes.append(event)
        elif event_type == "delegation_outcome":
            delegation_outcomes.append(event)
        elif event_type == "consultation":
            consultations.append(event)
        elif event_type == "block":
            blocks.append(event)
        elif event_type == "shadow":
            shadows.append(event)
        else:
            unclassified_count += 1

    # 4. Filter by period with shared `now` for consistent boundaries
    now = datetime.now(timezone.utc)

    dialogue_outcomes = stats_common.filter_by_period(dialogue_outcomes, period_days, now).events
    consultation_outcomes = stats_common.filter_by_period(consultation_outcomes, period_days, now).events
    consultations = stats_common.filter_by_period(consultations, period_days, now).events
    blocks = stats_common.filter_by_period(blocks, period_days, now).events
    shadows = stats_common.filter_by_period(shadows, period_days, now).events
    delegation_outcomes = stats_common.filter_by_period(delegation_outcomes, period_days, now).events

    # 5. Precompute shared counts
    invocations_completed_total = len(dialogue_outcomes) + len(consultation_outcomes)

    # 6. Compute window boundaries directly (all filter calls share same now/period_days)
    if period_days > 0:
        start = now - timedelta(days=period_days)
        window_start = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        window_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        window_start = ""
        window_end = ""

    # 7. Apply section inclusion matrix
    matrix = _SECTION_MATRIX[section_type]

    if matrix["usage"]:
        usage_section = _compute_usage(
            dialogue_outcomes, consultation_outcomes, delegation_outcomes,
            consultations, blocks, shadows
        )
    else:
        usage_section = copy.deepcopy(_USAGE_TEMPLATE)

    if matrix["dialogue"]:
        dialogue_section = _compute_dialogue(dialogue_outcomes)
    else:
        dialogue_section = copy.deepcopy(_DIALOGUE_TEMPLATE)

    if matrix["context"]:
        context_section = _compute_context(dialogue_outcomes)
    else:
        context_section = copy.deepcopy(_CONTEXT_TEMPLATE)

    if matrix["security"]:
        security_section = _compute_security(
            blocks, shadows, consultations, invocations_completed_total
        )
    else:
        security_section = copy.deepcopy(_SECURITY_TEMPLATE)

    if matrix.get("delegation"):
        delegation_section = _compute_delegation(delegation_outcomes)
    else:
        delegation_section = copy.deepcopy(_DELEGATION_TEMPLATE)

    # 8. Build output envelope
    return {
        "report_version": "1.0.0",
        "period_days": period_days,
        "window_start": window_start,
        "window_end": window_end,
        "meta": {
            "total_events_read": total_events_read,
            "malformed_lines_skipped": skipped_count,
            "invalid_events_count": invalid_count,
            "timestamp_parse_failed_count": timestamp_parse_failed,
            "unclassified_event_count": unclassified_count,
            "timezone": "UTC",
        },
        "usage": usage_section,
        "dialogue": dialogue_section,
        "context": context_section,
        "security": security_section,
        "delegation": delegation_section,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for compute_stats."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute cross-model consultation statistics"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(read_events._DEFAULT_PATH),
        help="JSONL event log path (default: ~/.claude/.codex-events.jsonl)",
    )
    parser.add_argument(
        "--period",
        default="30",
        help="Time period: integer days, '<N>d', or 'all' (default: 30)",
    )
    parser.add_argument(
        "--type",
        dest="section_type",
        default="all",
        choices=["dialogue", "consultation", "security", "delegation", "all"],
        help="Which sections to include (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=True,
        help="Output as JSON (default, kept for compatibility)",
    )
    args = parser.parse_args()

    try:
        period_days = stats_common.parse_period_days(args.period)
    except ValueError as exc:
        print(f"invalid --period: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        events, skipped = read_events.read_all(Path(args.path))
        result = compute(events, skipped, period_days, args.section_type)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"compute failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

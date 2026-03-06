#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Typed reader for the cross-model event log (~/.claude/.codex-events.jsonl).

Reads heterogeneous JSONL events (block, shadow, consultation,
dialogue_outcome, consultation_outcome, delegation_outcome), classifies by event type,
and validates per-event required fields.

Usage as library:
    from read_events import read_all, read_by_type, classify, validate_event

Usage as script:
    python3 read_events.py [--type dialogue_outcome] [--validate] [path]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_DEFAULT_PATH = Path.home() / ".claude" / ".codex-events.jsonl"

# Required fields per event type. Events not in this map are classified
# as their event field value but have no required-field validation.
_REQUIRED_FIELDS: dict[str, set[str]] = {
    "dialogue_outcome": {
        "schema_version",
        "consultation_id",
        "event",
        "ts",
        "posture",
        "turn_count",
        "turn_budget",
        "converged",
        "convergence_reason_code",
        "termination_reason",
        "resolved_count",
        "unresolved_count",
        "emerged_count",
        "seed_confidence",
        "mode",
    },
    "consultation_outcome": {
        "schema_version",
        "consultation_id",
        "event",
        "ts",
        "posture",
        "turn_count",
        "turn_budget",
        "termination_reason",
        "mode",
    },
    "delegation_outcome": {
        "schema_version",
        "event",
        "ts",
        "consultation_id",
        "session_id",
        "thread_id",
        "dispatched",
        "sandbox",
        "full_auto",
        "credential_blocked",
        "dirty_tree_blocked",
        "readable_secret_file_blocked",
        "commands_run_count",
        "exit_code",
        "termination_reason",
        "model",              # F10: nullable but present in event
        "reasoning_effort",   # F10: nullable but present in event
    },
}

# Known event types that are valid but have no required-field schema
_KNOWN_UNSTRUCTURED = {"block", "shadow", "consultation"}


def classify(event: dict) -> str:
    """Return the event type string, or 'unknown' if missing."""
    return event.get("event", "unknown")


def validate_event(event: dict) -> list[str]:
    """Validate an event against its type's required fields.

    Returns a list of error strings (empty = valid).
    """
    event_type = classify(event)

    if event_type == "unknown":
        return ["unknown event type: missing 'event' field"]

    required = _REQUIRED_FIELDS.get(event_type)
    if required is None:
        if event_type in _KNOWN_UNSTRUCTURED:
            return []
        return [f"unknown event type: '{event_type}'"]

    missing = required - set(event.keys())
    if missing:
        return [f"missing required field: {f}" for f in sorted(missing)]
    return []


def read_all(path: Path | None = None) -> tuple[list[dict], int]:
    """Read all events from the JSONL file. Skips malformed and non-object lines.

    Returns (events, skipped_count). Skipped counts malformed JSON
    and valid JSON that is not an object (e.g. null, [], 42).
    Blank lines are silently ignored and not counted.

    Returns ([], 0) if file does not exist.
    """
    path = path or _DEFAULT_PATH
    if not path.exists():
        return [], 0

    events: list[dict] = []
    skipped = 0
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                print(f"line {lineno}: skipped (malformed JSON)", file=sys.stderr)
                continue
            if not isinstance(parsed, dict):
                skipped += 1
                print(
                    f"line {lineno}: skipped (expected object, got {type(parsed).__name__})",
                    file=sys.stderr,
                )
                continue
            events.append(parsed)
    return events, skipped


def read_by_type(path: Path | None = None, event_type: str = "dialogue_outcome") -> tuple[list[dict], int]:
    """Read events filtered by type. Returns (filtered_events, skipped_count)."""
    events, skipped = read_all(path)
    return [e for e in events if classify(e) == event_type], skipped


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Read cross-model event log")
    parser.add_argument("path", nargs="?", default=str(_DEFAULT_PATH), help="JSONL file path")
    parser.add_argument("--type", dest="event_type", help="Filter by event type")
    parser.add_argument("--validate", action="store_true", help="Validate events and report errors")
    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        print(json.dumps({"events": 0, "errors": 0, "skipped": 0}))
        sys.exit(0)

    try:
        if args.event_type:
            events, skipped = read_by_type(path, args.event_type)
        else:
            events, skipped = read_all(path)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"read failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.validate:
        total_errors = 0
        for i, event in enumerate(events):
            errors = validate_event(event)
            if errors:
                total_errors += len(errors)
                eid = event.get("consultation_id", f"event-{i}")
                for err in errors:
                    print(f"[{eid}] {err}", file=sys.stderr)
        print(json.dumps({"events": len(events), "errors": total_errors, "skipped": skipped}))
        sys.exit(1 if total_errors > 0 else 0)
    else:
        for event in events:
            print(json.dumps(event))
        if skipped:
            print(f"{skipped} line(s) skipped", file=sys.stderr)


if __name__ == "__main__":
    main()

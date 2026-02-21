#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Typed reader for the cross-model event log (~/.claude/.codex-events.jsonl).

Reads heterogeneous JSONL events (block, shadow, consultation,
dialogue_outcome, consultation_outcome), classifies by event type,
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


def read_all(path: Path | None = None) -> list[dict]:
    """Read all events from the JSONL file. Skips malformed lines.

    Returns empty list if file does not exist.
    """
    path = path or _DEFAULT_PATH
    if not path.exists():
        return []

    events: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def read_by_type(path: Path | None = None, event_type: str = "dialogue_outcome") -> list[dict]:
    """Read events filtered by type."""
    return [e for e in read_all(path) if classify(e) == event_type]


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Read cross-model event log")
    parser.add_argument("path", nargs="?", default=str(_DEFAULT_PATH), help="JSONL file path")
    parser.add_argument("--type", dest="event_type", help="Filter by event type")
    parser.add_argument("--validate", action="store_true", help="Validate events and report errors")
    args = parser.parse_args()

    path = Path(args.path)
    events = read_by_type(path, args.event_type) if args.event_type else read_all(path)

    if args.validate:
        total_errors = 0
        for i, event in enumerate(events):
            errors = validate_event(event)
            if errors:
                total_errors += len(errors)
                eid = event.get("consultation_id", f"line-{i}")
                for err in errors:
                    print(f"[{eid}] {err}", file=sys.stderr)
        print(json.dumps({"events": len(events), "errors": total_errors}))
        sys.exit(1 if total_errors > 0 else 0)
    else:
        for event in events:
            print(json.dumps(event))


if __name__ == "__main__":
    main()

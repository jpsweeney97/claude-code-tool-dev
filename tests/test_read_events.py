"""Tests for packages/plugins/cross-model/scripts/read_events.py.

Tests the typed event reader: JSONL parsing, event classification,
per-event schema validation, and error handling for unknown/malformed events.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest  # noqa: F401

# ---------------------------------------------------------------------------
# Module import
# ---------------------------------------------------------------------------

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "plugins"
    / "cross-model"
    / "scripts"
    / "read_events.py"
)
SPEC = importlib.util.spec_from_file_location("read_events", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DIALOGUE_EVENT = {
    "schema_version": "0.1.0",
    "consultation_id": "uuid-1",
    "event": "dialogue_outcome",
    "ts": "2026-02-21T12:00:00Z",
    "posture": "evaluative",
    "turn_count": 4,
    "turn_budget": 8,
    "converged": True,
    "convergence_reason_code": "all_resolved",
    "termination_reason": "natural",
    "resolved_count": 5,
    "unresolved_count": 0,
    "emerged_count": 2,
    "seed_confidence": "normal",
    "mode": "server_assisted",
}

CONSULTATION_EVENT = {
    "schema_version": "0.1.0",
    "consultation_id": "uuid-2",
    "event": "consultation_outcome",
    "ts": "2026-02-21T13:00:00Z",
    "posture": "collaborative",
    "turn_count": 1,
    "turn_budget": 1,
    "termination_reason": "complete",
    "mode": "server_assisted",
}

BLOCK_EVENT = {
    "ts": "2026-02-21T10:00:00Z",
    "event": "block",
    "tool": "Bash",
    "session_id": "sess-1",
    "prompt_length": 500,
    "reason": "denied",
}

SHADOW_EVENT = {
    "ts": "2026-02-21T10:01:00Z",
    "event": "shadow",
    "tool": "Bash",
    "session_id": "sess-1",
    "prompt_length": 600,
}


def _write_jsonl(events: list[dict], path: Path) -> None:
    with open(path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReadAll:
    def test_reads_all_events(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        _write_jsonl([DIALOGUE_EVENT, CONSULTATION_EVENT, BLOCK_EVENT], path)
        events, skipped = MODULE.read_all(path)
        assert len(events) == 3
        assert skipped == 0

    def test_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        path.write_text("")
        events, skipped = MODULE.read_all(path)
        assert events == []
        assert skipped == 0

    def test_missing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.jsonl"
        events, skipped = MODULE.read_all(path)
        assert events == []
        assert skipped == 0

    def test_malformed_line_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        with open(path, "w") as f:
            f.write(json.dumps(DIALOGUE_EVENT) + "\n")
            f.write("not valid json\n")
            f.write(json.dumps(CONSULTATION_EVENT) + "\n")
        events, skipped = MODULE.read_all(path)
        assert len(events) == 2
        assert skipped == 1

    def test_blank_lines_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        with open(path, "w") as f:
            f.write(json.dumps(DIALOGUE_EVENT) + "\n")
            f.write("\n")
            f.write("   \n")
            f.write(json.dumps(CONSULTATION_EVENT) + "\n")
        events, skipped = MODULE.read_all(path)
        assert len(events) == 2
        assert skipped == 0  # blank lines are not counted as skipped

    def test_non_dict_json_lines_skipped(self, tmp_path: Path) -> None:
        """Valid JSON that is not an object (null, [], 42, "str") is skipped."""
        path = tmp_path / "events.jsonl"
        with open(path, "w") as f:
            f.write(json.dumps(DIALOGUE_EVENT) + "\n")
            f.write("null\n")
            f.write("42\n")
            f.write("[1, 2, 3]\n")
            f.write('"just a string"\n')
            f.write("true\n")
            f.write(json.dumps(CONSULTATION_EVENT) + "\n")
        events, skipped = MODULE.read_all(path)
        assert len(events) == 2
        assert skipped == 5


class TestFilterByType:
    def test_filter_dialogue_only(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        _write_jsonl([DIALOGUE_EVENT, CONSULTATION_EVENT, BLOCK_EVENT], path)
        events, _ = MODULE.read_by_type(path, "dialogue_outcome")
        assert len(events) == 1
        assert events[0]["event"] == "dialogue_outcome"

    def test_filter_consultation_only(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        _write_jsonl([DIALOGUE_EVENT, CONSULTATION_EVENT], path)
        events, _ = MODULE.read_by_type(path, "consultation_outcome")
        assert len(events) == 1
        assert events[0]["event"] == "consultation_outcome"

    def test_filter_no_matches(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        _write_jsonl([BLOCK_EVENT], path)
        events, _ = MODULE.read_by_type(path, "dialogue_outcome")
        assert events == []

    def test_filter_unstructured_type(self, tmp_path: Path) -> None:
        """Filtering by unstructured event types (block, shadow) works."""
        path = tmp_path / "events.jsonl"
        _write_jsonl([BLOCK_EVENT, SHADOW_EVENT, DIALOGUE_EVENT], path)
        events, _ = MODULE.read_by_type(path, "block")
        assert len(events) == 1
        assert events[0]["event"] == "block"

    def test_unknown_event_type_passes_through(self, tmp_path: Path) -> None:
        unknown = {"event": "future_event_type", "ts": "2026-01-01T00:00:00Z"}
        path = tmp_path / "events.jsonl"
        _write_jsonl([unknown, DIALOGUE_EVENT], path)
        all_events, _ = MODULE.read_all(path)
        assert len(all_events) == 2


class TestEventClassification:
    def test_classify_dialogue(self) -> None:
        assert MODULE.classify(DIALOGUE_EVENT) == "dialogue_outcome"

    def test_classify_consultation(self) -> None:
        assert MODULE.classify(CONSULTATION_EVENT) == "consultation_outcome"

    def test_classify_block(self) -> None:
        assert MODULE.classify(BLOCK_EVENT) == "block"

    def test_classify_shadow(self) -> None:
        assert MODULE.classify(SHADOW_EVENT) == "shadow"

    def test_classify_missing_event_field(self) -> None:
        assert MODULE.classify({"ts": "2026-01-01T00:00:00Z"}) == "unknown"

    def test_classify_empty_dict(self) -> None:
        assert MODULE.classify({}) == "unknown"


class TestValidateEvent:
    def test_valid_dialogue_passes(self) -> None:
        errors = MODULE.validate_event(DIALOGUE_EVENT)
        assert errors == []

    def test_valid_consultation_passes(self) -> None:
        errors = MODULE.validate_event(CONSULTATION_EVENT)
        assert errors == []

    def test_dialogue_missing_required_field(self) -> None:
        bad = {k: v for k, v in DIALOGUE_EVENT.items() if k != "turn_count"}
        errors = MODULE.validate_event(bad)
        assert len(errors) >= 1
        assert any("turn_count" in e for e in errors)

    def test_consultation_missing_required_field(self) -> None:
        bad = {k: v for k, v in CONSULTATION_EVENT.items() if k != "mode"}
        errors = MODULE.validate_event(bad)
        assert len(errors) >= 1
        assert any("mode" in e for e in errors)

    def test_block_event_passes_minimal(self) -> None:
        """Block/shadow events have no strict schema — just needs 'event' field."""
        errors = MODULE.validate_event(BLOCK_EVENT)
        assert errors == []

    def test_unknown_event_returns_warning(self) -> None:
        unknown = {"event": "future_unknown", "ts": "2026-01-01T00:00:00Z"}
        errors = MODULE.validate_event(unknown)
        assert len(errors) == 1
        assert "unknown" in errors[0].lower()


class TestSchemaParityWithEmitter:
    """Guard against reader/emitter schema drift via subset check."""

    def test_dialogue_required_subset(self) -> None:
        """Reader's dialogue required fields must be a subset of emitter's."""
        emitter_path = (
            Path(__file__).resolve().parents[1]
            / "packages" / "plugins" / "cross-model" / "scripts" / "emit_analytics.py"
        )
        spec = importlib.util.spec_from_file_location("emit_analytics", emitter_path)
        emitter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emitter)
        reader_required = MODULE._REQUIRED_FIELDS.get("dialogue_outcome", set())
        emitter_required = emitter._DIALOGUE_REQUIRED
        assert reader_required <= emitter_required, (
            f"Reader has fields not in emitter: {reader_required - emitter_required}"
        )

    def test_consultation_required_subset(self) -> None:
        """Reader's consultation required fields must be a subset of emitter's."""
        emitter_path = (
            Path(__file__).resolve().parents[1]
            / "packages" / "plugins" / "cross-model" / "scripts" / "emit_analytics.py"
        )
        spec = importlib.util.spec_from_file_location("emit_analytics", emitter_path)
        emitter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emitter)
        reader_required = MODULE._REQUIRED_FIELDS.get("consultation_outcome", set())
        emitter_required = emitter._CONSULTATION_REQUIRED
        assert reader_required <= emitter_required, (
            f"Reader has fields not in emitter: {reader_required - emitter_required}"
        )

    def test_emitter_event_types_covered_by_reader(self) -> None:
        """Reader must have schemas for all structured event types the emitter produces."""
        emitter_event_types = {"dialogue_outcome", "consultation_outcome"}
        reader_event_types = set(MODULE._REQUIRED_FIELDS.keys())
        assert emitter_event_types <= reader_event_types, (
            f"Emitter types not in reader: {emitter_event_types - reader_event_types}"
        )

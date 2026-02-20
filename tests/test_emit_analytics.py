"""Tests for packages/plugins/cross-model/scripts/emit_analytics.py.

Tests the analytics emitter: synthesis parsing, convergence mapping,
event building, validation, and JSONL append.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import (same pattern as test_codex_guard.py)
# ---------------------------------------------------------------------------

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "plugins"
    / "cross-model"
    / "scripts"
    / "emit_analytics.py"
)
SPEC = importlib.util.spec_from_file_location("emit_analytics", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SYNTHESIS = """\
### Conversation Summary
- **Topic:** Analytics design
- **Goal:** Evaluate design quality
- **Posture:** Evaluative
- **Turns:** 4 of 8 budget
- **Converged:** Yes — both sides agreed on core findings
- **Trajectory:** T1:advancing → T2:advancing → T3:advancing → T4:static
- **Evidence:** 3 scouts / 4 turns, entities: emit_analytics.py, codex_guard.py

### Key Outcomes

Some narrative content here.

### Areas of Agreement

Points both sides converged on.

### Contested Claims

Some contested claims here.

### Open Questions

Some open questions here.

### Continuation
- **Thread ID:** thread-abc-123
- **Continuation warranted:** No
- **Unresolved items carried forward:** none
- **Recommended posture for continuation:** N/A
- **Evidence trajectory:** T2: emit_analytics.py (CLAIM confirmed), T3: codex_guard.py

### Synthesis Checkpoint
```
## Synthesis Checkpoint
RESOLVED: echo-append is unsafe [confidence: High] [basis: convergence]
RESOLVED: Step 7 ownership correct [confidence: High] [basis: convergence]
RESOLVED: Need deterministic script [confidence: High] [basis: convergence]
RESOLVED: extraction drift confirmed [confidence: High] [basis: evidence]
RESOLVED: session_id policy [confidence: Medium] [basis: concession]
UNRESOLVED: dead field retention [raised: turn 3]
EMERGED: ownership-vs-mechanics [source: dialogue-born]
EMERGED: session_id_source field [source: dialogue-born]
```
"""

SAMPLE_PIPELINE = {
    "posture": "evaluative",
    "turn_budget": 8,
    "profile_name": None,
    "seed_confidence": "normal",
    "low_seed_confidence_reasons": [],
    "assumption_count": 4,
    "no_assumptions_fallback": False,
    "gatherer_a_lines": 23,
    "gatherer_b_lines": 8,
    "gatherer_a_retry": False,
    "gatherer_b_retry": False,
    "citations_total": 24,
    "unique_files_total": 7,
    "gatherer_a_unique_paths": 7,
    "gatherer_b_unique_paths": 3,
    "shared_citation_paths": 3,
    "counter_count": 3,
    "confirm_count": 2,
    "open_count": 7,
    "claim_count": 19,
    "source_classes": ["code", "docs"],
    "scope_root_count": 3,
    "scope_roots_fingerprint": None,
}


def _dialogue_input(
    synthesis: str = SAMPLE_SYNTHESIS,
    pipeline: dict | None = None,
    scope_breach: bool = False,
) -> dict:
    return {
        "event_type": "dialogue_outcome",
        "synthesis_text": synthesis,
        "scope_breach": scope_breach,
        "pipeline": pipeline or SAMPLE_PIPELINE,
    }


def _consultation_input(pipeline: dict | None = None) -> dict:
    return {
        "event_type": "consultation_outcome",
        "pipeline": pipeline
        or {
            "posture": "collaborative",
            "thread_id": "thread-xyz-789",
            "turn_count": 1,
            "turn_budget": 1,
            "profile_name": None,
            "mode": "server_assisted",
        },
    }


# ---------------------------------------------------------------------------
# TestSplitSections
# ---------------------------------------------------------------------------


class TestSplitSections:
    def test_basic_split(self) -> None:
        text = "### Section One\ncontent one\n### Section Two\ncontent two\n"
        result = MODULE._split_sections(text)
        assert "section one" in result
        assert "section two" in result

    def test_case_normalized_keys(self) -> None:
        text = "### Synthesis Checkpoint\nstuff\n### Synthesis checkpoint\nmore\n"
        result = MODULE._split_sections(text)
        assert "synthesis checkpoint" in result

    def test_strips_fenced_blocks(self) -> None:
        text = "### Outer\n```\n## Inner Header\ncontent\n```\n"
        result = MODULE._split_sections(text)
        assert "inner header" not in result
        assert "outer" in result

    def test_nested_fence_with_level2_header(self) -> None:
        """Regression: ## Synthesis Checkpoint inside code fence must not create section."""
        text = (
            "### Synthesis Checkpoint\n"
            "```\n"
            "## Synthesis Checkpoint\n"
            "RESOLVED: item [confidence: High]\n"
            "```\n"
        )
        result = MODULE._split_sections(text)
        # Only one section, from the ### header
        assert len(result) == 1
        assert "synthesis checkpoint" in result


# ---------------------------------------------------------------------------
# TestParseSynthesis
# ---------------------------------------------------------------------------


class TestParseSynthesis:
    def test_full_parse(self) -> None:
        result = MODULE.parse_synthesis(SAMPLE_SYNTHESIS)
        assert result["resolved_count"] == 5
        assert result["unresolved_count"] == 1
        assert result["emerged_count"] == 2
        assert result["converged"] is True
        assert result["turn_count"] == 4
        assert result["thread_id"] == "thread-abc-123"
        assert result["scout_count"] == 3

    def test_converged_no(self) -> None:
        text = "### Conversation Summary\n- **Converged:** No -- hit turn limit\n"
        result = MODULE.parse_synthesis(text)
        assert result["converged"] is False

    def test_converged_yes_case_insensitive(self) -> None:
        text = "### Conversation Summary\n- **Converged:** YES - strong agreement\n"
        result = MODULE.parse_synthesis(text)
        assert result["converged"] is True

    def test_converged_missing(self) -> None:
        result = MODULE.parse_synthesis("### Conversation Summary\n- **Topic:** test\n")
        assert result["converged"] is False

    def test_turn_count(self) -> None:
        text = "### Conversation Summary\n- **Turns:** 6 of 10 budget\n"
        result = MODULE.parse_synthesis(text)
        assert result["turn_count"] == 6

    def test_thread_id_none(self) -> None:
        text = "### Continuation\n- **Thread ID:** none\n"
        result = MODULE.parse_synthesis(text)
        assert result["thread_id"] is None

    def test_thread_id_with_backticks(self) -> None:
        text = "### Continuation\n- **Thread ID:** `thread-abc`\n"
        result = MODULE.parse_synthesis(text)
        assert result["thread_id"] == "thread-abc"

    def test_scout_count_from_summary_not_continuation(self) -> None:
        """Regression: scout_count must come from Summary Evidence, not Continuation."""
        text = (
            "### Conversation Summary\n"
            "- **Evidence:** 5 scouts / 8 turns, entities: foo.py\n"
            "\n### Continuation\n"
            "- **Evidence trajectory:** T2: foo.py, T5: bar.py\n"
        )
        result = MODULE.parse_synthesis(text)
        assert result["scout_count"] == 5

    def test_scout_count_zero_when_none(self) -> None:
        text = "### Conversation Summary\n- **Evidence:** 0 scouts / 4 turns\n"
        result = MODULE.parse_synthesis(text)
        assert result["scout_count"] == 0

    def test_empty_text(self) -> None:
        result = MODULE.parse_synthesis("")
        assert result["resolved_count"] == 0
        assert result["unresolved_count"] == 0
        assert result["emerged_count"] == 0
        assert result["converged"] is False
        assert result["turn_count"] == 0
        assert result["thread_id"] is None
        assert result["scout_count"] == 0

    def test_partial_synthesis_missing_continuation(self) -> None:
        text = (
            "### Conversation Summary\n"
            "- **Converged:** Yes\n"
            "- **Turns:** 3 of 5\n"
            "- **Evidence:** 1 scout / 3 turns\n"
            "\n### Synthesis Checkpoint\n"
            "RESOLVED: something [confidence: High]\n"
        )
        result = MODULE.parse_synthesis(text)
        assert result["converged"] is True
        assert result["turn_count"] == 3
        assert result["thread_id"] is None
        assert result["resolved_count"] == 1
        assert result["scout_count"] == 1

    def test_checkpoint_case_insensitive(self) -> None:
        text = "### Synthesis Checkpoint\nresolved: item one\nResolved: item two\n"
        result = MODULE.parse_synthesis(text)
        assert result["resolved_count"] == 2

    def test_checkpoint_fallback_to_whole_text(self) -> None:
        """When no Synthesis Checkpoint section header, search whole text."""
        text = "RESOLVED: item one\nRESOLVED: item two\nUNRESOLVED: item three\n"
        result = MODULE.parse_synthesis(text)
        assert result["resolved_count"] == 2
        assert result["unresolved_count"] == 1

    def test_scout_count_none_natural_language(self) -> None:
        """Agent may emit 'none (no scouts executed)' instead of '0 scouts'."""
        text = "### Conversation Summary\n- **Evidence:** none (no scouts executed)\n"
        result = MODULE.parse_synthesis(text)
        assert result["scout_count"] == 0


# ---------------------------------------------------------------------------
# TestMapConvergence
# ---------------------------------------------------------------------------


class TestMapConvergence:
    def test_all_resolved(self) -> None:
        assert MODULE.map_convergence(True, 0, 4, 8) == (
            "all_resolved",
            "convergence",
        )

    def test_natural_convergence(self) -> None:
        assert MODULE.map_convergence(True, 2, 4, 8) == (
            "natural_convergence",
            "convergence",
        )

    def test_budget_exhausted(self) -> None:
        assert MODULE.map_convergence(False, 1, 8, 8) == (
            "budget_exhausted",
            "budget",
        )

    def test_error(self) -> None:
        assert MODULE.map_convergence(False, 0, 3, 8) == ("error", "error")

    def test_scope_breach_overrides(self) -> None:
        """scope_breach takes priority even if converged=True."""
        assert MODULE.map_convergence(True, 0, 4, 8, scope_breach=True) == (
            "scope_breach",
            "scope_breach",
        )


# ---------------------------------------------------------------------------
# TestBuildDialogueOutcome
# ---------------------------------------------------------------------------


class TestBuildDialogueOutcome:
    def test_all_fields_present(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        expected_fields = {
            "schema_version", "consultation_id", "thread_id", "session_id",
            "event", "ts", "posture", "turn_count", "turn_budget",
            "profile_name", "mode", "converged", "convergence_reason_code",
            "termination_reason", "resolved_count", "unresolved_count",
            "emerged_count", "seed_confidence", "low_seed_confidence_reasons",
            "assumption_count", "no_assumptions_fallback",
            "gatherer_a_lines", "gatherer_b_lines",
            "gatherer_a_retry", "gatherer_b_retry",
            "citations_total", "unique_files_total",
            "gatherer_a_unique_paths", "gatherer_b_unique_paths",
            "shared_citation_paths", "counter_count", "confirm_count",
            "open_count", "claim_count", "scout_count",
            "source_classes", "scope_root_count", "scope_roots_fingerprint",
            "question_shaped", "shape_confidence",
            "assumptions_generated_count", "ambiguity_count",
            "provenance_unknown_count", "episode_id",
        }
        assert set(event.keys()) == expected_fields

    def test_consultation_id_is_uuid(self) -> None:
        import uuid as uuid_mod

        event = MODULE.build_dialogue_outcome(_dialogue_input())
        uuid_mod.UUID(event["consultation_id"])  # raises on invalid

    def test_ts_format(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["ts"].endswith("Z")
        assert "T" in event["ts"]

    def test_ts_format_strict(self) -> None:
        """Timestamp must be ISO 8601 with Z suffix, no microseconds."""
        import re as re_mod

        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert re_mod.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", event["ts"])

    def test_session_id_from_env(self, monkeypatch) -> None:
        monkeypatch.setenv("CLAUDE_SESSION_ID", "sess-test-123")
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["session_id"] == "sess-test-123"

    def test_session_id_missing(self, monkeypatch) -> None:
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["session_id"] is None

    def test_pipeline_fields_passed_through(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["posture"] == "evaluative"
        assert event["turn_budget"] == 8
        assert event["gatherer_a_lines"] == 23
        assert event["source_classes"] == ["code", "docs"]

    def test_nullable_fields_are_none(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["question_shaped"] is None
        assert event["provenance_unknown_count"] is None
        assert event["episode_id"] is None

    def test_scope_breach_event(self) -> None:
        event = MODULE.build_dialogue_outcome(
            _dialogue_input(scope_breach=True)
        )
        assert event["convergence_reason_code"] == "scope_breach"
        assert event["termination_reason"] == "scope_breach"

    def test_provenance_unknown_count_from_pipeline(self) -> None:
        """provenance_unknown_count flows from pipeline when provided."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["provenance_unknown_count"] == 3

    def test_provenance_unknown_count_none_when_absent(self) -> None:
        """provenance_unknown_count defaults to None when not in pipeline."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["provenance_unknown_count"] is None

    def test_schema_version_bumps_with_provenance(self) -> None:
        """schema_version auto-bumps to 0.2.0 when provenance_unknown_count is non-null."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 0}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.2.0"

    def test_schema_version_stays_without_provenance(self) -> None:
        """schema_version stays 0.1.0 when provenance_unknown_count is None."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["schema_version"] == "0.1.0"

    def test_provenance_unknown_count_explicit_none_schema_stays(self) -> None:
        """schema_version stays 0.1.0 when provenance_unknown_count is explicitly None."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": None}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.1.0"
        assert event["provenance_unknown_count"] is None


# ---------------------------------------------------------------------------
# TestBuildConsultationOutcome
# ---------------------------------------------------------------------------


class TestBuildConsultationOutcome:
    def test_field_count(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert len(event) == 13

    def test_converged_null(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["converged"] is None

    def test_termination_complete(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["termination_reason"] == "complete"

    def test_no_convergence_reason_code(self) -> None:
        """consultation_outcome should not include convergence_reason_code."""
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert "convergence_reason_code" not in event

    def test_thread_id_from_pipeline(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["thread_id"] == "thread-xyz-789"


# ---------------------------------------------------------------------------
# TestValidate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_valid_dialogue_passes(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        MODULE.validate(event, "dialogue_outcome")  # no exception

    def test_valid_consultation_passes(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        MODULE.validate(event, "consultation_outcome")  # no exception

    def test_missing_required_field(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        del event["consultation_id"]
        with pytest.raises(ValueError, match="missing required fields"):
            MODULE.validate(event, "dialogue_outcome")

    def test_invalid_posture_enum(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["posture"] = "aggressive"
        with pytest.raises(ValueError, match="invalid posture"):
            MODULE.validate(event, "dialogue_outcome")

    def test_invalid_termination_reason(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        event["termination_reason"] = "timeout"
        with pytest.raises(ValueError, match="invalid termination_reason"):
            MODULE.validate(event, "consultation_outcome")

    def test_negative_count(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["resolved_count"] = -1
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_turn_count_exceeds_budget(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_count"] = 10
        event["turn_budget"] = 8
        with pytest.raises(ValueError, match="turn_count.*turn_budget"):
            MODULE.validate(event, "dialogue_outcome")

    def test_turn_count_exceeds_budget_allowed_on_error(self) -> None:
        """turn_count > turn_budget is allowed when termination_reason is error."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_count"] = 10
        event["turn_budget"] = 8
        event["termination_reason"] = "error"
        MODULE.validate(event, "dialogue_outcome")  # no exception

    def test_dialogue_rejects_none_convergence_code(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["convergence_reason_code"] = None
        with pytest.raises(ValueError, match="convergence_reason_code required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_consultation_multi_turn_valid(self) -> None:
        """Multi-turn /codex: turn_count > turn_budget is valid."""
        event = MODULE.build_consultation_outcome(
            _consultation_input({"posture": "collaborative", "turn_count": 3, "turn_budget": 1})
        )
        MODULE.validate(event, "consultation_outcome")  # no exception

    def test_invalid_mode(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["mode"] = "raw_socket"
        with pytest.raises(ValueError, match="invalid mode"):
            MODULE.validate(event, "dialogue_outcome")

    def test_none_posture_rejected(self) -> None:
        """posture is required — None must not pass validation."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["posture"] = None
        with pytest.raises(ValueError, match="posture is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_none_posture_rejected_consultation(self) -> None:
        """posture is required for consultation_outcome too."""
        event = MODULE.build_consultation_outcome(_consultation_input())
        event["posture"] = None
        with pytest.raises(ValueError, match="posture is required"):
            MODULE.validate(event, "consultation_outcome")

    def test_boolean_count_rejected(self) -> None:
        """bool is a subclass of int — must be explicitly rejected for counts."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_count"] = True
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_boolean_false_count_rejected(self) -> None:
        """False (== 0) must also be rejected as a count value."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["resolved_count"] = False
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_none_termination_reason_rejected(self) -> None:
        """termination_reason is required — None must not pass."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["termination_reason"] = None
        with pytest.raises(ValueError, match="termination_reason is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_none_seed_confidence_rejected_for_dialogue(self) -> None:
        """seed_confidence is required for dialogue_outcome."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["seed_confidence"] = None
        with pytest.raises(ValueError, match="seed_confidence required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_none_seed_confidence_allowed_for_consultation(self) -> None:
        """seed_confidence is not required for consultation_outcome."""
        event = MODULE.build_consultation_outcome(_consultation_input())
        event["seed_confidence"] = None
        MODULE.validate(event, "consultation_outcome")  # no exception

    def test_invalid_seed_confidence_value(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["seed_confidence"] = "high"
        with pytest.raises(ValueError, match="invalid seed_confidence"):
            MODULE.validate(event, "dialogue_outcome")

    def test_invalid_convergence_reason_code(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["convergence_reason_code"] = "timeout"
        with pytest.raises(ValueError, match="invalid convergence_reason_code"):
            MODULE.validate(event, "dialogue_outcome")

    def test_turn_budget_zero_rejected(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_budget"] = 0
        with pytest.raises(ValueError, match="turn_budget must be >= 1"):
            MODULE.validate(event, "dialogue_outcome")

    def test_event_type_mismatch(self) -> None:
        """Event dict says dialogue_outcome but validate called with consultation_outcome."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        with pytest.raises(ValueError, match="event field mismatch"):
            MODULE.validate(event, "consultation_outcome")

    def test_converged_string_rejected(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["converged"] = "yes"
        with pytest.raises(ValueError, match="converged must be bool"):
            MODULE.validate(event, "dialogue_outcome")

    def test_source_classes_string_rejected(self) -> None:
        """source_classes must be a list, not a plain string."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["source_classes"] = "code"
        with pytest.raises(ValueError, match="source_classes must be a list"):
            MODULE.validate(event, "dialogue_outcome")

    def test_source_classes_non_string_items(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["source_classes"] = [1, 2]
        with pytest.raises(ValueError, match="source_classes must contain only strings"):
            MODULE.validate(event, "dialogue_outcome")

    def test_none_mode_rejected_dialogue(self) -> None:
        """mode is required — None must not pass validation."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["mode"] = None
        with pytest.raises(ValueError, match="mode is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_none_mode_rejected_consultation(self) -> None:
        """mode is required for consultation_outcome too."""
        event = MODULE.build_consultation_outcome(_consultation_input())
        event["mode"] = None
        with pytest.raises(ValueError, match="mode is required"):
            MODULE.validate(event, "consultation_outcome")

    def test_missing_mode_rejected(self) -> None:
        """mode in required sets — missing key caught by required fields check."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        del event["mode"]
        with pytest.raises(ValueError, match="missing required fields"):
            MODULE.validate(event, "dialogue_outcome")

    def test_turn_budget_null_rejected(self) -> None:
        """turn_budget=None must raise ValueError, not TypeError."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_budget"] = None
        with pytest.raises(ValueError, match="turn_budget must be a positive int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_turn_budget_bool_rejected(self) -> None:
        """turn_budget=True caught by count fields validator (bool is subclass of int)."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_budget"] = True
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_turn_budget_string_rejected(self) -> None:
        """turn_budget='5' caught by count fields validator."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_budget"] = "5"
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_low_seed_confidence_reasons_string_rejected(self) -> None:
        """low_seed_confidence_reasons must be a list, not a string."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = "insufficient coverage"
        with pytest.raises(ValueError, match="low_seed_confidence_reasons must be a list"):
            MODULE.validate(event, "dialogue_outcome")

    def test_low_seed_confidence_reasons_non_string_items(self) -> None:
        """low_seed_confidence_reasons items must be strings."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = [1, 2]
        with pytest.raises(ValueError, match="low_seed_confidence_reasons must contain only strings"):
            MODULE.validate(event, "dialogue_outcome")

    def test_low_seed_confidence_reasons_valid(self) -> None:
        """Valid list of enum strings passes."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = ["thin_citations", "few_files"]
        MODULE.validate(event, "dialogue_outcome")  # no exception

    def test_invalid_low_seed_confidence_reason_rejected(self) -> None:
        """Only enum values from §2.4a are accepted."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = ["narrow_scope"]
        with pytest.raises(ValueError, match="invalid low_seed_confidence_reasons"):
            MODULE.validate(event, "dialogue_outcome")

    def test_all_low_seed_confidence_reasons_accepted(self) -> None:
        """All four enum values pass validation together."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = [
            "thin_citations", "few_files", "zero_output", "provenance_violations"
        ]
        MODULE.validate(event, "dialogue_outcome")  # no exception

    def test_provenance_unknown_count_negative_rejected(self) -> None:
        """provenance_unknown_count must be non-negative (via _COUNT_FIELDS)."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["provenance_unknown_count"] = -1
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_provenance_unknown_count_bool_rejected(self) -> None:
        """provenance_unknown_count bool must be rejected (via _COUNT_FIELDS)."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["provenance_unknown_count"] = True
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")


# ---------------------------------------------------------------------------
# TestAppendLog
# ---------------------------------------------------------------------------


class TestAppendLog:
    def test_appends_valid_jsonl(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        entry = {"event": "test", "value": 42}
        assert MODULE._append_log(entry) is True
        line = log_path.read_text().strip()
        assert json.loads(line) == entry

    def test_appends_multiple(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        MODULE._append_log({"n": 1})
        MODULE._append_log({"n": 2})
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["n"] == 1
        assert json.loads(lines[1])["n"] == 2

    def test_creates_parent_dir(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "nested" / "dir" / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        assert MODULE._append_log({"test": True}) is True
        assert log_path.exists()

    def test_oserror_returns_false(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "readonly" / "events.jsonl"
        (tmp_path / "readonly").mkdir()
        (tmp_path / "readonly").chmod(0o444)
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        assert MODULE._append_log({"test": True}) is False
        (tmp_path / "readonly").chmod(0o755)  # cleanup

    def test_typeerror_returns_false(self, tmp_path, monkeypatch) -> None:
        """json.dumps TypeError on non-serializable values returns False (degraded)."""
        from pathlib import Path

        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        assert MODULE._append_log({"path": Path("/tmp")}) is False


# ---------------------------------------------------------------------------
# TestMain
# ---------------------------------------------------------------------------


class TestMain:
    def test_dialogue_end_to_end(self, tmp_path, monkeypatch, capsys) -> None:
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_dialogue_input()))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0
        assert not input_file.exists()  # cleaned up

        output = json.loads(capsys.readouterr().out.strip())
        assert output["status"] == "ok"

        event = json.loads(log_path.read_text().strip())
        assert event["event"] == "dialogue_outcome"
        assert event["schema_version"] == "0.1.0"
        assert event["resolved_count"] == 5

    def test_consultation_end_to_end(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_consultation_input()))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0

        event = json.loads(log_path.read_text().strip())
        assert event["event"] == "consultation_outcome"
        assert "convergence_reason_code" not in event

    def test_invalid_json(self, tmp_path, monkeypatch, capsys) -> None:
        input_file = tmp_path / "bad.json"
        input_file.write_text("not json")
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out.strip())
        assert output["status"] == "error"

    def test_unknown_event_type(self, tmp_path, monkeypatch, capsys) -> None:
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"event_type": "unknown"}))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out.strip())
        assert output["status"] == "error"

    def test_missing_file(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "sys.argv", ["emit_analytics.py", "/nonexistent/input.json"]
        )
        exit_code = MODULE.main()
        assert exit_code == 1

    def test_no_args(self, monkeypatch) -> None:
        monkeypatch.setattr("sys.argv", ["emit_analytics.py"])
        exit_code = MODULE.main()
        assert exit_code == 1

    def test_degraded_on_write_failure(self, tmp_path, monkeypatch, capsys) -> None:
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        log_path = readonly_dir / "events.jsonl"
        readonly_dir.chmod(0o444)
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_consultation_input()))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 2  # degraded: distinct from success (0) and error (1)
        output = json.loads(capsys.readouterr().out.strip())
        assert output["status"] == "degraded"
        readonly_dir.chmod(0o755)  # cleanup

    def test_input_cleanup_on_validation_error(self, tmp_path, monkeypatch) -> None:
        """Input file must be deleted even when validation fails."""
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"event_type": "unknown_type"}))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        MODULE.main()
        assert not input_file.exists()  # cleaned up despite error

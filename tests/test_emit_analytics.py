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
    "provenance_unknown_count": 0,
    "scout_count": 3,
    "mode": "server_assisted",
    # Planning fields (None = --plan not used)
    "question_shaped": None,
    "shape_confidence": None,
    "assumptions_generated_count": None,
    "ambiguity_count": None,
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


def _pipeline_with_planning(
    question_shaped: bool = True,
    shape_confidence: str = "high",
    assumptions_generated_count: int = 3,
    ambiguity_count: int = 1,
    **overrides,
) -> dict:
    return {
        **SAMPLE_PIPELINE,
        "question_shaped": question_shaped,
        "shape_confidence": shape_confidence,
        "assumptions_generated_count": assumptions_generated_count,
        "ambiguity_count": ambiguity_count,
        **overrides,
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
            "provenance_unknown_count": None,
            "question_shaped": None,
            "shape_confidence": None,
            "assumptions_generated_count": None,
            "ambiguity_count": None,
        },
    }


# ---------------------------------------------------------------------------
# TestSplitSections
# ---------------------------------------------------------------------------


class TestSplitSections:
    def test_basic_split(self) -> None:
        text = "### Section One\ncontent one\n### Section Two\ncontent two\n"
        result, truncated = MODULE._split_sections(text)
        assert "section one" in result
        assert "section two" in result
        assert truncated is False

    def test_case_normalized_keys(self) -> None:
        text = "### Synthesis Checkpoint\nstuff\n### Synthesis checkpoint\nmore\n"
        result, _ = MODULE._split_sections(text)
        assert "synthesis checkpoint" in result

    def test_strips_fenced_blocks(self) -> None:
        text = "### Outer\n```\n## Inner Header\ncontent\n```\n"
        result, truncated = MODULE._split_sections(text)
        assert "inner header" not in result
        assert "outer" in result
        assert truncated is False  # matched pair, not truncation

    def test_nested_fence_with_level2_header(self) -> None:
        """Regression: ## Synthesis Checkpoint inside code fence must not create section."""
        text = (
            "### Synthesis Checkpoint\n"
            "```\n"
            "## Synthesis Checkpoint\n"
            "RESOLVED: item [confidence: High]\n"
            "```\n"
        )
        result, _ = MODULE._split_sections(text)
        # Only one section, from the ### header
        assert len(result) == 1
        assert "synthesis checkpoint" in result

    def test_unclosed_fence_stripped(self) -> None:
        """Unclosed fence should not create spurious section headers."""
        text = "### Before\ncontent\n```\n## Inside Unclosed\nmore\n"
        result, truncated = MODULE._split_sections(text)
        assert "inside unclosed" not in result
        assert "before" in result
        assert truncated is True

    def test_unclosed_fence_no_content_loss(self) -> None:
        """Content before an unclosed fence is preserved."""
        text = "### Summary\nreal content\n```\n## Fake\ngarbage\n"
        result, truncated = MODULE._split_sections(text)
        assert "real content" in result.get("summary", "")
        assert truncated is True

    def test_unclosed_fence_with_lang_stripped(self) -> None:
        """Unclosed fence with language specifier is also stripped."""
        text = "### Before\ncontent\n```python\n## Inside\ncode\n"
        result, truncated = MODULE._split_sections(text)
        assert "inside" not in result
        assert "before" in result
        assert truncated is True

    def test_multiple_unclosed_fences_stripped(self) -> None:
        """Multiple unclosed fences: first pass pairs them, second pass catches remainder."""
        text = "### Before\ncontent\n```\nmid\n```\n## After Pair\nok\n```\n## Trailing\nlost\n"
        result, truncated = MODULE._split_sections(text)
        # The paired fences are stripped by pass 1, "After Pair" survives,
        # the trailing unclosed fence and "Trailing" are stripped by pass 2.
        assert "trailing" not in result
        assert "before" in result
        assert truncated is True


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

    def test_unclosed_fence_does_not_corrupt_fields(self) -> None:
        """Unclosed fence should not corrupt converged/turn_count/scout_count."""
        text = (
            "### Conversation Summary\n"
            "- **Converged:** Yes\n"
            "- **Turns:** 5 of 8\n"
            "- **Evidence:** 2 scouts / 5 turns\n"
            "\n```\n"
            "## Fake Section\n"
            "- **Converged:** No\n"
            "- **Turns:** 99 of 100\n"
        )
        result = MODULE.parse_synthesis(text)
        assert result["converged"] is True
        assert result["turn_count"] == 5
        assert result["scout_count"] == 2
        assert result["parse_truncated"] is True

    def test_parse_truncated_false_for_clean_synthesis(self) -> None:
        """Clean synthesis without unclosed fences has parse_truncated=False."""
        text = (
            "### Conversation Summary\n"
            "- **Converged:** Yes\n"
            "- **Turns:** 3 of 6\n"
            "- **Evidence:** 1 scout / 3 turns\n"
        )
        result = MODULE.parse_synthesis(text)
        assert result["parse_truncated"] is False


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

    def test_error_zero_unresolved(self) -> None:
        """Error fallback: not converged, zero unresolved, under budget."""
        assert MODULE.map_convergence(False, 0, 3, 8) == ("error", "error")

    def test_error_nonzero_unresolved(self) -> None:
        """Error fallback: not converged, unresolved remain, under budget."""
        assert MODULE.map_convergence(False, 5, 3, 8) == ("error", "error")

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
            "schema_version",
            "consultation_id",
            "thread_id",
            "session_id",
            "event",
            "ts",
            "posture",
            "turn_count",
            "turn_budget",
            "profile_name",
            "mode",
            "mode_source",
            "converged",
            "convergence_reason_code",
            "termination_reason",
            "resolved_count",
            "unresolved_count",
            "emerged_count",
            "seed_confidence",
            "low_seed_confidence_reasons",
            "assumption_count",
            "no_assumptions_fallback",
            "gatherer_a_lines",
            "gatherer_b_lines",
            "gatherer_a_retry",
            "gatherer_b_retry",
            "citations_total",
            "unique_files_total",
            "gatherer_a_unique_paths",
            "gatherer_b_unique_paths",
            "shared_citation_paths",
            "counter_count",
            "confirm_count",
            "open_count",
            "claim_count",
            "scout_count",
            "source_classes",
            "scope_root_count",
            "scope_roots_fingerprint",
            "question_shaped",
            "shape_confidence",
            "assumptions_generated_count",
            "ambiguity_count",
            "provenance_unknown_count",
            "episode_id",
            "parse_truncated",
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

    def test_session_id_empty_string(self, monkeypatch) -> None:
        """Empty string CLAUDE_SESSION_ID is normalized to None."""
        monkeypatch.setenv("CLAUDE_SESSION_ID", "")
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
        assert event["episode_id"] is None

    def test_scope_breach_event(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input(scope_breach=True))
        assert event["convergence_reason_code"] == "scope_breach"
        assert event["termination_reason"] == "scope_breach"

    def test_provenance_unknown_count_from_pipeline(self) -> None:
        """provenance_unknown_count flows from pipeline when provided."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["provenance_unknown_count"] == 3

    def test_provenance_unknown_count_none_when_absent(self) -> None:
        """provenance_unknown_count defaults to None when not in pipeline."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": None}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["provenance_unknown_count"] is None

    def test_schema_version_bumps_with_provenance(self) -> None:
        """schema_version auto-bumps to 0.2.0 when provenance_unknown_count is non-null."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 0}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.2.0"

    def test_schema_version_stays_without_provenance(self) -> None:
        """schema_version stays 0.1.0 when provenance_unknown_count is None."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": None}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.1.0"

    def test_provenance_unknown_count_explicit_none_schema_stays(self) -> None:
        """schema_version stays 0.1.0 when provenance_unknown_count is explicitly None."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": None}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.1.0"
        assert event["provenance_unknown_count"] is None

    def test_provenance_unknown_count_bool_pipeline_no_schema_bump(self) -> None:
        """Bool pipeline.provenance_unknown_count does NOT trigger schema bump."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": True}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        # Helper rejects bool — schema stays at base version
        assert event["schema_version"] == "0.1.0"

    def test_provenance_unknown_count_string_pipeline_no_schema_bump(self) -> None:
        """String pipeline.provenance_unknown_count does NOT trigger schema bump."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": "3"}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        # Helper rejects string — schema stays at base version
        assert event["schema_version"] == "0.1.0"

    def test_provenance_unknown_count_float_pipeline_no_schema_bump(self) -> None:
        """Float pipeline.provenance_unknown_count does NOT trigger schema bump."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 0.0}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        # Helper rejects float — schema stays at base version
        assert event["schema_version"] == "0.1.0"

    # --- Planning field build tests ---

    def test_schema_version_bumps_with_planning(self) -> None:
        """schema_version auto-bumps to 0.3.0 when question_shaped is non-None."""
        pipeline = _pipeline_with_planning()
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.3.0"

    def test_schema_version_bumps_with_planning_false(self) -> None:
        """schema_version 0.3.0 even when question_shaped=False (failure telemetry)."""
        pipeline = _pipeline_with_planning(question_shaped=False)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.3.0"

    def test_planning_fields_propagated_from_pipeline(self) -> None:
        """All 4 planning fields propagate from pipeline input."""
        pipeline = _pipeline_with_planning(
            question_shaped=True,
            shape_confidence="medium",
            assumptions_generated_count=5,
            ambiguity_count=2,
        )
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["question_shaped"] is True
        assert event["shape_confidence"] == "medium"
        assert event["assumptions_generated_count"] == 5
        assert event["ambiguity_count"] == 2

    def test_planning_none_when_absent(self) -> None:
        """Planning fields default to None when not in pipeline."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["question_shaped"] is None
        assert event["shape_confidence"] is None
        assert event["assumptions_generated_count"] is None
        assert event["ambiguity_count"] is None

    def test_planning_precedence_over_provenance(self) -> None:
        """schema_version 0.3.0 takes precedence when both planning and provenance active."""
        pipeline = _pipeline_with_planning(provenance_unknown_count=3)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.3.0"

    def test_planning_nonbool_question_shaped_still_bumps(self) -> None:
        """Non-bool question_shaped triggers 0.3.0 (resolver checks is not None, validation catches type)."""
        pipeline = {**SAMPLE_PIPELINE, "question_shaped": "yes"}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.3.0"

    def test_planning_question_shaped_false_all_fields_present(self) -> None:
        """question_shaped=False still propagates all planning fields."""
        pipeline = _pipeline_with_planning(
            question_shaped=False,
            shape_confidence="low",
            assumptions_generated_count=0,
            ambiguity_count=0,
        )
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["question_shaped"] is False
        assert event["shape_confidence"] == "low"

    def test_resolve_schema_version_base(self) -> None:
        """_resolve_schema_version returns 0.1.0 with no feature flags."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": None}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert MODULE._resolve_schema_version(event) == "0.1.0"

    def test_resolve_schema_version_planning_over_provenance(self) -> None:
        """_resolve_schema_version returns 0.3.0 when both planning and provenance present."""
        pipeline = _pipeline_with_planning(provenance_unknown_count=3)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert MODULE._resolve_schema_version(event) == "0.3.0"
        # Verify provenance field is also present (not just planning winning by absence)
        assert event["provenance_unknown_count"] == 3

    # --- Planning hardening tests ---

    def test_planning_bool_shape_confidence_passes_through(self) -> None:
        """Bool shape_confidence from pipeline passes through (validation catches)."""
        pipeline = _pipeline_with_planning(shape_confidence=True)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["shape_confidence"] is True

    def test_planning_negative_assumptions_count_passes_through(self) -> None:
        """Negative assumptions_generated_count passes through (validation catches)."""
        pipeline = _pipeline_with_planning(assumptions_generated_count=-1)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["assumptions_generated_count"] == -1

    def test_planning_float_ambiguity_count_passes_through(self) -> None:
        """Float ambiguity_count passes through (validation catches)."""
        pipeline = _pipeline_with_planning(ambiguity_count=1.5)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["ambiguity_count"] == 1.5

    def test_planning_string_count_passes_through(self) -> None:
        """String assumptions_generated_count passes through (validation catches)."""
        pipeline = _pipeline_with_planning(assumptions_generated_count="3")
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["assumptions_generated_count"] == "3"

    def test_mode_from_pipeline(self) -> None:
        """mode field propagates from pipeline input."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["mode"] == "server_assisted"

    def test_mode_manual_legacy(self) -> None:
        """manual_legacy mode propagates correctly."""
        pipeline = {**SAMPLE_PIPELINE, "mode": "manual_legacy"}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["mode"] == "manual_legacy"

    def test_mode_source_epilogue_propagated(self) -> None:
        """mode_source='epilogue' is propagated from pipeline input."""
        pipeline = {**SAMPLE_PIPELINE, "mode_source": "epilogue"}
        inp = _dialogue_input(pipeline=pipeline)
        event = MODULE.build_dialogue_outcome(inp)
        assert event["mode_source"] == "epilogue"

    def test_mode_source_fallback_propagated(self) -> None:
        """mode_source='fallback' is propagated from pipeline input."""
        pipeline = {**SAMPLE_PIPELINE, "mode_source": "fallback"}
        inp = _dialogue_input(pipeline=pipeline)
        event = MODULE.build_dialogue_outcome(inp)
        assert event["mode_source"] == "fallback"

    def test_mode_source_none_when_omitted(self) -> None:
        """mode_source defaults to None when not in pipeline input."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["mode_source"] is None

    def test_mode_source_absent_from_consultation_outcome(self) -> None:
        """mode_source must not be present in consultation_outcome events (D1: absent, not None)."""
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert "mode_source" not in event


# ---------------------------------------------------------------------------
# TestBuildConsultationOutcome
# ---------------------------------------------------------------------------


class TestBuildConsultationOutcome:
    def test_field_count(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert len(event) == 18

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

    def test_schema_version_base(self) -> None:
        """Consultation events default to base schema 0.1.0 when feature-flag fields are absent."""
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["schema_version"] == "0.1.0"

    def test_session_id_propagated(self, monkeypatch) -> None:
        monkeypatch.setenv("CLAUDE_SESSION_ID", "sess-consult-456")
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["session_id"] == "sess-consult-456"

    def test_ts_format(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["ts"].endswith("Z")
        assert "T" in event["ts"]

    def test_consultation_id_is_uuid(self) -> None:
        import uuid as uuid_mod

        event = MODULE.build_consultation_outcome(_consultation_input())
        uuid_mod.UUID(event["consultation_id"])  # raises on invalid

    def test_mode_from_pipeline(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["mode"] == "server_assisted"

    def test_mode_manual_legacy(self) -> None:
        """manual_legacy mode propagates through consultation_outcome."""
        pipeline = {
            "posture": "collaborative",
            "thread_id": None,
            "turn_count": 1,
            "turn_budget": 1,
            "profile_name": None,
            "mode": "manual_legacy",
            "provenance_unknown_count": None,
            "question_shaped": None,
            "shape_confidence": None,
            "assumptions_generated_count": None,
            "ambiguity_count": None,
        }
        event = MODULE.build_consultation_outcome(_consultation_input(pipeline))
        assert event["mode"] == "manual_legacy"

    def test_schema_version_uses_resolver(self) -> None:
        """consultation_outcome uses _resolve_schema_version like dialogue_outcome."""
        pipeline = {
            "posture": "collaborative",
            "thread_id": "thread-xyz-789",
            "turn_count": 1,
            "turn_budget": 1,
            "profile_name": None,
            "mode": "server_assisted",
            "provenance_unknown_count": 0,
            "question_shaped": None,
            "shape_confidence": None,
            "assumptions_generated_count": None,
            "ambiguity_count": None,
        }
        event = MODULE.build_consultation_outcome(_consultation_input(pipeline))
        # With provenance_unknown_count=0 (non-negative int), resolver returns 0.2.0
        assert event["schema_version"] == "0.2.0"

    def test_reverse_invariant_consultation(self) -> None:
        """Stray shape_confidence without question_shaped triggers validation error."""
        pipeline = {
            "posture": "collaborative",
            "thread_id": None,
            "turn_count": 1,
            "turn_budget": 1,
            "profile_name": None,
            "mode": "server_assisted",
            "provenance_unknown_count": None,
            "question_shaped": None,
            "shape_confidence": "high",
            "assumptions_generated_count": None,
            "ambiguity_count": None,
        }
        event = MODULE.build_consultation_outcome(_consultation_input(pipeline))
        with pytest.raises(ValueError, match="shape_confidence"):
            MODULE.validate(event, "consultation_outcome")

    def test_schema_version_with_planning(self) -> None:
        """consultation_outcome bumps to 0.3.0 when question_shaped is set."""
        pipeline = {
            "posture": "collaborative",
            "thread_id": None,
            "turn_count": 1,
            "turn_budget": 1,
            "profile_name": "planning",
            "mode": "server_assisted",
            "provenance_unknown_count": None,
            "question_shaped": True,
            "shape_confidence": "high",
            "assumptions_generated_count": 3,
            "ambiguity_count": 1,
        }
        event = MODULE.build_consultation_outcome(_consultation_input(pipeline))
        assert event["schema_version"] == "0.3.0"


# ---------------------------------------------------------------------------
# TestPipelineCompleteness
# ---------------------------------------------------------------------------


class TestPipelineCompleteness:
    """Verify test helpers produce complete pipeline dicts matching builder expectations."""

    def test_dialogue_pipeline_keys_cover_builder(self) -> None:
        """All pipeline.get() keys in build_dialogue_outcome have explicit values."""
        pipeline = _dialogue_input()["pipeline"]
        builder_keys = {
            "posture",
            "turn_budget",
            "profile_name",
            "seed_confidence",
            "low_seed_confidence_reasons",
            "assumption_count",
            "no_assumptions_fallback",
            "gatherer_a_lines",
            "gatherer_b_lines",
            "gatherer_a_retry",
            "gatherer_b_retry",
            "citations_total",
            "unique_files_total",
            "gatherer_a_unique_paths",
            "gatherer_b_unique_paths",
            "shared_citation_paths",
            "counter_count",
            "confirm_count",
            "open_count",
            "claim_count",
            "scout_count",
            "source_classes",
            "scope_root_count",
            "scope_roots_fingerprint",
            "question_shaped",
            "shape_confidence",
            "assumptions_generated_count",
            "ambiguity_count",
            "provenance_unknown_count",
            "mode",
        }
        assert builder_keys.issubset(set(pipeline.keys())), (
            f"Missing pipeline keys: {builder_keys - set(pipeline.keys())}"
        )

    def test_consultation_pipeline_keys_cover_builder(self) -> None:
        """All pipeline.get() keys in build_consultation_outcome have explicit values."""
        pipeline = _consultation_input()["pipeline"]
        builder_keys = {
            "thread_id",
            "posture",
            "turn_count",
            "turn_budget",
            "profile_name",
            "mode",
            "provenance_unknown_count",
            "question_shaped",
            "shape_confidence",
            "assumptions_generated_count",
            "ambiguity_count",
        }
        assert builder_keys.issubset(set(pipeline.keys())), (
            f"Missing pipeline keys: {builder_keys - set(pipeline.keys())}"
        )


# ---------------------------------------------------------------------------
# TestIsNonNegativeInt
# ---------------------------------------------------------------------------


class TestIsNonNegativeInt:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (0, True),
            (1, True),
            (100, True),
            (-1, False),
            (True, False),
            (False, False),
            (0.0, False),
            (3.5, False),
            ("5", False),
            (None, False),
        ],
    )
    def test_is_non_negative_int(self, value: object, expected: bool) -> None:
        assert MODULE._is_non_negative_int(value) is expected


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
            _consultation_input(
                {"posture": "collaborative", "turn_count": 3, "turn_budget": 1}
            )
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
        with pytest.raises(
            ValueError, match="source_classes must contain only strings"
        ):
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
        with pytest.raises(
            ValueError, match="low_seed_confidence_reasons must be a list"
        ):
            MODULE.validate(event, "dialogue_outcome")

    def test_low_seed_confidence_reasons_non_string_items(self) -> None:
        """low_seed_confidence_reasons items must be strings."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = [1, 2]
        with pytest.raises(
            ValueError, match="low_seed_confidence_reasons must contain only strings"
        ):
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
            "thin_citations",
            "few_files",
            "zero_output",
            "provenance_violations",
        ]
        MODULE.validate(event, "dialogue_outcome")  # no exception

    @pytest.mark.parametrize(
        "reasons",
        [
            ["few_files", "bad_reason"],
            ["thin_citations", "provenance_violations", "oops"],
            ["bad_reason", "few_files"],
        ],
    )
    def test_mixed_valid_invalid_low_seed_confidence_reasons_rejected(
        self, reasons: list[str]
    ) -> None:
        """Mixed valid and invalid low_seed_confidence_reasons are rejected."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = reasons
        with pytest.raises(ValueError, match="invalid low_seed_confidence_reasons"):
            MODULE.validate(event, "dialogue_outcome")

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

    def test_provenance_schema_version_cross_field_invariant(self) -> None:
        """provenance_unknown_count requires schema_version 0.2.0."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["schema_version"] = "0.1.0"
        with pytest.raises(ValueError, match="schema_version mismatch"):
            MODULE.validate(event, "dialogue_outcome")

    # --- Planning field validation tests ---

    def test_planning_tri_state_missing_shape_confidence(self) -> None:
        """question_shaped=True requires shape_confidence."""
        pipeline = _pipeline_with_planning(shape_confidence=None)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="shape_confidence is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_tri_state_missing_assumptions_count(self) -> None:
        """question_shaped=True requires assumptions_generated_count."""
        pipeline = _pipeline_with_planning(assumptions_generated_count=None)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="assumptions_generated_count is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_tri_state_missing_ambiguity_count(self) -> None:
        """question_shaped=True requires ambiguity_count."""
        pipeline = _pipeline_with_planning(ambiguity_count=None)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="ambiguity_count is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_tri_state_false_missing_companion(self) -> None:
        """question_shaped=False also requires companion fields (not just True)."""
        pipeline = _pipeline_with_planning(question_shaped=False, shape_confidence=None)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="shape_confidence is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_invalid_shape_confidence(self) -> None:
        """shape_confidence must be in valid set."""
        pipeline = _pipeline_with_planning(shape_confidence="very_high")
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="invalid shape_confidence"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_question_shaped_wrong_type(self) -> None:
        """question_shaped must be bool when non-None."""
        pipeline = {
            **SAMPLE_PIPELINE,
            "question_shaped": "yes",
            "shape_confidence": "high",
            "assumptions_generated_count": 3,
            "ambiguity_count": 1,
        }
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="question_shaped must be bool"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_schema_version_cross_field_invariant(self) -> None:
        """Planning active requires schema_version 0.3.0."""
        pipeline = _pipeline_with_planning()
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["schema_version"] = "0.2.0"
        with pytest.raises(ValueError, match="schema_version mismatch"):
            MODULE.validate(event, "dialogue_outcome")

    def test_provenance_schema_version_still_validated(self) -> None:
        """Provenance without planning still requires 0.2.0."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["schema_version"] = "0.1.0"
        with pytest.raises(ValueError, match="schema_version mismatch"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_valid_event_passes(self) -> None:
        """Fully valid planning event passes validation."""
        pipeline = _pipeline_with_planning()
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        MODULE.validate(event, "dialogue_outcome")

    # --- Reverse invariant tests ---

    def test_reverse_invariant_stray_shape_confidence(self) -> None:
        """question_shaped=None with stray shape_confidence rejects."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["shape_confidence"] = "high"
        with pytest.raises(
            ValueError,
            match="shape_confidence must be None when question_shaped is None",
        ):
            MODULE.validate(event, "dialogue_outcome")

    def test_reverse_invariant_stray_assumptions_count(self) -> None:
        """question_shaped=None with stray assumptions_generated_count rejects."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["assumptions_generated_count"] = 3
        with pytest.raises(
            ValueError,
            match="assumptions_generated_count must be None when question_shaped is None",
        ):
            MODULE.validate(event, "dialogue_outcome")

    def test_reverse_invariant_stray_ambiguity_count(self) -> None:
        """question_shaped=None with stray ambiguity_count rejects."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["ambiguity_count"] = 1
        with pytest.raises(
            ValueError,
            match="ambiguity_count must be None when question_shaped is None",
        ):
            MODULE.validate(event, "dialogue_outcome")

    # --- Error precedence test ---

    def test_planning_nonbool_no_companions_type_error_first(self) -> None:
        """Non-bool question_shaped without companions: type error takes precedence."""
        pipeline = {**SAMPLE_PIPELINE, "question_shaped": "yes"}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="question_shaped must be bool"):
            MODULE.validate(event, "dialogue_outcome")

    # --- Emerged tests from adversarial review ---

    def test_planning_valid_event_false_passes(self) -> None:
        """question_shaped=False with all companions present passes validation."""
        pipeline = _pipeline_with_planning(question_shaped=False)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        MODULE.validate(event, "dialogue_outcome")  # Should not raise

    def test_planning_count_fields_negative_rejected(self) -> None:
        """Negative assumptions_generated_count fails _COUNT_FIELDS validation."""
        pipeline = _pipeline_with_planning(assumptions_generated_count=-1)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="assumptions_generated_count"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_float_ambiguity_count_rejected(self) -> None:
        """Float ambiguity_count fails _COUNT_FIELDS validation (must be int >= 0)."""
        pipeline = _pipeline_with_planning(ambiguity_count=1.5)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="ambiguity_count"):
            MODULE.validate(event, "dialogue_outcome")

    def test_mode_source_invalid_value_rejected(self) -> None:
        """Invalid mode_source enum value is rejected."""
        pipeline = {**SAMPLE_PIPELINE, "mode_source": "invented"}
        inp = _dialogue_input(pipeline=pipeline)
        event = MODULE.build_dialogue_outcome(inp)
        with pytest.raises(ValueError, match="invalid mode_source"):
            MODULE.validate(event, "dialogue_outcome")

    def test_mode_source_rejected_on_consultation(self) -> None:
        """Non-None mode_source on consultation_outcome is rejected."""
        inp = _consultation_input()
        event = MODULE.build_consultation_outcome(inp)
        event["mode_source"] = "epilogue"  # manually inject
        with pytest.raises(ValueError, match="mode_source"):
            MODULE.validate(event, "consultation_outcome")

    def test_mode_source_valid_values_pass_validation(self) -> None:
        """Valid mode_source values ('epilogue', 'fallback') pass validation without error."""
        for ms in ("epilogue", "fallback"):
            pipeline = {**SAMPLE_PIPELINE, "mode_source": ms}
            inp = _dialogue_input(pipeline=pipeline)
            event = MODULE.build_dialogue_outcome(inp)
            MODULE.validate(event, "dialogue_outcome")  # should not raise

    def test_mode_source_non_hashable_raises_value_error(self) -> None:
        """Non-hashable mode_source (e.g. dict) raises ValueError, not TypeError."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["mode_source"] = {"nested": "object"}
        with pytest.raises(ValueError, match="invalid mode_source"):
            MODULE.validate(event, "dialogue_outcome")

    def test_null_episode_id_passes_validation(self) -> None:
        """episode_id=None should not cause validation errors (reserved nullable)."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["episode_id"] is None
        # Validation should pass — episode_id is not in _DIALOGUE_REQUIRED
        MODULE.validate(event, "dialogue_outcome")  # no exception = pass

    def test_episode_id_not_required(self) -> None:
        """episode_id must NOT be in _DIALOGUE_REQUIRED (reserved nullable)."""
        assert "episode_id" not in MODULE._DIALOGUE_REQUIRED


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

    def test_typeerror_propagates(self, tmp_path, monkeypatch) -> None:
        """json.dumps TypeError on non-serializable values propagates (code bug, not I/O)."""
        from pathlib import Path

        import pytest

        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        with pytest.raises(TypeError):
            MODULE._append_log({"path": Path("/tmp")})


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
        assert (
            event["schema_version"] == "0.2.0"
        )  # SAMPLE_PIPELINE has provenance_unknown_count=0
        assert event["resolved_count"] == 5

    def test_dialogue_provenance_end_to_end(self, tmp_path, monkeypatch) -> None:
        """E2E: provenance_unknown_count triggers schema_version 0.2.0 in log."""
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 5}
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_dialogue_input(pipeline=pipeline)))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0

        event = json.loads(log_path.read_text().strip())
        assert event["schema_version"] == "0.2.0"
        assert event["provenance_unknown_count"] == 5

    def test_dialogue_planning_end_to_end(self, tmp_path, monkeypatch) -> None:
        """E2E: planning fields trigger schema_version 0.3.0 in log."""
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        pipeline = _pipeline_with_planning()
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_dialogue_input(pipeline=pipeline)))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0

        event = json.loads(log_path.read_text().strip())
        assert event["schema_version"] == "0.3.0"
        assert event["question_shaped"] is True
        assert event["shape_confidence"] == "high"

    def test_dialogue_planning_and_provenance_end_to_end(
        self, tmp_path, monkeypatch
    ) -> None:
        """E2E: planning takes precedence over provenance for schema_version."""
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        pipeline = _pipeline_with_planning(provenance_unknown_count=5)
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_dialogue_input(pipeline=pipeline)))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0

        event = json.loads(log_path.read_text().strip())
        assert event["schema_version"] == "0.3.0"
        assert event["provenance_unknown_count"] == 5

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


# ---------------------------------------------------------------------------
# TestReplayConformance
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(FIXTURE_DIR / name) as f:
        return json.load(f)


class TestReplayConformance:
    """Replay realistic dialogue/consultation inputs through the emitter.

    These fixtures simulate actual codex-dialogue outputs, validating that
    emit_analytics.py produces correct events for real-world scenarios.
    """

    def test_converged_dialogue_turn_count(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["turn_count"] == 6
        assert event["turn_budget"] == 8
        assert event["turn_count"] >= 1, "multi-turn dialogue must have turn_count >= 1"

    def test_converged_dialogue_thread_id(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["thread_id"] == "019c819e-dc16-79d3-825b-0d54b23627ea"
        assert event["thread_id"] is not None, (
            "converged dialogue should have thread_id"
        )

    def test_converged_dialogue_convergence(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["converged"] is True
        assert event["convergence_reason_code"] == "natural_convergence"
        assert event["resolved_count"] == 7
        assert event["unresolved_count"] == 1
        assert event["emerged_count"] == 2

    def test_all_resolved_dialogue_convergence(self) -> None:
        """Fixture with 0 UNRESOLVED lines produces all_resolved."""
        fixture = _load_fixture("dialogue_converged.json")
        # Patch synthesis to have 0 UNRESOLVED lines
        fixture["synthesis_text"] = fixture["synthesis_text"].replace(
            "UNRESOLVED: Learning card retrieval failure interaction [raised: turn 3]\n",
            "",
        )
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["converged"] is True
        assert event["convergence_reason_code"] == "all_resolved"
        assert event["unresolved_count"] == 0

    def test_converged_dialogue_schema_version(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        # provenance_unknown_count=0 (non-negative int) -> 0.2.0
        assert event["schema_version"] == "0.2.0"

    def test_converged_dialogue_validates(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        MODULE.validate(event, "dialogue_outcome")  # no exception = pass

    def test_scope_breach_convergence(self) -> None:
        fixture = _load_fixture("dialogue_scope_breach.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["converged"] is False
        assert event["convergence_reason_code"] == "scope_breach"
        assert event["termination_reason"] == "scope_breach"
        assert event["turn_count"] == 1

    def test_scope_breach_validates(self) -> None:
        fixture = _load_fixture("dialogue_scope_breach.json")
        event = MODULE.build_dialogue_outcome(fixture)
        MODULE.validate(event, "dialogue_outcome")

    def test_planning_schema_version(self) -> None:
        fixture = _load_fixture("dialogue_with_planning.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["question_shaped"] is True
        assert event["schema_version"] == "0.3.0"
        assert event["shape_confidence"] == "high"
        assert event["assumptions_generated_count"] == 3
        assert event["ambiguity_count"] == 1

    def test_planning_validates(self) -> None:
        fixture = _load_fixture("dialogue_with_planning.json")
        event = MODULE.build_dialogue_outcome(fixture)
        MODULE.validate(event, "dialogue_outcome")

    def test_manual_legacy_mode(self) -> None:
        fixture = _load_fixture("dialogue_manual_legacy.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["mode"] == "manual_legacy"
        assert event["seed_confidence"] == "low"

    def test_manual_legacy_validates(self) -> None:
        fixture = _load_fixture("dialogue_manual_legacy.json")
        event = MODULE.build_dialogue_outcome(fixture)
        MODULE.validate(event, "dialogue_outcome")

    def test_consultation_simple(self) -> None:
        fixture = _load_fixture("consultation_simple.json")
        event = MODULE.build_consultation_outcome(fixture)
        assert event["turn_count"] == 1
        assert event["turn_budget"] == 1
        assert event["mode"] == "server_assisted"
        assert event["schema_version"] == "0.1.0"

    def test_consultation_simple_validates(self) -> None:
        fixture = _load_fixture("consultation_simple.json")
        event = MODULE.build_consultation_outcome(fixture)
        MODULE.validate(event, "consultation_outcome")

    def test_all_fixtures_load(self) -> None:
        """Verify all fixture files are loadable JSON."""
        fixture_files = sorted(FIXTURE_DIR.glob("*.json"))
        assert len(fixture_files) >= 5, (
            f"expected >= 5 fixtures, got {len(fixture_files)}"
        )
        for f in fixture_files:
            data = json.loads(f.read_text())
            assert "event_type" in data or "pipeline" in data

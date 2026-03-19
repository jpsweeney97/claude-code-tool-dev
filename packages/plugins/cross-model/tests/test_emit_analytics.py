"""Tests for emit_analytics posture validation."""

from __future__ import annotations

import pytest

from scripts.emit_analytics import (
    _parse_epilogue,
    build_dialogue_outcome,
    parse_synthesis,
    validate,
)


def _make_dialogue_event(**overrides: object) -> dict:
    """Build a minimal valid dialogue_outcome event for testing."""
    event = {
        "schema_version": "0.1.0",
        "consultation_id": "test-id",
        "event": "dialogue_outcome",
        "ts": "2026-01-01T00:00:00Z",
        "posture": "evaluative",
        "turn_count": 3,
        "turn_budget": 8,
        "converged": True,
        "convergence_reason_code": "natural_convergence",
        "termination_reason": "convergence",
        "resolved_count": 2,
        "unresolved_count": 0,
        "emerged_count": 1,
        "seed_confidence": "normal",
        "mode": "server_assisted",
    }
    event.update(overrides)
    return event


def _make_delegation_event(**overrides: object) -> dict:
    """Build a minimal valid delegation_outcome event for testing."""
    event = {
        "schema_version": "0.1.0",
        "event": "delegation_outcome",
        "ts": "2026-01-01T00:00:00Z",
        "consultation_id": "test-id",
        "session_id": "test-session",
        "thread_id": None,
        "dispatched": True,
        "sandbox": "workspace-write",
        "full_auto": False,
        "credential_blocked": False,
        "dirty_tree_blocked": False,
        "readable_secret_file_blocked": False,
        "commands_run_count": 0,
        "exit_code": 0,
        "termination_reason": "complete",
        "model": None,
        "reasoning_effort": "high",
    }
    event.update(overrides)
    return event


class TestPostureValidation:
    """Posture enum validation in validate()."""

    def test_comparative_posture_accepted(self) -> None:
        """comparative is a valid posture value (Release A taxonomy)."""
        event = _make_dialogue_event(posture="comparative")
        # validate raises on failure, returns None on success
        validate(event, "dialogue_outcome")

    def test_known_postures_accepted(self) -> None:
        """All 5 postures pass validation."""
        for posture in (
            "adversarial",
            "collaborative",
            "exploratory",
            "evaluative",
            "comparative",
        ):
            event = _make_dialogue_event(posture=posture)
            validate(event, "dialogue_outcome")

    def test_invalid_posture_rejected(self) -> None:
        """Unknown posture raises ValueError."""
        event = _make_dialogue_event(posture="aggressive")
        with pytest.raises(ValueError, match="invalid posture"):
            validate(event, "dialogue_outcome")


def test_parse_epilogue_valid() -> None:
    synthesis = """
### Conversation Summary
- ignored by parser

```json
<!-- pipeline-data -->
{
  "mode": "manual_legacy",
  "thread_id": "thread-123",
  "turn_count": 4,
  "converged": true,
  "convergence_reason_code": "all_resolved",
  "termination_reason": "convergence",
  "scout_count": 0,
  "resolved_count": 3,
  "unresolved_count": 0,
  "emerged_count": 1,
  "scope_breach_count": 0
}
```
"""
    payload, warnings = _parse_epilogue(synthesis)

    assert warnings == []
    assert payload == {
        "mode": "manual_legacy",
        "thread_id": "thread-123",
        "turn_count": 4,
        "converged": True,
        "convergence_reason_code": "all_resolved",
        "termination_reason": "convergence",
        "scout_count": 0,
        "resolved_count": 3,
        "unresolved_count": 0,
        "emerged_count": 1,
        "scope_breach_count": 0,
    }


def test_parse_epilogue_missing() -> None:
    payload, warnings = _parse_epilogue("### Conversation Summary\nNo epilogue here.\n")

    assert payload is None
    assert warnings == ["pipeline-data epilogue missing"]


def test_parse_epilogue_malformed_json() -> None:
    synthesis = """
<!-- pipeline-data -->
```json
{
  "turn_count": 2,
  "converged": true,
}
```
"""
    payload, warnings = _parse_epilogue(synthesis)

    assert payload is None
    assert warnings
    assert warnings[0].startswith("pipeline-data epilogue malformed:")


def test_parse_synthesis_epilogue_preferred() -> None:
    synthesis = """
### Conversation Summary
- **Converged:** no
- **Turns:** 9
- **Evidence:** 7 scouts / 9 turns

### Continuation
- **Thread ID:** `markdown-thread`

```text
RESOLVED: old issue
UNRESOLVED: old risk
EMERGED: old idea
```

```json
<!-- pipeline-data -->
{
  "mode": "manual_legacy",
  "thread_id": "epilogue-thread",
  "turn_count": 2,
  "converged": true,
  "convergence_reason_code": "all_resolved",
  "termination_reason": "convergence",
  "scout_count": 0,
  "resolved_count": 5,
  "unresolved_count": 0,
  "emerged_count": 1,
  "scope_breach_count": 0
}
```
"""
    parsed = parse_synthesis(synthesis)

    assert parsed["turn_count"] == 2
    assert parsed["converged"] is True
    assert parsed["thread_id"] == "epilogue-thread"
    assert parsed["scout_count"] == 0
    assert parsed["resolved_count"] == 5
    assert parsed["parse_failed"] is False


def test_parse_synthesis_markdown_fallback(capsys: pytest.CaptureFixture[str]) -> None:
    synthesis = """
### Conversation Summary
- **Converged:** yes
- **Turns:** 3 of 8
- **Evidence:** 2 scouts / 3 turns

### Continuation
- **Thread ID:** `fallback-thread`

```text
RESOLVED: item one
UNRESOLVED: item two
EMERGED: item three
```
"""
    parsed = parse_synthesis(synthesis)

    captured = capsys.readouterr()
    assert "epilogue missing or malformed, falling back to markdown parsing" in captured.err
    assert parsed["turn_count"] == 3
    assert parsed["converged"] is True
    assert parsed["thread_id"] == "fallback-thread"
    assert parsed["scout_count"] == 2
    assert parsed["resolved_count"] == 1
    assert parsed["unresolved_count"] == 1
    assert parsed["emerged_count"] == 1
    assert parsed["parse_failed"] is False


def test_parse_synthesis_both_fail(capsys: pytest.CaptureFixture[str]) -> None:
    synthesis = "Plain text without epilogue or recognizable markdown headings."

    parsed = parse_synthesis(synthesis)
    captured = capsys.readouterr()

    assert "epilogue missing or malformed, falling back to markdown parsing" in captured.err
    assert parsed["turn_count"] == 0
    assert parsed["converged"] is False
    assert parsed["thread_id"] is None
    assert parsed["scout_count"] == 0
    assert parsed["parse_failed"] is True

    # Should degrade gracefully instead of raising
    result = build_dialogue_outcome(
        {
            "pipeline": {"posture": "evaluative", "turn_budget": 4},
            "synthesis_text": synthesis,
            "scope_breach": False,
        }
    )
    assert result["convergence_reason_code"] == "error"
    assert result["termination_reason"] == "error"
    assert result["parse_degraded"] is True


def test_build_dialogue_outcome_invalid_epilogue_convergence_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invalid convergence_reason_code in epilogue is replaced by computed value."""
    # Epilogue has "convergence" (valid for termination_reason, NOT convergence_reason_code)
    synthesis = (
        "### Conversation Summary\n"
        "- **Converged:** Yes\n"
        "- **Turns:** 3\n"
        "\n"
        "```json\n"
        "<!-- pipeline-data -->\n"
        "{\n"
        '  "mode": "server_assisted",\n'
        '  "thread_id": "thread-1",\n'
        '  "turn_count": 3,\n'
        '  "converged": true,\n'
        '  "convergence_reason_code": "convergence",\n'
        '  "termination_reason": "convergence",\n'
        '  "scout_count": 1,\n'
        '  "resolved_count": 2,\n'
        '  "unresolved_count": 0,\n'
        '  "emerged_count": 1,\n'
        '  "scope_breach_count": 0\n'
        "}\n"
        "```\n"
    )
    result = build_dialogue_outcome(
        {
            "pipeline": {"posture": "evaluative", "turn_budget": 8},
            "synthesis_text": synthesis,
            "scope_breach": False,
        }
    )
    captured = capsys.readouterr()
    # Should have warned and fallen through to map_convergence
    assert "invalid epilogue convergence_reason_code" in captured.err
    # converged=True + unresolved=0 → all_resolved
    assert result["convergence_reason_code"] == "all_resolved"
    assert result["termination_reason"] == "convergence"


class TestDelegationOutcomeValidation:
    def test_valid_delegation_event_passes(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event()
        validate(event, "delegation_outcome")  # should not raise

    def test_blocked_termination_accepted_for_delegation(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event(termination_reason="blocked", dispatched=False,
                                       credential_blocked=True, exit_code=None)
        validate(event, "delegation_outcome")  # should not raise

    def test_blocked_termination_rejected_for_dialogue(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_dialogue_event(termination_reason="blocked")
        with pytest.raises(ValueError, match="invalid termination_reason"):
            validate(event, "dialogue_outcome")

    def test_convergence_rejected_for_delegation(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event(termination_reason="convergence")
        with pytest.raises(ValueError, match="invalid termination_reason"):
            validate(event, "delegation_outcome")

    def test_delegation_missing_field_raises(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event()
        del event["dispatched"]
        with pytest.raises(ValueError, match="missing required fields"):
            validate(event, "delegation_outcome")

    # --- Cross-field invariants (per Codex review) ---

    def test_complete_requires_dispatched_true(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event(termination_reason="complete", dispatched=False)
        with pytest.raises(ValueError, match="dispatched"):
            validate(event, "delegation_outcome")

    def test_blocked_requires_dispatched_false(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event(termination_reason="blocked", dispatched=True)
        with pytest.raises(ValueError, match="dispatched"):
            validate(event, "delegation_outcome")

    def test_blocked_requires_block_flag(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event(
            termination_reason="blocked", dispatched=False,
            credential_blocked=False, dirty_tree_blocked=False,
            readable_secret_file_blocked=False,
        )
        with pytest.raises(ValueError, match="block flag"):
            validate(event, "delegation_outcome")

    def test_commands_run_requires_dispatched(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event(commands_run_count=3, dispatched=False)
        with pytest.raises(ValueError, match="dispatched"):
            validate(event, "delegation_outcome")

    def test_exit_code_requires_dispatched(self) -> None:
        from scripts.emit_analytics import validate
        event = _make_delegation_event(exit_code=0, dispatched=False)
        with pytest.raises(ValueError, match="dispatched"):
            validate(event, "delegation_outcome")

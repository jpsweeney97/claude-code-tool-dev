# .claude/skills/audit-loop/tests/test_validate_state.py
"""Tests for validate_state module."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_validate_for_ship_passes_no_high(tmp_path):
    """--for ship passes when no high priority findings remain."""
    from validate_state import validate_for_ship
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)
    update_state(artifact, add_finding={
        "description": "Minor issue",
        "priority": "low",
    })

    result = validate_for_ship(artifact)

    assert result.ok


def test_validate_for_ship_fails_open_high(tmp_path):
    """--for ship fails when open high priority findings exist."""
    from validate_state import validate_for_ship
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)
    update_state(artifact, add_finding={
        "description": "Critical issue",
        "priority": "high",
    })

    result = validate_for_ship(artifact)

    assert not result.ok
    assert any("high" in e.lower() for e in result.errors)


def test_validate_for_iterate_passes_within_limit(tmp_path):
    """--for iterate passes when under cycle limit."""
    from validate_state import validate_for_iterate
    from state import create_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = validate_for_iterate(artifact)

    assert result.ok


def test_validate_for_iterate_fails_at_limit(tmp_path):
    """--for iterate fails at MAX_CYCLES."""
    from validate_state import validate_for_iterate
    from state import create_state
    from _common import MAX_CYCLES, get_state_path

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    # Set cycle to MAX_CYCLES
    state_path = get_state_path(artifact)
    state = json.loads(state_path.read_text())
    state["cycle"] = MAX_CYCLES
    state_path.write_text(json.dumps(state))

    result = validate_for_iterate(artifact)

    assert not result.ok
    assert "limit" in result.message.lower()

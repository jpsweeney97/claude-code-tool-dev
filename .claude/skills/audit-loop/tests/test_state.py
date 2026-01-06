"""Tests for state module."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_create_initializes_state(tmp_path):
    """create command initializes .audit.json with correct schema."""
    from state import create_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature\n\nDescription here.")

    result = create_state(artifact)

    assert result.ok
    state_path = tmp_path / "feature.audit.json"
    assert state_path.exists()

    state = json.loads(state_path.read_text())
    assert state["version"] == "1.0"
    assert state["artifact"] == str(artifact)
    assert state["phase"] == "stakes_assessment"
    assert state["cycle"] == 1
    assert state["findings"] == []


def test_create_fails_if_artifact_missing(tmp_path):
    """create fails when artifact doesn't exist."""
    from state import create_state

    artifact = tmp_path / "missing.md"
    result = create_state(artifact)

    assert not result.ok
    assert "not found" in result.message.lower()


def test_create_fails_if_state_exists(tmp_path):
    """create fails when .audit.json already exists."""
    from state import create_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    state_path = tmp_path / "feature.audit.json"
    state_path.write_text('{"existing": true}')

    result = create_state(artifact)

    assert not result.ok
    assert "exists" in result.message.lower()

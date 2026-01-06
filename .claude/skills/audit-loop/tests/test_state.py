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


# =============================================================================
# UPDATE TESTS
# =============================================================================


def test_update_phase(tmp_path):
    """update --phase transitions to new phase."""
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = update_state(artifact, phase="definition")

    assert result.ok
    state = result.data["state"]
    assert state["phase"] == "definition"


def test_update_phase_invalid(tmp_path):
    """update --phase rejects invalid phase."""
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = update_state(artifact, phase="invalid_phase")

    assert not result.ok
    assert "invalid phase" in result.message.lower()


def test_update_add_finding(tmp_path):
    """update --add-finding adds new finding with auto-ID."""
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = update_state(
        artifact,
        add_finding={
            "description": "Missing error handling",
            "confidence": "probable",
            "priority": "high",
            "evidence": "lines 45-50",
        },
    )

    assert result.ok
    state = result.data["state"]
    assert len(state["findings"]) == 1
    assert state["findings"][0]["id"] == "F1"
    assert state["findings"][0]["status"] == "open"


def test_update_next_cycle(tmp_path):
    """update --next-cycle increments cycle."""
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = update_state(artifact, next_cycle=True)

    assert result.ok
    assert result.data["state"]["cycle"] == 2


def test_update_cycle_limit(tmp_path):
    """update --next-cycle enforces MAX_CYCLES limit."""
    from state import create_state, update_state
    import json
    from _common import MAX_CYCLES, get_state_path

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    # Manually set cycle to MAX_CYCLES
    state_path = get_state_path(artifact)
    state = json.loads(state_path.read_text())
    state["cycle"] = MAX_CYCLES
    state_path.write_text(json.dumps(state))

    result = update_state(artifact, next_cycle=True)

    assert not result.ok
    assert "limit" in result.message.lower()


# =============================================================================
# VALIDATE TESTS
# =============================================================================


def test_validate_valid_state(tmp_path):
    """validate returns success for valid state."""
    from state import create_state, validate_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = validate_state(artifact)

    assert result.ok


def test_validate_missing_state(tmp_path):
    """validate fails when state doesn't exist."""
    from state import validate_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")

    result = validate_state(artifact)

    assert not result.ok


def test_validate_corrupt_state(tmp_path):
    """validate fails for invalid JSON."""
    from state import validate_state
    from _common import get_state_path

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    state_path = get_state_path(artifact)
    state_path.write_text("not valid json")

    result = validate_state(artifact)

    assert not result.ok
    assert "json" in result.message.lower() or "invalid" in result.message.lower()


# =============================================================================
# LIST TESTS
# =============================================================================


def test_list_finds_active_audits(tmp_path):
    """list finds all .audit.json files in directory."""
    from state import create_state, list_audits

    # Create two audits
    a1 = tmp_path / "feature1.md"
    a1.write_text("# Feature 1")
    create_state(a1)

    a2 = tmp_path / "feature2.md"
    a2.write_text("# Feature 2")
    create_state(a2)

    result = list_audits(tmp_path)

    assert result.ok
    assert len(result.data["audits"]) == 2


def test_list_empty_directory(tmp_path):
    """list returns empty list when no audits exist."""
    from state import list_audits

    result = list_audits(tmp_path)

    assert result.ok
    assert result.data["audits"] == []


# =============================================================================
# ARCHIVE TESTS
# =============================================================================


def test_archive_moves_state(tmp_path):
    """archive renames state file with date suffix."""
    from state import create_state, archive_audit
    from _common import get_state_path

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = archive_audit(artifact, "2026-01-06")

    assert result.ok
    # Original state gone
    assert not get_state_path(artifact).exists()
    # Archived state exists
    archived = tmp_path / "feature.audit.2026-01-06.json"
    assert archived.exists()


def test_archive_fails_if_no_state(tmp_path):
    """archive fails when no state exists."""
    from state import archive_audit

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")

    result = archive_audit(artifact, "2026-01-06")

    assert not result.ok
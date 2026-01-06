# .claude/skills/audit-loop/tests/test_generate_report.py
"""Tests for generate_report module."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_generate_report_basic(tmp_path):
    """generate_report produces markdown from state."""
    from generate_report import generate_report
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature\n\nDescription here.")
    create_state(artifact)
    update_state(artifact, calibration={"stakes": {}, "score": 8, "level": "medium"})

    result = generate_report(artifact)

    assert result.ok
    report = result.data["report"]
    assert "# Audit Report" in report
    assert "feature.md" in report
    assert "medium" in report.lower()


def test_generate_report_includes_findings(tmp_path):
    """generate_report includes findings table."""
    from generate_report import generate_report
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)
    update_state(artifact, add_finding={
        "description": "Missing validation",
        "priority": "high",
        "confidence": "certain",
        "evidence": "line 42",
    })

    result = generate_report(artifact)

    assert result.ok
    report = result.data["report"]
    assert "F1" in report
    assert "Missing validation" in report
    assert "high" in report.lower()


def test_generate_report_missing_state(tmp_path):
    """generate_report fails when state doesn't exist."""
    from generate_report import generate_report

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")

    result = generate_report(artifact)

    assert not result.ok

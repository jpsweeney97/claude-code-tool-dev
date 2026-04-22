"""Tests for the analytics aggregation script in the codex-analytics skill.

Generates fixture data, runs the standalone analytics script, and asserts
the five views produce correct counts.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from server.journal import OperationJournal
from server.models import (
    AuditEvent,
    DelegationOutcomeRecord,
    OutcomeRecord,
)

ANALYTICS_SCRIPT = (
    Path(__file__).parent.parent
    / "skills"
    / "codex-analytics"
    / "scripts"
    / "analytics.py"
)


def _extract_section(output: str, header: str) -> str:
    """Extract a markdown section by ## header, up to the next ## or end."""
    marker = f"## {header}"
    start = output.index(marker)
    rest = output[start + len(marker) :]
    end = rest.find("\n## ")
    return rest[:end] if end != -1 else rest


def _write_fixtures(plugin_data: Path) -> None:
    """Write a known set of outcome and audit records for testing."""
    journal = OperationJournal(plugin_data)

    # 3 consult outcomes: 2 with workflow=consult, 1 with workflow=review
    # Policy fingerprints: 2x fp-alpha, 1x fp-beta (for distribution test)
    for i, (wf, fp) in enumerate(
        [
            ("consult", "fp-alpha"),
            ("consult", "fp-alpha"),
            ("review", "fp-beta"),
        ]
    ):
        journal.append_outcome(
            OutcomeRecord(
                outcome_id=f"o-{i}",
                timestamp="2026-04-21T00:00:00Z",
                outcome_type="consult",
                collaboration_id=f"c-{i}",
                runtime_id="rt-1",
                context_size=1000 * (i + 1),
                turn_id=f"t-{i}",
                workflow=wf,
                policy_fingerprint=fp,
            )
        )

    # 2 dialogue turns (always workflow=consult by default)
    # Both use fp-alpha — contributes to fingerprint distribution
    for i in range(2):
        journal.append_outcome(
            OutcomeRecord(
                outcome_id=f"dt-{i}",
                timestamp="2026-04-21T00:00:00Z",
                outcome_type="dialogue_turn",
                collaboration_id=f"dc-{i}",
                runtime_id="rt-1",
                context_size=500,
                turn_id=f"dt-{i}",
                turn_sequence=i + 1,
                policy_fingerprint="fp-alpha",
            )
        )

    # 3 delegation terminals: 2 completed, 1 failed
    for i, status in enumerate(["completed", "completed", "failed"]):
        journal.append_delegation_outcome(
            DelegationOutcomeRecord(
                outcome_id=f"do-{i}",
                timestamp="2026-04-21T00:00:00Z",
                outcome_type="delegation_terminal",
                collaboration_id=f"del-c-{i}",
                runtime_id=f"rt-del-{i}",
                job_id=f"job-{i}",
                terminal_status=status,
                base_commit="abc123",
                repo_root="/tmp/repo",
            )
        )

    # 1 unknown outcome_type (future shape)
    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    with outcomes_path.open("a") as f:
        f.write(json.dumps({"outcome_type": "future_shape", "id": "x"}) + "\n")

    # 1 legacy row without workflow field
    with outcomes_path.open("a") as f:
        f.write(
            json.dumps(
                {
                    "outcome_id": "o-legacy",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "outcome_type": "consult",
                    "collaboration_id": "c-legacy",
                    "runtime_id": "rt-1",
                    "context_size": 2000,
                    "turn_id": "t-legacy",
                }
            )
            + "\n"
        )

    # Audit events
    audit_events = [
        {"action": "consult"},
        {"action": "consult"},
        {"action": "dialogue_turn"},
        {"action": "delegate_start", "job_id": "job-0"},
        {"action": "delegate_start", "job_id": "job-1"},
        {"action": "escalate", "job_id": "job-0", "request_id": "req-0"},
        {
            "action": "approve",
            "job_id": "job-0",
            "request_id": "req-0",
            "decision": "approve",
        },
        {
            "action": "approve",
            "job_id": "job-1",
            "request_id": "req-1",
            "decision": "deny",
        },
        {"action": "promote", "job_id": "job-0"},
        {"action": "discard", "job_id": "job-1"},
    ]
    for i, evt_data in enumerate(audit_events):
        journal.append_audit_event(
            AuditEvent(
                event_id=f"evt-{i}",
                timestamp="2026-04-21T00:00:00Z",
                actor="claude",
                action=evt_data["action"],
                collaboration_id=f"collab-{i}",
                runtime_id="rt-1",
                job_id=evt_data.get("job_id"),
                request_id=evt_data.get("request_id"),
                decision=evt_data.get("decision"),
            )
        )


def _run_analytics(tmp_path: Path) -> str:
    """Generate fixtures, run the analytics script, return stdout."""
    plugin_data = tmp_path / "data"
    _write_fixtures(plugin_data)
    outcomes = str(plugin_data / "analytics" / "outcomes.jsonl")
    audit = str(plugin_data / "audit" / "events.jsonl")
    result = subprocess.run(
        ["python3", str(ANALYTICS_SCRIPT), outcomes, audit],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    return result.stdout


class TestAnalyticsRecipe:
    def test_data_header_with_paths_and_counts(self, tmp_path: Path) -> None:
        output = _run_analytics(tmp_path)
        # 10 outcome records: 3 consult + 2 dialogue + 3 delegation + 1 unknown + 1 legacy
        assert "## Data Sources" in output
        assert "outcomes.jsonl" in output
        assert "events.jsonl" in output
        assert "10 records" in output  # total outcome records (also matches audit)

    def test_usage_view_counts(self, tmp_path: Path) -> None:
        output = _run_analytics(tmp_path)
        # Usage: 4 consults (3 explicit + 1 legacy), 2 dialogue, 3 delegation, 2 delegate_start, 1 review
        assert "| consult | 4 |" in output
        assert "| dialogue_turn | 2 |" in output
        assert "| delegation_terminal | 3 |" in output
        assert "| delegate_start | 2 |" in output
        assert "| reviews | 1 |" in output

    def test_unknown_type_metadata_counting(self, tmp_path: Path) -> None:
        output = _run_analytics(tmp_path)
        assert "Skipped 1 records with unknown outcome_type" in output
        assert "future_shape" in output

    def test_reliability_and_security_view(self, tmp_path: Path) -> None:
        output = _run_analytics(tmp_path)
        assert "## Reliability and Security" in output
        # 2 completed out of 3 total = 66%
        assert "2/3" in output
        assert "66%" in output
        assert "| Failed | 1 |" in output
        assert "| Escalation approvals | 1 |" in output
        assert "| Escalation denials | 1 |" in output
        # Metrics not yet emitted to audit stream — must be explicit
        assert "| Credential blocks/shadows | unavailable" in output
        assert "| Promotion rejections | unavailable" in output

    def test_delegation_lifecycle_view(self, tmp_path: Path) -> None:
        output = _run_analytics(tmp_path)
        section = _extract_section(output, "Delegation Lifecycle")
        assert "| started | 2 |" in section
        assert "| promoted | 1 |" in section
        assert "| discarded | 1 |" in section
        assert "| escalations | 1 |" in section

    def test_review_view(self, tmp_path: Path) -> None:
        output = _run_analytics(tmp_path)
        section = _extract_section(output, "Review")
        assert "| Review consultations | 1 |" in section
        # Workflow source distribution (ticket: Review view must show this)
        assert "| workflow=consult | 3 |" in section
        assert "| workflow=review | 1 |" in section
        assert "| Review:consult ratio | 1:3 |" in section

    def test_policy_fingerprint_distribution(self, tmp_path: Path) -> None:
        output = _run_analytics(tmp_path)
        assert "### Policy Fingerprints" in output
        # fp-alpha: 2 consult + 2 dialogue = 4; fp-beta: 1 review consult
        # Legacy row has no fingerprint — not counted
        assert "| `fp-alpha` | 4 |" in output
        assert "| `fp-beta` | 1 |" in output

    def test_missing_files_produce_zero_counts(self, tmp_path: Path) -> None:
        outcomes = tmp_path / "nonexistent_outcomes.jsonl"
        audit = tmp_path / "nonexistent_audit.jsonl"
        result = subprocess.run(
            ["python3", str(ANALYTICS_SCRIPT), str(outcomes), str(audit)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"
        assert "(0 records)" in result.stdout

    def test_malformed_lines_are_skipped_and_counted(self, tmp_path: Path) -> None:
        outcomes = tmp_path / "outcomes.jsonl"
        outcomes.write_text(
            '{"outcome_type": "consult", "outcome_id": "o1", "timestamp": "t",'
            ' "collaboration_id": "c1", "runtime_id": "r1", "context_size": 100,'
            ' "turn_id": "t1"}\n'
            "NOT VALID JSON\n"
            '{"outcome_type": "consult", "outcome_id": "o2", "timestamp": "t",'
            ' "collaboration_id": "c2", "runtime_id": "r1", "context_size": 200,'
            ' "turn_id": "t2"}\n'
        )
        audit = tmp_path / "audit.jsonl"
        audit.write_text("")
        result = subprocess.run(
            ["python3", str(ANALYTICS_SCRIPT), str(outcomes), str(audit)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"
        assert "(2 records, 1 malformed)" in result.stdout

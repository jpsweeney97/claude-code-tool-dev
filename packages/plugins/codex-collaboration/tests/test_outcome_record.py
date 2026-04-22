"""Tests for OutcomeRecord model."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from server.models import OutcomeRecord, DelegationOutcomeRecord
from server.journal import OperationJournal


class TestOutcomeRecord:
    def test_consult_outcome_fields(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-1",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-1",
        )
        assert record.outcome_type == "consult"
        assert record.context_size == 4096
        assert record.turn_sequence is None
        assert record.policy_fingerprint is None
        assert record.repo_root is None

    def test_dialogue_outcome_fields(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-2",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="dialogue_turn",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=2048,
            turn_id="turn-2",
            turn_sequence=3,
        )
        assert record.outcome_type == "dialogue_turn"
        assert record.turn_sequence == 3

    def test_frozen(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-3",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=1024,
            turn_id="turn-3",
        )
        import pytest

        with pytest.raises(AttributeError):
            record.outcome_type = "dialogue_turn"  # type: ignore[misc]

    def test_context_size_nullable(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-5",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="dialogue_turn",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=None,
            turn_id="turn-5",
            turn_sequence=1,
        )
        assert record.context_size is None
        d = asdict(record)
        assert d["context_size"] is None

    def test_asdict_roundtrip(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-4",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-4",
            policy_fingerprint="abc123",
            repo_root="/tmp/repo",
        )
        d = asdict(record)
        assert d["outcome_id"] == "o-4"
        assert d["outcome_type"] == "consult"
        assert d["policy_fingerprint"] == "abc123"
        assert d["repo_root"] == "/tmp/repo"
        assert d["turn_sequence"] is None


class TestOutcomeJournalPersistence:
    def test_append_outcome_creates_file_and_writes_jsonl(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        record = OutcomeRecord(
            outcome_id="o-1",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-1",
            policy_fingerprint="fp-abc",
            repo_root="/tmp/repo",
        )
        journal.append_outcome(record)

        outcomes_path = tmp_path / "plugin-data" / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        line = json.loads(outcomes_path.read_text(encoding="utf-8").strip())
        assert line["outcome_id"] == "o-1"
        assert line["outcome_type"] == "consult"
        assert line["context_size"] == 4096
        assert line["policy_fingerprint"] == "fp-abc"

    def test_append_outcome_appends_multiple_records(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        for i in range(3):
            journal.append_outcome(
                OutcomeRecord(
                    outcome_id=f"o-{i}",
                    timestamp="2026-04-01T00:00:00Z",
                    outcome_type="dialogue_turn",
                    collaboration_id=f"collab-{i}",
                    runtime_id="rt-1",
                    context_size=1024 * (i + 1),
                    turn_id=f"turn-{i}",
                    turn_sequence=i + 1,
                )
            )

        outcomes_path = tmp_path / "plugin-data" / "analytics" / "outcomes.jsonl"
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3
        records = [json.loads(line) for line in lines]
        assert records[0]["outcome_id"] == "o-0"
        assert records[2]["context_size"] == 3072
        assert records[1]["turn_sequence"] == 2

    def test_analytics_directory_created_on_init(self, tmp_path: Path) -> None:
        plugin_data = tmp_path / "plugin-data"
        OperationJournal(plugin_data)
        assert (plugin_data / "analytics").is_dir()


class TestOutcomeRecordWorkflow:
    def test_outcome_record_default_workflow(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-wf1",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-1",
        )
        assert record.workflow == "consult"

    def test_outcome_record_explicit_review_workflow(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-wf2",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-1",
            workflow="review",
        )
        assert record.workflow == "review"

    def test_outcome_record_workflow_in_asdict(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-wf3",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-1",
        )
        d = asdict(record)
        assert d["workflow"] == "consult"

    def test_consult_request_default_workflow(self) -> None:
        from server.models import ConsultRequest

        request = ConsultRequest(repo_root=Path("/tmp"), objective="test")
        assert request.workflow == "consult"

    def test_consult_request_explicit_workflow(self) -> None:
        from server.models import ConsultRequest

        request = ConsultRequest(
            repo_root=Path("/tmp"),
            objective="test",
            workflow="review",
        )
        assert request.workflow == "review"


class TestDelegationOutcomeRecord:
    def test_delegation_terminal_fields(self) -> None:
        record = DelegationOutcomeRecord(
            outcome_id="do-1",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="delegation_terminal",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            job_id="job-1",
            terminal_status="completed",
            base_commit="abc123",
            repo_root="/tmp/repo",
        )
        assert record.outcome_type == "delegation_terminal"
        assert record.terminal_status == "completed"
        assert record.job_id == "job-1"
        assert record.base_commit == "abc123"
        assert record.repo_root == "/tmp/repo"

    def test_delegation_terminal_repo_root_defaults_none(self) -> None:
        record = DelegationOutcomeRecord(
            outcome_id="do-2",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="delegation_terminal",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            job_id="job-2",
            terminal_status="failed",
            base_commit="def456",
        )
        assert record.repo_root is None

    def test_delegation_terminal_frozen(self) -> None:
        record = DelegationOutcomeRecord(
            outcome_id="do-3",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="delegation_terminal",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            job_id="job-3",
            terminal_status="unknown",
            base_commit="ghi789",
        )
        import pytest

        with pytest.raises(AttributeError):
            record.terminal_status = "completed"  # type: ignore[misc]

    def test_delegation_terminal_asdict_roundtrip(self) -> None:
        record = DelegationOutcomeRecord(
            outcome_id="do-4",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="delegation_terminal",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            job_id="job-4",
            terminal_status="completed",
            base_commit="abc123",
            repo_root="/tmp/repo",
        )
        d = asdict(record)
        assert d["outcome_type"] == "delegation_terminal"
        assert d["job_id"] == "job-4"
        assert d["terminal_status"] == "completed"
        assert d["base_commit"] == "abc123"
        assert d["repo_root"] == "/tmp/repo"
        # Fields NOT present (by design decision)
        assert "promotion_state" not in d
        assert "artifact_hash" not in d

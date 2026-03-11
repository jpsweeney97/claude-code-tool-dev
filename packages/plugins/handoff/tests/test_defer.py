"""Tests for defer.py — envelope emission logic."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


class TestEmitEnvelope:
    def test_same_second_same_summary_gets_unique_filenames(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Same-second collisions are resolved without overwriting data."""
        import scripts.defer as defer_module

        fixed_now = datetime(2026, 3, 10, 15, 4, 5, tzinfo=timezone.utc)

        class FixedDateTime:
            @classmethod
            def now(cls, tz: timezone | None = None) -> datetime:
                assert tz == timezone.utc
                return fixed_now

        monkeypatch.setattr(defer_module, "datetime", FixedDateTime)

        candidate_one = {
            "summary": "Duplicate summary",
            "problem": "First problem.",
            "source_text": "First source.",
            "proposed_approach": "First approach.",
            "acceptance_criteria": ["First criteria"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-dup-1",
        }
        candidate_two = {
            "summary": "Duplicate summary",
            "problem": "Second problem.",
            "source_text": "Second source.",
            "proposed_approach": "Second approach.",
            "acceptance_criteria": ["Second criteria"],
            "priority": "high",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-dup-2",
        }

        envelopes_dir = tmp_path / ".envelopes"
        path_one = defer_module.emit_envelope(candidate_one, envelopes_dir)
        path_two = defer_module.emit_envelope(candidate_two, envelopes_dir)

        assert path_one.name == "2026-03-10T150405Z-duplicate-summary.json"
        assert path_two.name == "2026-03-10T150405Z-duplicate-summary-01.json"
        assert path_one != path_two

        data_one = json.loads(path_one.read_text())
        data_two = json.loads(path_two.read_text())
        assert data_one["problem"] == "First problem."
        assert data_two["problem"] == "Second problem."

    def test_non_string_summary_raises_type_error(self, tmp_path: Path) -> None:
        """Non-string summary raises TypeError (caught by main's catch list)."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": 42,
            "problem": "Some problem.",
        }
        with pytest.raises(TypeError, match="summary must be a string"):
            emit_envelope(candidate, tmp_path / ".envelopes")

    def test_empty_summary_raises_value_error(self, tmp_path: Path) -> None:
        """Whitespace-only summary raises ValueError (caught by main's catch list)."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "   ",
            "problem": "Some problem.",
        }
        with pytest.raises(ValueError, match="summary must be non-empty"):
            emit_envelope(candidate, tmp_path / ".envelopes")

    def test_minimal_candidate(self, tmp_path: Path) -> None:
        """Minimal candidate produces valid envelope JSON."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Fix auth timeout",
            "problem": "Auth handler times out for large payloads.",
            "source_text": "Found during review.",
            "proposed_approach": "Increase timeout.",
            "acceptance_criteria": ["Timeout works for 10MB"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-1",
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        assert path.exists()
        assert path.suffix == ".json"
        data = json.loads(path.read_text())
        assert data["envelope_version"] == "1.0"
        assert data["title"] == "Fix auth timeout"
        assert data["problem"] == "Auth handler times out for large payloads."
        assert data["source"]["type"] == "ad-hoc"
        assert data["source"]["session"] == "sess-1"
        assert data["suggested_priority"] == "medium"
        assert data["approach"] == "Increase timeout."
        assert data["acceptance_criteria"] == ["Timeout works for 10MB"]
        assert "emitted_at" in data
        assert "status" not in data

    def test_full_candidate_with_effort_and_files(self, tmp_path: Path) -> None:
        """All candidate fields mapped correctly including effort."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Refactor parser",
            "problem": "Parser is too slow.",
            "source_text": "Profiling showed bottleneck.",
            "proposed_approach": "Use streaming parser.",
            "acceptance_criteria": ["10x faster", "No regressions"],
            "priority": "high",
            "effort": "M",
            "source_type": "pr-review",
            "source_ref": "PR #42",
            "session_id": "sess-2",
            "branch": "feature/parser",
            "files": ["src/parser.py", "src/lexer.py"],
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        data = json.loads(path.read_text())
        assert data["effort"] == "M"
        assert data["key_file_paths"] == ["src/parser.py", "src/lexer.py"]
        assert data["suggested_priority"] == "high"
        assert data["source"]["ref"] == "PR #42"

    def test_context_composition(self, tmp_path: Path) -> None:
        """Branch and source_text composed into context field."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Test context",
            "problem": "Problem text.",
            "source_text": "User said to defer this.",
            "proposed_approach": "TBD.",
            "acceptance_criteria": ["Done"],
            "priority": "low",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-3",
            "branch": "fix/auth",
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        data = json.loads(path.read_text())
        assert "context" in data
        assert "Captured on branch `fix/auth`" in data["context"]
        assert 'Evidence anchor:' in data["context"]
        assert "User said to defer this." in data["context"]

    def test_no_status_field(self, tmp_path: Path) -> None:
        """Envelope never contains status field."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "No status",
            "problem": "Problem.",
            "source_text": "Quote.",
            "proposed_approach": "Fix.",
            "acceptance_criteria": ["Fixed"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-4",
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        data = json.loads(path.read_text())
        assert "status" not in data

    def test_emitted_at_is_iso8601(self, tmp_path: Path) -> None:
        """emitted_at is a valid ISO 8601 timestamp."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Timestamp test",
            "problem": "Problem.",
            "source_text": "Quote.",
            "proposed_approach": "Fix.",
            "acceptance_criteria": ["Fixed"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-5",
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        data = json.loads(path.read_text())
        # Should parse without error
        ts = datetime.fromisoformat(data["emitted_at"])
        assert ts.tzinfo is not None  # Must be timezone-aware


class TestMainEmitsEnvelopes:
    def test_main_output_format(self, tmp_path: Path) -> None:
        """CLI writes envelopes and outputs JSON with 'envelopes' key."""
        import io

        from scripts.defer import main

        candidate = {
            "summary": "CLI test",
            "problem": "Test problem.",
            "source_text": "Quote.",
            "proposed_approach": "Fix.",
            "acceptance_criteria": ["Done"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-cli",
        }
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps([candidate]))
        try:
            buf = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = buf
            try:
                code = main(["--tickets-dir", str(tmp_path)])
            finally:
                sys.stdout = original_stdout
        finally:
            sys.stdin = original_stdin

        assert code == 0
        output = json.loads(buf.getvalue())
        assert output["status"] == "ok"
        assert "envelopes" in output
        assert len(output["envelopes"]) == 1
        assert output["envelopes"][0]["path"].endswith(".json")

    def test_envelopes_written_to_dir(self, tmp_path: Path) -> None:
        """Envelopes are written to .envelopes/ subdirectory."""
        import io

        from scripts.defer import main

        candidate = {
            "summary": "Dir test",
            "problem": "Problem.",
            "source_text": "Quote.",
            "proposed_approach": "Fix.",
            "acceptance_criteria": ["Done"],
            "priority": "low",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-dir",
        }
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps([candidate]))
        try:
            buf = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = buf
            try:
                main(["--tickets-dir", str(tmp_path)])
            finally:
                sys.stdout = original_stdout
        finally:
            sys.stdin = original_stdin

        envelopes = list((tmp_path / ".envelopes").glob("*.json"))
        assert len(envelopes) == 1

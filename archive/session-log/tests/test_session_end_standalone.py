"""Tests for standalone session_end hook (stdlib-only)."""

import json
import sys
from pathlib import Path

# Add scripts dir to path for importing standalone module
scripts_dir = Path(__file__).parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))


def test_parse_transcript_extracts_files(tmp_path):
    """Inlined parse_transcript extracts files from tool calls."""
    from session_end_standalone import parse_transcript, TranscriptData

    transcript = tmp_path / "test.jsonl"
    transcript.write_text(json.dumps({
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": "/path/to/file.py"}},
                {"type": "tool_use", "name": "Bash", "input": {"command": "pytest"}},
            ]
        }
    }) + "\n")

    result = parse_transcript(transcript)

    assert isinstance(result, TranscriptData)
    assert "/path/to/file.py" in result.files_touched
    assert "pytest" in result.commands_run
    assert result.assistant_message_count == 1


def test_no_heavy_imports():
    """Standalone script has no chromadb or session_log imports."""
    script_path = scripts_dir / "session_end_standalone.py"

    content = script_path.read_text()

    # Check for actual import statements (not mentions in docstrings)
    # Look for import patterns at start of line or after newline
    import re

    # chromadb imports
    assert not re.search(r"^\s*import chromadb", content, re.MULTILINE)
    assert not re.search(r"^\s*from chromadb", content, re.MULTILINE)

    # session_log imports
    assert not re.search(r"^\s*from session_log", content, re.MULTILINE)
    assert not re.search(r"^\s*import session_log", content, re.MULTILINE)


def test_handle_session_end_writes_summary_and_pending(tmp_path):
    """handle_session_end writes summary file and pending metadata."""
    from session_end_standalone import handle_session_end

    # Create state dir and file
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "session_test-123.json"
    state_file.write_text(json.dumps({
        "session_id": "test-123",
        "start_time": "2026-01-12T10:00:00+00:00",
        "cwd": str(tmp_path / "project"),
        "branch": "feat/test",
    }))

    # Create project dir
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create transcript
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        json.dumps({"type": "user", "message": {"content": "hello"}}) + "\n" +
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}}) + "\n" +
        json.dumps({"type": "user", "message": {"content": "bye"}}) + "\n" +
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "goodbye"}]}}) + "\n"
    )

    pending_dir = tmp_path / "pending"
    pending_dir.mkdir()

    result = handle_session_end(
        input_data={
            "session_id": "test-123",
            "transcript_path": str(transcript),
            "cwd": str(project_dir),
        },
        state_dir=state_dir,
        pending_dir=pending_dir,
    )

    assert result["success"] is True
    assert "summary_path" in result
    assert result["pending_written"] is True

    # Verify summary file exists
    summary_path = Path(result["summary_path"])
    assert summary_path.exists()
    assert "# Session:" in summary_path.read_text()

    # Verify pending file exists
    pending_files = list(pending_dir.glob("*.json"))
    assert len(pending_files) == 1

    # Verify state file deleted
    assert not state_file.exists()

"""Integration tests for SessionEnd hook."""

import json

import pytest


@pytest.fixture
def session_setup(tmp_path):
    """Set up session state and transcript."""
    # Create state file with session_id in filename
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state = {
        "session_id": "test-123",
        "start_time": "2026-01-01T10:00:00+00:00",
        "cwd": str(tmp_path / "project"),
        "branch": "feat/test",
        "commit_start": "abc1234",
    }
    (state_dir / "session_test-123.json").write_text(json.dumps(state))

    # Create project dir
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".claude").mkdir()
    (project_dir / ".claude" / "sessions").mkdir()

    # Create transcript
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        '{"type":"user","message":{"content":"Fix the bug"}}\n'
        '{"type":"assistant","message":{"content":[{"type":"text","text":"Done!"}]}}\n'
        '{"type":"user","message":{"content":"Thanks"}}\n'
        '{"type":"assistant","message":{"content":[{"type":"text","text":"You are welcome!"}]}}\n'
    )

    return {
        "state_dir": state_dir,
        "project_dir": project_dir,
        "transcript": transcript,
        "state": state,
    }


def test_session_end_creates_summary_file(session_setup):
    """SessionEnd creates a summary markdown file."""
    from scripts.session_end import handle_session_end

    input_data = {
        "session_id": "test-123",
        "transcript_path": str(session_setup["transcript"]),
        "cwd": str(session_setup["project_dir"]),
        "reason": "exit",
    }

    result = handle_session_end(
        input_data,
        state_dir=session_setup["state_dir"],
    )

    assert result["success"] is True

    # Check summary file was created
    sessions_dir = session_setup["project_dir"] / ".claude" / "sessions"
    summaries = list(sessions_dir.glob("*.md"))
    assert len(summaries) == 1


def test_session_end_summary_has_correct_frontmatter(session_setup):
    """Summary file has correct YAML frontmatter."""
    from scripts.session_end import handle_session_end

    input_data = {
        "session_id": "test-123",
        "transcript_path": str(session_setup["transcript"]),
        "cwd": str(session_setup["project_dir"]),
        "reason": "exit",
    }

    result = handle_session_end(
        input_data,
        state_dir=session_setup["state_dir"],
    )

    assert result["success"] is True

    # Read the summary and check frontmatter
    sessions_dir = session_setup["project_dir"] / ".claude" / "sessions"
    summary_file = list(sessions_dir.glob("*.md"))[0]
    content = summary_file.read_text()

    assert content.startswith("---\n")
    assert "branch: feat/test" in content
    assert "project: project" in content


def test_session_end_skips_short_sessions(session_setup):
    """SessionEnd skips sessions with fewer than 2 user messages."""
    from scripts.session_end import handle_session_end

    # Create a very short transcript
    short_transcript = session_setup["project_dir"] / "short.jsonl"
    short_transcript.write_text(
        '{"type":"user","message":{"content":"Hi"}}\n'
        '{"type":"assistant","message":{"content":[{"type":"text","text":"Hello!"}]}}\n'
    )

    input_data = {
        "session_id": "test-123",
        "transcript_path": str(short_transcript),
        "cwd": str(session_setup["project_dir"]),
        "reason": "exit",
    }

    result = handle_session_end(
        input_data,
        state_dir=session_setup["state_dir"],
    )

    assert result["success"] is True
    assert "too short" in result.get("reason", "")

    # No summary file should be created
    sessions_dir = session_setup["project_dir"] / ".claude" / "sessions"
    summaries = list(sessions_dir.glob("*.md"))
    assert len(summaries) == 0


def test_session_end_indexes_session(session_setup, tmp_path):
    """SessionEnd indexes the session in SQLite."""
    from scripts.session_end import handle_session_end
    from session_log.queries import list_sessions

    # Use a temporary database for this test
    db_path = tmp_path / "test_index.db"

    input_data = {
        "session_id": "test-123",
        "transcript_path": str(session_setup["transcript"]),
        "cwd": str(session_setup["project_dir"]),
        "reason": "exit",
    }

    result = handle_session_end(
        input_data,
        state_dir=session_setup["state_dir"],
        db_path=db_path,
    )

    assert result["success"] is True

    # Check session was indexed
    sessions = list_sessions(db_path=db_path)
    assert len(sessions) == 1
    assert sessions[0]["project"] == "project"
    assert sessions[0]["branch"] == "feat/test"


def test_session_end_embeds_in_chromadb(session_setup, tmp_path):
    """SessionEnd embeds session summary in ChromaDB."""
    from scripts.session_end import handle_session_end
    from session_log.search import get_collection

    db_path = tmp_path / "test_index.db"
    chroma_path = tmp_path / "chroma"

    input_data = {
        "session_id": "test-123",
        "transcript_path": str(session_setup["transcript"]),
        "cwd": str(session_setup["project_dir"]),
        "reason": "exit",
    }

    result = handle_session_end(
        input_data,
        state_dir=session_setup["state_dir"],
        db_path=db_path,
        chroma_path=chroma_path,
    )

    assert result["success"] is True
    assert result.get("embedded") is True

    # Verify embedding was stored
    collection = get_collection(chroma_path)
    assert collection.count() == 1

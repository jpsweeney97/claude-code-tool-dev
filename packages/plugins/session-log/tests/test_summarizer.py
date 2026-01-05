"""Tests for summary generator."""

from datetime import datetime, timezone

import pytest

from session_log.transcript import TranscriptData


@pytest.fixture
def sample_transcript_data():
    """Create sample parsed transcript data."""
    return TranscriptData(
        tool_calls=[
            {"name": "Read", "input": {"file_path": "src/auth.py"}},
            {"name": "Edit", "input": {"file_path": "src/auth.py"}},
            {"name": "Bash", "input": {"command": "pytest tests/"}},
        ],
        files_touched={"src/auth.py"},
        user_message_count=3,
        assistant_message_count=3,
        assistant_text="I found the bug in the auth module. Fixed the issue.",
        commands_run=["pytest tests/"],
    )


@pytest.fixture
def session_state():
    """Create sample session state."""
    return {
        "session_id": "test-123",
        "start_time": "2026-01-01T10:00:00+00:00",
        "cwd": "/home/user/project",
        "branch": "feat/auth-fix",
        "commit_start": "abc1234",
    }


def test_generate_summary_creates_frontmatter(sample_transcript_data, session_state):
    """Summary generator creates valid YAML frontmatter."""
    from session_log.summarizer import generate_summary

    summary = generate_summary(
        transcript_data=sample_transcript_data,
        session_state=session_state,
        commit_end="def5678",
        commits_made=2,
    )

    assert summary.startswith("---\n")
    assert "date:" in summary
    assert "project:" in summary
    assert "branch: feat/auth-fix" in summary


def test_generate_summary_includes_files(sample_transcript_data, session_state):
    """Summary includes files touched section."""
    from session_log.summarizer import generate_summary

    summary = generate_summary(
        transcript_data=sample_transcript_data,
        session_state=session_state,
    )

    assert "## Files" in summary
    assert "src/auth.py" in summary


def test_generate_summary_creates_title(sample_transcript_data, session_state):
    """Summary generates a title from session content."""
    from session_log.summarizer import generate_summary

    summary = generate_summary(
        transcript_data=sample_transcript_data,
        session_state=session_state,
    )

    # Title should be in the markdown
    assert "# Session:" in summary


def test_calculate_duration_with_naive_datetime():
    """Test that naive datetime in start_time is handled correctly."""
    from session_log.summarizer import calculate_duration_minutes

    # Naive datetime string (no timezone)
    naive_start = "2025-01-01T10:00:00"
    end_time = datetime(2025, 1, 1, 10, 30, 0, tzinfo=timezone.utc)

    # Should not crash and should return reasonable duration
    duration = calculate_duration_minutes(naive_start, end_time)
    assert duration == 30


def test_calculate_duration_with_aware_datetime():
    """Test that aware datetime is handled correctly."""
    from session_log.summarizer import calculate_duration_minutes

    aware_start = "2025-01-01T10:00:00+00:00"
    end_time = datetime(2025, 1, 1, 10, 45, 0, tzinfo=timezone.utc)

    duration = calculate_duration_minutes(aware_start, end_time)
    assert duration == 45


def test_get_summary_filename_with_naive_datetime():
    """Test that naive datetime in session state is handled correctly."""
    from session_log.summarizer import get_summary_filename

    session_state = {"start_time": "2025-01-01T10:00:00"}  # Naive
    filename = get_summary_filename(session_state, "Test Title")

    assert filename.startswith("2025-01-01")
    assert "test-title" in filename


def test_get_summary_filename_with_invalid_datetime():
    """Test that invalid datetime falls back gracefully."""
    from session_log.summarizer import get_summary_filename

    session_state = {"start_time": "not-a-date"}
    # Should not crash, should fall back to current time
    filename = get_summary_filename(session_state, "Test")
    assert filename.endswith(".md")

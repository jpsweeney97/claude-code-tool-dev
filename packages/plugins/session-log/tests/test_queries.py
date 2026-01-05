"""Tests for query functions."""


import pytest


@pytest.fixture
def db_with_sessions(tmp_path):
    """Create a database with sample sessions."""
    from session_log.storage import init_db

    db_path = tmp_path / "test.db"
    conn = init_db(db_path)

    sessions = [
        ("2026-01-01_10-00-00_auth.md", "2026-01-01T10:00:00", "project-a", "feat/auth", 30, 2, 5, 10, "Auth work", "/path/a.md", "2026-01-01T11:00:00"),
        ("2026-01-01_14-00-00_api.md", "2026-01-01T14:00:00", "project-a", "main", 45, 3, 8, 15, "API work", "/path/b.md", "2026-01-01T15:00:00"),
        ("2026-01-02_09-00-00_docs.md", "2026-01-02T09:00:00", "project-b", "main", 20, 1, 2, 5, "Docs update", "/path/c.md", "2026-01-02T09:30:00"),
    ]

    conn.executemany(
        """INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        sessions,
    )
    conn.commit()

    return db_path


def test_list_sessions_returns_all(db_with_sessions):
    """list_sessions returns all sessions by default."""
    from session_log.queries import list_sessions

    result = list_sessions(db_path=db_with_sessions)

    assert len(result) == 3


def test_list_sessions_filters_by_project(db_with_sessions):
    """list_sessions filters by project."""
    from session_log.queries import list_sessions

    result = list_sessions(project="project-a", db_path=db_with_sessions)

    assert len(result) == 2
    assert all(s["project"] == "project-a" for s in result)


def test_list_sessions_filters_by_date(db_with_sessions):
    """list_sessions filters by date range."""
    from session_log.queries import list_sessions

    result = list_sessions(
        after="2026-01-02",
        db_path=db_with_sessions,
    )

    assert len(result) == 1
    assert result[0]["project"] == "project-b"


def test_list_sessions_respects_limit(db_with_sessions):
    """list_sessions respects limit parameter."""
    from session_log.queries import list_sessions

    result = list_sessions(limit=2, db_path=db_with_sessions)

    assert len(result) == 2


def test_get_session_returns_session(db_with_sessions):
    """get_session returns a single session by filename."""
    from session_log.queries import get_session

    result = get_session("2026-01-01_10-00-00_auth.md", db_path=db_with_sessions)

    assert result is not None
    assert result["title"] == "Auth work"
    assert result["project"] == "project-a"


def test_get_session_returns_none_for_missing(db_with_sessions):
    """get_session returns None for non-existent session."""
    from session_log.queries import get_session

    result = get_session("nonexistent.md", db_path=db_with_sessions)

    assert result is None


def test_list_sessions_closes_connection_on_error(tmp_path):
    """Test that database connection is closed even when query fails."""
    from unittest.mock import patch, MagicMock
    from session_log.queries import list_sessions

    db_path = tmp_path / "test.db"
    db_path.touch()  # Create file so existence check passes

    mock_conn = MagicMock()
    mock_conn.execute.side_effect = Exception("Query failed")

    with patch("session_log.queries.init_db", return_value=mock_conn):
        # Now returns empty list instead of raising
        result = list_sessions(db_path=db_path)

    assert result == []
    # Connection should still be closed
    mock_conn.close.assert_called_once()

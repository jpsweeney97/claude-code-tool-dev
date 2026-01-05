"""Tests for search module."""

import tempfile
from pathlib import Path



def test_get_collection_creates_persistent_storage():
    """ChromaDB collection is created with persistent storage."""
    from session_log.search import get_collection

    with tempfile.TemporaryDirectory() as tmpdir:
        collection = get_collection(db_path=Path(tmpdir))

        assert collection is not None
        assert collection.name == "sessions"


def test_embed_session_stores_document():
    """embed_session stores session content in ChromaDB."""
    from session_log.search import embed_session, get_collection

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir)

        success, error = embed_session(
            session_id="2026-01-02_10-30-00_test-session",
            content="Fixed authentication bug in login flow",
            metadata={"project": "myapp", "branch": "fix/auth"},
            db_path=db_path,
        )

        assert success is True
        assert error is None

        # Verify it was stored
        collection = get_collection(db_path)
        assert collection.count() == 1


def test_embed_session_returns_error_on_failure():
    """embed_session returns error message on failure."""
    from unittest.mock import patch
    from session_log.search import embed_session

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir)

        with patch("session_log.search.get_collection", side_effect=RuntimeError("Connection failed")):
            success, error = embed_session(
                session_id="test-session",
                content="Test content",
                db_path=db_path,
            )

        assert success is False
        assert error is not None
        assert "ChromaDB runtime error" in error


def test_search_sessions_finds_relevant_content():
    """search_sessions returns semantically similar sessions."""
    from session_log.search import embed_session, search_sessions

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir)

        # Store some sessions
        embed_session(
            "session-1",
            "Fixed authentication bug in the login system",
            {"project": "webapp"},
            db_path,
        )
        embed_session(
            "session-2",
            "Added dark mode theme toggle to settings page",
            {"project": "webapp"},
            db_path,
        )
        embed_session(
            "session-3",
            "Refactored user login and password reset flow",
            {"project": "webapp"},
            db_path,
        )

        # Search for auth-related sessions
        results = search_sessions("authentication login", limit=2, db_path=db_path)

        assert len(results) == 2
        # Session 1 and 3 should be more relevant than session 2
        result_ids = [r["id"] for r in results]
        assert "session-2" not in result_ids


def test_search_sessions_filters_by_project():
    """search_sessions can filter results by project."""
    from session_log.search import embed_session, search_sessions

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir)

        embed_session("s1", "Auth bug fix", {"project": "frontend"}, db_path)
        embed_session("s2", "Auth bug fix", {"project": "backend"}, db_path)

        results = search_sessions("auth", project="frontend", db_path=db_path)

        assert len(results) == 1
        assert results[0]["id"] == "s1"

"""Tests for tool_handlers module."""

import json
import tempfile
from pathlib import Path


def test_clamp_limit_returns_default_for_none():
    """_clamp_limit returns default when limit is None."""
    from tool_handlers import _clamp_limit

    assert _clamp_limit(None, default=50) == 50
    assert _clamp_limit(None, default=10) == 10


def test_clamp_limit_clamps_to_valid_range():
    """_clamp_limit clamps values to [1, max_limit]."""
    from tool_handlers import _clamp_limit

    assert _clamp_limit(0, default=50) == 1
    assert _clamp_limit(-10, default=50) == 1
    assert _clamp_limit(5000, default=50) == 1000
    assert _clamp_limit(25, default=50) == 25
    assert _clamp_limit(1, default=50) == 1
    assert _clamp_limit(1000, default=50) == 1000


def test_handle_search_sessions_returns_results():
    """handle_search_sessions returns semantic search results."""
    from tool_handlers import handle_search_sessions
    from session_log.search import embed_session

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir)

        embed_session("s1", "Fixed login authentication", {"project": "app"}, db_path)
        embed_session("s2", "Added user profile page", {"project": "app"}, db_path)

        results = handle_search_sessions(
            {"query": "authentication", "limit": 5},
            chroma_path=db_path,
        )

        assert len(results) == 1
        assert results[0].type == "text"

        data = json.loads(results[0].text)
        assert len(data) >= 1
        assert data[0]["id"] == "s1"

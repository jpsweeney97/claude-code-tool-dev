"""Tests for storage module."""

import tempfile
from pathlib import Path



def test_init_db_creates_tables():
    """Database initialization creates required tables."""
    from session_log.storage import init_db

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_db(db_path)

        # Check sessions table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        )
        assert cursor.fetchone() is not None

        conn.close()


def test_init_db_creates_indexes():
    """Database initialization creates required indexes."""
    from session_log.storage import init_db

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_db(db_path)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_sessions_date" in indexes
        assert "idx_sessions_project" in indexes

        conn.close()

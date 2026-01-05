"""Query functions for session data."""

import sqlite3
import sys
from pathlib import Path
from typing import Any

from .storage import get_db_path, init_db


def list_sessions(
    project: str | None = None,
    after: str | None = None,
    before: str | None = None,
    limit: int = 50,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """List sessions with optional filtering.

    Args:
        project: Filter by project name.
        after: Filter sessions on or after this date (YYYY-MM-DD or ISO).
        before: Filter sessions on or before this date.
        limit: Maximum number of results.
        db_path: Optional override for database path (for testing).

    Returns:
        List of session dictionaries ordered by date descending.
        Returns empty list on error.
    """
    if db_path is None:
        db_path = get_db_path()

    if not db_path.exists():
        return []

    conn = init_db(db_path)
    try:
        query = "SELECT * FROM sessions WHERE 1=1"
        params: list[Any] = []

        if project:
            query += " AND project = ?"
            params.append(project)

        if after:
            query += " AND date >= ?"
            params.append(after)

        if before:
            query += " AND date <= ?"
            params.append(before)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description]

        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results
    except sqlite3.Error as e:
        print(f"list_sessions failed: Database error: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"list_sessions failed: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()


def get_session(filename: str, db_path: Path | None = None) -> dict[str, Any] | None:
    """Get a single session by filename.

    Args:
        filename: The session filename (primary key).
        db_path: Optional override for database path (for testing).

    Returns:
        Session dictionary or None if not found.
        Returns None on error (errors logged to stderr).
    """
    if db_path is None:
        db_path = get_db_path()

    if not db_path.exists():
        return None

    conn = init_db(db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM sessions WHERE filename = ?",
            (filename,),
        )
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        if row is None:
            return None

        return dict(zip(columns, row))
    except sqlite3.Error as e:
        print(f"get_session failed for {filename!r:.50}: Database error: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"get_session failed for {filename!r:.50}: {e}", file=sys.stderr)
        return None
    finally:
        conn.close()

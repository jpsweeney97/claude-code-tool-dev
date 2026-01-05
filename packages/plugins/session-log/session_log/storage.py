"""SQLite storage for session metadata."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    filename TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    project TEXT NOT NULL,
    branch TEXT,
    duration_minutes INTEGER,
    commits_made INTEGER,
    files_touched INTEGER,
    commands_run INTEGER,
    title TEXT,
    summary_path TEXT NOT NULL,
    indexed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project);
"""


def get_db_path() -> Path:
    """Get the path to the SQLite database."""
    db_dir = Path.home() / ".claude" / "session-log"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "index.db"


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Initialize the database and return a connection."""
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def index_session(metadata: dict, db_path: Path | None = None) -> tuple[bool, str | None]:
    """Index a session in SQLite.

    Args:
        metadata: Session metadata dictionary with required keys:
            - filename, date, project, summary_path
            Optional: branch, duration_minutes, commits_made,
                      files_touched, commands_run, title
        db_path: Optional override for database path (for testing).

    Returns:
        Tuple of (success, error_message). error_message is None on success.
    """
    if db_path is None:
        db_path = get_db_path()

    conn = init_db(db_path)
    try:
        indexed_at = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            INSERT OR REPLACE INTO sessions
            (filename, date, project, branch, duration_minutes, commits_made,
             files_touched, commands_run, title, summary_path, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata["filename"],
                metadata["date"],
                metadata["project"],
                metadata.get("branch"),
                metadata.get("duration_minutes"),
                metadata.get("commits_made"),
                metadata.get("files_touched"),
                metadata.get("commands_run"),
                metadata.get("title"),
                metadata["summary_path"],
                indexed_at,
            ),
        )
        conn.commit()
        return True, None
    except KeyError as e:
        return False, f"Missing required metadata key: {e}"
    except sqlite3.IntegrityError as e:
        return False, f"Database integrity error: {e}"
    except sqlite3.OperationalError as e:
        return False, f"Database operation failed: {e}"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()

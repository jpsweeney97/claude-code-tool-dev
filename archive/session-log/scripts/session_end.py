#!/usr/bin/env python3
"""SessionEnd hook: Generates session summary from transcript."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from session_log.transcript import parse_transcript
from session_log.summarizer import generate_summary, generate_title, get_summary_filename, calculate_duration_minutes
from session_log.storage import index_session
from session_log.search import embed_session


def get_state_dir() -> Path:
    """Get directory for session state files.

    Returns:
        Path to state directory (~/.claude/session-log/state/).
    """
    return Path.home() / ".claude" / "session-log" / "state"


def load_session_state(session_id: str, state_dir: Path | None = None) -> dict | None:
    """Load session state from SessionStart hook.

    Args:
        session_id: The session ID to load state for.
        state_dir: Optional override for state directory (for testing).

    Returns:
        Dict with session state, or None if state file doesn't exist or is malformed.
    """
    if state_dir is None:
        state_dir = get_state_dir()

    # Use session_id in filename to support concurrent sessions
    state_file = state_dir / f"session_{session_id}.json"
    if not state_file.exists():
        return None

    try:
        return json.loads(state_file.read_text())
    except json.JSONDecodeError as e:
        print(f"Warning: Malformed session state file: {e}", file=sys.stderr)
        return None


def delete_state_file(session_id: str, state_dir: Path | None = None) -> None:
    """Delete session state file after successful processing.

    Args:
        session_id: The session ID whose state file should be deleted.
        state_dir: Optional override for state directory (for testing).
    """
    if state_dir is None:
        state_dir = get_state_dir()

    state_file = state_dir / f"session_{session_id}.json"
    try:
        if state_file.exists():
            state_file.unlink()
    except OSError as e:
        print(f"Warning: Failed to delete state file: {e}", file=sys.stderr)


def get_git_info(cwd: str) -> tuple[str | None, int]:
    """Get current HEAD commit and count of new commits.

    Args:
        cwd: Working directory to run git commands in.

    Returns:
        Tuple of (commit hash, commits made count).
    """
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit_hash = commit.stdout.strip() if commit.returncode == 0 else None

        # Count commits (simplified - would need start commit for accurate count)
        return commit_hash, 0
    except subprocess.TimeoutExpired:
        print("Warning: Git command timed out", file=sys.stderr)
        return None, 0
    except FileNotFoundError:
        return None, 0


def ensure_sessions_dir(cwd: str) -> Path:
    """Ensure .claude/sessions/ directory exists.

    Args:
        cwd: Project working directory.

    Returns:
        Path to sessions directory.
    """
    sessions_dir = Path(cwd) / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def handle_session_end(
    input_data: dict,
    state_dir: Path | None = None,
    db_path: Path | None = None,
    chroma_path: Path | None = None,
) -> dict:
    """Handle SessionEnd event.

    Args:
        input_data: Hook input data containing transcript_path, session_id, etc.
        state_dir: Optional override for state directory (for testing).
        db_path: Optional override for database path (for testing).
        chroma_path: Optional override for ChromaDB path (for testing).

    Returns:
        Dict with 'success' key indicating operation result.
    """
    session_id = input_data.get("session_id")
    if not session_id:
        return {"success": False, "reason": "No session_id in input data"}

    session_state = load_session_state(session_id, state_dir)

    if session_state is None:
        return {"success": False, "reason": f"No session state found for session {session_id}"}

    transcript_path = input_data.get("transcript_path")
    if not transcript_path or not Path(transcript_path).exists():
        return {"success": False, "reason": "Transcript not found"}

    cwd = input_data.get("cwd", session_state.get("cwd", "."))

    # Parse transcript
    transcript_data = parse_transcript(Path(transcript_path))

    # Skip empty sessions
    if transcript_data.user_message_count < 2:
        return {"success": True, "reason": "Session too short, skipping"}

    # Get git info
    commit_end, commits_made = get_git_info(cwd)

    # Generate summary
    summary = generate_summary(
        transcript_data=transcript_data,
        session_state=session_state,
        commit_end=commit_end,
        commits_made=commits_made,
    )

    # Write summary file
    title = generate_title(transcript_data, session_state.get("branch"))
    filename = get_summary_filename(session_state, title)

    sessions_dir = ensure_sessions_dir(cwd)
    summary_path = sessions_dir / filename

    try:
        summary_path.write_text(summary)
    except OSError as e:
        print(f"Warning: Failed to write summary: {e}", file=sys.stderr)
        return {"success": False, "reason": f"Failed to write summary: {e}"}

    # Index in SQLite
    metadata = {
        "filename": filename,
        "date": session_state.get("start_time"),
        "project": Path(cwd).name,
        "branch": session_state.get("branch"),
        "duration_minutes": calculate_duration_minutes(
            session_state.get("start_time", datetime.now(timezone.utc).isoformat()),
            datetime.now(timezone.utc),
        ),
        "commits_made": commits_made,
        "files_touched": len(transcript_data.files_touched),
        "commands_run": len(transcript_data.commands_run),
        "title": title,
        "summary_path": str(summary_path),
    }
    indexed, index_error = index_session(metadata, db_path=db_path)

    if not indexed:
        print(f"Warning: Failed to index session in database: {index_error}", file=sys.stderr)

    # Embed in ChromaDB for semantic search
    embedded, embed_error = embed_session(
        session_id=filename,
        content=summary,
        metadata={
            "project": Path(cwd).name,
            "branch": session_state.get("branch"),
            "date": session_state.get("start_time"),
        },
        db_path=chroma_path,
    )

    if not embedded:
        print(f"Warning: Failed to embed session in ChromaDB: {embed_error}", file=sys.stderr)

    # Clean up state file after successful processing
    delete_state_file(session_id, state_dir)

    return {
        "success": True,
        "summary_path": str(summary_path),
        "indexed": indexed,
        "embedded": embedded,
    }


def main():
    """Entry point for hook."""
    try:
        input_data = json.load(sys.stdin)
        result = handle_session_end(input_data)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(f"SessionEnd hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

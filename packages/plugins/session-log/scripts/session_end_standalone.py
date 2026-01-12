#!/usr/bin/env python3
"""Standalone SessionEnd hook: Generates session summary from transcript.

This script is designed to run with bare python3 (no uv run needed).
It has NO imports from chromadb or session_log package - all functionality
is inlined from transcript.py and summarizer.py.

The script writes a pending file for deferred indexing instead of directly
accessing SQLite/ChromaDB.
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# =============================================================================
# Inlined from transcript.py
# =============================================================================


@dataclass
class TranscriptData:
    """Parsed data from a session transcript."""

    tool_calls: list[dict] = field(default_factory=list)
    files_touched: set[str] = field(default_factory=set)
    user_message_count: int = 0
    assistant_message_count: int = 0
    assistant_text: str = ""
    commands_run: list[str] = field(default_factory=list)


def extract_files_from_tool(name: str, input_data: dict) -> set[str]:
    """Extract file paths from tool input."""
    files: set[str] = set()

    if name in ("Read", "Write", "Edit"):
        if path := input_data.get("file_path"):
            files.add(path)
    elif name == "Glob":
        # Glob doesn't touch specific files, skip
        pass

    return files


def parse_transcript(path: Path) -> TranscriptData:
    """Parse a transcript JSONL file and extract session data."""
    result = TranscriptData()
    text_parts: list[str] = []

    with open(path) as f:
        for line_num, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(
                    f"Warning: Skipping malformed JSON at line {line_num}: {e}",
                    file=sys.stderr,
                )
                continue

            msg_type = entry.get("type")
            message = entry.get("message", {})

            if msg_type == "user":
                result.user_message_count += 1

            elif msg_type == "assistant":
                result.assistant_message_count += 1
                content = message.get("content", [])

                if isinstance(content, list):
                    for block in content:
                        block_type = block.get("type")

                        if block_type == "tool_use":
                            tool_name = block.get("name", "")
                            tool_input = block.get("input", {})

                            result.tool_calls.append({
                                "name": tool_name,
                                "input": tool_input,
                            })

                            result.files_touched.update(
                                extract_files_from_tool(tool_name, tool_input)
                            )

                            if tool_name == "Bash":
                                if cmd := tool_input.get("command"):
                                    result.commands_run.append(cmd)

                        elif block_type == "text":
                            if text := block.get("text"):
                                text_parts.append(text)

    result.assistant_text = "\n".join(text_parts)
    return result


# =============================================================================
# Inlined from summarizer.py
# =============================================================================


def generate_title(transcript_data: TranscriptData, branch: str | None) -> str:
    """Generate a session title from content."""
    # Use branch name as hint if available
    if branch and branch not in ("main", "master"):
        # Convert branch name to title
        # feat/auth-fix -> auth fix
        parts = branch.split("/")[-1].replace("-", " ").replace("_", " ")
        return parts.title()

    # Fall back to first file touched
    if transcript_data.files_touched:
        first_file = sorted(transcript_data.files_touched)[0]
        return Path(first_file).stem.replace("_", " ").title()

    return "Session"


def generate_slug(title: str) -> str:
    """Generate a filename slug from title."""
    return title.lower().replace(" ", "-")[:30]


def calculate_duration_minutes(start_time: str, end_time: datetime) -> int:
    """Calculate session duration in minutes."""
    start = datetime.fromisoformat(start_time)
    # Handle timezone-naive datetimes by assuming UTC
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    delta = end_time - start
    return max(1, int(delta.total_seconds() / 60))


def generate_summary(
    transcript_data: TranscriptData,
    session_state: dict,
    commit_end: str | None = None,
    commits_made: int = 0,
    end_time: datetime | None = None,
) -> str:
    """Generate a session summary markdown document."""
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    start_time = session_state.get("start_time", end_time.isoformat())
    branch = session_state.get("branch")
    project = Path(session_state.get("cwd", ".")).name

    title = generate_title(transcript_data, branch)
    duration = calculate_duration_minutes(start_time, end_time)

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f"date: {start_time}",
        f"duration_minutes: {duration}",
        f"project: {project}",
    ]

    if branch:
        frontmatter_lines.append(f"branch: {branch}")
    if session_state.get("commit_start"):
        frontmatter_lines.append(f"commit_start: {session_state['commit_start']}")
    if commit_end:
        frontmatter_lines.append(f"commit_end: {commit_end}")
    if commits_made:
        frontmatter_lines.append(f"commits_made: {commits_made}")

    frontmatter_lines.extend([
        f"files_touched: {len(transcript_data.files_touched)}",
        f"commands_run: {len(transcript_data.commands_run)}",
        "---",
    ])

    # Build content
    content_lines = [
        "",
        f"# Session: {title}",
        "",
        "## Accomplished",
        "",
        "- Session summary pending analysis",
        "",
        "## Files",
        "",
    ]

    if transcript_data.files_touched:
        files = sorted(transcript_data.files_touched)
        if len(files) <= 5:
            content_lines.append(", ".join(files))
        else:
            content_lines.append(", ".join(files[:5]) + f" (+{len(files) - 5})")
    else:
        content_lines.append("No files modified")

    content_lines.append("")

    return "\n".join(frontmatter_lines + content_lines)


def get_summary_filename(session_state: dict, title: str) -> str:
    """Generate the summary filename."""
    start_time = session_state.get("start_time", datetime.now(timezone.utc).isoformat())
    try:
        dt = datetime.fromisoformat(start_time)
    except ValueError:
        dt = datetime.now(timezone.utc)
    date_str = dt.strftime("%Y-%m-%d_%H-%M-%S")
    slug = generate_slug(title)
    return f"{date_str}_{slug}.md"


# =============================================================================
# Inlined from pending.py
# =============================================================================


def get_pending_dir() -> Path:
    """Get directory for pending session files."""
    pending_dir = Path.home() / ".claude" / "session-log" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    return pending_dir


def write_pending_metadata(
    filename: str,
    metadata: dict,
    embedding_data: dict,
    pending_dir: Path | None = None,
) -> tuple[bool, str | None]:
    """Write pending metadata for deferred indexing.

    Args:
        filename: The session filename (used as pending file basename).
        metadata: SQLite metadata dict.
        embedding_data: Dict with 'content' and 'metadata' for ChromaDB.
        pending_dir: Optional override for pending directory (for testing).

    Returns:
        Tuple of (success, error_message).
    """
    if pending_dir is None:
        pending_dir = get_pending_dir()

    pending_file = pending_dir / f"{filename}.json"

    pending_data = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
        "embedding": embedding_data,
    }

    try:
        pending_file.write_text(json.dumps(pending_data, indent=2))
        return True, None
    except OSError as e:
        return False, f"Failed to write pending file: {e}"


# =============================================================================
# Session state management (from session_start.py patterns)
# =============================================================================


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


# =============================================================================
# Git and filesystem helpers
# =============================================================================


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


# =============================================================================
# Main handler
# =============================================================================


def handle_session_end(
    input_data: dict,
    state_dir: Path | None = None,
    pending_dir: Path | None = None,
) -> dict:
    """Handle SessionEnd event.

    This standalone version writes a pending file instead of directly
    indexing in SQLite/ChromaDB.

    Args:
        input_data: Hook input data containing transcript_path, session_id, etc.
        state_dir: Optional override for state directory (for testing).
        pending_dir: Optional override for pending directory (for testing).

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
    # NOTE: Unlike session_end.py which leaves state files for short sessions,
    # the standalone version intentionally deletes them. This is correct behavior:
    # short sessions won't be indexed, so the state file serves no purpose and
    # would otherwise accumulate indefinitely.
    if transcript_data.user_message_count < 2:
        delete_state_file(session_id, state_dir)
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

    # Prepare metadata for pending file (deferred indexing)
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

    embedding_data = {
        "content": summary,
        "metadata": {
            "project": Path(cwd).name,
            "branch": session_state.get("branch"),
            "date": session_state.get("start_time"),
        },
    }

    # Write pending file for deferred indexing
    pending_written, pending_error = write_pending_metadata(
        filename=filename,
        metadata=metadata,
        embedding_data=embedding_data,
        pending_dir=pending_dir,
    )

    if not pending_written:
        # If pending file write fails, the session will never be indexed.
        # Preserve the state file to allow retry on next session end event.
        # The summary file is already written, so indexing can be retried.
        print(f"Warning: Failed to write pending file: {pending_error}", file=sys.stderr)
        return {
            "success": True,
            "summary_path": str(summary_path),
            "pending_written": False,
        }

    # Clean up state file only after ALL processing succeeds (including pending file)
    delete_state_file(session_id, state_dir)

    return {
        "success": True,
        "summary_path": str(summary_path),
        "pending_written": pending_written,
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

#!/usr/bin/env python3
"""SessionStart hook: Records start time and initial git state."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_git_info(cwd: str) -> dict:
    """Get current git branch and HEAD commit.

    Args:
        cwd: Working directory to run git commands in.

    Returns:
        Dict with 'branch' and 'commit' keys (values may be None if not in git repo).
    """
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {
            "branch": branch.stdout.strip() if branch.returncode == 0 else None,
            "commit": commit.stdout.strip() if commit.returncode == 0 else None,
        }
    except subprocess.TimeoutExpired:
        print("Warning: Git command timed out", file=sys.stderr)
        return {"branch": None, "commit": None}
    except FileNotFoundError:
        # Git not installed - not worth logging
        return {"branch": None, "commit": None}


def get_state_dir() -> Path:
    """Get directory for session state files.

    Returns:
        Path to state directory (~/.claude/session-log/state/).
    """
    state_dir = Path.home() / ".claude" / "session-log" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def handle_session_start(input_data: dict, state_dir: Path | None = None) -> dict:
    """Handle SessionStart event.

    Args:
        input_data: Hook input data containing session_id, cwd, etc.
        state_dir: Optional override for state directory (for testing).

    Returns:
        Dict with 'success' key indicating operation result.
    """
    if state_dir is None:
        state_dir = get_state_dir()

    session_id = input_data.get("session_id", "unknown")
    cwd = input_data.get("cwd", ".")

    git_info = get_git_info(cwd)

    state = {
        "session_id": session_id,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "cwd": cwd,
        "branch": git_info["branch"],
        "commit_start": git_info["commit"],
    }

    # Use session_id in filename to support concurrent sessions
    state_file = state_dir / f"session_{session_id}.json"
    try:
        state_file.write_text(json.dumps(state, indent=2))
    except OSError as e:
        print(f"Warning: Failed to write session state: {e}", file=sys.stderr)
        return {"success": False, "reason": str(e)}

    return {"success": True}


def main():
    """Entry point for hook."""
    try:
        input_data = json.load(sys.stdin)
        result = handle_session_start(input_data)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(f"SessionStart hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

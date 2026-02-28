"""Shared path utilities for handoff plugin scripts.

Provides project name detection and handoffs directory resolution.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_project_name() -> tuple[str, str]:
    """Get project name from git root directory, falling back to cwd.

    Returns:
        (project_name, source) where source is "git" or "cwd".
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name, "git"
        import sys
        print(f"Warning: git rev-parse failed (returncode={result.returncode}). Falling back to cwd.", file=sys.stderr)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        import sys
        print(f"Warning: git project detection failed ({type(exc).__name__}). Falling back to cwd.", file=sys.stderr)
    return Path.cwd().name, "cwd"


def get_handoffs_dir() -> Path:
    """Get handoffs directory: ~/.claude/handoffs/<project>/"""
    name, _ = get_project_name()
    return Path.home() / ".claude" / "handoffs" / name

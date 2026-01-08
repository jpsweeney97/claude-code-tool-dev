#!/usr/bin/env python3
"""
read_v2.py - Handoff skill v2 SessionStart hook script.

Responsibilities:
- Find latest handoff for current project
- Prune handoffs older than 30 days
- Output based on recency:
  - <24h: Auto-inject content
  - >24h: Prompt to resume
  - None: Signal no handoff

Exit Codes:
    0  - Success (output produced)
    1  - No handoff found (silent exit for hook)
"""

import subprocess
from pathlib import Path


def get_project_name() -> str:
    """Get project name from git root directory or current directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return Path.cwd().name

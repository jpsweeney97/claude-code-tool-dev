#!/usr/bin/env python3
"""
common.py - Shared utilities for handoff skill scripts.

Part of the handoff skill.

Provides:
- Result dataclass for consistent return values
- Directory resolution functions
- Frontmatter parsing
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class Result:
    """Standard result object for script operations."""
    success: bool
    message: str
    data: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "timestamp": datetime.now().isoformat()
        }


def get_project_name() -> str:
    """Get project name from git or directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return Path.cwd().name


def get_project_handoffs_dir() -> Path:
    """Get project-local handoffs directory."""
    claude_home = Path.home() / ".claude"

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip())
            # Avoid nested .claude/.claude when working inside ~/.claude
            if git_root == claude_home:
                return claude_home / "handoffs"
            return git_root / ".claude" / "handoffs"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return Path.cwd() / ".claude" / "handoffs"


def get_global_handoffs_dir() -> Path:
    """Get global handoffs directory."""
    return Path.home() / ".claude" / "handoffs"


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """Parse YAML frontmatter from markdown.

    Handles:
    - Standard YAML key: value pairs
    - JSON arrays in values (e.g., tags: ["a", "b"])
    """
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter_text = parts[1].strip()
    frontmatter = {}

    for line in frontmatter_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Try to parse JSON arrays
            if value.startswith("["):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass

            frontmatter[key] = value

    return frontmatter

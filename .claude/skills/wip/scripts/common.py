#!/usr/bin/env python3
"""
common.py - Shared utilities for WIP skill scripts.

Provides:
- Result dataclass for consistent return values
- WipItem and WipFile dataclasses
- Status enum
- Directory resolution functions
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Status(Enum):
    """Work item status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


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


@dataclass
class WipItem:
    """Single work-in-progress item."""
    id: str
    description: str
    added: datetime
    status: Status
    files: List[str] = field(default_factory=list)
    context: str = ""
    blocker: Optional[str] = None
    next_action: Optional[str] = None
    paused_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None


@dataclass
class WipFile:
    """Full WIP document."""
    version: int
    project: str
    updated: datetime
    next_id: int
    items: List[WipItem] = field(default_factory=list)


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


def get_wip_dir() -> Path:
    """Get WIP directory path."""
    claude_home = Path.home() / ".claude"

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip())
            if git_root == claude_home:
                return claude_home / "wip"
            return git_root / ".claude" / "wip"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return Path.cwd() / ".claude" / "wip"


def get_wip_path() -> Path:
    """Get WIP.md file path."""
    return get_wip_dir() / "WIP.md"


def get_archive_path() -> Path:
    """Get WIP-archive.md file path."""
    return get_wip_dir() / "WIP-archive.md"

#!/usr/bin/env python3
"""
common.py - Shared utilities for WIP skill scripts.

Provides:
- Result dataclass for consistent return values
- WipItem and WipFile dataclasses
- Status enum
- Directory resolution functions
"""

import fcntl
import json
import re
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


@contextmanager
def locked_wip_file(path: Path, mode: str = 'r'):
    """Context manager for locked file access.

    Uses shared lock (LOCK_SH) for reading, exclusive lock (LOCK_EX) for writing.
    """
    if 'w' in mode or 'a' in mode:
        path.parent.mkdir(parents=True, exist_ok=True)

    f = open(path, mode)
    try:
        lock_type = fcntl.LOCK_EX if ('w' in mode or 'a' in mode) else fcntl.LOCK_SH
        fcntl.flock(f.fileno(), lock_type)
        yield f
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()


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


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """Parse YAML frontmatter from markdown."""
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
            frontmatter[key.strip()] = value.strip()

    return frontmatter


def parse_wip(content: str) -> WipFile:
    """Parse WIP.md content into WipFile dataclass."""
    fm = parse_frontmatter(content)

    wip = WipFile(
        version=int(fm.get("version", 1)),
        project=fm.get("project", get_project_name()),
        updated=datetime.fromisoformat(fm.get("updated", datetime.now().isoformat())),
        next_id=int(fm.get("next_id", 1)),
        items=[]
    )

    # Parse items from each section
    section_pattern = r'^## (Active|Paused|Completed)\s*\n(.*?)(?=^## |\Z)'
    sections = re.findall(section_pattern, content, re.MULTILINE | re.DOTALL)

    status_map = {
        "Active": Status.ACTIVE,
        "Paused": Status.PAUSED,
        "Completed": Status.COMPLETED
    }

    for section_name, section_content in sections:
        status = status_map.get(section_name)
        if status and "(none)" not in section_content:
            items = parse_items_in_section(section_content, status)
            wip.items.extend(items)

    return wip


def parse_items_in_section(section_content: str, status: Status) -> List[WipItem]:
    """Parse individual items from a section."""
    items = []

    # Split by ### [WXXX] headers (W followed by any number of digits)
    item_pattern = r'^### \[(W\d+)\] (.+?)$'
    parts = re.split(item_pattern, section_content, flags=re.MULTILINE)

    # parts: ['', 'W001', 'Title1', 'content1', 'W002', 'Title2', 'content2', ...]
    i = 1
    while i < len(parts) - 2:
        item_id = parts[i]
        description = parts[i + 1].strip()
        item_content = parts[i + 2]

        item = parse_item_content(item_id, description, item_content, status)
        items.append(item)
        i += 3

    return items


def parse_item_content(item_id: str, description: str, content: str, status: Status) -> WipItem:
    """Parse the content of a single item."""
    # Extract metadata line: **Added:** 2026-01-05 | **Files:** src/a.py
    added = datetime.now()
    files = []

    meta_match = re.search(r'\*\*Added:\*\* ([\d-]+)', content)
    if meta_match:
        try:
            added = datetime.strptime(meta_match.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    files_match = re.search(r'\*\*Files:\*\* (.+?)(?:\n|$)', content)
    if files_match:
        files = [f.strip() for f in files_match.group(1).split(",")]

    # Extract blocker
    blocker = None
    blocker_match = re.search(r'\*\*Blocker:\*\* (.+?)(?:\n|$)', content)
    if blocker_match:
        blocker_text = blocker_match.group(1).strip()
        if blocker_text.lower() != "none":
            blocker = blocker_text

    # Extract next action
    next_action = None
    next_match = re.search(r'\*\*Next:\*\* (.+?)(?:\n|$)', content)
    if next_match:
        next_action = next_match.group(1).strip()

    # Extract context (everything between metadata and Blocker/Next)
    context = ""
    context_match = re.search(r'\*\*Files:\*\*[^\n]*\n\n(.+?)(?=\n\*\*Blocker|\n\*\*Next|\n---|$)', content, re.DOTALL)
    if context_match:
        context = context_match.group(1).strip()

    # Extract dates for paused/completed
    paused_date = None
    completed_date = None

    paused_match = re.search(r'\*\*Paused:\*\* ([\d-]+)', content)
    if paused_match:
        try:
            paused_date = datetime.strptime(paused_match.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    completed_match = re.search(r'\*\*Completed:\*\* ([\d-]+)', content)
    if completed_match:
        try:
            completed_date = datetime.strptime(completed_match.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    return WipItem(
        id=item_id,
        description=description,
        added=added,
        status=status,
        files=files,
        context=context,
        blocker=blocker,
        next_action=next_action,
        paused_date=paused_date,
        completed_date=completed_date
    )


def serialize_wip(wip: WipFile) -> str:
    """Serialize WipFile to markdown string."""
    lines = [
        "---",
        f"version: {wip.version}",
        f"project: {wip.project}",
        f"updated: {wip.updated.isoformat()}",
        f"next_id: {wip.next_id}",
        "---",
        "",
        "# Work In Progress",
        ""
    ]

    # Group items by status
    active = [i for i in wip.items if i.status == Status.ACTIVE]
    paused = [i for i in wip.items if i.status == Status.PAUSED]
    completed = [i for i in wip.items if i.status == Status.COMPLETED]

    # Active section
    lines.append("## Active")
    lines.append("")
    if active:
        for item in active:
            lines.extend(serialize_item(item))
    else:
        lines.append("(none)")
        lines.append("")
    lines.append("---")
    lines.append("")

    # Paused section
    lines.append("## Paused")
    lines.append("")
    if paused:
        for item in paused:
            lines.extend(serialize_item(item))
    else:
        lines.append("(none)")
        lines.append("")
    lines.append("---")
    lines.append("")

    # Completed section
    lines.append("## Completed")
    lines.append("")
    if completed:
        for item in completed:
            lines.extend(serialize_item(item))
    else:
        lines.append("(none)")
        lines.append("")
    lines.append("---")

    return "\n".join(lines)


def serialize_item(item: WipItem) -> List[str]:
    """Serialize a single WipItem to markdown lines."""
    lines = []

    # Header
    lines.append(f"### [{item.id}] {item.description}")

    # Metadata line
    meta_parts = [f"**Added:** {item.added.strftime('%Y-%m-%d')}"]
    if item.files:
        meta_parts.append(f"**Files:** {', '.join(item.files)}")
    if item.paused_date:
        meta_parts.append(f"**Paused:** {item.paused_date.strftime('%Y-%m-%d')}")
    if item.completed_date:
        meta_parts.append(f"**Completed:** {item.completed_date.strftime('%Y-%m-%d')}")
    lines.append(" | ".join(meta_parts))
    lines.append("")

    # Context
    if item.context:
        lines.append(item.context)
        lines.append("")

    # Blocker and Next (only for active items typically)
    if item.status == Status.ACTIVE:
        blocker_text = item.blocker if item.blocker else "None"
        lines.append(f"**Blocker:** {blocker_text}")
        if item.next_action:
            lines.append(f"**Next:** {item.next_action}")
        lines.append("")

    lines.append("---")
    lines.append("")

    return lines

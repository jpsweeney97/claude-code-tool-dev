# WIP Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a persistent, project-level work-in-progress tracker that survives across Claude Code sessions.

**Architecture:** Single markdown file (`.claude/wip/WIP.md`) with section-based organization (Active/Paused/Completed). Python scripts for parsing and mutation. SessionStart hook for auto-injection.

**Tech Stack:** Python 3.12 (stdlib only), markdown, YAML frontmatter

---

## Task 1: Create Directory Structure and Template

**Files:**
- Create: `.claude/skills/wip/SKILL.md` (placeholder)
- Create: `.claude/skills/wip/templates/wip-template.md`
- Create: `.claude/skills/wip/scripts/` (directory)

**Step 1: Create skill directory**

```bash
mkdir -p .claude/skills/wip/scripts .claude/skills/wip/templates
```

**Step 2: Create placeholder SKILL.md**

```markdown
---
name: wip
description: Persistent project-level work-in-progress tracking across sessions
metadata:
  version: 0.1.0
---

# WIP Skill

Work in progress - see implementation plan.
```

Save to: `.claude/skills/wip/SKILL.md`

**Step 3: Create WIP template**

```markdown
---
version: 1
project: {{PROJECT}}
updated: {{TIMESTAMP}}
next_id: 1
---

# Work In Progress

## Active

(none)

---

## Paused

(none)

---

## Completed

(none)

---
```

Save to: `.claude/skills/wip/templates/wip-template.md`

**Step 4: Commit**

```bash
git add .claude/skills/wip/
git commit -m "feat(wip): scaffold skill directory structure"
```

---

## Task 2: Implement common.py - Data Model

**Files:**
- Create: `.claude/skills/wip/scripts/common.py`

**Step 1: Write test file**

```python
#!/usr/bin/env python3
"""Tests for common.py"""

import sys
from pathlib import Path

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import Result, WipItem, WipFile, Status
from datetime import datetime


def test_result_to_dict():
    r = Result(success=True, message="ok", data={"key": "value"})
    d = r.to_dict()
    assert d["success"] is True
    assert d["message"] == "ok"
    assert d["data"]["key"] == "value"
    assert "timestamp" in d


def test_wip_item_creation():
    item = WipItem(
        id="W001",
        description="Test item",
        added=datetime(2026, 1, 7, 10, 0, 0),
        status=Status.ACTIVE,
    )
    assert item.id == "W001"
    assert item.status == Status.ACTIVE
    assert item.blocker is None


def test_status_enum():
    assert Status.ACTIVE.value == "active"
    assert Status.PAUSED.value == "paused"
    assert Status.COMPLETED.value == "completed"


if __name__ == "__main__":
    test_result_to_dict()
    test_wip_item_creation()
    test_status_enum()
    print("All tests passed!")
```

Save to: `.claude/skills/wip/scripts/test_common.py`

**Step 2: Run test to verify it fails**

```bash
python3 .claude/skills/wip/scripts/test_common.py
```

Expected: `ModuleNotFoundError: No module named 'common'`

**Step 3: Write common.py**

```python
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
```

Save to: `.claude/skills/wip/scripts/common.py`

**Step 4: Run test to verify it passes**

```bash
python3 .claude/skills/wip/scripts/test_common.py
```

Expected: `All tests passed!`

**Step 5: Commit**

```bash
git add .claude/skills/wip/scripts/
git commit -m "feat(wip): implement common.py with data model"
```

---

## Task 3: Implement Parsing - parse_frontmatter and parse_wip

**Files:**
- Modify: `.claude/skills/wip/scripts/common.py`
- Modify: `.claude/skills/wip/scripts/test_common.py`

**Step 1: Add parsing tests**

Append to `.claude/skills/wip/scripts/test_common.py`:

```python
def test_parse_frontmatter():
    content = """---
version: 1
project: test-project
updated: 2026-01-07T10:00:00
next_id: 3
---

# Work In Progress
"""
    fm = parse_frontmatter(content)
    assert fm["version"] == "1"
    assert fm["project"] == "test-project"
    assert fm["next_id"] == "3"


def test_parse_wip_empty():
    content = """---
version: 1
project: test
updated: 2026-01-07T10:00:00
next_id: 1
---

# Work In Progress

## Active

(none)

---

## Paused

(none)

---

## Completed

(none)

---
"""
    wip = parse_wip(content)
    assert wip.version == 1
    assert wip.project == "test"
    assert wip.next_id == 1
    assert len(wip.items) == 0


def test_parse_wip_with_items():
    content = """---
version: 1
project: test
updated: 2026-01-07T10:00:00
next_id: 3
---

# Work In Progress

## Active

### [W001] First item
**Added:** 2026-01-05 | **Files:** src/a.py

Context paragraph here.

**Blocker:** None
**Next:** Do something

---

### [W002] Second item
**Added:** 2026-01-06 | **Files:** src/b.py, src/c.py

More context.

**Blocker:** Waiting for review
**Next:** Wait

---

## Paused

(none)

---

## Completed

(none)

---
"""
    wip = parse_wip(content)
    assert len(wip.items) == 2
    assert wip.items[0].id == "W001"
    assert wip.items[0].description == "First item"
    assert wip.items[0].status == Status.ACTIVE
    assert wip.items[0].files == ["src/a.py"]
    assert wip.items[0].blocker is None
    assert wip.items[0].next_action == "Do something"

    assert wip.items[1].id == "W002"
    assert wip.items[1].blocker == "Waiting for review"
    assert wip.items[1].files == ["src/b.py", "src/c.py"]
```

Also update imports at top:
```python
from common import Result, WipItem, WipFile, Status, parse_frontmatter, parse_wip
```

And update `if __name__` block:
```python
if __name__ == "__main__":
    test_result_to_dict()
    test_wip_item_creation()
    test_status_enum()
    test_parse_frontmatter()
    test_parse_wip_empty()
    test_parse_wip_with_items()
    print("All tests passed!")
```

**Step 2: Run test to verify it fails**

```bash
python3 .claude/skills/wip/scripts/test_common.py
```

Expected: `ImportError: cannot import name 'parse_frontmatter'`

**Step 3: Implement parsing functions**

Append to `.claude/skills/wip/scripts/common.py`:

```python
import re


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

    # Split by ### [WXXX] headers
    item_pattern = r'^### \[(W\d{3})\] (.+?)$'
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
```

**Step 4: Run test to verify it passes**

```bash
python3 .claude/skills/wip/scripts/test_common.py
```

Expected: `All tests passed!`

**Step 5: Commit**

```bash
git add .claude/skills/wip/scripts/
git commit -m "feat(wip): implement WIP.md parsing"
```

---

## Task 4: Implement Serialization - serialize_wip

**Files:**
- Modify: `.claude/skills/wip/scripts/common.py`
- Modify: `.claude/skills/wip/scripts/test_common.py`

**Step 1: Add serialization test**

Append to test file:

```python
def test_serialize_wip_roundtrip():
    """Parse then serialize should produce equivalent content."""
    original = """---
version: 1
project: test
updated: 2026-01-07T10:00:00
next_id: 3
---

# Work In Progress

## Active

### [W001] First item
**Added:** 2026-01-05 | **Files:** src/a.py

Context here.

**Blocker:** None
**Next:** Do something

---

## Paused

(none)

---

## Completed

(none)

---
"""
    wip = parse_wip(original)
    serialized = serialize_wip(wip)
    reparsed = parse_wip(serialized)

    assert reparsed.version == wip.version
    assert reparsed.next_id == wip.next_id
    assert len(reparsed.items) == len(wip.items)
    assert reparsed.items[0].id == wip.items[0].id
    assert reparsed.items[0].description == wip.items[0].description
```

Update imports and main block.

**Step 2: Run test to verify it fails**

```bash
python3 .claude/skills/wip/scripts/test_common.py
```

Expected: `ImportError: cannot import name 'serialize_wip'`

**Step 3: Implement serialize_wip**

Append to `common.py`:

```python
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
```

**Step 4: Run test to verify it passes**

```bash
python3 .claude/skills/wip/scripts/test_common.py
```

Expected: `All tests passed!`

**Step 5: Commit**

```bash
git add .claude/skills/wip/scripts/
git commit -m "feat(wip): implement WIP serialization"
```

---

## Task 5: Implement init.py

**Files:**
- Create: `.claude/skills/wip/scripts/init.py`

**Step 1: Write test**

```python
#!/usr/bin/env python3
"""Tests for init.py"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from init import create_wip_file


def test_create_wip_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        wip_path = Path(tmpdir) / "WIP.md"
        result = create_wip_file(wip_path, project="test-project")

        assert result.success
        assert wip_path.exists()

        content = wip_path.read_text()
        assert "version: 1" in content
        assert "project: test-project" in content
        assert "next_id: 1" in content
        assert "## Active" in content


def test_create_wip_file_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        wip_path = Path(tmpdir) / "WIP.md"
        wip_path.write_text("existing content")

        result = create_wip_file(wip_path, project="test")

        assert not result.success
        assert "exists" in result.message.lower()


if __name__ == "__main__":
    test_create_wip_file()
    test_create_wip_file_exists()
    print("All tests passed!")
```

Save to: `.claude/skills/wip/scripts/test_init.py`

**Step 2: Run test to verify it fails**

```bash
python3 .claude/skills/wip/scripts/test_init.py
```

Expected: `ModuleNotFoundError: No module named 'init'`

**Step 3: Implement init.py**

```python
#!/usr/bin/env python3
"""
init.py - Create new WIP.md file.

Usage:
    python3 init.py [--force] [--path PATH]

Exit codes:
    0 - Success
    1 - File already exists
    2 - Write error
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from common import Result, WipFile, get_wip_path, get_project_name, serialize_wip


def create_wip_file(path: Path, project: str = None, force: bool = False) -> Result:
    """Create a new WIP.md file."""
    if path.exists() and not force:
        return Result(
            success=False,
            message=f"WIP file already exists: {path}",
            errors=["Use --force to overwrite"]
        )

    # Create parent directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create empty WIP file
    wip = WipFile(
        version=1,
        project=project or get_project_name(),
        updated=datetime.now(),
        next_id=1,
        items=[]
    )

    try:
        content = serialize_wip(wip)
        path.write_text(content)
        return Result(
            success=True,
            message=f"Created WIP file: {path}",
            data={"path": str(path)}
        )
    except OSError as e:
        return Result(
            success=False,
            message=f"Failed to write WIP file: {e}",
            errors=[str(e)]
        )


def main():
    parser = argparse.ArgumentParser(description="Create new WIP.md file")
    parser.add_argument("--force", action="store_true", help="Overwrite if exists")
    parser.add_argument("--path", type=Path, help="Custom path for WIP.md")
    parser.add_argument("--project", help="Project name")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    path = args.path or get_wip_path()
    result = create_wip_file(path, project=args.project, force=args.force)

    if args.json:
        import json
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.message)

    sys.exit(0 if result.success else (1 if "exists" in result.message else 2))


if __name__ == "__main__":
    main()
```

Save to: `.claude/skills/wip/scripts/init.py`

**Step 4: Run test to verify it passes**

```bash
python3 .claude/skills/wip/scripts/test_init.py
```

Expected: `All tests passed!`

**Step 5: Commit**

```bash
git add .claude/skills/wip/scripts/
git commit -m "feat(wip): implement init.py for WIP file creation"
```

---

## Task 6: Implement read.py

**Files:**
- Create: `.claude/skills/wip/scripts/read.py`

**Step 1: Write test**

```python
#!/usr/bin/env python3
"""Tests for read.py"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from read import read_wip, format_compact
from common import WipFile, WipItem, Status


def test_format_compact_empty():
    wip = WipFile(
        version=1, project="test",
        updated=datetime.now(), next_id=1, items=[]
    )
    output = format_compact(wip)
    assert "[WIP: 0 active" in output


def test_format_compact_with_items():
    wip = WipFile(
        version=1, project="test",
        updated=datetime.now(), next_id=3,
        items=[
            WipItem(id="W001", description="First task",
                    added=datetime.now(), status=Status.ACTIVE,
                    next_action="Do thing"),
            WipItem(id="W002", description="Blocked task",
                    added=datetime.now(), status=Status.ACTIVE,
                    blocker="Waiting for X"),
        ]
    )
    output = format_compact(wip)
    assert "[WIP: 2 active" in output
    assert "W001" in output
    assert "W002" in output
    assert "BLOCKED" in output


if __name__ == "__main__":
    test_format_compact_empty()
    test_format_compact_with_items()
    print("All tests passed!")
```

Save to: `.claude/skills/wip/scripts/test_read.py`

**Step 2: Run test to verify it fails**

```bash
python3 .claude/skills/wip/scripts/test_read.py
```

Expected: `ModuleNotFoundError: No module named 'read'`

**Step 3: Implement read.py**

```python
#!/usr/bin/env python3
"""
read.py - Display WIP items.

Usage:
    python3 read.py              # Full display
    python3 read.py --compact    # <100 tokens for SessionStart hook
    python3 read.py --json       # Structured output

Exit codes:
    0 - Success
    1 - File not found (silent for hooks)
"""

import argparse
import json
import sys
from pathlib import Path

from common import (
    Result, WipFile, WipItem, Status,
    get_wip_path, parse_wip
)


def read_wip(path: Path = None) -> Result:
    """Read and parse WIP.md file."""
    path = path or get_wip_path()

    if not path.exists():
        return Result(
            success=False,
            message="No WIP file found",
            errors=[f"Expected at: {path}"]
        )

    try:
        content = path.read_text()
        wip = parse_wip(content)
        return Result(
            success=True,
            message="WIP loaded",
            data={"wip": wip, "path": str(path)}
        )
    except Exception as e:
        return Result(
            success=False,
            message=f"Failed to parse WIP: {e}",
            errors=[str(e)]
        )


def format_compact(wip: WipFile) -> str:
    """Format WIP for SessionStart injection (<100 tokens)."""
    active = [i for i in wip.items if i.status == Status.ACTIVE]
    paused = [i for i in wip.items if i.status == Status.PAUSED]
    blocked = [i for i in active if i.blocker]

    lines = [f"[WIP: {len(active)} active, {len(paused)} paused]"]

    if active:
        lines.append("Active:")
        for item in active[:5]:  # Limit to 5 items
            if item.blocker:
                lines.append(f"  {item.id}: {item.description[:40]} [BLOCKED]")
            elif item.next_action:
                lines.append(f"  {item.id}: {item.description[:30]} → {item.next_action[:20]}")
            else:
                lines.append(f"  {item.id}: {item.description[:50]}")

        if len(active) > 5:
            lines.append(f"  ... and {len(active) - 5} more")

    return "\n".join(lines)


def format_full(wip: WipFile) -> str:
    """Format WIP for full display."""
    lines = [f"# Work In Progress ({wip.project})", ""]

    active = [i for i in wip.items if i.status == Status.ACTIVE]
    paused = [i for i in wip.items if i.status == Status.PAUSED]
    completed = [i for i in wip.items if i.status == Status.COMPLETED]

    if active:
        lines.append("## Active")
        for item in active:
            lines.append(format_item_full(item))
        lines.append("")

    if paused:
        lines.append("## Paused")
        for item in paused:
            lines.append(format_item_full(item))
        lines.append("")

    if completed:
        lines.append(f"## Completed ({len(completed)} items)")
        for item in completed[:3]:
            lines.append(f"- [{item.id}] {item.description}")
        if len(completed) > 3:
            lines.append(f"  ... and {len(completed) - 3} more")

    return "\n".join(lines)


def format_item_full(item: WipItem) -> str:
    """Format single item for display."""
    lines = [f"### [{item.id}] {item.description}"]
    lines.append(f"Added: {item.added.strftime('%Y-%m-%d')}")

    if item.files:
        lines.append(f"Files: {', '.join(item.files)}")
    if item.context:
        lines.append(f"Context: {item.context[:100]}...")
    if item.blocker:
        lines.append(f"**BLOCKED:** {item.blocker}")
    if item.next_action:
        lines.append(f"Next: {item.next_action}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Display WIP items")
    parser.add_argument("--compact", action="store_true", help="Compact format for hooks")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--path", type=Path, help="Custom WIP.md path")

    args = parser.parse_args()

    result = read_wip(args.path)

    if not result.success:
        # Silent failure for hooks
        if args.compact:
            sys.exit(0)
        print(result.message, file=sys.stderr)
        sys.exit(1)

    wip = result.data["wip"]

    if args.json:
        # Serialize WipFile to dict
        data = {
            "version": wip.version,
            "project": wip.project,
            "next_id": wip.next_id,
            "items": [
                {
                    "id": i.id,
                    "description": i.description,
                    "status": i.status.value,
                    "blocker": i.blocker,
                    "next_action": i.next_action
                }
                for i in wip.items
            ]
        }
        print(json.dumps(data, indent=2))
    elif args.compact:
        print(format_compact(wip))
    else:
        print(format_full(wip))


if __name__ == "__main__":
    main()
```

Save to: `.claude/skills/wip/scripts/read.py`

**Step 4: Run test to verify it passes**

```bash
python3 .claude/skills/wip/scripts/test_read.py
```

Expected: `All tests passed!`

**Step 5: Commit**

```bash
git add .claude/skills/wip/scripts/
git commit -m "feat(wip): implement read.py with compact format"
```

---

## Task 7: Implement update.py

**Files:**
- Create: `.claude/skills/wip/scripts/update.py`

**Step 1: Write test**

```python
#!/usr/bin/env python3
"""Tests for update.py"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from update import add_item, move_item, set_blocker
from common import WipFile, Status, serialize_wip, parse_wip


def test_add_item():
    with tempfile.TemporaryDirectory() as tmpdir:
        wip_path = Path(tmpdir) / "WIP.md"

        # Create initial WIP
        wip = WipFile(version=1, project="test",
                      updated=datetime.now(), next_id=1, items=[])
        wip_path.write_text(serialize_wip(wip))

        # Add item
        result = add_item(wip_path, "New task", files=["src/a.py"])

        assert result.success
        assert result.data["id"] == "W001"

        # Verify file
        content = wip_path.read_text()
        assert "W001" in content
        assert "New task" in content


def test_move_item():
    with tempfile.TemporaryDirectory() as tmpdir:
        wip_path = Path(tmpdir) / "WIP.md"

        # Create WIP with item
        wip = WipFile(version=1, project="test",
                      updated=datetime.now(), next_id=2, items=[])
        wip_path.write_text(serialize_wip(wip))
        add_item(wip_path, "Task to complete")

        # Move to completed
        result = move_item(wip_path, "W001", Status.COMPLETED)

        assert result.success

        # Verify
        reparsed = parse_wip(wip_path.read_text())
        assert reparsed.items[0].status == Status.COMPLETED


if __name__ == "__main__":
    test_add_item()
    test_move_item()
    print("All tests passed!")
```

Save to: `.claude/skills/wip/scripts/test_update.py`

**Step 2: Run test to verify it fails**

```bash
python3 .claude/skills/wip/scripts/test_update.py
```

Expected: `ModuleNotFoundError: No module named 'update'`

**Step 3: Implement update.py**

```python
#!/usr/bin/env python3
"""
update.py - Modify WIP items.

Usage:
    python3 update.py add --desc "Description" [--files "a.py,b.py"]
    python3 update.py move W001 --status completed
    python3 update.py block W001 --reason "Waiting for X"
    python3 update.py unblock W001
    python3 update.py set W001 --next "Do thing"
    python3 update.py archive

Exit codes:
    0 - Success
    1 - Input error (bad ID, missing args)
    2 - Write error
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from common import (
    Result, WipFile, WipItem, Status,
    get_wip_path, get_archive_path, parse_wip, serialize_wip
)


def load_wip(path: Path) -> tuple[Optional[WipFile], Optional[str]]:
    """Load WIP file, return (wip, error_message)."""
    if not path.exists():
        return None, f"WIP file not found: {path}"
    try:
        content = path.read_text()
        return parse_wip(content), None
    except Exception as e:
        return None, f"Failed to parse WIP: {e}"


def save_wip(path: Path, wip: WipFile) -> Optional[str]:
    """Save WIP file, return error message or None."""
    wip.updated = datetime.now()
    try:
        content = serialize_wip(wip)
        path.write_text(content)
        return None
    except Exception as e:
        return f"Failed to write WIP: {e}"


def add_item(
    path: Path,
    description: str,
    files: List[str] = None,
    context: str = "",
    next_action: str = None
) -> Result:
    """Add new item to WIP."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    # Generate ID
    item_id = f"W{wip.next_id:03d}"
    wip.next_id += 1

    item = WipItem(
        id=item_id,
        description=description,
        added=datetime.now(),
        status=Status.ACTIVE,
        files=files or [],
        context=context,
        next_action=next_action
    )
    wip.items.append(item)

    err = save_wip(path, wip)
    if err:
        return Result(success=False, message=err)

    return Result(
        success=True,
        message=f"Added {item_id}: {description}",
        data={"id": item_id}
    )


def move_item(path: Path, item_id: str, new_status: Status) -> Result:
    """Move item to different status."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    item = next((i for i in wip.items if i.id == item_id), None)
    if not item:
        return Result(
            success=False,
            message=f"Item not found: {item_id}",
            errors=[f"Valid IDs: {[i.id for i in wip.items]}"]
        )

    old_status = item.status
    item.status = new_status

    # Set date fields
    if new_status == Status.PAUSED:
        item.paused_date = datetime.now()
    elif new_status == Status.COMPLETED:
        item.completed_date = datetime.now()
    elif new_status == Status.ACTIVE:
        item.paused_date = None  # Clear if resuming

    err = save_wip(path, wip)
    if err:
        return Result(success=False, message=err)

    return Result(
        success=True,
        message=f"Moved {item_id} from {old_status.value} to {new_status.value}"
    )


def set_blocker(path: Path, item_id: str, reason: Optional[str]) -> Result:
    """Set or clear blocker on item."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    item = next((i for i in wip.items if i.id == item_id), None)
    if not item:
        return Result(success=False, message=f"Item not found: {item_id}")

    item.blocker = reason

    err = save_wip(path, wip)
    if err:
        return Result(success=False, message=err)

    if reason:
        return Result(success=True, message=f"Blocked {item_id}: {reason}")
    else:
        return Result(success=True, message=f"Unblocked {item_id}")


def set_field(path: Path, item_id: str, field: str, value: str) -> Result:
    """Set a field on an item."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    item = next((i for i in wip.items if i.id == item_id), None)
    if not item:
        return Result(success=False, message=f"Item not found: {item_id}")

    if field == "next":
        item.next_action = value
    elif field == "context":
        item.context = value
    elif field == "files":
        item.files = [f.strip() for f in value.split(",")]
    else:
        return Result(success=False, message=f"Unknown field: {field}")

    err = save_wip(path, wip)
    if err:
        return Result(success=False, message=err)

    return Result(success=True, message=f"Updated {item_id}.{field}")


def archive_completed(path: Path) -> Result:
    """Move completed items to archive file."""
    wip, err = load_wip(path)
    if err:
        return Result(success=False, message=err)

    completed = [i for i in wip.items if i.status == Status.COMPLETED]
    if not completed:
        return Result(success=True, message="No completed items to archive")

    # Remove from main WIP
    wip.items = [i for i in wip.items if i.status != Status.COMPLETED]

    # Append to archive
    archive_path = get_archive_path()
    archive_content = ""
    if archive_path.exists():
        archive_content = archive_path.read_text()

    # Add archived items with timestamp
    archive_lines = [
        f"\n## Archived {datetime.now().strftime('%Y-%m-%d')}\n"
    ]
    for item in completed:
        archive_lines.append(f"- [{item.id}] {item.description}")
        if item.completed_date:
            archive_lines.append(f"  Completed: {item.completed_date.strftime('%Y-%m-%d')}")
    archive_lines.append("")

    try:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with open(archive_path, "a") as f:
            f.write("\n".join(archive_lines))

        err = save_wip(path, wip)
        if err:
            return Result(success=False, message=err)

        return Result(
            success=True,
            message=f"Archived {len(completed)} items to {archive_path}"
        )
    except Exception as e:
        return Result(success=False, message=f"Failed to archive: {e}")


def main():
    parser = argparse.ArgumentParser(description="Modify WIP items")
    parser.add_argument("--path", type=Path, help="Custom WIP.md path")
    parser.add_argument("--json", action="store_true", help="JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add command
    add_parser = subparsers.add_parser("add", help="Add new item")
    add_parser.add_argument("--desc", required=True, help="Description")
    add_parser.add_argument("--files", help="Comma-separated file list")
    add_parser.add_argument("--context", default="", help="Context text")
    add_parser.add_argument("--next", dest="next_action", help="Next action")

    # move command
    move_parser = subparsers.add_parser("move", help="Move item status")
    move_parser.add_argument("item_id", help="Item ID (e.g., W001)")
    move_parser.add_argument("--status", required=True,
                             choices=["active", "paused", "completed"])

    # block command
    block_parser = subparsers.add_parser("block", help="Set blocker")
    block_parser.add_argument("item_id", help="Item ID")
    block_parser.add_argument("--reason", required=True, help="Blocker reason")

    # unblock command
    unblock_parser = subparsers.add_parser("unblock", help="Clear blocker")
    unblock_parser.add_argument("item_id", help="Item ID")

    # set command
    set_parser = subparsers.add_parser("set", help="Set field value")
    set_parser.add_argument("item_id", help="Item ID")
    set_parser.add_argument("--next", dest="next_val", help="Next action")
    set_parser.add_argument("--context", help="Context text")
    set_parser.add_argument("--files", help="Comma-separated files")

    # archive command
    subparsers.add_parser("archive", help="Archive completed items")

    args = parser.parse_args()
    path = args.path or get_wip_path()

    # Execute command
    if args.command == "add":
        files = [f.strip() for f in args.files.split(",")] if args.files else []
        result = add_item(path, args.desc, files, args.context, args.next_action)
    elif args.command == "move":
        status_map = {
            "active": Status.ACTIVE,
            "paused": Status.PAUSED,
            "completed": Status.COMPLETED
        }
        result = move_item(path, args.item_id.upper(), status_map[args.status])
    elif args.command == "block":
        result = set_blocker(path, args.item_id.upper(), args.reason)
    elif args.command == "unblock":
        result = set_blocker(path, args.item_id.upper(), None)
    elif args.command == "set":
        if args.next_val:
            result = set_field(path, args.item_id.upper(), "next", args.next_val)
        elif args.context:
            result = set_field(path, args.item_id.upper(), "context", args.context)
        elif args.files:
            result = set_field(path, args.item_id.upper(), "files", args.files)
        else:
            result = Result(success=False, message="No field specified")
    elif args.command == "archive":
        result = archive_completed(path)
    else:
        result = Result(success=False, message=f"Unknown command: {args.command}")

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.message)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
```

Save to: `.claude/skills/wip/scripts/update.py`

**Step 4: Run test to verify it passes**

```bash
python3 .claude/skills/wip/scripts/test_update.py
```

Expected: `All tests passed!`

**Step 5: Commit**

```bash
git add .claude/skills/wip/scripts/
git commit -m "feat(wip): implement update.py with CRUD operations"
```

---

## Task 8: Write SKILL.md Documentation

**Files:**
- Modify: `.claude/skills/wip/SKILL.md`

**Step 1: Write complete SKILL.md**

```markdown
---
name: wip
description: Persistent project-level work-in-progress tracking across sessions
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# WIP Skill

Track active work streams that persist across Claude Code sessions.

## Triggers

- `/wip` - Show current WIP items
- `/wip add <description>` - Add new item
- `/wip <id>` - Show item detail
- `/wip done <id>` - Mark completed
- `/wip block <id> <reason>` - Set blocker
- `/wip unblock <id>` - Clear blocker
- `/wip pause <id>` - Pause item
- `/wip resume <id>` - Resume paused item
- `/wip archive` - Move completed to archive

## Quick Reference

| Command | Action |
|---------|--------|
| `/wip` | Show active and blocked items |
| `/wip add Feature X` | Create new active item |
| `/wip W001` | Show full detail for W001 |
| `/wip done W001` | Mark W001 completed |
| `/wip block W001 Waiting for API` | Block W001 |
| `/wip unblock W001` | Clear blocker |
| `/wip pause W001` | Move to paused |
| `/wip resume W001` | Resume from paused |
| `/wip archive` | Archive completed items |

## How It Works

**Storage:** `.claude/wip/WIP.md` - single markdown file, version controlled.

**Sections:** Items organized by status (Active/Paused/Completed). Items move between sections on status change.

**IDs:** Sequential `W001`, `W002`, etc. Never reused.

**Archive:** Completed items stay in WIP.md until `/wip archive` moves them to `WIP-archive.md`.

## Item Structure

```markdown
### [W001] Implement authentication middleware
**Added:** 2026-01-05 | **Files:** src/auth/jwt.py, src/auth/middleware.py

JWT-based auth for API endpoints. Using RS256 for verification.

**Blocker:** None
**Next:** Write integration tests
```

## Scripts

Run scripts directly - do not read into context:

| Script | Purpose | Exit Codes |
|--------|---------|------------|
| `scripts/init.py` | Create WIP.md | 0=success, 1=exists, 2=error |
| `scripts/read.py` | Display items | 0=success, 1=not found |
| `scripts/update.py` | Modify items | 0=success, 1=input error, 2=write error |

### Usage Examples

**Initialize WIP:**
```bash
python3 ~/.claude/skills/wip/scripts/init.py
```

**Add item:**
```bash
python3 ~/.claude/skills/wip/scripts/update.py add \
  --desc "Implement feature X" \
  --files "src/x.py,src/y.py" \
  --next "Write failing tests"
```

**Mark completed:**
```bash
python3 ~/.claude/skills/wip/scripts/update.py move W001 --status completed
```

**Compact view (for hooks):**
```bash
python3 ~/.claude/skills/wip/scripts/read.py --compact
```

## SessionStart Hook

Add to settings to auto-inject WIP summary:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/skills/wip/scripts/read.py --compact 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

## Workflows

### Starting Work

1. User starts session
2. Hook injects WIP summary (active items, blockers)
3. Claude acknowledges current work state
4. User continues from context

### Adding New Work

1. User: `/wip add Implement caching layer`
2. Claude runs `update.py add --desc "..."`
3. Claude confirms: "Added W003: Implement caching layer"
4. Claude asks: "What files will this involve? Any next steps?"

### Completing Work

1. User: `/wip done W001`
2. Claude runs `update.py move W001 --status completed`
3. Claude confirms and asks if ready to archive

### Blocking/Unblocking

1. User: `/wip block W002 Waiting for design review`
2. Claude runs `update.py block W002 --reason "..."`
3. Item shows as blocked in next session's injection

## Relationship to Other Tools

| Tool | Use For |
|------|---------|
| **WIP** | Active work streams across sessions |
| **TodoWrite** | Subtask breakdown within sessions |
| **Handoff** | Detailed context transfer at session end |

**Pattern:** WIP tracks what; handoff captures why and how.

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| >10 active items | Too much parallel work | Pause or complete some |
| Items with no next action | Unclear what to do | Always set next step |
| Never archiving | File grows unbounded | Archive weekly |
| Duplicate with TodoWrite | Confusion about source of truth | WIP = persistent, Todo = session |

## Verification

After operations, verify:
- [ ] WIP.md exists at `.claude/wip/WIP.md`
- [ ] Item IDs are unique and sequential
- [ ] Sections are properly formatted
- [ ] Hook injection is <100 tokens
```

Save to: `.claude/skills/wip/SKILL.md`

**Step 2: Commit**

```bash
git add .claude/skills/wip/SKILL.md
git commit -m "docs(wip): write complete SKILL.md documentation"
```

---

## Task 9: End-to-End Test

**Step 1: Initialize WIP**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
python3 .claude/skills/wip/scripts/init.py
```

Expected: `Created WIP file: .claude/wip/WIP.md`

**Step 2: Add items**

```bash
python3 .claude/skills/wip/scripts/update.py add --desc "Test feature" --files "src/test.py" --next "Write tests"
python3 .claude/skills/wip/scripts/update.py add --desc "Another task"
```

Expected: `Added W001: Test feature` and `Added W002: Another task`

**Step 3: View items**

```bash
python3 .claude/skills/wip/scripts/read.py
python3 .claude/skills/wip/scripts/read.py --compact
```

Verify both formats work correctly.

**Step 4: Modify items**

```bash
python3 .claude/skills/wip/scripts/update.py block W001 --reason "Waiting for review"
python3 .claude/skills/wip/scripts/update.py move W002 --status completed
```

**Step 5: Archive**

```bash
python3 .claude/skills/wip/scripts/update.py archive
```

Verify `WIP-archive.md` created and W002 removed from main file.

**Step 6: Clean up test data**

```bash
rm .claude/wip/WIP.md .claude/wip/WIP-archive.md
```

**Step 7: Final commit**

```bash
git add .claude/skills/wip/
git commit -m "feat(wip): complete WIP skill implementation"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Directory structure and template |
| 2 | common.py data model |
| 3 | Parsing functions |
| 4 | Serialization functions |
| 5 | init.py |
| 6 | read.py |
| 7 | update.py |
| 8 | SKILL.md documentation |
| 9 | End-to-end test |

**Total commits:** 8 (one per task except e2e test is final)

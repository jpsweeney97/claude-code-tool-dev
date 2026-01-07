#!/usr/bin/env python3
"""Tests for common.py"""

import sys
from pathlib import Path

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import Result, WipItem, WipFile, Status, parse_frontmatter, parse_wip, serialize_wip
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


if __name__ == "__main__":
    test_result_to_dict()
    test_wip_item_creation()
    test_status_enum()
    test_parse_frontmatter()
    test_parse_wip_empty()
    test_parse_wip_with_items()
    test_serialize_wip_roundtrip()
    print("All tests passed!")

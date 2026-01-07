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
                      updated=datetime.now(), next_id=1, items=[])
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

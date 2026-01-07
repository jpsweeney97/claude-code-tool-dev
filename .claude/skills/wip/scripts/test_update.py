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


def test_add_item_auto_init():
    """Adding to non-existent WIP.md should auto-create it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wip_path = Path(tmpdir) / "subdir" / "WIP.md"
        # Don't create the file first

        result = add_item(wip_path, "First task")

        assert result.success, f"Expected success but got: {result.message}"
        assert result.data["id"] == "W001"
        assert wip_path.exists()


def test_add_item_sanitizes_newlines():
    """Newlines in description should be replaced with spaces."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wip_path = Path(tmpdir) / "WIP.md"
        wip = WipFile(version=1, project="test",
                      updated=datetime.now(), next_id=1, items=[])
        wip_path.write_text(serialize_wip(wip))

        result = add_item(wip_path, "Task with\nnewline\r\nhere")

        assert result.success
        reparsed = parse_wip(wip_path.read_text())
        assert reparsed.items[0].description == "Task with newline here"


def test_add_item_rejects_empty_description():
    """Empty description after sanitization should fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wip_path = Path(tmpdir) / "WIP.md"
        wip = WipFile(version=1, project="test",
                      updated=datetime.now(), next_id=1, items=[])
        wip_path.write_text(serialize_wip(wip))

        result = add_item(wip_path, "   \n\r\n   ")

        assert not result.success
        assert "empty" in result.message.lower()


if __name__ == "__main__":
    test_add_item()
    test_move_item()
    test_add_item_auto_init()
    test_add_item_sanitizes_newlines()
    test_add_item_rejects_empty_description()
    print("All tests passed!")

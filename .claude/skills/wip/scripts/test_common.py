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

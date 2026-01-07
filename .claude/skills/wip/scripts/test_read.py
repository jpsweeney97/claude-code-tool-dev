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

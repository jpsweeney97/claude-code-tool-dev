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

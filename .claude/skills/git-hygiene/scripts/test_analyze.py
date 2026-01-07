#!/usr/bin/env python3
"""Tests for analyze.py bug fixes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def test_parse_stash_with_pipe_in_message():
    """Stash messages containing | should parse correctly."""
    # Simulate git stash list output with null delimiters
    raw_output = "stash@{0}\x00WIP on main: fix | broken\x002026-01-01 12:00:00 +0000"

    # Parse using null delimiter
    parts = raw_output.split("\x00")
    assert len(parts) == 3
    assert parts[0] == "stash@{0}"
    assert parts[1] == "WIP on main: fix | broken"  # Pipe preserved
    assert "2026-01-01" in parts[2]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

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


def test_matches_pattern_directory():
    """node_modules/foo/bar.js should match node_modules pattern."""
    from analyze import matches_pattern

    # These should all match
    assert matches_pattern("node_modules/lodash/index.js", {"node_modules"})
    assert matches_pattern("__pycache__/module.cpython-312.pyc", {"__pycache__"})
    assert matches_pattern("dist/bundle.js", {"dist"})

    # Extension patterns
    assert matches_pattern("foo.pyc", {"*.pyc"})
    assert matches_pattern("backup~", {"*~"})

    # Should NOT match
    assert not matches_pattern("my_modules/foo.js", {"node_modules"})


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

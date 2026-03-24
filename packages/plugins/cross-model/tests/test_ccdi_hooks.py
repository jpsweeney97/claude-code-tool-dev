"""Tests for CCDI PostToolUse inventory refresh hook.

Covers all 6 test rows from delivery.md:
1. Hook fires on docs_epoch change
2. Hook skips non-epoch changes
3. Hook handles build failure gracefully
4. Manual --force bypasses epoch check
5. Hook ignores tool_result field
6. Hook ignores root-level docs_epoch
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any
from unittest.mock import MagicMock

import pytest

from hooks.ccdi_inventory_refresh import process_event


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_payload(
    *,
    tool_response: dict[str, Any] | None = None,
    tool_result: dict[str, Any] | None = None,
    root_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a PostToolUse payload.

    By default, tool_response and tool_result are empty dicts.
    root_extra merges additional top-level keys.
    """
    payload: dict[str, Any] = {
        "tool_name": "mcp__claude-code-docs__search_docs",
    }
    if tool_response is not None:
        payload["tool_response"] = tool_response
    if tool_result is not None:
        payload["tool_result"] = tool_result
    if root_extra is not None:
        payload.update(root_extra)
    return payload


# ===========================================================================
# Test 1: Hook fires on docs_epoch change
# ===========================================================================


class TestHookFiresOnEpochChange:
    """Test 1: PostToolUse with docs_epoch in tool_response → build invoked."""

    def test_build_invoked_when_epoch_present(self) -> None:
        payload = _make_payload(
            tool_response={"docs_epoch": "2026-03-20abc", "results": []}
        )
        build_fn = MagicMock(return_value=True)
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is True
        build_fn.assert_called_once()

    def test_epoch_value_passed_to_build(self) -> None:
        payload = _make_payload(
            tool_response={"docs_epoch": "epoch-v42", "results": []}
        )
        build_fn = MagicMock(return_value=True)
        process_event(payload, build_fn=build_fn)
        build_fn.assert_called_once_with("epoch-v42")


# ===========================================================================
# Test 2: Hook skips non-epoch changes
# ===========================================================================


class TestHookSkipsNonEpoch:
    """Test 2: PostToolUse without docs_epoch in tool_response → NOT invoked."""

    def test_no_epoch_in_tool_response(self) -> None:
        payload = _make_payload(
            tool_response={"results": ["some result"]}
        )
        build_fn = MagicMock()
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is False
        build_fn.assert_not_called()

    def test_empty_tool_response(self) -> None:
        payload = _make_payload(tool_response={})
        build_fn = MagicMock()
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is False
        build_fn.assert_not_called()

    def test_missing_tool_response(self) -> None:
        payload = _make_payload()  # no tool_response key at all
        build_fn = MagicMock()
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is False
        build_fn.assert_not_called()


# ===========================================================================
# Test 3: Hook handles build failure gracefully
# ===========================================================================


class TestHookHandlesBuildFailure:
    """Test 3: build_fn fails → hook logs warning, returns False, no exception."""

    def test_build_raises_exception(self) -> None:
        payload = _make_payload(
            tool_response={"docs_epoch": "2026-03-20abc"}
        )
        build_fn = MagicMock(side_effect=RuntimeError("MCP connection refused"))
        triggered = process_event(payload, build_fn=build_fn)
        # Hook must NOT propagate the exception — fail-open
        assert triggered is False
        build_fn.assert_called_once()

    def test_build_returns_false(self) -> None:
        payload = _make_payload(
            tool_response={"docs_epoch": "2026-03-20abc"}
        )
        build_fn = MagicMock(return_value=False)
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is False


# ===========================================================================
# Test 4: Manual --force bypasses epoch check
# ===========================================================================


class TestManualForce:
    """Test 4: build_inventory.py --force executes regardless of epoch.

    This tests the CLI __main__ path. Since the real build_inventory
    requires MCP, we verify by running it and checking exit code (will fail
    at MCP step, but the --force flag should be accepted by argparse).
    """

    def test_force_flag_accepted(self) -> None:
        """Verify --force is a valid argument for build_inventory CLI."""
        proc = subprocess.run(
            [sys.executable, "-m", "scripts.ccdi.build_inventory", "--force"],
            capture_output=True,
            text=True,
            cwd="/Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/ccdi/packages/plugins/cross-model",
        )
        # Will exit 1 because MCP is not available, but should NOT exit 2
        # (argparse error). The error message should be about MCP, not about
        # unrecognized arguments.
        assert proc.returncode == 1
        assert "unrecognized arguments" not in proc.stderr


# ===========================================================================
# Test 5: Hook ignores tool_result field
# ===========================================================================


class TestHookIgnoresToolResult:
    """Test 5: docs_epoch under tool_result (wrong key) → NOT invoked."""

    def test_epoch_in_tool_result_ignored(self) -> None:
        payload = _make_payload(
            tool_result={"docs_epoch": "2026-03-20abc"},
            tool_response={"results": []},
        )
        build_fn = MagicMock()
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is False
        build_fn.assert_not_called()

    def test_epoch_only_in_tool_result(self) -> None:
        payload = _make_payload(
            tool_result={"docs_epoch": "2026-03-20abc"},
        )
        build_fn = MagicMock()
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is False
        build_fn.assert_not_called()


# ===========================================================================
# Test 6: Hook ignores root-level docs_epoch
# ===========================================================================


class TestHookIgnoresRootEpoch:
    """Test 6: docs_epoch at root of JSON, not under tool_response → NOT invoked."""

    def test_epoch_at_root_ignored(self) -> None:
        payload = _make_payload(
            root_extra={"docs_epoch": "2026-03-20abc"},
            tool_response={"results": []},
        )
        build_fn = MagicMock()
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is False
        build_fn.assert_not_called()

    def test_epoch_at_root_without_tool_response(self) -> None:
        payload = _make_payload(
            root_extra={"docs_epoch": "2026-03-20abc"},
        )
        build_fn = MagicMock()
        triggered = process_event(payload, build_fn=build_fn)
        assert triggered is False
        build_fn.assert_not_called()

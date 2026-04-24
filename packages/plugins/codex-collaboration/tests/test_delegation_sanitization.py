"""Packet 1: _sanitize_error_string bounds & class-prefix format for forensic fields."""

from __future__ import annotations

import pytest

from server.delegation_controller import _sanitize_error_string


def test_sanitize_class_prefix_and_message() -> None:
    exc = RuntimeError("boom")
    assert _sanitize_error_string(exc) == "RuntimeError: boom"


def test_sanitize_truncates_message_at_200_chars_with_ellipsis() -> None:
    exc = RuntimeError("x" * 400)
    out = _sanitize_error_string(exc)
    # Message portion is truncated to 200 chars + "..." suffix
    assert out.startswith("RuntimeError: ")
    message_portion = out[len("RuntimeError: ") :]
    assert message_portion.endswith("...")
    assert len(message_portion) == 203  # 200 chars + "..."


def test_sanitize_strips_newlines_and_control_chars() -> None:
    exc = RuntimeError("line1\nline2\tcolumn")
    out = _sanitize_error_string(exc)
    assert "\n" not in out
    assert "\t" not in out
    assert "\\n" in out
    assert "\\t" in out


def test_sanitize_caps_total_at_256_chars() -> None:
    # Over-long class name triggers the combined cap.
    class ExceptionClassWithAVeryVeryVeryVeryVeryVeryVeryLongName(RuntimeError):
        pass

    exc = ExceptionClassWithAVeryVeryVeryVeryVeryVeryVeryLongName("x" * 400)
    # Guard: prove the fixture actually exceeds the cap before sanitization.
    # class_name (55) + ": " (2) + truncated_message (203) = 260 > 256.
    # This tripwire prevents future edits from accidentally returning the
    # fixture to a vacuous pass (where the 200-char message cap alone would
    # keep combined length under 256 regardless of _SANITIZE_TOTAL_CAP).
    unbounded = f"{type(exc).__name__}: {'x' * 200}..."
    assert len(unbounded) > 256

    out = _sanitize_error_string(exc)
    assert len(out) <= 256


def test_sanitize_handles_short_message_without_truncation() -> None:
    exc = BrokenPipeError("broken")
    assert _sanitize_error_string(exc) == "BrokenPipeError: broken"

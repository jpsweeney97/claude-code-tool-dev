"""Shared test harness for format redactor tests.

Provides assertion helpers and common case definitions. Used by D1
(test_redact_formats.py) and D3 (test_redact_json.py, test_redact_yaml.py,
test_redact_toml.py) to ensure consistent output contract verification.
"""

from __future__ import annotations

from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatRedactResult,
    FormatSuppressed,
)


def assert_redact_result(
    outcome: FormatRedactOutcome,
    *,
    expected_text: str | None = None,
    expected_count: int | None = None,
) -> FormatRedactResult:
    """Assert outcome is FormatRedactResult, optionally check text and count."""
    assert isinstance(outcome, FormatRedactResult), (
        f"Expected FormatRedactResult, got {type(outcome).__name__}"
    )
    if expected_text is not None:
        assert outcome.text == expected_text, (
            f"Text mismatch:\n  expected: {expected_text!r}\n  got:      {outcome.text!r}"
        )
    if expected_count is not None:
        assert outcome.redactions_applied == expected_count, (
            f"Count mismatch: expected {expected_count}, got {outcome.redactions_applied}"
        )
    return outcome


def assert_suppressed(
    outcome: FormatRedactOutcome,
    *,
    reason_contains: str | None = None,
) -> FormatSuppressed:
    """Assert outcome is FormatSuppressed, optionally check reason."""
    assert isinstance(outcome, FormatSuppressed), (
        f"Expected FormatSuppressed, got {type(outcome).__name__}"
    )
    if reason_contains is not None:
        assert reason_contains in outcome.reason, (
            f"Reason mismatch: expected substring {reason_contains!r} in {outcome.reason!r}"
        )
    return outcome


# Common test cases for output contract verification across all format redactors.
# Each tuple: (description, input_text, expected_redactions).
# Format-specific tests extend these with their own cases.
COMMON_REDACTION_CASES: list[tuple[str, str, int]] = [
    ("empty input", "", 0),
    ("whitespace only", "  \n  \n", 0),
]

"""Tests for format-specific config redactors."""

import pytest

from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatRedactResult,
    FormatSuppressed,
    redact_env,
)
from tests.redaction_harness import assert_redact_result


# --- Type tests ---


class TestFormatRedactTypes:
    def test_result_is_frozen(self) -> None:
        r = FormatRedactResult(text="a", redactions_applied=1)
        with pytest.raises(AttributeError):
            r.text = "b"

    def test_suppressed_is_frozen(self) -> None:
        s = FormatSuppressed(reason="test_desync")
        with pytest.raises(AttributeError):
            s.reason = "other"

    def test_union_type_discriminates(self) -> None:
        r: FormatRedactOutcome = FormatRedactResult(text="a", redactions_applied=0)
        s: FormatRedactOutcome = FormatSuppressed(reason="x")
        assert isinstance(r, FormatRedactResult)
        assert isinstance(s, FormatSuppressed)


# --- Env redactor ---


class TestRedactEnv:
    def test_basic_key_value(self) -> None:
        r = assert_redact_result(redact_env("DB_HOST=localhost\n"))
        assert r.text == "DB_HOST=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_multiple_keys(self) -> None:
        r = assert_redact_result(redact_env("A=1\nB=2\nC=3\n"))
        assert r.redactions_applied == 3
        assert "A=[REDACTED:value]" in r.text
        assert "B=[REDACTED:value]" in r.text
        assert "C=[REDACTED:value]" in r.text

    def test_export_prefix(self) -> None:
        r = assert_redact_result(redact_env("export SECRET=hunter2\n"))
        assert r.text == "export SECRET=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_quoted_double(self) -> None:
        r = assert_redact_result(redact_env('KEY="value with spaces"\n'))
        assert r.text == "KEY=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_quoted_single(self) -> None:
        r = assert_redact_result(redact_env("KEY='value'\n"))
        assert r.text == "KEY=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_comments_preserved(self) -> None:
        text = "# Database config\nDB_HOST=localhost\n# End\n"
        r = assert_redact_result(redact_env(text))
        assert "# Database config" in r.text
        assert "# End" in r.text
        assert r.redactions_applied == 1

    def test_empty_value(self) -> None:
        r = assert_redact_result(redact_env("EMPTY=\n"))
        assert "EMPTY=[REDACTED:value]" in r.text
        assert r.redactions_applied == 1

    def test_value_with_equals_sign(self) -> None:
        r = assert_redact_result(redact_env("URL=https://host?key=val\n"))
        assert r.text == "URL=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_backslash_continuation(self) -> None:
        # Each \\ in source -> one \ in content. Each \n -> newline.
        # Content: KEY=line1\ + newline + line2 + newline
        text = "KEY=line1\\\nline2\n"
        r = assert_redact_result(redact_env(text))
        assert r.text == "KEY=[REDACTED:value]\n"
        assert r.redactions_applied == 1
        assert "line2" not in r.text  # Continuation consumed

    def test_empty_input(self) -> None:
        r = assert_redact_result(redact_env(""))
        assert r.text == ""
        assert r.redactions_applied == 0

    def test_whitespace_only(self) -> None:
        r = assert_redact_result(redact_env("  \n  \n"))
        assert r.redactions_applied == 0

    def test_no_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_env("KEY=val"))
        assert not r.text.endswith("\n")

    def test_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_env("KEY=val\n"))
        assert r.text.endswith("\n")

    def test_bare_export_preserved(self) -> None:
        """'export KEY' without = is preserved as-is."""
        r = assert_redact_result(redact_env("export PATH\n"))
        assert r.text == "export PATH\n"
        assert r.redactions_applied == 0

    def test_multi_continuation_lines(self) -> None:
        """Multiple continuation lines all consumed into one redaction."""
        text = "KEY=val\\\nmore\\\nlast\nNEXT=zzz\n"
        r = assert_redact_result(redact_env(text))
        assert "KEY=[REDACTED:value]" in r.text
        assert "NEXT=[REDACTED:value]" in r.text
        assert r.redactions_applied == 2
        assert "more" not in r.text
        assert "last" not in r.text

    def test_continuation_eats_assignment_line(self) -> None:
        """Continuation consumes next line even if it looks like key=value.

        Security posture: don't leak continuation payloads as separate keys.
        """
        text = "KEY=val\\\nEVIL=secret\nNEXT=yyy\n"
        r = assert_redact_result(redact_env(text))
        assert "KEY=[REDACTED:value]" in r.text
        assert "NEXT=[REDACTED:value]" in r.text
        assert r.redactions_applied == 2
        assert "EVIL" not in r.text
        assert "secret" not in r.text

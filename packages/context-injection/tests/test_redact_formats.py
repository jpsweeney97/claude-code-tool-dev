"""Tests for format-specific config redactors."""

import pytest

from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatRedactResult,
    FormatSuppressed,
    redact_env,
    redact_ini,
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
        assert "# [REDACTED:comment]" in r.text
        assert "Database config" not in r.text
        assert "End" not in r.text.replace("[REDACTED:comment]", "")
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

    def test_comment_body_redacted_not_counted(self) -> None:
        """Comment redaction does not increment redactions_applied."""
        text = "# secret comment\nKEY=val\n"
        r = assert_redact_result(redact_env(text))
        assert "# [REDACTED:comment]" in r.text
        assert "secret comment" not in r.text
        assert r.redactions_applied == 1  # only the key=value counts

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


# --- INI redactor ---


class TestRedactIni:
    def test_equals_separator(self) -> None:
        r = assert_redact_result(redact_ini("key = value\n"))
        assert r.text == "key = [REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_no_space_equals(self) -> None:
        r = assert_redact_result(redact_ini("key=value\n"))
        assert r.text == "key=[REDACTED:value]\n"

    def test_colon_separator(self) -> None:
        r = assert_redact_result(redact_ini("host: localhost\n"))
        assert r.text == "host: [REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_first_separator_wins(self) -> None:
        """When both = and : present, first one is the separator."""
        r = assert_redact_result(redact_ini("url = https://host:8080\n"))
        assert r.text == "url = [REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_colon_before_equals(self) -> None:
        r = assert_redact_result(redact_ini("host: name=value\n"))
        assert r.text == "host: [REDACTED:value]\n"

    def test_section_headers_preserved(self) -> None:
        text = "[database]\nhost = localhost\nport = 5432\n"
        r = assert_redact_result(redact_ini(text))
        assert "[database]" in r.text
        assert r.redactions_applied == 2

    def test_semicolon_comment(self) -> None:
        text = "; comment\nkey = value\n"
        r = assert_redact_result(redact_ini(text))
        assert "; [REDACTED:comment]" in r.text
        assert r.redactions_applied == 1

    def test_hash_comment(self) -> None:
        text = "# comment\nkey = value\n"
        r = assert_redact_result(redact_ini(text))
        assert "# [REDACTED:comment]" in r.text
        assert r.redactions_applied == 1

    def test_no_value_key_preserved(self) -> None:
        """Key without separator is preserved as-is."""
        r = assert_redact_result(redact_ini("bare_key\n"))
        assert r.text == "bare_key\n"
        assert r.redactions_applied == 0

    def test_empty_value(self) -> None:
        r = assert_redact_result(redact_ini("key =\n"))
        assert "[REDACTED:value]" in r.text
        assert r.redactions_applied == 1

    def test_empty_input(self) -> None:
        r = assert_redact_result(redact_ini(""))
        assert r.redactions_applied == 0

    def test_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_ini("key=val\n"))
        assert r.text.endswith("\n")

    def test_no_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_ini("key=val"))
        assert not r.text.endswith("\n")

    def test_multiple_sections(self) -> None:
        text = "[s1]\na = 1\n[s2]\nb = 2\n"
        r = assert_redact_result(redact_ini(text))
        assert "[s1]" in r.text
        assert "[s2]" in r.text
        assert r.redactions_applied == 2

    def test_whitespace_after_separator_preserved(self) -> None:
        """Multi-space between separator and value is preserved exactly."""
        r = assert_redact_result(redact_ini("key =  value\n"))
        assert r.text == "key =  [REDACTED:value]\n"


class TestRedactIniPropertiesMode:
    def test_exclamation_comment(self) -> None:
        text = "! comment\nkey = value\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert "! [REDACTED:comment]" in r.text
        assert r.redactions_applied == 1

    def test_exclamation_not_comment_in_standard_mode(self) -> None:
        """! is NOT a comment prefix in standard INI mode."""
        text = "!key = value\n"
        r = assert_redact_result(redact_ini(text, properties_mode=False))
        # ! is part of the key, line still has = so it's redacted
        assert "[REDACTED:value]" in r.text

    def test_backslash_continuation(self) -> None:
        # Content: key=line1\ + newline + (spaces)line2\ + newline + (spaces)line3 + newline
        text = "key=line1\\\n  line2\\\n  line3\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert r.text == "key=[REDACTED:value]\n"
        assert r.redactions_applied == 1
        assert "line2" not in r.text
        assert "line3" not in r.text

    def test_escaped_backslash_not_continuation(self) -> None:
        # Content: key=value\\ (two backslashes) + newline + other=val + newline
        # Two trailing backslashes = even count = NOT continuation
        text = "key=value\\\\\nother=val\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert r.redactions_applied == 2

    def test_no_continuation_in_standard_mode(self) -> None:
        """Standard INI mode does NOT handle backslash continuation."""
        text = "key=line1\\\nline2\n"
        r = assert_redact_result(redact_ini(text, properties_mode=False))
        # Both lines processed independently
        assert r.redactions_applied == 1  # Only key=line1\ has =, line2 has no =

    def test_mid_continuation_passthrough(self) -> None:
        """Mid-continuation excerpt: no key= visible, line passed through.

        Generic token layer (D2a) catches secrets in passthrough lines.
        This test documents the accepted limitation.
        """
        text = "  continued_secret_value\nnormal_key=normal_value\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert "continued_secret_value" in r.text  # Passed through (no key=)
        assert "normal_key=[REDACTED:value]" in r.text
        assert r.redactions_applied == 1

    def test_properties_continuation_and_backstop_ordering(self) -> None:
        """Continuation + ordering: format redactor handles known patterns,
        generic token layer (D2a) is the backstop for missed patterns.

        This test verifies the format redactor correctly collapses continuations.
        The ordering guarantee (format-specific then generic) is tested in D2a.
        """
        text = "db.password=supersecret\\\n  continued\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert r.text == "db.password=[REDACTED:value]\n"
        assert r.redactions_applied == 1
        assert "supersecret" not in r.text
        assert "continued" not in r.text

    def test_mid_continuation_secret_survives_format_redaction(self) -> None:
        """Accepted limitation: a secret on a mid-continuation passthrough
        line survives format-specific redaction. D2a's generic token backstop
        is responsible for catching it.

        This is an executable reminder — if this test ever fails (secret
        gets redacted), the D2a backstop test may need updating.
        """
        # Simulates an excerpt starting mid-continuation: the first line
        # has no key= prefix, so the format redactor passes it through.
        text = "  secret_api_key_12345\nnormal_key = safe_value\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        # Secret survives format-specific redaction (no key= to trigger it)
        assert "secret_api_key_12345" in r.text
        # Normal key IS redacted
        assert "normal_key = [REDACTED:value]" in r.text
        assert r.redactions_applied == 1

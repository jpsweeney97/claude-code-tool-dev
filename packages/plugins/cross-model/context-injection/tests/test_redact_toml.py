"""Tests for TOML format redactor."""

from context_injection.redact_formats import FormatRedactResult, redact_toml
from tests.redaction_harness import assert_redact_result

_RV = "[REDACTED:value]"


class TestRedactToml:
    # --- Basic key=value ---

    def test_basic_string_value(self) -> None:
        r = assert_redact_result(redact_toml('host = "localhost"\n'))
        assert "host =" in r.text
        assert "localhost" not in r.text
        assert r.redactions_applied == 1

    def test_integer_value(self) -> None:
        r = assert_redact_result(redact_toml("port = 5432\n"))
        assert "port =" in r.text
        assert "5432" not in r.text

    def test_boolean_value(self) -> None:
        r = assert_redact_result(redact_toml("debug = true\n"))
        assert "debug =" in r.text
        assert "true" not in r.text

    def test_multiple_keys(self) -> None:
        text = 'host = "localhost"\nport = 5432\n'
        r = assert_redact_result(redact_toml(text))
        assert r.redactions_applied == 2

    def test_no_space_around_equals(self) -> None:
        r = assert_redact_result(redact_toml('key="value"\n'))
        assert "key=" in r.text
        assert r.redactions_applied == 1

    def test_whitespace_after_equals_preserved(self) -> None:
        r = assert_redact_result(redact_toml('key =  "value"\n'))
        assert "key =  " in r.text

    def test_empty_string_value(self) -> None:
        r = assert_redact_result(redact_toml('key = ""\n'))
        assert r.redactions_applied == 1

    def test_dotted_key(self) -> None:
        r = assert_redact_result(redact_toml('server.host = "localhost"\n'))
        assert "server.host =" in r.text
        assert "localhost" not in r.text

    # --- Structure preserved ---

    def test_table_header_preserved(self) -> None:
        text = '[database]\nhost = "localhost"\n'
        r = assert_redact_result(redact_toml(text))
        assert "[database]" in r.text
        assert r.redactions_applied == 1

    def test_array_of_tables_preserved(self) -> None:
        text = '[[servers]]\nname = "alpha"\n'
        r = assert_redact_result(redact_toml(text))
        assert "[[servers]]" in r.text
        assert r.redactions_applied == 1

    def test_comment_body_redacted(self) -> None:
        text = '# Database config\nhost = "localhost"\n'
        r = assert_redact_result(redact_toml(text))
        assert "# [REDACTED:comment]" in r.text
        assert "Database config" not in r.text
        assert r.redactions_applied == 1

    def test_inline_comment_after_value_consumed(self) -> None:
        """Inline # after value is consumed by value redaction (existing behavior)."""
        text = 'host = "localhost"  # production server\n'
        r = assert_redact_result(redact_toml(text))
        assert "host =" in r.text
        assert "localhost" not in r.text
        assert "production server" not in r.text
        assert r.redactions_applied == 1

    # --- Multi-line strings ---

    def test_multiline_basic_string(self) -> None:
        text = 'desc = """\nLine one\nLine two\n"""\nkey = "val"\n'
        r = assert_redact_result(redact_toml(text))
        assert "Line one" not in r.text
        assert "Line two" not in r.text
        assert "key =" in r.text
        assert r.redactions_applied == 2

    def test_multiline_literal_string(self) -> None:
        text = "desc = '''\nLine one\nLine two\n'''\nkey = 'val'\n"
        r = assert_redact_result(redact_toml(text))
        assert "Line one" not in r.text
        assert r.redactions_applied == 2

    def test_same_line_triple_quote(self) -> None:
        """Triple-quoted string opening and closing on same line."""
        r = assert_redact_result(redact_toml('key = """content"""\n'))
        assert "content" not in r.text
        assert r.redactions_applied == 1

    def test_eof_in_multiline_no_desync(self) -> None:
        """Excerpt ends inside multi-line string -- normal for windows."""
        result = redact_toml('key = """\nunclosed content')
        assert isinstance(result, FormatRedactResult)

    # --- Complex values ---

    def test_inline_table(self) -> None:
        r = assert_redact_result(redact_toml("point = {x = 1, y = 2}\n"))
        assert "point =" in r.text
        assert r.redactions_applied == 1

    def test_array_value(self) -> None:
        r = assert_redact_result(redact_toml("ports = [8080, 443, 80]\n"))
        assert "ports =" in r.text
        assert "8080" not in r.text

    # --- Orphaned triple-quote (mid-excerpt) ---

    def test_orphaned_triple_quote_continues(self) -> None:
        """Closing triple-quote without opener -- assume prior multiline, continue."""
        text = 'leftover content\n"""\nkey = "secret"\n'
        r = assert_redact_result(redact_toml(text))
        assert "key =" in r.text
        assert "secret" not in r.text
        assert r.redactions_applied >= 1

    def test_orphaned_literal_triple_quote_continues(self) -> None:
        text = "leftover\n'''\nkey = 'secret'\n"
        r = assert_redact_result(redact_toml(text))
        assert "key =" in r.text
        assert "secret" not in r.text
        assert r.redactions_applied >= 1

    def test_multiline_array_continuation_passthrough(self) -> None:
        """Multi-line array: opening line redacted, continuations pass through.

        Known limitation -- continuation lines are not tracked. Generic token
        backstop handles any secrets in continuation lines.
        """
        text = "ports = [\n  8080,\n  443\n]\nkey = 'val'\n"
        r = assert_redact_result(redact_toml(text))
        assert "ports =" in r.text
        assert "key =" in r.text

    # --- Edge cases ---

    def test_empty_input(self) -> None:
        r = assert_redact_result(redact_toml(""))
        assert r.redactions_applied == 0

    def test_whitespace_only(self) -> None:
        r = assert_redact_result(redact_toml("  \n  \n"))
        assert r.redactions_applied == 0

    def test_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_toml('key = "val"\n'))
        assert r.text.endswith("\n")

    def test_no_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_toml('key = "val"'))
        assert not r.text.endswith("\n")

    def test_unrecognized_line_preserved(self) -> None:
        """Lines without = that don't match any pattern pass through."""
        text = "some random text\nkey = val\n"
        r = assert_redact_result(redact_toml(text))
        assert "some random text" in r.text
        assert r.redactions_applied == 1
